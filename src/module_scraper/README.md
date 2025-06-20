# Module Scraper - La Máquina de Noticias

Sistema de web scraping especializado en extracción automática de contenido periodístico de medios latinoamericanos.

## 🎯 Propósito

Extrae, procesa y almacena artículos periodísticos de fuentes web predefinidas usando Scrapy con capacidades de renderizado JavaScript vía Playwright. Los datos se validan, limpian y almacenan en Supabase (PostgreSQL + Storage).

## ⚡ Características Principales

- **Web Scraping Inteligente**: Scrapy con Playwright para sitios JavaScript
- **Pipelines de Procesamiento**: Validación, limpieza y almacenamiento automático
- **Rate Limiting Dinámico**: Configuración por dominio para scraping respetuoso
- **Almacenamiento Dual**: Metadatos en PostgreSQL, HTML comprimido en Storage
- **Reintentos Inteligentes**: Tenacity para operaciones críticas con Supabase
- **Monitoreo Integrado**: Logging detallado y rotación automática
- **Dockerizado**: Desarrollo y deployment simplificado

## 🚀 Setup Rápido

### 1. Prerequisitos

- Docker y Docker Compose
- Cuenta de Supabase con proyecto creado

### 2. Configuración

```bash
# Clonar y navegar al directorio
cd module_scraper

# Configurar variables de entorno
cp config/.env config/.env.local
# Editar .env.local con tus credenciales de Supabase

# Levantar entorno de desarrollo
docker-compose --profile dev up -d scraper-dev

# Entrar al contenedor
docker-compose exec scraper-dev bash
```

### 3. Primera Ejecución

```bash
# Dentro del contenedor
scrapy list                    # Ver spiders disponibles
scrapy crawl infobae          # Ejecutar spider de prueba
```

## 📊 Uso Básico

### Spiders Disponibles

```bash
# Medios latinoamericanos
scrapy crawl infobae_spider              # Infobae (Argentina/Latinoamérica)
scrapy crawl elpais_latinoamerica        # El País - sección Latinoamérica  
scrapy crawl elnacional_latinoamerica    # El Nacional - Latinoamérica
scrapy crawl europapress_sudamerica      # Europa Press - Sudamérica
```

### Ejecución con Configuración Personalizada

```bash
# Debug mode con cache habilitado
scrapy crawl infobae -L DEBUG -s HTTPCACHE_ENABLED=True

# Configuración de concurrencia
scrapy crawl infobae -s CONCURRENT_REQUESTS=4 -s DOWNLOAD_DELAY=3

# Usando Playwright para sitios JavaScript
scrapy crawl infobae -s USE_PLAYWRIGHT_FOR_EMPTY_CONTENT=True
```

### Desarrollo y Testing

```bash
# Ejecutar tests
docker-compose --profile test up scraper-test

# Shell interactivo para debugging
scrapy shell "https://www.infobae.com/america/"

# Verificar configuración
scrapy check
```

## ⚙️ Configuración

### Variables de Entorno Principales

```env
# Supabase (requerido)
SUPABASE_URL="https://tu-proyecto.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="tu-service-role-key"
SUPABASE_HTML_BUCKET="html_content"

# Scrapy
LOG_LEVEL="INFO"
CONCURRENT_REQUESTS="8"
DOWNLOAD_DELAY="2"

# Playwright
PLAYWRIGHT_MAX_RETRIES="2"
PLAYWRIGHT_TIMEOUT="30000"
USE_PLAYWRIGHT_FOR_EMPTY_CONTENT="True"
```

### Rate Limiting por Dominio

El sistema incluye configuración específica por dominio en `config/rate_limits/domain_config.py`:

```python
DOMAIN_RATE_LIMITS = {
    'infobae.com': {
        'delay': 3,
        'concurrency': 1
    },
    'elpais.com': {
        'delay': 2,
        'concurrency': 2
    }
}
```

## 🏗️ Arquitectura

### Pipeline de Procesamiento

```
Extracción → Validación → Limpieza → Almacenamiento
    ↓            ↓           ↓           ↓
 Spiders   DataValidation DataCleaning SupabaseStorage
```

### Componentes Principales

- **`scraper_core/spiders/`**: Spiders especializados por medio
- **`scraper_core/pipelines/`**: Procesamiento de datos (validación, limpieza, storage)
- **`scraper_core/middlewares/`**: Playwright, rate limiting, user agents
- **`scraper_core/utils/`**: Clientes Supabase, compresión, logging

### Flujo de Datos

1. **Spider extrae** artículo de sitio web
2. **DataValidationPipeline** valida campos requeridos
3. **DataCleaningPipeline** limpia HTML y normaliza texto
4. **SupabaseStoragePipeline** almacena metadatos en PostgreSQL y HTML comprimido en Storage

## 📁 Estructura del Proyecto

