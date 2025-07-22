#!/usr/bin/env python3
"""
Script de prueba para actualizar artículo existente
"""
import requests
import json
import sys

# Leer archivo de prueba
with open("test_article_relevante.json", "r") as f:
    article_data = json.load(f)

# Crear payload para el endpoint
payload = {
    "articulos": [article_data]
}

# URL del endpoint
url = "http://localhost:8003/pipeline/procesar/lote"

# Enviar request
print("Enviando artículo para actualización...")
print(f"ID: {article_data['articulo_id']}")
print(f"URL: {article_data['url'][:50]}...")

try:
    response = requests.post(url, json=payload)
    response.raise_for_status()
    
    result = response.json()
    print("\n✅ Respuesta del servidor:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Verificar si hay errores
    if "detalles" in result and result["detalles"]:
        for detalle in result["detalles"]:
            if "error" in detalle:
                print(f"\n❌ Error en procesamiento: {detalle['error']}")
            else:
                print(f"\n✅ Artículo procesado exitosamente")
                
except requests.exceptions.RequestException as e:
    print(f"\n❌ Error de conexión: {e}")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"\n❌ Error decodificando respuesta: {e}")
    print(f"Respuesta raw: {response.text}")
    sys.exit(1)