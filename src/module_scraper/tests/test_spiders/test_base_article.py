"""
Unit tests for BaseArticleSpider

Tests the common functionality for article extraction including:
- User-agent rotation
- Error handling and logging
- Common parsing methods
- Data validation
- Compliance with @generador-spiders requirements
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

from scrapy.http import HtmlResponse, Request
from scrapy.utils.test import get_crawler
from scrapy import Spider

# Add the parent directory to the path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from scraper_core.spiders.base.base_article import BaseArticleSpider
from scraper_core.items import ArticuloInItem


class TestBaseArticleSpider(unittest.TestCase):
    """Test cases for BaseArticleSpider"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.spider = BaseArticleSpider(name='test_spider')
        self.spider.logger = Mock()
        
    def _create_response(self, html_content, url='http://example.com/article'):
        """Helper to create a mock response"""
        request = Request(url=url)
        return HtmlResponse(
            url=url,
            request=request,
            body=html_content.encode('utf-8'),
            encoding='utf-8'
        )
    
    def test_spider_initialization(self):
        """Test spider initializes with correct settings"""
        self.assertEqual(self.spider.name, 'test_spider')
        self.assertIsInstance(self.spider.user_agents, list)
        self.assertTrue(len(self.spider.user_agents) > 0)
        self.assertIsInstance(self.spider.failed_urls, list)
        self.assertIsInstance(self.spider.successful_urls, list)
        
    def test_make_request_adds_user_agent(self):
        """Test that make_request adds a random user agent"""
        request = self.spider.make_request('http://example.com')
        
        self.assertIsInstance(request, Request)
        self.assertIn('User-Agent', request.headers)
        user_agent = request.headers.get('User-Agent').decode('utf-8')
        self.assertIn(user_agent, self.spider.user_agents)
        
    def test_extract_article_title_from_meta_tags(self):
        """Test title extraction from meta tags"""
        html = '''
        <html>
            <head>
                <meta property="og:title" content="Test Article Title">
                <meta name="twitter:title" content="Twitter Title">
                <title>Page Title | Site Name</title>
            </head>
            <body>
                <h1>Body Title</h1>
            </body>
        </html>
        '''
        response = self._create_response(html)
        
        title = self.spider.extract_article_title(response)
        self.assertEqual(title, "Test Article Title")
        
    def test_extract_article_title_from_h1(self):
        """Test title extraction from h1 tags"""
        html = '''
        <html>
            <body>
                <article>
                    <h1 class="article-title">Main Article Title</h1>
                </article>
            </body>
        </html>
        '''
        response = self._create_response(html)
        
        title = self.spider.extract_article_title(response)
        self.assertEqual(title, "Main Article Title")
        
    def test_extract_article_title_fallback_to_page_title(self):
        """Test title extraction falls back to page title"""
        html = '''
        <html>
            <head>
                <title>Fallback Title | Site Name</title>
            </head>
            <body>
                <div>No proper h1 here</div>
            </body>
        </html>
        '''
        response = self._create_response(html)
        
        title = self.spider.extract_article_title(response)
        self.assertEqual(title, "Fallback Title")
        
    def test_extract_article_content_from_article_body(self):
        """Test content extraction from article body"""
        html = '''
        <html>
            <body>
                <article>
                    <div class="article-body">
                        <p>First paragraph of the article.</p>
                        <p>Second paragraph with more content.</p>
                        <p>Third paragraph to ensure we have enough text for validation.</p>
                    </div>
                </article>
            </body>
        </html>
        '''
        response = self._create_response(html)
        
        content = self.spider.extract_article_content(response)
        self.assertIsNotNone(content)
        self.assertIn("First paragraph", content)
        self.assertIn("Second paragraph", content)
        self.assertIn("Third paragraph", content)
        
    def test_extract_article_content_filters_scripts(self):
        """Test that script content is filtered out"""
        html = '''
        <html>
            <body>
                <div class="article-content">
                    <p>Actual article content here.</p>
                    <script>function someFunction() { return false; }</script>
                    <p>More article content after script.</p>
                    <style>.some-class { color: red; }</style>
                </div>
            </body>
        </html>
        '''
        response = self._create_response(html)
        
        content = self.spider.extract_article_content(response)
        self.assertIsNotNone(content)
        self.assertIn("Actual article content", content)
        self.assertIn("More article content", content)
        self.assertNotIn("function", content)
        self.assertNotIn("color: red", content)
        
    def test_extract_publication_date_from_meta(self):
        """Test date extraction from meta tags"""
        html = '''
        <html>
            <head>
                <meta property="article:published_time" content="2024-01-15T10:30:00Z">
            </head>
        </html>
        '''
        response = self._create_response(html)
        
        date = self.spider.extract_publication_date(response)
        self.assertIsInstance(date, datetime)
        self.assertEqual(date.year, 2024)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 15)
        
    def test_extract_publication_date_from_time_element(self):
        """Test date extraction from time elements"""
        html = '''
        <html>
            <body>
                <article>
                    <time datetime="2024-02-20T15:45:00+00:00">February 20, 2024</time>
                </article>
            </body>
        </html>
        '''
        response = self._create_response(html)
        
        date = self.spider.extract_publication_date(response)
        self.assertIsInstance(date, datetime)
        self.assertEqual(date.year, 2024)
        self.assertEqual(date.month, 2)
        self.assertEqual(date.day, 20)
        
    def test_extract_publication_date_from_json_ld(self):
        """Test date extraction from JSON-LD structured data"""
        html = '''
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "NewsArticle",
                    "datePublished": "2024-03-10T12:00:00Z"
                }
                </script>
            </head>
        </html>
        '''
        response = self._create_response(html)
        
        date = self.spider.extract_publication_date(response)
        self.assertIsInstance(date, datetime)
        self.assertEqual(date.year, 2024)
        self.assertEqual(date.month, 3)
        self.assertEqual(date.day, 10)
        
    def test_extract_author_from_meta(self):
        """Test author extraction from meta tags"""
        html = '''
        <html>
            <head>
                <meta name="author" content="John Doe">
            </head>
        </html>
        '''
        response = self._create_response(html)
        
        author = self.spider.extract_author(response)
        self.assertEqual(author, "John Doe")
        
    def test_extract_author_with_prefix_cleaning(self):
        """Test author extraction cleans common prefixes"""
        html = '''
        <html>
            <body>
                <span class="author-name">Por María García</span>
            </body>
        </html>
        '''
        response = self._create_response(html)
        
        author = self.spider.extract_author(response)
        self.assertEqual(author, "María García")
        
    def test_extract_multiple_authors(self):
        """Test extraction of multiple authors"""
        html = '''
        <html>
            <body>
                <div class="author">
                    <a>John Smith</a>
                    <a>Jane Doe</a>
                </div>
            </body>
        </html>
        '''
        response = self._create_response(html)
        
        author = self.spider.extract_author(response)
        self.assertEqual(author, "John Smith, Jane Doe")
        
    def test_extract_author_from_json_ld(self):
        """Test author extraction from JSON-LD"""
        html = '''
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@type": "NewsArticle",
                    "author": {
                        "@type": "Person",
                        "name": "Sarah Johnson"
                    }
                }
                </script>
            </head>
        </html>
        '''
        response = self._create_response(html)
        
        author = self.spider.extract_author(response)
        self.assertEqual(author, "Sarah Johnson")
        
    def test_extract_article_metadata(self):
        """Test metadata extraction"""
        html = '''
        <html>
            <head>
                <meta name="description" content="Article description here">
                <meta name="keywords" content="news, test, article">
                <meta property="og:image" content="http://example.com/image.jpg">
                <html lang="es">
            </head>
        </html>
        '''
        response = self._create_response(html)
        
        metadata = self.spider.extract_article_metadata(response)
        
        self.assertIsInstance(metadata, dict)
        self.assertEqual(metadata['description'], "Article description here")
        self.assertEqual(metadata['keywords'], ['news', 'test', 'article'])
        self.assertEqual(metadata['image'], "http://example.com/image.jpg")
        self.assertEqual(metadata['language'], "es")
        
    def test_validate_article_data_valid(self):
        """Test validation of valid article data"""
        article_data = {
            'title': 'Valid Article Title',
            'url': 'http://example.com/article',
            'content': 'This is a valid article with enough content to pass validation. ' * 10
        }
        
        is_valid = self.spider.validate_article_data(article_data)
        self.assertTrue(is_valid)
        
    def test_validate_article_data_missing_title(self):
        """Test validation fails with missing title"""
        article_data = {
            'url': 'http://example.com/article',
            'content': 'This is content without a title.'
        }
        
        is_valid = self.spider.validate_article_data(article_data)
        self.assertFalse(is_valid)
        
    def test_validate_article_data_short_content(self):
        """Test validation fails with short content"""
        article_data = {
            'title': 'Valid Title',
            'url': 'http://example.com/article',
            'content': 'Too short'
        }
        
        is_valid = self.spider.validate_article_data(article_data)
        self.assertFalse(is_valid)
        
    def test_handle_error_logging(self):
        """Test error handling logs appropriately"""
        failure = Mock()
        failure.request = Mock()
        failure.request.url = 'http://example.com/failed'
        failure.value = Exception("Test error")
        failure.check.return_value = False
        
        self.spider.handle_error(failure)
        
        self.assertIn('http://example.com/failed', self.spider.failed_urls)
        self.spider.logger.error.assert_called()
        
    def test_spider_closed_logging(self):
        """Test spider closed logs statistics"""
        self.spider.successful_urls = ['url1', 'url2']
        self.spider.failed_urls = ['url3']
        
        self.spider.spider_closed(self.spider)
        
        self.spider.logger.info.assert_called()
        # Check that statistics were logged
        call_args = str(self.spider.logger.info.call_args)
        self.assertIn('2', call_args)  # successful count
        self.assertIn('1', call_args)  # failed count

    # =========================================================================
    # Tests específicos para cumplimiento con @generador-spiders
    # =========================================================================
    
    def test_base_spider_provides_required_methods(self):
        """Test que BaseArticleSpider provee todos los métodos requeridos por el generador"""
        required_methods = [
            'extract_article_title',
            'extract_article_content',
            'extract_publication_date',
            'extract_author',
            'validate_article_data',
            'make_request',
            'handle_error'
        ]
        
        for method in required_methods:
            self.assertTrue(hasattr(self.spider, method), 
                          f"BaseArticleSpider debe proveer el método '{method}'")
            self.assertTrue(callable(getattr(self.spider, method)),
                          f"'{method}' debe ser callable")
    
    def test_base_spider_custom_settings(self):
        """Test que BaseArticleSpider tiene las configuraciones base requeridas"""
        self.assertTrue(hasattr(BaseArticleSpider, 'custom_settings'),
                       "BaseArticleSpider debe tener custom_settings")
        
        settings = BaseArticleSpider.custom_settings
        
        # Verificar configuraciones esenciales
        self.assertIn('USER_AGENT', settings,
                     "custom_settings debe incluir USER_AGENT")
        self.assertIn('ROBOTSTXT_OBEY', settings,
                     "custom_settings debe incluir ROBOTSTXT_OBEY")
        self.assertTrue(settings.get('ROBOTSTXT_OBEY', False),
                       "ROBOTSTXT_OBEY debe ser True por defecto")
    
    def test_base_spider_returns_articulo_in_item(self):
        """Test que los métodos pueden trabajar con ArticuloInItem"""
        # Crear un response completo
        html = '''
        <html>
            <head>
                <meta property="og:title" content="Test Article for Generator">
                <meta property="article:published_time" content="2024-01-15T10:30:00Z">
                <meta name="author" content="Test Author">
            </head>
            <body>
                <article>
                    <div class="article-content">
                        <p>This is a test article with sufficient content to pass validation requirements.</p>
                        <p>It contains multiple paragraphs to ensure we meet the minimum content length.</p>
                        <p>The content should be properly extracted and validated by the spider.</p>
                    </div>
                </article>
            </body>
        </html>
        '''
        response = self._create_response(html, 'http://example.com/section/article')
        
        # Simular creación de item como lo haría un spider hijo
        item = ArticuloInItem()
        item['url'] = response.url
        item['titular'] = self.spider.extract_article_title(response)
        item['contenido_texto'] = self.spider.extract_article_content(response)
        item['fecha_publicacion'] = self.spider.extract_publication_date(response)
        item['autor'] = self.spider.extract_author(response)
        
        # Verificar que los campos se extrajeron correctamente
        self.assertEqual(item['titular'], "Test Article for Generator")
        self.assertIn("test article with sufficient content", item['contenido_texto'])
        self.assertEqual(item['autor'], "Test Author")
        self.assertIsInstance(item['fecha_publicacion'], datetime)
    
    def test_base_spider_handles_empty_responses(self):
        """Test que BaseArticleSpider maneja respuestas vacías sin crashear"""
        empty_response = self._create_response('')
        
        # Ninguno de estos debe lanzar excepción
        title = self.spider.extract_article_title(empty_response)
        content = self.spider.extract_article_content(empty_response)
        date = self.spider.extract_publication_date(empty_response)
        author = self.spider.extract_author(empty_response)
        metadata = self.spider.extract_article_metadata(empty_response)
        
        # Deben retornar valores por defecto apropiados
        self.assertIsNone(title)
        self.assertEqual(content, '')
        self.assertIsNone(date)
        self.assertIsNone(author)
        self.assertIsInstance(metadata, dict)
    
    def test_base_spider_respects_minimum_content_length(self):
        """Test que la validación respeta longitud mínima de contenido (generador requiere 100 chars)"""
        # Contenido justo en el límite
        article_data_exact = {
            'title': 'Test Title',
            'url': 'http://example.com/article',
            'content': 'x' * 100  # Exactamente 100 caracteres
        }
        self.assertTrue(self.spider.validate_article_data(article_data_exact))
        
        # Contenido bajo el límite
        article_data_short = {
            'title': 'Test Title',
            'url': 'http://example.com/article',
            'content': 'x' * 99  # 99 caracteres
        }
        self.assertFalse(self.spider.validate_article_data(article_data_short))
    
    def test_base_spider_provides_error_callback(self):
        """Test que BaseArticleSpider puede ser usado como errback en requests"""
        # Verificar que handle_error puede ser usado como errback
        request = self.spider.make_request('http://example.com/test', errback=self.spider.handle_error)
        
        self.assertEqual(request.errback, self.spider.handle_error)
        self.assertIsNotNone(request.errback)
    
    def test_base_spider_extracts_structured_data(self):
        """Test extracción de datos estructurados (JSON-LD) como requiere el generador"""
        html = '''
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "NewsArticle",
                    "headline": "Structured Data Title",
                    "datePublished": "2024-01-15T10:30:00Z",
                    "author": {
                        "@type": "Person",
                        "name": "Structured Author"
                    },
                    "publisher": {
                        "@type": "Organization",
                        "name": "Test Publisher"
                    },
                    "description": "Article description from structured data"
                }
                </script>
            </head>
            <body>
                <article>
                    <p>Article content goes here.</p>
                </article>
            </body>
        </html>
        '''
        response = self._create_response(html)
        
        # Los métodos deben priorizar datos estructurados cuando están disponibles
        title = self.spider.extract_article_title(response)
        date = self.spider.extract_publication_date(response)
        author = self.spider.extract_author(response)
        
        # Verificar que se extrajeron del JSON-LD
        self.assertEqual(title, "Structured Data Title")
        self.assertEqual(author, "Structured Author")
        self.assertIsInstance(date, datetime)
        self.assertEqual(date.year, 2024)
    
    def test_base_spider_compatible_with_crawl_once(self):
        """Test que los requests creados son compatibles con scrapy-crawl-once"""
        request = self.spider.make_request(
            'http://example.com/article',
            meta={'crawl_once': True}
        )
        
        # Verificar que el meta se preserva
        self.assertTrue(request.meta.get('crawl_once'))
        
        # Verificar que se puede añadir callback
        request_with_callback = self.spider.make_request(
            'http://example.com/article',
            callback=self.spider.parse,
            meta={'crawl_once': True}
        )
        self.assertEqual(request_with_callback.callback, self.spider.parse)
        self.assertTrue(request_with_callback.meta.get('crawl_once'))


if __name__ == '__main__':
    unittest.main()
