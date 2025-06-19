"""
Unit tests for the Supabase client service
Tests singleton pattern, retry logic, and helper methods
"""

import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import pytest
from supabase import Client

from services.supabase_client import SupabaseClient
from utils.exceptions import DatabaseConnectionError


@pytest.fixture(autouse=True)
def reset_client():
    """Reset the singleton client before each test."""
    SupabaseClient._client = None
    SupabaseClient._instance = None
    yield
    # Clean up after test
    SupabaseClient._client = None
    SupabaseClient._instance = None


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    mock_client = MagicMock(spec=Client)
    return mock_client


@pytest.fixture
def mock_create_client(mock_supabase_client):
    """Mock the create_client function from supabase module."""
    with patch('services.supabase_client.create_client') as mock:
        mock.return_value = mock_supabase_client
        yield mock


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('services.supabase_client.settings') as mock:
        mock.supabase_url = "https://test.supabase.co"
        mock.supabase_key = "test-key-123"
        yield mock


class TestSupabaseClientInitialization:
    """Test suite for Supabase client initialization."""
    
    def test_singleton_pattern(self, mock_create_client, mock_settings):
        """Test that SupabaseClient follows singleton pattern."""
        # Get client twice
        client1 = SupabaseClient.get_client()
        client2 = SupabaseClient.get_client()
        
        # Should be the same instance
        assert client1 is client2
        
        # create_client should only be called once
        mock_create_client.assert_called_once_with(
            supabase_url="https://test.supabase.co",
            supabase_key="test-key-123"
        )
    
    def test_successful_initialization(self, mock_create_client, mock_settings):
        """Test successful client initialization."""
        # Get client
        client = SupabaseClient.get_client()
        
        # Verify client is returned
        assert client is not None
        assert client == mock_create_client.return_value
    
    def test_initialization_with_missing_url(self, mock_settings):
        """Test initialization fails with missing URL."""
        # Set URL to empty
        mock_settings.supabase_url = ""
        
        # Should raise DatabaseConnectionError
        with pytest.raises(DatabaseConnectionError) as exc_info:
            SupabaseClient.get_client()
        
        assert "Invalid Supabase configuration" in str(exc_info.value)
    
    def test_initialization_with_missing_key(self, mock_settings):
        """Test initialization fails with missing key."""
        # Set key to empty
        mock_settings.supabase_key = ""
        
        # Should raise DatabaseConnectionError
        with pytest.raises(DatabaseConnectionError) as exc_info:
            SupabaseClient.get_client()
        
        assert "Invalid Supabase configuration" in str(exc_info.value)
    
    def test_initialization_with_connection_error(self, mock_settings):
        """Test initialization handles connection errors."""
        with patch('services.supabase_client.create_client') as mock:
            # Simulate connection error
            mock.side_effect = Exception("Connection failed")
            
            # Should raise DatabaseConnectionError
            with pytest.raises(DatabaseConnectionError) as exc_info:
                SupabaseClient.get_client()
            
            assert "Could not connect to Supabase" in str(exc_info.value)
            assert "Connection failed" in str(exc_info.value.detail)
    
    def test_reset_client(self, mock_create_client, mock_settings):
        """Test reset_client clears the singleton instance."""
        # Get client
        client1 = SupabaseClient.get_client()
        
        # Reset client
        SupabaseClient.reset_client()
        
        # Get client again - should create new instance
        client2 = SupabaseClient.get_client()
        
        # create_client should be called twice
        assert mock_create_client.call_count == 2


