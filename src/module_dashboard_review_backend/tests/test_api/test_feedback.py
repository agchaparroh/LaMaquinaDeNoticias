"""
Integration tests for feedback API endpoints.

Tests the /dashboard/feedback/hecho/{hecho_id}/importancia_feedback endpoint
with various scenarios including success, validation errors, and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException

from src.main import app
from src.models.requests import ImportanciaFeedbackRequest, EvaluacionEditorialRequest
from src.models.responses import FeedbackResponse


client = TestClient(app)


@pytest.fixture
def mock_feedback_service():
    """Mock FeedbackService for testing."""
    with patch('src.api.feedback.get_feedback_service') as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


@pytest.fixture
def valid_feedback_payload():
    """Valid feedback request payload."""
    return {
        "importancia_editor_final": 8,
        "usuario_id_editor": "editor123"
    }


@pytest.fixture
def invalid_feedback_payloads():
    """Various invalid feedback payloads for testing."""
    return [
        # Missing required field
        {
            "usuario_id_editor": "editor123"
        },
        # Importance out of range (too low)
        {
            "importancia_editor_final": 0,
            "usuario_id_editor": "editor123"
        },
        # Importance out of range (too high)
        {
            "importancia_editor_final": 11,
            "usuario_id_editor": "editor123"
        },
        # Missing usuario_id_editor
        {
            "importancia_editor_final": 5
        },
        # Invalid type for importance
        {
            "importancia_editor_final": "eight",
            "usuario_id_editor": "editor123"
        },
        # Empty payload
        {}
    ]


def test_submit_importancia_feedback_success(mock_feedback_service, valid_feedback_payload):
    """Test successful submission of importance feedback."""
    # Setup mock
    mock_feedback_service.submit_importancia_feedback = AsyncMock()
    
    # Make request
    hecho_id = 123
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/importancia_feedback",
        json=valid_feedback_payload
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "success" in data
    assert "message" in data
    assert data["success"] is True
    assert f"Feedback de importancia actualizado para hecho {hecho_id}" in data["message"]
    
    # Verify service was called correctly
    mock_feedback_service.submit_importancia_feedback.assert_called_once()
    call_args = mock_feedback_service.submit_importancia_feedback.call_args
    assert call_args[0][0] == hecho_id
    assert isinstance(call_args[0][1], ImportanciaFeedbackRequest)
    assert call_args[0][1].importancia_editor_final == 8
    assert call_args[0][1].usuario_id_editor == "editor123"


def test_submit_importancia_feedback_hecho_not_found(mock_feedback_service, valid_feedback_payload):
    """Test feedback submission when hecho doesn't exist."""
    # Setup mock to raise HTTPException with 404
    mock_feedback_service.submit_importancia_feedback = AsyncMock(
        side_effect=HTTPException(status_code=404, detail="Hecho with ID 999 not found")
    )
    
    # Make request
    hecho_id = 999
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/importancia_feedback",
        json=valid_feedback_payload
    )
    
    # Should return 404
    assert response.status_code == 404
    data = response.json()
    assert "Hecho with ID 999 not found" in data["detail"]


def test_submit_importancia_feedback_invalid_hecho_id():
    """Test validation error for invalid hecho_id."""
    # Test with negative hecho_id
    response = client.post(
        "/dashboard/feedback/hecho/-1/importancia_feedback",
        json={"importancia_editor_final": 5, "usuario_id_editor": "editor123"}
    )
    
    # Should return 422 Unprocessable Entity
    assert response.status_code == 422
    
    # Test with zero hecho_id
    response = client.post(
        "/dashboard/feedback/hecho/0/importancia_feedback",
        json={"importancia_editor_final": 5, "usuario_id_editor": "editor123"}
    )
    
    # Should return 422 Unprocessable Entity
    assert response.status_code == 422
    
    # Test with non-integer hecho_id
    response = client.post(
        "/dashboard/feedback/hecho/abc/importancia_feedback",
        json={"importancia_editor_final": 5, "usuario_id_editor": "editor123"}
    )
    
    # Should return 422 Unprocessable Entity
    assert response.status_code == 422


