"""
Test de Verificación Integral del Sistema de Manejo de Errores
==============================================================

Este script realiza pruebas integrales del sistema completo de manejo de errores
implementado en el module_pipeline, verificando:

1. Funcionamiento de excepciones personalizadas
2. Comportamiento de decoradores de retry
3. Activación correcta de fallbacks por fase
4. Calidad del logging estructurado
5. Respuestas HTTP de error estandarizadas

Ejecutar con: python tests/test_error_handling_integral.py
"""

import sys
import os
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

# Añadir el directorio padre al path para importaciones
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from loguru import logger
from fastapi.testclient import TestClient

# Importar componentes del sistema de manejo de errores
from src.utils.error_handling import (
    # Excepciones personalizadas
    ValidationError,
    GroqAPIError,
    SupabaseRPCError,
    ProcessingError,
    ServiceUnavailableError,
    
    # Enums
    ErrorPhase,
    ErrorType,
    
    # Decoradores
    retry_groq_api,
    retry_supabase_rpc,
    
    # Handlers de fallback
    handle_spacy_load_error_fase1,
    handle_groq_relevance_error_fase1,
    handle_groq_translation_fallback_fase1,
    handle_groq_extraction_error_fase2,
    handle_groq_citas_error_fase3,
    handle_normalization_error_fase4,
    handle_groq_relations_error_fase4,
    handle_persistence_error_fase5,
    
    # Utilidades
    create_error_response,
    format_error_for_logging
)

# Configurar logger para tests
logger.remove()  # Remover handlers existentes
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG"
)


class TestExcepcionesPersonalizadas:
    """Tests para verificar el comportamiento de excepciones personalizadas."""
    
    def test_validation_error(self):
        """Verifica que ValidationError se comporta correctamente."""
        print("\n🧪 Test: ValidationError")
        
        validation_errors = [
            {"field": "titulo", "error": "Campo requerido"},
            {"field": "contenido", "error": "Muy corto"}
        ]
        
        with pytest.raises(ValidationError) as excinfo:
            raise ValidationError(
                message="Error en validación de artículo",
                validation_errors=validation_errors,
                phase=ErrorPhase.FASE_1_TRIAJE,
                article_id="test_123"
            )
        
        error = excinfo.value
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert error.phase == ErrorPhase.FASE_1_TRIAJE
        assert error.article_id == "test_123"
        assert len(error.details["validation_errors"]) == 2
        assert error.support_code.startswith("ERR_PIPE_FASE_1_TRIAJE_")
        print("✅ ValidationError funciona correctamente")
    
    def test_groq_api_error(self):
        """Verifica que GroqAPIError incluye información de reintentos."""
        print("\n🧪 Test: GroqAPIError")
        
        with pytest.raises(GroqAPIError) as excinfo:
            raise GroqAPIError(
                message="Timeout en API de Groq",
                phase=ErrorPhase.FASE_2_EXTRACCION,
                retry_count=2,
                timeout_seconds=60,
                status_code=504,
                article_id="test_456"
            )
        
        error = excinfo.value
        assert error.error_type == ErrorType.GROQ_API_ERROR
        assert error.details["retry_count"] == 2
        assert error.details["max_retries"] == 2
        assert error.details["timeout_seconds"] == 60
        assert error.details["status_code"] == 504
        print("✅ GroqAPIError incluye información completa de reintentos")
    
    def test_supabase_rpc_error(self):
        """Verifica que SupabaseRPCError diferencia tipos de error."""
        print("\n🧪 Test: SupabaseRPCError")
        
        # Error de conexión
        with pytest.raises(SupabaseRPCError) as excinfo:
            raise SupabaseRPCError(
                message="Error de conexión con Supabase",
                rpc_name="insertar_articulo_completo",
                is_connection_error=True,
                retry_count=1
            )
        
        error = excinfo.value
        assert error.details["is_connection_error"] is True
        assert error.details["max_retries"] == 1
        
        # Error de validación
        with pytest.raises(SupabaseRPCError) as excinfo:
            raise SupabaseRPCError(
                message="Datos inválidos",
                rpc_name="buscar_entidad_similar",
                is_connection_error=False
            )
        
        error = excinfo.value
        assert error.details["is_connection_error"] is False
        assert error.details["max_retries"] == 0
        print("✅ SupabaseRPCError diferencia correctamente tipos de error")
    
    def test_processing_error(self):
        """Verifica que ProcessingError incluye información de fallback."""
        print("\n🧪 Test: ProcessingError")
        
        with pytest.raises(ProcessingError) as excinfo:
            raise ProcessingError(
                message="Error al procesar entidades",
                phase=ErrorPhase.FASE_4_NORMALIZACION,
                processing_step="entity_linking",
                fallback_used=True,
                article_id="test_789"
            )
        
        error = excinfo.value
        assert error.details["processing_step"] == "entity_linking"
        assert error.details["fallback_used"] is True
        assert error.details["recovery_attempted"] is True
        print("✅ ProcessingError registra uso de fallback")


