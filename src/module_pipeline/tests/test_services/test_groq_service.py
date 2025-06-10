import pytest
import os
from unittest.mock import patch, MagicMock, ANY

# Importar GroqService y las excepciones de la librería groq
from src.services.groq_service import GroqService
from groq import APIConnectionError, RateLimitError, APIStatusError, Groq

# =============================================================================
# HELPER CLASSES SIMPLES PARA TESTING
# =============================================================================

class MockSettingsValid:
    """Settings mock válido con todos los valores necesarios"""
    GROQ_API_KEY = "test_api_key"
    GROQ_DEFAULT_MODEL_ID = "test_model_id"
    GROQ_DEFAULT_MAX_TOKENS = 150
    GROQ_DEFAULT_TEMPERATURE = 0.5
    GROQ_DEFAULT_TIMEOUT = 30.0

class MockSettingsMinimal:
    """Settings mock con solo lo mínimo requerido"""
    GROQ_API_KEY = "test_api_key"
    # Los demás atributos no existen - causarán AttributeError naturalmente

class MockSettingsNoKey:
    """Settings mock sin API key"""
    # No hay GROQ_API_KEY - causará AttributeError naturalmente
    pass

class MockSettingsEmptyKey:
    """Settings mock con API key vacía"""
    GROQ_API_KEY = ""

# =============================================================================
# FIXTURES SIMPLIFICADAS
# =============================================================================

@pytest.fixture
def mock_groq_client():
    """Mock del cliente Groq con comportamiento básico"""
    with patch('src.services.groq_service.Groq') as mock:
        instance = mock.return_value
        instance.chat.completions.create = MagicMock()
        yield instance

# =============================================================================
# PRUEBAS DE INICIALIZACIÓN - SIMPLIFICADAS
# =============================================================================

def test_groq_service_init_success_with_settings(mock_groq_client):
    """Prueba inicialización exitosa usando settings válidos"""
    with patch('src.services.groq_service.settings', MockSettingsValid()):
        service = GroqService()
        assert service.api_key == "test_api_key"
        assert service.model_id == "test_model_id"

def test_groq_service_init_success_with_direct_params(mock_groq_client):
    """Prueba inicialización exitosa pasando parámetros directamente"""
    with patch('src.services.groq_service.settings', MockSettingsValid()):
        service = GroqService(api_key="direct_key", model_id="direct_model")
        assert service.api_key == "direct_key"
        assert service.model_id == "direct_model"

def test_groq_service_init_no_api_key_fails():
    """Prueba que falla si no hay API key"""
    with patch('src.services.groq_service.settings', MockSettingsNoKey()):
        with pytest.raises(ValueError, match="GROQ_API_KEY es requerida"):
            GroqService()

def test_groq_service_init_empty_api_key_fails():
    """Prueba que falla si API key está vacía"""
    with patch('src.services.groq_service.settings', MockSettingsEmptyKey()):
        with pytest.raises(ValueError, match="GROQ_API_KEY no puede estar vacía"):
            GroqService()

def test_groq_service_init_uses_fallbacks(mock_groq_client):
    """Prueba que usa fallbacks cuando settings no tiene defaults"""
    with patch('src.services.groq_service.settings', MockSettingsMinimal()):
        service = GroqService()
        assert service.api_key == "test_api_key"
        assert service.model_id == "llama3-8b-8192"  # Fallback hardcodeado

# =============================================================================
# PRUEBAS DE SEND_PROMPT - FUNCIONALIDAD CORE
# =============================================================================

def test_send_prompt_success(mock_groq_client):
    """Prueba envío exitoso de prompt"""
    # Configurar respuesta mock
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Respuesta de prueba"
    mock_groq_client.chat.completions.create.return_value = mock_response

    with patch('src.services.groq_service.settings', MockSettingsValid()):
        service = GroqService()
        response = service.send_prompt("Hola")
        
        assert response == "Respuesta de prueba"
        mock_groq_client.chat.completions.create.assert_called_once()
        
        # Verificar que se pasaron los parámetros básicos
        call_args = mock_groq_client.chat.completions.create.call_args
        assert call_args[1]['messages'] == [{"role": "user", "content": "Hola"}]
        assert call_args[1]['model'] == "test_model_id"

def test_send_prompt_with_system_prompt(mock_groq_client):
    """Prueba envío con system prompt"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Respuesta con sistema"
    mock_groq_client.chat.completions.create.return_value = mock_response

    with patch('src.services.groq_service.settings', MockSettingsValid()):
        service = GroqService()
        response = service.send_prompt(
            prompt="Pregunta", 
            system_prompt="Eres un asistente útil"
        )
        
        assert response == "Respuesta con sistema"
        call_args = mock_groq_client.chat.completions.create.call_args
        expected_messages = [
            {"role": "system", "content": "Eres un asistente útil"},
            {"role": "user", "content": "Pregunta"}
        ]
        assert call_args[1]['messages'] == expected_messages

def test_send_prompt_with_custom_params(mock_groq_client):
    """Prueba envío con parámetros personalizados"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Respuesta personalizada"
    mock_groq_client.chat.completions.create.return_value = mock_response

    with patch('src.services.groq_service.settings', MockSettingsValid()):
        service = GroqService()
        response = service.send_prompt(
            prompt="Test",
            model_id="custom_model",
            max_tokens=200,
            temperature=0.8,
            timeout=45.0
        )
        
        assert response == "Respuesta personalizada"
        call_args = mock_groq_client.chat.completions.create.call_args
        assert call_args[1]['model'] == "custom_model"
        assert call_args[1]['max_tokens'] == 200
        assert call_args[1]['temperature'] == 0.8
        assert call_args[1]['timeout'] == 45.0

