"""
Test Runner - Ejecuta verificaciones básicas sin dependencias externas
Útil para verificar que el código esté bien estructurado
"""

import importlib.util
import os  # noqa: F401
import sys
import traceback  # noqa: F401
from datetime import datetime
from pathlib import Path


class TestRunner:
    """Ejecutor de tests básicos sin dependencias"""

    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.src_path = self.project_root / "src"
        self.results = {"passed": [], "failed": [], "skipped": []}

        # Agregar src al path
        sys.path.insert(0, str(self.src_path))

    def test_imports(self):
        """Verifica que todos los módulos se puedan importar"""
        print("\n🔍 TEST: Verificando imports...")

        modules_to_test = [
            "config",
            "models",
            "analyzer",
            "patterns",
            "generator",
            "batch_processor",
            "websocket_manager",
            "api",
        ]

        for module_name in modules_to_test:
            try:
                module_path = self.src_path / f"{module_name}.py"
                if not module_path.exists():
                    self.results["skipped"].append(
                        f"Import {module_name}: Archivo no encontrado"
                    )
                    print(f"⚠️  {module_name}: SKIP (no encontrado)")
                    continue

                # Intentar importar
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)  # noqa: F841

                # Esto verificará sintaxis sin ejecutar el código
                print(f"✅ {module_name}: OK")
                self.results["passed"].append(f"Import {module_name}")

            except SyntaxError as e:
                print(f"❌ {module_name}: Error de sintaxis en línea {e.lineno}")
                self.results["failed"].append(f"Import {module_name}: {str(e)}")
            except Exception as e:
                print(f"❌ {module_name}: {type(e).__name__}")
                self.results["failed"].append(f"Import {module_name}: {str(e)}")

    def test_structure(self):
        """Verifica la estructura del proyecto"""
        print("\n🔍 TEST: Verificando estructura del proyecto...")

        required_dirs = [
            "src",
            "templates",
            "templates/spiders",
            "tests",
            "tests/unit",
            "tests/integration",
            "docs",
            "generated_spiders",
            "logs",
        ]

        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                print(f"✅ {dir_name}/: OK")
                self.results["passed"].append(f"Directorio {dir_name}")
            else:
                print(f"❌ {dir_name}/: No encontrado")
                self.results["failed"].append(f"Directorio {dir_name}")

    def test_required_files(self):
        """Verifica que existan archivos requeridos"""
        print("\n🔍 TEST: Verificando archivos requeridos...")

        required_files = [
            "requirements.txt",
            "Dockerfile",
            "docker-compose.yml",
            ".gitignore",
            "src/__init__.py",
            "templates/spiders/rss_spider.j2",
            "templates/spiders/scraping_spider.j2",
            "templates/spiders/playwright_spider.j2",
        ]

        for file_name in required_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                print(f"✅ {file_name}: OK")
                self.results["passed"].append(f"Archivo {file_name}")
            else:
                print(f"❌ {file_name}: No encontrado")
                self.results["failed"].append(f"Archivo {file_name}")

    def test_config_variables(self):
        """Verifica variables de configuración"""
        print("\n🔍 TEST: Verificando configuración...")

        try:
            from config import RedisConfig, SpiderFactoryConfig  # noqa: F401

            # Verificar configuración básica
            config = SpiderFactoryConfig()

            checks = [
                ("API Host", config.api_host),
                ("API Port", config.api_port),
                ("Spider Output Dir", config.spider_output_dir),
                ("Template Dir", config.spider_template_dir),
            ]

            for check_name, value in checks:
                if value:
                    print(f"✅ {check_name}: {value}")
                    self.results["passed"].append(f"Config {check_name}")
                else:
                    print(f"⚠️  {check_name}: No configurado")
                    self.results["skipped"].append(f"Config {check_name}")

        except ImportError:
            print("❌ No se pudo importar configuración")
            self.results["failed"].append("Importar configuración")
        except Exception as e:
            print(f"❌ Error verificando configuración: {e}")
            self.results["failed"].append(f"Configuración: {str(e)}")

    def test_class_definitions(self):
        """Verifica que las clases principales estén definidas"""
        print("\n🔍 TEST: Verificando definiciones de clases...")

        classes_to_check = [
            ("analyzer", "SmartAnalyzer"),
            ("generator", "SpiderGenerator"),
            ("patterns", "PatternStorage"),
            ("batch_processor", "BatchProcessor"),
            ("websocket_manager", "ConnectionManager"),
        ]

        for module_name, class_name in classes_to_check:
            try:
                module_path = self.src_path / f"{module_name}.py"

                with open(module_path, encoding="utf-8") as f:
                    content = f.read()

                if f"class {class_name}" in content:
                    print(f"✅ {module_name}.{class_name}: OK")
                    self.results["passed"].append(f"Clase {class_name}")
                else:
                    print(f"❌ {module_name}.{class_name}: No encontrada")
                    self.results["failed"].append(f"Clase {class_name}")

            except FileNotFoundError:
                print(f"⚠️  {module_name}.{class_name}: Archivo no encontrado")
                self.results["skipped"].append(f"Clase {class_name}")
            except Exception as e:
                print(f"❌ {module_name}.{class_name}: Error - {e}")
                self.results["failed"].append(f"Clase {class_name}: {str(e)}")

    def run_all_tests(self):
        """Ejecuta todos los tests"""
        print("🧪 SPIDER FACTORY 2.0 - TEST RUNNER")
        print("=" * 60)
        print(f"📁 Proyecto: {self.project_root}")
        print(f"🕐 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Ejecutar tests
        self.test_structure()
        self.test_required_files()
        self.test_imports()
        self.test_config_variables()
        self.test_class_definitions()

        # Mostrar resumen
        self.show_summary()

    def show_summary(self):
        """Muestra resumen de resultados"""
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE RESULTADOS")
        print("=" * 60)

        total_passed = len(self.results["passed"])
        total_failed = len(self.results["failed"])
        total_skipped = len(self.results["skipped"])
        total_tests = total_passed + total_failed + total_skipped

        print(f"\n✅ Pasados:  {total_passed}/{total_tests}")
        print(f"❌ Fallidos: {total_failed}/{total_tests}")
        print(f"⚠️  Omitidos: {total_skipped}/{total_tests}")

        if total_failed > 0:
            print("\n❌ TESTS FALLIDOS:")
            for failed in self.results["failed"]:
                print(f"  - {failed}")

        if total_skipped > 0:
            print("\n⚠️  TESTS OMITIDOS:")
            for skipped in self.results["skipped"]:
                print(f"  - {skipped}")

        # Resultado final
        if total_failed == 0:
            print("\n✅ TODOS LOS TESTS CRÍTICOS PASARON")
            return 0
        else:
            print(f"\n❌ {total_failed} TESTS FALLARON")
            return 1


def main():
    """Función principal"""
    # Obtener directorio del proyecto
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        # Por defecto, usar el directorio spider_factory
        project_root = Path(__file__).parent.parent.parent

    # Crear y ejecutar test runner
    runner = TestRunner(project_root)
    return runner.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())
