# TEMPLATES PARA SPIDERS - La Máquina de Noticias

## 🎯 OBJETIVO
Proporcionar plantillas de código que se integren completamente con la arquitectura existente de La Máquina de Noticias.

## 📋 REQUISITOS DE TODOS LOS TEMPLATES

### **Imports obligatorios:**
```python
# Base del proyecto
from scraper_core.spiders.base.base_article import BaseArticleSpider
from scraper_core.items import ArticuloInItem
from scraper_core.itemloaders import ArticuloInItemLoader

# Utilities del proyecto
from scraper_core.spiders.base.utils import parse_date_string

# Python estándar
import logging
from typing import Iterator, Dict, Any, Optional
from datetime import datetime
import re
```

### **Herencia obligatoria:**
```python
# TODOS los spiders deben heredar de BaseArticleSpider
class MiSpider(BaseArticleSpider):
    # Esto proporciona:
    # - Rotación de user agents
    # - Manejo de errores
    # - Métodos de extracción comunes
    # - Logging configurado
```

## 🎯 TEMPLATE 1: SPIDER CON RSS

### **Cuándo usar:**
- El medio proporciona RSS para la sección
- Se quiere optimizar el consumo del feed

### **Código completo:**
```python
# -*- coding: utf-8 -*-
"""
Spider RSS para [NOMBRE_SECCION] de [NOMBRE_MEDIO]

Este spider convierte el feed RSS de la sección en artículos procesados,
emulando un comportamiento de monitoreo continuo tipo RSS.
"""
import logging
from typing import Iterator, Dict, Any, Optional
from datetime import datetime
import feedparser

from scrapy.http import Response, Request

from scraper_core.items import ArticuloInItem
from scraper_core.spiders.base.base_article import BaseArticleSpider
from scraper_core.spiders.base.utils import parse_date_string

logger = logging.getLogger(__name__)


class [MEDIO][SECCION]RssSpider(BaseArticleSpider):
    """
    Spider RSS para la sección [SECCION] de [MEDIO].
    
    Características:
    - Procesa feed RSS oficial de la sección
    - Extrae contenido completo de cada artículo
    - Deduplicación automática mediante scrapy-crawl-once
    - Ejecución recomendada: cada 30 minutos
    """
    
    name = '[MEDIO_LOWER]_[SECCION_LOWER]_rss'
    allowed_domains = ['[DOMINIO]']
    
    # Configuración específica del spider
    feed_url = '[URL_RSS]'
    medio_nombre = '[NOMBRE_MEDIO]'
    area_geografica = '[AREA_GEOGRAFICA]'
    tipo_medio = '[TIPO_MEDIO]'  # diario/agencia/revista
    target_section = '[SECCION]'
    
    custom_settings = {
        **BaseArticleSpider.custom_settings,
        'DOWNLOAD_DELAY': 2.0,  # Más rápido para RSS
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CLOSESPIDER_ITEMCOUNT': 50,
        'CLOSESPIDER_TIMEOUT': 1800,
        # Deduplicación con scrapy-crawl-once
        'CRAWL_ONCE_ENABLED': True,
        'CRAWL_ONCE_PATH': '.scrapy/crawl_once/',
        'CRAWL_ONCE_DEFAULT': False,  # Control explícito por request
        
        'FEED_EXPORT_ENCODING': 'utf-8',
    }
    
    def start_requests(self) -> Iterator[Request]:
        """Iniciar con el feed RSS."""
        self.logger.info(f"Iniciando spider RSS para {self.medio_nombre} - {self.target_section}")
        yield self.make_request(self.feed_url, self.parse_feed)
    
    def parse_feed(self, response: Response) -> Iterator[Request]:
        """
        Parsear el feed RSS y generar requests para artículos.
        """
        self.logger.info(f"Parseando feed RSS: {response.url}")
        
        try:
            # Parsear feed con feedparser
            feed = feedparser.parse(response.text)
            
            if feed.bozo:
                self.logger.warning(f"Feed RSS mal formado: {feed.bozo_exception}")
            
            entries_count = len(feed.entries)
            self.logger.info(f"Encontradas {entries_count} entradas en el feed")
            
            for entry in feed.entries[:self.custom_settings['CLOSESPIDER_ITEMCOUNT']]:
                # Extraer URL del artículo
                article_url = entry.get('link', '')
                
                if not article_url:
                    continue
                
                # Preparar metadata del RSS
                rss_data = {
                    'title': entry.get('title', ''),
                    'description': entry.get('description', ''),
                    'published': entry.get('published', ''),
                    'author': entry.get('author', ''),
                    'tags': [tag.term for tag in entry.get('tags', [])]
                }
                
                # Request para obtener contenido completo
                yield self.make_request(
                    article_url,
                    self.parse_article,
                    meta={
                        'rss_data': rss_data,
                        'crawl_once': True  # Evitar duplicados
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Error parseando feed RSS: {e}", exc_info=True)
    
    def parse_article(self, response: Response) -> Optional[ArticuloInItem]:
        """
        Extraer contenido completo del artículo.
        Combina datos del RSS con contenido extraído.
        """
        self.logger.info(f"Parseando artículo: {response.url}")
        
        # Obtener metadata del RSS
        rss_data = response.meta.get('rss_data', {})
        
        # Crear item
        item = ArticuloInItem()
        
        # URL y fuente
        item['url'] = response.url
        item['fuente'] = self.name
        
        # Información del medio
        item['medio'] = self.medio_nombre
        item['medio_url_principal'] = f"https://{self.allowed_domains[0]}"
        item['area_geografica'] = self.area_geografica
        item['tipo_medio'] = self.tipo_medio
        
        # Título (priorizar RSS, fallback a extracción)
        item['titular'] = rss_data.get('title') or self.extract_article_title(response)
        
        # Contenido
        item['contenido_texto'] = self.extract_article_content(response)
        item['contenido_html'] = response.text
        
        # Fecha (priorizar RSS, fallback a extracción)
        fecha_rss = rss_data.get('published')
        if fecha_rss:
            item['fecha_publicacion'] = parse_date_string(fecha_rss)
        else:
            item['fecha_publicacion'] = self.extract_publication_date(response)
        
        # Autor (combinar RSS y extracción)
        item['autor'] = rss_data.get('author') or self.extract_author(response)
        
        # Metadata de sección
        item['seccion'] = self.target_section
        item['idioma'] = 'es'
        
        # Etiquetas del RSS
        if rss_data.get('tags'):
            item['etiquetas_fuente'] = rss_data['tags']
        
        # Clasificación
        item['es_opinion'] = self._is_opinion(response)
        item['es_oficial'] = False
        
        # Timestamps
        item['fecha_recopilacion'] = datetime.utcnow()
        
        # Metadata adicional
        item['metadata'] = {
            'spider_type': 'rss',
            'rss_description': rss_data.get('description'),
            'extraction_method': 'rss_plus_scraping'
        }
        
        # Validar antes de retornar
        if self.validate_article_data(dict(item)):
            return item
        else:
            self.logger.warning(f"Artículo inválido descartado: {response.url}")
            return None
    
    def _is_opinion(self, response: Response) -> bool:
        """Detectar si es artículo de opinión."""
        url_lower = response.url.lower()
        indicators = ['/opinion/', '/columna/', '/editorial/', '/tribuna/']
        return any(ind in url_lower for ind in indicators)
```

