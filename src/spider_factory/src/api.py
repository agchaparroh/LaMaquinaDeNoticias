"""
API FastAPI para Spider Factory 2.0

Proporciona endpoints para análisis, generación y gestión de spiders.
"""
import os
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
import httpx

from .analyzer import SmartAnalyzer, SiteAnalysisRequest, AnalysisResult, AnalysisStrategy
from .generator import SpiderGenerator
from .patterns import PatternStorage, PatternStatus, Pattern
from .config import settings
from .redis_pool import get_redis_client
from .websocket_manager import ConnectionManager
from .batch_processor import BatchProcessor, BatchRequest, BatchResponse, BatchSite
from .models import GenerateSpiderRequest

# Pydantic models para API
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from enum import Enum


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
    name: str = ""  # MANTENER por compatibilidad
    force_analysis: bool = False
    check_rss: bool = True
    
    # Nuevos campos opcionales (Fase 1 - retrocompatibilidad)
    medio: Optional[str] = None
    seccion: Optional[str] = None
    area_geografica: Optional[str] = None
    tipo_medio: Optional[Literal["diario", "revista", "agencia"]] = None
    frecuencia_minutos: Optional[int] = 60
    comentarios: Optional[str] = None
    rss_url: Optional[HttpUrl] = None
    
    @validator('medio', pre=True, always=True)
    def set_medio_from_name(cls, v, values):
        # Si no hay medio, usar name como fallback
        return v or values.get('name', 'Sin nombre')
    
    @validator('seccion', pre=True, always=True)
    def set_default_seccion(cls, v):
        # Si no hay sección, usar "general" por defecto
        return v or 'general'
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://elpais.com/internacional",
                "medio": "El País",
                "seccion": "Internacional",
                "area_geografica": "ESPAÑA",
                "tipo_medio": "diario",
                "frecuencia_minutos": 60
            }
        }


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
    
    # Nuevos campos
    medio: str
    seccion: str
    area_geografica: str
    tipo_medio: str
    frecuencia_minutos: int


# GenerateSpiderRequest now imported from models.py


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


class DuplicateCheckRequest(BaseModel):
    medio: str = Field(..., description="Nombre del medio")
    seccion: str = Field(..., description="Sección específica del medio")
    
    class Config:
        schema_extra = {
            "example": {
                "medio": "El País",
                "seccion": "Internacional"
            }
        }


