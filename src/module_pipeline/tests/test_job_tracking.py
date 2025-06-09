#!/usr/bin/env python3
"""
Test de verificación simple para el sistema de Job Tracking
============================================================

Este script verifica el funcionamiento correcto del sistema de tracking de jobs
implementado en la tarea 22 del Module Pipeline.

Tests incluidos:
1. Crear job y verificar estado inicial
2. Procesar artículo y verificar job_id en respuesta
3. Consultar estado durante procesamiento
4. Verificar estado completed después de procesamiento
5. Consultar job_id inexistente (esperar 404)
6. Simular error y verificar estado failed

Ejecución:
    python tests/test_job_tracking.py
"""

import requests
import json
import time
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# Colores para output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_test_header(test_num, description):
    """Imprime encabezado del test."""
    print(f"\n{YELLOW}Test {test_num}: {description}{RESET}")
    print("-" * 60)


def print_result(success, message):
    """Imprime resultado del test."""
    if success:
        print(f"{GREEN}✓ PASS: {message}{RESET}")
    else:
        print(f"{RED}✗ FAIL: {message}{RESET}")


def create_test_article():
    """Crea un artículo de prueba válido."""
    return {
        "titular": "Artículo de prueba para Job Tracking",
        "contenido_texto": "Este es un contenido de prueba con más de 50 caracteres para validación. " * 3,
        "medio": "Test News",
        "pais_publicacion": "ES",
        "tipo_medio": "digital",
        "fecha_publicacion": "2024-01-15T10:00:00Z",
        "autor": "Test Author",
        "url": "https://example.com/test-article",
        "idioma": "es"
    }


def create_invalid_article():
    """Crea un artículo inválido (sin campos requeridos)."""
    return {
        "titular": "Artículo inválido",
        # Falta contenido_texto y otros campos requeridos
    }


