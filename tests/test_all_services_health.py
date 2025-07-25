"""
Test: test_all_services_health.py
Objetivo: Verificar que todos los servicios del sistema están disponibles y responden correctamente
Módulos: Todos los servicios definidos en docker-compose.yml
Punto de integración: Health endpoints HTTP de cada servicio
"""

import os
import time
from typing import Dict, Tuple

import pytest
import requests

# Configuración de servicios y sus endpoints de health
SERVICES = {
    # Servicios Backend (FastAPI)
    "module_pipeline": {
        "url": "http://localhost:8003/health",
        "container": "lamacquina_pipeline",
        "type": "api",
    },
    "module_dashboard_review_backend": {
        "url": "http://localhost:8004/health",
        "container": "lamacquina_dashboard_review_backend",
        "type": "api",
    },
    "module_chat_interface_backend": {
        "url": "http://localhost:8005/health",
        "container": "lamacquina_chat_interface_backend",
        "type": "api",
    },
    "module_dev_interface_backend": {
        "url": "http://localhost:8006/health",
        "container": "lamacquina_dev_interface_backend",
        "type": "api",
    },
    # Servicios Frontend (Nginx)
    "module_dashboard_review_frontend": {
        "url": "http://localhost:3001/",
        "container": "lamacquina_dashboard_review_frontend",
        "type": "frontend",
    },
    "module_chat_interface_frontend": {
        "url": "http://localhost:3002/",
        "container": "lamacquina_chat_interface_frontend",
        "type": "frontend",
    },
    "module_dev_interface_frontend": {
        "url": "http://localhost:3003/",
        "container": "lamacquina_dev_interface_frontend",
        "type": "frontend",
    },
    # Reverse Proxy
    "nginx_reverse_proxy": {
        "url": "http://localhost:80/",
        "container": "lamacquina_reverse_proxy",
        "type": "proxy",
    },
}

# Servicios que no exponen HTTP pero deben estar corriendo
WORKER_SERVICES = {
    "module_scraper": "lamacquina_scraper",
    "module_connector": "lamacquina_connector",
    "module_orchestration_agent": "lamacquina_orchestration_agent",
}


def check_service_health(service_name: str, service_config: Dict) -> Tuple[bool, str]:
    """
    Verifica que un servicio responda correctamente.

    Returns:
        Tuple[bool, str]: (servicio_saludable, mensaje)
    """
    try:
        response = requests.get(service_config["url"], timeout=10)

        if service_config["type"] == "api":
            # Para APIs esperamos un endpoint /health con status 200
            if response.status_code == 200:
                return (
                    True,
                    f"✅ {service_name}: Health check OK (status {response.status_code})",
                )
            else:
                return (
                    False,
                    f"❌ {service_name}: Health check failed (status {response.status_code})",
                )

        elif service_config["type"] in ["frontend", "proxy"]:
            # Para frontends/proxy, cualquier respuesta 200-299 es válida
            if 200 <= response.status_code < 300:
                return (
                    True,
                    f"✅ {service_name}: Service responding (status {response.status_code})",
                )
            else:
                return (
                    False,
                    f"❌ {service_name}: Service not responding correctly (status {response.status_code})",
                )

    except requests.exceptions.ConnectionError:
        return False, f"❌ {service_name}: Connection refused - service may be down"
    except requests.exceptions.Timeout:
        return False, f"❌ {service_name}: Request timeout - service not responding"
    except Exception as e:
        return False, f"❌ {service_name}: Unexpected error - {str(e)}"


def check_container_running(container_name: str) -> Tuple[bool, str]:
    """
    Verifica que un contenedor Docker esté corriendo.

    Returns:
        Tuple[bool, str]: (container_corriendo, mensaje)
    """
    try:
        result = (
            os.popen(
                f"docker ps --filter name={container_name} --format '{{{{.Status}}}}'"
            )
            .read()
            .strip()
        )
        if result and "Up" in result:
            return True, f"✅ {container_name}: Container running ({result})"
        else:
            return False, f"❌ {container_name}: Container not running"
    except Exception as e:
        return False, f"❌ {container_name}: Error checking container - {str(e)}"


