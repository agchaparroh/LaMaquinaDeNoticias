"""
API FastAPI para Spider Factory 2.0

Proporciona endpoints para análisis, generación y gestión de spiders.
"""
import os
import csv
import io
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from uuid import uuid4

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import httpx

from analyzer import SmartAnalyzer, SiteAnalysisRequest, AnalysisStrategy, AnalysisResult, ScrapingStrategy
from generator import SpiderGenerator
from patterns import PatternStorage, PatternStatus, SitePattern
from config import SpiderFactoryConfig, get_redis_client
from websocket_manager import ConnectionManager
from batch_processor import BatchProcessor, BatchRequest, BatchResponse

# Pydantic models para API
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


# Configuración
config = SpiderFactoryConfig()

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Modelos Pydantic para la API
class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "2.0.0"
    services: Dict[str, str]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class AnalysisRequest(BaseModel):
    url: HttpUrl
    force_analysis: bool = False
    check_rss: bool = True


class AnalysisResponse(BaseModel):
    url: str
    strategy: str
    confidence: float
    rss_url: Optional[str] = None
    selectors: Optional[Dict[str, str]] = None
    needs_javascript: bool = False
    from_cache: bool = False
    sample_articles: Optional[List[Dict[str, Any]]] = None
    analysis_time: float


class GenerateSpiderRequest(BaseModel):
    analysis_result: Dict[str, Any]  # AnalysisResult as dict
    spider_name: str
    site_name: str
    metadata: Dict[str, Any] = {}


class GenerateSpiderResponse(BaseModel):
    spider_name: str
    file_path: str
    code_preview: str
    is_valid: bool
    generation_time: float


class PatternSearchRequest(BaseModel):
    domain: Optional[str] = None
    strategy: Optional[str] = None
    min_confidence: float = 0.0


class PatternSearchResponse(BaseModel):
    patterns: List[Dict[str, Any]]
    total: int


class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


# Crear aplicación FastAPI
app = FastAPI(
    title="Spider Factory 2.0 API",
    description="Sistema inteligente de generación de spiders para scraping de noticias",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],  # Ajustar en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estado global
app.state.start_time = time.time()
app.state.active_tasks: Dict[str, Dict[str, Any]] = {}

# Instancias de servicios
analyzer = SmartAnalyzer()
generator = SpiderGenerator()
pattern_storage = PatternStorage()
ws_manager = ConnectionManager()
batch_processor = BatchProcessor(analyzer, generator, ws_manager)


@app.on_event("startup")
async def startup_event():
    """Inicialización al arrancar la aplicación"""
    logger.info("Iniciando Spider Factory 2.0 API...")
    
    # Verificar conexión Redis
    try:
        redis_client = get_redis_client()
        if redis_client:
            await redis_client.ping()
            logger.info("Redis conectado correctamente")
    except Exception as e:
        logger.error(f"Redis no está disponible: {e}")
    
    # Crear directorios necesarios
    directories = ["generated_spiders", "logs", "templates/spiders"]
    for dir_name in directories:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
    
    logger.info("Spider Factory 2.0 API iniciada correctamente")


@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar la aplicación"""
    logger.info("Cerrando Spider Factory 2.0 API...")
    
    # Cerrar conexiones WebSocket
    for ws in app.state.websocket_connections:
        await ws.close()
    
    # Cerrar cliente HTTP del analyzer
    await analyzer.close()


@app.get("/", response_model=Dict[str, str])
async def root():
    """Endpoint raíz con información básica"""
    return {
        "service": "Spider Factory 2.0",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Verificar salud del sistema"""
    services = {}
    
    # Verificar Redis
    try:
        redis = get_redis_client()
        if redis:
            await redis.ping()
            services["redis"] = "healthy"
            # Contar patrones
            pattern_count = await pattern_storage.count_patterns()
        else:
            services["redis"] = "unavailable"
            pattern_count = 0
    except Exception as e:
        services["redis"] = f"error: {str(e)}"
        pattern_count = 0
    
    # Verificar Firecrawl
    services["firecrawl"] = "configured" if config.firecrawl_api_key else "not_configured"
    
    # Verificar generador
    services["generator"] = "healthy" if generator.templates_dir.exists() else "templates_missing"
    
    return HealthCheckResponse(
        status="healthy" if services.get("redis") == "healthy" else "degraded",
        timestamp=datetime.now(),
        version="2.0.0",
        services=services
    )


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_site(request: AnalysisRequest):
    """Analizar un sitio web para determinar estrategia de scraping"""
    start_time = time.time()
    
    try:
        # Crear request para el analyzer
        analysis_request = SiteAnalysisRequest(
            url=str(request.url),
            force_analysis=request.force_analysis,
            check_rss=request.check_rss
        )
        
        # Ejecutar análisis
        result = await analyzer.analyze(analysis_request)
        
        # Convertir a response model
        return AnalysisResponse(
            url=str(result.url),
            strategy=result.strategy.value,
            confidence=result.confidence,
            rss_url=result.rss_url,
            selectors=result.selectors,
            needs_javascript=result.needs_javascript,
            from_cache=result.from_cache,
            sample_articles=result.sample_articles,
            analysis_time=time.time() - start_time
        )
        
    except httpx.HTTPError as e:
        logger.error(f"Error HTTP en análisis: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Error conectando con el sitio: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error en análisis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate", response_model=GenerateSpiderResponse)
