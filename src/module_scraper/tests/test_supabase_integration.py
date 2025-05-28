import unittest
from unittest.mock import patch, MagicMock
import os
import uuid  # For unique URLs
from datetime import datetime
import gzip  # For decompressing HTML

# Adjust these imports based on your project structure
from scraper_core.items import ArticuloInItem
from scraper_core.pipelines import SupabaseStoragePipeline
from scraper_core.utils.supabase_client import SupabaseClient # Direct import for test client
from scraper_core.utils.compression import decompress_html # For verifying content

from scrapy.settings import Settings
from scrapy.crawler import Crawler # For spec in MagicMock
from scrapy.utils.project import get_project_settings
from scrapy.spiders import Spider

# Load .env.test for test environment
from dotenv import load_dotenv
test_env_path = os.path.join(os.path.dirname(__file__), '..', '.env.test')
if os.path.exists(test_env_path):
    load_dotenv(dotenv_path=test_env_path, override=True)
    print(f"Loaded test environment from: {test_env_path}")
else:
    # Fallback or raise error if test env not found
    print("Warning: .env.test not found, ensure test Supabase credentials are set in environment")

class TestSupabaseIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up a test Supabase client and shared resources for all tests in the class."""
        cls.project_settings = get_project_settings()
        
        # Use environment variables directly for test environment
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

        if not supabase_url or not supabase_key:
            raise unittest.SkipTest(
                "Supabase URL/Key not configured. Ensure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
                "env vars are set for a TEST Supabase project before running integration tests."
            )

        cls.supabase_client = SupabaseClient(
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )
        
        cls.test_bucket_name = 'test-articulos-html-integration'
        
        try:
            buckets = cls.supabase_client.list_buckets()
            bucket_exists = any(bucket.get('name') == cls.test_bucket_name for bucket in buckets)
            if not bucket_exists:
                cls.supabase_client.create_bucket(cls.test_bucket_name, public=False)
                print(f"Created test bucket: {cls.test_bucket_name}")
            else:
                print(f"Test bucket already exists: {cls.test_bucket_name}")
        except Exception as e:
            print(f"Warning: Could not ensure test bucket '{cls.test_bucket_name}' exists: {e}")
            # For now, we'll continue - the actual test will fail if bucket is crucial.

        # Override settings for pipeline instances created in tests
        cls.project_settings['SUPABASE_STORAGE_BUCKET'] = cls.test_bucket_name

    @classmethod
    def tearDownClass(cls):
        """Clean up resources after all tests in the class are run."""
        print(f"--- tearDownClass: Starting cleanup for Supabase integration tests ---")
        if hasattr(cls, 'supabase_client') and hasattr(cls, 'test_bucket_name'):
            try:
                # Delete articles created by tests (matching a specific 'medio')
                # Ensure your SupabaseClient's table method returns a query builder that supports .delete(), .eq(), .execute()
                delete_response = cls.supabase_client.table('articulos').delete().eq('medio', 'Test Medio Integration').execute()
                print(f"Cleanup: Attempted to delete test articles. Response: {hasattr(delete_response, 'data') and delete_response.data or 'No data in response'}")

                # List and delete files from the test bucket
                try:
                    # List all files in the bucket
                    files_in_bucket = cls.supabase_client.storage.from_(cls.test_bucket_name).list()
                    if files_in_bucket:
                        # Extract file names/paths
                        file_paths_to_delete = [f['name'] for f in files_in_bucket if 'name' in f]
                        if file_paths_to_delete:
                            # Delete files in batches
                            for file_path in file_paths_to_delete:
                                try:
                                    cls.supabase_client.storage.from_(cls.test_bucket_name).remove([file_path])
                                except Exception as e:
                                    print(f"Failed to delete file {file_path}: {e}")
                            print(f"Cleanup: Deleted {len(file_paths_to_delete)} files from bucket '{cls.test_bucket_name}'.")
                except Exception as e:
                    print(f"Could not list/delete files from bucket: {e}")

            except Exception as e:
                print(f"Error during tearDownClass cleanup: {e}. Manual cleanup of test data may be required.")
        print(f"--- tearDownClass: Finished cleanup ---")

    def setUp(self):
        """Set up resources before each test method."""
        mock_crawler = MagicMock(spec=Crawler) 
        mock_crawler.settings = self.project_settings
        self.pipeline = SupabaseStoragePipeline.from_crawler(mock_crawler)
        self.test_article_url = f'http://example.com/test-article-integration-{uuid.uuid4()}'

    def _get_sample_articulo_item(self):
        item = ArticuloInItem()
        item['url'] = self.test_article_url
        item['titular'] = 'Test Article Titular for Integration Test'
        item['medio'] = 'Test Medio Integration' # Specific medio for easier cleanup
        item['pais_publicacion'] = 'Test Country'
        item['tipo_medio'] = 'Test Type'
        item['fecha_publicacion'] = datetime.now()
        item['contenido_html'] = '<html><body><h1>Test HTML Content for Integration</h1></body></html>'
        item['contenido_texto'] = 'Test HTML Content for Integration'
        item['autor'] = 'Test Author'
        item['idioma'] = 'es'
        item['seccion'] = 'Test Section'
        item['etiquetas_fuente'] = ['test', 'integration']
        item['es_opinion'] = False
        item['es_oficial'] = False
        return item

    def test_process_item_success_scenario(self):
        """Test the successful processing of an item through the pipeline."""
        item = self._get_sample_articulo_item()
        
        self.assertIsNotNone(self.pipeline.supabase_client, "Supabase client in pipeline should not be None")

        adapter = self.pipeline.process_item(item, spider=None)

        self.assertIsNotNone(adapter.get('storage_path'), "storage_path should be set after processing.")
        self.assertTrue(adapter.get('storage_path').endswith('.html.gz'))
        # Check if medio_slug is part of the path (adjust based on actual slugification)
        medio_slug = item['medio'].lower().replace(' ', '-') 
        self.assertIn(medio_slug, adapter.get('storage_path'))
        self.assertNotIn('error_detalle', adapter, "No error should be present for successful processing.")

        try:
            # 1. Verify article metadata in 'articulos' table
            db_response = self.supabase_client.table('articulos').select('*').eq('url', item['url']).execute()
            self.assertTrue(len(db_response.data) > 0, f"Article with URL {item['url']} not found in DB.")
            article_from_db = db_response.data[0]
            self.assertEqual(article_from_db['titular'], item['titular'])
            self.assertEqual(article_from_db['storage_path'], adapter.get('storage_path'))

            # 2. Verify HTML content in Supabase Storage
            storage_path = adapter.get('storage_path')
            # Ensure download method exists and works as expected in your SupabaseClient
            file_bytes = self.supabase_client.storage.from_(self.test_bucket_name).download(storage_path)
            self.assertIsNotNone(file_bytes, f"File {storage_path} not found in bucket {self.test_bucket_name}.")
            
            decompressed_html = decompress_html(file_bytes)
            self.assertEqual(decompressed_html, item['contenido_html'])

        except Exception as e:
            self.fail(f"Supabase verification failed: {e}")

    def test_process_item_missing_required_fields(self):
        """Test handling of items with missing required fields."""
        item = ArticuloInItem()
        # Only set partial data - missing required fields like 'url', 'titular', etc.
        item['contenido_html'] = '<html><body>Test</body></html>'
        
        # Process should handle the item gracefully (either drop or mark with error)
        try:
            adapter = self.pipeline.process_item(item, spider=None)
            # If it doesn't raise an exception, check for error_detalle
            self.assertIn('error_detalle', adapter, "Item with missing fields should have error_detalle")
        except Exception as e:
            # This is also acceptable - the pipeline might raise an exception for invalid items
            self.assertIn("required", str(e).lower())
    
    def test_process_item_empty_html_content(self):
        """Test handling of items with empty HTML content."""
        item = self._get_sample_articulo_item()
        item['contenido_html'] = ''  # Empty HTML
        
        adapter = self.pipeline.process_item(item, spider=None)
        
        # Should process but might flag as having empty content
        if 'error_detalle' in adapter:
            self.assertIn('empty', adapter['error_detalle'].lower())
        else:
            # Verify empty content was handled (possibly stored as empty compressed file)
            self.assertIsNotNone(adapter.get('storage_path'))
    
    @patch('scraper_core.utils.supabase_client.SupabaseClient.upsert_articulo')
    def test_process_item_database_error(self, mock_upsert):
        """Test handling of database errors during upsert."""
        # Configure mock to raise an exception
        mock_upsert.side_effect = Exception("Database connection error")
        
        item = self._get_sample_articulo_item()
        
        # Process should handle the error gracefully
        adapter = self.pipeline.process_item(item, spider=None)
        
        self.assertIn('error_detalle', adapter, "Database error should be captured in error_detalle")
        self.assertIn('database', adapter['error_detalle'].lower())
    
    @patch('scraper_core.utils.supabase_client.SupabaseClient.upload_to_storage')
    def test_process_item_storage_error(self, mock_upload):
        """Test handling of storage errors during HTML upload."""
        # Configure mock to raise an exception
        mock_upload.side_effect = Exception("Storage upload failed")
        
        item = self._get_sample_articulo_item()
        
        # Process should handle the error gracefully
        adapter = self.pipeline.process_item(item, spider=None)
        
        self.assertIn('error_detalle', adapter, "Storage error should be captured in error_detalle")
        self.assertIn('storage', adapter['error_detalle'].lower())
    
    def test_duplicate_article_handling(self):
        """Test handling of duplicate articles (same URL)."""
        item = self._get_sample_articulo_item()
        
        # Process the same item twice
        adapter1 = self.pipeline.process_item(item, spider=None)
        adapter2 = self.pipeline.process_item(item, spider=None)
        
        # Both should succeed (upsert should handle duplicates)
        self.assertIsNotNone(adapter1.get('storage_path'))
        self.assertIsNotNone(adapter2.get('storage_path'))
        
        # Verify only one record exists in database
        db_response = self.supabase_client.table('articulos').select('*').eq('url', item['url']).execute()
        self.assertEqual(len(db_response.data), 1, "Should only have one record for duplicate URL")

if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
