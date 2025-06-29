# Flujo de Trabajo CPMS - {project_name}

## 🚀 Inicio Rápido

Si acabas de recibir la instrucción de trabajar en este proyecto:

1. **Carga el proyecto**:
   ```
   "Carga proyecto {project_name} desde CPMS-Workspace/projects"
   ```

2. **Lee estos documentos** (en este orden):
   - Este archivo (workflow.md) - contiene todo lo necesario
   - tasks.yaml (especialmente architecture_critical_notes al final)

3. **Ubicación del código**:
   ```bash
   # NOTA: Claude Code no puede hacer cd fuera de su directorio
   # Usar rutas absolutas: {code_location}
   ```

## 📋 Proceso de Trabajo por Tarea

### 1️⃣ ANTES de Comenzar una Tarea

```yaml
# En tasks.yaml, cambiar:
status: "pending" → status: "in_progress"
```

**Verificar acceso a archivos**:
```bash
ls {code_location} | head -5
```

**Leer la tarea completa**:
- Leer `acceptance_criteria` para entender qué lograr
- Leer `implementation_details` que contiene TODO el código e instrucciones
- Si dice "ANTES DE COMENZAR: Consultar documentación de X", ejecutar los comandos indicados

### 2️⃣ DURANTE la Implementación

[Incluir instrucciones específicas del proyecto aquí]

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
"Completa el proyecto {project_name} de forma autónoma"
```

---

**REGLA FINAL**: Si tienes dudas, relee `implementation_details`. Todo está documentado. No improvises, y actúa con AUTONOMÍA.