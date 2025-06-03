### 0.1. `module_pipeline` (Pipeline de Procesamiento)

**1. Descripción general**

Este módulo es el núcleo de análisis e inteligencia de la Máquina de Noticias. Recibe contenido textual (artículos de noticias o fragmentos de documentos extensos) y lo procesa a través de una secuencia de fases utilizando un modelo de lenguaje grande (LLM). Su objetivo es transformar texto no estructurado en información estructurada y conectada (hechos, entidades, citas, datos, relaciones), validarla, normalizarla y persistirla de forma atómica en la base de datos central. Actúa como el motor de extracción y estructuración de conocimiento del sistema.

**2. Input (entradas)**

*   **Tipo de entrada:**
    1.  Datos de artículos (`ArticuloInItem`): Recibidos del `module_connector`.
    2.  Datos de fragmentos de documentos: Recibidos del `module_ingestion_engine`.
*   **Formato:**
    1.  Para artículos: Objeto JSON dentro de una solicitud HTTP POST, con la estructura `{"articulo": {...}}`.
    2.  Para fragmentos: Diccionario Python pasado como argumento a una función interna (actualmente `_procesar_fragmento` en `controller.py`) o potencialmente un mensaje en una cola si se desacopla. La estructura incluye el contenido del fragmento y metadatos del documento original (`documento_id`, `fragmento_id`, título, tipo, etc.).
*   **Fuente:**
    1.  `module_connector` (para artículos).
    2.  `module_ingestion_engine` (para fragmentos de documentos).
*   **Frecuencia o modo de recepción:** Bajo demanda. Se activa cuando el `module_connector` envía un artículo o cuando el `module_ingestion_engine` envía un fragmento para procesar. El procesamiento interno puede ser gestionado por una cola asíncrona (`asyncio.Queue` en la implementación actual).
*   **Interfaz de comunicación (protocolo, método, cómo se reciben los datos):**
    1.  Para artículos: API HTTP (POST al endpoint `/procesar`).
    2.  Para fragmentos: Llamada a función asíncrona interna (podría cambiar a cola de mensajes).

### 2.1. Entrada desde `module_connector`: `ArticuloInItem`

El `module_pipeline` recibe los artículos de noticias desde el `module_connector`. La estructura de datos para cada artículo es un objeto JSON que se corresponde con el modelo Pydantic `ArticuloInItem`, definido en el `module_connector`. El `module_pipeline` debe estar preparado para recibir todos los campos definidos en este modelo.

**Definición del Modelo Pydantic `ArticuloInItem` (según `module_connector`):**

(Nota: La siguiente estructura es una representación del modelo Pydantic `ArticuloInItem` tal como se define en `module_connector/src/models.py`. El `module_pipeline` recibe objetos que se adhieren a esta estructura.)

```python
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, validator # Asumiendo que BaseModel y validator son relevantes aquí

class ArticuloInItem(BaseModel):
    # --- Campos Principales ---
    url: Optional[str] = None
    storage_path: Optional[str] = None
    fuente: Optional[str] = None
    medio: str  # Requerido por el modelo Pydantic de module_connector
    medio_url_principal: Optional[str] = None
    pais_publicacion: str  # Requerido por el modelo Pydantic de module_connector
    tipo_medio: str  # Requerido por el modelo Pydantic de module_connector
    titular: str  # Requerido por el modelo Pydantic de module_connector
    fecha_publicacion: datetime  # Requerido por el modelo Pydantic de module_connector
    autor: Optional[str] = None
    idioma: Optional[str] = None
    seccion: Optional[str] = None
    etiquetas_fuente: Optional[List[str]] = None
    es_opinion: Optional[bool] = False
    es_oficial: Optional[bool] = False
    
    # --- Campos que pueden ser generados por etapas previas o por el pipeline ---
    resumen: Optional[str] = None
    categorias_asignadas: Optional[List[str]] = None
    puntuacion_relevancia: Optional[float] = None
    
    # --- Campos de Control ---
    fecha_recopilacion: Optional[datetime] = None
    fecha_procesamiento: Optional[datetime] = None
    estado_procesamiento: Optional[str] = "pendiente_connector" # Valor por defecto en el modelo original
    error_detalle: Optional[str] = None
    
    # --- Contenido del Artículo ---
    contenido_texto: str  # Requerido por el modelo Pydantic de module_connector
    contenido_html: Optional[str] = None
    
    # --- Metadatos Adicionales ---
    metadata: Optional[Dict[str, Any]] = None

    # Nota: Los validadores @validator y la clase Config interna del modelo original 
    # en module_connector/src/models.py definen el comportamiento de validación
    # y serialización para el module_connector. El module_pipeline recibe el
    # objeto JSON resultante. La opción `extra = "allow"` en la Config original
    # indica que el JSON recibido podría contener campos adicionales no listados aquí,
    # los cuales el module_pipeline generalmente ignorará si no los espera explícitamente.

    class Config: # Ejemplo de cómo podría estar configurado en el origen
        extra = "allow"
        # schema_extra = { ... } # El schema_extra original contiene un ejemplo detallado
```

