"""
Scrapy extension for log rotation support.
Integrates Python's rotating file handlers with Scrapy's logging system.
"""

import logging
import logging.handlers
from scrapy import signals
from scrapy.exceptions import NotConfigured
from scraper_core.log_rotation import LogRotationConfig


class LogRotationExtension:
    """
    Scrapy extension that adds log rotation support.
    
    This extension replaces Scrapy's default file handler with a rotating
    file handler to prevent log files from growing too large.
    """
    
    def __init__(self, settings):
        """Initialize the extension with Scrapy settings."""
        self.settings = settings
        self.enabled = settings.getbool('LOG_ROTATION_ENABLED', True)
        
        if not self.enabled:
            raise NotConfigured('Log rotation is disabled')
        
        # Check if file logging is enabled
        if not settings.get('LOG_FILE'):
            raise NotConfigured('LOG_FILE not set, rotation not needed')
    
    @classmethod
    def from_crawler(cls, crawler):
        """Create extension instance from crawler."""
        ext = cls(crawler.settings)
        
        # Connect to spider_opened signal
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        
        # Set up rotation immediately for the root logger
        ext.setup_rotation()
        
        return ext
    
    def setup_rotation(self):
        """Set up log rotation for Scrapy's root logger."""
        # Get the root logger
        root_logger = logging.getLogger()
        
        # Find and remove existing file handlers
        file_handlers = [h for h in root_logger.handlers 
                        if isinstance(h, logging.FileHandler) 
                        and not isinstance(h, logging.handlers.RotatingFileHandler)]
        
        for handler in file_handlers:
            root_logger.removeHandler(handler)
        
        # Create rotating handler
        rotating_handler = LogRotationConfig.create_scrapy_log_handler(self.settings)
        
        # Set the same level as the root logger
        rotating_handler.setLevel(root_logger.level)
        
        # Add the rotating handler
        root_logger.addHandler(rotating_handler)
        
        # Log that rotation is set up
        logger = logging.getLogger(__name__)
        logger.info("Log rotation enabled for Scrapy logs")
    
    def spider_opened(self, spider):
        """Handle spider opened signal."""
        # Set up spider-specific rotating logger if needed
        if self.settings.getbool('LOG_ROTATION_PER_SPIDER', False):
            self.setup_spider_rotation(spider)
    
    def setup_spider_rotation(self, spider):
        """Set up rotation for spider-specific logs."""
        from scraper_core.logging_config import LoggingConfig
        
        # Get spider-specific log path
        log_path = LoggingConfig.get_log_file_path(spider.name)
        
        # Get spider logger
        spider_logger = logging.getLogger(spider.name)
        
        # Create rotating handler for spider
        rotation_settings = LogRotationConfig.get_rotation_settings()
        
        if rotation_settings['type'] == 'size':
            handler = logging.handlers.RotatingFileHandler(
                filename=str(log_path),
                maxBytes=rotation_settings['max_bytes'],
                backupCount=rotation_settings['backup_count'],
                encoding='utf-8'
            )
        else:
            handler = logging.handlers.TimedRotatingFileHandler(
                filename=str(log_path),
                when=rotation_settings['when'],
                interval=rotation_settings['interval'],
                backupCount=rotation_settings['backup_count'],
                encoding='utf-8'
            )
        
        # Set format
        log_format = self.settings.get('LOG_FORMAT', '%(levelname)s: %(message)s')
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        
        # Add handler to spider logger
        spider_logger.addHandler(handler)
        spider_logger.info(f"Spider-specific log rotation enabled for {spider.name}")
