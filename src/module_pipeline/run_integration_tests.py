"""
Script para ejecutar tests de integración del controller
"""
import subprocess
import sys
import os

# Cambiar al directorio del proyecto
os.chdir(r'C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline')

# Ejecutar pytest con los tests de integración
print("Ejecutando tests de integración del PipelineController...")
print("=" * 60)

result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/test_controller_integration.py', '-v', '--tb=short'],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("\nERRORES:")
    print(result.stderr)

print(f"\nCódigo de salida: {result.returncode}")
print("=" * 60)

# Resumen
if result.returncode == 0:
    print("✅ TODOS LOS TESTS PASARON")
else:
    print("❌ ALGUNOS TESTS FALLARON")
    print("\nRecomendaciones:")
    print("1. Verificar que los modelos Pydantic estén correctamente definidos")
    print("2. Asegurarse de que los mocks coincidan con las firmas de las funciones")
    print("3. Revisar los imports y rutas de los módulos")
