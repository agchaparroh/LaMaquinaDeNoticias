"""
Tests para ArticuloProcesableItem
==================================

Tests unitarios para el nuevo modelo ArticuloProcesableItem
que validan su funcionalidad y compatibilidad con el pipeline.
"""

import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timezone
from pydantic import ValidationError

# Importar solo los modelos básicos necesarios
try:
    from src.models.entrada import ArticuloProcesableItem, ArticuloInItem, FragmentoProcesableItem
except ImportError as e:
    print(f"Warning: Could not import models due to missing dependencies: {e}")
    pytest.skip("Skipping tests due to missing dependencies")


class TestArticuloProcesableItem:
    """Tests para el modelo ArticuloProcesableItem."""
    
    def test_articulo_procesable_item_creation(self):
        """Test básico de creación del modelo."""
        articulo = ArticuloProcesableItem(
            id_articulo="ART-123456",
            contenido_texto="Este es el contenido del artículo de prueba.",
            medio="Test News",
            area_geografica="España",
            tipo_medio="Diario Digital",
            titular="Título de prueba",
            fecha_publicacion=datetime.now(timezone.utc)
        )
        
        assert articulo.id_articulo == "ART-123456"
        assert articulo.contenido_texto == "Este es el contenido del artículo de prueba."
        assert articulo.medio == "Test News"
        assert articulo.idioma == "es"  # Valor por defecto
        assert articulo.es_opinion is False  # Valor por defecto
        assert articulo.es_oficial is True  # Valor por defecto
    
    def test_from_articulo_in_item_conversion(self):
        """Test de conversión desde ArticuloInItem."""
        articulo_in = ArticuloInItem(
            articulo_id=123456,
            medio="El País",
            area_geografica="España",
            tipo_medio="Diario Digital",
            titular="Nuevas medidas económicas",
            fecha_publicacion=datetime.now(timezone.utc),
            contenido_texto="El presidente anunció nuevas medidas económicas..."
        )
        
        articulo_procesable = ArticuloProcesableItem.from_articulo_in_item(articulo_in)
        
        assert articulo_procesable.id_articulo == "ART-123456"
        assert articulo_procesable.id_articulo_fuente == 123456
        assert articulo_procesable.contenido_texto == articulo_in.contenido_texto
        assert articulo_procesable.medio == articulo_in.medio
        assert articulo_procesable.titular == articulo_in.titular
        assert articulo_procesable.fecha_publicacion == articulo_in.fecha_publicacion
    
    def test_to_fragmento_procesable_conversion(self):
        """Test de conversión a FragmentoProcesableItem."""
        articulo = ArticuloProcesableItem(
            id_articulo="ART-123456",
            contenido_texto="Contenido del artículo",
            medio="Test News",
            area_geografica="España",
            tipo_medio="Diario Digital",
            titular="Título de prueba",
            fecha_publicacion=datetime.now(timezone.utc)
        )
        
        fragmento = articulo.to_fragmento_procesable()
        
        assert fragmento.id_fragmento == "ART-123456"
        assert fragmento.texto_original == "Contenido del artículo"
        assert fragmento.id_articulo_fuente == "ART-123456"
        assert fragmento.orden_en_articulo == 0
        assert fragmento.metadata_adicional["es_articulo_completo"] is True
        assert fragmento.metadata_adicional["medio"] == "Test News"
        assert fragmento.metadata_adicional["titular"] == "Título de prueba"
    
    def test_validate_required_fields(self):
        """Test de validación de campos requeridos."""
        articulo = ArticuloProcesableItem(
            id_articulo="ART-123456",
            contenido_texto="Contenido del artículo",
            medio="Test News",
            area_geografica="España",
            tipo_medio="Diario Digital",
            titular="Título de prueba",
            fecha_publicacion=datetime.now(timezone.utc)
        )
        
        assert articulo.validate_required_fields() is True
    
    def test_get_processing_context(self):
        """Test de obtención del contexto de procesamiento."""
        articulo = ArticuloProcesableItem(
            id_articulo="ART-123456",
            contenido_texto="Contenido del artículo",
            medio="Test News",
            area_geografica="España",
            tipo_medio="Diario Digital",
            titular="Título de prueba",
            fecha_publicacion=datetime.now(timezone.utc),
            autor="Juan Pérez"
        )
        
        context = articulo.get_processing_context()
        
        assert context["titulo"] == "Título de prueba"
        assert context["fuente"] == "Test News"
        assert context["pais"] == "España"
        assert context["tipo_medio"] == "Diario Digital"
        assert context["idioma"] == "es"
        assert context["autor"] == "Juan Pérez"
        assert context["es_opinion"] is False
    
    def test_validation_error_empty_content(self):
        """Test de error de validación con contenido vacío."""
        with pytest.raises(ValidationError) as exc_info:
            ArticuloProcesableItem(
                id_articulo="ART-123456",
                contenido_texto="",  # Contenido vacío
                medio="Test News",
                area_geografica="España",
                tipo_medio="Diario Digital",
                titular="Título de prueba",
                fecha_publicacion=datetime.now(timezone.utc)
            )
        
        assert "min_length" in str(exc_info.value)
    
    def test_validation_error_short_content(self):
        """Test de error de validación con contenido muy corto."""
        with pytest.raises(ValidationError) as exc_info:
            ArticuloProcesableItem(
                id_articulo="ART-123456",
                contenido_texto="Muy corto",  # Menos de 50 caracteres
                medio="Test News",
                area_geografica="España",
                tipo_medio="Diario Digital",
                titular="Título de prueba",
                fecha_publicacion=datetime.now(timezone.utc)
            )
        
        assert "debe tener al menos 50 caracteres" in str(exc_info.value)
    
    def test_validation_error_opinion_without_author(self):
        """Test de error de validación para artículo de opinión sin autor."""
        with pytest.raises(ValidationError) as exc_info:
            ArticuloProcesableItem(
                id_articulo="ART-123456",
                contenido_texto="Este es un artículo de opinión muy interesante con contenido suficiente.",
                medio="Test News",
                area_geografica="España",
                tipo_medio="Diario Digital",
                titular="Título de prueba",
                fecha_publicacion=datetime.now(timezone.utc),
                es_opinion=True,
                autor=None  # Sin autor
            )
        
        assert "deben tener autor identificado" in str(exc_info.value)
    
    def test_json_serialization(self):
        """Test de serialización JSON."""
        articulo = ArticuloProcesableItem(
            id_articulo="ART-123456",
            contenido_texto="Contenido del artículo de prueba para serialización.",
            medio="Test News",
            area_geografica="España",
            tipo_medio="Diario Digital",
            titular="Título de prueba",
            fecha_publicacion=datetime.now(timezone.utc)
        )
        
        json_data = articulo.model_dump_json()
        assert isinstance(json_data, str)
        assert "ART-123456" in json_data
        assert "Test News" in json_data
    
    def test_url_validation(self):
        """Test de validación de URLs."""
        articulo = ArticuloProcesableItem(
            id_articulo="ART-123456",
            contenido_texto="Contenido del artículo de prueba para validación de URL.",
            medio="Test News",
            area_geografica="España",
            tipo_medio="Diario Digital",
            titular="Título de prueba",
            fecha_publicacion=datetime.now(timezone.utc),
            url="https://example.com/article"
        )
        
        assert articulo.url == "https://example.com/article"
    
    def test_invalid_url_handling(self):
        """Test de manejo de URLs inválidas."""
        articulo = ArticuloProcesableItem(
            id_articulo="ART-123456",
            contenido_texto="Contenido del artículo de prueba para validación de URL inválida.",
            medio="Test News",
            area_geografica="España",
            tipo_medio="Diario Digital",
            titular="Título de prueba",
            fecha_publicacion=datetime.now(timezone.utc),
            url="invalid-url"
        )
        
        # La URL inválida debería ser removida (None)
        assert articulo.url is None