async def generate_spider(request: GenerateSpiderRequest):
    """Generar un spider basado en análisis"""
    start_time = time.time()
    
    try:
        # Reconstruir AnalysisResult desde el dict
        analysis_result = AnalysisResult(
            url=request.analysis_result.get("url"),
            domain=request.analysis_result.get("domain", ""),
            strategy=ScrapingStrategy(request.analysis_result.get("strategy", "scraping")),
            confidence=request.analysis_result.get("confidence", 0.5),
            rss_url=request.analysis_result.get("rss_url"),
            selectors=request.analysis_result.get("selectors"),
            needs_javascript=request.analysis_result.get("needs_javascript", False),
            url_patterns=request.analysis_result.get("url_patterns"),
            sample_articles=request.analysis_result.get("sample_articles"),
            from_cache=request.analysis_result.get("from_cache", False)
        )
        
        # Generar código del spider
        spider_code = generator.generate_spider(
            analysis_result,
            request.spider_name,
            request.site_name,
            request.metadata
        )
        
        # Validar código
        is_valid = generator.validate_spider(spider_code)
        
        if not is_valid:
            raise ValueError("El código generado tiene errores de sintaxis")
        
        # Guardar spider
        output_dir = Path("generated_spiders")
        output_dir.mkdir(exist_ok=True)
        
        file_path = output_dir / f"{request.spider_name}.py"
        file_path.write_text(spider_code, encoding="utf-8")
        
        # Preview del código (primeras 50 líneas)
        code_lines = spider_code.split('\n')
        code_preview = '\n'.join(code_lines[:50])
        if len(code_lines) > 50:
            code_preview += "\n\n# ... (código truncado)"
        
        return GenerateSpiderResponse(
            spider_name=request.spider_name,
            file_path=str(file_path),
            code_preview=code_preview,
            is_valid=is_valid,
            generation_time=time.time() - start_time
        )
        
    except Exception as e:
        logger.error(f"Error generando spider: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch/analyze")
async def batch_analyze(file_content: str, session_id: str = "default"):
    """Analizar múltiples sitios desde CSV"""
    try:
        # Procesar CSV con el batch processor
        response = await batch_processor.process_csv_file(file_content, session_id)
        
        return response
        
    except Exception as e:
        logger.error(f"Error en análisis batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/patterns/search", response_model=PatternSearchResponse)
async def search_patterns(request: PatternSearchRequest):
    """Buscar patrones almacenados"""
    try:
        # Buscar patrones
        if request.domain:
            patterns = await pattern_storage.search_by_domain(request.domain)
        elif request.strategy:
            patterns = await pattern_storage.search_by_strategy(ScrapingStrategy(request.strategy))
        else:
            # Obtener todos los patrones
            patterns = await pattern_storage.get_all_patterns(limit=100)
        
        # Filtrar por confianza mínima
        filtered_patterns = [
            p for p in patterns 
            if p.confidence >= request.min_confidence
        ]
        
        # Convertir a dict para respuesta
        pattern_dicts = [
            {
                "domain": p.domain,
                "strategy": p.strategy.value,
                "confidence": p.confidence,
                "selectors": p.selectors,
                "last_updated": p.last_updated.isoformat(),
                "times_used": p.times_used,
                "success_rate": p.success_rate
            }
            for p in filtered_patterns
        ]
        
        return PatternSearchResponse(
            patterns=pattern_dicts,
            total=len(pattern_dicts)
        )
        
    except Exception as e:
        logger.error(f"Error buscando patrones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket para actualizaciones en tiempo real"""
    await ws_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Mantener la conexión abierta
            data = await websocket.receive_text()
            
            # Echo para mantener viva la conexión
            await ws_manager.send_to_session(
                session_id,
                {
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, session_id)
        logger.info(f"WebSocket desconectado: {session_id}")
                    "error": str(e)
                })
        
        # Completar tarea
        task.status = SpiderStatus.COMPLETED
        task.progress = 100.0
        task.result = {
            "total_requested": len(sites),
            "generated": sum(1 for r in results if r.get('success')),
            "failed": sum(1 for r in results if not r.get('success')),
            "results": results
        }
        task.updated_at = datetime.now()
        
    except Exception as e:
        task.status = SpiderStatus.FAILED
        task.error = str(e)
        task.updated_at = datetime.now()
    
    finally:
        await _broadcast_progress(task)


