"""
Unit tests for exception handling system.

Tests custom exceptions, exception handlers, and error response formats
to ensure consistent error handling across the application.
"""

import pytest
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.main import app
from src.utils.exceptions import (
    BaseAPIException,
    DatabaseConnectionError,
    ResourceNotFoundError,
    ValidationError
)
from src.core.exceptions import (
    base_exception_handler,
    validation_exception_handler,
    general_exception_handler
)


# Test client for integration tests
client = TestClient(app)


class TestCustomExceptions:
    """Test suite for custom exception classes."""
    
    def test_base_api_exception_creation(self):
        """Test BaseAPIException initialization with status code and detail."""
        exc = BaseAPIException(status_code=400, detail="Test error")
        
        assert exc.status_code == 400
        assert exc.detail == "Test error"
        assert str(exc) == "Test error"
    
    def test_database_connection_error_defaults(self):
        """Test DatabaseConnectionError with default message."""
        exc = DatabaseConnectionError()
        
        assert exc.status_code == 503
        assert exc.detail == "Database connection error"
    
    def test_database_connection_error_custom_message(self):
        """Test DatabaseConnectionError with custom message."""
        custom_msg = "Connection timeout: All retry attempts exhausted"
        exc = DatabaseConnectionError(detail=custom_msg)
        
        assert exc.status_code == 503
        assert exc.detail == custom_msg
    
    def test_resource_not_found_error_defaults(self):
        """Test ResourceNotFoundError with default message."""
        exc = ResourceNotFoundError()
        
        assert exc.status_code == 404
        assert exc.detail == "Resource not found"
    
    def test_resource_not_found_error_custom_message(self):
        """Test ResourceNotFoundError with custom message."""
        custom_msg = "Hecho with ID 123 not found"
        exc = ResourceNotFoundError(detail=custom_msg)
        
        assert exc.status_code == 404
        assert exc.detail == custom_msg
    
    def test_validation_error_defaults(self):
        """Test ValidationError with default message."""
        exc = ValidationError()
        
        assert exc.status_code == 422
        assert exc.detail == "Validation error"
    
    def test_validation_error_custom_message(self):
        """Test ValidationError with custom message."""
        custom_msg = "Start date cannot be after end date"
        exc = ValidationError(detail=custom_msg)
        
        assert exc.status_code == 422
        assert exc.detail == custom_msg
    
    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from BaseAPIException."""
        assert issubclass(DatabaseConnectionError, BaseAPIException)
        assert issubclass(ResourceNotFoundError, BaseAPIException)
        assert issubclass(ValidationError, BaseAPIException)


class TestExceptionHandlers:
    """Test suite for exception handler functions."""
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = MagicMock(spec=Request)
        request.url.path = "/test/path"
        request.method = "GET"
        request.state.request_id = "test-request-123"
        return request
    
    @pytest.mark.asyncio
    async def test_base_exception_handler(self, mock_request):
        """Test base exception handler returns correct JSON response."""
        exc = DatabaseConnectionError("Test DB error")
        
        with patch('src.core.exceptions.logger') as mock_logger:
            response = await base_exception_handler(mock_request, exc)
            
            # Verify logging
            mock_logger.error.assert_called_once()
            log_call = mock_logger.error.call_args
            assert "API error: Test DB error" in log_call[0][0]
            assert log_call[1]['extra']['status_code'] == 503
            
            # Verify response
            assert response.status_code == 503
            assert response.body == b'{"error":"Test DB error"}'
    
    @pytest.mark.asyncio
    async def test_validation_exception_handler(self, mock_request):
        """Test validation exception handler returns detailed errors."""
        # Create mock validation error
        mock_errors = [
            {
                "loc": ["body", "field1"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
        
        exc = RequestValidationError(errors=mock_errors)
        exc.errors = MagicMock(return_value=mock_errors)
        
        with patch('src.core.exceptions.logger') as mock_logger:
            response = await validation_exception_handler(mock_request, exc)
            
            # Verify logging
            mock_logger.error.assert_called_once()
            
            # Verify response
            assert response.status_code == 422
            # Parse response body
            import json
            body = json.loads(response.body)
            assert body["error"] == "Validation error"
            assert body["details"] == mock_errors
    
    @pytest.mark.asyncio
    async def test_general_exception_handler(self, mock_request):
        """Test general exception handler for unhandled exceptions."""
        exc = RuntimeError("Unexpected error")
        
        with patch('src.core.exceptions.logger') as mock_logger:
            response = await general_exception_handler(mock_request, exc)
            
            # Verify logging with traceback
            mock_logger.error.assert_called_once()
            assert "Unhandled exception: Unexpected error" in mock_logger.error.call_args[0][0]
            assert mock_logger.error.call_args[1]['exc_info'] is True
            
            # Verify generic response (no sensitive details)
            assert response.status_code == 500
            assert response.body == b'{"error":"Internal server error"}'


class TestExceptionHandlerIntegration:
    """Integration tests for exception handlers with FastAPI app."""
    
    def test_custom_exception_handler_integration(self):
        """Test that custom exceptions are handled correctly by the app."""
        # Create a test endpoint that raises our custom exception
        @app.get("/test-exception")
        async def test_endpoint():
            raise ResourceNotFoundError("Test resource not found")
        
        response = client.get("/test-exception")
        
        assert response.status_code == 404
        assert response.json() == {"error": "Test resource not found"}
    
    def test_validation_error_integration(self):
        """Test request validation error handling."""
        # Use an existing endpoint that expects specific parameters
        # Send invalid data to trigger validation error
        response = client.get("/dashboard/hechos_revision", params={"limit": -1})
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data or "detail" in data  # FastAPI default validation
    
    def test_unhandled_exception_integration(self):
        """Test general exception handler for unexpected errors."""
        # Create a test endpoint that raises an unexpected exception
        @app.get("/test-unhandled")
        async def test_unhandled():
            raise RuntimeError("Unexpected error in endpoint")
        
        response = client.get("/test-unhandled")
        
        assert response.status_code == 500
        assert response.json() == {"error": "Internal server error"}
    
    def test_http_exception_still_works(self):
        """Test that standard HTTPException still works as expected."""
        from fastapi import HTTPException
        
        @app.get("/test-http-exception")
        async def test_http_exc():
            raise HTTPException(status_code=400, detail="Bad request test")
        
        response = client.get("/test-http-exception")
        
        assert response.status_code == 400
        assert response.json() == {"detail": "Bad request test"}


class TestErrorResponseFormat:
    """Test suite for verifying consistent error response formats."""
    
    def test_custom_exception_format(self):
        """Test that custom exceptions return consistent format."""
        @app.get("/test-format-custom")
        async def test_format():
            raise ValidationError("Invalid data format")
        
        response = client.get("/test-format-custom")
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert data["error"] == "Invalid data format"
        # Should not have 'detail' key (that's for HTTPException)
        assert "detail" not in data
    
    def test_multiple_exception_types(self):
        """Test different exception types return appropriate formats."""
        # Test DatabaseConnectionError
        @app.get("/test-db-error")
        async def test_db():
            raise DatabaseConnectionError("DB unavailable")
        
        response = client.get("/test-db-error")
        assert response.status_code == 503
        assert response.json() == {"error": "DB unavailable"}
        
        # Test ResourceNotFoundError
        @app.get("/test-not-found")
        async def test_not_found():
            raise ResourceNotFoundError("Item not found")
        
        response = client.get("/test-not-found")
        assert response.status_code == 404
        assert response.json() == {"error": "Item not found"}


class TestLoggingBehavior:
    """Test suite for verifying logging behavior in exception handlers."""
    
    @pytest.mark.asyncio
    async def test_request_context_logged(self):
        """Test that request context is included in error logs."""
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        request.method = "POST"
        request.state.request_id = "unique-id-123"
        
        exc = ValidationError("Test validation error")
        
        with patch('src.core.exceptions.logger') as mock_logger:
            await base_exception_handler(request, exc)
            
            log_extra = mock_logger.error.call_args[1]['extra']
            assert log_extra['path'] == "/api/test"
            assert log_extra['method'] == "POST"
            assert log_extra['request_id'] == "unique-id-123"
    
    @pytest.mark.asyncio
    async def test_missing_request_id_handled(self):
        """Test handler works even if request_id is missing."""
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        # Don't set request_id to simulate missing attribute
        request.state = MagicMock()
        del request.state.request_id
        
        exc = ResourceNotFoundError("Not found")
        
        with patch('src.core.exceptions.logger') as mock_logger:
            response = await base_exception_handler(request, exc)
            
            # Should still work and log None for request_id
            log_extra = mock_logger.error.call_args[1]['extra']
            assert log_extra['request_id'] is None
            assert response.status_code == 404