def test_send_prompt_uses_fallback_params(mock_groq_client):
    """Prueba que usa parámetros fallback cuando settings no los tiene"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Respuesta con fallbacks"
    mock_groq_client.chat.completions.create.return_value = mock_response

    with patch('src.services.groq_service.settings', MockSettingsMinimal()):
        service = GroqService()
        response = service.send_prompt("Test")

        assert response == "Respuesta con fallbacks"
        call_args = mock_groq_client.chat.completions.create.call_args
        assert call_args[1]['model'] == "llama3-8b-8192"  # Fallback del constructor
        assert call_args[1]['max_tokens'] == 1024         # Fallback de send_prompt
        assert call_args[1]['temperature'] == 0.7         # Fallback de send_prompt
        assert call_args[1]['timeout'] == 60.0            # Fallback de send_prompt

# =============================================================================
# PRUEBAS DE MANEJO DE ERRORES - COMPORTAMIENTO PRINCIPAL
# =============================================================================

def test_send_prompt_handles_connection_error(mock_groq_client):
    """Prueba que maneja errores de conexión y eventualmente retorna None"""
    # Crear excepción mínima que funcione
    mock_groq_client.chat.completions.create.side_effect = Exception("Simulando error de conexión")

    with patch('src.services.groq_service.settings', MockSettingsValid()):
        service = GroqService()
        response = service.send_prompt("Test")
        
        # Lo importante es que retorna None en caso de error
        assert response is None
        # Y que intentó hacer la llamada
        assert mock_groq_client.chat.completions.create.called

def test_send_prompt_eventually_succeeds_after_retry(mock_groq_client):
    """Prueba que eventualmente tiene éxito después de fallos iniciales"""
    mock_success_response = MagicMock()
    mock_success_response.choices = [MagicMock()]
    mock_success_response.choices[0].message.content = "Éxito después de retry"
    
    # Primer intento falla, segundo tiene éxito
    mock_groq_client.chat.completions.create.side_effect = [
        Exception("Fallo temporal"),
        mock_success_response
    ]

    with patch('src.services.groq_service.settings', MockSettingsValid()):
        service = GroqService()
        response = service.send_prompt("Test")
        
        assert response == "Éxito después de retry"
        assert mock_groq_client.chat.completions.create.call_count == 2

def test_send_prompt_returns_none_on_persistent_failure(mock_groq_client):
    """Prueba que retorna None si todos los reintentos fallan"""
    # Todos los intentos fallan
    mock_groq_client.chat.completions.create.side_effect = Exception("Error persistente")

    with patch('src.services.groq_service.settings', MockSettingsValid()):
        service = GroqService()
        response = service.send_prompt("Test")
        
        assert response is None
        # Debe haber intentado múltiples veces (debido al decorador @retry)
        assert mock_groq_client.chat.completions.create.call_count > 1

# =============================================================================
# PRUEBAS DE LOGGING - VERIFICACIÓN BÁSICA
# =============================================================================

@patch('src.services.groq_service.logger')
def test_logging_occurs_during_operations(mock_logger, mock_groq_client):
    """Prueba que se registran logs durante las operaciones"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_groq_client.chat.completions.create.return_value = mock_response

    with patch('src.services.groq_service.settings', MockSettingsValid()):
        service = GroqService()
        mock_logger.info.assert_called()  # Should log initialization
        
        service.send_prompt("Test")
        
        # Verificar que se registraron logs importantes
        assert any("inicializado" in str(call) for call in mock_logger.info.call_args_list)
        assert any("Enviando prompt" in str(call) for call in mock_logger.info.call_args_list)

# =============================================================================
# PRUEBAS DE INTEGRACIÓN BÁSICA
# =============================================================================

def test_groq_service_basic_workflow():
    """Prueba de flujo básico sin mocks complejos"""
    # Esta prueba verifica que la clase se puede instanciar y configurar correctamente
    # sin hacer llamadas reales a la API
    
    with patch('src.services.groq_service.settings', MockSettingsValid()), \
         patch('src.services.groq_service.Groq') as MockGroq:
        
        # Instanciar servicio
        service = GroqService()
        
        # Verificar configuración básica
        assert hasattr(service, 'api_key')
        assert hasattr(service, 'model_id')
        assert hasattr(service, 'client')
        
        # Verificar que se creó el cliente Groq
        MockGroq.assert_called_once_with(api_key="test_api_key")
