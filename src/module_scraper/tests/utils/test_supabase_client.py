"""
Tests for SupabaseClient utility class.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import os
from scraper_core.utils.supabase_client import SupabaseClient, get_supabase_client, retry_on_failure


class TestSupabaseClient(unittest.TestCase):
    """Test cases for SupabaseClient class."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset singleton instance
        SupabaseClient._instance = None
        SupabaseClient._client = None
        
        # Set up environment variables
        os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
        os.environ['SUPABASE_KEY'] = 'test-key'
    
    def tearDown(self):
        """Clean up after tests."""
        # Reset singleton instance
        SupabaseClient._instance = None
        SupabaseClient._client = None
    
    @patch('scraper_core.utils.supabase_client.create_client')
    def test_singleton_pattern(self, mock_create_client):
        """Test that SupabaseClient follows singleton pattern."""
        mock_create_client.return_value = Mock()
        
        client1 = SupabaseClient()
        client2 = SupabaseClient()
        
        self.assertIs(client1, client2)
        mock_create_client.assert_called_once()
    
    @patch('scraper_core.utils.supabase_client.create_client')
    def test_client_initialization(self, mock_create_client):
        """Test proper client initialization with environment variables."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        client = SupabaseClient()
        
        mock_create_client.assert_called_once_with(
            'https://test.supabase.co',
            'test-key',
            unittest.mock.ANY
        )
        self.assertEqual(client._client, mock_client)
    
    def test_missing_environment_variables(self):
        """Test error handling when environment variables are missing."""
        # Remove environment variables
        del os.environ['SUPABASE_URL']
        
        with self.assertRaises(ValueError) as context:
            SupabaseClient()
        
        self.assertIn("SUPABASE_URL and SUPABASE_KEY must be set", str(context.exception))
    
    @patch('scraper_core.utils.supabase_client.create_client')
    def test_health_check_success(self, mock_create_client):
        """Test successful health check."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.execute.return_value = Mock(data=[{'id': 1}])
        mock_client.table.return_value.select.return_value.limit.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        client = SupabaseClient()
        result = client.health_check()
        
        self.assertTrue(result)
        mock_client.table.assert_called_with('articulos')
    
    @patch('scraper_core.utils.supabase_client.create_client')
    def test_health_check_failure(self, mock_create_client):
        """Test failed health check."""
        mock_client = Mock()
        mock_client.table.side_effect = Exception("Connection error")
        mock_create_client.return_value = mock_client
        
        client = SupabaseClient()
        result = client.health_check()
        
        self.assertFalse(result)
    
    @patch('scraper_core.utils.supabase_client.create_client')
    def test_insert_articulo_success(self, mock_create_client):
        """Test successful article insertion."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.execute.return_value = Mock(data=[{'id': 1, 'url': 'http://test.com'}])
        mock_client.table.return_value.insert.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        client = SupabaseClient()
        data = {'url': 'http://test.com', 'titulo': 'Test Article'}
        result = client.insert_articulo(data)
        
        self.assertEqual(result, {'id': 1, 'url': 'http://test.com'})
        mock_client.table.assert_called_with('articulos')
        mock_client.table.return_value.insert.assert_called_with(data)
    
    @patch('scraper_core.utils.supabase_client.create_client')
    def test_check_article_exists(self, mock_create_client):
        """Test checking if article exists."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.execute.return_value = Mock(data=[{'id': 1}])
        mock_client.table.return_value.select.return_value.eq.return_value = mock_response
        mock_create_client.return_value = mock_client
        
        client = SupabaseClient()
        exists = client.check_article_exists('http://test.com')
        
        self.assertTrue(exists)
        mock_client.table.assert_called_with('articulos')
    
    @patch('scraper_core.utils.supabase_client.create_client')
    def test_upload_to_storage(self, mock_create_client):
        """Test file upload to storage."""
        mock_client = Mock()
        mock_storage = Mock()
        mock_storage.from_.return_value.upload.return_value = {'path': 'test/file.gz'}
        mock_client.storage = mock_storage
        mock_create_client.return_value = mock_client
        
        client = SupabaseClient()
        result = client.upload_to_storage(
            'test-bucket',
            'test/file.gz',
            b'test content'
        )
        
        self.assertEqual(result, {'path': 'test/file.gz'})
        mock_storage.from_.assert_called_with('test-bucket')
    
    def test_retry_decorator(self):
        """Test retry decorator functionality."""
        attempt_count = 0
        
        @retry_on_failure(max_retries=2, delay=0.1, backoff=2.0)
        def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Test error")
            return "success"
        
        result = failing_function()
        
        self.assertEqual(result, "success")
        self.assertEqual(attempt_count, 3)
    
    def test_get_supabase_client(self):
        """Test convenience function for getting client instance."""
        with patch('scraper_core.utils.supabase_client.create_client'):
            client1 = get_supabase_client()
            client2 = get_supabase_client()
            
            self.assertIs(client1, client2)
            self.assertIsInstance(client1, SupabaseClient)


if __name__ == '__main__':
    unittest.main()
