# Module Scraper - La Máquina de Noticias

Este módulo es responsable de la recopilación automática de contenido periodístico de fuentes web predefinidas utilizando el framework Scrapy.

## Arquitectura

El módulo está diseñado con una arquitectura de pipelines que procesa los datos en etapas:

1. **Extracción** - Los spiders extraen datos de las fuentes
2. **Validación** - Se validan los campos requeridos y tipos de datos
3. **Limpieza** - Se normalizan y limpian los datos
4. **Almacenamiento** - Se guardan en Supabase

## Estructura del Proyecto

```
module_scraper/
├── scraper_core/
│   ├── spiders/         # Spiders para cada fuente de noticias
│   ├── items.py         # Modelos de datos (ArticuloInItem)
│   ├── pipelines/       # Pipelines de procesamiento
│   │   ├── validation.py    # Pipeline de validación
│   │   ├── cleaning.py      # Pipeline de limpieza
│   │   └── exceptions.py    # Excepciones personalizadas
│   ├── pipelines.py     # Pipeline de almacenamiento (Supabase)
│   ├── itemloaders.py   # Procesadores para campos
│   ├── middlewares.py   # Middlewares personalizados
│   ├── settings.py      # Configuración de Scrapy
│   └── utils/           # Utilidades
├── tests/               # Pruebas unitarias e integración
├── examples/            # Ejemplos de uso
├── docs/                # Documentación
└── requirements.txt     # Dependencias
```

## Pipelines de Procesamiento

### 1. DataValidationPipeline

Valida que los artículos cumplan con los requisitos mínimos:
- Campos requeridos presentes
- Tipos de datos correctos
- Formato de fechas válido
- URLs bien formadas
- Contenido de longitud mínima

### 2. DataCleaningPipeline

Normaliza y limpia los datos validados:
- Elimina etiquetas HTML del texto
- Normaliza espacios y caracteres especiales
- Estandariza fechas a formato ISO
- Limpia URLs (elimina parámetros de tracking)
- Normaliza nombres de autores
- Deduplica y normaliza etiquetas

### 3. SupabaseStoragePipeline

Almacena los datos procesados:
- Guarda metadatos en la tabla `articulos`
- Comprime y almacena HTML original en Storage
- Maneja reintentos con backoff exponencial

Ver [documentación completa de pipelines](docs/pipelines_documentation.md) para más detalles.

## Configuración

### Variables de Entorno

Crear un archivo `.env` basado en `.env.example`:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Logging
LOG_LEVEL=INFO
```

### Settings de Scrapy

Configuración principal en `scraper_core/settings.py`:

```python
# Pipelines activos y su orden
ITEM_PIPELINES = {
    "scraper_core.pipelines.validation.DataValidationPipeline": 100,
    "scraper_core.pipelines.cleaning.DataCleaningPipeline": 200,
    "scraper_core.pipelines.SupabaseStoragePipeline": 300,
}

# Configuración de validación
VALIDATION_MIN_CONTENT_LENGTH = 100
VALIDATION_MIN_TITLE_LENGTH = 10

# Configuración de limpieza
CLEANING_STRIP_HTML = True
CLEANING_NORMALIZE_WHITESPACE = True
```

## Uso

### Ejecutar un Spider

```bash
# Ejecutar spider específico
scrapy crawl nombre_spider

# Con configuración personalizada
scrapy crawl nombre_spider -s LOG_LEVEL=DEBUG
```

### Desarrollo de Nuevos Spiders

1. Crear archivo en `scraper_core/spiders/`
2. Heredar de las clases base apropiadas
3. Definir selectores para extraer campos de `ArticuloInItem`
4. Documentar la estructura del sitio

Ejemplo básico:

```python
from scraper_core.spiders.base import BaseArticleSpider
from scraper_core.items import ArticuloInItem

class MiPeriodicoSpider(BaseArticleSpider):
    name = 'mi_periodico'
    allowed_domains = ['miperiodico.com']
    start_urls = ['https://miperiodico.com/noticias']
    
    def parse_article(self, response):
        item = ArticuloInItem()
        item['url'] = response.url
        item['titular'] = response.css('h1.title::text').get()
        item['contenido_texto'] = response.css('.article-body').get()
        # ... más campos
        yield item
```

## Testing

### Ejecutar Pruebas

```bash
# Todas las pruebas
pytest

# Solo pipelines
pytest tests/test_pipelines/

# Con coverage
pytest --cov=scraper_core
```

### Pruebas de Integración con Supabase

Ver [EJECUTAR_TESTS.md](EJECUTAR_TESTS.md) para instrucciones detalladas.

## Ejemplos

- [pipeline_example.py](examples/pipeline_example.py) - Demostración de pipelines de validación y limpieza

## Monitoreo y Debugging

### Logs

Los logs se configuran en `settings.py`:

```python
LOG_LEVEL = 'INFO'
LOGGERS = {
    'scraper_core.pipelines.validation': 'DEBUG',
    'scraper_core.pipelines.cleaning': 'DEBUG',
}
```

### Estadísticas

Ambos pipelines de validación y limpieza mantienen estadísticas:
- Items procesados/válidos/inválidos
- Tipos de errores encontrados
- Operaciones de limpieza realizadas

## Decisiones de Diseño

1. **Pipelines Modulares**: Cada pipeline tiene una responsabilidad específica
2. **Validación Estricta**: Se prefiere rechazar datos dudosos
3. **Limpieza No Destructiva**: Se preserva el contenido original cuando es posible
4. **Reintentos Inteligentes**: Solo para errores de red, no para errores de datos
5. **Estadísticas Detalladas**: Para identificar problemas comunes

## Troubleshooting

### Items siendo rechazados

1. Revisar logs de validación
2. Verificar campos requeridos
3. Ajustar reglas de validación si es necesario

### Problemas de conexión con Supabase

1. Verificar credenciales en `.env`
2. Revisar logs de Tenacity para reintentos
3. Verificar límites de rate en Supabase

### Rendimiento

1. Ajustar `CONCURRENT_REQUESTS` en settings
2. Considerar deshabilitar operaciones de limpieza innecesarias
3. Revisar tamaño de contenido HTML

## Próximos Pasos

- [ ] Implementar spiders específicos para cada fuente
- [ ] Integrar Playwright para sitios con JavaScript
- [ ] Añadir detección de duplicados (DeltaFetch)
- [ ] Implementar monitoreo con Spidermon
- [ ] Configurar CI/CD
