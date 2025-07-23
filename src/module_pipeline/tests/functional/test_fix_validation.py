#!/usr/bin/env python3
"""
Test script to verify the fact ID validation fix.
Tests the pipeline with data that includes fact relationships.
"""

import requests
import json
from datetime import datetime
import uuid

# Pipeline API URL
PIPELINE_URL = "http://localhost:8003/procesar_articulo"

# Test article with facts and relationships
test_article = {
    "id_articulo": str(uuid.uuid4()),
    "url": "https://test.example.com/article-test",
    "titular": "Test Article for Fact ID Validation",
    "contenido_texto": """El presidente Pedro Sánchez anunció un aumento del PIB del 3.5% en el primer trimestre. 
    Esta cifra supera las expectativas de los analistas. La inflación se mantiene en el 2.7%.
    El ministro de Economía Carlos Cuerpo confirmó estas cifras en rueda de prensa.""",
    "fecha_publicacion": datetime.now().isoformat(),
    "fecha_captura": datetime.now().isoformat(),
    "medio": "Test Media",
    "tipo_medio": "digital",
    "area_geografica": "España",
    "categorias": ["economia", "politica"],
    "autores": ["Test Author"],
    "idioma": "es",
    "pais_origen": "España",
    "estado_extraccion": "completado",
    "html": "<p>Test HTML</p>",
    "tokens_estimados": 100
}

def test_pipeline():
    """Test the pipeline with the fixed validation."""
    print("Testing pipeline with fact relationships...")
    
    try:
        response = requests.post(
            PIPELINE_URL,
            json=test_article,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS! Pipeline completed without validation errors.")
            print(f"Job ID: {result.get('job_id')}")
            print(f"Status: {result.get('status')}")
            print(f"Message: {result.get('message', 'No message')}")
            
            # Check if facts were processed
            if 'resultado' in result:
                hechos = result['resultado'].get('hechos_extraidos', [])
                print(f"Facts extracted: {len(hechos)}")
                
                relaciones = result['resultado'].get('relaciones_hechos', [])
                print(f"Fact relationships: {len(relaciones)}")
            
            # Print full response for debugging
            print("\nFull response:")
            print(json.dumps(result, indent=2))
        else:
            print(f"ERROR: {response.text}")
            
    except Exception as e:
        print(f"Error calling pipeline: {e}")

if __name__ == "__main__":
    test_pipeline()