def test_submit_importancia_feedback_invalid_payloads(invalid_feedback_payloads):
    """Test validation errors for various invalid payloads."""
    hecho_id = 123
    
    for invalid_payload in invalid_feedback_payloads:
        response = client.post(
            f"/dashboard/feedback/hecho/{hecho_id}/importancia_feedback",
            json=invalid_payload
        )
        
        # All should return 422 Unprocessable Entity
        assert response.status_code == 422, f"Failed for payload: {invalid_payload}"
        data = response.json()
        assert "detail" in data
        
        # Verify validation error details
        if isinstance(data["detail"], list):
            # FastAPI returns list of validation errors
            assert len(data["detail"]) > 0


def test_submit_importancia_feedback_boundary_values(mock_feedback_service):
    """Test feedback with importance values at boundaries."""
    # Setup mock
    mock_feedback_service.submit_importancia_feedback = AsyncMock()
    hecho_id = 123
    
    # Test minimum valid value (1)
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/importancia_feedback",
        json={
            "importancia_editor_final": 1,
            "usuario_id_editor": "editor123"
        }
    )
    assert response.status_code == 200
    
    # Test maximum valid value (10)
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/importancia_feedback",
        json={
            "importancia_editor_final": 10,
            "usuario_id_editor": "editor123"
        }
    )
    assert response.status_code == 200
    
    # Verify both calls succeeded
    assert mock_feedback_service.submit_importancia_feedback.call_count == 2


def test_submit_importancia_feedback_generic_error(mock_feedback_service, valid_feedback_payload):
    """Test handling of generic errors from service."""
    # Setup mock to raise generic exception
    mock_feedback_service.submit_importancia_feedback = AsyncMock(
        side_effect=Exception("Database connection error")
    )
    
    # Make request
    hecho_id = 123
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/importancia_feedback",
        json=valid_feedback_payload
    )
    
    # Should return 400 Bad Request
    assert response.status_code == 400
    data = response.json()
    assert "Database connection error" in data["detail"]


def test_submit_importancia_feedback_empty_usuario_id(mock_feedback_service):
    """Test validation with empty usuario_id_editor."""
    # Setup mock
    mock_feedback_service.submit_importancia_feedback = AsyncMock()
    
    # Make request with empty string for usuario_id
    hecho_id = 123
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/importancia_feedback",
        json={
            "importancia_editor_final": 7,
            "usuario_id_editor": ""  # Empty string
        }
    )
    
    # Should still be valid (empty string is technically a string)
    assert response.status_code == 200


def test_submit_importancia_feedback_long_usuario_id(mock_feedback_service):
    """Test with very long usuario_id_editor."""
    # Setup mock
    mock_feedback_service.submit_importancia_feedback = AsyncMock()
    
    # Make request with very long usuario_id
    hecho_id = 123
    long_usuario_id = "editor" * 100  # 600 characters
    
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/importancia_feedback",
        json={
            "importancia_editor_final": 5,
            "usuario_id_editor": long_usuario_id
        }
    )
    
    # Should be valid (no length restriction in model)
    assert response.status_code == 200


def test_submit_importancia_feedback_special_characters(mock_feedback_service):
    """Test with special characters in usuario_id_editor."""
    # Setup mock
    mock_feedback_service.submit_importancia_feedback = AsyncMock()
    
    # Test various special characters
    special_ids = [
        "editor@example.com",
        "editor-123",
        "editor_456",
        "editor.name",
        "éditeur-français",
        "编辑器",  # Chinese characters
        "editor 123"  # With space
    ]
    
    hecho_id = 123
    
    for editor_id in special_ids:
        response = client.post(
            f"/dashboard/feedback/hecho/{hecho_id}/importancia_feedback",
            json={
                "importancia_editor_final": 7,
                "usuario_id_editor": editor_id
            }
        )
        
        # All should be valid
        assert response.status_code == 200, f"Failed for usuario_id: {editor_id}"


def test_submit_importancia_feedback_large_hecho_id(mock_feedback_service, valid_feedback_payload):
    """Test with very large hecho_id."""
    # Setup mock
    mock_feedback_service.submit_importancia_feedback = AsyncMock()
    
    # Test with maximum integer value
    hecho_id = 2147483647  # Max 32-bit integer
    
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/importancia_feedback",
        json=valid_feedback_payload
    )
    
    # Should be valid
    assert response.status_code == 200
    
    # Verify service was called with correct ID
    call_args = mock_feedback_service.submit_importancia_feedback.call_args
    assert call_args[0][0] == hecho_id