class DuplicateCheckResponse(BaseModel):
    exists: bool
    spider_name: Optional[str] = None
    file_path: Optional[str] = None
    similar_spiders: List[str] = []
    message: str


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
        redis_client = await get_redis_client()
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
    
    # Cerrar conexiones
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
    
    # Verificar Redis con cliente síncrono simple (hotfix temporal)
    try:
        import redis
        redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
        ping_result = redis_client.ping()
        if ping_result:
            services["redis"] = "healthy"
        else:
            services["redis"] = "unavailable"
    except Exception as e:
        services["redis"] = f"error: {str(e)}"
    
    # Verificar Firecrawl
    services["firecrawl"] = "configured" if settings.firecrawl_api_key else "not_configured"
    
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
        # Usar nuevos campos si están presentes, sino fallback a los antiguos
        medio = request.medio or request.name
        seccion = request.seccion or "general"
        area_geografica = request.area_geografica or "GLOBAL"
        tipo_medio = request.tipo_medio or "diario"
        
        # Crear request para el analyzer con nuevos campos
        analysis_request = SiteAnalysisRequest(
            url=str(request.url),
            medio=medio,
            seccion=seccion,
            area_geografica=area_geografica,
            tipo_medio=tipo_medio,
            frecuencia_minutos=request.frecuencia_minutos,
            comentarios=request.comentarios,
            rss_url=request.rss_url,
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
            rss_url=str(result.rss_url) if result.rss_url else None,
            selectors=result.selectors.dict() if result.selectors else None,
            needs_javascript=result.needs_javascript,
            from_cache=result.from_cache,
            sample_articles=result.sample_articles,
            analysis_time=time.time() - start_time,
            # Nuevos campos
            medio=result.medio,
            seccion=result.seccion,
            area_geografica=result.area_geografica,
            tipo_medio=result.tipo_medio,
            frecuencia_minutos=result.frecuencia_minutos
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


@app.post(
    "/api/check-duplicate",
    response_model=DuplicateCheckResponse,
    summary="Verifica duplicados de spiders",
    description="Verifica si ya existe un spider para el medio y sección especificados",
    responses={
        200: {"description": "Verificación completada"},
        400: {"description": "Datos inválidos"},
        500: {"description": "Error del servidor"}
    }
)
async def check_duplicate(request: DuplicateCheckRequest):
    """Verifica si un spider medio_seccion ya existe"""
    try:
        # Generar nombre del spider
        spider_name = f"{request.medio.lower().replace(' ', '_')}_{request.seccion.lower().replace(' ', '_')}"
        
        # Verificar si existe el archivo
        file_path = Path(settings.SPIDER_OUTPUT_PATH) / f"{spider_name}.py"
        exists = file_path.exists()
        
        # Buscar spiders similares
        similar_spiders = []
        if Path(settings.SPIDER_OUTPUT_PATH).exists():
            # Buscar archivos que contengan el nombre del medio
            medio_pattern = request.medio.lower().replace(' ', '_')
            for spider_file in Path(settings.SPIDER_OUTPUT_PATH).glob("*.py"):
                if medio_pattern in spider_file.stem and spider_file.stem != spider_name:
                    similar_spiders.append(spider_file.stem)
        
        return DuplicateCheckResponse(
            exists=exists,
            spider_name=spider_name if exists else None,
            file_path=str(file_path) if exists else None,
            similar_spiders=similar_spiders[:5],  # Limitar a 5 similares
            message="Spider ya existe" if exists else "Nombre disponible"
        )
        
    except Exception as e:
        logger.error(f"Error verificando duplicado: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate", response_model=GenerateSpiderResponse)
async def generate_spider(request: GenerateSpiderRequest):
    """Generar un spider basado en análisis"""
    start_time = time.time()
    
    try:
        # Los campos básicos ahora son obligatorios en el modelo
        medio = request.medio
        seccion = request.seccion
        area_geografica = request.area_geografica
        tipo_medio = request.tipo_medio
        frecuencia_minutos = request.frecuencia_minutos or 60
        
        # Generar nombre del spider automáticamente
        spider_name = request.spider_name  # Usa la propiedad del modelo
        
        # Obtener análisis: desde URL o desde patrón
        analysis_result = None
        
        if request.analysis_url:
            # Realizar análisis de la URL con todos los campos obligatorios
            analyzer = SmartAnalyzer()
            analysis_request = SiteAnalysisRequest(
                url=request.analysis_url,
                medio=medio,
                seccion=seccion,
                area_geografica=area_geografica,
                tipo_medio=tipo_medio,
                frecuencia_minutos=frecuencia_minutos,
                comentarios=request.comentarios
            )
            analysis_result = await analyzer.analyze(analysis_request)
            
        else:
            raise HTTPException(status_code=400, detail="Debe proporcionar analysis_url para el análisis")
        
        # Generar código del spider usando la instancia global del generator
        additional_config = {
            'comentarios': request.comentarios,
            'excluded_urls': request.excluded_urls,
            'follow_pagination': request.follow_pagination,
            'max_pages': request.max_pages,
            'custom_settings': request.custom_settings
        }
        
        spider_code = generator.generate_spider(
            analysis=analysis_result,
            medio=medio,
            seccion=seccion,
            area_geografica=area_geografica,
            tipo_medio=tipo_medio,
            frecuencia_minutos=frecuencia_minutos,
            additional_config=additional_config
        )
        
        # Validar código
        is_valid = generator.validate_spider(spider_code)
        
        if not is_valid:
            raise ValueError("El código generado tiene errores de sintaxis")
        
        # Directorio de salida correcto según el plan
        output_dir = Path(settings.SPIDER_OUTPUT_PATH)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / f"{spider_name}.py"
        file_path.write_text(spider_code, encoding="utf-8")
        
        # Preview del código (primeras 50 líneas)
        code_lines = spider_code.split('\n')
        code_preview = '\n'.join(code_lines[:50])
        if len(code_lines) > 50:
            code_preview += "\n\n# ... (código truncado)"
        
        logger.info(f"Spider generado: {spider_name} en {file_path}")
        
        return GenerateSpiderResponse(
            spider_name=spider_name,
            file_path=str(file_path),
            code_preview=code_preview,
            is_valid=is_valid,
            generation_time=time.time() - start_time
        )
        
    except Exception as e:
        logger.error(f"Error generando spider: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch/analyze")
async def batch_analyze(
    file: UploadFile = File(...),
    session_id: str = Form(default="default")
):
    """Analizar múltiples sitios desde CSV"""
    try:
        # Leer contenido del archivo
        content = await file.read()
        file_content = content.decode('utf-8')
        
        # Procesar CSV con el batch processor
        response = await batch_processor.process_csv_file(file_content, session_id)
        
        return response
        
    except Exception as e:
        logger.error(f"Error en análisis batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch/generate")
async def batch_generate(request: BatchRequest):
    """Generar múltiples spiders"""
    try:
        # Procesar batch
        response = await batch_processor.process_batch(request)
        
        return response
        
    except Exception as e:
        logger.error(f"Error en generación batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/patterns/search", response_model=PatternSearchResponse)
async def search_patterns(request: PatternSearchRequest):
    """Buscar patrones almacenados"""
    try:
        # Buscar patrones
        if request.domain:
            patterns = await pattern_storage.search_by_domain(request.domain)
        elif request.strategy:
            patterns = await pattern_storage.search_by_strategy(AnalysisStrategy(request.strategy))
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


@app.get("/download/{spider_name}")
async def download_spider(spider_name: str):
    """Descargar archivo de spider generado"""
    file_path = Path("generated_spiders") / f"{spider_name}.py"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Spider no encontrado")
    
    return FileResponse(
        path=str(file_path),
        filename=f"{spider_name}.py",
        media_type="text/x-python"
    )


@app.get("/metrics")
async def get_metrics():
    """
    Obtiene métricas del sistema según KPIs del plan
    
    Retorna métricas de:
    - Tiempo de generación (reducción 97%)
    - Tiempos promedio por estrategia
    - Precisión de spiders
    - Cache hit rate
    - Throughput diario
    """
    try:
        # Importar aquí para evitar import circular
        from .metrics import Metrics
        from .performance_metrics import PerformanceMetrics
        
        # Obtener cliente Redis
        redis_client = await get_redis_client()
        
        # Inicializar sistemas de métricas
        metrics = Metrics(redis_client)
        performance = PerformanceMetrics(redis_client)
        
        # Obtener métricas completas
        system_metrics = await metrics.get_system_metrics()
        performance_trends = await performance.analyze_performance_trends()
        cost_savings = await performance.calculate_cost_savings()
        
        # Combinar todas las métricas
        response = {
            **system_metrics,
            "performance_trends": performance_trends,
            "cost_savings": cost_savings,
            "service": "Spider Factory 2.0",
            "version": "2.0.0"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo métricas: {str(e)}"
        )


@app.get("/metrics/summary")
async def get_metrics_summary():
    """
    Obtiene resumen de métricas en formato texto
    Útil para dashboards simples o alertas
    """
    try:
        from .metrics import Metrics
        
        redis_client = await get_redis_client()
        metrics = Metrics(redis_client)
        
        summary = await metrics.get_metrics_summary()
        
        return PlainTextResponse(summary)
        
    except Exception as e:
        logger.error(f"Error obteniendo resumen de métricas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo resumen: {str(e)}"
        )


@app.get("/metrics/performance")
async def get_performance_report():
    """
    Obtiene reporte detallado de rendimiento
    Incluye análisis de tendencias y cuellos de botella
    """
    try:
        from .performance_metrics import PerformanceMetrics
        
        redis_client = await get_redis_client()
        performance = PerformanceMetrics(redis_client)
        
        report = await performance.get_performance_report()
        
        return PlainTextResponse(report)
        
    except Exception as e:
        logger.error(f"Error generando reporte de rendimiento: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generando reporte: {str(e)}"
        )


# Manejo de errores global
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Manejador personalizado de excepciones HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP {exc.status_code}",
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Manejador general de excepciones"""
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "Ha ocurrido un error inesperado",
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )