#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Conectar a Supabase
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

# Consultar estructura real de las tablas
tables = ['articulos', 'entidades', 'hechos', 'citas_textuales', 'datos_cuantitativos', 'hecho_entidad', 'hecho_articulo']

for table in tables:
    print(f"\n=== TABLA: {table} ===")
    try:
        # Consultar information_schema para obtener columnas
        schema_query = f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = '{table}'
        ORDER BY ordinal_position
        """
        
        # Intentar ejecutar query directa
        result = supabase.rpc('get_table_schema', {'table_name': table}).execute()
        print(f"Columnas desde RPC: {result.data}")
    except:
        # Si no hay RPC, intentar con select limit 0
        try:
            result = supabase.table(table).select("*").limit(0).execute()
            # Esto debería devolver estructura sin datos
            print(f"Estructura obtenida con limit 0")
        except:
            # Último intento: hacer query que no devuelva filas
            try:
                result = supabase.table(table).select("*").eq('id', -999999).execute()
                # La respuesta debería incluir la estructura aunque no haya datos
                if hasattr(result, 'data'):
                    print(f"Query ejecutada, verificando estructura...")
                    # Para Postgrest, los campos vienen en la respuesta aunque esté vacía
            except Exception as e:
                print(f"Error: {e}")