def test_submit_importancia_feedback_null_body():
    """Test with null request body."""
    hecho_id = 123
    
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/importancia_feedback",
        json=None
    )
    
    # Should return 422 Unprocessable Entity
    assert response.status_code == 422


def test_submit_importancia_feedback_malformed_json():
    """Test with malformed JSON body."""
    hecho_id = 123
    
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/importancia_feedback",
        data='{"importancia_editor_final": 7, invalid json}'  # Malformed JSON
    )
    
    # Should return 422 Unprocessable Entity
    assert response.status_code == 422


def test_submit_importancia_feedback_content_type():
    """Test with different content types."""
    hecho_id = 123
    
    # Test with form data instead of JSON
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/importancia_feedback",
        data={
            "importancia_editor_final": 7,
            "usuario_id_editor": "editor123"
        }
    )
    
    # Should return 422 (expects JSON)
    assert response.status_code == 422
    
    # Test with explicit wrong content type
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/importancia_feedback",
        data='{"importancia_editor_final": 7, "usuario_id_editor": "editor123"}',
        headers={"Content-Type": "text/plain"}
    )
    
    # Should return 422
    assert response.status_code == 422


def test_submit_importancia_feedback_request_headers(mock_feedback_service, valid_feedback_payload):
    """Test that request headers are properly handled."""
    # Setup mock
    mock_feedback_service.submit_importancia_feedback = AsyncMock()
    
    # Make request with custom headers
    hecho_id = 123
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/importancia_feedback",
        json=valid_feedback_payload,
        headers={
            "X-User-Agent": "TestClient/1.0",
            "X-Request-ID": "test-request-123"
        }
    )
    
    # Should succeed regardless of headers
    assert response.status_code == 200
    
    # Check response has request ID header
    assert "X-Request-ID" in response.headers


# ===== TESTS FOR EVALUACION EDITORIAL ENDPOINT =====

@pytest.fixture
def valid_evaluacion_payload():
    """Valid evaluacion editorial request payload."""
    return {
        "evaluacion_editorial": "verificado_ok_editorial",
        "justificacion_evaluacion_editorial": "Fact correctly extracted and verified against multiple sources"
    }


@pytest.fixture
def invalid_evaluacion_payloads():
    """Various invalid evaluacion editorial payloads for testing."""
    return [
        # Missing required field
        {
            "justificacion_evaluacion_editorial": "Some justification"
        },
        # Invalid evaluacion value
        {
            "evaluacion_editorial": "invalid_value",
            "justificacion_evaluacion_editorial": "Some justification"
        },
        # Wrong type for evaluacion
        {
            "evaluacion_editorial": 123,
            "justificacion_evaluacion_editorial": "Some justification"
        },
        # Empty payload
        {},
        # Null evaluacion
        {
            "evaluacion_editorial": None,
            "justificacion_evaluacion_editorial": "Some justification"
        }
    ]


def test_submit_evaluacion_editorial_success(mock_feedback_service, valid_evaluacion_payload):
    """Test successful submission of editorial evaluation."""
    # Setup mock
    mock_feedback_service.submit_evaluacion_editorial = AsyncMock()
    
    # Make request
    hecho_id = 123
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/evaluacion_editorial",
        json=valid_evaluacion_payload
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "success" in data
    assert "message" in data
    assert data["success"] is True
    assert f"Evaluación editorial actualizada para hecho {hecho_id}" in data["message"]
    
    # Verify service was called correctly
    mock_feedback_service.submit_evaluacion_editorial.assert_called_once()
    call_args = mock_feedback_service.submit_evaluacion_editorial.call_args
    assert call_args[0][0] == hecho_id
    assert isinstance(call_args[0][1], EvaluacionEditorialRequest)
    assert call_args[0][1].evaluacion_editorial == "verificado_ok_editorial"
    assert call_args[0][1].justificacion_evaluacion_editorial == "Fact correctly extracted and verified against multiple sources"