**Campos Requeridos por el Modelo `ArticuloInItem` de `module_connector`:**

El modelo `ArticuloInItem` definido en `module_connector` especifica los siguientes campos como no opcionales y sin valor por defecto, por lo que siempre deben estar presentes en el objeto JSON que recibe el `module_pipeline`:

*   `medio: str`
*   `pais_publicacion: str`
*   `tipo_medio: str`
*   `titular: str`
*   `fecha_publicacion: datetime`
*   `contenido_texto: str`

El `module_pipeline` debe verificar la presencia y validez de estos campos al inicio de su procesamiento.

**Interacción del `module_pipeline` con los Campos de `ArticuloInItem`:**

*   **Campos de Entrada Primaria:** El `module_pipeline` utilizará principalmente `url`, `fuente`, `medio`, `medio_url_principal`, `pais_publicacion`, `tipo_medio`, `titular`, `fecha_publicacion`, `autor`, `idioma`, `seccion`, `etiquetas_fuente`, `es_opinion`, `es_oficial`, `contenido_texto`, `contenido_html`, y `metadata` como la base para su análisis y extracción de información.
*   **Campos Generados/Actualizados por `module_pipeline`:**
    *   `resumen`: Este campo será generado por la Fase 2 del `module_pipeline`. Cualquier valor de entrada en este campo será sobrescrito.
    *   `categorias_asignadas`: Este campo será generado por la Fase 2 del `module_pipeline`. Cualquier valor de entrada será sobrescrito.
    *   `puntuacion_relevancia`: Este campo será generado por la Fase 4.5 del `module_pipeline`. Cualquier valor de entrada será sobrescrito.
    *   `fecha_procesamiento`: El `module_pipeline` establecerá este campo al finalizar su procesamiento completo del artículo.
    *   `estado_procesamiento`: El `module_pipeline` actualizará este campo para reflejar el estado del artículo a medida que avanza por las fases internas (ej. "procesando_fase1", "completado", "error_fase3").
    *   `error_detalle`: Si ocurre un error durante el procesamiento en el `module_pipeline`, este campo se utilizará para registrar los detalles del error.

**Ejemplo de Objeto JSON `ArticuloInItem` (como lo recibe el `module_pipeline`):**

(Este ejemplo se basa en el `schema_extra` del modelo `ArticuloInItem` en `module_connector`, mostrando la estructura completa que el pipeline podría recibir.)

```json
{
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
    "es_opinion": false,
    "es_oficial": false,
    "resumen": "Este es un resumen que podría venir del connector, pero el pipeline lo regenerará.",
    "categorias_asignadas": ["categoría_del_connector"],
    "puntuacion_relevancia": 7.5,
    "fecha_recopilacion": "2023-10-26T10:05:00Z",
    "fecha_procesamiento": null,
    "estado_procesamiento": "pendiente_pipeline", 
    "error_detalle": null,
    "contenido_texto": "Este es el contenido completo en texto plano del artículo de ejemplo que será procesado por el module_pipeline...",
    "contenido_html": "<html><body><h1>Titular de Ejemplo</h1><p>Este es el contenido HTML original...</p></body></html>",
    "metadata": {
        "palabras_clave_seo": ["ejemplo", "noticia", "desarrollo"],
        "fuente_original_id": "ext-789xyz"
    }
}
```

