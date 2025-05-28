"""
Example spiders demonstrating how to use the base spider classes

These examples show how to create custom spiders for specific news sites
by inheriting from the base classes.
"""

from scraper_core.spiders.base import BaseArticleSpider, BaseSitemapSpider, BaseCrawlSpider
from scrapy.http import Response


class ExampleArticleSpider(BaseArticleSpider):
    """
    Example spider that scrapes specific article URLs.
    
    This spider directly visits article URLs and extracts content.
    """
    
    name = 'example_article'
    allowed_domains = ['example.com']
    start_urls = [
        'https://example.com/2024/01/15/important-news-story',
        'https://example.com/2024/01/14/another-story',
    ]
    
    def parse(self, response: Response):
        """Parse an article page."""
        # Use base class methods for extraction
        article_data = {
            'url': response.url,
            'title': self.extract_article_title(response),
            'content': self.extract_article_content(response),
            'author': self.extract_author(response),
            'publication_date': self.extract_publication_date(response),
            'source': self.name,
        }
        
        # Add custom fields specific to this site
        article_data['section'] = response.css('.article-section::text').get()
        article_data['tags'] = response.css('.article-tags a::text').getall()
        
        # Validate and yield
        if self.validate_article_data(article_data):
            yield article_data


class ExampleSitemapSpider(BaseSitemapSpider):
    """
    Example spider that discovers articles through sitemaps.
    
    This spider reads the site's sitemap and extracts articles from the last 7 days.
    """
    
    name = 'example_sitemap'
    allowed_domains = ['news.example.com']
    sitemap_urls = ['https://news.example.com/sitemap.xml']
    
    # Optional: customize sitemap rules for different URL patterns
    sitemap_rules = [
        ('/politics/', 'parse_politics_article'),
        ('/technology/', 'parse_tech_article'),
        ('/', 'parse'),  # Default parser for other articles
    ]
    
    def parse_politics_article(self, response: Response):
        """Parse politics articles with specific logic."""
        article_data = {
            'url': response.url,
            'title': self.extract_article_title(response),
            'content': self.extract_article_content(response),
            'author': self.extract_author(response),
            'publication_date': self.extract_publication_date(response),
            'source': self.name,
            'category': 'politics',
        }
        
        # Extract politics-specific metadata
        article_data['political_parties'] = response.css('.political-party-tag::text').getall()
        
        if self.validate_article_data(article_data):
            yield article_data
    
    def parse_tech_article(self, response: Response):
        """Parse technology articles with specific logic."""
        article_data = {
            'url': response.url,
            'title': self.extract_article_title(response),
            'content': self.extract_article_content(response),
            'author': self.extract_author(response),
            'publication_date': self.extract_publication_date(response),
            'source': self.name,
            'category': 'technology',
        }
        
        # Extract tech-specific metadata
        article_data['technologies'] = response.css('.tech-tag::text').getall()
        article_data['companies'] = response.css('.company-mention::text').getall()
        
        if self.validate_article_data(article_data):
            yield article_data


class ExampleCrawlSpider(BaseCrawlSpider):
    """
    Example spider that crawls a news site following links.
    
    This spider starts from the homepage and follows links to discover articles.
    """
    
    name = 'example_crawl'
    allowed_domains = ['newssite.example.com']
    start_urls = ['https://newssite.example.com/']
    
    # Custom settings for this spider
    custom_settings = {
        **BaseCrawlSpider.custom_settings,
        'DEPTH_LIMIT': 2,  # Only go 2 levels deep
        'CLOSESPIDER_PAGECOUNT': 50,  # Stop after 50 pages
    }
    
    # Custom article patterns for this site
    article_url_patterns = [
        r'/story-\d+\.html',
        r'/\d{4}/\d{2}/[\w-]+$',
    ]
    
    def parse_article(self, response: Response):
        """Parse an article discovered through crawling."""
        # Check if this is a premium article
        if response.css('.premium-content').get():
            self.logger.info(f"Skipping premium article: {response.url}")
            return
        
        article_data = {
            'url': response.url,
            'title': self.extract_article_title(response),
            'content': self.extract_article_content(response),
            'author': self.extract_author(response),
            'publication_date': self.extract_publication_date(response),
            'source': self.name,
        }
        
        # Add crawl-specific metadata
        article_data['crawl_depth'] = response.meta.get('depth', 0)
        article_data['discovered_from'] = response.request.headers.get('Referer', b'').decode('utf-8')
        
        # Extract comments count
        comments_text = response.css('.comments-count::text').get()
        if comments_text:
            import re
            match = re.search(r'\d+', comments_text)
            if match:
                article_data['comments_count'] = int(match.group())
        
        if self.validate_article_data(article_data):
            yield article_data


class AdvancedExampleSpider(BaseCrawlSpider):
    """
    Advanced example showing how to combine multiple approaches.
    
    This spider uses crawling but also checks for sitemaps and RSS feeds.
    """
    
    name = 'example_advanced'
    allowed_domains = ['advanced-news.example.com']
    start_urls = [
        'https://advanced-news.example.com/',
        'https://advanced-news.example.com/rss',
        'https://advanced-news.example.com/sitemap.xml',
    ]
    
    custom_settings = {
        **BaseCrawlSpider.custom_settings,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 4,  # Can handle more load
        'DOWNLOAD_DELAY': 0.5,  # Faster crawling
        'AUTOTHROTTLE_ENABLED': True,  # Enable AutoThrottle
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 4.0,
    }
    
    def parse_start_url(self, response: Response):
        """Handle different types of start URLs."""
        if 'sitemap.xml' in response.url:
            # Parse as sitemap
            yield from self._parse_sitemap(response)
        elif '/rss' in response.url:
            # Parse as RSS feed
            yield from self._parse_rss(response)
        else:
            # Regular crawling
            yield from super().parse_start_url(response)
    
    def _parse_sitemap(self, response: Response):
        """Parse sitemap XML."""
        response.selector.remove_namespaces()
        for url in response.xpath('//url/loc/text()').getall():
            yield self.make_request(url, callback=self.parse_article)
    
    def _parse_rss(self, response: Response):
        """Parse RSS feed."""
        response.selector.remove_namespaces()
        for item in response.xpath('//item'):
            url = item.xpath('link/text()').get()
            if url:
                yield self.make_request(url, callback=self.parse_article)
    
    def parse_article(self, response: Response):
        """Enhanced article parsing with fallback strategies."""
        # Try JSON-LD structured data first
        json_ld = response.xpath('//script[@type="application/ld+json"]/text()').get()
        if json_ld:
            try:
                import json
                data = json.loads(json_ld)
                if data.get('@type') == 'NewsArticle':
                    yield self._extract_from_json_ld(data, response)
                    return
            except:
                pass
        
        # Fall back to standard extraction
        yield from super().parse_article(response)
    
    def _extract_from_json_ld(self, data: dict, response: Response) -> dict:
        """Extract article data from JSON-LD structured data."""
        article_data = {
            'url': response.url,
            'title': data.get('headline'),
            'content': data.get('articleBody'),
            'author': data.get('author', {}).get('name'),
            'publication_date': data.get('datePublished'),
            'source': self.name,
            'description': data.get('description'),
        }
        
        # Add image if available
        if 'image' in data:
            if isinstance(data['image'], dict):
                article_data['image'] = data['image'].get('url')
            else:
                article_data['image'] = data['image']
        
        return article_data


# Command line usage examples:
# scrapy crawl example_article
# scrapy crawl example_sitemap -a days_back=14
# scrapy crawl example_crawl -a max_pages=100
# scrapy crawl example_advanced -a follow_links=true
