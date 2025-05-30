#!/usr/bin/env python
"""
Script para ejecutar los tests de integración de Supabase
"""
import os
import sys
import subprocess
from pathlib import Path

# Añadir el directorio del módulo al path
module_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(module_dir))

def run_integration_tests():
    """Ejecuta los tests de integración de Supabase"""
    print("=" * 60)
    print("EJECUTANDO TESTS DE INTEGRACIÓN DE SUPABASE")
    print("=" * 60)
    
    # Cambiar al directorio del módulo
    os.chdir(module_dir)
    
    # Verificar que existe el archivo .env.test en la nueva ubicación
    env_test_path = module_dir / 'config' / '.env.test'
    if not env_test_path.exists():
        print("ERROR: No se encontró el archivo config/.env.test")
        print(f"Por favor, crea el archivo en: {env_test_path}")
        print("Copia config/.env.test.example y edita con tus credenciales")
        return False
    
    print(f"✓ Archivo .env.test encontrado en: {env_test_path}")
    
    # Ejecutar los tests
    test_command = [
        sys.executable,
        "-m", "pytest",
        "tests/test_supabase_integration.py",
        "-v",  # Verbose
        "-s",  # No capturar output
        "--tb=short"  # Traceback corto
    ]
    
    print(f"\nEjecutando comando: {' '.join(test_command)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(test_command, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error al ejecutar tests: {e}")
        return False

if __name__ == "__main__":
    success = run_integration_tests()
    
    if success:
        print("\n✓ Todos los tests pasaron exitosamente!")
    else:
        print("\n✗ Algunos tests fallaron. Revisa los errores arriba.")
    
    sys.exit(0 if success else 1)
