"""
Test de conexión sin dotenv - Variables hardcodeadas temporalmente
"""
import os
import sys
from pathlib import Path

# Configurar el path
module_dir = Path(__file__).parent
sys.path.insert(0, str(module_dir))

print("=== TEST RÁPIDO DE CONEXIÓN SUPABASE (sin dotenv) ===\n")

# Configurar variables directamente (temporal para pruebas)
os.environ['SUPABASE_URL'] = 'https://aukbzqbcvbsnjdhflyvr.supabase.co'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1a2J6cWJjdmJzbmpkaGZseXZyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NTkxMjY2NiwiZXhwIjoyMDYxNDg4NjY2fQ.83yZqoMnj15_qkEbvqwCQsDgObQpmBoQsd-spxywAsw'
os.environ['SUPABASE_STORAGE_BUCKET'] = 'test-articulos-html-integration'

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
            # Intentar crear el bucket
            try:
                client.storage.create_bucket(bucket_name, options={"public": False})
                print(f"  - ✓ Bucket '{bucket_name}' creado exitosamente")
            except Exception as e:
                print(f"  - No se pudo crear el bucket: {e}")
    except Exception as e:
        print(f"  - Error verificando buckets: {e}")
    
except ImportError:
    print("\n✗ ERROR: La librería 'supabase' no está instalada")
    print("  Ejecuta: pip install supabase")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ ERROR DE CONEXIÓN: {e}")
    sys.exit(1)

print("\n¡Todo listo para ejecutar los tests!")
print("\nNOTA: Este script usa credenciales hardcodeadas temporalmente.")
print("Para los tests reales, asegúrate de que python-dotenv esté instalado")
print("y que .env.test esté configurado correctamente.")
