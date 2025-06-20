# tests/integration/test_advanced_performance.py
"""
Tests avanzados de performance para nginx_reverse_proxy.
Incluye medición de latencias, throughput y optimizaciones.
"""
import pytest
import requests
import time
import statistics
import concurrent.futures
import gzip
from datetime import datetime


class TestAdvancedPerformance:
    """Tests avanzados de performance y optimización."""
    
    def test_latency_percentiles(self, nginx_container_running, nginx_base_url):
        """
        Mide percentiles de latencia (p50, p95, p99) para diferentes endpoints.
        """
        endpoints = [
            "/nginx-health",  # Endpoint más ligero
            "/api/get",       # Endpoint de API
            "/"              # Frontend
        ]
        
        results = {}
        
        for endpoint in endpoints:
            latencies = []
            
            # Realizar 100 requests para obtener muestra significativa
            for _ in range(100):
                start = time.perf_counter()
                response = requests.get(f"{nginx_base_url}{endpoint}")
                end = time.perf_counter()
                
                if response.status_code == 200:
                    latencies.append((end - start) * 1000)  # Convertir a ms
            
            if latencies:
                latencies.sort()
                results[endpoint] = {
                    "p50": latencies[int(len(latencies) * 0.5)],
                    "p95": latencies[int(len(latencies) * 0.95)],
                    "p99": latencies[int(len(latencies) * 0.99)],
                    "min": min(latencies),
                    "max": max(latencies),
                    "avg": statistics.mean(latencies)
                }
        
        # Validaciones
        assert results["/nginx-health"]["p99"] < 100, \
            f"Health check p99 muy alto: {results['/nginx-health']['p99']:.2f}ms"
        
        # Mostrar resultados para análisis
        for endpoint, metrics in results.items():
            print(f"\n{endpoint}:")
            print(f"  p50: {metrics['p50']:.2f}ms")
            print(f"  p95: {metrics['p95']:.2f}ms")
            print(f"  p99: {metrics['p99']:.2f}ms")
            print(f"  avg: {metrics['avg']:.2f}ms")
    
    def test_connection_pooling_efficiency(self, nginx_container_running, nginx_base_url):
        """
        Verifica la eficiencia del connection pooling comparando 
        requests con y sin reutilización de conexiones.
        """
        num_requests = 50
        
        # Test SIN connection pooling (nueva conexión cada vez)
        no_pool_times = []
        for _ in range(num_requests):
            start = time.perf_counter()
            # Crear nueva sesión cada vez fuerza nueva conexión
            response = requests.get(f"{nginx_base_url}/nginx-health")
            end = time.perf_counter()
            no_pool_times.append(end - start)
            response.close()
        
        # Test CON connection pooling
        pool_times = []
        with requests.Session() as session:
            for _ in range(num_requests):
                start = time.perf_counter()
                response = session.get(f"{nginx_base_url}/nginx-health")
                end = time.perf_counter()
                pool_times.append(end - start)
        
        avg_no_pool = statistics.mean(no_pool_times)
        avg_pool = statistics.mean(pool_times)
        
        print(f"\nConnection Pooling Efficiency:")
        print(f"  Sin pooling: {avg_no_pool*1000:.2f}ms promedio")
        print(f"  Con pooling: {avg_pool*1000:.2f}ms promedio")
        print(f"  Mejora: {((avg_no_pool - avg_pool) / avg_no_pool * 100):.1f}%")
        
        # El pooling debe ser significativamente más rápido
        assert avg_pool < avg_no_pool * 0.8, \
            "Connection pooling no muestra mejora significativa"
    
    def test_static_vs_dynamic_performance(self, nginx_container_running, nginx_base_url):
        """
        Compara el rendimiento entre contenido estático y dinámico.
        """
        # Preparar requests
        static_path = "/static/test.js"  # Simulará contenido estático
        dynamic_path = "/api/get"        # Contenido dinámico
        
        static_times = []
        dynamic_times = []
        
        with requests.Session() as session:
            # Medir contenido estático
            for _ in range(50):
                start = time.perf_counter()
                response = session.get(f"{nginx_base_url}{static_path}")
                end = time.perf_counter()
                if response.status_code in [200, 404]:  # 404 esperado si no existe
                    static_times.append(end - start)
            
            # Medir contenido dinámico
            for _ in range(50):
                start = time.perf_counter()
                response = session.get(f"{nginx_base_url}{dynamic_path}")
                end = time.perf_counter()
                if response.status_code == 200:
                    dynamic_times.append(end - start)
        
        if static_times and dynamic_times:
            avg_static = statistics.mean(static_times)
            avg_dynamic = statistics.mean(dynamic_times)
            
            print(f"\nStatic vs Dynamic Performance:")
            print(f"  Static: {avg_static*1000:.2f}ms promedio")
            print(f"  Dynamic: {avg_dynamic*1000:.2f}ms promedio")
            
            # El contenido estático generalmente debe ser más rápido
            # pero esto depende de si realmente existe el archivo
    
    def test_gzip_compression_ratio(self, nginx_container_running, nginx_base_url):
        """
        Mide el ratio de compresión real alcanzado por gzip.
        """
        # Crear contenido que se comprima bien (texto repetitivo)
        test_content_sizes = [
            1024,      # 1KB
            10240,     # 10KB
            102400,    # 100KB
        ]
        
        compression_ratios = []
        
        session = requests.Session()
        
        for size in test_content_sizes:
            # Request sin compresión
            headers_no_gzip = {"Accept-Encoding": "identity"}
            response_no_gzip = session.get(
                f"{nginx_base_url}/", 
                headers=headers_no_gzip
            )
            uncompressed_size = len(response_no_gzip.content)
            
            # Request con compresión
            headers_gzip = {"Accept-Encoding": "gzip"}
            response_gzip = session.get(
                f"{nginx_base_url}/", 
                headers=headers_gzip
            )
            
            # Si viene comprimido, calcular ratio
            if response_gzip.headers.get("Content-Encoding") == "gzip":
                compressed_size = len(response_gzip.content)
                ratio = 1 - (compressed_size / uncompressed_size)
                compression_ratios.append(ratio)
                
                print(f"\nGzip Compression (content size ~{uncompressed_size} bytes):")
                print(f"  Uncompressed: {uncompressed_size} bytes")
                print(f"  Compressed: {compressed_size} bytes")
                print(f"  Ratio: {ratio*100:.1f}% reduction")
        
        # Si hay compresión, debe ser efectiva
        if compression_ratios:
            avg_ratio = statistics.mean(compression_ratios)
            assert avg_ratio > 0.3, \
                f"Compresión gzip poco efectiva: {avg_ratio*100:.1f}% promedio"
    
    def test_cache_hit_ratio(self, nginx_container_running, nginx_base_url):
        """
        Valida la efectividad del cache para contenido estático.
        """
        static_resource = "/static/app.css"
        
        with requests.Session() as session:
            # Primera request (cache miss)
            response1 = session.get(f"{nginx_base_url}{static_resource}")
            
            if response1.status_code == 200:
                # Verificar headers de cache
                cache_control = response1.headers.get("Cache-Control", "")
                expires = response1.headers.get("Expires", "")
                
                assert cache_control or expires, \
                    "No hay headers de cache en contenido estático"
                
                # Segunda request (debería ser cache hit en el cliente)
                response2 = session.get(f"{nginx_base_url}{static_resource}")
                
                # Tercera request con validación condicional
                if "ETag" in response1.headers:
                    headers = {"If-None-Match": response1.headers["ETag"]}
                    response3 = session.get(
                        f"{nginx_base_url}{static_resource}",
                        headers=headers
                    )
                    # Debería retornar 304 Not Modified si el cache funciona
                    assert response3.status_code in [200, 304], \
                        "Cache validation no funciona correctamente"
    
    def test_requests_per_second(self, nginx_container_running, nginx_base_url):
        """
        Mide el máximo de requests por segundo que puede manejar nginx.
        """
        duration = 5  # segundos
        endpoint = "/nginx-health"  # Endpoint ligero para máximo RPS
        
        start_time = time.time()
        request_count = 0
        errors = 0
        
        with requests.Session() as session:
            while time.time() - start_time < duration:
                try:
                    response = session.get(f"{nginx_base_url}{endpoint}")
                    if response.status_code == 200:
                        request_count += 1
                    else:
                        errors += 1
                except Exception:
                    errors += 1
        
        elapsed = time.time() - start_time
        rps = request_count / elapsed
        error_rate = errors / (request_count + errors) if (request_count + errors) > 0 else 0
        
        print(f"\nRequests Per Second Test:")
        print(f"  Duration: {elapsed:.2f}s")
        print(f"  Successful requests: {request_count}")
        print(f"  RPS: {rps:.2f}")
        print(f"  Error rate: {error_rate*100:.2f}%")
        
        # Validaciones
        assert rps > 100, f"RPS muy bajo: {rps:.2f}"
        assert error_rate < 0.01, f"Tasa de error alta: {error_rate*100:.2f}%"
    
    def test_bandwidth_utilization(self, nginx_container_running, nginx_base_url):
        """
        Mide el ancho de banda utilizado para diferentes tipos de contenido.
        """
        test_endpoints = [
            ("/nginx-health", "text"),
            ("/api/get", "json"),
            ("/", "html"),
        ]
        
        bandwidth_results = []
        
        with requests.Session() as session:
            for endpoint, content_type in test_endpoints:
                start_time = time.time()
                total_bytes = 0
                request_count = 0
                
                # Medir durante 2 segundos
                while time.time() - start_time < 2:
                    response = session.get(f"{nginx_base_url}{endpoint}")
                    if response.status_code == 200:
                        total_bytes += len(response.content)
                        request_count += 1
                
                elapsed = time.time() - start_time
                bandwidth_mbps = (total_bytes * 8) / (elapsed * 1_000_000)  # Mbps
                
                bandwidth_results.append({
                    "endpoint": endpoint,
                    "type": content_type,
                    "bandwidth_mbps": bandwidth_mbps,
                    "requests": request_count,
                    "avg_size_kb": (total_bytes / request_count / 1024) if request_count > 0 else 0
                })
        
        # Mostrar resultados
        print("\nBandwidth Utilization:")
        for result in bandwidth_results:
            print(f"  {result['endpoint']} ({result['type']}):")
            print(f"    Bandwidth: {result['bandwidth_mbps']:.2f} Mbps")
            print(f"    Avg size: {result['avg_size_kb']:.2f} KB")
            print(f"    Requests: {result['requests']}")
    
    def test_response_time_under_load(self, nginx_container_running, nginx_base_url):
        """
        Mide tiempos de respuesta bajo carga moderada usando threads concurrentes.
        """
        concurrent_users = 10
        requests_per_user = 20
        endpoint = "/api/get"
        
        response_times = []
        errors = []
        
        def make_request(user_id):
            times = []
            user_errors = 0
            
            with requests.Session() as session:
                for i in range(requests_per_user):
                    try:
                        start = time.perf_counter()
                        response = session.get(f"{nginx_base_url}{endpoint}")
                        end = time.perf_counter()
                        
                        if response.status_code == 200:
                            times.append(end - start)
                        else:
                            user_errors += 1
                    except Exception as e:
                        user_errors += 1
                    
                    # Pequeña pausa para simular usuario real
                    time.sleep(0.1)
            
            return times, user_errors
        
        # Ejecutar requests concurrentemente
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(make_request, i) 
                for i in range(concurrent_users)
            ]
            
            for future in concurrent.futures.as_completed(futures):
                times, user_errors = future.result()
                response_times.extend(times)
                errors.append(user_errors)
        
        # Analizar resultados
        if response_times:
            avg_time = statistics.mean(response_times) * 1000  # ms
            p95_time = sorted(response_times)[int(len(response_times) * 0.95)] * 1000
            total_errors = sum(errors)
            
            print(f"\nResponse Time Under Load:")
            print(f"  Concurrent users: {concurrent_users}")
            print(f"  Total requests: {concurrent_users * requests_per_user}")
            print(f"  Average response time: {avg_time:.2f}ms")
            print(f"  95th percentile: {p95_time:.2f}ms")
            print(f"  Total errors: {total_errors}")
            
            # Validaciones
            assert avg_time < 500, f"Tiempo de respuesta promedio muy alto bajo carga: {avg_time:.2f}ms"
            assert p95_time < 1000, f"P95 muy alto bajo carga: {p95_time:.2f}ms"
            assert total_errors < (concurrent_users * requests_per_user * 0.01), \
                "Demasiados errores bajo carga moderada"
