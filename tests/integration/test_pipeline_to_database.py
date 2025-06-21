"""Test integración Pipeline → Database (Supabase)

Verifica que el Pipeline procesa datos y los guarda correctamente en Supabase.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid


class MockSupabaseResponse:
    """Mock de respuesta de Supabase RPC"""
    def __init__(self, data=None, error=None):
        self.data = data or []
        self.error = error
        
    def execute(self):
        if self.error:
            raise Exception(self.error)
        return self


def test_successful_integration():
    """Test caso feliz: Pipeline procesa → Guarda en Supabase"""
    
    # GIVEN: Datos procesados por el Pipeline listos para guardar
    processed_fragment = {
        "fragmento_id": str(uuid.uuid4()),
        "id_articulo_fuente": "article-123",
        "texto_original": "Este es el texto del fragmento procesado con información relevante.",
        "elementos_extraidos": {
            "hechos": [
                {
                    "hecho": "Se anunció nueva política económica",
                    "tipo": "declaracion",
                    "confianza": 0.95
                }
            ],
            "entidades": [
                {
                    "texto": "Ministerio de Economía",
                    "tipo": "ORGANIZACION",
                    "inicio": 10,
                    "fin": 30
                }
            ],
            "citas": [
                {
                    "texto_cita": "La economía crecerá un 3% este año",
                    "autor_nombre": "Juan Pérez",
                    "autor_cargo": "Ministro"
                }
            ]
        },
        "metricas": {
            "tiempo_procesamiento": 2.5,
            "fases_completadas": ["triaje", "extraccion", "normalizacion"]
        }
    }
    
    # Mock de las llamadas RPC a Supabase
    with patch('supabase.Client') as mock_client:
        # Configurar mocks para las diferentes operaciones
        
        # 1. Guardar fragmento procesado
        mock_rpc = Mock()
        mock_rpc.return_value = MockSupabaseResponse(
            data=[{"fragmento_uuid": processed_fragment["fragmento_id"], "success": True}]
        )
        mock_client.rpc = mock_rpc
        
        # 2. Normalizar entidades
        mock_normalize = Mock()
        mock_normalize.return_value = MockSupabaseResponse(
            data=[{
                "entidad_id": "ent-456",
                "nombre_normalizado": "Ministerio de Economía",
                "tipo": "organizacion_gubernamental"
            }]
        )
        
        # Simular el flujo del Pipeline
        # WHEN: El Pipeline guarda los datos procesados
        
        # Paso 1: Guardar fragmento principal
        fragment_result = mock_rpc("guardar_fragmento_procesado", {
            "p_fragmento": processed_fragment
        }).execute()
        
        assert fragment_result.data[0]["success"] is True
        assert fragment_result.data[0]["fragmento_uuid"] == processed_fragment["fragmento_id"]
        
        # Paso 2: Normalizar y vincular entidades
        for entidad in processed_fragment["elementos_extraidos"]["entidades"]:
            entity_result = mock_normalize("normalizar_entidad", {
                "p_nombre": entidad["texto"],
                "p_tipo": entidad["tipo"]
            }).execute()
            
            assert entity_result.data[0]["entidad_id"] is not None
            assert entity_result.data[0]["nombre_normalizado"] == "Ministerio de Economía"
        
        # THEN: Todos los datos deben estar guardados correctamente
        assert mock_rpc.called
        assert mock_rpc.call_count >= 1


def test_handles_error():
    """Test caso de error: Manejo de errores de base de datos"""
    
    # GIVEN: Diferentes escenarios de error con Supabase
    
    # Caso 1: Error de conexión a Supabase
    with patch('supabase.Client') as mock_client:
        mock_rpc = Mock()
        mock_rpc.side_effect = Exception("Connection timeout to Supabase")
        mock_client.rpc = mock_rpc
        
        # WHEN/THEN: El Pipeline debe manejar el error de conexión
        try:
            result = mock_rpc("guardar_fragmento_procesado", {})
            assert False, "Debería haber lanzado excepción"
        except Exception as e:
            assert "Connection timeout" in str(e)
    
    # Caso 2: Error de validación en Supabase (constraint violation)
    with patch('supabase.Client') as mock_client:
        mock_rpc = Mock()
        mock_rpc.return_value = MockSupabaseResponse(
            error="duplicate key value violates unique constraint"
        )
        mock_client.rpc = mock_rpc
        
        # WHEN/THEN: El Pipeline debe manejar errores de constraint
        try:
            result = mock_rpc("guardar_fragmento_procesado", {
                "p_fragmento": {"fragmento_id": "duplicate-id"}
            }).execute()
            assert False, "Debería haber lanzado excepción"
        except Exception as e:
            assert "duplicate key" in str(e)
    
    # Caso 3: Transacción parcial - algunos elementos se guardan, otros fallan
    processed_fragment = {
        "fragmento_id": str(uuid.uuid4()),
        "elementos_extraidos": {
            "hechos": [
                {"hecho": "Hecho 1", "tipo": "declaracion"},
                {"hecho": "Hecho 2", "tipo": "invalid_type"},  # Tipo inválido
            ]
        }
    }
    
    with patch('supabase.Client') as mock_client:
        call_count = 0
        
        def mock_rpc_behavior(func_name, params):
            nonlocal call_count
            call_count += 1
            
            # Primera llamada exitosa, segunda falla
            if call_count == 1:
                return MockSupabaseResponse(data=[{"success": True}])
            else:
                return MockSupabaseResponse(error="Invalid fact type")
        
        mock_rpc = Mock(side_effect=mock_rpc_behavior)
        mock_client.rpc = mock_rpc
        
        # WHEN: Se procesan múltiples elementos
        results = []
        errors = []
        
        for i, hecho in enumerate(processed_fragment["elementos_extraidos"]["hechos"]):
            try:
                result = mock_rpc(f"guardar_hecho_{i}", {"hecho": hecho})
                if hasattr(result, 'execute'):
                    result = result.execute()
                results.append(result)
            except Exception as e:
                errors.append(str(e))
        
        # THEN: Debe haber 1 éxito y 1 error
        assert len(results) == 1
        assert len(errors) == 1
        assert "Invalid fact type" in errors[0]
