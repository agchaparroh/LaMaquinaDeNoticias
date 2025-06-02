# scraper_core/middlewares/playwright_optimized_middleware.py
import logging
from typing import Optional, Union
from scrapy import signals
from scrapy.http import HtmlResponse, Request
from scrapy.exceptions import IgnoreRequest, NotConfigured

class PlaywrightOptimizedMiddleware:
    """
    Middleware optimizado para Playwright que maneja mejor la compatibilidad con Windows
    y tiene mejor manejo de errores.
    """

    def __init__(self, crawler):
        self.crawler = crawler
        self.settings = crawler.settings
        self.stats = crawler.stats
        
        # Configuración optimizada
        self.max_retries = self.settings.getint('PLAYWRIGHT_MAX_RETRIES', 1)  # Reducido
        self.timeout = self.settings.getint('PLAYWRIGHT_TIMEOUT', 20000)  # 20s en lugar de 30s
        self.enable_fallback = self.settings.getbool('PLAYWRIGHT_ENABLE_FALLBACK', True)
        self.enable_playwright = self.settings.getbool('ENABLE_PLAYWRIGHT_MIDDLEWARE', False)  # Deshabilitado por defecto
        
        # Contadores
        self.empty_content_detections = 0
        self.retries = 0
        self.failures = 0
        self.recoveries = 0
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler)
        
        # Solo conectar señales si Playwright está habilitado
        if middleware.enable_playwright:
            try:
                # Verificar si scrapy-playwright está disponible y funcional
                from scrapy_playwright.handler import ScrapyPlaywrightDownloadHandler
                crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
                crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
            except (ImportError, NotConfigured) as e:
                middleware.logger.warning(f"Playwright not available, disabling middleware: {e}")
                middleware.enable_playwright = False
        
        return middleware

    def spider_opened(self, spider):
        if self.enable_playwright:
            self.logger.info(f'PlaywrightOptimizedMiddleware enabled for {spider.name} '
                           f'(max_retries={self.max_retries}, timeout={self.timeout}ms)')
        else:
            self.logger.info(f'PlaywrightOptimizedMiddleware disabled for {spider.name}')

    def spider_closed(self, spider):
        if self.enable_playwright:
            self.logger.info(f'Playwright stats - Detections: {self.empty_content_detections}, '
                           f'Retries: {self.retries}, Failures: {self.failures}, Recoveries: {self.recoveries}')
            
            # Actualizar estadísticas
            self.stats.set_value('playwright_optimized/empty_content_detections', self.empty_content_detections)
            self.stats.set_value('playwright_optimized/retries', self.retries)
            self.stats.set_value('playwright_optimized/failures', self.failures)
            self.stats.set_value('playwright_optimized/recoveries', self.recoveries)

    def process_request(self, request, spider):
        """Configurar requests de Playwright solo si está habilitado."""
        if not self.enable_playwright:
            return None
            
        if request.meta.get('playwright'):
            # Configuración simplificada y robusta
            request.meta.update({
                'playwright': True,
                'playwright_include_page': False,  # Simplificado
                'playwright_page_methods': [
                    {'method': 'set_default_timeout', 'args': [self.timeout]},
                ],
                'playwright_context_kwargs': {
                    'ignore_https_errors': True,
                    'java_script_enabled': True,
                },
            })
            self.logger.debug(f"Configured simplified Playwright for {request.url}")
        
        return None

    def process_response(self, request, response, spider):
        """Procesar respuestas con manejo optimizado."""
        if not self.enable_playwright or not isinstance(response, HtmlResponse):
            return response

        # Verificar si necesita Playwright
        if self._should_retry_with_playwright(request, response):
            return self._create_playwright_retry(request, response, spider)
        
        # Si llegamos aquí con un request de Playwright exitoso
        if request.meta.get('playwright'):
            self.recoveries += 1
            self.logger.info(f"Playwright successfully loaded {response.url}")
        
        return response

    def _should_retry_with_playwright(self, request, response) -> bool:
        """Determinar si se debe reintentar con Playwright."""
        # No reintentar si ya es un request de Playwright
        if request.meta.get('playwright'):
            return False
        
        # No reintentar si ya se intentó
        if request.meta.get('playwright_attempted'):
            return False
        
        # No reintentar si Playwright está deshabilitado para este request
        if not self.settings.getbool('USE_PLAYWRIGHT_FOR_EMPTY_CONTENT', False):
            return False
        
        # Verificar contenido vacío
        return self._is_content_empty(response)

    def _is_content_empty(self, response) -> bool:
        """Detectar contenido vacío de forma optimizada."""
        # Verificar tamaño mínimo
        if len(response.body) < 500:  # Muy pequeño
            return True
        
        # Verificar texto útil
        text = response.xpath('//text()[normalize-space()]').getall()
        useful_text = ' '.join(text).strip()
        
        if len(useful_text) < 100:
            return True
        
        # Verificar indicadores de contenido no renderizado
        text_lower = useful_text.lower()
        empty_indicators = ['loading', 'javascript required', 'please enable javascript']
        
        return any(indicator in text_lower for indicator in empty_indicators)

    def _create_playwright_retry(self, request, response, spider):
        """Crear request de reintento con Playwright."""
        self.empty_content_detections += 1
        self.retries += 1
        
        self.logger.info(f"Empty content detected, retrying with Playwright: {response.url}")
        
        new_meta = request.meta.copy()
        new_meta.update({
            'playwright': True,
            'playwright_attempted': True,
            'playwright_include_page': False,
            'playwright_page_methods': [
                {'method': 'set_default_timeout', 'args': [self.timeout]},
            ],
            'playwright_context_kwargs': {
                'ignore_https_errors': True,
                'java_script_enabled': True,
            },
        })
        
        return Request(
            response.url,
            callback=request.callback,
            errback=request.errback,
            meta=new_meta,
            dont_filter=True,
            priority=request.priority + 1  # Prioridad ligeramente mayor
        )

    def process_exception(self, request, exception, spider):
        """Manejar excepciones de Playwright de forma optimizada."""
        if not self.enable_playwright or not request.meta.get('playwright'):
            return None
        
        self.failures += 1
        exception_str = str(exception).lower()
        
        # Log pero no reintentar - es mejor fallar rápido
        self.logger.warning(f"Playwright exception for {request.url}: {exception}")
        
        # Si el fallback está habilitado, crear request sin Playwright
        if self.enable_fallback:
            new_meta = request.meta.copy()
            # Limpiar metadatos de Playwright
            for key in list(new_meta.keys()):
                if 'playwright' in key.lower():
                    del new_meta[key]
            
            new_meta['playwright_fallback'] = True
            
            return Request(
                request.url,
                callback=request.callback,
                errback=request.errback,
                meta=new_meta,
                dont_filter=True
            )
        
        return None
