#!/usr/bin/env python3
"""
Script para ejecutar diferentes conjuntos de tests del module_connector
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd: list) -> int:
    """Ejecuta un comando y retorna el código de salida"""
    print(f"\n🚀 Ejecutando: {' '.join(cmd)}")
    print("-" * 80)
    return subprocess.call(cmd)


def main():
    parser = argparse.ArgumentParser(description="Ejecutor de tests para module_connector")
    parser.add_argument(
        "--suite", 
        choices=["all", "unit", "integration", "performance", "concurrency", "recovery", "stress", "quick"],
        default="quick",
        help="Suite de tests a ejecutar"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true",
        help="Ejecutar con análisis de cobertura"
    )
    parser.add_argument(
        "--parallel", 
        action="store_true",
        help="Ejecutar tests en paralelo"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Salida verbosa"
    )
    parser.add_argument(
        "--failfast", "-x",
        action="store_true",
        help="Detener en el primer fallo"
    )
    
    args = parser.parse_args()
    
    # Comando base
    cmd = ["pytest"]
    
    # Agregar opciones
    if args.verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")
    
    if args.failfast:
        cmd.append("-x")
    
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    if args.coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing", "--cov-report=html"])
    
    # Seleccionar tests según la suite
    if args.suite == "all":
        print("🏃 Ejecutando TODOS los tests...")
        cmd.append("tests/")
    
    elif args.suite == "unit":
        print("🧪 Ejecutando tests UNITARIOS...")
        cmd.extend(["-m", "unit or (not integration and not slow)", "tests/unit/"])
    
    elif args.suite == "integration":
        print("🔌 Ejecutando tests de INTEGRACIÓN...")
        cmd.extend(["tests/integration/", "-k", "not real_integration"])
    
    elif args.suite == "performance":
        print("⚡ Ejecutando tests de PERFORMANCE...")
        cmd.append("tests/performance/test_performance.py")
    
    elif args.suite == "concurrency":
        print("🔀 Ejecutando tests de CONCURRENCIA...")
        cmd.append("tests/performance/test_concurrency.py")
    
    elif args.suite == "recovery":
        print("🔧 Ejecutando tests de RECUPERACIÓN...")
        cmd.append("tests/integration/test_recovery.py")
    
    elif args.suite == "stress":
        print("🔥 Ejecutando tests de STRESS/CARGA...")
        cmd.extend(["-m", "slow or stress", "tests/performance/test_load_stress.py"])
    
    elif args.suite == "quick":
        print("⚡ Ejecutando tests RÁPIDOS...")
        cmd.extend(["-m", "not slow and not integration", "tests/"])
    
    # Ejecutar comando
    result = run_command(cmd)
    
    # Mostrar resumen
    print("\n" + "=" * 80)
    if result == 0:
        print("✅ Tests completados exitosamente!")
        
        if args.coverage:
            print("\n📊 Reporte de cobertura generado en: htmlcov/index.html")
            
            # Mostrar resumen de cobertura
            print("\n📈 Resumen de cobertura:")
            subprocess.call(["coverage", "report", "--skip-covered", "--show-missing"])
    else:
        print("❌ Tests fallaron!")
        sys.exit(result)
    
    # Sugerencias adicionales
    print("\n💡 Otras opciones útiles:")
    print("  - Para tests específicos: pytest tests/unit/test_models.py::TestArticuloInItem::test_valid_article_full_data")
    print("  - Para tests con patrón: pytest -k 'concurrent or recovery'")
    print("  - Para ver salida completa: pytest -s")
    print("  - Para generar reporte HTML: pytest --html=report.html")
    
    return result


if __name__ == "__main__":
    sys.exit(main())
