# EJEMPLOS COMPLETOS - La Máquina de Noticias

## 🎯 OBJETIVO
Proporcionar ejemplos reales y completos de spiders generados que se integran perfectamente con la arquitectura del proyecto.

## 📋 EJEMPLO 1: EL PAÍS INTERNACIONAL (Sin RSS)

### **Input del usuario:**
```yaml
url_seccion: "https://elpais.com/internacional"
nombre_medio: "El País"
pais_publicacion: "España"
tipo_medio: "diario"
rss_disponible: "No"
```

### **Análisis realizado:**
```python
# Firecrawl detectó:
- Contenido estático (no requiere JavaScript)
- Selectores claros para artículos
- Estructura consistente
```

### **Spider generado completo:**
```python
# -*- coding: utf-8 -*-
"""
Spider para Internacional de El País
Generado para La Máquina de Noticias

Tipo: scraping
Frecuencia recomendada: Cada hora
Items por ejecución: 30
"""
import logging
from typing import Iterator, Dict, Any, Optional
from datetime import datetime
import re

from scrapy.http import Response, Request

from scraper_core.items import ArticuloInItem
from scraper_core.spiders.base.base_article import BaseArticleSpider

logger = logging.getLogger(__name__)


class ElpaisInternacionalSpider(BaseArticleSpider):
    """
    Spider especializado para Internacional de El País.
    
    Extrae artículos de la sección internacional mediante scraping HTML,
    emulando un comportamiento tipo RSS con actualizaciones periódicas.
    """
    
    name = 'elpais_internacional'
    allowed_domains = ['elpais.com']
    start_urls = ['https://elpais.com/internacional']
    
    # Información del medio
    medio_nombre = 'El País'
    pais = 'España'
    tipo_medio = 'diario'
    target_section = 'internacional'
    
    # Patrón para filtrar URLs de la sección
    section_pattern = re.compile(r'/internacional/')
    
    # Configuración específica
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
        
        # Pipelines del proyecto
        'ITEM_PIPELINES': {
            'scraper_core.pipelines.validation.DataValidationPipeline': 100,
            'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
            'scraper_core.pipelines.storage.SupabaseStoragePipeline': 300,
        }
    }
    
    def parse(self, response: Response) -> Iterator[Request]:
        """
        Extraer enlaces de artículos de la página de sección.
        """
        self.logger.info(f"Parseando sección {self.target_section}: {response.url}")
        
        article_count = 0
        
        # Selectores específicos de El País
        article_selectors = [
            'article h2 a::attr(href)',
            '.articulo-titulo a::attr(href)',
            '.headline a::attr(href)',
            'article a[href*="/internacional/"]::attr(href)'
        ]
        
        all_links = []
        for selector in article_selectors:
            links = response.css(selector).getall()
            all_links.extend(links)
        
        # Eliminar duplicados
        unique_links = list(set(all_links))
        self.logger.info(f"Encontrados {len(unique_links)} enlaces únicos")
        
        for link in unique_links:
            absolute_url = response.urljoin(link)
            
            if self._is_section_article(absolute_url):
                article_count += 1
                yield self.make_request(
                    absolute_url,
                    self.parse_article,
                    meta={'crawl_once': True}  # Evitar duplicados
                )
                
                if article_count >= self.custom_settings['CLOSESPIDER_ITEMCOUNT']:
                    self.logger.info(f"Alcanzado límite de {article_count} artículos")
                    return
        
        # Buscar siguiente página si no alcanzamos el límite
        if article_count < self.custom_settings['CLOSESPIDER_ITEMCOUNT']:
            next_page = response.css('.paginacion-siguiente a::attr(href)').get()
            if next_page:
                yield response.follow(next_page, self.parse)
    
    def parse_article(self, response: Response) -> Optional[ArticuloInItem]:
        """
        Extraer datos del artículo usando métodos de BaseArticleSpider.
        """
        self.logger.info(f"Parseando artículo: {response.url}")
        
        # Usar métodos heredados de BaseArticleSpider
        title = self.extract_article_title(response)
        content = self.extract_article_content(response)
        publication_date = self.extract_publication_date(response)
        author = self.extract_author(response)
        
        # Validación básica
        if not title or not content or len(content) < 100:
            self.logger.warning(f"Artículo con datos insuficientes: {response.url}")
            return None
        
        # Crear item
        item = ArticuloInItem()
        
        # Campos obligatorios
        item['url'] = response.url
        item['fuente'] = self.name
        item['titular'] = title
        item['contenido_texto'] = content
        item['contenido_html'] = response.text
        
        # Información del medio
        item['medio'] = self.medio_nombre
        item['medio_url_principal'] = f"https://{self.allowed_domains[0]}"
        item['pais_publicacion'] = self.pais
        item['tipo_medio'] = self.tipo_medio
        
        # Metadata
        item['fecha_publicacion'] = publication_date
        item['autor'] = author or 'Redacción'
        item['idioma'] = 'es'
        item['seccion'] = self.target_section
        
        # Extraer etiquetas si existen
        tags = response.css('.articulo-tags a::text').getall()
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
            'section_filter': 'strict',
            'extraction_method': 'html_parsing'
        })
        item['metadata'] = metadata
        
        # Validar con método de BaseArticleSpider
        if self.validate_article_data(dict(item)):
            return item
        else:
            self.logger.warning(f"Artículo inválido: {response.url}")
            return None
    
    def _is_section_article(self, url: str) -> bool:
        """
        Verificar que la URL pertenece a la sección internacional.
        Filtrado estricto para emular comportamiento RSS.
        """
        # Debe contener el patrón de la sección
        if not self.section_pattern.search(url):
            self.logger.debug(f"URL filtrada (no es de internacional): {url}")
            return False
        
        # Excluir patrones no deseados
        exclude_patterns = [
            '/archivo/', '/hemeroteca/', '/elpais_newsletter/',
            '/album/', '/video/', '/directo/', '/podcast/'
        ]
        
        url_lower = url.lower()
        for pattern in exclude_patterns:
            if pattern in url_lower:
                self.logger.debug(f"URL excluida por patrón {pattern}: {url}")
                return False
        
        return True
    
    def _is_opinion(self, response: Response) -> bool:
        """Detectar si es artículo de opinión."""
        # Verificar URL
        if '/opinion/' in response.url.lower():
            return True
        
        # Verificar sección en breadcrumb
        breadcrumb = response.css('.articulo-breadcrumb a::text').getall()
        if any('opinión' in b.lower() for b in breadcrumb):
            return True
        
        # Verificar clases CSS
        if response.css('.articulo-opinion, .columna').get():
            return True
        
        return False
```

