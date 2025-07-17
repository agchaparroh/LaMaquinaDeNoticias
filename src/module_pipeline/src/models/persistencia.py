from __future__ import annotations # Necesario para referencias de tipo forward en Listas de modelos aún no definidos completamente

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict # HttpUrl si se decide usar para URLs

# --- Modelo Base para Persistencia ---
class PersistenciaBaseModel(BaseModel):
    """
    Modelo base para todos los modelos de persistencia.
    Configuraciones comunes como ignorar campos extra y permitir populación por alias.
    """
    model_config = ConfigDict(extra='ignore', populate_by_name=True)

# --- Modelos para Elementos Anidados Comunes ---

class EntidadEnHechoItem(PersistenciaBaseModel):
    """
    Representa una entidad mencionada dentro de un hecho específico.
    Referencia: "Documento 1 de Persistencia", sección "hechos_extraidos[].entidades_del_hecho[]".
    """
    id_temporal_entidad: str = Field(description="ID temporal único para esta entidad dentro del payload (puede repetirse si la misma entidad aparece en múltiples hechos).")
    nombre_entidad: str = Field(description="Nombre de la entidad tal como aparece o fue identificada.")
    tipo_entidad: str = Field(description="Tipo de entidad (ej: 'PERSONA', 'ORGANIZACION', 'LUGAR').")
    rol_en_hecho: Optional[str] = Field(default=None, description="Rol que juega la entidad en este hecho (ej: 'protagonista', 'afectado', 'testigo').")

class HechoExtraidoItem(PersistenciaBaseModel):
    """
    Representa un hecho estructurado extraído del contenido.
    Referencia: "Documento 1 de Persistencia", sección "hechos_extraidos[]".
    """
    id_temporal_hecho: str = Field(description="ID temporal único para este hecho dentro del payload.")
    descripcion_hecho: str = Field(description="Descripción del hecho.")
    tipo_hecho: Optional[str] = Field(default=None, description="Tipo de hecho (ej: 'declaracion', 'evento_social', 'hallazgo_cientifico').")
    subtipo_hecho: Optional[str] = Field(default=None, description="Subtipo más específico del hecho.")
    # Nota: El documento menciona "timestamp string (YYYY-MM-DDTHH:MM:SSZ)". Pydantic puede convertir a datetime,
    # pero para ser fiel al formato esperado por la RPC, se usa str.
    fecha_ocurrencia_hecho_inicio: Optional[str] = Field(default=None, description="Fecha y hora de inicio de ocurrencia del hecho (formato ISO 8601).")
    fecha_ocurrencia_hecho_fin: Optional[str] = Field(default=None, description="Fecha y hora de fin de ocurrencia del hecho (formato ISO 8601), si es un rango.")
    lugar_ocurrencia_hecho: Optional[str] = Field(default=None, description="Lugar donde ocurrió el hecho.")
    relevancia_hecho: Optional[int] = Field(default=None, ge=1, le=10, description="Relevancia del hecho (1-10).")
    contexto_adicional_hecho: Optional[str] = Field(default=None, description="Contexto adicional sobre el hecho.")
    
    # CAMPOS AGREGADOS (existen en base de datos Supabase pero faltaban en modelo)
    precision_temporal: Optional[str] = Field(default=None, description="Precisión temporal del hecho (coincide con columna 'precision_temporal' en DB).")
    es_evento_futuro: Optional[bool] = Field(default=None, description="Indica si el hecho es un evento futuro (coincide con columna 'es_evento_futuro' en DB).")
    estado_programacion: Optional[str] = Field(default=None, description="Estado de programación para eventos futuros (coincide con columna 'estado_programacion' en DB).")
    
    detalle_complejo_hecho: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Objeto JSON para detalles más complejos o no estructurados del hecho.")
    embedding_hecho_vector: Optional[List[float]] = Field(default=None, description="Vector de embedding semántico del hecho.")
    entidades_del_hecho: Optional[List[EntidadEnHechoItem]] = Field(default_factory=list, description="Lista de entidades involucradas en este hecho.")

