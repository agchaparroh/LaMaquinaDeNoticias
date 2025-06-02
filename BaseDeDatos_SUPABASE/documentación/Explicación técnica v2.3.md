## 1. Visión General del Sistema y Flujo de Datos
La **Máquina de Noticias** constituye un sistema integral diseñado para recopilar, procesar, analizar y consultar grandes volúmenes de información periodística y documentos extensos. El sistema aprovecha técnicas avanzadas de Inteligencia Artificial —específicamente Procesamiento de Lenguaje Natural con LLMs (Large Language Models)— para extraer datos estructurados, identificar relaciones complejas y facilitar la investigación periodística mediante interfaces especializadas.

La arquitectura del proyecto se organiza en módulos independientes pero interconectados, donde cada componente se responsabiliza de una fase específica en el flujo de datos, abarcando desde la recopilación inicial hasta la consulta y monitorización final.


## 2. Funcionamiento de "La Máquina"
La Máquina de Noticias es un sistema avanzado diseñado para ayudar a los periodistas a navegar y comprender grandes volúmenes de información. Su objetivo es transformar noticias y documentos en conocimiento estructurado y fácilmente consultable. A continuación, se describe su funcionamiento de manera general:

1.  **Recopilación Continua de Información:**
    *   La Máquina comienza por **recopilar automáticamente artículos** de una amplia gama de medios de comunicación predefinidos, utilizando tecnología de web scraping (`module_scraper`). También permite la **ingesta manual de documentos extensos** (como informes, libros o leyes) proporcionados por los periodistas (`module_ingestion_engine`).
    *   Los artículos y documentos originales se guardan íntegramente (Memoria Profunda) para referencia futura y posible re-análisis.

2.  **Procesamiento Inteligente del Texto:**
    *   Cada artículo o fragmento de documento pasa por un **pipeline de procesamiento inteligente** (`module_pipeline`). Este pipeline utiliza Modelos de Lenguaje Grandes (LLM), una forma avanzada de inteligencia artificial, para "leer" y "entender" el texto.
    *   Este proceso se realiza en varias fases:
        *   Primero, se evalúa si el contenido es relevante para los temas de interés.
        *   Luego, el LLM identifica y extrae los **elementos informativos clave**: los hechos principales que se narran, las personas, organizaciones y lugares involucrados (entidades), las declaraciones textuales importantes (citas) y cualquier dato numérico significativo.
        *   Finalmente, el sistema intenta establecer **relaciones** entre estos elementos (ej. qué entidad participó en qué hecho, o cómo un hecho puede ser causa de otro) e identifica posibles contradicciones entre diferentes piezas de información.

3.  **Almacenamiento Estructurado del Conocimiento:**
    *   Toda esta información extraída y estructurada se almacena de forma organizada en una **base de datos central** (Memoria Relacional). Esta base de datos no solo guarda los datos, sino también las conexiones entre ellos, creando una rica red de conocimiento.
    *   Para acelerar las consultas comunes, se utilizan técnicas como vistas materializadas y cachés (Memoria Superficial).

4.  **Mantenimiento y Enriquecimiento Constante ("IA Nocturna"):**
    *   De forma periódica (generalmente durante la noche), una serie de **procesos automatizados de mantenimiento y enriquecimiento** (`module_maintenance_scripts` orquestados por `module_orchestration`) se ejecutan.
    *   Estas tareas incluyen: generar representaciones numéricas (embeddings) del texto para permitir búsquedas por similitud conceptual, actualizar dinámicamente los "Hilos Narrativos" (ver punto 6), identificar y gestionar posibles duplicados de información, normalizar nombres de entidades, y aprender de las correcciones editoriales para mejorar la asignación de importancia a los hechos.

5.  **Revisión y Curación Editorial:**
    *   Los periodistas y editores cuentan con un **dashboard de revisión** (`module_dashboard_review`) donde pueden visualizar la información procesada.
    *   Aquí pueden validar la información, ajustar la importancia asignada a los hechos, corregir detalles y, crucialmente, agrupar hechos relacionados en "Hilos Narrativos". Este feedback humano es fundamental para mantener la calidad y relevancia del sistema, y para reentrenar sus componentes de IA.

