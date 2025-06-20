# Tests para Middlewares
"""
Tests para los middlewares del proyecto, especialmente
el middleware de Playwright para renderizado JavaScript.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from scrapy.http import Request, Response, HtmlResponse
from scrapy.utils.test import get_crawler
from scrapy import Spider

from scraper_core.middlewares.playwright_custom_middleware import PlaywrightCustomDownloaderMiddleware


class TestPlaywrightMiddleware:
    """Tests para el middleware de Playwright."""
    
    @pytest.fixture
    def middleware(self):
        """Crear instancia del middleware con mocks."""
        crawler = Mock()
        crawler.settings = {
            'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
            'PLAYWRIGHT_LAUNCH_OPTIONS': {'headless': True},
            'PLAYWRIGHT_MAX_RETRIES': 2,
            'PLAYWRIGHT_TIMEOUT': 30000,
            'USE_PLAYWRIGHT_FOR_EMPTY_CONTENT': True,
        }
        
        middleware = PlaywrightCustomDownloaderMiddleware.from_crawler(crawler)
        return middleware
    
    @pytest.fixture
    def mock_request(self):
        """Request mock para testing."""
        request = Request('https://example.com/test')
        request.meta['playwright'] = True
        return request
    
    def test_middleware_initialization(self, middleware):
        """Test que el middleware se inicializa correctamente."""
        assert middleware.browser_type == 'chromium'
        assert middleware.launch_options['headless'] is True
        assert middleware.max_retries == 2
        assert middleware.timeout == 30000
    
    def test_should_use_playwright_meta(self, middleware):
        """Test detección de requests que requieren Playwright."""
        # Request con meta playwright=True
        request_with_meta = Request('https://example.com', meta={'playwright': True})
        assert middleware._should_use_playwright(request_with_meta) is True
        
        # Request sin meta
        request_without_meta = Request('https://example.com')
        assert middleware._should_use_playwright(request_without_meta) is False
        
        # Request con playwright=False explícito
        request_disabled = Request('https://example.com', meta={'playwright': False})
        assert middleware._should_use_playwright(request_disabled) is False
    
    @pytest.mark.asyncio
    async def test_process_request_with_playwright(self, middleware, mock_request):
        """Test procesamiento de request con Playwright."""
        # Mock del navegador y página
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.content = AsyncMock(return_value='<html><body>Rendered content</body></html>')
        mock_page.close = AsyncMock()
        
        mock_browser = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        
        # Mock de playwright
        with patch('playwright.async_api.async_playwright') as mock_playwright:
            mock_pw = AsyncMock()
            mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_playwright.return_value.__aenter__.return_value = mock_pw
            
            # Procesar request
            response = await middleware.download_request(mock_request, Mock())
            
            # Verificaciones
            assert response is not None
            assert isinstance(response, HtmlResponse)
            assert 'Rendered content' in response.text
            mock_page.goto.assert_called_once()
            mock_page.close.assert_called_once()
    
    def test_handle_empty_content_detection(self, middleware):
        """Test detección de contenido vacío."""
        # Response con contenido vacío
        empty_response = HtmlResponse(
            url='https://example.com',
            body=b'<html><body></body></html>',
            encoding='utf-8'
        )
        
        # Response con contenido
        full_response = HtmlResponse(
            url='https://example.com',
            body=b'<html><body><p>Content here</p></body></html>',
            encoding='utf-8'
        )
        
        assert middleware._is_empty_content(empty_response) is True
        assert middleware._is_empty_content(full_response) is False
    
    def test_retry_logic_on_empty_content(self, middleware):
        """Test que reintenta cuando encuentra contenido vacío."""
        spider = Mock()
        spider.name = 'test_spider'
        
        request = Request('https://example.com/dynamic')
        request.meta['playwright_retries'] = 0
        
        # Response vacío
        empty_response = HtmlResponse(
            url=request.url,
            body=b'<html><body></body></html>',
            request=request
        )
        
        # Procesar response vacío
        result = middleware.process_response(request, empty_response, spider)
        
        # Debe retornar un nuevo request con playwright habilitado
        assert isinstance(result, Request)
        assert result.meta.get('playwright') is True
        assert result.meta.get('playwright_retries') == 1
    
    def test_max_retries_limit(self, middleware):
        """Test que respeta el límite máximo de reintentos."""
        spider = Mock()
        request = Request('https://example.com/test')
        request.meta['playwright_retries'] = 2  # Ya en el límite
        
        empty_response = HtmlResponse(
            url=request.url,
            body=b'<html><body></body></html>',
            request=request
        )
        
        # No debe reintentar más
        result = middleware.process_response(request, empty_response, spider)
        
        # Debe retornar la response vacía, no un nuevo request
        assert isinstance(result, Response)
        assert result == empty_response


class TestRateLimitMiddleware:
    """Tests para el middleware de rate limiting."""
    
    @pytest.fixture
    def rate_limit_middleware(self):
        """Crear middleware de rate limit."""
        from scraper_core.middlewares.rate_limit_monitor import RateLimitMonitorMiddleware
        
        crawler = Mock()
        crawler.settings = {}
        crawler.stats = Mock()
        
        return RateLimitMonitorMiddleware.from_crawler(crawler)
    
    def test_rate_limit_monitoring(self, rate_limit_middleware):
        """Test que el middleware monitorea las tasas correctamente."""
        spider = Mock()
        spider.name = 'test_spider'
        
        request = Request('https://example.com/test')
        
        # Procesar request
        rate_limit_middleware.process_request(request, spider)
        
        # Verificar que se registró
        assert 'example.com' in rate_limit_middleware.domain_request_count
        assert rate_limit_middleware.domain_request_count['example.com'] == 1
        
        # Procesar otro request al mismo dominio
        request2 = Request('https://example.com/test2')
        rate_limit_middleware.process_request(request2, spider)
        
        assert rate_limit_middleware.domain_request_count['example.com'] == 2
    
    def test_rate_limit_warning(self, rate_limit_middleware):
        """Test que advierte cuando se excede el rate limit."""
        spider = Mock()
        spider.name = 'test_spider'
        spider.logger = Mock()
        
        # Simular muchos requests rápidos
        for i in range(10):
            request = Request(f'https://example.com/test{i}')
            rate_limit_middleware.process_request(request, spider)
        
        # Verificar que se haya registrado estadísticas
        assert rate_limit_middleware.domain_request_count['example.com'] == 10


class TestUserAgentMiddleware:
    """Tests para rotación de user agents."""
    
    def test_user_agent_rotation(self):
        """Test que los user agents rotan correctamente."""
        # Este test verifica que BaseArticleSpider maneja la rotación
        from scraper_core.spiders.base.base_article import BaseArticleSpider
        
        spider = BaseArticleSpider(name='test')
        
        # Crear varios requests
        user_agents = set()
        for _ in range(10):
            request = spider.make_request('https://example.com')
            ua = request.headers.get('User-Agent')
            if ua:
                user_agents.add(ua.decode('utf-8'))
        
        # Debe haber múltiples user agents diferentes
        assert len(user_agents) > 1