class EntidadAutonomaItem(PersistenciaBaseModel):
    """
    Representa una entidad extraída de forma autónoma, no necesariamente ligada a un hecho específico en este punto.
    Referencia: "Documento 1 de Persistencia", sección "entidades_autonomas[]".
    
    ACTUALIZACIÓN: Campos sincronizados con esquema real de base de datos Supabase.
    Los campos con nombres correctos coinciden exactamente con las columnas de la tabla 'entidades'.
    """
    # CAMPOS CORRECTOS (coinciden con base de datos Supabase)
    id: str = Field(description="ID único para esta entidad (coincide con columna 'id' en DB).")
    nombre: str = Field(description="Nombre de la entidad (coincide con columna 'nombre' en DB).")
    tipo: str = Field(description="Tipo de entidad (coincide con columna 'tipo' en DB).")
    descripcion: Optional[str] = Field(default=None, description="Descripción breve de la entidad (coincide con columna 'descripcion' en DB).")
    alias: Optional[List[str]] = Field(default_factory=list, description="Lista de alias o nombres alternativos (coincide con columna 'alias' en DB).")
    
    # CAMPOS AGREGADOS (existen en base de datos pero faltaban en modelo)
    fecha_nacimiento: Optional[str] = Field(default=None, description="Fecha de nacimiento/inicio de la entidad (coincide con columna 'fecha_nacimiento' tstzrange en DB).")
    fecha_disolucion: Optional[str] = Field(default=None, description="Fecha de disolución/fin de la entidad (coincide con columna 'fecha_disolucion' tstzrange en DB).")
    
    # CAMPOS ADICIONALES (no están en esquema de base de datos pero se mantienen para lógica de negocio)
    relevancia_entidad_articulo: Optional[int] = Field(default=None, ge=1, le=10, description="Relevancia de la entidad en el contexto general del artículo (1-10).")
    metadata_entidad: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadatos adicionales sobre la entidad.")
    embedding_entidad_vector: Optional[List[float]] = Field(default=None, description="Vector de embedding semántico de la entidad.")
    
    # CAMPOS DEPRECATED (mantener compatibilidad temporal - REMOVER EN PRÓXIMA VERSIÓN)
    id_temporal_entidad: Optional[str] = Field(default=None, description="DEPRECATED: Usar 'id' en su lugar.")
    nombre_entidad: Optional[str] = Field(default=None, description="DEPRECATED: Usar 'nombre' en su lugar.")
    tipo_entidad: Optional[str] = Field(default=None, description="DEPRECATED: Usar 'tipo' en su lugar.")
    descripcion_entidad: Optional[str] = Field(default=None, description="DEPRECATED: Usar 'descripcion' en su lugar.")
    alias_entidad: Optional[List[str]] = Field(default=None, description="DEPRECATED: Usar 'alias' en su lugar.")

class CitaTextualExtraidaItem(PersistenciaBaseModel):
    """
    Representa una cita textual extraída del contenido.
    Referencia: "Documento 1 de Persistencia", sección "citas_textuales_extraidas[]".
    """
    id_temporal_cita: str = Field(description="ID temporal único para esta cita.")
    texto_cita: str = Field(description="El contenido textual de la cita.")
    entidad_emisora_id_temporal: Optional[str] = Field(default=None, description="ID temporal de la entidad que emitió la cita.")
    nombre_entidad_emisora: Optional[str] = Field(default=None, description="Nombre de la entidad que emitió la cita (puede ser redundante si se usa ID temporal).")
    cargo_entidad_emisora: Optional[str] = Field(default=None, description="Cargo o afiliación de la entidad emisora al momento de la cita.")
    fecha_cita: Optional[str] = Field(default=None, description="Fecha en que se emitió la cita (formato ISO 8601).")
    contexto_cita: Optional[str] = Field(default=None, description="Contexto en el que se dio la cita.")
    relevancia_cita: Optional[int] = Field(default=None, ge=1, le=10, description="Relevancia de la cita (1-10).")
    hecho_principal_relacionado_id_temporal: Optional[str] = Field(default=None, description="ID temporal_hecho del hecho principal al que se relaciona esta cita.")

