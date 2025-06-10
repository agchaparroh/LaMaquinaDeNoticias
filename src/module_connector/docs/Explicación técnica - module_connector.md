# Conector Scrapy-Pipeline

## Descripción general
Este módulo actúa como un puente entre el `module_scraper` y el `module_pipeline`. Su función principal es monitorizar un directorio específico (/data/scrapy_output/pending/) donde el scraper deposita archivos con datos de artículos extraídos. Al detectar un nuevo archivo, lo procesa, valida su contenido, lo envía a la API del Pipeline de Procesamiento y gestiona el ciclo de vida del archivo moviéndolo a directorios de "completados" o "errores" según el resultado del envío. Garantiza que los artículos recopilados lleguen de forma ordenada y fiable al siguiente paso de análisis.

## Input (entradas)
- **Tipo de entrada:** Archivos.
- **Formato:** Archivos .json.gz comprimidos. Cada archivo contiene un objeto JSON o una lista de objetos JSON, donde cada objeto sigue la estructura del ArticuloInItem definido en el module_scraper.

### Estructura de `ArticuloInItem` (definida en `module_scraper/scraper_core/items.py`)

El `module_connector` debe ser capaz de procesar objetos JSON que sigan la siguiente estructura de Pydantic/Scrapy Item:

```python
import scrapy
from typing import Optional
from datetime import datetime

class ArticuloInItem(scrapy.Item):
    """
    Item para almacenar artículos periodísticos extraídos.
    Mapea directamente a la tabla 'articulos' en la base de datos.
    """
    # Campos principales
    url = scrapy.Field()                    # URL original del artículo
    storage_path = scrapy.Field()           # Ruta en Supabase Storage
    fuente = scrapy.Field()                 # Nombre/identificador del spider que lo extrajo
    medio = scrapy.Field()                  # Nombre del medio (ej: "El País")
    medio_url_principal = scrapy.Field()    # URL principal del medio (ej: https://elpais.com)
    pais_publicacion = scrapy.Field()       # País de publicación (ej: "España")
    tipo_medio = scrapy.Field()             # Tipo: diario, agencia, televisión, etc.
    titular = scrapy.Field()                # Título del artículo
    fecha_publicacion = scrapy.Field()      # Fecha de publicación
    autor = scrapy.Field()                  # Autor(es) del artículo
    idioma = scrapy.Field()                 # Idioma del artículo
    seccion = scrapy.Field()                # Sección del medio
    etiquetas_fuente = scrapy.Field()       # Etiquetas del medio original
    es_opinion = scrapy.Field()             # Boolean: ¿Es artículo de opinión?
    es_oficial = scrapy.Field()             # Boolean: ¿Es fuente oficial?
    
    # Campos generados por el pipeline
    resumen = scrapy.Field()                # Resumen generado en Fase 2
    categorias_asignadas = scrapy.Field()   # Categorías asignadas en Fase 2
    puntuacion_relevancia = scrapy.Field()  # Puntuación 0-10 asignada en Fase 2
    
    # Campos de control
    fecha_recopilacion = scrapy.Field()     # Timestamp de scraping
    fecha_procesamiento = scrapy.Field()    # Timestamp de fin de Fase 5
    estado_procesamiento = scrapy.Field()   # Estado: pendiente, procesando, etc.
    error_detalle = scrapy.Field()          # Detalle del error si lo hay
    
    # Contenido extraído
    contenido_texto = scrapy.Field()        # Texto completo del artículo
    contenido_html = scrapy.Field()         # HTML original del artículo
    
    # Metadatos adicionales
    metadata = scrapy.Field()               # JSONB para datos adicionales

    # Validación de campos requeridos
    def validate(self) -> bool:
        """Valida que los campos requeridos estén presentes"""
        required_fields = ['titular', 'medio', 'pais_publicacion', 'tipo_medio', 
                          'fecha_publicacion', 'contenido_texto']
        for field in required_fields:
            if not self.get(field):
                return False
        return True
```

### Ejemplo de Objeto JSON (`ArticuloInItem`) con Datos Dummy

