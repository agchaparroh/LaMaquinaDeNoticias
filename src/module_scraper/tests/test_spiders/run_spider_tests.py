#!/usr/bin/env python
"""
Script para ejecutar tests de spiders de La Máquina de Noticias

Uso:
    python run_spider_tests.py                    # Ejecutar todos los tests
    python run_spider_tests.py --universal        # Solo tests universales
    python run_spider_tests.py --compliance       # Solo tests de conformidad
    python run_spider_tests.py --spider nombre    # Validar un spider específico
    python run_spider_tests.py --report           # Generar reporte completo
"""

import argparse
import os
import sys
from pathlib import Path

import pytest

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.test_spiders import (  # noqa: E402
    TestUniversalSpider,
    generate_compliance_report,
    print_compliance_report,
    validate_spider,
)


def run_all_tests():
    """Ejecutar todos los tests de spiders."""
    print("\n" + "=" * 60)
    print("EJECUTANDO TODOS LOS TESTS DE SPIDERS")
    print("=" * 60 + "\n")

    # Ejecutar pytest con los tests de spiders
    exit_code = pytest.main(["tests/test_spiders/", "-v", "--tb=short"])

    return exit_code


def run_universal_tests():
    """Ejecutar solo los tests universales."""
    print("\n" + "=" * 60)
    print("EJECUTANDO TESTS UNIVERSALES DE SPIDERS")
    print("=" * 60 + "\n")

    exit_code = pytest.main(
        ["tests/test_spiders/test_universal_spider.py", "-v", "--tb=short"]
    )

    return exit_code


def run_compliance_tests():
    """Ejecutar solo los tests de conformidad con el generador."""
    print("\n" + "=" * 60)
    print("EJECUTANDO TESTS DE CONFORMIDAD CON @GENERADOR-SPIDERS")
    print("=" * 60 + "\n")

    exit_code = pytest.main(
        ["tests/test_spiders/test_generator_compliance.py", "-v", "--tb=short"]
    )

    return exit_code


def validate_specific_spider(spider_name):
    """Validar un spider específico."""
    print("\n" + "=" * 60)
    print(f"VALIDANDO SPIDER: {spider_name}")
    print("=" * 60 + "\n")

    try:
        # Intentar importar el spider
        module_name = f"scraper_core.spiders.{spider_name}_spider"
        module = __import__(module_name, fromlist=[spider_name])

        # Buscar la clase del spider
        spider_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, Spider)  # noqa: F821
                and attr.__name__ != "Spider"
                and attr.__name__ != "BaseArticleSpider"
            ):
                spider_class = attr
                break

        if not spider_class:
            print(f"❌ No se encontró la clase del spider en {module_name}")
            return 1

        # Validar el spider
        validate_spider(spider_class)

        # Generar reporte de conformidad
        report = generate_compliance_report(spider_class)
        print_compliance_report(report)

        return 0 if report["status"] == "COMPLIANT" else 1

    except ImportError as e:
        print(f"❌ No se pudo importar el spider '{spider_name}': {e}")
        return 1
    except Exception as e:
        print(f"❌ Error validando el spider: {e}")
        return 1


def generate_full_report():
    """Generar reporte completo de todos los spiders."""
    print("\n" + "=" * 60)
    print("GENERANDO REPORTE COMPLETO DE SPIDERS")
    print("=" * 60 + "\n")

    test_helper = TestUniversalSpider()
    spiders = test_helper.get_all_spiders()

    if not spiders:
        print("⚠️  No se encontraron spiders para analizar")
        return 1

    print(f"📊 Analizando {len(spiders)} spiders...\n")

    reports = []
    compliant_count = 0
    mostly_compliant_count = 0
    non_compliant_count = 0

    for spider_class in spiders:
        try:
            report = generate_compliance_report(spider_class)
            reports.append(report)

            if report["status"] == "COMPLIANT":
                compliant_count += 1
                print(
                    f"✅ {spider_class.name}: COMPLIANT ({report['compliance_percentage']:.1f}%)"
                )
            elif report["status"] == "MOSTLY_COMPLIANT":
                mostly_compliant_count += 1
                print(
                    f"⚠️  {spider_class.name}: MOSTLY_COMPLIANT ({report['compliance_percentage']:.1f}%)"
                )
            else:
                non_compliant_count += 1
                print(
                    f"❌ {spider_class.name}: NON_COMPLIANT ({report['compliance_percentage']:.1f}%)"
                )

        except Exception as e:
            print(f"❌ {spider_class.name}: ERROR - {e}")

    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Total de spiders: {len(spiders)}")
    print(f"✅ Compliant: {compliant_count}")
    print(f"⚠️  Mostly Compliant: {mostly_compliant_count}")
    print(f"❌ Non-Compliant: {non_compliant_count}")
    print(f"\nTasa de conformidad: {(compliant_count / len(spiders) * 100):.1f}%")

    # Mostrar detalles de los no conformes
    if non_compliant_count > 0:
        print("\n" + "-" * 60)
        print("SPIDERS NO CONFORMES - REQUIEREN ATENCIÓN:")
        print("-" * 60)

        for report in reports:
            if report["status"] == "NON_COMPLIANT":
                print(f"\n{report['spider_name']}:")
                for issue in report["issues"][
                    :3
                ]:  # Mostrar solo los primeros 3 problemas
                    print(f"  - {issue}")
                if len(report["issues"]) > 3:
                    print(f"  ... y {len(report['issues']) - 3} problemas más")

    return 0 if non_compliant_count == 0 else 1


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Ejecutar tests de spiders de La Máquina de Noticias"
    )

    parser.add_argument(
        "--universal", action="store_true", help="Ejecutar solo tests universales"
    )

    parser.add_argument(
        "--compliance",
        action="store_true",
        help="Ejecutar solo tests de conformidad con el generador",
    )

    parser.add_argument(
        "--spider", type=str, help="Validar un spider específico (nombre sin _spider)"
    )

    parser.add_argument(
        "--report",
        action="store_true",
        help="Generar reporte completo de todos los spiders",
    )

    parser.add_argument(
        "--coverage", action="store_true", help="Ejecutar con análisis de cobertura"
    )

    args = parser.parse_args()

    # Cambiar al directorio del proyecto
    os.chdir(project_root)

    # Ejecutar la acción solicitada
    if args.spider:
        exit_code = validate_specific_spider(args.spider)
    elif args.report:
        exit_code = generate_full_report()
    elif args.universal:
        exit_code = run_universal_tests()
    elif args.compliance:
        exit_code = run_compliance_tests()
    else:
        # Sin argumentos, ejecutar todos los tests
        exit_code = run_all_tests()

    # Si se solicitó cobertura, ejecutar análisis
    if args.coverage and exit_code == 0:
        print("\n" + "=" * 60)
        print("GENERANDO REPORTE DE COBERTURA")
        print("=" * 60 + "\n")

        coverage_code = pytest.main(
            [
                "tests/test_spiders/",
                "--cov=scraper_core.spiders",
                "--cov-report=html",
                "--cov-report=term-missing",
            ]
        )

        if coverage_code == 0:
            print("\n✅ Reporte de cobertura generado en htmlcov/index.html")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
