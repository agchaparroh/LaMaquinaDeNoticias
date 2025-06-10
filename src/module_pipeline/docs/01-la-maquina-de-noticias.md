# 💡 La Máquina de Noticias

# Contexto del Sistema "La Máquina de Noticias" para el Desarrollador del `module_pipeline`

## 1. Visión General del Sistema y Rol del `module_pipeline`

**La Máquina de Noticias** es un sistema integral diseñado para procesar y analizar grandes volúmenes de información periodística y documentos extensos. Utiliza inteligencia artificial, específicamente modelos de lenguaje grandes (LLM), para transformar texto no estructurado en datos estructurados y conectados, facilitando así la investigación periodística.

El `module_pipeline` constituye el **núcleo de análisis e inteligencia** de este sistema. Su responsabilidad principal es recibir contenido textual (artículos de noticias o fragmentos de documentos) y, mediante una secuencia de fases de procesamiento con LLMs, extraer, estructurar, validar y normalizar la información. Los resultados de este procesamiento se persisten en una base de datos central para su posterior consulta y utilización por otros componentes del sistema.

Este documento proporciona el contexto general del sistema para facilitar la comprensión de cómo el `module_pipeline` se integra y colabora con otros componentes de "La Máquina de Noticias".

## 2. Flujo General de Datos y Funcionamiento del Sistema

El sistema opera mediante un flujo de datos que involucra varios componentes conceptuales:

### 2.1. Fuentes y Recopilación de Información

El sistema se alimenta de dos fuentes principales de texto:

- **Artículos de noticias:** Recopilados automáticamente de diversos medios de comunicación mediante un componente de web scraping (conceptualizado como `module_scraper`).
- **Documentos extensos:** Informes, libros, leyes, etc., que pueden ingresarse manualmente al sistema a través de un motor de ingesta (conceptualizado como `module_ingestion_engine`), el cual también puede segmentarlos cuando son muy extensos.

Estos textos originales se almacenan para referencia en lo que denominamos "Memoria Profunda".

### 2.2. Conexión y Entrega de Datos al Pipeline

Los artículos recopilados y los fragmentos de documentos son preparados y enviados al `module_pipeline` para su procesamiento. Un componente conector (conceptualizado como `module_connector`) es responsable de formalizar los datos del scraper y entregarlos al pipeline.

### 2.3. Procesamiento Inteligente en el `module_pipeline`

Aquí se centra el trabajo principal. El `module_pipeline` recibe el texto y lo procesa en varias fases:

- **Triaje y Preprocesamiento:** Evaluación inicial, limpieza y posible traducción.
- **Extracción de Información:** Utilización de LLMs para identificar y extraer elementos clave como hechos, entidades (personas, organizaciones, lugares), citas textuales y datos cuantitativos.
- **Normalización y Vinculación:** Estandarización de la información extraída y vinculación de entidades a una base de conocimiento existente.
- **Evaluación y Enriquecimiento:** Asignación de metadatos adicionales, como la importancia contextual de los hechos.

La configuración de cómo el LLM realiza estas extracciones (los "prompts") se gestiona mediante archivos externos, permitiendo flexibilidad.

### 2.4. Almacenamiento Estructurado (Memoria Relacional)

La información estructurada y enriquecida generada por el `module_pipeline` se almacena de forma persistente en una base de datos central (actualmente Supabase/PostgreSQL). Esta base de datos constituye la "Memoria Relacional" del sistema, guardando los hechos, entidades y sus relaciones de manera organizada.

### 2.5. Consulta, Exploración y Utilización

Una vez que los datos están en la base de datos, otros módulos del sistema (conceptualizados como `module_dashboard_review` para revisión editorial, `module_chat_interface` para investigación) acceden a esta información para sus respectivas funcionalidades. El `module_pipeline` es, por tanto, un productor clave de la información que estos módulos consumirán.

### 2.6. Curación Editorial y Retroalimentación

Existe un componente de revisión y curación editorial. El feedback generado puede influir en la mejora de los prompts del `module_pipeline` o en el reentrenamiento de modelos auxiliares (como el de asignación de importancia).

## 3. Conceptos Clave para el `module_pipeline`

Para comprender el trabajo del `module_pipeline`, es fundamental conocer estos conceptos sobre los datos que maneja y produce:

- **Hechos (Facts):** Unidades de información que describen un evento, situación o declaración específica, extraídas del texto. Cada hecho incluye atributos como descripción, fecha, ubicación y entidades involucradas.

- **Entidades (Entities):** Personas, organizaciones, lugares u otros conceptos nombrados relevantes en el contexto de los hechos. El pipeline las identifica y busca normalizarlas.

- **Citas Textuales:** Fragmentos exactos de texto atribuidos a una entidad específica.

- **Datos Cuantitativos:** Información numérica estructurada extraída del texto (ej., cifras económicas, estadísticas).

- **Relaciones:** Vínculos significativos entre los diferentes elementos extraídos (ej., una entidad participa en un hecho, un hecho contradice a otro).

- **Importancia Contextual:** Una métrica (escala 1-10) que el `module_pipeline` asigna a los hechos, indicando su relevancia o significancia. Este proceso puede estar guiado por un modelo de machine learning externo o por criterios definidos.

- **Modelo de "Tres Memorias" (Contexto para el Pipeline):**
  - **Memoria Profunda:** Almacén de los textos originales (artículos, documentos). El `module_pipeline` consume de aquí.
  - **Memoria Relacional:** La base de datos estructurada (Supabase) donde el `module_pipeline` escribe sus resultados (hechos, entidades, etc.).
  - **Memoria Superficial (Cachés):** Almacenes temporales o de acceso rápido (ej., `cache_entidades` en la BD) que el `module_pipeline` puede consultar durante el procesamiento para optimizar la normalización de entidades u otras tareas.

- **Trazabilidad:** Es importante poder rastrear la información estructurada hasta su origen en el texto original. El `module_pipeline` debe facilitar esto mediante la correcta asignación de IDs y referencias.

- **Fragmentos de Documentos:** El `module_pipeline` debe ser capaz de procesar no solo artículos completos sino también segmentos o fragmentos de documentos más largos, manteniendo el contexto del documento original.

## 4. Configuración y Adaptabilidad del `module_pipeline`

Una característica importante del `module_pipeline` es su adaptabilidad, lograda principalmente a través de:

- **Prompts del LLM Externalizados:** Las instrucciones detalladas que guían al LLM en cada fase de extracción se almacenan en archivos de texto externos. Esto permite que los prompts sean ajustados y mejorados sin modificar el código central del pipeline. Estos archivos se gestionan dentro del directorio `prompts/` del `module_pipeline`.

- **Modelos de ML Auxiliares:** Para tareas como la asignación de "importancia", el `module_pipeline` puede interactuar con modelos de machine learning que son entrenados y versionados por procesos externos (conceptualizados como "IA Nocturna"). El pipeline integra y utiliza las predicciones de estos modelos.

Esta estructura permite que el `module_pipeline` evolucione y se adapte a nuevas necesidades o mejoras en los modelos de IA.
