#!/usr/bin/env python3
"""
CPMS Universal Verifier
Verifica que una tarea cumple con sus criterios de aceptación antes de marcarla como completada.

Uso: python check.py TASK-XXX
"""
import yaml
import subprocess
import sys
import os
from pathlib import Path

def load_tasks():
    """Carga las tareas desde tasks.yaml"""
    tasks_file = Path('tasks.yaml')
    if not tasks_file.exists():
        print("❌ Error: No se encuentra tasks.yaml")
        print("   Asegúrate de ejecutar este comando desde la raíz del proyecto CPMS")
        sys.exit(1)
    
    with open(tasks_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def find_task(task_id, tasks_data):
    """Busca una tarea específica por ID"""
    tasks = tasks_data.get('tasks', [])
    for task in tasks:
        if task.get('id') == task_id:
            return task
    return None

def print_criteria(criteria_text):
    """Imprime los criterios de aceptación formateados"""
    if not criteria_text:
        print("⚠️  No hay criterios de aceptación definidos")
        return
    
    lines = criteria_text.strip().split('\n')
    for line in lines:
        print(f"  {line}")

def run_verification_command(command):
    """Ejecuta el comando de verificación si existe"""
    if not command or command.strip() == "":
        return None
    
    print(f"\n🔧 Ejecutando verificación automática:")
    print(f"   {command}")
    print()
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=60  # Timeout de 60 segundos
        )
        
        if result.returncode == 0:
            print("✅ Verificación automática: PASÓ")
            if result.stdout:
                print(f"\n📋 Output:\n{result.stdout}")
        else:
            print("❌ Verificación automática: FALLÓ")
            if result.stderr:
                print(f"\n❌ Error:\n{result.stderr}")
            elif result.stdout:
                print(f"\n📋 Output:\n{result.stdout}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Verificación automática: TIMEOUT (60s)")
        return False
    except Exception as e:
        print(f"❌ Error ejecutando verificación: {e}")
        return False

def check_task(task_id):
    """Verifica si una tarea cumple con sus criterios de aceptación"""
    # Cargar tareas
    tasks_data = load_tasks()
    
    # Buscar tarea específica
    task = find_task(task_id, tasks_data)
    if not task:
        print(f"❌ Tarea {task_id} no encontrada")
        return False
    
    # Mostrar información de la tarea
    print(f"\n📋 Verificando: {task.get('title', 'Sin título')}")
    print(f"📊 Estado actual: {task.get('status', 'unknown')}")
    print("=" * 60)
    
    # Mostrar criterios de aceptación
    criteria = task.get('acceptance_criteria', '')
    print("\n✅ Criterios de aceptación:")
    print_criteria(criteria)
    
    if not criteria:
        print("\n⚠️  ADVERTENCIA: No hay criterios de aceptación definidos.")
        print("   Es altamente recomendable definir criterios claros antes de implementar.")
    
    # Ejecutar verificación automática si existe
    verification_result = None
    verification_cmd = task.get('verification_command')
    if verification_cmd:
        print("=" * 60)
        verification_result = run_verification_command(verification_cmd)
    
    # Solicitar confirmación manual
    print("=" * 60)
    print("\n❓ ¿Se cumplen TODOS los criterios de aceptación listados arriba?")
    print("   Responde solo después de verificar cada criterio cuidadosamente.")
    print("   (s/n): ", end='', flush=True)
    
    try:
        response = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n\n❌ Verificación cancelada")
        return False
    
    # Determinar resultado final
    manual_check = response == 's' or response == 'si' or response == 'sí'
    
    # Si hay verificación automática, ambas deben pasar
    if verification_cmd and verification_result is not None:
        success = manual_check and verification_result
        if manual_check and not verification_result:
            print("\n⚠️  La verificación manual pasó pero la automática falló.")
            print("   Ambas deben pasar para completar la tarea.")
    else:
        success = manual_check
    
    # Mostrar resultado final
    print("\n" + "=" * 60)
    if success:
        print("✅ TAREA VERIFICADA - Puede marcarse como completada")
        print("\n📝 Próximos pasos:")
        print("   1. Actualiza el status a 'completed' en tasks.yaml")
        print("   2. Documenta la verificación en el log de sesión")
        print("   3. Guarda los cambios")
    else:
        print("❌ TAREA NO VERIFICADA - Revisa los criterios pendientes")
        print("\n📝 Recomendaciones:")
        print("   1. Revisa qué criterios no se cumplen")
        print("   2. Completa la implementación faltante")
        print("   3. Vuelve a ejecutar la verificación")
    
    return success

def main():
    """Función principal"""
    if len(sys.argv) != 2:
        print("Uso: python check.py TASK-XXX")
        print("\nEjemplo:")
        print("  python check.py TASK-001")
        sys.exit(1)
    
    task_id = sys.argv[1]
    
    # Verificar que estamos en un proyecto CPMS
    if not Path('project.yaml').exists() or not Path('tasks.yaml').exists():
        print("❌ Error: No se encuentran los archivos project.yaml y tasks.yaml")
        print("   Este comando debe ejecutarse desde la raíz de un proyecto CPMS")
        sys.exit(1)
    
    # Ejecutar verificación
    success = check_task(task_id)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()