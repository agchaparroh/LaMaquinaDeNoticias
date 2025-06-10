from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, constr, conint, model_validator, field_validator
from datetime import datetime
from src.utils.validation import clean_text, validate_url

# --- MODELO TEMPORAL PARA TESTING ---
class ArticuloInItem(BaseModel):
    """
    Modelo temporal para testing del sistema de monitoreo.
    Representa un artículo completo para procesamiento en el pipeline.
    """
    medio: str = Field(..., description="Nombre del medio de comunicación")
    pais_publicacion: str = Field(..., description="País donde se publicó el artículo")
    tipo_medio: str = Field(..., description="Tipo de medio (digital, impreso, televisión, etc.)")
    titular: str = Field(..., description="Titular del artículo")
    fecha_publicacion: datetime = Field(..., description="Fecha de publicación del artículo")
    contenido_texto: str = Field(..., description="Contenido completo del artículo")
    idioma: Optional[str] = Field(default="es", description="Idioma del artículo")
    autor: Optional[str] = Field(default=None, description="Autor del artículo")
    url: Optional[str] = Field(default=None, description="URL del artículo")
    seccion: Optional[str] = Field(default=None, description="Sección del medio")
    es_opinion: Optional[bool] = Field(default=False, description="Indica si es un artículo de opinión")
    es_oficial: Optional[bool] = Field(default=True, description="Indica si es contenido oficial")
    fecha_recopilacion: Optional[datetime] = Field(default=None, description="Fecha de recopilación")
    estado_procesamiento: Optional[str] = Field(default="pendiente_connector", description="Estado actual del procesamiento")
    etiquetas_fuente: Optional[List[str]] = Field(default_factory=list, description="Etiquetas del medio fuente")
    
    def validate_required_fields(self) -> bool:
        """Valida que los campos requeridos estén presentes."""
        required_fields = ['titular', 'medio', 'pais_publicacion', 'tipo_medio', 'fecha_publicacion', 'contenido_texto']
        for field in required_fields:
            value = getattr(self, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                return False
        return True

class FragmentoProcesableItem(BaseModel):
    """
    Modelo Pydantic que representa un fragmento de documento procesable en el pipeline.
    Sirve como contrato de datos para las primeras etapas del procesamiento.
    """
    id_fragmento: constr(strip_whitespace=True, min_length=1, max_length=255) = Field(
        ...,
        description="Identificador único del fragmento, sin espacios al inicio/final y longitud entre 1 y 255 caracteres."
    )
    texto_original: constr(strip_whitespace=True, min_length=1) = Field(
        ...,
        description="Contenido textual original del fragmento, no debe estar vacío."
    )
    
    @field_validator('texto_original', mode='after')
    @classmethod
    def clean_texto_original(cls, value: str) -> str:
        """Limpia el texto original de caracteres no deseados."""
        # Aplicar limpieza preservando saltos de línea
        return clean_text(value, preserve_newlines=True)
    id_articulo_fuente: constr(strip_whitespace=True, min_length=1, max_length=255) = Field(
        ...,
        description="Identificador único del artículo fuente al que pertenece el fragmento."
    )
    orden_en_articulo: Optional[conint(ge=0)] = Field(
        default=None,
        description="Posición ordinal del fragmento dentro del artículo fuente, debe ser un entero no negativo si se provee."
    )
    metadata_adicional: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Metadatos adicionales asociados al fragmento en formato de diccionario."
    )
    
    @field_validator('metadata_adicional', mode='after')
    @classmethod
    def validate_metadata_urls(cls, value: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Valida URLs en metadata si existen."""
        if value and 'url_fuente' in value and value['url_fuente']:
            try:
                value['url_fuente'] = validate_url(value['url_fuente'])
            except ValueError:
                # Si la URL es inválida, la removemos
                del value['url_fuente']
        return value

    @model_validator(mode='after')
    def check_revision_especial_texto_longitud(self) -> "FragmentoProcesableItem":
        if self.metadata_adicional and self.metadata_adicional.get("requiere_revision_especial") is True:
            if len(self.texto_original) < 50:
                raise ValueError(
                    "Si 'requiere_revision_especial' es True en metadata_adicional, "
                    "texto_original debe tener al menos 50 caracteres."
                )
        return self