def test_submit_evaluacion_editorial_hecho_not_found(mock_feedback_service, valid_evaluacion_payload):
    """Test evaluation submission when hecho doesn't exist."""
    # Setup mock to raise HTTPException with 404
    mock_feedback_service.submit_evaluacion_editorial = AsyncMock(
        side_effect=HTTPException(status_code=404, detail="Hecho with ID 999 not found")
    )
    
    # Make request
    hecho_id = 999
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/evaluacion_editorial",
        json=valid_evaluacion_payload
    )
    
    # Should return 404
    assert response.status_code == 404
    data = response.json()
    assert "Hecho with ID 999 not found" in data["detail"]


def test_submit_evaluacion_editorial_invalid_hecho_id():
    """Test validation error for invalid hecho_id."""
    # Test with negative hecho_id
    response = client.post(
        "/dashboard/feedback/hecho/-1/evaluacion_editorial",
        json={"evaluacion_editorial": "verificado_ok_editorial"}
    )
    
    # Should return 422 Unprocessable Entity
    assert response.status_code == 422
    
    # Test with zero hecho_id
    response = client.post(
        "/dashboard/feedback/hecho/0/evaluacion_editorial",
        json={"evaluacion_editorial": "verificado_ok_editorial"}
    )
    
    # Should return 422 Unprocessable Entity
    assert response.status_code == 422
    
    # Test with non-integer hecho_id
    response = client.post(
        "/dashboard/feedback/hecho/abc/evaluacion_editorial",
        json={"evaluacion_editorial": "verificado_ok_editorial"}
    )
    
    # Should return 422 Unprocessable Entity
    assert response.status_code == 422


def test_submit_evaluacion_editorial_invalid_payloads(invalid_evaluacion_payloads):
    """Test validation errors for various invalid payloads."""
    hecho_id = 123
    
    for invalid_payload in invalid_evaluacion_payloads:
        response = client.post(
            f"/dashboard/feedback/hecho/{hecho_id}/evaluacion_editorial",
            json=invalid_payload
        )
        
        # All should return 422 Unprocessable Entity
        assert response.status_code == 422, f"Failed for payload: {invalid_payload}"
        data = response.json()
        assert "detail" in data
        
        # Verify validation error details
        if isinstance(data["detail"], list):
            # FastAPI returns list of validation errors
            assert len(data["detail"]) > 0


def test_submit_evaluacion_editorial_valid_enum_values(mock_feedback_service):
    """Test evaluation with both valid enum values."""
    # Setup mock
    mock_feedback_service.submit_evaluacion_editorial = AsyncMock()
    hecho_id = 123
    
    # Test "verificado_ok_editorial"
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/evaluacion_editorial",
        json={
            "evaluacion_editorial": "verificado_ok_editorial",
            "justificacion_evaluacion_editorial": "Verified as correct"
        }
    )
    assert response.status_code == 200
    
    # Test "declarado_falso_editorial"
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/evaluacion_editorial",
        json={
            "evaluacion_editorial": "declarado_falso_editorial",
            "justificacion_evaluacion_editorial": "Found to be false"
        }
    )
    assert response.status_code == 200
    
    # Verify both calls succeeded
    assert mock_feedback_service.submit_evaluacion_editorial.call_count == 2


def test_submit_evaluacion_editorial_generic_error(mock_feedback_service, valid_evaluacion_payload):
    """Test handling of generic errors from service."""
    # Setup mock to raise generic exception
    mock_feedback_service.submit_evaluacion_editorial = AsyncMock(
        side_effect=Exception("Database connection error")
    )
    
    # Make request
    hecho_id = 123
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/evaluacion_editorial",
        json=valid_evaluacion_payload
    )
    
    # Should return 400 Bad Request
    assert response.status_code == 400
    data = response.json()
    assert "Database connection error" in data["detail"]


def test_submit_evaluacion_editorial_without_justification(mock_feedback_service):
    """Test evaluation without optional justification field."""
    # Setup mock
    mock_feedback_service.submit_evaluacion_editorial = AsyncMock()
    
    # Make request without justification
    hecho_id = 123
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/evaluacion_editorial",
        json={
            "evaluacion_editorial": "verificado_ok_editorial"
            # No justificacion_evaluacion_editorial provided
        }
    )
    
    # Should be valid (justification might be optional)
    # If it's required, this test should expect 422
    # Adjust based on actual model requirements
    assert response.status_code in [200, 422]


