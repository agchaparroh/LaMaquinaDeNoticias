"""
Base spider classes for La Máquina de Noticias

This package contains the base spider classes that provide common functionality
for all article scraping spiders in the project.
"""

from .base_article import BaseArticleSpider
from .base_sitemap import BaseSitemapSpider
from .base_crawl import BaseCrawlSpider

__all__ = ['BaseArticleSpider', 'BaseSitemapSpider', 'BaseCrawlSpider']