6.  **Investigación y Consulta en Lenguaje Natural ("Hilos Narrativos" y Chat):**
    *   El **Chat de Investigación** (`module_chat_interface`) es la principal herramienta para que los periodistas interactúen con el conocimiento acumulado.
    *   Pueden hacer preguntas en lenguaje natural. El LLM del chat interpreta estas preguntas y, utilizando un conjunto de "herramientas de consulta" especializadas, busca la información relevante en la base de datos.
    *   Un concepto central aquí son los **Hilos Narrativos**: agrupaciones temáticas de información que permiten seguir la evolución de una historia o tema a lo largo del tiempo. El chat puede explicar estos hilos, resumir sus novedades y contextualizar eventos dentro de ellos.
    *   El sistema siempre se esfuerza por proporcionar las **fuentes originales** de la información, asegurando la trazabilidad y permitiendo la verificación.

7.  **Monitorización y Desarrollo:**
    *   Una **interfaz de desarrollador** (`module_dev_interface`) permite al equipo técnico supervisar la salud y el rendimiento de todos los componentes del sistema, facilitando el mantenimiento y la evolución continua de la Máquina de Noticias.

En esencia, la Máquina de Noticias actúa como un asistente de investigación inteligente: recopila, procesa, estructura, y facilita la exploración de información periodística, permitiendo a los usuarios descubrir conexiones, entender narrativas complejas y acceder rápidamente a los datos que necesitan, siempre con un enfoque en la calidad, la trazabilidad y la mejora continua a través de la colaboración entre la IA y la supervisión humana.

## 3. Conceptos Clave
La Máquina de Noticias se fundamenta en varios conceptos clave que definen su arquitectura, funcionamiento y capacidades. Comprender estos conceptos es esencial para entender cómo el sistema transforma información cruda en conocimiento accionable para la investigación periodística.

### 3.1. Modelo Conceptual de Memoria

La Máquina de Noticias gestiona la información a través de un modelo de memoria de tres niveles para optimizar el acceso, la profundidad del análisis y los costos:

*   **Memoria Profunda:** Constituida por el almacenamiento de los datos originales sin procesar (ej. HTML completos de artículos, archivos PDF/DOCX de documentos extensos). Su objetivo es la preservación completa de la fuente y la posibilidad de re-procesamiento futuro. Se implementa principalmente mediante **Supabase Storage**, donde módulos como `module_scraper` (ver [[Módulo de Recopilación - Scrapy (module_scraper)]]) y `module_ingestion_engine` (ver [[Motor de Ingesta y Segmentación (module_ingestion_engine)]]) depositan estos archivos.
*   **Memoria Relacional:** Es el núcleo de la información estructurada y conectada del sistema. Aquí se almacenan los hechos, entidades, citas, datos cuantitativos, y las complejas relaciones entre ellos, extraídos por el `module_pipeline`. Esta memoria permite consultas analíticas profundas y es la base para la mayoría de las `query_tools` del `module_chat_interface`. Se implementa en **PostgreSQL (gestionado por Supabase)**, utilizando un esquema detallado de tablas e índices (ver [[8 de mayo/La Máquina 2/Arquitectura/Arquitectura de la base de datos|Arquitectura de la base de datos]]).
*   **Memoria Superficial:** Diseñada para el acceso rápido a información agregada, precalculada o frecuentemente consultada. Incluye cachés (como `cache_entidades` usada por el `module_pipeline` para la normalización rápida de entidades) y **vistas materializadas** (ej. `resumen_hilos_activos`, `tendencias_temas`) que son refrescadas periódicamente por `pg_cron` (ver [[8 de mayo/La Máquina 2/Arquitectura/Vistas materializadas|Vistas materializadas]]). Esta memoria acelera las respuestas del `module_chat_interface` y provee contexto para el `module_dashboard_review` y la `IA Nocturna`.

Este modelo permite que el sistema combine la riqueza de los datos originales con la eficiencia de las estructuras de datos optimizadas para diferentes tipos de consulta y análisis.

### 3.2. Ontología de Información Central

El sistema transforma el texto no estructurado en un conjunto bien definido de *tipos* de información estructurada, que constituyen su ontología fundamental:

