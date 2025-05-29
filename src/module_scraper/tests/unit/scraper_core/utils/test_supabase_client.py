import unittest
import os
import logging
from unittest.mock import patch, MagicMock, mock_open

# Ensure the SupabaseClient can be imported
# This might require adjusting sys.path if tests are run from a different root
# For now, assuming standard Python module resolution from the project root or PYTHONPATH configured
from src.module_scraper.scraper_core.utils.supabase_client import SupabaseClient

# Disable logging for tests unless specifically testing logging output
logging.disable(logging.CRITICAL)

class TestSupabaseClient(unittest.TestCase):

    def setUp(self):
        """
        Common setup for all tests.
        Resets the SupabaseClient singleton instance before each test
        to ensure test isolation.
        """
        SupabaseClient._instance = None # Reset singleton instance

    @patch.dict(os.environ, {"SUPABASE_URL": "http://test.supabase.co", "SUPABASE_KEY": "test_key"})
    @patch('src.module_scraper.scraper_core.utils.supabase_client.create_client')
    def test_singleton_pattern(self, mock_create_client):
        """Test that SupabaseClient follows the singleton pattern."""
        mock_create_client.return_value = MagicMock()
        client1 = SupabaseClient()
        client2 = SupabaseClient()
        self.assertIs(client1, client2, "SupabaseClient should be a singleton.")
        self.assertTrue(client1._initialized, "Client should be initialized.")

    @patch.dict(os.environ, {"SUPABASE_URL": "http://test.supabase.co", "SUPABASE_KEY": "test_key"})
    @patch('src.module_scraper.scraper_core.utils.supabase_client.create_client')
    def test_initialization_success(self, mock_create_client):
        """Test successful initialization of SupabaseClient."""
        mock_supabase_client_instance = MagicMock()
        mock_create_client.return_value = mock_supabase_client_instance
        
        client = SupabaseClient()
        
        self.assertEqual(client.supabase_url, "http://test.supabase.co")
        self.assertEqual(client.supabase_key, "test_key")
        mock_create_client.assert_called_once_with("http://test.supabase.co", "test_key")
        self.assertIsNotNone(client.client, "Supabase internal client should be initialized.")
        self.assertTrue(client._initialized)

    @patch.dict(os.environ, {}, clear=True) # No env vars
    def test_initialization_failure_missing_env_vars(self):
        """Test initialization failure when environment variables are missing."""
        with self.assertRaisesRegex(ValueError, "Supabase URL and Key not found in environment variables."):
            SupabaseClient()

    @patch.dict(os.environ, {"SUPABASE_URL": "http://test.supabase.co", "SUPABASE_KEY": "test_key"})
    @patch('src.module_scraper.scraper_core.utils.supabase_client.create_client')
    def test_initialization_failure_create_client_exception(self, mock_create_client):
        """Test initialization failure if create_client raises an exception."""
        mock_create_client.side_effect = Exception("Connection failed")
        with self.assertRaisesRegex(Exception, "Connection failed"):
            SupabaseClient()

    @patch.dict(os.environ, {"SUPABASE_URL": "http://test.supabase.co", "SUPABASE_KEY": "test_key"})
    @patch('src.module_scraper.scraper_core.utils.supabase_client.create_client')
    def test_get_client_success(self, mock_create_client):
        """Test get_client returns the underlying client instance."""
        mock_internal_client = MagicMock()
        mock_create_client.return_value = mock_internal_client
        
        sc_instance = SupabaseClient()
        retrieved_client = sc_instance.get_client()
        
        self.assertIs(retrieved_client, mock_internal_client)

    def test_get_client_not_initialized(self):
        """Test get_client raises error if client not initialized (e.g., env vars missing)."""
        # Temporarily remove env vars to simulate failed init
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError): # Init fails
                 SupabaseClient()
            
            # Create an instance without proper init (for testing this specific path, though unusual)
            sc_instance = SupabaseClient.__new__(SupabaseClient) # Create instance without calling __init__
            sc_instance.client = None # Ensure client is None
            sc_instance.logger = MagicMock() # Mock logger to avoid errors on logger calls

            with self.assertRaisesRegex(ConnectionError, "Supabase client not initialized."):
                sc_instance.get_client()


    @patch.dict(os.environ, {"SUPABASE_URL": "http://test.supabase.co", "SUPABASE_KEY": "test_key"})
    @patch('src.module_scraper.scraper_core.utils.supabase_client.create_client')
    def test_upload_file_with_local_path_success(self, mock_create_client):
        """Test successful file upload using a local file path."""
        mock_storage_response = MagicMock()
        mock_storage_response.json.return_value = {"path": "test/file.txt"}
        
        mock_supabase_internal_client = MagicMock()
        mock_supabase_internal_client.storage.from_().upload.return_value = mock_storage_response
        mock_create_client.return_value = mock_supabase_internal_client

        client = SupabaseClient()
        
        with patch('builtins.open', mock_open(read_data=b"file content")) as mocked_file:
            result = client.upload_file("test_bucket", "test/file.txt", local_file_path="dummy/path.txt")
        
        mocked_file.assert_called_once_with("dummy/path.txt", 'rb')
        client.client.storage.from_("test_bucket").upload.assert_called_once()
        # More specific check on args if needed, e.g. using call_args
        self.assertEqual(result, {"path": "test/file.txt"})

    @patch.dict(os.environ, {"SUPABASE_URL": "http://test.supabase.co", "SUPABASE_KEY": "test_key"})
    @patch('src.module_scraper.scraper_core.utils.supabase_client.create_client')
    def test_upload_file_with_file_content_success(self, mock_create_client):
        """Test successful file upload using file content (bytes)."""
        mock_storage_response = MagicMock()
        mock_storage_response.json.return_value = {"path": "test/content.txt"}

        mock_supabase_internal_client = MagicMock()
        mock_supabase_internal_client.storage.from_().upload.return_value = mock_storage_response
        mock_create_client.return_value = mock_supabase_internal_client

        client = SupabaseClient()
        file_bytes = b"some binary content"
        file_options = {'content-type': 'text/plain'}
        
        result = client.upload_file(
            "test_bucket", 
            "test/content.txt", 
            file_content=file_bytes,
            file_options=file_options
        )
        
        client.client.storage.from_("test_bucket").upload.assert_called_once_with(
            path="test/content.txt",
            file=file_bytes,
            file_options=file_options
        )
        self.assertEqual(result, {"path": "test/content.txt"})

    @patch.dict(os.environ, {"SUPABASE_URL": "http://test.supabase.co", "SUPABASE_KEY": "test_key"})
    @patch('src.module_scraper.scraper_core.utils.supabase_client.create_client')
    def test_upload_file_no_source_provided(self, mock_create_client):
        """Test upload_file returns None if no file source is provided."""
        mock_create_client.return_value = MagicMock()
        client = SupabaseClient()
        with patch.object(client.logger, 'error') as mock_logger_error:
            result = client.upload_file("test_bucket", "test/path.txt")
            self.assertIsNone(result)
            mock_logger_error.assert_called_with("Either local_file_path or file_content must be provided for upload.")

    @patch.dict(os.environ, {"SUPABASE_URL": "http://test.supabase.co", "SUPABASE_KEY": "test_key"})
    @patch('src.module_scraper.scraper_core.utils.supabase_client.create_client')
    def test_upload_file_storage_exception(self, mock_create_client):
        """Test upload_file handles exceptions from Supabase storage."""
        mock_supabase_internal_client = MagicMock()
        mock_supabase_internal_client.storage.from_().upload.side_effect = Exception("Storage error")
        mock_create_client.return_value = mock_supabase_internal_client

        client = SupabaseClient()
        with patch.object(client.logger, 'error') as mock_logger_error:
            result = client.upload_file("test_bucket", "test/path.txt", file_content=b"data")
            self.assertIsNone(result)
            mock_logger_error.assert_called_with("Error uploading file to test_bucket/test/path.txt: Storage error")

    @patch.dict(os.environ, {"SUPABASE_URL": "http://test.supabase.co", "SUPABASE_KEY": "test_key"})
    @patch('src.module_scraper.scraper_core.utils.supabase_client.create_client')
    def test_insert_data_success(self, mock_create_client):
        """Test successful data insertion."""
        mock_insert_response = MagicMock()
        mock_insert_response.data = [{"id": 1, "name": "Test"}]
        
        mock_supabase_internal_client = MagicMock()
        mock_supabase_internal_client.table().insert().execute.return_value = mock_insert_response
        mock_create_client.return_value = mock_supabase_internal_client

        client = SupabaseClient()
        test_data = {"name": "Test"}
        result = client.insert_data("test_table", test_data)
        
        client.client.table("test_table").insert(test_data).execute.assert_called_once()
        self.assertEqual(result, [{"id": 1, "name": "Test"}])

    @patch.dict(os.environ, {"SUPABASE_URL": "http://test.supabase.co", "SUPABASE_KEY": "test_key"})
    @patch('src.module_scraper.scraper_core.utils.supabase_client.create_client')
    def test_insert_data_no_data_provided(self, mock_create_client):
        """Test insert_data returns None if no data is provided."""
        mock_create_client.return_value = MagicMock()
        client = SupabaseClient()
        with patch.object(client.logger, 'warning') as mock_logger_warning:
            result = client.insert_data("test_table", {}) # or None or []
            self.assertIsNone(result)
            mock_logger_warning.assert_called_with("No data provided for insertion into table test_table.")
            
            result_list = client.insert_data("test_table", [])
            self.assertIsNone(result_list)


    @patch.dict(os.environ, {"SUPABASE_URL": "http://test.supabase.co", "SUPABASE_KEY": "test_key"})
    @patch('src.module_scraper.scraper_core.utils.supabase_client.create_client')
    def test_insert_data_api_exception(self, mock_create_client):
        """Test insert_data handles exceptions from Supabase API."""
        mock_supabase_internal_client = MagicMock()
        mock_supabase_internal_client.table().insert().execute.side_effect = Exception("API error")
        mock_create_client.return_value = mock_supabase_internal_client

        client = SupabaseClient()
        with patch.object(client.logger, 'error') as mock_logger_error:
            result = client.insert_data("test_table", {"name": "Test"})
            self.assertIsNone(result)
            mock_logger_error.assert_called_with("Error inserting data into test_table: API error")

if __name__ == '__main__':
    logging.disable(logging.NOTSET) # Re-enable logging for direct script execution
    unittest.main()
