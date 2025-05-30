# Module Scraper - Estructura del Proyecto

## Estructura Reorganizada

```
module_scraper/
├── .dev/                          # Configuraciones de herramientas de desarrollo
│   ├── .cursor/                   # Configuración de Cursor/VS Code
│   ├── .roo/                      # Configuración de Roo
│   ├── .roomodes                  # Modos de Roo
│   ├── .taskmasterconfig          # Configuración de TaskMaster
│   └── .windsurfrules             # Reglas de Windsurf
├── .git/                          # Control de versiones Git
├── config/                        # Configuraciones del proyecto
│   ├── .env.test                  # Variables de entorno para tests
│   └── .env.test.example          # Plantilla de configuración
├── docs/                          # Documentación del proyecto
│   ├── architecture/              # Documentación de arquitectura
│   │   ├── decision_spidermon_monitoring.md
│   │   └── pipelines_documentation.md
│   └── development/               # Guías de desarrollo
│       └── items_loaders_guide.md
├── examples/                      # Ejemplos de uso
│   ├── example_spiders.py
│   ├── item_loader_usage.py
│   └── pipeline_example.py
├── scraper_core/                  # Código principal del scraper
│   ├── items/                     # Definiciones de items
│   │   ├── articulo.py
│   │   └── __init__.py
│   ├── middlewares/               # Middlewares personalizados
│   │   ├── playwright_custom_middleware.py
│   │   └── __init__.py
│   ├── monitors/                  # Monitores de Spidermon
│   │   └── spider_monitors.py
│   ├── pipelines/                 # Pipelines de procesamiento
│   │   ├── cleaning.py
│   │   ├── exceptions.py
│   │   ├── validation.py
│   │   └── __init__.py
│   ├── schemas/                   # Esquemas de validación
│   ├── spiders/                   # Spiders de scraping
│   │   ├── base/                  # Clases base para spiders
│   │   │   ├── base_article.py
│   │   │   ├── base_crawl.py
│   │   │   ├── base_sitemap.py
│   │   │   ├── utils.py
│   │   │   └── README.md
│   │   ├── infobae_spider.py
│   │   └── __init__.py
│   ├── utils/                     # Utilidades compartidas
│   │   ├── compression.py
│   │   ├── supabase_client.py
│   │   └── __init__.py
│   ├── itemloaders.py             # Cargadores de items
│   ├── items.py                   # Items principales
│   ├── middlewares.py             # Middlewares principales
│   ├── pipelines.py               # Pipelines principales
│   ├── settings.py                # Configuración de Scrapy
│   └── __init__.py
├── scripts/                       # Scripts de utilidad
│   └── example_prd.txt
├── tests/                         # Tests y calidad del código
│   ├── .pytest_cache/             # Cache de pytest
│   ├── config/                    # Tests de configuración
│   │   ├── test_env.py
│   │   └── test_settings.py
│   ├── db_tests/                  # Tests de base de datos
│   │   └── test_schema_fix.py
│   ├── docs/                      # Documentación de tests
│   │   ├── EJECUTAR_TESTS.md
│   │   └── README_tests.md
│   ├── e2e/                       # Tests end-to-end
│   ├── fixtures/                  # Datos de prueba
│   ├── integration/               # Tests de integración
│   │   ├── test_conexion.py
│   │   ├── test_conexion_directa.py
│   │   ├── test_supabase_integration.py
│   │   └── __init__.py
│   ├── performance/               # Tests de rendimiento
│   ├── scripts/                   # Scripts de testing
│   │   ├── diagnostico.py
│   │   ├── run_integration_tests.py
│   │   ├── run_unittest.py
│   │   ├── verificar_tests.py
│   │   └── verify_fix.py
│   ├── test_pipelines/            # Tests de pipelines
│   │   ├── test_cleaning.py
│   │   ├── test_validation.py
│   │   └── __init__.py
│   ├── test_spiders/              # Tests de spiders
│   │   ├── test_base_article.py
│   │   └── __init__.py
│   ├── unit/                      # Tests unitarios
│   │   ├── scraper_core/
│   │   │   ├── utils/
│   │   │   │   ├── test_supabase_client.py
│   │   │   │   └── __init__.py
│   │   │   └── __init__.py
│   │   ├── test_items_loaders.py
│   │   └── __init__.py
│   ├── utils/                     # Utilidades de testing
│   │   ├── test_compression.py
│   │   ├── test_supabase_client.py
│   │   └── __init__.py
│   └── __init__.py
├── .gitignore                     # Archivos ignorados por Git
├── Dockerfile                     # Configuración de Docker
├── README.md                      # Documentación principal
├── requirements.txt               # Dependencias de Python
├── scrapy.cfg                     # Configuración de Scrapy
└── STRUCTURE.md                   # Este archivo (estructura del proyecto)
```

## Principios de Organización

### 1. Separación por Función
- **`.dev/`**: Todo lo relacionado con herramientas de desarrollo
- **`config/`**: Configuraciones del proyecto y entorno
- **`docs/`**: Documentación organizada por tipo
- **`tests/`**: Todo lo relacionado con calidad y testing
- **`scraper_core/`**: Código principal del scraper

### 2. Claridad y Mantenibilidad
- Estructura jerárquica clara
- Nombres descriptivos
- Agrupación lógica de archivos relacionados

### 3. Escalabilidad
- Estructura preparada para crecimiento
- Separación clara entre tipos de tests
- Organización modular

## Beneficios de esta Estructura

1. **Comprensión Rápida**: Cualquier desarrollador puede entender la organización al primer vistazo
2. **Mantenimiento Simplificado**: Archivos relacionados están agrupados
3. **Configuración Centralizada**: Todas las configuraciones en lugares predecibles
4. **Testing Organizado**: Tests separados por tipo y propósito
5. **Desarrollo Limpio**: Herramientas de desarrollo no interfieren con el código principal

## Uso de Directorios

### `.dev/`
Contiene configuraciones de herramientas de desarrollo que no deben afectar el funcionamiento del scraper en producción.

### `config/`
Centralizamos todas las configuraciones de entorno y proyecto.

### `docs/`
- `architecture/`: Decisiones técnicas y documentación de componentes
- `development/`: Guías para desarrolladores

### `tests/`
- `unit/`: Tests unitarios para componentes individuales
- `integration/`: Tests de integración entre componentes
- `e2e/`: Tests end-to-end del flujo completo
- `performance/`: Tests de rendimiento y carga
- `fixtures/`: Datos de prueba reutilizables

### `scraper_core/`
El núcleo del sistema de scraping con estructura modular clara.
