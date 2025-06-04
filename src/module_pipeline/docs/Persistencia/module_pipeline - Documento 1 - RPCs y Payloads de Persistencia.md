# Documento 1: RPCs y Payloads de Persistencia del `module_pipeline`

## 1. Introducción a la Persistencia de Datos

La Fase 5 del `module_pipeline` es responsable de la persistencia de los datos procesados. Esta fase toma la información estructurada y enriquecida de las fases anteriores y la almacena de forma permanente en la base de datos Supabase. La interacción principal con la base de datos para la escritura de datos se realiza a través de Funciones de Procedimiento Remoto (RPCs) específicas.

Este documento detalla las RPCs clave utilizadas para la persistencia y la estructura exacta de los payloads JSONB que estas funciones esperan como entrada.

## 2. RPCs Principales y Estructura de Payloads

Las RPCs centrales para la persistencia de datos son `insertar_articulo_completo` para artículos de noticias y `insertar_fragmento_completo` para fragmentos de documentos extensos.

### 2.1. RPC: `insertar_articulo_completo`

*   **Función SQL:** `insertar_articulo_completo(p_articulo_data JSONB)`
*   **Propósito:** Persiste toda la información procesada y extraída de un único artículo de noticias. Esta función es llamada al final del pipeline si el artículo ha pasado todas las fases de procesamiento y validación.
*   **Parámetro Principal:** `p_articulo_data` (tipo `JSONB`)
    *   **Descripción:** Un objeto JSON que encapsula todos los datos del artículo original y los resultados del procesamiento del pipeline. La estructura de este JSONB se deriva de la lógica interna de la RPC y de los datos generados por los prompts del LLM en las fases previas.
    *   **IDs Temporales:** Dentro de este payload, se utilizan "IDs temporales" (ej. `id_temporal_hecho`, `id_temporal_entidad`) para referenciar elementos que aún no tienen un ID asignado por la base de datos. Estos IDs son cruciales para establecer relaciones entre los diferentes elementos extraídos (hechos, entidades, citas) antes de que se les asignen IDs permanentes durante la persistencia.

#### 2.1.1. Estructura Detallada del Payload `p_articulo_data`

A continuación, se desglosa la estructura esperada del objeto `p_articulo_data`. Los campos marcados como "(Opcional)" pueden no estar presentes en todos los casos. El origen de la información (ej. "Fase X", "Input Original") se indica para mayor claridad.