```
module_scraper/
├── scraper_core/           # Código principal
│   ├── spiders/           # Spiders por medio
│   │   ├── base/          # Clases base reutilizables
│   │   └── [medio]_spider.py
│   ├── pipelines/         # Procesamiento de datos
│   ├── middlewares/       # Middlewares personalizados
│   ├── utils/            # Utilidades (Supabase, compresión)
│   ├── items.py          # Definición de datos
│   └── settings.py       # Configuración principal
├── config/               # Configuraciones y entorno
├── tests/               # Testing completo
├── scripts/             # Scripts de utilidad
├── examples/            # Ejemplos de uso
└── docs/               # Documentación técnica
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
docker-compose --profile test up scraper-test

# Tests específicos (dentro del contenedor)
pytest tests/unit/                    # Tests unitarios
pytest tests/integration/             # Tests de integración
pytest tests/test_pipelines/          # Tests de pipelines

# Con coverage
pytest --cov=scraper_core --cov-report=html
```

### Tipos de Tests

- **Unitarios**: Componentes individuales
- **Integración**: Interacción con Supabase
- **End-to-End**: Flujo completo de scraping
- **Pipelines**: Validación y limpieza de datos

## 🔧 Desarrollo

### Crear Nuevo Spider

```python
from scraper_core.spiders.base import BaseArticleSpider
from scraper_core.items import ArticuloInItem

class MiMedioSpider(BaseArticleSpider):
    name = 'mi_medio'
    allowed_domains = ['mimedio.com']
    start_urls = ['https://mimedio.com/noticias']
    
    def parse(self, response):
        item = ArticuloInItem()
        item['url'] = response.url
        item['titular'] = response.css('h1::text').get()
        item['contenido_texto'] = self.extract_article_content(response)
        # Usar métodos heredados para funcionalidad común
        yield item
```

### Debugging

```bash
# Logs detallados
scrapy crawl mi_spider -L DEBUG

# Cache para desarrollo
scrapy crawl mi_spider -s HTTPCACHE_ENABLED=True

# Shell interactivo
scrapy shell "https://mimedio.com/articulo"
```

## 🐛 Troubleshooting

### Problemas Comunes

| Problema | Solución |
|----------|----------|
| Items rechazados | Revisar logs de `DataValidationPipeline` |
| Contenido vacío | Habilitar `USE_PLAYWRIGHT_FOR_EMPTY_CONTENT=True` |
| Error Supabase | Verificar credenciales en `config/.env` |
| Rate limiting | Ajustar `DOWNLOAD_DELAY` y `CONCURRENT_REQUESTS` |

### Logs Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f scraper-dev

# Logs específicos de pipelines
tail -f logs/scraper_core.pipelines.validation.log
```

## 🔄 Pipelines de Datos

### DataValidationPipeline

- Valida campos requeridos: `url`, `titulo`, `medio`, `fecha_publicacion`
- Normaliza URLs y fechas
- Rechaza contenido insuficiente

### DataCleaningPipeline

- Limpia HTML y normaliza whitespace
- Estandariza caracteres especiales
- Deduplica etiquetas

### SupabaseStoragePipeline

- Almacena metadatos en tabla `articulos`
- Comprime y guarda HTML original en Storage
- Implementa reintentos con Tenacity

## 📝 Items de Datos

### ArticuloInItem

Campos principales extraídos:

```python
item['url']                    # URL original
item['titular']                # Título del artículo  
item['medio']                  # Nombre del medio
item['fecha_publicacion']      # Fecha de publicación
item['contenido_texto']        # Texto limpio
item['contenido_html']         # HTML original
item['autor']                  # Autor(es)
item['seccion']               # Sección del medio
item['pais_publicacion']      # País de origen
```

## 🚀 Deployment

### Docker Compose

```bash
# Producción
docker-compose up -d scraper

# Desarrollo con volúmenes
docker-compose --profile dev up -d scraper-dev

# Solo testing  
docker-compose --profile test up scraper-test
```

### Variables de Entorno Críticas

- `SUPABASE_URL`: URL del proyecto Supabase
- `SUPABASE_SERVICE_ROLE_KEY`: Key con permisos de escritura
- `SUPABASE_HTML_BUCKET`: Bucket para almacenar HTML

## 📚 Documentación Adicional

- [STRUCTURE.md](STRUCTURE.md) - Estructura detallada del proyecto
- [CONFIGURACION.md](CONFIGURACION.md) - Guía de configuración completa
- [tests/docs/](tests/docs/) - Documentación de testing
- [examples/](examples/) - Ejemplos de código

## 🤝 Contribuir

1. Fork el repositorio
2. Crear rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'Agregar funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

### Estándares

- Tests para nuevos spiders
- Logging apropiado
- Documentación actualizada
- Respeto por rate limiting

## 📄 Licencia

[Definir licencia del proyecto]

---

**Parte de La Máquina de Noticias** - Sistema integral de procesamiento de información periodística.