**Notas para el Desarrollador del `module_pipeline`:**
*   El `module_pipeline` debe estar preparado para manejar la estructura completa de `ArticuloInItem` tal como la define el `module_connector`.
*   La validación de los campos requeridos por el modelo Pydantic original ya habrá sido realizada por el `module_connector` antes de enviar los datos. Sin embargo, es una buena práctica que el `module_pipeline` también verifique la presencia de los campos que considera indispensables para su propio funcionamiento.
*   El `module_pipeline` tiene la responsabilidad de generar o actualizar los campos `resumen`, `categorias_asignadas`, `puntuacion_relevancia`, `fecha_procesamiento`, `estado_procesamiento` y `error_detalle` según su lógica interna.


### 2.2. Entrada desde `module_ingestion_engine`: `FragmentoProcesableItem` (Estructura Inferida)

El `module_pipeline` también está diseñado para procesar fragmentos de documentos extensos (como informes, libros, etc.) que son gestionados y segmentados por el `module_ingestion_engine`.

**Nota Importante:** La siguiente estructura, denominada `FragmentoProcesableItem`, es una **definición inferida** basada en la documentación actual del `module_ingestion_engine`. Dado que `module_ingestion_engine` puede estar aún en desarrollo o su interfaz podría evolucionar (especialmente si se desacopla como un microservicio independiente), esta estructura debe considerarse una propuesta bien fundamentada, diseñada para ser lo más completa y adaptable posible. El `module_pipeline` deberá ajustarse a la estructura final que provea `module_ingestion_engine`.

El objetivo de esta estructura es proporcionar al `module_pipeline` no solo el texto del fragmento, sino también todo el contexto necesario sobre el documento original del que proviene.

**Definición del Modelo Pydantic Inferido `FragmentoProcesableItem`:**

```python
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel # Asumiendo BaseModel

class FragmentoProcesableItem(BaseModel):
    # --- Identificadores Clave ---
    documento_id: str  # ID único del documento original en la tabla `documentos_extensos`. **Esencial.**
    fragmento_id: str  # ID único del fragmento en la tabla `fragmentos_extensos`. **Esencial.**

    # --- Contenido del Fragmento ---
    texto_fragmento: str  # El contenido textual del fragmento a procesar. **Esencial.**
    numero_fragmento: int  # Número secuencial del fragmento dentro del documento (ej. 1, 2, 3...). **Esencial.**
    total_fragmentos: int  # Número total de fragmentos generados para el documento original. **Esencial.**
    offset_inicio_fragmento: Optional[int] = None # Posición de inicio del fragmento en el texto original (en caracteres o tokens).
    offset_fin_fragmento: Optional[int] = None   # Posición de fin del fragmento en el texto original.

    # --- Metadatos Heredados del Documento Original ---
    # Estos campos proporcionan contexto crucial sobre el origen del fragmento.
    titulo_documento_original: Optional[str] = None
    tipo_documento_original: Optional[str] = None # Ej: "informe_anual", "libro_tecnico", "articulo_investigacion", "ley_decreto"
    fuente_documento_original: Optional[str] = None # Ej: "Organización Mundial de la Salud", "Libro 'Inteligencia Artificial Avanzada'"
    autor_documento_original: Optional[str] = None # Puede ser una lista de autores separada por comas o un campo JSON.
    fecha_publicacion_documento_original: Optional[datetime] = None
    idioma_documento_original: Optional[str] = None # Ej: "es", "en"
    storage_path_documento_original: Optional[str] = None # Ruta en Supabase Storage del archivo original completo.
    url_documento_original: Optional[str] = None # Si el documento original tiene una URL de referencia.
    metadata_documento_original: Optional[Dict[str, Any]] = None # Para otros metadatos específicos del documento (ej. ISBN, DOI, editorial, palabras clave originales).

    # --- Campos de Control para el Procesamiento del Fragmento ---
    fecha_ingesta_fragmento: datetime # Timestamp de cuándo el fragmento fue preparado y enviado al pipeline. **Esencial.**
    estado_procesamiento_fragmento: str = "pendiente_pipeline" # Estado inicial para el pipeline.
    # El pipeline actualizará este estado (ej. "procesando_fase1_fragmento", "completado_fragmento", "error_fragmento").
    error_detalle_fragmento: Optional[str] = None # Para registrar errores específicos del procesamiento de este fragmento.
    
    class Config:
        extra = "allow" # Para flexibilidad si `module_ingestion_engine` envía campos adicionales.
```

