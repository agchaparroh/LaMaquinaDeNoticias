"""
Pytest fixtures for Dashboard Review Backend tests
Provides mock Supabase client and test configurations
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def async_test_client():
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    mock_client = MagicMock()
    
    # Mock table operations
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    
    # Mock query chain
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.neq.return_value = mock_table
    mock_table.gt.return_value = mock_table
    mock_table.gte.return_value = mock_table
    mock_table.lt.return_value = mock_table
    mock_table.lte.return_value = mock_table
    mock_table.like.return_value = mock_table
    mock_table.ilike.return_value = mock_table
    mock_table.in_.return_value = mock_table
    mock_table.contains.return_value = mock_table
    mock_table.contained_by.return_value = mock_table
    mock_table.filter.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.range.return_value = mock_table
    mock_table.single.return_value = mock_table
    
    # Default execute response
    mock_response = MagicMock()
    mock_response.data = []
    mock_response.count = 0
    mock_table.execute.return_value = mock_response
    
    return mock_client


@pytest.fixture
def mock_supabase_dependency(mock_supabase):
    """Override the Supabase client dependency for testing."""
    with patch('core.dependencies.get_supabase_client', return_value=mock_supabase):
        yield mock_supabase


@pytest.fixture
def sample_hecho():
    """Sample hecho data for testing."""
    return {
        "id": 1,
        "fecha": "2024-01-15",
        "titulo": "Test Hecho",
        "descripcion": "Esta es una descripción de prueba",
        "url": "https://example.com/noticia",
        "medio": "Test Medio",
        "pais": "Argentina",
        "importancia": 8,
        "evaluacion_editorial": None,
        "fecha_feedback_importancia": None,
        "fecha_evaluacion_editorial": None
    }


@pytest.fixture
def sample_hechos_list(sample_hecho):
    """Sample list of hechos for testing."""
    hechos = []
    for i in range(1, 6):
        hecho = sample_hecho.copy()
        hecho["id"] = i
        hecho["titulo"] = f"Test Hecho {i}"
        hecho["importancia"] = 6 + (i % 3)  # Values between 6-8
        hechos.append(hecho)
    return hechos


@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    env_vars = {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
        "API_HOST": "0.0.0.0",
        "API_PORT": "8004",
        "CORS_ORIGINS": "http://localhost:3001",
        "LOG_LEVEL": "INFO",
        "ENVIRONMENT": "testing"
    }
    with patch.dict("os.environ", env_vars):
        yield env_vars


# Async fixtures for async tests
@pytest.fixture
async def async_mock_supabase():
    """Async mock Supabase client for async testing."""
    mock_client = AsyncMock()
    
    # Mock async table operations
    mock_table = AsyncMock()
    mock_client.table.return_value = mock_table
    
    # Mock async query chain
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.range.return_value = mock_table
    mock_table.execute = AsyncMock()
    
    # Default async execute response
    mock_response = MagicMock()
    mock_response.data = []
    mock_response.count = 0
    mock_table.execute.return_value = mock_response
    
    return mock_client


@pytest.fixture
def mock_supabase_with_errors():
    """Mock Supabase client that simulates various error conditions."""
    mock_client = MagicMock()
    
    # Mock table operations
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    
    # Setup query chain that will raise errors
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.range.return_value = mock_table
    mock_table.filter.return_value = mock_table
    
    # Configure to raise different types of errors
    def configure_error(error_type="connection", message="Test error"):
        if error_type == "connection":
            mock_table.execute.side_effect = ConnectionError(message)
        elif error_type == "timeout":
            mock_table.execute.side_effect = TimeoutError(message)
        elif error_type == "api":
            from supabase import APIError
            mock_table.execute.side_effect = APIError({"message": message, "code": "TEST_ERROR"})
        elif error_type == "generic":
            mock_table.execute.side_effect = Exception(message)
        else:
            # Reset to no error
            mock_table.execute.side_effect = None
            mock_response = MagicMock()
            mock_response.data = []
            mock_response.count = 0
            mock_table.execute.return_value = mock_response
    
    mock_client.configure_error = configure_error
    return mock_client


@pytest.fixture
def complete_hecho_data():
    """Complete hecho data with all fields from the database model."""
    return {
        "id": 1,
        "contenido": "El presidente anunció nuevas medidas económicas para combatir la inflación",
        "fecha_ocurrencia": "2024-01-15T10:30:00",
        "importancia": 8,
        "tipo_hecho": "declaracion",
        "pais": "Argentina",
        "evaluacion_editorial": None,
        "consenso_fuentes": 3,
        # Join data that would come from related tables
        "articulos": {
            "id": 101,
            "medio": "La Nación",
            "titular": "Presidente anuncia paquete de medidas antiinflacionarias",
            "fecha_publicacion": "2024-01-15T11:00:00",
            "url": "https://www.lanacion.com.ar/economia/medidas-antiinflacion"
        },
        # Computed fields
        "fecha_feedback_importancia": None,
        "fecha_evaluacion_editorial": None
    }


@pytest.fixture
def complete_hechos_list():
    """List of complete hechos with various states and data."""
    return [
        {
            "id": 1,
            "contenido": "El presidente anunció nuevas medidas económicas",
            "fecha_ocurrencia": "2024-01-15T10:30:00",
            "importancia": 8,
            "tipo_hecho": "declaracion",
            "pais": "Argentina",
            "evaluacion_editorial": "relevante",
            "consenso_fuentes": 3,
            "articulos": {
                "id": 101,
                "medio": "La Nación",
                "titular": "Presidente anuncia medidas económicas",
                "fecha_publicacion": "2024-01-15T11:00:00",
                "url": "https://www.lanacion.com.ar/economia/medidas"
            },
            "fecha_feedback_importancia": "2024-01-15T15:00:00",
            "fecha_evaluacion_editorial": "2024-01-15T16:00:00"
        },
        {
            "id": 2,
            "contenido": "Se registró un terremoto de 6.5 grados en la región norte",
            "fecha_ocurrencia": "2024-01-14T23:45:00",
            "importancia": 9,
            "tipo_hecho": "acontecimiento",
            "pais": "Chile",
            "evaluacion_editorial": None,
            "consenso_fuentes": 5,
            "articulos": {
                "id": 102,
                "medio": "El Mercurio",
                "titular": "Fuerte terremoto sacude el norte del país",
                "fecha_publicacion": "2024-01-15T00:30:00",
                "url": "https://www.elmercurio.com/nacional/terremoto-norte"
            },
            "fecha_feedback_importancia": None,
            "fecha_evaluacion_editorial": None
        },
        {
            "id": 3,
            "contenido": "El banco central modificó la tasa de interés de referencia",
            "fecha_ocurrencia": "2024-01-13T14:00:00",
            "importancia": 7,
            "tipo_hecho": "medida",
            "pais": "Brasil",
            "evaluacion_editorial": "contextual",
            "consenso_fuentes": 2,
            "articulos": {
                "id": 103,
                "medio": "Folha de S.Paulo",
                "titular": "Banco Central ajusta taxa de juros",
                "fecha_publicacion": "2024-01-13T15:30:00",
                "url": "https://www.folha.com.br/economia/banco-central-juros"
            },
            "fecha_feedback_importancia": "2024-01-14T09:00:00",
            "fecha_evaluacion_editorial": None
        },
        {
            "id": 4,
            "contenido": "Investigación revela casos de corrupción en empresa estatal",
            "fecha_ocurrencia": "2024-01-12T09:00:00",
            "importancia": 6,
            "tipo_hecho": "investigacion",
            "pais": "Perú",
            "evaluacion_editorial": "irrelevante",
            "consenso_fuentes": 1,
            "articulos": {
                "id": 104,
                "medio": "El Comercio",
                "titular": "Destapan red de corrupción en empresa del Estado",
                "fecha_publicacion": "2024-01-12T10:00:00",
                "url": "https://www.elcomercio.pe/politica/corrupcion-empresa-estatal"
            },
            "fecha_feedback_importancia": "2024-01-12T18:00:00",
            "fecha_evaluacion_editorial": "2024-01-13T10:00:00"
        },
        {
            "id": 5,
            "contenido": "Nuevo estudio científico sobre cambio climático en la región",
            "fecha_ocurrencia": "2024-01-11T12:00:00",
            "importancia": 5,
            "tipo_hecho": "estudio",
            "pais": "Colombia",
            "evaluacion_editorial": None,
            "consenso_fuentes": 4,
            "articulos": {
                "id": 105,
                "medio": "El Tiempo",
                "titular": "Alarmante estudio sobre impacto del cambio climático",
                "fecha_publicacion": "2024-01-11T14:00:00",
                "url": "https://www.eltiempo.com/vida/medio-ambiente/cambio-climatico-estudio"
            },
            "fecha_feedback_importancia": None,
            "fecha_evaluacion_editorial": None
        }
    ]


@pytest.fixture
def feedback_importancia_data():
    """Sample feedback importancia data for testing."""
    return {
        "hecho_id": 1,
        "importancia_editor_final": 9
    }


@pytest.fixture
def evaluacion_editorial_data():
    """Sample evaluacion editorial data for testing."""
    return {
        "hecho_id": 2,
        "evaluacion": "relevante"
    }


@pytest.fixture
def filter_options_data():
    """Sample filter options data for testing."""
    return {
        "medios": ["La Nación", "El Mercurio", "Folha de S.Paulo", "El Comercio", "El Tiempo"],
        "paises": ["Argentina", "Brasil", "Chile", "Colombia", "Perú"],
        "tipos_evaluacion": ["relevante", "contextual", "irrelevante"]
    }
