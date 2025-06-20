#!/usr/bin/env python3
"""
run_all_tests.py - Script para ejecutar todos los tests del módulo nginx_reverse_proxy
con diferentes configuraciones y generar reportes.
"""

import subprocess
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path


def run_command(cmd, description):
    """Ejecuta un comando y muestra el resultado."""
    print(f"\n{'='*60}")
    print(f"Ejecutando: {description}")
    print(f"Comando: {cmd}")
    print('='*60)
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print(f"✅ {description} - EXITOSO")
    else:
        print(f"❌ {description} - FALLÓ (código: {result.returncode})")
    
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description='Ejecutar tests de nginx_reverse_proxy')
    parser.add_argument('--type', choices=['all', 'unit', 'integration', 'performance', 'concurrency', 'recovery', 'load', 'real'],
                       default='all', help='Tipo de tests a ejecutar')
    parser.add_argument('--coverage', action='store_true', help='Generar reporte de cobertura')
    parser.add_argument('--parallel', action='store_true', help='Ejecutar tests en paralelo')
    parser.add_argument('--verbose', '-v', action='store_true', help='Salida verbosa')
    parser.add_argument('--load-test', action='store_true', help='Ejecutar tests de carga con Locust')
    parser.add_argument('--report', action='store_true', help='Generar reporte HTML')
    
    args = parser.parse_args()
    
    # Timestamp para reportes
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Base del comando pytest
    pytest_cmd = "pytest"
    
    if args.verbose:
        pytest_cmd += " -v"
    
    if args.parallel:
        pytest_cmd += " -n auto"
    
    if args.coverage:
        pytest_cmd += " --cov=. --cov-report=term-missing"
        if args.report:
            pytest_cmd += f" --cov-report=html:htmlcov_{timestamp}"
    
    # Determinar qué tests ejecutar
    test_commands = []
    
    if args.type == 'all':
        test_commands.append((f"{pytest_cmd} tests/", "Todos los tests"))
    elif args.type == 'unit':
        test_commands.append((f"{pytest_cmd} tests/unit/", "Tests unitarios"))
    elif args.type == 'integration':
        test_commands.append((f"{pytest_cmd} tests/integration/", "Tests de integración"))
    elif args.type == 'performance':
        test_commands.append((f"{pytest_cmd} tests/integration/test_performance.py tests/integration/test_advanced_performance.py", "Tests de performance"))
    elif args.type == 'concurrency':
        test_commands.append((f"{pytest_cmd} tests/integration/test_concurrency.py", "Tests de concurrencia"))
    elif args.type == 'recovery':
        test_commands.append((f"{pytest_cmd} tests/integration/test_recovery.py", "Tests de recuperación"))
    elif args.type == 'load':
        test_commands.append((f"{pytest_cmd} tests/integration/test_load.py", "Tests de carga"))
    elif args.type == 'real':
        test_commands.append((f"{pytest_cmd} tests/integration/test_real_integration.py", "Tests de integración real"))
    
    # Ejecutar tests
    failed_tests = []
    
    print(f"\n{'#'*60}")
    print(f"# Ejecutando tests de nginx_reverse_proxy")
    print(f"# Tipo: {args.type}")
    print(f"# Timestamp: {timestamp}")
    print(f"{'#'*60}")
    
    for cmd, description in test_commands:
        if run_command(cmd, description) != 0:
            failed_tests.append(description)
    
    # Tests de carga con Locust (opcional)
    if args.load_test:
        print(f"\n{'='*60}")
        print("Iniciando Locust para tests de carga...")
        print("Accede a http://localhost:8089 para configurar el test")
        print("Presiona Ctrl+C para detener")
        print('='*60)
        
        locust_cmd = "locust -f locustfile.py --host=http://localhost"
        subprocess.run(locust_cmd, shell=True)
    
    # Resumen final
    print(f"\n{'#'*60}")
    print("# RESUMEN DE EJECUCIÓN")
    print(f"{'#'*60}")
    
    if failed_tests:
        print(f"\n❌ Tests fallidos ({len(failed_tests)}):")
        for test in failed_tests:
            print(f"  - {test}")
    else:
        print("\n✅ Todos los tests pasaron exitosamente!")
    
    if args.coverage and args.report:
        print(f"\n📊 Reporte de cobertura generado en: htmlcov_{timestamp}/index.html")
    
    # Generar reporte adicional si se solicita
    if args.report and not args.coverage:
        report_file = f"test_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(f"Reporte de Tests - nginx_reverse_proxy\n")
            f.write(f"Fecha: {datetime.now()}\n")
            f.write(f"Tipo de tests: {args.type}\n")
            f.write(f"\nResultados:\n")
            
            if failed_tests:
                f.write(f"Tests fallidos: {len(failed_tests)}\n")
                for test in failed_tests:
                    f.write(f"  - {test}\n")
            else:
                f.write("Todos los tests pasaron exitosamente!\n")
        
        print(f"\n📄 Reporte guardado en: {report_file}")
    
    # Código de salida
    sys.exit(len(failed_tests))


if __name__ == "__main__":
    main()