*   **Hechos:** Eventos, sucesos, declaraciones o anuncios significativos, caracterizados por su contenido, fecha, ubicación, tipo e importancia.
*   **Entidades:** Actores clave como Personas, Organizaciones, Instituciones, Lugares, o conceptos abstractos como Eventos (genéricos), Normativas y Conceptos (ideas, teorías).
*   **Citas Textuales:** Declaraciones directas atribuidas a entidades específicas.
*   **Datos Cuantitativos:** Cifras, estadísticas y valores numéricos extraídos del texto.
*   **Relaciones:** Conexiones significativas entre los elementos anteriores (ej. Hecho-Entidad, Hecho-Hecho, Entidad-Entidad) que estructuran el conocimiento.
*   **Contradicciones:** Vínculos entre hechos que presentan información inconsistente.

Esta ontología es el lenguaje común que usa el `module_pipeline` (ver [[Pipeline de Procesamiento (module_pipeline)]]) para extraer, la `Base de Datos` (ver [[Supabase _ base de datos]]) para almacenar, y el `module_chat_interface` (ver [[Chat de Investigación (module_chat_interface)]]) para consultar y razonar.

### 3.3. Procesamiento por Fases con LLM (Pipeline de Inteligencia)

El `module_pipeline` (ver [[Pipeline de Procesamiento (module_pipeline)]]) es el motor de extracción y estructuración de conocimiento. El contenido (artículos de noticias o fragmentos de documentos extensos) se procesa a través de una secuencia de fases orquestadas. Cada fase utiliza un Modelo de Lenguaje Grande (LLM - Groq) con prompts específicos (ver [[8 de mayo/La Máquina 2/Prompts/Prompt_1_ filtrado|Prompt 1]], [[8 de mayo/La Máquina 2/Prompts/Prompt_2_elementos_basicos|Prompt 2]], [[8 de mayo/La Máquina 2/Prompts/Prompt_3_citas_datos|Prompt 3]], [[8 de mayo/La Máquina 2/Prompts/Prompt_4_relaciones|Prompt 4]]) para realizar tareas progresivamente más complejas:

1.  **Preprocesamiento y Triaje:** Limpieza, evaluación de relevancia inicial.
2.  **Extracción de Elementos Básicos:** Identificación de Hechos y Entidades.
3.  **Extracción de Citas y Datos Cuantitativos.**
4.  **Normalización, Vinculación y Relaciones:** Consolidación de Entidades, detección de duplicados L1, extracción de Relaciones y Contradicciones.
5.  **Evaluación de Importancia Contextual:** Asignación de un score de importancia al hecho.
6.  **Persistencia Atómica:** Almacenamiento de toda la información procesada.

Este enfoque modular permite un análisis profundo y estructurado del texto.

### 3.4. Atomicidad de la Persistencia de Datos Estructurados

Un principio fundamental es que la información extraída de una fuente (artículo o fragmento) por el `module_pipeline` se persiste en la Memoria Relacional como una unidad transaccional. Las funciones RPC de la base de datos (`insertar_articulo_completo`, `insertar_fragmento_completo` en [[8 de mayo/La Máquina 2/Arquitectura/Funciones-triggers|Funciones-triggers]]) están diseñadas para asegurar que si alguna parte crítica de la inserción falla, toda la transacción se revierte. Esto garantiza la integridad y consistencia de los datos, evitando información parcial o "huérfana".

### 3.5. Hilos Narrativos

Los Hilos Narrativos son el mecanismo central para organizar y dar sentido a secuencias de eventos e información interconectada sobre un tema específico a lo largo del tiempo.

*   **Propósito:** Permiten a los periodistas y al LLM del `module_chat_interface` comprender la evolución de una historia, identificar patrones y obtener resúmenes contextualizados.
*   **Creación y Curación Editorial:** Se definen en el `module_dashboard_review` (ver [[Dashboard de Revisión (module_dashboard_review)]]), estableciendo una `descripcion_hilo_curada` (ángulo editorial) y `criterios_consulta_estructurados` (qué información pertenece al hilo).
*   **Actualización Dinámica ("Archivo"):** La `IA Nocturna` (ver concepto 7), mediante el script `hilo_updater.py` (ver [[8 de mayo/La Máquina 2/En detalle/Tareas de Mantenimiento Detalladas|Tareas de Mantenimiento Detalladas]]), usa estos criterios para ejecutar `query_tools` y actualizar la `lista_elementos_ids_actualizada` del hilo y generar `puntos_clave_novedades`.
*   **Consulta y Explicación:** El `module_chat_interface` (ver [[Chat de Investigación (module_chat_interface)]]), a través de `obtener_info_hilo` (ver [[8 de mayo/La Máquina 2/En detalle/Query Tools Detalladas|Query Tools Detalladas]]), accede a esta información para que el LLM construya explicaciones narrativas.