**Campos Esenciales para el `module_pipeline` (inferidos):**

Para que el `module_pipeline` pueda procesar un fragmento de manera significativa y vincularlo correctamente, los siguientes campos se consideran esenciales:

*   `documento_id`
*   `fragmento_id`
*   `texto_fragmento`
*   `numero_fragmento`
*   `total_fragmentos`
*   `fecha_ingesta_fragmento`

La ausencia de estos campos dificultaría o impediría el procesamiento y la correcta atribución de la información extraída.

**Interacción del `module_pipeline` con los Campos de `FragmentoProcesableItem`:**

*   El `module_pipeline` utilizará `texto_fragmento` como la entrada principal para sus fases de análisis (extracción de hechos, entidades, etc.).
*   Los identificadores (`documento_id`, `fragmento_id`) y los metadatos del documento original (`titulo_documento_original`, `tipo_documento_original`, etc.) serán cruciales para:
    *   Contextualizar la información extraída.
    *   Permitir la vinculación de los hechos y entidades tanto al fragmento específico como al documento maestro en la base de datos (Fase 5: Persistencia).
    *   Posibilitar análisis que consideren el documento completo a través de sus fragmentos.
*   Los campos `estado_procesamiento_fragmento` y `error_detalle_fragmento` serán gestionados por el `module_pipeline` para rastrear el progreso y los posibles problemas en el procesamiento de cada fragmento individual.
*   Campos como `resumen_fragmento` (si se decidiera generar resúmenes por fragmento), `categorias_fragmento`, `puntuacion_relevancia_fragmento` serían generados y gestionados internamente por el `module_pipeline`, de manera análoga a como se hace con `ArticuloInItem`.

**Ejemplo de Objeto JSON `FragmentoProcesableItem` (inferido):**

```json
{
    "documento_id": "doc_xyz_789",
    "fragmento_id": "frag_xyz_789_part_002",
    "texto_fragmento": "Este es el segundo fragmento del documento extenso. Contiene información detallada sobre las implicaciones económicas de la nueva regulación propuesta. Se espera que el pipeline extraiga los datos cuantitativos y las entidades relevantes mencionadas aquí.",
    "numero_fragmento": 2,
    "total_fragmentos": 15,
    "offset_inicio_fragmento": 4096,
    "offset_fin_fragmento": 8192,
    "titulo_documento_original": "Análisis Exhaustivo de la Nueva Regulación Económica Global",
    "tipo_documento_original": "informe_investigacion",
    "fuente_documento_original": "Instituto Internacional de Estudios Económicos",
    "autor_documento_original": "Dra. Elena Silva, Dr. Juan Pérez",
    "fecha_publicacion_documento_original": "2023-09-15T00:00:00Z",
    "idioma_documento_original": "es",
    "storage_path_documento_original": "/documentos_extensos/2023/informe_regulacion_global.pdf",
    "url_documento_original": "https://iiee.org/informes/regulacion_global_2023",
    "metadata_documento_original": {
        "isbn": "978-3-16-148410-0",
        "palabras_clave_fuente": ["economía global", "regulación", "impacto financiero"],
        "departamento_origen": "Investigación Macroeconómica"
    },
    "fecha_ingesta_fragmento": "2023-10-27T14:30:00Z",
    "estado_procesamiento_fragmento": "pendiente_pipeline",
    "error_detalle_fragmento": null
}
```

**Notas para el Desarrollador del `module_pipeline`:**
*   Esta estructura es una propuesta. La implementación final dependerá de la salida real del `module_ingestion_engine`.
*   El `module_pipeline` debe ser capaz de procesar fragmentos individualmente, pero también de utilizar la información contextual del documento original para enriquecer el análisis.
*   La persistencia de los datos extraídos de un fragmento deberá referenciar tanto al `fragmento_id` como al `documento_id`.
*   Se debe considerar cómo se manejarán los campos que son resultado del procesamiento del pipeline (como resúmenes, categorías, relevancia) a nivel de fragmento y si/cómo se agregan a nivel de documento. Esto se definirá en la sección de "Salidas" y "Estructuras de Datos Internas".