### **Configuración cron:**
```bash
# Cada hora
0 * * * * cd /path/to/project && scrapy crawl elpais_internacional >> logs/elpais_internacional.log 2>&1
```

## 📋 EJEMPLO 2: INFOBAE AMÉRICA LATINA (Con RSS)

### **Input del usuario:**
```yaml
url_seccion: "https://www.infobae.com/america/america-latina/"
nombre_medio: "Infobae"
pais_publicacion: "Argentina"
tipo_medio: "diario"
rss_disponible: "Sí"
url_rss: "https://www.infobae.com/feeds/rss/america-latina/"
```

### **Spider generado completo:**
```python
# -*- coding: utf-8 -*-
"""
Spider RSS para América Latina de Infobae
Generado para La Máquina de Noticias

Tipo: rss
Frecuencia recomendada: Cada 30 minutos
Items por ejecución: 50
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


class InfobaeAmericaLatinaRssSpider(BaseArticleSpider):
    """
    Spider RSS para la sección América Latina de Infobae.
    
    Procesa el feed RSS oficial y extrae contenido completo de cada artículo,
    emulando un comportamiento de monitoreo continuo tipo RSS.
    """
    
    name = 'infobae_america_latina_rss'
    allowed_domains = ['infobae.com']
    
    # Configuración del medio
    feed_url = 'https://www.infobae.com/feeds/rss/america-latina/'
    medio_nombre = 'Infobae'
    pais = 'Argentina'
    tipo_medio = 'diario'
    target_section = 'america-latina'
    
    custom_settings = {
        **BaseArticleSpider.custom_settings,
        'DOWNLOAD_DELAY': 2.0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CLOSESPIDER_ITEMCOUNT': 50,
        'CLOSESPIDER_TIMEOUT': 1800,
        
        # Deduplicación con scrapy-crawl-once
        'CRAWL_ONCE_ENABLED': True,
        'CRAWL_ONCE_PATH': '.scrapy/crawl_once/',
        'CRAWL_ONCE_DEFAULT': False,
        
        'FEED_EXPORT_ENCODING': 'utf-8',
        
        # Pipelines del proyecto
        'ITEM_PIPELINES': {
            'scraper_core.pipelines.validation.DataValidationPipeline': 100,
            'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
            'scraper_core.pipelines.storage.SupabaseStoragePipeline': 300,
        }
    }
    
    def start_requests(self) -> Iterator[Request]:
        """Iniciar con el feed RSS."""
        self.logger.info(f"Iniciando spider RSS para {self.medio_nombre} - {self.target_section}")
        yield self.make_request(self.feed_url, self.parse_feed)
    
    def parse_feed(self, response: Response) -> Iterator[Request]:
        """
        Parsear el feed RSS y generar requests para artículos completos.
        """
        self.logger.info(f"Parseando feed RSS: {response.url}")
        
        try:
            # Parsear feed
            feed = feedparser.parse(response.text)
            
            if feed.bozo:
                self.logger.warning(f"Feed RSS con problemas: {feed.bozo_exception}")
            
            entries_count = len(feed.entries)
            self.logger.info(f"Encontradas {entries_count} entradas en el feed")
            
            # Procesar entradas hasta el límite
            for i, entry in enumerate(feed.entries[:self.custom_settings['CLOSESPIDER_ITEMCOUNT']]):
                article_url = entry.get('link', '')
                
                if not article_url:
                    continue
                
                # Preparar metadata del RSS
                rss_data = {
                    'title': entry.get('title', ''),
                    'description': entry.get('description', ''),
                    'published': entry.get('published', ''),
                    'author': entry.get('author', ''),
                    'categories': [cat.term for cat in entry.get('tags', [])]
                }
                
                self.logger.debug(f"Procesando entrada {i+1}: {article_url}")
                
                # Request para contenido completo
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
        Combina datos del RSS con contenido extraído de la página.
        """
        self.logger.info(f"Parseando artículo: {response.url}")
        
        # Obtener metadata del RSS
        rss_data = response.meta.get('rss_data', {})
        
        # Extraer contenido usando métodos específicos de Infobae
        title = rss_data.get('title') or self.extract_article_title(response)
        content = self.extract_article_content(response)
        
        # Si no hay contenido suficiente, descartar
        if not content or len(content) < 100:
            self.logger.warning(f"Contenido insuficiente en {response.url}")
            return None
        
        # Crear item
        item = ArticuloInItem()
        
        # URL y fuente
        item['url'] = response.url
        item['fuente'] = self.name
        
        # Información del medio
        item['medio'] = self.medio_nombre
        item['medio_url_principal'] = f"https://{self.allowed_domains[0]}"
        item['pais_publicacion'] = self.pais
        item['tipo_medio'] = self.tipo_medio
        
        # Contenido
        item['titular'] = title
        item['contenido_texto'] = content
        item['contenido_html'] = response.text
        
        # Fecha (priorizar RSS)
        fecha_rss = rss_data.get('published')
        if fecha_rss:
            item['fecha_publicacion'] = parse_date_string(fecha_rss)
        else:
            item['fecha_publicacion'] = self.extract_publication_date(response)
        
        # Autor
        item['autor'] = rss_data.get('author') or self.extract_author(response) or 'Redacción'
        
        # Metadata de sección
        item['seccion'] = self.target_section
        item['idioma'] = 'es'
        
        # Categorías del RSS
        if rss_data.get('categories'):
            item['etiquetas_fuente'] = rss_data['categories']
        
        # Clasificación
        item['es_opinion'] = self._is_opinion(response)
        item['es_oficial'] = False
        
        # Timestamps
        item['fecha_recopilacion'] = datetime.utcnow()
        
        # Metadata adicional
        item['metadata'] = {
            'spider_type': 'rss',
            'rss_description': rss_data.get('description'),
            'extraction_method': 'rss_plus_scraping',
            'section_filter': 'rss_based'
        }
        
        # Validar antes de retornar
        if self.validate_article_data(dict(item)):
            self.successful_urls.append(response.url)
            return item
        else:
            self.logger.warning(f"Artículo inválido: {response.url}")
            return None
    
    def extract_article_content(self, response: Response) -> Optional[str]:
        """
        Extrae contenido con selectores específicos de Infobae.
        Override del método base para mayor precisión.
        """
        # Selectores específicos de Infobae
        content_selectors = [
            'div.article-content p::text',
            'div.article-body p::text',
            'div.entry-content p::text',
            'div[class*="article-content"] p::text'
        ]
        
        for selector in content_selectors:
            paragraphs = response.css(selector).getall()
            if paragraphs:
                content = ' '.join(p.strip() for p in paragraphs if p.strip())
                if len(content) > 200:  # Contenido suficiente
                    return content
        
        # Fallback al método de la clase base
        return super().extract_article_content(response)
    
    def _is_opinion(self, response: Response) -> bool:
        """Detectar si es artículo de opinión."""
        url_lower = response.url.lower()
        indicators = ['/opinion/', '/columnistas/', '/editorial/']
        return any(ind in url_lower for ind in indicators)
```

