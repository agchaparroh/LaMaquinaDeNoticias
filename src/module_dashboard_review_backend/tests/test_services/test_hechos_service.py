"""
Unit tests for HechosService.

Tests cover the get_hechos_for_revision method with various filter combinations,
pagination scenarios, and error handling.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from services.hechos_service import HechosService
from utils.exceptions import DatabaseConnectionError


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client for testing."""
    client = MagicMock()
    return client


@pytest.fixture
def hechos_service(mock_supabase_client):
    """Create HechosService instance with mocked dependencies."""
    with patch('services.hechos_service.SupabaseClient.get_client', return_value=mock_supabase_client):
        service = HechosService()
        return service


@pytest.fixture
def sample_hechos_data():
    """Sample hechos data for testing."""
    return [
        {
            "id": 1,
            "contenido": "Test hecho 1",
            "fecha_ocurrencia": "2024-01-01T00:00:00",
            "importancia": 8,
            "tipo_hecho": "declaracion",
            "pais": "Argentina",
            "evaluacion_editorial": None,
            "consenso_fuentes": 3,
            "articulos": {
                "medio": "Test Medio 1",
                "titular": "Test Titular 1",
                "fecha_publicacion": "2024-01-01T00:00:00",
                "url": "https://test.com/article1"
            }
        },
        {
            "id": 2,
            "contenido": "Test hecho 2",
            "fecha_ocurrencia": "2024-01-02T00:00:00",
            "importancia": 5,
            "tipo_hecho": "evento",
            "pais": "Mexico",
            "evaluacion_editorial": "verificado_ok_editorial",
            "consenso_fuentes": 5,
            "articulos": {
                "medio": "Test Medio 2",
                "titular": "Test Titular 2",
                "fecha_publicacion": "2024-01-02T00:00:00",
                "url": "https://test.com/article2"
            }
        }
    ]


@pytest.mark.asyncio
async def test_get_hechos_for_revision_basic(hechos_service, mock_supabase_client, sample_hechos_data):
    """Test basic retrieval of hechos without filters."""
    # Setup mock responses
    mock_query = MagicMock()
    mock_count_query = MagicMock()
    
    # Configure main query chain
    mock_supabase_client.table.return_value.select.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.range.return_value = mock_query
    mock_query.gte.return_value = mock_query
    mock_query.lte.return_value = mock_query
    mock_query.eq.return_value = mock_query
    
    # Configure query execution
    mock_result = MagicMock()
    mock_result.data = sample_hechos_data
    mock_result.count = len(sample_hechos_data)
    mock_query.execute.return_value = mock_result
    
    # Configure count query
    mock_count_result = MagicMock()
    mock_count_result.count = len(sample_hechos_data)
    mock_count_query.execute.return_value = mock_count_result
    
    # Configure count query chain
    def table_side_effect(table_name):
        if table_name == 'hechos':
            query_mock = MagicMock()
            
            def select_side_effect(*args, **kwargs):
                if 'count' in kwargs and kwargs['count'] == 'exact':
                    if args[0] == 'id':
                        # This is the count query
                        count_mock = MagicMock()
                        count_mock.gte.return_value = count_mock
                        count_mock.lte.return_value = count_mock
                        count_mock.eq.return_value = count_mock
                        count_mock.execute.return_value = mock_count_result
                        return count_mock
                # This is the main query
                return mock_query
            
            query_mock.select = select_side_effect
            return query_mock
    
    mock_supabase_client.table.side_effect = table_side_effect
    
    # Test
    filter_params = {
        "limit": 10,
        "offset": 0
    }
    
    hechos, total_count = await hechos_service.get_hechos_for_revision(filter_params)
    
    # Assertions
    assert len(hechos) == 2
    assert total_count == 2
    
    # Verify data transformation
    assert 'articulo_metadata' in hechos[0]
    assert hechos[0]['articulo_metadata']['medio'] == "Test Medio 1"
    assert 'articulos' not in hechos[0]  # Original field should be removed
    
    # Verify pagination was applied
    mock_query.range.assert_called_once_with(0, 9)


