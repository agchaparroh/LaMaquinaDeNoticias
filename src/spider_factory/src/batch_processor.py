"""
Procesador batch para Spider Factory 2.0

Maneja el procesamiento masivo de sitios web para análisis y generación de spiders.
"""
import asyncio
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
from pathlib import Path
import pandas as pd
from io import StringIO

from .analyzer import SmartAnalyzer, SiteAnalysisRequest, AnalysisResult
from .generator import SpiderGenerator
from .websocket_manager import ConnectionManager
from pydantic import BaseModel, HttpUrl

# Configurar logging
logger = logging.getLogger(__name__)


class BatchSite(BaseModel):
    """Sitio individual en un batch"""
    url: HttpUrl
    name: str
    category: Optional[str] = None
    metadata: Dict[str, Any] = {}


class BatchRequest(BaseModel):
    """Request para procesamiento batch"""
    sites: List[BatchSite]
    session_id: str
    options: Dict[str, Any] = {}


class BatchResponse(BaseModel):
    """Response del procesamiento batch"""
    batch_id: str
    total_sites: int
    processed: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None


@dataclass
class BatchStatus:
    """Estado del procesamiento batch"""
    batch_id: str
    total: int
    processed: int = 0
    successful: int = 0
    failed: int = 0
    current_site: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    results: List[Dict[str, Any]] = field(default_factory=list)


