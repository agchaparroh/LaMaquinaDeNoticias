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
from uuid import uuid4

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
            # UUID removido - ahora usamos strings directamente
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
    del procesamiento interno de la fase, análisis de contenido y decisiones de flujo.
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
    
    # Análisis de contenido (NUEVA FUNCIONALIDAD)
    analisis_contenido: Optional[Dict[str, Any]] = Field(None, description="Resultados del análisis de contenido con SpacyAnalyzer")
    decisiones_flujo: Optional[Dict[str, Any]] = Field(None, description="Decisiones de flujo adaptativo generadas por AdaptiveFlowController")
    estadisticas_procesamiento: Optional[Dict[str, Any]] = Field(None, description="Estadísticas sobre la complejidad y configuración del procesamiento")

# --- Modelos de Subtarea 5.2: HechoBase y EntidadBase ---
# SOLUCIÓN ARQUITECTÓNICA: IDs Secuenciales para optimización LLM
# Los IDs secuenciales (1, 2, 3...) son más eficientes para LLMs que UUIDs
# La conversión a UUIDs/strings se hace solo en PayloadBuilder para persistencia
class HechoBase(PipelineBaseModel):
    id_hecho: int = Field(..., description="Identificador secuencial del hecho dentro del fragmento (1, 2, 3...).")
    contenido: constr(min_length=1) = Field(..., description="Descripción completa del hecho.")
    fecha_inicio: str = Field(..., description="Fecha de inicio del hecho en formato YYYY-MM-DD.")
    fecha_fin: str = Field(..., description="Fecha de fin del hecho en formato YYYY-MM-DD.")
    precision_temporal: str = Field(..., description="Precisión temporal del hecho (exacta, dia, semana, mes, etc.).")
    tipo_hecho: str = Field(..., description="Tipo de hecho (SUCESO, ANUNCIO, DECLARACION, etc.).")
    importancia: int = Field(..., ge=1, le=10, description="Nivel de importancia del hecho (1 a 10).")
    pais: List[str] = Field(default_factory=list, description="Lista de países relacionados con el hecho.")
    region: Optional[List[str]] = Field(default=None, description="Lista de regiones relacionadas con el hecho.")
    ciudad: Optional[List[str]] = Field(default=None, description="Lista de ciudades relacionadas con el hecho.")
    etiquetas: Optional[List[str]] = Field(default=None, description="Etiquetas o categorías del hecho.")
    
    # ✅ CAMBIO CRÍTICO: Reemplazar Dict[str, Any] con modelo específico
    metadata_hecho: MetadatosHecho = Field(
        default_factory=MetadatosHecho,
        description="Metadatos específicos del hecho extraído por LLM"
    )

class EntidadBase(PipelineBaseModel):
    id_entidad: int = Field(..., description="Identificador secuencial de la entidad dentro del fragmento (1, 2, 3...).")
    nombre: constr(min_length=1) = Field(..., description="Nombre canónico/principal de la entidad.")
    tipo: constr(min_length=1) = Field(..., description="Tipo de entidad (ej: PERSONA, ORGANIZACION, LUGAR).")
    descripcion: Optional[str] = Field(default=None, description="Descripción textual de la entidad.")
    alias: List[str] = Field(default_factory=list, description="Lista de nombres alternativos, siglas o alias.")
    relevancia: int = Field(..., ge=1, le=10, description="Nivel de relevancia de la entidad (1 a 10).")
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
    id_fragmento_origen: str = Field(..., description="ID del FragmentoProcesableItem del cual se extrajo este hecho (formato ART-{ID} o UUID).")
    id_articulo_fuente: Optional[str] = Field(default=None, description="ID del artículo original en Supabase del cual proviene el fragmento (si está disponible).")
    vinculado_a_entidades: List[int] = Field(default_factory=list, description="Lista de IDs secuenciales de EntidadProcesada relacionadas con este hecho.")
    prompt_utilizado: Optional[str] = Field(default=None, description="Prompt de Groq API usado para extraer o procesar este hecho.")
    respuesta_llm_bruta: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Respuesta completa (o relevante) del LLM asociada a este hecho.")

