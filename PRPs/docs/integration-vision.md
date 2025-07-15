# Visión: Integración PRP-SuperClaude con Comandos Explícitos

## Resumen Ejecutivo

Este documento describe la visión para una integración profunda entre el sistema PRP (Product Requirements Prompt) y SuperClaude, donde cada PRP generado especifica explícitamente qué comandos SuperClaude usar, con qué persona, y la ejecución es absolutamente fiel al plan detallado.

## Principios Fundamentales

### 1. Especificidad Total
- Cada tarea en un PRP debe especificar el comando SuperClaude exacto
- No hay ambigüedad sobre qué herramienta usar
- Los parámetros y flags están predefinidos

### 2. Obediencia Absoluta
- Claude ejecuta exactamente lo que dice el PRP
- No toma decisiones autónomas sobre herramientas
- Respeta la secuencia y dependencias tal cual

### 3. Determinismo
- El mismo PRP produce el mismo resultado
- Ejecución predecible y repetible
- Sin variaciones basadas en interpretación

## Generación de PRPs (`/generate-prp`)

### Comportamiento Esperado

Cuando se ejecuta `/generate-prp [feature]`, el sistema debe:

1. **Analizar la feature** y descomponerla en tareas
2. **Mapear cada tarea** a un comando SuperClaude específico
3. **Asignar la persona** más apropiada para cada comando
4. **Incluir validaciones** ejecutables

### Mapeo de Tareas a Comandos

```yaml
Análisis → /analyze --architecture --code --dependencies
Diseño → /design --api|--frontend|--system --patterns
Implementación → /build --[tipo] --tdd --uc
Testing → /test --unit|--integration|--e2e --coverage
Seguridad → /scan --security --owasp --strict
Optimización → /improve --performance|--refactor
Documentación → /document --api|--user --examples
```

### Formato de Tarea Generada

```yaml
Task N: [Descripción clara de la tarea]
  Priority: high|medium|low
  Dependencies: [Task M, Task L]
  SuperClaude Command: /[comando] --[flags] [argumentos]
  Persona: --persona-[tipo]
  Files:
    - CREATE: [archivos a crear]
    - MODIFY: [archivos a modificar]
  Validation:
    - [comando de validación 1]
    - [comando de validación 2]
  Expected Output: [qué debe producir esta tarea]
  Success Criteria: [cómo saber que está completa]
```

## Ejecución de PRPs (`/execute-prp`)

### Comportamiento de Ejecución

Cuando se ejecuta `/execute-prp [archivo-prp]`, Claude debe:

1. **Cargar el PRP** completo con todo su contexto
2. **Ejecutar cada tarea** en orden, respetando dependencias
3. **Usar EXACTAMENTE** el comando SuperClaude especificado
4. **Adoptar la persona** indicada para cada comando
5. **Validar** después de cada tarea según lo especificado
6. **No desviarse** del plan bajo ninguna circunstancia

### Flujo de Ejecución

```
Cargar PRP
    ↓
Para cada Tarea:
    ├─ Verificar dependencias completadas
    ├─ Ejecutar comando SuperClaude especificado
    ├─ Con la persona indicada
    ├─ Con los flags exactos
    ├─ Ejecutar validaciones
    └─ Marcar como completada si pasa
```

### Sin Decisiones Autónomas

❌ **NO HACER**:
- "Veo que necesito analizar, usaré /analyze"
- "Creo que /build sería mejor aquí"
- "Voy a agregar --think-hard para mejor resultado"

✅ **HACER**:
- Ejecutar: `/analyze --architecture --code src/` (porque el PRP lo especifica)
- Usar persona: `--persona-architect` (porque el PRP lo indica)
- Validar con: `pytest tests/` (porque el PRP lo requiere)

## Ejemplo Concreto

### Input para generate-prp:
```bash
/generate-prp "Sistema de autenticación OAuth 2.0"
```

### Output del PRP (fragmento):
```yaml
Task 1: Analizar sistema de autenticación actual
  Priority: high
  SuperClaude Command: /analyze --architecture --code --dependencies src/auth/
  Persona: --persona-analyzer
  Expected Output: Reporte de arquitectura actual en .claudedocs/analysis/
  Validation: 
    - Verificar que existe .claudedocs/analysis/auth-analysis.md

Task 2: Diseñar nueva arquitectura OAuth
  Priority: high
  Dependencies: Task 1
  SuperClaude Command: /design --api --oauth --patterns --think-hard
  Persona: --persona-architect
  Deliverable: docs/design/oauth-architecture.md
  Validation:
    - Archivo docs/design/oauth-architecture.md existe
    - Incluye diagrama de flujo OAuth

Task 3: Implementar configuración OAuth
  Priority: high
  Dependencies: Task 2
  SuperClaude Command: /build --config --oauth-providers --tdd
  Persona: --persona-backend
  Files:
    - CREATE: src/config/oauth.js
    - CREATE: src/config/providers/google.js
    - MODIFY: .env.example
  Validation:
    - npm test src/config/oauth.test.js
    - Configuración carga sin errores

[... más tareas con comandos específicos ...]
```

### Ejecución:
```bash
/execute-prp PRPs/oauth-authentication.md
```

Claude ejecutará:
1. Exactamente `/analyze --architecture --code --dependencies src/auth/` con `--persona-analyzer`
2. Luego `/design --api --oauth --patterns --think-hard` con `--persona-architect`
3. Y así sucesivamente, sin desviarse

## Beneficios de Este Enfoque

### 1. Predictibilidad Total
- Sabes exactamente qué comandos se ejecutarán
- Puedes revisar y ajustar antes de ejecutar
- Sin sorpresas durante la ejecución

### 2. Aprovechamiento Completo de SuperClaude
- Usa los 19 comandos especializados
- Aplica las 9 personas cognitivas
- Maximiza las capacidades del framework

### 3. Trazabilidad y Auditoría
- Cada acción está documentada
- Fácil debugging si algo falla
- Historial claro de qué se ejecutó

### 4. Repetibilidad
- El mismo PRP genera los mismos resultados
- Ideal para CI/CD y automatización
- Reduce variabilidad entre ejecuciones

### 5. Control Granular
- Ajusta comandos específicos sin rehacer todo
- Cambia personas para diferentes perspectivas
- Modifica flags para optimización

## Implementación Técnica Requerida

### 1. Modificar generate-prp.md
- Agregar lógica de mapeo tarea→comando
- Incluir asignación automática de personas
- Generar formato con comandos explícitos

### 2. Modificar execute-prp.md
- Cambiar a ejecución literal de comandos
- Eliminar toma de decisiones
- Agregar adopción de personas

### 3. Actualizar Templates
- Incluir sección de SuperClaude Command en cada tarea
- Agregar campo Persona obligatorio
- Ejemplos con comandos reales

### 4. Crear Mapeos en prp-patterns.yml
- Tabla de tipo de tarea → comando SuperClaude
- Reglas de asignación de personas
- Flags comunes por tipo de operación

## Conclusión

Esta visión transforma los PRPs de especificaciones genéricas a planes de ejecución deterministas que aprovechan completamente el poder de SuperClaude. La clave está en la especificidad de los comandos y la obediencia absoluta durante la ejecución, creando un sistema predecible, potente y profesional.

---

*Documento de Visión v1.0 - Integración PRP-SuperClaude con Comandos Explícitos*