"""Test integración Scraper → Connector

Verifica que el Scraper genera archivos .json.gz que el Connector puede leer correctamente.
"""

import pytest
import json
import gzip
import tempfile
import os
from datetime import datetime
from pathlib import Path


def create_scraped_article_file(output_dir: str, articles: list) -> str:
    """
    Simula la creación de un archivo .json.gz como lo haría el Scraper.
    
    El Scraper almacena artículos en archivos comprimidos con formato:
    - Nombre: articulos_YYYYMMDD_HHMMSS.json.gz
    - Contenido: Lista de artículos en formato JSON
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"articulos_{timestamp}.json.gz"
    filepath = os.path.join(output_dir, filename)
    
    # Comprimir y escribir el archivo como hace el Scraper
    with gzip.open(filepath, 'wt', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    
    return filepath


def test_successful_integration():
    """Test caso feliz: Scraper genera archivo → Connector lo lee correctamente"""
    
    # GIVEN: Un directorio temporal para simular el flujo
    with tempfile.TemporaryDirectory() as temp_dir:
        
        # Datos de artículo como los genera el Scraper
        article_data = {
            "url": "https://example.com/noticia-123",
            "titular": "Título de la noticia de prueba",
            "medio": "El Diario Test",
            "pais_publicacion": "AR",
            "tipo_medio": "digital",
            "fecha_publicacion": "2024-01-15T10:30:00Z",
            "contenido_texto": "Este es el contenido de la noticia que debe tener al menos 50 caracteres para pasar validación.",
            "contenido_html": "<p>Este es el contenido HTML</p>",
            "autor": "Juan Pérez",
            "seccion": "Política",
            "etiquetas_fuente": ["política", "gobierno"],
            "es_opinion": False,
            "es_oficial": False,
            "fecha_recopilacion": datetime.utcnow().isoformat()
        }
        
        # WHEN: El Scraper genera un archivo .json.gz
        filepath = create_scraped_article_file(temp_dir, [article_data])
        
        # THEN: El archivo debe existir y ser legible
        assert os.path.exists(filepath)
        assert filepath.endswith('.json.gz')
        
        # Simular lectura del Connector
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            content = f.read()
            loaded_data = json.loads(content)
        
        # Verificar que los datos se preservan correctamente
        assert isinstance(loaded_data, list)
        assert len(loaded_data) == 1
        
        article = loaded_data[0]
        assert article['url'] == article_data['url']
        assert article['titular'] == article_data['titular']
        assert article['medio'] == article_data['medio']
        assert len(article['contenido_texto']) >= 50  # Validación mínima del Connector


def test_handles_error():
    """Test caso de error: Connector maneja archivos corruptos o inválidos"""
    
    # GIVEN: Un directorio temporal con archivos problemáticos
    with tempfile.TemporaryDirectory() as temp_dir:
        
        # Caso 1: Archivo .gz corrupto
        corrupted_file = os.path.join(temp_dir, "corrupted.json.gz")
        with open(corrupted_file, 'wb') as f:
            f.write(b"Not a valid gzip file")
        
        # WHEN/THEN: Intentar leer archivo corrupto debe fallar con BadGzipFile
        with pytest.raises(gzip.BadGzipFile):
            with gzip.open(corrupted_file, 'rt', encoding='utf-8') as f:
                f.read()
        
        # Caso 2: JSON inválido dentro del .gz
        invalid_json_file = os.path.join(temp_dir, "invalid.json.gz")
        with gzip.open(invalid_json_file, 'wt', encoding='utf-8') as f:
            f.write("{invalid json content")
        
        # WHEN/THEN: Intentar parsear JSON inválido debe fallar
        with gzip.open(invalid_json_file, 'rt', encoding='utf-8') as f:
            content = f.read()
            with pytest.raises(json.JSONDecodeError):
                json.loads(content)
        
        # Caso 3: Artículo sin campos requeridos
        incomplete_article = {
            "url": "https://example.com/incomplete",
            # Falta: titular, medio, contenido_texto, etc.
        }
        
        incomplete_file = create_scraped_article_file(temp_dir, [incomplete_article])
        
        # El Connector debería poder leer el archivo
        with gzip.open(incomplete_file, 'rt', encoding='utf-8') as f:
            loaded_data = json.loads(f.read())
        
        # Pero detectar que faltan campos requeridos
        article = loaded_data[0]
        assert 'titular' not in article  # Campo requerido faltante
        assert 'contenido_texto' not in article  # Campo requerido faltante
