"""
Tests for logging configuration and utilities.
"""

import unittest
import logging
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

from scraper_core.logging_config import LoggingConfig
from scraper_core.log_rotation import LogRotationConfig
from scraper_core.utils.logging_utils import (
    LoggerMixin, log_execution_time, log_exceptions,
    log_item_processing, StructuredLogger, sanitize_log_data,
    SpiderLoggerAdapter
)


class TestLoggingConfig(unittest.TestCase):
    """Test cases for LoggingConfig class."""
    
    def test_get_environment_default(self):
        """Test default environment detection."""
        with patch.dict(os.environ, {}, clear=True):
            env = LoggingConfig.get_environment()
            self.assertEqual(env, 'development')
    
    def test_get_environment_from_env_var(self):
        """Test environment detection from env variable."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            env = LoggingConfig.get_environment()
            self.assertEqual(env, 'production')
    
    def test_get_log_level_by_environment(self):
        """Test log level selection by environment."""
        test_cases = {
            'development': 'DEBUG',
            'staging': 'INFO',
            'production': 'WARNING',
            'test': 'INFO'
        }
        
        for env, expected_level in test_cases.items():
            level = LoggingConfig.get_log_level(environment=env)
            self.assertEqual(level, expected_level)
    
    def test_get_log_level_override(self):
        """Test log level override via environment variable."""
        with patch.dict(os.environ, {'LOG_LEVEL': 'ERROR'}):
            level = LoggingConfig.get_log_level()
            self.assertEqual(level, 'ERROR')
    
    def test_get_log_format_by_environment(self):
        """Test log format selection by environment."""
        formats = {
            'development': LoggingConfig.FORMATS['detailed'],
            'production': LoggingConfig.FORMATS['production'],
            'test': LoggingConfig.FORMATS['simple']
        }
        
        for env, expected_format in formats.items():
            format_str = LoggingConfig.get_log_format(environment=env)
            self.assertEqual(format_str, expected_format)
    
    def test_get_log_file_path(self):
        """Test log file path generation."""
        with patch('scraper_core.logging_config.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '2024-01-01'
            
            # Test main log path
            path = LoggingConfig.get_log_file_path()
            self.assertTrue(str(path).endswith('scrapy_2024-01-01.log'))
            
            # Test spider-specific log path
            spider_path = LoggingConfig.get_log_file_path('test_spider')
            self.assertTrue(str(spider_path).endswith('test_spider_2024-01-01.log'))
            self.assertIn('spiders', str(spider_path))
    
    def test_get_component_log_levels(self):
        """Test component-specific log level configuration."""
        # Development environment
        dev_levels = LoggingConfig.get_component_log_levels('development')
        self.assertEqual(dev_levels['scraper_core.pipelines'], 'DEBUG')
        self.assertEqual(dev_levels['scrapy.dupefilters'], 'INFO')
        
        # Production environment
        prod_levels = LoggingConfig.get_component_log_levels('production')
        self.assertEqual(prod_levels['scraper_core.pipelines'], 'WARNING')
        self.assertEqual(prod_levels['urllib3.connectionpool'], 'WARNING')
    
    def test_should_log_to_file(self):
        """Test file logging decision logic."""
        # Production and staging always log to file
        self.assertTrue(LoggingConfig.should_log_to_file('production'))
        self.assertTrue(LoggingConfig.should_log_to_file('staging'))
        
        # Development depends on env var
        with patch.dict(os.environ, {'LOG_TO_FILE': 'true'}):
            self.assertTrue(LoggingConfig.should_log_to_file('development'))
        
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(LoggingConfig.should_log_to_file('development'))
    
    def test_get_scrapy_settings(self):
        """Test Scrapy settings generation."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            settings = LoggingConfig.get_scrapy_settings()
            
            self.assertEqual(settings['LOG_LEVEL'], 'WARNING')
            self.assertIn('LOG_FORMAT', settings)
            self.assertIn('LOGGERS', settings)
            self.assertIsInstance(settings['LOGGERS'], dict)


class TestLogRotation(unittest.TestCase):
    """Test cases for log rotation functionality."""
    
    def test_get_rotation_settings_by_environment(self):
        """Test rotation settings for different environments."""
        # Development - size-based rotation
        dev_settings = LogRotationConfig.get_rotation_settings('development')
        self.assertEqual(dev_settings['type'], 'size')
        self.assertEqual(dev_settings['max_bytes'], 5 * 1024 * 1024)
        
        # Production - time-based rotation
        prod_settings = LogRotationConfig.get_rotation_settings('production')
        self.assertEqual(prod_settings['type'], 'time')
        self.assertEqual(prod_settings['when'], 'midnight')
        self.assertEqual(prod_settings['backup_count'], 30)
    
    def test_setup_rotating_logger(self):
        """Test rotating logger setup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'test.log'
            
            logger = LogRotationConfig.setup_rotating_logger(
                'test_logger',
                log_path,
                max_bytes=1024,
                backup_count=3
            )
            
            self.assertIsInstance(logger, logging.Logger)
            self.assertEqual(len(logger.handlers), 1)
            handler = logger.handlers[0]
            self.assertIsInstance(handler, logging.handlers.RotatingFileHandler)
    
    def test_setup_time_rotating_logger(self):
        """Test time-based rotating logger setup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'test.log'
            
            logger = LogRotationConfig.setup_time_rotating_logger(
                'test_time_logger',
                log_path,
                when='S',  # Seconds for testing
                interval=1,
                backup_count=3
            )
            
            self.assertIsInstance(logger, logging.Logger)
            self.assertEqual(len(logger.handlers), 1)
            handler = logger.handlers[0]
            self.assertIsInstance(handler, logging.handlers.TimedRotatingFileHandler)