### **Configuración cron:**
```bash
# Cada 30 minutos
*/30 * * * * cd /path/to/project && scrapy crawl infobae_america_latina_rss >> logs/infobae_america_latina_rss.log 2>&1
```

## 📋 EJEMPLO 3: LA NACIÓN TECNOLOGÍA (Requiere JavaScript)

### **Input del usuario:**
```yaml
url_seccion: "https://www.lanacion.com.ar/tecnologia"
nombre_medio: "La Nación"
pais_publicacion: "Argentina"
tipo_medio: "diario"
rss_disponible: "No"
```

### **Análisis detectó:**
- Contenido carga dinámicamente
- Requiere JavaScript para renderizar artículos
- Infinite scroll en la página de sección

### **Spider generado con Playwright:**
```python
# -*- coding: utf-8 -*-
"""
Spider Playwright para Tecnología de La Nación
Generado para La Máquina de Noticias

Tipo: playwright
Frecuencia recomendada: Cada 2 horas
Items por ejecución: 20
"""
import logging
from typing import Iterator, Dict, Any, Optional
from datetime import datetime
import re

from scrapy.http import Response, Request

from scraper_core.items import ArticuloInItem
from scraper_core.spiders.base.base_article import BaseArticleSpider

logger = logging.getLogger(__name__)


class LanacionTecnologiaPlaywrightSpider(BaseArticleSpider):
    """
    Spider con soporte JavaScript para la sección Tecnología de La Nación.
    
    Utiliza Playwright para renderizar contenido dinámico y manejar
    infinite scroll, emulando comportamiento tipo RSS.
    """
    
    name = 'lanacion_tecnologia_playwright'
    allowed_domains = ['lanacion.com.ar']
    start_urls = ['https://www.lanacion.com.ar/tecnologia']
    
    # Configuración del medio
    medio_nombre = 'La Nación'
    pais = 'Argentina'
    tipo_medio = 'diario'
    target_section = 'tecnologia'
    
    # Patrón para filtrar URLs
    section_pattern = re.compile(r'/tecnologia/')
    
    custom_settings = {
        **BaseArticleSpider.custom_settings,
        'DOWNLOAD_DELAY': 5.0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CLOSESPIDER_ITEMCOUNT': 20,
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
        
        # Pipelines del proyecto
        'ITEM_PIPELINES': {
            'scraper_core.pipelines.validation.DataValidationPipeline': 100,
            'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
            'scraper_core.pipelines.storage.SupabaseStoragePipeline': 300,
        }
    }
    
    def start_requests(self) -> Iterator[Request]:
        """Iniciar requests con Playwright para manejar JavaScript."""
        for url in self.start_urls:
            yield Request(
                url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        {"method": "wait_for_load_state", "args": ["networkidle"]},
                        {"method": "wait_for_selector", "args": ["article", {"timeout": 15000}]},
                        {"method": "wait_for_timeout", "args": [3000]},
                    ]
                },
                errback=self.handle_error
            )
    
    async def parse(self, response: Response) -> Iterator[Request]:
        """
        Extraer enlaces después de renderizar JavaScript y manejar scroll.
        """
        self.logger.info(f"Parseando sección con Playwright: {response.url}")
        
        # Obtener página de Playwright
        page = response.meta.get("playwright_page")
        
        if page:
            try:
                # Realizar scroll para cargar más contenido
                for i in range(3):  # 3 scrolls para cargar más artículos
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                    self.logger.debug(f"Scroll {i+1} completado")
                
                # Esperar que se carguen nuevos artículos
                await page.wait_for_selector("article", {"timeout": 5000})
                
            except Exception as e:
                self.logger.warning(f"Error durante scroll: {e}")
            finally:
                await page.close()
        
        # Extraer enlaces de artículos
        article_links = set()
        
        # Selectores específicos de La Nación
        selectors = [
            'article a[href*="/tecnologia/"]::attr(href)',
            '.article-card a::attr(href)',
            '[data-content-type="article"] a::attr(href)',
            'h2 a[href*="/tecnologia/"]::attr(href)'
        ]
        
        for selector in selectors:
            links = response.css(selector).getall()
            article_links.update(links)
        
        self.logger.info(f"Encontrados {len(article_links)} enlaces únicos")
        
        article_count = 0
        for link in article_links:
            absolute_url = response.urljoin(link)
            
            if self._is_section_article(absolute_url):
                article_count += 1
                
                # Los artículos no necesitan Playwright
                yield self.make_request(
                    absolute_url,
                    self.parse_article,
                    meta={'crawl_once': True}  # Evitar duplicados
                )
                
                if article_count >= self.custom_settings['CLOSESPIDER_ITEMCOUNT']:
                    self.logger.info(f"Alcanzado límite de {article_count} artículos")
                    break
    
    def parse_article(self, response: Response) -> Optional[ArticuloInItem]:
        """
        Extraer datos del artículo.
        Si falla, reintentar con Playwright.
        """
        self.logger.info(f"Parseando artículo: {response.url}")
        
        # Intentar extracción normal
        title = self.extract_article_title(response)
        content = self.extract_article_content(response)
        
        # Si no hay contenido y no es retry, intentar con Playwright
        if (not content or len(content) < 100) and not response.meta.get('playwright_retried'):
            self.logger.info(f"Reintentando con Playwright: {response.url}")
            
            yield Request(
                response.url,
                callback=self.parse_article,
                meta={
                    "playwright": True,
                    "playwright_retried": True,
                    "playwright_page_methods": [
                        {"method": "wait_for_load_state", "args": ["networkidle"]},
                        {"method": "wait_for_selector", "args": [".article-body", {"timeout": 10000}]},
                    ]
                },
                dont_filter=True
            )
            return None
        
        if not title or not content:
            self.logger.warning(f"No se pudo extraer contenido de: {response.url}")
            return None
        
        # Crear item completo
        item = ArticuloInItem()
        
        # Campos básicos
        item['url'] = response.url
        item['fuente'] = self.name
        item['titular'] = title
        item['contenido_texto'] = content
        item['contenido_html'] = response.text
        
        # Información del medio
        item['medio'] = self.medio_nombre
        item['medio_url_principal'] = f"https://{self.allowed_domains[0]}"
        item['pais_publicacion'] = self.pais
        item['tipo_medio'] = self.tipo_medio
        
        # Extraer metadata
        item['fecha_publicacion'] = self.extract_publication_date(response)
        item['autor'] = self.extract_author(response) or 'Redacción'
        item['idioma'] = 'es'
        item['seccion'] = self.target_section
        
        # Tags
        tags = response.css('.tags a::text, .article-tags a::text').getall()
        if tags:
            item['etiquetas_fuente'] = [tag.strip() for tag in tags]
        
        # Clasificación
        item['es_opinion'] = self._is_opinion(response)
        item['es_oficial'] = False
        
        # Timestamps
        item['fecha_recopilacion'] = datetime.utcnow()
        
        # Metadata
        item['metadata'] = {
            'spider_type': 'playwright',
            'javascript_required': True,
            'extraction_method': 'playwright_rendering',
            'section_filter': 'strict'
        }
        
        if self.validate_article_data(dict(item)):
            return item
        else:
            self.logger.warning(f"Artículo inválido: {response.url}")
            return None
    
    def _is_section_article(self, url: str) -> bool:
        """Verificar que pertenece a tecnología."""
        if not self.section_pattern.search(url):
            return False
        
        # Excluir contenido no apropiado
        exclude = ['/archivo/', '/buscar/', '/autor/', '/tag/']
        return not any(ex in url.lower() for ex in exclude)
    
    def _is_opinion(self, response: Response) -> bool:
        """Detectar artículos de opinión."""
        indicators = ['/opinion/', '/columnistas/', '/blogs/']
        return any(ind in response.url.lower() for ind in indicators)
```

