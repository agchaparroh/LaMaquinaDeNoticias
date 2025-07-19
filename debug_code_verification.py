#!/usr/bin/env python3
"""Script simple para verificar cambios en el código usando Docker"""

import subprocess
import json

def run_docker_command(cmd):
    """Ejecutar comando en el contenedor Docker"""
    full_cmd = f"docker exec lamaquina-pipeline {cmd}"
    try:
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr
    except Exception as e:
        return "", str(e)

def check_code_changes():
    """Verificar si los cambios están en el código"""
    print("=== VERIFICACIÓN DE CAMBIOS EN CÓDIGO ===\n")
    
    # 1. Verificar si existe el método _generar_payload_articulo_completo
    stdout, stderr = run_docker_command(
        "sh -c \"cd /app && python3 -c \\\"import sys; sys.path.insert(0, '/app'); "
        "from src.pipeline.pipeline_coordinator import PipelineCoordinator; "
        "pc = PipelineCoordinator(); "
        "print('Método existe:', hasattr(pc, '_generar_payload_articulo_completo'))\\\"\""
    )
    print("1. Método _generar_payload_articulo_completo:")
    print(f"   Resultado: {stdout.strip()}")
    if stderr:
        print(f"   Error: {stderr}")
    
    # 2. Verificar si el código tiene el comentario de detección
    stdout, stderr = run_docker_command(
        "grep -n 'Detección de tipo de contenido' /app/src/pipeline/pipeline_coordinator.py"
    )
    print("\n2. Comentario 'Detección de tipo de contenido':")
    if stdout:
        print(f"   ✅ Encontrado: {stdout.strip()}")
    else:
        print(f"   ❌ NO encontrado")
    
    # 3. Verificar log específico en el método
    stdout, stderr = run_docker_command(
        "grep -n 'Generando payload para artículo completo' /app/src/pipeline/pipeline_coordinator.py"
    )
    print("\n3. Log 'Generando payload para artículo completo':")
    if stdout:
        print(f"   ✅ Encontrado: {stdout.strip()}")
    else:
        print(f"   ❌ NO encontrado")
    
    # 4. Verificar la condición específica
    stdout, stderr = run_docker_command(
        "grep -A2 -B2 'articulo_original_preserved is not None and es_articulo_completo' /app/src/pipeline/pipeline_coordinator.py"
    )
    print("\n4. Condición de detección de artículo:")
    if stdout:
        print(f"   ✅ Encontrado:")
        for line in stdout.split('\n'):
            if line.strip():
                print(f"       {line}")
    else:
        print(f"   ❌ NO encontrado")

if __name__ == "__main__":
    check_code_changes()