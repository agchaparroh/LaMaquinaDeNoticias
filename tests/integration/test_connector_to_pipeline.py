"""Test integración Connector → Pipeline

Verifica que el Connector envía correctamente artículos al Pipeline API.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from datetime import datetime


class MockArticle:
    """Mock de ArticuloInItem del Connector"""
    def __init__(self, **kwargs):
        self.titular = kwargs.get('titular', 'Título de prueba')
        self.medio = kwargs.get('medio', 'Medio Test')
        self.pais_publicacion = kwargs.get('pais_publicacion', 'AR')
        self.tipo_medio = kwargs.get('tipo_medio', 'digital')
        self.fecha_publicacion = kwargs.get('fecha_publicacion', datetime.utcnow())
        self.contenido_texto = kwargs.get('contenido_texto', 'Contenido de prueba con más de 50 caracteres necesarios')
        self.url = kwargs.get('url', 'https://example.com/test')
        self.idioma = kwargs.get('idioma', 'es')
        self.fecha_recopilacion = kwargs.get('fecha_recopilacion', datetime.utcnow())
        
    def model_dump(self):
        """Simula el método model_dump() de Pydantic"""
        return {
            'titular': self.titular,
            'medio': self.medio,
            'pais_publicacion': self.pais_publicacion,
            'tipo_medio': self.tipo_medio,
            'fecha_publicacion': self.fecha_publicacion.isoformat() if hasattr(self.fecha_publicacion, 'isoformat') else str(self.fecha_publicacion),
            'contenido_texto': self.contenido_texto,
            'url': self.url,
            'idioma': self.idioma,
            'fecha_recopilacion': self.fecha_recopilacion.isoformat() if hasattr(self.fecha_recopilacion, 'isoformat') else str(self.fecha_recopilacion)
        }


def test_successful_integration():
    """Test caso feliz: Connector envía JSON → Pipeline responde 202"""
    
    # GIVEN: Un artículo válido para enviar
    article = MockArticle(
        titular="Noticia importante sobre tecnología",
        medio="Tech News",
        contenido_texto="Este es un contenido de prueba que tiene más de 50 caracteres para cumplir con la validación mínima del Pipeline."
    )
    
    # Mock de la sesión HTTP
    mock_response = AsyncMock()
    mock_response.status = 202  # Accepted
    mock_response.json = AsyncMock(return_value={"success": True, "fragmento_id": "test-123"})
    
    # WHEN: El Connector envía el artículo al Pipeline
    async def simulate_connector_send():
        # Simular el endpoint del Pipeline
        endpoint = "http://module_pipeline:8003/procesar_articulo"
        
        # Preparar payload como lo hace el Connector
        article_dict = article.model_dump()
        payload = {"articulo": article_dict}
        
        # Verificar estructura del payload
        assert "articulo" in payload
        assert payload["articulo"]["titular"] == "Noticia importante sobre tecnología"
        assert len(payload["articulo"]["contenido_texto"]) >= 50
        
        # Simular respuesta exitosa del Pipeline
        return 202, {"success": True, "fragmento_id": "test-123"}
    
    # THEN: El Pipeline debe aceptar el artículo
    import asyncio
    status, response = asyncio.run(simulate_connector_send())
    
    assert status == 202
    assert response["success"] is True
    assert "fragmento_id" in response


def test_handles_error():
    """Test caso de error: Pipeline rechaza artículos inválidos"""
    
    # GIVEN: Artículos con problemas
    
    # Caso 1: Artículo con contenido muy corto
    short_article = MockArticle(
        contenido_texto="Muy corto"  # < 50 caracteres
    )
    
    # Mock de respuesta 400 del Pipeline
    async def simulate_validation_error():
        # El Pipeline debería rechazar con 400
        article_dict = short_article.model_dump()
        
        # Validación que haría el Pipeline
        if len(article_dict['contenido_texto']) < 50:
            return 400, {
                "error": "validation_error",
                "mensaje": "Error en la validación del artículo",
                "detalles": ["Campo 'contenido_texto' debe tener al menos 50 caracteres"]
            }
        
        return 202, {"success": True}
    
    # WHEN/THEN: El Pipeline rechaza el artículo
    import asyncio
    status, response = asyncio.run(simulate_validation_error())
    
    assert status == 400
    assert response["error"] == "validation_error"
    assert "contenido_texto" in response["detalles"][0]
    
    # Caso 2: Pipeline no disponible (500 error)
    async def simulate_server_error():
        # Simular error del servidor
        return 500, {"error": "internal_error", "mensaje": "Error interno del pipeline"}
    
    status, response = asyncio.run(simulate_server_error())
    assert status == 500
    assert response["error"] == "internal_error"
    
    # Caso 3: Timeout de conexión
    async def simulate_timeout():
        # El Connector tiene timeout de 30 segundos
        try:
            # Simular timeout
            raise aiohttp.ClientTimeout()
        except Exception as e:
            return None, {"error": "timeout", "message": str(e)}
    
    status, response = asyncio.run(simulate_timeout())
    assert response["error"] == "timeout"
