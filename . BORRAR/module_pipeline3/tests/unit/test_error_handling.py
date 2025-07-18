"""
Tests Unitarios para el Sistema de Manejo de Errores
====================================================

Este módulo contiene tests exhaustivos para verificar el funcionamiento
del sistema de manejo de errores implementado en error_handling.py.

Cobertura de tests:
- Excepciones personalizadas
- Respuestas de error estandarizadas
- Decoradores de retry
- Funciones de fallback por fase
- Logging estructurado
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import time
from datetime import datetime
from uuid import UUID, uuid4
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

# Importar el módulo a testear
from src.utils.error_handling import (
    # Excepciones
    PipelineException,
    ValidationError,
    GroqAPIError,
    SupabaseRPCError,
    ProcessingError,
    ServiceUnavailableError,
    FallbackExecuted,
    
    # Enums
    ErrorPhase,
    ErrorType,
    
    # Utilidades de respuesta
    create_error_response,
    create_validation_error_response,
    extract_validation_errors,
    async_create_error_response,
    
    # Utilidades de logging
    format_error_for_logging,
    
    # Decoradores
    retry_with_backoff,
    retry_groq_api,
    retry_supabase_rpc,
    no_retry,
    
    # Handlers de fallback
    handle_spacy_load_error_fase1,
    handle_groq_relevance_error_fase1,
    handle_groq_translation_fallback_fase1,
    handle_generic_phase_error,
    handle_groq_extraction_error_fase2,
    handle_json_parsing_error_fase2,
    handle_groq_citas_error_fase3,
    handle_normalization_error_fase4,
    handle_groq_relations_error_fase4,
    handle_importance_ml_error,
    handle_persistence_error_fase5,
)


# ============================================================================
# TESTS PARA EXCEPCIONES PERSONALIZADAS
# ============================================================================

class TestCustomExceptions:
    """Tests para las excepciones personalizadas del sistema."""
    
    def test_pipeline_exception_creation(self):
        """Verifica creación correcta de PipelineException."""
        exc = PipelineException(
            message="Error de prueba",
            error_type=ErrorType.INTERNAL_ERROR,
            phase=ErrorPhase.FASE_2_EXTRACCION,
            details={"key": "value"},
            article_id="art_123"
        )
        
        assert exc.message == "Error de prueba"
        assert exc.error_type == ErrorType.INTERNAL_ERROR
        assert exc.phase == ErrorPhase.FASE_2_EXTRACCION
        assert exc.details == {"key": "value"}
        assert exc.article_id == "art_123"
        assert exc.support_code.startswith("ERR_PIPE_FASE_2_EXTRACCION_")
        assert isinstance(exc.timestamp, datetime)
    
    def test_pipeline_exception_to_dict(self):
        """Verifica conversión de excepción a diccionario."""
        exc = PipelineException(
            message="Error de prueba",
            error_type=ErrorType.GROQ_API_ERROR,
            phase=ErrorPhase.FASE_1_TRIAJE
        )
        
        exc_dict = exc.to_dict()
        assert exc_dict["error"] == "groq_api_error"
        assert exc_dict["message"] == "Error de prueba"
        assert exc_dict["phase"] == "fase_1_triaje"
        assert "support_code" in exc_dict
        assert "timestamp" in exc_dict
    
    def test_validation_error_specific(self):
        """Verifica ValidationError con errores de validación específicos."""
        validation_errors = [
            {"field": "titulo", "error": "required"},
            {"field": "contenido", "error": "too_short"}
        ]
        
        exc = ValidationError(
            message="Validación fallida",
            validation_errors=validation_errors,
            phase=ErrorPhase.GENERAL,
            article_id="art_456"
        )
        
        assert exc.error_type == ErrorType.VALIDATION_ERROR
        assert exc.details["validation_errors"] == validation_errors
        assert exc.details["error_count"] == 2
    
    def test_groq_api_error_specific(self):
        """Verifica GroqAPIError con información de reintentos."""
        exc = GroqAPIError(
            message="Timeout en API",
            phase=ErrorPhase.FASE_2_EXTRACCION,
            retry_count=2,
            timeout_seconds=30,
            status_code=504,
            article_id="art_789"
        )
        
        assert exc.error_type == ErrorType.GROQ_API_ERROR
        assert exc.details["retry_count"] == 2
        assert exc.details["max_retries"] == 2
        assert exc.details["timeout_seconds"] == 30
        assert exc.details["status_code"] == 504
        assert exc.details["api_provider"] == "groq"
    
    def test_supabase_rpc_error_connection(self):
        """Verifica SupabaseRPCError para errores de conexión."""
        exc = SupabaseRPCError(
            message="Connection timeout",
            rpc_name="insertar_articulo_completo",
            is_connection_error=True,
            retry_count=1
        )
        
        assert exc.error_type == ErrorType.SUPABASE_ERROR
        assert exc.phase == ErrorPhase.FASE_5_PERSISTENCIA
        assert exc.details["is_connection_error"] is True
        assert exc.details["max_retries"] == 1
    
    def test_processing_error_with_fallback(self):
        """Verifica ProcessingError con indicación de fallback."""
        exc = ProcessingError(
            message="Fallo en procesamiento",
            phase=ErrorPhase.FASE_3_CITAS_DATOS,
            processing_step="parse_quotes",
            fallback_used=True,
            article_id="art_999"
        )
        
        assert exc.details["fallback_used"] is True
        assert exc.details["recovery_attempted"] is True
    
    def test_service_unavailable_error(self):
        """Verifica ServiceUnavailableError con información de estado."""
        exc = ServiceUnavailableError(
            retry_after=300,
            queue_size=150,
            workers_active=3
        )
        
        assert exc.error_type == ErrorType.SERVICE_UNAVAILABLE
        assert exc.details["retry_after"] == 300
        assert exc.details["queue_size"] == 150
        assert exc.details["workers_active"] == 3
        assert exc.details["status"] == "overloaded"


# ============================================================================
# TESTS PARA UTILIDADES DE RESPUESTA DE ERROR
# ============================================================================

class TestErrorResponses:
    """Tests para las funciones de creación de respuestas de error."""
    
    def test_create_error_response_validation_error(self):
        """Verifica respuesta para errores de validación."""
        exc = ValidationError(
            message="Error de validación",
            validation_errors=[
                "Campo 'titulo' es requerido",
                "Campo 'contenido' muy corto"
            ]
        )
        
        response = create_error_response(exc, request_id="req_test123")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        content = json.loads(response.body)
        assert content["error"] == "validation_error"
        assert content["mensaje"] == "Error de validación"
        assert len(content["detalles"]) == 2
        assert content["request_id"] == "req_test123"
    
    def test_create_error_response_service_unavailable(self):
        """Verifica respuesta para servicio no disponible."""
        exc = ServiceUnavailableError(retry_after=600)
        
        response = create_error_response(exc)
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        
        content = json.loads(response.body)
        assert content["error"] == "service_unavailable"
        assert content["retry_after"] == 600
        assert "request_id" in content
    
    def test_create_error_response_internal_error(self):
        """Verifica respuesta para errores internos."""
        exc = ProcessingError(
            message="Error interno",
            phase=ErrorPhase.FASE_2_EXTRACCION,
            processing_step="extraction"
        )
        
        response = create_error_response(exc)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
        content = json.loads(response.body)
        assert content["error"] == "internal_error"
        assert "support_code" in content
    
    def test_create_error_response_pydantic_validation(self):
        """Verifica manejo de errores de Pydantic."""
        # Simular un error de Pydantic
        try:
            from pydantic import BaseModel
            class TestModel(BaseModel):
                campo_requerido: str
                campo_numerico: int
            
            TestModel(campo_numerico="no es número")
        except PydanticValidationError as e:
            response = create_error_response(e)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            content = json.loads(response.body)
            assert content["error"] == "validation_error"
            assert len(content["detalles"]) > 0
    
    def test_create_validation_error_response_direct(self):
        """Verifica creación directa de respuesta de validación."""
        errors = [
            "El título es demasiado largo",
            "La fecha no tiene formato válido"
        ]
        
        response = create_validation_error_response(errors, "req_456")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        content = json.loads(response.body)
        assert content["detalles"] == errors
        assert content["request_id"] == "req_456"
    
    @pytest.mark.asyncio
    async def test_async_create_error_response(self):
        """Verifica versión asíncrona de create_error_response."""
        exc = GroqAPIError(
            message="API timeout",
            phase=ErrorPhase.FASE_3_CITAS_DATOS
        )
        
        response = await async_create_error_response(exc)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        content = json.loads(response.body)
        assert content["error"] == "internal_error"


# ============================================================================
# TESTS PARA UTILIDADES DE LOGGING
# ============================================================================

class TestLoggingUtilities:
    """Tests para las funciones de formateo de logs."""
    
    def test_format_error_for_logging_pipeline_exception(self):
        """Verifica formateo de PipelineException para logging."""
        exc = GroqAPIError(
            message="API failed",
            phase=ErrorPhase.FASE_2_EXTRACCION,
            retry_count=2,
            article_id="art_log_test"
        )
        
        log_data = format_error_for_logging(exc, context={"extra": "data"})
        
        assert log_data["module"] == "module_pipeline"
        assert log_data["message"] == "API failed"
        assert log_data["level"] == "ERROR"
        assert log_data["fase"] == "fase_2_extraccion"
        assert log_data["error_type"] == "groq_api_error"
        assert log_data["articulo_id"] == "art_log_test"
        assert log_data["context"]["extra"] == "data"
    
    def test_format_error_for_logging_generic_exception(self):
        """Verifica formateo de excepción genérica para logging."""
        exc = ValueError("Generic error")
        
        log_data = format_error_for_logging(exc)
        
        assert log_data["level"] == "ERROR"
        assert log_data["error_type"] == "unknown_error"
        assert log_data["message"] == "Generic error"


# ============================================================================
# TESTS PARA DECORADORES DE RETRY
# ============================================================================

class TestRetryDecorators:
    """Tests para los decoradores de reintentos."""
    
    def test_retry_with_backoff_success(self):
        """Verifica retry exitoso después de fallos."""
        attempt_count = 0
        
        @retry_with_backoff(max_attempts=3, wait_min=0.1, wait_max=0.2)
        def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError("Fail")
            return "Success"
        
        result = flaky_function()
        assert result == "Success"
        assert attempt_count == 3
    
    def test_retry_with_backoff_max_attempts_exceeded(self):
        """Verifica que se respeta el máximo de intentos."""
        attempt_count = 0
        
        @retry_with_backoff(max_attempts=2, wait_min=0.1, wait_max=0.2)
        def always_fails():
            nonlocal attempt_count
            attempt_count += 1
            raise ConnectionError("Always fails")
        
        with pytest.raises(ConnectionError):
            always_fails()
        
        assert attempt_count == 2
    
    def test_retry_groq_api_decorator(self):
        """Verifica decorador específico para Groq API."""
        # Test simplificado que verifica el comportamiento del decorador
        # sin depender de las excepciones específicas de Groq
        attempt_count = 0
        
        @retry_groq_api(max_attempts=1, wait_seconds=0.1)
        def call_groq():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                # Usar una excepción genérica que el decorador debería reintentar
                raise ConnectionError("Connection failed")
            return "Success"
        
        result = call_groq()
        assert result == "Success"
        assert attempt_count == 2
    
    def test_retry_supabase_rpc_connection_error(self):
        """Verifica retry para errores de conexión en Supabase."""
        attempt_count = 0
        
        @retry_supabase_rpc(connection_retries=1)
        def call_supabase():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise ConnectionError("Connection lost")
            return "Success"
        
        result = call_supabase()
        assert result == "Success"
        assert attempt_count == 2
    
    def test_retry_supabase_rpc_validation_no_retry(self):
        """Verifica que no hay retry para errores de validación."""
        attempt_count = 0
        
        @retry_supabase_rpc()
        def call_supabase_validation():
            nonlocal attempt_count
            attempt_count += 1
            raise ValueError("Validation error")
        
        with pytest.raises(SupabaseRPCError) as exc_info:
            call_supabase_validation()
        
        assert attempt_count == 1
        assert not exc_info.value.details["is_connection_error"]
    
    def test_no_retry_decorator(self):
        """Verifica decorador no_retry."""
        @no_retry
        def critical_function():
            return "No retry needed"
        
        result = critical_function()
        assert result == "No retry needed"


# ============================================================================
# TESTS PARA HANDLERS DE FALLBACK
# ============================================================================

class TestFallbackHandlers:
    """Tests para las funciones de manejo de fallback por fase."""
    
    def test_handle_spacy_load_error_fase1(self):
        """Verifica fallback para error de carga de spaCy."""
        result = handle_spacy_load_error_fase1(
            article_id="art_spacy_test",
            model_name="es_core_news_lg",
            exception=ImportError("Model not found")
        )
        
        assert result["es_relevante"] is True
        assert result["decision_triaje"] == "FALLBACK_ACEPTADO_ERROR_PREPROCESO"
        assert "spaCy" in result["justificacion_triaje"]
        assert result["metadatos_specificos_triaje"]["error_type"] == "SPACY_MODEL_LOAD_FAILURE"
    
    def test_handle_groq_relevance_error_fase1(self):
        """Verifica fallback para error de relevancia con Groq."""
        result = handle_groq_relevance_error_fase1(
            article_id="art_groq_test",
            text_cleaned="Texto de prueba para análisis",
            exception=TimeoutError("API timeout")
        )
        
        assert result["es_relevante"] is True
        assert result["decision_triaje"] == "FALLBACK_ACEPTADO_ERROR_LLM"
        assert result["texto_para_siguiente_fase"] == "Texto de prueba para análisis"
    
    def test_handle_groq_extraction_error_fase2(self):
        """Verifica fallback para error de extracción en fase 2."""
        result = handle_groq_extraction_error_fase2(
            article_id="art_ext_test",
            titulo="Noticia importante sobre economía",
            medio="El País",
            exception=ConnectionError("API down")
        )
        
        assert len(result["hechos_extraidos"]) == 1
        assert result["hechos_extraidos"][0]["texto_original_del_hecho"] == "Noticia importante sobre economía"
        assert len(result["entidades_extraidas"]) == 1
        assert result["entidades_extraidas"][0]["texto_entidad"] == "El País"
        assert len(result["advertencias"]) > 0
    
    def test_handle_json_parsing_error_fase2(self):
        """Verifica manejo de errores de parseo JSON."""
        malformed_json = '{"hechos": [{"id": 1, "contenido": "Test"'
        
        result = handle_json_parsing_error_fase2(
            article_id="art_json_test",
            json_response=malformed_json,
            exception=json.JSONDecodeError("Expecting ']'", malformed_json, 50)
        )
        
        # Debería recurrir al fallback básico
        assert "hechos_extraidos" in result
        assert "entidades_extraidas" in result
    
    def test_handle_groq_citas_error_fase3(self):
        """Verifica fallback para error en extracción de citas."""
        result = handle_groq_citas_error_fase3(
            article_id="art_citas_test",
            exception=RuntimeError("Model overloaded")
        )
        
        assert result["citas_textuales_extraidas"] == []
        assert result["datos_cuantitativos_extraidos"] == []
        assert "omitida por fallo" in result["advertencias_citas_datos"][0]
    
    def test_handle_normalization_error_fase4(self):
        """Verifica fallback para error de normalización."""
        # Mock de entidades
        entidades = [
            Mock(
                id_entidad_normalizada=uuid4(),
                nombre_entidad_normalizada="Test Entity",
                similitud_normalizacion=0.9
            )
            for _ in range(3)
        ]
        
        result = handle_normalization_error_fase4(
            article_id="art_norm_test",
            entidades=entidades,
            exception=ConnectionError("DB unavailable")
        )
        
        # Verificar que todas las entidades se marcan como nuevas
        for entidad in result:
            assert entidad.id_entidad_normalizada is None
            assert entidad.nombre_entidad_normalizada is None
            assert entidad.similitud_normalizacion == 0.0
    
    def test_handle_groq_relations_error_fase4(self):
        """Verifica fallback para error en extracción de relaciones."""
        result = handle_groq_relations_error_fase4(
            article_id="art_rel_test",
            exception=TimeoutError("Timeout")
        )
        
        assert result["relaciones_hecho_entidad"] == []
        assert result["relaciones_hecho_hecho"] == []
        assert result["relaciones_entidad_entidad"] == []
        assert result["contradicciones"] == []
        assert "indices" in result
    
    def test_handle_importance_ml_error(self):
        """Verifica fallback para error en modelo ML de importancia."""
        result = handle_importance_ml_error(
            article_id="art_ml_test",
            exception=FileNotFoundError("Model not found")
        )
        
        assert result == 5  # Valor por defecto según documentación
    
    def test_handle_persistence_error_fase5(self):
        """Verifica fallback para error de persistencia."""
        datos_test = {
            "articulo": {"id": "art_123", "titulo": "Test"},
            "hechos": [{"id": 1, "contenido": "Hecho test"}]
        }
        
        result = handle_persistence_error_fase5(
            article_id="art_persist_test",
            datos_completos=datos_test,
            exception=RuntimeError("RPC failed")
        )
        
        assert result["status"] == "ERROR_PERSISTENCIA"
        assert result["article_id"] == "art_persist_test"
        assert result["datos_para_revision"] == datos_test
        assert "tabla de errores" in result["mensaje"]
    
    def test_handle_generic_phase_error(self):
        """Verifica handler genérico de errores por fase."""
        result = handle_generic_phase_error(
            article_id="art_generic_test",
            phase=ErrorPhase.FASE_2_EXTRACCION,
            step_failed="json_parsing",
            exception=ValueError("Unexpected format")
        )
        
        assert result["id_fragmento"] == "art_generic_test"
        assert result["status"] == "ERROR"
        assert result["phase_name"] == "fase_2_extraccion"
        assert result["error_type"] == "PROCESSING_ERROR"
        assert result["step_failed"] == "json_parsing"


# ============================================================================
# TESTS DE INTEGRACIÓN
# ============================================================================

class TestIntegration:
    """Tests de integración para verificar el sistema completo."""
    
    @patch('src.utils.error_handling.logger')
    def test_error_flow_with_logging(self, mock_logger):
        """Verifica flujo completo de error con logging."""
        # Crear excepción
        exc = GroqAPIError(
            message="API timeout",
            phase=ErrorPhase.FASE_2_EXTRACCION,
            retry_count=3,
            article_id="art_integration"
        )
        
        # Crear respuesta de error
        response = create_error_response(exc)
        
        # Verificar respuesta
        assert response.status_code == 500
        content = json.loads(response.body)
        assert content["error"] == "internal_error"
        
        # Formatear para logging
        log_data = format_error_for_logging(exc)
        assert log_data["error_type"] == "groq_api_error"
    
    def test_retry_decorator_with_custom_exception(self):
        """Verifica decorador retry con excepciones personalizadas."""
        attempt_count = 0
        
        @retry_with_backoff(
            max_attempts=2,
            wait_min=0.1,
            exceptions=(GroqAPIError,)
        )
        def api_call():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise GroqAPIError(
                    "API failed",
                    phase=ErrorPhase.FASE_1_TRIAJE
                )
            return "Success"
        
        result = api_call()
        assert result == "Success"
        assert attempt_count == 2
    
    def test_fallback_chain_fase2(self):
        """Verifica cadena de fallbacks en fase 2."""
        # Simular fallo de Groq -> JSON malformado -> fallback básico
        
        # Primer intento: Groq falla
        result1 = handle_groq_extraction_error_fase2(
            article_id="art_chain",
            titulo="Título de prueba",
            exception=TimeoutError()
        )
        
        assert len(result1["hechos_extraidos"]) == 1
        assert result1["hechos_extraidos"][0]["metadata_hecho"]["es_fallback"] is True
        
        # Segundo intento: JSON malformado recurre al mismo fallback
        result2 = handle_json_parsing_error_fase2(
            article_id="art_chain",
            json_response='{"invalid json',
            exception=json.JSONDecodeError("test", "", 0)
        )
        
        assert "hechos_extraidos" in result2


# ============================================================================
# FIXTURES Y CONFIGURACIÓN
# ============================================================================

@pytest.fixture
def mock_article_id():
    """Fixture para ID de artículo de prueba."""
    return str(uuid4())


@pytest.fixture
def mock_fragment_id():
    """Fixture para ID de fragmento de prueba."""
    return uuid4()


@pytest.fixture
def sample_pipeline_exception():
    """Fixture para excepción de pipeline de muestra."""
    return PipelineException(
        message="Test exception",
        error_type=ErrorType.PROCESSING_ERROR,
        phase=ErrorPhase.FASE_3_CITAS_DATOS,
        details={"test": True},
        article_id="test_article"
    )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
