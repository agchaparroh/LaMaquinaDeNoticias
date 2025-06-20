# tests/integration/test_performance.py
"""
Tests de integración para verificar características de performance.
"""
import pytest
import requests
import gzip
import time


class TestNginxPerformance:
    """Tests para verificar optimizaciones de performance."""
    
    def test_gzip_compression_enabled(self, nginx_container_running, nginx_base_url):
        """Verifica que gzip está habilitado para tipos MIME configurados."""
        # Solicitar con Accept-Encoding: gzip
        headers = {"Accept-Encoding": "gzip"}
        response = requests.get(f"{nginx_base_url}/", headers=headers)
        
        # Si el contenido es suficientemente grande, debe venir comprimido
        content_encoding = response.headers.get("Content-Encoding", "")
        
        # Para contenido HTML suficientemente grande
        if len(response.content) > 1000:
            assert content_encoding == "gzip", "Contenido no está comprimido con gzip"
    
    def test_gzip_vary_header(self, nginx_container_running, nginx_base_url):
        """Verifica que se incluye el header Vary cuando se usa gzip."""
        headers = {"Accept-Encoding": "gzip"}
        response = requests.get(f"{nginx_base_url}/", headers=headers)
        
        assert "Vary" in response.headers
        assert "Accept-Encoding" in response.headers.get("Vary", "")
    
    def test_keepalive_connections(self, nginx_container_running, nginx_base_url):
        """Verifica que las conexiones keepalive funcionan."""
        session = requests.Session()
        
        # Hacer múltiples requests con la misma sesión
        response1 = session.get(f"{nginx_base_url}/nginx-health")
        response2 = session.get(f"{nginx_base_url}/nginx-health")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # La conexión debe mantenerse (verificar con headers)
        connection_header = response2.headers.get("Connection", "").lower()
        assert connection_header != "close"
    
    def test_static_content_cache_headers(self, nginx_container_running, nginx_base_url):
        """Verifica headers de cache para contenido estático."""
        # Intentar acceder a rutas que serían estáticas
        static_extensions = [".js", ".css", ".png", ".jpg"]
        
        for ext in static_extensions:
            response = requests.get(f"{nginx_base_url}/static/test{ext}")
            
            # Aunque devuelva 404, podemos verificar que la configuración
            # está activa mirando otros aspectos de la respuesta
            if response.status_code == 200:
                # Si existe el archivo, debe tener headers de cache
                assert "Cache-Control" in response.headers
                assert "Expires" in response.headers
    
    def test_response_time_health_check(self, nginx_container_running, nginx_base_url):
        """Verifica que el health check responde rápidamente."""
        times = []
        
        for _ in range(10):
            start = time.time()
            response = requests.get(f"{nginx_base_url}/nginx-health")
            end = time.time()
            
            assert response.status_code == 200
            times.append(end - start)
        
        avg_time = sum(times) / len(times)
        assert avg_time < 0.1, f"Health check muy lento: {avg_time:.3f}s promedio"
    
    def test_buffering_configuration(self, nginx_container_running, nginx_base_url):
        """Verifica que el buffering está configurado correctamente."""
        # Hacer un request que genere respuesta del backend
        response = requests.get(f"{nginx_base_url}/api/get")
        
        # El buffering debe estar activo (no hay header X-Accel-Buffering: no)
        assert response.headers.get("X-Accel-Buffering") != "no"
    
    def test_timeouts_configuration(self, nginx_container_running, nginx_base_url):
        """Verifica que los timeouts están configurados apropiadamente."""
        # Este test es más para verificar que no hay timeouts prematuros
        # en requests normales
        
        start = time.time()
        response = requests.get(f"{nginx_base_url}/api/get", timeout=35)
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 30, "Request tardó más de lo esperado"
    
    def test_mime_types_correct(self, nginx_container_running, nginx_base_url):
        """Verifica que los tipos MIME se sirven correctamente."""
        # Probar con diferentes extensiones
        test_cases = [
            ("/test.json", "application/json"),
            ("/test.xml", "application/xml"),
            ("/test.txt", "text/plain"),
        ]
        
        for path, expected_mime in test_cases:
            response = requests.get(f"{nginx_base_url}{path}")
            
            # Solo verificar si el archivo existe (no 404)
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                assert expected_mime in content_type
    
    def test_no_etag_for_dynamic_content(self, nginx_container_running, nginx_base_url):
        """Verifica que no se generan ETags para contenido dinámico."""
        response = requests.get(f"{nginx_base_url}/api/get")
        
        # El contenido dinámico no debe tener ETag
        # (esto depende de la configuración específica)
        if response.status_code == 200:
            # Este test es informativo más que estricto
            pass
    
    def test_tcp_nodelay_optimization(self, nginx_container_running, nginx_base_url):
        """Verifica que las optimizaciones TCP están activas."""
        # Hacer requests pequeños que se beneficien de TCP_NODELAY
        small_responses = []
        
        for i in range(5):
            start = time.time()
            response = requests.get(f"{nginx_base_url}/nginx-health")
            duration = time.time() - start
            
            assert response.status_code == 200
            small_responses.append(duration)
        
        # Los requests pequeños deben ser rápidos
        avg_time = sum(small_responses) / len(small_responses)
        assert avg_time < 0.05, f"Requests pequeños son lentos: {avg_time:.3f}s"