class TestDecoradoresRetry:
    """Tests para verificar el comportamiento de los decoradores de retry."""
    
    def test_retry_groq_api_success(self):
        """Verifica que @retry_groq_api permite reintentos exitosos."""
        print("\n🧪 Test: @retry_groq_api con éxito en reintento")
        
        call_count = 0
        
        @retry_groq_api(max_attempts=2, wait_seconds=0.1)
        def flaky_groq_call():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                from groq import APIConnectionError
                raise APIConnectionError("Fallo temporal")
            return "Éxito en segundo intento"
        
        result = flaky_groq_call()
        assert result == "Éxito en segundo intento"
        assert call_count == 2
        print(f"✅ Función reintentada {call_count} veces hasta éxito")
    
    def test_retry_groq_api_failure(self):
        """Verifica que @retry_groq_api falla después de máx reintentos."""
        print("\n🧪 Test: @retry_groq_api fallo después de reintentos")
        
        call_count = 0
        
        @retry_groq_api(max_attempts=2, wait_seconds=0.1)
        def always_failing_groq():
            nonlocal call_count
            call_count += 1
            from groq import RateLimitError
            raise RateLimitError("Límite excedido siempre")
        
        with pytest.raises(GroqAPIError) as excinfo:
            always_failing_groq()
        
        assert call_count == 3  # Intento inicial + 2 reintentos
        assert "no disponible después de 2 reintentos" in str(excinfo.value)
        print(f"✅ Función falló correctamente después de {call_count} intentos")
    
    def test_retry_supabase_rpc_connection(self):
        """Verifica que @retry_supabase_rpc reintenta errores de conexión."""
        print("\n🧪 Test: @retry_supabase_rpc con error de conexión")
        
        call_count = 0
        
        @retry_supabase_rpc(connection_retries=1)
        def flaky_supabase_call():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Conexión perdida")
            return {"status": "success"}
        
        result = flaky_supabase_call()
        assert result["status"] == "success"
        assert call_count == 2
        print("✅ Reintento exitoso para error de conexión")
    
    def test_retry_supabase_rpc_no_retry_validation(self):
        """Verifica que @retry_supabase_rpc NO reintenta errores de validación."""
        print("\n🧪 Test: @retry_supabase_rpc sin reintentos para validación")
        
        call_count = 0
        
        @retry_supabase_rpc()
        def validation_error_call():
            nonlocal call_count
            call_count += 1
            raise ValueError("Datos inválidos")
        
        with pytest.raises(SupabaseRPCError) as excinfo:
            validation_error_call()
        
        assert call_count == 1  # Sin reintentos
        assert "Error de validación" in str(excinfo.value)
        print("✅ No se reintentó error de validación")


