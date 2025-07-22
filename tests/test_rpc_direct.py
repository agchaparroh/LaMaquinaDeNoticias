#!/usr/bin/env python3
"""
Script para probar el RPC actualizar_articulo_procesado directamente
"""
import os
from supabase import create_client, Client

# Credenciales
url = "https://aukbzqbcvbsnjdhflyvr.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1a2J6cWJjdmJzbmpkaGZseXZyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NTkxMjY2NiwiZXhwIjoyMDYxNDg4NjY2fQ.83yZqoMnj15_qkEbvqwCQsDgObQpmBoQsd-spxywAsw"

# Crear cliente
supabase: Client = create_client(url, key)

# Payload mínimo para probar
test_payload = {
    "articulo_id": 1100,
    "resumen_generado_pipeline": "Test de actualización"
}

print("=== TEST RPC DIRECTO ===")
print(f"Probando actualizar_articulo_procesado con ID: {test_payload['articulo_id']}")

try:
    # Llamar al RPC
    response = supabase.rpc("actualizar_articulo_procesado", {"datos_json": test_payload}).execute()
    
    print("\nRespuesta del RPC:")
    print(response.data)
    
except Exception as e:
    print(f"\nError: {e}")