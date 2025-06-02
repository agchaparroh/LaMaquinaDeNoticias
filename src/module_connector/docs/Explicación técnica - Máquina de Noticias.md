# Introducción a "La Máquina de Noticias" y el Rol del `module_connector`

## 1. Visión General del Sistema

"La Máquina de Noticias" es un sistema integral diseñado para la recopilación, procesamiento y análisis avanzado de información periodística y documentos extensos. Su objetivo principal es transformar grandes volúmenes de texto no estructurado en conocimiento organizado y accionable, utilizando para ello técnicas de Inteligencia Artificial, especialmente Procesamiento de Lenguaje Natural (NLP) con Modelos de Lenguaje Grandes (LLMs).

La arquitectura del sistema se basa en una serie de módulos especializados e interconectados, cada uno encargado de una fase específica del flujo de datos. Estos módulos están pensados para operar de forma independiente, a menudo como contenedores Docker, facilitando su desarrollo, despliegue y mantenimiento.

## 2. Flujo de Datos Principal y Ubicación del `module_connector`

El flujo de datos fundamental que concierne directamente al `module_connector` es el siguiente:

1.  **`module_scraper` (Módulo de Recopilación):**
    *   **Responsabilidad:** Este módulo se encarga de recopilar automáticamente artículos de diversas fuentes de noticias predefinidas mediante técnicas de web scraping.
    *   **Salida:** Genera archivos (generalmente en formato `.json.gz`) que contienen los datos extraídos de los artículos. Estos archivos se depositan en un directorio específico del sistema de archivos, que actúa como un área de "pendientes" para el siguiente módulo.

2.  **`module_connector` (Conector Scrapy-Pipeline):**
    *   **Responsabilidad:** **Este es el módulo que nos ocupa.** Actúa como un puente crucial entre el `module_scraper` y el `module_pipeline`.
    *   **Funcionamiento:**
        *   Monitoriza continuamente el directorio donde el `module_scraper` deposita los archivos de artículos.
        *   Al detectar un nuevo archivo, lo toma, lo procesa (lee, descomprime, valida su contenido según la estructura esperada, por ejemplo, `ArticuloInItem`).
        *   Envía cada artículo validado a una API expuesta por el `module_pipeline`.
        *   Gestiona el ciclo de vida de los archivos procesados, moviéndolos a directorios de "completados" o "errores" según el resultado del envío a la API del pipeline.
    *   **Importancia:** Asegura que los datos recopilados por el scraper lleguen de forma fiable, ordenada y validada al `module_pipeline` para su análisis profundo.

3.  **`module_pipeline` (Pipeline de Procesamiento Inteligente):**
    *   **Responsabilidad:** Recibe los artículos individuales enviados por el `module_connector` a través de su API.
    *   **Funcionamiento:** Aplica una serie de pasos de procesamiento inteligente utilizando LLMs para "leer" y "entender" el texto. Esto incluye la extracción de elementos informativos clave (hechos, entidades, citas, datos), el establecimiento de relaciones entre ellos y la preparación de esta información estructurada para su almacenamiento en una base de datos central.
    *   **Entrada:** Espera recibir datos de artículos (por ejemplo, en formato JSON) a través de un endpoint de API específico (ej. `/procesar`).

## 3. Contexto para el Desarrollador del `module_connector`

Para el desarrollador del `module_connector`, es fundamental entender:

*   La **estructura y formato exactos de los archivos y datos** que produce el `module_scraper`.
*   El **contrato de la API** que expondrá el `module_pipeline` (endpoint, método HTTP, formato del payload esperado para enviar artículos, y los códigos de respuesta esperados para éxito y error). Aunque el `module_pipeline` aún no esté implementado, se debe trabajar con una definición clara de esta interfaz.
*   Los **directorios del sistema de archivos** que utilizará para leer los archivos del scraper y para mover los archivos procesados o erróneos. Estos directorios suelen ser volúmenes compartidos en un entorno Docker.

Este documento proporciona el contexto general. Para los detalles específicos sobre la implementación, las entradas, salidas, el flujo interno y la configuración del `module_connector`, se debe consultar el documento `Explicación técnica - module_connector.md`.