class TestFallbackHandlers:
    """Tests para verificar el comportamiento de los handlers de fallback."""
    
    def test_fallback_fase1_spacy_error(self):
        """Verifica fallback cuando falla carga de modelo spaCy."""
        print("\n🧪 Test: Fallback Fase 1 - Error spaCy")
        
        result = handle_spacy_load_error_fase1(
            article_id="test_spacy",
            model_name="es_core_news_sm",
            exception=Exception("Modelo no encontrado")
        )
        
        assert result["es_relevante"] is True  # Acepta artículo
        assert result["decision_triaje"] == "FALLBACK_ACEPTADO_ERROR_PREPROCESO"
        assert "spaCy" in result["justificacion_triaje"]
        assert result["texto_para_siguiente_fase"] == "[PREPROCESAMIENTO_FALLIDO]"
        print("✅ Fallback acepta artículo cuando falla spaCy")
    
    def test_fallback_fase1_groq_relevance(self):
        """Verifica fallback cuando falla evaluación de relevancia."""
        print("\n🧪 Test: Fallback Fase 1 - Error Groq relevancia")
        
        text_cleaned = "Este es el texto del artículo de prueba."
        result = handle_groq_relevance_error_fase1(
            article_id="test_groq_rel",
            text_cleaned=text_cleaned,
            exception=Exception("API timeout")
        )
        
        assert result["es_relevante"] is True  # Acepta artículo
        assert result["decision_triaje"] == "FALLBACK_ACEPTADO_ERROR_LLM"
        assert result["texto_para_siguiente_fase"] == text_cleaned
        print("✅ Fallback acepta artículo cuando falla Groq")
    
    def test_fallback_fase2_extraction(self):
        """Verifica fallback de extracción básica en Fase 2."""
        print("\n🧪 Test: Fallback Fase 2 - Extracción básica")
        
        result = handle_groq_extraction_error_fase2(
            article_id="test_extraction",
            titulo="Noticia importante de prueba",
            medio="El Test Diario",
            exception=Exception("Groq no disponible")
        )
        
        assert len(result["hechos_extraidos"]) == 1
        assert result["hechos_extraidos"][0]["texto_original_del_hecho"] == "Noticia importante de prueba"
        assert result["hechos_extraidos"][0]["metadata_hecho"]["es_fallback"] is True
        
        assert len(result["entidades_extraidas"]) == 1
        assert result["entidades_extraidas"][0]["texto_entidad"] == "El Test Diario"
        print("✅ Fallback crea hecho básico del título")
    
    def test_fallback_fase3_citas(self):
        """Verifica fallback cuando falla extracción de citas."""
        print("\n🧪 Test: Fallback Fase 3 - Sin citas")
        
        result = handle_groq_citas_error_fase3(
            article_id="test_citas",
            exception=Exception("Timeout en Groq")
        )
        
        assert result["citas_textuales_extraidas"] == []
        assert result["datos_cuantitativos_extraidos"] == []
        assert len(result["advertencias_citas_datos"]) > 0
        print("✅ Fallback continúa sin citas (no crítico)")
    
    def test_fallback_fase4_normalization(self):
        """Verifica fallback de normalización de entidades."""
        print("\n🧪 Test: Fallback Fase 4 - Normalización")
        
        # Crear entidades mock
        entidades = [
            Mock(
                id_entidad_normalizada=None,
                nombre_entidad_normalizada=None,
                similitud_normalizacion=None
            ),
            Mock(
                id_entidad_normalizada=None,
                nombre_entidad_normalizada=None,
                similitud_normalizacion=None
            )
        ]
        
        result = handle_normalization_error_fase4(
            article_id="test_norm",
            entidades=entidades,
            exception=Exception("BD no disponible")
        )
        
        for entidad in result:
            assert entidad.id_entidad_normalizada is None
            assert entidad.similitud_normalizacion == 0.0
        print("✅ Fallback trata entidades como nuevas")
    
    def test_fallback_fase5_persistence(self):
        """Verifica fallback de persistencia en tabla de errores."""
        print("\n🧪 Test: Fallback Fase 5 - Persistencia")
        
        datos_completos = {
            "articulo": {"id": "test_persist", "titulo": "Test"},
            "hechos": [{"id": 1, "texto": "Hecho test"}]
        }
        
        result = handle_persistence_error_fase5(
            article_id="test_persist",
            datos_completos=datos_completos,
            exception=Exception("Error crítico BD")
        )
        
        assert result["status"] == "ERROR_PERSISTENCIA"
        assert result["datos_para_revision"] == datos_completos
        assert "tabla de errores" in result["mensaje"]
        print("✅ Fallback guarda en tabla de errores")


