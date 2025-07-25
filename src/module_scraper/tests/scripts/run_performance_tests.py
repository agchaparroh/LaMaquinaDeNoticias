#!/usr/bin/env python3
"""
Script para ejecutar todos los tests de performance, concurrencia y carga.
"""

import os  # noqa: F401
import subprocess
import sys
import time
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def run_test_file(test_file, test_name):
    """Ejecuta un archivo de test individual"""
    print(f"\n{'=' * 60}")
    print(f"🧪 Ejecutando: {test_name}")
    print(f"📄 Archivo: {test_file}")
    print("=" * 60)

    try:
        # Ejecutar con pytest si está disponible, sino con python
        try:
            result = subprocess.run(
                ["pytest", "-v", test_file],
                capture_output=True,
                text=True,
                cwd=project_root,
            )
        except FileNotFoundError:
            # Pytest no disponible, ejecutar directamente
            result = subprocess.run(
                ["python", test_file], capture_output=True, text=True, cwd=project_root
            )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        if result.returncode == 0:
            print(f"✅ {test_name} - EXITOSO")
            return True
        else:
            print(f"❌ {test_name} - FALLÓ")
            return False

    except Exception as e:
        print(f"❌ Error ejecutando {test_name}: {str(e)}")
        return False


def main():
    """Ejecuta todos los tests de performance"""
    print("🚀 EJECUTANDO SUITE DE TESTS DE PERFORMANCE")
    print(f"📁 Directorio: {project_root}")

    # Lista de tests a ejecutar
    tests = [
        ("tests/performance/test_basic_performance.py", "Test de Performance Básico"),
        ("tests/performance/test_simple_concurrency.py", "Test de Concurrencia"),
        ("tests/performance/test_basic_recovery.py", "Test de Recuperación"),
        ("tests/integration/test_real_integration.py", "Test de Integración Real"),
        ("tests/performance/test_basic_load.py", "Test de Carga"),
    ]

    # Ejecutar cada test
    results = []
    start_time = time.time()

    for test_file, test_name in tests:
        test_path = project_root / test_file
        if test_path.exists():
            success = run_test_file(str(test_path), test_name)
            results.append((test_name, success))
        else:
            print(f"⚠️  {test_name} - NO ENCONTRADO en {test_path}")
            results.append((test_name, False))

    # Resumen
    elapsed_time = time.time() - start_time

    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 60)

    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)

    for test_name, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{status} - {test_name}")

    print(f"\n📈 Total: {passed_tests}/{total_tests} tests exitosos")
    print(f"⏱️  Tiempo total: {elapsed_time:.2f} segundos")

    # Código de salida
    if passed_tests == total_tests:
        print("\n🎉 ¡Todos los tests pasaron exitosamente!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests fallaron")
        return 1


if __name__ == "__main__":
    sys.exit(main())
