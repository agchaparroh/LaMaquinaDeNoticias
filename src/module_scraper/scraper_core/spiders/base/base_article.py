"""
Base Article Spider for La Máquina de Noticias

This module provides the BaseArticleSpider class, which contains common functionality
for spiders that extract individual articles from news websites.
"""

import logging
import random
from typing import Dict, Any, Optional, Iterator
from datetime import datetime

import scrapy
from scrapy.http import Response, Request

from scrapy.utils.misc import arg_to_iter
from ..items import ArticuloInItem
from ..itemloaders import ArticuloInItemLoader


class BaseArticleSpider(scrapy.Spider):
    """
    Base spider class for article extraction.
    
    This class provides common functionality for extracting article data including:
    - User-agent rotation
    - Error handling and logging
    - Common parsing methods
    - Respect for robots.txt
    - Delay and throttling logic
    """
    
    # User agents pool for rotation
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ]
    
    # Default spider settings
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,  # Default delay between requests
        'RANDOMIZE_DOWNLOAD_DELAY': True,  # Randomize delays (0.5 * to 1.5 * delay)
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,  # Be polite
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        'USE_PLAYWRIGHT_FOR_EMPTY_CONTENT': True, # Intentar con Playwright si el contenido inicial está vacío
        'DOWNLOAD_TIMEOUT': 30,
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = list(arg_to_iter(kwargs.get('start_urls', [])))
        self.allowed_domains = list(arg_to_iter(kwargs.get('allowed_domains', [])))
        self.feed_url = kwargs.get('feed_url') # For RSS/Atom feeds
        self.sitemap_urls = list(arg_to_iter(kwargs.get('sitemap_urls', []))) # For sitemap spiders
        
        # Initialize logger
        self.logger = logging.getLogger(self.name)
        
        # Tracking URLs
        self.successful_urls = []
        self.failed_urls = []

    def start_requests(self) -> Iterator[Request]:
        """
        Generate initial requests based on spider configuration.
        
        Handles start_urls, feed_url, and sitemap_urls.
        """
        if self.start_urls:
            for url in self.start_urls:
                yield self.make_request(url, self.parse_article_list) # Assumes a method to parse lists of articles
        elif self.feed_url:
            yield self.make_request(self.feed_url, self.parse_feed)
        elif self.sitemap_urls:
            for url in self.sitemap_urls: # This part is usually handled by SitemapSpider itself
                yield self.make_request(url, self.parse_sitemap_index_or_sitemap) # Custom method for sitemap handling
        else:
            self.logger.warning("No start_urls, feed_url, or sitemap_urls provided.")

    def make_request(self, url: str, callback_method, meta: Optional[Dict[str, Any]] = None, 
                     method: str = 'GET', body: Optional[Any] = None, 
                     dont_filter: bool = False) -> Request:
        """
        Create a Scrapy Request object with rotated user-agent and error handling.
        
        Args:
            url: The URL to request
            callback_method: The method to call upon successful download
            meta: Optional dictionary of metadata for the request
            method: HTTP method (default: 'GET')
            body: Optional request body
            dont_filter: If True, request will not be filtered by DupeFilter
            
        Returns:
            A Scrapy Request object
        """
        headers = {'User-Agent': random.choice(self.user_agents)}
        
        current_meta = meta.copy() if meta else {}
        # Add Playwright meta if needed by specific spiders
        # current_meta.setdefault('playwright', False) 
        # current_meta.setdefault('playwright_include_page', False)
        # current_meta.setdefault('playwright_page_methods', [])

        return Request(
            url,
            callback=callback_method,
            errback=self.handle_error,
            headers=headers,
            meta=current_meta,
            method=method,
            body=body,
            dont_filter=dont_filter
        )

    def parse_article_list(self, response: Response) -> Iterator[Request]:
        """
        Parse a page listing multiple articles and yield requests for each article.
        
        This method should be overridden by specific spiders.
        
        Args:
            response: The HTTP response from the article list page
            
        Yields:
            Scrapy Request objects for individual article pages
        """
        self.logger.info(f"Parsing article list: {response.url}")
        # Example: extract article links (to be customized)
        # article_links = response.xpath('//a[@class="article-link"]/@href').getall()
        # for link in article_links:
        #     yield self.make_request(response.urljoin(link), self.parse_article)
        raise NotImplementedError(f"{self.name} must implement parse_article_list or override start_requests.")

    def parse_feed(self, response: Response) -> Iterator[Request]:
        """
        Parse an RSS or Atom feed and yield requests for each article.
        
        This method should be overridden by specific spiders.
        
        Args:
            response: The HTTP response from the feed URL
            
        Yields:
            Scrapy Request objects for individual article pages
        """
        self.logger.info(f"Parsing feed: {response.url}")
        # Example: extract links from feed items (to be customized)
        # response.selector.remove_namespaces() # If namespaces are an issue
        # links = response.xpath('//item/link/text()').getall() # For RSS
        # links.extend(response.xpath('//entry/link[@rel="alternate"]/@href').getall()) # For Atom
        # for link in links:
        #     yield self.make_request(link, self.parse_article)
        raise NotImplementedError(f"{self.name} must implement parse_feed or override start_requests.")

    def parse_sitemap_index_or_sitemap(self, response: Response) -> Iterator[Request]:
        """
        Parse a sitemap index or a sitemap file.
        
        This method is a placeholder. Scrapy's SitemapSpider handles this automatically.
        If not using SitemapSpider, this needs custom implementation.
        
        Args:
            response: The HTTP response from the sitemap URL
            
        Yields:
            Scrapy Request objects for sitemaps or article pages
        """
        self.logger.info(f"Parsing sitemap: {response.url}")
        # This logic is typically handled by SitemapSpider.
        # If implementing manually:
        # 1. Check if it's a sitemap index (contains <sitemaploc>) or a URL sitemap (contains <url>).
        # 2. If sitemap index, extract sitemap URLs and yield requests for them.
        # 3. If URL sitemap, extract article URLs and yield requests for them (to self.parse_article).
        raise NotImplementedError(f"{self.name} should use SitemapSpider or implement sitemap parsing.")

    def parse_article(self, response: Response) -> Optional[ArticuloInItem]:
        """
        Parse the article page and extract data using ArticuloItemLoader.
        Optionally retries with Playwright if initial content is insufficient.
        
        This method provides a base implementation. Specific spiders should override
        the selectors or this method entirely if more complex logic is needed.
        Validation of the item should be handled by item pipelines.
        
        Args:
            response: The HTTP response from the article page
            
        Returns:
            An ArticuloInItem instance or None if retrying.
        """
        self.logger.info(f"Parsing article: {response.url}")

        is_playwright_retry = response.meta.get('playwright_retried', False)
        was_original_playwright_request = response.meta.get('playwright', False)

        loader = ArticuloInItemLoader(item=ArticuloInItem(), response=response)

        # --- Populate common fields ---
        loader.add_value('url', response.url)
        loader.add_value('fuente', self.name)
        loader.add_xpath('titular', '//title/text()')
        loader.add_xpath('titular', '//h1/text()')
        loader.add_xpath('contenido_html', '//article')
        loader.add_xpath('contenido_html', '//*[contains(@class, "article-body")]')
        loader.add_xpath('contenido_html', '//*[contains(@id, "article-content")]')
        loader.add_xpath('contenido_html', '//*[contains(@class, "entry-content")]')
        loader.add_xpath('contenido_html', '//*[contains(@itemprop, "articleBody")]')

        metadata_dict = self._extract_metadata(response)
        if metadata_dict.get('publication_date'):
            loader.add_value('fecha_publicacion', metadata_dict.get('publication_date'))
        if metadata_dict.get('language'):
            loader.add_value('idioma', metadata_dict.get('language'))
        if metadata_dict.get('keywords'):
            loader.add_value('etiquetas_fuente', metadata_dict.get('keywords'))

        # --- Load the item ---
        article_item = loader.load_item()

        # Verificar si el contenido se extrajo
        # Usamos 'get_output_value' del loader para verificar el campo procesado.
        # El campo exacto a verificar puede depender de tus procesadores de items.
        # Asumimos que 'contenido_html' es el campo crudo y 'contenido_texto' podría ser el procesado.
        # Si 'contenido_html' está vacío después de los XPaths, es un buen indicador.
        
        # Para ser más robustos, verificamos el 'contenido_html' directamente del loader ANTES de que se procese a texto.
        # O, si confías en que 'contenido_texto' se genera a partir de 'contenido_html', puedes verificar 'contenido_texto' en el item.
        # Aquí vamos a verificar si 'contenido_html' obtuvo algún valor a través de los XPath.
        # Si el loader no pudo encontrar nada para 'contenido_html' con los selectores,
        # el campo 'contenido_html' en 'article_item' podría estar vacío o no existir.

        # Una forma de verificar si los selectores de contenido funcionaron es ver el valor recogido por el loader:
        collected_content_html = loader.get_collected_values('contenido_html')

        if not collected_content_html: # Si no se recolectó nada para contenido_html
            self.logger.warning(f"No content extracted for 'contenido_html' from {response.url} with standard request.")
            if not is_playwright_retry and not was_original_playwright_request and self.settings.getbool('USE_PLAYWRIGHT_FOR_EMPTY_CONTENT', True):
                self.logger.info(f"Retrying {response.url} with Playwright as 'contenido_html' was empty.")
                new_meta = response.meta.copy()
                new_meta.update({
                    'playwright': True,
                    'playwright_retried': True,
                })
                yield Request(
                    response.url,
                    callback=self.parse_article,
                    meta=new_meta,
                    errback=self.handle_error, # Asegúrate que este método existe y es adecuado
                    dont_filter=True
                )
                return # No devuelvas el item actual, espera el reintento

        # Si llegamos aquí, el contenido se extrajo o es un reintento de Playwright, o no se reintenta.
        self.successful_urls.append(response.url)
        self.logger.info(f"Successfully parsed: {response.url}. Item will be passed to pipelines for validation and processing.")
        return article_item

    def _extract_metadata(self, response: Response) -> Dict[str, Any]:
        """
        Extract common metadata from the article page.
        
        Looks for meta tags (OpenGraph, Twitter Cards, standard meta) and LD+JSON.
        
        Args:
            response: The HTTP response from the article page
            
        Returns:
            A dictionary containing extracted metadata.
        """
        metadata = {}
        
        # OpenGraph
        metadata['og_title'] = response.xpath("//meta[@property='og:title']/@content").get()
        metadata['og_description'] = response.xpath("//meta[@property='og:description']/@content").get()
        metadata['og_url'] = response.xpath("//meta[@property='og:url']/@content").get()
        metadata['og_image'] = response.xpath("//meta[@property='og:image']/@content").get()
        metadata['og_type'] = response.xpath("//meta[@property='og:type']/@content").get()
        metadata['og_site_name'] = response.xpath("//meta[@property='og:site_name']/@content").get()
        
        # Twitter Cards
        metadata['twitter_card'] = response.xpath("//meta[@name='twitter:card']/@content").get()
        metadata['twitter_title'] = response.xpath("//meta[@name='twitter:title']/@content").get()
        metadata['twitter_description'] = response.xpath("//meta[@name='twitter:description']/@content").get()
        metadata['twitter_image'] = response.xpath("//meta[@name='twitter:image']/@content").get()
        metadata['twitter_site'] = response.xpath("//meta[@name='twitter:site']/@content").get()
        
        # Standard meta tags
        metadata['description'] = response.xpath("//meta[@name='description']/@content").get()
        metadata['keywords'] = response.xpath("//meta[@name='keywords']/@content").get()
        metadata['author'] = response.xpath("//meta[@name='author']/@content").get()
        
        # Publication date (common meta tags)
        pub_date_str = response.xpath("//meta[@property='article:published_time']/@content").get() or \
                       response.xpath("//meta[@name='pubdate']/@content").get() or \
                       response.xpath("//meta[@name='sailthru.date']/@content").get() or \
                       response.xpath("//meta[@name='date']/@content").get()
        
        if pub_date_str:
            try:
                # Attempt to parse with timezone info if present
                metadata['publication_date'] = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Fallback for simpler date formats without timezone
                    metadata['publication_date'] = datetime.strptime(pub_date_str.split('T')[0], '%Y-%m-%d')
                except ValueError:
                    self.logger.debug(f"Could not parse publication date: {pub_date_str}")
                    metadata['publication_date'] = None
        
        # Language (from html lang attribute)
        lang = response.xpath("/html/@lang").get()
        if lang:
            metadata['language'] = lang
        
        return metadata
    
    def handle_error(self, failure):
        """
        Handle request errors.
        
        Args:
            failure: The failure object from Twisted
        """
        request = failure.request
        self.failed_urls.append(request.url)
        
        if failure.check(scrapy.exceptions.IgnoreRequest):
            self.logger.info(f"Request ignored: {request.url}")
        else:
            self.logger.error(f"Request failed: {request.url} - {failure.value}")
        
        # Log statistics periodically
        if len(self.failed_urls) % 10 == 0:
            self.logger.info(
                f"Progress - Successful: {len(self.successful_urls)}, "
                f"Failed: {len(self.failed_urls)}"
            )
    
    def validate_article_data(self, article_data: Dict[str, Any]) -> bool:
        """
        Validate extracted article data.
        
        Args:
            article_data: The extracted article data
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        # Check required fields
        required_fields = ['title', 'url']
        for field in required_fields:
            if not article_data.get(field):
                self.logger.warning(f"Missing required field: {field}")
                return False
        
        # Check content length
        content = article_data.get('content', '')
        if len(content) < 100:
            self.logger.warning(f"Content too short for {article_data['url']}")
            return False
        
        return True
    
    def spider_closed(self, spider):
        """
        Called when the spider is closed.
        
        Log final statistics.
        """
        self.logger.info(
            f"Spider closed - Total successful: {len(self.successful_urls)}, "
            f"Total failed: {len(self.failed_urls)}"
        )
        
        if self.failed_urls:
            self.logger.info(f"Failed URLs: {self.failed_urls[:10]}...")  # Log first 10
