"""
Script para ejecutar los tests End-to-End
"""
import subprocess
import sys
import os

def run_e2e_tests():
    """Ejecuta todos los tests e2e y muestra resultados"""
    
    print("=" * 60)
    print("🚀 EJECUTANDO TESTS END-TO-END")
    print("=" * 60)
    
    # Cambiar al directorio de tests
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(tests_dir)
    
    # Comando para ejecutar pytest
    cmd = [sys.executable, "-m", "pytest", "e2e/", "-v", "-s", "--tb=short"]
    
    print(f"\nComando: {' '.join(cmd)}")
    print("-" * 60)
    
    # Ejecutar tests
    result = subprocess.run(cmd, capture_output=False)
    
    print("\n" + "=" * 60)
    if result.returncode == 0:
        print("✅ TODOS LOS TESTS E2E PASARON EXITOSAMENTE")
    else:
        print("❌ ALGUNOS TESTS E2E FALLARON")
    print("=" * 60)
    
    return result.returncode

if __name__ == "__main__":
    exit_code = run_e2e_tests()
    sys.exit(exit_code)