A continuación, un ejemplo de cómo se vería un objeto JSON individual que el `module_connector` podría encontrar dentro de un archivo `.json.gz`:

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
    "resumen": "Este es un resumen generado automáticamente del artículo de ejemplo.",
    "categorias_asignadas": ["tecnología", "innovación"],
    "puntuacion_relevancia": 8.5,
    "fecha_recopilacion": "2023-10-26T10:05:00Z",
    "fecha_procesamiento": null,
    "estado_procesamiento": "pendiente_connector",
    "error_detalle": null,
    "contenido_texto": "Este es el contenido completo en texto plano del artículo de ejemplo. Aquí iría todo el cuerpo de la noticia...",
    "contenido_html": "<html><body><h1>Titular de Ejemplo</h1><p>Este es el contenido HTML original...</p></body></html>",
    "metadata": {
        "palabras_clave_seo": ["ejemplo", "noticia", "desarrollo"],
        "fuente_original_id": "ext-789xyz"
    }
}
```

### Ejemplo de Archivo de Entrada (`.json.gz`)

El `module_scraper` genera archivos `.json.gz`. Cada uno de estos archivos contiene un objeto JSON (o una lista de objetos JSON) como el mostrado en el ejemplo anterior.

Para facilitar las pruebas, se ha incluido un archivo de ejemplo con el contenido JSON anterior en la ruta (relativa a la raíz del módulo `module_connector`):
`examples/ejemplo_articulo.json`

**Nota:** En un escenario real, este archivo `ejemplo_articulo.json` estaría comprimido como `ejemplo_articulo.json.gz` en el directorio de entrada del `module_connector`. El `module_connector` deberá ser capaz de leer y descomprimir estos archivos `.gz`.
- **Fuente:** module_scraper, que escribe estos archivos en el directorio /data/scrapy_output/pending/.
- **Frecuencia o modo de recepción:** Continuo. El módulo monitoriza el directorio de entrada constantemente (mediante polling en la implementación proporcionada) y procesa los archivos tan pronto como aparecen.
- **Interfaz de comunicación (protocolo, método, cómo se reciben los datos):** Sistema de archivos local (volumen Docker compartido). El módulo lee archivos del directorio SCRAPER_OUTPUT_DIR.
**3. Output (salidas)**

El `module_connector` tiene dos tipos principales de salidas: la comunicación de datos de artículos al `module_pipeline` y la gestión de los archivos de entrada una vez procesados.

**A. Interacción con `module_pipeline` (API Provisional)**

El `module_connector` envía cada artículo validado individualmente a una API que se espera sea expuesta por el `module_pipeline`. A continuación, se detalla el contrato provisional de esta API:

*   **Descripción General:** El `module_connector` actúa como cliente de la API del `module_pipeline`, enviando artículos para su procesamiento inteligente.
*   **Endpoint:**
    *   La URL base de la API del `module_pipeline` se configurará mediante la variable de entorno `PIPELINE_API_URL`.
    *   El path específico para enviar artículos será `/procesar`.
    *   Ejemplo de URL completa: `http://localhost:8001/procesar` (si `PIPELINE_API_URL` es `http://localhost:8001`).
*   **Método HTTP:** `POST`
*   **Cabeceras (Headers):**
    *   `Content-Type: application/json` (El `module_connector` debe enviar esta cabecera).
*   **Cuerpo de la Solicitud (Request Body):**
    *   Formato: JSON.
    *   Estructura: Un objeto JSON que contiene una única clave `"articulo"`, cuyo valor es el objeto `ArticuloInItem` completo (ver la estructura detallada en la sección "Input (entradas)").
    *   Ejemplo de cuerpo de la solicitud:
        ```json
        {
            "articulo": {
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
                "resumen": null, // Campos generados por pipeline pueden ir null o no estar
                "categorias_asignadas": null,
                "puntuacion_relevancia": null,
                "fecha_recopilacion": "2023-10-26T10:05:00Z",
                "fecha_procesamiento": null,
                "estado_procesamiento": "pendiente_pipeline", // El estado puede actualizarse
                "error_detalle": null,
                "contenido_texto": "Este es el contenido completo...",
                "contenido_html": "<html><body>...</body></html>",
                "metadata": {
                    "palabras_clave_seo": ["ejemplo"],
                    "fuente_original_id": "ext-789xyz"
                }
            }
        }
        ```