### 3.6. Interacción Basada en LLM y Herramientas de Consulta (Query Tools)

El `module_chat_interface` (ver [[Chat de Investigación (module_chat_interface)]]) permite una interacción avanzada donde el LLM actúa como un "agente razonador". Interpreta las preguntas en lenguaje natural del usuario y utiliza un conjunto de herramientas de consulta especializadas (`Query Tools`, ver [[8 de mayo/La Máquina 2/En detalle/Query Tools Detalladas|Query Tools Detalladas]]) para buscar y recuperar información específica de la Memoria Relacional y Superficial. Tras obtener los datos estructurados, el LLM los sintetiza para generar una respuesta coherente y fundamentada, facilitando la investigación periodística.

### 3.7. IA Nocturna / Mantenimiento y Evolución Automatizada

La "IA Nocturna" se refiere a un conjunto de procesos automatizados, definidos en `module_maintenance_scripts` (ver [[Lógica de Mantenimiento (module_maintenance_scripts)]] y [[8 de mayo/La Máquina 2/En detalle/Tareas de Mantenimiento Detalladas|Tareas de Mantenimiento Detalladas]]) y orquestados por `module_orchestration` (ver [[Orquestación - Prefect (module_orchestration)]]). Estas tareas se ejecutan periódicamente para:

*   Generar y actualizar embeddings vectoriales.
*   Mantener actualizados los Hilos Narrativos.
*   Gestionar duplicados de hechos.
*   Normalizar entidades
*   Asignación de etiquetas
*   Construir el contexto de tendencias diario (`tendencias_contexto_diario`).
*   Reentrenar modelos de ML (ej. el modelo de importancia de hechos).
*   Vincular entidades con Wikidata.
*   Calcular el consenso de fuentes para hechos.
*   Realizar chequeos de salud del sistema y limpieza de datos.

Estos procesos aseguran que el sistema se mantenga operativo, que la calidad de los datos mejore continuamente y que el conocimiento esté actualizado y sea consistente.

### 3.8. Embeddings y Búsqueda Semántica

El sistema utiliza representaciones vectoriales numéricas (embeddings) para capturar el significado semántico del contenido textual (hechos, entidades, citas, fragmentos). Estos son generados por `embeddings_generator.py` (ver [[8 de mayo/La Máquina 2/En detalle/Tareas de Mantenimiento Detalladas|Tareas de Mantenimiento Detalladas]]). Esta capacidad habilita la `busqueda_semantica` (ver [[8 de mayo/La Máquina 2/En detalle/Query Tools Detalladas|Query Tools Detalladas]]), una potente herramienta del `module_chat_interface` que permite encontrar información conceptualmente similar a una consulta, incluso si no comparten las mismas palabras clave exactas. Esto es crucial para la exploración temática y el descubrimiento de conexiones no obvias.

### 3.9. Curación Editorial y Ciclo de Feedback

El `module_dashboard_review` (ver [[Dashboard de Revisión (module_dashboard_review)]]) es más que una interfaz de revisión; es un componente integral del ciclo de calidad y aprendizaje del sistema. Las acciones de los periodistas y editores (ej. validar hechos, ajustar su importancia editorial, crear y refinar Hilos Narrativos, corregir entidades) no solo mejoran los datos directamente, sino que también generan feedback estructurado (ej. en la tabla `feedback_importancia_hechos`). Este feedback es utilizado por la `IA Nocturna` (específicamente por `importancia_model_trainer.py`, ver [[8 de mayo/La Máquina 2/En detalle/Tareas de Mantenimiento Detalladas|Tareas de Mantenimiento Detalladas]]) para reentrenar y mejorar los modelos de IA del sistema, en un enfoque de "human-in-the-loop".

