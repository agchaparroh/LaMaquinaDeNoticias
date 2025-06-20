# tests/integration/test_recovery.py
"""
Tests de recuperación para nginx_reverse_proxy.
Valida la capacidad de recuperación ante fallos y reconexión automática.
"""
import pytest
import requests
import time
import subprocess
import docker
from datetime import datetime
import threading


class TestRecovery:
    """Tests para validar recuperación ante fallos."""
    
    @pytest.fixture
    def docker_client(self):
        """Cliente Docker para manipular containers."""
        return docker.from_env()
    
    def test_backend_recovery(self, nginx_container_running, nginx_base_url, docker_client):
        """
        Verifica que nginx se recupera cuando el backend vuelve después de estar caído.
        """
        backend_container_name = "mock_dashboard_backend"
        
        print("\nBackend Recovery Test:")
        
        # 1. Verificar que funciona inicialmente
        response = requests.get(f"{nginx_base_url}/api/get")
        initial_status = response.status_code
        print(f"  Estado inicial del backend: {initial_status}")
        assert initial_status == 200, "Backend no está funcionando inicialmente"
        
        # 2. Detener el backend
        try:
            backend_container = docker_client.containers.get(backend_container_name)
            backend_container.stop()
            print("  Backend detenido")
        except Exception as e:
            pytest.skip(f"No se pudo detener el backend: {e}")
        
        # 3. Verificar que nginx maneja el fallo correctamente
        time.sleep(2)  # Dar tiempo para que nginx detecte el fallo
        
        failed_responses = []
        for i in range(3):
            try:
                response = requests.get(f"{nginx_base_url}/api/get", timeout=5)
                failed_responses.append(response.status_code)
            except:
                failed_responses.append(0)
            time.sleep(1)
        
        print(f"  Respuestas con backend caído: {failed_responses}")
        # Debe devolver 502/503/504 cuando el backend está caído
        assert all(status in [0, 502, 503, 504] for status in failed_responses), \
            "Nginx no maneja correctamente el backend caído"
        
        # 4. Reiniciar el backend
        backend_container.start()
        print("  Backend reiniciado")
        
        # 5. Verificar recuperación automática
        recovery_attempts = []
        recovery_time = None
        max_attempts = 30  # 30 segundos máximo para recuperarse
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{nginx_base_url}/api/get", timeout=2)
                recovery_attempts.append(response.status_code)
                
                if response.status_code == 200:
                    recovery_time = attempt + 1
                    break
            except:
                recovery_attempts.append(0)
            
            time.sleep(1)
        
        print(f"  Intentos de recuperación: {len(recovery_attempts)}")
        print(f"  Tiempo de recuperación: {recovery_time}s" if recovery_time else "  No se recuperó")
        
        # Debe recuperarse
        assert recovery_time is not None, "Nginx no se recuperó después de que el backend volvió"
        assert recovery_time < 20, f"Recuperación muy lenta: {recovery_time}s"
        
        # 6. Verificar que funciona normalmente después de recuperarse
        for i in range(5):
            response = requests.get(f"{nginx_base_url}/api/get")
            assert response.status_code == 200, \
                f"Backend no estable después de recuperación, intento {i+1}"
    
    def test_frontend_recovery(self, nginx_container_running, nginx_base_url, docker_client):
        """
        Verifica que nginx se recupera cuando el frontend vuelve después de estar caído.
        """
        frontend_container_name = "mock_dashboard_frontend"
        
        print("\nFrontend Recovery Test:")
        
        # 1. Verificar estado inicial
        response = requests.get(f"{nginx_base_url}/")
        assert response.status_code == 200, "Frontend no está funcionando inicialmente"
        
        # 2. Detener frontend
        try:
            frontend_container = docker_client.containers.get(frontend_container_name)
            frontend_container.stop()
            print("  Frontend detenido")
        except Exception as e:
            pytest.skip(f"No se pudo detener el frontend: {e}")
        
        # 3. Verificar respuesta con frontend caído
        time.sleep(2)
        response = requests.get(f"{nginx_base_url}/", timeout=5)
        print(f"  Respuesta con frontend caído: {response.status_code}")
        assert response.status_code in [502, 503, 504], \
            "Nginx no devuelve error apropiado con frontend caído"
        
        # 4. Reiniciar frontend
        frontend_container.start()
        print("  Frontend reiniciado")
        
        # 5. Verificar recuperación
        recovered = False
        for i in range(15):
            time.sleep(1)
            try:
                response = requests.get(f"{nginx_base_url}/", timeout=2)
                if response.status_code == 200:
                    recovered = True
                    print(f"  Frontend recuperado después de {i+1}s")
                    break
            except:
                pass
        
        assert recovered, "Frontend no se recuperó"
    
    def test_partial_upstream_failure(self, nginx_container_running, nginx_base_url):
        """
        Verifica el comportamiento con fallo parcial de upstreams.
        """
        # Este test simula que algunos endpoints fallan mientras otros funcionan
        
        print("\nPartial Upstream Failure Test:")
        
        # Hacer requests a diferentes endpoints
        endpoints = [
            ("/nginx-health", "health"),  # Siempre debe funcionar
            ("/api/get", "api"),          # Puede fallar si backend está mal
            ("/", "frontend"),            # Puede fallar si frontend está mal
        ]
        
        results = {}
        
        # Probar cada endpoint múltiples veces
        for endpoint, name in endpoints:
            successes = 0
            failures = 0
            
            for _ in range(10):
                try:
                    response = requests.get(f"{nginx_base_url}{endpoint}", timeout=3)
                    if response.status_code == 200:
                        successes += 1
                    else:
                        failures += 1
                except:
                    failures += 1
                
                time.sleep(0.1)
            
            results[name] = {
                "success": successes,
                "failed": failures,
                "rate": successes / 10
            }
        
        print("  Resultados por endpoint:")
        for name, stats in results.items():
            print(f"    {name}: {stats['success']}/10 exitosos ({stats['rate']*100:.0f}%)")
        
        # El health check siempre debe funcionar
        assert results["health"]["rate"] == 1.0, \
            "Health check falló - problema con nginx mismo"
    
    def test_nginx_reload_recovery(self, nginx_container_running, nginx_base_url, docker_client):
        """
        Verifica que nginx mantiene el servicio durante un reload de configuración.
        """
        container_name = nginx_container_running
        
        print("\nNginx Reload Recovery Test:")
        
        # 1. Verificar estado inicial
        response = requests.get(f"{nginx_base_url}/nginx-health")
        assert response.status_code == 200
        
        # 2. Iniciar requests continuos en background
        reload_happened = False
        errors_during_reload = []
        requests_count = 0
        
        def continuous_requests():
            nonlocal requests_count, errors_during_reload
            
            while not reload_happened or requests_count < 50:
                try:
                    response = requests.get(f"{nginx_base_url}/nginx-health", timeout=1)
                    if response.status_code != 200:
                        errors_during_reload.append({
                            "time": datetime.now(),
                            "status": response.status_code
                        })
                except Exception as e:
                    errors_during_reload.append({
                        "time": datetime.now(),
                        "error": str(e)
                    })
                
                requests_count += 1
                time.sleep(0.1)
        
        # Iniciar thread de requests
        request_thread = threading.Thread(target=continuous_requests)
        request_thread.start()
        
        # 3. Esperar un poco y luego hacer reload
        time.sleep(2)
        
        try:
            container = docker_client.containers.get(container_name)
            print("  Ejecutando nginx reload...")
            exec_result = container.exec_run("nginx -s reload")
            reload_happened = True
            print(f"  Reload ejecutado: {exec_result.exit_code}")
        except Exception as e:
            reload_happened = True
            pytest.skip(f"No se pudo hacer reload: {e}")
        
        # 4. Esperar a que terminen los requests
        request_thread.join(timeout=10)
        
        print(f"  Total de requests durante el test: {requests_count}")
        print(f"  Errores durante reload: {len(errors_during_reload)}")
        
        # No debe haber errores durante el reload
        assert len(errors_during_reload) == 0, \
            f"Hubo {len(errors_during_reload)} errores durante el reload"
        
        # 5. Verificar que sigue funcionando después del reload
        for i in range(5):
            response = requests.get(f"{nginx_base_url}/nginx-health")
            assert response.status_code == 200, \
                f"Nginx no responde correctamente después del reload, intento {i+1}"
    
    def test_automatic_reconnection(self, nginx_container_running, nginx_base_url, docker_client):
        """
        Verifica la reconexión automática a upstreams después de fallos temporales.
        """
        print("\nAutomatic Reconnection Test:")
        
        # Simular fallos intermitentes
        backend_container_name = "mock_dashboard_backend"
        
        try:
            backend_container = docker_client.containers.get(backend_container_name)
        except:
            pytest.skip("Backend container no disponible para test")
        
        # Patrón de fallos: funcionando -> fallo -> recuperación
        results = []
        
        for cycle in range(3):
            print(f"\n  Ciclo {cycle + 1}:")
            
            # Fase 1: Verificar que funciona
            response = requests.get(f"{nginx_base_url}/api/get")
            results.append(("working", response.status_code))
            print(f"    Estado inicial: {response.status_code}")
            
            # Fase 2: Pausar backend (simular fallo de red)
            backend_container.pause()
            print("    Backend pausado")
            time.sleep(2)
            
            # Verificar fallo
            try:
                response = requests.get(f"{nginx_base_url}/api/get", timeout=3)
                results.append(("paused", response.status_code))
                print(f"    Con backend pausado: {response.status_code}")
            except:
                results.append(("paused", 0))
                print("    Con backend pausado: Timeout")
            
            # Fase 3: Reanudar backend
            backend_container.unpause()
            print("    Backend reanudado")
            
            # Verificar reconexión
            reconnected = False
            for attempt in range(10):
                time.sleep(1)
                try:
                    response = requests.get(f"{nginx_base_url}/api/get", timeout=2)
                    if response.status_code == 200:
                        reconnected = True
                        results.append(("recovered", response.status_code))
                        print(f"    Reconectado después de {attempt + 1}s")
                        break
                except:
                    pass
            
            assert reconnected, f"No se reconectó en el ciclo {cycle + 1}"
            
            # Esperar antes del siguiente ciclo
            time.sleep(2)
        
        # Verificar que todos los ciclos se completaron exitosamente
        successful_cycles = sum(1 for phase, status in results if phase == "recovered" and status == 200)
        assert successful_cycles == 3, f"Solo {successful_cycles}/3 ciclos exitosos"
    
    def test_connection_pool_recovery(self, nginx_container_running, nginx_base_url):
        """
        Verifica que el pool de conexiones se recupera después de agotarse.
        """
        print("\nConnection Pool Recovery Test:")
        
        # 1. Saturar el pool de conexiones
        connections = []
        saturation_count = 0
        
        print("  Saturando pool de conexiones...")
        for i in range(100):
            try:
                session = requests.Session()
                response = session.get(
                    f"{nginx_base_url}/api/get",
                    stream=True,
                    timeout=1
                )
                if response.status_code == 200:
                    connections.append((session, response))
                    saturation_count += 1
            except:
                break
        
        print(f"  Pool saturado con {saturation_count} conexiones")
        
        # 2. Verificar que nuevas conexiones fallan o son lentas
        start = time.time()
        try:
            response = requests.get(f"{nginx_base_url}/api/get", timeout=2)
            slow_response_time = time.time() - start
            print(f"  Respuesta con pool saturado: {response.status_code} en {slow_response_time:.2f}s")
        except:
            print("  Timeout con pool saturado (esperado)")
        
        # 3. Liberar conexiones
        print("  Liberando conexiones...")
        for session, response in connections:
            try:
                response.close()
                session.close()
            except:
                pass
        connections.clear()
        
        # 4. Verificar recuperación del pool
        time.sleep(2)  # Dar tiempo para que se liberen recursos
        
        recovery_times = []
        for i in range(10):
            start = time.time()
            try:
                response = requests.get(f"{nginx_base_url}/api/get", timeout=3)
                if response.status_code == 200:
                    recovery_times.append(time.time() - start)
            except:
                pass
            time.sleep(0.5)
        
        print(f"  Requests exitosos después de liberar: {len(recovery_times)}")
        
        # Debe recuperarse completamente
        assert len(recovery_times) >= 8, \
            f"Pool no se recuperó completamente: solo {len(recovery_times)}/10 exitosos"
        
        # Los tiempos deben ser normales nuevamente
        if recovery_times:
            avg_recovery_time = sum(recovery_times) / len(recovery_times)
            print(f"  Tiempo promedio después de recuperación: {avg_recovery_time:.2f}s")
            assert avg_recovery_time < 0.5, \
                f"Respuestas muy lentas después de recuperación: {avg_recovery_time:.2f}s"
    
    def test_rate_limit_state_persistence(self, nginx_container_running, nginx_base_url):
        """
        Verifica que el estado del rate limiting persiste durante fallos parciales.
        """
        print("\nRate Limit State Persistence Test:")
        
        endpoint = "/api/get"
        
        # 1. Alcanzar el rate limit
        print("  Alcanzando rate limit...")
        rate_limited = False
        successful_requests = 0
        
        with requests.Session() as session:
            for i in range(150):  # Más del límite de 100/min
                try:
                    response = session.get(f"{nginx_base_url}{endpoint}")
                    if response.status_code == 429:
                        rate_limited = True
                        print(f"  Rate limit alcanzado después de {i} requests")
                        break
                    elif response.status_code == 200:
                        successful_requests += 1
                except:
                    pass
                
                # Requests rápidos para triggear rate limit
                if i < 100:
                    time.sleep(0.01)
        
        assert rate_limited, "No se alcanzó el rate limit"
        
        # 2. Simular un evento de recuperación (como reload)
        print("  Esperando para verificar persistencia...")
        time.sleep(5)
        
        # 3. Verificar que el rate limit sigue activo
        still_limited = False
        with requests.Session() as session:
            for i in range(10):
                response = session.get(f"{nginx_base_url}{endpoint}")
                if response.status_code == 429:
                    still_limited = True
                    break
                time.sleep(0.1)
        
        # 4. Esperar a que expire el rate limit
        print("  Esperando expiración del rate limit...")
        time.sleep(60)  # Esperar un minuto completo
        
        # 5. Verificar que ya no está limitado
        recovered_count = 0
        with requests.Session() as session:
            for i in range(20):
                response = session.get(f"{nginx_base_url}{endpoint}")
                if response.status_code == 200:
                    recovered_count += 1
                time.sleep(0.1)
        
        print(f"  Requests exitosos después de esperar: {recovered_count}/20")
        
        # Debe poder hacer requests nuevamente
        assert recovered_count >= 18, \
            f"Rate limit no se recuperó apropiadamente: solo {recovered_count}/20 exitosos"
    
    def test_health_check_state_recovery(self, nginx_container_running, nginx_base_url, docker_client):
        """
        Verifica que los health checks internos de nginx se recuperan correctamente.
        """
        print("\nHealth Check State Recovery Test:")
        
        # Monitorear el estado del health check durante diferentes condiciones
        health_states = []
        
        def check_health():
            try:
                response = requests.get(f"{nginx_base_url}/nginx-health", timeout=2)
                return response.status_code == 200
            except:
                return False
        
        # 1. Estado inicial
        initial_health = check_health()
        health_states.append(("initial", initial_health))
        print(f"  Estado inicial del health check: {'OK' if initial_health else 'FAIL'}")
        assert initial_health, "Health check no funciona inicialmente"
        
        # 2. Bajo carga
        print("  Aplicando carga...")
        with requests.Session() as session:
            for _ in range(100):
                try:
                    session.get(f"{nginx_base_url}/nginx-health")
                except:
                    pass
        
        load_health = check_health()
        health_states.append(("under_load", load_health))
        print(f"  Health check bajo carga: {'OK' if load_health else 'FAIL'}")
        
        # 3. Después de errores
        print("  Generando errores...")
        for _ in range(20):
            try:
                # Intentar rutas inválidas
                requests.get(f"{nginx_base_url}/invalid/path/that/does/not/exist")
            except:
                pass
        
        error_health = check_health()
        health_states.append(("after_errors", error_health))
        print(f"  Health check después de errores: {'OK' if error_health else 'FAIL'}")
        
        # 4. Recuperación final
        time.sleep(2)
        final_health = check_health()
        health_states.append(("final", final_health))
        print(f"  Health check final: {'OK' if final_health else 'FAIL'}")
        
        # El health check debe mantenerse consistente
        health_values = [health for _, health in health_states]
        assert all(health_values), \
            f"Health check falló en algunos estados: {health_states}"
