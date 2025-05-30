# Module Scraper - La Máquina de Noticias

Este módulo es responsable de la recopilación automática de contenido periodístico de fuentes web predefinidas utilizando el framework Scrapy.

## 🚀 Quick Start

```bash
# 1. Configurar el entorno
cp config/.env.test.example config/.env.test
# Editar config/.env.test con tus credenciales

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar un spider de prueba
scrapy crawl infobae

# 4. Ejecutar tests
pytest tests/
```

## 📁 Estructura del Proyecto

La estructura ha sido reorganizada para mayor claridad y mantenibilidad:

```
module_scraper/
├── .dev/                    # Configuraciones de herramientas de desarrollo
├── config/                  # Configuraciones del proyecto y entorno
├── docs/                    # Documentación organizada
│   ├── architecture/        # Documentación técnica y arquitectural
│   └── development/         # Guías para desarrolladores
├── examples/                # Ejemplos de uso y plantillas
├── scraper_core/           # Código principal del scraper
│   ├── items/              # Definiciones de items de datos
│   ├── pipelines/          # Pipelines de procesamiento de datos
│   ├── spiders/            # Spiders para extracción de contenido
│   │   └── base/           # Clases base reutilizables
│   ├── utils/              # Utilidades compartidas
│   └── middlewares/        # Middlewares personalizados
├── scripts/                # Scripts de utilidad
├── tests/                  # Todo lo relacionado con testing y calidad
│   ├── unit/               # Tests unitarios
│   ├── integration/        # Tests de integración
│   ├── e2e/                # Tests end-to-end
│   ├── performance/        # Tests de rendimiento
│   └── fixtures/           # Datos de prueba
└── STRUCTURE.md            # Documentación detallada de la estructura
```

Ver [STRUCTURE.md](STRUCTURE.md) para documentación completa de la organización.

## 🏗️ Arquitectura

El sistema utiliza una arquitectura de pipelines que procesa los datos en etapas secuenciales:

```
Extracción → Validación → Limpieza → Almacenamiento
    ↓            ↓           ↓           ↓
 Spiders   DataValidation DataCleaning SupabaseStorage
```

### Componentes Principales

1. **Spiders** - Extraen datos de fuentes web específicas
2. **Items & ItemLoaders** - Definen estructura de datos y procesamiento
3. **Pipelines** - Procesan, validan y limpian los datos
4. **Storage** - Almacenan datos en Supabase (PostgreSQL + Storage)

## 🔧 Configuración

### Variables de Entorno

Las configuraciones se centralizan en `config/`:

```bash
# Copiar plantilla de configuración
cp config/.env.test.example config/.env.test

# Editar con tus credenciales (NO usar producción para tests)
```

Variables principales:
```env
SUPABASE_URL=https://tu-proyecto-test.supabase.co
SUPABASE_KEY=tu-anon-key
SUPABASE_SERVICE_ROLE_KEY=tu-service-role-key
LOG_LEVEL=INFO
```

Ver [config/README.md](config/README.md) para guía completa de configuración.

### Settings de Scrapy

Configuración principal en `scraper_core/settings.py`:

```python
# Orden de pipelines (prioridad por número)
ITEM_PIPELINES = {
    "scraper_core.pipelines.validation.DataValidationPipeline": 100,
    "scraper_core.pipelines.cleaning.DataCleaningPipeline": 200,
    "scraper_core.pipelines.SupabaseStoragePipeline": 300,
}
```

## 🕷️ Desarrollo de Spiders

### Crear un Nuevo Spider

1. **Usar clases base**: Hereda de `BaseArticleSpider`, `BaseSitemapSpider`, o `BaseCrawlSpider`
2. **Definir selectores**: Configura extractores específicos del sitio
3. **Implementar parsing**: Override métodos según tus necesidades

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
        item['titular'] = response.css('h1::text').get()
        item['contenido_texto'] = self.extract_article_content(response)
        # Usar métodos de la clase base cuando sea posible
        yield item
```

Ver [examples/example_spiders.py](examples/example_spiders.py) para ejemplos completos.

## 🧪 Testing y Calidad

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests específicos
pytest tests/unit/                    # Tests unitarios
pytest tests/integration/             # Tests de integración
pytest tests/test_pipelines/          # Tests de pipelines

# Con coverage
pytest --cov=scraper_core --cov-report=html
```

### Estructura de Tests

