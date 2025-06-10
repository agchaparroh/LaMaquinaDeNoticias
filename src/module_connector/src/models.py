"""
Data models for Module Connector

Contains Pydantic models for validating article data
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ArticuloInItem(BaseModel):
    """
    Pydantic model for article data validation.
    Maps to the ArticuloInItem structure from module_scraper.
    """
    # Campos principales
    url: Optional[str] = None                    # URL original del artículo
    storage_path: Optional[str] = None           # Ruta en Supabase Storage
    fuente: Optional[str] = None                 # Nombre/identificador del spider que lo extrajo
    medio: str                                   # Nombre del medio (ej: "El País")
    medio_url_principal: Optional[str] = None    # URL principal del medio (ej: https://elpais.com)
    pais_publicacion: str                        # País de publicación (ej: "España")
    tipo_medio: str                              # Tipo: diario, agencia, televisión, etc.
    titular: str                                 # Título del artículo
    fecha_publicacion: datetime                  # Fecha de publicación
    autor: Optional[str] = None                  # Autor(es) del artículo
    idioma: Optional[str] = None                 # Idioma del artículo
    seccion: Optional[str] = None                # Sección del medio
    etiquetas_fuente: Optional[List[str]] = None # Etiquetas del medio original
    es_opinion: Optional[bool] = False           # Boolean: ¿Es artículo de opinión?
    es_oficial: Optional[bool] = False           # Boolean: ¿Es fuente oficial?
    
    # Campos generados por el pipeline
    resumen: Optional[str] = None                # Resumen generado en Fase 2
    categorias_asignadas: Optional[List[str]] = None   # Categorías asignadas en Fase 2
    puntuacion_relevancia: Optional[float] = None     # Puntuación 0-10 asignada en Fase 2
    
    # Campos de control
    fecha_recopilacion: Optional[datetime] = None     # Timestamp de scraping
    fecha_procesamiento: Optional[datetime] = None    # Timestamp de fin de Fase 5
    estado_procesamiento: Optional[str] = "pendiente_connector"  # Estado: pendiente, procesando, etc.
    error_detalle: Optional[str] = None               # Detalle del error si lo hay
    
    # Contenido extraído
    contenido_texto: str                         # Texto completo del artículo
    contenido_html: Optional[str] = None         # HTML original del artículo
    
    # Metadatos adicionales
    metadata: Optional[Dict[str, Any]] = None    # JSONB para datos adicionales

    @validator('fecha_publicacion', pre=True)
    def parse_fecha_publicacion(cls, v):
        """Parse fecha_publicacion from string if needed"""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                # Try alternative formats
                from dateutil.parser import parse
                return parse(v)
        return v

    @validator('fecha_recopilacion', pre=True)
    def parse_fecha_recopilacion(cls, v):
        """Parse fecha_recopilacion from string if needed"""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                from dateutil.parser import parse
                return parse(v)
        return v

    def validate_required_fields(self) -> bool:
        """Validate that the required fields are present"""
        required_fields = ['titular', 'medio', 'pais_publicacion', 'tipo_medio', 
                          'fecha_publicacion', 'contenido_texto']
        for field in required_fields:
            if not getattr(self, field):
                return False
        return True

    class Config:
        # Allow extra fields to maintain compatibility
        extra = "allow"
        
        # Example schema
        schema_extra = {
            "example": {
                "url": "https://www.ejemplo.com/noticia/123",
                "storage_path": "/articulos/2023/10/noticia_123.json.gz",
                "fuente": "spider_ejemplo_news",
                "medio": "Diario Ejemplo",
                "medio_url_principal": "https://www.ejemplo.com",
                "pais_publicacion": "País Ficticio",
                "tipo_medio": "Diario Digital",
                "titular": "Titular de Ejemplo para la Noticia",
                "fecha_publicacion": "2023-10-26T10:00:00Z",
                "autor": "Autor de Ejemplo",
                "idioma": "es",
                "seccion": "Actualidad",
                "etiquetas_fuente": ["ejemplo", "noticias", "ficticio"],
                "es_opinion": False,
                "es_oficial": False,
                "resumen": "Este es un resumen generado automáticamente del artículo de ejemplo.",
                "categorias_asignadas": ["tecnología", "innovación"],
                "puntuacion_relevancia": 8.5,
                "fecha_recopilacion": "2023-10-26T10:05:00Z",
                "fecha_procesamiento": None,
                "estado_procesamiento": "pendiente_connector",
                "error_detalle": None,
                "contenido_texto": "Este es el contenido completo en texto plano del artículo de ejemplo...",
                "contenido_html": "<html><body><h1>Titular de Ejemplo</h1><p>Este es el contenido HTML original...</p></body></html>",
                "metadata": {
                    "palabras_clave_seo": ["ejemplo", "noticia", "desarrollo"],
                    "fuente_original_id": "ext-789xyz"
                }
            }
        }


def prepare_articulo(articulo_data: dict) -> ArticuloInItem:
    """
    Prepare article data by adding default values for missing fields
    
    Args:
        articulo_data: Dictionary containing article data
        
    Returns:
        ArticuloInItem: Validated article instance
        
    Raises:
        ValueError: If validation fails
    """
    # Create a copy to avoid modifying original data
    data = articulo_data.copy()
    
    # If ID is not present, generate a unique one based on URL or timestamp
    if 'id' not in data or not data['id']:
        if data.get('url'):
            data['id'] = f"art_{hash(data['url']) % 1000000:06d}"
        else:
            data['id'] = f"art_{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(data) % 1000:03d}"
    
    # If fecha_recopilacion is not present, add current time
    if 'fecha_recopilacion' not in data or not data['fecha_recopilacion']:
        data['fecha_recopilacion'] = datetime.now()
        
    # Ensure estado_procesamiento is set
    if 'estado_procesamiento' not in data or not data['estado_procesamiento']:
        data['estado_procesamiento'] = "pendiente_connector"
        
    return ArticuloInItem(**data)
