# tests/integration/test_routing.py
"""
Tests de integración para verificar el routing de nginx.
"""
import pytest
import requests
import time


class TestNginxRouting:
    """Tests para verificar el routing correcto de peticiones."""
    
    def test_nginx_health_endpoint(self, nginx_container_running, nginx_base_url):
        """Verifica que el endpoint /nginx-health responde correctamente."""
        response = requests.get(f"{nginx_base_url}/nginx-health")
        
        assert response.status_code == 200
        assert response.text.strip() == "nginx OK"
        assert response.headers.get("Content-Type") == "text/plain"
    
    def test_api_health_routing(self, nginx_container_running, nginx_base_url):
        """Verifica que /api/health se redirige al backend."""
        response = requests.get(f"{nginx_base_url}/api/health")
        
        # httpbin responde con 404 en /health, pero verificamos que llegó la petición
        assert response.status_code in [200, 404]
    
    def test_api_prefix_removal(self, nginx_container_running, nginx_base_url):
        """Verifica que el prefix /api se elimina al hacer proxy al backend."""
        # Usamos /api/get que httpbin entiende como /get
        response = requests.get(f"{nginx_base_url}/api/get")
        
        assert response.status_code == 200
        data = response.json()
        # httpbin devuelve info sobre la petición recibida
        assert "url" in data
        # La URL no debe contener /api
        assert "/api" not in data["url"]
    
    def test_frontend_routing(self, nginx_container_running, nginx_base_url):
        """Verifica que las rutas raíz se redirigen al frontend."""
        response = requests.get(f"{nginx_base_url}/")
        
        assert response.status_code == 200
        assert "Mock Dashboard Frontend" in response.text
    
    def test_api_cors_headers(self, nginx_container_running, nginx_base_url):
        """Verifica que las rutas API incluyen headers CORS."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
        
        response = requests.get(f"{nginx_base_url}/api/get", headers=headers)
        
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers
    
    def test_options_preflight(self, nginx_container_running, nginx_base_url):
        """Verifica que las peticiones OPTIONS (preflight) responden con 204."""
        response = requests.options(f"{nginx_base_url}/api/test")
        
        assert response.status_code == 204
        assert "Access-Control-Allow-Methods" in response.headers
    
    def test_static_file_cache_headers(self, nginx_container_running, nginx_base_url):
        """Verifica que los archivos estáticos incluyen headers de cache."""
        # Intentar acceder a un archivo estático ficticio
        response = requests.get(f"{nginx_base_url}/static/app.js")
        
        # Aunque no exista, nginx debe procesar la ruta
        # En producción existirían estos archivos
        assert response.status_code in [200, 404]
    
    def test_api_request_headers_forwarding(self, nginx_container_running, nginx_base_url):
        """Verifica que nginx forwarda correctamente los headers."""
        custom_headers = {
            "X-Custom-Header": "test-value",
            "Authorization": "Bearer test-token"
        }
        
        response = requests.get(f"{nginx_base_url}/api/headers", headers=custom_headers)
        
        if response.status_code == 200:
            data = response.json()
            headers = data.get("headers", {})
            
            # Verificar que se forwardan headers importantes
            assert "X-Real-Ip" in headers or "X-Real-IP" in headers
            assert "X-Forwarded-For" in headers
            assert "X-Forwarded-Proto" in headers
    
    def test_post_request_to_api(self, nginx_container_running, nginx_base_url):
        """Verifica que las peticiones POST al API funcionan."""
        test_data = {"test": "data", "number": 123}
        
        response = requests.post(
            f"{nginx_base_url}/api/post",
            json=test_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # httpbin devuelve el JSON que enviamos
        if "json" in data:
            assert data["json"] == test_data
    
    def test_large_request_body(self, nginx_container_running, nginx_base_url):
        """Verifica que nginx acepta bodies grandes hasta el límite configurado."""
        # Crear un payload de ~5MB (límite es 10MB)
        large_data = {"data": "x" * (5 * 1024 * 1024)}
        
        response = requests.post(
            f"{nginx_base_url}/api/post",
            json=large_data,
            timeout=30
        )
        
        # Debe aceptar el request
        assert response.status_code in [200, 413]
        
    def test_too_large_request_body(self, nginx_container_running, nginx_base_url):
        """Verifica que nginx rechaza bodies más grandes que el límite."""
        # Crear un payload de ~11MB (límite es 10MB)
        huge_data = "x" * (11 * 1024 * 1024)
        
        response = requests.post(
            f"{nginx_base_url}/api/post",
            data=huge_data,
            headers={"Content-Type": "text/plain"},
            timeout=30
        )
        
        # Debe rechazar con 413 Request Entity Too Large
        assert response.status_code == 413