**3. Output (salidas)**

*   **Tipo de salida:**
    1.  Datos estructurados persistidos en la base de datos.
    2.  Registro de estado del procesamiento (éxito, error, descartado) en la tabla `articulos` o `documentos_extensos`.
    3.  Registro de errores persistentes en `articulos_error_persistente`.
    4.  Registros de posibles duplicados en `posibles_duplicados_hechos`.
    5.  Actualización de métricas en `system_status`.
    6.  Respuesta HTTP a la llamada API inicial (para el endpoint `/procesar`).
*   **Formato:**
    1.  Registros en tablas PostgreSQL.
    2.  Campos actualizados en tablas PostgreSQL.
    3.  Registros en tablas PostgreSQL.
    4.  Registros en tablas PostgreSQL.
    5.  Campos JSONB actualizados en `system_status`.
    6.  Respuesta JSON (ej. `{"estado": "aceptado", ...}`).
*   **Destino:**
    1.  Base de Datos (Supabase/PostgreSQL) - Tablas: `hechos`, `entidades`, `citas_textuales`, `datos_cuantitativos`, `hecho_entidad`, `hecho_articulo`, `hecho_relacionado`, `entidad_relacion`, `contradicciones`, `cache_entidades` (indirectamente vía trigger).
    2.  Base de Datos (Supabase/PostgreSQL) - Tablas: `articulos`, `documentos_extensos`.
    3.  Base de Datos (Supabase/PostgreSQL) - Tabla: `articulos_error_persistente`.
    4.  Base de Datos (Supabase/PostgreSQL) - Tabla: `posibles_duplicados_hechos`.
    5.  Base de Datos (Supabase/PostgreSQL) - Tabla: `system_status`.
    6.  `module_connector` o el iniciador de la solicitud API.
*   **Frecuencia o modo de entrega:** Las salidas a la base de datos ocurren al final del procesamiento de cada artículo/fragmento (Fase 5). La respuesta API es inmediata tras la recepción (para el endpoint asíncrono `/procesar`).
*   **Interfaz de comunicación (protocolo, método, cómo se envían los datos):**
    1-5: Interacción con la Base de Datos (Supabase/PostgreSQL) mediante la biblioteca `supabase-py` y llamadas a funciones RPC SQL.
    6: Respuesta HTTP (JSON).

**4. Flujo de procesamiento interno**

El procesamiento se divide en fases secuenciales. Cada fase toma la salida de la anterior como entrada:

1. **Fase 1: Preprocesamiento y Triaje (ejecutar_fase_1)**
    
    - **Objetivo:** Limpiar el texto, detectar idioma, traducir si es necesario y evaluar la relevancia inicial (solo para artículos completos, los fragmentos siempre se procesan).
        
    - **Entrada:** Datos del artículo o fragmento.
        
    - **Salida:** Decisión de procesar/descartar, texto limpio/traducido (contenido_procesable), evaluación inicial (puntuación, tipo).
        
    - **Interacciones:** LLM Groq (para evaluación y traducción), spaCy (opcional, para prefiltrado).
        
    - **Prompt:** [[8 de mayo/La Máquina 2/Prompts/Prompt_1_ filtrado]]
        
2. **Fase 2: Extracción de Elementos Básicos (ejecutar_fase_2)**
    
    - **Objetivo:** Identificar y extraer los hechos principales y las entidades mencionadas en el texto.
        
    - **Entrada:** Texto procesable de Fase 1, metadatos del artículo/documento.
        
    - **Salida:** Lista de HechoBase y EntidadBase con IDs temporales. (Nota: En esta fase, el LLM podría intentar asignar una importancia preliminar al hecho, pero esta será refinada en la Fase 4.5).
        
    - **Interacciones:** LLM Groq.
        
    - **Prompt:** [[8 de mayo/La Máquina 2/Prompts/Prompt_2_elementos_basicos]]
        
