# Guía de Uso de scrapy-crawl-once

Esta guía explica cómo usar scrapy-crawl-once en tus spiders para prevenir el procesamiento de artículos duplicados.

## Configuración Implementada

El middleware ya está configurado en `settings.py`:

```python
# Spider Middleware
SPIDER_MIDDLEWARES = {
    'scrapy_crawl_once.CrawlOnceMiddleware': 100,
}

# Downloader Middleware
DOWNLOADER_MIDDLEWARES = {
    'scrapy_crawl_once.CrawlOnceMiddleware': 50,
}

# Configuraciones
CRAWL_ONCE_ENABLED = True
CRAWL_ONCE_PATH = project_root / '.scrapy' / 'crawl_once'
CRAWL_ONCE_DEFAULT = False  # Control explícito
```

## Uso en Spiders

### Método 1: Control Explícito (Recomendado)

Marca específicamente qué requests deben ser trackeados:

```python
class MyNewsSpider(scrapy.Spider):
    name = 'my_news'
    
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={'crawl_once': True}  # ← Activar tracking
            )
    
    def parse(self, response):
        # Extraer enlaces de artículos
        for article_url in response.css('a.article-link::attr(href)').getall():
            yield scrapy.Request(
                url=response.urljoin(article_url),
                callback=self.parse_article,
                meta={'crawl_once': True}  # ← Solo procesar una vez
            )
    
    def parse_article(self, response):
        # Extraer datos del artículo
        yield {
            'url': response.url,
            'titulo': response.css('h1::text').get(),
            'contenido': response.css('.article-content::text').getall(),
            # ... más campos
        }
```

### Método 2: Activar para Todo el Spider

Si quieres que TODOS los requests sean trackeados:

```python
class MySpider(scrapy.Spider):
    name = 'my_spider'
    
    custom_settings = {
        'CRAWL_ONCE_DEFAULT': True  # ← Activar para todos los requests
    }
    
    def parse(self, response):
        # Todos los requests serán automáticamente trackeados
        for link in response.css('a::attr(href)').getall():
            yield scrapy.Request(url=response.urljoin(link))
```

### Método 3: Control Granular

Usa diferentes configuraciones según el tipo de request:

```python
def parse(self, response):
    # Páginas de listado: NO trackear (pueden cambiar)
    for page_url in response.css('.pagination a::attr(href)').getall():
        yield scrapy.Request(
            url=response.urljoin(page_url),
            callback=self.parse,
            meta={'crawl_once': False}  # ← No trackear
        )
    
    # Artículos individuales: SÍ trackear
    for article_url in response.css('.article-link::attr(href)').getall():
        yield scrapy.Request(
            url=response.urljoin(article_url),
            callback=self.parse_article,
            meta={'crawl_once': True}  # ← Trackear para evitar duplicados
        )
```

## Opciones Avanzadas

### Custom Key para Tracking

Por defecto se usa el fingerprint del request, pero puedes usar un identificador custom:

```python
yield scrapy.Request(
    url=article_url,
    callback=self.parse_article,
    meta={
        'crawl_once': True,
        'crawl_once_key': f"article_{article_id}"  # ← Key personalizada
    }
)
```

### Custom Value para Almacenar

Por defecto se almacena un timestamp, pero puedes guardar información custom:

```python
yield scrapy.Request(
    url=article_url,
    callback=self.parse_article,
    meta={
        'crawl_once': True,
        'crawl_once_value': {
            'last_crawled': datetime.now().isoformat(),
            'spider_version': '1.0',
            'source': 'sitemap'
        }
    }
)
```

## Base de Datos de Tracking

- **Ubicación**: `.scrapy/crawl_once/`
- **Formato**: SQLite (`<spider_name>.sqlite`)
- **Contenido**: Mapeo de request fingerprints/keys a valores/timestamps

### Resetear Historial

Para hacer que un spider vuelva a procesar todo:

```bash
# Eliminar base de datos específica
rm .scrapy/crawl_once/my_spider.sqlite

# O eliminar todo el historial
rm -rf .scrapy/crawl_once/
```

## Casos de Uso Recomendados

### ✅ Usar crawl_once para:
- Artículos de noticias individuales
- Páginas de productos
- Posts de blogs
- Cualquier contenido que no cambia frecuentemente

### ❌ NO usar crawl_once para:
- Páginas de listado/índice (pueden tener contenido nuevo)
- APIs que devuelven datos dinámicos
- Páginas con contenido que cambia frecuentemente
- Requests de paginación

## Ejemplo Completo: Spider de Noticias

```python
import scrapy
from datetime import datetime

class NoticiasSpider(scrapy.Spider):
    name = 'noticias'
    allowed_domains = ['ejemplo.com']
    start_urls = ['https://ejemplo.com/noticias']
    
    def start_requests(self):
        for url in self.start_urls:
            # Páginas principales: NO trackear
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        # Extraer artículos
        for article in response.css('.article-item'):
            article_url = article.css('a::attr(href)').get()
            article_id = article.css('::attr(data-id)').get()
            
            if article_url and article_id:
                yield scrapy.Request(
                    url=response.urljoin(article_url),
                    callback=self.parse_article,
                    meta={
                        'crawl_once': True,
                        'crawl_once_key': f"article_{article_id}",
                        'article_id': article_id
                    }
                )
        
        # Siguiente página: NO trackear
        next_page = response.css('.pagination .next::attr(href)').get()
        if next_page:
            yield scrapy.Request(
                url=response.urljoin(next_page),
                callback=self.parse
            )
    
    def parse_article(self, response):
        # Este callback solo se ejecutará una vez por artículo
        yield {
            'id': response.meta['article_id'],
            'url': response.url,
            'titulo': response.css('h1::text').get(),
            'fecha': response.css('.date::text').get(),
            'contenido': ' '.join(response.css('.content p::text').getall()),
            'crawled_at': datetime.now().isoformat()
        }
```

## Testing

Usa los scripts proporcionados para verificar que funciona:

```bash
# Verificar configuración
python scripts/verify_crawl_once.py

# Test automatizado completo
python scripts/test_crawl_once.py
```
