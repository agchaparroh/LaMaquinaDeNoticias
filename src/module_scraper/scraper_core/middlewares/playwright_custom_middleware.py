# scraper_core/middlewares/playwright_custom_middleware.py
import logging
import asyncio
from typing import Optional, Union
from scrapy import signals
from scrapy.http import HtmlResponse, Request
from scrapy.exceptions import IgnoreRequest, NotConfigured
from scrapy.utils.misc import load_object
from twisted.internet.defer import Deferred
from twisted.internet import defer

class PlaywrightError(Exception):
    """Base exception for Playwright-related errors."""
    pass

class PlaywrightTimeoutError(PlaywrightError):
    """Raised when Playwright operations timeout."""
    pass

class PlaywrightNavigationError(PlaywrightError):
    """Raised when Playwright navigation fails."""
    pass

class PlaywrightResourceError(PlaywrightError):
    """Raised when Playwright encounters resource limitations."""
    pass

class PlaywrightCustomDownloaderMiddleware:
    """
    Middleware personalizado para detectar respuestas con contenido vacío y reintentar
    la solicitud utilizando Playwright para el renderizado de JavaScript.
    
    Incluye manejo robusto de errores específicos de Playwright y mecanismos de recuperación.
    """

    def __init__(self, crawler):
        self.crawler = crawler
        self.settings = crawler.settings
        self.stats = crawler.stats
        
        # Configuración de error handling
        self.max_playwright_retries = self.settings.getint('PLAYWRIGHT_MAX_RETRIES', 2)
        self.playwright_timeout = self.settings.getint('PLAYWRIGHT_TIMEOUT', 30000)  # 30 segundos
        self.enable_fallback_on_error = self.settings.getbool('PLAYWRIGHT_ENABLE_FALLBACK', True)
        self.max_empty_retries = self.settings.getint('PLAYWRIGHT_MAX_EMPTY_RETRIES', 1)
        
        # Contadores para estadísticas
        self.playwright_retries = 0
        self.playwright_failures = 0
        self.empty_content_detections = 0
        self.successful_recoveries = 0
        
        # Logger específico para este middleware
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @classmethod
    def from_crawler(cls, crawler):
        # Verificar si scrapy-playwright está disponible
        try:
            load_object('scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler')
        except (ImportError, AttributeError) as e:
            raise NotConfigured(f"scrapy-playwright not available: {e}")
        
        middleware = cls(crawler)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def spider_opened(self, spider):
        """Inicialización cuando se abre el spider."""
        self.logger.info(f'{self.__class__.__name__} opened for spider {spider.name}')
        self.logger.info(f'Playwright configuration: max_retries={self.max_playwright_retries}, '
                        f'timeout={self.playwright_timeout}ms, fallback_enabled={self.enable_fallback_on_error}')

    def spider_closed(self, spider):
        """Logging de estadísticas cuando se cierra el spider."""
        self.logger.info(f'{self.__class__.__name__} closed for spider {spider.name}')
        self.logger.info(f'Playwright statistics - Empty content detections: {self.empty_content_detections}, '
                        f'Retries: {self.playwright_retries}, Failures: {self.playwright_failures}, '
                        f'Successful recoveries: {self.successful_recoveries}')
        
        # Actualizar estadísticas de Scrapy
        self.stats.set_value('playwright/empty_content_detections', self.empty_content_detections)
        self.stats.set_value('playwright/retries', self.playwright_retries)
        self.stats.set_value('playwright/failures', self.playwright_failures)
        self.stats.set_value('playwright/successful_recoveries', self.successful_recoveries)

    def process_request(self, request, spider):
        """
        Procesa requests antes de ser enviados al downloader.
        Configura opciones robustas de Playwright para requests marcados.
        """
        if request.meta.get('playwright'):
            # Configurar opciones robustas de Playwright
            playwright_meta = self._get_robust_playwright_config(request, spider)
            request.meta.update(playwright_meta)
            
            self.logger.debug(f"Configured robust Playwright options for {request.url}")
        
        return None

    def _get_robust_playwright_config(self, request, spider) -> dict:
        """
        Genera configuración robusta de Playwright para el request.
        
        Args:
            request: El request de Scrapy
            spider: La instancia del spider
            
        Returns:
            dict: Configuración de Playwright
        """
        config = {
            'playwright': True,
            'playwright_include_page': True,  # Incluir objeto page para manejo avanzado
            'playwright_page_methods': [
                # Configurar timeouts robustos
                {'method': 'set_default_timeout', 'args': [self.playwright_timeout]},
                {'method': 'set_default_navigation_timeout', 'args': [self.playwright_timeout]},
            ],
            'playwright_page_coroutines': [
                # Esperar a que el contenido se cargue completamente
                {'method': 'wait_for_load_state', 'args': ['networkidle'], 'kwargs': {'timeout': self.playwright_timeout}},
            ],
            'playwright_context_kwargs': {
                'ignore_https_errors': True,  # Ignorar errores de certificados SSL
                'java_script_enabled': True,
                'user_agent': request.headers.get('User-Agent', '').decode('utf-8') if request.headers.get('User-Agent') else None,
            },
            'playwright_page_kwargs': {
                'extra_http_headers': dict(request.headers) if request.headers else {},
            }
        }
        
        # Añadir configuraciones específicas basadas en el tipo de sitio
        url_lower = request.url.lower()
        if any(spa_indicator in url_lower for spa_indicator in ['react', 'angular', 'vue', 'spa']):
            # Para Single Page Applications, esperar más tiempo
            config['playwright_page_coroutines'].append(
                {'method': 'wait_for_timeout', 'args': [2000]}  # Esperar 2 segundos adicionales
            )
        
        return config

    async def process_response(self, request, response, spider):
        """
        Procesa responses y maneja errores de Playwright con recuperación robusta.
        
        Args:
            request: El request original
            response: La response recibida
            spider: La instancia del spider
            
        Returns:
            Union[HtmlResponse, Request]: La response original o un nuevo request para reintento
        """
        # Solo procesar respuestas HTML
        if not isinstance(response, HtmlResponse):
            return response

        # Obtener información de contexto del request
        is_playwright_request = request.meta.get('playwright', False)
        playwright_retry_count = request.meta.get('playwright_retry_count', 0)
        empty_retry_count = request.meta.get('empty_retry_count', 0)
        
        # Verificar si la respuesta contiene errores de Playwright
        playwright_error = self._detect_playwright_error(response, spider)
        if playwright_error and is_playwright_request:
            return self._handle_playwright_error(
                request, response, spider, playwright_error, playwright_retry_count
            )
        
        # Verificar contenido vacío solo en responses no-Playwright o con pocos reintentos
        if self._should_check_empty_content(request, response, empty_retry_count):
            body_is_empty = self._is_content_empty(response, spider)
            
            if body_is_empty:
                self.empty_content_detections += 1
                return self._handle_empty_content(
                    request, response, spider, empty_retry_count
                )
        
        # Si llegamos aquí, la response es válida
        if is_playwright_request:
            self.successful_recoveries += 1
            self.logger.info(f"Playwright successfully recovered content for {response.url}")
        
        return response

    def _detect_playwright_error(self, response, spider) -> Optional[str]:
        """
        Detecta errores específicos de Playwright en la response.
        
        Args:
            response: La response a analizar
            spider: La instancia del spider
            
        Returns:
            Optional[str]: Tipo de error detectado o None
        """
        # Verificar errores en headers o contenido de la response
        status_code = response.status
        
        # Errores de timeout de Playwright
        if status_code == 524 or 'timeout' in response.text.lower():
            return 'timeout'
        
        # Errores de navegación
        if status_code in [502, 503, 504] and 'playwright' in str(response.headers).lower():
            return 'navigation'
        
        # Verificar contenido que indica errores de Playwright
        response_text_lower = response.text.lower()
        error_indicators = [
            'playwright error',
            'browser context',
            'page crash',
            'connection refused',
            'target closed'
        ]
        
        for indicator in error_indicators:
            if indicator in response_text_lower:
                return 'browser_error'
        
        # Verificar si el contenido indica limitaciones de recursos
        if 'out of memory' in response_text_lower or 'resource exhausted' in response_text_lower:
            return 'resource_limit'
        
        return None

    def _handle_playwright_error(self, request, response, spider, error_type: str, retry_count: int):
        """
        Maneja errores específicos de Playwright con estrategias de recuperación.
        
        Args:
            request: El request original
            response: La response con error
            spider: La instancia del spider
            error_type: Tipo de error detectado
            retry_count: Número de reintentos actuales
            
        Returns:
            Union[HtmlResponse, Request]: Response original o nuevo request para reintento
        """
        self.playwright_failures += 1
        
        if retry_count >= self.max_playwright_retries:
            self.logger.error(
                f"Max Playwright retries ({self.max_playwright_retries}) exceeded for {response.url}. "
                f"Error type: {error_type}"
            )
            
            if self.enable_fallback_on_error:
                return self._create_fallback_request(request, spider, "max_retries_exceeded")
            else:
                # Marcar el request para ser ignorado por otros componentes
                request.meta['playwright_failed'] = True
                return response
        
        self.logger.warning(
            f"Playwright error detected ({error_type}) for {response.url}. "
            f"Retry {retry_count + 1}/{self.max_playwright_retries}"
        )
        
        # Crear nuevo request con configuración específica para el tipo de error
        new_meta = request.meta.copy()
        new_meta['playwright_retry_count'] = retry_count + 1
        
        # Ajustar configuración basada en el tipo de error
        if error_type == 'timeout':
            # Aumentar timeout para el siguiente intento
            timeout = min(self.playwright_timeout * 2, 60000)  # Max 60 segundos
            new_meta['playwright_page_methods'] = [
                {'method': 'set_default_timeout', 'args': [timeout]},
                {'method': 'set_default_navigation_timeout', 'args': [timeout]},
            ]
            
        elif error_type == 'resource_limit':
            # Reducir concurrencia y usar configuración más ligera
            new_meta['playwright_context_kwargs'] = {
                'ignore_https_errors': True,
                'java_script_enabled': True,
            }
            new_meta['playwright_page_coroutines'] = [
                {'method': 'wait_for_load_state', 'args': ['domcontentloaded']}  # Menos estricto
            ]
            
        elif error_type == 'browser_error':
            # Reiniciar con configuración limpia
            new_meta.pop('playwright_page_methods', None)
            new_meta.pop('playwright_page_coroutines', None)
        
        self.playwright_retries += 1
        
        return Request(
            response.url,
            callback=request.callback,
            errback=request.errback,
            priority=request.priority,
            meta=new_meta,
            dont_filter=True
        )

    def _should_check_empty_content(self, request, response, empty_retry_count: int) -> bool:
        """
        Determina si se debe verificar contenido vacío en esta response.
        
        Args:
            request: El request original
            response: La response recibida
            empty_retry_count: Número de reintentos por contenido vacío
            
        Returns:
            bool: True si se debe verificar contenido vacío
        """
        # No verificar si ya se han agotado los reintentos por contenido vacío
        if empty_retry_count >= self.max_empty_retries:
            return False
        
        # No verificar si ya es un request de Playwright que falló
        if request.meta.get('playwright_failed'):
            return False
        
        # No verificar si el usuario ha deshabilitado esta funcionalidad
        if not self.settings.getbool('USE_PLAYWRIGHT_FOR_EMPTY_CONTENT', True):
            return False
        
        return True

    def _is_content_empty(self, response, spider) -> bool:
        """
        Determina si el contenido de la response está vacío o es insuficiente.
        
        Args:
            response: La response a analizar
            spider: La instancia del spider
            
        Returns:
            bool: True si el contenido se considera vacío
        """
        # Verificar cuerpo completamente vacío
        if not response.body.strip():
            return True
        
        # Verificar contenido HTML mínimo
        text_content = response.xpath('//text()').getall()
        text_content = ' '.join(text_content).strip()
        
        # Considerar vacío si hay menos de 100 caracteres de texto útil
        if len(text_content) < 100:
            return True
        
        # Verificar patrones que indican contenido no renderizado
        empty_indicators = [
            'loading...',
            'please enable javascript',
            'javascript required',
            'this page requires javascript'
        ]
        
        text_lower = text_content.lower()
        for indicator in empty_indicators:
            if indicator in text_lower:
                return True
        
        return False

    def _handle_empty_content(self, request, response, spider, empty_retry_count: int):
        """
        Maneja responses con contenido vacío reintentando con Playwright.
        
        Args:
            request: El request original
            response: La response con contenido vacío
            spider: La instancia del spider
            empty_retry_count: Número de reintentos actuales por contenido vacío
            
        Returns:
            Request: Nuevo request con Playwright habilitado
        """
        self.logger.info(
            f"Empty content detected for {response.url}. "
            f"Retrying with Playwright (attempt {empty_retry_count + 1}/{self.max_empty_retries + 1})"
        )
        
        # Crear nuevo request con Playwright habilitado
        new_meta = request.meta.copy()
        new_meta.update(self._get_robust_playwright_config(request, spider))
        new_meta['empty_retry_count'] = empty_retry_count + 1
        new_meta['playwright_retried'] = True  # Para compatibilidad con BaseArticleSpider
        
        return Request(
            response.url,
            callback=request.callback,
            errback=request.errback,
            priority=request.priority,
            meta=new_meta,
            dont_filter=True
        )

    def _create_fallback_request(self, request, spider, reason: str):
        """
        Crea un request de fallback sin Playwright cuando todas las opciones fallan.
        
        Args:
            request: El request original
            spider: La instancia del spider
            reason: Razón del fallback
            
        Returns:
            Request: Request sin Playwright para último intento
        """
        self.logger.warning(
            f"Creating fallback request for {request.url} due to: {reason}"
        )
        
        # Crear request limpio sin Playwright
        new_meta = request.meta.copy()
        
        # Remover todas las configuraciones de Playwright
        playwright_keys = [k for k in new_meta.keys() if 'playwright' in k.lower()]
        for key in playwright_keys:
            new_meta.pop(key, None)
        
        # Marcar como request de fallback
        new_meta['playwright_fallback'] = True
        new_meta['playwright_fallback_reason'] = reason
        
        return Request(
            request.url,
            callback=request.callback,
            errback=request.errback,
            priority=request.priority,
            meta=new_meta,
            dont_filter=True
        )

    def process_exception(self, request, exception, spider):
        """
        Maneja excepciones que ocurren durante el procesamiento de requests.
        
        Args:
            request: El request que causó la excepción
            exception: La excepción ocurrida
            spider: La instancia del spider
            
        Returns:
            Optional[Request]: Request para reintento o None
        """
        if not request.meta.get('playwright'):
            return None
        
        # Manejar excepciones específicas de Playwright
        exception_str = str(exception).lower()
        
        if any(keyword in exception_str for keyword in ['playwright', 'browser', 'timeout', 'target closed']):
            retry_count = request.meta.get('playwright_retry_count', 0)
            
            if retry_count < self.max_playwright_retries:
                self.logger.warning(
                    f"Playwright exception for {request.url}: {exception}. "
                    f"Retry {retry_count + 1}/{self.max_playwright_retries}"
                )
                
                new_meta = request.meta.copy()
                new_meta['playwright_retry_count'] = retry_count + 1
                
                self.playwright_retries += 1
                self.playwright_failures += 1
                
                return Request(
                    request.url,
                    callback=request.callback,
                    errback=request.errback,
                    priority=request.priority,
                    meta=new_meta,
                    dont_filter=True
                )
            else:
                self.logger.error(
                    f"Max Playwright retries exceeded for {request.url} due to exception: {exception}"
                )
                
                if self.enable_fallback_on_error:
                    return self._create_fallback_request(request, spider, f"exception: {exception}")
        
        return None