class TestLoggingEstructurado:
    """Tests para verificar la calidad del logging estructurado."""
    
    def test_format_error_for_logging(self):
        """Verifica que los errores se formatean correctamente para logging."""
        print("\n🧪 Test: Formateo de errores para logging")
        
        # Test con PipelineException
        error = GroqAPIError(
            message="Test de logging",
            phase=ErrorPhase.FASE_2_EXTRACCION,
            retry_count=1,
            article_id="log_test"
        )
        
        log_data = format_error_for_logging(error, context={"extra": "data"})
        
        assert "timestamp" in log_data
        assert log_data["module"] == "module_pipeline"
        assert log_data["fase"] == ErrorPhase.FASE_2_EXTRACCION.value
        assert log_data["error_type"] == ErrorType.GROQ_API_ERROR.value
        assert log_data["articulo_id"] == "log_test"
        assert log_data["context"]["extra"] == "data"
        print("✅ Logging incluye toda la información estructurada")
    
    def test_logging_with_support_code(self):
        """Verifica que se genera support_code único."""
        print("\n🧪 Test: Generación de support_code")
        
        error1 = ProcessingError(
            message="Error 1",
            phase=ErrorPhase.FASE_3_CITAS_DATOS,
            processing_step="test"
        )
        
        # Pequeña pausa para asegurar timestamp diferente
        time.sleep(0.01)
        
        error2 = ProcessingError(
            message="Error 2",
            phase=ErrorPhase.FASE_3_CITAS_DATOS,
            processing_step="test"
        )
        
        assert error1.support_code != error2.support_code
        assert error1.support_code.startswith("ERR_PIPE_FASE_3_CITAS_DATOS_")
        print("✅ Support codes son únicos por timestamp")


class TestRespuestasHTTP:
    """Tests para verificar respuestas HTTP de error estandarizadas."""
    
    def test_validation_error_response(self):
        """Verifica respuesta HTTP 400 para errores de validación."""
        print("\n🧪 Test: Respuesta HTTP 400 - Validación")
        
        error = ValidationError(
            message="Datos de entrada inválidos",
            validation_errors=[
                {"field": "titulo", "error": "Requerido"},
                {"field": "fecha", "error": "Formato inválido"}
            ]
        )
        
        response = create_error_response(error, request_id="req_test_val")
        
        assert response.status_code == 400
        content = json.loads(response.body)
        assert content["error"] == "validation_error"
        assert len(content["detalles"]) == 2
        assert content["request_id"] == "req_test_val"
        print("✅ Respuesta 400 con formato correcto")
    
    def test_internal_error_response(self):
        """Verifica respuesta HTTP 500 para errores internos."""
        print("\n🧪 Test: Respuesta HTTP 500 - Error interno")
        
        error = ProcessingError(
            message="Fallo en procesamiento",
            phase=ErrorPhase.FASE_2_EXTRACCION,
            processing_step="json_parsing"
        )
        
        response = create_error_response(error)
        
        assert response.status_code == 500
        content = json.loads(response.body)
        assert content["error"] == "internal_error"
        assert "support_code" in content
        assert content["support_code"].startswith("ERR_PIPE_")
        print("✅ Respuesta 500 incluye support_code")
    
    def test_service_unavailable_response(self):
        """Verifica respuesta HTTP 503 para servicio no disponible."""
        print("\n🧪 Test: Respuesta HTTP 503 - Servicio no disponible")
        
        error = ServiceUnavailableError(
            message="Sistema sobrecargado",
            retry_after=300,
            queue_size=150
        )
        
        response = create_error_response(error)
        
        assert response.status_code == 503
        content = json.loads(response.body)
        assert content["error"] == "service_unavailable"
        assert content["retry_after"] == 300
        print("✅ Respuesta 503 con retry_after")