class DatoCuantitativoExtraidoItem(PersistenciaBaseModel):
    """
    Representa un dato cuantitativo extraído.
    Referencia: "Documento 1 de Persistencia", sección "datos_cuantitativos_extraidos[]".
    """
    id_temporal_dato: str = Field(description="ID temporal único para este dato.")
    descripcion_dato: str = Field(description="Descripción del dato cuantitativo.")
    valor_dato: Union[float, int, str, None] = Field(default=None, description="El valor numérico o textual del dato.") # Doc: "float | integer | string"
    unidad_dato: Optional[str] = Field(default=None, description="Unidad de medida del dato (ej: 'USD', 'kilogramos', '%').")
    fecha_dato: Optional[str] = Field(default=None, description="Fecha a la que corresponde el dato (formato ISO 8601).")
    contexto_dato: Optional[str] = Field(default=None, description="Contexto del dato cuantitativo.")
    relevancia_dato: Optional[int] = Field(default=None, ge=1, le=10, description="Relevancia del dato (1-10).")
    hecho_principal_relacionado_id_temporal: Optional[str] = Field(default=None, description="ID temporal_hecho del hecho principal al que se relaciona este dato.")
    
    # CAMPOS AGREGADOS (existen en base de datos Supabase pero faltaban en modelo)
    categoria: Optional[str] = Field(default=None, description="Categoría del dato cuantitativo (coincide con columna 'categoria' en DB).")
    tipo_periodo: Optional[str] = Field(default=None, description="Tipo de período al que se refiere el dato (coincide con columna 'tipo_periodo' en DB).")
    tendencia: Optional[str] = Field(default=None, description="Tendencia observada en el dato (coincide con columna 'tendencia' en DB).")
    valor_anterior: Optional[float] = Field(default=None, description="Valor anterior para comparación (coincide con columna 'valor_anterior' en DB).")
    variacion_absoluta: Optional[float] = Field(default=None, description="Variación absoluta respecto al valor anterior (coincide con columna 'variacion_absoluta' en DB).")
    variacion_porcentual: Optional[float] = Field(default=None, description="Variación porcentual respecto al valor anterior (coincide con columna 'variacion_porcentual' en DB).")
    periodo_referencia_inicio: Optional[str] = Field(default=None, description="Fecha de inicio del período de referencia (coincide con columna 'periodo_referencia_inicio' en DB).")
    periodo_referencia_fin: Optional[str] = Field(default=None, description="Fecha de fin del período de referencia (coincide con columna 'periodo_referencia_fin' en DB).")

class RelacionHechosItem(PersistenciaBaseModel):
    """
    Representa una relación entre dos hechos extraídos.
    Referencia: "Documento 1 de Persistencia", sección "relaciones_hechos[]".
    """
    hecho_origen_id_temporal: str = Field(description="ID temporal_hecho del primer hecho en la relación.")
    hecho_destino_id_temporal: str = Field(description="ID temporal_hecho del segundo hecho en la relación.")
    tipo_relacion: str = Field(description="Tipo de relación (ej: 'causa-efecto', 'temporal_secuencial', 'aclaracion').")
    descripcion_relacion: Optional[str] = Field(default=None, description="Descripción de la naturaleza de la relación.")
    direccion_relacion: Optional[str] = Field(default=None, description="Dirección de la relación (ej: 'bidireccional', 'origen_a_destino').")
    fecha_inicio_relacion: Optional[str] = Field(default=None, description="Fecha de inicio de la validez de la relación (formato ISO 8601).")
    fecha_fin_relacion: Optional[str] = Field(default=None, description="Fecha de fin de la validez de la relación (formato ISO 8601).")
    fuerza_relacion: Optional[int] = Field(default=None, ge=1, le=10, description="Fuerza o confianza en la relación (1-10).")

class RelacionEntidadesItem(PersistenciaBaseModel):
    """
    Representa una relación entre dos entidades.
    Referencia: "Documento 1 de Persistencia", sección "relaciones_entidades[]".
    """
    entidad_origen_id_temporal: str = Field(description="ID temporal de la entidad origen.")
    entidad_destino_id_temporal: str = Field(description="ID temporal de la entidad destino.")
    tipo_relacion: str = Field(description="Tipo de relación entre las entidades (ej: 'empleado_de', 'subsidiaria_de', 'aliado_con').")
    descripcion_relacion: Optional[str] = Field(default=None, description="Descripción de la naturaleza de la relación.")
    contexto_relacion: Optional[str] = Field(default=None, description="Contexto en el que se da esta relación.")
    fecha_inicio_relacion: Optional[str] = Field(default=None, description="Fecha de inicio de la validez de la relación (formato ISO 8601).")
    fecha_fin_relacion: Optional[str] = Field(default=None, description="Fecha de fin de la validez de la relación (formato ISO 8601).")
    fuerza_relacion: Optional[int] = Field(default=None, ge=1, le=10, description="Fuerza o confianza en la relación (1-10).")