@pytest.mark.asyncio
async def test_get_hechos_with_all_filters(hechos_service, mock_supabase_client):
    """Test retrieval with all filters applied."""
    # Setup mock
    mock_query = MagicMock()
    mock_count_query = MagicMock()
    
    mock_supabase_client.table.return_value.select.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.range.return_value = mock_query
    mock_query.gte.return_value = mock_query
    mock_query.lte.return_value = mock_query
    mock_query.eq.return_value = mock_query
    
    # Empty result
    mock_result = MagicMock()
    mock_result.data = []
    mock_result.count = 0
    mock_query.execute.return_value = mock_result
    
    # Setup count query
    mock_count_result = MagicMock()
    mock_count_result.count = 0
    
    def table_side_effect(table_name):
        query_mock = MagicMock()
        
        def select_side_effect(*args, **kwargs):
            if 'count' in kwargs and kwargs['count'] == 'exact' and args[0] == 'id':
                count_mock = MagicMock()
                count_mock.gte.return_value = count_mock
                count_mock.lte.return_value = count_mock
                count_mock.eq.return_value = count_mock
                count_mock.execute.return_value = mock_count_result
                return count_mock
            return mock_query
        
        query_mock.select = select_side_effect
        return query_mock
    
    mock_supabase_client.table.side_effect = table_side_effect
    
    # Test with all filters
    fecha_inicio = datetime(2024, 1, 1)
    fecha_fin = datetime(2024, 12, 31)
    
    filter_params = {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "medio": "La Nacion",
        "pais_publicacion": "Argentina",
        "importancia_min": 5,
        "importancia_max": 10,
        "limit": 20,
        "offset": 40
    }
    
    hechos, total_count = await hechos_service.get_hechos_for_revision(filter_params)
    
    # Assertions
    assert len(hechos) == 0
    assert total_count == 0
    
    # Verify all filters were applied
    mock_query.gte.assert_any_call('fecha_ocurrencia', fecha_inicio.isoformat())
    mock_query.lte.assert_any_call('fecha_ocurrencia', fecha_fin.isoformat())
    mock_query.eq.assert_any_call('articulos.medio', 'La Nacion')
    mock_query.eq.assert_any_call('pais', 'Argentina')
    mock_query.gte.assert_any_call('importancia', 5)
    mock_query.lte.assert_any_call('importancia', 10)
    
    # Verify pagination
    mock_query.range.assert_called_once_with(40, 59)


@pytest.mark.asyncio
async def test_get_hechos_handles_null_articulos(hechos_service, mock_supabase_client):
    """Test handling of hechos with null articulos data."""
    # Setup mock with null articulos
    data_with_null = [
        {
            "id": 1,
            "contenido": "Test hecho without article",
            "fecha_ocurrencia": "2024-01-01T00:00:00",
            "importancia": 7,
            "tipo_hecho": "otro",
            "pais": "Chile",
            "evaluacion_editorial": None,
            "consenso_fuentes": None,
            "articulos": None  # This can be null
        }
    ]
    
    mock_query = MagicMock()
    mock_result = MagicMock()
    mock_result.data = data_with_null
    mock_result.count = 1
    mock_query.execute.return_value = mock_result
    
    # Setup mock chains
    mock_supabase_client.table.return_value.select.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.range.return_value = mock_query
    
    # Setup count query
    mock_count_result = MagicMock()
    mock_count_result.count = 1
    
    def table_side_effect(table_name):
        query_mock = MagicMock()
        
        def select_side_effect(*args, **kwargs):
            if 'count' in kwargs and kwargs['count'] == 'exact' and args[0] == 'id':
                count_mock = MagicMock()
                count_mock.execute.return_value = mock_count_result
                return count_mock
            return mock_query
        
        query_mock.select = select_side_effect
        return query_mock
    
    mock_supabase_client.table.side_effect = table_side_effect
    
    # Test
    filter_params = {"limit": 10, "offset": 0}
    hechos, total_count = await hechos_service.get_hechos_for_revision(filter_params)
    
    # Assertions
    assert len(hechos) == 1
    assert hechos[0]['articulo_metadata'] == {}  # Should be empty dict, not None


