# Sistema de Logging - La Máquina de Noticias

## 🎯 Objetivo

Proporcionar un sistema de logging robusto y escalable para el módulo scraper que facilite el debugging en desarrollo y el monitoreo en producción.

## 🚀 Inicio Rápido

### Configuración Básica

1. **Variables de Ambiente** (opcional):
```bash
# En tu archivo .env o config/.env
ENVIRONMENT=development  # o staging, production
LOG_LEVEL=DEBUG         # Override del nivel por defecto
LOG_TO_FILE=true        # Habilitar logs a archivo en development
```

2. **Uso en tu Spider**:
```python
from scraper_core.spiders.base import BaseArticleSpider

class MySpider(BaseArticleSpider):
    name = 'my_spider'
    
    def parse(self, response):
        self.logger.info(f"Parsing {response.url}")
        # El logger ya está configurado y listo
```

### Verificar la Instalación

```bash
# Ejecutar el script de verificación
python scripts/verify_logging.py

# Ver el spider de ejemplo
scrapy crawl logging_example -L DEBUG
```

## 📁 Estructura de Archivos

```
scraper_core/
├── logging_config.py      # Configuración centralizada
├── log_rotation.py        # Manejo de rotación de logs
├── extensions/
│   └── log_rotation.py    # Extensión de Scrapy para rotación
└── utils/
    └── logging_utils.py   # Utilidades y decoradores

logs/                      # Directorio de logs (creado automáticamente)
├── development/
├── staging/
└── production/
```

## 🔧 Características

### 1. Configuración por Ambiente

| Ambiente | Log Level | Formato | Rotación | A Archivo |
|----------|-----------|---------|----------|-----------|
| development | DEBUG | Detallado | Por tamaño (5MB) | Opcional |
| staging | INFO | Estándar | Diaria (7 días) | Sí |
| production | WARNING | Mínimo | Diaria (30 días) | Sí |

### 2. Decoradores Útiles

#### `@log_execution_time`
```python
@log_execution_time
def slow_operation(self):
    # Se loggea automáticamente si toma > 1 segundo
    time.sleep(2)
```

#### `@log_exceptions`
```python
@log_exceptions(include_traceback=True)
def risky_operation(self):
    # Las excepciones se loggean antes de propagarse
    raise ValueError("Algo salió mal")
```

#### `@log_item_processing`
```python
class MyPipeline:
    @log_item_processing
    def process_item(self, item, spider):
        # Loggea entrada/salida del item automáticamente
        return item
```

### 3. Logging Estructurado

Para sistemas de agregación de logs:

```python
from scraper_core.utils.logging_utils import StructuredLogger

logger = StructuredLogger('my_module')
logger.info('user_action', 
           user_id=123, 
           action='parse_article',
           duration_ms=150)
# Output: {"event": "user_action", "user_id": 123, ...}
```

### 4. Sanitización Automática

```python
from scraper_core.utils.logging_utils import sanitize_log_data

data = {
    'url': 'https://example.com',
    'api_key': 'secret123',  # Será ocultado
    'password': 'mypass'     # Será ocultado
}

safe_data = sanitize_log_data(data)
self.logger.info(f"Data: {safe_data}")
# Output: Data: {'url': 'https://example.com', 'api_key': '***REDACTED***', ...}
```

## 📊 Monitoreo y Análisis

### Ver Logs en Tiempo Real

```bash
# Todos los logs
tail -f logs/development/scrapy_*.log

# Solo errores
tail -f logs/development/scrapy_*.log | grep -E "ERROR|CRITICAL"

# Logs de un spider específico
tail -f logs/development/spiders/infobae_*.log
```

### Analizar Logs Estructurados

```bash
# Contar eventos por tipo
grep '"event":' logs/production/scrapy_*.log | \
  jq -r '.event' | sort | uniq -c

# Ver todos los errores de hoy
grep '"level": "ERROR"' logs/production/scrapy_$(date +%Y-%m-%d).log | \
  jq '.'
```

### Métricas de Performance

```bash
# Tiempos de procesamiento promedio
grep '"event": "item_processed"' logs/production/scrapy_*.log | \
  jq '.processing_time_ms' | \
  awk '{sum+=$1; count++} END {print "Promedio:", sum/count, "ms"}'
```

## 🛠️ Personalización

### Cambiar Nivel de Log Temporalmente

```bash
# Por comando
scrapy crawl my_spider -L WARNING

# Por variable de ambiente
LOG_LEVEL=WARNING scrapy crawl my_spider
```

### Configurar Componentes Específicos

En `settings.py`:

```python
LOGGERS = {
    'scrapy.downloadermiddlewares': 'WARNING',  # Menos verbose
    'scraper_core.pipelines': 'DEBUG',          # Más verbose
    'my_custom_module': 'INFO',                 # Personalizado
}
```

### Habilitar Logs por Spider

```python
LOG_ROTATION_PER_SPIDER = True  # Un archivo por spider
```

## 🐛 Solución de Problemas

### No se crean archivos de log

1. Verifica permisos en el directorio del proyecto
2. En development, asegúrate que `LOG_TO_FILE=true`
3. Revisa que la extensión esté habilitada en `EXTENSIONS`

### Logs muy verbosos

1. Ajusta `LOG_LEVEL` a WARNING o ERROR
2. Configura componentes específicos en `LOGGERS`
3. Desactiva `AUTOTHROTTLE_DEBUG` si está habilitado

### Espacio en disco

1. Revisa la configuración de rotación
2. Ajusta `backup_count` para menos archivos históricos
3. Configura logrotate en sistemas Linux

## 📚 Referencias

- [Ejemplo completo](../examples/logging_example_spider.py)
- [Guía detallada](../docs/logging_guide.md)
- [Tests](../tests/test_logging/)

## ✅ Checklist de Implementación

- [x] Configuración centralizada por ambiente
- [x] Rotación automática de logs
- [x] Decoradores para logging consistente
- [x] Sanitización de datos sensibles
- [x] Logging estructurado para análisis
- [x] Integración con Scrapy
- [x] Tests unitarios
- [x] Documentación completa
- [x] Script de verificación
- [x] Ejemplos de uso

---

💡 **Tip**: Ejecuta `python scripts/verify_logging.py` para verificar que todo esté configurado correctamente.