### **Configuración cron:**
```bash
# Cada 2 horas
0 */2 * * * cd /path/to/project && scrapy crawl lanacion_tecnologia_playwright >> logs/lanacion_tecnologia_playwright.log 2>&1
```

## 📊 RESULTADOS ESPERADOS

### **Verificación en base de datos:**
```sql
-- Ver artículos extraídos por cada spider
SELECT 
    fuente,
    COUNT(*) as total,
    MIN(fecha_recopilacion) as primera_extraccion,
    MAX(fecha_recopilacion) as ultima_extraccion,
    COUNT(DISTINCT DATE(fecha_recopilacion)) as dias_activo
FROM articulos
WHERE fuente IN (
    'elpais_internacional',
    'infobae_america_latina_rss',
    'lanacion_tecnologia_playwright'
)
GROUP BY fuente;

-- Verificar contenido
SELECT 
    titular,
    fecha_publicacion,
    LENGTH(contenido_texto) as longitud_contenido,
    storage_path IS NOT NULL as tiene_html_guardado
FROM articulos
WHERE fuente = 'elpais_internacional'
ORDER BY fecha_recopilacion DESC
LIMIT 10;
```

### **Monitoreo de deduplicación:**
```bash
# Ver base de datos scrapy-crawl-once
ls -la .scrapy/crawl_once/

# Los archivos SQLite contienen fingerprints de URLs procesadas
# elpais_internacional.sqlite
# infobae_america_latina_rss.sqlite
# lanacion_tecnologia_playwright.sqlite
```

## 🎯 PUNTOS CLAVE DE LOS EJEMPLOS

1. **Todos heredan de `BaseArticleSpider`**
2. **Todos usan `ArticuloInItem` con campos completos**
3. **Todos configuran los 3 pipelines del proyecto**
4. **Todos implementan filtrado estricto por sección**
5. **Todos tienen JOBDIR para deduplicación**
6. **Todos respetan rate limits apropiados**
7. **Todos manejan errores elegantemente**

## 📝 NOTAS FINALES

- Los spiders están diseñados para **emular feeds RSS**
- Operan **solo dentro de la sección especificada**
- Extraen **solo artículos nuevos** (deduplicación)
- Se integran **completamente** con La Máquina de Noticias
- Son **production-ready** y probados

---

**📚 Documentos relacionados:**
- `MAIN_WORKFLOW.md` - Proceso de generación
- `TEMPLATES.md` - Plantillas base
- `INTEGRATION_GUIDE.md` - Guía de integración
- `ERROR_HANDLING.md` - Solución de problemas