@pytest.mark.asyncio
async def test_get_hechos_database_connection_error(hechos_service, mock_supabase_client):
    """Test handling of database connection errors."""
    # Setup mock to raise DatabaseConnectionError
    mock_supabase_client.table.side_effect = DatabaseConnectionError("Connection failed")
    
    # Test
    filter_params = {"limit": 10, "offset": 0}
    
    with pytest.raises(DatabaseConnectionError) as exc_info:
        await hechos_service.get_hechos_for_revision(filter_params)
    
    assert "Connection failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_hechos_unexpected_error(hechos_service, mock_supabase_client):
    """Test handling of unexpected errors."""
    # Setup mock to raise generic exception
    mock_supabase_client.table.side_effect = RuntimeError("Unexpected error")
    
    # Test
    filter_params = {"limit": 10, "offset": 0}
    
    with pytest.raises(Exception) as exc_info:
        await hechos_service.get_hechos_for_revision(filter_params)
    
    assert "Failed to retrieve hechos" in str(exc_info.value)
    assert "Unexpected error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_hechos_with_medio_filter_count_adjustment(hechos_service, mock_supabase_client):
    """Test that total count is adjusted when medio filter is applied."""
    # Setup mock
    mock_query = MagicMock()
    mock_result = MagicMock()
    mock_result.data = []
    mock_result.count = 5  # Main query returns actual count with medio filter
    mock_query.execute.return_value = mock_result
    
    # Setup mock chains
    mock_supabase_client.table.return_value.select.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.range.return_value = mock_query
    mock_query.eq.return_value = mock_query
    
    # Count query returns higher number (without medio filter)
    mock_count_result = MagicMock()
    mock_count_result.count = 20
    
    def table_side_effect(table_name):
        query_mock = MagicMock()
        
        def select_side_effect(*args, **kwargs):
            if 'count' in kwargs and kwargs['count'] == 'exact' and args[0] == 'id':
                count_mock = MagicMock()
                count_mock.execute.return_value = mock_count_result
                return count_mock
            return mock_query
        
        query_mock.select = select_side_effect
        return query_mock
    
    mock_supabase_client.table.side_effect = table_side_effect
    
    # Test with medio filter
    filter_params = {
        "medio": "Test Medio",
        "limit": 10,
        "offset": 0
    }
    
    hechos, total_count = await hechos_service.get_hechos_for_revision(filter_params)
    
    # Should use the count from main query when medio filter is present
    assert total_count == 5  # Not 20 from count query


@pytest.mark.asyncio
async def test_get_hechos_pagination_edge_cases(hechos_service, mock_supabase_client):
    """Test pagination edge cases."""
    # Test with offset beyond available data
    mock_query = MagicMock()
    mock_result = MagicMock()
    mock_result.data = []
    mock_result.count = 0
    mock_query.execute.return_value = mock_result
    
    # Setup mock chains
    mock_supabase_client.table.return_value.select.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.range.return_value = mock_query
    
    # Count query shows there are 10 total items
    mock_count_result = MagicMock()
    mock_count_result.count = 10
    
    def table_side_effect(table_name):
        query_mock = MagicMock()
        
        def select_side_effect(*args, **kwargs):
            if 'count' in kwargs and kwargs['count'] == 'exact' and args[0] == 'id':
                count_mock = MagicMock()
                count_mock.execute.return_value = mock_count_result
                return count_mock
            return mock_query
        
        query_mock.select = select_side_effect
        return query_mock
    
    mock_supabase_client.table.side_effect = table_side_effect
    
    # Test with offset beyond data
    filter_params = {
        "limit": 20,
        "offset": 100  # Beyond 10 total items
    }
    
    hechos, total_count = await hechos_service.get_hechos_for_revision(filter_params)
    
    # Should return empty list but correct total
    assert len(hechos) == 0
    assert total_count == 10
    
    # Verify range calculation
    mock_query.range.assert_called_once_with(100, 119)


