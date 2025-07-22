#!/usr/bin/env python3
import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=== DESCUBRIENDO COLUMNAS DE TABLAS VACÍAS ===\n")

# Intentar insertar datos dummy para ver qué columnas espera cada tabla
test_inserts = {
    'entidades': {
        'nombre': 'Test',
        'tipo': 'PERSONA'
    },
    'hechos': {
        'contenido': 'Test',
        'fecha_ocurrencia': '[2024-01-01,2024-01-02)',
        'tipo_hecho': 'SUCESO'
    },
    'citas_textuales': {
        'cita': 'Test quote',
        'articulo_id': 1
    },
    'datos_cuantitativos': {
        'hecho_id': 1,
        'articulo_id': 1,
        'indicador': 'Test'
    }
}

for table, dummy_data in test_inserts.items():
    print(f"\n📋 TABLA: {table}")
    print("-" * 60)
    
    try:
        # Intentar insertar y capturar el error
        result = supabase.table(table).insert(dummy_data).execute()
        print(f"✅ Insert exitoso (inesperado) - ID: {result.data}")
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error (esperado): {error_msg[:200]}...")
        
        # El error puede contener información sobre columnas faltantes
        if "column" in error_msg.lower():
            print("\n📌 Información de columnas en el error:")
            # Extraer información relevante del error
            if "required" in error_msg.lower() or "null" in error_msg.lower():
                print("   -> El error sugiere columnas requeridas")

# Ahora intentar con consultas más específicas
print("\n\n=== USANDO POSTGREST PARA OBTENER ESQUEMA ===\n")

# Las tablas de relación suelen tener estructura diferente
relation_tables = ['hecho_entidad', 'hecho_articulo']

for table in relation_tables:
    print(f"\n📋 TABLA: {table}")
    print("-" * 60)
    
    try:
        # Para tablas de relación, intentar un insert diferente
        if table == 'hecho_entidad':
            test_data = {
                'hecho_id': 1,
                'entidad_id': 1,
                'fecha_ocurrencia_hecho': '[2024-01-01,2024-01-02)'
            }
        else:  # hecho_articulo
            test_data = {
                'hecho_id': 1,
                'articulo_id': 1,
                'fecha_ocurrencia_hecho': '[2024-01-01,2024-01-02)'
            }
            
        result = supabase.table(table).insert(test_data).execute()
        print(f"✅ Insert exitoso (inesperado)")
    except Exception as e:
        print(f"❌ Error: {str(e)[:300]}...")