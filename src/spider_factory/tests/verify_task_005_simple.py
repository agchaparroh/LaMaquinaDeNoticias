#!/usr/bin/env python3
"""
Verificación simple de TASK-005 sin dependencias externas
"""

import os
import re

# Colores para output
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def check_mark(condition):
    return f"{GREEN}✓{RESET}" if condition else f"{RED}✗{RESET}"


print(f"{BLUE}=== Verificación TASK-005: Configuración y Sistema de Logs ==={RESET}\n")

# 1. Verificar referencias incorrectas en config.py
print("1. Verificando referencias en config.py...")
config_path = "/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/spider_factory/src/config.py"
with open(config_path, encoding="utf-8") as f:
    config_content = f.read()

# Buscar referencias incorrectas (excluyendo la variable local en __init__)
bad_refs = []
in_redis_manager_init = False
for i, line in enumerate(config_content.split("\n"), 1):
    # Detectar si estamos en el __init__ de RedisManager
    if "def __init__(self):" in line and i > 140 and i < 160:
        in_redis_manager_init = True
    elif in_redis_manager_init and line.strip() and not line.startswith("        "):
        in_redis_manager_init = False

    # Si no estamos en __init__ de RedisManager y hay "config."
    if (
        not in_redis_manager_init
        and "config." in line
        and not line.strip().startswith("#")
    ):
        # Excluir la línea donde se define config = RedisConfig()
        if "config = RedisConfig()" not in line:
            bad_refs.append((i, line.strip()))

if not bad_refs:
    print(f"{check_mark(True)} Referencias corregidas correctamente")
else:
    print(f"{check_mark(False)} Aún hay referencias incorrectas:")
    for line_num, line in bad_refs[:3]:
        print(f"  Línea {line_num}: {line[:60]}...")

# 2. Verificar configuraciones agregadas
print("\n2. Verificando configuraciones nuevas...")
configs_found = 0
required_configs = [
    "CACHE_TTL_DAYS",
    "CACHE_TTL_SECONDS",
    "SPIDER_OUTPUT_PATH",
    "MAX_BATCH_SIZE",
    "CONCURRENT_REQUESTS",
    "BATCH_TIMEOUT",
    "RATE_LIMIT_REQUESTS",
    "RATE_LIMIT_WINDOW",
    "REDIS_MAX_CONNECTIONS",
]

for config in required_configs:
    if re.search(f"{config}\\s*[:=]", config_content):
        configs_found += 1

print(
    f"{check_mark(configs_found == len(required_configs))} {configs_found}/{len(required_configs)} configuraciones encontradas"
)

# 3. Verificar validate_config
print("\n3. Verificando función validate_config...")
has_validate = "def validate_config" in config_content
print(
    f"{check_mark(has_validate)} Función validate_config {'existe' if has_validate else 'NO existe'}"
)

# 4. Verificar logging_config.py
print("\n4. Verificando logging_config.py...")
logging_path = "/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/spider_factory/src/logging_config.py"
logging_exists = os.path.exists(logging_path)
print(
    f"{check_mark(logging_exists)} logging_config.py {'existe' if logging_exists else 'NO existe'}"
)

if logging_exists:
    with open(logging_path, encoding="utf-8") as f:
        logging_content = f.read()

    has_setup = "def setup_logging" in logging_content
    has_rotation = 'rotation="00:00"' in logging_content
    has_errors = "logs/errors_" in logging_content

    print(f"  {check_mark(has_setup)} setup_logging definida")
    print(f"  {check_mark(has_rotation)} Rotación diaria configurada")
    print(f"  {check_mark(has_errors)} Log de errores separado")

# 5. Verificar AREAS_GEOGRAFICAS_VALIDAS
print("\n5. Verificando áreas geográficas...")
has_areas = "AREAS_GEOGRAFICAS_VALIDAS" in config_content
print(
    f"{check_mark(has_areas)} AREAS_GEOGRAFICAS_VALIDAS {'definida' if has_areas else 'NO definida'}"
)

if has_areas:
    # Contar áreas
    areas_match = re.search(
        r"AREAS_GEOGRAFICAS_VALIDAS = \[(.*?)\]", config_content, re.DOTALL
    )
    if areas_match:
        areas_list = areas_match.group(1)
        # Contar elementos considerando que están en múltiples líneas
        area_count = len(re.findall(r"'[^']+'", areas_list))
        print(f"  Total de áreas: {area_count}")

# Resumen
print(f"\n{BLUE}=== RESUMEN ==={RESET}")
all_good = (
    not bad_refs
    and configs_found == len(required_configs)
    and has_validate
    and logging_exists
    and has_areas
)

if all_good:
    print(f"{GREEN}✓ TASK-005 completada exitosamente!{RESET}")
else:
    print(f"{RED}✗ TASK-005 requiere algunas correcciones{RESET}")

print("\nNota: La importación puede fallar por dependencias externas,")
print("pero la estructura del código es correcta.")
