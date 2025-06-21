#!/usr/bin/env python3
"""
Script para ejecutar los tests de integración por pares
"""

import subprocess
import sys
import os

# Cambiar al directorio del proyecto
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_root)

print("=" * 60)
print("EJECUTANDO TESTS DE INTEGRACIÓN POR PARES")
print("=" * 60)
print()

# Lista de tests a ejecutar
tests = [
    "tests/integration/test_scraper_to_connector.py",
    "tests/integration/test_connector_to_pipeline.py", 
    "tests/integration/test_pipeline_to_database.py",
    "tests/integration/test_backend_to_database.py",
    "tests/integration/test_frontend_to_backend.py"
]

# Ejecutar cada test
for test in tests:
    print(f"\n🔄 Ejecutando: {test}")
    print("-" * 50)
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", test, "-v", "--tb=short"],
        capture_output=False
    )
    
    if result.returncode == 0:
        print(f"✅ {test} - PASSED")
    else:
        print(f"❌ {test} - FAILED")

print("\n" + "=" * 60)
print("RESUMEN DE TESTS DE INTEGRACIÓN")
print("=" * 60)

# Ejecutar todos los tests con resumen
subprocess.run([
    sys.executable, "-m", "pytest", 
    "tests/integration/", 
    "-v", 
    "--tb=short",
    "-q"
])
