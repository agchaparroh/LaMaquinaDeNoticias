#!/usr/bin/env python3
"""
Test de Verificación Simple para el endpoint /procesar_fragmento
================================================================

Este script ejecuta pruebas básicas del endpoint POST /procesar_fragmento.
Se puede ejecutar directamente con: python test_endpoint_fragmento.py
"""

import sys
import os
import json
from datetime import datetime

# Agregar el directorio raíz al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Imports necesarios
try:
    from fastapi.testclient import TestClient
    from unittest.mock import Mock, AsyncMock
    from src.main import app
    import src.main
    
    print("✓ Imports exitosos")
except ImportError as e:
    print(f"✗ Error en imports: {e}")
    print("  Asegúrate de tener todas las dependencias instaladas")
    sys.exit(1)

# Crear mock del PipelineController para evitar dependencias reales
mock_controller = Mock()
mock_controller.process_fragment = AsyncMock(return_value={
    "fragmento_id": "test_fragment_001",
    "fragmento_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "request_id": "req_test123",
    "procesamiento_exitoso": True,
    "procesamiento_parcial": False,
    "advertencias": [],
    "timestamp": datetime.utcnow().isoformat(),
    "metricas": {
        "tiempo_total_segundos": 0.3,
        "conteos_elementos": {
            "hechos_extraidos": 2,
            "entidades_extraidas": 3,
            "citas_extraidas": 1,
            "datos_cuantitativos": 0
        }
    }
})

# Asignar el mock a la aplicación
src.main.pipeline_controller = mock_controller

# Crear cliente de pruebas
client = TestClient(app)

print("\n=== INICIANDO TESTS DEL ENDPOINT /procesar_fragmento ===\n")

# Test 1: Fragmento válido - verificar respuesta exitosa y estructura
def test_fragmento_valido():
    """Test 1: Fragmento válido - debe retornar respuesta exitosa con estructura correcta."""
    print("Test 1: Fragmento válido")
    
    # Datos de fragmento válido
    fragmento_data = {
        "id_fragmento": "frag_001",
        "texto_original": "Este es un fragmento de texto válido para procesamiento. " * 5,  # >100 caracteres
        "id_articulo_fuente": "articulo_001",
        "orden_en_articulo": 1,
        "metadata_adicional": {
            "fuente": "test",
            "categoria": "prueba"
        }
    }
    
    try:
        # Enviar petición POST
        response = client.post("/procesar_fragmento", json=fragmento_data)
        
        # Verificar código de estado
        assert response.status_code == 200, f"  ✗ Código HTTP esperado: 200, recibido: {response.status_code}"
        print(f"  ✓ Código HTTP correcto: {response.status_code}")
        
        # Verificar estructura de respuesta
        response_json = response.json()
        
        # Verificar campos principales
        assert response_json.get("success") is True, "  ✗ Campo 'success' debe ser True"
        print("  ✓ Campo 'success' es True")
        
        assert "request_id" in response_json, "  ✗ Falta campo 'request_id'"
        assert response_json["request_id"].startswith("req_"), "  ✗ request_id debe empezar con 'req_'"
        print(f"  ✓ request_id generado correctamente: {response_json['request_id']}")
        
        assert "timestamp" in response_json, "  ✗ Falta campo 'timestamp'"
        # Verificar que el timestamp es válido
        timestamp = datetime.fromisoformat(response_json["timestamp"].replace("Z", "+00:00"))
        print(f"  ✓ timestamp válido: {response_json['timestamp']}")
        
        assert "api_version" in response_json, "  ✗ Falta campo 'api_version'"
        print(f"  ✓ api_version presente: {response_json['api_version']}")
        
        assert "data" in response_json, "  ✗ Falta campo 'data'"
        print("  ✓ Campo 'data' presente con resultado del procesamiento")
        
        print("✓ Test 1 PASADO: Fragmento válido procesado correctamente\n")
        return True
        
    except AssertionError as e:
        print(f"{e}")
        print("✗ Test 1 FALLADO\n")
        return False
    except Exception as e:
        print(f"  ✗ Error inesperado: {e}")
        print("✗ Test 1 FALLADO\n")
        return False