class ContradiccionDetectadaItem(PersistenciaBaseModel):
    """
    Representa una contradicción detectada entre dos hechos.
    Referencia: "Documento 1 de Persistencia", sección "contradicciones_detectadas[]".
    """
    hecho_principal_id_temporal: str = Field(description="ID temporal_hecho del primer hecho.")
    hecho_contradictorio_id_temporal: str = Field(description="ID temporal_hecho del hecho que lo contradice.")
    tipo_contradiccion: Optional[str] = Field(default=None, description="Tipo de contradicción (ej: 'temporal', 'logica', 'factual').")
    grado_contradiccion: Optional[int] = Field(default=None, ge=1, le=5, description="Grado de la contradicción (1-5).")
    descripcion_contradiccion: Optional[str] = Field(default=None, description="Explicación de la contradicción.")


# --- Modelo Principal para el Payload de `insertar_articulo_completo` ---

class ArticuloPersistenciaPayload(PersistenciaBaseModel):
    """
    Representa el payload JSONB completo para la RPC `insertar_articulo_completo`.
    Referencia: "Documento 1 de Persistencia", sección "2.1.1. Estructura Detallada del Payload p_articulo_data".
    """
    # --- Sección A: Información del Artículo Original ---
    url: Optional[str] = Field(default=None, description="URL original del artículo.")
    storage_path: Optional[str] = Field(default=None, description="Ruta al archivo en Supabase Storage si aplica.")
    fuente_original: Optional[str] = Field(default=None, description="Identificador del scraper o fuente original (ej: nombre del spider).")
    medio: str = Field(description="Nombre del medio de comunicación (ej: \"El País\").")
    medio_url_principal: Optional[str] = Field(default=None, description="URL principal del medio.")
    area_geografica: Optional[str] = Field(default=None, description="Área geográfica donde se publicó el artículo.")
    tipo_medio: Optional[str] = Field(default=None, description="Tipo de medio (ej: 'Diario Digital', 'Agencia de Noticias').")
    titular: str = Field(description="Titular original del artículo.")
    fecha_publicacion: str = Field(description="Fecha de publicación original (formato ISO 8601).")
    autor: Optional[str] = Field(default=None, description="Autor(es) del artículo.")
    idioma_original: Optional[str] = Field(default=None, description="Código de idioma original del artículo (ej: 'es', 'en').")
    seccion: Optional[str] = Field(default=None, description="Sección del medio donde se publicó (ej: 'Política', 'Economía').")
    etiquetas_fuente: Optional[List[str]] = Field(default_factory=list, description="Etiquetas o keywords proporcionadas por la fuente original.")
    es_opinion: Optional[bool] = Field(default=False, description="Indica si el artículo es de opinión.")
    es_oficial: Optional[bool] = Field(default=False, description="Indica si el artículo es una comunicación oficial.")
    contenido_texto_original: str = Field(description="Contenido completo del texto del artículo que fue procesado.")
    contenido_html_original: Optional[str] = Field(default=None, description="Contenido HTML original del artículo.")
    metadata_original: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadatos adicionales del input original.")

    # --- Sección B: Resultados del Procesamiento del Pipeline ---
    resumen_generado_pipeline: Optional[str] = Field(default=None, description="Resumen del artículo generado por el pipeline.")
    palabras_clave_generadas: Optional[List[str]] = Field(default_factory=list, description="Palabras clave extraídas o generadas por el pipeline.")
    sentimiento_general_articulo: Optional[str] = Field(default=None, description="Análisis de sentimiento general del artículo (ej: 'positivo', 'negativo', 'neutral').")
    estado_procesamiento_final_pipeline: str = Field(description="Estado final del procesamiento del artículo en el pipeline (ej: 'completado_ok', 'error_extraccion').")
    version_pipeline_aplicada: Optional[str] = Field(default=None, description="Versión del pipeline que procesó este artículo.")
    fecha_ingesta_sistema: str = Field(description="Fecha y hora de ingesta del artículo en el sistema (formato ISO 8601).")
    fecha_procesamiento_pipeline: str = Field(description="Fecha y hora de finalización del procesamiento por el pipeline (formato ISO 8601).")
    error_detalle_pipeline: Optional[str] = Field(default=None, description="Descripción de errores ocurridos durante el pipeline, si los hubo.")
    embedding_articulo_vector: Optional[List[float]] = Field(default=None, description="Vector de embedding semántico del artículo completo.")

    # --- Sección C: Elementos Estructurados Extraídos ---
    hechos_extraidos: Optional[List[HechoExtraidoItem]] = Field(default_factory=list)
    entidades_autonomas: Optional[List[EntidadAutonomaItem]] = Field(default_factory=list)
    citas_textuales_extraidas: Optional[List[CitaTextualExtraidaItem]] = Field(default_factory=list)
    datos_cuantitativos_extraidos: Optional[List[DatoCuantitativoExtraidoItem]] = Field(default_factory=list)

    # --- Sección D: Relaciones Estructuradas ---
    relaciones_hechos: Optional[List[RelacionHechosItem]] = Field(default_factory=list)
    relaciones_entidades: Optional[List[RelacionEntidadesItem]] = Field(default_factory=list)
    contradicciones_detectadas: Optional[List[ContradiccionDetectadaItem]] = Field(default_factory=list)


