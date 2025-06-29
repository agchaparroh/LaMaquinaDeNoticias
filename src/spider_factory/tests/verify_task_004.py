#!/usr/bin/env python3
"""
Verificación de TASK-004: API y Endpoints
"""

import sys
import os
import ast
import re

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Colores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_mark(condition):
    return f"{GREEN}✓{RESET}" if condition else f"{RED}✗{RESET}"

print(f"{BLUE}=== Verificación TASK-004: API y Endpoints ==={RESET}\n")

# 1. Verificar sintaxis del archivo
print("1. Verificando sintaxis de api.py...")
api_path = '/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/spider_factory/src/api.py'
try:
    with open(api_path, 'r', encoding='utf-8') as f:
        api_content = f.read()
    ast.parse(api_content)
    print(f"{check_mark(True)} Sintaxis correcta")
except Exception as e:
    print(f"{check_mark(False)} Error de sintaxis: {e}")
    sys.exit(1)

# 2. Verificar campos en AnalysisRequest
print("\n2. Verificando campos en AnalysisRequest...")
required_fields = ['medio', 'seccion', 'area_geografica', 'tipo_medio', 'frecuencia_minutos']
found_fields = []

# Buscar definición de AnalysisRequest
analysis_match = re.search(r'class AnalysisRequest\(BaseModel\):(.*?)(?=class|\Z)', api_content, re.DOTALL)
if analysis_match:
    class_content = analysis_match.group(1)
    for field in required_fields:
        if f'{field}:' in class_content:
            found_fields.append(field)
            print(f"{check_mark(True)} Campo '{field}' encontrado")
        else:
            print(f"{check_mark(False)} Campo '{field}' NO encontrado")

# 3. Verificar validadores de retrocompatibilidad
print("\n3. Verificando validadores para retrocompatibilidad...")
validators = ['set_medio_from_name', 'set_default_seccion']
found_validators = []

for validator in validators:
    if f'def {validator}' in api_content:
        found_validators.append(validator)
        print(f"{check_mark(True)} Validador '{validator}' encontrado")
    else:
        print(f"{check_mark(False)} Validador '{validator}' NO encontrado")

# 4. Verificar nuevo endpoint check-duplicate
print("\n4. Verificando endpoint /api/check-duplicate...")
if '/api/check-duplicate' in api_content and '@app.post' in api_content:
    print(f"{check_mark(True)} Endpoint check-duplicate implementado")
    
    # Verificar DuplicateCheckRequest
    if 'class DuplicateCheckRequest' in api_content:
        print(f"{check_mark(True)} Modelo DuplicateCheckRequest definido")
    else:
        print(f"{check_mark(False)} Modelo DuplicateCheckRequest NO encontrado")
    
    # Verificar DuplicateCheckResponse
    if 'class DuplicateCheckResponse' in api_content:
        print(f"{check_mark(True)} Modelo DuplicateCheckResponse definido")
    else:
        print(f"{check_mark(False)} Modelo DuplicateCheckResponse NO encontrado")
else:
    print(f"{check_mark(False)} Endpoint check-duplicate NO encontrado")

# 5. Verificar actualización del endpoint analyze
print("\n5. Verificando actualización del endpoint /analyze...")
analyze_match = re.search(r'async def analyze_site\(request: AnalysisRequest\):(.*?)(?=@app|\Z)', api_content, re.DOTALL)
if analyze_match:
    analyze_content = analyze_match.group(1)
    
    # Verificar uso de nuevos campos
    checks = [
        ('medio = request.medio', "Usa campo medio"),
        ('seccion = request.seccion', "Usa campo seccion"),
        ('area_geografica = request.area_geografica', "Usa campo area_geografica"),
        ('tipo_medio = request.tipo_medio', "Usa campo tipo_medio"),
        ('SiteAnalysisRequest', "Crea SiteAnalysisRequest con nuevos campos")
    ]
    
    for check, desc in checks:
        if check in analyze_content:
            print(f"{check_mark(True)} {desc}")
        else:
            print(f"{check_mark(False)} {desc}")