@app.get("/patterns/search", response_model=PatternSearchResponse)
async def search_patterns(
    domain: Optional[str] = None,
    status: Optional[str] = None,
    min_confidence: Optional[float] = None,
    strategy: Optional[AnalysisStrategy] = None,
    limit: int = 50
):
    """Buscar patrones almacenados"""
    try:
        # Convertir status string a enum si se proporciona
        pattern_status = None
        if status:
            try:
                pattern_status = PatternStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Estado inválido: {status}"
                )
        
        # Buscar patrones
        patterns = pattern_storage.search_patterns(
            status=pattern_status,
            min_confidence=min_confidence,
            strategy=strategy,
            limit=limit
        )
        
        # Filtrar por dominio si se especifica
        if domain:
            patterns = [p for p in patterns if domain.lower() in p.domain.lower()]
        
        # Convertir a dict para response
        pattern_dicts = []
        for pattern in patterns:
            pattern_dict = pattern.dict()
            pattern_dict['id'] = f"{pattern.domain}:{pattern.section}"
            pattern_dicts.append(pattern_dict)
        
        return PatternSearchResponse(
            total=len(pattern_dicts),
            patterns=pattern_dicts
        )
        
    except Exception as e:
        logger.error(f"Error buscando patrones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/patterns/top", response_model=Dict[str, Any])
async def get_top_patterns(limit: int = 10):
    """Obtener patrones más usados"""
    try:
        top_patterns = pattern_storage.get_top_patterns(limit)
        
        return {
            "patterns": [
                {"pattern_id": pattern_id, "usage_count": count}
                for pattern_id, count in top_patterns
            ]
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo top patrones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Obtener estado de una tarea asíncrona"""
    if task_id not in app.state.active_tasks:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    return app.state.active_tasks[task_id]


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: Optional[str] = None):
    """WebSocket para actualizaciones en tiempo real"""
    # Conectar usando el manager
    actual_session_id = await ws_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Mantener conexión viva y recibir mensajes
            data = await websocket.receive_text()
            
            # Manejar diferentes tipos de mensajes
            if data == "ping":
                await ws_manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                    websocket
                )
            else:
                # Broadcast a la sesión
                await ws_manager.broadcast_to_session(
                    {
                        "type": "message",
                        "data": data,
                        "session_id": actual_session_id,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    actual_session_id
                )
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info(f"Cliente desconectado de sesión {actual_session_id}")


async def _broadcast_progress(task: TaskStatus, session_id: str = None):
    """Broadcast progreso usando el WebSocket manager"""
    message = {
        "type": "task_progress",
        "task_id": task.task_id,
        "status": task.status.value,
        "progress": task.progress,
        "current_step": task.current_step,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if session_id:
        # Enviar solo a una sesión específica
        await ws_manager.broadcast_to_session(message, session_id)
    else:
        # Enviar a todas las sesiones activas
        for session in ws_manager.active_connections:
            await ws_manager.broadcast_to_session(message, session)


@app.get("/download/{spider_name}")
async def download_spider(spider_name: str):
    """Descargar archivo de spider generado"""
    file_path = Path(config.output_directory) / f"{spider_name}.py"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Spider no encontrado")
    
    return FileResponse(
        path=str(file_path),
        filename=f"{spider_name}.py",
        media_type="text/x-python"
    )


# Manejo de errores global
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Manejador personalizado de excepciones HTTP"""
    return ErrorResponse(
        error=f"HTTP {exc.status_code}",
        message=exc.detail,
        details={"path": str(request.url)},
        timestamp=datetime.now()
    ).dict()


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Manejador general de excepciones"""
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    
    return ErrorResponse(
        error="Internal Server Error",
        message="Ha ocurrido un error inesperado",
        details={"type": type(exc).__name__},
        timestamp=datetime.now()
    ).dict()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "spider_factory.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )