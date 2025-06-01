# tests/test_playwright/test_playwright_basic.py
import unittest
from unittest.mock import Mock, patch
from scrapy.http import HtmlResponse, Request
from scrapy.utils.test import get_crawler

from scraper_core.middlewares.playwright_custom_middleware import PlaywrightCustomDownloaderMiddleware


class TestPlaywrightBasicFunctionality(unittest.TestCase):
    """Basic tests to verify Playwright middleware works correctly."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.crawler = get_crawler()
        self.crawler.stats = Mock()
        
        with patch('scraper_core.middlewares.playwright_custom_middleware.load_object'):
            self.middleware = PlaywrightCustomDownloaderMiddleware.from_crawler(self.crawler)
    
    def test_middleware_initialization(self):
        """Test middleware initializes with correct settings."""
        self.assertIsNotNone(self.middleware)
        self.assertEqual(self.middleware.max_playwright_retries, 2)
        self.assertEqual(self.middleware.playwright_timeout, 30000)
    
    def test_empty_content_detection(self):
        """Test empty content is correctly detected."""
        spider = Mock()
        
        # Empty body
        response = HtmlResponse('http://test.com', body=b'')
        self.assertTrue(self.middleware._is_content_empty(response, spider))
        
        # Loading message
        response = HtmlResponse('http://test.com', body=b'<html><body>Loading...</body></html>')
        self.assertTrue(self.middleware._is_content_empty(response, spider))
        
        # Sufficient content
        content = "Real article content. " * 20  # Over 100 chars
        response = HtmlResponse('http://test.com', body=f'<html><body>{content}</body></html>'.encode())
        self.assertFalse(self.middleware._is_content_empty(response, spider))
    
    def test_playwright_error_detection(self):
        """Test Playwright errors are correctly identified."""
        spider = Mock()
        
        # Timeout error
        response = HtmlResponse('http://test.com', status=524)
        self.assertEqual(self.middleware._detect_playwright_error(response, spider), 'timeout')
        
        # Browser error
        response = HtmlResponse('http://test.com', body=b'playwright error occurred')
        self.assertEqual(self.middleware._detect_playwright_error(response, spider), 'browser_error')
        
        # No error
        response = HtmlResponse('http://test.com', body=b'normal content')
        self.assertIsNone(self.middleware._detect_playwright_error(response, spider))
    
    async def test_empty_content_triggers_playwright_retry(self):
        """Test that empty content triggers Playwright retry."""
        spider = Mock()
        request = Request('http://test.com')
        empty_response = HtmlResponse('http://test.com', body=b'')
        
        result = await self.middleware.process_response(request, empty_response, spider)
        
        # Should return a new Request with Playwright enabled
        self.assertIsInstance(result, Request)
        self.assertTrue(result.meta['playwright'])
        self.assertTrue(result.meta['playwright_retried'])
    
    async def test_playwright_error_triggers_retry(self):
        """Test that Playwright errors trigger retries."""
        spider = Mock()
        request = Request('http://test.com')
        request.meta['playwright'] = True
        error_response = HtmlResponse('http://test.com', status=524)
        
        result = await self.middleware.process_response(request, error_response, spider)
        
        # Should return retry request
        self.assertIsInstance(result, Request)
        self.assertEqual(result.meta['playwright_retry_count'], 1)
    
    async def test_successful_response_passthrough(self):
        """Test that successful responses pass through unchanged."""
        spider = Mock()
        request = Request('http://test.com')
        good_content = "This is good article content. " * 10
        good_response = HtmlResponse('http://test.com', body=f'<html><body>{good_content}</body></html>'.encode())
        
        result = await self.middleware.process_response(request, good_response, spider)
        
        # Should return the original response
        self.assertEqual(result, good_response)
    
    def test_fallback_request_creation(self):
        """Test fallback request creation removes Playwright metadata."""
        spider = Mock()
        request = Request('http://test.com')
        request.meta.update({
            'playwright': True,
            'playwright_include_page': True,
            'other_meta': 'keep_this'
        })
        
        fallback = self.middleware._create_fallback_request(request, spider, 'test_reason')
        
        # Should remove Playwright keys but keep others
        self.assertNotIn('playwright', fallback.meta)
        self.assertNotIn('playwright_include_page', fallback.meta)
        self.assertIn('other_meta', fallback.meta)
        self.assertTrue(fallback.meta['playwright_fallback'])


if __name__ == '__main__':
    unittest.main()
