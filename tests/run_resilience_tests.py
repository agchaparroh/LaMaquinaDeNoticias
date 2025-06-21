"""
Script para ejecutar los tests de Resiliencia
"""
import subprocess
import sys
import os

def run_resilience_tests():
    """Ejecuta todos los tests de resiliencia y muestra resultados"""
    
    print("=" * 60)
    print("🛡️ EJECUTANDO TESTS DE RESILIENCIA")
    print("=" * 60)
    
    # Cambiar al directorio de tests
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(tests_dir)
    
    # Comando para ejecutar pytest
    cmd = [sys.executable, "-m", "pytest", "resilience/", "-v", "-s", "--tb=short"]
    
    print(f"\nComando: {' '.join(cmd)}")
    print("-" * 60)
    
    # Ejecutar tests
    result = subprocess.run(cmd, capture_output=False)
    
    print("\n" + "=" * 60)
    if result.returncode == 0:
        print("✅ TODOS LOS TESTS DE RESILIENCIA PASARON EXITOSAMENTE")
    else:
        print("❌ ALGUNOS TESTS DE RESILIENCIA FALLARON")
    print("=" * 60)
    
    return result.returncode

if __name__ == "__main__":
    exit_code = run_resilience_tests()
    sys.exit(exit_code)
