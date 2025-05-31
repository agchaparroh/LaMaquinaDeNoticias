"""
Log rotation configuration for the scraper project.
Provides utilities for setting up log rotation using Python's logging handlers.
"""

import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime


class LogRotationConfig:
    """Configuration for log rotation in the scraper project."""
    
    # Default rotation settings
    DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    DEFAULT_BACKUP_COUNT = 5  # Keep 5 old log files
    
    @classmethod
    def setup_rotating_logger(cls, logger_name, log_file_path, 
                            max_bytes=None, backup_count=None,
                            log_level=None, log_format=None):
        """
        Set up a rotating file logger.
        
        Args:
            logger_name: Name of the logger
            log_file_path: Path to the log file
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            log_level: Logging level
            log_format: Log message format
            
        Returns:
            logging.Logger: Configured logger instance
        """
        if max_bytes is None:
            max_bytes = cls.DEFAULT_MAX_BYTES
        if backup_count is None:
            backup_count = cls.DEFAULT_BACKUP_COUNT
            
        # Create logger
        logger = logging.getLogger(logger_name)
        
        # Set level
        if log_level:
            logger.setLevel(log_level)
        
        # Ensure log directory exists
        log_file_path = Path(log_file_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # Set format
        if log_format:
            formatter = logging.Formatter(log_format)
            handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        return logger
    
    @classmethod
    def setup_time_rotating_logger(cls, logger_name, log_file_path,
                                 when='midnight', interval=1, backup_count=7,
                                 log_level=None, log_format=None):
        """
        Set up a time-based rotating file logger.
        
        Args:
            logger_name: Name of the logger
            log_file_path: Path to the log file
            when: Type of interval ('S', 'M', 'H', 'D', 'midnight')
            interval: Rotation interval
            backup_count: Number of backup files to keep
            log_level: Logging level
            log_format: Log message format
            
        Returns:
            logging.Logger: Configured logger instance
        """
        # Create logger
        logger = logging.getLogger(logger_name)
        
        # Set level
        if log_level:
            logger.setLevel(log_level)
        
        # Ensure log directory exists
        log_file_path = Path(log_file_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create time rotating file handler
        handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(log_file_path),
            when=when,
            interval=interval,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # Set format
        if log_format:
            formatter = logging.Formatter(log_format)
            handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        return logger
    
    @classmethod
    def get_rotation_settings(cls, environment=None):
        """
        Get rotation settings based on environment.
        
        Args:
            environment: Environment name (development, staging, production)
            
        Returns:
            dict: Rotation configuration
        """
        if environment is None:
            environment = os.getenv('ENVIRONMENT', 'development').lower()
        
        # Environment-specific settings
        settings = {
            'development': {
                'type': 'size',
                'max_bytes': 5 * 1024 * 1024,  # 5 MB
                'backup_count': 3,
            },
            'staging': {
                'type': 'time',
                'when': 'midnight',
                'interval': 1,
                'backup_count': 7,  # Keep 1 week
            },
            'production': {
                'type': 'time',
                'when': 'midnight',
                'interval': 1,
                'backup_count': 30,  # Keep 1 month
            },
            'test': {
                'type': 'size',
                'max_bytes': 1 * 1024 * 1024,  # 1 MB
                'backup_count': 1,
            }
        }
        
        return settings.get(environment, settings['development'])
    
    @classmethod
    def create_scrapy_log_handler(cls, settings):
        """
        Create a log handler compatible with Scrapy's logging system.
        
        Args:
            settings: Scrapy settings object
            
        Returns:
            logging.Handler: Configured handler
        """
        from scraper_core.logging_config import LoggingConfig
        
        # Get log file path
        log_file = settings.get('LOG_FILE')
        if not log_file:
            log_file = str(LoggingConfig.get_log_file_path())
        
        # Get rotation settings
        rotation_settings = cls.get_rotation_settings()
        
        if rotation_settings['type'] == 'size':
            handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=rotation_settings['max_bytes'],
                backupCount=rotation_settings['backup_count'],
                encoding='utf-8'
            )
        else:  # time-based
            handler = logging.handlers.TimedRotatingFileHandler(
                filename=log_file,
                when=rotation_settings['when'],
                interval=rotation_settings['interval'],
                backupCount=rotation_settings['backup_count'],
                encoding='utf-8'
            )
        
        # Set format
        log_format = settings.get('LOG_FORMAT', '%(levelname)s: %(message)s')
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        
        return handler


# Logrotate configuration template for production systems
LOGROTATE_CONFIG_TEMPLATE = """# Logrotate configuration for Scrapy logs
# Place this file in /etc/logrotate.d/scrapy-scraper

{log_path}/*.log {{
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 {user} {group}
    sharedscripts
    postrotate
        # Send SIGUSR1 to Scrapy process to reopen log files
        if [ -f {pid_file} ]; then
            kill -USR1 `cat {pid_file}` > /dev/null 2>&1 || true
        fi
    endscript
}}

# Spider-specific logs
{log_path}/*/spiders/*.log {{
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 {user} {group}
}}

# Environment-specific logs
{log_path}/production/*.log {{
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    maxsize 100M
    create 0644 {user} {group}
}}

{log_path}/staging/*.log {{
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    maxsize 50M
    create 0644 {user} {group}
}}
"""


def generate_logrotate_config(project_root, user='scrapy', group='scrapy', pid_file='/var/run/scrapy.pid'):
    """
    Generate logrotate configuration for the project.
    
    Args:
        project_root: Path to project root
        user: System user for log files
        group: System group for log files
        pid_file: Path to PID file
        
    Returns:
        str: Logrotate configuration
    """
    log_path = Path(project_root) / 'logs'
    
    return LOGROTATE_CONFIG_TEMPLATE.format(
        log_path=log_path,
        user=user,
        group=group,
        pid_file=pid_file
    )


if __name__ == '__main__':
    # Example: Generate logrotate config
    import sys
    
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
        config = generate_logrotate_config(project_root)
        
        # Save to file
        config_path = Path(project_root) / 'config' / 'logrotate.conf'
        config_path.parent.mkdir(exist_ok=True)
        config_path.write_text(config)
        
        print(f"Logrotate configuration saved to: {config_path}")
        print("\nTo install (requires sudo):")
        print(f"sudo cp {config_path} /etc/logrotate.d/scrapy-scraper")
        print("sudo chown root:root /etc/logrotate.d/scrapy-scraper")
        print("sudo chmod 644 /etc/logrotate.d/scrapy-scraper")
    else:
        print("Usage: python log_rotation.py <project_root>")
