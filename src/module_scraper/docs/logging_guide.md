# Sistema de Logging para el Módulo Scraper

## Visión General

El sistema de logging del módulo scraper proporciona capacidades completas de registro y debugging para todos los componentes del proyecto. Está basado en el sistema de logging estándar de Scrapy, pero con mejoras adicionales para facilitar el desarrollo y la producción.

## Características Principales

1. **Configuración por Ambiente**: Diferentes niveles de logging para development, staging y production
2. **Rotación de Logs**: Previene que los archivos de log crezcan demasiado
3. **Logging Estructurado**: Soporte para logs en formato JSON para sistemas de agregación
4. **Utilidades de Logging**: Decoradores y mixins para facilitar el logging consistente
5. **Sanitización de Datos**: Automáticamente oculta información sensible en los logs

## Configuración

### Variables de Ambiente

```bash
# Nivel de ambiente (development, staging, production)
ENVIRONMENT=development

# Nivel de log override (opcional)
LOG_LEVEL=DEBUG

# Tipo de formato de log (opcional: detailed, simple, json, production)
LOG_FORMAT_TYPE=detailed

# Habilitar logging a archivo en development
LOG_TO_FILE=true

# Codificación de archivos de log
LOG_FILE_ENCODING=utf-8
```

### Niveles de Log por Ambiente

- **Development**: DEBUG (máximo detalle)
- **Staging**: INFO (información operacional)
- **Production**: WARNING (solo problemas y errores)
- **Test**: INFO (para pruebas automatizadas)

## Uso en Componentes

### En Spiders

```python
from scraper_core.utils.logging_utils import LoggerMixin, log_exceptions

class MySpider(scrapy.Spider, LoggerMixin):
    name = 'my_spider'
    
    def parse(self, response):
        # El logger está disponible automáticamente
        self.logger.info(f"Parsing {response.url}")
        
        # Loggear estadísticas de respuesta
        from scraper_core.utils.logging_utils import log_response_stats
        log_response_stats(response, self.logger)
    
    @log_exceptions(include_traceback=True)
    def parse_article(self, response):
        # Las excepciones serán loggeadas automáticamente
        # ... parsing logic ...
```

### En Pipelines

```python
from scraper_core.utils.logging_utils import log_item_processing, log_execution_time

class MyPipeline:
    
    @log_execution_time
    @log_item_processing
    def process_item(self, item, spider):
        # Logging automático de:
        # - Tiempo de ejecución
        # - Detalles del item (resumidos)
        # - Errores si ocurren
        
        # ... processing logic ...
        return item
```

### En Middlewares

```python
from scraper_core.utils.logging_utils import StructuredLogger

class MyMiddleware:
    def __init__(self):
        self.logger = StructuredLogger(__name__)
    
    def process_request(self, request, spider):
        # Logging estructurado para fácil análisis
        self.logger.info('request_processed',
                        url=request.url,
                        method=request.method,
                        spider=spider.name,
                        headers=dict(request.headers))
```

## Decoradores Disponibles

### @log_execution_time

Registra el tiempo de ejecución de una función:

```python
@log_execution_time
def slow_operation():
    # Si toma más de 1 segundo, se loggea como WARNING
    time.sleep(2)
```

### @log_exceptions

Captura y loggea excepciones con contexto:

```python
@log_exceptions(log_level=logging.ERROR, include_traceback=True)
def risky_operation():
    # Las excepciones se loggean antes de propagarse
    raise ValueError("Something went wrong")
```

### @log_item_processing

Específico para pipelines, loggea el procesamiento de items:

```python
@log_item_processing
def process_item(self, item, spider):
    # Loggea un resumen del item al entrar y salir
    return item
```

## Sanitización de Datos Sensibles

El sistema automáticamente oculta información sensible:

```python
from scraper_core.utils.logging_utils import sanitize_log_data

data = {
    'url': 'https://example.com',
    'api_key': 'secret123',  # Será ocultado
    'password': 'mypass',    # Será ocultado
    'content': 'public data'
}

safe_data = sanitize_log_data(data)
# safe_data['api_key'] == '***REDACTED***'
# safe_data['password'] == '***REDACTED***'
```

## Rotación de Logs

