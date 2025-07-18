# 📋 Especificación Técnica Minimalista para PRP

> **Propósito**: Template esencial con SOLO la información técnica necesaria para generar un PRP preciso.
  *Anotación*: Un PRP (Product Requirements Prompt) es como ese "plan de construcción" pero para software.
>**Precauciones**: Evita alucinaciones. Rellena únicamente lo que conozcas con certeza

---

## 1. ¿Qué vamos a construir?

```markdown
### Nombre
[Nombre técnico del sistema/feature]

### Descripción funcional
[Qué hace en 3-5 líneas. Solo comportamiento observable]

### Problema técnico que resuelve
[El problema desde perspectiva de ingeniería]
```

---

## 2. Funcionalidades

```markdown
### Qué SÍ incluye
1. [Funcionalidad 1 - descripción técnica]
2. [Funcionalidad 2 - descripción técnica]
3. [Funcionalidad 3 - descripción técnica]

### Qué NO incluye
- [Cosa que NO haremos - razón técnica]
- [Otra cosa que NO haremos - razón técnica]
```

---

## 3. Casos de uso técnicos

```markdown
### Caso 1: [Nombre]
Input: [Qué entra al sistema]
Proceso: [Qué debe hacer]
Output: [Qué debe salir]
Validación: [Cómo verificar que funciona]

### Caso 2: [Nombre]
Input: [...]
Proceso: [...]
Output: [...]
Validación: [...]
```

---

## 4. Arquitectura y contexto técnico

```markdown
### Stack actual
- Frontend: [React 18.2, TypeScript 5.0]
- Backend: [Node.js 20, Express 4.18]
- Database: [PostgreSQL 15]
- Infra: [Docker, AWS]

### Integraciones necesarias
| Sistema | Tipo | Para qué |
|---------|------|----------|
| [API X] | REST | [Obtener datos Y] |
| [Service Z] | gRPC | [Procesar W] |

### Archivos/módulos que se modificarán
- src/controllers/[...]
- src/services/[...]
- src/models/[...]

### Restricciones técnicas importantes
- [Debe ser compatible con X]
- [No puede modificar Y]
- [Debe respetar límite Z]
```

---

## 5. Requisitos técnicos

```markdown
### Performance
- Latencia: <[X]ms
- Throughput: >[Y] ops/sec
- Memoria: <[Z]MB

### Escalabilidad
- Usuarios concurrentes: [número]
- Volumen datos: [GB/día]

### Seguridad
- Autenticación: [método]
- Autorización: [modelo]
- Datos sensibles: [cuáles y cómo proteger]
```

---

## 6. Criterios de aceptación técnicos

```markdown
### Tests requeridos
- [ ] Unit tests con coverage >80%
- [ ] Integration tests de APIs
- [ ] E2E del flujo principal

### Validaciones
- [ ] [Comportamiento específico a validar]
- [ ] [Métrica específica a cumplir]
- [ ] [Integración específica funcionando]

### Definition of Done
- [ ] Code review aprobado
- [ ] Tests pasando
- [ ] Sin vulnerabilidades críticas
- [ ] Documentación técnica actualizada
```

---

## 7. Información adicional relevante

```markdown
### Ejemplos de input/output
```json
// Input ejemplo
{
  "field1": "value1",
  "field2": 123
}

// Output esperado
{
  "result": "processed",
  "data": {...}
}
```

### Errores a manejar
- [Error 1]: [Cómo manejarlo]
- [Error 2]: [Cómo manejarlo]

### Notas técnicas
- [Consideración importante 1]
- [Gotcha conocido 2]
```

---

## ✅ Checklist pre-PRP

**¿El documento describe claramente?**
- [ ] QUÉ debe hacer el sistema (no CÓMO)
- [ ] Casos de uso con inputs/outputs concretos
- [ ] Stack técnico y restricciones
- [ ] Criterios objetivos de validación
- [ ] Archivos/módulos afectados

**¿El documento EVITA?**
- [ ] Detalles de implementación
- [ ] Justificaciones de negocio
- [ ] Información de stakeholders
- [ ] Timelines y presupuestos
- [ ] Historias de usuario narrativas

---

*Template Minimalista v2.0 - Solo información técnica relevante para PRP*