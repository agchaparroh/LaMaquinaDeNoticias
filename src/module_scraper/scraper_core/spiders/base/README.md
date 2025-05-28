# Base Spider Classes - La Máquina de Noticias

Este módulo proporciona clases base para crear spiders de Scrapy especializados en la extracción de artículos de noticias.

## Clases Base Disponibles

### 1. BaseArticleSpider

Spider base para extracción directa de artículos. Ideal cuando tienes URLs específicas de artículos.

**Características:**
- Rotación automática de user agents
- Métodos de extracción comunes (título, contenido, autor, fecha)
- Manejo de errores y logging mejorado
- Respeto por robots.txt
- Validación de datos extraídos

**Ejemplo de uso:**

```python
from scraper_core.spiders.base import BaseArticleSpider

class MiSpider(BaseArticleSpider):
    name = 'mi_periodico'
    allowed_domains = ['miperiodico.com']
    start_urls = ['https://miperiodico.com/articulo-1']
    
    def parse(self, response):
        article_data = {
            'url': response.url,
            'title': self.extract_article_title(response),
            'content': self.extract_article_content(response),
            'author': self.extract_author(response),
            'publication_date': self.extract_publication_date(response),
        }
        
        if self.validate_article_data(article_data):
            yield article_data
```

### 2. BaseSitemapSpider

Spider base para descubrir artículos a través de sitemaps XML. Ideal para sitios de noticias con sitemaps bien estructurados.

**Características:**
- Parseo automático de sitemaps
- Filtrado por fecha (últimos N días)
- Soporte para robots.txt con sitemaps
- Reglas de sitemap personalizables

**Ejemplo de uso:**

```python
from scraper_core.spiders.base import BaseSitemapSpider

class MiSitemapSpider(BaseSitemapSpider):
    name = 'mi_periodico_sitemap'
    allowed_domains = ['miperiodico.com']
    sitemap_urls = ['https://miperiodico.com/sitemap.xml']
    
    # Opcional: diferentes parsers para diferentes secciones
    sitemap_rules = [
        ('/deportes/', 'parse_deportes'),
        ('/politica/', 'parse_politica'),
    ]
    
    def parse_deportes(self, response):
        # Lógica específica para artículos de deportes
        pass
```

**Parámetros de línea de comandos:**
```bash
scrapy crawl mi_periodico_sitemap -a days_back=14
```

### 3. BaseCrawlSpider

Spider base para crawlear un sitio completo siguiendo enlaces. Ideal para sitios sin sitemap o para descubrimiento exhaustivo.

**Características:**
- Seguimiento inteligente de enlaces
- Control de profundidad
- Límite de páginas configurado
- Detección automática de artículos
- Estadísticas de crawl

**Ejemplo de uso:**

```python
from scraper_core.spiders.base import BaseCrawlSpider

class MiCrawlSpider(BaseCrawlSpider):
    name = 'mi_periodico_crawl'
    allowed_domains = ['miperiodico.com']
    start_urls = ['https://miperiodico.com/']
    
    # Patrones personalizados para identificar artículos
    article_url_patterns = [
        r'/noticia-\d+\.html',
        r'/\d{4}/\d{2}/[\w-]+$',
    ]
    
    custom_settings = {
        **BaseCrawlSpider.custom_settings,
        'DEPTH_LIMIT': 2,
        'CLOSESPIDER_PAGECOUNT': 50,
    }
```

**Parámetros de línea de comandos:**
```bash
scrapy crawl mi_periodico_crawl -a max_pages=100 -a follow_links=true
```

## Métodos Comunes de Extracción

Todas las clases base incluyen estos métodos:

- `extract_article_title(response)`: Extrae el título del artículo
- `extract_article_content(response)`: Extrae el contenido principal
- `extract_author(response)`: Extrae el autor
- `extract_publication_date(response)`: Extrae la fecha de publicación
- `extract_article_metadata(response)`: Extrae metadatos adicionales
- `validate_article_data(data)`: Valida los datos extraídos
- `make_request(url, callback=None, **kwargs)`: Crea requests con configuración apropiada

## Configuración Personalizada

Cada spider puede sobrescribir la configuración:

```python
class MiSpider(BaseArticleSpider):
    custom_settings = {
        'DOWNLOAD_DELAY': 2,  # Segundos entre requests
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'ROBOTSTXT_OBEY': True,
        'USER_AGENT': 'MiBot/1.0',
    }
```

## Utilidades Disponibles

El módulo incluye funciones de utilidad en `base.utils`:

```python
from scraper_core.spiders.base.utils import (
    parse_date_string,  # Parsea fechas en múltiples formatos
    clean_text,  # Limpia y normaliza texto
    extract_domain,  # Extrae dominio de URL
    is_valid_article_url,  # Valida si una URL es de artículo
    normalize_url,  # Normaliza URLs
    estimate_reading_time,  # Estima tiempo de lectura
)
```

## Mejores Prácticas

1. **Respeta robots.txt**: Siempre mantén `ROBOTSTXT_OBEY = True`
2. **Usa delays apropiados**: No sobrecargues los servidores
3. **Valida los datos**: Usa `validate_article_data()` antes de yield
4. **Maneja errores**: Implementa manejo de errores específico del sitio
5. **Logging detallado**: Usa el logger para debugging

## Ejecutar Tests

```bash
cd src/module_scraper
python -m pytest tests/
```

## Ejemplos Completos

Ver el directorio `examples/` para ejemplos más detallados de implementación.
