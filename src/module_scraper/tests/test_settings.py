"""
Tests for Scrapy settings configuration.
"""
import unittest
import os
from unittest.mock import patch
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scraper_core import settings


class TestSettings(unittest.TestCase):
    """Test cases for settings configuration."""
    
    def setUp(self):
        """Set up test environment."""
        # Set test environment variables
        os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
        os.environ['SUPABASE_KEY'] = 'test-anon-key'
        os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test-service-key'
        os.environ['LOG_LEVEL'] = 'DEBUG'
    
    def test_supabase_settings_loaded(self):
        """Test that Supabase settings are loaded from environment."""
        # Reload settings to pick up environment variables
        import importlib
        importlib.reload(settings)
        
        self.assertEqual(settings.SUPABASE_URL, 'https://test.supabase.co')
        self.assertEqual(settings.SUPABASE_KEY, 'test-anon-key')
        self.assertEqual(settings.SUPABASE_SERVICE_ROLE_KEY, 'test-service-key')
    
    def test_supabase_storage_settings(self):
        """Test Supabase storage configuration."""
        self.assertEqual(settings.SUPABASE_STORAGE_BUCKET, 'articulos-html')
        self.assertFalse(settings.SUPABASE_STORAGE_PUBLIC)
    
    def test_supabase_retry_settings(self):
        """Test Supabase retry configuration."""
        self.assertEqual(settings.SUPABASE_MAX_RETRIES, 3)
        self.assertEqual(settings.SUPABASE_RETRY_DELAY, 1.0)
        self.assertEqual(settings.SUPABASE_RETRY_BACKOFF, 2.0)
    
    def test_supabase_timeout_settings(self):
        """Test Supabase timeout configuration."""
        self.assertEqual(settings.SUPABASE_POSTGREST_TIMEOUT, 10)
        self.assertEqual(settings.SUPABASE_STORAGE_TIMEOUT, 30)
    
    def test_pipeline_configuration(self):
        """Test that Supabase pipeline is configured."""
        self.assertIn('scraper_core.pipelines.supabase_pipeline.SupabaseStoragePipeline', 
                      settings.ITEM_PIPELINES)
        self.assertEqual(
            settings.ITEM_PIPELINES['scraper_core.pipelines.supabase_pipeline.SupabaseStoragePipeline'],
            300
        )
    
    def test_logging_configuration(self):
        """Test logging configuration."""
        import importlib
        importlib.reload(settings)
        
        self.assertEqual(settings.LOG_LEVEL, 'DEBUG')
        self.assertIn('scraper_core.pipelines.supabase_pipeline', settings.LOGGERS)
        self.assertIn('scraper_core.utils.supabase_client', settings.LOGGERS)
    
    @patch.dict(os.environ, {'ENVIRONMENT': 'production'})
    def test_production_settings(self):
        """Test production environment settings."""
        import importlib
        importlib.reload(settings)
        
        self.assertEqual(settings.CONCURRENT_REQUESTS, 16)
        self.assertEqual(settings.CONCURRENT_REQUESTS_PER_DOMAIN, 4)
        self.assertEqual(settings.DOWNLOAD_DELAY, 1)
        self.assertEqual(settings.AUTOTHROTTLE_TARGET_CONCURRENCY, 4.0)
        self.assertEqual(settings.LOG_LEVEL, 'WARNING')


if __name__ == '__main__':
    unittest.main()