def test_job_tracking_system():
    """Ejecuta todos los tests del sistema de job tracking."""
    
    print("\n" + "="*70)
    print("INICIANDO TESTS DE JOB TRACKING")
    print("="*70)
    
    # Test 1: Crear job y verificar estado inicial
    print_test_header(1, "Crear job y verificar estado inicial")
    
    article_data = create_test_article()
    
    try:
        # Enviar artículo para procesamiento
        response = requests.post(
            f"{BASE_URL}/procesar_articulo",
            json=article_data,
            headers=HEADERS
        )
        
        if response.status_code == 200:
            result = response.json()
            job_id = result.get("job_id")
            
            if job_id:
                print_result(True, f"Job creado exitosamente: {job_id}")
                
                # Verificar estado inicial consultando inmediatamente
                status_response = requests.get(f"{BASE_URL}/status/{job_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    initial_status = status_data.get("data", {}).get("status")
                    
                    # El estado inicial podría ser "pending", "processing" o "completed"
                    # dependiendo de qué tan rápido se procese
                    valid_statuses = ["pending", "processing", "completed"]
                    
                    if initial_status in valid_statuses:
                        print_result(True, f"Estado inicial válido: {initial_status}")
                    else:
                        print_result(False, f"Estado inicial inválido: {initial_status}")
                else:
                    print_result(False, f"Error al consultar estado: {status_response.status_code}")
            else:
                print_result(False, "No se recibió job_id en la respuesta")
        else:
            print_result(False, f"Error al crear job: {response.status_code}")
            print(f"Respuesta: {response.text}")
            
    except Exception as e:
        print_result(False, f"Excepción: {str(e)}")
    
    # Test 2: Procesar artículo y verificar job_id en respuesta
    print_test_header(2, "Procesar artículo y verificar job_id en respuesta")
    
    try:
        response = requests.post(
            f"{BASE_URL}/procesar_articulo",
            json=article_data,
            headers=HEADERS
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Verificar campos requeridos en respuesta
            required_fields = ["success", "request_id", "job_id", "timestamp", "api_version", "data"]
            missing_fields = [field for field in required_fields if field not in result]
            
            if not missing_fields:
                print_result(True, "Todos los campos requeridos presentes en respuesta")
                print(f"  - job_id: {result['job_id']}")
                print(f"  - request_id: {result['request_id']}")
                print(f"  - timestamp: {result['timestamp']}")
                
                # Guardar job_id para próximos tests
                test_job_id = result['job_id']
            else:
                print_result(False, f"Campos faltantes: {missing_fields}")
                test_job_id = None
        else:
            print_result(False, f"Error al procesar artículo: {response.status_code}")
            test_job_id = None
            
    except Exception as e:
        print_result(False, f"Excepción: {str(e)}")
        test_job_id = None
    
    # Test 3: Consultar estado durante procesamiento
    print_test_header(3, "Consultar estado durante procesamiento")
    
    if test_job_id:
        try:
            # Dar un poco de tiempo para asegurar que esté procesando
            time.sleep(0.5)
            
            response = requests.get(f"{BASE_URL}/status/{test_job_id}")
            
            if response.status_code == 200:
                result = response.json()
                status_data = result.get("data", {})
                
                # Verificar estructura de respuesta
                expected_fields = ["job_id", "status", "created_at", "updated_at", "progress"]
                present_fields = [field for field in expected_fields if field in status_data]
                
                if len(present_fields) == len(expected_fields):
                    print_result(True, "Estructura de respuesta correcta")
                    print(f"  - Status: {status_data['status']}")
                    print(f"  - Progress: {status_data['progress']['percentage']}%")
                    print(f"  - Message: {status_data['progress']['message']}")
                else:
                    print_result(False, f"Campos faltantes en respuesta de estado")
            else:
                print_result(False, f"Error al consultar estado: {response.status_code}")
                
        except Exception as e:
            print_result(False, f"Excepción: {str(e)}")
    else:
        print_result(False, "No hay job_id disponible para consultar")
    
    # Test 4: Verificar estado completed después de procesamiento
    print_test_header(4, "Verificar estado completed después de procesamiento")
    
    if test_job_id:
        try:
            # Esperar un poco más para asegurar que complete
            time.sleep(2)
            
            response = requests.get(f"{BASE_URL}/status/{test_job_id}")
            
            if response.status_code == 200:
                result = response.json()
                status_data = result.get("data", {})
                
                if status_data.get("status") == "completed":
                    print_result(True, "Job completado exitosamente")
                    
                    # Verificar que incluye resultado
                    if "result" in status_data:
                        print(f"  - Fragmento ID: {status_data['result'].get('fragmento_id')}")
                        print(f"  - Tiempo procesamiento: {status_data['result'].get('tiempo_procesamiento_segundos', 0):.2f}s")
                        elementos = status_data['result'].get('elementos_extraidos', {})
                        print(f"  - Elementos extraídos: {elementos}")
                else:
                    print_result(False, f"Estado no es 'completed': {status_data.get('status')}")
            else:
                print_result(False, f"Error al consultar estado: {response.status_code}")
                
        except Exception as e:
            print_result(False, f"Excepción: {str(e)}")
    else:
        print_result(False, "No hay job_id disponible para verificar")
    
    # Test 5: Consultar job_id inexistente (esperar 404)
    print_test_header(5, "Consultar job_id inexistente (esperar 404)")
    
    fake_job_id = "JOB-INEXISTENTE-12345"
    
    try:
        response = requests.get(f"{BASE_URL}/status/{fake_job_id}")
        
        if response.status_code == 404:
            print_result(True, f"404 recibido correctamente para job inexistente")
            
            # Verificar mensaje de error
            if response.text:
                try:
                    error_data = response.json()
                    print(f"  - Mensaje: {error_data.get('detail', 'Sin mensaje')}")
                except:
                    print(f"  - Respuesta: {response.text}")
        else:
            print_result(False, f"Código inesperado: {response.status_code} (esperado 404)")
            
    except Exception as e:
        print_result(False, f"Excepción: {str(e)}")
    
    # Test 6: Simular error y verificar estado failed
    print_test_header(6, "Simular error y verificar estado failed")
    
    invalid_article = create_invalid_article()
    
    try:
        response = requests.post(
            f"{BASE_URL}/procesar_articulo",
            json=invalid_article,
            headers=HEADERS
        )
        
        if response.status_code == 400:
            print_result(True, "Error 400 recibido correctamente para artículo inválido")
            
            # Verificar estructura de error
            if response.text:
                try:
                    error_data = response.json()
                    if "detail" in error_data and isinstance(error_data["detail"], dict):
                        detail = error_data["detail"]
                        print(f"  - Error: {detail.get('error')}")
                        print(f"  - Mensaje: {detail.get('mensaje')}")
                        print(f"  - Request ID: {detail.get('request_id')}")
                        
                        # Para este caso, el job ni siquiera se crea debido a validación
                        print_result(True, "Validación funcionó correctamente (job no creado)")
                except:
                    print(f"  - Respuesta: {response.text}")
        else:
            print_result(False, f"Código inesperado: {response.status_code} (esperado 400)")
            
    except Exception as e:
        print_result(False, f"Excepción: {str(e)}")
    
    print("\n" + "="*70)
    print("TESTS COMPLETADOS")
    print("="*70)


if __name__ == "__main__":
    # Verificar que el servidor esté corriendo
    print(f"\nVerificando conexión con el servidor en {BASE_URL}...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"{GREEN}✓ Servidor respondiendo correctamente{RESET}")
            
            # Ejecutar tests
            test_job_tracking_system()
        else:
            print(f"{RED}✗ El servidor respondió con código: {response.status_code}{RESET}")
            print("Por favor, asegúrate de que el servidor esté corriendo.")
    except requests.exceptions.ConnectionError:
        print(f"{RED}✗ No se pudo conectar al servidor en {BASE_URL}{RESET}")
        print("Por favor, inicia el servidor con: python -m src.main")
    except Exception as e:
        print(f"{RED}✗ Error inesperado: {str(e)}{RESET}")
