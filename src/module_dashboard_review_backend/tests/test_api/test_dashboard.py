"""
Integration tests for dashboard API endpoints.

Tests the /dashboard/hechos_revision endpoint with various filter combinations,
pagination scenarios, and error conditions.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from src.main import app
from src.utils.exceptions import DatabaseConnectionError


client = TestClient(app)


@pytest.fixture
def mock_hechos_service():
    """Mock HechosService for testing."""
    with patch('src.api.dashboard.get_hechos_service') as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


@pytest.fixture
def sample_hechos_response():
    """Sample formatted hechos data for API responses."""
    return [
        {
            "id": 1,
            "contenido": "Presidente anuncia nuevas medidas económicas",
            "fecha_ocurrencia": "2024-01-15T10:30:00",
            "importancia": 9,
            "tipo_hecho": "declaracion",
            "pais": "Argentina",
            "evaluacion_editorial": None,
            "consenso_fuentes": 5,
            "articulo_metadata": {
                "medio": "La Nacion",
                "titular": "Presidente presenta plan económico",
                "fecha_publicacion": "2024-01-15T12:00:00",
                "url": "https://lanacion.com/economia/1234"
            }
        },
        {
            "id": 2,
            "contenido": "Inflación mensual alcanza el 4.2%",
            "fecha_ocurrencia": "2024-01-10T00:00:00",
            "importancia": 8,
            "tipo_hecho": "estadistica",
            "pais": "Argentina",
            "evaluacion_editorial": "verificado_ok_editorial",
            "consenso_fuentes": 8,
            "articulo_metadata": {
                "medio": "Clarin",
                "titular": "INDEC publica datos de inflación",
                "fecha_publicacion": "2024-01-10T09:00:00",
                "url": "https://clarin.com/economia/5678"
            }
        }
    ]


def test_get_hechos_revision_success(mock_hechos_service, sample_hechos_response):
    """Test successful retrieval of hechos with default pagination."""
    # Setup mock
    mock_hechos_service.get_hechos_for_revision = AsyncMock(
        return_value=(sample_hechos_response, 2)
    )
    
    # Make request
    response = client.get("/dashboard/hechos_revision")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "items" in data
    assert "pagination" in data
    
    # Check items
    assert len(data["items"]) == 2
    assert data["items"][0]["contenido"] == "Presidente anuncia nuevas medidas económicas"
    
    # Check pagination metadata
    pagination = data["pagination"]
    assert pagination["total_items"] == 2
    assert pagination["page"] == 1
    assert pagination["per_page"] == 20
    assert pagination["total_pages"] == 1
    assert pagination["has_next"] is False
    assert pagination["has_prev"] is False
    
    # Verify service was called with correct params
    mock_hechos_service.get_hechos_for_revision.assert_called_once()
    call_args = mock_hechos_service.get_hechos_for_revision.call_args[0][0]
    assert call_args["limit"] == 20
    assert call_args["offset"] == 0


def test_get_hechos_revision_with_all_filters(mock_hechos_service):
    """Test retrieval with all filter parameters."""
    # Setup mock
    mock_hechos_service.get_hechos_for_revision = AsyncMock(
        return_value=([], 0)
    )
    
    # Make request with all filters
    params = {
        "fecha_inicio": "2024-01-01T00:00:00",
        "fecha_fin": "2024-12-31T23:59:59",
        "medio": "La Nacion",
        "pais_publicacion": "Argentina",
        "importancia_min": 5,
        "importancia_max": 10,
        "limit": 50,
        "offset": 100
    }
    
    response = client.get("/dashboard/hechos_revision", params=params)
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0
    assert data["pagination"]["total_items"] == 0
    
    # Verify service was called with all filters
    mock_hechos_service.get_hechos_for_revision.assert_called_once()
    call_args = mock_hechos_service.get_hechos_for_revision.call_args[0][0]
    
    assert call_args["fecha_inicio"] == datetime(2024, 1, 1, 0, 0, 0)
    assert call_args["fecha_fin"] == datetime(2024, 12, 31, 23, 59, 59)
    assert call_args["medio"] == "La Nacion"
    assert call_args["pais_publicacion"] == "Argentina"
    assert call_args["importancia_min"] == 5
    assert call_args["importancia_max"] == 10
    assert call_args["limit"] == 50
    assert call_args["offset"] == 100


def test_get_hechos_revision_invalid_importance_range(mock_hechos_service):
    """Test validation error when importancia_min > importancia_max."""
    # Make request with invalid range
    params = {
        "importancia_min": 8,
        "importancia_max": 3  # Invalid: less than min
    }
    
    response = client.get("/dashboard/hechos_revision", params=params)
    
    # Should return 400 Bad Request
    assert response.status_code == 400
    data = response.json()
    assert "importancia_min must be less than or equal to importancia_max" in data["detail"]
    
    # Service should not be called
    mock_hechos_service.get_hechos_for_revision.assert_not_called()


def test_get_hechos_revision_invalid_parameter_values():
    """Test validation errors for invalid parameter values."""
    # Test negative offset
    response = client.get("/dashboard/hechos_revision", params={"offset": -1})
    assert response.status_code == 422
    
    # Test limit too high
    response = client.get("/dashboard/hechos_revision", params={"limit": 101})
    assert response.status_code == 422
    
    # Test limit too low
    response = client.get("/dashboard/hechos_revision", params={"limit": 0})
    assert response.status_code == 422
    
    # Test importance out of range
    response = client.get("/dashboard/hechos_revision", params={"importancia_min": 11})
    assert response.status_code == 422
    
    response = client.get("/dashboard/hechos_revision", params={"importancia_max": 0})
    assert response.status_code == 422


def test_get_hechos_revision_pagination_calculations(mock_hechos_service):
    """Test correct pagination metadata calculations."""
    # Test page 3 of results
    mock_hechos_service.get_hechos_for_revision = AsyncMock(
        return_value=([], 150)  # Total 150 items
    )
    
    params = {
        "limit": 20,
        "offset": 40  # Page 3 (0-19, 20-39, 40-59)
    }
    
    response = client.get("/dashboard/hechos_revision", params=params)
    
    assert response.status_code == 200
    data = response.json()
    
    pagination = data["pagination"]
    assert pagination["total_items"] == 150
    assert pagination["page"] == 3
    assert pagination["per_page"] == 20
    assert pagination["total_pages"] == 8  # 150/20 = 7.5, rounded up to 8
    assert pagination["has_next"] is True
    assert pagination["has_prev"] is True


def test_get_hechos_revision_last_page(mock_hechos_service):
    """Test pagination on the last page."""
    # 50 items total, page size 20, requesting page 3 (last page)
    mock_hechos_service.get_hechos_for_revision = AsyncMock(
        return_value=([], 50)
    )
    
    params = {
        "limit": 20,
        "offset": 40  # Last page with 10 items
    }
    
    response = client.get("/dashboard/hechos_revision", params=params)
    
    assert response.status_code == 200
    data = response.json()
    
    pagination = data["pagination"]
    assert pagination["page"] == 3
    assert pagination["total_pages"] == 3
    assert pagination["has_next"] is False
    assert pagination["has_prev"] is True


def test_get_hechos_revision_database_error(mock_hechos_service):
    """Test handling of database connection errors."""
    # Setup mock to raise DatabaseConnectionError
    mock_hechos_service.get_hechos_for_revision = AsyncMock(
        side_effect=DatabaseConnectionError("Cannot connect to database")
    )
    
    response = client.get("/dashboard/hechos_revision")
    
    # Should return 500 Internal Server Error
    assert response.status_code == 500
    data = response.json()
    assert "Internal server error" in data["detail"]


def test_get_hechos_revision_unexpected_error(mock_hechos_service):
    """Test handling of unexpected errors."""
    # Setup mock to raise generic exception
    mock_hechos_service.get_hechos_for_revision = AsyncMock(
        side_effect=RuntimeError("Unexpected error occurred")
    )
    
    response = client.get("/dashboard/hechos_revision")
    
    # Should return 500 Internal Server Error
    assert response.status_code == 500
    data = response.json()
    assert "Internal server error" in data["detail"]


def test_get_hechos_revision_empty_results(mock_hechos_service):
    """Test response when no hechos match the filters."""
    # Setup mock to return empty results
    mock_hechos_service.get_hechos_for_revision = AsyncMock(
        return_value=([], 0)
    )
    
    response = client.get("/dashboard/hechos_revision")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["items"]) == 0
    assert data["pagination"]["total_items"] == 0
    assert data["pagination"]["total_pages"] == 0
    assert data["pagination"]["has_next"] is False
    assert data["pagination"]["has_prev"] is False


def test_get_hechos_revision_date_parsing():
    """Test that date parameters are correctly parsed."""
    with patch('src.api.dashboard.get_hechos_service') as mock_get_service:
        service = MagicMock()
        service.get_hechos_for_revision = AsyncMock(return_value=([], 0))
        mock_get_service.return_value = service
        
        # Test various date formats
        params = {
            "fecha_inicio": "2024-01-15",  # Date only
            "fecha_fin": "2024-01-31T23:59:59"  # Date with time
        }
        
        response = client.get("/dashboard/hechos_revision", params=params)
        
        assert response.status_code == 200
        
        # Verify dates were parsed correctly
        call_args = service.get_hechos_for_revision.call_args[0][0]
        assert isinstance(call_args["fecha_inicio"], datetime)
        assert isinstance(call_args["fecha_fin"], datetime)
        assert call_args["fecha_inicio"] == datetime(2024, 1, 15, 0, 0, 0)
        assert call_args["fecha_fin"] == datetime(2024, 1, 31, 23, 59, 59)


def test_get_hechos_revision_special_characters_in_filters(mock_hechos_service):
    """Test handling of special characters in string filters."""
    # Setup mock
    mock_hechos_service.get_hechos_for_revision = AsyncMock(
        return_value=([], 0)
    )
    
    # Test with special characters
    params = {
        "medio": "El País (España)",
        "pais_publicacion": "São Paulo"
    }
    
    response = client.get("/dashboard/hechos_revision", params=params)
    
    assert response.status_code == 200
    
    # Verify special characters were preserved
    call_args = mock_hechos_service.get_hechos_for_revision.call_args[0][0]
    assert call_args["medio"] == "El País (España)"
    assert call_args["pais_publicacion"] == "São Paulo"


# Tests for /dashboard/filtros/opciones endpoint

def test_get_filter_options_success(mock_hechos_service):
    """Test successful retrieval of filter options."""
    # Setup mock response
    expected_options = {
        "medios_disponibles": ["Clarin", "La Nacion", "Pagina 12"],
        "paises_disponibles": ["Argentina", "Chile", "Mexico"],
        "importancia_range": {"min": 1, "max": 10}
    }
    
    mock_hechos_service.get_filter_options = AsyncMock(
        return_value=expected_options
    )
    
    # Make request
    response = client.get("/dashboard/filtros/opciones")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    
    # Check structure matches FilterOptionsResponse
    assert "medios_disponibles" in data
    assert "paises_disponibles" in data
    assert "importancia_range" in data
    
    # Check data content
    assert data["medios_disponibles"] == expected_options["medios_disponibles"]
    assert data["paises_disponibles"] == expected_options["paises_disponibles"]
    assert data["importancia_range"] == expected_options["importancia_range"]
    
    # Verify service was called
    mock_hechos_service.get_filter_options.assert_called_once()


def test_get_filter_options_empty_lists(mock_hechos_service):
    """Test response when no filter options are available."""
    # Setup mock to return empty lists
    empty_options = {
        "medios_disponibles": [],
        "paises_disponibles": [],
        "importancia_range": {"min": 1, "max": 10}
    }
    
    mock_hechos_service.get_filter_options = AsyncMock(
        return_value=empty_options
    )
    
    # Make request
    response = client.get("/dashboard/filtros/opciones")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["medios_disponibles"]) == 0
    assert len(data["paises_disponibles"]) == 0
    assert data["importancia_range"]["min"] == 1
    assert data["importancia_range"]["max"] == 10


def test_get_filter_options_database_error(mock_hechos_service):
    """Test handling of database errors."""
    # Setup mock to raise exception
    mock_hechos_service.get_filter_options = AsyncMock(
        side_effect=Exception("Database connection failed")
    )
    
    # Make request
    response = client.get("/dashboard/filtros/opciones")
    
    # Should return 500 Internal Server Error
    assert response.status_code == 500
    data = response.json()
    assert "Error retrieving filter options" in data["detail"]


def test_get_filter_options_large_dataset(mock_hechos_service):
    """Test response with large number of filter options."""
    # Setup mock with many options
    large_options = {
        "medios_disponibles": [f"Medio {i}" for i in range(100)],
        "paises_disponibles": [f"Pais {i}" for i in range(50)],
        "importancia_range": {"min": 2, "max": 9}
    }
    
    mock_hechos_service.get_filter_options = AsyncMock(
        return_value=large_options
    )
    
    # Make request
    response = client.get("/dashboard/filtros/opciones")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["medios_disponibles"]) == 100
    assert len(data["paises_disponibles"]) == 50
    assert data["importancia_range"]["min"] == 2
    assert data["importancia_range"]["max"] == 9


def test_get_filter_options_special_characters(mock_hechos_service):
    """Test handling of special characters in filter options."""
    # Setup mock with special characters
    special_options = {
        "medios_disponibles": [
            "El País (España)",
            "Süddeutsche Zeitung",
            "L'Équipe"
        ],
        "paises_disponibles": [
            "São Paulo",
            "Côte d'Ivoire",
            "España"
        ],
        "importancia_range": {"min": 1, "max": 10}
    }
    
    mock_hechos_service.get_filter_options = AsyncMock(
        return_value=special_options
    )
    
    # Make request
    response = client.get("/dashboard/filtros/opciones")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    
    # Verify special characters are preserved
    assert "El País (España)" in data["medios_disponibles"]
    assert "São Paulo" in data["paises_disponibles"]