class TestLoggingUtils(unittest.TestCase):
    """Test cases for logging utilities."""
    
    def test_logger_mixin(self):
        """Test LoggerMixin functionality."""
        class TestClass(LoggerMixin):
            pass
        
        obj = TestClass()
        logger = obj.logger
        
        self.assertIsInstance(logger, logging.Logger)
        self.assertIn('TestClass', logger.name)
    
    def test_log_execution_time_decorator(self):
        """Test execution time logging decorator."""
        mock_logger = Mock()
        
        with patch('logging.getLogger', return_value=mock_logger):
            @log_execution_time
            def test_func():
                return "result"
            
            result = test_func()
            self.assertEqual(result, "result")
            
            # Check that debug was called
            mock_logger.debug.assert_called()
    
    def test_log_exceptions_decorator(self):
        """Test exception logging decorator."""
        mock_logger = Mock()
        
        with patch('logging.getLogger', return_value=mock_logger):
            @log_exceptions()
            def failing_func():
                raise ValueError("Test error")
            
            with self.assertRaises(ValueError):
                failing_func()
            
            # Check that error was logged
            mock_logger.log.assert_called_with(
                logging.ERROR,
                "Exception in %s: %s",
                'failing_func',
                'Test error',
                exc_info=unittest.mock.ANY
            )
    
    def test_sanitize_log_data(self):
        """Test sensitive data sanitization."""
        sensitive_data = {
            'username': 'john',
            'password': 'secret123',
            'api_key': 'abc123',
            'data': {
                'token': 'xyz789',
                'info': 'public'
            }
        }
        
        sanitized = sanitize_log_data(sensitive_data)
        
        self.assertEqual(sanitized['username'], 'john')
        self.assertEqual(sanitized['password'], '***REDACTED***')
        self.assertEqual(sanitized['api_key'], '***REDACTED***')
        self.assertEqual(sanitized['data']['token'], '***REDACTED***')
        self.assertEqual(sanitized['data']['info'], 'public')
    
    def test_structured_logger(self):
        """Test structured logging functionality."""
        mock_logger = Mock()
        
        with patch('logging.getLogger', return_value=mock_logger):
            structured = StructuredLogger('test')
            structured.info('user_login', user_id=123, ip='192.168.1.1')
            
            # Verify JSON logging
            mock_logger.log.assert_called()
            call_args = mock_logger.log.call_args[0]
            self.assertEqual(call_args[0], logging.INFO)
            
            # Parse logged JSON
            logged_data = json.loads(call_args[1])
            self.assertEqual(logged_data['event'], 'user_login')
            self.assertEqual(logged_data['user_id'], 123)
            self.assertEqual(logged_data['ip'], '192.168.1.1')
    
    def test_spider_logger_adapter(self):
        """Test spider logger adapter."""
        mock_logger = Mock()
        mock_spider = Mock()
        mock_spider.name = 'test_spider'
        
        adapter = SpiderLoggerAdapter(mock_logger, {'spider': mock_spider})
        
        # Test message processing
        msg, kwargs = adapter.process("Test message", {})
        self.assertEqual(msg, "[test_spider] Test message")
        self.assertEqual(kwargs['extra']['spider_name'], 'test_spider')


class TestLogItemProcessing(unittest.TestCase):
    """Test item processing decorator."""
    
    def test_successful_item_processing(self):
        """Test logging of successful item processing."""
        mock_logger = Mock()
        
        class TestPipeline:
            @log_item_processing
            def process_item(self, item, spider):
                return item
        
        with patch('logging.getLogger', return_value=mock_logger):
            pipeline = TestPipeline()
            spider = Mock(name='test_spider')
            item = {'url': 'http://test.com', 'titulo': 'Test Title'}
            
            result = pipeline.process_item(item, spider)
            
            self.assertEqual(result, item)
            # Verify debug logging occurred
            self.assertEqual(mock_logger.debug.call_count, 2)
    
    def test_failed_item_processing(self):
        """Test logging of failed item processing."""
        mock_logger = Mock()
        
        class TestPipeline:
            @log_item_processing
            def process_item(self, item, spider):
                raise ValueError("Processing error")
        
        with patch('logging.getLogger', return_value=mock_logger):
            pipeline = TestPipeline()
            spider = Mock(name='test_spider')
            item = {'url': 'http://test.com'}
            
            with self.assertRaises(ValueError):
                pipeline.process_item(item, spider)
            
            # Verify error was logged
            mock_logger.error.assert_called()


if __name__ == '__main__':
    unittest.main()
