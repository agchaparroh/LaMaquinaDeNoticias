# Mejoras a las Plantillas CPMS
**Basado en**: Proyecto SpiderFactoryCorrections  
**Fecha**: 2024-12-27

## 🎯 Objetivo

Aplicar las lecciones aprendidas del proyecto SpiderFactoryCorrections al sistema generador de plantillas CPMS para garantizar que todos los proyectos futuros sean autónomos por diseño.

## 📁 Archivos a Modificar

### 1. `/templates/project.yaml.template`

**Agregar nueva sección obligatoria**:

```yaml
# === NUEVA SECCIÓN: WORKFLOW INSTRUCTIONS ===
workflow_instructions:
  start_command: "Carga proyecto {{ project_name }} desde CPMS-Workspace/projects"
  
  initial_setup:
    - "# NOTA: Claude Code no puede hacer cd fuera del directorio de trabajo"
    - "# Todos los comandos usan rutas absolutas al código: {{ code_location }}"
    - "Verificar acceso a archivos del proyecto"
    - "ls {{ code_location }} | head -5  # Verificar acceso"
    - "Leer workflow.md para entender el proceso completo"
    - "Ejecutar TodoRead para ver el estado de las tareas"
  
  before_each_task:
    - "Cambiar task status de 'pending' a 'in_progress' en tasks.yaml"
    - "# NOTA: No hacer cd - usar rutas absolutas en todos los comandos"
    - "# Ejemplo: python3 {{ code_location }}/manage.py"
    - "Leer completamente implementation_details de la tarea"
    - "Si la tarea indica, usar Context7 para revisar documentación:"
    - "  1. mcp__context7__resolve-library-id --libraryName [biblioteca]"
    - "  2. mcp__context7__get-library-docs --context7CompatibleLibraryID [id]"
    - "Revisar architecture_critical_notes al final de tasks.yaml"
    
  during_implementation:
    - "Seguir las instrucciones exactas en implementation_details"
    - "NO modificar arquitectura base del proyecto"
    - "Mantener retrocompatibilidad con componentes existentes"
    - "Hacer commits frecuentes con conventional commits"
    
  after_each_task:
    - "Ejecutar el verification_command completo de la tarea"
    - "Verificar que TODOS los acceptance_criteria se cumplan"
    - "Marcar cada criterio completado con [x] en tasks.yaml"
    - "Cambiar task status a 'completed'"
    - "Documentar problemas encontrados en problems_found si los hay"
    - "Crear archivo de sesión en sessions/ documentando el trabajo"
    
  verification_checklist:
    - "[ ] Sintaxis correcta (python3 -m py_compile o equivalente)"
    - "[ ] Tests pasando"
    - "[ ] No se rompieron funcionalidades existentes"
    - "[ ] Logs sin errores críticos"
    - "[ ] Documentación actualizada si aplica"

# === NUEVA SECCIÓN: GETTING STARTED ===
getting_started: |
  Para comenzar a trabajar en este proyecto:
  
  1. Ejecuta: "Carga proyecto {{ project_name }} desde CPMS-Workspace/projects"
  2. Lee workflow.md para entender el proceso de trabajo
  3. Comienza con la primera tarea pendiente siguiendo workflow_instructions
  
  IMPORTANTE: Toda la información técnica está en implementation_details de cada tarea.
  No necesitas acceso a documentos externos.
  
  AUTONOMÍA: Este proyecto está diseñado para ejecutarse sin intervención del usuario.
  - NO pidas confirmación para realizar cambios
  - NO preguntes si debes continuar
  - SI encuentras errores, documenta en problems_found y continúa
  - SI algo no está claro, usa tu mejor criterio basado en implementation_details
  - EJECUTA cada tarea de principio a fin antes de pasar a la siguiente
```

### 2. `/templates/tasks.yaml.template`

**Mejorar estructura de tareas**:

