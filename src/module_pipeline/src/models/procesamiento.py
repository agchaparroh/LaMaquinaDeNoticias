"""
Módulo que define los modelos de datos Pydantic para el pipeline de procesamiento de noticias.

SOLUCIÓN IMPLEMENTADA: Preservación de Información Estructurada
===============================================================
ANTES: 43 campos específicos del LLM se perdían en metadata_*: Dict[str, Any]
DESPUÉS: Información preservada al 100% con modelos Pydantic específicos

Patrón de Diseño para Metadatos de Fases:
-----------------------------------------
Para asegurar una estructura de datos robusta, validada y clara, los metadatos específicos
de cada fase del pipeline (ej. Fase 1 Triaje, Fase 2 Extracción, etc.) deben ser
encapsulados en sus propias clases Pydantic dedicadas (ej. `MetadatosFase1Triaje`).

Esto es preferible a utilizar diccionarios genéricos (`Dict[str, Any]`) porque:
1. Proporciona validación automática de tipos y formatos para los campos de metadatos.
2. Mejora la legibilidad del código y la auto-documentación, ya que la estructura
   de los metadatos es explícita.
3. Facilita el mantenimiento y la refactorización, ya que los cambios en la estructura
   de los metadatos están localizados en una clase específica.

Se recomienda seguir este patrón para los metadatos de todas las fases del pipeline.
"""
from datetime import datetime, timezone
from typing import Optional, Any, Dict, List, Union # Union no se usa actualmente, pero es útil tenerla
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator, constr, confloat, HttpUrl
from typing_extensions import Self # Para el tipo de retorno en model_validator de Pydantic v2

# IMPORTAR MODELOS DE METADATOS ESPECÍFICOS
from .metadatos import MetadatosHecho, MetadatosEntidad, MetadatosCita, MetadatosDato

# Para asegurar que las fechas sean "aware" (con zona horaria)
AwareDatetime = datetime

def get_aware_now() -> AwareDatetime:
    return datetime.now(timezone.utc)

class PipelineBaseModel(BaseModel):
    fecha_creacion: AwareDatetime = Field(default_factory=get_aware_now, description="Fecha y hora de creación del registro, con zona horaria UTC.")
    fecha_actualizacion: AwareDatetime = Field(default_factory=get_aware_now, description="Fecha y hora de la última actualización del registro, con zona horaria UTC.")

    model_config = {
        "validate_assignment": True,
        "extra": "forbid",
        "use_enum_values": True,
        "json_encoders": {
            datetime: lambda dt: dt.isoformat().replace('+00:00', 'Z'), # Asegurar 'Z' para UTC
            UUID: lambda u: str(u)
        },
        "populate_by_name": True,
    }

    def touch(self) -> None:
        """Actualiza la fecha_actualizacion al momento actual."""
        self.fecha_actualizacion = get_aware_now()

class MetadatosFase1Triaje(BaseModel):
    """
    Metadatos específicos y estructurados de la fase 1 (triaje).
    
    Incluye tanto información técnica de la llamada al LLM como metadatos 
    del procesamiento interno de la fase.
    """
    # Metadatos de la llamada al LLM
    nombre_modelo_triaje: Optional[str] = Field(None, description="Nombre del modelo LLM utilizado para el triaje")
    tokens_prompt_triaje: Optional[int] = Field(None, description="Número de tokens del prompt enviado al LLM")
    tokens_respuesta_triaje: Optional[int] = Field(None, description="Número de tokens en la respuesta del LLM")
    duracion_llamada_ms_triaje: Optional[int] = Field(None, description="Duración de la llamada al LLM en milisegundos")
    
    # Metadatos del procesamiento interno
    texto_limpio_utilizado: Optional[str] = Field(None, description="Texto limpio que se utilizó para la evaluación")
    idioma_detectado_original: Optional[str] = Field(None, description="Idioma detectado del texto original")
    notas_adicionales: Optional[List[str]] = Field(default=None, description="Notas adicionales sobre el procesamiento, como fallbacks aplicados.")