@pytest.fixture(scope="module")
def wait_for_services():
    """
    Fixture que espera a que los servicios estén listos antes de ejecutar tests.
    """
    print("\n⏳ Esperando a que los servicios estén listos...")
    time.sleep(5)  # Espera inicial

    # Intentar hasta 30 segundos para que los servicios respondan
    max_attempts = 6
    for attempt in range(max_attempts):
        ready_count = 0
        for service_name, config in SERVICES.items():
            is_healthy, _ = check_service_health(service_name, config)
            if is_healthy:
                ready_count += 1

        if ready_count == len(SERVICES):
            print(
                f"✅ Todos los servicios HTTP están listos ({ready_count}/{len(SERVICES)})"
            )
            break
        else:
            print(
                f"⏳ Esperando... {ready_count}/{len(SERVICES)} servicios listos (intento {attempt + 1}/{max_attempts})"
            )
            time.sleep(5)

    yield
    # No hay limpieza necesaria


def test_all_http_services_health(wait_for_services):
    """Test que verifica que todos los servicios HTTP responden correctamente"""
    print("\n🔍 Verificando health de servicios HTTP...")

    all_healthy = True
    results = []

    # GIVEN: El sistema está desplegado con docker-compose

    # WHEN: Verificamos cada servicio HTTP
    for service_name, config in SERVICES.items():
        is_healthy, message = check_service_health(service_name, config)
        results.append(message)
        if not is_healthy:
            all_healthy = False

    # THEN: Todos los servicios deben responder correctamente
    print("\n📋 Resultados de Health Checks HTTP:")
    for result in results:
        print(result)

    assert all_healthy, "Algunos servicios HTTP no están respondiendo correctamente"


def test_all_worker_services_running():
    """Test que verifica que todos los servicios worker estén corriendo"""
    print("\n🔍 Verificando servicios worker...")

    all_running = True
    results = []

    # GIVEN: El sistema está desplegado con docker-compose

    # WHEN: Verificamos cada contenedor worker
    for service_name, container_name in WORKER_SERVICES.items():
        is_running, message = check_container_running(container_name)
        results.append(message)
        if not is_running:
            all_running = False

    # THEN: Todos los contenedores worker deben estar corriendo
    print("\n📋 Resultados de Workers:")
    for result in results:
        print(result)

    assert all_running, "Algunos servicios worker no están corriendo"


def test_supabase_connection():
    """Test que verifica la conexión a Supabase (base de datos externa)"""
    print("\n🔍 Verificando conexión a Supabase...")

    # GIVEN: Variables de entorno configuradas
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        pytest.skip("SUPABASE_URL y SUPABASE_KEY deben estar configuradas")

    # WHEN: Intentamos conectar a Supabase
    try:
        # Verificar que el URL es accesible
        response = requests.get(
            f"{supabase_url}/rest/v1/", headers={"apikey": supabase_key}, timeout=10
        )

        # THEN: Debemos recibir una respuesta (aunque sea 404 por no especificar tabla)
        # Lo importante es que el servicio responda
        connection_ok = response.status_code in [200, 404, 400]

        if connection_ok:
            print(f"✅ Supabase: Conexión exitosa (status {response.status_code})")
        else:
            print(f"❌ Supabase: Error de conexión (status {response.status_code})")

        assert connection_ok, (
            f"No se pudo conectar a Supabase (status {response.status_code})"
        )

    except Exception as e:
        pytest.fail(f"Error al conectar con Supabase: {str(e)}")


if __name__ == "__main__":
    # Ejecutar con: pytest test_all_services_health.py -v -s
    pytest.main([__file__, "-v", "-s"])
