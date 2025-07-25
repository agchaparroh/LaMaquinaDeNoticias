#!/usr/bin/env python3
"""Test directo de la función RPC actualizar_articulo_procesado"""

import json
import os

from supabase import create_client

# Configuración
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Variables SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY no configuradas")
    exit(1)

# Crear cliente
client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Payload de prueba mínimo
test_payload = {
    "articulo_id": 1100,
    "url": "https://test.com/article",
    "resumen": "Test de actualización",
    "hechos_extraidos": [],
    "entidades_autonomas": [],
    "citas_textuales_extraidas": [],
    "datos_cuantitativos_extraidos": [],
    "relaciones_hechos": [],
    "relaciones_entidades": [],
    "contradicciones_detectadas": [],
}

print("Payload de prueba:")
print(json.dumps(test_payload, indent=2))
print("\n" + "=" * 50 + "\n")

try:
    # Llamar RPC con estructura correcta
    print("Llamando RPC actualizar_articulo_procesado...")
    response = client.rpc(
        "actualizar_articulo_procesado", {"datos_json": test_payload}
    ).execute()

    print("Respuesta exitosa:")
    print(json.dumps(response.data, indent=2))

except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    if hasattr(e, "response"):
        print(
            f"Response status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}"
        )
        print(
            f"Response body: {e.response.text if hasattr(e.response, 'text') else 'N/A'}"
        )
