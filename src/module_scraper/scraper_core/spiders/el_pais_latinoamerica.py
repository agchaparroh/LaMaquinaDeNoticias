"""
Spider generado automáticamente por Spider Factory 2.0
Medio: El País
Sección: latinoamerica
Fecha: 2025-07-01T19:30:00.123456
Estrategia: rss

GENERADO AUTOMÁTICAMENTE - NO EDITAR MANUALMENTE
Los cambios manuales se perderán en la próxima generación
"""
import re
import scrapy
from scrapy import signals
from scrapy.exceptions import CloseSpider
import feedparser
from datetime import datetime
import logging
from typing import Dict, Any, Optional, Iterator

# Para métodos avanzados de evasión
try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False

import requests


class ElPaisLatinoamericaSpider(scrapy.Spider):
    """
    Spider RSS para El País - latinoamerica
    
    Utiliza feeds RSS para obtener artículos de noticias.
    Área geográfica: HISPANOAMERICA
    Tipo de medio: diario
    """
    name = "el_pais_latinoamerica"
    allowed_domains = ["elpais.com", "feeds.elpais.com"]
    
    # Configuración
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,  # Deshabilitado para feeds RSS
        'CONCURRENT_REQUESTS': 6,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 3,
        'DOWNLOAD_DELAY': 1.5,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
        'COOKIES_ENABLED': True,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
        
        # Headers realistas para evasión
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8,en-US;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Pragma': 'no-cache',
            'DNT': '1',
        },
        
        # Scrapy-crawl-once configuration
        'CRAWL_ONCE_ENABLED': True,
        'CRAWL_ONCE_PATH': f'.scrapy/crawl_once/el_pais_latinoamerica',
        'CRAWL_ONCE_DEFAULT': False,
        
        # Configuración de encoding
        'FEED_EXPORT_ENCODING': 'utf-8',
        
        # SCRAPYD CONFIGURATION:
        # Schedule: Every 60 minutes
        # Project: lamaquina
        # Spider: el_pais_latinoamerica
        # Arguments: -a max_items=100
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rss_url = "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/america/portada"
        self.articles_scraped = 0
        self.max_articles = int(kwargs.get('max_items', 100))
        
        # Información del medio
        self.medio_info = {
            'medio': "El País",
            'seccion': "latinoamerica",
            'area_geografica': "HISPANOAMERICA",
            'tipo_medio': "diario",
            'medio_url_principal': "https://elpais.com/noticias/latinoamerica/",
            'frecuencia_minutos': 60,
        }
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider
    
    def start_requests(self):
        """Inicia el scraping desde el feed RSS"""
        self.logger.info(f"Iniciando scraping de RSS: {self.rss_url}")
        
        # Usar scrapy para descargar el RSS (respeta robots.txt y delays)
        yield scrapy.Request(
            url=self.rss_url,
            callback=self.parse_rss,
            errback=self.handle_error,
            meta={'handle_httpstatus_all': True}
        )
    
    def get_rss_with_cloudscraper(self, url: str) -> str:
        """
        Método alternativo usando cloudscraper para bypasser Cloudflare
        """
        if not HAS_CLOUDSCRAPER:
            self.logger.error("cloudscraper no está instalado")
            return None
            
        self.logger.info("🌩️ Iniciando CloudScraper CHROME method...")
        
        try:
            # Crear sesión cloudscraper con Chrome browser
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )
            
            # Headers adicionales realistas
            scraper.headers.update({
                'Accept': 'application/rss+xml, application/xml, text/xml',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8,en-US;q=0.7',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            })
            
            # Realizar request
            response = scraper.get(url, timeout=30)
            
            if response.status_code == 200:
                self.logger.info(f"✅ CloudScraper CHROME exitoso: {len(response.text)} chars")
                return response.text
            else:
                self.logger.warning(f"⚠️ CloudScraper CHROME status: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ CloudScraper CHROME falló: {e}")
            return None
    
    def get_article_with_cloudscraper(self, url: str) -> str:
        """
        Obtiene contenido de artículo usando cloudscraper
        """
        if not HAS_CLOUDSCRAPER:
            self.logger.error("cloudscraper no está instalado")
            return None
            
        self.logger.info(f"🌩️ Obteniendo artículo con CloudScraper: {url}")
        
        try:
            # Crear sesión cloudscraper con Chrome browser
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )
            
            # Headers para páginas de artículo
            scraper.headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8,en-US;q=0.7',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
            })
            
            # Realizar request
            response = scraper.get(url, timeout=30)
            
            if response.status_code == 200:
                self.logger.info(f"✅ Artículo obtenido: {len(response.text)} chars")
                return response.text
            else:
                self.logger.warning(f"⚠️ CloudScraper artículo status: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ CloudScraper artículo falló: {e}")
            return None
    
    def _extract_content_from_html(self, html_content: str, article_data: Dict[str, Any]):
        """
        Extrae contenido de HTML obtenido con cloudscraper
        """
        try:
            from scrapy import Selector
            selector = Selector(text=html_content)
            
            # Extraer contenido usando selectores genéricos
            content = self._extract_generic_content_from_selector(selector)
            if content:
                article_data['contenido_texto'] = content
                article_data['contenido_html'] = selector.css('article').get() or \
                                              selector.css('main').get() or \
                                              selector.css('[role="main"]').get()
            
            # Extraer metadata adicional
            self._extract_metadata_from_selector(selector, article_data)
            
            # Actualizar fecha si se encontró en la página
            fecha = self._extract_date_from_selector(selector)
            if fecha:
                article_data['fecha_publicacion'] = fecha.isoformat()
                
            article_data['metadata']['extraction_method'] = 'cloudscraper'
            
        except Exception as e:
            self.logger.error(f"Error extrayendo contenido de HTML: {e}")
    
    def _extract_generic_content_from_selector(self, selector) -> str:
        """Extracción genérica de contenido desde selector"""
        content_selectors = [
            'article',
            'main',
            '[role="main"]',
            '.post-content',
            '.entry-content',
            '.article-body',
            '.story-body',
            '#content'
        ]
        
        for css_selector in content_selectors:
            content = selector.css(f'{css_selector} ::text').getall()
            if content:
                return ' '.join(content).strip()
        
        # Fallback: extraer todos los párrafos
        paragraphs = selector.css('p::text').getall()
        return ' '.join(paragraphs).strip()
    
    def _extract_date_from_selector(self, selector) -> Optional[datetime]:
        """Intenta extraer la fecha de publicación del selector"""
        date_selectors = [
            'meta[property="article:published_time"]::attr(content)',
            'meta[name="publish_date"]::attr(content)',
            'meta[name="DC.date.issued"]::attr(content)',
            'time[datetime]::attr(datetime)',
            'time[pubdate]::attr(datetime)',
        ]
        
        for css_selector in date_selectors:
            date_str = selector.css(css_selector).get()
            if date_str:
                try:
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    try:
                        return datetime.strptime(date_str[:19], '%Y-%m-%dT%H:%M:%S')
                    except:
                        pass
        return None
    
    def _extract_metadata_from_selector(self, selector, article_data: Dict[str, Any]):
        """Extrae metadata adicional del selector"""
        og_mappings = {
            'og_title': 'meta[property="og:title"]::attr(content)',
            'og_description': 'meta[property="og:description"]::attr(content)',
            'og_image': 'meta[property="og:image"]::attr(content)',
            'og_type': 'meta[property="og:type"]::attr(content)',
        }
        
        for key, css_selector in og_mappings.items():
            value = selector.css(css_selector).get()
            if value:
                article_data['metadata'][key] = value
        
        if 'imagen_principal' not in article_data and 'og_image' in article_data['metadata']:
            article_data['imagen_principal'] = article_data['metadata']['og_image']
    
    def parse_rss(self, response):
        """Parsea el feed RSS y genera requests para cada artículo"""
        if response.status != 200:
            self.logger.error(f"Error descargando RSS: {response.status}")
            
            # Si falla con 403, intentar con cloudscraper
            if response.status == 403:
                self.logger.warning("🚫 Scrapy bloqueado (403), intentando con CloudScraper...")
                rss_content = self.get_rss_with_cloudscraper(self.rss_url)
                if rss_content:
                    # Procesar RSS obtenido con cloudscraper
                    for item in self._process_rss_content(rss_content):
                        yield item
                    return
                else:
                    self.logger.error("❌ Todos los métodos fallaron para obtener RSS")
            return
        
        # Procesar RSS normal de Scrapy
        for item in self._process_rss_content(response.text):
            yield item
    
    def _process_rss_content(self, rss_content: str):
        """Procesa el contenido RSS independientemente de cómo se obtuvo"""
        
        try:
            # Parsear RSS con feedparser
            feed = feedparser.parse(rss_content)
            
            if feed.bozo:
                self.logger.warning(f"RSS mal formado: {feed.bozo_exception}")
            
            self.logger.info(f"Encontrados {len(feed.entries)} artículos en RSS")
            
            # Contadores para estadísticas
            articles_processed = 0
            articles_accepted = 0
            
            # Procesar cada entrada del feed
            for entry in feed.entries[:self.max_articles]:
                articles_processed += 1
                
                # Verificar si el artículo pertenece a la sección
                if self._belongs_to_section(entry):
                    articles_accepted += 1
                    article_data = self.extract_rss_data(entry)
                    
                    # Agregar información de filtrado a metadata
                    article_data['metadata']['section_filter'] = 'accepted'
                    article_data['metadata']['filter_reason'] = self._get_filter_reason(entry)
                    
                    if article_data.get('url'):
                        # Intentar obtener contenido del artículo directamente con cloudscraper
                        self.logger.info(f"📄 Procesando artículo: {article_data['url']}")
                        article_content = self.get_article_with_cloudscraper(article_data['url'])
                        if article_content:
                            # Extraer contenido del HTML obtenido
                            self._extract_content_from_html(article_content, article_data)
                        else:
                            self.logger.warning(f"⚠️ No se pudo obtener contenido completo del artículo")
                        
                        # Procesar el artículo (con o sin contenido completo)
                        yield self._process_article_item(article_data)
                    else:
                        # Si no hay link, procesar directamente los datos del RSS
                        yield self._process_article_item(article_data)
                else:
                    # Log de artículos rechazados para debugging
                    self.logger.debug(f"Artículo rechazado: {getattr(entry, 'title', 'Sin título')} - "
                                    f"Razón: {self._get_rejection_reason(entry)}")
            
            # Log de estadísticas de filtrado
            filter_rate = (articles_accepted / articles_processed * 100) if articles_processed > 0 else 0
            self.logger.info(f"Filtrado RSS: {articles_accepted}/{articles_processed} artículos aceptados "
                           f"({filter_rate:.1f}%) para sección 'latinoamerica'")
                
        except Exception as e:
            self.logger.error(f"Error parseando RSS: {e}")
    
    def _process_article_item(self, article_data):
        """Procesa un artículo y lo devuelve para el pipeline"""
        self.articles_scraped += 1
        self.logger.info(f"Artículo {self.articles_scraped} extraído: {article_data.get('titular', 'Sin título')}")
        
        # Devolver el artículo directamente para que Scrapy lo procese
        return article_data
    
    def _get_filter_reason(self, entry) -> str:
        """Determina por qué se aceptó un artículo (para debugging)"""
        target_section = "latinoamerica"
        
        # Verificar categorías
        if hasattr(entry, 'tags') and entry.tags:
            categories = [tag.term.lower().strip() for tag in entry.tags if hasattr(tag, 'term')]
            if target_section in categories:
                return "categoria_exacta"
            for category in categories:
                if target_section in category or category in target_section:
                    return "categoria_parcial"
        
        # Verificar URL
        if hasattr(entry, 'link') and entry.link:
            if self._is_section_article(entry.link):
                return "url_pattern"
        
        return "inclusion_por_defecto"
    
    def _get_rejection_reason(self, entry) -> str:
        """Determina por qué se rechazó un artículo (para debugging)"""
        if not hasattr(entry, 'link') or not entry.link:
            return "sin_url"
        
        # Este método solo se llama si _belongs_to_section devuelve False
        # Que en el código actual solo ocurre si _is_section_article devuelve False
        # Ya que _belongs_to_section devuelve True por defecto
        return "url_no_coincide_con_seccion"
    
    def _belongs_to_section(self, entry) -> bool:
        """
        Verifica si la entrada RSS pertenece a la sección objetivo.
        
        Criterios de filtrado:
        1. Categorías RSS (tags) - primera prioridad
        2. Patrones de URL - segunda prioridad  
        3. Inclusión por defecto si no se puede determinar
        
        Args:
            entry: Entrada del feed RSS parseada por feedparser
            
        Returns:
            bool: True si la entrada pertenece a la sección
        """
        target_section = "latinoamerica"
        
        # Criterio 1: Verificar por categorías RSS
        if hasattr(entry, 'tags') and entry.tags:
            categories = [tag.term.lower().strip() for tag in entry.tags if hasattr(tag, 'term')]
            
            # Buscar coincidencia exacta primero
            if target_section in categories:
                self.logger.debug(f"Artículo aceptado por categoría exacta: {target_section}")
                return True
            
            # Buscar coincidencia parcial en categorías
            for category in categories:
                if target_section in category or category in target_section:
                    self.logger.debug(f"Artículo aceptado por categoría parcial: {category}")
                    return True
        
        # Criterio 2: Verificar por URL si hay link
        if hasattr(entry, 'link') and entry.link:
            url_matches = self._is_section_article(entry.link)
            if url_matches:
                self.logger.debug(f"Artículo aceptado por URL: {entry.link}")
                return url_matches
        
        # Criterio 3: Por defecto incluir si no podemos determinar sección
        # Esto evita perder contenido válido de feeds mal configurados
        self.logger.debug(f"Artículo incluido por defecto (sin información de sección)")
        return True
    
    def _is_section_article(self, url: str) -> bool:
        """
        Valida si la URL del artículo pertenece a la sección objetivo.
        
        Filtros aplicados:
        1. Exclusión de contenido no deseado (archivos, multimedia, etc.)
        2. Verificación de patrones de sección en la URL
        
        Args:
            url: URL del artículo a verificar
            
        Returns:
            bool: True si la URL pertenece a la sección objetivo
        """
        if not url:
            return False
        
        # Patrones a excluir (contenido no deseado)
        excluded_patterns = [
            r'/archivo/',          # Archivos/hemeroteca
            r'/hemeroteca/',       # Archivo histórico  
            r'/newsletter/',       # Boletines
            r'/multimedia/',       # Contenido multimedia
            r'/video[s]?/',        # Videos
            r'/podcast[s]?/',      # Podcasts
            r'/audio[s]?/',        # Audio
            r'/galeria[s]?/',      # Galerías de fotos
            r'/foto[s]?/',         # Fotos
            r'/infografia[s]?/',   # Infografías
            r'/tags?/',            # Páginas de tags
            r'/etiqueta[s]?/',     # Etiquetas (español)
            r'/autor[es]?/',       # Páginas de autor
            r'/busca[rd]?/',       # Búsquedas
            r'/search/',           # Búsquedas (inglés)
            r'/categoria[s]?/',    # Páginas de categoría
            r'/archivo-por-fecha/',# Archivo por fecha
            r'/rss/',              # Feeds RSS
            r'/feed/',             # Feeds
            r'/sitemap/',          # Sitemaps
        ]
        
        # Verificar exclusiones
        for pattern in excluded_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                self.logger.debug(f"URL excluida por patrón {pattern}: {url}")
                return False
        
        # Patrones específicos de El País para Latinoamérica
        # El País usa rutas como /america-colombia/, /mexico/, /chile/, etc.
        latinoamerica_patterns = [
            r'/america[-_]?',         # /america-colombia/, /america/, etc.
            r'/mexico/',              # /mexico/
            r'/chile/',               # /chile/
            r'/argentina/',           # /argentina/
            r'/colombia/',            # /colombia/
            r'/venezuela/',           # /venezuela/
            r'/peru/',                # /peru/
            r'/brasil/',              # /brasil/
            r'/ecuador/',             # /ecuador/
            r'/bolivia/',             # /bolivia/
            r'/uruguay/',             # /uruguay/
            r'/paraguay/',            # /paraguay/
            r'/centroamerica/',       # /centroamerica/
            r'/latinoamerica/',       # /latinoamerica/
            r'/hispanoamerica/',      # /hispanoamerica/
        ]
        
        # Verificar que pertenece a Latinoamérica
        for pattern in latinoamerica_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                self.logger.debug(f"URL aceptada por patrón {pattern}: {url}")
                return True
        
        # Si no encuentra patrón específico, rechazar para ser conservador
        self.logger.debug(f"URL no contiene patrón de Latinoamérica: {url}")
        return False
    
    def extract_rss_data(self, entry) -> Dict[str, Any]:
        """Extrae datos estructurados de una entrada RSS con campos obligatorios"""
        # Extraer fecha de publicación
        fecha_pub = None
        if hasattr(entry, 'published_parsed'):
            fecha_pub = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed'):
            fecha_pub = datetime(*entry.updated_parsed[:6])
        
        # Extraer contenido
        contenido = ""
        if hasattr(entry, 'summary'):
            contenido = entry.summary
        elif hasattr(entry, 'description'):
            contenido = entry.description
        
        # Crear item con TODOS los campos obligatorios
        article_data = {
            # Campos obligatorios
            'url': getattr(entry, 'link', ''),
            'titular': getattr(entry, 'title', ''),  # IMPORTANTE: 'titular' no 'titulo'
            'medio': self.medio_info['medio'],
            'medio_url_principal': self.medio_info['medio_url_principal'],
            'area_geografica': self.medio_info['area_geografica'],
            'tipo_medio': self.medio_info['tipo_medio'],
            'seccion': self.medio_info['seccion'],
            'fecha_publicacion': fecha_pub.isoformat() if fecha_pub else None,
            'contenido_texto': contenido,
            'contenido_html': contenido,  # RSS normalmente no tiene HTML separado
            'fuente': self.name,
            'fecha_extraccion': datetime.now().isoformat(),
            
            # Metadata adicional
            'metadata': {
                'spider_type': 'rss',
                'extraction_method': 'feedparser',
                'section_filter': 'pending',  # Se actualiza en parse_rss
                'rss_guid': getattr(entry, 'id', None),
                'from_rss': True,
                'rss_url': self.rss_url,
                'spider_name': self.name,
                'generation_date': "2025-07-01T19:30:00.123456",
                'frecuencia_minutos': 60,
            }
        }
        
        # Campos opcionales
        if hasattr(entry, 'author'):
            article_data['autor'] = entry.author
        
        # Categorías/Tags
        if hasattr(entry, 'tags'):
            article_data['metadata']['categorias'] = [tag.term for tag in entry.tags]
        
        # Media/Imágenes
        if hasattr(entry, 'media_content'):
            article_data['metadata']['media'] = [
                {'url': media.get('url'), 'type': media.get('type')}
                for media in entry.media_content
            ]
        
        return article_data
    
    def parse_article(self, response):
        """Parsea la página del artículo para extraer contenido completo"""
        if response.status != 200:
            self.logger.warning(f"Error accediendo artículo: {response.status} - {response.url}")
            
            # Si es 403, intentar con cloudscraper
            if response.status == 403:
                self.logger.warning(f"🚫 Artículo bloqueado (403), intentando con CloudScraper: {response.url}")
                article_content = self.get_article_with_cloudscraper(response.url)
                if article_content:
                    # Procesar artículo obtenido con cloudscraper
                    article_data = response.meta['article_data']
                    self._extract_content_from_html(article_content, article_data)
                    yield self._process_article_item(article_data)
                    return
            
            # Devolver solo datos del RSS como fallback
            yield response.meta['article_data']
            return
        
        article_data = response.meta['article_data']
        article_data['url'] = response.url  # Actualizar con URL final (redirects)
        article_data['metadata']['http_status'] = response.status
        
        try:
            # Selectores genéricos si no hay específicos
            content = self.extract_generic_content(response)
            if content:
                article_data['contenido_texto'] = content
                article_data['contenido_html'] = response.css('article').get() or \
                                               response.css('main').get() or \
                                               response.css('[role="main"]').get()
            
            # Extraer metadata adicional
            self.extract_metadata(response, article_data)
            
            # Actualizar fecha si se encontró en la página
            fecha = self._extract_date(response)
            if fecha:
                article_data['fecha_publicacion'] = fecha.isoformat()
            
        except Exception as e:
            self.logger.error(f"Error extrayendo contenido de {response.url}: {e}")
        
        self.articles_scraped += 1
        self.logger.info(f"Artículo {self.articles_scraped} extraído: {article_data.get('titular', 'Sin título')}")
        
        yield article_data
    
    def extract_generic_content(self, response) -> str:
        """Extracción genérica de contenido cuando no hay selectores específicos"""
        # Intentar encontrar el contenido principal
        content_selectors = [
            'article',
            'main',
            '[role="main"]',
            '.post-content',
            '.entry-content',
            '.article-body',
            '.story-body',
            '#content'
        ]
        
        for selector in content_selectors:
            content = response.css(f'{selector} ::text').getall()
            if content:
                return ' '.join(content).strip()
        
        # Fallback: extraer todos los párrafos
        paragraphs = response.css('p::text').getall()
        return ' '.join(paragraphs).strip()
    
    def _extract_date(self, response) -> Optional[datetime]:
        """Intenta extraer la fecha de publicación del artículo"""
        # Buscar en meta tags comunes
        date_selectors = [
            'meta[property="article:published_time"]::attr(content)',
            'meta[name="publish_date"]::attr(content)',
            'meta[name="DC.date.issued"]::attr(content)',
            'time[datetime]::attr(datetime)',
            'time[pubdate]::attr(datetime)',
        ]
        
        for selector in date_selectors:
            date_str = response.css(selector).get()
            if date_str:
                try:
                    # Intentar parsear ISO format
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    try:
                        # Intentar otros formatos comunes
                        return datetime.strptime(date_str[:19], '%Y-%m-%dT%H:%M:%S')
                    except:
                        pass
        
        return None
    
    def extract_metadata(self, response, article_data: Dict[str, Any]):
        """Extrae metadata adicional de la página"""
        # Open Graph
        og_mappings = {
            'og_title': 'meta[property="og:title"]::attr(content)',
            'og_description': 'meta[property="og:description"]::attr(content)',
            'og_image': 'meta[property="og:image"]::attr(content)',
            'og_type': 'meta[property="og:type"]::attr(content)',
        }
        
        for key, selector in og_mappings.items():
            value = response.css(selector).get()
            if value:
                article_data['metadata'][key] = value
        
        # Si no hay imagen principal, usar og:image
        if 'imagen_principal' not in article_data and 'og_image' in article_data['metadata']:
            article_data['imagen_principal'] = article_data['metadata']['og_image']
        
        # Schema.org/JSON-LD
        json_ld = response.css('script[type="application/ld+json"]::text').getall()
        if json_ld:
            article_data['metadata']['structured_data'] = json_ld
    
    def handle_error(self, failure):
        """Maneja errores durante el scraping"""
        self.logger.error(f"Error en request: {failure.value}")
        
        # Log del tipo de error
        from scrapy.spidermiddlewares.httperror import HttpError
        from twisted.internet.error import DNSLookupError, TimeoutError
        
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error(f"HTTP Error {response.status} en {response.url}")
        elif failure.check(DNSLookupError):
            self.logger.error(f"DNS Error: {failure.request.url}")
        elif failure.check(TimeoutError):
            self.logger.error(f"Timeout: {failure.request.url}")
    
    def spider_closed(self, spider):
        """Llamado cuando el spider termina"""
        stats = spider.crawler.stats.get_stats()
        
        self.logger.info(f"""
        ========== RESUMEN DE SCRAPING RSS ==========
        Spider: {spider.name}
        Medio: {self.medio_info['medio']}
        Sección: {self.medio_info['seccion']}
        RSS URL: {self.rss_url}
        Artículos extraídos: {self.articles_scraped}
        Duración: {stats.get('elapsed_time_seconds', 0):.2f} segundos
        Requests exitosos: {stats.get('downloader/response_status_count/200', 0)}
        Requests fallidos: {stats.get('downloader/response_status_count/404', 0) + stats.get('downloader/response_status_count/500', 0)}
        Errores de red: {stats.get('downloader/exception_count', 0)}
        Items generados: {stats.get('item_scraped_count', 0)}
        ============================================
        """)