```yaml
tasks:
  - id: "{{ task_id }}"
    title: "{{ task_title }}"
    description: "{{ task_description }}"
    priority: "{{ priority }}"
    status: "pending"
    estimated_hours: {{ hours }}
    assigned_to: null
    dependencies: {{ dependencies }}
    
    acceptance_criteria:
      - [ ] "{{ criterion_1 }}"
      - [ ] "{{ criterion_2 }}"
      # Criterios específicos y verificables
    
    implementation_details: |
      ANTES DE COMENZAR: Consultar documentación oficial de [biblioteca]:
      ```bash
      # Paso 1: Buscar el ID de la librería
      mcp__context7__resolve-library-id --libraryName "[biblioteca]"
      # Paso 2: Con el ID obtenido, obtener docs
      mcp__context7__get-library-docs --context7CompatibleLibraryID "[id]" --topic "[topics]"
      ```
      
      ### Sección 1: [Título]
      UBICACIÓN: {{ code_location }}/path/to/file.py (líneas ~XX-YY)
      
      CAMBIOS NECESARIOS:
      ```python
      # Código exacto a implementar
      ```
      
      NOTAS IMPORTANTES:
      - Mantener retrocompatibilidad con [componente]
      - Verificar que [condición]
    
    context7_queries:
      commands:
        - "mcp__context7__resolve-library-id --libraryName '[biblioteca]'"
        - "mcp__context7__get-library-docs --context7CompatibleLibraryID '[id]' --topic '[topics]'"
    
    verification_command: |
      # Verificación con rutas absolutas (compatible con WSL)
      echo "=== Verificando implementación de {{ task_title }} ==="
      
      # 1. Verificar sintaxis
      python3 -m py_compile {{ code_location }}/path/to/file.py
      echo "✓ Sintaxis correcta"
      
      # 2. Ejecutar tests específicos
      python3 -m pytest {{ code_location }}/tests/test_feature.py -v
      
      # 3. Verificación manual
      echo "MANUAL: Verificar que [condición específica]"
      
      # 4. Checklist
      echo "[ ] ¿Todos los criterios de aceptación cumplidos?"
      echo "[ ] ¿Tests pasando?"
      echo "[ ] ¿Sin errores en logs?"
    
    subtasks: []
    
    notes: |
      - Esta tarea es crítica para [razón]
      - Considerar [aspecto importante]
    
    problems_found: []
    
    # Sección para decisiones autónomas tomadas
    autonomous_decisions: []
```

### 3. Crear `/templates/workflow.md.template`

```markdown
# Flujo de Trabajo CPMS - {{ project_name }}

## 🚀 Inicio Rápido

Si acabas de recibir la instrucción de trabajar en este proyecto:

1. **Carga el proyecto**:
   ```
   "Carga proyecto {{ project_name }} desde CPMS-Workspace/projects"
   ```

2. **Lee estos documentos** (en este orden):
   - Este archivo (workflow.md) - contiene todo lo necesario
   - tasks.yaml (especialmente architecture_critical_notes al final)

3. **Ubicación del código**:
   ```bash
   # NOTA: Claude Code no puede hacer cd fuera de su directorio
   # Usar rutas absolutas: {{ code_location }}
   ```

## 📋 Proceso de Trabajo por Tarea

### 1️⃣ ANTES de Comenzar una Tarea

```yaml
# En tasks.yaml, cambiar:
status: "pending" → status: "in_progress"
```

**Verificar acceso a archivos**:
```bash
ls {{ code_location }} | head -5
```

**Leer la tarea completa**:
- Leer `acceptance_criteria` para entender qué lograr
- Leer `implementation_details` que contiene TODO el código e instrucciones
- Si dice "ANTES DE COMENZAR: Consultar documentación de X", ejecutar los comandos indicados

### 2️⃣ DURANTE la Implementación

## 🚫 PROHIBICIONES ABSOLUTAS

[Incluir prohibiciones específicas del proyecto]

## ✅ REGLAS FUNDAMENTALES

[Incluir reglas específicas del proyecto]

### 3️⃣ DESPUÉS de Implementar

## 🎯 VERIFICACIÓN ANTES DE MARCAR TAREA COMPLETADA

**NUNCA marques una tarea como completada sin:**

1. ✅ Ejecutar TODOS los comandos en `verification_command`
2. ✅ Verificar que TODOS los `acceptance_criteria` se cumplan
3. ✅ Probar que funcionalidades existentes siguen operativas
4. ✅ Verificar logs sin errores críticos
5. ✅ Documentar cualquier problema en `problems_found`

## 🤖 Principios de Ejecución Autónoma

Este proyecto está diseñado para ejecutarse **SIN intervención del usuario**.

### ✅ HACER (Sin Pedir Permiso):
1. **Modificar archivos** según implementation_details
2. **Ejecutar comandos** de verificación 
3. **Crear/actualizar tests**
4. **Hacer commits** con mensajes descriptivos
5. **Documentar problemas** en problems_found
6. **Marcar tareas** como completadas
7. **Continuar** con la siguiente tarea

### ❌ NO HACER:
1. **NO preguntar** "¿Debo continuar?"
2. **NO pedir confirmación** para cambios
3. **NO detenerse** por errores menores
4. **NO esperar** aprobación entre tareas
5. **NO pedir** clarificaciones al usuario

## 📊 Flujo de Decisión Autónoma

Cuando encuentres un error:
```yaml
# En tasks.yaml, agregar:
problems_found:
  - "Error X encontrado: solución aplicada Y"
  - "Dependencia faltante: instalada con pip install Z"