# 6. Verificar actualización del endpoint generate
print("\n6. Verificando actualización del endpoint /generate...")
generate_match = re.search(r'async def generate_spider\(request: GenerateSpiderRequest\):(.*?)(?=@app|\Z)', api_content, re.DOTALL)
if generate_match:
    generate_content = generate_match.group(1)
    
    # Verificar extracción de campos con fallbacks
    checks = [
        ('medio = request.medio', "Extrae campo medio"),
        ('seccion = request.seccion', "Extrae campo seccion"),
        ('spider_name = f"{medio}_{seccion}"', "Genera nombre automático"),
        ('settings.SPIDER_OUTPUT_PATH', "Usa directorio correcto"),
        ('await generator.generate_spider', "Llama al generador con await"),
    ]
    
    for check, desc in checks:
        if check in generate_content:
            print(f"{check_mark(True)} {desc}")
        else:
            print(f"{check_mark(False)} {desc}")

# 7. Verificar imports correctos
print("\n7. Verificando imports...")
required_imports = [
    'from .analyzer import SmartAnalyzer, SiteAnalysisRequest, AnalysisResult, AnalysisStrategy',
    'from pydantic import BaseModel, HttpUrl, Field, validator',
    'from typing import List, Dict, Any, Optional, Literal'
]

for imp in required_imports:
    if imp in api_content:
        print(f"{check_mark(True)} Import correcto: {imp[:50]}...")
    else:
        print(f"{check_mark(False)} Import faltante: {imp[:50]}...")

# 8. Verificar que no hay ScrapingStrategy (debe ser AnalysisStrategy)
print("\n8. Verificando uso correcto de AnalysisStrategy...")
if 'ScrapingStrategy' in api_content:
    print(f"{check_mark(False)} ERROR: Se encontró ScrapingStrategy (debe ser AnalysisStrategy)")
else:
    print(f"{check_mark(True)} No se usa ScrapingStrategy (correcto)")

# Resumen
print(f"\n{BLUE}=== RESUMEN ==={RESET}")
total_checks = 8
passed_checks = sum([
    len(found_fields) == len(required_fields),  # Todos los campos en AnalysisRequest
    len(found_validators) == len(validators),   # Validadores retrocompatibilidad
    '/api/check-duplicate' in api_content and '@app.post' in api_content,  # Endpoint existe
    'DuplicateCheckRequest' in api_content,     # Modelo request
    'DuplicateCheckResponse' in api_content,    # Modelo response  
    'medio = request.medio' in api_content,     # Analyze usa nuevos campos
    'spider_name = f"{medio}_{seccion}"' in api_content,  # Generate auto-nombra
    'ScrapingStrategy' not in api_content       # No usa clase incorrecta
])

print(f"Verificaciones pasadas: {passed_checks}/{total_checks}")

if passed_checks == total_checks:
    print(f"{GREEN}✓ TASK-004 completada exitosamente!{RESET}")
else:
    print(f"{RED}✗ TASK-004 requiere correcciones{RESET}")

# Verificar retrocompatibilidad
print(f"\n{BLUE}=== Verificación de Retrocompatibilidad ==={RESET}")
print("Los endpoints deben seguir aceptando el formato antiguo:")
print("- /analyze debe aceptar 'name' además de 'medio'")
print("- /generate debe aceptar 'spider_name' y 'site_name'")
print("- Los campos nuevos deben ser opcionales en la primera fase")

# Mostrar ejemplo de uso
print(f"\n{BLUE}=== Ejemplo de uso del nuevo endpoint ==={RESET}")
print("""
# Verificar duplicado:
curl -X POST http://localhost/spider-factory/api/check-duplicate \\
  -H "Content-Type: application/json" \\
  -d '{
    "medio": "El País",
    "seccion": "Internacional"
  }'

# Respuesta esperada:
{
  "exists": false,
  "spider_name": null,
  "file_path": null,
  "similar_spiders": ["el_pais_economia", "el_pais_deportes"],
  "message": "Nombre disponible"
}
""")