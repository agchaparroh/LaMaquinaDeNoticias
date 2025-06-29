# CPMS Workspace - Sistema de Gestión de Proyectos

## 🚀 Inicio Rápido

### Para cargar proyecto:
```
"Carga proyecto {nombre} desde C:/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/CPMS-Workspace/projects"
```

### Para crear proyecto:
```
"Crea nuevo proyecto CPMS llamado {nombre}"
```

## 📂 Proyectos disponibles:
- SpiderFactory2.0 (planning)
- SpiderFactoryCorrections (development)

## 🔴 REGLA FUNDAMENTAL: Verificación de Tareas

ANTES de marcar cualquier tarea como completada:
1. Ejecuta: `python check.py TASK-XXX` (desde el directorio del proyecto)
2. Verificar que TODOS los acceptance_criteria se cumplan
3. NO marques como completada sin verificación exitosa
4. Documenta el resultado en el log de sesión

## 🤖 Principios de Ejecución Autónoma

Este sistema está diseñado para ejecutarse **SIN intervención del usuario**.

### ✅ HACER (Sin Pedir Permiso):
1. **Modificar archivos** según implementation_details
2. **Ejecutar comandos** de verificación y testing
3. **Crear/actualizar tests**
4. **Hacer commits** con mensajes descriptivos (conventional commits)
5. **Documentar problemas** en problems_found
6. **Marcar tareas** como completadas tras verificación
7. **Continuar** con la siguiente tarea automáticamente
8. **Usar Context7** para consultar documentación cuando se indique
9. **Tomar decisiones** basadas en best practices cuando no esté especificado

### ❌ NO HACER:
1. **NO preguntar** "¿Debo continuar?"
2. **NO pedir confirmación** para cambios de código
3. **NO detenerse** por errores menores (documentar y continuar)
4. **NO esperar** aprobación entre tareas
5. **NO pedir** clarificaciones al usuario
6. **NO hacer push** sin autorización explícita
7. **NO modificar** arquitectura base sin instrucciones específicas

## 🎯 Flujo de Trabajo Autónomo

1. **Al iniciar**: Leer project.yaml → workflow.md → tasks.yaml
2. **Por tarea**: 
   - Cambiar status a "in_progress"
   - Leer implementation_details completo
   - Ejecutar comandos Context7 si se indican
   - Implementar siguiendo instrucciones exactas
   - Ejecutar verification_command
   - Marcar como "completed" si pasa verificación
3. **Al finalizar**: Reportar resumen de tareas completadas

## 🛠️ Comandos Autorizados (Ejecutar Sin Confirmación)

### Testing y Verificación:
- `pytest` (cualquier variación)
- `python -m pytest`
- `npm test`
- `python check.py TASK-XXX`
- `python3 -m py_compile [archivo]`

### Formateo y Calidad:
- `black` (cualquier archivo o directorio)
- `flake8`
- `mypy`
- `eslint`
- `prettier`

### Git (NO push):
- `git status`
- `git diff`
- `git add`
- `git commit -m "[mensaje]"`
- `git log`

### Navegación y Lectura:
- `ls`, `cat`, `grep`, `find`
- Lectura de cualquier archivo del proyecto
- `docker-compose logs`

### Context7 (Documentación):
- `mcp__context7__resolve-library-id`
- `mcp__context7__get-library-docs`

## 📊 Manejo de Errores

Cuando encuentres un error:
1. Documentar en `problems_found` de la tarea
2. Intentar solución basada en experiencia
3. Si es crítico y bloquea la tarea, documentar y continuar con la siguiente
4. NUNCA detenerse a esperar intervención

## 🎯 Objetivo Final

Tu objetivo es completar TODAS las tareas del proyecto de forma autónoma, verificando el cumplimiento de los criterios de aceptación y manteniendo la calidad del código.

---

**RECUERDA**: La autonomía es la clave. Si está documentado en implementation_details, ejecútalo. Si necesitas tomar una decisión técnica menor, usa tu mejor criterio basado en las convenciones del proyecto.