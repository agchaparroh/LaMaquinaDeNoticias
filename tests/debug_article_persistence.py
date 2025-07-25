#!/usr/bin/env python3
"""
Script para depurar el problema de persistencia del artículo ID 1100
"""

import json

import requests

# Configuración
PIPELINE_URL = "http://localhost:8003/procesar_articulo"

# Crear artículo de prueba con ID específico
test_article = {
    "articulo_id": 1100,  # ID numérico directo
    "id": "ART-1100",  # ID con prefijo
    "url": "https://www.infobae.com/america/agencias/2025/07/09/eeuu-espera-llegar-a-finales-de-semana-a-un-acuerdo-de-alto-el-fuego-en-gaza",
    "medio": "Infobae",
    "area_geografica": "HISPANOAMERICA",
    "tipo_medio": "otro",
    "titular": "EEUU espera llegar a finales de semana a un acuerdo de alto el fuego en Gaza",
    "fecha_publicacion": "2025-07-09T00:22:29.466Z",
    "contenido_texto": "El enviado especial de Estados Unidos para Oriente Próximo, Steve Witkoff, se ha mostrado optimista sobre la posibilidad de alcanzar un acuerdo de alto el fuego en Gaza. Durante una conferencia de prensa, Witkoff afirmó que las negociaciones han avanzado significativamente y que espera que se pueda llegar a un acuerdo antes del fin de semana.",
    "idioma": "es",
    "autor": "Newsroom Infobae",
    "seccion": "america_latina",
    "es_opinion": False,
    "es_oficial": False,
    "etiquetas_fuente": None,  # Probando con None explícito
    "estado_procesamiento": "pendiente",
}

print("=== DEBUG PERSISTENCIA ARTÍCULO ===")
print(f"Enviando artículo con:")  # noqa: F541
print(
    f"  - articulo_id: {test_article['articulo_id']} (tipo: {type(test_article['articulo_id'])})"
)
print(f"  - id: {test_article['id']}")
print(f"  - url: {test_article['url'][:50]}...")
print(f"  - etiquetas_fuente: {test_article['etiquetas_fuente']}")

try:
    # Enviar al pipeline (directamente el artículo, no en un wrapper)
    response = requests.post(PIPELINE_URL, json=test_article)
    print(f"\nRespuesta HTTP: {response.status_code}")

    result = response.json()
    print("\nRespuesta del pipeline:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Analizar resultado
    if "resultado" in result:
        print(f"\nProcesamiento:")  # noqa: F541
        print(f"  - Estado: {result['resultado'].get('estado', '?')}")
        print(f"  - Job ID: {result.get('job_id', '?')}")
        if "error" in result:
            print(f"  - Error: {result['error']}")
    elif "error" in result:
        print(f"\nError: {result['error']}")
        if "mensaje" in result:
            print(f"Mensaje: {result['mensaje']}")

except Exception as e:
    print(f"\nError: {e}")