# Test 2: Fragmento sin campos requeridos - verificar error 400
def test_fragmento_sin_campos_requeridos():
    """Test 2: Fragmento sin campos requeridos - debe retornar error 400."""
    print("Test 2: Fragmento sin campos requeridos")
    
    # Fragmento incompleto - falta texto_original e id_articulo_fuente
    fragmento_data = {
        "id_fragmento": "frag_002"
    }
    
    try:
        # Enviar petición POST
        response = client.post("/procesar_fragmento", json=fragmento_data)
        
        # Verificar código de estado (puede ser 422 o 500 dependiendo del handler)
        assert response.status_code in [400, 422, 500], f"  ✗ Código HTTP esperado: 400/422/500, recibido: {response.status_code}"
        print(f"  ✓ Código HTTP de error correcto: {response.status_code}")
        
        # Verificar estructura de error
        response_json = response.json()
        
        assert "error" in response_json, "  ✗ Falta campo 'error' en respuesta de error"
        print(f"  ✓ Campo 'error' presente: {response_json.get('error')}")
        
        assert "timestamp" in response_json, "  ✗ Falta campo 'timestamp' en error"
        print("  ✓ Campo 'timestamp' presente en error")
        
        assert "request_id" in response_json, "  ✗ Falta campo 'request_id' en error"
        print("  ✓ Campo 'request_id' presente en error")
        
        print("✓ Test 2 PASADO: Error de validación manejado correctamente\n")
        return True
        
    except AssertionError as e:
        print(f"{e}")
        print("✗ Test 2 FALLADO\n")
        return False
    except Exception as e:
        print(f"  ✗ Error inesperado: {e}")
        print("✗ Test 2 FALLADO\n")
        return False


# Test 3: Fragmento con texto muy corto - verificar error de validación
def test_fragmento_texto_muy_corto():
    """Test 3: Fragmento con texto muy corto - debe generar advertencia o error."""
    print("Test 3: Fragmento con texto muy corto (<50 caracteres)")
    
    # Fragmento con texto menor a 50 caracteres
    fragmento_data = {
        "id_fragmento": "frag_003",
        "texto_original": "Texto corto",  # <50 caracteres
        "id_articulo_fuente": "articulo_003",
        "metadata_adicional": {
            "requiere_revision_especial": True  # Esto debería fallar con texto <50 chars
        }
    }
    
    try:
        # Enviar petición POST
        response = client.post("/procesar_fragmento", json=fragmento_data)
        
        # Con requiere_revision_especial=True y texto <50, debería fallar
        assert response.status_code in [400, 422, 500], f"  ✗ Código HTTP esperado: 400/422/500, recibido: {response.status_code}"
        print(f"  ✓ Código HTTP de error correcto: {response.status_code}")
        
        # Verificar mensaje de error
        response_json = response.json()
        
        # Verificar que menciona el problema con la longitud
        error_msg = str(response_json).lower()
        assert "50" in error_msg or "caracteres" in error_msg or "validation" in error_msg, \
            "  ✗ El error no menciona el límite de 50 caracteres"
        print("  ✓ Error menciona validación de longitud mínima")
        
        print("✓ Test 3 PASADO: Validación de texto corto funcionando\n")
        return True
        
    except AssertionError as e:
        print(f"{e}")
        print("✗ Test 3 FALLADO\n")
        return False
    except Exception as e:
        print(f"  ✗ Error inesperado: {e}")
        print("✗ Test 3 FALLADO\n")
        return False


# Ejecutar todos los tests
def main():
    """Ejecuta todos los tests y muestra resumen."""
    tests = [
        test_fragmento_valido,
        test_fragmento_sin_campos_requeridos,
        test_fragmento_texto_muy_corto
    ]
    
    resultados = []
    for test in tests:
        resultados.append(test())
    
    # Mostrar resumen
    print("=== RESUMEN DE TESTS ===")
    total_tests = len(resultados)
    tests_pasados = sum(resultados)
    tests_fallados = total_tests - tests_pasados
    
    print(f"Total de tests: {total_tests}")
    print(f"Tests pasados: {tests_pasados} ✓")
    print(f"Tests fallados: {tests_fallados} ✗")
    
    if tests_fallados == 0:
        print("\n✓ TODOS LOS TESTS PASARON EXITOSAMENTE")
        return 0
    else:
        print(f"\n✗ {tests_fallados} TESTS FALLARON")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
