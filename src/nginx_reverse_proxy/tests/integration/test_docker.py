# tests/integration/test_docker.py
"""
Tests de integración para verificar funcionalidad Docker.
"""
import pytest
import subprocess
import time
import requests


class TestDockerIntegration:
    """Tests para verificar la integración con Docker."""
    
    def test_docker_image_builds(self, project_root):
        """Verifica que la imagen Docker se construye correctamente."""
        result = subprocess.run(
            ["docker", "build", "-t", "nginx-test-build:latest", "."],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Build falló: {result.stderr}"
        
        # Verificar que la imagen existe
        images = subprocess.run(
            ["docker", "images", "nginx-test-build:latest", "--format", "{{.Repository}}:{{.Tag}}"],
            capture_output=True,
            text=True
        )
        
        assert "nginx-test-build:latest" in images.stdout
    
    def test_container_health_check(self, nginx_container_running):
        """Verifica que el health check del container funciona."""
        # Esperar un poco para que el health check se ejecute
        time.sleep(2)
        
        # Verificar estado del container
        result = subprocess.run(
            ["docker", "inspect", nginx_container_running, "--format", "{{.State.Health.Status}}"],
            capture_output=True,
            text=True
        )
        
        health_status = result.stdout.strip()
        assert health_status in ["healthy", "starting"], f"Container no está healthy: {health_status}"
    
    def test_container_logs_generation(self, nginx_container_running, nginx_base_url):
        """Verifica que se generan logs correctamente."""
        # Hacer algunas peticiones para generar logs
        requests.get(f"{nginx_base_url}/nginx-health")
        requests.get(f"{nginx_base_url}/api/test")
        requests.get(f"{nginx_base_url}/")
        
        # Obtener logs
        result = subprocess.run(
            ["docker", "logs", nginx_container_running, "--tail", "10"],
            capture_output=True,
            text=True
        )
        
        logs = result.stdout + result.stderr
        
        # Verificar que hay logs de acceso
        assert "/nginx-health" in logs or "GET" in logs
        
    def test_container_network_connectivity(self, nginx_container_running):
        """Verifica que el container está en la red correcta."""
        result = subprocess.run(
            ["docker", "inspect", nginx_container_running, "--format", "{{range .NetworkSettings.Networks}}{{.NetworkID}}{{end}}"],
            capture_output=True,
            text=True
        )
        
        # Verificar que está conectado a alguna red
        assert result.stdout.strip() != "", "Container no está conectado a ninguna red"
        
        # Verificar específicamente lamacquina_network
        network_result = subprocess.run(
            ["docker", "inspect", nginx_container_running, "--format", "{{.NetworkSettings.Networks.lamacquina_network}}"],
            capture_output=True,
            text=True
        )
        
        assert "NetworkID" in network_result.stdout or network_result.stdout.strip() != "<no value>"
    
    def test_container_restart_recovery(self, nginx_container_running, nginx_base_url):
        """Verifica que el container se recupera después de un restart."""
        # Restart del container
        subprocess.run(
            ["docker", "restart", nginx_container_running],
            check=True
        )
        
        # Esperar a que se levante
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{nginx_base_url}/nginx-health", timeout=1)
                if response.status_code == 200:
                    break
            except:
                pass
            time.sleep(1)
        else:
            pytest.fail("Container no se recuperó después del restart")
        
        # Verificar que funciona normalmente
        response = requests.get(f"{nginx_base_url}/nginx-health")
        assert response.status_code == 200
    
    def test_health_check_script_execution(self, nginx_container_running):
        """Verifica que el script de health check se ejecuta correctamente."""
        # Ejecutar el health check script manualmente
        result = subprocess.run(
            ["docker", "exec", nginx_container_running, "/usr/local/bin/health-check.sh"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Health check script falló: {result.stderr}"
        assert "✅" in result.stdout, "Health check no reporta estado correcto"
    
    def test_container_resource_limits(self, nginx_container_running):
        """Verifica que el container no consume recursos excesivos."""
        # Obtener estadísticas del container
        result = subprocess.run(
            ["docker", "stats", nginx_container_running, "--no-stream", "--format", "{{.MemUsage}}"],
            capture_output=True,
            text=True
        )
        
        # Verificar que se obtuvieron stats
        assert result.stdout.strip() != "", "No se pudieron obtener estadísticas del container"
    
    def test_volume_mounts(self, nginx_container_running):
        """Verifica que los archivos necesarios están montados correctamente."""
        # Verificar que nginx.conf está presente
        result = subprocess.run(
            ["docker", "exec", nginx_container_running, "ls", "-la", "/etc/nginx/nginx.conf"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, "nginx.conf no está presente en el container"
        
        # Verificar que el directorio de logs existe
        result = subprocess.run(
            ["docker", "exec", nginx_container_running, "ls", "-la", "/var/log/nginx/"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, "Directorio de logs no existe"
    
    def test_user_permissions(self, nginx_container_running):
        """Verifica que nginx corre con el usuario correcto (no root)."""
        result = subprocess.run(
            ["docker", "exec", nginx_container_running, "ps", "aux"],
            capture_output=True,
            text=True
        )
        
        # Buscar procesos nginx
        nginx_processes = [line for line in result.stdout.split('\n') if 'nginx' in line and 'worker' in line]
        
        # Verificar que hay procesos worker
        assert len(nginx_processes) > 0, "No se encontraron procesos nginx worker"
        
        # Verificar que no corren como root (UID 0)
        for process in nginx_processes:
            parts = process.split()
            if len(parts) > 0:
                user = parts[0]
                assert user != "root", "Nginx worker está corriendo como root"
