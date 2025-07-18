from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, constr, conint, model_validator, field_validator
from datetime import datetime
from uuid import uuid4
from src.utils.validation import clean_text, validate_url
from .procesamiento import PipelineBaseModel, AwareDatetime
import os

# --- MODELO TEMPORAL PARA TESTING ---
class ArticuloInItem(BaseModel):
    """
    Modelo temporal para testing del sistema de monitoreo.
    Representa un artículo completo para procesamiento en el pipeline.
    """
    # ID del artículo en la base de datos (propagado desde el scraper)
    articulo_id: Optional[int] = Field(default=None, description="ID del artículo en la base de datos")
    
    medio: str = Field(..., description="Nombre del medio de comunicación")
    area_geografica: str = Field(..., description="Área geográfica donde se publicó el artículo")
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
        required_fields = ['titular', 'medio', 'area_geografica', 'tipo_medio', 'fecha_publicacion', 'contenido_texto']
        for field in required_fields:
            value = getattr(self, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                return False
        return True
    
    class Config:
        # En modo desarrollo, permitir campos extra para facilitar debugging
        # En producción, ser estricto con los campos
        extra = "allow" if os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true' else "ignore"

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


class ArticuloProcesableItem(PipelineBaseModel):
    """
    Modelo que representa un artículo completo procesable en el pipeline.
    
    Este modelo elimina la conversión innecesaria de artículos a fragmentos,
    preservando toda la metadata del artículo original y proporcionando
    una interfaz compatible con el pipeline de procesamiento.
    
    Mapea ArticuloInItem.contenido_texto a campos específicos del pipeline
    mientras mantiene la semántica de artículo completo.
    """
    
    # === CAMPOS DE IDENTIFICACIÓN ===
    id_articulo: constr(strip_whitespace=True, min_length=1, max_length=255) = Field(
        ...,
        description="ID único del artículo (formato ART-{ID} o UUID)"
    )
    id_articulo_fuente: Optional[int] = Field(
        default=None,
        description="ID del artículo en la base de datos original"
    )
    
    # === CONTENIDO PROCESABLE ===
    contenido_texto: constr(strip_whitespace=True, min_length=1) = Field(
        ...,
        description="Texto completo del artículo para procesamiento"
    )
    
    # === METADATOS DEL ARTÍCULO (preservados desde ArticuloInItem) ===
    medio: str = Field(..., description="Nombre del medio de comunicación")
    area_geografica: str = Field(..., description="Área geográfica donde se publicó el artículo")
    tipo_medio: str = Field(..., description="Tipo de medio (digital, impreso, televisión, etc.)")
    titular: str = Field(..., description="Titular del artículo")
    fecha_publicacion: AwareDatetime = Field(..., description="Fecha de publicación del artículo")
    
    # === CAMPOS OPCIONALES PRESERVADOS ===
    idioma: Optional[str] = Field(default="es", description="Idioma del artículo")
    autor: Optional[str] = Field(default=None, description="Autor del artículo")
    url: Optional[str] = Field(default=None, description="URL del artículo")
    seccion: Optional[str] = Field(default=None, description="Sección del medio")
    es_opinion: bool = Field(default=False, description="Indica si es un artículo de opinión")
    es_oficial: bool = Field(default=True, description="Indica si es contenido oficial")
    fecha_recopilacion: Optional[AwareDatetime] = Field(default=None, description="Fecha de recopilación")
    estado_procesamiento: Optional[str] = Field(default="pendiente_pipeline", description="Estado actual del procesamiento")
    etiquetas_fuente: List[str] = Field(default_factory=list, description="Etiquetas del medio fuente")
    
    # === METADATOS ADICIONALES ===
    metadata_adicional: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Metadatos adicionales del artículo en formato de diccionario"
    )
    
    # === VALIDACIONES ESPECÍFICAS DEL DOMINIO ===
    
    @field_validator('contenido_texto', mode='after')
    @classmethod
    def clean_contenido_texto(cls, value: str) -> str:
        """Limpia el texto completo preservando estructura."""
        return clean_text(value, preserve_newlines=True)
    
    @field_validator('url', mode='after')
    @classmethod
    def validate_url_if_present(cls, value: Optional[str]) -> Optional[str]:
        """Valida URL si está presente."""
        if value:
            try:
                return validate_url(value)
            except ValueError:
                # Si la URL es inválida, la removemos
                return None
        return value
    
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
    def validate_articulo_coherence(self) -> "ArticuloProcesableItem":
        """Valida coherencia del artículo completo."""
        # Validar que artículos de opinión tengan autor
        if self.es_opinion and not self.autor:
            raise ValueError("Artículos de opinión deben tener autor identificado")
        
        # Validar longitud mínima del texto
        if len(self.contenido_texto.strip()) < 50:
            raise ValueError("Contenido del artículo debe tener al menos 50 caracteres")
        
        # Validar campos requeridos
        required_fields = ['titular', 'medio', 'area_geografica', 'tipo_medio']
        for field in required_fields:
            value = getattr(self, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                raise ValueError(f"Campo requerido '{field}' no puede estar vacío")
        
        return self
    
    # === MÉTODOS DE CONVERSIÓN ===
    
    @classmethod
    def from_articulo_in_item(cls, articulo_in: ArticuloInItem) -> "ArticuloProcesableItem":
        """
        Convierte ArticuloInItem a ArticuloProcesableItem.
        
        Args:
            articulo_in: Instancia de ArticuloInItem
            
        Returns:
            Instancia de ArticuloProcesableItem
            
        Raises:
            ValueError: Si el artículo no pasa las validaciones
        """
        # Generar ID único del artículo
        if articulo_in.articulo_id:
            id_articulo = f"ART-{articulo_in.articulo_id}"
        else:
            id_articulo = str(uuid4())
        
        # Convertir fecha_publicacion a AwareDatetime si es necesario
        fecha_pub = articulo_in.fecha_publicacion
        if fecha_pub.tzinfo is None:
            from datetime import timezone
            fecha_pub = fecha_pub.replace(tzinfo=timezone.utc)
        
        # Convertir fecha_recopilacion si existe
        fecha_recap = articulo_in.fecha_recopilacion
        if fecha_recap and fecha_recap.tzinfo is None:
            from datetime import timezone
            fecha_recap = fecha_recap.replace(tzinfo=timezone.utc)
        
        return cls(
            id_articulo=id_articulo,
            id_articulo_fuente=articulo_in.articulo_id,
            contenido_texto=articulo_in.contenido_texto,
            medio=articulo_in.medio,
            area_geografica=articulo_in.area_geografica,
            tipo_medio=articulo_in.tipo_medio,
            titular=articulo_in.titular,
            fecha_publicacion=fecha_pub,
            idioma=articulo_in.idioma or "es",
            autor=articulo_in.autor,
            url=articulo_in.url,
            seccion=articulo_in.seccion,
            es_opinion=articulo_in.es_opinion or False,
            es_oficial=articulo_in.es_oficial or True,
            fecha_recopilacion=fecha_recap,
            estado_procesamiento=articulo_in.estado_procesamiento or "pendiente_pipeline",
            etiquetas_fuente=articulo_in.etiquetas_fuente or [],
            metadata_adicional={}
        )
    
    def to_fragmento_procesable(self) -> "FragmentoProcesableItem":
        """
        Convierte el artículo completo a un fragmento procesable.
        
        Este método mantiene compatibilidad con el pipeline existente
        para casos donde se necesite procesamiento como fragmento.
        
        Returns:
            FragmentoProcesableItem equivalente
        """
        return FragmentoProcesableItem(
            id_fragmento=self.id_articulo,
            texto_original=self.contenido_texto,
            id_articulo_fuente=self.id_articulo,
            orden_en_articulo=0,
            metadata_adicional={
                "es_articulo_completo": True,
                "fragmentado": False,
                "medio": self.medio,
                "area_geografica": self.area_geografica,
                "tipo_medio": self.tipo_medio,
                "titular": self.titular,
                "fecha_publicacion": self.fecha_publicacion.isoformat(),
                "autor": self.autor,
                "idioma": self.idioma,
                "seccion": self.seccion,
                "es_opinion": self.es_opinion,
                "es_oficial": self.es_oficial,
                "url": self.url,
                "etiquetas_fuente": self.etiquetas_fuente,
                **self.metadata_adicional
            }
        )
    
    def validate_required_fields(self) -> bool:
        """
        Valida que los campos requeridos estén presentes.
        
        Returns:
            True si todos los campos requeridos están presentes
        """
        required_fields = ['titular', 'medio', 'area_geografica', 'tipo_medio', 'contenido_texto']
        for field in required_fields:
            value = getattr(self, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                return False
        return True
    
    def get_processing_context(self) -> Dict[str, Any]:
        """
        Obtiene el contexto de procesamiento para el pipeline.
        
        Returns:
            Diccionario con contexto del artículo para las fases
        """
        return {
            "titulo": self.titular,
            "fecha_publicacion": self.fecha_publicacion.isoformat(),
            "fuente": self.medio,
            "pais": self.area_geografica,
            "tipo_medio": self.tipo_medio,
            "idioma": self.idioma,
            "autor": self.autor,
            "seccion": self.seccion,
            "es_opinion": self.es_opinion,
            "url": self.url
        }
    
    class Config:
        """Configuración del modelo siguiendo patrones del pipeline."""
        json_schema_extra = {
            "example": {
                "id_articulo": "ART-123456",
                "contenido_texto": "El presidente anunció nuevas medidas económicas...",
                "medio": "El País",
                "area_geografica": "España",
                "tipo_medio": "Diario Digital",
                "titular": "Nuevas medidas económicas anunciadas por el gobierno",
                "fecha_publicacion": "2024-01-15T10:30:00Z",
                "idioma": "es",
                "autor": "Juan Pérez",
                "es_opinion": False,
                "es_oficial": True
            }
        }
