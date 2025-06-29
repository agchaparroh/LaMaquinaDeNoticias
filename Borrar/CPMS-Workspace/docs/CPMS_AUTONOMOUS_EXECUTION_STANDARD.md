# Estándar de Ejecución Autónoma CPMS
**Versión**: 1.0  
**Fecha**: 2024-12-27  
**Proyecto de Referencia**: SpiderFactoryCorrections

## 📋 Resumen Ejecutivo

Este documento establece el nuevo estándar para proyectos CPMS basado en las mejoras implementadas en SpiderFactoryCorrections. El objetivo es garantizar que cualquier proyecto CPMS pueda ejecutarse de forma completamente autónoma, sin intervención del usuario.

## 🎯 Principio Fundamental

> **"Si el desarrollador tiene que preguntar algo, el sistema CPMS falló"**

Todo proyecto CPMS debe ser auto-contenido, auto-explicativo y auto-ejecutable.

## 🔍 Problemas Identificados y Soluciones

### 1. Falta de Punto de Entrada Claro

**Problema**: El desarrollador no sabe cómo comenzar.

**Solución**: Agregar `workflow_instructions` en project.yaml:

```yaml
workflow_instructions:
  start_command: "Carga proyecto [NombreProyecto] desde CPMS-Workspace/projects"
  
  initial_setup:
    - "Verificar acceso a archivos del proyecto"
    - "Leer workflow.md para entender el proceso completo"
    - "Ejecutar TodoRead para ver el estado de las tareas"
  
  before_each_task:
    - "Cambiar task status de 'pending' a 'in_progress' en tasks.yaml"
    - "Leer completamente implementation_details de la tarea"
    - "Si indica, consultar documentación con Context7"
    
  after_each_task:
    - "Ejecutar el verification_command completo"
    - "Verificar que TODOS los acceptance_criteria se cumplan"
    - "Cambiar task status a 'completed'"
    - "Documentar problemas en problems_found si los hay"
```

### 2. Instrucciones Ambiguas para Herramientas

**Problema**: "Revisar documentación en Context7" - ¿Cómo exactamente?

**Solución**: Comandos explícitos paso a paso:

```yaml
implementation_details: |
  ANTES DE COMENZAR: Consultar documentación oficial de FastAPI:
  ```bash
  # Paso 1: Buscar el ID de la librería
  mcp__context7__resolve-library-id --libraryName "fastapi"
  # Paso 2: Con el ID obtenido (ej: /fastapi/fastapi), obtener docs
  mcp__context7__get-library-docs --context7CompatibleLibraryID "/fastapi/fastapi" --topic "websockets background-tasks"
  ```
```

### 3. Documentación Dispersa

**Problema**: Múltiples archivos con información crítica (DONT_FORGET.md, AUTONOMY_GUIDE.md, etc.)

**Solución**: Un único workflow.md consolidado que incluye:
- Proceso de trabajo completo
- Prohibiciones absolutas
- Reglas fundamentales
- Principios de autonomía
- Manejo de errores
- Checklist mental

### 4. Verificación No Adaptada al Entorno

**Problema**: Comandos que asumen capacidades que no existen (ej: cd en WSL)

**Solución**: Adaptar todos los comandos al entorno real:

```yaml
verification_command: |
  # ANTES (no funciona en Claude Code WSL):
  cd /ruta/al/proyecto && python -m py_compile src/models.py
  
  # DESPUÉS (funciona siempre):
  python3 -m py_compile /ruta/absoluta/al/proyecto/src/models.py
```

### 5. Falta de Contexto de Autonomía

**Problema**: El desarrollador espera confirmación para cada acción.

**Solución**: Principios de autonomía explícitos:

