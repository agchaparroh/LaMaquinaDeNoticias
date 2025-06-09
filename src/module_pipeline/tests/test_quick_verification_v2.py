"""
Test rápido para verificar el sistema de manejo de errores - V2
===============================================================

Versión corregida que maneja correctamente los atributos de las excepciones.
"""

import sys
from pathlib import Path

# Añadir el directorio src al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from uuid import uuid4
import json

# Importar componentes del sistema de manejo de errores
from src.utils.error_handling import (
    PipelineException,
    ValidationError,
    GroqAPIError,
    ErrorPhase,
    ErrorType,
    create_error_response,
    retry_with_backoff,
    handle_groq_extraction_error_fase2,
    handle_groq_citas_error_fase3,
    format_error_for_logging
)

def test_custom_exceptions():
    """Test 1: Verificar creación de excepciones personalizadas."""
    print("\n🧪 Test 1: Excepciones personalizadas")
    print("-" * 40)
    
    try:
        # Crear excepción de validación
        exc = ValidationError(
            message="Campo requerido faltante",
            validation_errors=[
                {"field": "titulo", "error": "required"},
                {"field": "contenido", "error": "too_short"}
            ],
            phase=ErrorPhase.GENERAL,
            article_id="test_123"
        )
        
        print(f"✅ ValidationError creada correctamente")
        print(f"   - Tipo de error: {exc.error_type.value}")
        print(f"   - Errores: {exc.details['error_count']}")
        print(f"   - Support code: {exc.support_code}")
        
        # Verificar método to_dict
        exc_dict = exc.to_dict()
        print(f"   - Serialización exitosa: {bool(exc_dict)}")
        
        # Crear excepción de Groq API
        groq_exc = GroqAPIError(
            message="Timeout en API",
            phase=ErrorPhase.FASE_2_EXTRACCION,
            retry_count=2,
            timeout_seconds=30
        )
        
        print(f"\n✅ GroqAPIError creada correctamente")
        print(f"   - Fase: {groq_exc.phase.value}")
        print(f"   - Reintentos: {groq_exc.details['retry_count']}/{groq_exc.details['max_retries']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_responses():
    """Test 2: Verificar respuestas de error HTTP."""
    print("\n🧪 Test 2: Respuestas de error HTTP")
    print("-" * 40)
    
    try:
        # Test respuesta de validación usando lista de strings simple
        exc = ValidationError(
            message="Datos inválidos",
            validation_errors=[
                {"field": "titulo", "message": "El título es muy corto"}
            ],
            phase=ErrorPhase.GENERAL
        )
        
        response = create_error_response(exc, request_id="req_test_123")
        
        print(f"✅ Respuesta de validación creada")
        print(f"   - Status code: {response.status_code}")
        
        content = json.loads(response.body)
        print(f"   - Error type: {content['error']}")
        print(f"   - Request ID: {content['request_id']}")
        print(f"   - Tiene detalles: {'detalles' in content}")
        
        # Test respuesta de error interno
        internal_exc = PipelineException(
            message="Error procesando",
            error_type=ErrorType.PROCESSING_ERROR,
            phase=ErrorPhase.FASE_3_CITAS_DATOS
        )
        
        internal_response = create_error_response(internal_exc)
        print(f"\n✅ Respuesta de error interno creada")
        print(f"   - Status code: {internal_response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_retry_decorator():
    """Test 3: Verificar decoradores de retry."""
    print("\n🧪 Test 3: Decoradores de retry")
    print("-" * 40)
    
    try:
        attempt_count = 0
        
        @retry_with_backoff(max_attempts=3, wait_min=0.1, wait_max=0.2)
        def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            print(f"   - Intento #{attempt_count}")
            if attempt_count < 2:
                raise ConnectionError("Simulando fallo")
            return "Éxito"
        
        result = flaky_function()
        
        print(f"✅ Retry funcionó correctamente")
        print(f"   - Intentos totales: {attempt_count}")
        print(f"   - Resultado: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_fallback_handlers():
    """Test 4: Verificar handlers de fallback."""
    print("\n🧪 Test 4: Handlers de fallback")
    print("-" * 40)
    
    try:
        # Test fallback fase 2
        result_fase2 = handle_groq_extraction_error_fase2(
            article_id="test_art_123",
            titulo="Noticia de prueba sobre tecnología",
            medio="TechNews",
            exception=TimeoutError("API timeout")
        )
        
        print(f"✅ Fallback Fase 2 ejecutado")
        print(f"   - Hechos creados: {len(result_fase2['hechos_extraidos'])}")
        print(f"   - Hecho: {result_fase2['hechos_extraidos'][0]['texto_original_del_hecho']}")
        print(f"   - Entidades creadas: {len(result_fase2['entidades_extraidas'])}")
        print(f"   - Entidad: {result_fase2['entidades_extraidas'][0]['texto_entidad']}")
        
        # Test fallback fase 3
        result_fase3 = handle_groq_citas_error_fase3(
            article_id="test_art_456",
            exception=RuntimeError("Model overloaded")
        )
        
        print(f"\n✅ Fallback Fase 3 ejecutado")
        print(f"   - Citas extraídas: {len(result_fase3['citas_textuales_extraidas'])}")
        print(f"   - Datos extraídos: {len(result_fase3['datos_cuantitativos_extraidos'])}")
        print(f"   - Advertencia: {result_fase3['advertencias_citas_datos'][0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logging_format():
    """Test 5: Verificar formateo para logging."""
    print("\n🧪 Test 5: Formateo para logging")
    print("-" * 40)
    
    try:
        exc = GroqAPIError(
            message="API no disponible",
            phase=ErrorPhase.FASE_2_EXTRACCION,
            retry_count=3,
            article_id="log_test_789"
        )
        
        log_data = format_error_for_logging(exc, context={"extra_info": "test"})
        
        print(f"✅ Formato de log generado")
        print(f"   - Módulo: {log_data['module']}")
        print(f"   - Nivel: {log_data['level']}")
        print(f"   - Fase: {log_data.get('fase', 'N/A')}")
        print(f"   - Tipo error: {log_data.get('error_type', 'N/A')}")
        print(f"   - Artículo ID: {log_data.get('articulo_id', 'N/A')}")
        print(f"   - Context extra: {log_data.get('context', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecutar todos los tests."""
    print("=" * 60)
    print("VERIFICACIÓN RÁPIDA DEL SISTEMA DE MANEJO DE ERRORES - V2")
    print("=" * 60)
    
    tests = [
        test_custom_exceptions,
        test_error_responses,
        test_retry_decorator,
        test_fallback_handlers,
        test_logging_format
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ Test {test.__name__} falló con excepción: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESUMEN: {passed} tests pasaron, {failed} tests fallaron")
    
    if failed == 0:
        print("✅ ¡TODOS LOS TESTS PASARON! El sistema está funcionando correctamente")
    else:
        print("❌ Algunos tests fallaron. Revisa los errores arriba.")
    
    print("=" * 60)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
