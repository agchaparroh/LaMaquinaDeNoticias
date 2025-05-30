"""
Verificación manual de la configuración de tests
"""
import os
import sys
from pathlib import Path

# Configurar el path
module_dir = Path(__file__).parent.parent
sys.path.insert(0, str(module_dir))

print("Verificando configuración del módulo scraper...")
print(f"Directorio del módulo: {module_dir}")

# Verificar archivos clave
files_to_check = [
    '.env.test',
    'scraper_core/utils/supabase_client.py',
    'scraper_core/utils/compression.py',
    'scraper_core/pipelines/supabase_pipeline.py',
    'tests/test_supabase_integration.py'
]

all_exist = True
for file in files_to_check:
    file_path = module_dir / file
    exists = file_path.exists()
    status = "✓" if exists else "✗"
    print(f"{status} {file}: {'Existe' if exists else 'NO EXISTE'}")
    if not exists:
        all_exist = False

if all_exist:
    print("\n✓ Todos los archivos necesarios están presentes")
    print("\nPara ejecutar los tests:")
    print("1. Navega al directorio: cd 'C:\\Users\\DELL\\Desktop\\Prueba con Windsurf AI\\La Máquina de Noticias\\src\\module_scraper'")
    print("2. Ejecuta: python tests/diagnostico.py")
    print("3. Si todo está bien, ejecuta: python tests/run_unittest.py")
else:
    print("\n✗ Faltan archivos necesarios para los tests")
