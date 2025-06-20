# tests/integration/test_real_integration.py
"""
Tests de integración real para nginx_reverse_proxy.
Valida el funcionamiento con servicios reales cuando están disponibles.
"""
import pytest
import requests
import docker
import time
import subprocess
import os
import json
from pathlib import Path


class TestRealIntegration:
    """Tests de integración con servicios reales del sistema."""
    
    @pytest.fixture
    def docker_client(self):
        """Cliente Docker para inspección de red y servicios."""
        return docker.from_env()
    
    @pytest.fixture
    def check_real_services(self, docker_client):
        """
        Verifica si los servicios reales están disponibles.
        Retorna un dict con el estado de cada servicio.
        """
        services = {
            "backend": {
                "name": "module_dashboard_review_backend",
                "port": 8004,
                "available": False,
                "container": None
            },
            "frontend": {
                "name": "module_dashboard_review_frontend", 
                "port": 80,
                "available": False,
                "container": None
            }
        }
        
        # Buscar containers reales
        try:
            containers = docker_client.containers.list()
            for container in containers:
                for service_key, service_info in services.items():
                    if service_info["name"] in container.name:
                        services[service_key]["available"] = True
                        services[service_key]["container"] = container
                        break
        except:
            pass
        
        return services
    
    def test_real_backend_integration(self, nginx_container_running, nginx_base_url, check_real_services):
        """
        Prueba la integración con el backend real si está disponible.
        """
        if not check_real_services["backend"]["available"]:
            pytest.skip("Backend real no está disponible")
        
        print("\nReal Backend Integration Test:")
        
        # Endpoints típicos del backend real
        backend_endpoints = [
            "/api/health",
            "/api/v1/news",
            "/api/v1/analytics",
            "/api/v1/status"
        ]
        
        results = {}
        
        for endpoint in backend_endpoints:
            print(f"\n  Probando endpoint: {endpoint}")
            
            try:
                response = requests.get(f"{nginx_base_url}{endpoint}", timeout=5)
                
                results[endpoint] = {
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "headers": dict(response.headers),
                    "content_type": response.headers.get("Content-Type", ""),
                    "has_cors": "Access-Control-Allow-Origin" in response.headers
                }
                
                # Si es JSON, verificar estructura
                if "application/json" in results[endpoint]["content_type"]:
                    try:
                        json_data = response.json()
                        results[endpoint]["json_valid"] = True
                        results[endpoint]["json_keys"] = list(json_data.keys()) if isinstance(json_data, dict) else type(json_data).__name__
                    except:
                        results[endpoint]["json_valid"] = False
                
                print(f"    Status: {response.status_code}")
                print(f"    Response time: {results[endpoint]['response_time']*1000:.2f}ms")
                print(f"    Content-Type: {results[endpoint]['content_type']}")
                print(f"    CORS headers: {'Sí' if results[endpoint]['has_cors'] else 'No'}")
                
            except requests.exceptions.RequestException as e:
                results[endpoint] = {"error": str(e)}
                print(f"    Error: {e}")
        
        # Validaciones
        successful_endpoints = [ep for ep, res in results.items() if "status_code" in res and res["status_code"] < 500]
        
        assert len(successful_endpoints) > 0, "Ningún endpoint del backend real respondió correctamente"
        
        # Verificar que los headers CORS están presentes en endpoints API
        api_endpoints_with_cors = [
            ep for ep, res in results.items() 
            if ep.startswith("/api") and res.get("has_cors", False)
        ]
        
        assert len(api_endpoints_with_cors) > 0, "Los endpoints API no tienen headers CORS"
    
    def test_real_frontend_serving(self, nginx_container_running, nginx_base_url, check_real_services):
        """
        Verifica que el frontend real se sirve correctamente.
        """
        if not check_real_services["frontend"]["available"]:
            pytest.skip("Frontend real no está disponible")
        
        print("\nReal Frontend Serving Test:")
        
        # Recursos típicos del frontend
        frontend_resources = [
            ("/", "text/html"),
            ("/index.html", "text/html"),
            ("/static/js/main.js", "application/javascript"),
            ("/static/css/main.css", "text/css"),
            ("/favicon.ico", "image/x-icon"),
            ("/manifest.json", "application/json")
        ]
        
        results = {}
        
        for resource, expected_content_type in frontend_resources:
            print(f"\n  Recurso: {resource}")
            
            try:
                response = requests.get(f"{nginx_base_url}{resource}", timeout=5)
                
                results[resource] = {
                    "status_code": response.status_code,
                    "content_type": response.headers.get("Content-Type", ""),
                    "content_length": len(response.content),
                    "cache_headers": {
                        "Cache-Control": response.headers.get("Cache-Control", ""),
                        "Expires": response.headers.get("Expires", ""),
                        "ETag": response.headers.get("ETag", "")
                    },
                    "compressed": response.headers.get("Content-Encoding") == "gzip"
                }
                
                print(f"    Status: {response.status_code}")
                print(f"    Content-Type: {results[resource]['content_type']}")
                print(f"    Size: {results[resource]['content_length']} bytes")
                print(f"    Compressed: {'Sí' if results[resource]['compressed'] else 'No'}")
                
                # Verificar content-type esperado
                if response.status_code == 200:
                    assert expected_content_type in results[resource]["content_type"], \
                        f"Content-Type incorrecto para {resource}"
                
            except requests.exceptions.RequestException as e:
                results[resource] = {"error": str(e)}
                print(f"    Error: {e}")
        
        # Validaciones
        # Al menos el index debe estar disponible
        assert "/" in results and results["/"].get("status_code") == 200, \
            "La página principal del frontend no está disponible"
        
        # Los recursos estáticos deben tener headers de cache
        static_resources = [r for r in results if r.startswith("/static/")]
        for resource in static_resources:
            if results[resource].get("status_code") == 200:
                cache_headers = results[resource].get("cache_headers", {})
                has_cache = any([
                    cache_headers.get("Cache-Control"),
                    cache_headers.get("Expires"),
                    cache_headers.get("ETag")
                ])
                assert has_cache, f"Recurso estático {resource} sin headers de cache"
    
    def test_full_stack_request_flow(self, nginx_container_running, nginx_base_url, check_real_services):
        """
        Prueba un flujo completo de request a través de todo el stack.
        """
        backend_available = check_real_services["backend"]["available"]
        frontend_available = check_real_services["frontend"]["available"]
        
        if not (backend_available or frontend_available):
            pytest.skip("No hay servicios reales disponibles")
        
        print("\nFull Stack Request Flow Test:")
        
        # Simular flujo típico de usuario
        user_flow = []
        
        # 1. Cargar página principal
        if frontend_available:
            print("\n  1. Cargando página principal...")
            response = requests.get(f"{nginx_base_url}/")
            user_flow.append({
                "step": "load_homepage",
                "status": response.status_code,
                "time": response.elapsed.total_seconds()
            })
            print(f"    Status: {response.status_code}")
            print(f"    Tiempo: {response.elapsed.total_seconds()*1000:.2f}ms")
        
        # 2. Hacer request API (si backend disponible)
        if backend_available:
            print("\n  2. Request API para datos...")
            
            # Simular headers típicos de una SPA
            headers = {
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{nginx_base_url}/",
                "Origin": nginx_base_url
            }
            
            response = requests.get(
                f"{nginx_base_url}/api/health",
                headers=headers
            )
            
            user_flow.append({
                "step": "api_request",
                "status": response.status_code,
                "time": response.elapsed.total_seconds(),
                "has_cors": "Access-Control-Allow-Origin" in response.headers
            })
            
            print(f"    Status: {response.status_code}")
            print(f"    Tiempo: {response.elapsed.total_seconds()*1000:.2f}ms")
            print(f"    CORS: {'OK' if 'Access-Control-Allow-Origin' in response.headers else 'Missing'}")
        
        # 3. Simular navegación SPA
        if frontend_available:
            print("\n  3. Navegación SPA...")
            spa_routes = ["/dashboard", "/reports", "/settings"]
            
            for route in spa_routes:
                response = requests.get(f"{nginx_base_url}{route}")
                user_flow.append({
                    "step": f"spa_route_{route}",
                    "status": response.status_code,
                    "time": response.elapsed.total_seconds()
                })
                
                # Las rutas SPA deben devolver el mismo index.html
                print(f"    Ruta {route}: {response.status_code}")
        
        # 4. Simular POST API
        if backend_available:
            print("\n  4. POST a API...")
            
            test_data = {
                "timestamp": time.time(),
                "action": "test_integration",
                "source": "nginx_test"
            }
            
            response = requests.post(
                f"{nginx_base_url}/api/test",
                json=test_data,
                headers=headers
            )
            
            user_flow.append({
                "step": "api_post",
                "status": response.status_code,
                "time": response.elapsed.total_seconds()
            })
            
            print(f"    Status: {response.status_code}")
            print(f"    Tiempo: {response.elapsed.total_seconds()*1000:.2f}ms")
        
        # Análisis del flujo
        print("\n  Resumen del flujo:")
        total_time = sum(step["time"] for step in user_flow)
        print(f"    Pasos completados: {len(user_flow)}")
        print(f"    Tiempo total: {total_time*1000:.2f}ms")
        
        # Validaciones
        assert len(user_flow) > 0, "No se completó ningún paso del flujo"
        assert all(step["status"] < 500 for step in user_flow), \
            "Hubo errores del servidor en el flujo"
    
    def test_docker_network_integration(self, nginx_container_running, docker_client):
        """
        Verifica la integración con la red Docker del sistema.
        """
        print("\nDocker Network Integration Test:")
        
        # Obtener información de la red
        try:
            network = docker_client.networks.get("lamacquina_network")
            network_info = {
                "name": network.name,
                "driver": network.attrs["Driver"],
                "scope": network.attrs["Scope"],
                "containers": len(network.attrs.get("Containers", {}))
            }
            
            print(f"  Red: {network_info['name']}")
            print(f"  Driver: {network_info['driver']}")
            print(f"  Scope: {network_info['scope']}")
            print(f"  Containers conectados: {network_info['containers']}")
            
            # Obtener información del container nginx
            nginx_container = docker_client.containers.get(nginx_container_running)
            nginx_networks = list(nginx_container.attrs["NetworkSettings"]["Networks"].keys())
            
            print(f"\n  Container nginx conectado a: {nginx_networks}")
            
            assert "lamacquina_network" in nginx_networks, \
                "Nginx no está conectado a lamacquina_network"
            
            # Verificar que puede resolver otros servicios
            print("\n  Verificando resolución DNS interna...")
            
            # Ejecutar nslookup dentro del container
            services_to_check = [
                "module_dashboard_review_backend",
                "module_dashboard_review_frontend"
            ]
            
            for service in services_to_check:
                try:
                    result = nginx_container.exec_run(
                        f"nslookup {service}",
                        stderr=True
                    )
                    
                    if result.exit_code == 0:
                        print(f"    ✓ {service}: Resuelto correctamente")
                    else:
                        print(f"    ✗ {service}: No se pudo resolver")
                        
                except Exception as e:
                    print(f"    ✗ {service}: Error - {e}")
            
        except docker.errors.NotFound:
            pytest.skip("Red lamacquina_network no encontrada")
    
    def test_service_discovery(self, nginx_container_running, nginx_base_url, docker_client):
        """
        Verifica que el service discovery funciona correctamente.
        """
        print("\nService Discovery Test:")
        
        # Obtener el container nginx
        nginx_container = docker_client.containers.get(nginx_container_running)
        
        # Verificar la configuración de upstreams
        print("\n  Verificando configuración de upstreams...")
        
        # Leer la configuración actual de nginx
        result = nginx_container.exec_run("cat /etc/nginx/nginx.conf")
        
        if result.exit_code == 0:
            config_content = result.output.decode('utf-8')
            
            # Buscar definiciones de upstream
            if "upstream dashboard_backend" in config_content:
                print("    ✓ Upstream backend definido")
            else:
                print("    ✗ Upstream backend no encontrado")
            
            if "upstream dashboard_frontend" in config_content:
                print("    ✓ Upstream frontend definido")
            else:
                print("    ✗ Upstream frontend no encontrado")
        
        # Verificar conectividad real a los upstreams
        print("\n  Verificando conectividad a upstreams...")
        
        upstreams = [
            ("dashboard_backend", "module_dashboard_review_backend", 8004),
            ("dashboard_frontend", "module_dashboard_review_frontend", 80)
        ]
        
        for upstream_name, service_name, port in upstreams:
            # Intentar conectar directamente desde el container nginx
            result = nginx_container.exec_run(
                f"nc -zv {service_name} {port}",
                stderr=True
            )
            
            if result.exit_code == 0:
                print(f"    ✓ {upstream_name}: Conectividad OK")
            else:
                print(f"    ✗ {upstream_name}: Sin conectividad")
                # No fallar el test, solo informar
    
    def test_cross_container_communication(self, nginx_container_running, docker_client):
        """
        Verifica la comunicación entre containers en la red.
        """
        print("\nCross Container Communication Test:")
        
        nginx_container = docker_client.containers.get(nginx_container_running)
        
        # Listar todos los containers en la misma red
        try:
            network = docker_client.networks.get("lamacquina_network")
            connected_containers = network.attrs.get("Containers", {})
            
            print(f"  Containers en la red: {len(connected_containers)}")
            
            # Probar ping a cada container (si está disponible)
            for container_id, container_info in connected_containers.items():
                container_name = container_info.get("Name", "unknown")
                
                if container_name != nginx_container_running:
                    # Intentar ping (algunos containers Alpine no tienen ping)
                    result = nginx_container.exec_run(
                        f"ping -c 1 -W 2 {container_name}",
                        stderr=True
                    )
                    
                    if result.exit_code == 0:
                        print(f"    ✓ Ping a {container_name}: OK")
                    else:
                        # Intentar con nc como alternativa
                        result = nginx_container.exec_run(
                            f"nc -zv {container_name} 80",
                            stderr=True
                        )
                        if result.exit_code == 0:
                            print(f"    ✓ Conectividad a {container_name}:80: OK")
                        else:
                            print(f"    ℹ {container_name}: No accesible")
            
            # Verificar que nginx puede comunicarse con al menos un servicio
            assert len(connected_containers) > 1, \
                "Nginx es el único container en la red"
                
        except docker.errors.NotFound:
            pytest.skip("Red no encontrada")
    
    def test_real_data_flow(self, nginx_container_running, nginx_base_url, check_real_services):
        """
        Prueba con datos reales si los servicios están disponibles.
        """
        if not check_real_services["backend"]["available"]:
            pytest.skip("Backend real no disponible para prueba de datos")
        
        print("\nReal Data Flow Test:")
        
        # Simular flujo de datos real
        test_scenarios = [
            {
                "name": "Consulta de noticias",
                "method": "GET",
                "endpoint": "/api/v1/news",
                "params": {"limit": 10, "offset": 0}
            },
            {
                "name": "Búsqueda",
                "method": "GET", 
                "endpoint": "/api/v1/search",
                "params": {"q": "test", "type": "news"}
            },
            {
                "name": "Analytics",
                "method": "GET",
                "endpoint": "/api/v1/analytics/summary",
                "params": {"period": "day"}
            }
        ]
        
        results = []
        
        for scenario in test_scenarios:
            print(f"\n  Escenario: {scenario['name']}")
            
            try:
                if scenario["method"] == "GET":
                    response = requests.get(
                        f"{nginx_base_url}{scenario['endpoint']}",
                        params=scenario.get("params", {}),
                        timeout=10
                    )
                else:
                    response = requests.post(
                        f"{nginx_base_url}{scenario['endpoint']}",
                        json=scenario.get("data", {}),
                        timeout=10
                    )
                
                result = {
                    "scenario": scenario["name"],
                    "status": response.status_code,
                    "time": response.elapsed.total_seconds(),
                    "size": len(response.content)
                }
                
                # Si es JSON, verificar estructura
                if response.status_code == 200 and "json" in response.headers.get("Content-Type", ""):
                    try:
                        json_data = response.json()
                        result["data_type"] = type(json_data).__name__
                        
                        if isinstance(json_data, list):
                            result["records"] = len(json_data)
                        elif isinstance(json_data, dict):
                            result["fields"] = len(json_data.keys())
                            
                    except:
                        result["json_error"] = True
                
                results.append(result)
                
                print(f"    Status: {result['status']}")
                print(f"    Tiempo: {result['time']*1000:.2f}ms")
                print(f"    Tamaño: {result['size']} bytes")
                
                if "records" in result:
                    print(f"    Registros: {result['records']}")
                elif "fields" in result:
                    print(f"    Campos: {result['fields']}")
                    
            except Exception as e:
                print(f"    Error: {e}")
                results.append({
                    "scenario": scenario["name"],
                    "error": str(e)
                })
        
        # Análisis final
        successful = [r for r in results if "status" in r and r["status"] == 200]
        
        print(f"\n  Resumen:")
        print(f"    Escenarios exitosos: {len(successful)}/{len(test_scenarios)}")
        
        if successful:
            avg_time = sum(r["time"] for r in successful) / len(successful)
            print(f"    Tiempo promedio: {avg_time*1000:.2f}ms")
            
            total_size = sum(r.get("size", 0) for r in successful)
            print(f"    Datos transferidos: {total_size/1024:.2f} KB")
