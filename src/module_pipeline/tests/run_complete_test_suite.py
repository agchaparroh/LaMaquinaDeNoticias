"""
Suite Completa de Tests del Pipeline
===================================

Script para ejecutar todos los tests de performance, concurrencia,
recuperación e integración del módulo Pipeline.

Uso:
    python tests/run_complete_test_suite.py [opciones]

Opciones:
    --all           Ejecutar todos los tests
    --performance   Ejecutar solo tests de performance
    --concurrency   Ejecutar solo tests de concurrencia
    --recovery      Ejecutar solo tests de recuperación
    --integration   Ejecutar tests de integración real (requiere servicios)
    --report        Generar reporte HTML al finalizar
"""

import argparse
import json  # noqa: F401
import os  # noqa: F401
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


class TestSuiteRunner:
    """Ejecutor de la suite completa de tests."""

    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None

    def run_test_module(
        self, module_name: str, test_file: str, extra_args: list = None
    ) -> bool:
        """
        Ejecuta un módulo de tests y captura los resultados.

        Args:
            module_name: Nombre del módulo para mostrar
            test_file: Archivo de test a ejecutar
            extra_args: Argumentos adicionales para pytest

        Returns:
            True si los tests pasaron, False en caso contrario
        """
        print(f"\n{'=' * 80}")
        print(f"Ejecutando: {module_name}")
        print(f"{'=' * 80}")

        cmd = [sys.executable, "-m", "pytest", test_file, "-v", "-s"]
        if extra_args:
            cmd.extend(extra_args)

        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start

        # Analizar salida
        output = result.stdout + result.stderr
        passed = result.returncode == 0

        # Extraer estadísticas de pytest
        stats = self._extract_pytest_stats(output)

        self.results[module_name] = {
            "passed": passed,
            "duration": duration,
            "return_code": result.returncode,
            "stats": stats,
            "output_summary": self._extract_summary(output),
        }

        if passed:
            print(f"\n✅ {module_name} completado exitosamente en {duration:.2f}s")
        else:
            print(f"\n❌ {module_name} falló después de {duration:.2f}s")

        return passed

    def _extract_pytest_stats(self, output: str) -> dict:
        """Extrae estadísticas de la salida de pytest."""
        stats = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}

        # Buscar línea de resumen de pytest
        for line in output.split("\n"):
            if "passed" in line and ("failed" in line or "error" in line):
                # Extraer números
                import re

                numbers = re.findall(r"(\d+)\s+(\w+)", line)
                for num, status in numbers:
                    if "passed" in status:
                        stats["passed"] = int(num)
                    elif "failed" in status:
                        stats["failed"] = int(num)
                    elif "skipped" in status:
                        stats["skipped"] = int(num)
                    elif "error" in status:
                        stats["errors"] = int(num)
                break

        return stats

    def _extract_summary(self, output: str) -> str:
        """Extrae un resumen de la salida."""
        lines = output.split("\n")
        summary_lines = []

        # Buscar líneas importantes
        for line in lines:
            if any(
                keyword in line.lower()
                for keyword in [
                    "throughput",
                    "latencia",
                    "éxito",
                    "error",
                    "resumen",
                    "passed",
                    "failed",
                ]
            ):
                summary_lines.append(line.strip())

        return "\n".join(summary_lines[-10:])  # Últimas 10 líneas importantes

    def run_all_tests(self, include_integration: bool = False):
        """Ejecuta todos los tests de la suite."""
        self.start_time = datetime.now()

        # Tests a ejecutar
        test_modules = [
            ("Tests de Performance y Carga", "tests/test_performance_load.py", []),
            ("Tests de Concurrencia", "tests/test_concurrency.py", []),
            ("Tests de Recuperación", "tests/test_recovery.py", []),
        ]

        if include_integration:
            test_modules.append(
                (
                    "Tests de Integración Real",
                    "tests/test_integration_real.py",
                    ["--real-services"],
                )
            )

        # Ejecutar cada módulo
        total_passed = 0
        total_modules = len(test_modules)

        for module_name, test_file, extra_args in test_modules:
            if self.run_test_module(module_name, test_file, extra_args):
                total_passed += 1

            # Pausa entre módulos para evitar sobrecarga
            time.sleep(2)

        self.end_time = datetime.now()

        # Resumen final
        self._print_final_summary(total_passed, total_modules)

        return total_passed == total_modules

    def run_specific_test(self, test_type: str) -> bool:
        """Ejecuta un tipo específico de test."""
        self.start_time = datetime.now()

        test_mapping = {
            "performance": (
                "Tests de Performance y Carga",
                "tests/test_performance_load.py",
                [],
            ),
            "concurrency": ("Tests de Concurrencia", "tests/test_concurrency.py", []),
            "recovery": ("Tests de Recuperación", "tests/test_recovery.py", []),
            "integration": (
                "Tests de Integración Real",
                "tests/test_integration_real.py",
                ["--real-services"],
            ),
        }

        if test_type not in test_mapping:
            print(f"❌ Tipo de test no reconocido: {test_type}")
            return False

        module_name, test_file, extra_args = test_mapping[test_type]
        result = self.run_test_module(module_name, test_file, extra_args)

        self.end_time = datetime.now()
        self._print_final_summary(1 if result else 0, 1)

        return result

    def _print_final_summary(self, passed: int, total: int):
        """Imprime el resumen final de todos los tests."""
        duration = (self.end_time - self.start_time).total_seconds()

        print(f"\n{'=' * 80}")
        print("RESUMEN FINAL DE LA SUITE DE TESTS")
        print(f"{'=' * 80}")
        print(f"Tiempo total: {duration:.2f} segundos")
        print(f"Módulos ejecutados: {total}")
        print(f"Módulos exitosos: {passed}")
        print(f"Módulos fallidos: {total - passed}")
        print(f"Tasa de éxito: {(passed / total * 100):.1f}%")

        # Detalle por módulo
        print(f"\nDETALLE POR MÓDULO:")  # noqa: F541
        print("-" * 80)

        for module_name, result in self.results.items():
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            stats = result["stats"]
            total_tests = sum(stats.values())

            print(f"\n{module_name}:")
            print(f"  Estado: {status}")
            print(f"  Duración: {result['duration']:.2f}s")
            print(
                f"  Tests: {total_tests} total "
                f"({stats['passed']} passed, {stats['failed']} failed, "
                f"{stats['skipped']} skipped, {stats['errors']} errors)"
            )

        print(f"\n{'=' * 80}")

        if passed == total:
            print("🎉 ¡TODOS LOS TESTS PASARON! 🎉")
        else:
            print("❌ Algunos tests fallaron. Revisa los detalles arriba.")

    def generate_html_report(self):
        """Genera un reporte HTML con los resultados."""
        if not self.results:
            print("No hay resultados para generar reporte")
            return

        # Crear directorio de reportes
        report_dir = Path("test_results/reports")
        report_dir.mkdir(parents=True, exist_ok=True)

        # Generar HTML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"test_suite_report_{timestamp}.html"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Reporte de Tests - Pipeline</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        .summary {{
            background-color: #f0f0f0;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .module {{
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        .module.passed {{
            border-left: 5px solid #4CAF50;
        }}
        .module.failed {{
            border-left: 5px solid #f44336;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin: 10px 0;
        }}
        .stat {{
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 14px;
        }}
        .stat.passed {{ background-color: #4CAF50; color: white; }}
        .stat.failed {{ background-color: #f44336; color: white; }}
        .stat.skipped {{ background-color: #ff9800; color: white; }}
        .stat.errors {{ background-color: #9c27b0; color: white; }}
        pre {{
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 3px;
            overflow-x: auto;
            font-size: 12px;
        }}
        .timestamp {{
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Reporte de Tests del Pipeline</h1>
        <p class="timestamp">Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="summary">
            <h2>Resumen General</h2>
            <p><strong>Duración total:</strong> {(self.end_time - self.start_time).total_seconds():.2f} segundos</p>
            <p><strong>Módulos ejecutados:</strong> {len(self.results)}</p>
            <p><strong>Módulos exitosos:</strong> {sum(1 for r in self.results.values() if r["passed"])}</p>
            <p><strong>Tasa de éxito:</strong> {sum(1 for r in self.results.values() if r["passed"]) / len(self.results) * 100:.1f}%</p>
        </div>
        
        <h2>Resultados por Módulo</h2>
        {self._generate_module_sections()}
    </div>
</body>
</html>
        """

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"\n📊 Reporte HTML generado: {report_file}")

        # Intentar abrir en el navegador
        try:
            import webbrowser

            webbrowser.open(f"file://{report_file.absolute()}")
        except:  # noqa: E722
            pass

    def _generate_module_sections(self) -> str:
        """Genera las secciones HTML para cada módulo."""
        sections = []

        for module_name, result in self.results.items():
            status_class = "passed" if result["passed"] else "failed"
            stats = result["stats"]

            section = f"""
        <div class="module {status_class}">
            <h3>{module_name}</h3>
            <p><strong>Estado:</strong> {"✅ EXITOSO" if result["passed"] else "❌ FALLIDO"}</p>
            <p><strong>Duración:</strong> {result["duration"]:.2f} segundos</p>
            
            <div class="stats">
                <span class="stat passed">Passed: {stats["passed"]}</span>
                <span class="stat failed">Failed: {stats["failed"]}</span>
                <span class="stat skipped">Skipped: {stats["skipped"]}</span>
                <span class="stat errors">Errors: {stats["errors"]}</span>
            </div>
            
            <details>
                <summary>Ver resumen de salida</summary>
                <pre>{result["output_summary"]}</pre>
            </details>
        </div>
            """
            sections.append(section)

        return "\n".join(sections)


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="Suite completa de tests del Pipeline")
    parser.add_argument("--all", action="store_true", help="Ejecutar todos los tests")
    parser.add_argument(
        "--performance", action="store_true", help="Ejecutar tests de performance"
    )
    parser.add_argument(
        "--concurrency", action="store_true", help="Ejecutar tests de concurrencia"
    )
    parser.add_argument(
        "--recovery", action="store_true", help="Ejecutar tests de recuperación"
    )
    parser.add_argument(
        "--integration", action="store_true", help="Ejecutar tests de integración real"
    )
    parser.add_argument("--report", action="store_true", help="Generar reporte HTML")

    args = parser.parse_args()

    # Si no se especifica ningún test, mostrar ayuda
    if not any(
        [args.all, args.performance, args.concurrency, args.recovery, args.integration]
    ):
        parser.print_help()
        return 1

    # Verificar que el servidor esté ejecutándose
    print("🔍 Verificando que el servidor del Pipeline esté activo...")

    import requests

    from src.utils.config import API_HOST, API_PORT

    try:
        response = requests.get(f"http://{API_HOST}:{API_PORT}/health", timeout=5)
        if response.status_code != 200:
            print("❌ El servidor del Pipeline no está respondiendo correctamente")
            print(f"   Inicia el servidor con: python -m src.main")  # noqa: F541
            return 1
        print("✅ Servidor activo y respondiendo\n")
    except Exception as e:
        print(f"❌ No se puede conectar al servidor del Pipeline")  # noqa: F541
        print(f"   Error: {e}")
        print(
            f"   Asegúrate de que el servidor esté ejecutándose en http://{API_HOST}:{API_PORT}"
        )
        return 1

    # Ejecutar tests
    runner = TestSuiteRunner()
    success = True

    if args.all:
        success = runner.run_all_tests(include_integration=args.integration)
    else:
        # Ejecutar tests específicos
        if args.performance:
            success &= runner.run_specific_test("performance")
        if args.concurrency:
            success &= runner.run_specific_test("concurrency")
        if args.recovery:
            success &= runner.run_specific_test("recovery")
        if args.integration:
            success &= runner.run_specific_test("integration")

    # Generar reporte si se solicitó
    if args.report:
        runner.generate_html_report()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
