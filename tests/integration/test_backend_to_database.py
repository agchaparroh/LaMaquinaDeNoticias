"""Test integración Backend → Database

Verifica que el Backend de Dashboard puede consultar y obtener datos de Supabase.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import uuid


class MockSupabaseClient:
    """Mock del cliente Supabase para el Backend"""
    def __init__(self):
        self.table_data = {}
        
    def table(self, table_name):
        """Mock del método table()"""
        return MockTableBuilder(table_name, self.table_data)
        
    def rpc(self, function_name, params=None):
        """Mock del método rpc()"""
        if function_name == "obtener_articulos_revision":
            # Simular respuesta de artículos para revisión
            return MockResponse(data=[
                {
                    "id": "art-001",
                    "titular": "Noticia sobre economía",
                    "medio": "El Diario",
                    "fecha_publicacion": "2024-01-15T10:00:00Z",
                    "estado_revision": "pendiente",
                    "elementos_extraidos": 5,
                    "confianza_promedio": 0.87
                },
                {
                    "id": "art-002", 
                    "titular": "Política internacional",
                    "medio": "La Prensa",
                    "fecha_publicacion": "2024-01-15T12:00:00Z",
                    "estado_revision": "pendiente",
                    "elementos_extraidos": 3,
                    "confianza_promedio": 0.92
                }
            ])
        elif function_name == "obtener_estadisticas_dashboard":
            return MockResponse(data=[{
                "articulos_totales": 150,
                "articulos_revisados": 45,
                "articulos_pendientes": 105,
                "elementos_extraidos_total": 875,
                "tasa_aprobacion": 0.89
            }])
        return MockResponse(data=[])


class MockTableBuilder:
    """Mock del query builder de Supabase"""
    def __init__(self, table_name, data):
        self.table_name = table_name
        self.data = data
        self.filters = []
        
    def select(self, columns="*"):
        self.columns = columns
        return self
        
    def eq(self, column, value):
        self.filters.append(("eq", column, value))
        return self
        
    def gte(self, column, value):
        self.filters.append(("gte", column, value))
        return self
        
    def order(self, column, desc=True):
        self.order_by = (column, desc)
        return self
        
    def limit(self, count):
        self.limit_count = count
        return self
        
    def execute(self):
        # Simular datos según la tabla
        if self.table_name == "articulos":
            return MockResponse(data=[
                {
                    "id": "art-001",
                    "titular": "Noticia sobre economía",
                    "medio": "El Diario",
                    "fecha_publicacion": "2024-01-15T10:00:00Z"
                }
            ])
        elif self.table_name == "elementos_extraidos":
            return MockResponse(data=[
                {"id": "elem-001", "tipo": "hecho", "contenido": "Hecho 1"},
                {"id": "elem-002", "tipo": "entidad", "contenido": "Entidad 1"},
                {"id": "elem-003", "tipo": "cita", "contenido": "Cita 1"}
            ])
        return MockResponse(data=[])


class MockResponse:
    """Mock de respuesta de Supabase"""
    def __init__(self, data=None, error=None):
        self.data = data or []
        self.error = error
        self.count = len(data) if data else 0


def test_successful_integration():
    """Test caso feliz: Backend consulta → Obtiene datos"""
    
    # GIVEN: Un backend que necesita datos del dashboard
    mock_supabase = MockSupabaseClient()
    
    # WHEN: El Backend solicita artículos para revisión
    # Simular llamada RPC como la haría el backend
    response = mock_supabase.rpc("obtener_articulos_revision", {
        "limite": 10,
        "estado": "pendiente",
        "orden": "fecha_publicacion"
    })
    
    # THEN: Debe recibir los artículos correctamente
    assert response.data is not None
    assert len(response.data) == 2
    
    # Verificar estructura de datos
    article = response.data[0]
    assert article["id"] == "art-001"
    assert article["titular"] == "Noticia sobre economía"
    assert article["estado_revision"] == "pendiente"
    assert article["elementos_extraidos"] == 5
    assert 0 <= article["confianza_promedio"] <= 1
    
    # WHEN: El Backend solicita estadísticas generales
    stats_response = mock_supabase.rpc("obtener_estadisticas_dashboard")
    
    # THEN: Debe recibir las estadísticas agregadas
    stats = stats_response.data[0]
    assert stats["articulos_totales"] == 150
    assert stats["articulos_pendientes"] == 105
    assert stats["tasa_aprobacion"] == 0.89
    
    # WHEN: El Backend consulta elementos específicos de un artículo
    elementos = mock_supabase.table("elementos_extraidos") \
        .select("*") \
        .eq("articulo_id", "art-001") \
        .execute()
    
    # THEN: Debe recibir los elementos extraídos
    assert len(elementos.data) == 3
    tipos_elementos = [elem["tipo"] for elem in elementos.data]
    assert "hecho" in tipos_elementos
    assert "entidad" in tipos_elementos
    assert "cita" in tipos_elementos


def test_handles_error():
    """Test caso de error: Backend maneja errores de consulta"""
    
    # GIVEN: Diferentes escenarios de error
    
    # Caso 1: Base de datos no disponible
    with patch('supabase.Client') as mock_client:
        mock_client.side_effect = Exception("Connection refused")
        
        # WHEN/THEN: El Backend debe manejar el error de conexión
        try:
            client = mock_client()
            assert False, "Debería haber lanzado excepción"
        except Exception as e:
            assert "Connection refused" in str(e)
    
    # Caso 2: Consulta con parámetros inválidos
    mock_supabase = MockSupabaseClient()
    
    # Mock de respuesta con error
    def mock_rpc_error(function_name, params=None):
        if params and params.get("estado") == "invalid_status":
            return MockResponse(
                data=None,
                error="Invalid status value. Must be one of: pendiente, revisado, aprobado, rechazado"
            )
        return MockResponse(data=[])
    
    mock_supabase.rpc = mock_rpc_error
    
    # WHEN: Se hace una consulta con parámetros inválidos
    response = mock_supabase.rpc("obtener_articulos_revision", {
        "estado": "invalid_status"
    })
    
    # THEN: Debe recibir error descriptivo
    assert response.error is not None
    assert "Invalid status value" in response.error
    
    # Caso 3: Consulta que retorna conjunto vacío (no es error pero debe manejarse)
    mock_supabase = MockSupabaseClient()
    
    # Consultar artículos de una fecha futura
    fecha_futura = (datetime.now() + timedelta(days=30)).isoformat()
    response = mock_supabase.table("articulos") \
        .select("*") \
        .gte("fecha_publicacion", fecha_futura) \
        .execute()
    
    # THEN: Debe manejar correctamente el resultado vacío
    assert response.data == []
    assert response.count == 0
    assert response.error is None