### 3.10. Gestión Proactiva de la Calidad de Datos

La Máquina de Noticias incorpora múltiples mecanismos automatizados y editoriales para gestionar y mejorar la calidad de los datos de forma proactiva. Esto incluye:

*   **Detección y Gestión de Duplicados:** Tanto en el `module_pipeline` (L1) como por `duplicates_manager.py` en la `IA Nocturna`.
*   **Normalización de Entidades:** Fusión de representaciones duplicadas de la misma entidad por `entity_normalizer.py`.
*   **Vinculación con Wikidata:** Enriquecimiento y estandarización de entidades mediante `entity_linker.py`.
*   **Consenso de Fuentes:** Cálculo automático del campo `hechos.consenso_fuentes` por la `IA Nocturna` para reflejar el acuerdo entre fuentes.
*   **Evaluación Editorial:** Posibilidad de que los editores marquen hechos como `verificado_ok_editorial` o `declarado_falso_editorial` en el `module_dashboard_review`.

Estos procesos buscan asegurar que la información no solo sea extraída, sino también depurada y confiable.

### 3.11. Trazabilidad y Citación de Fuentes

Un principio fundamental del sistema es asegurar que toda la información recuperada o generada pueda ser rastreada hasta sus fuentes originales (artículos o documentos/fragmentos). El `module_pipeline` establece los vínculos iniciales (ej. `hecho_articulo`). Las `Query Tools` del `module_chat_interface` (ver [[8 de mayo/La Máquina 2/En detalle/Query Tools Detalladas|Query Tools Detalladas]]) están diseñadas para devolver no solo los datos solicitados, sino también información detallada sobre las fuentes consultadas. Esto es esencial para la credibilidad, permitiendo la verificación por parte de los periodistas y la correcta citación en sus trabajos.

### 3.12. Adaptabilidad y Configuración de la Inteligencia

Una parte significativa de la "inteligencia" y el comportamiento del sistema reside en configuraciones externas que pueden ser ajustadas sin necesidad de reescribir el código central:

*   **Prompts del LLM:** Las instrucciones detalladas que guían al LLM en las diferentes fases de extracción del `module_pipeline` se almacenan en archivos externos (en `PROMPTS_DIR`, ver [[8 de mayo/La Máquina 2/Prompts/Prompt_1_ filtrado|Prompt 1]], etc.) y pueden ser refinados.
*   **Criterios de Hilos Narrativos:** Los `criterios_consulta_estructurados` que definen el contenido de un Hilo Narrativo son configurables (JSONB en la tabla `hilos_narrativos`) y pueden ser ajustados por los editores o por sistemas de sugerencia automática.
*   **Modelos de ML:** El modelo de asignación de importancia, por ejemplo, es entrenado y versionado periódicamente, permitiendo que el sistema se adapte al feedback editorial.

Esta flexibilidad permite que el sistema evolucione y mejore su rendimiento y alineación con las necesidades editoriales a lo largo del tiempo.

## 4. Componentes detallados:

[[Módulo de Recopilación - Scrapy (module_scraper)]]
[[Conector Scrapy-Pipeline (module_connector)]]
[[Motor de Ingesta y Segmentación (module_ingestion_engine)]]
[[Pipeline de Procesamiento (module_pipeline)]]
+ [[Prompt_1_ filtrado]]
+ [[Prompt_2_elementos_basicos]]
+ [[Prompt_3_citas_datos]]
+ [[Prompt_4_relaciones]]
+ [[Criterios_de_Importancia_Guia]]
[[Supabase _  base de datos]]
+ [[Arquitectura de la base de datos]]
+ [[Vistas materializadas]]
+ [[Funciones-triggers]]


[[Dashboard de Revisión (module_dashboard_review)]]
[[Chat de Investigación (module_chat_interface)]]
+ [[Query Tools Detalladas]]
[[Interfaz de Desarrollador (module_dev_interface)]]
[[Lógica de Mantenimiento (module_maintenance_scripts)]]
+ [[Tareas de Mantenimiento Detalladas]]
[[Orquestación - Prefect (module_orchestration)]]