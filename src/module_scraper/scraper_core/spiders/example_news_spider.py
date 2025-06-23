# -*- coding: utf-8 -*-
"""
Example News Spider - La Máquina de Noticias

This is an example spider that demonstrates proper implementation
following all project standards and requirements.
"""
import logging
from typing import Iterator, Dict, Any, Optional
from datetime import datetime

from scrapy.http import Response

from scraper_core.items import ArticuloInItem
from scraper_core.spiders.base.base_article import BaseArticleSpider

logger = logging.getLogger(__name__)


class ExampleNewsSpider(BaseArticleSpider):
    """
    Example spider that demonstrates proper implementation.
    This spider is configured but doesn't actually scrape any site.
    """
    name = 'example_news'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com/news']
    
    # Required attributes for La Máquina de Noticias
    medio_nombre = 'Example News'
    pais = 'Argentina'
    tipo_medio = 'diario'
    target_section = 'general'
    
    # Custom settings extending from BaseArticleSpider
    custom_settings = {
        **BaseArticleSpider.custom_settings,
        'DOWNLOAD_DELAY': 3.0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CLOSESPIDER_ITEMCOUNT': 30,  # RSS-like behavior
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.RFPDupeFilter',
        'ROBOTSTXT_OBEY': True,
    }
    
    def parse(self, response: Response) -> Iterator[Dict[str, Any]]:
        """
        Parse the main page and extract article links.
        """
        self.logger.info(f"Parsing {response.url}")
        
        # Example: Extract article links
        article_links = response.css('article a::attr(href)').getall()
        
        for link in article_links[:self.custom_settings['CLOSESPIDER_ITEMCOUNT']]:
            yield response.follow(link, callback=self.parse_article)
    
    def parse_article(self, response: Response) -> Optional[ArticuloInItem]:
        """
        Parse individual article page.
        """
        self.logger.debug(f"Parsing article: {response.url}")
        
        # Check if this is a valid article for our section
        if not self._is_section_article(response):
            self.logger.debug(f"Article {response.url} not in target section")
            return None
        
        # Create item loader
        loader = self.create_loader(response)
        
        # Extract basic fields
        loader.add_css('titular', 'h1::text')
        loader.add_css('descripcion', 'meta[name="description"]::attr(content)')
        loader.add_value('url', response.url)
        loader.add_value('fecha_publicacion', datetime.now().isoformat())
        
        # Extract content
        loader.add_css('contenido', 'div.article-content p::text')
        
        # Add metadata
        loader.add_value('medio_nombre', self.medio_nombre)
        loader.add_value('pais', self.pais)
        loader.add_value('tipo_medio', self.tipo_medio)
        loader.add_value('seccion', self.target_section)
        
        # Load and validate item
        item = loader.load_item()
        
        if self._validate_article(item):
            return item
        else:
            self.logger.warning(f"Invalid article at {response.url}")
            return None
    
    def _is_section_article(self, response: Response) -> bool:
        """
        Check if the article belongs to the target section.
        """
        # Example implementation
        url = response.url.lower()
        return self.target_section in url or '/news/' in url
    
    def _validate_article(self, item: ArticuloInItem) -> bool:
        """
        Validate that the article has required fields.
        """
        required_fields = ['titular', 'url', 'contenido']
        
        for field in required_fields:
            if not item.get(field):
                self.logger.warning(f"Missing required field: {field}")
                return False
        
        # Additional validation
        if len(item.get('contenido', '')) < 100:
            self.logger.warning("Article content too short")
            return False
        
        return True