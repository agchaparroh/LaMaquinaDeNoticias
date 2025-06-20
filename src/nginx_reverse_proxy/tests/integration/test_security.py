# tests/integration/test_security.py
"""
Tests de integración para verificar características de seguridad.
"""
import pytest
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestNginxSecurity:
    """Tests para verificar headers de seguridad y rate limiting."""
    
    def test_security_headers_present(self, nginx_container_running, nginx_base_url):
        """Verifica que todos los headers de seguridad están presentes."""
        response = requests.get(f"{nginx_base_url}/")
        
        required_headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
        
        for header, expected_value in required_headers.items():
            assert header in response.headers, f"Header {header} no encontrado"
            assert response.headers[header] == expected_value, \
                f"Header {header} tiene valor incorrecto: {response.headers[header]}"
    
    def test_api_rate_limiting(self, nginx_container_running, nginx_base_url, http_session):
        """Verifica que el rate limiting funciona para rutas API."""
        # API está limitada a 100 requests por minuto (burst 20)
        # Aproximadamente 1.67 requests por segundo
        
        # Hacer 25 requests rápidos (más que el burst de 20)
        responses = []
        for i in range(25):
            response = http_session.get(f"{nginx_base_url}/api/get")
            responses.append(response.status_code)
        
        # Algunos requests deben ser rechazados con 429 o 503
        rejected = [status for status in responses if status in [429, 503]]
        assert len(rejected) > 0, "Rate limiting no está funcionando para API"
    
    def test_general_rate_limiting(self, nginx_container_running, nginx_base_url):
        """Verifica que el rate limiting funciona para rutas generales."""
        # General está limitado a 300 requests por minuto (burst 50)
        # Aproximadamente 5 requests por segundo
        
        # Hacer 60 requests rápidos (más que el burst de 50)
        session = requests.Session()
        responses = []
        
        for i in range(60):
            response = session.get(f"{nginx_base_url}/")
            responses.append(response.status_code)
        
        # Algunos requests deben ser rechazados
        rejected = [status for status in responses if status in [429, 503]]
        assert len(rejected) > 0, "Rate limiting no está funcionando para rutas generales"
    
    def test_rate_limit_burst_recovery(self, nginx_container_running, nginx_base_url):
        """Verifica que el rate limiting se recupera después del burst."""
        session = requests.Session()
        
        # Agotar el burst con requests rápidos
        for i in range(25):
            session.get(f"{nginx_base_url}/api/get")
        
        # Esperar un poco para que se recupere
        time.sleep(2)
        
        # El siguiente request debe pasar
        response = session.get(f"{nginx_base_url}/api/get")
        assert response.status_code == 200, "Rate limiting no se recupera correctamente"
    
    def test_cors_security_on_api(self, nginx_container_running, nginx_base_url):
        """Verifica que CORS está configurado correctamente en rutas API."""
        # Test con origen válido
        headers = {"Origin": "http://localhost:3000"}
        response = requests.get(f"{nginx_base_url}/api/get", headers=headers)
        
        assert "Access-Control-Allow-Origin" in response.headers
        assert response.headers["Access-Control-Allow-Credentials"] == "true"
        assert response.headers["Access-Control-Max-Age"] == "86400"
    
    def test_no_cors_on_frontend(self, nginx_container_running, nginx_base_url):
        """Verifica que CORS no está en rutas frontend."""
        headers = {"Origin": "http://localhost:3000"}
        response = requests.get(f"{nginx_base_url}/", headers=headers)
        
        # Frontend no debe tener headers CORS (solo API)
        assert "Access-Control-Allow-Origin" not in response.headers
    
    def test_method_restrictions(self, nginx_container_running, nginx_base_url):
        """Verifica que solo se permiten métodos HTTP esperados."""
        # Método no estándar
        response = requests.request("TRACE", f"{nginx_base_url}/api/test")
        
        # Nginx debe rechazar métodos no permitidos
        assert response.status_code in [405, 501]
    
    def test_error_page_no_info_disclosure(self, nginx_container_running, nginx_base_url):
        """Verifica que las páginas de error no revelan información sensible."""
        # Forzar un error accediendo a una ruta que cause problemas
        response = requests.get(f"{nginx_base_url}/this-will-cause-error-maybe")
        
        # No debe revelar versión de nginx o detalles internos
        if response.status_code >= 400:
            assert "nginx/" not in response.text.lower()
            assert "version" not in response.text.lower()
    
    def test_concurrent_connections_limit(self, nginx_container_running, nginx_base_url):
        """Verifica que nginx maneja correctamente múltiples conexiones concurrentes."""
        def make_request(i):
            try:
                response = requests.get(f"{nginx_base_url}/nginx-health", timeout=5)
                return response.status_code
            except:
                return -1
        
        # Hacer 50 requests concurrentes
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request, i) for i in range(50)]
            results = [f.result() for f in as_completed(futures)]
        
        # La mayoría deben ser exitosos
        successful = [r for r in results if r == 200]
        assert len(successful) > 40, "Nginx no maneja bien conexiones concurrentes"
    
    def test_headers_not_exposing_backend_info(self, nginx_container_running, nginx_base_url):
        """Verifica que no se expone información del backend."""
        response = requests.get(f"{nginx_base_url}/api/get")
        
        # No debe exponer headers que revelen información del backend
        sensitive_headers = ["Server", "X-Powered-By", "X-AspNet-Version"]
        
        for header in sensitive_headers:
            if header in response.headers:
                value = response.headers[header].lower()
                # Si existe, no debe revelar detalles específicos
                assert "httpbin" not in value
                assert "python" not in value
                assert "gunicorn" not in value