class EntidadProcesada(EntidadBase):
    id_fragmento_origen: str = Field(..., description="ID del FragmentoProcesableItem del cual se extrajo esta entidad (formato ART-{ID} o UUID).")
    id_entidad_normalizada: Optional[str] = Field(default=None, description="ID de la entidad canónica en Supabase después de la normalización (si se encontró).")
    nombre_entidad_normalizada: Optional[str] = Field(default=None, description="Nombre de la entidad canónica.")
    uri_wikidata: Optional[HttpUrl] = Field(default=None, description="URI de Wikidata para la entidad normalizada (si aplica).")
    similitud_normalizacion: Optional[confloat(ge=0.0, le=1.0)] = Field(default=None, description="Puntuación de similitud devuelta por buscar_entidad_similar (0.0 a 1.0).")
    prompt_utilizado_normalizacion: Optional[str] = Field(default=None, description="Prompt de Groq API usado para la normalización (si aplica).")

# --- Modelos de Subtarea 5.4: CitaTextual y DatosCuantitativos ---
class CitaTextual(PipelineBaseModel):
    id_cita: int = Field(..., description="Identificador secuencial de la cita textual dentro del fragmento.")
    id_fragmento_origen: str = Field(..., description="ID del FragmentoProcesableItem del cual se extrajo esta cita (formato ART-{ID} o UUID).")
    cita: constr(min_length=5) = Field(..., description="El contenido textual exacto de la cita.")
    persona_citada: Optional[str] = Field(default=None, description="Nombre de la persona o entidad que realiza la cita.")
    entidad_emisora_id: Optional[int] = Field(default=None, description="ID secuencial de la EntidadProcesada (persona/organización) que realiza la cita, si está identificada.")
    hecho_contexto_id: Optional[int] = Field(default=None, description="ID del hecho al que pertenece o contextualiza la cita.")
    fecha_cita: Optional[str] = Field(default=None, description="Fecha de la cita en formato YYYY-MM-DD.")
    offset_inicio_cita: Optional[int] = Field(default=None, description="Posición inicial de la cita en el texto original del fragmento.", ge=0)
    offset_fin_cita: Optional[int] = Field(default=None, description="Posición final de la cita en el texto original del fragmento.", ge=0)
    contexto: Optional[str] = Field(default=None, description="Contexto breve que rodea la cita para mejor entendimiento.")
    relevancia: int = Field(..., ge=1, le=5, description="Relevancia de la cita en escala 1-5.")
    
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
    id_fragmento_origen: str = Field(..., description="ID del FragmentoProcesableItem del cual se extrajo este dato (formato ART-{ID} o UUID).")
    hecho_id: Optional[int] = Field(default=None, description="ID del hecho relacionado con este dato cuantitativo.")
    indicador: constr(min_length=3) = Field(..., description="Indicador o concepto medido (ej: 'PIB', 'Tasa de desempleo', 'Inflación').")
    categoria: str = Field(..., description="Categoría del dato cuantitativo.", 
        pattern=r"^(económico|demográfico|electoral|social|presupuestario|sanitario|ambiental|conflicto|otro)$")
    valor_numerico: float = Field(..., description="Valor numérico exacto del dato.")
    unidad: str = Field(..., description="Unidad de medida del dato (ej: 'millones', '%', 'USD').")
    ambito_geografico: List[str] = Field(default_factory=list, description="Ámbito geográfico al que se refiere el dato.")
    periodo_referencia_inicio: Optional[str] = Field(default=None, pattern=r'^(\d{4}-\d{2}-\d{2})?$', description="Fecha de inicio del periodo de referencia en formato YYYY-MM-DD.")
    periodo_referencia_fin: Optional[str] = Field(default=None, pattern=r'^(\d{4}-\d{2}-\d{2})?$', description="Fecha de fin del periodo de referencia en formato YYYY-MM-DD.")
    tipo_periodo: Optional[str] = Field(default=None, description="Tipo de periodo al que se refiere el dato.",
        pattern=r"^(anual|trimestral|mensual|semanal|diario|puntual|acumulado)?$")
    tendencia: Optional[str] = Field(default=None, description="Tendencia observada en el dato.",
        pattern=r"^(aumento|disminución|estable)?$")
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
    id_resultado_triaje: str = Field(default_factory=lambda: str(uuid4()), description="ID único del resultado de esta fase de triaje.")
    id_fragmento: str = Field(..., description="ID del FragmentoProcesableItem que fue triado (formato ART-{ID} o UUID).")
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
    id_resultado_extraccion: str = Field(default_factory=lambda: str(uuid4()), description="ID único del resultado de esta fase de extracción.")
    id_fragmento: str = Field(..., description="ID del FragmentoProcesableItem del cual se extrajeron datos (formato ART-{ID} o UUID).")
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
    id_resultado_citas_datos: str = Field(default_factory=lambda: str(uuid4()), description="ID único del resultado de esta fase de citas y datos.")
    id_fragmento: str = Field(..., description="ID del FragmentoProcesableItem procesado (formato ART-{ID} o UUID).")
    citas_textuales_extraidas: List[CitaTextual] = Field(default_factory=list, description="Lista de citas textuales identificadas en el fragmento.")
    datos_cuantitativos_extraidos: List[DatosCuantitativos] = Field(default_factory=list, description="Lista de datos cuantitativos identificados en el fragmento.")
    prompt_citas_datos_usado: Optional[str] = Field(default=None, description="Prompt específico utilizado para la extracción de citas y datos.")
    advertencias_citas_datos: List[str] = Field(default_factory=list, description="Posibles advertencias durante la extracción de citas y datos.")
    # TODO: Refactorizar para usar una clase Pydantic específica para metadatos de citas y datos,
    #       siguiendo el patrón de MetadatosFase1Triaje.
    metadata_citas_datos: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales de la fase de citas y datos.")

