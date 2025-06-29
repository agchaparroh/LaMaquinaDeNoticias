# CPMS Changelog

## [2.0.0] - 2025-06-28

### 🚀 Mejoras Implementadas

#### Templates Actualizados
- **project.yaml**: Agregada sección `workflow_instructions` con instrucciones detalladas para cada fase del trabajo
- **tasks.yaml**: Nueva estructura con `implementation_details`, `context7_queries`, y `verification_command` obligatorios
- **workflow.md**: Nueva plantilla con secciones para autonomía, prohibiciones, y flujo de trabajo
- **check.py**: Actualizado para trabajar desde el directorio raíz del proyecto

#### Nuevas Funcionalidades
- **validate_cpms_project.py**: Validador que verifica el cumplimiento del estándar CPMS
- **CLAUDE.md**: Actualizado con principios de ejecución autónoma y comandos autorizados

#### Documentación
- Integradas las mejoras del estándar de ejecución autónoma
- Templates ahora incluyen instrucciones explícitas para Claude Code
- Enfoque en proyectos auto-ejecutables sin intervención del usuario

### 📋 Cambios Principales

1. **Autonomía Total**: Los proyectos ahora pueden ejecutarse con un solo comando
2. **Verificación Integrada**: Cada tarea incluye comandos de verificación específicos
3. **Context7 Integration**: Instrucciones explícitas para consultar documentación
4. **Rutas Absolutas**: Compatibilidad con restricciones de WSL/Claude Code
5. **Validación Automática**: Script para verificar proyectos antes de ejecución

### 🔧 Uso

Para crear un nuevo proyecto con el estándar actualizado:
1. Copiar los archivos de `/templates/` al nuevo proyecto
2. Completar los campos marcados con `{placeholder}`
3. Ejecutar `python validate_cpms_project.py projects/[nombre]`
4. Corregir cualquier error antes de comenzar el desarrollo

### 📝 Notas

- Los proyectos existentes (SpiderFactory2.0) necesitarán actualización para cumplir el nuevo estándar
- SpiderFactoryCorrections ya implementa parcialmente estas mejoras
- El validador ayuda a identificar qué cambios son necesarios