*   **Respuestas Esperadas del `module_pipeline`:**

    *   **Éxito (Artículo Aceptado para Procesamiento):**
        *   **Código de Estado HTTP:** `202 Accepted`
        *   **Descripción:** Indica que el `module_pipeline` ha recibido el artículo y lo ha aceptado para su procesamiento asíncrono. No implica que el procesamiento haya finalizado.
        *   **Cuerpo de la Respuesta (JSON):**
            ```json
            {
                "status": "recibido",
                "mensaje": "Artículo recibido y encolado para procesamiento.",
                "id_articulo_procesamiento": "<ID_INTERNO_PIPELINE>" // Opcional: un ID para seguimiento dentro del pipeline
            }
            ```

    *   **Error de Validación (Datos del Artículo Inválidos o Malformados):**
        *   **Código de Estado HTTP:** `400 Bad Request`
        *   **Descripción:** Indica que los datos del artículo enviados por el `module_connector` no pasaron la validación del `module_pipeline` (ej. campos requeridos faltantes, tipos de datos incorrectos, formato general incorrecto).
        *   **Cuerpo de la Respuesta (JSON):**
            ```json
            {
                "status": "error_validacion_payload",
                "mensaje": "Los datos del artículo proporcionados son inválidos.",
                "detalles": [ // Lista opcional de errores específicos
                    {"campo": "articulo.titular", "error": "El titular es un campo requerido y no puede estar vacío."},
                    {"campo": "articulo.fecha_publicacion", "error": "El formato de fecha no es válido."}
                ]
            }
            ```

    *   **Error Interno del Servidor (Fallo en `module_pipeline`):**
        *   **Código de Estado HTTP:** `500 Internal Server Error`
        *   **Descripción:** Indica que ocurrió un error inesperado dentro del `module_pipeline` mientras intentaba aceptar o procesar inicialmente la solicitud.
        *   **Cuerpo de la Respuesta (JSON):**
            ```json
            {
                "status": "error_interno_pipeline",
                "mensaje": "Ocurrió un error inesperado en el pipeline. Por favor, reintente más tarde."
            }
            ```

    *   **Servicio No Disponible (`module_pipeline` no operativo o sobrecargado):**
        *   **Código de Estado HTTP:** `503 Service Unavailable`
        *   **Descripción:** Indica que el `module_pipeline` no está disponible para aceptar solicitudes en este momento (ej. está caído, en mantenimiento o temporalmente sobrecargado). El `module_connector` debería reintentar después de un tiempo.
        *   **Cuerpo de la Respuesta (JSON):**
            ```json
            {
                "status": "servicio_no_disponible",
                "mensaje": "El servicio de pipeline no está disponible actualmente. Intente más tarde."
            }
            ```

**B. Gestión de Archivos de Entrada Procesados**

Una vez que todos los artículos de un archivo `.json.gz` de entrada han sido intentados enviar al `module_pipeline`:

*   **Tipo de salida:** Movimiento de archivos en el sistema de archivos.
*   **Formato:** Archivos `.json.gz` (los mismos que entraron, pero movidos de directorio).
*   **Destino:**
    *   Si al menos un artículo del archivo se envió con éxito (recibió un `202 Accepted` del pipeline), el archivo original `.json.gz` se mueve del directorio `PIPELINE_PENDING_DIR` (o `SCRAPER_OUTPUT_DIR` si no hay movimiento intermedio) al directorio `PIPELINE_COMPLETED_DIR`.
    *   Si todos los artículos de un archivo fallaron al ser enviados (o si hubo un error irrecuperable al leer o parsear el archivo mismo), el archivo original `.json.gz` se mueve al directorio `PIPELINE_ERROR_DIR`.
*   **Frecuencia o modo de entrega:** Los archivos se mueven una vez que se completa el intento de procesamiento de todos sus artículos contenidos.
*   **Interfaz de comunicación:** Operaciones del sistema de archivos (ej. `shutil.move` en Python).
**4. Flujo de procesamiento interno**
1. **Monitorización:** El script vigila continuamente (mediante polling a intervalos definidos por POLLING_INTERVAL) el directorio SCRAPER_OUTPUT_DIR en busca de nuevos archivos .json.gz.
2. **Movimiento Inicial:** Al detectar un archivo nuevo, lo mueve inmediatamente al directorio PIPELINE_PENDING_DIR para indicar que está siendo procesado y evitar que otro proceso lo tome.
3. **Lectura y Descompresión:** Abre el archivo .json.gz, lo descomprime y lee su contenido.
4. **Parseo JSON:** Parsea el contenido JSON. Espera un único objeto JSON o una lista de objetos JSON. Normaliza a una lista.
5. **Iteración de Artículos:** Procesa cada objeto (artículo) dentro de la lista:
    - **Asignación de ID/Timestamp:** Si el artículo no tiene un id o timestamp_recopilacion, se le asignan valores por defecto.
    - **Validación Pydantic:** Valida la estructura del artículo contra el modelo ArticuloInItem. Si falla la validación, se registra un error y se salta al siguiente artículo.
    - **Envío a API:** Llama a la función send_to_pipeline para enviar el artículo validado (en formato {"articulo": {...}}) al endpoint /procesar de la API del module_pipeline vía HTTP POST.
    - **Manejo de Respuesta API:** Verifica si la API responde con un código de estado 202 Accepted, indicando que el artículo fue recibido correctamente por el pipeline.
    - **Reintentos:** La función send_to_pipeline utiliza tenacity para reintentar automáticamente el envío en caso de errores de red o timeouts, con backoff exponencial.
