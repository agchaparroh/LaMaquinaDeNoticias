#!/usr/bin/env python3
"""
Validador de Proyectos CPMS
Verifica que un proyecto cumpla con el estándar de ejecución autónoma

Uso: python validate_cpms_project.py <ruta_al_proyecto>
"""

import yaml
import sys
from pathlib import Path
from typing import List, Tuple

def validate_project(project_path: Path) -> bool:
    """Valida que un proyecto CPMS cumpla el estándar"""
    errors: List[str] = []
    warnings: List[str] = []
    
    # Verificar archivos requeridos
    required_files = ['project.yaml', 'tasks.yaml', 'workflow.md', 'knowledge.md']
    for file in required_files:
        if not (project_path / file).exists():
            errors.append(f"Archivo requerido faltante: {file}")
    
    # Validar project.yaml
    if (project_path / 'project.yaml').exists():
        try:
            with open(project_path / 'project.yaml', 'r', encoding='utf-8') as f:
                project = yaml.safe_load(f)
                
            # Verificar secciones obligatorias
            if 'workflow_instructions' not in project:
                errors.append("project.yaml: falta sección 'workflow_instructions'")
            else:
                required_instructions = [
                    'start_command', 'initial_setup', 'before_each_task',
                    'during_implementation', 'after_each_task', 'verification_checklist'
                ]
                for inst in required_instructions:
                    if inst not in project['workflow_instructions']:
                        errors.append(f"workflow_instructions: falta '{inst}'")
            
            if 'getting_started' not in project:
                errors.append("project.yaml: falta sección 'getting_started'")
                
            if 'code_location' not in project or not project['code_location']:
                errors.append("project.yaml: falta 'code_location' (obligatorio)")
                
        except yaml.YAMLError as e:
            errors.append(f"Error parseando project.yaml: {e}")
        except Exception as e:
            errors.append(f"Error leyendo project.yaml: {e}")
    
    # Validar tasks.yaml
    if (project_path / 'tasks.yaml').exists():
        try:
            with open(project_path / 'tasks.yaml', 'r', encoding='utf-8') as f:
                tasks_data = yaml.safe_load(f)
                
            if 'tasks' not in tasks_data:
                errors.append("tasks.yaml: falta sección 'tasks'")
            else:
                for i, task in enumerate(tasks_data.get('tasks', [])):
                    task_id = task.get('id', f'Tarea_{i}')
                    
                    # Verificar campos obligatorios
                    required_fields = [
                        'implementation_details', 'verification_command',
                        'acceptance_criteria'
                    ]
                    for field in required_fields:
                        if field not in task or not task[field]:
                            errors.append(f"Tarea {task_id}: falta campo obligatorio '{field}'")
                    
                    # Verificar rutas absolutas en verification_command
                    if 'verification_command' in task and task['verification_command']:
                        if 'cd ' in str(task['verification_command']):
                            warnings.append(f"Tarea {task_id}: usa 'cd' en verification_command (usar rutas absolutas)")
                        if 'python ' in str(task['verification_command']) and 'python3' not in str(task['verification_command']):
                            warnings.append(f"Tarea {task_id}: usa 'python' en lugar de 'python3'")
                    
                    # Verificar que implementation_details tenga contenido útil
                    if 'implementation_details' in task:
                        details = str(task['implementation_details'])
                        if len(details) < 50:
                            warnings.append(f"Tarea {task_id}: implementation_details muy corto ({len(details)} chars)")
                        if 'UBICACIÓN:' not in details and 'path' not in details.lower():
                            warnings.append(f"Tarea {task_id}: implementation_details no especifica ubicación de archivos")
                            
            # Verificar architecture_critical_notes
            if 'architecture_critical_notes' not in tasks_data:
                warnings.append("tasks.yaml: falta 'architecture_critical_notes' al final")
                
        except yaml.YAMLError as e:
            errors.append(f"Error parseando tasks.yaml: {e}")
        except Exception as e:
            errors.append(f"Error leyendo tasks.yaml: {e}")
    
    # Validar workflow.md
    if (project_path / 'workflow.md').exists():
        try:
            with open(project_path / 'workflow.md', 'r', encoding='utf-8') as f:
                workflow_content = f.read()
                
            # Verificar secciones requeridas
            required_sections = [
                '## 🚀 Inicio Rápido',
                '## 📋 Proceso de Trabajo',
                '## 🚫 PROHIBICIONES ABSOLUTAS',
                '## ✅ REGLAS FUNDAMENTALES',
                '## 🤖 Principios de Ejecución Autónoma',
                '## 🚨 SI ALGO FALLA',
                '## 📋 CHECKLIST MENTAL'
            ]
            
            for section in required_sections:
                if section not in workflow_content:
                    warnings.append(f"workflow.md: falta sección '{section}'")
                    
        except Exception as e:
            errors.append(f"Error leyendo workflow.md: {e}")
    
    # Verificar estructura de sesiones
    sessions_dir = project_path / 'sessions'
    if not sessions_dir.exists():
        warnings.append("Falta directorio 'sessions/' para logs de sesión")
    
    # Mostrar resultados
    print(f"\n🔍 Validación de {project_path.name}")
    print("=" * 60)
    
    if errors:
        print(f"\n❌ ERRORES ({len(errors)}):")
        for error in errors:
            print(f"  • {error}")
    
    if warnings:
        print(f"\n⚠️  ADVERTENCIAS ({len(warnings)}):")
        for warning in warnings:
            print(f"  • {warning}")
    
    if not errors and not warnings:
        print("\n✅ El proyecto cumple completamente con el estándar CPMS!")
    elif not errors:
        print("\n✅ El proyecto cumple con los requisitos mínimos CPMS")
        print("   (revisa las advertencias para mejorar)")
    
    # Mostrar estadísticas
    if (project_path / 'tasks.yaml').exists():
        try:
            with open(project_path / 'tasks.yaml', 'r', encoding='utf-8') as f:
                tasks_data = yaml.safe_load(f)
                tasks = tasks_data.get('tasks', [])
                
            if tasks:
                print(f"\n📊 Estadísticas:")
                print(f"  • Total de tareas: {len(tasks)}")
                
                statuses = {}
                for task in tasks:
                    status = task.get('status', 'unknown')
                    statuses[status] = statuses.get(status, 0) + 1
                
                for status, count in statuses.items():
                    print(f"  • {status}: {count}")
                    
        except:
            pass
    
    return len(errors) == 0

def main():
    """Función principal"""
    if len(sys.argv) != 2:
        print("Uso: python validate_cpms_project.py <ruta_al_proyecto>")
        print("\nEjemplo:")
        print("  python validate_cpms_project.py projects/mi-proyecto")
        sys.exit(1)
    
    project_path = Path(sys.argv[1])
    if not project_path.exists():
        print(f"❌ Error: No se encuentra el directorio {project_path}")
        sys.exit(1)
    
    if not project_path.is_dir():
        print(f"❌ Error: {project_path} no es un directorio")
        sys.exit(1)
    
    success = validate_project(project_path)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Validación exitosa")
    else:
        print("❌ Validación fallida - corrige los errores antes de continuar")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()