3. **Fase 3: Extracción de Citas y Datos Cuantitativos (ejecutar_fase_3)**
    
    - **Objetivo:** Extraer citas textuales directas atribuidas a entidades y datos numéricos estructurados.
        
    - **Entrada:** Texto procesable, salida de Fase 2 (hechos y entidades con IDs temporales).
        
    - **Salida:** Lista de CitaTextual y DatosCuantitativos referenciando IDs temporales de hechos/entidades. Se añade articulo_id o documento_id/fragmento_id.
        
    - **Interacciones:** LLM Groq.
        
    - **Prompt:** [[8 de mayo/La Máquina 2/Prompts/Prompt_3_citas_datos]]
        
4. **Fase 4: Normalización, Vinculación y Relaciones (ejecutar_fase_4)**
    
    - **Objetivo:** Consolidar la información, vincular entidades a la base de datos, extraer relaciones entre elementos.
        
    - **Entrada:** Salidas de Fase 2 y Fase 3, contexto del artículo/fragmento.
        
    - **Salida:** Diccionario ResultadoFase4 conteniendo:
        
        - hechos: Hechos formateados (HechoProcesado) con fechas TSTZRANGE. (Nota: La importancia aquí es aún la preliminar de Fase 2).
            
        - entidades: Entidades normalizadas (EntidadProcesada) con db_id si existen o marcadas como es_nueva.
            
        - citas, datos: Listas de citas y datos (sin cambios desde Fase 3).
            
        - relaciones: Estructura Relaciones (hecho-entidad, hecho-hecho, entidad-entidad, contradicciones) usando IDs temporales.
            

            
    - **Interacciones:**
        
        - Base de Datos (tabla cache_entidades y RPC buscar_entidad_similar para normalización de entidades).
            
        - Base de Datos (RPC  para consultas especializadas).
            
        - LLM Groq (para extraer relaciones y contradicciones).
            
    - **Prompt:** [[8 de mayo/La Máquina 2/Prompts/Prompt_4_relaciones]]
        
5. **Fase 4.5: Evaluación de Importancia Contextual
    
    - **Objetivo:** Asignar un valor de importancia (escala 1-10) al hecho procesado, considerando no solo sus características intrínsecas sino también el contexto de tendencias informativas actual.
        
    - **Entrada:** Hechos procesados de la Fase 4 (con su importancia preliminar si fue asignada), metadatos del artículo/documento.
        
    - **Proceso:**
        
        1. Esta fase se activa después de la extracción y normalización básica del hecho.
            
        2. Consulta la tabla tendencias_contexto_diario para obtener el registro de contexto de tendencias correspondiente a la fecha de procesamiento del artículo/fragmento.
            
        3. Utiliza un modelo de Machine Learning clásico (previamente entrenado y versionado por el script importancia_model_trainer.py de la IA Nocturna).
            
        4. El modelo de ML toma como entrada un conjunto de características (features):
            
            - **Características intrínsecas del hecho:** tipo de hecho, país(es) asociados, número y tipo de entidades involucradas, si es un evento futuro, longitud del contenido textual, etc. La importancia preliminar asignada en Fase 2 puede ser una de estas características.
            - **Características contextuales (derivadas de tendencias_contexto_diario):** relevancia actual de las temáticas del hecho, si las entidades principales del hecho están marcadas como 'calientes' o relevantes recientemente, si el hecho se relaciona con eventos próximos de alta prioridad, si se alinea con hilos narrativos actualmente activos y con alta relevancia editorial, etc.
                
        5. El modelo predice el valor de importancia para el hecho.
            
    - **Salida:** Hechos con el campo importancia actualizado por el modelo de ML. Este valor de importancia se pasa a la Fase 5 para ser insertado en el campo hechos.importancia. Adicionalmente, este valor se registrará como importancia_asignada_sistema en la tabla feedback_importancia_hechos durante la persistencia en Fase 5.
        
    - **Interacciones:** Base de Datos (lectura de tendencias_contexto_diario), Modelo de ML (carga y predicción).
        