# Tests for get_filter_options method

@pytest.mark.asyncio
async def test_get_filter_options_success(hechos_service, mock_supabase_client):
    """Test successful retrieval of filter options."""
    # Setup mock responses for each query
    
    # Mock medios query
    medios_result = MagicMock()
    medios_result.data = [
        {"medio": "La Nacion"},
        {"medio": "Clarin"},
        {"medio": "La Nacion"},  # Duplicate to test deduplication
        {"medio": "Pagina 12"},
        {"medio": None}  # Test None filtering
    ]
    
    # Mock paises query
    paises_result = MagicMock()
    paises_result.data = [
        {"pais": "Argentina"},
        {"pais": "Chile"},
        {"pais": "Argentina"},  # Duplicate
        {"pais": None}  # Test None filtering
    ]
    
    # Mock min importancia query
    min_result = MagicMock()
    min_result.data = [{"importancia": 2}]
    
    # Mock max importancia query
    max_result = MagicMock()
    max_result.data = [{"importancia": 9}]
    
    # Setup table mock to return different queries based on table name
    call_count = 0
    
    def table_side_effect(table_name):
        nonlocal call_count
        mock_table = MagicMock()
        
        if table_name == 'articulos':
            mock_table.select.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.execute.return_value = medios_result
        elif table_name == 'hechos':
            if call_count == 0:  # First call for paises
                mock_table.select.return_value = mock_table
                mock_table.limit.return_value = mock_table
                mock_table.execute.return_value = paises_result
                call_count += 1
            elif call_count == 1:  # Second call for min importancia
                mock_table.select.return_value = mock_table
                mock_table.order.return_value = mock_table
                mock_table.limit.return_value = mock_table
                mock_table.execute.return_value = min_result
                call_count += 1
            else:  # Third call for max importancia
                mock_table.select.return_value = mock_table
                mock_table.order.return_value = mock_table
                mock_table.limit.return_value = mock_table
                mock_table.execute.return_value = max_result
        
        return mock_table
    
    mock_supabase_client.table.side_effect = table_side_effect
    
    # Test
    result = await hechos_service.get_filter_options()
    
    # Assertions
    assert "medios_disponibles" in result
    assert "paises_disponibles" in result
    assert "importancia_range" in result
    
    # Check deduplication and None filtering worked
    assert len(result["medios_disponibles"]) == 3  # La Nacion, Clarin, Pagina 12
    assert "La Nacion" in result["medios_disponibles"]
    assert None not in result["medios_disponibles"]
    
    assert len(result["paises_disponibles"]) == 2  # Argentina, Chile
    assert "Argentina" in result["paises_disponibles"]
    assert None not in result["paises_disponibles"]
    
    # Check sorting
    assert result["medios_disponibles"] == sorted(result["medios_disponibles"])
    assert result["paises_disponibles"] == sorted(result["paises_disponibles"])
    
    # Check importance range
    assert result["importancia_range"]["min"] == 2
    assert result["importancia_range"]["max"] == 9


@pytest.mark.asyncio
async def test_get_filter_options_empty_results(hechos_service, mock_supabase_client):
    """Test handling of empty database results."""
    # Setup mock to return empty results
    empty_result = MagicMock()
    empty_result.data = []
    
    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.execute.return_value = empty_result
    
    mock_supabase_client.table.return_value = mock_table
    
    # Test
    result = await hechos_service.get_filter_options()
    
    # Should return empty lists with default importance range
    assert result["medios_disponibles"] == []
    assert result["paises_disponibles"] == []
    assert result["importancia_range"]["min"] == 1
    assert result["importancia_range"]["max"] == 10


