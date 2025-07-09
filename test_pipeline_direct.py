#!/usr/bin/env python3
import requests
import json
from datetime import datetime

# Payload mínimo esperado por el pipeline
test_payload = {
    "articulo": {
        "medio": "Infobae",
        "area_geografica": "HISPANOAMERICA",
        "tipo_medio": "revista",
        "titular": "Test article title",
        "fecha_publicacion": "2025-07-09T00:05:06.128000+00:00",
        "contenido_texto": "This is a test article content that has enough text to pass validation. " * 10,
        "idioma": "es",
        "autor": "Test Author",
        "url": "https://example.com/test",
        "seccion": "test_section",
        "es_opinion": False,
        "es_oficial": True,
        "fecha_recopilacion": "2025-07-09T00:00:00+00:00",
        "estado_procesamiento": "pendiente_connector",
        "etiquetas_fuente": ["test", "development"]
    }
}

# Enviar petición
url = "http://localhost:8003/procesar_articulo"
headers = {"Content-Type": "application/json"}

print("Enviando payload al pipeline...")
print(f"Campos enviados: {list(test_payload['articulo'].keys())}")
print(f"Total de campos: {len(test_payload['articulo'])}")

try:
    response = requests.post(url, json=test_payload, headers=headers)
    print(f"\nRespuesta del servidor:")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Body: {response.text}")
    
    if response.status_code != 200:
        try:
            error_data = response.json()
            print(f"\nError detalles:")
            print(json.dumps(error_data, indent=2))
        except:
            print(f"\nNo se pudo parsear el error como JSON")
            
except Exception as e:
    print(f"\nError al conectar: {e}")