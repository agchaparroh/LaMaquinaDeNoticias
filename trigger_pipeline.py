#!/usr/bin/env python3
"""
Script para iniciar el procesamiento de un artículo pendiente
"""

import json

import requests

# URL del pipeline
PIPELINE_URL = "http://localhost:8003/pipeline/process"

# Datos del artículo a procesar
article_data = {
    "url": "https://www.infobae.com/america/agencias/2025/07/09/eeuu-espera-llegar-a-finales-de-semana-a-un-acuerdo-de-alto-el-fuego-en-gaza/",
    "articulo_id": 1100,
    "medio": "Infobae",
    "area_geografica": "HISPANOAMERICA",
    "tipo_medio": "otro",
    "titular": 'EEUU espera llegar a "finales de semana" a un acuerdo de alto el fuego en Gaza',
    "fecha_publicacion": "2025-07-09T00:22:29.466+00:00",
    "contenido_texto": "Contenido de prueba para verificar el procesamiento",
    "autor": "Newsroom Infobae",
    "idioma": "es",
    "seccion": "america_latina",
}

print("=== Iniciando procesamiento del artículo ===")
print(f"ID: {article_data['articulo_id']}")
print(f"Titular: {article_data['titular']}")

try:
    response = requests.post(PIPELINE_URL, json=article_data)

    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Procesamiento iniciado exitosamente!")  # noqa: F541
        print(f"Response: {json.dumps(result, indent=2)}")
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"\n❌ Error al conectar con el pipeline: {e}")