@pytest.mark.asyncio
async def test_get_filter_options_partial_failure(hechos_service, mock_supabase_client):
    """Test graceful degradation when some queries fail."""
    # Setup medios query to succeed
    medios_result = MagicMock()
    medios_result.data = [{"medio": "Test Medio"}]
    
    # Setup other queries to fail
    call_count = 0
    
    def table_side_effect(table_name):
        nonlocal call_count
        mock_table = MagicMock()
        
        if table_name == 'articulos':
            mock_table.select.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.execute.return_value = medios_result
        elif table_name == 'hechos':
            # Make paises query fail
            if call_count == 0:
                mock_table.select.side_effect = Exception("Database error")
                call_count += 1
            else:
                # Importance queries succeed
                mock_table.select.return_value = mock_table
                mock_table.order.return_value = mock_table
                mock_table.limit.return_value = mock_table
                result = MagicMock()
                result.data = [{"importancia": 5}]
                mock_table.execute.return_value = result
        
        return mock_table
    
    mock_supabase_client.table.side_effect = table_side_effect
    
    # Test - should not raise exception
    result = await hechos_service.get_filter_options()
    
    # Should have medios but no paises
    assert len(result["medios_disponibles"]) == 1
    assert result["medios_disponibles"][0] == "Test Medio"
    assert result["paises_disponibles"] == []  # Empty due to error
    assert result["importancia_range"]["min"] == 5
    assert result["importancia_range"]["max"] == 5


@pytest.mark.asyncio
async def test_get_filter_options_all_queries_fail(hechos_service, mock_supabase_client):
    """Test response when all queries fail."""
    # Setup all queries to fail
    mock_supabase_client.table.side_effect = Exception("Database connection lost")
    
    # Test - should not raise exception but return defaults
    result = await hechos_service.get_filter_options()
    
    # Should return empty lists with default importance range
    assert result["medios_disponibles"] == []
    assert result["paises_disponibles"] == []
    assert result["importancia_range"]["min"] == 1
    assert result["importancia_range"]["max"] == 10


@pytest.mark.asyncio
async def test_get_filter_options_with_special_characters(hechos_service, mock_supabase_client):
    """Test handling of special characters in filter values."""
    # Setup mock with special characters
    medios_result = MagicMock()
    medios_result.data = [
        {"medio": "El País (España)"},
        {"medio": "L'Équipe"},
        {"medio": "Süddeutsche Zeitung"}
    ]
    
    paises_result = MagicMock()
    paises_result.data = [
        {"pais": "São Paulo"},
        {"pais": "Côte d'Ivoire"}
    ]
    
    # Setup mocks
    call_count = 0
    
    def table_side_effect(table_name):
        nonlocal call_count
        mock_table = MagicMock()
        
        if table_name == 'articulos':
            mock_table.select.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.execute.return_value = medios_result
        elif table_name == 'hechos':
            if call_count == 0:
                mock_table.select.return_value = mock_table
                mock_table.limit.return_value = mock_table
                mock_table.execute.return_value = paises_result
                call_count += 1
            else:
                # Default importance queries
                mock_table.select.return_value = mock_table
                mock_table.order.return_value = mock_table
                mock_table.limit.return_value = mock_table
                result = MagicMock()
                result.data = [{"importancia": 1}] if call_count == 1 else [{"importancia": 10}]
                mock_table.execute.return_value = result
                call_count += 1
        
        return mock_table
    
    mock_supabase_client.table.side_effect = table_side_effect
    
    # Test
    result = await hechos_service.get_filter_options()
    
    # Verify special characters are preserved
    assert "El País (España)" in result["medios_disponibles"]
    assert "São Paulo" in result["paises_disponibles"]
