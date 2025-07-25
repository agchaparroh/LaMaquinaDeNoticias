"""
Base spider classes for La Máquina de Noticias

This package contains the base spider classes that provide common functionality
for all article scraping spiders in the project.
"""

from .base_article import BaseArticleSpider
from .base_crawl import BaseCrawlSpider
from .base_sitemap import BaseSitemapSpider

__all__ = ["BaseArticleSpider", "BaseSitemapSpider", "BaseCrawlSpider"]