```json
{
    // --- Sección A: Información del Artículo Original (Input Original / Fase 1) ---
    "url": "string (Opcional) - URL original del artículo.",
    "storage_path": "string (Opcional) - Ruta al archivo en Supabase Storage si aplica.",
    "fuente_original": "string (Opcional) - Identificador del scraper o fuente original (ej: nombre del spider).",
    "medio": "string - Nombre del medio de comunicación (ej: \"El País\").",
    "medio_url_principal": "string (Opcional) - URL principal del medio.",
    "pais_publicacion": "string (Opcional) - País donde se publicó el artículo.",
    "tipo_medio": "string (Opcional) - Tipo de medio (ej: 'Diario Digital', 'Agencia de Noticias').",
    "titular": "string - Titular original del artículo.",
    "fecha_publicacion": "timestamp string (YYYY-MM-DDTHH:MM:SSZ) - Fecha de publicación original.",
    "autor": "string (Opcional) - Autor(es) del artículo.",
    "idioma_original": "string (Opcional) - Código de idioma original del artículo (ej: 'es', 'en').",
    "seccion": "string (Opcional) - Sección del medio donde se publicó (ej: 'Política', 'Economía').",
    "etiquetas_fuente": ["string (Opcional)"] ,
    "es_opinion": "boolean (Opcional, default: false) - Indica si el artículo es de opinión.",
    "es_oficial": "boolean (Opcional, default: false) - Indica si el artículo es una comunicación oficial.",
    "contenido_texto_original": "string - Contenido completo del texto del artículo que fue procesado.",
    "contenido_html_original": "string (Opcional) - Contenido HTML original del artículo.",
    "metadata_original": {}, 

    // --- Sección B: Resultados del Procesamiento del Pipeline (Fases 1-4.5) ---
    "resumen_generado": "string (Opcional) - Resumen del artículo generado por el LLM (Fase 2).",
    "categorias_asignadas_ia": ["string (Opcional)"], 
    "puntuacion_relevancia_ia": "float (Opcional) - Puntuación de relevancia asignada por el pipeline (Fase 4.5).",
    "idioma_detectado_ia": "string (Opcional) - Código de idioma detectado por el LLM (Fase 1, ej: 'es').",
    "palabras_clave_ia": ["string (Opcional)"], 
    "sentimiento_articulo": { 
        "etiqueta": "string (Opcional, ej: 'positivo', 'negativo', 'neutral')",
        "puntuacion": "float (Opcional)"
    },
    "estado_procesamiento_final": "string - Estado final del procesamiento del artículo por el pipeline (ej: 'completado_ok', 'error_validacion_datos').",
    "fecha_procesamiento_pipeline": "timestamp string (YYYY-MM-DDTHH:MM:SSZ) - Fecha y hora de finalización del procesamiento.",
    "error_detalle_pipeline": "string (Opcional) - Descripción de errores ocurridos durante el pipeline, si los hubo.",
    "embedding_articulo_vector": "[float (Opcional)]", 

    // --- Sección C: Elementos Estructurados Extraídos (Fase 2, 3, 4) ---
    "hechos_extraidos": [ 
        {
            "id_temporal_hecho": "string - ID temporal único para este hecho dentro del payload.",
            "descripcion_hecho": "string - Descripción del hecho.",
            "fecha_ocurrencia_estimada": "timestamp string (Opcional, YYYY-MM-DDTHH:MM:SSZ) - Fecha estimada de ocurrencia del hecho.",
            "lugar_principal_ocurrencia": "string (Opcional) - Lugar principal donde ocurrió el hecho (podría ser un objeto JSON con más detalle si la BD lo soporta así).",
            "tipo_hecho": "string (Opcional) - Clasificación del tipo de hecho (ej: 'declaracion', 'evento_politico').",
            "relevancia_hecho": "integer (Opcional, 1-10) - Relevancia estimada del hecho.",
            "contexto_adicional_hecho": "string (Opcional) - Contexto adicional sobre el hecho.",
            "detalle_complejo_hecho": {}, 
            "embedding_hecho_vector": "[float (Opcional)]", 
            "entidades_del_hecho": [ 
                {
                    "id_temporal_entidad": "string - ID temporal único para esta entidad dentro del payload (puede repetirse si la misma entidad aparece en múltiples hechos).",
                    "nombre_entidad": "string - Nombre de la entidad.",
                    "tipo_entidad": "string - Tipo de entidad (ej: 'PERSONA', 'ORGANIZACION', 'LUGAR', 'EVENTO', 'PRODUCTO', 'MISCELANEA').",
                    "subtipo_entidad": "string (Opcional) - Subtipo más específico de la entidad.",
                    "relevancia_entidad_en_hecho": "integer (Opcional, 1-10) - Relevancia de la entidad en el contexto específico de este hecho.",
                    "rol_en_hecho": "string (Opcional) - Rol que juega la entidad en este hecho (ej: 'protagonista', 'afectado', 'testigo')."
                }
            ]
        }
    ],
    "entidades_autonomas": [ 
        {
            "id_temporal_entidad": "string - ID temporal único para esta entidad.",
            "nombre_entidad": "string - Nombre de la entidad.",
            "tipo_entidad": "string - Tipo de entidad.",
            "subtipo_entidad": "string (Opcional) - Subtipo de la entidad.",
            "relevancia_entidad_articulo": "integer (Opcional, 1-10) - Relevancia de la entidad en el contexto general del artículo.",
            "metadata_entidad": {}, 
            "embedding_entidad_vector": "[float (Opcional)]" 
        }
    ],
    "citas_textuales_extraidas": [ 
        {
            "id_temporal_cita": "string - ID temporal único para esta cita.",
            "texto_cita": "string - El contenido textual de la cita.",
            "persona_citada": "string (Opcional) - Nombre de la persona/entidad que dijo la cita. Podría referenciar un `id_temporal_entidad`.",
            "cargo_persona_citada": "string (Opcional) - Cargo o rol de la persona citada.",
            "fecha_cita": "timestamp string (Opcional, YYYY-MM-DDTHH:MM:SSZ) - Fecha en que se dijo la cita.",
            "contexto_cita": "string (Opcional) - Contexto en el que se emitió la cita.",
            "relevancia_cita": "integer (Opcional, 1-10) - Relevancia de la cita.",
            "hecho_principal_relacionado_id_temporal": "string (Opcional) - `id_temporal_hecho` del hecho principal al que se relaciona esta cita."
        }
    ],
    "datos_cuantitativos_extraidos": [ 
        {
            "id_temporal_dato": "string - ID temporal único para este dato.",
            "descripcion_dato": "string - Descripción del dato cuantitativo.",
            "valor_dato": "float | integer | string - Valor del dato (flexible según la naturaleza del mismo).",
            "unidad_dato": "string (Opcional) - Unidad de medida del dato (ej: 'USD', '%', 'personas').",
            "fecha_dato": "timestamp string (Opcional, YYYY-MM-DDTHH:MM:SSZ) - Fecha a la que corresponde el dato.",
            "fuente_especifica_dato": "string (Opcional) - Fuente específica del dato si se menciona en el texto.",
            "contexto_dato": "string (Opcional) - Contexto del dato.",
            "relevancia_dato": "integer (Opcional, 1-10) - Relevancia del dato.",
            "hecho_principal_relacionado_id_temporal": "string (Opcional) - `id_temporal_hecho` del hecho principal al que se relaciona este dato."
        }
    ],

    // --- Sección D: Relaciones Estructuradas (Fase 4) ---
    "relaciones_hechos": [ 
        {
            "hecho_origen_id_temporal": "string - `id_temporal_hecho` del primer hecho en la relación.",
            "hecho_destino_id_temporal": "string - `id_temporal_hecho` del segundo hecho en la relación.",
            "tipo_relacion": "string - Tipo de relación (ej: 'causa-efecto', 'secuencia_temporal', 'sub-evento_de').",
            "fuerza_relacion": "integer (Opcional, 1-10) - Fuerza o confianza en la relación.",
            "descripcion_relacion": "string (Opcional) - Descripción adicional de la relación."
        }
    ],
    "relaciones_entidades": [ 
        {
            "entidad_origen_id_temporal": "string - `id_temporal_entidad` de la primera entidad.",
            "entidad_destino_id_temporal": "string - `id_temporal_entidad` de la segunda entidad.",
            "tipo_relacion": "string - Tipo de relación (ej: 'empleado_de', 'miembro_de', 'ubicado_en', 'aliado_con').",
            "descripcion_relacion": "string (Opcional) - Descripción de la relación.",
            "fecha_inicio_relacion": "timestamp string (Opcional, YYYY-MM-DDTHH:MM:SSZ)",
            "fecha_fin_relacion": "timestamp string (Opcional, YYYY-MM-DDTHH:MM:SSZ)",
            "fuerza_relacion": "integer (Opcional, 1-10)"
        }
    ],
    "contradicciones_detectadas": [ 
        {
            "hecho_principal_id_temporal": "string - `id_temporal_hecho` del primer hecho.",
            "hecho_contradictorio_id_temporal": "string - `id_temporal_hecho` del hecho que lo contradice.",
            "tipo_contradiccion": "string (Opcional) - Tipo de contradicción (ej: 'temporal', 'factual').",
            "grado_contradiccion": "integer (Opcional, 1-5) - Grado de la contradicción.",
            "descripcion_contradiccion": "string (Opcional) - Explicación de la contradicción."
        }
    ]
}

2.1.2. Ejemplo de Payload p_articulo_data (Simplificado)

{
    "url": "https://www.ejemplonews.com/articulo/123",
    "medio": "Ejemplo News",
    "titular": "Gran Avance Científico Anunciado Hoy",
    "fecha_publicacion": "2024-05-15T10:00:00Z",
    "contenido_texto_original": "Científicos del Instituto X han anunciado hoy un descubrimiento revolucionario...",
    "resumen_generado": "Un nuevo descubrimiento por el Instituto X podría cambiar la tecnología.",
    "categorias_asignadas_ia": ["ciencia", "tecnologia"],
    "idioma_detectado_ia": "es",
    "palabras_clave_ia": ["descubrimiento", "instituto x", "tecnologia"],
    "estado_procesamiento_final": "completado_ok",
    "fecha_procesamiento_pipeline": "2024-05-15T12:30:00Z",
    "hechos_extraidos": [
        {
            "id_temporal_hecho": "hecho_1",
            "descripcion_hecho": "Científicos del Instituto X anuncian descubrimiento revolucionario.",
            "fecha_ocurrencia_estimada": "2024-05-15T00:00:00Z",
            "tipo_hecho": "anuncio_cientifico",
            "entidades_del_hecho": [
                {
                    "id_temporal_entidad": "ent_1",
                    "nombre_entidad": "Instituto X",
                    "tipo_entidad": "ORGANIZACION",
                    "rol_en_hecho": "protagonista"
                }
            ]
        }
    ],
    "entidades_autonomas": [
        {
            "id_temporal_entidad": "ent_1",
            "nombre_entidad": "Instituto X",
            "tipo_entidad": "ORGANIZACION",
            "relevancia_entidad_articulo": 9
        }
    ]
}

2.2. RPC: insertar_fragmento_completo
+ Función SQL: insertar_fragmento_completo(p_fragmento_data JSONB, p_documento_id BIGINT)
+ Propósito: Persiste toda la información procesada y extraída de un fragmento de un documento extenso (como un libro o un informe largo).
+ Parámetros:
    + p_fragmento_data (tipo JSONB):
        + Descripción: Similar en estructura al p_articulo_data, pero adaptado para un fragmento. Contendrá información específica del fragmento (como su índice secuencial, contenido original del fragmento) y luego los mismos tipos de elementos estructurados (hechos_extraidos, entidades_autonomas, citas_textuales_extraidas, etc.) que se hayan extraído del contenido de ese fragmento en particular.
    + Campos Adicionales/Diferentes esperados en p_fragmento_data (respecto a p_articulo_data):
        + indice_secuencial_fragmento: "integer - El orden numérico de este fragmento dentro del documento extenso."
        + titulo_seccion_fragmento: "string (Opcional) - Si el fragmento corresponde a una sección con título."
        + contenido_texto_original_fragmento: "string - El texto del fragmento que fue procesado."
    + p_documento_id (tipo BIGINT):
        + Descripción: El ID (clave primaria de la tabla documentos_extensos) del documento maestro al que pertenece este fragmento. Este ID es crucial para vincular el fragmento y sus datos extraídos con el documento extenso correcto.

2.2.1. Estructura Detallada del Payload p_fragmento_data
La estructura interna de p_fragmento_data para las secciones B (Resultados del Procesamiento), C (Elementos Estructurados Extraídos) y D (Relaciones Estructuradas) es análoga a la de p_articulo_data. La principal diferencia radica en la sección de información original, que se enfoca en el fragmento:

{
    // --- Sección A': Información del Fragmento Original (Input Original / Fase 1) ---
    "indice_secuencial_fragmento": "integer - El orden numérico de este fragmento dentro del documento extenso.",
    "titulo_seccion_fragmento": "string (Opcional) - Título de la sección a la que pertenece el fragmento.",
    "contenido_texto_original_fragmento": "string - Contenido completo del texto del fragmento que fue procesado.",
    "num_pagina_inicio_fragmento": "integer (Opcional) - Número de página donde inicia el fragmento en el documento original.",
    "num_pagina_fin_fragmento": "integer (Opcional) - Número de página donde finaliza el fragmento.",

    // --- Sección B: Resultados del Procesamiento del Pipeline (Análogo a p_articulo_data) ---
    "resumen_generado_fragmento": "string (Opcional)",
    "estado_procesamiento_final_fragmento": "string",
    "fecha_procesamiento_pipeline_fragmento": "timestamp string",

    // --- Sección C: Elementos Estructurados Extraídos (Análogo a p_articulo_data) ---
    "hechos_extraidos": [ /* ... */ ],
    "entidades_autonomas": [ /* ... */ ],
    "citas_textuales_extraidas": [ /* ... */ ],
    "datos_cuantitativos_extraidos": [ /* ... */ ],

    // --- Sección D: Relaciones Estructuradas (Análogo a p_articulo_data) ---
    "relaciones_hechos": [ /* ... */ ],
    "relaciones_entidades": [ /* ... */ ],
    "contradicciones_detectadas": [ /* ... */ ]
}

2.2.2. Ejemplo de Payload p_fragmento_data (Simplificado)

{
    "indice_secuencial_fragmento": 5,
    "titulo_seccion_fragmento": "Capítulo 3: Resultados Experimentales",
    "contenido_texto_original_fragmento": "Los datos recopilados en la Tabla 3.1 muestran un incremento...",
    "estado_procesamiento_final_fragmento": "completado_ok",
    "fecha_procesamiento_pipeline_fragmento": "2024-05-16T14:00:00Z",
    "hechos_extraidos": [
        {
            "id_temporal_hecho": "frag5_hecho_1",
            "descripcion_hecho": "Datos de Tabla 3.1 muestran incremento.",
            "tipo_hecho": "presentacion_resultado",
            "entidades_del_hecho": [
                {
                    "id_temporal_entidad": "frag5_ent_1",
                    "nombre_entidad": "Tabla 3.1",
                    "tipo_entidad": "DATO_ESTRUCTURADO"
                }
            ]
        }
    ]
}