```
**Y CONTINUAR** con la implementación.

## 🚨 SI ALGO FALLA

[Incluir soluciones específicas a problemas comunes del proyecto]

## 📋 CHECKLIST MENTAL CONSTANTE

Antes de CADA acción, pregúntate:
- [ ] ¿Estoy siguiendo exactamente implementation_details?
- [ ] ¿Mantengo la compatibilidad con componentes existentes?
- [ ] ¿Mi código sigue las convenciones del proyecto?
- [ ] ¿Estoy documentando decisiones importantes?

## 🚀 Comando de Ejecución Autónoma

```
"Completa el proyecto {{ project_name }} de forma autónoma"
```

---

**REGLA FINAL**: Si tienes dudas, relee `implementation_details`. Todo está documentado. No improvises, y actúa con AUTONOMÍA.
```

## 🔧 Script de Validación CPMS

Crear `validate_cpms_project.py`:

```python
#!/usr/bin/env python3
"""
Validador de Proyectos CPMS
Verifica que un proyecto cumpla con el estándar de ejecución autónoma
"""

import yaml
import sys
from pathlib import Path

def validate_project(project_path):
    """Valida que un proyecto CPMS cumpla el estándar"""
    errors = []
    warnings = []
    
    # Verificar archivos requeridos
    required_files = ['project.yaml', 'tasks.yaml', 'workflow.md', 'knowledge.md']
    for file in required_files:
        if not (project_path / file).exists():
            errors.append(f"Archivo requerido faltante: {file}")
    
    # Validar project.yaml
    if (project_path / 'project.yaml').exists():
        with open(project_path / 'project.yaml', 'r') as f:
            project = yaml.safe_load(f)
            
        # Verificar secciones obligatorias
        if 'workflow_instructions' not in project:
            errors.append("project.yaml: falta sección 'workflow_instructions'")
        else:
            required_instructions = [
                'start_command', 'initial_setup', 'before_each_task',
                'during_implementation', 'after_each_task'
            ]
            for inst in required_instructions:
                if inst not in project['workflow_instructions']:
                    errors.append(f"workflow_instructions: falta '{inst}'")
        
        if 'getting_started' not in project:
            errors.append("project.yaml: falta sección 'getting_started'")
    
    # Validar tasks.yaml
    if (project_path / 'tasks.yaml').exists():
        with open(project_path / 'tasks.yaml', 'r') as f:
            tasks_data = yaml.safe_load(f)
            
        for task in tasks_data.get('tasks', []):
            task_id = task.get('id', 'SIN_ID')
            
            # Verificar campos obligatorios
            required_fields = [
                'implementation_details', 'verification_command',
                'acceptance_criteria'
            ]
            for field in required_fields:
                if field not in task or not task[field]:
                    errors.append(f"Tarea {task_id}: falta '{field}'")
            
            # Verificar rutas absolutas en verification_command
            if 'verification_command' in task:
                if 'cd ' in task['verification_command']:
                    warnings.append(f"Tarea {task_id}: usa 'cd' en verification_command")
                if 'python ' in task['verification_command']:
                    warnings.append(f"Tarea {task_id}: usa 'python' en lugar de 'python3'")
    
    # Mostrar resultados
    print(f"\n🔍 Validación de {project_path.name}")
    print("=" * 50)
    
    if errors:
        print(f"\n❌ ERRORES ({len(errors)}):")
        for error in errors:
            print(f"  • {error}")
    
    if warnings:
        print(f"\n⚠️  ADVERTENCIAS ({len(warnings)}):")
        for warning in warnings:
            print(f"  • {warning}")
    
    if not errors and not warnings:
        print("\n✅ El proyecto cumple con el estándar CPMS!")
    
    return len(errors) == 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python validate_cpms_project.py <ruta_al_proyecto>")
        sys.exit(1)
    
    project_path = Path(sys.argv[1])
    if not project_path.exists():
        print(f"Error: No se encuentra el directorio {project_path}")
        sys.exit(1)
    
    success = validate_project(project_path)
    sys.exit(0 if success else 1)
```

## 📝 Checklist de Implementación

- [ ] Actualizar `/templates/project.yaml.template` con workflow_instructions
- [ ] Actualizar `/templates/tasks.yaml.template` con nueva estructura
- [ ] Crear `/templates/workflow.md.template`
- [ ] Implementar `validate_cpms_project.py`
- [ ] Actualizar documentación del generador CPMS
- [ ] Crear ejemplos de proyectos usando el nuevo estándar
- [ ] Probar con un proyecto piloto

## 🎯 Resultado Esperado

Con estas mejoras, todos los proyectos CPMS generados serán:
- **Auto-ejecutables**: Un comando para completar todo
- **Auto-contenidos**: Toda la información necesaria incluida
- **Auto-verificables**: Cada tarea valida su propia completitud
- **Resilientes**: Manejan errores sin detenerse
- **Trazables**: Documentan todas las decisiones

---

*Estas mejoras garantizan que el sistema CPMS evolucione hacia un estándar de excelencia en automatización de proyectos.*