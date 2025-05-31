"""
Logging utilities for the scraper project.
Provides helper functions and decorators for consistent logging across components.
"""

import logging
import functools
import time
import traceback
from typing import Any, Callable, Optional, Dict
import json


class LoggerMixin:
    """
    Mixin class that provides a logger instance to any class.
    
    Usage:
        class MySpider(scrapy.Spider, LoggerMixin):
            def parse(self, response):
                self.logger.info("Parsing response from %s", response.url)
    """
    
    @property
    def logger(self):
        """Get logger instance for this class."""
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)
        return self._logger


def log_execution_time(func: Callable) -> Callable:
    """
    Decorator that logs the execution time of a function.
    
    Usage:
        @log_execution_time
        def process_item(self, item, spider):
            # processing logic
            return item
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__ + '.' + func.__qualname__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > 1.0:  # Log if execution takes more than 1 second
                logger.warning(
                    "%s took %.2f seconds to execute",
                    func.__qualname__, execution_time
                )
            else:
                logger.debug(
                    "%s executed in %.3f seconds",
                    func.__qualname__, execution_time
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "%s failed after %.2f seconds: %s",
                func.__qualname__, execution_time, str(e)
            )
            raise
    
    return wrapper


def log_exceptions(logger_name: Optional[str] = None, 
                  log_level: int = logging.ERROR,
                  include_traceback: bool = True) -> Callable:
    """
    Decorator that logs exceptions from a function.
    
    Args:
        logger_name: Optional logger name (defaults to function module)
        log_level: Log level for exceptions (default: ERROR)
        include_traceback: Whether to include full traceback
    
    Usage:
        @log_exceptions()
        def risky_operation(self):
            # code that might raise exceptions
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name or func.__module__)
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                exc_info = traceback.format_exc() if include_traceback else None
                
                logger.log(
                    log_level,
                    "Exception in %s: %s",
                    func.__qualname__,
                    str(e),
                    exc_info=exc_info
                )
                raise
        
        return wrapper
    return decorator


def log_item_processing(func: Callable) -> Callable:
    """
    Decorator specifically for item processing in pipelines.
    Logs item details at various stages.
    
    Usage:
        @log_item_processing
        def process_item(self, item, spider):
            # processing logic
            return item
    """
    @functools.wraps(func)
    def wrapper(self, item, spider, *args, **kwargs):
        logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
        # Log item input (summary only)
        item_summary = {
            'url': item.get('url', 'N/A'),
            'titulo': item.get('titulo', 'N/A')[:50] + '...' if item.get('titulo') else 'N/A',
            'medio': item.get('medio_nombre', 'N/A')
        }
        
        logger.debug(
            "Processing item from %s: %s",
            spider.name,
            json.dumps(item_summary, ensure_ascii=False)
        )
        
        try:
            result = func(self, item, spider, *args, **kwargs)
            
            # Log successful processing
            logger.debug(
                "Successfully processed item: %s",
                item.get('url', 'Unknown URL')
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to process item %s: %s",
                item.get('url', 'Unknown URL'),
                str(e),
                exc_info=True
            )
            raise
    
    return wrapper


