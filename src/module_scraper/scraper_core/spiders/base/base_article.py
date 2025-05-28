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
from scrapy.exceptions import DropItem
from scrapy.utils.misc import arg_to_iter


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
        'DOWNLOAD_TIMEOUT': 30,
    }
    
    def __init__(self, *args, **kwargs):
        """Initialize the spider with enhanced logging and configuration."""
        super().__init__(*args, **kwargs)
        self.logger.setLevel(logging.INFO)
        self.failed_urls = []
        self.successful_urls = []
        
    def start_requests(self) -> Iterator[Request]:
        """
        Generate initial requests with random user agents.
        
        Yields:
            Request: Initial requests with custom headers
        """
        for url in self.start_urls:
            yield self.make_request(url)
    
    def make_request(self, url: str, callback=None, **kwargs) -> Request:
        """
        Create a request with a random user agent.
        
        Args:
            url: The URL to request
            callback: The callback method (defaults to self.parse)
            **kwargs: Additional request parameters
            
        Returns:
            Request: A configured request object
        """
        headers = kwargs.pop('headers', {})
        headers['User-Agent'] = random.choice(self.user_agents)
        
        return Request(
            url,
            callback=callback or self.parse,
            headers=headers,
            errback=self.handle_error,
            **kwargs
        )
    
    def parse(self, response: Response) -> Iterator[Dict[str, Any]]:
        """
        Parse the response and extract article data.
        
        This method should be overridden by subclasses to implement
        specific parsing logic.
        
        Args:
            response: The response object to parse
            
        Yields:
            dict: Extracted article data
        """
        raise NotImplementedError("Subclasses must implement parse method")
    
    def extract_article_title(self, response: Response) -> Optional[str]:
        """
        Extract article title from the response.
        
        This method tries multiple selectors to find the title.
        
        Args:
            response: The response object
            
        Returns:
            str: The article title or None if not found
        """
        # Try common title selectors
        title_selectors = [
            'h1::text',
            'h1 *::text',
            'title::text',
            'meta[property="og:title"]::attr(content)',
            'meta[name="twitter:title"]::attr(content)',
            '.article-title::text',
            '.title::text',
            '.headline::text',
        ]
        
        for selector in title_selectors:
            title = response.css(selector).get()
            if title:
                return title.strip()
        
        # Try XPath selectors
        title_xpaths = [
            '//h1/text()',
            '//h1//text()',
            '//article//h1//text()',
        ]
        
        for xpath in title_xpaths:
            titles = response.xpath(xpath).getall()
            if titles:
                return ' '.join(titles).strip()
        
        self.logger.warning(f"Could not extract title from {response.url}")
        return None
    
    def extract_article_content(self, response: Response) -> Optional[str]:
        """
        Extract article content from the response.
        
        This method tries multiple selectors to find the main content.
        
        Args:
            response: The response object
            
        Returns:
            str: The article content or None if not found
        """
        # Try common content selectors
        content_selectors = [
            'article p::text',
            '.article-content p::text',
            '.article-body p::text',
            '.content p::text',
            '.entry-content p::text',
            'div[itemprop="articleBody"] p::text',
            '.story-body p::text',
        ]
        
        for selector in content_selectors:
            paragraphs = response.css(selector).getall()
            if paragraphs:
                content = ' '.join(p.strip() for p in paragraphs if p.strip())
                if len(content) > 100:  # Ensure we have substantial content
                    return content
        
        # Try XPath selectors
        content_xpaths = [
            '//article//p/text()',
            '//div[@class="article-content"]//p/text()',
            '//div[@class="article-body"]//p/text()',
        ]
        
        for xpath in content_xpaths:
            paragraphs = response.xpath(xpath).getall()
            if paragraphs:
                content = ' '.join(p.strip() for p in paragraphs if p.strip())
                if len(content) > 100:
                    return content
        
        self.logger.warning(f"Could not extract content from {response.url}")
        return None
    
    def extract_publication_date(self, response: Response) -> Optional[datetime]:
        """
        Extract publication date from the response.
        
        Args:
            response: The response object
            
        Returns:
            datetime: The publication date or None if not found
        """
        # Try meta tags first
        date_selectors = [
            'meta[property="article:published_time"]::attr(content)',
            'meta[name="publishdate"]::attr(content)',
            'meta[name="publication_date"]::attr(content)',
            'meta[itemprop="datePublished"]::attr(content)',
            'time[itemprop="datePublished"]::attr(datetime)',
            'time[pubdate]::attr(datetime)',
        ]
        
        for selector in date_selectors:
            date_str = response.css(selector).get()
            if date_str:
                try:
                    # Try to parse ISO format
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    self.logger.debug(f"Could not parse date: {date_str}")
        
        return None
    
    def extract_author(self, response: Response) -> Optional[str]:
        """
        Extract author name from the response.
        
        Args:
            response: The response object
            
        Returns:
            str: The author name or None if not found
        """
        # Try common author selectors
        author_selectors = [
            'meta[name="author"]::attr(content)',
            'meta[property="article:author"]::attr(content)',
            '[itemprop="author"]::text',
            '.author-name::text',
            '.by-author::text',
            '.article-author::text',
            'span[class*="author"]::text',
        ]
        
        for selector in author_selectors:
            author = response.css(selector).get()
            if author:
                return author.strip()
        
        # Try XPath selectors
        author_xpaths = [
            '//span[@class="author"]/text()',
            '//div[@class="author"]/text()',
            '//p[@class="author"]/text()',
        ]
        
        for xpath in author_xpaths:
            authors = response.xpath(xpath).getall()
            if authors:
                return ', '.join(a.strip() for a in authors if a.strip())
        
        return None
    
    def extract_article_metadata(self, response: Response) -> Dict[str, Any]:
        """
        Extract additional metadata from the response.
        
        Args:
            response: The response object
            
        Returns:
            dict: Additional metadata
        """
        metadata = {}
        
        # Extract description
        description = response.css('meta[name="description"]::attr(content)').get() or \
                     response.css('meta[property="og:description"]::attr(content)').get()
        if description:
            metadata['description'] = description.strip()
        
        # Extract keywords/tags
        keywords = response.css('meta[name="keywords"]::attr(content)').get()
        if keywords:
            metadata['keywords'] = [k.strip() for k in keywords.split(',')]
        
        # Extract image
        image = response.css('meta[property="og:image"]::attr(content)').get()
        if image:
            metadata['image'] = response.urljoin(image)
        
        # Extract language
        lang = response.css('html::attr(lang)').get()
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
