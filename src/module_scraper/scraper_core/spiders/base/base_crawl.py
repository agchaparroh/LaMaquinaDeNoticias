"""
Base Crawl Spider for La Máquina de Noticias

This module provides the BaseCrawlSpider class, which extends Scrapy's CrawlSpider
with common functionality for crawling news websites following links.
"""

import logging
import random
from typing import Iterator, Dict, Any, Optional, List, Union, Tuple
from datetime import datetime
from urllib.parse import urlparse

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request, Response
from scrapy.utils.misc import arg_to_iter

from .base_article import BaseArticleSpider


class BaseCrawlSpider(BaseArticleSpider, CrawlSpider):
    """
    Base spider class for crawl-based article extraction.
    
    This class extends both BaseArticleSpider and Scrapy's CrawlSpider to provide:
    - Rule-based link following
    - Depth control
    - Domain filtering
    - Article extraction from crawled pages
    - Customizable link extraction patterns
    """
    
    # Override custom settings to add crawl-specific configurations
    custom_settings = {
        **BaseArticleSpider.custom_settings,
        'DEPTH_LIMIT': 3,  # Maximum depth to crawl
        'DEPTH_STATS': True,  # Enable depth statistics
        'CLOSESPIDER_PAGECOUNT': 100,  # Stop after crawling N pages
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_DELAY': 1.5,
    }
    
    # Default patterns for article URLs
    article_url_patterns = [
        r'/\d{4}/\d{2}/\d{2}/',  # Date patterns (2024/01/15)
        r'/article/',
        r'/news/',
        r'/story/',
    ]
    
    # Default patterns to exclude
    exclude_patterns = [
        r'/tag/',
        r'/category/',
        r'/author/',
        r'/search/',
        r'/login',
        r'/register',
        r'\.pdf$',
        r'\.jpg$',
        r'\.png$',
    ]
    
    def __init__(self, *args, **kwargs):
        """Initialize the spider with crawl-specific settings."""
        # Extract custom parameters
        self.follow_links = kwargs.pop('follow_links', True)
        self.max_pages = int(kwargs.pop('max_pages', 100))
        self.custom_article_patterns = kwargs.pop('article_patterns', '').split(',') if kwargs.get('article_patterns') else []
        
        # Initialize parent classes
        super().__init__(*args, **kwargs)
        
        # Set up page counter
        self.pages_crawled = 0
        
        # Build rules if not already defined by subclass
        if not hasattr(self, 'rules') or not self.rules:
            self.rules = self._build_default_rules()
            self._compile_rules()
        
        self.logger.info(f"Crawl spider initialized - max pages: {self.max_pages}, follow links: {self.follow_links}")
    
    def _build_default_rules(self) -> Tuple[Rule, ...]:
        """
        Build default crawling rules.
        
        Returns:
            tuple: Tuple of Rule objects
        """
        rules = []
        
        # Combine default and custom article patterns
        all_article_patterns = self.article_url_patterns + self.custom_article_patterns
        
        # Rule for following links (without callback)
        if self.follow_links:
            follow_rule = Rule(
                LinkExtractor(
                    deny=self.exclude_patterns,
                    unique=True,
                ),
                follow=True,
            )
            rules.append(follow_rule)
        
        # Rule for parsing article pages
        if all_article_patterns:
            article_rule = Rule(
                LinkExtractor(
                    allow=all_article_patterns,
                    deny=self.exclude_patterns,
                    unique=True,
                ),
                callback='parse_article',
                follow=False,
            )
            rules.append(article_rule)
        
        # Default rule to parse any page not matched by other rules
        default_rule = Rule(
            LinkExtractor(
                deny=self.exclude_patterns,
                unique=True,
            ),
            callback='parse_page',
            follow=self.follow_links,
        )
        rules.append(default_rule)
        
        return tuple(rules)
    
    def parse_start_url(self, response: Response) -> Iterator[Union[Dict[str, Any], Request]]:
        """
        Parse start URLs.
        
        This method is called for the start URLs. It can be overridden
        to implement custom logic for start pages.
        
        Args:
            response: The response object
            
        Yields:
            dict or Request: Items or requests
        """
        self.logger.info(f"Parsing start URL: {response.url}")
        
        # Try to extract article from start page if it matches patterns
        if self._is_article_page(response):
            yield from self.parse_article(response)
        
        # Follow links from start page
        if self.follow_links:
            yield from self._follow_links(response)
    
    def parse_page(self, response: Response) -> Iterator[Union[Dict[str, Any], Request]]:
        """
        Parse a general page.
        
        This is the default callback for pages that don't match article patterns.
        
        Args:
            response: The response object
            
        Yields:
            dict or Request: Items or requests
        """
        self.pages_crawled += 1
        
        if self.pages_crawled >= self.max_pages:
            self.logger.info(f"Reached maximum page count ({self.max_pages}), stopping spider")
            self.crawler.engine.close_spider(self, 'closespider_pagecount')
            return
        
        self.logger.debug(f"Parsing page: {response.url}")
        
        # Check if this is actually an article page
        if self._is_article_page(response):
            yield from self.parse_article(response)
    
    def parse_article(self, response: Response) -> Iterator[Dict[str, Any]]:
        """
        Parse an article page.
        
        This method is called for URLs that match article patterns.
        
        Args:
            response: The response object
            
        Yields:
            dict: Extracted article data
        """
        self.logger.info(f"Parsing article: {response.url}")
        
        # Extract article data using parent class methods
        article_data = {
            'url': response.url,
            'title': self.extract_article_title(response),
            'content': self.extract_article_content(response),
            'author': self.extract_author(response),
            'publication_date': self.extract_publication_date(response),
            'source': self.name,
            'scraped_at': datetime.now().isoformat(),
        }
        
        # Add crawl-specific metadata
        article_data['depth'] = response.meta.get('depth', 0)
        article_data['referrer'] = response.request.headers.get('Referer', b'').decode('utf-8')
        
        # Add general metadata
        metadata = self.extract_article_metadata(response)
        article_data.update(metadata)
        
        # Validate and yield
        if self.validate_article_data(article_data):
            self.successful_urls.append(response.url)
            yield article_data
        else:
            self.logger.warning(f"Invalid article data for {response.url}")
    
    def _is_article_page(self, response: Response) -> bool:
        """
        Determine if a page is an article based on various heuristics.
        
        Args:
            response: The response object
            
        Returns:
            bool: True if the page appears to be an article
        """
        # Check URL patterns
        url = response.url
        for pattern in self.article_url_patterns + self.custom_article_patterns:
            if pattern in url:
                return True
        
        # Check for article schema.org markup
        if response.css('[itemtype*="Article"]').get():
            return True
        
        # Check for article-specific meta tags
        article_meta_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="article:author"]',
            'meta[property="og:type"][content="article"]',
        ]
        
        for selector in article_meta_selectors:
            if response.css(selector).get():
                return True
        
        # Check content length and structure
        paragraphs = response.css('article p::text, .article-content p::text, .content p::text').getall()
        if paragraphs and len(' '.join(paragraphs)) > 500:
            return True
        
        return False
    
    def _follow_links(self, response: Response) -> Iterator[Request]:
        """
        Extract and follow links from a response.
        
        This method is used internally when custom link following is needed.
        
        Args:
            response: The response object
            
        Yields:
            Request: Requests for found links
        """
        # This is typically handled by CrawlSpider's rules
        # But can be overridden for custom behavior
        pass
    
    def _requests_to_follow(self, response: Response) -> Iterator[Request]:
        """
        Override CrawlSpider's method to add custom request filtering.
        
        Args:
            response: The response object
            
        Yields:
            Request: Filtered requests
        """
        if not isinstance(response, scrapy.http.Response):
            return
        
        # Check if we've reached the page limit
        if self.pages_crawled >= self.max_pages:
            self.logger.info(f"Reached maximum page count ({self.max_pages}), not following more links")
            return
        
        # Get requests from parent class
        seen = set()
        for request in super()._requests_to_follow(response):
            # Additional filtering can be added here
            if request.url not in seen:
                seen.add(request.url)
                # Add custom headers
                request.headers['User-Agent'] = random.choice(self.user_agents)
                yield request
    
    def handle_error(self, failure):
        """
        Handle request errors with additional crawl-specific logging.
        
        Args:
            failure: The failure object from Twisted
        """
        super().handle_error(failure)
        
        # Log crawl-specific information
        if hasattr(failure.request, 'meta'):
            depth = failure.request.meta.get('depth', 0)
            self.logger.debug(f"Failed request at depth {depth}: {failure.request.url}")
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """
        Create spider instance from crawler.
        
        This allows us to access crawler settings and signals.
        """
        spider = super().from_crawler(crawler, *args, **kwargs)
        
        # Connect to spider_closed signal
        crawler.signals.connect(
            spider.spider_closed,
            signal=scrapy.signals.spider_closed
        )
        
        # Connect to other useful signals
        crawler.signals.connect(
            spider._item_scraped,
            signal=scrapy.signals.item_scraped
        )
        
        return spider
    
    def _item_scraped(self, item, response, spider):
        """
        Called when an item is successfully scraped.
        
        Args:
            item: The scraped item
            response: The response that generated the item
            spider: The spider instance
        """
        self.logger.debug(f"Item scraped from {response.url} at depth {response.meta.get('depth', 0)}")
    
    def spider_closed(self, spider):
        """
        Called when the spider is closed.
        
        Log final crawl statistics.
        """
        super().spider_closed(spider)
        
        # Log crawl-specific stats
        stats = self.crawler.stats
        self.logger.info(
            f"Crawl statistics - Pages crawled: {self.pages_crawled}, "
            f"Max depth: {stats.get_value('request_depth_max', 0)}, "
            f"Domains: {len(stats.get_value('offsite/domains', []))}"
        )
