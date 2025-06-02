"""
Spider base optimizado con mejores prácticas de desempeño.
"""

import logging
import time
from typing import Dict, Any, Optional, Iterator
from datetime import datetime

import scrapy
from scrapy.http import Response, Request
from scrapy.utils.misc import arg_to_iter

from scraper_core.items import ArticuloInItem
from scraper_core.itemloaders import ArticuloInItemLoader
from scraper_core.utils.logging_utils import LoggerMixin, log_exceptions
from scraper_core.optimized_settings import apply_runtime_optimizations


class OptimizedSpiderMixin:
    """
    Mixin que proporciona optimizaciones de desempeño para spiders.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = time.time()
        self.performance_stats = {
            'requests_made': 0,
            'items_scraped': 0,
            'errors': 0,
            'avg_response_time': 0,
            'slow_responses': 0,
        }
    
    def spider_opened(self, spider):
        """Callback cuando el spider se abre."""
        self.logger.info(f"🚀 Optimized spider {spider.name} started")
        # Aplicar optimizaciones runtime iniciales
        apply_runtime_optimizations(spider)
    
    def spider_closed(self, spider):
        """Callback cuando el spider se cierra con estadísticas de desempeño."""
        elapsed_time = time.time() - self.start_time
        stats = spider.crawler.stats
        
        # Calcular métricas de desempeño
        total_requests = stats.get_value('downloader/request_count', 0)
        total_responses = stats.get_value('downloader/response_count', 0)
        total_items = stats.get_value('item_scraped_count', 0)
        
        requests_per_second = total_requests / elapsed_time if elapsed_time > 0 else 0
        items_per_minute = (total_items * 60) / elapsed_time if elapsed_time > 0 else 0
        
        self.logger.info("📊 PERFORMANCE SUMMARY:")
        self.logger.info(f"   ⏱️  Total time: {elapsed_time:.1f}s")
        self.logger.info(f"   📡 Requests: {total_requests} ({requests_per_second:.1f}/s)")
        self.logger.info(f"   📥 Responses: {total_responses}")
        self.logger.info(f"   📋 Items: {total_items} ({items_per_minute:.1f}/min)")
        
        if total_requests > 0:
            success_rate = (total_responses / total_requests) * 100
            self.logger.info(f"   ✅ Success rate: {success_rate:.1f}%")
    
    def make_request_optimized(self, url: str, callback_method, meta: Optional[Dict[str, Any]] = None, 
                             priority: int = 0, dont_filter: bool = False) -> Request:
        """
        Crear request optimizado con mejores configuraciones.
        
        Args:
            url: URL a solicitar
            callback_method: Método callback
            meta: Metadatos opcionales
            priority: Prioridad del request (mayor = más importante)
            dont_filter: Si True, no filtra duplicados
            
        Returns:
            Request optimizado
        """
        current_meta = meta.copy() if meta else {}
        
        # Configurar metadatos optimizados
        current_meta.setdefault('download_timeout', 15)  # Timeout más corto
        current_meta.setdefault('download_delay', 0.5)   # Delay dinámico
        
        # Priorizar requests importantes
        if 'important' in url or callback_method.__name__ == 'parse_article':
            priority = max(priority, 10)
        
        # Headers optimizados
        headers = {
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=300',  # Cache 5 minutos
        }
        
        return Request(
            url,
            callback=callback_method,
            errback=self.handle_error_optimized,
            headers=headers,
            meta=current_meta,
            priority=priority,
            dont_filter=dont_filter
        )
    
    def handle_error_optimized(self, failure):
        """
        Manejo optimizado de errores con categorización.
        """
        request = failure.request
        self.performance_stats['errors'] += 1
        
        # Categorizar errores
        error_type = self._categorize_error(failure)
        
        # Log con nivel apropiado
        if error_type == 'temporary':
            self.logger.warning(f"⚠️  Temporary error for {request.url}: {failure.value}")
        elif error_type == 'permanent':
            self.logger.error(f"❌ Permanent error for {request.url}: {failure.value}")
        else:
            self.logger.debug(f"🔍 Minor error for {request.url}: {failure.value}")
        
        # Actualizar estadísticas cada 50 errores
        if self.performance_stats['errors'] % 50 == 0:
            self._log_performance_update()
    
    def _categorize_error(self, failure) -> str:
        """Categorizar tipo de error."""
        error_str = str(failure.value).lower()
        
        if any(temp in error_str for temp in ['timeout', '503', '502', '429']):
            return 'temporary'
        elif any(perm in error_str for perm in ['404', '403', '401']):
            return 'permanent'
        else:
            return 'other'
    
    def _log_performance_update(self):
        """Log actualización de desempeño durante la ejecución."""
        elapsed = time.time() - self.start_time
        rate = self.performance_stats['requests_made'] / elapsed if elapsed > 0 else 0
        
        self.logger.info(f"📈 Performance update: {rate:.1f} req/s, "
                        f"{self.performance_stats['errors']} errors")


class OptimizedArticleSpider(scrapy.Spider, OptimizedSpiderMixin, LoggerMixin):
    """
    Spider base optimizado para extracción de artículos de noticias.
    """
    
    # Configuración optimizada por defecto
    custom_settings = {
        'CONCURRENT_REQUESTS': 16,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 4,
        'DOWNLOAD_DELAY': 0.8,
        'DOWNLOAD_TIMEOUT': 15,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 0.5,
        'AUTOTHROTTLE_MAX_DELAY': 20,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
        'HTTPCACHE_ENABLED': True,
        'HTTPCACHE_EXPIRATION_SECS': 1800,  # 30 minutos
        'RETRY_TIMES': 2,
        'LOG_LEVEL': 'INFO',
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.successful_urls = []
        self.failed_urls = []
        
        # Configurar start_urls desde argumentos
        self.start_urls = list(arg_to_iter(kwargs.get('start_urls', [])))
        self.allowed_domains = list(arg_to_iter(kwargs.get('allowed_domains', [])))
    
    @log_exceptions(include_traceback=True)
    def parse(self, response: Response) -> Iterator[Request]:
        """
        Método principal de parsing optimizado.
        
        Args:
            response: Respuesta HTTP
            
        Yields:
            Requests para artículos individuales
        """
        self.logger.info(f"📄 Parsing article list: {response.url}")
        
        # Extraer enlaces de artículos con selectores robustos
        article_selectors = [
            'article a[href]::attr(href)',
            'h2 a[href]::attr(href)',
            'h3 a[href]::attr(href)',
            '.article-link::attr(href)',
            '.news-link::attr(href)',
            'a[href*="/article/"]::attr(href)',
            'a[href*="/news/"]::attr(href)',
        ]
        
        article_links = []
        for selector in article_selectors:
            links = response.css(selector).getall()
            article_links.extend(links)
            if len(article_links) >= 50:  # Límite para evitar sobrecarga
                break
        
        # Filtrar y procesar enlaces
        unique_links = list(dict.fromkeys(article_links))  # Remover duplicados preservando orden
        valid_links = [link for link in unique_links if self._is_valid_article_link(link)]
        
        self.logger.info(f"🔗 Found {len(valid_links)} valid article links")
        
        # Generar requests optimizados
        for i, link in enumerate(valid_links[:100]):  # Límite máximo
            full_url = response.urljoin(link)
            priority = 20 - (i // 10)  # Prioridad decreciente por lotes
            
            yield self.make_request_optimized(
                full_url,
                self.parse_article,
                meta={'article_index': i},
                priority=priority
            )
        
        # Paginación optimizada
        yield from self._handle_pagination(response)
    
    def _is_valid_article_link(self, link: str) -> bool:
        """Validar si el enlace es un artículo válido."""
        if not link:
            return False
        
        # Filtros positivos
        article_indicators = ['/article/', '/news/', '/story/', '/post/']
        if any(indicator in link.lower() for indicator in article_indicators):
            return True
        
        # Filtros negativos
        invalid_patterns = [
            'javascript:', 'mailto:', '#', 
            '/category/', '/tag/', '/author/',
            '/search/', '/archive/', '/feed/',
            '.pdf', '.jpg', '.png', '.gif'
        ]
        
        return not any(pattern in link.lower() for pattern in invalid_patterns)
    
    def _handle_pagination(self, response: Response) -> Iterator[Request]:
        """Manejo optimizado de paginación."""
        next_selectors = [
            'a.next::attr(href)',
            'a.page-next::attr(href)',
            '.pagination .next::attr(href)',
            'a[aria-label="Next"]::attr(href)',
            '//a[contains(text(), "Next") or contains(text(), "Siguiente")]/@href',
        ]
        
        for selector in next_selectors:
            if selector.startswith('//'):
                next_url = response.xpath(selector).get()
            else:
                next_url = response.css(selector).get()
            
            if next_url:
                self.logger.info(f"➡️  Following pagination: {next_url}")
                yield self.make_request_optimized(
                    response.urljoin(next_url),
                    self.parse,
                    priority=5  # Menor prioridad que artículos individuales
                )
                break  # Solo una página siguiente
    
    @log_exceptions(include_traceback=True)
    def parse_article(self, response: Response) -> Optional[ArticuloInItem]:
        """
        Parseo optimizado de artículos individuales.
        
        Args:
            response: Respuesta HTTP del artículo
            
        Returns:
            Item del artículo o None si hay error
        """
        self.performance_stats['requests_made'] += 1
        start_time = time.time()
        
        self.logger.debug(f"📰 Parsing article: {response.url}")
        
        # Verificar respuesta válida
        if not self._is_valid_response(response):
            return None
        
        try:
            # Usar ItemLoader optimizado
            loader = ArticuloInItemLoader(item=ArticuloInItem(), response=response)
            
            # Extraer datos con selectores robustos
            self._extract_title(loader, response)
            self._extract_content(loader, response)
            self._extract_metadata(loader, response)
            
            # Datos básicos
            loader.add_value('url', response.url)
            loader.add_value('fuente', self.name)
            loader.add_value('fecha_recopilacion', datetime.now())
            
            # Cargar item
            item = loader.load_item()
            
            # Validación rápida
            if self._validate_item_fast(item):
                self.successful_urls.append(response.url)
                self.performance_stats['items_scraped'] += 1
                
                # Log tiempo de procesamiento
                processing_time = time.time() - start_time
                if processing_time > 2:  # Más de 2 segundos es lento
                    self.performance_stats['slow_responses'] += 1
                    self.logger.warning(f"⏱️  Slow article processing: {processing_time:.2f}s for {response.url}")
                
                return item
            else:
                self.logger.debug(f"❌ Article validation failed: {response.url}")
                return None
                
        except Exception as e:
            self.logger.error(f"💥 Error parsing article {response.url}: {e}")
            self.failed_urls.append(response.url)
            return None
    
    def _is_valid_response(self, response: Response) -> bool:
        """Validación rápida de respuesta."""
        if response.status != 200:
            return False
        
        if len(response.body) < 1000:  # Muy pequeño
            return False
        
        # Verificar content-type
        content_type = response.headers.get('content-type', b'').decode('utf-8', errors='ignore')
        if 'text/html' not in content_type.lower():
            return False
        
        return True
    
    def _extract_title(self, loader: ArticuloInItemLoader, response: Response):
        """Extracción optimizada de título."""
        title_selectors = [
            'h1::text',
            'title::text',
            'meta[property="og:title"]::attr(content)',
            'meta[name="twitter:title"]::attr(content)',
            '.article-title::text',
            '.entry-title::text',
        ]
        
        for selector in title_selectors:
            titles = response.css(selector).getall()
            if titles:
                loader.add_value('titular', titles[0])
                break
    
    def _extract_content(self, loader: ArticuloInItemLoader, response: Response):
        """Extracción optimizada de contenido."""
        content_selectors = [
            'article p',
            '.article-content p',
            '.entry-content p',
            '.post-content p',
            '[itemprop="articleBody"] p',
            '.content p',
        ]
        
        for selector in content_selectors:
            paragraphs = response.css(selector).getall()
            if len(paragraphs) >= 3:  # Al menos 3 párrafos
                loader.add_css('contenido_texto', selector)
                loader.add_css('contenido_html', selector)
                break
    
    def _extract_metadata(self, loader: ArticuloInItemLoader, response: Response):
        """Extracción rápida de metadatos."""
        # Fecha de publicación
        date_selectors = [
            'meta[property="article:published_time"]::attr(content)',
            'time[datetime]::attr(datetime)',
            'meta[name="date"]::attr(content)',
            '.date::text',
            '.published::text',
        ]
        
        for selector in date_selectors:
            dates = response.css(selector).getall()
            if dates:
                loader.add_value('fecha_publicacion', dates[0])
                break
        
        # Autor
        author_selectors = [
            'meta[name="author"]::attr(content)',
            '.author::text',
            '.byline::text',
            '[rel="author"]::text',
        ]
        
        for selector in author_selectors:
            authors = response.css(selector).getall()
            if authors:
                loader.add_value('autor', authors[0])
                break
    
    def _validate_item_fast(self, item: ArticuloInItem) -> bool:
        """Validación rápida de item."""
        # Campos requeridos
        if not item.get('titular') or len(item['titular']) < 10:
            return False
        
        if not item.get('contenido_texto') or len(item['contenido_texto']) < 200:
            return False
        
        if not item.get('url'):
            return False
        
        return True


# Función helper para aplicar optimizaciones a spiders existentes
def optimize_existing_spider(spider_class):
    """
    Decorator para aplicar optimizaciones a spiders existentes.
    
    Usage:
        @optimize_existing_spider
        class MySpider(scrapy.Spider):
            ...
    """
    # Mezclar OptimizedSpiderMixin si no está presente
    if OptimizedSpiderMixin not in spider_class.__mro__:
        class OptimizedSpider(OptimizedSpiderMixin, spider_class):
            pass
        OptimizedSpider.__name__ = spider_class.__name__
        OptimizedSpider.__qualname__ = spider_class.__qualname__
        return OptimizedSpider
    
    return spider_class
