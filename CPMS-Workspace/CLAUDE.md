# CPMS Workspace

## Para cargar proyecto:
"Carga proyecto {nombre} desde C:/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/CPMS-Workspace/projects"

## Para crear proyecto:
"Crea nuevo proyecto CPMS llamado {nombre}"

## Proyectos disponibles:
- SpiderFactory2.0 (en revisión)

## 🔴 REGLA FUNDAMENTAL: Verificación de Tareas

ANTES de marcar cualquier tarea como completada:
1. Ejecuta: `python .claude/check.py TASK-XXX`
2. NO marques como completada sin verificación exitosa
3. Documenta el resultado en el log de sesión

Si los criterios de aceptación no son claros, PREGUNTA antes de implementar.

## Autonomía Autorizada
Tienes permiso para ejecutar SIN PEDIR CONFIRMACIÓN:
- Todos los comandos de testing (pytest, npm test)
- Formateo y linting (black, eslint, flake8)
- Git (status, diff, add, commit) - NO push
- Lectura de archivos y navegación
- Script de verificación (.claude/check.py)

Tu objetivo es completar las tareas correctamente, verificando el cumplimiento de los criterios de aceptación.