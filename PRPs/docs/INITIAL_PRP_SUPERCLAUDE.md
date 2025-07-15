## FEATURE:

Integrar selectivamente el sistema de PRPs (Product Requirements Prompts) de Context Engineering en SuperClaude v2.0.1, creando un "Modo PRP" que se activa solo para features complejas mientras mantiene la simplicidad de SuperClaude para tareas rápidas.

El objetivo es obtener lo mejor de ambos mundos:
- Velocidad y simplicidad de SuperClaude para tareas cotidianas
- Poder y exhaustividad de PRPs para proyectos complejos
- Reutilización de componentes existentes (personas, flags, optimización)
- Una sola interfaz coherente sin duplicación

## EXAMPLES:

En la carpeta `ContextEngineering/context-engineering-intro/` están todos los ejemplos necesarios:

- `PRPs/templates/prp_base.md` - Template base de PRP para adaptar a SuperClaude
- `PRPs/EXAMPLE_multi_agent_prp.md` - Ejemplo completo de PRP generado
- `.claude/commands/generate-prp.md` - Comando de generación de Context Engineering
- `.claude/commands/execute-prp.md` - Comando de ejecución de Context Engineering
- `INITIAL.md` y `INITIAL_EXAMPLE.md` - Plantillas para solicitud de features

En la carpeta `.claude/` del proyecto están los componentes de SuperClaude:
- `commands/` - Los 19 comandos existentes y su estructura
- `shared/` - Archivos YAML compartidos con patrones
- `commands/task.md` - Sistema de tareas actual para integrar

## DOCUMENTATION:

Referencias clave para la implementación:

1. **SuperClaude v2.0.1**:
   - `README.md` en `ContextEngineering/SuperClaude/` - Arquitectura y diseño
   - `COMMANDS.md` - Referencia completa de comandos y flags
   - Sistema @include para templates y reducción de duplicación

2. **Context Engineering**:
   - `README.md` en `context-engineering-intro/` - Filosofía y flujo PRP
   - Principios: Context is King, Validation Loops, Information Dense
   - Flujo: INITIAL → generate-prp → execute-prp

3. **Integración propuesta**:
   - Crear comando `/prp` con suboperaciones (init, generate, execute, status, exit)
   - PRPs como "Level 0" en jerarquía de task management
   - Reutilizar personas (`--persona-*`) en generación de PRPs
   - Aplicar flags de optimización (`--uc`, `--think-hard`) a PRPs

## OTHER CONSIDERATIONS:

**Decisiones de diseño críticas**:

1. **No duplicar funcionalidad** - El comando `/prp` debe integrarse naturalmente con los comandos existentes, no reemplazarlos.

2. **Triggers automáticos claros**:
   - < 3 archivos nuevos → SuperClaude directo
   - ≥ 3 archivos nuevos → Sugerir modo PRP
   - Features multi-sistema → Requerir PRP

3. **Mantener filosofía KISS/YAGNI** - Solo activar complejidad de PRPs cuando realmente agregue valor.

4. **Preservar velocidad** - El 80% de tareas deben seguir siendo rápidas con comandos directos.

5. **Templates modulares** - Crear templates de PRP específicos para casos comunes:
   - `prp_api.md` - Para backends/APIs
   - `prp_frontend.md` - Para interfaces React
   - `prp_fullstack.md` - Para features completas
   - `prp_integration.md` - Para integraciones externas

6. **Sincronización con TodoWrite** - Los PRPs deben generar automáticamente todos en TodoWrite para tracking en tiempo real.

7. **Validación integrada** - Reutilizar sistema de validación de SuperClaude en los validation loops de PRPs.

8. **Documentación automática** - Al completar un PRP, generar documentación con `/document`.

**Gotchas a evitar**:
- No hacer PRPs obligatorios para todo
- No romper flujos existentes de SuperClaude
- No crear complejidad innecesaria
- Mantener la curva de aprendizaje suave