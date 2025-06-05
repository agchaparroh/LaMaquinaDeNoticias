from typing import Dict, List, Optional, Any, Self
from pydantic import BaseModel, Field, constr, conint, model_validator

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

    @model_validator(mode='after')
    def check_revision_especial_texto_longitud(self) -> Self:
        if self.metadata_adicional and self.metadata_adicional.get("requiere_revision_especial") is True:
            if len(self.texto_original) < 50:
                raise ValueError(
                    "Si 'requiere_revision_especial' es True en metadata_adicional, "
                    "texto_original debe tener al menos 50 caracteres."
                )
        return self
