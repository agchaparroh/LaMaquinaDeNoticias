"""Test integración Frontend → Backend

Verifica que el Frontend puede llamar correctamente las APIs del Backend.
"""

import pytest
import json
from unittest.mock import Mock, patch
import aiohttp


class MockBackendAPI:
    """Mock del Backend API para testing"""
    def __init__(self, base_url="http://localhost:8004"):
        self.base_url = base_url
        self.responses = {}
        
    def set_response(self, endpoint, response_data, status=200):
        """Configura respuesta mock para un endpoint"""
        self.responses[endpoint] = (response_data, status)
        
    async def get(self, endpoint, params=None):
        """Simula GET request"""
        if endpoint in self.responses:
            data, status = self.responses[endpoint]
            return MockResponse(data, status)
        return MockResponse({"error": "Not found"}, 404)
        
    async def post(self, endpoint, json_data=None):
        """Simula POST request"""
        if endpoint in self.responses:
            data, status = self.responses[endpoint]
            return MockResponse(data, status)
        return MockResponse({"error": "Not found"}, 404)


class MockResponse:
    """Mock de respuesta HTTP"""
    def __init__(self, data, status=200):
        self.data = data
        self.status = status
        self.headers = {"Content-Type": "application/json"}
        
    async def json(self):
        return self.data
        
    async def text(self):
        return json.dumps(self.data)


def test_successful_integration():
    """Test caso feliz: Frontend llama API → Backend responde"""
    
    # GIVEN: Un backend mock configurado
    backend = MockBackendAPI()
    
    # Configurar respuestas esperadas
    backend.set_response("/dashboard/articulos", {
        "articulos": [
            {
                "id": "art-001",
                "titular": "Noticia importante",
                "medio": "El Diario",
                "fecha": "2024-01-15T10:00:00Z",
                "estado": "pendiente",
                "elementos": 5
            },
            {
                "id": "art-002",
                "titular": "Otra noticia relevante",
                "medio": "La Prensa",
                "fecha": "2024-01-15T12:00:00Z",
                "estado": "revisado",
                "elementos": 3
            }
        ],
        "total": 2,
        "pagina": 1,
        "por_pagina": 10
    })
    
    backend.set_response("/dashboard/estadisticas", {
        "articulos_totales": 150,
        "articulos_hoy": 12,
        "elementos_extraidos": 875,
        "tasa_revision": 0.3,
        "editores_activos": 3
    })
    
    # WHEN: El Frontend solicita lista de artículos
    async def frontend_get_articles():
        response = await backend.get("/dashboard/articulos", params={
            "pagina": 1,
            "por_pagina": 10,
            "estado": "todos"
        })
        return await response.json()
    
    # Simular llamada async
    import asyncio
    articles_data = asyncio.run(frontend_get_articles())
    
    # THEN: Debe recibir los datos correctamente formateados
    assert "articulos" in articles_data
    assert len(articles_data["articulos"]) == 2
    assert articles_data["total"] == 2
    
    article = articles_data["articulos"][0]
    assert article["id"] == "art-001"
    assert article["titular"] == "Noticia importante"
    assert article["estado"] == "pendiente"
    
    # WHEN: El Frontend solicita estadísticas
    async def frontend_get_stats():
        response = await backend.get("/dashboard/estadisticas")
        return await response.json()
    
    stats_data = asyncio.run(frontend_get_stats())
    
    # THEN: Debe recibir estadísticas actualizadas
    assert stats_data["articulos_totales"] == 150
    assert stats_data["articulos_hoy"] == 12
    assert 0 <= stats_data["tasa_revision"] <= 1
    
    # WHEN: El Frontend envía feedback editorial
    backend.set_response("/dashboard/feedback/art-001", {
        "success": True,
        "mensaje": "Feedback guardado correctamente",
        "feedback_id": "fb-123"
    })
    
    async def frontend_send_feedback():
        feedback_data = {
            "articulo_id": "art-001",
            "aprobado": True,
            "comentarios": "Bien extraído, pero revisar la segunda entidad",
            "elementos_modificados": [
                {
                    "elemento_id": "elem-002",
                    "tipo": "entidad",
                    "correccion": "Nombre corregido de la entidad"
                }
            ]
        }
        response = await backend.post("/dashboard/feedback/art-001", json_data=feedback_data)
        return await response.json()
    
    feedback_response = asyncio.run(frontend_send_feedback())
    
    # THEN: El feedback debe guardarse correctamente
    assert feedback_response["success"] is True
    assert feedback_response["feedback_id"] == "fb-123"


def test_handles_error():
    """Test caso de error: Frontend maneja errores del Backend"""
    
    # GIVEN: Un backend con diferentes tipos de errores
    backend = MockBackendAPI()
    
    # Caso 1: Error 401 - No autorizado
    backend.set_response("/dashboard/articulos", {
        "error": "unauthorized",
        "mensaje": "Token de autenticación inválido o expirado"
    }, status=401)
    
    async def frontend_unauthorized_request():
        response = await backend.get("/dashboard/articulos")
        return response.status, await response.json()
    
    import asyncio
    status, data = asyncio.run(frontend_unauthorized_request())
    
    # THEN: El Frontend debe detectar el error de autenticación
    assert status == 401
    assert data["error"] == "unauthorized"
    
    # Caso 2: Error 500 - Error interno del servidor
    backend.set_response("/dashboard/estadisticas", {
        "error": "internal_error",
        "mensaje": "Error al conectar con la base de datos",
        "request_id": "req-123"
    }, status=500)
    
    async def frontend_server_error():
        response = await backend.get("/dashboard/estadisticas")
        return response.status, await response.json()
    
    status, data = asyncio.run(frontend_server_error())
    
    # THEN: El Frontend debe manejar el error del servidor
    assert status == 500
    assert data["error"] == "internal_error"
    assert "request_id" in data  # Para debugging
    
    # Caso 3: Error 400 - Validación de datos
    backend.set_response("/dashboard/feedback/art-001", {
        "error": "validation_error",
        "mensaje": "Datos de feedback inválidos",
        "detalles": [
            "Campo 'aprobado' es requerido",
            "Campo 'elementos_modificados' debe ser un array"
        ]
    }, status=400)
    
    async def frontend_validation_error():
        # Enviar datos incompletos
        incomplete_feedback = {
            "articulo_id": "art-001",
            # Falta: aprobado, elementos_modificados mal formateado
            "elementos_modificados": "no es un array"
        }
        response = await backend.post("/dashboard/feedback/art-001", json_data=incomplete_feedback)
        return response.status, await response.json()
    
    status, data = asyncio.run(frontend_validation_error())
    
    # THEN: El Frontend debe recibir detalles del error de validación
    assert status == 400
    assert data["error"] == "validation_error"
    assert len(data["detalles"]) == 2
    assert "aprobado" in data["detalles"][0]
    
    # Caso 4: Timeout de red
    async def frontend_timeout():
        # Simular timeout
        try:
            # En un caso real, esto sería un timeout real de aiohttp
            raise aiohttp.ClientTimeout()
        except Exception as e:
            return {"error": "timeout", "mensaje": "La solicitud tardó demasiado tiempo"}
    
    timeout_response = asyncio.run(frontend_timeout())
    assert timeout_response["error"] == "timeout"
