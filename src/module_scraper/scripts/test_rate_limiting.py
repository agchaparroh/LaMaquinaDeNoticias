"""
Test script for rate limiting and politeness policies.

This script tests:
1. AutoThrottle configuration
2. Robots.txt compliance
3. Domain-specific rate limits
4. Rate limit monitoring
"""

import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlparse

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from scrapy import Spider, Request
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class RateLimitTestSpider(Spider):
    """Spider to test rate limiting configurations."""
    
    name = 'rate_limit_test'
    
    def __init__(self, test_urls=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Default test URLs from different domains
        self.test_urls = test_urls or [
            # Sites with different rate limit configurations
            'https://www.bbc.com/news',
            'https://www.bbc.com/sport',
            'https://edition.cnn.com/',
            'https://edition.cnn.com/world',
            'https://www.reuters.com/',
            'https://www.reuters.com/technology',
            
            # Test robots.txt compliance (common disallowed paths)
            'https://www.example.com/admin/',
            'https://www.example.com/search?q=test',
        ]
        
        self.request_times = {}
        self.response_times = {}
    
    def start_requests(self):
        """Generate initial requests."""
        for url in self.test_urls:
            yield Request(
                url,
                callback=self.parse,
                errback=self.handle_error,
                meta={
                    'request_start_time': time.time(),
                    'dont_redirect': True,  # To see actual response codes
                }
            )
    
    def parse(self, response):
        """Parse response and log timing information."""
        url = response.url
        domain = urlparse(url).netloc
        request_time = response.meta.get('request_start_time', 0)
        response_time = time.time()
        
        # Calculate request timing
        if domain not in self.request_times:
            self.request_times[domain] = []
        self.request_times[domain].append(request_time)
        
        # Log response
        logger.info(
            f"Response from {domain}: "
            f"Status={response.status}, "
            f"Time={response_time - request_time:.2f}s, "
            f"URL={url}"
        )
        
        # Check if we were delayed appropriately
        if len(self.request_times[domain]) > 1:
            delay = request_time - self.request_times[domain][-2]
            logger.info(f"Delay between requests to {domain}: {delay:.2f}s")
        
        # Yield some data for pipeline testing
        yield {
            'url': url,
            'domain': domain,
            'status': response.status,
            'response_time': response_time - request_time,
            'timestamp': response_time,
        }
    
    def handle_error(self, failure):
        """Handle request failures."""
        request = failure.request
        url = request.url
        domain = urlparse(url).netloc
        
        logger.error(
            f"Request failed for {url}: {failure.value}"
        )
        
        # Check if blocked by robots.txt
        if 'Forbidden by robots.txt' in str(failure.value):
            logger.warning(f"URL blocked by robots.txt: {url}")
    
    def closed(self, reason):
        """Spider closed, print summary."""
        logger.info("=" * 70)
        logger.info("RATE LIMITING TEST SUMMARY")
        logger.info("=" * 70)
        
        # Print timing summary per domain
        for domain, times in self.request_times.items():
            if len(times) > 1:
                delays = [times[i] - times[i-1] for i in range(1, len(times))]
                avg_delay = sum(delays) / len(delays)
                logger.info(
                    f"{domain}: "
                    f"Requests={len(times)}, "
                    f"Avg delay={avg_delay:.2f}s"
                )
        
        logger.info("=" * 70)


def run_rate_limit_test():
    """Run the rate limit test spider."""
    # Get project settings
    settings = get_project_settings()
    
    # Override some settings for testing
    settings.update({
        'LOG_LEVEL': 'INFO',
        'AUTOTHROTTLE_DEBUG': True,  # Enable AutoThrottle debug logging
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 8,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        
        # Enable our monitoring middleware
        'DOWNLOADER_MIDDLEWARES': {
            **settings.get('DOWNLOADER_MIDDLEWARES', {}),
            'scraper_core.middlewares.rate_limit_monitor.RateLimitMonitorMiddleware': 543,
            'scraper_core.middlewares.rate_limit_monitor.EnhancedRobotsTxtMiddleware': 100,
            'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': None,  # Disable default
        },
        
        # Disable pipelines for this test
        'ITEM_PIPELINES': {},
        
        # Disable caching for accurate timing tests
        'HTTPCACHE_ENABLED': False,
    })
    
    # Create and configure crawler
    process = CrawlerProcess(settings)
    
    # Add our test spider
    process.crawl(RateLimitTestSpider)
    
    # Start the crawling process
    logger.info("Starting rate limit test...")
    process.start()


def test_specific_domains(domains: List[str]):
    """Test rate limiting for specific domains."""
    urls = []
    for domain in domains:
        # Add multiple URLs per domain to test rate limiting
        urls.extend([
            f"https://{domain}/",
            f"https://{domain}/news",
            f"https://{domain}/about",
        ])
    
    # Run test with specific URLs
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(RateLimitTestSpider, test_urls=urls)
    process.start()


def print_rate_limit_config():
    """Print current rate limit configuration."""
    from config.rate_limits.domain_config import DOMAIN_RATE_LIMITS
    
    logger.info("=" * 70)
    logger.info("CURRENT RATE LIMIT CONFIGURATION")
    logger.info("=" * 70)
    
    for domain, config in sorted(DOMAIN_RATE_LIMITS.items()):
        logger.info(
            f"{domain}: "
            f"delay={config.get('delay', 'N/A')}s, "
            f"concurrency={config.get('concurrency', 'N/A')}, "
            f"randomize={config.get('randomize_delay', False)}"
        )
    
    logger.info("=" * 70)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test rate limiting configuration')
    parser.add_argument(
        '--domains',
        nargs='+',
        help='Specific domains to test (e.g., bbc.com cnn.com)'
    )
    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Show current rate limit configuration'
    )
    
    args = parser.parse_args()
    
    if args.show_config:
        print_rate_limit_config()
    elif args.domains:
        test_specific_domains(args.domains)
    else:
        run_rate_limit_test()
