# Module Connector

**Bridge between module_scraper and module_pipeline** (según documentación en `src/main.py`)

## Descripción

Según el código fuente en `src/main.py`, este módulo:

- Monitorea un directorio en busca de archivos `.json.gz` que contienen artículos
- Los valida usando modelos definidos en `src/models.py`
- Los envía al Pipeline API para procesamiento

## Estructura de Archivos Presente

```
module_connector/
├── src/
│   ├── main.py              # Punto de entrada principal
│   ├── config.py            # Configuración via variables de entorno
│   └── models.py            # Modelo ArticuloInItem para validación
├── requirements.txt         # Dependencias Python
├── Dockerfile              # Configuración de contenedor
├── docker-compose.yml      # Definición de servicios
├── nginx.conf              # Configuración nginx
├── .env.example            # Template de variables de entorno
├── .dockerignore           # Exclusiones para Docker build
├── .gitignore             # Exclusiones para Git (creado)
├── README.md              # Este archivo
└── DEPLOYMENT.md          # Guía de despliegue
```

## Dependencias (desde requirements.txt)

- `aiohttp==3.12.6` - HTTP client for async API calls
- `tenacity==9.1.2` - Robust retry logic  
- `loguru==0.7.3` - Logging
- `python-dotenv==1.1.0` - Environment variables
- `pydantic==2.11.5` - Data validation
- `python-dateutil==2.8.2` - Date parsing utilities
- `sentry-sdk==2.29.1` - Error monitoring (optional)
- `watchdog==6.0.0` - File system monitoring (for future use)

## Variables de Entorno (desde config.py)

| Variable | Default | Descripción según código |
|----------|---------|---------------------------|
| `SCRAPER_OUTPUT_DIR` | `/data/scrapy_output/pending` | Directorio de salida del scraper |
| `PIPELINE_PENDING_DIR` | `/data/pipeline_input/pending` | Directorio de archivos pendientes |
| `PIPELINE_COMPLETED_DIR` | `/data/pipeline_input/completed` | Directorio de archivos completados |
| `PIPELINE_ERROR_DIR` | `/data/pipeline_input/error` | Directorio de archivos con error |
| `PIPELINE_API_URL` | `http://module_pipeline:8003` | URL del Pipeline API |
| `POLLING_INTERVAL` | `5` | Intervalo de polling en segundos |
| `MAX_RETRIES` | `3` | Máximo número de reintentos |
| `RETRY_BACKOFF` | `2.0` | Tiempo base entre reintentos |
| `LOG_LEVEL` | `INFO` | Nivel de logging |
| `ENABLE_SENTRY` | `false` | Habilitar monitoreo Sentry |
| `SENTRY_DSN` | `` | DSN de Sentry |

## Modelo de Datos (desde models.py)

El código define un modelo `ArticuloInItem` con estos campos principales:

**Campos requeridos:**
- `medio: str` - Nombre del medio
- `pais_publicacion: str` - País de publicación
- `tipo_medio: str` - Tipo de medio
- `titular: str` - Título del artículo
- `fecha_publicacion: datetime` - Fecha de publicación
- `contenido_texto: str` - Texto completo del artículo

**Campos opcionales incluyen:**
- `url`, `autor`, `idioma`, `seccion`, `etiquetas_fuente`, `resumen`, `categorias_asignadas`, etc.

## Configuración Docker

**Desde Dockerfile:**
- Imagen base: `python:3.9-slim`
- Usuario no-root: `connector`
- Directorio de trabajo: `/app/src`
- Comando: `python main.py`
- Health check: Verifica existencia de `/data/pipeline_input/pending`

**Desde docker-compose.yml:**
- Servicio principal: `module-connector`
- Puerto Pipeline API: `8001` (según docker-compose)
- Red: `module-network`
- Volúmenes: `./data:/data` y `./logs:/app/logs`

## Funciones Principales (desde main.py)

El código implementa estas funciones:

- `monitor_directory()` - Monitorea directorio por archivos .json.gz
- `process_file()` - Procesa archivos individuales
- `send_to_pipeline()` - Envía artículos al Pipeline API
- `move_file()` - Mueve archivos según resultado de procesamiento

## Configuración de Logging (desde main.py)

- Console handler con formato específico
- File handler: `logs/connector.log` con rotación de 10 MB
- Retención: 1 semana

## Archivos Referenciados Pero No Encontrados

**NOTA**: Los siguientes archivos se mencionan en la configuración pero NO están presentes:

- `mock_pipeline.py` (referenciado en docker-compose.yml)
- Archivos de tests (mencionados en .dockerignore pero no existen)
- `demo.py` (mencionado en .dockerignore pero no existe)

## Endpoints Esperados del Pipeline API (desde main.py)

El código espera:
- **Endpoint**: `POST {PIPELINE_API_URL}/procesar_articulo`
- **Content-Type**: `application/json`
- **Body**: `{"articulo": {...}}`
- **Respuestas esperadas**: 202 (éxito), 400 (validación), 500/503 (reintentar)

## Ejecución

**Local:**
```bash
cd src
python main.py
```

**Docker:**
```bash
docker-compose up --build
```

## Preguntas Sobre Funcionalidad No Clara

**Estas funcionalidades no están claras en el código y requieren aclaración:**

1. **¿El módulo ha sido probado funcionalmente?** (No se encuentran archivos de tests)
2. **¿Debe crearse el archivo `mock_pipeline.py` referenciado en docker-compose.yml?**
3. **¿Cuál es el estado real de implementación del módulo?** (No se puede verificar sin ejecutarlo)
4. **¿La integración con module_scraper y module_pipeline está verificada?** (No hay evidencia de testing de integración)

---

**NOTA**: Esta documentación se basa únicamente en el código fuente presente. Para información sobre funcionalidad verificada, testing, o estado de producción, se requiere información adicional.