class BatchProcessor:
    """Procesador para análisis y generación masiva de spiders"""
    
    def __init__(self, analyzer: SmartAnalyzer, generator: SpiderGenerator, 
                 connection_manager: ConnectionManager):
        self.analyzer = analyzer
        self.generator = generator
        self.connection_manager = connection_manager
        self.active_batches: Dict[str, BatchStatus] = {}
        
    async def process_csv_file(self, file_content: str, session_id: str) -> BatchResponse:
        """
        Procesa un archivo CSV con sitios web
        
        Args:
            file_content: Contenido del archivo CSV
            session_id: ID de sesión para WebSocket
            
        Returns:
            BatchResponse con resultados
        """
        try:
            # Parsear CSV
            df = pd.read_csv(StringIO(file_content))
            
            # Validar columnas requeridas
            required_columns = ['url', 'name']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"El CSV debe contener las columnas: {required_columns}")
            
            # Convertir a lista de BatchSite
            sites = []
            for _, row in df.iterrows():
                site = BatchSite(
                    url=row['url'],
                    name=row['name'],
                    category=row.get('category'),
                    metadata={k: v for k, v in row.items() 
                             if k not in ['url', 'name', 'category'] and pd.notna(v)}
                )
                sites.append(site)
            
            # Crear request batch
            batch_request = BatchRequest(
                sites=sites,
                session_id=session_id
            )
            
            # Procesar batch
            return await self.process_batch(batch_request)
            
        except Exception as e:
            logger.error(f"Error procesando CSV: {e}")
            raise
    
    async def process_batch(self, request: BatchRequest) -> BatchResponse:
        """
        Procesa un batch de sitios
        
        Args:
            request: Request con sitios a procesar
            
        Returns:
            BatchResponse con resultados
        """
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Inicializar estado
        status = BatchStatus(
            batch_id=batch_id,
            total=len(request.sites)
        )
        self.active_batches[batch_id] = status
        
        # Notificar inicio
        await self._send_update(request.session_id, {
            "type": "batch_started",
            "batch_id": batch_id,
            "total_sites": status.total
        })
        
        try:
            # Procesar sitios
            async for result in self._process_sites(request.sites, request.session_id, batch_id):
                status.results.append(result)
                status.processed += 1
                
                if result.get("success"):
                    status.successful += 1
                else:
                    status.failed += 1
            
            # Calcular duración
            end_time = datetime.now()
            duration = (end_time - status.start_time).total_seconds()
            
            # Crear response
            response = BatchResponse(
                batch_id=batch_id,
                total_sites=status.total,
                processed=status.processed,
                successful=status.successful,
                failed=status.failed,
                results=status.results,
                start_time=status.start_time,
                end_time=end_time,
                duration_seconds=duration
            )
            
            # Notificar fin
            await self._send_update(request.session_id, {
                "type": "batch_completed",
                "batch_id": batch_id,
                "summary": {
                    "total": status.total,
                    "successful": status.successful,
                    "failed": status.failed,
                    "duration_seconds": duration
                }
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error en batch {batch_id}: {e}")
            await self._send_update(request.session_id, {
                "type": "batch_error",
                "batch_id": batch_id,
                "error": str(e)
            })
            raise
        finally:
            # Limpiar estado
            self.active_batches.pop(batch_id, None)
    
    async def _process_sites(self, sites: List[BatchSite], session_id: str, 
                           batch_id: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Procesa sitios de forma asíncrona
        
        Args:
            sites: Lista de sitios a procesar
            session_id: ID de sesión para actualizaciones
            batch_id: ID del batch
            
        Yields:
            Resultados de cada sitio procesado
        """
        for i, site in enumerate(sites):
            try:
                # Actualizar estado actual
                await self._send_update(session_id, {
                    "type": "site_processing",
                    "batch_id": batch_id,
                    "site_index": i + 1,
                    "site_name": site.name,
                    "site_url": str(site.url),
                    "progress": (i / len(sites)) * 100
                })
                
                # Analizar sitio
                analysis_request = SiteAnalysisRequest(
                    url=str(site.url),
                    check_rss=True
                )
                
                analysis_result = await self.analyzer.analyze(analysis_request)
                
                # Generar spider
                spider_name = site.name.lower().replace(" ", "_").replace("-", "_")
                spider_code = self.generator.generate_spider(
                    analysis_result,
                    spider_name,
                    site.name,
                    {
                        "category": site.category,
                        **site.metadata
                    }
                )
                
                # Validar código
                is_valid = self.generator.validate_spider(spider_code)
                
                # Crear resultado
                result = {
                    "site": site.name,
                    "url": str(site.url),
                    "success": True,
                    "analysis": {
                        "strategy": analysis_result.strategy.value,
                        "confidence": analysis_result.confidence,
                        "has_rss": bool(analysis_result.rss_url),
                        "needs_javascript": analysis_result.needs_javascript,
                        "from_cache": analysis_result.from_cache
                    },
                    "spider": {
                        "name": spider_name,
                        "valid": is_valid,
                        "code_length": len(spider_code)
                    }
                }
                
                # Guardar spider si es válido
                if is_valid:
                    output_dir = Path("generated_spiders") / batch_id
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    spider_file = output_dir / f"{spider_name}.py"
                    spider_file.write_text(spider_code, encoding="utf-8")
                    result["spider"]["file_path"] = str(spider_file)
                
                # Notificar éxito
                await self._send_update(session_id, {
                    "type": "site_completed",
                    "batch_id": batch_id,
                    "site_name": site.name,
                    "success": True,
                    "confidence": analysis_result.confidence
                })
                
                yield result
                
            except Exception as e:
                logger.error(f"Error procesando {site.name}: {e}")
                
                # Notificar error
                await self._send_update(session_id, {
                    "type": "site_error",
                    "batch_id": batch_id,
                    "site_name": site.name,
                    "error": str(e)
                })
                
                yield {
                    "site": site.name,
                    "url": str(site.url),
                    "success": False,
                    "error": str(e)
                }
    
    async def _send_update(self, session_id: str, data: Dict[str, Any]):
        """Envía actualización vía WebSocket"""
        try:
            await self.connection_manager.send_to_session(
                session_id,
                {
                    "timestamp": datetime.now().isoformat(),
                    **data
                }
            )
        except Exception as e:
            logger.warning(f"No se pudo enviar actualización WebSocket: {e}")
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado de un batch activo"""
        status = self.active_batches.get(batch_id)
        if not status:
            return None
        
        return {
            "batch_id": batch_id,
            "total": status.total,
            "processed": status.processed,
            "successful": status.successful,
            "failed": status.failed,
            "current_site": status.current_site,
            "progress": (status.processed / status.total * 100) if status.total > 0 else 0,
            "elapsed_seconds": (datetime.now() - status.start_time).total_seconds()
        }
    
    def export_results(self, response: BatchResponse, format: str = "json") -> str:
        """
        Exporta resultados en diferentes formatos
        
        Args:
            response: Response del batch
            format: Formato de exportación (json, csv)
            
        Returns:
            String con los datos exportados
        """
        if format == "csv":
            # Convertir a DataFrame
            rows = []
            for result in response.results:
                row = {
                    "site": result["site"],
                    "url": result["url"],
                    "success": result["success"],
                    "error": result.get("error", "")
                }
                
                if result["success"]:
                    row.update({
                        "strategy": result["analysis"]["strategy"],
                        "confidence": result["analysis"]["confidence"],
                        "has_rss": result["analysis"]["has_rss"],
                        "needs_javascript": result["analysis"]["needs_javascript"],
                        "spider_name": result["spider"]["name"],
                        "spider_valid": result["spider"]["valid"]
                    })
                
                rows.append(row)
            
            df = pd.DataFrame(rows)
            return df.to_csv(index=False)
        
        else:  # json
            return json.dumps(response.dict(), indent=2, default=str)