# --- Modelos de Subtarea 5.2: HechoBase y EntidadBase ---
# SOLUCIÓN ARQUITECTÓNICA: IDs Secuenciales para optimización LLM
# Los IDs secuenciales (1, 2, 3...) son más eficientes para LLMs que UUIDs
# La conversión a UUIDs/strings se hace solo en PayloadBuilder para persistencia
class HechoBase(PipelineBaseModel):
    id_hecho: int = Field(..., description="Identificador secuencial del hecho dentro del fragmento (1, 2, 3...).")
    texto_original_del_hecho: constr(min_length=1) = Field(..., description="Texto literal del hecho extraído.")
    confianza_extraccion: confloat(ge=0.0, le=1.0) = Field(..., description="Nivel de confianza de la extracción del hecho (0.0 a 1.0).")
    offset_inicio_hecho: Optional[int] = Field(default=None, description="Posición inicial del hecho en el texto original del fragmento.", ge=0)
    offset_fin_hecho: Optional[int] = Field(default=None, description="Posición final del hecho en el texto original del fragmento.", ge=0)
    
    # ✅ CAMBIO CRÍTICO: Reemplazar Dict[str, Any] con modelo específico
    metadata_hecho: MetadatosHecho = Field(
        default_factory=MetadatosHecho,
        description="Metadatos específicos del hecho extraído por LLM"
    )

    @model_validator(mode='after')
    def check_offsets_hecho(self) -> Self:
        if self.offset_inicio_hecho is not None and self.offset_fin_hecho is not None:
            if self.offset_fin_hecho < self.offset_inicio_hecho:
                raise ValueError("offset_fin_hecho no puede ser menor que offset_inicio_hecho.")
        return self

class EntidadBase(PipelineBaseModel):
    id_entidad: int = Field(..., description="Identificador secuencial de la entidad dentro del fragmento (1, 2, 3...).")
    texto_entidad: constr(min_length=1) = Field(..., description="Texto literal de la entidad extraída.")
    tipo_entidad: constr(min_length=1) = Field(..., description="Tipo de entidad (ej: PERSONA, ORGANIZACION, LUGAR).")
    relevancia_entidad: confloat(ge=0.0, le=1.0) = Field(..., description="Nivel de relevancia de la entidad (0.0 a 1.0).")
    offset_inicio_entidad: Optional[int] = Field(default=None, description="Posición inicial de la entidad en el texto original del fragmento.", ge=0)
    offset_fin_entidad: Optional[int] = Field(default=None, description="Posición final de la entidad en el texto original del fragmento.", ge=0)
    
    # ✅ CAMBIO CRÍTICO: Reemplazar Dict[str, Any] con modelo específico
    metadata_entidad: MetadatosEntidad = Field(
        default_factory=MetadatosEntidad,
        description="Metadatos específicos de la entidad extraída por LLM"
    )

    @model_validator(mode='after')
    def check_offsets_entidad(self) -> Self:
        if self.offset_inicio_entidad is not None and self.offset_fin_entidad is not None:
            if self.offset_fin_entidad < self.offset_inicio_entidad:
                raise ValueError("offset_fin_entidad no puede ser menor que offset_inicio_entidad.")
        return self

# --- Modelos de Subtarea 5.3: HechoProcesado y EntidadProcesada ---
class HechoProcesado(HechoBase):
    id_fragmento_origen: UUID = Field(..., description="ID del FragmentoProcesableItem del cual se extrajo este hecho.")
    id_articulo_fuente: Optional[UUID] = Field(default=None, description="ID del artículo original en Supabase del cual proviene el fragmento (si está disponible).")
    vinculado_a_entidades: List[int] = Field(default_factory=list, description="Lista de IDs secuenciales de EntidadProcesada relacionadas con este hecho.")
    prompt_utilizado: Optional[str] = Field(default=None, description="Prompt de Groq API usado para extraer o procesar este hecho.")
    respuesta_llm_bruta: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Respuesta completa (o relevante) del LLM asociada a este hecho.")

class EntidadProcesada(EntidadBase):
    id_fragmento_origen: UUID = Field(..., description="ID del FragmentoProcesableItem del cual se extrajo esta entidad.")
    id_entidad_normalizada: Optional[UUID] = Field(default=None, description="ID de la entidad canónica en Supabase después de la normalización (si se encontró).")
    nombre_entidad_normalizada: Optional[str] = Field(default=None, description="Nombre de la entidad canónica.")
    uri_wikidata: Optional[HttpUrl] = Field(default=None, description="URI de Wikidata para la entidad normalizada (si aplica).")
    similitud_normalizacion: Optional[confloat(ge=0.0, le=1.0)] = Field(default=None, description="Puntuación de similitud devuelta por buscar_entidad_similar (0.0 a 1.0).")
    prompt_utilizado_normalizacion: Optional[str] = Field(default=None, description="Prompt de Groq API usado para la normalización (si aplica).")

