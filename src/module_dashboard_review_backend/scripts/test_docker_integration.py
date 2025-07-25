#!/usr/bin/env python3
"""
test_docker_integration.py
Pruebas de integración Docker para Dashboard Review Backend
"""

import os
import subprocess
import sys
import time
from typing import Dict, Optional, Tuple  # noqa: F401

import requests

# Añadir el directorio padre al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class DockerIntegrationTester:
    """Clase para ejecutar pruebas de integración Docker"""

    def __init__(self):
        self.container_name = "module_dashboard_review_backend"
        self.image_name = "module_dashboard_review_backend"
        self.port = 8004
        self.base_url = f"http://localhost:{self.port}"

    def run_command(self, command: str) -> Tuple[int, str, str]:
        """Ejecuta un comando y retorna código de salida, stdout y stderr"""
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"

    def test_build(self) -> bool:
        """Prueba la construcción de la imagen Docker"""
        print("🔨 Probando construcción de imagen Docker...")

        returncode, stdout, stderr = self.run_command(
            f"docker build -t {self.image_name} ."
        )

        if returncode == 0:
            print("✅ Imagen construida exitosamente")

            # Verificar detalles de la imagen
            returncode, stdout, _ = self.run_command(
                f"docker images {self.image_name} --format '{{{{.Repository}}}}:{{{{.Tag}}}} {{{{.Size}}}}'"
            )
            if stdout:
                print(f"📦 Detalles de imagen: {stdout.strip()}")
            return True
        else:
            print(f"❌ Error al construir imagen: {stderr}")
            return False

    def test_container_start(self) -> bool:
        """Prueba el inicio del contenedor"""
        print("\n🚀 Probando inicio del contenedor...")

        # Detener y eliminar contenedor existente
        self.run_command(f"docker stop {self.container_name} 2>/dev/null")
        self.run_command(f"docker rm {self.container_name} 2>/dev/null")

        # Verificar/crear red
        returncode, _, _ = self.run_command("docker network inspect lamacquina_network")
        if returncode != 0:
            print("📡 Creando red lamacquina_network...")
            self.run_command("docker network create lamacquina_network")

        # Iniciar contenedor
        returncode, _, stderr = self.run_command(
            f"docker run -d --name {self.container_name} "
            f"--network lamacquina_network "
            f"-p {self.port}:{self.port} "
            f"--env-file .env "
            f"{self.image_name}"
        )

        if returncode == 0:
            print("✅ Contenedor iniciado")
            time.sleep(10)  # Esperar a que el servicio esté listo
            return True
        else:
            print(f"❌ Error al iniciar contenedor: {stderr}")
            return False

    def test_health_checks(self) -> bool:
        """Prueba los endpoints de health check"""
        print("\n🏥 Probando health checks...")

        all_passed = True

        # Test basic health check
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Health check básico: OK")
                data = response.json()
                print(
                    f"   Status: {data.get('status')}, Version: {data.get('version')}"
                )
            else:
                print(f"❌ Health check básico falló: {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"❌ Error en health check básico: {e}")
            all_passed = False

        # Test detailed health check
        try:
            response = requests.get(f"{self.base_url}/health/detailed", timeout=5)
            if response.status_code == 200:
                print("✅ Health check detallado: OK")
                data = response.json()

                # Verificar estado de Supabase
                supabase_status = data.get("dependencies", {}).get("supabase", {})
                if supabase_status.get("status") == "ok":
                    print(
                        f"   Supabase: OK (response time: {supabase_status.get('response_time_ms')}ms)"
                    )
                else:
                    print(
                        f"⚠️  Supabase: {supabase_status.get('status')} - {supabase_status.get('error', 'Unknown error')}"
                    )

                # Mostrar uptime
                uptime = data.get("uptime", 0)
                print(f"   Uptime: {uptime:.2f} segundos")
            else:
                print(f"❌ Health check detallado falló: {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"❌ Error en health check detallado: {e}")
            all_passed = False

        return all_passed

    def test_container_health_command(self) -> bool:
        """Prueba el comando de health check interno del contenedor"""
        print("\n🔍 Probando health check interno del contenedor...")

        returncode, stdout, stderr = self.run_command(
            f"docker exec {self.container_name} curl -f http://localhost:{self.port}/health"
        )

        if returncode == 0:
            print("✅ Health check interno funciona correctamente")
            return True
        else:
            print(f"❌ Health check interno falló: {stderr}")
            return False

    def test_security(self) -> bool:
        """Prueba configuraciones de seguridad"""
        print("\n🔒 Verificando seguridad...")

        all_passed = True

        # Verificar usuario no-root
        returncode, stdout, _ = self.run_command(
            f"docker exec {self.container_name} whoami"
        )
        if returncode == 0 and stdout.strip() == "appuser":
            print("✅ Ejecutándose como usuario no-root (appuser)")
        else:
            print(f"❌ No está ejecutándose como appuser: {stdout.strip()}")
            all_passed = False

        # Verificar UID
        returncode, stdout, _ = self.run_command(
            f"docker exec {self.container_name} id -u"
        )
        if returncode == 0 and stdout.strip() == "1000":
            print("✅ UID correcto (1000)")
        else:
            print(f"❌ UID incorrecto: {stdout.strip()}")
            all_passed = False

        return all_passed

    def test_environment_variables(self) -> bool:
        """Prueba las variables de entorno"""
        print("\n🔧 Verificando variables de entorno...")

        required_vars = ["API_PORT", "API_HOST", "SUPABASE_URL", "SUPABASE_KEY"]
        all_passed = True

        for var in required_vars:
            returncode, stdout, _ = self.run_command(
                f"docker exec {self.container_name} printenv {var}"
            )
            if returncode == 0 and stdout.strip():
                # No mostrar valores sensibles
                if "KEY" in var or "URL" in var:
                    print(f"✅ {var}: [CONFIGURADO]")
                else:
                    print(f"✅ {var}: {stdout.strip()}")
            else:
                print(f"❌ {var}: NO CONFIGURADO")
                all_passed = False

        return all_passed

    def test_error_handling(self) -> bool:
        """Prueba manejo de errores"""
        print("\n⚠️  Probando manejo de errores...")

        # Test endpoint inexistente
        try:
            response = requests.get(f"{self.base_url}/endpoint-inexistente", timeout=5)
            if response.status_code == 404:
                print("✅ Manejo correcto de endpoint inexistente (404)")
            else:
                print(
                    f"❌ Código inesperado para endpoint inexistente: {response.status_code}"
                )
                return False
        except Exception as e:
            print(f"❌ Error al probar endpoint inexistente: {e}")
            return False

        return True

    def test_logs(self) -> bool:
        """Verifica los logs del contenedor"""
        print("\n📋 Verificando logs del contenedor...")

        returncode, stdout, stderr = self.run_command(
            f"docker logs {self.container_name} --tail 20"
        )

        if returncode == 0:
            if "Dashboard Review API started successfully" in stdout:
                print("✅ Logs muestran inicio exitoso")
            else:
                print("⚠️  No se encontró mensaje de inicio en logs")

            if "ERROR" in stdout or "Exception" in stdout:
                print("⚠️  Se encontraron errores en los logs")
                return False
            else:
                print("✅ No se encontraron errores en los logs")

            return True
        else:
            print(f"❌ Error al obtener logs: {stderr}")
            return False

    def cleanup(self):
        """Limpia recursos después de las pruebas"""
        print("\n🧹 Limpiando recursos...")
        self.run_command(f"docker stop {self.container_name}")
        self.run_command(f"docker rm {self.container_name}")
        print("✅ Limpieza completada")

    def run_all_tests(self) -> bool:
        """Ejecuta todas las pruebas"""
        print("=== 🐳 Pruebas de Integración Docker ===\n")

        tests = [
            ("Build", self.test_build),
            ("Container Start", self.test_container_start),
            ("Health Checks", self.test_health_checks),
            ("Container Health Command", self.test_container_health_command),
            ("Security", self.test_security),
            ("Environment Variables", self.test_environment_variables),
            ("Error Handling", self.test_error_handling),
            ("Logs", self.test_logs),
        ]

        results = {}

        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ Error inesperado en {test_name}: {e}")
                results[test_name] = False

        # Resumen
        print("\n=== 📊 Resumen de Resultados ===")
        passed = sum(1 for result in results.values() if result)
        total = len(results)

        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name}: {status}")

        print(f"\nTotal: {passed}/{total} pruebas pasadas")

        # Limpiar
        self.cleanup()

        return passed == total


if __name__ == "__main__":
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("Dockerfile"):
        print("❌ Error: Este script debe ejecutarse desde el directorio del módulo")
        print("   Directorio actual:", os.getcwd())
        sys.exit(1)

    # Verificar que existe .env
    if not os.path.exists(".env"):
        print("⚠️  Advertencia: No se encontró archivo .env")
        print("   Copiando .env.example a .env...")
        try:
            with open(".env.example") as src, open(".env", "w") as dst:
                dst.write(src.read())
            print("✅ Archivo .env creado")
        except Exception as e:
            print(f"❌ Error al crear .env: {e}")
            sys.exit(1)

    # Ejecutar pruebas
    tester = DockerIntegrationTester()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)
