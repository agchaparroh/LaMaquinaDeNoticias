"""
Tests para SupabaseService
==========================

Pruebas unitarias del servicio de integración con Supabase,
incluyendo:
- Patrón Singleton
- Manejo de errores
- Reintentos automáticos
- Llamadas a RPCs
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from supabase import Client

from src.services.supabase_service import SupabaseService, get_supabase_service


class TestSupabaseService:
    """Tests para la clase SupabaseService."""
    
    def test_singleton_pattern(self):
        """Verifica que SupabaseService implemente correctamente el patrón Singleton."""
        service1 = SupabaseService()
        service2 = SupabaseService()
        assert service1 is service2, "SupabaseService debe ser un Singleton"
    
    def test_singleton_global_function(self):
        """Verifica que get_supabase_service retorne siempre la misma instancia."""
        service1 = get_supabase_service()
        service2 = get_supabase_service()
        assert service1 is service2, "get_supabase_service debe retornar el mismo objeto"
    
    @patch('src.services.supabase_service.create_client')
    @patch('src.services.supabase_service.SUPABASE_URL', 'https://test.supabase.co')
    @patch('src.services.supabase_service.SUPABASE_KEY', 'test-key')
    def test_initialization_success(self, mock_create_client):
        """Prueba inicialización exitosa del servicio."""
        # Limpiar instancia singleton para esta prueba
        SupabaseService._instance = None
        
        mock_client = Mock(spec=Client)
        mock_create_client.return_value = mock_client
        
        service = SupabaseService()
        
        mock_create_client.assert_called_once_with(
            'https://test.supabase.co',
            'test-key'
        )
        assert service.client == mock_client
    
    @patch('src.services.supabase_service.SUPABASE_URL', '')
    @patch('src.services.supabase_service.SUPABASE_KEY', 'test-key')
    def test_initialization_missing_url(self):
        """Prueba que falle la inicialización sin URL."""
        # Limpiar instancia singleton
        SupabaseService._instance = None
        
        with pytest.raises(ValueError, match="Credenciales de Supabase no encontradas"):
            SupabaseService()
    
    @patch('src.services.supabase_service.SUPABASE_URL', 'https://test.supabase.co')
    @patch('src.services.supabase_service.SUPABASE_KEY', '')
    def test_initialization_missing_key(self):
        """Prueba que falle la inicialización sin API key."""
        # Limpiar instancia singleton
        SupabaseService._instance = None
        
        with pytest.raises(ValueError, match="Credenciales de Supabase no encontradas"):
            SupabaseService()
    
    @patch('src.services.supabase_service.create_client')
    def test_get_client(self, mock_create_client):
        """Prueba obtención del cliente."""
        # Setup
        SupabaseService._instance = None
        mock_client = Mock(spec=Client)
        mock_create_client.return_value = mock_client
        
        with patch('src.services.supabase_service.SUPABASE_URL', 'https://test.supabase.co'), \
             patch('src.services.supabase_service.SUPABASE_KEY', 'test-key'):
            service = SupabaseService()
            client = service.get_client()
            
            assert client == mock_client
    
    @patch('src.services.supabase_service.create_client')
    def test_insertar_articulo_completo_success(self, mock_create_client):
        """Prueba inserción exitosa de artículo completo."""
        # Setup
        SupabaseService._instance = None
        mock_client = Mock(spec=Client)
        mock_create_client.return_value = mock_client
        
        # Mock RPC response
        mock_response = Mock()
        mock_response.data = [{
            'articulo_id': 123,
            'hechos_insertados': 5,
            'entidades_insertadas': 8,
            'citas_insertadas': 3,
            'datos_insertados': 2,
            'relaciones_insertadas': 4,
            'warnings': []
        }]
        mock_client.rpc.return_value.execute.return_value = mock_response
        
        with patch('src.services.supabase_service.SUPABASE_URL', 'https://test.supabase.co'), \
             patch('src.services.supabase_service.SUPABASE_KEY', 'test-key'):
            service = SupabaseService()
            
            payload = {'test': 'data'}
            result = service.insertar_articulo_completo(payload)
            
            # Verificaciones
            mock_client.rpc.assert_called_once_with(
                'insertar_articulo_completo',
                {'datos_json': payload}
            )
            assert result['articulo_id'] == 123
            assert result['hechos_insertados'] == 5
    
    @patch('src.services.supabase_service.create_client')
    def test_insertar_articulo_completo_empty_response(self, mock_create_client):
        """Prueba manejo de respuesta vacía en insertar_articulo_completo."""
        # Setup
        SupabaseService._instance = None
        mock_client = Mock(spec=Client)
        mock_create_client.return_value = mock_client
        
        # Mock empty response
        mock_response = Mock()
        mock_response.data = None
        mock_client.rpc.return_value.execute.return_value = mock_response
        
        with patch('src.services.supabase_service.SUPABASE_URL', 'https://test.supabase.co'), \
             patch('src.services.supabase_service.SUPABASE_KEY', 'test-key'):
            service = SupabaseService()
            
            result = service.insertar_articulo_completo({'test': 'data'})
            assert result is None
    
    @patch('src.services.supabase_service.create_client')
    def test_buscar_entidad_similar_success(self, mock_create_client):
        """Prueba búsqueda exitosa de entidad similar."""
        # Setup
        SupabaseService._instance = None
        mock_client = Mock(spec=Client)
        mock_create_client.return_value = mock_client
        
        # Mock RPC response
        mock_response = Mock()
        mock_response.data = [
            {'id': 1, 'nombre': 'Pedro Sánchez', 'tipo': 'PERSONA', 'score': 0.95},
            {'id': 2, 'nombre': 'Pedro Sánchez Castejón', 'tipo': 'PERSONA', 'score': 0.88}
        ]
        mock_client.rpc.return_value.execute.return_value = mock_response
        
        with patch('src.services.supabase_service.SUPABASE_URL', 'https://test.supabase.co'), \
             patch('src.services.supabase_service.SUPABASE_KEY', 'test-key'):
            service = SupabaseService()
            
            results = service.buscar_entidad_similar(
                'Pedro Sanchez',
                tipo_entidad='PERSONA',
                umbral_similitud=0.8
            )
            
            # Verificaciones
            assert len(results) == 2
            assert results[0] == (1, 'Pedro Sánchez', 'PERSONA', 0.95)
            assert results[1] == (2, 'Pedro Sánchez Castejón', 'PERSONA', 0.88)
            
            # Verificar llamada RPC
            expected_params = {
                'nombre_busqueda': 'Pedro Sanchez',
                'tipo_entidad': 'PERSONA',
                'umbral_similitud': 0.8,
                'limite_resultados': 5
            }
            mock_client.rpc.assert_called_once_with('buscar_entidad_similar', expected_params)
    
    @patch('src.services.supabase_service.create_client')
    def test_buscar_entidad_similar_no_results(self, mock_create_client):
        """Prueba búsqueda sin resultados."""
        # Setup
        SupabaseService._instance = None
        mock_client = Mock(spec=Client)
        mock_create_client.return_value = mock_client
        
        # Mock empty response
        mock_response = Mock()
        mock_response.data = []
        mock_client.rpc.return_value.execute.return_value = mock_response
        
        with patch('src.services.supabase_service.SUPABASE_URL', 'https://test.supabase.co'), \
             patch('src.services.supabase_service.SUPABASE_KEY', 'test-key'):
            service = SupabaseService()
            
            results = service.buscar_entidad_similar('Entidad Inexistente')
            assert results == []
    
    @patch('src.services.supabase_service.create_client')
    def test_test_connection_success(self, mock_create_client):
        """Prueba conexión exitosa."""
        # Setup
        SupabaseService._instance = None
        mock_client = Mock(spec=Client)
        mock_create_client.return_value = mock_client
        
        # Mock successful query
        mock_response = Mock()
        mock_response.data = [{'id': 1}]
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = mock_response
        
        with patch('src.services.supabase_service.SUPABASE_URL', 'https://test.supabase.co'), \
             patch('src.services.supabase_service.SUPABASE_KEY', 'test-key'):
            service = SupabaseService()
            
            result = service.test_connection()
            assert result is True
            
            # Verificar llamada
            mock_client.table.assert_called_once_with('entidades')
    
    @patch('src.services.supabase_service.create_client')
    def test_test_connection_failure(self, mock_create_client):
        """Prueba fallo de conexión."""
        # Setup
        SupabaseService._instance = None
        mock_client = Mock(spec=Client)
        mock_create_client.return_value = mock_client
        
        # Mock failed query
        mock_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception("Connection error")
        
        with patch('src.services.supabase_service.SUPABASE_URL', 'https://test.supabase.co'), \
             patch('src.services.supabase_service.SUPABASE_KEY', 'test-key'):
            service = SupabaseService()
            
            result = service.test_connection()
            assert result is False
    
    @patch('src.services.supabase_service.create_client')
    def test_retry_on_failure(self, mock_create_client):
        """Prueba que los métodos reintenten en caso de fallo."""
        # Setup
        SupabaseService._instance = None
        mock_client = Mock(spec=Client)
        mock_create_client.return_value = mock_client
        
        # Mock que falla la primera vez, luego tiene éxito
        mock_response = Mock()
        mock_response.data = [{'articulo_id': 123}]
        
        mock_rpc = mock_client.rpc.return_value
        mock_rpc.execute.side_effect = [
            Exception("Temporary error"),
            mock_response  # Éxito en el segundo intento
        ]
        
        with patch('src.services.supabase_service.SUPABASE_URL', 'https://test.supabase.co'), \
             patch('src.services.supabase_service.SUPABASE_KEY', 'test-key'), \
             patch('src.services.supabase_service.MAX_RETRIES', 2):
            service = SupabaseService()
            
            result = service.insertar_articulo_completo({'test': 'data'})
            
            # Verificar que se reintentó
            assert mock_client.rpc.call_count == 2
            assert result['articulo_id'] == 123
    
    @patch('src.services.supabase_service.create_client')
    def test_insertar_fragmento_completo_success(self, mock_create_client):
        """Prueba inserción exitosa de fragmento completo."""
        # Setup
        SupabaseService._instance = None
        mock_client = Mock(spec=Client)
        mock_create_client.return_value = mock_client
        
        # Mock RPC response
        mock_response = Mock()
        mock_response.data = [{
            'fragmento_id': 456,
            'hechos_insertados': 3,
            'entidades_insertadas': 5,
            'citas_insertadas': 2,
            'datos_insertados': 1,
            'relaciones_insertadas': 2,
            'warnings': []
        }]
        mock_client.rpc.return_value.execute.return_value = mock_response
        
        with patch('src.services.supabase_service.SUPABASE_URL', 'https://test.supabase.co'), \
             patch('src.services.supabase_service.SUPABASE_KEY', 'test-key'):
            service = SupabaseService()
            
            payload = {'fragmento': 'data'}
            result = service.insertar_fragmento_completo(payload)
            
            # Verificaciones
            mock_client.rpc.assert_called_once_with(
                'insertar_fragmento_completo',
                {'datos_json': payload}
            )
            assert result['fragmento_id'] == 456
            assert result['hechos_insertados'] == 3
    
    @patch('src.services.supabase_service.create_client')
    def test_buscar_entidad_similar_without_type(self, mock_create_client):
        """Prueba búsqueda de entidad sin especificar tipo."""
        # Setup
        SupabaseService._instance = None
        mock_client = Mock(spec=Client)
        mock_create_client.return_value = mock_client
        
        # Mock RPC response
        mock_response = Mock()
        mock_response.data = [
            {'id': 10, 'nombre': 'Madrid', 'tipo': 'LUGAR', 'score': 0.92},
            {'id': 11, 'nombre': 'Real Madrid', 'tipo': 'ORGANIZACION', 'score': 0.85}
        ]
        mock_client.rpc.return_value.execute.return_value = mock_response
        
        with patch('src.services.supabase_service.SUPABASE_URL', 'https://test.supabase.co'), \
             patch('src.services.supabase_service.SUPABASE_KEY', 'test-key'):
            service = SupabaseService()
            
            results = service.buscar_entidad_similar('Madrid')
            
            # Verificaciones
            assert len(results) == 2
            
            # Verificar que no se envió tipo_entidad en los parámetros
            call_args = mock_client.rpc.call_args[0]
            call_params = call_args[1]
            assert 'tipo_entidad' not in call_params
            assert call_params['nombre_busqueda'] == 'Madrid'


# Tests para función helper
def test_get_supabase_service_creates_singleton():
    """Verifica que get_supabase_service cree y mantenga un singleton."""
    # Limpiar cualquier instancia previa
    import src.services.supabase_service as module
    module._supabase_service = None
    
    with patch('src.services.supabase_service.SupabaseService') as MockService:
        mock_instance = Mock()
        MockService.return_value = mock_instance
        
        # Primera llamada debe crear instancia
        service1 = get_supabase_service()
        assert service1 == mock_instance
        MockService.assert_called_once()
        
        # Segunda llamada debe retornar la misma instancia sin crear nueva
        MockService.reset_mock()
        service2 = get_supabase_service()
        assert service2 == mock_instance
        MockService.assert_not_called()