# --- Modelos de Subtarea 5.4: CitaTextual y DatosCuantitativos ---
class CitaTextual(PipelineBaseModel):
    id_cita: int = Field(..., description="Identificador secuencial de la cita textual dentro del fragmento.")
    id_fragmento_origen: UUID = Field(..., description="ID del FragmentoProcesableItem del cual se extrajo esta cita.")
    texto_cita: constr(min_length=5) = Field(..., description="El contenido textual exacto de la cita.")
    persona_citada: Optional[str] = Field(default=None, description="Nombre de la persona o entidad que realiza la cita.")
    id_entidad_citada: Optional[int] = Field(default=None, description="ID secuencial de la EntidadProcesada (persona/organización) que realiza la cita, si está identificada.")
    offset_inicio_cita: Optional[int] = Field(default=None, description="Posición inicial de la cita en el texto original del fragmento.", ge=0)
    offset_fin_cita: Optional[int] = Field(default=None, description="Posición final de la cita en el texto original del fragmento.", ge=0)
    contexto_cita: Optional[str] = Field(default=None, description="Contexto breve que rodea la cita para mejor entendimiento.")
    
    # ✅ CAMBIO CRÍTICO: Reemplazar Dict[str, Any] con modelo específico
    metadata_cita: MetadatosCita = Field(
        default_factory=MetadatosCita,
        description="Metadatos específicos de la cita extraída por LLM"
    )

    @model_validator(mode='after')
    def check_offsets_cita(self) -> Self:
        if self.offset_inicio_cita is not None and self.offset_fin_cita is not None:
            if self.offset_fin_cita < self.offset_inicio_cita:
                raise ValueError("offset_fin_cita no puede ser menor que offset_inicio_cita.")
        return self

class DatosCuantitativos(PipelineBaseModel):
    id_dato_cuantitativo: int = Field(..., description="Identificador secuencial del dato cuantitativo dentro del fragmento.")
    id_fragmento_origen: UUID = Field(..., description="ID del FragmentoProcesableItem del cual se extrajo este dato.")
    descripcion_dato: constr(min_length=3) = Field(..., description="Descripción del dato cuantitativo (ej: 'Número de empleados', 'Porcentaje de aumento').")
    valor_dato: float = Field(..., description="Valor numérico del dato.")
    unidad_dato: Optional[str] = Field(default=None, description="Unidad de medida del dato (ej: 'millones', '%', 'USD').")
    fecha_dato: Optional[str] = Field(default=None, description="Fecha o período al que se refiere el dato (ej: '2023-Q4', 'anual').")
    fuente_especifica_dato: Optional[str] = Field(default=None, description="Fuente específica mencionada para este dato dentro del texto, si la hay.")
    offset_inicio_dato: Optional[int] = Field(default=None, description="Posición inicial del dato en el texto original del fragmento.", ge=0)
    offset_fin_dato: Optional[int] = Field(default=None, description="Posición final del dato en el texto original del fragmento.", ge=0)
    
    # ✅ CAMBIO CRÍTICO: Reemplazar Dict[str, Any] con modelo específico
    metadata_dato: MetadatosDato = Field(
        default_factory=MetadatosDato,
        description="Metadatos específicos del dato cuantitativo extraído por LLM"
    )

    @model_validator(mode='after')
    def check_offsets_dato(self) -> Self:
        if self.offset_inicio_dato is not None and self.offset_fin_dato is not None:
            if self.offset_fin_dato < self.offset_inicio_dato:
                raise ValueError("offset_fin_dato no puede ser menor que offset_inicio_dato.")
        return self

# --- Modelos de Subtarea 5.5: ResultadoFase1Triaje y ResultadoFase2Extraccion ---
class ResultadoFase1Triaje(PipelineBaseModel):
    id_resultado_triaje: UUID = Field(default_factory=uuid4, description="ID único del resultado de esta fase de triaje.")
    id_fragmento: UUID = Field(..., description="ID del FragmentoProcesableItem que fue triado.")
    es_relevante: bool = Field(..., description="Indica si el fragmento fue considerado relevante por el LLM.")
    
    # Campos derivados de la evaluación del LLM
    decision_triaje: Optional[str] = Field(default=None, description="Decisión del triaje: PROCESAR, DESCARTAR, ERROR_TRIAGE")
    justificacion_triaje: Optional[str] = Field(default=None, description="Explicación o justificación proporcionada por el LLM para la decisión de relevancia.")
    categoria_principal: Optional[str] = Field(default=None, description="Categoría principal asignada al fragmento durante el triaje.")
    palabras_clave_triaje: List[str] = Field(default_factory=list, description="Lista de palabras clave identificadas en el fragmento durante el triaje.")
    puntuacion_triaje: Optional[float] = Field(default=None, description="Puntuación numérica asignada por el LLM")
    confianza_triaje: Optional[confloat(ge=0.0, le=1.0)] = Field(default=None, description="Nivel de confianza del LLM en la decisión de triaje (0.0 a 1.0).")
    
    # Campo para el texto procesado que se pasará a la siguiente fase
    texto_para_siguiente_fase: Optional[str] = Field(default=None, description="Texto (limpio o traducido) que se pasará a la siguiente fase del pipeline")
    
    metadatos_specificos_triaje: Optional[MetadatosFase1Triaje] = Field(None, description="Metadatos específicos y estructurados de la fase de triaje.")