## 🎯 TEMPLATE 2: SPIDER SCRAPING HTML

### **Cuándo usar:**
- No hay RSS disponible
- El contenido es HTML estático
- No requiere JavaScript

### **Código completo:**
```python
# -*- coding: utf-8 -*-
"""
Spider de scraping para [NOMBRE_SECCION] de [NOMBRE_MEDIO]

Este spider extrae artículos directamente del HTML de la sección,
emulando un comportamiento tipo RSS mediante monitoreo periódico.
"""
import logging
from typing import Iterator, Dict, Any, Optional
from datetime import datetime
import re

from scrapy.http import Response, Request

from scraper_core.items import ArticuloInItem
from scraper_core.spiders.base.base_article import BaseArticleSpider

logger = logging.getLogger(__name__)


class [MEDIO][SECCION]Spider(BaseArticleSpider):
    """
    Spider de scraping para la sección [SECCION] de [MEDIO].
    
    Características:
    - Extrae artículos directamente del HTML
    - Filtrado estricto por sección
    - Deduplicación mediante scrapy-crawl-once
    - Ejecución recomendada: cada 60 minutos
    """
    
    name = '[MEDIO_LOWER]_[SECCION_LOWER]'
    allowed_domains = ['[DOMINIO]']
    start_urls = ['[URL_SECCION]']
    
    # Configuración del medio
    medio_nombre = '[NOMBRE_MEDIO]'
    area_geografica = '[AREA_GEOGRAFICA]'
    tipo_medio = '[TIPO_MEDIO]'
    target_section = '[SECCION]'
    
    # Patrón para filtrar URLs de la sección
    section_pattern = re.compile(r'/[SECCION_PATH]/')
    
    custom_settings = {
        **BaseArticleSpider.custom_settings,
        'DOWNLOAD_DELAY': 3.0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CLOSESPIDER_ITEMCOUNT': 30,
        'CLOSESPIDER_TIMEOUT': 1800,
        # Deduplicación con scrapy-crawl-once
        'CRAWL_ONCE_ENABLED': True,
        'CRAWL_ONCE_PATH': '.scrapy/crawl_once/',
        'CRAWL_ONCE_DEFAULT': False,
        
        'DEPTH_LIMIT': 2,
    }
    
    # Selectores CSS (personalizar según el medio)
    SELECTORS = {
        'article_links': [
            'article a::attr(href)',
            '.article-list a::attr(href)',
            'h2 a::attr(href)',
            '.headline a::attr(href)',
        ],
        'title': [
            'h1::text',
            '.article-title::text',
            '.headline::text',
        ],
        'content': [
            '.article-body p::text',
            '.article-content p::text',
            '.entry-content p::text',
        ],
        'author': [
            '.author::text',
            '.byline::text',
            '.article-author::text',
        ],
        'date': [
            'time::attr(datetime)',
            '.publish-date::text',
            '.article-date::text',
        ]
    }
    
    def parse(self, response: Response) -> Iterator[Request]:
        """
        Extraer enlaces de artículos de la página de sección.
        """
        self.logger.info(f"Parseando sección {self.target_section}: {response.url}")
        
        article_count = 0
        
        # Intentar con cada selector hasta encontrar enlaces
        for selector in self.SELECTORS['article_links']:
            links = response.css(selector).getall()
            
            if not links:
                continue
                
            self.logger.info(f"Encontrados {len(links)} enlaces con selector: {selector}")
            
            for link in links:
                # Construir URL absoluta
                absolute_url = response.urljoin(link)
                
                # Filtrar solo artículos de la sección
                if self._is_section_article(absolute_url):
                    article_count += 1
                    yield self.make_request(
                        absolute_url,
                        self.parse_article,
                        meta={'crawl_once': True}  # Evitar duplicados
                    )
                    
                    # Respetar límite por ejecución
                    if article_count >= self.custom_settings['CLOSESPIDER_ITEMCOUNT']:
                        self.logger.info(f"Alcanzado límite de {article_count} artículos")
                        return
            
            # Si encontramos enlaces, no probar más selectores
            if article_count > 0:
                break
        
        if article_count == 0:
            self.logger.warning("No se encontraron artículos de la sección")
        
        # Buscar paginación
        next_page = response.css('.pagination a.next::attr(href)').get()
        if next_page and article_count < self.custom_settings['CLOSESPIDER_ITEMCOUNT']:
            yield response.follow(next_page, self.parse)
    
    def parse_article(self, response: Response) -> Optional[ArticuloInItem]:
        """
        Extraer datos del artículo.
        """
        self.logger.info(f"Parseando artículo: {response.url}")
        
        # Usar los métodos de BaseArticleSpider
        title = self.extract_article_title(response)
        content = self.extract_article_content(response)
        publication_date = self.extract_publication_date(response)
        author = self.extract_author(response)
        
        # Si falta contenido esencial, descartar
        if not title or not content:
            self.logger.warning(f"Artículo sin título o contenido: {response.url}")
            return None
        
        # Crear item
        item = ArticuloInItem()
        
        # Datos básicos
        item['url'] = response.url
        item['fuente'] = self.name
        item['titular'] = title
        item['contenido_texto'] = content
        item['contenido_html'] = response.text
        
        # Información del medio
        item['medio'] = self.medio_nombre
        item['medio_url_principal'] = f"https://{self.allowed_domains[0]}"
        item['area_geografica'] = self.area_geografica
        item['tipo_medio'] = self.tipo_medio
        
        # Metadata
        item['fecha_publicacion'] = publication_date
        item['autor'] = author or 'Redacción'
        item['idioma'] = 'es'
        item['seccion'] = self.target_section
        
        # Extraer etiquetas si existen
        tags = response.css('.article-tags a::text').getall()
        if tags:
            item['etiquetas_fuente'] = [tag.strip() for tag in tags]
        
        # Clasificación
        item['es_opinion'] = self._is_opinion(response)
        item['es_oficial'] = False
        
        # Timestamps
        item['fecha_recopilacion'] = datetime.utcnow()
        
        # Metadata adicional
        metadata = self._extract_metadata(response)
        metadata.update({
            'spider_type': 'scraping',
            'extraction_method': 'html_parsing'
        })
        item['metadata'] = metadata
        
        # Validar antes de retornar
        if self.validate_article_data(dict(item)):
            return item
        else:
            self.logger.warning(f"Artículo inválido descartado: {response.url}")
            return None
    
    def _is_section_article(self, url: str) -> bool:
        """
        Verificar que la URL pertenece a la sección objetivo.
        """
        return bool(self.section_pattern.search(url))
    
    def _is_opinion(self, response: Response) -> bool:
        """Detectar si es artículo de opinión."""
        url_lower = response.url.lower()
        indicators = ['/opinion/', '/columna/', '/editorial/']
        
        # Verificar URL
        if any(ind in url_lower for ind in indicators):
            return True
        
        # Verificar clases CSS
        opinion_classes = response.css('.opinion-article, .column, .editorial').get()
        return bool(opinion_classes)
```

