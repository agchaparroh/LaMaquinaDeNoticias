"""
Mock del modelo ArticuloInItem para pruebas
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ArticuloInItem(BaseModel):
    """
    Mock del modelo ArticuloInItem del module_connector.
    Basado en el uso en main.py.
    """
    # Campos requeridos
    medio: str = Field(..., description="Nombre del medio de comunicación")
    pais_publicacion: str = Field(..., description="País de publicación")
    tipo_medio: str = Field(..., description="Tipo de medio (Digital, Impreso, etc.)")
    titular: str = Field(..., description="Titular del artículo")
    fecha_publicacion: datetime = Field(..., description="Fecha de publicación")
    contenido_texto: str = Field(..., description="Contenido textual del artículo")
    
    # Campos opcionales
    idioma: Optional[str] = Field(None, description="Idioma del artículo")
    fecha_recopilacion: Optional[datetime] = Field(None, description="Fecha de recopilación")
    estado_procesamiento: Optional[str] = Field("pendiente_connector", description="Estado del procesamiento")
    url: Optional[str] = Field(None, description="URL del artículo")
    autor: Optional[str] = Field(None, description="Autor del artículo")
    seccion: Optional[str] = Field(None, description="Sección del artículo")
    etiquetas_fuente: Optional[List[str]] = Field(None, description="Etiquetas del artículo")
    es_opinion: Optional[bool] = Field(False, description="Si es artículo de opinión")
    es_oficial: Optional[bool] = Field(False, description="Si es comunicado oficial")
    
    def validate_required_fields(self) -> bool:
        """
        Valida que todos los campos requeridos estén presentes.
        """
        required_fields = ["titular", "medio", "pais_publicacion", "tipo_medio", "fecha_publicacion", "contenido_texto"]
        
        for field in required_fields:
            value = getattr(self, field)
            if value is None or (isinstance(value, str) and not value.strip()):
                return False
        
        return True
