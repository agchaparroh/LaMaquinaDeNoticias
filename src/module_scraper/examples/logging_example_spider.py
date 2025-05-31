"""
Example spider demonstrating the logging system usage.
This spider showcases all logging features for reference.
"""

import time
from datetime import datetime

import scrapy
from scrapy.http import Response

from scraper_core.spiders.base import BaseArticleSpider
from scraper_core.utils.logging_utils import (
    log_execution_time, log_exceptions, StructuredLogger,
    sanitize_log_data, log_response_stats
)
from scraper_core.items import ArticuloInItem
from scraper_core.itemloaders import ArticuloInItemLoader


class LoggingExampleSpider(BaseArticleSpider):
    """
    Spider de ejemplo que demuestra el uso del sistema de logging.
    
    Este spider no hace scraping real, solo demuestra las capacidades de logging.
    """
    
    name = 'logging_example'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com/articles']
    
    # Custom settings for demonstration
    custom_settings = {
        'LOG_LEVEL': 'DEBUG',  # Maximum verbosity for demo
        'LOG_TO_FILE': 'true',  # Force file logging
        'CLOSESPIDER_PAGECOUNT': 5,  # Limit pages for demo
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize structured logger for JSON logging
        self.structured_logger = StructuredLogger(f"{self.name}.structured")
        
        # Log spider initialization
        self.logger.info(f"Spider {self.name} initialized with settings: {self.custom_settings}")
        
        # Log structured event
        self.structured_logger.info('spider_initialized',
                                  spider_name=self.name,
                                  start_urls=self.start_urls,
                                  timestamp=datetime.now().isoformat())
    
    def start_requests(self):
        """Generate initial requests with detailed logging."""
        self.logger.debug("Starting request generation")
        
        for i, url in enumerate(self.start_urls):
            # Log each request creation
            self.logger.debug(f"Creating request #{i+1} for URL: {url}")
            
            # Create request with metadata
            request = self.make_request(
                url,
                callback=self.parse_article_list,
                meta={'request_number': i+1, 'request_time': time.time()}
            )
            
            # Log structured request info
            self.structured_logger.info('request_created',
                                      url=url,
                                      request_number=i+1,
                                      headers=dict(request.headers))
            
            yield request
    
    @log_execution_time
    @log_exceptions(include_traceback=True)
    def parse_article_list(self, response: Response):
        """
        Parse article list with comprehensive logging.
        
        Demonstrates:
        - Response statistics logging
        - Execution time tracking
        - Exception handling
        - Different log levels
        """
        # Log response statistics
        self.logger.info(f"Received response from {response.url}")
        log_response_stats(response, self.logger)
        
        # Log request timing
        request_time = response.meta.get('request_time')
        if request_time:
            duration = time.time() - request_time
            self.logger.debug(f"Request took {duration:.2f} seconds")
        
        # Extract article URLs (mock data for demo)
        article_urls = [
            'https://example.com/article/1',
            'https://example.com/article/2',
            'https://example.com/article/3',
        ]
        
        # Log extraction results
        self.logger.info(f"Found {len(article_urls)} articles on {response.url}")
        
        # Demonstrate different log levels
        for i, url in enumerate(article_urls):
            # DEBUG: Detailed information
            self.logger.debug(f"Processing article URL #{i+1}: {url}")
            
            # Create article request
            yield self.make_request(
                url,
                callback=self.parse_article,
                meta={
                    'article_number': i+1,
                    'list_page': response.url,
                    'extraction_time': datetime.now().isoformat()
                }
            )
        
        # Demonstrate warning
        if len(article_urls) < 5:
            self.logger.warning(
                f"Low article count ({len(article_urls)}) on {response.url}. "
                "Page structure might have changed."
            )
        
        # Log structured event
        self.structured_logger.info('article_list_parsed',
                                  page_url=response.url,
                                  article_count=len(article_urls),
                                  response_status=response.status)
    
    @log_exceptions(log_level=logging.ERROR)
    def parse_article(self, response: Response):
        """
        Parse individual article with error handling and data sanitization.
        
        Demonstrates:
        - Item processing logging
        - Data sanitization
        - Error scenarios
        - Structured logging
        """
        article_number = response.meta.get('article_number', 0)
        
        self.logger.info(f"Parsing article #{article_number} from {response.url}")
        
        # Create item loader
        loader = ArticuloInItemLoader(item=ArticuloInItem(), response=response)
        
        # Basic fields
        loader.add_value('url', response.url)
        loader.add_value('fuente', self.name)
        
        # Simulate extraction with potential issues
        loader.add_xpath('titular', '//h1/text()')
        loader.add_xpath('contenido_html', '//article')
        
        # Load item
        item = loader.load_item()
        
        # Demonstrate data sanitization before logging
        item_dict = dict(item)
        
        # Add some fake sensitive data for demonstration
        item_dict['api_response'] = {
            'status': 'success',
            'api_key': 'secret123',  # This should be redacted
            'content_id': '12345'
        }
        
        # Sanitize before logging
        safe_item = sanitize_log_data(item_dict)
        self.logger.debug(f"Extracted item (sanitized): {safe_item}")
        
        # Simulate different scenarios
        if article_number == 2:
            # Demonstrate error logging
            self.logger.error(
                f"Critical field missing for article {response.url}",
                extra={'article_data': safe_item}
            )
            # Don't return item to simulate drop
            return
        
        if article_number == 3:
            # Demonstrate critical error
            self.logger.critical(
                "Unexpected page structure detected! Manual review required.",
                extra={'url': response.url, 'selector_results': loader.get_collected_values('titular')}
            )
        
        # Log successful extraction
        self.structured_logger.info('article_extracted',
                                  url=response.url,
                                  article_number=article_number,
                                  has_title=bool(item.get('titular')),
                                  has_content=bool(item.get('contenido_html')),
                                  extraction_timestamp=response.meta.get('extraction_time'))
        
        # Track success
        self.successful_urls.append(response.url)
        
        return item
    
    def closed(self, reason):
        """
        Spider closed callback with summary logging.
        
        Demonstrates:
        - Summary statistics
        - Performance metrics
        - Structured logging for analytics
        """
        # Call parent method
        super().spider_closed(self)
        
        # Additional summary logging
        total_urls = len(self.successful_urls) + len(self.failed_urls)
        success_rate = (len(self.successful_urls) / total_urls * 100) if total_urls > 0 else 0
        
        # Log summary
        self.logger.info("="*50)
        self.logger.info("SPIDER EXECUTION SUMMARY")
        self.logger.info("="*50)
        self.logger.info(f"Spider: {self.name}")
        self.logger.info(f"Reason: {reason}")
        self.logger.info(f"Total URLs processed: {total_urls}")
        self.logger.info(f"Successful: {len(self.successful_urls)}")
        self.logger.info(f"Failed: {len(self.failed_urls)}")
        self.logger.info(f"Success rate: {success_rate:.1f}%")
        self.logger.info("="*50)
        
        # Log structured summary for analytics
        self.structured_logger.info('spider_closed',
                                  spider_name=self.name,
                                  close_reason=reason,
                                  total_urls=total_urls,
                                  successful_urls=len(self.successful_urls),
                                  failed_urls=len(self.failed_urls),
                                  success_rate=success_rate,
                                  execution_time_seconds=time.time() - self.start_time if hasattr(self, 'start_time') else None)
    
    def handle_error(self, failure):
        """
        Enhanced error handling with detailed logging.
        
        Demonstrates:
        - Error categorization
        - Failure analysis
        - Retry logging
        """
        # Call parent error handler
        super().handle_error(failure)
        
        # Additional error analysis
        request = failure.request
        
        # Categorize error
        if failure.check(scrapy.exceptions.IgnoreRequest):
            error_type = 'ignored'
            log_level = logging.INFO
        elif failure.check(scrapy.exceptions.NotSupported):
            error_type = 'not_supported'
            log_level = logging.WARNING
        else:
            error_type = 'general_failure'
            log_level = logging.ERROR
        
        # Log structured error
        self.structured_logger.error('request_failed',
                                   url=request.url,
                                   error_type=error_type,
                                   error_class=failure.type.__name__,
                                   error_message=str(failure.value),
                                   retry_times=request.meta.get('retry_times', 0))
        
        # Log with appropriate level
        self.logger.log(
            log_level,
            f"Request failed ({error_type}): {request.url} - {failure.value}"
        )


# Example of a custom pipeline with logging
class LoggingExamplePipeline:
    """
    Pipeline de ejemplo que demuestra logging en pipelines.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.structured_logger = StructuredLogger(__name__)
        self.processed_count = 0
    
    @log_execution_time
    @log_item_processing
    def process_item(self, item, spider):
        """
        Process item with comprehensive logging.
        """
        self.processed_count += 1
        
        # Log item processing
        self.logger.debug(f"Processing item #{self.processed_count} from {spider.name}")
        
        # Simulate processing with timing
        start_time = time.time()
        
        # Mock processing steps
        if item.get('titulo'):
            item['titulo'] = item['titulo'].strip()
            self.logger.debug("Title cleaned")
        
        if item.get('contenido_html'):
            # Simulate content processing
            time.sleep(0.1)  # Simulate processing time
            self.logger.debug("Content processed")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log structured metrics
        self.structured_logger.info('item_processed',
                                  spider=spider.name,
                                  item_url=item.get('url'),
                                  processing_time_ms=processing_time * 1000,
                                  item_number=self.processed_count,
                                  has_content=bool(item.get('contenido_html')))
        
        # Log performance warning if slow
        if processing_time > 0.5:
            self.logger.warning(
                f"Slow item processing: {processing_time:.2f}s for {item.get('url')}"
            )
        
        return item
