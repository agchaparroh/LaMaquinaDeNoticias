# tests/conftest.py
"""
Fixtures compartidos para los tests de nginx_reverse_proxy.
"""
import pytest
import subprocess
import time
import requests
import os
from pathlib import Path


@pytest.fixture(scope="session")
def project_root():
    """Retorna la ruta raíz del módulo nginx_reverse_proxy."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def docker_compose_file(project_root):
    """Retorna la ruta al archivo docker-compose.yml."""
    return project_root / "docker-compose.yml"


@pytest.fixture(scope="session")
def nginx_config_file(project_root):
    """Retorna la ruta al archivo nginx.conf."""
    return project_root / "config" / "nginx.conf"


@pytest.fixture(scope="session")
def env_file(project_root):
    """Retorna la ruta al archivo .env."""
    return project_root / ".env"


@pytest.fixture(scope="session")
def nginx_container_name():
    """Nombre del container nginx para tests."""
    return "nginx_reverse_proxy_test"


@pytest.fixture(scope="session")
def nginx_base_url():
    """URL base para tests contra nginx."""
    return "http://localhost"


@pytest.fixture(scope="session")
def mock_backend_container():
    """
    Crea un container mock para simular el backend.
    Usa httpbin como servidor de echo para simular respuestas.
    """
    container_name = "mock_dashboard_backend"
    
    # Verificar si ya existe y eliminarlo
    subprocess.run(
        ["docker", "rm", "-f", container_name],
        capture_output=True
    )
    
    # Crear red si no existe
    subprocess.run(
        ["docker", "network", "create", "lamacquina_network"],
        capture_output=True
    )
    
    # Levantar container mock
    subprocess.run([
        "docker", "run", "-d",
        "--name", container_name,
        "--network", "lamacquina_network",
        "--network-alias", "module_dashboard_review_backend",
        "-p", "8004:80",
        "kennethreitz/httpbin"
    ], check=True)
    
    # Esperar a que esté listo
    time.sleep(3)
    
    yield container_name
    
    # Cleanup
    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)


@pytest.fixture(scope="session")
def mock_frontend_container():
    """
    Crea un container mock para simular el frontend.
    Usa nginx con contenido estático simple.
    """
    container_name = "mock_dashboard_frontend"
    
    # Verificar si ya existe y eliminarlo
    subprocess.run(
        ["docker", "rm", "-f", container_name],
        capture_output=True
    )
    
    # Crear red si no existe
    subprocess.run(
        ["docker", "network", "create", "lamacquina_network"],
        capture_output=True
    )
    
    # Crear contenido HTML simple
    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Mock Frontend</title></head>
    <body><h1>Mock Dashboard Frontend</h1></body>
    </html>
    """
    
    # Levantar container mock
    subprocess.run([
        "docker", "run", "-d",
        "--name", container_name,
        "--network", "lamacquina_network",
        "--network-alias", "module_dashboard_review_frontend",
        "-p", "8080:80",
        "nginx:alpine"
    ], check=True)
    
    # Inyectar HTML
    subprocess.run([
        "docker", "exec", container_name,
        "sh", "-c", f"echo '{html_content}' > /usr/share/nginx/html/index.html"
    ], check=True)
    
    # Esperar a que esté listo
    time.sleep(2)
    
    yield container_name
    
    # Cleanup
    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)


@pytest.fixture(scope="session")
def nginx_container_running(project_root, mock_backend_container, mock_frontend_container, nginx_container_name):
    """
    Asegura que el container nginx está corriendo para los tests.
    """
    # Detener container si existe
    subprocess.run(
        ["docker", "rm", "-f", nginx_container_name],
        capture_output=True
    )
    
    # Build de la imagen
    build_result = subprocess.run(
        ["docker", "build", "-t", f"{nginx_container_name}:test", "."],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if build_result.returncode != 0:
        pytest.fail(f"Failed to build nginx image: {build_result.stderr}")
    
    # Levantar container
    run_result = subprocess.run([
        "docker", "run", "-d",
        "--name", nginx_container_name,
        "--network", "lamacquina_network",
        "-p", "80:80",
        "-e", "NGINX_HOST=localhost",
        "-e", "NGINX_PORT=80",
        f"{nginx_container_name}:test"
    ], capture_output=True, text=True)
    
    if run_result.returncode != 0:
        pytest.fail(f"Failed to run nginx container: {run_result.stderr}")
    
    # Esperar a que nginx esté listo
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost/nginx-health", timeout=1)
            if response.status_code == 200:
                break
        except:
            pass
        time.sleep(1)
    else:
        pytest.fail("Nginx container did not start properly")
    
    yield nginx_container_name
    
    # Cleanup
    subprocess.run(["docker", "rm", "-f", nginx_container_name], capture_output=True)


@pytest.fixture
def http_session():
    """Session HTTP reutilizable para tests."""
    session = requests.Session()
    session.headers.update({"User-Agent": "nginx-test-client"})
    return session
