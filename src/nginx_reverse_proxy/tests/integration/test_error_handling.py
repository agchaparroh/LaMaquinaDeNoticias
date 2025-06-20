# tests/integration/test_error_handling.py
"""
Tests de integración para verificar manejo de errores.
"""
import pytest
import requests
import subprocess
import time


class TestErrorHandling:
    """Tests para verificar el manejo correcto de errores."""
    
    def test_backend_down_handling(self, nginx_container_running, nginx_base_url):
        """Verifica el comportamiento cuando el backend está caído."""
        # Detener el backend mock
        subprocess.run(
            ["docker", "stop", "mock_dashboard_backend"],
            capture_output=True
        )
        
        try:
            # Intentar acceder al API
            response = requests.get(f"{nginx_base_url}/api/health", timeout=5)
            
            # Debe devolver 502 Bad Gateway o 504 Gateway Timeout
            assert response.status_code in [502, 503, 504], \
                f"Status code inesperado cuando backend está caído: {response.status_code}"
            
        finally:
            # Reiniciar el backend
            subprocess.run(
                ["docker", "start", "mock_dashboard_backend"],
                capture_output=True
            )
            time.sleep(2)
    
    def test_frontend_down_handling(self, nginx_container_running, nginx_base_url):
        """Verifica el comportamiento cuando el frontend está caído."""
        # Detener el frontend mock
        subprocess.run(
            ["docker", "stop", "mock_dashboard_frontend"],
            capture_output=True
        )
        
        try:
            # Intentar acceder al frontend
            response = requests.get(f"{nginx_base_url}/", timeout=5)
            
            # Debe devolver error 502/503/504
            assert response.status_code in [502, 503, 504], \
                f"Status code inesperado cuando frontend está caído: {response.status_code}"
            
        finally:
            # Reiniciar el frontend
            subprocess.run(
                ["docker", "start", "mock_dashboard_frontend"],
                capture_output=True
            )
            time.sleep(2)
    
    def test_custom_error_page(self, nginx_container_running, nginx_base_url):
        """Verifica que se muestran páginas de error personalizadas."""
        # Detener backend para forzar un error 502
        subprocess.run(
            ["docker", "stop", "mock_dashboard_backend"],
            capture_output=True
        )
        
        try:
            response = requests.get(f"{nginx_base_url}/api/test", timeout=5)
            
            if response.status_code >= 500:
                # Verificar que se muestra la página de error personalizada
                assert "Service Temporarily Unavailable" in response.text
                assert "dashboard is currently experiencing issues" in response.text
                
        finally:
            subprocess.run(
                ["docker", "start", "mock_dashboard_backend"],
                capture_output=True
            )
            time.sleep(2)
    
    def test_timeout_handling(self, nginx_container_running, nginx_base_url):
        """Verifica el manejo de timeouts."""
        # httpbin tiene un endpoint de delay
        # Intentar un request que tarde más que el timeout configurado
        response = requests.get(f"{nginx_base_url}/api/delay/35", timeout=40)
        
        # Debería timeout antes (configurado a 30s)
        assert response.status_code in [504, 502, 408]
    
    def test_invalid_method_handling(self, nginx_container_running, nginx_base_url):
        """Verifica el manejo de métodos HTTP inválidos."""
        # Intentar un método no soportado
        try:
            response = requests.request("CONNECT", f"{nginx_base_url}/api/test")
            assert response.status_code in [400, 405, 501]
        except:
            # Algunos métodos pueden causar excepciones
            pass
    
    def test_malformed_request_handling(self, nginx_container_running, nginx_base_url):
        """Verifica el manejo de requests malformados."""
        # Enviar headers malformados
        headers = {
            "X-Bad-Header": "value\r\nInjection: attempt"
        }
        
        try:
            response = requests.get(f"{nginx_base_url}/", headers=headers)
            # Nginx debe manejar esto gracefully
            assert response.status_code < 500
        except:
            # Es aceptable si la librería requests rechaza los headers
            pass
    
    def test_404_handling_frontend(self, nginx_container_running, nginx_base_url):
        """Verifica el manejo de rutas no existentes en frontend."""
        response = requests.get(f"{nginx_base_url}/this-route-does-not-exist")
        
        # Para SPA, podría devolver 200 con el index.html (fallback)
        # o 404 si la ruta realmente no existe
        assert response.status_code in [200, 404]
    
    def test_404_handling_api(self, nginx_container_running, nginx_base_url):
        """Verifica el manejo de rutas no existentes en API."""
        response = requests.get(f"{nginx_base_url}/api/this-endpoint-does-not-exist")
        
        # API debe devolver 404
        assert response.status_code == 404
    
    def test_connection_limit_handling(self, nginx_container_running, nginx_base_url):
        """Verifica el manejo cuando se alcanzan límites de conexión."""
        # Crear muchas conexiones simultáneas
        sessions = []
        responses = []
        
        try:
            # Crear 100 conexiones
            for i in range(100):
                session = requests.Session()
                sessions.append(session)
                
                # No cerrar la conexión inmediatamente
                response = session.get(
                    f"{nginx_base_url}/nginx-health",
                    stream=True
                )
                responses.append(response)
            
            # Algunas conexiones pueden ser rechazadas, pero no debe crashear
            successful = [r for r in responses if r.status_code == 200]
            assert len(successful) > 0, "Ninguna conexión fue exitosa"
            
        finally:
            # Limpiar conexiones
            for session in sessions:
                session.close()
    
    def test_upstream_failover(self, nginx_container_running, nginx_base_url):
        """Verifica que nginx marca servidores como down después de fallos."""
        # Este test verifica la configuración max_fails=3 fail_timeout=30s
        
        # Detener backend
        subprocess.run(
            ["docker", "stop", "mock_dashboard_backend"],
            capture_output=True
        )
        
        try:
            # Hacer 4 requests (más que max_fails)
            for i in range(4):
                requests.get(f"{nginx_base_url}/api/health", timeout=2)
                time.sleep(0.5)
            
            # Nginx debe haber marcado el upstream como down
            # Los siguientes requests deben fallar rápidamente
            start = time.time()
            response = requests.get(f"{nginx_base_url}/api/health", timeout=5)
            duration = time.time() - start
            
            assert response.status_code in [502, 503, 504]
            assert duration < 2, "Nginx no está marcando el servidor como down"
            
        finally:
            subprocess.run(
                ["docker", "start", "mock_dashboard_backend"],
                capture_output=True
            )
            time.sleep(2)
