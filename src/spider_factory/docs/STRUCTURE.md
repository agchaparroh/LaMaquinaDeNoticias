# Estructura de Spider Factory 2.0

## 📁 Organización de Directorios

```
spider_factory/
├── 📄 __init__.py              # Inicialización del módulo
├── 🔧 Core Components/
│   ├── analyzer.py             # SmartAnalyzer - Análisis inteligente de sitios
│   ├── generator.py            # SpiderGenerator - Generación de spiders
│   ├── patterns.py             # PatternStorage - Gestión de patrones con Redis
│   ├── config.py               # Configuración central y conexión Redis
│   └── models.py               # Modelos Pydantic compartidos
│
├── 🌐 API & Services/
│   ├── api.py                  # FastAPI - Endpoints REST
│   ├── websocket_manager.py    # Gestión de conexiones WebSocket
│   └── batch_processor.py      # Procesamiento masivo de sitios
│
├── 📝 Templates/
│   └── spiders/                # Templates Jinja2 para generación
│       ├── rss_spider.j2       # Template para sitios con RSS
│       ├── scraping_spider.j2  # Template para scraping tradicional
│       └── playwright_spider.j2 # Template para sitios con JavaScript
│
├── 🧪 Testing/
│   ├── tests/                  # Tests unitarios
│   │   ├── __init__.py
│   │   ├── test_analyzer.py    # Tests del analizador
│   │   └── test_patterns.py    # Tests de patrones
│   ├── test_real_sites.py      # Tests con sitios reales
│   ├── test_redis_setup.py     # Verificación de Redis
│   ├── test_runner.py          # Runner de tests sin dependencias
│   ├── integration_test.py     # Tests de integración
│   └── syntax_check.py         # Verificación de sintaxis
│
├── 📂 Output Directories/
│   ├── generated_spiders/      # Spiders generados (vacío, se crea en runtime)
│   └── logs/                   # Logs del sistema (vacío, se crea en runtime)
│
├── 🐳 Docker & Config/
│   ├── Dockerfile              # Imagen Docker del backend
│   ├── docker-compose.yml      # Composición completa
│   ├── docker-compose.dev.yml  # Composición para desarrollo
│   ├── .dockerignore           # Exclusiones Docker
│   ├── .env.example            # Variables de entorno ejemplo
│   ├── requirements.txt        # Dependencias Python
│   └── Makefile               # Comandos útiles
│
└── 📚 Documentation/
    ├── README.md               # Documentación principal
    ├── QUICKSTART.md          # Guía rápida
    ├── API_DOCUMENTATION.md   # Documentación de la API
    ├── STRUCTURE.md           # Este archivo
    ├── TASK_019_OPTIMIZATIONS.md
    ├── TASK_020_COMPLETED.md
    └── bug_report_and_optimizations.md
```

## 🏗️ Componentes Principales

### Core Components
- **analyzer.py**: Implementa SmartAnalyzer con lógica de decisión inteligente
- **generator.py**: Genera código Scrapy usando templates Jinja2
- **patterns.py**: Almacena y gestiona patrones exitosos en Redis
- **config.py**: Configuración centralizada y gestión de Redis
- **models.py**: Modelos Pydantic para validación de datos

### API & Services
- **api.py**: Endpoints REST con FastAPI y documentación automática
- **websocket_manager.py**: Maneja conexiones WebSocket para tiempo real
- **batch_processor.py**: Procesa múltiples sitios de forma asíncrona

### Templates
- Todos los templates están en `templates/spiders/`
- Cada estrategia tiene su propio template optimizado
- Templates incluyen manejo de errores y mejores prácticas

### Testing
- Tests unitarios en `tests/`
- Scripts de testing independientes para diferentes propósitos
- Verificación de sintaxis y tests de integración

## 🔄 Flujo de Trabajo

1. **Análisis** → `analyzer.py` analiza el sitio
2. **Patrones** → `patterns.py` busca/guarda patrones
3. **Generación** → `generator.py` crea el spider
4. **API** → `api.py` expone todo via REST
5. **WebSocket** → `websocket_manager.py` notifica progreso
6. **Batch** → `batch_processor.py` maneja múltiples sitios

## 📝 Notas de Mantenimiento

- Los directorios `generated_spiders/` y `logs/` se crean automáticamente
- Los archivos `.pyc` y `__pycache__/` deben ignorarse (ya en .gitignore)
- Los templates deben mantenerse solo en `templates/spiders/`
- Los tests de integración requieren todas las dependencias instaladas