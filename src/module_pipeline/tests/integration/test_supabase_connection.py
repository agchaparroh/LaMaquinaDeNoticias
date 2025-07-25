#!/usr/bin/env python3
"""
Script de prueba para verificar conexión y RPC de Supabase
"""

import os  # noqa: F401
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent))

from ..src.services.supabase_service import SupabaseService


def test_connection():
    print("=== TEST DE CONEXIÓN SUPABASE ===")

    try:
        # Inicializar servicio
        service = SupabaseService()
        print("✓ SupabaseService inicializado correctamente")

        # Probar una consulta simple
        print("\nProbando consulta simple a tabla 'articuloscontenido'...")
        response = (
            service.client.table("articuloscontenido").select("id").limit(1).execute()
        )
        print(f"✓ Consulta exitosa. Registros encontrados: {len(response.data)}")

        # Probar RPC con payload mínimo
        print("\nProbando RPC 'insertar_fragmento_completo' con payload vacío...")
        test_payload = {
            "fragmento": {
                "id_fragmento": "test-000-debug",
                "contenido_original": "Test de conexión",
                "es_relevante": True,
            },
            "entidades": [],
            "hechos": [],
            "datos": [],
            "citas": [],
        }

        try:
            response = service.client.rpc(
                "insertar_fragmento_completo", {"datos_json": test_payload}
            ).execute()

            print(f"Respuesta RPC: {response}")
            print(f"response.data: {response.data}")

            if hasattr(response, "error") and response.error:
                print(f"ERROR en RPC: {response.error}")

        except Exception as e:
            print(f"ERROR al llamar RPC: {type(e).__name__}: {e}")

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_connection()