6. **Gestión del Archivo:** Una vez procesados todos los artículos del archivo:
    - **Éxito:** Si al menos un artículo del archivo se envió con éxito a la API, el archivo . json.gz se mueve del PIPELINE_PENDING_DIR al PIPELINE_COMPLETED_DIR.
    - **Fallo:** Si ningún artículo pudo enviarse con éxito (o hubo errores al leer/procesar el archivo), el archivo se mueve del PIPELINE_PENDING_DIR al PIPELINE_ERROR_DIR. Se puede añadir una extensión . retryN para futuros reintentos.
7. **Reintento de Errores (Opcional):** Una función separada (retry_error_files) puede ser llamada periódicamente para intentar reprocesar archivos que terminaron en PIPELINE_ERROR_DIR y que están marcados para reintento.
8. **Reporte de Estado (Opcional):** Una función (report_status) puede ser llamada para enviar métricas de operación (archivos procesados, errores, etc.) al sistema de monitorización central (ej. tabla system_status).
**5. Herramientas y tecnologías utilizadas**
- **Lenguajes de programación:** Python (versión 3.8 o superior recomendada).
- **Frameworks o librerías:**
    - asyncio: Para operaciones asíncronas (I/O de red y archivos).
    - aiohttp: Cliente HTTP asíncrono para interactuar con la API del Pipeline. (Context7 ID: /aio-libs/aiohttp)
    - shutil: Para operaciones de movimiento de archivos.
    - gzip: Para leer archivos .gz.
    - json: Para parsear datos JSON.
    - tenacity: Para implementar reintentos robustos en las llamadas API. (Context7 ID: /jd/tenacity)
    - loguru: Para logging. (Context7 ID: /delgan/loguru)
    - python-dotenv: Para cargar variables de entorno. (Context7 ID: /theskumar/python-dotenv)
    - pydantic: Para validar la estructura de los datos del artículo antes de enviarlos. (Context7 ID: /pydantic/pydantic)
    - sentry-sdk (Opcional): Para reporte de errores a Sentry. (PyPI: [sentry-sdk](https://pypi.org/project/sentry-sdk/))
    - watchdog: Para monitorización de eventos del sistema de archivos. (Context7 ID: /gorakhargosh/watchdog)
    - Nota: La implementación de referencia actual usa polling (os.listdir y asyncio.sleep), pero `watchdog` está disponible y recomendado para una detección de archivos más eficiente basada en eventos del sistema de archivos.
- **Otras herramientas relevantes:** Docker (para despliegue).
**6. Dependencias externas**
- **Otros módulos:**
    - module_scraper: Genera los archivos . json.gz que este módulo consume.
    - module_pipeline: Recibe los datos procesados a través de su API HTTP (/procesar).
- **Servicios externos:** Sentry (opcional, para monitorización de errores).
- **Bases de datos:** No interactúa directamente con ninguna base de datos. Su estado se basa en el sistema de archivos.
**7. Configuración y requisitos especiales**
- **Variables de entorno:**
    - SCRAPER_OUTPUT_DIR: Directorio de entrada donde Scrapy deja los archivos.
    - PIPELINE_PENDING_DIR: Directorio de trabajo para archivos en proceso.
    - PIPELINE_COMPLETED_DIR: Directorio para archivos procesados con éxito.
    - PIPELINE_ERROR_DIR: Directorio para archivos fallidos.
    - PIPELINE_API_URL: URL completa del endpoint /procesar del Pipeline API.
    - POLLING_INTERVAL: Intervalo (segundos) para revisar el directorio de entrada.
    - MAX_RETRIES: Número máximo de reintentos para enviar a la API.
    - RETRY_BACKOFF: Factor exponencial para el delay entre reintentos.
    - LOG_LEVEL: Nivel de detalle para los logs.
    - ENABLE_SENTRY, SENTRY_DSN (Opcional): Para configuración de Sentry.
- **Archivos de configuración:** .env (opcional, para cargar variables de entorno).
- **Otros requisitos:**
    - Acceso de lectura/escritura/borrado a los directorios /data/scrapy_output/pending/, /data/pipeline_input/pending/, /data/pipeline_input/completed/, /data/pipeline_input/error/ (probablemente a través de volúmenes Docker).
    - Conectividad de red al module_pipeline (API HTTP).
**8. Notas adicionales**
- El script está diseñado para ser resiliente usando tenacity para reintentar envíos fallidos a la API.
- Valida la estructura de los datos usando Pydantic antes de enviarlos, previniendo enviar datos malformados al pipeline.
- Gestiona el ciclo de vida de los archivos moviéndolos entre directorios, lo que facilita el seguimiento y la depuración.
- La implementación actual usa polling; podría adaptarse para usar watchdog para una detección de archivos basada en eventos del sistema de archivos, lo cual es generalmente más eficiente.
- Incluye lógica (aunque puede necesitar refinamiento) para reintentar archivos que fallaron previamente.
