"""
Script para ejecutar los tests del sistema de manejo de errores
===============================================================

Este script ejecuta los tests unitarios y genera un reporte de cobertura.
"""

import sys
import os
import subprocess
from pathlib import Path

# Añadir el directorio src al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def run_tests():
    """Ejecuta los tests con pytest."""
    print("=" * 70)
    print("EJECUTANDO TESTS DEL SISTEMA DE MANEJO DE ERRORES")
    print("=" * 70)
    
    # Cambiar al directorio del proyecto
    os.chdir(project_root)
    
    # Comando pytest con opciones útiles
    pytest_cmd = [
        "python", "-m", "pytest",
        "tests/unit/test_error_handling.py",
        "-v",  # Verbose
        "-s",  # No capture output
        "--tb=short",  # Traceback corto
        "--color=yes",  # Colores en output
        "-x",  # Stop on first failure
    ]
    
    try:
        # Ejecutar pytest
        result = subprocess.run(pytest_cmd, capture_output=False)
        
        if result.returncode == 0:
            print("\n" + "=" * 70)
            print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print("❌ ALGUNOS TESTS FALLARON")
            print("=" * 70)
            
        return result.returncode
        
    except FileNotFoundError:
        print("\n❌ Error: pytest no está instalado")
        print("Instala las dependencias con: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"\n❌ Error ejecutando tests: {e}")
        return 1

def run_specific_test(test_name):
    """Ejecuta un test específico."""
    print(f"\nEjecutando test específico: {test_name}")
    
    pytest_cmd = [
        "python", "-m", "pytest",
        f"tests/unit/test_error_handling.py::{test_name}",
        "-v", "-s"
    ]
    
    subprocess.run(pytest_cmd)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Ejecutar test específico
        run_specific_test(sys.argv[1])
    else:
        # Ejecutar todos los tests
        exit_code = run_tests()
        sys.exit(exit_code)
