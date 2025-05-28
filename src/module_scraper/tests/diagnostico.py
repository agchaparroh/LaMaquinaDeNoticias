#!/usr/bin/env python
"""
Script de diagnóstico para verificar la configuración antes de ejecutar tests
"""
import os
import sys
from pathlib import Path

# Configurar el path
module_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(module_dir))

print("=" * 60)
print("DIAGNÓSTICO DE CONFIGURACIÓN DE TESTS")
print("=" * 60)

# 1. Verificar .env.test
env_test_path = module_dir / '.env.test'
print(f"\n1. Verificando archivo .env.test:")
if env_test_path.exists():
    print(f"   ✓ Archivo encontrado en: {env_test_path}")
    
    # Cargar y verificar variables
    from dotenv import load_dotenv
    load_dotenv(env_test_path, override=True)
    
    required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_STORAGE_BUCKET']
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mostrar solo parte del valor por seguridad
            display_value = value[:20] + "..." if len(value) > 20 else value
            print(f"   ✓ {var}: {display_value}")
        else:
            print(f"   ✗ {var}: NO CONFIGURADA")
else:
    print(f"   ✗ Archivo NO encontrado")

# 2. Verificar importaciones
print(f"\n2. Verificando importaciones:")
try:
    from scraper_core.items import ArticuloInItem
    print("   ✓ ArticuloInItem importado correctamente")
except ImportError as e:
    print(f"   ✗ Error importando ArticuloInItem: {e}")

try:
    from scraper_core.pipelines import SupabaseStoragePipeline
    print("   ✓ SupabaseStoragePipeline importado correctamente")
except ImportError as e:
    print(f"   ✗ Error importando SupabaseStoragePipeline: {e}")

try:
    from scraper_core.utils.supabase_client import SupabaseClient
    print("   ✓ SupabaseClient importado correctamente")
except ImportError as e:
    print(f"   ✗ Error importando SupabaseClient: {e}")

try:
    from scraper_core.utils.compression import compress_html, decompress_html
    print("   ✓ Funciones de compresión importadas correctamente")
except ImportError as e:
    print(f"   ✗ Error importando funciones de compresión: {e}")

# 3. Verificar conexión con Supabase
print(f"\n3. Verificando conexión con Supabase:")
try:
    from scraper_core.utils.supabase_client import SupabaseClient
    client = SupabaseClient()
    
    # Verificar health check
    if client.health_check():
        print("   ✓ Conexión con Supabase exitosa")
    else:
        print("   ✗ No se pudo conectar con Supabase")
    
    # Verificar bucket de prueba
    test_bucket = os.getenv('SUPABASE_STORAGE_BUCKET', 'test-articulos-html-integration')
    try:
        buckets = client.list_buckets()
        bucket_names = [b.get('name') for b in buckets]
        if test_bucket in bucket_names:
            print(f"   ✓ Bucket de prueba '{test_bucket}' existe")
        else:
            print(f"   ℹ Bucket de prueba '{test_bucket}' no existe (se creará durante los tests)")
    except Exception as e:
        print(f"   ✗ Error verificando buckets: {e}")
        
except Exception as e:
    print(f"   ✗ Error creando cliente Supabase: {e}")

# 4. Verificar estructura de archivos de test
print(f"\n4. Verificando archivos de test:")
test_file = module_dir / 'tests' / 'test_supabase_integration.py'
if test_file.exists():
    print(f"   ✓ Archivo de test encontrado: {test_file}")
else:
    print(f"   ✗ Archivo de test NO encontrado")

print("\n" + "=" * 60)
print("FIN DEL DIAGNÓSTICO")
print("=" * 60)
