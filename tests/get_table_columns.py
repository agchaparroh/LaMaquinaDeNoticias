#!/usr/bin/env python3
import os

import requests
from dotenv import load_dotenv

load_dotenv()

# Credenciales
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Headers para la API
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
}

# Tablas a consultar
tables = [
    "articulos",
    "entidades",
    "hechos",
    "citas_textuales",
    "datos_cuantitativos",
    "hecho_entidad",
    "hecho_articulo",
]

print("=== COLUMNAS REALES DE LAS TABLAS EN SUPABASE ===\n")

for table in tables:
    # Hacer request a la API REST de Supabase con limit=0 para obtener solo estructura
    response = requests.get(f"{url}/rest/v1/{table}?limit=0", headers=headers)

    print(f"\n📋 TABLA: {table}")
    print("-" * 60)

    if response.status_code == 200:
        # Los headers de respuesta incluyen información sobre las columnas
        if "content-range" in response.headers:
            print(f"Estado: Tabla existe")  # noqa: F541

        # Hacer otra consulta para obtener un registro (si existe) y ver estructura
        response2 = requests.get(
            f"{url}/rest/v1/{table}?select=*&limit=1", headers=headers
        )

        if response2.status_code == 200:
            data = response2.json()
            if data and len(data) > 0:
                # Si hay datos, mostrar columnas
                columns = list(data[0].keys())
                print(f"Columnas ({len(columns)}): {', '.join(sorted(columns))}")
            else:
                # Si no hay datos, intentar con OPTIONS
                options_response = requests.options(
                    f"{url}/rest/v1/{table}", headers=headers
                )
                print(f"Tabla vacía, verificando con OPTIONS...")  # noqa: F541
                print(f"Headers: {dict(options_response.headers)}")
    else:
        print(f"Error {response.status_code}: {response.text}")

print("\n" + "=" * 60)
