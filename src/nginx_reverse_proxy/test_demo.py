# test_demo.py - Test de demostración para verificar que todo funciona

import subprocess
import sys
import os

def test_configuration_files_exist():
    """Verifica que los archivos de configuración existen."""
    required_files = [
        "config/nginx.conf",
        ".env",
        "Dockerfile",
        "docker-compose.yml"
    ]
    
    for file in required_files:
        assert os.path.exists(file), f"Archivo requerido {file} no encontrado"
    
    print("✅ Todos los archivos de configuración existen")

def test_nginx_syntax():
    """Valida la sintaxis de nginx.conf."""
    config_path = os.path.abspath("config/nginx.conf")
    
    result = subprocess.run([
        "docker", "run", "--rm",
        "-v", f"{config_path}:/etc/nginx/nginx.conf:ro",
        "nginx:1.25-alpine",
        "nginx", "-t"
    ], capture_output=True, text=True)
    
    assert result.returncode == 0, f"Sintaxis nginx inválida: {result.stderr}"
    print("✅ Sintaxis de nginx.conf es válida")

def test_docker_build():
    """Verifica que la imagen Docker se construye correctamente."""
    print("🔨 Construyendo imagen Docker...")
    
    result = subprocess.run([
        "docker", "build", "-t", "nginx-demo-test:latest", "."
    ], capture_output=True, text=True)
    
    assert result.returncode == 0, f"Build falló: {result.stderr}"
    print("✅ Imagen Docker construida exitosamente")

def main():
    """Ejecuta los tests de demostración."""
    print("🧪 Ejecutando tests de demostración para nginx_reverse_proxy\n")
    
    try:
        test_configuration_files_exist()
        test_nginx_syntax()
        test_docker_build()
        
        print("\n✅ ¡Todos los tests de demostración pasaron!")
        print("\n📝 Para ejecutar la suite completa de tests:")
        print("   make test-all      # Con Makefile")
        print("   pytest tests/ -v   # Directamente con pytest")
        
    except AssertionError as e:
        print(f"\n❌ Test falló: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
