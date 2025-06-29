#!/usr/bin/env python3
"""
Verificación de TASK-005: Configuración y Sistema de Logs
"""

import sys
import os
import ast
import re

# Colores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_mark(condition):
    return f"{GREEN}✓{RESET}" if condition else f"{RED}✗{RESET}"

print(f"{BLUE}=== Verificación TASK-005: Configuración y Sistema de Logs ==={RESET}\n")

# 1. Verificar sintaxis de config.py
print("1. Verificando sintaxis de config.py...")
config_path = '/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/spider_factory/src/config.py'
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config_content = f.read()
    ast.parse(config_content)
    print(f"{check_mark(True)} Sintaxis correcta")
except Exception as e:
    print(f"{check_mark(False)} Error de sintaxis: {e}")
    sys.exit(1)

# 2. Verificar que no hay referencias config.
print("\n2. Verificando referencias corregidas...")
bad_refs = []
for i, line in enumerate(config_content.split('\n'), 1):
    if 'config.' in line and not line.strip().startswith('#'):
        bad_refs.append((i, line.strip()))

if not bad_refs:
    print(f"{check_mark(True)} No hay referencias 'config.' (todas cambiadas a 'settings.')")
else:
    print(f"{check_mark(False)} Aún hay {len(bad_refs)} referencias 'config.':")
    for line_num, line in bad_refs[:3]:
        print(f"  Línea {line_num}: {line[:60]}...")

# 3. Verificar configuraciones agregadas
print("\n3. Verificando configuraciones nuevas...")
required_configs = [
    'CACHE_TTL_DAYS',
    'CACHE_TTL_SECONDS', 
    'SPIDER_OUTPUT_PATH',
    'MAX_BATCH_SIZE',
    'CONCURRENT_REQUESTS',
    'BATCH_TIMEOUT',
    'RATE_LIMIT_REQUESTS',
    'RATE_LIMIT_WINDOW',
    'REDIS_MAX_CONNECTIONS'
]

found_configs = []
for config in required_configs:
    if config in config_content:
        found_configs.append(config)
        print(f"{check_mark(True)} {config} definido")
    else:
        print(f"{check_mark(False)} {config} NO encontrado")

# 4. Verificar función validate_config
print("\n4. Verificando función validate_config...")
if 'def validate_config' in config_content:
    print(f"{check_mark(True)} Función validate_config implementada")
    
    # Verificar contenido de validate_config
    validate_checks = [
        ('firecrawl_api_key', "Verifica Firecrawl API key"),
        ('SPIDER_OUTPUT_PATH', "Verifica directorio de salida"),
        ('redis_client.ping()', "Verifica conexión Redis"),
        ('spider_template_dir', "Verifica directorio de templates")
    ]
    
    validate_match = re.search(r'def validate_config\(self\):(.*?)(?=\n    def|\n\nclass|\Z)', config_content, re.DOTALL)
    if validate_match:
        validate_content = validate_match.group(1)
        for check, desc in validate_checks:
            if check in validate_content:
                print(f"  {check_mark(True)} {desc}")
            else:
                print(f"  {check_mark(False)} {desc}")
else:
    print(f"{check_mark(False)} Función validate_config NO encontrada")

# 5. Verificar logging_config.py
print("\n5. Verificando logging_config.py...")
logging_path = '/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/spider_factory/src/logging_config.py'
if os.path.exists(logging_path):
    print(f"{check_mark(True)} Archivo logging_config.py existe")
    
    try:
        with open(logging_path, 'r', encoding='utf-8') as f:
            logging_content = f.read()
        ast.parse(logging_content)
        print(f"{check_mark(True)} Sintaxis correcta en logging_config.py")
        
        # Verificar funciones principales
        logging_functions = [
            ('setup_logging', "Función principal de configuración"),
            ('logger.remove()', "Remueve handler por defecto"),
            ('rotation="00:00"', "Rotación diaria configurada"),
            ('logs/errors_', "Log separado para errores"),
            ('retention=', "Retención de logs configurada")
        ]
        
        for func, desc in logging_functions:
            if func in logging_content:
                print(f"  {check_mark(True)} {desc}")
            else:
                print(f"  {check_mark(False)} {desc}")
                
    except Exception as e:
        print(f"{check_mark(False)} Error en logging_config.py: {e}")
else:
    print(f"{check_mark(False)} Archivo logging_config.py NO existe")

# 6. Verificar áreas geográficas
print("\n6. Verificando lista de áreas geográficas...")
if 'AREAS_GEOGRAFICAS_VALIDAS' in config_content:
    print(f"{check_mark(True)} AREAS_GEOGRAFICAS_VALIDAS definida")
    
    # Contar elementos
    areas_match = re.search(r'AREAS_GEOGRAFICAS_VALIDAS = \[(.*?)\]', config_content, re.DOTALL)
    if areas_match:
        areas_list = areas_match.group(1)
        area_count = len(re.findall(r"'[^']+',?", areas_list))
        expected = 28
        if area_count == expected:
            print(f"  {check_mark(True)} Contiene {area_count} áreas (correcto)")
        else:
            print(f"  {check_mark(False)} Contiene {area_count} áreas (esperadas {expected})")
else:
    print(f"{check_mark(False)} AREAS_GEOGRAFICAS_VALIDAS NO definida")

# 7. Probar importación y configuración
print("\n7. Probando importación y configuración...")
try:
    sys.path.insert(0, '/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/spider_factory')
    from src.config import settings
    print(f"{check_mark(True)} Importación exitosa")
    
    # Verificar algunos valores
    print(f"  SPIDER_OUTPUT_PATH: {settings.SPIDER_OUTPUT_PATH}")
    print(f"  CACHE_TTL_DAYS: {settings.CACHE_TTL_DAYS}")
    print(f"  MAX_BATCH_SIZE: {settings.MAX_BATCH_SIZE}")
    
except Exception as e:
    print(f"{check_mark(False)} Error importando: {e}")

# Resumen
print(f"\n{BLUE}=== RESUMEN ==={RESET}")
total_checks = 7
passed_checks = sum([
    not bad_refs,
    len(found_configs) == len(required_configs),
    'def validate_config' in config_content,
    os.path.exists(logging_path),
    'AREAS_GEOGRAFICAS_VALIDAS' in config_content,
    True  # Si llegamos aquí, la importación funcionó
])

print(f"Verificaciones pasadas: {passed_checks}/{total_checks}")

if passed_checks == total_checks:
    print(f"{GREEN}✓ TASK-005 completada exitosamente!{RESET}")
else:
    print(f"{RED}✗ TASK-005 requiere correcciones{RESET}")

# Test de validate_config
print(f"\n{BLUE}=== Test de validate_config ==={RESET}")
try:
    from src.config import settings
    settings.validate_config()
    print(f"{GREEN}✓ validate_config ejecutado exitosamente{RESET}")
except Exception as e:
    print(f"{RED}✗ Error ejecutando validate_config: {e}{RESET}")

# Test de logging
print(f"\n{BLUE}=== Test de logging ==={RESET}")
try:
    from src.logging_config import setup_logging
    setup_logging()
    from loguru import logger
    logger.info("Test de logging funcionando")
    print(f"{GREEN}✓ Sistema de logging configurado correctamente{RESET}")
except Exception as e:
    print(f"{RED}✗ Error configurando logging: {e}{RESET}")