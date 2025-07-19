#!/usr/bin/env python3
"""
Script para verificar y corregir los campos de entidades en el pipeline.
Este script analiza dónde se están generando los campos con sufijo.
"""

import json
import re
import sys
from pathlib import Path

def find_entity_field_patterns():
    """Busca patrones de campos de entidad con sufijo en el código."""
    
    pipeline_path = Path("/home/ec2-user/projects/LaMaquinaDeNoticias/src/module_pipeline")
    
    # Patrones a buscar
    patterns = [
        (r'"nombre_entidad":', "nombre_entidad con sufijo"),
        (r'"tipo_entidad":', "tipo_entidad con sufijo"),
        (r'"descripcion_entidad":', "descripcion_entidad con sufijo"),
        (r'nombre_entidad\s*=', "asignación nombre_entidad"),
        (r'tipo_entidad\s*=', "asignación tipo_entidad"),
    ]
    
    results = {}
    
    # Buscar en archivos Python
    for py_file in pipeline_path.rglob("*.py"):
        if "test" in str(py_file) or "__pycache__" in str(py_file):
            continue
            
        try:
            content = py_file.read_text()
            for pattern, desc in patterns:
                matches = list(re.finditer(pattern, content))
                if matches:
                    if str(py_file) not in results:
                        results[str(py_file)] = []
                    
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        # Obtener contexto
                        lines = content.split('\n')
                        start = max(0, line_num - 3)
                        end = min(len(lines), line_num + 2)
                        context = '\n'.join(f"{i+1}: {lines[i]}" for i in range(start, end))
                        
                        results[str(py_file)].append({
                            'pattern': desc,
                            'line': line_num,
                            'context': context
                        })
        except Exception as e:
            print(f"Error leyendo {py_file}: {e}")
    
    return results

def main():
    """Función principal."""
    print("=" * 80)
    print("ANÁLISIS DE CAMPOS DE ENTIDAD CON SUFIJO")
    print("=" * 80)
    
    results = find_entity_field_patterns()
    
    if not results:
        print("No se encontraron patrones de campos con sufijo.")
        return
    
    # Mostrar resultados
    for file_path, matches in results.items():
        print(f"\n📄 {file_path}")
        print("-" * 40)
        
        for match in matches:
            print(f"\n  Patrón: {match['pattern']} (línea {match['line']})")
            print("  Contexto:")
            for line in match['context'].split('\n'):
                print(f"    {line}")
    
    # Análisis específico de archivos clave
    print("\n" + "=" * 80)
    print("ARCHIVOS CLAVE A REVISAR:")
    print("=" * 80)
    
    key_files = [
        "src/pipeline/pipeline_coordinator.py",
        "src/services/payload_builder.py",
        "src/controller.py"
    ]
    
    for key_file in key_files:
        found = False
        for file_path in results:
            if key_file in file_path:
                found = True
                print(f"\n✓ {key_file}: ENCONTRADO con campos con sufijo")
                break
        if not found:
            print(f"\n✗ {key_file}: Sin campos con sufijo detectados")
    
    # Sugerencia de corrección
    print("\n" + "=" * 80)
    print("SUGERENCIA DE CORRECCIÓN:")
    print("=" * 80)
    print("""
1. El problema parece estar en algún lugar donde se transforman los datos
   antes de enviarlos al PayloadBuilder.

2. Los campos deben enviarse SIN sufijo:
   - "nombre" en lugar de "nombre_entidad"
   - "tipo" en lugar de "tipo_entidad"
   - "descripcion" en lugar de "descripcion_entidad"

3. Verificar:
   - Que el código Docker esté actualizado
   - Que no haya transformaciones intermedias
   - Que el modelo Pydantic esté configurado correctamente
""")

if __name__ == "__main__":
    main()