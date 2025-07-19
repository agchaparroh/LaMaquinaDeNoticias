#!/usr/bin/env python3
"""
Script para verificar si el pipeline puede leer artículos de Supabase
"""
import os
from supabase import create_client, Client

# Obtener credenciales del entorno
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_ANON_KEY')  # El pipeline usa ANON_KEY

print(f"=== TEST LECTURA SUPABASE ===")
print(f"URL: {url}")
print(f"Key: {key[:20]}..." if key else "Key: None")

try:
    # Crear cliente
    supabase: Client = create_client(url, key)
    
    # Intentar leer el artículo ID 1100
    print("\nBuscando artículo con ID 1100...")
    response = supabase.table('articulos').select("*").eq('id', 1100).execute()
    
    if response.data and len(response.data) > 0:
        article = response.data[0]
        print(f"\n✅ ARTÍCULO ENCONTRADO:")
        print(f"  - ID: {article.get('id')}")
        print(f"  - URL: {article.get('url')[:50]}...")
        print(f"  - Titular: {article.get('titular')}")
        print(f"  - Estado: {article.get('estado_procesamiento')}")
        print(f"  - Storage Path: {article.get('storage_path')}")
    else:
        print("\n❌ ARTÍCULO NO ENCONTRADO")
        
        # Intentar contar artículos
        print("\nContando artículos en la tabla...")
        count_response = supabase.table('articulos').select("id", count='exact').execute()
        print(f"Total de artículos: {count_response.count}")
        
        # Ver últimos 5 artículos
        print("\nÚltimos 5 artículos:")
        recent = supabase.table('articulos').select("id, url, titular").order('id', desc=True).limit(5).execute()
        for art in recent.data:
            print(f"  - ID {art['id']}: {art['titular'][:50]}...")
            
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print(f"Tipo de error: {type(e).__name__}")