"""
Test rápido de conexión con Supabase
"""
import os
import sys
from pathlib import Path

# Configurar el path
module_dir = Path(__file__).parent
sys.path.insert(0, str(module_dir))

# Cargar .env.test
from dotenv import load_dotenv
env_path = module_dir / '.env.test'
print(f"Buscando .env.test en: {env_path}")
if env_path.exists():
    print(f"✓ Archivo .env.test encontrado")
    load_dotenv(env_path, override=True)
else:
    print(f"✗ Archivo .env.test NO encontrado en {env_path}")
    # Intentar en el directorio actual
    env_path = Path('.env.test')
    if env_path.exists():
        print(f"✓ Archivo .env.test encontrado en directorio actual")
        load_dotenv(env_path, override=True)
    else:
        print(f"✗ No se pudo encontrar .env.test")

print("=== TEST RÁPIDO DE CONEXIÓN SUPABASE ===\n")

# Verificar variables de entorno
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print(f"URL: {url[:30]}..." if url else "URL: NO CONFIGURADA")
print(f"KEY: {key[:20]}..." if key else "KEY: NO CONFIGURADA")

if not url or not key:
    print("\n✗ ERROR: Credenciales no configuradas")
    sys.exit(1)

# Intentar conexión
try:
    from supabase import create_client
    client = create_client(url, key)
    
    # Intentar una consulta simple
    response = client.table('articulos').select('id').limit(1).execute()
    print("\n✓ CONEXIÓN EXITOSA!")
    print(f"  - Cliente Supabase creado")
    print(f"  - Tabla 'articulos' accesible")
    
    # Verificar bucket
    bucket_name = os.getenv('SUPABASE_STORAGE_BUCKET', 'test-articulos-html-integration')
    try:
        buckets = client.storage.list_buckets()
        bucket_names = [b.get('name', '') for b in buckets]
        if bucket_name in bucket_names:
            print(f"  - Bucket '{bucket_name}' existe")
        else:
            print(f"  - Bucket '{bucket_name}' NO existe (se creará en los tests)")
    except Exception as e:
        print(f"  - Error verificando buckets: {e}")
    
except Exception as e:
    print(f"\n✗ ERROR DE CONEXIÓN: {e}")
    sys.exit(1)

print("\n¡Todo listo para ejecutar los tests!")
print("Ejecuta: python tests/run_unittest.py")
