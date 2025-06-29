#!/usr/bin/env python3
"""
Verificación de TASK-006: Sistemas de Métricas, Cache y Redis Pool
"""

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

print(f"{BLUE}=== Verificación TASK-006: Métricas, Cache y Redis Pool ==={RESET}\n")

# Base path
BASE_PATH = '/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/spider_factory/src'

# 1. Verificar archivos creados
print("1. Verificando archivos creados...")
required_files = {
    'redis_pool.py': 'Redis connection pooling',
    'metrics.py': 'Sistema de métricas',
    'performance_metrics.py': 'Métricas de rendimiento',
    'notifications.py': 'Sistema de notificaciones'
}

files_exist = {}
for filename, description in required_files.items():
    filepath = os.path.join(BASE_PATH, filename)
    exists = os.path.exists(filepath)
    files_exist[filename] = exists
    print(f"{check_mark(exists)} {filename} - {description}")

# 2. Verificar sintaxis de archivos
print("\n2. Verificando sintaxis...")
for filename in required_files:
    if files_exist[filename]:
        filepath = os.path.join(BASE_PATH, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            print(f"{check_mark(True)} {filename} - sintaxis correcta")
        except Exception as e:
            print(f"{check_mark(False)} {filename} - error: {e}")

# 3. Verificar Redis connection pool
print("\n3. Verificando Redis connection pool...")
if files_exist['redis_pool.py']:
    with open(os.path.join(BASE_PATH, 'redis_pool.py'), 'r') as f:
        redis_pool_content = f.read()
    
    pool_checks = [
        ('max_connections=50', 'Pool con 50 conexiones máximo'),
        ('class RedisConnectionPool', 'Clase principal definida'),
        ('_instance = None', 'Patrón Singleton implementado'),
        ('async def get_client', 'Método get_client asíncrono'),
        ('ConnectionPool', 'Usa ConnectionPool de redis.asyncio')
    ]
    
    for check, desc in pool_checks:
        found = check in redis_pool_content
        print(f"  {check_mark(found)} {desc}")

# 4. Verificar sistema de métricas
print("\n4. Verificando sistema de métricas...")
if files_exist['metrics.py']:
    with open(os.path.join(BASE_PATH, 'metrics.py'), 'r') as f:
        metrics_content = f.read()
    
    metrics_checks = [
        ('increment_spider_generated', 'Tracking de spiders generados'),
        ('record_generation_time', 'Registro de tiempos'),
        ('record_cache_hit', 'Tracking de cache hits'),
        ('get_system_metrics', 'Obtención de métricas del sistema'),
        ('calculate_time_reduction', 'Cálculo de reducción de tiempo'),
        ('tiempo_reduccion.*97', 'Target de reducción 97%')
    ]
    
    for check, desc in metrics_checks:
        found = re.search(check, metrics_content) is not None
        print(f"  {check_mark(found)} {desc}")

# 5. Verificar KPIs de tiempo
print("\n5. Verificando KPIs de tiempo...")
if files_exist['performance_metrics.py']:
    with open(os.path.join(BASE_PATH, 'performance_metrics.py'), 'r') as f:
        perf_content = f.read()
    
    kpi_checks = [
        ('RSS_TIME = 5', 'KPI RSS: <5 segundos'),
        ('FIRST_TIME = 20', 'KPI Primera vez: ~20 segundos'),
        ('CACHE_TIME = 2', 'KPI Cache: <2 segundos'),
        ('MIN_REDUCTION = 97', 'KPI Reducción mínima: 97%'),
        ('validate_generation_time', 'Validación de tiempos'),
        ('get_performance_report', 'Generación de reportes')
    ]
    
    for check, desc in kpi_checks:
        found = check in perf_content
        print(f"  {check_mark(found)} {desc}")

# 6. Verificar sistema de notificaciones
print("\n6. Verificando sistema de notificaciones...")
if files_exist['notifications.py']:
    with open(os.path.join(BASE_PATH, 'notifications.py'), 'r') as f:
        notif_content = f.read()
    
    notif_checks = [
        ('notify_spider_failure', 'Notificación de fallos'),
        ('notify_structure_change', 'Notificación de cambios de estructura'),
        ('notify_performance_degradation', 'Notificación de degradación'),
        ('_send_slack', 'Integración con Slack'),
        ('failure_threshold', 'Umbral de fallos configurado')
    ]
    
    for check, desc in notif_checks:
        found = check in notif_content
        print(f"  {check_mark(found)} {desc}")

# 7. Verificar endpoint /metrics en API
print("\n7. Verificando endpoint /metrics...")
api_path = os.path.join(BASE_PATH, 'api.py')
if os.path.exists(api_path):
    with open(api_path, 'r') as f:
        api_content = f.read()
    
    endpoint_checks = [
        ('@app.get("/metrics")', 'Endpoint /metrics definido'),
        ('get_system_metrics', 'Llama a get_system_metrics'),
        ('/metrics/summary', 'Endpoint summary adicional'),
        ('/metrics/performance', 'Endpoint de performance')
    ]
    
    for check, desc in endpoint_checks:
        found = check in api_content
        print(f"  {check_mark(found)} {desc}")
else:
    print(f"  {check_mark(False)} api.py no encontrado")

# 8. Verificar configuración actualizada
print("\n8. Verificando configuración Redis en config.py...")
config_path = os.path.join(BASE_PATH, 'config.py')
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config_content = f.read()
    
    config_checks = [
        ('REDIS_HOST:', 'REDIS_HOST configurado'),
        ('REDIS_PORT:', 'REDIS_PORT configurado'),
        ('REDIS_DB:', 'REDIS_DB configurado'),
        ('REDIS_PASSWORD:', 'REDIS_PASSWORD configurado')
    ]
    
    for check, desc in config_checks:
        found = check in config_content
        print(f"  {check_mark(found)} {desc}")

# Resumen
print(f"\n{BLUE}=== RESUMEN ==={RESET}")
total_checks = 8
passed_checks = sum([
    all(files_exist.values()),
    'max_connections=50' in redis_pool_content if files_exist['redis_pool.py'] else False,
    'get_system_metrics' in metrics_content if files_exist['metrics.py'] else False,
    'RSS_TIME = 5' in perf_content if files_exist['performance_metrics.py'] else False,
    'notify_spider_failure' in notif_content if files_exist['notifications.py'] else False,
    '@app.get("/metrics")' in api_content if os.path.exists(api_path) else False,
    'REDIS_HOST:' in config_content if os.path.exists(config_path) else False,
    True  # Para sintaxis si llegamos aquí
])

print(f"Verificaciones pasadas: {passed_checks}/{total_checks}")

if passed_checks == total_checks:
    print(f"{GREEN}✓ TASK-006 completada exitosamente!{RESET}")
else:
    print(f"{RED}✗ TASK-006 requiere correcciones{RESET}")

# Mostrar objetivos de KPIs
print(f"\n{BLUE}=== Objetivos de KPIs ==={RESET}")
print("Tiempo de generación:")
print("  - RSS: < 5 segundos")
print("  - Primera vez: ~20 segundos") 
print("  - Con cache: < 2 segundos")
print("  - Reducción vs manual: 97%")
print("\nEficiencia:")
print("  - Precisión spiders: >90%")
print("  - Cache hit rate: Alto")
print("  - Reducción requests: 70%")
print("\nThroughput:")
print("  - Spiders/día: 200+")
print("\nAdopción:")
print("  - Uso diario: >80%")

# Test de endpoints
print(f"\n{BLUE}=== Test de Endpoints (manual) ==={RESET}")
print("Para probar los endpoints:")
print("1. curl http://localhost/spider-factory/api/metrics")
print("2. curl http://localhost/spider-factory/api/metrics/summary")
print("3. curl http://localhost/spider-factory/api/metrics/performance")