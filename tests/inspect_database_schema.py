#!/usr/bin/env python3
"""
Script para inspeccionar el esquema real de la base de datos
"""
import os
from supabase import create_client, Client

# Configuración
SUPABASE_URL = "https://aukbzqbcvbsnjdhflyvr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1a2J6cWJjdmJzbmpkaGZseXZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5MTI2NjYsImV4cCI6MjA2MTQ4ODY2Nn0.KfRQ1Jv7HIGwMHUS8e8IgN92iv1go7VvyK-6wqgog3s"

def inspect_database_schema():
    """Inspecciona el esquema real de la base de datos"""
    
    print("=" * 60)
    print("INSPECCIÓN DE ESQUEMA DE BASE DE DATOS")
    print("=" * 60)
    
    try:
        # Crear cliente
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Conexión establecida con Supabase")
        
        # Obtener lista de tablas
        print("\n📋 LISTADO DE TABLAS EXISTENTES:")
        print("-" * 40)
        
        try:
            # Consultar información del esquema
            tables_query = """
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
            """
            
            response = supabase.rpc('execute_sql', {'query': tables_query}).execute()
            
            if response.data:
                print("Tablas encontradas:")
                for table in response.data:
                    print(f"  - {table['table_name']} ({table['table_type']})")
            else:
                print("❌ No se pudieron obtener las tablas")
                
        except Exception as e:
            print(f"❌ Error obteniendo tablas: {e}")
            
            # Método alternativo: intentar acceder a tablas conocidas
            print("\n🔄 Intentando método alternativo...")
            
            known_tables = [
                'articulos', 'hechos', 'entidades', 'citas_textuales',
                'datos_cuantitativos', 'contradicciones', 'documentos_extensos',
                'fragmentos_extensos', 'hilos_narrativos'
            ]
            
            existing_tables = []
            for table in known_tables:
                try:
                    # Intentar hacer una consulta simple
                    test_response = supabase.table(table).select('*').limit(1).execute()
                    existing_tables.append(table)
                    print(f"✅ {table} - Existe")
                except Exception as table_error:
                    if "does not exist" in str(table_error):
                        print(f"❌ {table} - No existe")
                    else:
                        print(f"⚠️  {table} - Error: {str(table_error)[:50]}")
        
        # Inspeccionar estructura de tablas existentes
        print("\n🔍 ESTRUCTURA DE TABLAS PRINCIPALES:")
        print("-" * 40)
        
        # Lista de tablas principales a inspeccionar
        main_tables = ['articulos', 'hechos', 'entidades', 'citas_textuales']
        
        for table in main_tables:
            try:
                print(f"\n📊 Tabla: {table}")
                print("-" * 20)
                
                # Intentar obtener la estructura
                columns_query = f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = '{table}' AND table_schema = 'public'
                ORDER BY ordinal_position
                """
                
                try:
                    response = supabase.rpc('execute_sql', {'query': columns_query}).execute()
                    
                    if response.data:
                        print("Columnas:")
                        for col in response.data:
                            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                            print(f"  - {col['column_name']:<30} {col['data_type']:<15} {nullable}{default}")
                    else:
                        print("❌ No se pudo obtener estructura de columnas")
                        
                except Exception:
                    # Método alternativo: obtener una muestra y ver campos
                    print("🔄 Obteniendo estructura desde muestra...")
                    sample_response = supabase.table(table).select('*').limit(1).execute()
                    
                    if sample_response.data and len(sample_response.data) > 0:
                        sample_record = sample_response.data[0]
                        print("Campos encontrados en muestra:")
                        for field, value in sample_record.items():
                            value_type = type(value).__name__
                            print(f"  - {field:<30} {value_type:<15} = {str(value)[:30]}")
                    else:
                        print("   (Tabla vacía, no se puede determinar estructura)")
                        
            except Exception as e:
                if "does not exist" in str(e):
                    print(f"❌ Tabla '{table}' no existe")
                else:
                    print(f"❌ Error inspeccionando '{table}': {str(e)[:50]}")
        
        # Verificar funciones/RPCs
        print("\n🛠️  FUNCIONES RPC DISPONIBLES:")
        print("-" * 40)
        
        try:
            functions_query = """
            SELECT routine_name, routine_type 
            FROM information_schema.routines 
            WHERE routine_schema = 'public' 
            AND routine_name LIKE '%articulo%' OR routine_name LIKE '%fragmento%' OR routine_name LIKE '%entidad%'
            ORDER BY routine_name
            """
            
            response = supabase.rpc('execute_sql', {'query': functions_query}).execute()
            
            if response.data:
                for func in response.data:
                    print(f"✅ {func['routine_name']} ({func['routine_type']})")
            else:
                print("❌ No se encontraron funciones relacionadas")
                
        except Exception as e:
            print(f"❌ Error obteniendo funciones: {e}")
            
            # Método alternativo: probar funciones conocidas
            print("\n🔄 Probando funciones conocidas...")
            known_functions = [
                'insertar_articulo_completo',
                'actualizar_articulo_procesado', 
                'insertar_fragmento_completo',
                'buscar_entidad_similar'
            ]
            
            for func_name in known_functions:
                try:
                    # Llamada mínima para verificar existencia
                    if func_name == 'buscar_entidad_similar':
                        supabase.rpc(func_name, {
                            'nombre_busqueda': 'test',
                            'umbral_similitud': 0.1,
                            'limite_resultados': 1
                        }).execute()
                    print(f"✅ {func_name} - Disponible")
                except Exception as func_error:
                    if "does not exist" in str(func_error):
                        print(f"❌ {func_name} - No existe")
                    else:
                        print(f"⚠️  {func_name} - Existe (error en parámetros)")
        
        # Verificar vistas y triggers
        print("\n📋 ELEMENTOS ADICIONALES:")
        print("-" * 40)
        
        try:
            views_query = """
            SELECT table_name as view_name 
            FROM information_schema.views 
            WHERE table_schema = 'public'
            ORDER BY table_name
            """
            
            response = supabase.rpc('execute_sql', {'query': views_query}).execute()
            
            if response.data:
                print("Vistas disponibles:")
                for view in response.data:
                    print(f"  - {view['view_name']}")
            else:
                print("❌ No se encontraron vistas")
                
        except Exception as e:
            print(f"❌ Error obteniendo vistas: {e}")
            
    except Exception as e:
        print(f"❌ ERROR GENERAL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_database_schema()