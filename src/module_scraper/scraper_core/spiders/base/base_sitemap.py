"""
Base Sitemap Spider for La Máquina de Noticias

This module provides the BaseSitemapSpider class, which extends Scrapy's SitemapSpider
with common functionality for extracting articles from news websites using sitemaps.
"""

import logging
import random
from typing import Iterator, Dict, Any, Optional, List
from datetime import datetime, timedelta

import scrapy
from scrapy.spiders import SitemapSpider
from scrapy.http import Request, Response

from .base_article import BaseArticleSpider


class BaseSitemapSpider(BaseArticleSpider, SitemapSpider):
    """
    Base spider class for sitemap-based article extraction.
    
    This class extends both BaseArticleSpider and Scrapy's SitemapSpider to provide:
    - Sitemap parsing and filtering
    - Article extraction from sitemap URLs
    - Date-based filtering
    - Respect for robots.txt and crawl delays
    """
    
    # Override custom settings to add sitemap-specific configurations
    custom_settings = {
        **BaseArticleSpider.custom_settings,
        'DOWNLOAD_DELAY': 2,  # Be more polite with sitemaps
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # Sequential requests for sitemaps
    }
    
    # Default sitemap filtering settings
    sitemap_follow = ['/sitemap']  # Follow sitemaps containing this string
    sitemap_alternate_links = False  # Don't follow alternate language links by default
    
    def __init__(self, *args, **kwargs):
        """Initialize the spider with sitemap-specific settings."""
        # Extract custom parameters
        self.days_back = int(kwargs.pop('days_back', 7))  # How many days back to crawl
        self.min_date = datetime.now() - timedelta(days=self.days_back)
        
        super().__init__(*args, **kwargs)
        
        self.logger.info(f"Sitemap spider initialized - crawling articles from last {self.days_back} days")
    
    def start_requests(self) -> Iterator[Request]:
        """
        Generate requests for sitemap URLs.
        
        First checks robots.txt for sitemap locations, then falls back to
        configured sitemap_urls.
        
        Yields:
            Request: Requests for sitemap URLs
        """
        # Check if we should look for sitemaps in robots.txt
        if any(url.endswith('/robots.txt') for url in self.sitemap_urls):
            for url in self.sitemap_urls:
                if url.endswith('/robots.txt'):
                    yield self.make_request(
                        url,
                        callback=self._parse_robots,
                        priority=1
                    )
                else:
                    yield self.make_request(
                        url,
                        callback=self._parse_sitemap,
                        priority=0
                    )
        else:
            # Direct sitemap URLs
            for url in self.sitemap_urls:
                yield self.make_request(
                    url,
                    callback=self._parse_sitemap,
                    priority=0
                )
    
    def sitemap_filter(self, entries: Iterator[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
        """
        Filter sitemap entries based on date and other criteria.
        
        Args:
            entries: Iterator of sitemap entries
            
        Yields:
            dict: Filtered sitemap entries
        """
        for entry in entries:
            # Check if entry has lastmod date
            if 'lastmod' in entry:
                try:
                    # Parse the date
                    lastmod = datetime.fromisoformat(entry['lastmod'].replace('Z', '+00:00'))
                    
                    # Filter by date
                    if lastmod >= self.min_date:
                        self.logger.debug(f"Including URL from {lastmod}: {entry['loc']}")
                        yield entry
                    else:
                        self.logger.debug(f"Skipping old URL from {lastmod}: {entry['loc']}")
                except (ValueError, AttributeError) as e:
                    self.logger.warning(f"Could not parse lastmod date: {entry.get('lastmod')} - {e}")
                    # Include entry if we can't parse the date
                    yield entry
            else:
                # No date information, include by default
                self.logger.debug(f"No lastmod for URL, including: {entry['loc']}")
                yield entry
    
    def parse(self, response: Response) -> Iterator[Dict[str, Any]]:
        """
        Parse article page from sitemap.
        
        This method can be overridden by subclasses for custom parsing.
        
        Args:
            response: The response object
            
        Yields:
            dict: Extracted article data
        """
        self.logger.info(f"Parsing article: {response.url}")
        
        # Extract basic article data using parent class methods
        article_data = {
            'url': response.url,
            'title': self.extract_article_title(response),
            'content': self.extract_article_content(response),
            'author': self.extract_author(response),
            'publication_date': self.extract_publication_date(response),
            'source': self.name,
            'scraped_at': datetime.now().isoformat(),
        }
        
        # Add metadata
        metadata = self.extract_article_metadata(response)
        article_data.update(metadata)
        
        # Get lastmod from sitemap if available
        if hasattr(response, 'meta') and 'sitemap' in response.meta:
            sitemap_data = response.meta['sitemap']
            if 'lastmod' in sitemap_data:
                article_data['sitemap_lastmod'] = sitemap_data['lastmod']
        
        # Validate and yield
        if self.validate_article_data(article_data):
            self.successful_urls.append(response.url)
            yield article_data
        else:
            self.logger.warning(f"Invalid article data for {response.url}")
    
    def _parse_robots(self, response: Response) -> Iterator[Request]:
        """
        Parse robots.txt to find sitemap URLs.
        
        Args:
            response: The robots.txt response
            
        Yields:
            Request: Requests for found sitemaps
        """
        self.logger.info(f"Parsing robots.txt: {response.url}")
        
        # Extract sitemap URLs from robots.txt
        for line in response.text.splitlines():
            line = line.strip()
            if line.lower().startswith('sitemap:'):
                sitemap_url = line.split(':', 1)[1].strip()
                
                # Check if we should follow this sitemap
                should_follow = True
                if self.sitemap_follow:
                    should_follow = any(
                        pattern in sitemap_url 
                        for pattern in self.sitemap_follow
                    )
                
                if should_follow:
                    self.logger.info(f"Found sitemap in robots.txt: {sitemap_url}")
                    yield self.make_request(
                        sitemap_url,
                        callback=self._parse_sitemap,
                        priority=0
                    )
                else:
                    self.logger.debug(f"Skipping sitemap (not in follow list): {sitemap_url}")
    
    def _get_sitemap_body(self, response: Response) -> bytes:
        """
        Get sitemap body, handling compression if needed.
        
        Args:
            response: The sitemap response
            
        Returns:
            bytes: The sitemap body
        """
        # This is handled by Scrapy's built-in middleware
        return response.body
    
    def _check_sitemap_type(self, response: Response) -> str:
        """
        Determine the type of sitemap (index or urlset).
        
        Args:
            response: The sitemap response
            
        Returns:
            str: 'index' for sitemap index, 'urlset' for URL sitemap
        """
        if b'<sitemapindex' in response.body:
            return 'index'
        elif b'<urlset' in response.body:
            return 'urlset'
        else:
            self.logger.warning(f"Unknown sitemap type for {response.url}")
            return 'unknown'
    
    def parse_sitemap(self, response: Response) -> Iterator[Request]:
        """
        Parse a sitemap file.
        
        This method is called by Scrapy's SitemapSpider and should not be
        overridden unless you need custom sitemap parsing logic.
        
        Args:
            response: The sitemap response
            
        Yields:
            Request: Requests for URLs in the sitemap
        """
        # Let parent class handle the parsing
        yield from super().parse_sitemap(response)
    
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
        
        return spider