class TestRetryLogic:
    """Test suite for retry logic with exponential backoff."""
    
    @pytest.mark.asyncio
    async def test_successful_operation_no_retry(self):
        """Test successful operation doesn't retry."""
        # Mock successful operation
        mock_operation = AsyncMock(return_value="success")
        
        # Execute with retry
        result = await SupabaseClient.execute_with_retry(mock_operation, "arg1", kwarg="value")
        
        # Should return result
        assert result == "success"
        
        # Should only be called once
        mock_operation.assert_called_once_with("arg1", kwarg="value")
    
    @pytest.mark.asyncio
    async def test_sync_operation_with_retry(self):
        """Test sync operation can be executed with retry."""
        # Mock sync operation
        mock_operation = Mock(return_value="sync_result")
        
        # Execute with retry
        result = await SupabaseClient.execute_with_retry(mock_operation, "test")
        
        # Should return result
        assert result == "sync_result"
        mock_operation.assert_called_once_with("test")
    
    @pytest.mark.asyncio
    async def test_retry_on_failure_then_success(self):
        """Test operation retries on failure then succeeds."""
        # Mock operation that fails twice then succeeds
        mock_operation = AsyncMock(side_effect=[
            Exception("First failure"),
            Exception("Second failure"),
            "success"
        ])
        
        # Mock sleep to speed up test
        with patch('asyncio.sleep', new_callable=AsyncMock):
            # Execute with retry
            result = await SupabaseClient.execute_with_retry(mock_operation)
        
        # Should return result
        assert result == "success"
        
        # Should be called 3 times
        assert mock_operation.call_count == 3
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test operation fails after max retries."""
        # Mock operation that always fails
        mock_operation = AsyncMock(side_effect=Exception("Always fails"))
        
        # Mock sleep to speed up test
        with patch('asyncio.sleep', new_callable=AsyncMock):
            # Should raise the exception after max retries
            with pytest.raises(Exception) as exc_info:
                await SupabaseClient.execute_with_retry(mock_operation)
            
            assert "Always fails" in str(exc_info.value)
        
        # Should be called max_retries times
        assert mock_operation.call_count == SupabaseClient._max_retries
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_delays(self):
        """Test exponential backoff delays are applied correctly."""
        # Mock operation that always fails
        mock_operation = AsyncMock(side_effect=Exception("Fail"))
        
        # Track sleep calls
        sleep_calls = []
        
        async def mock_sleep(delay):
            sleep_calls.append(delay)
        
        with patch('asyncio.sleep', side_effect=mock_sleep):
            # Execute and expect failure
            with pytest.raises(Exception):
                await SupabaseClient.execute_with_retry(mock_operation)
        
        # Verify exponential backoff delays
        expected_delays = [
            SupabaseClient._base_delay * 1,  # First retry
            SupabaseClient._base_delay * 2,  # Second retry
        ]
        assert sleep_calls == expected_delays


class TestHelperMethods:
    """Test suite for helper methods."""
    
    @pytest.mark.asyncio
    async def test_select_with_pagination(self, mock_create_client, mock_settings):
        """Test select_with_pagination method."""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = [{"id": 1}, {"id": 2}]
        mock_result.count = 100
        
        # Setup mock query chain
        mock_query = Mock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = mock_result
        
        # Setup mock client
        mock_client = mock_create_client.return_value
        mock_client.table.return_value = mock_query
        
        # Execute query
        data, total = await SupabaseClient.select_with_pagination(
            table_name="hechos",
            columns="id,titulo",
            filters={"pais": "Argentina"},
            limit=10,
            offset=20,
            order_by="fecha",
            order_desc=True
        )
        
        # Verify results
        assert data == [{"id": 1}, {"id": 2}]
        assert total == 100
        
        # Verify query chain calls
        mock_client.table.assert_called_with("hechos")
        mock_query.select.assert_called_with("id,titulo", count='exact')
        mock_query.eq.assert_called_with("pais", "Argentina")
        mock_query.order.assert_called_with("fecha", desc=True)
        mock_query.range.assert_called_with(20, 29)
    
    @pytest.mark.asyncio
    async def test_get_single_record_found(self, mock_create_client, mock_settings):
        """Test get_single_record when record is found."""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = [{"id": 123, "titulo": "Test"}]
        
        # Setup mock query chain
        mock_query = Mock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_result
        
        # Setup mock client
        mock_client = mock_create_client.return_value
        mock_client.table.return_value = mock_query
        
        # Execute query
        record = await SupabaseClient.get_single_record(
            table_name="hechos",
            record_id=123
        )
        
        # Verify result
        assert record == {"id": 123, "titulo": "Test"}
        
        # Verify query chain
        mock_client.table.assert_called_with("hechos")
        mock_query.select.assert_called_with("*")
        mock_query.eq.assert_called_with("id", 123)
        mock_query.limit.assert_called_with(1)
    
    @pytest.mark.asyncio
    async def test_get_single_record_not_found(self, mock_create_client, mock_settings):
        """Test get_single_record when record is not found."""
        # Setup mock response with empty data
        mock_result = Mock()
        mock_result.data = []
        
        # Setup mock query chain
        mock_query = Mock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_result
        
        # Setup mock client
        mock_client = mock_create_client.return_value
        mock_client.table.return_value = mock_query
        
        # Execute query
        record = await SupabaseClient.get_single_record(
            table_name="hechos",
            record_id=999
        )
        
        # Should return None
        assert record is None
    
    @pytest.mark.asyncio
    async def test_update_record_success(self, mock_create_client, mock_settings):
        """Test update_record with successful update."""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = [{"id": 123, "status": "updated"}]
        
        # Setup mock query chain
        mock_query = Mock()
        mock_query.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_result
        
        # Setup mock client
        mock_client = mock_create_client.return_value
        mock_client.table.return_value = mock_query
        
        # Execute update
        result = await SupabaseClient.update_record(
            table_name="hechos",
            record_id=123,
            data={"status": "updated"}
        )
        
        # Verify result
        assert result == {"id": 123, "status": "updated"}
        
        # Verify query chain
        mock_client.table.assert_called_with("hechos")
        mock_query.update.assert_called_with({"status": "updated"})
        mock_query.eq.assert_called_with("id", 123)
    
    @pytest.mark.asyncio
    async def test_update_record_failure(self, mock_create_client, mock_settings):
        """Test update_record when update fails."""
        # Setup mock response with empty data
        mock_result = Mock()
        mock_result.data = []
        
        # Setup mock query chain
        mock_query = Mock()
        mock_query.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_result
        
        # Setup mock client
        mock_client = mock_create_client.return_value
        mock_client.table.return_value = mock_query
        
        # Should raise exception
        with pytest.raises(Exception) as exc_info:
            await SupabaseClient.update_record(
                table_name="hechos",
                record_id=999,
                data={"status": "updated"}
            )
        
        assert "Failed to update record 999" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_count_records_with_filters(self, mock_create_client, mock_settings):
        """Test count_records with filters."""
        # Setup mock response
        mock_result = Mock()
        mock_result.count = 42
        
        # Setup mock query chain
        mock_query = Mock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_result
        
        # Setup mock client
        mock_client = mock_create_client.return_value
        mock_client.table.return_value = mock_query
        
        # Execute count
        count = await SupabaseClient.count_records(
            table_name="hechos",
            filters={"pais": "Mexico", "importancia": 8}
        )
        
        # Verify result
        assert count == 42
        
        # Verify query chain
        mock_client.table.assert_called_with("hechos")
        mock_query.select.assert_called_with('id', count='exact')
        # eq should be called twice for two filters
        assert mock_query.eq.call_count == 2
    
    @pytest.mark.asyncio
    async def test_count_records_without_filters(self, mock_create_client, mock_settings):
        """Test count_records without filters."""
        # Setup mock response
        mock_result = Mock()
        mock_result.count = 1000
        
        # Setup mock query chain
        mock_query = Mock()
        mock_query.select.return_value = mock_query
        mock_query.execute.return_value = mock_result
        
        # Setup mock client
        mock_client = mock_create_client.return_value
        mock_client.table.return_value = mock_query
        
        # Execute count
        count = await SupabaseClient.count_records(
            table_name="hechos"
        )
        
        # Verify result
        assert count == 1000
        
        # Verify eq was not called (no filters)
        mock_query.eq.assert_not_called()


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple features."""
    
    @pytest.mark.asyncio
    async def test_retry_with_helper_method(self, mock_create_client, mock_settings):
        """Test that helper methods use retry logic correctly."""
        # Setup mock that fails once then succeeds
        mock_result = Mock()
        mock_result.data = [{"id": 1}]
        mock_result.count = 1
        
        mock_query = Mock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.side_effect = [
            Exception("Temporary failure"),
            mock_result
        ]
        
        mock_client = mock_create_client.return_value
        mock_client.table.return_value = mock_query
        
        # Mock sleep to speed up test
        with patch('asyncio.sleep', new_callable=AsyncMock):
            # Should succeed after retry
            record = await SupabaseClient.get_single_record(
                table_name="test",
                record_id=1
            )
        
        assert record == {"id": 1}
        # execute should be called twice due to retry
        assert mock_query.execute.call_count == 2


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_retry_with_different_exception_types(self):
        """Test retry handles different types of exceptions."""
        # Mock operation that raises different exceptions
        mock_operation = AsyncMock(side_effect=[
            ConnectionError("Network error"),
            TimeoutError("Request timeout"),
            ValueError("Invalid value"),
            "success"
        ])
        
        # Mock sleep to speed up test
        with patch('asyncio.sleep', new_callable=AsyncMock):
            # Should succeed after multiple different exceptions
            result = await SupabaseClient.execute_with_retry(mock_operation)
        
        assert result == "success"
        assert mock_operation.call_count == 4
    
    @pytest.mark.asyncio
    async def test_select_with_pagination_edge_cases(self, mock_create_client, mock_settings):
        """Test select_with_pagination with edge case parameters."""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = []
        mock_result.count = 0
        
        # Setup mock query chain
        mock_query = Mock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = mock_result
        
        # Setup mock client
        mock_client = mock_create_client.return_value
        mock_client.table.return_value = mock_query
        
        # Test with zero limit (should still work)
        data, total = await SupabaseClient.select_with_pagination(
            table_name="hechos",
            limit=0,
            offset=0
        )
        
        assert data == []
        assert total == 0
        # range should be called with (-1, -1) for limit=0
        mock_query.range.assert_called_with(0, -1)
        
        # Reset mock
        mock_query.reset_mock()
        
        # Test with very large offset
        data, total = await SupabaseClient.select_with_pagination(
            table_name="hechos",
            limit=10,
            offset=1000000
        )
        
        assert data == []
        assert total == 0
        mock_query.range.assert_called_with(1000000, 1000009)
    
    @pytest.mark.asyncio
    async def test_count_records_with_none_filters(self, mock_create_client, mock_settings):
        """Test count_records ignores None values in filters."""
        # Setup mock response
        mock_result = Mock()
        mock_result.count = 25
        
        # Setup mock query chain
        mock_query = Mock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_result
        
        # Setup mock client
        mock_client = mock_create_client.return_value
        mock_client.table.return_value = mock_query
        
        # Execute count with mixed None and valid filters
        count = await SupabaseClient.count_records(
            table_name="hechos",
            filters={"pais": "Chile", "tipo": None, "importancia": 8}
        )
        
        assert count == 25
        # eq should only be called for non-None values
        assert mock_query.eq.call_count == 2
        mock_query.eq.assert_any_call("pais", "Chile")
        mock_query.eq.assert_any_call("importancia", 8)
    
    def test_singleton_thread_safety(self, mock_create_client, mock_settings):
        """Test singleton pattern is thread-safe."""
        import threading
        import concurrent.futures
        
        clients = []
        
        def get_client_in_thread():
            client = SupabaseClient.get_client()
            clients.append(client)
        
        # Create multiple threads trying to get client simultaneously
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_client_in_thread) for _ in range(10)]
            concurrent.futures.wait(futures)
        
        # All clients should be the same instance
        assert len(clients) == 10
        assert all(client is clients[0] for client in clients)
        
        # create_client should still only be called once
        mock_create_client.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_preserves_args_kwargs(self):
        """Test that retry logic preserves original args and kwargs."""
        call_args = []
        
        async def mock_operation(*args, **kwargs):
            call_args.append((args, kwargs))
            if len(call_args) < 3:
                raise Exception("Fail")
            return "success"
        
        # Mock sleep to speed up test
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await SupabaseClient.execute_with_retry(
                mock_operation,
                "arg1", "arg2",
                kwarg1="value1", kwarg2="value2"
            )
        
        assert result == "success"
        assert len(call_args) == 3
        
        # All calls should have the same args and kwargs
        for args, kwargs in call_args:
            assert args == ("arg1", "arg2")
            assert kwargs == {"kwarg1": "value1", "kwarg2": "value2"}
    
    @pytest.mark.asyncio
    async def test_update_record_with_custom_id_column(self, mock_create_client, mock_settings):
        """Test update_record with custom ID column name."""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = [{"uuid": "123-456", "name": "Updated"}]
        
        # Setup mock query chain
        mock_query = Mock()
        mock_query.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_result
        
        # Setup mock client
        mock_client = mock_create_client.return_value
        mock_client.table.return_value = mock_query
        
        # Execute update with custom ID column
        result = await SupabaseClient.update_record(
            table_name="custom_table",
            record_id="123-456",
            data={"name": "Updated"},
            id_column="uuid"
        )
        
        assert result == {"uuid": "123-456", "name": "Updated"}
        mock_query.eq.assert_called_with("uuid", "123-456")
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_runtime_error(self):
        """Test execute_with_retry raises RuntimeError in edge case."""
        # This tests the edge case where last_exception is None
        # (which should never happen in practice)
        
        # Create a custom mock that manipulates the retry logic
        original_max_retries = SupabaseClient._max_retries
        SupabaseClient._max_retries = 0  # Force immediate exit
        
        try:
            # Mock operation that would normally fail
            mock_operation = AsyncMock(side_effect=Exception("Should not be called"))
            
            # This should raise RuntimeError due to the edge case
            with pytest.raises(RuntimeError) as exc_info:
                await SupabaseClient.execute_with_retry(mock_operation)
            
            assert "Unexpected error in retry logic" in str(exc_info.value)
        finally:
            # Restore original value
            SupabaseClient._max_retries = original_max_retries
    
    @pytest.mark.asyncio
    async def test_get_single_record_with_special_characters(self, mock_create_client, mock_settings):
        """Test get_single_record handles IDs with special characters."""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = [{"id": "test@example.com", "type": "email"}]
        
        # Setup mock query chain
        mock_query = Mock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_result
        
        # Setup mock client
        mock_client = mock_create_client.return_value
        mock_client.table.return_value = mock_query
        
        # Execute with email as ID
        record = await SupabaseClient.get_single_record(
            table_name="users",
            record_id="test@example.com",
            columns="id,type"
        )
        
        assert record == {"id": "test@example.com", "type": "email"}
        mock_query.eq.assert_called_with("id", "test@example.com")
        mock_query.select.assert_called_with("id,type")
    
    @pytest.mark.asyncio
    async def test_select_with_pagination_without_ordering(self, mock_create_client, mock_settings):
        """Test select_with_pagination works without order_by parameter."""
        # Setup mock response
        mock_result = Mock()
        mock_result.data = [{"id": 1}, {"id": 2}]
        mock_result.count = 2
        
        # Setup mock query chain
        mock_query = Mock()
        mock_query.select.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = mock_result
        
        # Setup mock client
        mock_client = mock_create_client.return_value
        mock_client.table.return_value = mock_query
        
        # Execute without order_by
        data, total = await SupabaseClient.select_with_pagination(
            table_name="test_table",
            limit=10,
            offset=0,
            order_by=None  # Explicitly set to None
        )
        
        assert data == [{"id": 1}, {"id": 2}]
        assert total == 2
        
        # order should not be called
        mock_query.order.assert_not_called()
