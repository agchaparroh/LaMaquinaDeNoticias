"""
Tests for health check endpoints
"""

import time
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.main import app, START_TIME


# Create test client
client = TestClient(app)


class TestHealthEndpoints:
    """Test suite for health check endpoints."""
    
    def test_health_endpoint(self):
        """Test the basic health endpoint returns 200 and correct structure."""
        response = client.get("/health")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"
    
    @patch('src.services.supabase_client.SupabaseClient.get_client')
    @patch('src.services.supabase_client.SupabaseClient.execute_with_retry')
    def test_detailed_health_endpoint_success(self, mock_execute_retry, mock_get_client):
        """Test the detailed health endpoint with successful dependency checks."""
        # Mock successful Supabase response
        mock_execute_retry.return_value = MagicMock()
        
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Check basic fields
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"
        
        # Check dependencies
        assert "dependencies" in data
        assert "supabase" in data["dependencies"]
        assert data["dependencies"]["supabase"]["status"] == "ok"
        assert "response_time_ms" in data["dependencies"]["supabase"]
        assert isinstance(data["dependencies"]["supabase"]["response_time_ms"], float)
        
        # Check uptime
        assert "uptime" in data
        assert isinstance(data["uptime"], float)
        assert data["uptime"] >= 0
    
    @patch('src.services.supabase_client.SupabaseClient.get_client')
    @patch('src.services.supabase_client.SupabaseClient.execute_with_retry')
    def test_detailed_health_endpoint_degraded(self, mock_execute_retry, mock_get_client):
        """Test the detailed health endpoint when Supabase is down."""
        # Mock Supabase client to raise exception
        mock_execute_retry.side_effect = Exception("Connection error")
        
        response = client.get("/health/detailed")
        
        # Still returns 200 even when degraded
        assert response.status_code == 200
        
        data = response.json()
        
        # Check status is degraded
        assert data["status"] == "degraded"
        assert data["version"] == "1.0.0"
        
        # Check Supabase error details
        assert data["dependencies"]["supabase"]["status"] == "error"
        assert "error" in data["dependencies"]["supabase"]
        assert data["dependencies"]["supabase"]["error"] == "Connection error"
    
    @patch('src.services.supabase_client.SupabaseClient.get_client')
    @patch('src.services.supabase_client.SupabaseClient.execute_with_retry')
    def test_supabase_health_check_timing(self, mock_execute_retry, mock_get_client):
        """Test that response time is calculated correctly."""
        # Mock delay in execute
        async def delayed_execute(*args, **kwargs):
            time.sleep(0.1)  # 100ms delay
            return MagicMock()
        
        mock_execute_retry.side_effect = delayed_execute
        
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        
        data = response.json()
        response_time = data["dependencies"]["supabase"]["response_time_ms"]
        
        # Response time should be at least 100ms due to our delay
        assert response_time >= 100.0
    
    def test_health_response_schema(self):
        """Test that health endpoint response matches expected schema."""
        response = client.get("/health")
        
        assert response.status_code == 200
        
        # Check response headers indicate JSON
        assert response.headers["content-type"] == "application/json"
        
        # Validate schema
        data = response.json()
        assert set(data.keys()) == {"status", "version"}
        assert isinstance(data["status"], str)
        assert isinstance(data["version"], str)
    
    def test_detailed_health_response_schema(self):
        """Test that detailed health endpoint response matches expected schema."""
        with patch('src.services.supabase_client.SupabaseClient.get_client'):
            with patch('src.services.supabase_client.SupabaseClient.execute_with_retry'):
                response = client.get("/health/detailed")
        
        assert response.status_code == 200
        
        # Validate schema
        data = response.json()
        assert set(data.keys()) == {"status", "version", "dependencies", "uptime"}
        assert isinstance(data["status"], str)
        assert isinstance(data["version"], str)
        assert isinstance(data["dependencies"], dict)
        assert isinstance(data["uptime"], float)
    
    @patch('src.services.supabase_client.SupabaseClient._initialize_client')
    def test_health_check_with_uninitialized_client(self, mock_initialize):
        """Test health check when Supabase client needs initialization."""
        # Mock successful initialization
        mock_initialize.return_value = None
        
        # Reset client to force initialization
        with patch('src.services.supabase_client.SupabaseClient._client', None):
            response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still work after initialization
        assert data["status"] in ["ok", "degraded"]
    
    def test_uptime_calculation(self):
        """Test that uptime is calculated correctly from START_TIME."""
        # Get current time and calculate expected uptime
        current_time = time.time()
        expected_min_uptime = current_time - START_TIME
        
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        
        data = response.json()
        actual_uptime = data["uptime"]
        
        # Uptime should be at least the minimum we calculated
        # and not more than a second more (to account for test execution time)
        assert actual_uptime >= expected_min_uptime
        assert actual_uptime <= expected_min_uptime + 1.0


class TestHealthCheckFunction:
    """Test the check_supabase_health function directly."""
    
    @pytest.mark.asyncio
    @patch('src.services.supabase_client.SupabaseClient.get_client')
    @patch('src.services.supabase_client.SupabaseClient.execute_with_retry')
    async def test_check_supabase_health_success(self, mock_execute_retry, mock_get_client):
        """Test successful Supabase health check."""
        from src.api.health import check_supabase_health
        
        # Mock successful response
        mock_execute_retry.return_value = MagicMock()
        
        result = await check_supabase_health()
        
        assert result["status"] == "ok"
        assert "response_time_ms" in result
        assert isinstance(result["response_time_ms"], float)
        assert result["response_time_ms"] >= 0
    
    @pytest.mark.asyncio
    @patch('src.services.supabase_client.SupabaseClient.get_client')
    @patch('src.services.supabase_client.SupabaseClient.execute_with_retry')
    async def test_check_supabase_health_error(self, mock_execute_retry, mock_get_client):
        """Test Supabase health check with error."""
        from src.api.health import check_supabase_health
        
        # Mock error
        mock_execute_retry.side_effect = Exception("Database connection failed")
        
        result = await check_supabase_health()
        
        assert result["status"] == "error"
        assert result["error"] == "Database connection failed"
        assert "response_time_ms" not in result
