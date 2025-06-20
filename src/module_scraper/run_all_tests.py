#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script principal para ejecutar todos los tests del módulo scraper.

Uso:
    python run_all_tests.py              # Ejecutar todos los tests
    python run_all_tests.py --unit       # Solo tests unitarios
    python run_all_tests.py --integration # Solo tests de integración
    python run_all_tests.py --spiders    # Solo tests de spiders
    python run_all_tests.py --coverage   # Con reporte de cobertura
    python run_all_tests.py --fast       # Excluir tests lentos
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# Colores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Imprimir encabezado con formato."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_section(text):
    """Imprimir sección con formato."""
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'-'*len(text)}{Colors.ENDC}")


def run_command(cmd, description):
    """Ejecutar comando y mostrar resultado."""
    print(f"{Colors.OKBLUE}Ejecutando: {description}{Colors.ENDC}")
    print(f"{Colors.WARNING}Comando: {' '.join(cmd)}{Colors.ENDC}\n")
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print(f"\n{Colors.OKGREEN}✓ {description} completado exitosamente{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}✗ {description} falló con código {result.returncode}{Colors.ENDC}")
    
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description='Ejecutar tests del módulo scraper')
    
    # Opciones de categorías
    parser.add_argument('--unit', action='store_true', help='Solo tests unitarios')
    parser.add_argument('--integration', action='store_true', help='Solo tests de integración')
    parser.add_argument('--e2e', action='store_true', help='Solo tests end-to-end')
    parser.add_argument('--spiders', action='store_true', help='Solo tests de spiders')
    parser.add_argument('--middlewares', action='store_true', help='Solo tests de middlewares')
    parser.add_argument('--error-handling', action='store_true', help='Solo tests de error handling')
    parser.add_argument('--pipelines', action='store_true', help='Solo tests de pipelines')
    
    # Opciones adicionales
    parser.add_argument('--coverage', action='store_true', help='Generar reporte de cobertura')
    parser.add_argument('--fast', action='store_true', help='Excluir tests marcados como lentos')
    parser.add_argument('--verbose', '-v', action='store_true', help='Output detallado')
    parser.add_argument('--failfast', '-x', action='store_true', help='Detener en el primer fallo')
    parser.add_argument('--html', action='store_true', help='Generar reporte HTML de cobertura')
    
    args = parser.parse_args()
    
    # Cambiar al directorio del proyecto
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print_header("TESTS DEL MÓDULO SCRAPER")
    
    # Construir comando pytest
    cmd = ['pytest']
    
    # Agregar opciones
    if args.verbose:
        cmd.append('-vv')
    else:
        cmd.append('-v')
    
    if args.failfast:
        cmd.append('-x')
    
    if args.fast:
        cmd.extend(['-m', 'not slow'])
    
    # Determinar qué tests ejecutar
    test_paths = []
    
    if args.unit:
        test_paths.append('tests/unit/')
        print_section("Ejecutando Tests Unitarios")
    elif args.integration:
        test_paths.append('tests/integration/')
        print_section("Ejecutando Tests de Integración")
    elif args.e2e:
        test_paths.append('tests/e2e/')
        print_section("Ejecutando Tests End-to-End")
    elif args.spiders:
        test_paths.append('tests/test_spiders/')
        print_section("Ejecutando Tests de Spiders")
    elif args.middlewares:
        test_paths.append('tests/test_middlewares/')
        print_section("Ejecutando Tests de Middlewares")
    elif args.error_handling:
        test_paths.append('tests/test_error_handling/')
        print_section("Ejecutando Tests de Error Handling")
    elif args.pipelines:
        test_paths.append('tests/test_pipelines/')
        print_section("Ejecutando Tests de Pipelines")
    else:
        # Si no se especifica categoría, ejecutar todos
        test_paths.append('tests/')
        print_section("Ejecutando TODOS los Tests")
    
    # Agregar paths al comando
    cmd.extend(test_paths)
    
    # Agregar cobertura si se solicita
    if args.coverage:
        cmd.extend([
            '--cov=scraper_core',
            '--cov-report=term-missing'
        ])
        
        if args.html:
            cmd.append('--cov-report=html')
    
    # Ejecutar tests principales
    exit_code = run_command(cmd, "Suite de Tests")
    
    # Si se solicitó cobertura HTML, mostrar mensaje
    if args.coverage and args.html and exit_code == 0:
        print(f"\n{Colors.OKGREEN}Reporte HTML de cobertura generado en: htmlcov/index.html{Colors.ENDC}")
    
    # Ejecutar validación de spiders si todo pasó
    if exit_code == 0 and not any([args.unit, args.integration, args.e2e, args.middlewares, 
                                   args.error_handling, args.pipelines]):
        print_section("Ejecutando Validación Universal de Spiders")
        
        spider_cmd = [
            sys.executable,
            'tests/test_spiders/run_spider_tests.py',
            '--report'
        ]
        
        spider_exit = run_command(spider_cmd, "Validación de Spiders")
        
        if spider_exit != 0:
            exit_code = spider_exit
    
    # Resumen final
    print_header("RESUMEN DE TESTS")
    
    if exit_code == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ Todos los tests pasaron exitosamente!{Colors.ENDC}")
        
        # Mostrar estadísticas si están disponibles
        if args.coverage:
            print(f"\n{Colors.OKCYAN}Revisa el reporte de cobertura para más detalles.{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}✗ Algunos tests fallaron. Revisa los errores arriba.{Colors.ENDC}")
    
    # Sugerencias
    print(f"\n{Colors.WARNING}Sugerencias:{Colors.ENDC}")
    print("• Para tests más rápidos: python run_all_tests.py --fast")
    print("• Para debugging: python run_all_tests.py -v --failfast")
    print("• Para cobertura completa: python run_all_tests.py --coverage --html")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
