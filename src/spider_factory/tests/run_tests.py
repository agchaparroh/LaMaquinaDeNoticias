#!/usr/bin/env python3
"""
Script para ejecutar los tests de Spider Factory 2.0
"""
import subprocess
import sys
from pathlib import Path

def run_tests():
    """Ejecuta todos los tests con pytest"""
    print("=== Ejecutando Tests de Spider Factory 2.0 ===\n")
    
    # Directorio base
    base_dir = Path(__file__).parent
    
    # Comandos de pytest
    commands = [
        # Tests unitarios por módulo
        ["pytest", "tests/test_models.py", "-v", "--tb=short"],
        ["pytest", "tests/test_analyzer.py", "-v", "--tb=short"],
        ["pytest", "tests/test_generator.py", "-v", "--tb=short"],
        ["pytest", "tests/test_patterns.py", "-v", "--tb=short"],
        ["pytest", "tests/test_api.py", "-v", "--tb=short"],
        ["pytest", "tests/test_metrics.py", "-v", "--tb=short"],
        ["pytest", "tests/test_integration.py", "-v", "--tb=short"],
        
        # Todos los tests con coverage
        ["pytest", "tests/", "-v", "--cov=src", "--cov-report=term-missing", "--cov-report=html"]
    ]
    
    # Ejecutar cada comando
    for i, cmd in enumerate(commands):
        if i < len(commands) - 1:
            print(f"\n{'='*60}")
            print(f"Ejecutando: {' '.join(cmd[1:3])}")
            print(f"{'='*60}\n")
        else:
            print(f"\n{'='*60}")
            print("Ejecutando TODOS los tests con coverage")
            print(f"{'='*60}\n")
        
        try:
            result = subprocess.run(cmd, cwd=base_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Tests pasaron exitosamente")
                if "--cov" in cmd:
                    # Mostrar resumen de coverage
                    output_lines = result.stdout.split('\n')
                    coverage_started = False
                    for line in output_lines:
                        if "TOTAL" in line or coverage_started:
                            print(line)
                            coverage_started = True
            else:
                print(f"❌ Tests fallaron")
                print("\nSTDOUT:")
                print(result.stdout)
                print("\nSTDERR:")
                print(result.stderr)
                
        except Exception as e:
            print(f"❌ Error ejecutando tests: {e}")
    
    print("\n=== Resumen de Tests ===")
    print("- Los tests unitarios cubren todos los módulos principales")
    print("- Los tests de integración verifican el flujo completo")
    print("- El reporte de coverage está en htmlcov/index.html")
    
    # Verificar si se cumple el mínimo de coverage (80%)
    try:
        result = subprocess.run(
            ["pytest", "tests/", "--cov=src", "--cov-fail-under=80", "-q"],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ Coverage cumple con el mínimo requerido (80%)")
        else:
            print("\n⚠️  Coverage por debajo del mínimo requerido (80%)")
            
    except Exception as e:
        print(f"\n⚠️  No se pudo verificar coverage: {e}")

if __name__ == "__main__":
    run_tests()