- **`tests/unit/`**: Tests unitarios para componentes individuales
- **`tests/integration/`**: Tests de integración con Supabase
- **`tests/test_pipelines/`**: Tests específicos de pipelines
- **`tests/e2e/`**: Tests end-to-end del flujo completo
- **`tests/performance/`**: Tests de rendimiento y carga

Ver [tests/docs/README_tests.md](tests/docs/README_tests.md) para guía completa de testing.

## 📊 Pipelines de Procesamiento

### 1. DataValidationPipeline
- ✅ Valida campos requeridos
- ✅ Verifica tipos de datos
- ✅ Normaliza fechas y URLs
- ✅ Rechaza contenido insuficiente

### 2. DataCleaningPipeline
- 🧹 Limpia HTML y texto
- 🔧 Normaliza caracteres especiales
- 📅 Estandariza fechas
- 🏷️ Deduplica etiquetas

### 3. SupabaseStoragePipeline
- 💾 Almacena metadatos en PostgreSQL
- 🗜️ Comprime y guarda HTML original
- 🔄 Maneja reintentos inteligentes

Ver [docs/architecture/pipelines_documentation.md](docs/architecture/pipelines_documentation.md) para documentación detallada.

## 🚀 Ejecución

### Comandos Básicos

```bash
# Ejecutar spider específico
scrapy crawl infobae

# Con configuración personalizada
scrapy crawl infobae -s LOG_LEVEL=DEBUG -s CONCURRENT_REQUESTS=1

# Listar spiders disponibles
scrapy list

# Verificar configuración
scrapy check
```

### Para Desarrollo

```bash
# Ejecutar con recarga automática
scrapy crawl infobae -s AUTOTHROTTLE_ENABLED=True

# Debug mode completo
scrapy crawl infobae -L DEBUG -s HTTPCACHE_ENABLED=False
```

## 📈 Monitoreo y Debugging

### Logging

```python
# En settings.py
LOG_LEVEL = 'INFO'
LOGGERS = {
    'scraper_core.pipelines.validation': 'DEBUG',
    'scraper_core.pipelines.cleaning': 'DEBUG',
    'scraper_core.utils.supabase_client': 'INFO'
}
```

### Estadísticas

Los pipelines mantienen estadísticas automáticas:
- Items procesados/válidos/inválidos
- Tipos de errores encontrados
- Operaciones de limpieza realizadas
- Tiempos de procesamiento

## 🐛 Troubleshooting

### Problemas Comunes

| Problema | Solución |
|----------|----------|
| Items rechazados | Revisar logs de validación, verificar campos requeridos |
| Conexión Supabase | Verificar credenciales en `config/.env.test` |
| Contenido vacío | Revisar selectores CSS/XPath, considerar usar Playwright |
| Rendimiento lento | Ajustar `CONCURRENT_REQUESTS` y delays |

### Debug Tips

1. **Habilitar cache HTTP** para desarrollo: `HTTPCACHE_ENABLED = True`
2. **Usar Scrapy shell** para probar selectores: `scrapy shell "https://example.com"`
3. **Verificar logs** en orden: spider → pipelines → storage

## 📚 Documentación

- [**Arquitectura**](docs/architecture/) - Decisiones técnicas y componentes
- [**Desarrollo**](docs/development/) - Guías para desarrolladores
- [**Ejemplos**](examples/) - Código de ejemplo y plantillas
- [**Tests**](tests/docs/) - Documentación de testing
- [**Configuración**](config/README.md) - Guía de configuración

## 🛣️ Roadmap

### Próximas Mejoras

- [ ] Sistema de métricas avanzado (Prometheus/Grafana)
- [ ] Cache inteligente de páginas renderizadas
- [ ] Detección automática de sitios que requieren JavaScript
- [ ] Rate limiting dinámico por dominio
- [ ] Integración con Spidermon para alertas

### En Desarrollo

- [ ] Spiders para más fuentes de noticias
- [ ] Mejoras en el sistema de detección de duplicados
- [ ] Dashboard de monitoreo en tiempo real

## 🤝 Contribuir

1. **Fork** el repositorio
2. **Crear rama** para tu feature: `git checkout -b feature/nueva-funcionalidad`
3. **Hacer commit** de cambios: `git commit -am 'Agregar nueva funcionalidad'`
4. **Push** a la rama: `git push origin feature/nueva-funcionalidad`
5. **Crear Pull Request**

## 📄 Licencia

[Especificar licencia del proyecto]

---

**Nota**: Este proyecto es parte de La Máquina de Noticias, un sistema integral de procesamiento de información periodística.
