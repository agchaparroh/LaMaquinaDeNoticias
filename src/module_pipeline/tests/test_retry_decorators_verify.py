"""
Script de verificación para los decoradores de retry
=====================================================

Este script verifica que los decoradores @retry_groq_api y @retry_supabase_rpc
funcionen correctamente con las excepciones personalizadas.
"""

import time
import sys
from pathlib import Path

# Añadir el directorio src al path para importar los módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.error_handling import (
    retry_groq_api, retry_supabase_rpc,
    GroqAPIError, SupabaseRPCError, ErrorPhase
)
from groq import APIConnectionError, RateLimitError
from loguru import logger

# Configurar logger para ver los mensajes
logger.add(sys.stdout, level="DEBUG")


class TestRetryDecorators:
    """Clase para probar los decoradores de retry."""
    
    def __init__(self):
        self.groq_attempts = 0
        self.supabase_connection_attempts = 0
        self.supabase_validation_attempts = 0
    
    @retry_groq_api(max_attempts=2, wait_seconds=1)  # Reducido para pruebas rápidas
    def test_groq_retry_success(self):
        """Simula una llamada a Groq que falla 1 vez y luego tiene éxito."""
        self.groq_attempts += 1
        logger.info(f"Intento Groq #{self.groq_attempts}")
        
        if self.groq_attempts < 2:
            raise APIConnectionError("Simulated connection error")
        
        return "Success after retry!"
    
    @retry_groq_api(max_attempts=2, wait_seconds=1)
    def test_groq_retry_failure(self):
        """Simula una llamada a Groq que siempre falla."""
        logger.info("Intento Groq que siempre falla")
        raise RateLimitError("Rate limit exceeded")
    
    @retry_supabase_rpc(connection_retries=1)
    def test_supabase_connection_retry(self):
        """Simula un error de conexión con Supabase."""
        self.supabase_connection_attempts += 1
        logger.info(f"Intento Supabase conexión #{self.supabase_connection_attempts}")
        
        if self.supabase_connection_attempts < 2:
            raise ConnectionError("Simulated connection error")
        
        return {"status": "connected"}
    
    @retry_supabase_rpc(connection_retries=1)
    def test_supabase_validation_no_retry(self):
        """Simula un error de validación con Supabase (no debe reintentar)."""
        self.supabase_validation_attempts += 1
        logger.info(f"Intento Supabase validación #{self.supabase_validation_attempts}")
        
        raise ValueError("Invalid data - should not retry")


def run_tests():
    """Ejecuta las pruebas de los decoradores."""
    tester = TestRetryDecorators()
    
    print("\n" + "="*60)
    print("PRUEBA DE DECORADORES DE RETRY")
    print("="*60)
    
    # Test 1: Groq retry con éxito
    print("\n1. Test Groq Retry con Éxito")
    print("-" * 30)
    try:
        result = tester.test_groq_retry_success()
        print(f"✅ Resultado: {result}")
        print(f"   Intentos totales: {tester.groq_attempts}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
    
    # Test 2: Groq retry con fallo
    print("\n2. Test Groq Retry con Fallo Permanente")
    print("-" * 30)
    try:
        result = tester.test_groq_retry_failure()
        print(f"✅ Resultado: {result}")
    except GroqAPIError as e:
        print(f"✅ GroqAPIError capturado correctamente:")
        print(f"   - Mensaje: {e.message}")
        print(f"   - Reintentos: {e.details.get('retry_count', 0)}")
        print(f"   - Fase: {e.phase}")
    except Exception as e:
        print(f"❌ Error inesperado: {type(e).__name__}: {e}")
    
    # Test 3: Supabase retry conexión
    print("\n3. Test Supabase Retry Conexión")
    print("-" * 30)
    try:
        result = tester.test_supabase_connection_retry()
        print(f"✅ Resultado: {result}")
        print(f"   Intentos totales: {tester.supabase_connection_attempts}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
    
    # Test 4: Supabase sin retry (validación)
    print("\n4. Test Supabase Sin Retry (Validación)")
    print("-" * 30)
    try:
        result = tester.test_supabase_validation_no_retry()
        print(f"✅ Resultado: {result}")
    except SupabaseRPCError as e:
        print(f"✅ SupabaseRPCError capturado correctamente:")
        print(f"   - Mensaje: {e.message}")
        print(f"   - Es error de conexión: {e.details.get('is_connection_error', False)}")
        print(f"   - Reintentos: {e.details.get('retry_count', 0)}")
        print(f"   - Intentos totales: {tester.supabase_validation_attempts} (debe ser 1)")
    except Exception as e:
        print(f"❌ Error inesperado: {type(e).__name__}: {e}")
    
    print("\n" + "="*60)
    print("RESUMEN DE VERIFICACIÓN")
    print("="*60)
    
    # Verificar comportamiento esperado
    checks = [
        ("Groq reintenta en caso de error", tester.groq_attempts == 2),
        ("Supabase reintenta errores de conexión", tester.supabase_connection_attempts == 2),
        ("Supabase NO reintenta errores de validación", tester.supabase_validation_attempts == 1),
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ TODOS LOS DECORADORES FUNCIONAN CORRECTAMENTE")
    else:
        print("❌ ALGUNOS DECORADORES NO FUNCIONAN COMO SE ESPERABA")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
