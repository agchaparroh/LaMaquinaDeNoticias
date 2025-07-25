"""
Procesador batch para Spider Factory 2.0

Maneja el procesamiento masivo de sitios web para análisis y generación de spiders.
"""

import asyncio  # noqa: F401
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Literal, Optional

import pandas as pd
from pydantic import BaseModel, HttpUrl, field_validator

from .analyzer import AnalysisResult, SiteAnalysisRequest, SmartAnalyzer  # noqa: F401
from .generator import SpiderGenerator
from .websocket_manager import ConnectionManager

# Configurar logging
logger = logging.getLogger(__name__)


class BatchSite(BaseModel):
    """Sitio individual en un batch según plan original"""

    medio: str
    seccion: str
    url: HttpUrl
    area_geografica: str
    tipo_medio: Literal["diario", "revista", "agencia"]
    frecuencia_minutos: Optional[int] = 60
    rss_url: Optional[HttpUrl] = None
    comentarios: Optional[str] = None

    @field_validator("area_geografica")
    @classmethod
    def validate_area_geografica(cls, v: str) -> str:
        """Valida que el área geográfica sea válida"""
        from .config import AREAS_GEOGRAFICAS_VALIDAS

        if v not in AREAS_GEOGRAFICAS_VALIDAS:
            raise ValueError(
                f"Área geográfica inválida: {v}. Debe ser una de: {', '.join(AREAS_GEOGRAFICAS_VALIDAS)}"
            )
        return v


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

    def __init__(
        self,
        analyzer: SmartAnalyzer,
        generator: SpiderGenerator,
        connection_manager: ConnectionManager,
    ):
        self.analyzer = analyzer
        self.generator = generator
        self.connection_manager = connection_manager
        self.active_batches: Dict[str, BatchStatus] = {}

    async def process_csv_file(
        self, file_content: str, session_id: str
    ) -> BatchResponse:
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

            # Validar columnas requeridas según el plan
            required_columns = [
                "medio",
                "seccion",
                "url",
                "area_geografica",
                "tipo_medio",
            ]
            if not all(col in df.columns for col in required_columns):
                raise ValueError(
                    f"El CSV debe contener las columnas: {required_columns}"
                )

            # Validar tipo_medio válidos
            valid_tipos = ["diario", "revista", "agencia"]
            invalid_tipos = df[~df["tipo_medio"].isin(valid_tipos)][
                "tipo_medio"
            ].unique()
            if len(invalid_tipos) > 0:
                raise ValueError(
                    f"Tipos de medio inválidos: {invalid_tipos}. Deben ser: {valid_tipos}"
                )

            # Convertir a lista de BatchSite
            sites = []
            for _, row in df.iterrows():
                # Procesar frecuencia_minutos como entero opcional
                frecuencia = None
                if "frecuencia_minutos" in row and pd.notna(row["frecuencia_minutos"]):
                    try:
                        frecuencia = int(row["frecuencia_minutos"])
                    except (ValueError, TypeError):
                        frecuencia = 60

                # Procesar rss_url como URL válida o None
                rss_url = None
                if (
                    "rss_url" in row
                    and pd.notna(row["rss_url"])
                    and row["rss_url"].strip()
                ):
                    rss_url = row["rss_url"].strip()

                site = BatchSite(
                    medio=row["medio"],
                    seccion=row["seccion"],
                    url=row["url"],
                    area_geografica=row["area_geografica"],
                    tipo_medio=row["tipo_medio"],
                    frecuencia_minutos=frecuencia or 60,
                    rss_url=rss_url,
                    comentarios=row.get("comentarios")
                    if pd.notna(row.get("comentarios"))
                    else None,
                )
                sites.append(site)

            # Crear request batch
            batch_request = BatchRequest(sites=sites, session_id=session_id)

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
        status = BatchStatus(batch_id=batch_id, total=len(request.sites))
        self.active_batches[batch_id] = status

        # Notificar inicio
        await self._send_update(
            request.session_id,
            {
                "type": "batch_started",
                "batch_id": batch_id,
                "total_sites": status.total,
            },
        )

        try:
            # Procesar sitios
            async for result in self._process_sites(
                request.sites, request.session_id, batch_id
            ):
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
                duration_seconds=duration,
            )

            # Notificar fin
            await self._send_update(
                request.session_id,
                {
                    "type": "batch_completed",
                    "batch_id": batch_id,
                    "summary": {
                        "total": status.total,
                        "successful": status.successful,
                        "failed": status.failed,
                        "duration_seconds": duration,
                    },
                },
            )

            return response

        except Exception as e:
            logger.error(f"Error en batch {batch_id}: {e}")
            await self._send_update(
                request.session_id,
                {"type": "batch_error", "batch_id": batch_id, "error": str(e)},
            )
            raise
        finally:
            # Limpiar estado
            self.active_batches.pop(batch_id, None)

    async def _process_sites(
        self, sites: List[BatchSite], session_id: str, batch_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
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
                await self._send_update(
                    session_id,
                    {
                        "type": "site_processing",
                        "batch_id": batch_id,
                        "site_index": i + 1,
                        "site_name": f"{site.medio} - {site.seccion}",
                        "site_url": str(site.url),
                        "progress": (i / len(sites)) * 100,
                    },
                )

                # Analizar sitio con todos los campos obligatorios
                analysis_request = SiteAnalysisRequest(
                    url=site.url,
                    medio=site.medio,
                    seccion=site.seccion,
                    area_geografica=site.area_geografica,
                    tipo_medio=site.tipo_medio,
                    frecuencia_minutos=site.frecuencia_minutos or 60,
                    comentarios=site.comentarios,
                    rss_url=site.rss_url,
                    check_rss=True,
                )

                analysis_result = await self.analyzer.analyze(analysis_request)

                # Generar spider usando interfaz correcta del generator
                spider_code = self.generator.generate_spider(
                    analysis=analysis_result,
                    medio=site.medio,
                    seccion=site.seccion,
                    area_geografica=site.area_geografica,
                    tipo_medio=site.tipo_medio,
                    frecuencia_minutos=site.frecuencia_minutos or 60,
                    additional_config={
                        "rss_url": str(site.rss_url) if site.rss_url else None,
                        "comentarios": site.comentarios,
                    },
                )

                # Validar código
                is_valid = self.generator.validate_spider(spider_code)

                # Crear resultado
                result = {
                    "medio": site.medio,
                    "seccion": site.seccion,
                    "url": str(site.url),
                    "area_geografica": site.area_geografica,
                    "tipo_medio": site.tipo_medio,
                    "success": True,
                    "analysis": {
                        "strategy": analysis_result.strategy.value,
                        "confidence": analysis_result.confidence,
                        "has_rss": bool(analysis_result.rss_url),
                        "needs_javascript": analysis_result.needs_javascript,
                        "from_cache": analysis_result.from_cache,
                    },
                    "spider": {
                        "name": spider_name,  # noqa: F821
                        "valid": is_valid,
                        "code_length": len(spider_code),
                    },
                }

                # Guardar spider si es válido
                if is_valid:
                    output_dir = Path("generated_spiders") / batch_id
                    output_dir.mkdir(parents=True, exist_ok=True)

                    spider_file = output_dir / f"{spider_name}.py"  # noqa: F821
                    spider_file.write_text(spider_code, encoding="utf-8")
                    result["spider"]["file_path"] = str(spider_file)

                # Notificar éxito
                await self._send_update(
                    session_id,
                    {
                        "type": "site_completed",
                        "batch_id": batch_id,
                        "site_name": f"{site.medio} - {site.seccion}",
                        "success": True,
                        "confidence": analysis_result.confidence,
                    },
                )

                yield result

            except Exception as e:
                logger.error(f"Error procesando {site.name}: {e}")

                # Notificar error
                await self._send_update(
                    session_id,
                    {
                        "type": "site_error",
                        "batch_id": batch_id,
                        "site_name": f"{site.medio} - {site.seccion}",
                        "error": str(e),
                    },
                )

                yield {
                    "medio": site.medio,
                    "seccion": site.seccion,
                    "url": str(site.url),
                    "area_geografica": site.area_geografica,
                    "tipo_medio": site.tipo_medio,
                    "success": False,
                    "error": str(e),
                }

    async def _send_update(self, session_id: str, data: Dict[str, Any]):
        """Envía actualización vía WebSocket"""
        try:
            await self.connection_manager.send_to_session(
                session_id, {"timestamp": datetime.now().isoformat(), **data}
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
            "progress": (status.processed / status.total * 100)
            if status.total > 0
            else 0,
            "elapsed_seconds": (datetime.now() - status.start_time).total_seconds(),
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
                    "medio": result["medio"],
                    "seccion": result["seccion"],
                    "url": result["url"],
                    "area_geografica": result["area_geografica"],
                    "tipo_medio": result["tipo_medio"],
                    "success": result["success"],
                    "error": result.get("error", ""),
                }

                if result["success"]:
                    row.update(
                        {
                            "strategy": result["analysis"]["strategy"],
                            "confidence": result["analysis"]["confidence"],
                            "has_rss": result["analysis"]["has_rss"],
                            "needs_javascript": result["analysis"]["needs_javascript"],
                            "spider_name": result["spider"]["name"],
                            "spider_valid": result["spider"]["valid"],
                        }
                    )

                rows.append(row)

            df = pd.DataFrame(rows)
            return df.to_csv(index=False)

        else:  # json
            return json.dumps(response.dict(), indent=2, default=str)
