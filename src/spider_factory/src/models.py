"""
Modelos Pydantic para validación de requests/responses de la API
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator

from .analyzer import AnalysisConfidence, AnalysisStrategy  # noqa: F401
from .config import AREAS_GEOGRAFICAS_VALIDAS


class SpiderStatus(str, Enum):
    """Estados posibles de un spider"""

    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class DuplicateCheckRequest(BaseModel):
    """Request para verificar si un medio ya existe"""

    medio: str = Field(..., description="Nombre del medio")
    seccion: str = Field(..., description="Sección específica")

    @field_validator("medio", "seccion")
    @classmethod
    def clean_names(cls, v: str) -> str:
        """Limpia y normaliza nombres para formar spider_name"""
        # Convertir a minúsculas y reemplazar caracteres no válidos
        import re

        v = v.lower().strip()
        v = re.sub(r"[^a-z0-9]+", "_", v)
        v = re.sub(r"_+", "_", v)  # Eliminar guiones bajos múltiples
        v = v.strip("_")  # Eliminar guiones bajos al inicio/final
        return v

    @property
    def spider_name(self) -> str:
        """Genera el nombre del spider como {medio}_{seccion}"""
        return f"{self.medio}_{self.seccion}"


class DuplicateCheckResponse(BaseModel):
    """Response de verificación de duplicados"""

    exists: bool = Field(..., description="Si el medio ya existe")
    spider_name: Optional[str] = Field(None, description="Nombre del spider existente")
    file_path: Optional[str] = Field(None, description="Ruta al archivo del spider")
    similar_spiders: List[str] = Field(
        default_factory=list, description="Lista de spiders similares"
    )
    message: str = Field(..., description="Mensaje descriptivo")


class AnalysisRequest(BaseModel):
    """Request para analizar un sitio web"""

    url: HttpUrl = Field(..., description="URL del sitio a analizar")
    medio: str = Field(..., description="Nombre del medio")
    seccion: str = Field(..., description="Nombre de la sección")
    area_geografica: str = Field(..., description="Área geográfica del medio")
    tipo_medio: Literal["diario", "revista", "agencia"] = Field(
        ..., description="Tipo de medio"
    )
    rss_url: Optional[HttpUrl] = Field(None, description="URL del RSS si es conocida")
    force_analysis: bool = Field(
        False, description="Forzar nuevo análisis ignorando cache"
    )
    check_rss: bool = Field(True, description="Verificar si el sitio tiene RSS")

    @field_validator("area_geografica")
    @classmethod
    def validate_area_geografica(cls, v: str) -> str:
        """Valida que el área geográfica sea válida"""
        if v not in AREAS_GEOGRAFICAS_VALIDAS:
            raise ValueError(
                f"Área geográfica inválida: {v}. Debe ser una de: {', '.join(AREAS_GEOGRAFICAS_VALIDAS)}"
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/news",
                "medio": "Example News",
                "seccion": "politica",
                "area_geografica": "ESPAÑA",
                "tipo_medio": "diario",
                "rss_url": "https://example.com/rss",
                "force_analysis": False,
                "check_rss": True,
            }
        }


class AnalysisResponse(BaseModel):
    """Response del análisis de un sitio"""

    url: str = Field(..., description="URL analizada")
    domain: str = Field(..., description="Dominio del sitio")
    strategy: AnalysisStrategy = Field(..., description="Estrategia recomendada")
    confidence: float = Field(..., description="Nivel de confianza (0-1)")
    needs_javascript: bool = Field(..., description="Si requiere JavaScript")
    rss_url: Optional[str] = Field(None, description="URL del RSS si existe")
    selectors: Optional[Dict[str, str]] = Field(
        None, description="Selectores CSS/XPath detectados"
    )
    sample_articles: List[Dict[str, str]] = Field(
        default_factory=list, description="Artículos de muestra encontrados"
    )
    from_cache: bool = Field(False, description="Si vino de cache")
    pattern_id: Optional[str] = Field(None, description="ID del patrón usado")
    analysis_timestamp: datetime = Field(..., description="Timestamp del análisis")
    notes: Optional[str] = Field(None, description="Notas adicionales")

    class Config:
        use_enum_values = True


class GenerateSpiderRequest(BaseModel):
    """Request para generar un spider"""

    # Datos del análisis o patrón
    analysis_url: Optional[HttpUrl] = Field(
        None, description="URL analizada (requerida si no hay pattern_id)"
    )
    pattern_id: Optional[str] = Field(
        None, description="ID del patrón a usar (alternativa a analysis_url)"
    )

    # Información del medio (OBLIGATORIOS)
    medio: str = Field(..., description="Nombre del medio")
    seccion: str = Field(..., description="Sección del medio")
    area_geografica: str = Field(..., description="Área geográfica del medio")
    tipo_medio: Literal["diario", "revista", "agencia"] = Field(
        ..., description="Tipo de medio"
    )

    # Configuración adicional
    frecuencia_minutos: Optional[int] = Field(
        60, description="Frecuencia de actualización en minutos", ge=1
    )
    comentarios: Optional[str] = Field(
        None, description="Comentarios adicionales sobre el medio o spider"
    )
    excluded_urls: List[str] = Field(
        default_factory=list, description="Patrones de URL a excluir"
    )
    follow_pagination: bool = Field(True, description="Si debe seguir paginación")
    max_pages: int = Field(100, description="Máximo de páginas a seguir", ge=1, le=1000)
    custom_settings: Dict[str, Any] = Field(
        default_factory=dict, description="Configuración personalizada de Scrapy"
    )

    @field_validator("medio", "seccion")
    @classmethod
    def clean_names(cls, v: str) -> str:
        """Limpia y normaliza nombres"""
        import re

        v = v.lower().strip()
        v = re.sub(r"[^a-z0-9]+", "_", v)
        v = re.sub(r"_+", "_", v)
        v = v.strip("_")
        return v

    @field_validator("area_geografica")
    @classmethod
    def validate_area_geografica(cls, v: str) -> str:
        """Valida que el área geográfica sea válida"""
        if v not in AREAS_GEOGRAFICAS_VALIDAS:
            raise ValueError(
                f"Área geográfica inválida: {v}. Debe ser una de: {', '.join(AREAS_GEOGRAFICAS_VALIDAS)}"
            )
        return v

    @property
    def spider_name(self) -> str:
        """Genera automáticamente el nombre del spider como {medio}_{seccion}"""
        return f"{self.medio}_{self.seccion}"

    @property
    def media_name(self) -> str:
        """Mantiene compatibilidad con media_name para el frontend"""
        return self.medio.replace("_", " ").title()

    @field_validator("analysis_url")
    @classmethod
    def validate_source(cls, v: Optional[HttpUrl], info) -> Optional[HttpUrl]:
        """Valida que se proporcione analysis_url o pattern_id"""
        values = info.data
        if not v and not values.get("pattern_id"):
            raise ValueError("Debe proporcionar analysis_url o pattern_id")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "analysis_url": "https://example.com/news",
                "medio": "example",
                "seccion": "news",
                "area_geografica": "ESPAÑA",
                "tipo_medio": "diario",
                "frecuencia_minutos": 60,
                "comentarios": "Principal sección de noticias",
                "excluded_urls": ["*/tags/*", "*/author/*"],
                "follow_pagination": True,
                "max_pages": 50,
            }
        }


class GenerateSpiderResponse(BaseModel):
    """Response de generación de spider"""

    success: bool = Field(..., description="Si la generación fue exitosa")
    spider_name: str = Field(..., description="Nombre del spider generado")
    file_path: str = Field(..., description="Ruta donde se guardó el spider")
    strategy: AnalysisStrategy = Field(..., description="Estrategia utilizada")
    code_preview: str = Field(..., description="Vista previa del código")
    message: str = Field(..., description="Mensaje descriptivo")
    warnings: List[str] = Field(
        default_factory=list, description="Advertencias durante la generación"
    )


class BatchAnalysisRequest(BaseModel):
    """Request para análisis batch desde CSV"""

    csv_content: str = Field(..., description="Contenido del archivo CSV")
    force_analysis: bool = Field(False, description="Forzar nuevo análisis para todos")
    check_rss: bool = Field(True, description="Verificar RSS en todos los sitios")

    class Config:
        json_schema_extra = {
            "example": {
                "csv_content": "medio,seccion,url,area_geografica,tipo_medio,frecuencia_minutos,rss_url\nexample,news,https://example.com/news,ESPAÑA,diario,60,https://example.com/rss\n",
                "force_analysis": False,
                "check_rss": True,
            }
        }


class BatchAnalysisResponse(BaseModel):
    """Response de análisis batch"""

    total_sites: int = Field(..., description="Total de sitios en el CSV")
    analyzed: int = Field(..., description="Sitios analizados exitosamente")
    failed: int = Field(..., description="Sitios que fallaron")
    results: List[Dict[str, Any]] = Field(..., description="Resultados individuales")
    errors: List[Dict[str, str]] = Field(
        default_factory=list, description="Errores encontrados"
    )


class BatchGenerateRequest(BaseModel):
    """Request para generación batch de spiders"""

    sites: List[Dict[str, Any]] = Field(
        ..., description="Lista de sitios con sus configuraciones"
    )
    output_format: Literal["individual", "module"] = Field(
        "individual", description="Formato de salida de los spiders"
    )
    base_settings: Dict[str, Any] = Field(
        default_factory=dict, description="Configuración base para todos los spiders"
    )


class BatchGenerateResponse(BaseModel):
    """Response de generación batch"""

    total_requested: int = Field(..., description="Total de spiders solicitados")
    generated: int = Field(..., description="Spiders generados exitosamente")
    failed: int = Field(..., description="Spiders que fallaron")
    results: List[GenerateSpiderResponse] = Field(
        ..., description="Resultados individuales"
    )
    output_directory: Optional[str] = Field(
        None, description="Directorio donde se guardaron los spiders"
    )


class PatternSearchRequest(BaseModel):
    """Request para buscar patrones"""

    domain: Optional[str] = Field(None, description="Filtrar por dominio")
    status: Optional[str] = Field(None, description="Filtrar por estado")
    min_confidence: Optional[float] = Field(
        None, description="Confianza mínima", ge=0.0, le=1.0
    )
    strategy: Optional[AnalysisStrategy] = Field(
        None, description="Filtrar por estrategia"
    )
    limit: int = Field(50, description="Límite de resultados", ge=1, le=200)


class PatternSearchResponse(BaseModel):
    """Response de búsqueda de patrones"""

    total: int = Field(..., description="Total de patrones encontrados")
    patterns: List[Dict[str, Any]] = Field(..., description="Lista de patrones")


class HealthCheckResponse(BaseModel):
    """Response del health check"""

    status: Literal["healthy", "unhealthy"] = Field(
        ..., description="Estado del sistema"
    )
    version: str = Field(..., description="Versión de Spider Factory")
    redis_connected: bool = Field(..., description="Estado de conexión Redis")
    firecrawl_available: bool = Field(..., description="Disponibilidad de Firecrawl")
    patterns_count: int = Field(..., description="Número de patrones almacenados")
    uptime_seconds: float = Field(..., description="Tiempo activo en segundos")
    timestamp: datetime = Field(..., description="Timestamp de la verificación")


class ErrorResponse(BaseModel):
    """Response estándar para errores"""

    error: str = Field(..., description="Tipo de error")
    message: str = Field(..., description="Mensaje descriptivo del error")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Detalles adicionales del error"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp del error"
    )


class WebSocketMessage(BaseModel):
    """Mensaje para comunicación WebSocket"""

    type: Literal["progress", "result", "error", "ping"] = Field(
        ..., description="Tipo de mensaje"
    )
    data: Dict[str, Any] = Field(..., description="Datos del mensaje")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp del mensaje"
    )


class TaskStatus(BaseModel):
    """Estado de una tarea asíncrona"""

    task_id: str = Field(..., description="ID único de la tarea")
    status: SpiderStatus = Field(..., description="Estado actual")
    progress: float = Field(0.0, description="Progreso (0-100)", ge=0.0, le=100.0)
    current_step: Optional[str] = Field(None, description="Paso actual en proceso")
    result: Optional[Dict[str, Any]] = Field(
        None, description="Resultado si está completo"
    )
    error: Optional[str] = Field(None, description="Error si falló")
    created_at: datetime = Field(..., description="Timestamp de creación")
    updated_at: datetime = Field(..., description="Última actualización")
