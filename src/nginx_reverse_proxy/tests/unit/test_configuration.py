# tests/unit/test_configuration.py
"""
Tests unitarios para validar la configuración de nginx.
"""
import pytest
import subprocess
import os
from pathlib import Path


class TestNginxConfiguration:
    """Tests para validar la configuración de nginx."""
    
    def test_nginx_config_exists(self, nginx_config_file):
        """Verifica que el archivo nginx.conf existe."""
        assert nginx_config_file.exists(), f"nginx.conf no encontrado en {nginx_config_file}"
    
    def test_nginx_config_syntax(self, nginx_config_file, project_root):
        """Valida la sintaxis del archivo nginx.conf."""
        # Crear un container temporal para validar sintaxis
        result = subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{nginx_config_file}:/etc/nginx/nginx.conf:ro",
            "nginx:1.25-alpine",
            "nginx", "-t"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Sintaxis inválida en nginx.conf: {result.stderr}"
    
    def test_env_file_exists(self, env_file):
        """Verifica que el archivo .env existe."""
        assert env_file.exists(), f".env no encontrado en {env_file}"
    
    def test_env_file_contains_required_vars(self, env_file):
        """Verifica que .env contiene las variables requeridas."""
        required_vars = [
            "NGINX_HOST",
            "NGINX_PORT",
            "DASHBOARD_BACKEND_HOST",
            "DASHBOARD_BACKEND_PORT",
            "DASHBOARD_FRONTEND_HOST",
            "DASHBOARD_FRONTEND_PORT"
        ]
        
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        for var in required_vars:
            assert var in env_content, f"Variable requerida {var} no encontrada en .env"
    
    def test_dockerfile_exists(self, project_root):
        """Verifica que el Dockerfile existe."""
        dockerfile = project_root / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile no encontrado"
    
    def test_docker_compose_files_exist(self, project_root):
        """Verifica que los archivos docker-compose existen."""
        compose_files = [
            "docker-compose.yml",
            "docker-compose.integration.yml"
        ]
        
        for file in compose_files:
            filepath = project_root / file
            assert filepath.exists(), f"{file} no encontrado"
    
    def test_nginx_config_has_upstreams(self, nginx_config_file):
        """Verifica que nginx.conf define los upstreams necesarios."""
        with open(nginx_config_file, 'r') as f:
            config_content = f.read()
        
        required_upstreams = [
            "upstream dashboard_backend",
            "upstream dashboard_frontend"
        ]
        
        for upstream in required_upstreams:
            assert upstream in config_content, f"Upstream '{upstream}' no encontrado en nginx.conf"
    
    def test_nginx_config_has_rate_limiting(self, nginx_config_file):
        """Verifica que nginx.conf tiene configuración de rate limiting."""
        with open(nginx_config_file, 'r') as f:
            config_content = f.read()
        
        rate_limit_zones = [
            "zone=api:10m rate=100r/m",
            "zone=general:10m rate=300r/m"
        ]
        
        for zone in rate_limit_zones:
            assert zone in config_content, f"Rate limit zone '{zone}' no encontrada"
    
    def test_nginx_config_has_security_headers(self, nginx_config_file):
        """Verifica que nginx.conf incluye headers de seguridad."""
        with open(nginx_config_file, 'r') as f:
            config_content = f.read()
        
        security_headers = [
            "X-Frame-Options DENY",
            "X-Content-Type-Options nosniff",
            "X-XSS-Protection",
            "Referrer-Policy"
        ]
        
        for header in security_headers:
            assert header in config_content, f"Security header '{header}' no encontrado"
    
    def test_nginx_config_has_gzip(self, nginx_config_file):
        """Verifica que nginx.conf tiene gzip habilitado."""
        with open(nginx_config_file, 'r') as f:
            config_content = f.read()
        
        assert "gzip on;" in config_content, "Gzip no está habilitado"
        assert "gzip_types" in config_content, "Tipos de gzip no configurados"
    
    def test_health_check_script_in_dockerfile(self, project_root):
        """Verifica que el Dockerfile incluye el script de health check."""
        dockerfile = project_root / "Dockerfile"
        with open(dockerfile, 'r') as f:
            dockerfile_content = f.read()
        
        assert "health-check.sh" in dockerfile_content, "Script de health check no encontrado en Dockerfile"
        assert "HEALTHCHECK" in dockerfile_content, "HEALTHCHECK no configurado en Dockerfile"
