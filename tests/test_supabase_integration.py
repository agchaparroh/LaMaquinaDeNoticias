import unittest
import os
import logging
from datetime import datetime, timezone
import uuid

# Adjust imports based on the new file location relative to the src directory
# This assumes that the 'tests' directory is at the same level as 'src'
# and Python's path is configured to find 'src.module_scraper...'
from src.module_scraper.scraper_core.utils.supabase_client import SupabaseClient
from src.module_scraper.scraper_core.pipelines import SupabaseStoragePipeline
from src.module_scraper.scraper_core.items import ArticuloInItem

# Configure basic logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestSupabaseIntegration(unittest.TestCase):
    """Integration tests for SupabaseClient and SupabaseStoragePipeline."""

    @classmethod
    def setUpClass(cls):
        """Set up the Supabase client and pipeline once for all tests in the class."""
        logger.info("Setting up TestSupabaseIntegration class...")
        cls.supabase_url = os.getenv('SUPABASE_URL')
        cls.supabase_key = os.getenv('SUPABASE_KEY')

        if not cls.supabase_url or not cls.supabase_key:
            raise unittest.SkipTest(
                "SUPABASE_URL and SUPABASE_KEY environment variables must be set for integration tests."
            )

        try:
            # Initialize SupabaseClient directly
            cls.supabase_client = SupabaseClient() 
            logger.info("SupabaseClient initialized for integration tests.")

            # Initialize SupabaseStoragePipeline
            # Mock crawler settings for pipeline initialization if necessary,
            # or pass parameters directly if from_crawler is not strictly needed here.
            # For simplicity, we'll instantiate it directly if possible, 
            # or mock the parts of 'crawler' it needs.
            class MockCrawler:
                def __init__(self):
                    self.settings = {
                        'SUPABASE_STORAGE_BUCKET': 'test-articulos-html', # Use a dedicated test bucket
                        'TENACITY_STOP_AFTER_ATTEMPT': 2, # Faster retries for tests
                        'TENACITY_WAIT_MIN': 1,
                        'TENACITY_WAIT_MAX': 2
                    }
                def settings_get(self, key, default=None):
                    return self.settings.get(key, default)
                def settings_getint(self, key, default=None):
                    return int(self.settings.get(key, default))

            mock_crawler = MockCrawler()
            cls.pipeline = SupabaseStoragePipeline.from_crawler(mock_crawler)
            # Manually assign the already initialized SupabaseClient instance
            cls.pipeline.supabase_client = cls.supabase_client
            cls.pipeline.html_bucket_name = mock_crawler.settings.get('SUPABASE_STORAGE_BUCKET')
            
            logger.info(f"SupabaseStoragePipeline initialized for integration tests. Bucket: {cls.pipeline.html_bucket_name}")

            # Ensure the test bucket exists
            cls.pipeline.open_spider(spider=None) # 'spider' arg is not used by current open_spider logic for bucket creation
            logger.info(f"Ensured test bucket '{cls.pipeline.html_bucket_name}' exists.")

        except Exception as e:
            logger.error(f"Error during setUpClass: {e}", exc_info=True)
            # Re-raise or handle as appropriate, perhaps skipping all tests in class
            raise unittest.SkipTest(f"Failed to initialize Supabase resources: {e}")

    @classmethod
    def tearDownClass(cls):
        """Clean up resources after all tests in the class have run."""
        logger.info("Tearing down TestSupabaseIntegration class...")
        if hasattr(cls, 'pipeline') and cls.pipeline:
            cls.pipeline.close_spider(spider=None) # 'spider' arg is not used by current close_spider logic
        # Note: Data cleanup (deleting test items/files) is not implemented here yet.
        # This should be added for robust testing (e.g., deleting items by a test run ID or specific test tags).

    def _create_sample_item(self, unique_id: str) -> ArticuloInItem:
        """Helper method to create a sample ArticuloInItem for testing."""
        item = ArticuloInItem()
        item['url'] = f'http://example.com/test-article-{unique_id}'
        item['titular'] = f'Test Article Title {unique_id}'
        item['medio'] = 'Test Medio'
        item['categoria_principal'] = 'Test Categoria'
        item['contenido_html'] = f'<html><body><h1>Test Article {unique_id}</h1><p>Some content.</p></body></html>'
        item['fecha_publicacion'] = datetime.now(timezone.utc).isoformat()
        item['autores'] = [{'nombre': f'Test Author {unique_id}'}]
        item['etiquetas'] = [{'nombre': f'Test Tag {unique_id}'}]
        # fecha_recopilacion will be set by the pipeline
        return item

    def test_pipeline_processes_item_successfully(self):
        """Test that the pipeline can successfully process and store a new item."""
        logger.info("Running test_pipeline_processes_item_successfully...")
        test_id = str(uuid.uuid4())
        sample_item = self._create_sample_item(test_id)
        
        processed_item_adapter = self.pipeline.process_item(sample_item, spider=None) # 'spider' is not used by process_item
        processed_item = processed_item_adapter.item

        self.assertIsNotNone(processed_item, "Pipeline returned None")
        self.assertNotIn('error_detalle', processed_item, 
                         f"Pipeline reported an error: {processed_item.get('error_detalle')}")
        self.assertIn('storage_path', processed_item, "storage_path not set in processed item")
        self.assertTrue(processed_item['storage_path'].startswith(f"{sample_item['medio'].lower()}/"))
        logger.info(f"Item processed. Storage path: {processed_item['storage_path']}")

        # Verification: Check if data exists in Supabase
        # 1. Check if article exists in 'articulos' table
        try:
            response = self.supabase_client.client.table('articulos_beta') \
                .select('url, titular') \
                .eq('url', sample_item['url']) \
                .execute()
            self.assertTrue(len(response.data) > 0, f"Article with URL {sample_item['url']} not found in DB.")
            self.assertEqual(response.data[0]['titular'], sample_item['titular'])
            logger.info(f"Verified article '{sample_item['url']}' in database.")

            # 2. Check if HTML file exists in storage (optional, more complex to verify content directly)
            # For now, we trust that if storage_path is set and no error, upload was attempted.
            # A more thorough test would download and verify content or check metadata.
            # Example: list files in bucket/path
            # file_list_response = self.supabase_client.client.storage.from_(self.pipeline.html_bucket_name).list(path=processed_item['storage_path'].rsplit('/', 1)[0])
            # self.assertTrue(any(f['name'] == processed_item['storage_path'].split('/')[-1] for f in file_list_response), "HTML file not found in storage bucket listing.")
            # logger.info(f"Verified HTML file for '{sample_item['url']}' in storage (by listing).")

        except Exception as e:
            self.fail(f"Supabase verification query failed: {e}")

        # TODO: Add cleanup for the created item and file to make test idempotent
        # For example, delete the article by URL and the file by storage_path
        # self.supabase_client.client.table('articulos_beta').delete().eq('url', sample_item['url']).execute()
        # self.supabase_client.client.storage.from_(self.pipeline.html_bucket_name).remove([processed_item['storage_path']])


if __name__ == '__main__':
    unittest.main()
