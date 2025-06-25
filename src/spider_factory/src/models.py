"""
Modelos Pydantic para validación de requests/responses de la API
"""
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator
from enum import Enum

from .analyzer import AnalysisStrategy, AnalysisConfidence


class SpiderStatus(str, Enum):
    """Estados posibles de un spider"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class DuplicateCheckRequest(BaseModel):
    """Request para verificar si un medio ya existe"""
    domain: str = Field(..., description="Dominio del medio a verificar")
    name: Optional[str] = Field(None, description="Nombre del medio")
    
    @validator('domain')
    def clean_domain(cls, v):
        """Limpia y normaliza el dominio"""
        # Remover protocolo si existe
        v = v.replace('https://', '').replace('http://', '')
        # Remover www si existe
        v = v.replace('www.', '')
        # Remover trailing slash
        v = v.rstrip('/')
        return v.lower()


class DuplicateCheckResponse(BaseModel):
    """Response de verificación de duplicados"""
    exists: bool = Field(..., description="Si el medio ya existe")
    spider_name: Optional[str] = Field(None, description="Nombre del spider existente")
    file_path: Optional[str] = Field(None, description="Ruta al archivo del spider")
    similar_spiders: List[str] = Field(
        default_factory=list, 
        description="Lista de spiders similares"
    )
    message: str = Field(..., description="Mensaje descriptivo")


class AnalysisRequest(BaseModel):
    """Request para analizar un sitio web"""
    url: HttpUrl = Field(..., description="URL del sitio a analizar")
    section_name: Optional[str] = Field(
        None, 
        description="Nombre de la sección específica"
    )
    force_analysis: bool = Field(
        False, 
        description="Forzar nuevo análisis ignorando cache"
    )
    check_rss: bool = Field(
        True, 
        description="Verificar si el sitio tiene RSS"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com/news",
                "section_name": "politica",
                "force_analysis": False,
                "check_rss": True
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
        None, 
        description="Selectores CSS/XPath detectados"
    )
    sample_articles: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Artículos de muestra encontrados"
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
        None, 
        description="URL analizada (requerida si no hay pattern_id)"
    )
    pattern_id: Optional[str] = Field(
        None, 
        description="ID del patrón a usar (alternativa a analysis_url)"
    )
    
    # Información del spider
    spider_name: str = Field(
        ..., 
        description="Nombre del spider (snake_case)",
        regex="^[a-z][a-z0-9_]*$"
    )
    media_name: str = Field(
        ..., 
        description="Nombre del medio para display"
    )
    
    # Configuración adicional
    area_geografica: Optional[str] = Field(
        None, 
        description="Área geográfica del medio"
    )
    excluded_urls: List[str] = Field(
        default_factory=list,
        description="Patrones de URL a excluir"
    )
    follow_pagination: bool = Field(
        True, 
        description="Si debe seguir paginación"
    )
    max_pages: int = Field(
        100, 
        description="Máximo de páginas a seguir",
        ge=1,
        le=1000
    )
    custom_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuración personalizada de Scrapy"
    )
    
    @validator('analysis_url', 'pattern_id')
    def validate_source(cls, v, values):
        """Valida que se proporcione analysis_url o pattern_id"""
        if not v and not values.get('pattern_id') and not values.get('analysis_url'):
            raise ValueError("Debe proporcionar analysis_url o pattern_id")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "analysis_url": "https://example.com/news",
                "spider_name": "example_news",
                "media_name": "Example News",
                "area_geografica": "ESPAÑA",
                "excluded_urls": ["*/tags/*", "*/author/*"],
                "follow_pagination": True,
                "max_pages": 50
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
        default_factory=list,
        description="Advertencias durante la generación"
    )


class BatchAnalysisRequest(BaseModel):
    """Request para análisis batch desde CSV"""
    csv_content: str = Field(..., description="Contenido del archivo CSV")
    force_analysis: bool = Field(
        False, 
        description="Forzar nuevo análisis para todos"
    )
    check_rss: bool = Field(
        True, 
        description="Verificar RSS en todos los sitios"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "csv_content": "url,nombre,area\nhttps://example.com,Example News,Nacional\n",
                "force_analysis": False,
                "check_rss": True
            }
        }


class BatchAnalysisResponse(BaseModel):
    """Response de análisis batch"""
    total_sites: int = Field(..., description="Total de sitios en el CSV")
    analyzed: int = Field(..., description="Sitios analizados exitosamente")
    failed: int = Field(..., description="Sitios que fallaron")
    results: List[Dict[str, Any]] = Field(
        ..., 
        description="Resultados individuales"
    )
    errors: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Errores encontrados"
    )


class BatchGenerateRequest(BaseModel):
    """Request para generación batch de spiders"""
    sites: List[Dict[str, Any]] = Field(
        ..., 
        description="Lista de sitios con sus configuraciones"
    )
    output_format: Literal["individual", "module"] = Field(
        "individual",
        description="Formato de salida de los spiders"
    )
    base_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuración base para todos los spiders"
    )


class BatchGenerateResponse(BaseModel):
    """Response de generación batch"""
    total_requested: int = Field(..., description="Total de spiders solicitados")
    generated: int = Field(..., description="Spiders generados exitosamente")
    failed: int = Field(..., description="Spiders que fallaron")
    results: List[GenerateSpiderResponse] = Field(
        ..., 
        description="Resultados individuales"
    )
    output_directory: Optional[str] = Field(
        None,
        description="Directorio donde se guardaron los spiders"
    )


class PatternSearchRequest(BaseModel):
    """Request para buscar patrones"""
    domain: Optional[str] = Field(None, description="Filtrar por dominio")
    status: Optional[str] = Field(None, description="Filtrar por estado")
    min_confidence: Optional[float] = Field(
        None, 
        description="Confianza mínima",
        ge=0.0,
        le=1.0
    )
    strategy: Optional[AnalysisStrategy] = Field(
        None, 
        description="Filtrar por estrategia"
    )
    limit: int = Field(50, description="Límite de resultados", ge=1, le=200)


class PatternSearchResponse(BaseModel):
    """Response de búsqueda de patrones"""
    total: int = Field(..., description="Total de patrones encontrados")
    patterns: List[Dict[str, Any]] = Field(
        ..., 
        description="Lista de patrones"
    )


class HealthCheckResponse(BaseModel):
    """Response del health check"""
    status: Literal["healthy", "unhealthy"] = Field(
        ..., 
        description="Estado del sistema"
    )
    version: str = Field(..., description="Versión de Spider Factory")
    redis_connected: bool = Field(..., description="Estado de conexión Redis")
    firecrawl_available: bool = Field(
        ..., 
        description="Disponibilidad de Firecrawl"
    )
    patterns_count: int = Field(..., description="Número de patrones almacenados")
    uptime_seconds: float = Field(..., description="Tiempo activo en segundos")
    timestamp: datetime = Field(..., description="Timestamp de la verificación")


class ErrorResponse(BaseModel):
    """Response estándar para errores"""
    error: str = Field(..., description="Tipo de error")
    message: str = Field(..., description="Mensaje descriptivo del error")
    details: Optional[Dict[str, Any]] = Field(
        None, 
        description="Detalles adicionales del error"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp del error"
    )


class WebSocketMessage(BaseModel):
    """Mensaje para comunicación WebSocket"""
    type: Literal["progress", "result", "error", "ping"] = Field(
        ..., 
        description="Tipo de mensaje"
    )
    data: Dict[str, Any] = Field(..., description="Datos del mensaje")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp del mensaje"
    )


class TaskStatus(BaseModel):
    """Estado de una tarea asíncrona"""
    task_id: str = Field(..., description="ID único de la tarea")
    status: SpiderStatus = Field(..., description="Estado actual")
    progress: float = Field(
        0.0, 
        description="Progreso (0-100)",
        ge=0.0,
        le=100.0
    )
    current_step: Optional[str] = Field(
        None, 
        description="Paso actual en proceso"
    )
    result: Optional[Dict[str, Any]] = Field(
        None, 
        description="Resultado si está completo"
    )
    error: Optional[str] = Field(
        None, 
        description="Error si falló"
    )
    created_at: datetime = Field(..., description="Timestamp de creación")
    updated_at: datetime = Field(..., description="Última actualización")