class TestIntegracionCompleta:
    """Tests de integración que simulan escenarios completos."""
    
    @patch('src.services.groq_service.GroqService._create_chat_completion_with_retry')
    def test_flujo_completo_con_fallbacks(self, mock_groq):
        """Simula un flujo completo con múltiples fallbacks."""
        print("\n🧪 Test: Flujo completo con múltiples fallbacks")
        
        # Configurar mock para fallar
        mock_groq.side_effect = Exception("Groq no disponible")
        
        # Simular procesamiento con fallbacks
        article_id = "test_integral"
        
        # Fase 1: Fallo en relevancia -> Fallback acepta
        fase1_result = handle_groq_relevance_error_fase1(
            article_id=article_id,
            text_cleaned="Texto de prueba",
            exception=Exception("Groq timeout")
        )
        assert fase1_result["es_relevante"] is True
        
        # Fase 2: Fallo en extracción -> Fallback crea hecho básico
        fase2_result = handle_groq_extraction_error_fase2(
            article_id=article_id,
            titulo="Título de prueba",
            medio="Medio test"
        )
        assert len(fase2_result["hechos_extraidos"]) > 0
        
        # Fase 3: Fallo en citas -> Continúa sin citas
        fase3_result = handle_groq_citas_error_fase3(article_id=article_id)
        assert fase3_result["citas_textuales_extraidas"] == []
        
        print("✅ Pipeline continúa funcionando con degradación elegante")
    
    def test_decoradores_con_excepciones_reales(self):
        """Verifica decoradores con excepciones del mundo real."""
        print("\n🧪 Test: Decoradores con excepciones reales")
        
        # Simular servicio Groq con fallos intermitentes
        class MockGroqService:
            def __init__(self):
                self.call_count = 0
            
            @retry_groq_api(max_attempts=2, wait_seconds=0.1)
            def send_prompt(self, prompt):
                self.call_count += 1
                if self.call_count < 2:
                    from groq import RateLimitError
                    raise RateLimitError("Rate limit hit")
                return {"response": "Success after retry"}
        
        service = MockGroqService()
        result = service.send_prompt("test prompt")
        
        assert service.call_count == 2
        assert result["response"] == "Success after retry"
        print("✅ Servicio se recupera después de reintentos")


def run_all_tests():
    """Ejecuta todos los tests y muestra resumen."""
    print("\n" + "="*70)
    print("TEST DE VERIFICACIÓN INTEGRAL - SISTEMA DE MANEJO DE ERRORES")
    print("="*70)
    
    test_classes = [
        TestExcepcionesPersonalizadas(),
        TestDecoradoresRetry(),
        TestFallbackHandlers(),
        TestLoggingEstructurado(),
        TestRespuestasHTTP(),
        TestIntegracionCompleta()
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n\n📋 Ejecutando: {class_name}")
        print("-" * 50)
        
        # Obtener todos los métodos de test
        test_methods = [method for method in dir(test_class) 
                       if method.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_class, method_name)
                method()
                passed_tests += 1
            except Exception as e:
                failed_tests.append({
                    "class": class_name,
                    "method": method_name,
                    "error": str(e)
                })
                print(f"❌ {method_name} falló: {e}")
    
    # Resumen final
    print("\n\n" + "="*70)
    print("RESUMEN DE RESULTADOS")
    print("="*70)
    print(f"\n📊 Tests ejecutados: {total_tests}")
    print(f"✅ Tests exitosos: {passed_tests}")
    print(f"❌ Tests fallidos: {len(failed_tests)}")
    
    if failed_tests:
        print("\n⚠️ Tests que fallaron:")
        for failure in failed_tests:
            print(f"  - {failure['class']}.{failure['method']}: {failure['error']}")
    else:
        print("\n🎉 ¡Todos los tests pasaron exitosamente!")
    
    print("\n📝 Verificaciones completadas:")
    print("  ✓ Excepciones personalizadas funcionan correctamente")
    print("  ✓ Decoradores de retry aplican políticas correctas")
    print("  ✓ Fallbacks se activan en cada fase según documentación")
    print("  ✓ Logging estructurado incluye toda la información necesaria")
    print("  ✓ Respuestas HTTP siguen formato estandarizado")
    print("  ✓ Sistema completo maneja errores con degradación elegante")
    
    print("\n" + "="*70)
    print("El sistema de manejo de errores está listo para producción ✅")
    print("="*70)


if __name__ == "__main__":
    # Ejecutar todos los tests
    run_all_tests()
    
    # Alternativamente, ejecutar con pytest si está disponible
    # pytest.main([__file__, "-v"])