### Configuración Automática

La rotación se configura automáticamente según el ambiente:

- **Development**: Por tamaño (5MB por archivo, 3 archivos)
- **Staging**: Diaria (7 días de retención)
- **Production**: Diaria (30 días de retención)

### Configuración Manual

Para sistemas Linux en producción, se puede usar logrotate:

```bash
# Generar configuración de logrotate
python scraper_core/log_rotation.py /path/to/project

# Instalar en el sistema
sudo cp config/logrotate.conf /etc/logrotate.d/scrapy-scraper
```

## Estructura de Archivos de Log

```
logs/
├── development/
│   ├── scrapy_2024-01-01.log
│   └── spiders/
│       └── infobae_2024-01-01.log
├── staging/
│   └── scrapy_2024-01-01.log
└── production/
    ├── scrapy_2024-01-01.log
    └── scrapy_2024-01-01.log.1.gz  # Rotado y comprimido
```

## Mejores Prácticas

### 1. Usa el Nivel Apropiado

```python
# DEBUG: Información detallada para debugging
self.logger.debug(f"Processing item with fields: {item.keys()}")

# INFO: Eventos importantes del flujo normal
self.logger.info(f"Spider started: {self.name}")

# WARNING: Situaciones inesperadas pero recuperables
self.logger.warning(f"Missing optional field 'author' in {item['url']}")

# ERROR: Errores que requieren atención
self.logger.error(f"Failed to connect to database: {e}")

# CRITICAL: Errores que detienen el sistema
self.logger.critical("Configuration file not found - cannot continue")
```

### 2. Incluye Contexto Relevante

```python
# Malo
self.logger.error("Failed to process")

# Bueno
self.logger.error(f"Failed to process item from {spider.name}: {item.get('url')}", 
                 exc_info=True)
```

### 3. No Loggees Información Sensible

```python
# Malo
self.logger.info(f"Connecting with password: {password}")

# Bueno
self.logger.info("Connecting to database")
```

### 4. Usa Logging Estructurado para Análisis

```python
# Para logs que serán analizados por herramientas
structured_logger.info('item_processed',
                      spider=spider.name,
                      url=item['url'],
                      duration_ms=processing_time * 1000,
                      success=True)
```

## Debugging

### Ver Logs en Tiempo Real

```bash
# Desarrollo
tail -f logs/development/scrapy_*.log

# Ver solo errores
tail -f logs/development/scrapy_*.log | grep -E "(ERROR|CRITICAL)"

# Ver logs de un spider específico
tail -f logs/development/spiders/infobae_*.log
```

### Cambiar Nivel de Log Temporalmente

```bash
# Por línea de comandos
scrapy crawl my_spider -L DEBUG

# Por variable de ambiente
LOG_LEVEL=DEBUG scrapy crawl my_spider
```

### Analizar Logs Estructurados

```bash
# Buscar todos los errores de items
grep '"event": "item_error"' logs/production/scrapy_*.log | jq '.'

# Contar items procesados por spider
grep '"event": "item_processed"' logs/production/scrapy_*.log | \
  jq -r '.spider' | sort | uniq -c
```

## Solución de Problemas

### Los logs no se están escribiendo a archivo

1. Verifica la variable `ENVIRONMENT` (production/staging escriben a archivo por defecto)
2. En development, establece `LOG_TO_FILE=true`
3. Verifica permisos en el directorio `logs/`

### Los logs son demasiado verbosos

1. Ajusta el nivel de log: `LOG_LEVEL=WARNING`
2. Configura niveles específicos por componente en `settings.py`

### No veo información de debugging

1. Asegúrate de estar en ambiente development
2. Verifica que `LOG_LEVEL=DEBUG`
3. Usa los decoradores de logging para más contexto

## Testing

Ejecuta las pruebas del sistema de logging:

```bash
# Todas las pruebas de logging
python -m pytest tests/test_logging/

# Prueba específica
python -m pytest tests/test_logging/test_logging_config.py::TestLoggingConfig
```

## Referencias

- [Documentación de Logging de Scrapy](https://docs.scrapy.org/en/latest/topics/logging.html)
- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [Structured Logging Best Practices](https://www.structlog.org/en/stable/why.html)
