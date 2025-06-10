"""
Script de demostración completa del Sistema de Manejo de Errores
================================================================

Este script muestra todas las capacidades del sistema funcionando.
"""

import sys
from pathlib import Path

# Añadir el directorio src al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.utils.error_handling import (
    PipelineException, ValidationError, GroqAPIError,
    ErrorPhase, ErrorType, create_error_response,
    handle_groq_extraction_error_fase2
)
import json

print("=" * 70)
print("DEMOSTRACIÓN COMPLETA - SISTEMA DE MANEJO DE ERRORES")
print("=" * 70)

# 1. Crear y mostrar una excepción personalizada
print("\n1. Excepción personalizada con todos los detalles:")
print("-" * 50)
exc = GroqAPIError(
    message="Timeout al llamar a Groq API",
    phase=ErrorPhase.FASE_2_EXTRACCION,
    retry_count=2,
    timeout_seconds=30,
    article_id="demo_123"
)
print(f"✅ Excepción creada: {exc.message}")
print(f"   - Support code: {exc.support_code}")
print(f"   - Timestamp: {exc.timestamp}")
print(f"   - Reintentos: {exc.details['retry_count']}/{exc.details['max_retries']}")

# 2. Crear respuesta HTTP de error
print("\n2. Respuesta HTTP estandarizada:")
print("-" * 50)
response = create_error_response(exc, request_id="req_demo_456")
content = json.loads(response.body)
print(f"✅ Respuesta HTTP creada")
print(f"   - Status: {response.status_code}")
print(f"   - Body: {json.dumps(content, indent=2)}")

# 3. Demostrar fallback
print("\n3. Handler de fallback en acción:")
print("-" * 50)
result = handle_groq_extraction_error_fase2(
    article_id="demo_789",
    titulo="El gobierno anuncia nuevas medidas económicas",
    medio="El País",
    exception=TimeoutError("API no disponible")
)
print(f"✅ Fallback ejecutado exitosamente")
print(f"   - Hecho creado: {result['hechos_extraidos'][0]['texto_original_del_hecho']}")
print(f"   - Entidad creada: {result['entidades_extraidas'][0]['texto_entidad']}")
print(f"   - Es fallback: {result['hechos_extraidos'][0]['metadata_hecho']['es_fallback']}")

# 4. Mostrar serialización completa
print("\n4. Serialización completa de excepción:")
print("-" * 50)
exc_dict = exc.to_dict()
print(f"✅ Excepción serializada a diccionario:")
print(json.dumps(exc_dict, indent=2, default=str))

print("\n" + "=" * 70)
print("✅ SISTEMA DE MANEJO DE ERRORES - TOTALMENTE FUNCIONAL")
print("=" * 70)
print("\nCaracterísticas demostradas:")
print("- Excepciones personalizadas con metadata completa")
print("- Support codes únicos para debugging")
print("- Respuestas HTTP según estándar de la documentación")
print("- Handlers de fallback que garantizan continuidad")
print("- Serialización completa para logging")
print("\n🎉 El sistema cumple con el principio: 'Nunca fallar completamente'")
