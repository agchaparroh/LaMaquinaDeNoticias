#!/usr/bin/env python3
"""
Script para verificar el estado del artículo procesado
"""
import os
import sys
from supabase import create_client

# Configuración
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://aukbzqbcvbsnjdhflyvr.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_KEY no está configurada")
    sys.exit(1)

# Crear cliente
client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=== Verificando estado del artículo ID 1100 ===")

# Consultar el artículo
response = client.table("articulos").select("*").eq("id", 1100).single().execute()

if response.data:
    articulo = response.data
    print(f"\n✓ Artículo encontrado:")
    print(f"  - ID: {articulo.get('id')}")
    print(f"  - URL: {articulo.get('url')}")
    print(f"  - Estado: {articulo.get('estado_procesamiento')}")
    print(f"  - Fecha procesamiento: {articulo.get('fecha_procesamiento')}")
    print(f"  - Resumen: {articulo.get('resumen', 'No disponible')}")
    print(f"  - Error: {articulo.get('error_detalle', 'Ninguno')}")
    
    # Verificar si fue procesado
    if articulo.get('estado_procesamiento') == 'completado':
        print("\n✅ ÉXITO: El artículo fue procesado completamente!")
        
        # Verificar elementos procesados
        print("\n=== Verificando elementos procesados ===")
        
        # Hechos
        hechos = client.table("hechos").select("id").eq("articulo_id", 1100).execute()
        print(f"✓ Hechos: {len(hechos.data) if hechos.data else 0}")
        
        # Entidades (a través de hecho_entidad)
        entidades = client.rpc("contar_entidades_articulo", {"p_articulo_id": 1100}).execute()
        print(f"✓ Entidades: {entidades.data if entidades.data else 0}")
        
        # Citas
        citas = client.table("citas_textuales").select("id").eq("articulo_id", 1100).execute()
        print(f"✓ Citas: {len(citas.data) if citas.data else 0}")
        
        # Datos cuantitativos
        datos = client.table("datos_cuantitativos").select("id").eq("articulo_id", 1100).execute()
        print(f"✓ Datos: {len(datos.data) if datos.data else 0}")
        
    else:
        print(f"\n⚠️ El artículo está en estado: {articulo.get('estado_procesamiento')}")
else:
    print("\n❌ No se encontró el artículo con ID 1100")

print("\n=== Verificando últimos artículos procesados ===")
# Buscar últimos artículos procesados exitosamente
ultimos = client.table("articulos").select("id, titular, fecha_procesamiento, estado_procesamiento").eq("estado_procesamiento", "completado").order("fecha_procesamiento", desc=True).limit(5).execute()

if ultimos.data:
    print(f"\nÚltimos {len(ultimos.data)} artículos procesados exitosamente:")
    for art in ultimos.data:
        print(f"  - ID {art['id']}: {art['titular'][:50]}... ({art['fecha_procesamiento']})")
else:
    print("\n⚠️ No hay artículos procesados exitosamente")