## 🎯 TEMPLATE 3: SPIDER CON PLAYWRIGHT

### **Cuándo usar:**
- No hay RSS disponible
- El contenido requiere JavaScript
- La página carga dinámicamente

### **Código completo:**
```python
# -*- coding: utf-8 -*-
"""
Spider Playwright para [NOMBRE_SECCION] de [NOMBRE_MEDIO]

Este spider utiliza Playwright para renderizar JavaScript y extraer
contenido dinámico, emulando un comportamiento tipo RSS.
"""
import logging
from typing import Iterator, Dict, Any, Optional
from datetime import datetime
import re

from scrapy.http import Response, Request

from scraper_core.items import ArticuloInItem
from scraper_core.spiders.base.base_article import BaseArticleSpider

logger = logging.getLogger(__name__)


class [MEDIO][SECCION]PlaywrightSpider(BaseArticleSpider):
    """
    Spider con soporte JavaScript para la sección [SECCION] de [MEDIO].
    
    Características:
    - Renderiza JavaScript con Playwright
    - Maneja contenido cargado dinámicamente
    - Filtrado estricto por sección
    - Ejecución recomendada: cada 120 minutos
    """
    
    name = '[MEDIO_LOWER]_[SECCION_LOWER]_playwright'
    allowed_domains = ['[DOMINIO]']
    start_urls = ['[URL_SECCION]']
    
    # Configuración del medio
    medio_nombre = '[NOMBRE_MEDIO]'
    area_geografica = '[AREA_GEOGRAFICA]'
    tipo_medio = '[TIPO_MEDIO]'
    target_section = '[SECCION]'
    
    # Patrón para filtrar URLs
    section_pattern = re.compile(r'/[SECCION_PATH]/')
    
    custom_settings = {
        **BaseArticleSpider.custom_settings,
        'DOWNLOAD_DELAY': 5.0,  # Más lento para Playwright
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CLOSESPIDER_ITEMCOUNT': 20,  # Menos items por ser más lento
        'CLOSESPIDER_TIMEOUT': 1800,
        # Deduplicación con scrapy-crawl-once
        'CRAWL_ONCE_ENABLED': True,
        'CRAWL_ONCE_PATH': '.scrapy/crawl_once/',
        'CRAWL_ONCE_DEFAULT': False,
        
        'DEPTH_LIMIT': 2,
        
        # Configuración Playwright
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'args': ['--disable-blink-features=AutomationControlled']
        },
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 30000,
    }
    
    def start_requests(self) -> Iterator[Request]:
        """Iniciar requests con Playwright."""
        for url in self.start_urls:
            yield Request(
                url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        {"method": "wait_for_load_state", "args": ["networkidle"]},
                        {"method": "wait_for_selector", "args": [".article", {"timeout": 10000}]},
                        {"method": "wait_for_timeout", "args": [2000]},  # Espera adicional
                    ]
                },
                errback=self.handle_error
            )
    
    async def parse(self, response: Response) -> Iterator[Request]:
        """
        Extraer enlaces de artículos después de renderizar JavaScript.
        """
        self.logger.info(f"Parseando sección con Playwright: {response.url}")
        
        # Obtener página de Playwright
        page = response.meta.get("playwright_page")
        
        if page:
            # Scroll para cargar más contenido si es necesario
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
            # Cerrar página para liberar recursos
            await page.close()
        
        article_count = 0
        
        # Buscar enlaces de artículos
        article_links = response.css('article a::attr(href)').getall()
        article_links.extend(response.css('.article-link::attr(href)').getall())
        article_links.extend(response.css('[data-testid="article-link"]::attr(href)').getall())
        
        # Eliminar duplicados
        article_links = list(set(article_links))
        
        self.logger.info(f"Encontrados {len(article_links)} enlaces únicos")
        
        for link in article_links:
            absolute_url = response.urljoin(link)
            
            if self._is_section_article(absolute_url):
                article_count += 1
                
                # Los artículos individuales pueden no necesitar Playwright
                yield self.make_request(
                    absolute_url,
                    self.parse_article,
                    meta={
                        "playwright": False,  # Intentar sin Playwright primero
                        'crawl_once': True  # Evitar duplicados
                    }
                )
                
                if article_count >= self.custom_settings['CLOSESPIDER_ITEMCOUNT']:
                    break
        
        if article_count == 0:
            self.logger.warning("No se encontraron artículos después de renderizar")
    
    def parse_article(self, response: Response) -> Optional[ArticuloInItem]:
        """
        Extraer datos del artículo.
        Si falla, reintentar con Playwright.
        """
        self.logger.info(f"Parseando artículo: {response.url}")
        
        # Intentar extracción normal primero
        title = self.extract_article_title(response)
        content = self.extract_article_content(response)
        
        # Si no hay contenido y no usamos Playwright, reintentar
        if (not content or len(content) < 100) and not response.meta.get('playwright_retried'):
            self.logger.info(f"Contenido insuficiente, reintentando con Playwright: {response.url}")
            
            # Crear nueva request con Playwright
            return Request(
                response.url,
                callback=self.parse_article,
                meta={
                    "playwright": True,
                    "playwright_retried": True,
                    "playwright_page_methods": [
                        {"method": "wait_for_load_state", "args": ["networkidle"]},
                        {"method": "wait_for_selector", "args": [".article-content", {"timeout": 10000}]},
                    ]
                },
                dont_filter=True
            )
        
        if not title or not content:
            self.logger.warning(f"No se pudo extraer contenido de: {response.url}")
            return None
        
        # Crear item
        item = ArticuloInItem()
        
        # Llenar todos los campos
        item['url'] = response.url
        item['fuente'] = self.name
        item['titular'] = title
        item['contenido_texto'] = content
        item['contenido_html'] = response.text
        
        # Información del medio
        item['medio'] = self.medio_nombre
        item['medio_url_principal'] = f"https://{self.allowed_domains[0]}"
        item['area_geografica'] = self.area_geografica
        item['tipo_medio'] = self.tipo_medio
        
        # Extraer metadata
        item['fecha_publicacion'] = self.extract_publication_date(response)
        item['autor'] = self.extract_author(response) or 'Redacción'
        item['idioma'] = 'es'
        item['seccion'] = self.target_section
        
        # Clasificación
        item['es_opinion'] = self._is_opinion(response)
        item['es_oficial'] = False
        
        # Timestamps
        item['fecha_recopilacion'] = datetime.utcnow()
        
        # Metadata
        item['metadata'] = {
            'spider_type': 'playwright',
            'javascript_required': True,
            'extraction_method': 'playwright_rendering'
        }
        
        if self.validate_article_data(dict(item)):
            return item
        else:
            self.logger.warning(f"Artículo inválido: {response.url}")
            return None
    
    def _is_section_article(self, url: str) -> bool:
        """Verificar que pertenece a la sección."""
        return bool(self.section_pattern.search(url))
    
    def _is_opinion(self, response: Response) -> bool:
        """Detectar artículos de opinión."""
        indicators = ['/opinion/', '/columna/', '/tribuna/']
        return any(ind in response.url.lower() for ind in indicators)
```