class ResultadoFase4Normalizacion(PipelineBaseModel):
    id_resultado_normalizacion: str = Field(default_factory=lambda: str(uuid4()), description="ID único del resultado de esta fase de normalización.")
    id_fragmento: str = Field(..., description="ID del FragmentoProcesableItem cuyas entidades fueron normalizadas (formato ART-{ID} o UUID).")
    entidades_normalizadas: List[EntidadProcesada] = Field(default_factory=list, description="Lista de entidades procesadas que ahora incluyen información de normalización.")
    resumen_normalizacion: Optional[str] = Field(default=None, description="Resumen del proceso de normalización para este fragmento.")
    prompt_normalizacion_usado: Optional[str] = Field(default=None, description="Prompt específico utilizado para la fase de normalización (si aplica).")
    estado_general_normalizacion: str = Field(..., description="Estado general del proceso de normalización (ej: 'Completo', 'Parcial', 'Fallido', 'No Requerido').") # Considerar Enum para estados fijos
    # TODO: Refactorizar para usar una clase Pydantic específica para metadatos de normalización,
    #       siguiendo el patrón de MetadatosFase1Triaje.
    metadata_normalizacion: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales de la fase de normalización.")

# --- Modelos de Subtarea 7B: Relaciones Detectadas por Fase 7 ---
class HechoEntidadRelacion(PipelineBaseModel):
    """
    Representa una relación entre un hecho y una entidad (tabla hecho_entidad).
    
    Modelo Pydantic para validar relaciones hecho-entidad detectadas en Fase 7B.1.
    Los campos coinciden exactamente con la tabla hecho_entidad en la BD.
    """
    hecho_id: int = Field(..., description="ID secuencial del hecho dentro del fragmento.")
    fecha_ocurrencia_hecho: str = Field(..., description="Rango temporal de ocurrencia del hecho (tstzrange format).")
    entidad_id: int = Field(..., description="ID secuencial de la entidad dentro del fragmento.")
    tipo_relacion: constr(pattern=r"^(protagonista|mencionado|afectado|declarante|ubicacion|contexto|victima|agresor|organizador|participante|otro)$") = Field(
        ..., description="Tipo de relación entre el hecho y la entidad."
    )
    relevancia_en_hecho: int = Field(..., ge=1, le=10, description="Relevancia de la entidad en el hecho (1-10).")

class EntidadEntidadRelacion(PipelineBaseModel):
    """
    Representa una relación entre dos entidades (tabla entidad_relacion).
    
    Modelo Pydantic para validar relaciones entidad-entidad detectadas en Fase 7B.1.
    Los campos coinciden exactamente con la tabla entidad_relacion en la BD.
    """
    entidad_origen_id: int = Field(..., description="ID secuencial de la entidad origen.")
    entidad_destino_id: int = Field(..., description="ID secuencial de la entidad destino.")
    tipo_relacion: constr(pattern=r"^(miembro_de|subsidiaria_de|aliado_con|opositor_a|sucesor_de|predecesor_de|casado_con|familiar_de|empleado_de)$") = Field(
        ..., description="Tipo de relación estructural entre las entidades."
    )
    descripcion: Optional[str] = Field(default=None, description="Descripción textual de la relación.")
    fuerza_relacion: int = Field(..., ge=1, le=10, description="Fuerza o confianza en la relación (1-10).")
    
    @model_validator(mode='after')
    def check_entidades_diferentes(self) -> Self:
        """Valida que las entidades origen y destino sean diferentes."""
        if self.entidad_origen_id == self.entidad_destino_id:
            raise ValueError("entidad_origen_id no puede ser igual a entidad_destino_id")
        return self

