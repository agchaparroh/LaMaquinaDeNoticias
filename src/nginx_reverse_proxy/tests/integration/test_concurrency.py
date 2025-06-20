# tests/integration/test_concurrency.py
"""
Tests de concurrencia para nginx_reverse_proxy.
Valida el manejo de conexiones simultáneas, aislamiento y límites.
"""
import pytest
import requests
import time
import threading
import multiprocessing
import queue
import psutil
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import string


class TestConcurrency:
    """Tests para validar manejo de concurrencia en nginx."""
    
    def test_concurrent_requests_handling(self, nginx_container_running, nginx_base_url):
        """
        Verifica que nginx puede manejar 100 requests simultáneos correctamente.
        """
        num_concurrent_requests = 100
        endpoint = "/nginx-health"
        
        results = {
            "success": 0,
            "failed": 0,
            "response_times": []
        }
        results_lock = threading.Lock()
        
        def make_request(request_id):
            try:
                start = time.perf_counter()
                response = requests.get(f"{nginx_base_url}{endpoint}", timeout=5)
                end = time.perf_counter()
                
                with results_lock:
                    if response.status_code == 200:
                        results["success"] += 1
                        results["response_times"].append(end - start)
                    else:
                        results["failed"] += 1
                        
            except Exception as e:
                with results_lock:
                    results["failed"] += 1
        
        # Lanzar todos los threads simultáneamente
        threads = []
        start_time = time.time()
        
        for i in range(num_concurrent_requests):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Esperar a que terminen todos
        for thread in threads:
            thread.join(timeout=10)
        
        total_time = time.time() - start_time
        
        # Análisis de resultados
        success_rate = results["success"] / num_concurrent_requests
        avg_response_time = sum(results["response_times"]) / len(results["response_times"]) if results["response_times"] else 0
        
        print(f"\nConcurrent Requests Test ({num_concurrent_requests} simultáneos):")
        print(f"  Exitosos: {results['success']}")
        print(f"  Fallidos: {results['failed']}")
        print(f"  Tasa de éxito: {success_rate*100:.1f}%")
        print(f"  Tiempo promedio: {avg_response_time*1000:.2f}ms")
        print(f"  Tiempo total: {total_time:.2f}s")
        
        # Validaciones
        assert success_rate > 0.98, f"Tasa de éxito muy baja: {success_rate*100:.1f}%"
        assert avg_response_time < 1.0, f"Tiempo de respuesta muy alto: {avg_response_time:.2f}s"
    
    def test_connection_limit_behavior(self, nginx_container_running, nginx_base_url):
        """
        Prueba el comportamiento cuando se alcanza el límite de conexiones.
        """
        # Crear muchas conexiones persistentes
        connections = []
        max_connections = 200  # Intentar superar límites típicos
        endpoint = "/api/get"
        
        successful_connections = 0
        rejected_connections = 0
        
        try:
            # Abrir conexiones sin cerrarlas inmediatamente
            for i in range(max_connections):
                try:
                    session = requests.Session()
                    # Hacer request pero mantener la conexión abierta
                    response = session.get(
                        f"{nginx_base_url}{endpoint}",
                        stream=True,  # Mantener conexión abierta
                        timeout=2
                    )
                    
                    if response.status_code == 200:
                        connections.append((session, response))
                        successful_connections += 1
                    else:
                        rejected_connections += 1
                        session.close()
                        
                except Exception:
                    rejected_connections += 1
                
                # Pequeña pausa para no saturar instantáneamente
                if i % 10 == 0:
                    time.sleep(0.1)
            
            print(f"\nConnection Limit Test:")
            print(f"  Conexiones exitosas: {successful_connections}")
            print(f"  Conexiones rechazadas: {rejected_connections}")
            print(f"  Total intentado: {max_connections}")
            
            # Debe manejar gracefully el exceso de conexiones
            assert successful_connections > 50, \
                "Muy pocas conexiones aceptadas"
            assert successful_connections < max_connections, \
                "No hay límite aparente de conexiones"
            
        finally:
            # Limpiar conexiones
            for session, response in connections:
                try:
                    response.close()
                    session.close()
                except:
                    pass
    
    def test_rate_limiting_fairness(self, nginx_container_running, nginx_base_url):
        """
        Verifica que el rate limiting sea justo entre diferentes clientes.
        """
        num_clients = 5
        requests_per_client = 30  # Suficiente para triggear rate limit
        endpoint = "/api/get"
        
        client_results = {}
        
        def client_requests(client_id):
            results = {
                "success": 0,
                "rate_limited": 0,
                "errors": 0
            }
            
            # Simular diferentes IPs con diferentes headers
            headers = {
                "X-Forwarded-For": f"192.168.1.{client_id}",
                "X-Client-Id": f"client-{client_id}"
            }
            
            with requests.Session() as session:
                for i in range(requests_per_client):
                    try:
                        response = session.get(
                            f"{nginx_base_url}{endpoint}",
                            headers=headers
                        )
                        
                        if response.status_code == 200:
                            results["success"] += 1
                        elif response.status_code == 429:  # Too Many Requests
                            results["rate_limited"] += 1
                        else:
                            results["errors"] += 1
                            
                    except Exception:
                        results["errors"] += 1
                    
                    # Pequeña pausa entre requests
                    time.sleep(0.05)
            
            return results
        
        # Ejecutar clientes en paralelo
        with ThreadPoolExecutor(max_workers=num_clients) as executor:
            futures = {
                executor.submit(client_requests, i): i 
                for i in range(num_clients)
            }
            
            for future in as_completed(futures):
                client_id = futures[future]
                client_results[client_id] = future.result()
        
        # Analizar fairness
        print("\nRate Limiting Fairness Test:")
        total_success = 0
        total_limited = 0
        
        for client_id, results in client_results.items():
            success_rate = results["success"] / requests_per_client
            print(f"  Cliente {client_id}:")
            print(f"    Exitosos: {results['success']}")
            print(f"    Rate limited: {results['rate_limited']}")
            print(f"    Tasa de éxito: {success_rate*100:.1f}%")
            
            total_success += results["success"]
            total_limited += results["rate_limited"]
        
        # Verificar que el rate limiting afecta a todos por igual
        success_rates = [
            r["success"] / requests_per_client 
            for r in client_results.values()
        ]
        
        # La desviación no debe ser muy alta (fairness)
        if len(success_rates) > 1:
            avg_rate = sum(success_rates) / len(success_rates)
            max_deviation = max(abs(rate - avg_rate) for rate in success_rates)
            
            assert max_deviation < 0.3, \
                f"Rate limiting no es justo, desviación máxima: {max_deviation:.2f}"
    
    def test_request_isolation(self, nginx_container_running, nginx_base_url):
        """
        Verifica que los headers y datos no se mezclan entre requests concurrentes.
        """
        num_concurrent = 50
        endpoint = "/api/headers"  # httpbin endpoint que devuelve headers
        
        errors = []
        
        def make_isolated_request(request_id):
            # Generar datos únicos para este request
            unique_value = f"request-{request_id}-{random.randint(1000,9999)}"
            headers = {
                "X-Test-Request-Id": unique_value,
                "X-Test-Data": ''.join(random.choices(string.ascii_letters, k=20))
            }
            
            try:
                response = requests.get(
                    f"{nginx_base_url}{endpoint}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    returned_headers = data.get("headers", {})
                    
                    # Verificar que nuestros headers únicos están presentes
                    # y no hay contaminación de otros requests
                    test_id = returned_headers.get("X-Test-Request-Id", "")
                    
                    if test_id != unique_value:
                        errors.append(f"Request {request_id}: Header mismatch")
                        
            except Exception as e:
                errors.append(f"Request {request_id}: {str(e)}")
        
        # Lanzar requests concurrentes
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [
                executor.submit(make_isolated_request, i)
                for i in range(num_concurrent)
            ]
            
            for future in as_completed(futures):
                future.result()
        
        print(f"\nRequest Isolation Test:")
        print(f"  Requests concurrentes: {num_concurrent}")
        print(f"  Errores de aislamiento: {len(errors)}")
        
        if errors:
            for error in errors[:5]:  # Mostrar máximo 5 errores
                print(f"    {error}")
        
        # No debe haber errores de aislamiento
        assert len(errors) == 0, f"Se detectaron {len(errors)} errores de aislamiento"
    
    def test_concurrent_different_routes(self, nginx_container_running, nginx_base_url):
        """
        Prueba requests concurrentes a diferentes rutas (API, frontend, health).
        """
        routes = [
            ("/nginx-health", "health"),
            ("/api/get", "api"),
            ("/", "frontend"),
            ("/api/post", "api_post"),
        ]
        
        results = {route: {"success": 0, "failed": 0} for route, _ in routes}
        results_lock = threading.Lock()
        
        def make_route_request(route_info):
            route, route_type = route_info
            url = f"{nginx_base_url}{route}"
            
            try:
                if route_type == "api_post":
                    response = requests.post(url, json={"test": "data"})
                else:
                    response = requests.get(url)
                
                with results_lock:
                    if response.status_code in [200, 201]:
                        results[route]["success"] += 1
                    else:
                        results[route]["failed"] += 1
                        
            except Exception:
                with results_lock:
                    results[route]["failed"] += 1
        
        # Crear mix de requests a diferentes rutas
        total_requests = 200
        request_mix = []
        for i in range(total_requests):
            request_mix.append(routes[i % len(routes)])
        
        # Ejecutar concurrentemente
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(make_route_request, route_info)
                for route_info in request_mix
            ]
            
            for future in as_completed(futures):
                future.result()
        
        # Mostrar resultados
        print("\nConcurrent Different Routes Test:")
        for route, counts in results.items():
            total = counts["success"] + counts["failed"]
            if total > 0:
                success_rate = counts["success"] / total
                print(f"  {route}:")
                print(f"    Exitosos: {counts['success']}")
                print(f"    Fallidos: {counts['failed']}")
                print(f"    Tasa de éxito: {success_rate*100:.1f}%")
                
                # Todas las rutas deben funcionar concurrentemente
                assert success_rate > 0.95, \
                    f"Ruta {route} tiene baja tasa de éxito: {success_rate*100:.1f}%"
    
    def test_memory_usage_under_concurrency(self, nginx_container_running, nginx_base_url):
        """
        Monitorea el uso de memoria durante alta concurrencia.
        """
        # Obtener uso de memoria inicial del container
        container_name = nginx_container_running
        
        def get_container_memory():
            try:
                result = os.popen(
                    f"docker stats {container_name} --no-stream --format '{{{{.MemUsage}}}}'"
                ).read().strip()
                # Parsear resultado como "50MiB / 100MiB"
                if "/" in result:
                    current = result.split("/")[0].strip()
                    # Convertir a MB
                    if "MiB" in current:
                        return float(current.replace("MiB", ""))
                    elif "GiB" in current:
                        return float(current.replace("GiB", "")) * 1024
                    elif "KiB" in current:
                        return float(current.replace("KiB", "")) / 1024
            except:
                return None
            return None
        
        # Memoria inicial
        initial_memory = get_container_memory()
        print(f"\nMemory Usage Test:")
        print(f"  Memoria inicial: {initial_memory:.2f} MB" if initial_memory else "  No se pudo leer memoria inicial")
        
        # Generar carga concurrente
        num_threads = 100
        requests_per_thread = 50
        
        def generate_load():
            with requests.Session() as session:
                for _ in range(requests_per_thread):
                    try:
                        # Mix de requests
                        if random.random() < 0.7:
                            session.get(f"{nginx_base_url}/nginx-health")
                        else:
                            session.get(f"{nginx_base_url}/api/get")
                        time.sleep(0.01)
                    except:
                        pass
        
        # Ejecutar carga
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(generate_load) for _ in range(num_threads)]
            
            # Monitorear memoria durante la ejecución
            peak_memory = initial_memory or 0
            samples = []
            
            while not all(f.done() for f in futures):
                current_memory = get_container_memory()
                if current_memory:
                    samples.append(current_memory)
                    if current_memory > peak_memory:
                        peak_memory = current_memory
                time.sleep(0.5)
        
        # Memoria final
        time.sleep(2)  # Dar tiempo para estabilizarse
        final_memory = get_container_memory()
        
        if initial_memory and final_memory and samples:
            avg_memory = sum(samples) / len(samples)
            memory_increase = peak_memory - initial_memory
            
            print(f"  Memoria promedio: {avg_memory:.2f} MB")
            print(f"  Memoria pico: {peak_memory:.2f} MB")
            print(f"  Memoria final: {final_memory:.2f} MB")
            print(f"  Incremento máximo: {memory_increase:.2f} MB")
            
            # La memoria no debe crecer excesivamente
            assert memory_increase < 100, \
                f"Uso excesivo de memoria bajo concurrencia: +{memory_increase:.2f} MB"
            
            # Debe haber liberado la mayoría de la memoria
            assert final_memory < initial_memory + 20, \
                "Posible memory leak - memoria no liberada después de la carga"
    
    def test_file_descriptor_limits(self, nginx_container_running, nginx_base_url):
        """
        Verifica que nginx no agota los file descriptors bajo alta concurrencia.
        """
        # Este test crea muchas conexiones simultáneas
        connections = []
        max_connections = 500
        successful = 0
        
        try:
            # Crear conexiones rápidamente
            for i in range(max_connections):
                try:
                    # Crear conexión sin cerrarla inmediatamente
                    session = requests.Session()
                    # Usar stream para mantener la conexión abierta
                    response = session.get(
                        f"{nginx_base_url}/nginx-health",
                        stream=True,
                        timeout=1
                    )
                    
                    if response.status_code == 200:
                        connections.append((session, response))
                        successful += 1
                        
                except Exception:
                    # Esperado cuando se alcanzan límites
                    pass
                
                # Verificar cada 100 conexiones
                if i % 100 == 0 and i > 0:
                    # Hacer un request normal para ver si nginx sigue respondiendo
                    try:
                        test_response = requests.get(
                            f"{nginx_base_url}/nginx-health",
                            timeout=2
                        )
                        if test_response.status_code != 200:
                            print(f"  Nginx dejó de responder después de {i} conexiones")
                            break
                    except:
                        print(f"  Nginx no responde después de {i} conexiones")
                        break
            
            print(f"\nFile Descriptor Test:")
            print(f"  Conexiones simultáneas exitosas: {successful}")
            print(f"  Límite aparente: {successful} conexiones")
            
            # Nginx debe seguir respondiendo incluso con muchas conexiones
            final_test = requests.get(f"{nginx_base_url}/nginx-health", timeout=5)
            assert final_test.status_code == 200, \
                "Nginx no responde después de muchas conexiones"
            
        finally:
            # Limpiar todas las conexiones
            for session, response in connections:
                try:
                    response.close()
                    session.close()
                except:
                    pass