## 📋 CONFIGURACIÓN COMÚN

### **Settings.py del proyecto:**
```python
# Asegurar que los pipelines estén configurados
ITEM_PIPELINES = {
    'scraper_core.pipelines.validation.DataValidationPipeline': 100,
    'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
    'scraper_core.pipelines.storage.SupabaseStoragePipeline': 300,
}

# Configuración de Supabase (desde variables de entorno)
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
```

### **Programación con cron:**
```bash
# RSS - cada 30 minutos
*/30 * * * * cd /path/to/project && scrapy crawl [medio]_[seccion]_rss

# Scraping HTML - cada hora
0 * * * * cd /path/to/project && scrapy crawl [medio]_[seccion]

# Playwright - cada 2 horas
0 */2 * * * cd /path/to/project && scrapy crawl [medio]_[seccion]_playwright
```

## 🔧 PERSONALIZACIÓN POR MEDIO

### **Selectores específicos comunes:**
```python
# El País
ELPAIS_SELECTORS = {
    'article_links': 'article h2 a::attr(href)',
    'title': 'h1.articulo-titulo::text',
    'content': '.articulo-cuerpo p::text',
}

# La Nación
LANACION_SELECTORS = {
    'article_links': '.archivo article a::attr(href)',
    'title': 'h1.titulo::text',
    'content': '.cuerpo p::text',
}

# Infobae
INFOBAE_SELECTORS = {
    'article_links': 'a[href*="/"]::attr(href)',
    'title': 'h1.article-headline::text',
    'content': '.article-body p::text',
}
```

---

**📚 Documentos relacionados:**
- `MAIN_WORKFLOW.md` - Proceso principal
- `CODE_GENERATION.md` - Generación del código final
- `DEFAULTS_CONFIG.md` - Configuraciones estándar
- `INTEGRATION_GUIDE.md` - Guía de integración