```markdown
## 🤖 Principios de Ejecución Autónoma

### ✅ HACER (Sin Pedir Permiso):
1. Modificar archivos según implementation_details
2. Ejecutar comandos de verificación
3. Crear/actualizar tests
4. Hacer commits con mensajes descriptivos
5. Documentar problemas en problems_found
6. Marcar tareas como completadas
7. Continuar con la siguiente tarea

### ❌ NO HACER:
1. NO preguntar "¿Debo continuar?"
2. NO pedir confirmación para cambios
3. NO detenerse por errores menores
4. NO esperar aprobación entre tareas
5. NO pedir clarificaciones al usuario
```

## 🛠️ Implementación en el Generador CPMS

### 1. Actualizar la Plantilla base de project.yaml

```yaml
# Agregar sección obligatoria:
workflow_instructions:
  start_command: "Carga proyecto {project_name} desde CPMS-Workspace/projects"
  initial_setup: [...]
  before_each_task: [...]
  during_implementation: [...]
  after_each_task: [...]
  verification_checklist: [...]
```

### 2. Crear Plantilla de workflow.md

Incluir secciones estándar:
- 🚀 Inicio Rápido
- 📋 Proceso de Trabajo por Tarea
- 🚫 Prohibiciones Absolutas
- ✅ Reglas Fundamentales
- 🤖 Principios de Ejecución Autónoma
- 🚨 Si Algo Falla
- 📋 Checklist Mental Constante

### 3. Mejorar Estructura de tasks.yaml

Cada tarea debe incluir:
```yaml
- id: "TASK-XXX"
  title: "Título descriptivo"
  description: "Qué lograr"
  implementation_details: |
    # Código exacto e instrucciones detalladas
    # Referencias a líneas específicas
    # Comandos exactos para Context7
  context7_queries:
    commands:
      - "mcp__context7__resolve-library-id --libraryName 'library'"
      - "mcp__context7__get-library-docs --context7CompatibleLibraryID '/org/lib'"
  verification_command: |
    # Comandos con rutas absolutas
    # Adaptados al entorno real
    # Con mensajes de éxito claros
```

### 4. Validación de Proyectos CPMS

Crear un validador que verifique:
- [ ] ¿Existe workflow_instructions en project.yaml?
- [ ] ¿Todas las tareas tienen implementation_details completos?
- [ ] ¿Los verification_commands usan rutas absolutas?
- [ ] ¿Existe workflow.md con todas las secciones requeridas?
- [ ] ¿Las referencias a herramientas incluyen comandos exactos?

## 📊 Métricas de Éxito

Un proyecto CPMS cumple el estándar si:

1. **Autonomía Total**: Se puede ejecutar con un solo comando inicial
2. **Cero Preguntas**: El desarrollador nunca necesita pedir clarificaciones
3. **Auto-Verificable**: Cada tarea puede validar su propia completitud
4. **Resiliente**: Maneja errores sin detenerse
5. **Trazable**: Documenta todas las decisiones y problemas

## 🚀 Próximos Pasos

1. **Actualizar el generador CPMS** con estas plantillas mejoradas
2. **Crear un linter CPMS** que valide proyectos contra este estándar
3. **Documentar casos de uso** para diferentes tipos de proyectos
4. **Establecer versionado** del estándar CPMS

## 📝 Ejemplo de Comando de Ejecución

```bash
# Un proyecto CPMS bien diseñado debe ejecutarse así:
"Completa el proyecto [NombreProyecto] de forma autónoma"

# Y Claude debe:
# 1. Cargar el proyecto
# 2. Ejecutar TODAS las tareas
# 3. Resolver TODOS los problemas
# 4. Completar TODO el trabajo
# 5. Reportar: "Proyecto completado. X tareas ejecutadas, Y problemas resueltos."
```

## 🔄 Ciclo de Mejora Continua

Este estándar debe evolucionar basándose en:
- Feedback de ejecución de proyectos
- Nuevas capacidades de herramientas
- Cambios en el entorno de ejecución
- Lecciones aprendidas de proyectos complejos

---

**Nota**: Este estándar se basa en la experiencia del proyecto SpiderFactoryCorrections y debe aplicarse a todos los futuros proyectos CPMS para garantizar ejecución autónoma y eficiente.