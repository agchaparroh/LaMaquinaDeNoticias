#!/usr/bin/env python
"""
Script para ejecutar y verificar las correcciones de los tests
"""

import subprocess
import sys
import os

# Cambiar al directorio del módulo
os.chdir(r"C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline")

# Ejecutar los tests
print("Ejecutando tests de integración con las correcciones aplicadas...")
print("=" * 80)

cmd = [sys.executable, "-m", "pytest", "tests/test_controller_integration.py", "-v", "--tb=short"]

try:
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Mostrar la salida
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    # Analizar resultados
    if result.returncode == 0:
        print("\n✅ TODOS LOS TESTS PASARON!")
    else:
        print(f"\n❌ Tests fallaron con código: {result.returncode}")
        
        # Buscar patrones de error específicos
        output = result.stdout + result.stderr
        
        if "datetime" in output and "referenced before assignment" in output:
            print("\n⚠️  Todavía hay problemas con 'datetime' no definida")
        
        if "Field required" in output and "id_fragmento_origen" in output:
            print("\n⚠️  Todavía falta el campo 'id_fragmento_origen' en algún lugar")
            
        if "KeyError" in output and "'id_hecho'" in output:
            print("\n⚠️  Todavía hay problemas con el formato de logging")
            
        if "confianza_extraccion" in output and "Extra inputs" in output:
            print("\n⚠️  Todavía se está usando 'confianza_extraccion' incorrectamente")
            
        if "KeyError" in output and "hechos_generados" in output:
            print("\n⚠️  Los nombres de campos en stats no coinciden")

except Exception as e:
    print(f"Error ejecutando tests: {e}")
    sys.exit(1)