6. **Fase 5: Ensamblaje Final y Persistencia Atómica (ejecutar_fase_5)**
    
    - **Objetivo:** Ensamblar todos los datos procesados en el formato correcto y persistirlos en la base de datos de forma atómica usando una función RPC.
        
    - **Entrada:** Datos del artículo/fragmento original, salida completa de Fase 4 y Fase 4.5 (incluyendo la importancia finalizada del hecho).
        
    - **Proceso:**
        
        1. Se preparan los datos del hecho, incluyendo el campo importancia determinado en la Fase 4.5.
            
        2. Para la inserción en la tabla hechos, se inicializa evaluacion_editorial a 'pendiente_revision_editorial' y consenso_fuentes a 'pendiente_analisis_fuentes' (CP-005). Los campos confiabilidad y menciones_contradictorias ya no se insertan.
            
        3. Se llama a la RPC de base de datos (insertar_articulo_completo o insertar_fragmento_completo).
            
        4. Dentro de la RPC, además de insertar el hecho y sus elementos relacionados, se realiza una inserción en la tabla feedback_importancia_hechos, registrando el hecho_id y la importancia_asignada_sistema (que es el valor de importancia calculado en la Fase 4.5) (CP-004).
            
    - **Salida:** Estado de la persistencia (éxito/error), contadores de elementos insertados/procesados. Actualización del estado del artículo/documento en la BD. Registro de errores persistentes si falla.
        
    - **Interacciones:** Base de Datos (llamada a RPC insertar_articulo_completo o insertar_fragmento_completo).

**5. Herramientas y tecnologías utilizadas**

*   **Lenguajes de programación:** Python (se recomienda versión 3.8 o superior, especialmente para compatibilidad con Groq SDK).
*   **Frameworks o librerías:**
    *   **FastAPI:** `0.115.12` (para la API web). Context7 ID: `/fastapi/fastapi`.
    *   **Uvicorn:** `0.34.3` (servidor ASGI, usado con `[standard]` para dependencias opcionales).
    *   **Groq Python SDK (`groq`):** `0.9.0` (interacción con la API de Groq, requiere Python 3.8+). Context7 ID: `/groq/groq-python`.
    *   **Supabase Python SDK (`supabase`):** `2.15.2` (interacción con Supabase DB y Storage). Context7 ID: `/supabase/supabase-py`.
    *   **Pydantic:** `2.11.5` (validación de datos y configuración, junto con Pydantic-Settings). Context7 ID: `/pydantic/pydantic`.
    *   **Loguru:** `0.7.3` (logging). Context7 ID: `/emilepetrone/loguru`.
    *   **python-dotenv:** `1.1.0` (carga de variables de entorno desde archivos `.env`).
    *   **spaCy:** `3.8.7` (opcional, para filtrado en Fase 1 y otras tareas NLP. Requiere descarga de modelos, ej: `python -m spacy download en_core_web_sm`). Context7 ID: `/explosion/spaCy`.
    *   **json-repair-llm:** `0.2.0` (para reparar JSON malformado proveniente de LLMs).
    *   `asyncio` (para procesamiento asíncrono y gestión de cola/workers).
    *   `tenacity` (para reintentos en llamadas a Groq).
    *   `langdetect` (detección de idioma).
    *   `tiktoken` (opcional, usado por `doc_extensos_processor.py` para segmentación).
    *   `sentry-sdk` (opcional, para monitorización de errores).
*   **Otras herramientas relevantes:** Docker (para despliegue), PostgreSQL (base de datos subyacente), pgvector (extensión para embeddings), pg_trgm (extensión para similitud de texto).

**6. Dependencias externas**

*   **Otros módulos:**
    *   `module_connector`: Proporciona la entrada de artículos.
    *   `module_ingestion_engine`: Proporciona la entrada de fragmentos de documentos y realiza la segmentación.
    *   Base de Datos (Supabase/PostgreSQL): Lee (`cache_entidades`, búsqueda de duplicados) de la "Memoria Superficial" y "Memoria Relacional", y escribe en la "Memoria Relacional" (todas las tablas de datos estructurados, estado de artículos/documentos, errores, métricas).
*   **Servicios externos:**
    *   Groq API (para el procesamiento LLM en Fases 1, 2, 3, 4).
    *   Sentry (opcional, para monitorización de errores).
*   **Bases de datos:** PostgreSQL (gestionada por Supabase).

**7. Posibles errores o riesgos**

*   **Fase 1 (Triaje/Preproc):**
    *   Descarte incorrecto de artículos relevantes o procesamiento de irrelevantes.
    *   Errores en detección de idioma o traducción fallida.
    *   Fallo en la evaluación de relevancia por parte del LLM.