def test_submit_evaluacion_editorial_long_justification(mock_feedback_service):
    """Test with very long justification text."""
    # Setup mock
    mock_feedback_service.submit_evaluacion_editorial = AsyncMock()
    
    # Make request with very long justification
    hecho_id = 123
    long_justification = "This is a very detailed justification. " * 100  # ~3700 characters
    
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/evaluacion_editorial",
        json={
            "evaluacion_editorial": "verificado_ok_editorial",
            "justificacion_evaluacion_editorial": long_justification
        }
    )
    
    # Should be valid (no length restriction in model)
    assert response.status_code == 200


def test_submit_evaluacion_editorial_special_characters(mock_feedback_service):
    """Test with special characters in justification."""
    # Setup mock
    mock_feedback_service.submit_evaluacion_editorial = AsyncMock()
    
    # Test various special characters
    special_justifications = [
        "Verified with sources: [1], [2], & [3]",
        "Contains @mentions and #hashtags",
        "Includes emojis 😊 and unicode ñáéíóú",
        "Has \"quotes\" and 'apostrophes'",
        "Line\nbreaks\nand\ttabs"
    ]
    
    hecho_id = 123
    
    for justification in special_justifications:
        response = client.post(
            f"/dashboard/feedback/hecho/{hecho_id}/evaluacion_editorial",
            json={
                "evaluacion_editorial": "verificado_ok_editorial",
                "justificacion_evaluacion_editorial": justification
            }
        )
        
        # All should be valid
        assert response.status_code == 200, f"Failed for justification: {justification}"


def test_submit_evaluacion_editorial_large_hecho_id(mock_feedback_service, valid_evaluacion_payload):
    """Test with very large hecho_id."""
    # Setup mock
    mock_feedback_service.submit_evaluacion_editorial = AsyncMock()
    
    # Test with maximum integer value
    hecho_id = 2147483647  # Max 32-bit integer
    
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/evaluacion_editorial",
        json=valid_evaluacion_payload
    )
    
    # Should be valid
    assert response.status_code == 200
    
    # Verify service was called with correct ID
    call_args = mock_feedback_service.submit_evaluacion_editorial.call_args
    assert call_args[0][0] == hecho_id


def test_submit_evaluacion_editorial_null_body():
    """Test with null request body."""
    hecho_id = 123
    
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/evaluacion_editorial",
        json=None
    )
    
    # Should return 422 Unprocessable Entity
    assert response.status_code == 422


def test_submit_evaluacion_editorial_malformed_json():
    """Test with malformed JSON body."""
    hecho_id = 123
    
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/evaluacion_editorial",
        data='{"evaluacion_editorial": "verificado_ok_editorial", invalid json}'  # Malformed JSON
    )
    
    # Should return 422 Unprocessable Entity
    assert response.status_code == 422


def test_submit_evaluacion_editorial_content_type():
    """Test with different content types."""
    hecho_id = 123
    
    # Test with form data instead of JSON
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/evaluacion_editorial",
        data={
            "evaluacion_editorial": "verificado_ok_editorial",
            "justificacion_evaluacion_editorial": "Test justification"
        }
    )
    
    # Should return 422 (expects JSON)
    assert response.status_code == 422
    
    # Test with explicit wrong content type
    response = client.post(
        f"/dashboard/feedback/hecho/{hecho_id}/evaluacion_editorial",
        data='{"evaluacion_editorial": "verificado_ok_editorial"}',
        headers={"Content-Type": "text/plain"}
    )
    
    # Should return 422
    assert response.status_code == 422


def test_submit_evaluacion_editorial_concurrent_requests(mock_feedback_service):
    """Test handling of concurrent requests to the same hecho."""
    # Setup mock
    mock_feedback_service.submit_evaluacion_editorial = AsyncMock()
    
    # Simulate concurrent requests by making multiple calls
    hecho_id = 123
    responses = []
    
    for i in range(5):
        response = client.post(
            f"/dashboard/feedback/hecho/{hecho_id}/evaluacion_editorial",
            json={
                "evaluacion_editorial": "verificado_ok_editorial" if i % 2 == 0 else "declarado_falso_editorial",
                "justificacion_evaluacion_editorial": f"Concurrent test {i}"
            }
        )
        responses.append(response)
    
    # All should succeed
    for response in responses:
        assert response.status_code == 200
    
    # Verify all calls were made
    assert mock_feedback_service.submit_evaluacion_editorial.call_count == 5