class ResultadoFase2Extraccion(PipelineBaseModel):
    id_resultado_extraccion: UUID = Field(default_factory=uuid4, description="ID único del resultado de esta fase de extracción.")
    id_fragmento: UUID = Field(..., description="ID del FragmentoProcesableItem del cual se extrajeron datos.")
    hechos_extraidos: List[HechoProcesado] = Field(default_factory=list, description="Lista de hechos procesados extraídos del fragmento.")
    entidades_extraidas: List[EntidadProcesada] = Field(default_factory=list, description="Lista de entidades procesadas extraídas del fragmento.")
    resumen_extraccion: Optional[str] = Field(default=None, description="Resumen generado por el LLM a partir de la información extraída.")
    prompt_extraccion_usado: Optional[str] = Field(default=None, description="El prompt específico utilizado para la fase de extracción.")
    advertencias_extraccion: List[str] = Field(default_factory=list, description="Posibles advertencias o problemas identificados durante la extracción.")
    # TODO: Refactorizar para usar una clase Pydantic específica para metadatos de extracción,
    #       siguiendo el patrón de MetadatosFase1Triaje.
    metadata_extraccion: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales específicos de la fase de extracción.")

# --- Modelos de Subtarea 5.6: ResultadoFase3CitasDatos y ResultadoFase4Normalizacion ---
class ResultadoFase3CitasDatos(PipelineBaseModel):
    id_resultado_citas_datos: UUID = Field(default_factory=uuid4, description="ID único del resultado de esta fase de citas y datos.")
    id_fragmento: UUID = Field(..., description="ID del FragmentoProcesableItem procesado.")
    citas_textuales_extraidas: List[CitaTextual] = Field(default_factory=list, description="Lista de citas textuales identificadas en el fragmento.")
    datos_cuantitativos_extraidos: List[DatosCuantitativos] = Field(default_factory=list, description="Lista de datos cuantitativos identificados en el fragmento.")
    prompt_citas_datos_usado: Optional[str] = Field(default=None, description="Prompt específico utilizado para la extracción de citas y datos.")
    advertencias_citas_datos: List[str] = Field(default_factory=list, description="Posibles advertencias durante la extracción de citas y datos.")
    # TODO: Refactorizar para usar una clase Pydantic específica para metadatos de citas y datos,
    #       siguiendo el patrón de MetadatosFase1Triaje.
    metadata_citas_datos: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales de la fase de citas y datos.")

class ResultadoFase4Normalizacion(PipelineBaseModel):
    id_resultado_normalizacion: UUID = Field(default_factory=uuid4, description="ID único del resultado de esta fase de normalización.")
    id_fragmento: UUID = Field(..., description="ID del FragmentoProcesableItem cuyas entidades fueron normalizadas.")
    entidades_normalizadas: List[EntidadProcesada] = Field(default_factory=list, description="Lista de entidades procesadas que ahora incluyen información de normalización.")
    resumen_normalizacion: Optional[str] = Field(default=None, description="Resumen del proceso de normalización para este fragmento.")
    prompt_normalizacion_usado: Optional[str] = Field(default=None, description="Prompt específico utilizado para la fase de normalización (si aplica).")
    estado_general_normalizacion: str = Field(..., description="Estado general del proceso de normalización (ej: 'Completo', 'Parcial', 'Fallido', 'No Requerido').") # Considerar Enum para estados fijos
    # TODO: Refactorizar para usar una clase Pydantic específica para metadatos de normalización,
    #       siguiendo el patrón de MetadatosFase1Triaje.
    metadata_normalizacion: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales de la fase de normalización.")