# --- Modelo Principal para el Payload de `insertar_fragmento_completo` ---

class FragmentoPersistenciaPayload(PersistenciaBaseModel):
    """
    Representa el payload JSONB para la RPC `insertar_fragmento_completo`.
    Referencia: "Documento 1 de Persistencia", sección "2.2.1. Estructura Detallada del Payload p_fragmento_data".
    El `p_documento_id` se pasa como argumento separado a la RPC.
    """
    # --- Sección A': Información del Fragmento Original ---
    indice_secuencial_fragmento: int = Field(description="El orden numérico de este fragmento dentro del documento extenso.")
    titulo_seccion_fragmento: Optional[str] = Field(default=None, description="Título de la sección a la que pertenece el fragmento.")
    contenido_texto_original_fragmento: str = Field(description="Contenido completo del texto del fragmento que fue procesado.")
    num_pagina_inicio_fragmento: Optional[int] = Field(default=None, description="Número de página donde inicia el fragmento en el documento original.")
    num_pagina_fin_fragmento: Optional[int] = Field(default=None, description="Número de página donde finaliza el fragmento.")

    # --- Sección B: Resultados del Procesamiento del Pipeline (Fragmento) ---
    resumen_generado_fragmento: Optional[str] = Field(default=None, description="Resumen del fragmento generado por el pipeline.")
    estado_procesamiento_final_fragmento: str = Field(description="Estado final del procesamiento del fragmento (ej: 'completado_ok').")
    fecha_procesamiento_pipeline_fragmento: str = Field(description="Fecha y hora de finalización del procesamiento del fragmento (formato ISO 8601).")
    # Se podrían añadir más campos de la Sección B de Artículo si aplican a fragmentos,
    # como palabras_clave_generadas_fragmento, sentimiento_fragmento, embedding_fragmento_vector, etc.
    # El "Documento 1" es menos explícito aquí, se asume analogía.

    # --- Sección C: Elementos Estructurados Extraídos (Análogo a p_articulo_data) ---
    hechos_extraidos: Optional[List[HechoExtraidoItem]] = Field(default_factory=list)
    entidades_autonomas: Optional[List[EntidadAutonomaItem]] = Field(default_factory=list)
    citas_textuales_extraidas: Optional[List[CitaTextualExtraidaItem]] = Field(default_factory=list)
    datos_cuantitativos_extraidos: Optional[List[DatoCuantitativoExtraidoItem]] = Field(default_factory=list)

    # --- Sección D: Relaciones Estructuradas (Análogo a p_articulo_data) ---
    relaciones_hechos: Optional[List[RelacionHechosItem]] = Field(default_factory=list)
    relaciones_entidades: Optional[List[RelacionEntidadesItem]] = Field(default_factory=list)
    contradicciones_detectadas: Optional[List[ContradiccionDetectadaItem]] = Field(default_factory=list)