class StructuredLogger:
    """
    Helper class for structured logging (useful for log aggregation systems).
    
    Usage:
        logger = StructuredLogger('my_module')
        logger.info('user_action', user_id=123, action='login', ip='192.168.1.1')
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _log(self, level: int, event: str, **kwargs):
        """Internal method to log structured data."""
        # Create structured message
        data = {
            'event': event,
            **kwargs
        }
        
        # Log as JSON for structured logging systems
        message = json.dumps(data, ensure_ascii=False, default=str)
        self.logger.log(level, message)
    
    def debug(self, event: str, **kwargs):
        """Log debug level structured event."""
        self._log(logging.DEBUG, event, **kwargs)
    
    def info(self, event: str, **kwargs):
        """Log info level structured event."""
        self._log(logging.INFO, event, **kwargs)
    
    def warning(self, event: str, **kwargs):
        """Log warning level structured event."""
        self._log(logging.WARNING, event, **kwargs)
    
    def error(self, event: str, **kwargs):
        """Log error level structured event."""
        self._log(logging.ERROR, event, **kwargs)
    
    def critical(self, event: str, **kwargs):
        """Log critical level structured event."""
        self._log(logging.CRITICAL, event, **kwargs)


def sanitize_log_data(data: Dict[str, Any], 
                     sensitive_keys: Optional[list] = None) -> Dict[str, Any]:
    """
    Sanitize sensitive data before logging.
    
    Args:
        data: Dictionary to sanitize
        sensitive_keys: List of keys to mask (default: common sensitive keys)
    
    Returns:
        Sanitized dictionary safe for logging
    """
    if sensitive_keys is None:
        sensitive_keys = [
            'password', 'pwd', 'pass', 'secret', 'token', 'api_key',
            'apikey', 'auth', 'authorization', 'credential', 'private'
        ]
    
    sanitized = {}
    
    for key, value in data.items():
        # Check if key contains sensitive information
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = '***REDACTED***'
        elif isinstance(value, dict):
            # Recursively sanitize nested dictionaries
            sanitized[key] = sanitize_log_data(value, sensitive_keys)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            # Sanitize lists of dictionaries
            sanitized[key] = [sanitize_log_data(item, sensitive_keys) for item in value]
        else:
            sanitized[key] = value
    
    return sanitized


class SpiderLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that automatically includes spider context in log messages.
    
    Usage:
        class MySpider(scrapy.Spider):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.logger = SpiderLoggerAdapter(logging.getLogger(self.name), {'spider': self})
    """
    
    def process(self, msg, kwargs):
        """Add spider context to log messages."""
        spider = self.extra.get('spider')
        if spider:
            # Add spider info to the message
            spider_info = f"[{spider.name}]"
            msg = f"{spider_info} {msg}"
            
            # Add spider context to kwargs if using structured logging
            if 'extra' in kwargs:
                kwargs['extra']['spider_name'] = spider.name
            else:
                kwargs['extra'] = {'spider_name': spider.name}
        
        return msg, kwargs


# Utility functions for common logging patterns

def log_response_stats(response, logger: logging.Logger):
    """
    Log statistics about a Scrapy response.
    
    Args:
        response: Scrapy Response object
        logger: Logger instance
    """
    stats = {
        'url': response.url,
        'status': response.status,
        'size': len(response.body),
        'encoding': response.encoding,
        'headers': dict(response.headers),
    }
    
    # Sanitize headers (might contain auth tokens)
    stats['headers'] = sanitize_log_data(stats['headers'])
    
    logger.debug(
        "Response stats: %s",
        json.dumps(stats, ensure_ascii=False, default=str)
    )


def log_item_stats(item: Dict[str, Any], logger: logging.Logger):
    """
    Log statistics about a scraped item.
    
    Args:
        item: Scraped item dictionary
        logger: Logger instance
    """
    stats = {
        'url': item.get('url', 'N/A'),
        'title_length': len(item.get('titulo', '')),
        'content_length': len(item.get('contenido_texto', '')),
        'has_images': bool(item.get('imagenes')),
        'has_tags': bool(item.get('etiquetas')),
        'fields_count': len([k for k, v in item.items() if v is not None]),
    }
    
    logger.info(
        "Item statistics: %s",
        json.dumps(stats, ensure_ascii=False)
    )


# Example usage documentation
LOGGING_EXAMPLES = """
# Example 1: Using LoggerMixin in a Spider
from scraper_core.utils.logging_utils import LoggerMixin

class MySpider(scrapy.Spider, LoggerMixin):
    name = 'my_spider'
    
    def parse(self, response):
        self.logger.info("Parsing %s", response.url)
        # ... parsing logic ...


# Example 2: Using decorators in pipelines
from scraper_core.utils.logging_utils import log_execution_time, log_item_processing

class MyPipeline:
    @log_execution_time
    @log_item_processing
    def process_item(self, item, spider):
        # ... processing logic ...
        return item


# Example 3: Using structured logging
from scraper_core.utils.logging_utils import StructuredLogger

class MyMiddleware:
    def __init__(self):
        self.logger = StructuredLogger(__name__)
    
    def process_request(self, request, spider):
        self.logger.info('request_processed',
                        url=request.url,
                        method=request.method,
                        spider=spider.name)


# Example 4: Sanitizing sensitive data
from scraper_core.utils.logging_utils import sanitize_log_data

def log_api_response(response_data, logger):
    safe_data = sanitize_log_data(response_data)
    logger.debug("API response: %s", safe_data)
"""
