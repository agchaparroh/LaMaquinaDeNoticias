#!/usr/bin/env python3
"""
Test simple del pipeline con un artículo mínimo
"""

import json  # noqa: F401
from datetime import datetime

import requests

# URL del pipeline
PIPELINE_URL = "http://localhost:8003/procesar_articulo"

# Datos mínimos del artículo
article_data = {
    "medio": "Test",
    "area_geografica": "España",
    "tipo_medio": "digital",
    "titular": "Prueba de procesamiento con id_temporal",
    "fecha_publicacion": datetime.now().isoformat(),
    "contenido_texto": """
    Este es un artículo de prueba para verificar que el campo id_temporal
    se está incluyendo correctamente en las entidades. El presidente
    Pedro Sánchez se reunió con el ministro de Economía en Madrid.
    La empresa Apple anunció nuevos productos. El encuentro tuvo lugar
    en el Palacio de la Moncloa el día 15 de enero de 2025.
    
    El ministro de Economía, Carlos Cuerpo, presentó las nuevas medidas
    económicas que se implementarán durante el primer trimestre del año.
    Estas medidas incluyen un paquete de ayudas por valor de 500 millones
    de euros destinados a pequeñas y medianas empresas.
    
    Por su parte, el presidente del Gobierno destacó la importancia de
    estas iniciativas para fortalecer la economía española. "Estamos
    comprometidos con el crecimiento sostenible y la creación de empleo",
    afirmó Sánchez durante la rueda de prensa.
    
    La reunión contó también con la presencia de la vicepresidenta primera,
    María Jesús Montero, quien explicó los detalles técnicos del plan.
    Se espera que las medidas beneficien a más de 50.000 empresas en
    todo el territorio nacional.
    """,
}

print("=== Enviando artículo de prueba al pipeline ===")
print(f"Titular: {article_data['titular']}")

try:
    response = requests.post(PIPELINE_URL, json=article_data)

    if response.status_code == 200:
        result = response.json()
        print("\n✅ Procesamiento completado!")
        print(f"Request ID: {result.get('request_id')}")
        print(f"Procesamiento exitoso: {result.get('procesamiento_exitoso')}")

        if result.get("persistencia"):
            pers = result["persistencia"]
            print(f"\nPersistencia: {pers.get('exitosa')}")
            if pers.get("exitosa"):
                print(f"  - Artículo ID: {pers.get('articulo_id')}")
                print(
                    f"  - Hechos: {pers.get('elementos_insertados', {}).get('hechos', 0)}"
                )
                print(
                    f"  - Entidades: {pers.get('elementos_insertados', {}).get('entidades', 0)}"
                )

        if result.get("advertencias"):
            print(f"\n⚠️ Advertencias: {result['advertencias']}")

    else:
        print(f"\n❌ Error: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"\n❌ Error al conectar con el pipeline: {e}")
