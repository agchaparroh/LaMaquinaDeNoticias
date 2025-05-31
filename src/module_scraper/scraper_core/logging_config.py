"""
Logging configuration module for the scraper project.
Provides centralized logging configuration for different environments.
"""

import os
import logging
from datetime import datetime
from pathlib import Path


class LoggingConfig:
    """Configuration class for Scrapy logging system."""
    
    # Log levels mapping
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    # Default log format with more detailed information
    DEFAULT_LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    
    # Alternative formats for different use cases
    FORMATS = {
        'detailed': '%(asctime)s [%(process)d:%(thread)d] [%(name)s] %(levelname)s: %(message)s',
        'simple': '%(levelname)s: %(message)s',
        'json': '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
        'production': '%(asctime)s %(levelname)s: %(message)s'
    }
    
    # Date format
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    @classmethod
    def get_environment(cls):
        """Get current environment from environment variable."""
        return os.getenv('ENVIRONMENT', 'development').lower()
    
    @classmethod
    def get_log_level(cls, environment=None):
        """
        Get appropriate log level for the environment.
        
        Args:
            environment: Override environment (development, staging, production)
            
        Returns:
            str: Log level name
        """
        if environment is None:
            environment = cls.get_environment()
            
        # Environment-specific log levels
        env_levels = {
            'development': 'DEBUG',
            'staging': 'INFO',
            'production': 'WARNING',
            'test': 'INFO'
        }
        
        # Allow override via environment variable
        env_log_level = os.getenv('LOG_LEVEL')
        if env_log_level and env_log_level.upper() in cls.LOG_LEVELS:
            return env_log_level.upper()
            
        return env_levels.get(environment, 'INFO')
    
    @classmethod
    def get_log_format(cls, environment=None):
        """
        Get appropriate log format for the environment.
        
        Args:
            environment: Override environment
            
        Returns:
            str: Log format string
        """
        if environment is None:
            environment = cls.get_environment()
            
        # Environment-specific formats
        env_formats = {
            'development': cls.FORMATS['detailed'],
            'staging': cls.DEFAULT_LOG_FORMAT,
            'production': cls.FORMATS['production'],
            'test': cls.FORMATS['simple']
        }
        
        # Allow override via environment variable
        format_type = os.getenv('LOG_FORMAT_TYPE')
        if format_type and format_type in cls.FORMATS:
            return cls.FORMATS[format_type]
            
        return env_formats.get(environment, cls.DEFAULT_LOG_FORMAT)
    
    @classmethod
    def get_log_file_path(cls, spider_name=None):
        """
        Get the log file path for the current environment.
        
        Args:
            spider_name: Optional spider name for spider-specific logs
            
        Returns:
            Path: Log file path
        """
        # Base log directory
        project_root = Path(__file__).resolve().parent.parent.parent
        log_dir = project_root / 'logs'
        
        # Create logs directory structure
        environment = cls.get_environment()
        env_log_dir = log_dir / environment
        
        if spider_name:
            spider_log_dir = env_log_dir / 'spiders'
            spider_log_dir.mkdir(parents=True, exist_ok=True)
            
            # Include date in filename for easier rotation
            date_str = datetime.now().strftime('%Y-%m-%d')
            return spider_log_dir / f'{spider_name}_{date_str}.log'
        else:
            env_log_dir.mkdir(parents=True, exist_ok=True)
            
            # Main scrapy log
            date_str = datetime.now().strftime('%Y-%m-%d')
            return env_log_dir / f'scrapy_{date_str}.log'
    
    @classmethod
    def get_component_log_levels(cls, environment=None):
        """
        Get component-specific log levels.
        
        Args:
            environment: Override environment
            
        Returns:
            dict: Component name to log level mapping
        """
        if environment is None:
            environment = cls.get_environment()
            
        base_level = cls.get_log_level(environment)
        
        # Component-specific overrides
        components = {
            'scrapy': base_level,
            'scrapy.core.engine': base_level,
            'scrapy.downloadermiddlewares': base_level,
            'scrapy.spidermiddlewares': base_level,
            'scrapy.extensions': base_level,
            'scrapy.middleware': base_level,
            'scrapy.pipelines': base_level,
            'scrapy.dupefilters': 'INFO',  # Less verbose for duplicate filtering
            'scrapy.core.scraper': base_level,
            'scrapy.utils.log': 'WARNING',  # Reduce noise from utils
            
            # Our custom components - more verbose in development
            'scraper_core.pipelines': 'DEBUG' if environment == 'development' else base_level,
            'scraper_core.middlewares': 'DEBUG' if environment == 'development' else base_level,
            'scraper_core.spiders': 'DEBUG' if environment == 'development' else base_level,
            'scraper_core.utils': 'DEBUG' if environment == 'development' else base_level,
            
            # Specific pipeline logging
            'scraper_core.pipelines.validation': 'INFO',
            'scraper_core.pipelines.cleaning': 'INFO',
            'scraper_core.pipelines.supabase_pipeline': 'DEBUG' if environment == 'development' else 'INFO',
            
            # Third-party libraries
            'scrapy_user_agents': 'WARNING',
            'scrapy_crawl_once': 'INFO',
            'urllib3.connectionpool': 'WARNING',  # Reduce connection pool noise
            'filelock': 'WARNING',  # Reduce filelock noise
        }
        
        return components
    
    @classmethod
    def should_log_to_file(cls, environment=None):
        """
        Determine if logs should be written to files.
        
        Args:
            environment: Override environment
            
        Returns:
            bool: True if logs should be written to files
        """
        if environment is None:
            environment = cls.get_environment()
            
        # Always log to file in production and staging
        if environment in ['production', 'staging']:
            return True
            
        # Check environment variable for development/test
        return os.getenv('LOG_TO_FILE', 'false').lower() == 'true'
    
    @classmethod
    def get_log_file_encoding(cls):
        """Get log file encoding."""
        return os.getenv('LOG_FILE_ENCODING', 'utf-8')
    
    @classmethod
    def get_scrapy_settings(cls):
        """
        Get Scrapy settings dictionary for logging configuration.
        
        Returns:
            dict: Settings to be merged with Scrapy settings
        """
        environment = cls.get_environment()
        settings = {
            'LOG_LEVEL': cls.get_log_level(environment),
            'LOG_FORMAT': cls.get_log_format(environment),
            'LOG_DATEFORMAT': cls.DATE_FORMAT,
            'LOG_STDOUT': environment == 'test',  # Capture logs in tests
            'LOG_SHORT_NAMES': False,  # Use full logger names
        }
        
        # Add file logging if enabled
        if cls.should_log_to_file(environment):
            settings['LOG_FILE'] = str(cls.get_log_file_path())
            settings['LOG_FILE_ENCODING'] = cls.get_log_file_encoding()
        
        # Component-specific log levels
        settings['LOGGERS'] = cls.get_component_log_levels(environment)
        
        return settings


