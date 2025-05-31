"""
Rate limiting and politeness monitoring middleware.

This middleware provides enhanced logging and monitoring for rate limiting,
AutoThrottle, and robots.txt compliance.
"""

import time
import logging
from typing import Optional, Union
from urllib.parse import urlparse

from scrapy import Spider, Request
from scrapy.http import Response
from scrapy.exceptions import IgnoreRequest
from scrapy.downloadermiddlewares.robotstxt import RobotsTxtMiddleware

logger = logging.getLogger(__name__)


class RateLimitMonitorMiddleware:
    """
    Middleware to monitor and log rate limiting behavior.
    
    This middleware tracks:
    - Download delays applied per domain
    - AutoThrottle adjustments
    - Robots.txt compliance
    - Request timing statistics
    """
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.stats = crawler.stats
        self.domain_last_request = {}
        self.domain_request_count = {}
        
        # Get settings
        self.autothrottle_enabled = crawler.settings.getbool('AUTOTHROTTLE_ENABLED')
        self.robotstxt_obey = crawler.settings.getbool('ROBOTSTXT_OBEY')
        self.download_slots = crawler.settings.getdict('DOWNLOAD_SLOTS', {})
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)
    
    def process_request(self, request: Request, spider: Spider) -> Optional[Request]:
        """Process request and log rate limiting information."""
        domain = urlparse(request.url).netloc
        current_time = time.time()
        
        # Track request count per domain
        self.domain_request_count[domain] = self.domain_request_count.get(domain, 0) + 1
        self.stats.set_value(f'rate_limit/requests/{domain}', self.domain_request_count[domain])
        
        # Calculate time since last request to this domain
        if domain in self.domain_last_request:
            time_since_last = current_time - self.domain_last_request[domain]
            self.stats.set_value(f'rate_limit/delay/{domain}', time_since_last)
            
            # Log if delay seems too short
            expected_delay = self._get_expected_delay(domain)
            if time_since_last < expected_delay * 0.9:  # 10% tolerance
                logger.warning(
                    f"Request to {domain} may be too fast. "
                    f"Expected delay: {expected_delay:.2f}s, Actual: {time_since_last:.2f}s"
                )
        
        # Store timestamp for next calculation
        self.domain_last_request[domain] = current_time
        
        # Add metadata to track this request
        request.meta['rate_limit_start_time'] = current_time
        request.meta['rate_limit_domain'] = domain
        
        return None
    
    def process_response(self, request: Request, response: Response, spider: Spider) -> Response:
        """Process response and update statistics."""
        domain = request.meta.get('rate_limit_domain')
        start_time = request.meta.get('rate_limit_start_time')
        
        if domain and start_time:
            download_time = time.time() - start_time
            self.stats.set_value(f'rate_limit/download_time/{domain}', download_time)
            
            # Log slow responses
            if download_time > 10:  # More than 10 seconds
                logger.warning(
                    f"Slow response from {domain}: {download_time:.2f}s for {request.url}"
                )
        
        # Check if AutoThrottle adjusted the delay
        if self.autothrottle_enabled and hasattr(spider, 'download_delay'):
            current_delay = spider.download_delay
            self.stats.set_value('autothrottle/current_delay', current_delay)
            
        return response
    
    def process_exception(self, request: Request, exception: Exception, spider: Spider) -> Optional[Union[Response, Request]]:
        """Handle exceptions and track failures."""
        domain = request.meta.get('rate_limit_domain')
        
        if domain:
            failure_count = self.stats.get_value(f'rate_limit/failures/{domain}', 0)
            self.stats.set_value(f'rate_limit/failures/{domain}', failure_count + 1)
            
            # Log if we're seeing many failures from a domain
            if failure_count > 5:
                logger.error(
                    f"Multiple failures from {domain} ({failure_count} total). "
                    f"Consider adjusting rate limits."
                )
        
        return None
    
    def _get_expected_delay(self, domain: str) -> float:
        """Get the expected delay for a domain."""
        if domain in self.download_slots:
            return self.download_slots[domain].get('delay', 0)
        return self.crawler.settings.getfloat('DOWNLOAD_DELAY', 0)


class EnhancedRobotsTxtMiddleware(RobotsTxtMiddleware):
    """
    Enhanced RobotsTxtMiddleware with additional logging and monitoring.
    """
    
    def __init__(self, crawler):
        super().__init__(crawler)
        self.stats = crawler.stats
        self.blocked_count = {}
    
    def robot_parser(self, request, spider):
        """Override to add logging when robots.txt is fetched."""
        parser = super().robot_parser(request, spider)
        domain = urlparse(request.url).netloc
        
        if parser:
            logger.info(f"Fetched and parsed robots.txt for {domain}")
            self.stats.set_value(f'robots_txt/fetched/{domain}', 1)
        
        return parser
    
    def process_request(self, request, spider):
        """Process request and log if blocked by robots.txt."""
        result = super().process_request(request, spider)
        
        if isinstance(result, IgnoreRequest):
            domain = urlparse(request.url).netloc
            self.blocked_count[domain] = self.blocked_count.get(domain, 0) + 1
            
            logger.warning(
                f"Request blocked by robots.txt: {request.url} "
                f"(Total blocked for {domain}: {self.blocked_count[domain]})"
            )
            
            self.stats.set_value(f'robots_txt/blocked/{domain}', self.blocked_count[domain])
            self.stats.inc_value('robots_txt/blocked_total')
        
        return result
