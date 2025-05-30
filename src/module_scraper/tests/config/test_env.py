"""
Test básico para verificar carga de variables de entorno
"""
import os
import sys
from pathlib import Path

print("=== VERIFICACIÓN DE CARGA DE .env.test ===\n")

# Verificar si python-dotenv está instalado
try:
    from dotenv import load_dotenv
    print("✓ python-dotenv está instalado")
except ImportError:
    print("✗ ERROR: python-dotenv NO está instalado")
    print("  Ejecuta: pip install python-dotenv")
    sys.exit(1)

# Buscar .env.test
current_dir = Path.cwd()
print(f"\nDirectorio actual: {current_dir}")

# Intentar diferentes ubicaciones (nuevas ubicaciones primero)
locations = [
    Path('config/.env.test'),  # Nueva ubicación principal
    current_dir / 'config' / '.env.test',
    Path(__file__).parent.parent.parent / 'config' / '.env.test',  # Desde tests/config/
    Path('.env.test'),  # Legacy
    Path(__file__).parent / '.env.test',  # Legacy
    current_dir / '.env.test'  # Legacy
]

env_file = None
for loc in locations:
    print(f"\nBuscando en: {loc}")
    if loc.exists():
        print(f"  ✓ ENCONTRADO!")
        env_file = loc
        break
    else:
        print(f"  ✗ No existe")

if env_file:
    # Cargar el archivo
    load_dotenv(env_file, override=True)
    print(f"\n✓ Archivo cargado desde: {env_file}")
    
    # Verificar variables
    print("\nVariables cargadas:")
    vars_to_check = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_KEY']
    
    for var in vars_to_check:
        value = os.getenv(var)
        if value:
            display = value[:30] + "..." if len(value) > 30 else value
            print(f"  ✓ {var} = {display}")
        else:
            print(f"  ✗ {var} = NO CONFIGURADA")
else:
    print("\n✗ ERROR: No se encontró .env.test en ninguna ubicación")
    print("\nAsegúrate de que el archivo existe en el directorio module_scraper")
