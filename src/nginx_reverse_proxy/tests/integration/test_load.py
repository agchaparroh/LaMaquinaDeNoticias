# tests/integration/test_load.py
"""
Tests de carga para nginx_reverse_proxy.
Determina capacidad máxima, punto de quiebre y comportamiento bajo estrés.
"""
import pytest
import requests
import time
import statistics
import concurrent.futures
from datetime import datetime
import json
import os


class TestLoad:
    """Tests de carga y estrés para nginx."""
    
    def test_ramp_up_load(self, nginx_container_running, nginx_base_url):
        """
        Prueba con carga incremental hasta encontrar el límite del sistema.
        """
        print("\nRamp Up Load Test:")
        
        # Configuración del test
        initial_users = 10
        increment = 10
        max_users = 200
        duration_per_level = 10  # segundos
        target_endpoint = "/api/get"
        
        results = []
        breaking_point = None
        
        current_users = initial_users
        
        while current_users <= max_users:
            print(f"\n  Nivel de carga: {current_users} usuarios concurrentes")
            
            # Métricas para este nivel
            level_metrics = {
                "users": current_users,
                "requests": 0,
                "errors": 0,
                "response_times": [],
                "start_time": time.time()
            }
            
            # Flag para controlar la duración
            stop_time = time.time() + duration_per_level
            
            def user_simulation(user_id):
                local_metrics = {
                    "requests": 0,
                    "errors": 0,
                    "response_times": []
                }
                
                session = requests.Session()
                
                while time.time() < stop_time:
                    try:
                        start = time.perf_counter()
                        response = session.get(f"{nginx_base_url}{target_endpoint}", timeout=5)
                        end = time.perf_counter()
                        
                        local_metrics["requests"] += 1
                        
                        if response.status_code == 200:
                            local_metrics["response_times"].append(end - start)
                        else:
                            local_metrics["errors"] += 1
                            
                    except Exception:
                        local_metrics["errors"] += 1
                    
                    # Pausa variable para simular usuario real
                    time.sleep(0.1 + (user_id % 10) * 0.01)
                
                return local_metrics
            
            # Ejecutar usuarios concurrentes
            with concurrent.futures.ThreadPoolExecutor(max_workers=current_users) as executor:
                futures = [
                    executor.submit(user_simulation, i)
                    for i in range(current_users)
                ]
                
                # Recolectar métricas
                for future in concurrent.futures.as_completed(futures):
                    user_metrics = future.result()
                    level_metrics["requests"] += user_metrics["requests"]
                    level_metrics["errors"] += user_metrics["errors"]
                    level_metrics["response_times"].extend(user_metrics["response_times"])
            
            # Calcular estadísticas para este nivel
            level_metrics["duration"] = time.time() - level_metrics["start_time"]
            level_metrics["rps"] = level_metrics["requests"] / level_metrics["duration"]
            level_metrics["error_rate"] = level_metrics["errors"] / level_metrics["requests"] if level_metrics["requests"] > 0 else 0
            
            if level_metrics["response_times"]:
                level_metrics["avg_response_time"] = statistics.mean(level_metrics["response_times"])
                level_metrics["p95_response_time"] = sorted(level_metrics["response_times"])[int(len(level_metrics["response_times"]) * 0.95)]
            else:
                level_metrics["avg_response_time"] = 0
                level_metrics["p95_response_time"] = 0
            
            results.append(level_metrics)
            
            # Mostrar métricas
            print(f"    RPS: {level_metrics['rps']:.2f}")
            print(f"    Error rate: {level_metrics['error_rate']*100:.2f}%")
            print(f"    Avg response time: {level_metrics['avg_response_time']*1000:.2f}ms")
            print(f"    P95 response time: {level_metrics['p95_response_time']*1000:.2f}ms")
            
            # Determinar si hemos alcanzado el punto de quiebre
            if level_metrics["error_rate"] > 0.05 or level_metrics["p95_response_time"] > 2.0:
                breaking_point = current_users
                print(f"\n  ⚠️ Punto de quiebre detectado en {breaking_point} usuarios")
                break
            
            # Incrementar usuarios
            current_users += increment
            
            # Pausa entre niveles
            time.sleep(5)
        
        # Resumen del test
        print("\n  Resumen del test Ramp Up:")
        print(f"    Niveles probados: {len(results)}")
        print(f"    Punto de quiebre: {breaking_point or 'No alcanzado'}")
        
        # Encontrar el nivel óptimo (mejor RPS con error rate < 1%)
        optimal_level = max(
            (r for r in results if r["error_rate"] < 0.01),
            key=lambda x: x["rps"],
            default=None
        )
        
        if optimal_level:
            print(f"    Nivel óptimo: {optimal_level['users']} usuarios")
            print(f"    RPS óptimo: {optimal_level['rps']:.2f}")
        
        # Validaciones
        assert len(results) > 0, "No se completó ningún nivel de carga"
        assert results[0]["error_rate"] < 0.02, "Errores incluso con carga baja"
    
    def test_sustained_load(self, nginx_container_running, nginx_base_url):
        """
        Prueba carga sostenida durante un período prolongado.
        """
        print("\nSustained Load Test:")
        
        # Configuración
        num_users = 50
        test_duration = 60  # 1 minuto
        endpoint = "/api/get"
        
        metrics = {
            "total_requests": 0,
            "total_errors": 0,
            "response_times": [],
            "errors_by_second": {},
            "rps_by_second": {}
        }
        
        start_time = time.time()
        stop_time = start_time + test_duration
        
        def sustained_user_load(user_id):
            local_requests = 0
            local_errors = 0
            local_times = []
            
            session = requests.Session()
            
            while time.time() < stop_time:
                second_key = int(time.time() - start_time)
                
                try:
                    req_start = time.perf_counter()
                    response = session.get(f"{nginx_base_url}{endpoint}", timeout=3)
                    req_end = time.perf_counter()
                    
                    local_requests += 1
                    
                    if response.status_code == 200:
                        local_times.append(req_end - req_start)
                    else:
                        local_errors += 1
                        
                except Exception:
                    local_errors += 1
                
                # Pausa para mantener carga estable
                time.sleep(0.2)
            
            return local_requests, local_errors, local_times
        
        # Ejecutar carga sostenida
        print(f"  Ejecutando {num_users} usuarios durante {test_duration}s...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [
                executor.submit(sustained_user_load, i)
                for i in range(num_users)
            ]
            
            # Monitorear mientras se ejecuta
            monitoring_start = time.time()
            while time.time() < stop_time:
                elapsed = int(time.time() - monitoring_start)
                if elapsed % 10 == 0 and elapsed > 0:
                    print(f"    Progreso: {elapsed}s / {test_duration}s")
                time.sleep(1)
            
            # Recolectar resultados
            for future in concurrent.futures.as_completed(futures):
                reqs, errs, times = future.result()
                metrics["total_requests"] += reqs
                metrics["total_errors"] += errs
                metrics["response_times"].extend(times)
        
        # Calcular estadísticas
        actual_duration = time.time() - start_time
        overall_rps = metrics["total_requests"] / actual_duration
        error_rate = metrics["total_errors"] / metrics["total_requests"] if metrics["total_requests"] > 0 else 0
        
        if metrics["response_times"]:
            avg_response = statistics.mean(metrics["response_times"])
            median_response = statistics.median(metrics["response_times"])
            p99_response = sorted(metrics["response_times"])[int(len(metrics["response_times"]) * 0.99)]
            
            # Analizar estabilidad (desviación estándar)
            stdev_response = statistics.stdev(metrics["response_times"]) if len(metrics["response_times"]) > 1 else 0
        else:
            avg_response = median_response = p99_response = stdev_response = 0
        
        print(f"\n  Resultados de carga sostenida:")
        print(f"    Duración real: {actual_duration:.2f}s")
        print(f"    Total requests: {metrics['total_requests']}")
        print(f"    RPS promedio: {overall_rps:.2f}")
        print(f"    Tasa de error: {error_rate*100:.2f}%")
        print(f"    Tiempo de respuesta promedio: {avg_response*1000:.2f}ms")
        print(f"    Tiempo de respuesta mediano: {median_response*1000:.2f}ms")
        print(f"    Tiempo de respuesta P99: {p99_response*1000:.2f}ms")
        print(f"    Desviación estándar: {stdev_response*1000:.2f}ms")
        
        # Validaciones
        assert error_rate < 0.02, f"Tasa de error muy alta bajo carga sostenida: {error_rate*100:.2f}%"
        assert avg_response < 1.0, f"Tiempo de respuesta muy alto: {avg_response:.2f}s"
        assert stdev_response < avg_response, "Respuestas muy inestables (alta desviación)"
    
    def test_spike_load(self, nginx_container_running, nginx_base_url):
        """
        Prueba picos súbitos de tráfico.
        """
        print("\nSpike Load Test:")
        
        # Configuración
        baseline_users = 20
        spike_users = 100
        baseline_duration = 10
        spike_duration = 5
        recovery_duration = 10
        
        phases = [
            ("baseline", baseline_users, baseline_duration),
            ("spike", spike_users, spike_duration),
            ("recovery", baseline_users, recovery_duration)
        ]
        
        results = {}
        
        for phase_name, num_users, duration in phases:
            print(f"\n  Fase: {phase_name} ({num_users} usuarios por {duration}s)")
            
            phase_metrics = {
                "requests": 0,
                "errors": 0,
                "response_times": [],
                "start_time": time.time()
            }
            
            stop_time = time.time() + duration
            
            def spike_user_load(user_id):
                local_metrics = {"requests": 0, "errors": 0, "times": []}
                session = requests.Session()
                
                while time.time() < stop_time:
                    try:
                        start = time.perf_counter()
                        response = session.get(f"{nginx_base_url}/api/get", timeout=5)
                        end = time.perf_counter()
                        
                        local_metrics["requests"] += 1
                        if response.status_code == 200:
                            local_metrics["times"].append(end - start)
                        else:
                            local_metrics["errors"] += 1
                    except:
                        local_metrics["errors"] += 1
                    
                    time.sleep(0.1)
                
                return local_metrics
            
            # Ejecutar fase
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
                futures = [executor.submit(spike_user_load, i) for i in range(num_users)]
                
                for future in concurrent.futures.as_completed(futures):
                    user_metrics = future.result()
                    phase_metrics["requests"] += user_metrics["requests"]
                    phase_metrics["errors"] += user_metrics["errors"]
                    phase_metrics["response_times"].extend(user_metrics["times"])
            
            # Calcular métricas
            phase_metrics["duration"] = time.time() - phase_metrics["start_time"]
            phase_metrics["rps"] = phase_metrics["requests"] / phase_metrics["duration"]
            phase_metrics["error_rate"] = phase_metrics["errors"] / phase_metrics["requests"] if phase_metrics["requests"] > 0 else 0
            
            if phase_metrics["response_times"]:
                phase_metrics["avg_response"] = statistics.mean(phase_metrics["response_times"])
                phase_metrics["p95_response"] = sorted(phase_metrics["response_times"])[int(len(phase_metrics["response_times"]) * 0.95)]
            else:
                phase_metrics["avg_response"] = 0
                phase_metrics["p95_response"] = 0
            
            results[phase_name] = phase_metrics
            
            print(f"    RPS: {phase_metrics['rps']:.2f}")
            print(f"    Error rate: {phase_metrics['error_rate']*100:.2f}%")
            print(f"    Avg response: {phase_metrics['avg_response']*1000:.2f}ms")
            print(f"    P95 response: {phase_metrics['p95_response']*1000:.2f}ms")
        
        # Análisis de recuperación
        print("\n  Análisis de impacto del spike:")
        
        baseline_avg = results["baseline"]["avg_response"]
        spike_avg = results["spike"]["avg_response"]
        recovery_avg = results["recovery"]["avg_response"]
        
        spike_degradation = (spike_avg - baseline_avg) / baseline_avg if baseline_avg > 0 else 0
        recovery_ratio = recovery_avg / baseline_avg if baseline_avg > 0 else 0
        
        print(f"    Degradación durante spike: {spike_degradation*100:.1f}%")
        print(f"    Ratio de recuperación: {recovery_ratio:.2f}x baseline")
        
        # Validaciones
        assert results["spike"]["error_rate"] < 0.1, \
            f"Demasiados errores durante spike: {results['spike']['error_rate']*100:.2f}%"
        assert recovery_ratio < 1.5, \
            f"No se recuperó completamente después del spike: {recovery_ratio:.2f}x baseline"
    
    def test_mixed_load_pattern(self, nginx_container_running, nginx_base_url):
        """
        Prueba con patrones de carga mixtos que simulan tráfico real.
        """
        print("\nMixed Load Pattern Test:")
        
        # Diferentes tipos de usuarios
        user_patterns = {
            "heavy": {
                "count": 10,
                "delay": 0.1,
                "endpoints": ["/api/get", "/api/post"],
                "ratio": 0.8  # 80% GET, 20% POST
            },
            "normal": {
                "count": 30,
                "delay": 0.5,
                "endpoints": ["/api/get", "/"],
                "ratio": 0.5  # 50% API, 50% frontend
            },
            "light": {
                "count": 20,
                "delay": 2.0,
                "endpoints": ["/", "/nginx-health"],
                "ratio": 0.9  # 90% frontend, 10% health
            }
        }
        
        test_duration = 30
        stop_time = time.time() + test_duration
        
        aggregated_metrics = {
            "total_requests": 0,
            "total_errors": 0,
            "requests_by_type": {},
            "response_times_by_type": {}
        }
        
        def mixed_user_behavior(user_type, user_id):
            pattern = user_patterns[user_type]
            local_metrics = {
                "requests": 0,
                "errors": 0,
                "requests_by_endpoint": {},
                "response_times": []
            }
            
            session = requests.Session()
            
            while time.time() < stop_time:
                # Seleccionar endpoint basado en ratio
                if len(pattern["endpoints"]) > 1:
                    endpoint = pattern["endpoints"][0] if user_id % 10 < pattern["ratio"] * 10 else pattern["endpoints"][1]
                else:
                    endpoint = pattern["endpoints"][0]
                
                try:
                    start = time.perf_counter()
                    
                    if "post" in endpoint.lower():
                        response = session.post(
                            f"{nginx_base_url}{endpoint}",
                            json={"user": user_id, "type": user_type, "timestamp": time.time()}
                        )
                    else:
                        response = session.get(f"{nginx_base_url}{endpoint}")
                    
                    end = time.perf_counter()
                    
                    local_metrics["requests"] += 1
                    local_metrics["requests_by_endpoint"][endpoint] = local_metrics["requests_by_endpoint"].get(endpoint, 0) + 1
                    
                    if response.status_code in [200, 201]:
                        local_metrics["response_times"].append(end - start)
                    else:
                        local_metrics["errors"] += 1
                        
                except Exception:
                    local_metrics["errors"] += 1
                
                time.sleep(pattern["delay"])
            
            return user_type, local_metrics
        
        # Lanzar todos los usuarios con sus patrones
        all_futures = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            for user_type, pattern in user_patterns.items():
                for i in range(pattern["count"]):
                    future = executor.submit(mixed_user_behavior, user_type, i)
                    all_futures.append(future)
            
            # Recolectar resultados
            for future in concurrent.futures.as_completed(all_futures):
                user_type, metrics = future.result()
                
                aggregated_metrics["total_requests"] += metrics["requests"]
                aggregated_metrics["total_errors"] += metrics["errors"]
                
                if user_type not in aggregated_metrics["requests_by_type"]:
                    aggregated_metrics["requests_by_type"][user_type] = 0
                    aggregated_metrics["response_times_by_type"][user_type] = []
                
                aggregated_metrics["requests_by_type"][user_type] += metrics["requests"]
                aggregated_metrics["response_times_by_type"][user_type].extend(metrics["response_times"])
        
        # Mostrar resultados
        print(f"\n  Resultados de carga mixta:")
        print(f"    Duración: {test_duration}s")
        print(f"    Total requests: {aggregated_metrics['total_requests']}")
        print(f"    Total errors: {aggregated_metrics['total_errors']}")
        print(f"    Error rate global: {(aggregated_metrics['total_errors']/aggregated_metrics['total_requests']*100):.2f}%")
        
        print("\n  Por tipo de usuario:")
        for user_type in user_patterns:
            if user_type in aggregated_metrics["requests_by_type"]:
                requests = aggregated_metrics["requests_by_type"][user_type]
                times = aggregated_metrics["response_times_by_type"][user_type]
                
                if times:
                    avg_time = statistics.mean(times)
                    p95_time = sorted(times)[int(len(times) * 0.95)]
                else:
                    avg_time = p95_time = 0
                
                print(f"    {user_type}:")
                print(f"      Requests: {requests}")
                print(f"      Avg response: {avg_time*1000:.2f}ms")
                print(f"      P95 response: {p95_time*1000:.2f}ms")
        
        # Validaciones
        error_rate = aggregated_metrics["total_errors"] / aggregated_metrics["total_requests"]
        assert error_rate < 0.02, f"Error rate muy alto en carga mixta: {error_rate*100:.2f}%"
    
    def test_graceful_degradation(self, nginx_container_running, nginx_base_url):
        """
        Verifica que nginx degrada gracefully cuando se supera su capacidad.
        """
        print("\nGraceful Degradation Test:")
        
        # Intentar sobrecargar nginx gradualmente
        stages = [
            ("normal", 50, 5),
            ("high", 150, 5),
            ("overload", 300, 5),
            ("extreme", 500, 5)
        ]
        
        degradation_metrics = []
        
        for stage_name, concurrent_users, duration in stages:
            print(f"\n  Etapa: {stage_name} ({concurrent_users} usuarios)")
            
            stage_start = time.time()
            stage_stop = stage_start + duration
            
            stage_metrics = {
                "stage": stage_name,
                "users": concurrent_users,
                "success": 0,
                "rate_limited": 0,
                "errors": 0,
                "timeouts": 0,
                "response_times": []
            }
            
            def overload_request(user_id):
                metrics = {"success": 0, "rate_limited": 0, "errors": 0, "timeouts": 0, "times": []}
                
                while time.time() < stage_stop:
                    try:
                        start = time.perf_counter()
                        response = requests.get(f"{nginx_base_url}/api/get", timeout=2)
                        end = time.perf_counter()
                        
                        if response.status_code == 200:
                            metrics["success"] += 1
                            metrics["times"].append(end - start)
                        elif response.status_code == 429:
                            metrics["rate_limited"] += 1
                        else:
                            metrics["errors"] += 1
                            
                    except requests.exceptions.Timeout:
                        metrics["timeouts"] += 1
                    except Exception:
                        metrics["errors"] += 1
                    
                    time.sleep(0.05)
                
                return metrics
            
            # Ejecutar stage
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = [executor.submit(overload_request, i) for i in range(concurrent_users)]
                
                for future in concurrent.futures.as_completed(futures):
                    user_metrics = future.result()
                    stage_metrics["success"] += user_metrics["success"]
                    stage_metrics["rate_limited"] += user_metrics["rate_limited"]
                    stage_metrics["errors"] += user_metrics["errors"]
                    stage_metrics["timeouts"] += user_metrics["timeouts"]
                    stage_metrics["response_times"].extend(user_metrics["times"])
            
            # Calcular métricas
            total_requests = sum([
                stage_metrics["success"],
                stage_metrics["rate_limited"],
                stage_metrics["errors"],
                stage_metrics["timeouts"]
            ])
            
            if stage_metrics["response_times"]:
                stage_metrics["avg_response"] = statistics.mean(stage_metrics["response_times"])
            else:
                stage_metrics["avg_response"] = 0
            
            stage_metrics["total_requests"] = total_requests
            stage_metrics["success_rate"] = stage_metrics["success"] / total_requests if total_requests > 0 else 0
            
            degradation_metrics.append(stage_metrics)
            
            print(f"    Total requests: {total_requests}")
            print(f"    Exitosos: {stage_metrics['success']} ({stage_metrics['success_rate']*100:.1f}%)")
            print(f"    Rate limited: {stage_metrics['rate_limited']}")
            print(f"    Errores: {stage_metrics['errors']}")
            print(f"    Timeouts: {stage_metrics['timeouts']}")
            if stage_metrics["avg_response"] > 0:
                print(f"    Avg response: {stage_metrics['avg_response']*1000:.2f}ms")
        
        # Análisis de degradación
        print("\n  Análisis de degradación:")
        
        # Verificar que degrada gracefully (no colapsa completamente)
        for i, metrics in enumerate(degradation_metrics):
            if i > 0:
                prev_success_rate = degradation_metrics[i-1]["success_rate"]
                curr_success_rate = metrics["success_rate"]
                
                # La tasa de éxito debe degradar gradualmente, no colapsar
                if prev_success_rate > 0.5 and curr_success_rate < 0.1:
                    print(f"    ⚠️ Colapso detectado entre {degradation_metrics[i-1]['stage']} y {metrics['stage']}")
                else:
                    print(f"    ✓ Degradación controlada en {metrics['stage']}")
        
        # Nginx debe seguir respondiendo algo incluso bajo carga extrema
        extreme_metrics = degradation_metrics[-1]
        assert extreme_metrics["success"] > 0 or extreme_metrics["rate_limited"] > 0, \
            "Nginx colapsó completamente bajo carga extrema"
    
    def test_recovery_from_overload(self, nginx_container_running, nginx_base_url):
        """
        Verifica que nginx se recupera correctamente después de una sobrecarga.
        """
        print("\nRecovery from Overload Test:")
        
        # Fases del test
        phases = [
            ("baseline", 20, 10),     # Establecer baseline
            ("overload", 200, 15),    # Sobrecargar
            ("cooldown", 0, 10),      # Sin carga
            ("recovery", 20, 10)      # Verificar recuperación
        ]
        
        phase_results = {}
        
        for phase_name, num_users, duration in phases:
            print(f"\n  Fase: {phase_name}")
            
            if num_users == 0:
                # Fase de cooldown - solo esperar
                print(f"    Esperando {duration}s...")
                time.sleep(duration)
                continue
            
            phase_metrics = {
                "requests": 0,
                "success": 0,
                "errors": 0,
                "response_times": [],
                "start_time": time.time()
            }
            
            stop_time = time.time() + duration
            
            def phase_load(user_id):
                local_metrics = {"requests": 0, "success": 0, "errors": 0, "times": []}
                session = requests.Session()
                
                while time.time() < stop_time:
                    try:
                        start = time.perf_counter()
                        response = session.get(f"{nginx_base_url}/api/get", timeout=3)
                        end = time.perf_counter()
                        
                        local_metrics["requests"] += 1
                        if response.status_code == 200:
                            local_metrics["success"] += 1
                            local_metrics["times"].append(end - start)
                        else:
                            local_metrics["errors"] += 1
                    except:
                        local_metrics["errors"] += 1
                    
                    time.sleep(0.2)
                
                return local_metrics
            
            # Ejecutar fase
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
                futures = [executor.submit(phase_load, i) for i in range(num_users)]
                
                for future in concurrent.futures.as_completed(futures):
                    metrics = future.result()
                    phase_metrics["requests"] += metrics["requests"]
                    phase_metrics["success"] += metrics["success"]
                    phase_metrics["errors"] += metrics["errors"]
                    phase_metrics["response_times"].extend(metrics["times"])
            
            # Calcular estadísticas
            phase_metrics["duration"] = time.time() - phase_metrics["start_time"]
            phase_metrics["success_rate"] = phase_metrics["success"] / phase_metrics["requests"] if phase_metrics["requests"] > 0 else 0
            
            if phase_metrics["response_times"]:
                phase_metrics["avg_response"] = statistics.mean(phase_metrics["response_times"])
                phase_metrics["p95_response"] = sorted(phase_metrics["response_times"])[int(len(phase_metrics["response_times"]) * 0.95)]
            else:
                phase_metrics["avg_response"] = 0
                phase_metrics["p95_response"] = 0
            
            phase_results[phase_name] = phase_metrics
            
            print(f"    Requests: {phase_metrics['requests']}")
            print(f"    Success rate: {phase_metrics['success_rate']*100:.1f}%")
            print(f"    Avg response: {phase_metrics['avg_response']*1000:.2f}ms")
            print(f"    P95 response: {phase_metrics['p95_response']*1000:.2f}ms")
        
        # Comparar baseline con recovery
        if "baseline" in phase_results and "recovery" in phase_results:
            baseline = phase_results["baseline"]
            recovery = phase_results["recovery"]
            
            print("\n  Comparación Baseline vs Recovery:")
            print(f"    Success rate: {baseline['success_rate']*100:.1f}% → {recovery['success_rate']*100:.1f}%")
            print(f"    Avg response: {baseline['avg_response']*1000:.2f}ms → {recovery['avg_response']*1000:.2f}ms")
            
            # La recuperación debe ser casi completa
            assert recovery["success_rate"] >= baseline["success_rate"] * 0.95, \
                "No se recuperó completamente la tasa de éxito"
            assert recovery["avg_response"] <= baseline["avg_response"] * 1.5, \
                "Los tiempos de respuesta no se recuperaron"