# Logging best practices documentation
LOGGING_GUIDELINES = """
# Scrapy Logging Guidelines

## Log Levels Usage:

### DEBUG
- Detailed information for diagnosing problems
- Variable values, function entry/exit
- Intermediate processing steps
- Use in development only

Examples:
```python
logger.debug(f"Processing item: {item.get('url')}")
logger.debug(f"Request headers: {request.headers}")
```

### INFO
- General informational messages
- Spider start/stop
- Successfully processed items
- Configuration confirmations

Examples:
```python
logger.info(f"Spider {self.name} started")
logger.info(f"Processed {count} items successfully")
```

### WARNING
- Warning messages for recoverable issues
- Deprecated features usage
- Missing optional data
- Performance concerns

Examples:
```python
logger.warning(f"Missing optional field 'author' for {item['url']}")
logger.warning("Response took longer than expected: {duration}s")
```

### ERROR
- Error messages for serious problems
- Failed requests after retries
- Data validation failures
- External service errors

Examples:
```python
logger.error(f"Failed to parse date: {e}")
logger.error(f"Supabase connection failed: {e}")
```

### CRITICAL
- Critical failures requiring immediate attention
- System-wide failures
- Data corruption risks
- Security issues

Examples:
```python
logger.critical("Database connection lost - stopping spider")
logger.critical("Invalid API credentials detected")
```

## Best Practices:

1. Always use logger instead of print()
2. Include context in log messages (URLs, item IDs, etc.)
3. Don't log sensitive information (passwords, API keys)
4. Use structured logging where possible
5. Keep production logs concise and actionable
"""