class HechoHechoRelacion(PipelineBaseModel):
    """
    Representa una relación entre dos hechos (tabla hecho_relacionado).
    
    Modelo Pydantic para validar relaciones hecho-hecho detectadas en Fase 7B.2.
    Los campos coinciden exactamente con la tabla hecho_relacionado en la BD.
    """
    hecho_origen_id: int = Field(..., description="ID secuencial del hecho origen.")
    fecha_ocurrencia_origen: str = Field(..., description="Rango temporal de ocurrencia del hecho origen (tstzrange format).")
    hecho_destino_id: int = Field(..., description="ID secuencial del hecho destino.")
    fecha_ocurrencia_destino: str = Field(..., description="Rango temporal de ocurrencia del hecho destino (tstzrange format).")
    tipo_relacion: constr(pattern=r"^(causa|consecuencia|contexto_historico|respuesta_a|aclaracion_de|version_alternativa|seguimiento_de)$") = Field(
        ..., description="Tipo de relación temporal/causal entre los hechos."
    )
    fuerza_relacion: int = Field(..., ge=1, le=10, description="Fuerza o confianza en la relación (1-10).")
    descripcion_relacion: Optional[str] = Field(default=None, description="Descripción de cómo se relacionan los hechos.")
    
    @model_validator(mode='after')
    def check_hechos_diferentes(self) -> Self:
        """Valida que los hechos origen y destino sean diferentes O tengan fechas diferentes."""
        if (self.hecho_origen_id == self.hecho_destino_id and 
            self.fecha_ocurrencia_origen == self.fecha_ocurrencia_destino):
            raise ValueError("Los hechos deben ser diferentes o tener fechas de ocurrencia diferentes")
        return self

class ContradiccionDetectada(PipelineBaseModel):
    """
    Representa una contradicción detectada entre dos hechos (tabla contradicciones).
    
    Modelo Pydantic para validar contradicciones detectadas en Fase 7B.2.
    Los campos coinciden exactamente con la tabla contradicciones en la BD.
    
    NOTA: El campo 'id' (bigint PRIMARY KEY) se genera automáticamente en la BD,
    por lo que no se incluye en este modelo de procesamiento.
    """
    hecho_principal_id: int = Field(..., description="ID secuencial del hecho principal.")
    fecha_ocurrencia_principal: str = Field(..., description="Rango temporal del hecho principal (tstzrange format).")
    hecho_contradictorio_id: int = Field(..., description="ID secuencial del hecho que contradice.")
    fecha_ocurrencia_contradictoria: str = Field(..., description="Rango temporal del hecho contradictorio (tstzrange format).")
    tipo_contradiccion: constr(pattern=r"^(fecha|contenido|entidades|ubicacion|valor|completa)$") = Field(
        ..., description="Tipo de contradicción detectada."
    )
    grado_contradiccion: int = Field(..., ge=1, le=5, description="Grado de la contradicción (1-5).")
    descripcion: Optional[str] = Field(default=None, description="Descripción de la contradicción.")
    estado_resolucion: Optional[constr(pattern=r"^(pendiente|analizada|resuelta|ignorada)$")] = Field(
        default="pendiente", description="Estado de resolución de la contradicción."
    )
    fecha_deteccion: AwareDatetime = Field(default_factory=get_aware_now, description="Fecha y hora de detección de la contradicción.")
    
    @model_validator(mode='after')
    def check_hechos_diferentes(self) -> Self:
        """Valida que los hechos sean diferentes O tengan fechas diferentes."""
        if (self.hecho_principal_id == self.hecho_contradictorio_id and 
            self.fecha_ocurrencia_principal == self.fecha_ocurrencia_contradictoria):
            raise ValueError("Los hechos contradictorios deben ser diferentes o tener fechas de ocurrencia diferentes")
        return self
