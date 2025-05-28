"""
Scrapy Items for the news scraper module
"""
import scrapy
from scrapy import Field
from datetime import datetime
from typing import Optional, List


class ArticuloInItem(scrapy.Item):
    """
    Item for storing extracted article data.
    Maps to the 'articulos' table in Supabase.
    """
    # Primary identification
    url = Field()  # Required: URL única del artículo
    
    # Core content
    titular = Field()  # Required: Título del artículo
    contenido_html = Field()  # HTML completo del artículo
    contenido_texto = Field()  # Texto plano extraído
    
    # Publication metadata
    medio = Field()  # Required: Nombre del medio
    pais_publicacion = Field()  # País de publicación
    tipo_medio = Field()  # Tipo de medio (e.g., 'periodico', 'revista')
    fecha_publicacion = Field()  # Fecha de publicación
    
    # Article metadata
    autor = Field()  # Autor del artículo
    idioma = Field()  # Idioma del artículo (ISO 639-1)
    seccion = Field()  # Sección del medio
    etiquetas_fuente = Field()  # Tags del propio medio
    
    # Classification flags
    es_opinion = Field()  # Boolean: es artículo de opinión
    es_oficial = Field()  # Boolean: es fuente oficial
    
    # Processing metadata
    fecha_captura = Field()  # Auto-generated: cuándo se capturó
    storage_path = Field()  # Path en Supabase Storage
    error_detalle = Field()  # Detalles si hubo error en procesamiento
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values
        if 'fecha_captura' not in self:
            self['fecha_captura'] = datetime.now()
        if 'es_opinion' not in self:
            self['es_opinion'] = False
        if 'es_oficial' not in self:
            self['es_oficial'] = False
        if 'etiquetas_fuente' not in self:
            self['etiquetas_fuente'] = []


class ArticuloAdapter(dict):
    """
    Adapter to convert ArticuloInItem to dict format for Supabase
    """
    def __init__(self, item: ArticuloInItem):
        super().__init__()
        
        # Map all fields
        self['url'] = item.get('url')
        self['titular'] = item.get('titular')
        self['contenido_texto'] = item.get('contenido_texto')
        self['medio'] = item.get('medio')
        self['pais_publicacion'] = item.get('pais_publicacion')
        self['tipo_medio'] = item.get('tipo_medio')
        self['fecha_publicacion'] = item.get('fecha_publicacion')
        self['autor'] = item.get('autor')
        self['idioma'] = item.get('idioma')
        self['seccion'] = item.get('seccion')
        self['etiquetas_fuente'] = item.get('etiquetas_fuente', [])
        self['es_opinion'] = item.get('es_opinion', False)
        self['es_oficial'] = item.get('es_oficial', False)
        self['fecha_captura'] = item.get('fecha_captura', datetime.now())
        self['storage_path'] = item.get('storage_path')
        self['error_detalle'] = item.get('error_detalle')
        
        # Convert datetime objects to ISO format strings
        if isinstance(self['fecha_publicacion'], datetime):
            self['fecha_publicacion'] = self['fecha_publicacion'].isoformat()
        if isinstance(self['fecha_captura'], datetime):
            self['fecha_captura'] = self['fecha_captura'].isoformat()
        
        # Ensure etiquetas_fuente is a list
        if isinstance(self['etiquetas_fuente'], str):
            self['etiquetas_fuente'] = [self['etiquetas_fuente']]
        elif not isinstance(self['etiquetas_fuente'], list):
            self['etiquetas_fuente'] = []
        
        # Remove None values
        self._remove_none_values()
    
    def _remove_none_values(self):
        """Remove keys with None values"""
        keys_to_remove = [k for k, v in self.items() if v is None]
        for key in keys_to_remove:
            del self[key]
    
    def validate_required_fields(self):
        """Validate that all required fields are present"""
        required_fields = ['url', 'titular', 'medio']
        missing_fields = [field for field in required_fields if not self.get(field)]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        return True
