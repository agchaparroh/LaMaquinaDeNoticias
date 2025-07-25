"""
Unit tests for HechosService.

Tests cover the get_hechos_for_revision method with various filter combinations,
pagination scenarios, and error handling.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch  # noqa: F401

import pytest
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
    with patch(
        "services.hechos_service.SupabaseClient.get_client",
        return_value=mock_supabase_client,
    ):
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
                "url": "https://test.com/article1",
            },
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
                "url": "https://test.com/article2",
            },
        },
    ]


@pytest.mark.asyncio
async def test_get_hechos_for_revision_basic(
    hechos_service, mock_supabase_client, sample_hechos_data
):
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
        if table_name == "hechos":
            query_mock = MagicMock()

            def select_side_effect(*args, **kwargs):
                if "count" in kwargs and kwargs["count"] == "exact":
                    if args[0] == "id":
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
    filter_params = {"limit": 10, "offset": 0}

    hechos, total_count = await hechos_service.get_hechos_for_revision(filter_params)

    # Assertions
    assert len(hechos) == 2
    assert total_count == 2

    # Verify data transformation
    assert "articulo_metadata" in hechos[0]
    assert hechos[0]["articulo_metadata"]["medio"] == "Test Medio 1"
    assert "articulos" not in hechos[0]  # Original field should be removed

    # Verify pagination was applied
    mock_query.range.assert_called_once_with(0, 9)


@pytest.mark.asyncio
async def test_get_hechos_with_all_filters(hechos_service, mock_supabase_client):
    """Test retrieval with all filters applied."""
    # Setup mock
    mock_query = MagicMock()
    mock_count_query = MagicMock()  # noqa: F841

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
            if "count" in kwargs and kwargs["count"] == "exact" and args[0] == "id":
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
        "area_geografica": "Argentina",
        "importancia_min": 5,
        "importancia_max": 10,
        "limit": 20,
        "offset": 40,
    }

    hechos, total_count = await hechos_service.get_hechos_for_revision(filter_params)

    # Assertions
    assert len(hechos) == 0
    assert total_count == 0

    # Verify all filters were applied
    mock_query.gte.assert_any_call("fecha_ocurrencia", fecha_inicio.isoformat())
    mock_query.lte.assert_any_call("fecha_ocurrencia", fecha_fin.isoformat())
    mock_query.eq.assert_any_call("articulos.medio", "La Nacion")
    mock_query.eq.assert_any_call("pais", "Argentina")
    mock_query.gte.assert_any_call("importancia", 5)
    mock_query.lte.assert_any_call("importancia", 10)

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
            "articulos": None,  # This can be null
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
            if "count" in kwargs and kwargs["count"] == "exact" and args[0] == "id":
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
    assert hechos[0]["articulo_metadata"] == {}  # Should be empty dict, not None


@pytest.mark.asyncio
async def test_get_hechos_database_connection_error(
    hechos_service, mock_supabase_client
):
    """Test handling of database connection errors."""
    # Setup mock to raise DatabaseConnectionError
    mock_supabase_client.table.side_effect = DatabaseConnectionError(
        "Connection failed"
    )

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
async def test_get_hechos_with_medio_filter_count_adjustment(
    hechos_service, mock_supabase_client
):
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
            if "count" in kwargs and kwargs["count"] == "exact" and args[0] == "id":
                count_mock = MagicMock()
                count_mock.execute.return_value = mock_count_result
                return count_mock
            return mock_query

        query_mock.select = select_side_effect
        return query_mock

    mock_supabase_client.table.side_effect = table_side_effect

    # Test with medio filter
    filter_params = {"medio": "Test Medio", "limit": 10, "offset": 0}

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
            if "count" in kwargs and kwargs["count"] == "exact" and args[0] == "id":
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
        "offset": 100,  # Beyond 10 total items
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
        {"medio": None},  # Test None filtering
    ]

    # Mock paises query
    paises_result = MagicMock()
    paises_result.data = [
        {"pais": "Argentina"},
        {"pais": "Chile"},
        {"pais": "Argentina"},  # Duplicate
        {"pais": None},  # Test None filtering
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

        if table_name == "articulos":
            mock_table.select.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.execute.return_value = medios_result
        elif table_name == "hechos":
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

        if table_name == "articulos":
            mock_table.select.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.execute.return_value = medios_result
        elif table_name == "hechos":
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
async def test_get_filter_options_all_queries_fail(
    hechos_service, mock_supabase_client
):
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
async def test_get_filter_options_with_special_characters(
    hechos_service, mock_supabase_client
):
    """Test handling of special characters in filter values."""
    # Setup mock with special characters
    medios_result = MagicMock()
    medios_result.data = [
        {"medio": "El País (España)"},
        {"medio": "L'Équipe"},
        {"medio": "Süddeutsche Zeitung"},
    ]

    paises_result = MagicMock()
    paises_result.data = [{"pais": "São Paulo"}, {"pais": "Côte d'Ivoire"}]

    # Setup mocks
    call_count = 0

    def table_side_effect(table_name):
        nonlocal call_count
        mock_table = MagicMock()

        if table_name == "articulos":
            mock_table.select.return_value = mock_table
            mock_table.limit.return_value = mock_table
            mock_table.execute.return_value = medios_result
        elif table_name == "hechos":
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
                result.data = (
                    [{"importancia": 1}] if call_count == 1 else [{"importancia": 10}]
                )
                mock_table.execute.return_value = result
                call_count += 1

        return mock_table

    mock_supabase_client.table.side_effect = table_side_effect

    # Test
    result = await hechos_service.get_filter_options()

    # Verify special characters are preserved
    assert "El País (España)" in result["medios_disponibles"]
    assert "São Paulo" in result["paises_disponibles"]


# Tests for get_relaciones_para_hechos method


@pytest.fixture
def sample_relaciones_data():
    """Sample relaciones data for testing."""
    return [
        {
            "hecho_origen_id": 1,
            "fecha_ocurrencia_origen": "[2024-01-01 10:00:00,2024-01-01 12:00:00)",
            "hecho_destino_id": 2,
            "fecha_ocurrencia_destino": "[2024-01-01 14:00:00,2024-01-01 16:00:00)",
            "tipo_relacion": "consecuencia",
            "fuerza_relacion": 8,
            "descripcion_relacion": "El evento A causó el evento B",
            "fecha_deteccion": "2024-01-15T10:30:00",
        },
        {
            "hecho_origen_id": 3,
            "fecha_ocurrencia_origen": "[2024-01-02 10:00:00,2024-01-02 12:00:00)",
            "hecho_destino_id": 1,
            "fecha_ocurrencia_destino": "[2024-01-01 10:00:00,2024-01-01 12:00:00)",
            "tipo_relacion": "contradictorio",
            "fuerza_relacion": 6,
            "descripcion_relacion": "Versiones conflictivas del mismo evento",
            "fecha_deteccion": "2024-01-15T11:00:00",
        },
        {
            "hecho_origen_id": 4,
            "fecha_ocurrencia_origen": "[2024-01-03 09:00:00,2024-01-03 11:00:00)",
            "hecho_destino_id": 5,
            "fecha_ocurrencia_destino": "[2024-01-03 15:00:00,2024-01-03 17:00:00)",
            "tipo_relacion": "complementario",
            "fuerza_relacion": 7,
            "descripcion_relacion": None,
            "fecha_deteccion": "2024-01-15T12:00:00",
        },
    ]


@pytest.mark.asyncio
async def test_get_relaciones_para_hechos_success(
    hechos_service, mock_supabase_client, sample_relaciones_data
):
    """Test successful retrieval of relationships for multiple hechos."""
    # Setup mock query
    mock_query = MagicMock()
    mock_result = MagicMock()
    mock_result.data = sample_relaciones_data
    mock_query.execute.return_value = mock_result

    # Setup mock chains
    mock_supabase_client.table.return_value.select.return_value = mock_query
    mock_query.or_.return_value = mock_query

    # Test with multiple hecho IDs
    hecho_ids = [1, 2, 3]
    result = await hechos_service.get_relaciones_para_hechos(hecho_ids)

    # Verify query was called correctly
    mock_supabase_client.table.assert_called_once_with("hecho_relacionado")
    expected_or_filter = "hecho_origen_id.in.(1,2,3), hecho_destino_id.in.(1,2,3)"
    mock_query.or_.assert_called_once_with(expected_or_filter)

    # Verify results are grouped correctly
    assert isinstance(result, dict)
    assert 1 in result  # hecho 1 has relationships
    assert 2 in result  # hecho 2 has relationships
    assert 3 in result  # hecho 3 has relationships

    # Check hecho 1 relationships (appears as origen and destino)
    hecho_1_relaciones = result[1]
    assert len(hecho_1_relaciones) == 2  # origen in one, destino in another

    # Check relationship details
    relacion_ids = [r.hecho_relacionado_id for r in hecho_1_relaciones]
    assert 2 in relacion_ids  # related to hecho 2
    assert 3 in relacion_ids  # related to hecho 3


@pytest.mark.asyncio
async def test_get_relaciones_para_hechos_empty_list(
    hechos_service, mock_supabase_client
):
    """Test behavior with empty hecho_ids list."""
    result = await hechos_service.get_relaciones_para_hechos([])

    # Should return empty dict without making database call
    assert result == {}
    mock_supabase_client.table.assert_not_called()


@pytest.mark.asyncio
async def test_get_relaciones_para_hechos_no_relationships(
    hechos_service, mock_supabase_client
):
    """Test when no relationships exist for given hechos."""
    # Setup mock to return empty results
    mock_query = MagicMock()
    mock_result = MagicMock()
    mock_result.data = []  # No relationships found
    mock_query.execute.return_value = mock_result

    # Setup mock chains
    mock_supabase_client.table.return_value.select.return_value = mock_query
    mock_query.or_.return_value = mock_query

    # Test
    hecho_ids = [1, 2, 3]
    result = await hechos_service.get_relaciones_para_hechos(hecho_ids)

    # Should return empty dict
    assert result == {}

    # Verify query was made
    mock_supabase_client.table.assert_called_once_with("hecho_relacionado")


@pytest.mark.asyncio
async def test_get_relaciones_para_hechos_single_hecho(
    hechos_service, mock_supabase_client
):
    """Test relationships for a single hecho."""
    # Setup mock with one relationship
    relacion_data = [
        {
            "hecho_origen_id": 1,
            "fecha_ocurrencia_origen": "[2024-01-01 10:00:00,2024-01-01 12:00:00)",
            "hecho_destino_id": 2,
            "fecha_ocurrencia_destino": "[2024-01-01 14:00:00,2024-01-01 16:00:00)",
            "tipo_relacion": "causa",
            "fuerza_relacion": 9,
            "descripcion_relacion": "Causa directa",
            "fecha_deteccion": "2024-01-15T10:30:00",
        }
    ]

    mock_query = MagicMock()
    mock_result = MagicMock()
    mock_result.data = relacion_data
    mock_query.execute.return_value = mock_result

    # Setup mock chains
    mock_supabase_client.table.return_value.select.return_value = mock_query
    mock_query.or_.return_value = mock_query

    # Test with single hecho
    result = await hechos_service.get_relaciones_para_hechos([1])

    # Verify result
    assert 1 in result
    assert len(result[1]) == 1

    relacion = result[1][0]
    assert relacion.hecho_relacionado_id == 2
    assert relacion.tipo_relacion == "causa"
    assert relacion.fuerza_relacion == 9
    assert relacion.direccion == "origen"


@pytest.mark.asyncio
async def test_get_relaciones_para_hechos_bidirectional(
    hechos_service, mock_supabase_client
):
    """Test bidirectional relationships."""
    # Setup mock with bidirectional relationship
    relacion_data = [
        {
            "hecho_origen_id": 1,
            "fecha_ocurrencia_origen": "[2024-01-01 10:00:00,2024-01-01 12:00:00)",
            "hecho_destino_id": 2,
            "fecha_ocurrencia_destino": "[2024-01-01 14:00:00,2024-01-01 16:00:00)",
            "tipo_relacion": "contradictorio",  # Bidirectional type
            "fuerza_relacion": 7,
            "descripcion_relacion": "Versiones contradictorias",
            "fecha_deteccion": "2024-01-15T10:30:00",
        }
    ]

    mock_query = MagicMock()
    mock_result = MagicMock()
    mock_result.data = relacion_data
    mock_query.execute.return_value = mock_result

    # Setup mock chains
    mock_supabase_client.table.return_value.select.return_value = mock_query
    mock_query.or_.return_value = mock_query

    # Test with both hechos involved
    result = await hechos_service.get_relaciones_para_hechos([1, 2])

    # Both hechos should have the relationship listed
    assert 1 in result
    assert 2 in result

    # Hecho 1 should see hecho 2 as related (as origen)
    hecho_1_rel = result[1][0]
    assert hecho_1_rel.hecho_relacionado_id == 2
    assert hecho_1_rel.direccion == "origen"

    # Hecho 2 should see hecho 1 as related (as destino)
    hecho_2_rel = result[2][0]
    assert hecho_2_rel.hecho_relacionado_id == 1
    assert hecho_2_rel.direccion == "destino"


@pytest.mark.asyncio
async def test_get_relaciones_para_hechos_multiple_relations_per_hecho(
    hechos_service, mock_supabase_client
):
    """Test hecho with multiple relationships."""
    # Setup mock where hecho 1 has multiple relationships
    relaciones_data = [
        {
            "hecho_origen_id": 1,
            "fecha_ocurrencia_origen": "[2024-01-01 10:00:00,2024-01-01 12:00:00)",
            "hecho_destino_id": 2,
            "fecha_ocurrencia_destino": "[2024-01-01 14:00:00,2024-01-01 16:00:00)",
            "tipo_relacion": "consecuencia",
            "fuerza_relacion": 8,
            "descripcion_relacion": None,
            "fecha_deteccion": "2024-01-15T10:30:00",
        },
        {
            "hecho_origen_id": 1,
            "fecha_ocurrencia_origen": "[2024-01-01 10:00:00,2024-01-01 12:00:00)",
            "hecho_destino_id": 3,
            "fecha_ocurrencia_destino": "[2024-01-01 16:00:00,2024-01-01 18:00:00)",
            "tipo_relacion": "consecuencia",
            "fuerza_relacion": 6,
            "descripcion_relacion": "Otra consecuencia",
            "fecha_deteccion": "2024-01-15T11:00:00",
        },
        {
            "hecho_origen_id": 4,
            "fecha_ocurrencia_origen": "[2024-01-01 08:00:00,2024-01-01 09:00:00)",
            "hecho_destino_id": 1,
            "fecha_ocurrencia_destino": "[2024-01-01 10:00:00,2024-01-01 12:00:00)",
            "tipo_relacion": "causa",
            "fuerza_relacion": 9,
            "descripcion_relacion": "Causa del evento principal",
            "fecha_deteccion": "2024-01-15T09:00:00",
        },
    ]

    mock_query = MagicMock()
    mock_result = MagicMock()
    mock_result.data = relaciones_data
    mock_query.execute.return_value = mock_result

    # Setup mock chains
    mock_supabase_client.table.return_value.select.return_value = mock_query
    mock_query.or_.return_value = mock_query

    # Test
    result = await hechos_service.get_relaciones_para_hechos([1])

    # Hecho 1 should have 3 relationships
    assert 1 in result
    assert len(result[1]) == 3

    # Verify relationship details
    relaciones = result[1]
    related_ids = [r.hecho_relacionado_id for r in relaciones]
    direcciones = [r.direccion for r in relaciones]

    assert 2 in related_ids  # consecuencia (origen)
    assert 3 in related_ids  # consecuencia (origen)
    assert 4 in related_ids  # causa (destino)

    assert "origen" in direcciones  # For consecuencias
    assert "destino" in direcciones  # For causa


@pytest.mark.asyncio
async def test_get_relaciones_para_hechos_database_error(
    hechos_service, mock_supabase_client
):
    """Test handling of database errors."""
    # Setup mock to raise exception
    mock_supabase_client.table.side_effect = Exception("Database connection failed")

    # Test
    hecho_ids = [1, 2, 3]

    with pytest.raises(Exception) as exc_info:
        await hechos_service.get_relaciones_para_hechos(hecho_ids)

    assert "Failed to retrieve fact relationships" in str(exc_info.value)
    assert "Database connection failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_relaciones_para_hechos_invalid_relationship_data(
    hechos_service, mock_supabase_client
):
    """Test handling of invalid relationship data from database."""
    # Setup mock with invalid data (missing required fields)
    invalid_data = [
        {
            "hecho_origen_id": 1,
            # Missing required fields
            "tipo_relacion": "consecuencia",
        }
    ]

    mock_query = MagicMock()
    mock_result = MagicMock()
    mock_result.data = invalid_data
    mock_query.execute.return_value = mock_result

    # Setup mock chains
    mock_supabase_client.table.return_value.select.return_value = mock_query
    mock_query.or_.return_value = mock_query

    # Test - should handle validation errors gracefully
    with pytest.raises(Exception):
        await hechos_service.get_relaciones_para_hechos([1])


@pytest.mark.asyncio
async def test_get_relaciones_para_hechos_large_list(
    hechos_service, mock_supabase_client
):
    """Test with large list of hecho IDs."""
    # Setup mock
    mock_query = MagicMock()
    mock_result = MagicMock()
    mock_result.data = []
    mock_query.execute.return_value = mock_result

    # Setup mock chains
    mock_supabase_client.table.return_value.select.return_value = mock_query
    mock_query.or_.return_value = mock_query

    # Test with large list
    large_list = list(range(1, 101))  # 100 hecho IDs
    result = await hechos_service.get_relaciones_para_hechos(large_list)

    # Should handle large lists without issues
    assert result == {}

    # Verify query construction with large ID list
    expected_or_filter = (
        f"hecho_origen_id.in.({','.join(map(str, large_list))}), "
        f"hecho_destino_id.in.({','.join(map(str, large_list))})"
    )
    mock_query.or_.assert_called_once_with(expected_or_filter)