*   **Fase 2/3/4 (LLM):**
    *   Errores de la API de Groq (timeouts, rate limits, errores internos).
    *   Respuestas del LLM vacías, incompletas o en formato JSON inválido.
    *   Fallos en la limpieza/parseo del JSON (`json_cleaner`).
    *   Errores de validación Pydantic si el LLM no sigue la estructura esperada.
    *   Extracción de información incorrecta o incompleta por el LLM.
*   **Fase 4 (Normalización/Vinculación):**
    *   Errores al consultar `cache_entidades` o RPCs de búsqueda en la BD.
    *   Identificación incorrecta de entidades existentes (falsos positivos/negativos).
    *   Fallo en la detección de posibles duplicados.
*   **Fase 5 (Persistencia):**
    *   Errores en la ejecución de la función RPC en la base de datos (constraints violados, timeouts, lógica interna de la RPC).
    *   Fallo al registrar errores persistentes.
*   **Generales:**
    *   **Cuello de botella:** La velocidad de procesamiento depende de la API de Groq y del número de workers. Una avalancha de artículos podría llenar la cola.
    *   **Consumo de API:** Alto consumo de tokens/créditos de la API de Groq.
    *   **Errores no controlados:** Excepciones inesperadas en cualquier fase.
    *   **Gestión de estado:** Inconsistencias si un artículo falla a mitad del pipeline.

**8. Configuración y requisitos especiales**

*   **Variables de entorno:**
    *   `GROQ_API_KEY`, `MODEL_ID`, `API_TIMEOUT`, `API_TEMPERATURE`, `API_MAX_TOKENS`, `MAX_RETRIES`, `MAX_WAIT_SECONDS`: Configuración de Groq.
    *   `SUPABASE_URL`, `SUPABASE_KEY`: Conexión a Supabase.
    *   `API_HOST`, `API_PORT`: Para el servidor FastAPI.
    *   `WORKER_COUNT`, `QUEUE_MAX_SIZE`: Configuración del controlador asíncrono.
    *   `USE_SPACY_FILTER`, `USE_SENTRY`, `SENTRY_DSN`, `ENABLE_NOTIFICATIONS`, `STORE_METRICS`, `DEBUG_MODE`: Flags de comportamiento.
    *   `PROMPTS_DIR`, `METRICS_DIR`, `LOG_DIR`: Rutas a directorios importantes.
    *   `MIN_CONTENT_LENGTH`, `MAX_CONTENT_LENGTH`: Límites para el procesamiento de texto.
*   **Archivos de configuración:**
    *   `.env`: Para cargar variables de entorno.
    *   Archivos de texto en `PROMPTS_DIR` conteniendo las plantillas de los prompts para el LLM.
*   **Otros requisitos:**
    *   Modelo spaCy (`es_core_news_lg`) descargado si `USE_SPACY_FILTER` es True.
    *   Acceso de red a la API de Groq y a Supabase.
    *   Directorio de logs (`/var/log/maquina_noticias`) con permisos de escritura.
    *   Base de datos configurada con el esquema correcto y las funciones RPC (`insertar_articulo_completo`, `insertar_fragmento_completo`, `buscar_entidad_similar`, `buscar_posibles_duplicados_lote`).

**9. Notas adicionales**

*   El pipeline está diseñado para ser modular, permitiendo potencialmente la modificación o reemplazo de fases individuales.
*   La calidad de la extracción depende en gran medida de la calidad de los prompts y de la capacidad del modelo LLM (`llama-3.1-8b-instant`).
*   La Fase 4 es crucial para la integración con los datos existentes en la BD.
*   La Fase 5, mediante el uso de RPCs, busca garantizar la atomicidad de la inserción de datos complejos.
*   El manejo de errores incluye el registro en `articulos_error_persistente` para facilitar el reintento o la intervención manual.
*   El controlador (`controller.py`) gestiona la cola y los workers para el procesamiento asíncrono de los artículos/fragmentos.
*   La adaptación para procesar fragmentos de documentos implica pasar metadatos adicionales (`documento_id`, `fragmento_id`) a través de las fases y usar la RPC `insertar_fragmento_completo` en la Fase 5.
*   Interactúa con el "Modelo de Tres Memorias": lee de la "Memoria Superficial" (`cache_entidades`) y escribe en la "Memoria Relacional".