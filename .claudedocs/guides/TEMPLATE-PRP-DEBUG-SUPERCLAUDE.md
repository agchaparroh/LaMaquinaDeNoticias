# 🚨 Template PRP-Debug con SuperClaude v2.0
## Sistema Avanzado de Resolución de Problemas

### 📋 INFORMACIÓN DEL TEMPLATE
- **Versión**: 2.0.0
- **Fecha**: 2025-01-19
- **Propósito**: Template base para debugging sistemático y exhaustivo
- **Integración**: Comandos reales + TodoWrite + Documentación completa

---

## ✅ CRITERIOS DE ÉXITO DEL DEBUGGING

### Criterios Obligatorios
1. **Error Resuelto**: El error original no se reproduce bajo las mismas condiciones
2. **Sin Regresiones**: No se han introducido nuevos errores
3. **Documentación Completa**: Todas las fases tienen su archivo correspondiente
4. **Hipótesis Confirmada**: Al menos una hipótesis fue verificada y confirmada
5. **Validación Exhaustiva**: Todas las pruebas de validación pasaron

### Criterios de Calidad
1. **Diagnóstico Completo**: Se analizaron todas las dimensiones relevantes
2. **Múltiples Hipótesis**: Se generaron al menos 3 hipótesis verificables
3. **Trazabilidad**: Cada decisión está documentada con evidencia
4. **Reproducibilidad**: Otro desarrollador puede seguir el proceso documentado
5. **Prevención**: Se identificaron medidas para prevenir recurrencia

### Métricas de Éxito
- **Tiempo de Resolución**: Documentado desde detección hasta validación
- **Intentos de Solución**: Número de hipótesis verificadas antes del éxito
- **Calidad de Documentación**: 7 archivos mínimo en carpeta de debugging
- **Lecciones Aprendidas**: Al menos 3 lecciones documentadas

---

## 🎯 ESTRUCTURA DE DOCUMENTACIÓN SISTEMÁTICA

```yaml
# ESTRUCTURA OBLIGATORIA PARA CADA SESIÓN DE DEBUG
Estructura_Documentación:
  base_path: .claudedocs/debugging/
  
  carpeta_sesión: "[ERROR-YYYYMMDD-HHMM]/"
  
  archivos_requeridos:
    - "00-PRP-ACTIVO.md"          # Este template en ejecución
    - "01-captura-inicial.md"      # Datos crudos del error
    - "02-analisis-completo.md"    # Análisis multi-dimensional
    - "03-hipotesis.md"            # Todas las hipótesis generadas
    - "04-verificacion-[X].md"     # Una por cada hipótesis verificada
    - "05-solucion.md"             # Solución implementada
    - "06-validacion.md"           # Resultados de validación
    - "07-lecciones.md"            # Post-mortem y aprendizajes
```

---

## 📋 SISTEMA DE TAREAS CON TODOWRITE

```markdown
# CREAR AL INICIO DEL DEBUGGING

Task Principal: "DEBUG: [descripción-error] - Seguir PRP en .claudedocs/debugging/[ERROR-ID]/00-PRP-ACTIVO.md"

Subtasks automáticas:
1. "Fase 1: Captura completa → Ver PRP sección FASE-1"
2. "Fase 2: Análisis sistemático → Ver PRP sección FASE-2"
3. "Fase 3: Generar hipótesis → Ver PRP sección FASE-3"
4. "Fase 4: Verificar cada hipótesis → Ver PRP sección FASE-4"
5. "Fase 5: Implementar solución → Ver PRP sección FASE-5"
6. "Fase 6: Validar exhaustivamente → Ver PRP sección FASE-6"
7. "Fase 7: Documentar lecciones → Ver PRP sección FASE-7"

IMPORTANTE: Cada task DEBE referenciar la sección específica del PRP activo
```

---

# 🚨 PRP-DEBUG ACTIVO: [Nombre descriptivo del error]

## 📍 INFORMACIÓN VITAL
- **Carpeta de trabajo**: .claudedocs/debugging/[ERROR-ID]/
- **Task principal**: [ID del task en TodoWrite]
- **Inicio**: [timestamp]
- **Estado actual**: [Fase X - descripción]

## 🎯 REGLAS DE EJECUCIÓN
1. **DOCUMENTAR TODO**: Cada comando y su resultado en el archivo correspondiente
2. **NO SALTAR FASES**: Completar exhaustivamente cada fase
3. **VERIFICAR CHECKPOINTS**: No avanzar sin validar completamente
4. **ACTUALIZAR ESTE PRP**: Mantener el estado actual siempre actualizado

---

## FASE-1: CAPTURA COMPLETA DEL ERROR

### Estado: [ ] Pendiente | [⏳] En progreso | [✅] Completada

### Comandos Obligatorios:
```bash
# 1. Crear estructura de documentación
Bash: mkdir -p .claudedocs/debugging/[ERROR-ID]

# 2. Capturar el error exacto
[Comando específico según el tipo de error - ejemplos:]
- Si es Docker: Bash: docker logs [container] --tail 200
- Si es aplicación: Read: [path/to/error.log]
- Si es servicio: Bash: systemctl status [service]

# 3. Capturar contexto del sistema
Bash: date >> 01-captura-inicial.md
Bash: pwd >> 01-captura-inicial.md
Bash: [comandos relevantes de estado] >> 01-captura-inicial.md

# 4. Analizar código relacionado
Read: [archivo donde ocurre el error]
Grep: "[patrón del error]" --type [extensión]

# 5. Documentar todo
Write: Completar template en 01-captura-inicial.md con TODA la información
```

### Template para 01-captura-inicial.md:
```markdown
# Captura Inicial - [ERROR-ID]

## Error Exacto
```
[Pegar el mensaje de error completo]
```

## Stack Trace
```
[Pegar stack trace si existe]
```

## Contexto de Ejecución
- Comando ejecutado: [comando que causó el error]
- Usuario: [usuario que ejecutó]
- Directorio: [pwd]
- Timestamp: [fecha y hora exacta]
- Entorno: [dev/staging/prod]

## Estado del Sistema
- Servicios activos: [listar servicios relevantes]
- Recursos: [memoria, CPU si es relevante]
- Configuración actual: [variables de entorno relevantes]

## Archivos Involucrados
- [archivo1]: líneas [X-Y] - [descripción de qué hace]
- [archivo2]: líneas [X-Y] - [descripción de qué hace]

## Observaciones Iniciales
[Cualquier observación inmediata sin interpretar]
```

### ✅ Checkpoint FASE-1:
- [ ] Error capturado completamente en 01-captura-inicial.md
- [ ] Contexto del sistema documentado
- [ ] Archivos relevantes identificados
- [ ] Sin interpretaciones prematuras
- [ ] Task "Fase 1" marcada como completada

---

## FASE-2: ANÁLISIS MULTI-DIMENSIONAL

### Estado: [ ] Pendiente | [ ] En progreso | [ ] Completada

### Comandos de Análisis:
```bash
# 1. Análisis temporal
/analyze --git --recent  # Cambios recientes
Bash: git log --oneline -20 >> 02-analisis-completo.md

# 2. Análisis de dependencias
/analyze --dependencies --affected
Write: Documentar dependencias en 02-analisis-completo.md

# 3. Análisis de configuración
Read: [archivos de configuración relevantes]
Grep: "[variables relacionadas]" .env*

# 4. Análisis de código (SI APLICA Sequential)
# USAR --seq SOLO SI: múltiples componentes, flujo complejo, causa no obvia
/analyze --architecture --code --seq  # Solo si es necesario

# 5. Documentar análisis completo
Write: Completar todas las dimensiones en 02-analisis-completo.md
```

### Template para 02-analisis-completo.md:
```markdown
# Análisis Multi-Dimensional - [ERROR-ID]

## 1. Análisis Temporal
- Primera aparición: [cuándo empezó]
- Frecuencia: [constante/intermitente/único]
- Cambios recientes:
  - [commit1]: [descripción]
  - [commit2]: [descripción]

## 2. Análisis de Dependencias
- Componentes afectados:
  - [componente1]: [cómo se ve afectado]
  - [componente2]: [cómo se ve afectado]
- Servicios externos: [listar si hay]
- Librerías: [versiones si es relevante]

## 3. Análisis de Configuración
- Variables verificadas:
  - [VAR1]: valor = [valor], esperado = [esperado]
  - [VAR2]: valor = [valor], esperado = [esperado]
- Archivos de config:
  - [archivo1]: [estado/contenido relevante]

## 4. Análisis de Datos
- Datos que fallan: [patrón si se identificó]
- Datos que funcionan: [patrón si se identificó]
- Casos límite: [si se encontraron]

## 5. Análisis de Código
- Asunciones identificadas:
  - [asunción1]: [dónde está en el código]
  - [asunción2]: [dónde está en el código]
- Flujo de ejecución: [describir si es relevante]

## Patrones Identificados
[Listar cualquier patrón que emerja del análisis]
```

### ✅ Checkpoint FASE-2:
- [ ] Todas las dimensiones analizadas
- [ ] Patrones documentados en 02-analisis-completo.md
- [ ] Sin saltar al diagnóstico prematuro
- [ ] Task "Fase 2" marcada como completada

---

## FASE-3: GENERACIÓN DE HIPÓTESIS

### Estado: [ ] Pendiente | [ ] En progreso | [ ] Completada

### Proceso de Generación:
```bash
# 1. Basándose en el análisis, generar hipótesis
/design --hypotheses --based-on-analysis

# 2. Para cada hipótesis, diseñar verificación
/design --test-strategy "para hipótesis A"

# 3. Documentar TODAS las hipótesis
Write: Crear 03-hipotesis.md con todas las hipótesis estructuradas

# 4. Priorizar hipótesis
Task: Ordenar hipótesis por probabilidad y facilidad de verificación
```

### Template para 03-hipotesis.md:
```markdown
# Hipótesis Generadas - [ERROR-ID]

## Hipótesis A: [Nombre descriptivo]
**Probabilidad**: [Alta/Media/Baja]
**Categoría**: [config/código/datos/infra/dependencia]

### Descripción
[Explicación clara de cuál sería la causa]

### Evidencia a Favor
1. [Evidencia del análisis que apoya esta hipótesis]
2. [Otra evidencia]

### Evidencia en Contra
1. [Algo que no cuadra con esta hipótesis]
2. [Otra contradicción si existe]

### Plan de Verificación
```bash
# Comandos específicos para verificar
Comando 1: [comando exacto]
Resultado esperado si es correcta: [qué veríamos]
Resultado esperado si es incorrecta: [qué veríamos]
```

### Solución si se Confirma
[Descripción de cómo se resolvería]

---

## Hipótesis B: [Nombre descriptivo]
[Mismo formato...]

---

## Hipótesis C: [Nombre descriptivo]
[Mismo formato...]

## Orden de Verificación Recomendado
1. [Hipótesis X] - Razón: [más probable y fácil de verificar]
2. [Hipótesis Y] - Razón: [segunda más probable]
3. [Hipótesis Z] - Razón: [menos probable pero posible]
```

### ✅ Checkpoint FASE-3:
- [ ] Mínimo 3 hipótesis generadas
- [ ] Cada hipótesis con plan de verificación claro
- [ ] Priorización documentada
- [ ] Task "Fase 3" marcada como completada

---

## FASE-4: VERIFICACIÓN SISTEMÁTICA

### Estado: [ ] Pendiente | [ ] En progreso | [ ] Completada

### Proceso por Hipótesis:
```bash
# Para CADA hipótesis en orden:

# 1. Crear archivo de verificación
Write: Iniciar 04-verificacion-A.md

# 2. Ejecutar plan de verificación
[Ejecutar comandos específicos del plan]

# 3. Documentar resultados inmediatamente
Write: Agregar cada resultado a 04-verificacion-A.md

# 4. Analizar resultados
/analyze --results --objective

# 5. Conclusión
Write: Documentar si la hipótesis se confirma, refuta o es parcial

# 6. Si se confirma, parar. Si no, continuar con siguiente hipótesis
```

### Template para 04-verificacion-[X].md:
```markdown
# Verificación Hipótesis [X] - [ERROR-ID]

## Hipótesis
[Copiar descripción de la hipótesis]

## Ejecución de Verificación

### Paso 1: [Descripción del paso]
**Comando**: `[comando exacto ejecutado]`
**Timestamp**: [hora de ejecución]
**Resultado**:
```
[Pegar output completo relevante]
```
**Interpretación**: [Qué significa este resultado]

### Paso 2: [Descripción del paso]
[Mismo formato...]

## Evidencia Nueva Encontrada
- [Cualquier cosa no anticipada]
- [Otros hallazgos durante verificación]

## Conclusión
**Estado**: [✅ Confirmada | ❌ Refutada | ⚠️ Parcial]
**Razonamiento**: [Por qué llegamos a esta conclusión]
**Siguiente paso**: [Implementar solución si confirmada, o verificar siguiente hipótesis]
```

### ✅ Checkpoint FASE-4:
- [ ] Cada hipótesis verificada sistemáticamente
- [ ] Resultados documentados en archivos separados
- [ ] Al menos una hipótesis confirmada
- [ ] Task "Fase 4" marcada como completada

---

## FASE-5: IMPLEMENTACIÓN DE SOLUCIÓN

### Estado: [ ] Pendiente | [ ] En progreso | [ ] Completada

### Solo proceder si hay hipótesis confirmada

### Proceso de Implementación:
```bash
# 1. Diseñar solución específica
/design --solution --based-on "[hipótesis confirmada]"

# 2. Crear respaldo si es necesario
Bash: cp [archivo] [archivo].backup-$(date +%Y%m%d-%H%M%S)

# 3. Implementar solución
[Comandos específicos según la solución]
Edit: [si es cambio de código]
Write: [si es crear archivo]
Bash: [si es comando de sistema]

# 4. Documentar cada cambio
Write: Registrar en 05-solucion.md exactamente qué se cambió

# 5. Verificación inmediata
[Comando para verificar que el error ya no ocurre]
```

### Template para 05-solucion.md:
```markdown
# Solución Implementada - [ERROR-ID]

## Hipótesis Confirmada
[Cuál hipótesis se confirmó y resumen de por qué]

## Cambios Realizados

### Cambio 1: [Descripción]
**Archivo**: [path/al/archivo]
**Tipo**: [crear/modificar/eliminar]
**Cambio específico**:
```diff
- [línea anterior si es modificación]
+ [línea nueva si es modificación]
```
**Justificación**: [Por qué este cambio resuelve el problema]

### Cambio 2: [Si hay más cambios]
[Mismo formato...]

## Comandos de Implementación
```bash
# Secuencia exacta de comandos ejecutados
[comando 1]
[comando 2]
```

## Respaldos Creados
- [archivo].backup-[timestamp]
- [otro respaldo si se hizo]

## Verificación Inicial
**Comando de verificación**: `[comando usado]`
**Resultado**: [✅ Error ya no aparece | ❌ Error persiste]
```

### ✅ Checkpoint FASE-5:
- [ ] Solución implementada según hipótesis confirmada
- [ ] Todos los cambios documentados
- [ ] Respaldos creados
- [ ] Verificación inicial exitosa
- [ ] Task "Fase 5" marcada como completada

---

## FASE-6: VALIDACIÓN EXHAUSTIVA

### Estado: [ ] Pendiente | [ ] En progreso | [ ] Completada

### Batería de Validación:
```bash
# 1. Verificar que el error original no ocurre
[Repetir el comando/acción que causaba el error]

# 2. Verificar servicios afectados
Bash: [comandos para verificar servicios]

# 3. Tests de regresión
/test --regression --affected
[O comandos específicos de test del proyecto]

# 4. Verificar funcionalidad relacionada
[Comandos para probar funcionalidad adyacente]

# 5. Monitoreo por tiempo definido
Bash: [comando de monitoreo] # Observar por 5-10 minutos

# 6. Documentar todos los resultados
Write: Completar 06-validacion.md
```

### Template para 06-validacion.md:
```markdown
# Validación de Solución - [ERROR-ID]

## Error Original
**Test**: [Comando/acción que causaba el error]
**Resultado**: [✅ Ya no ocurre | ❌ Aún ocurre]
**Evidencia**:
```
[Output que demuestra que está resuelto]
```

## Servicios Afectados
- [Servicio1]: [✅ Funcionando normal | ❌ Con problemas]
- [Servicio2]: [✅ Funcionando normal | ❌ Con problemas]

## Tests de Regresión
- [Test1]: [✅ Pasó | ❌ Falló] - [descripción]
- [Test2]: [✅ Pasó | ❌ Falló] - [descripción]

## Funcionalidad Relacionada
- [Función1]: [✅ Sin afectar | ⚠️ Afectada]
- [Función2]: [✅ Sin afectar | ⚠️ Afectada]

## Monitoreo Continuo
**Duración**: [X minutos]
**Resultados**: [Estable/Inestable]
**Logs relevantes**: [Si hay warnings o errores nuevos]

## Conclusión de Validación
**Estado**: [✅ Solución validada | ❌ Requiere ajustes]
**Confianza**: [Alta/Media/Baja]
**Recomendaciones**: [Si hay alguna]
```

### ✅ Checkpoint FASE-6:
- [ ] Error original verificado como resuelto
- [ ] Sin regresiones introducidas
- [ ] Funcionalidad validada
- [ ] Documentación completa en 06-validacion.md
- [ ] Task "Fase 6" marcada como completada

---

## FASE-7: DOCUMENTACIÓN Y LECCIONES

### Estado: [ ] Pendiente | [ ] En progreso | [ ] Completada

### Proceso de Cierre:
```bash
# 1. Generar resumen ejecutivo
/document --summary --from-debug-session

# 2. Extraer lecciones aprendidas
/analyze --patterns --lessons

# 3. Actualizar knowledge base si es necesario
Write: Si hay patrón nuevo, documentar para futura referencia

# 4. Crear post-mortem completo
Write: Completar 07-lecciones.md

# 5. Archivar sesión
Task: Marcar debug como completado con link a carpeta
```

### Template para 07-lecciones.md:
```markdown
# Post-Mortem y Lecciones - [ERROR-ID]

## Resumen Ejecutivo
- **Problema**: [1-2 líneas describiendo el problema]
- **Causa raíz**: [1 línea con la causa confirmada]
- **Solución**: [1-2 líneas con la solución aplicada]
- **Tiempo total**: [desde detección hasta resolución]
- **Impacto**: [quién/qué fue afectado]

## Timeline
- [HH:MM] - Error detectado
- [HH:MM] - Análisis iniciado
- [HH:MM] - Hipótesis A verificada
- [HH:MM] - Solución implementada
- [HH:MM] - Validación completada

## Lecciones Aprendidas

### Lo que funcionó bien
1. [Proceso/herramienta que ayudó]
2. [Decisión acertada]

### Lo que puede mejorar
1. [Proceso que tomó mucho tiempo]
2. [Algo que se pudo hacer diferente]

### Patrones Identificados
- **Tipo de error**: [categoría]
- **Indicadores tempranos**: [qué buscar en el futuro]
- **Solución típica**: [patrón de solución]

## Prevención Futura
1. [Acción preventiva recomendada]
2. [Monitoreo a agregar]
3. [Documentación a actualizar]

## Archivos de esta Sesión
- 00-PRP-ACTIVO.md - Plan de ejecución
- 01-captura-inicial.md - Datos del error
- 02-analisis-completo.md - Análisis detallado
- 03-hipotesis.md - Hipótesis generadas
- 04-verificacion-*.md - Verificaciones realizadas
- 05-solucion.md - Cambios implementados
- 06-validacion.md - Validación completa
- 07-lecciones.md - Este archivo
```

### ✅ Checkpoint FASE-7:
- [ ] Post-mortem completo
- [ ] Lecciones documentadas
- [ ] Patrones identificados
- [ ] Prevención futura definida
- [ ] Task principal marcada como completada

---

## 🔄 ACTUALIZACIÓN CONTINUA DE ESTE PRP

### Durante la ejecución, actualizar:
```markdown
## 📊 PROGRESO ACTUAL
**Fase activa**: [Número y nombre]
**Último comando ejecutado**: [comando]
**Próximo paso**: [qué sigue]
**Tiempo transcurrido**: [tiempo desde inicio]

## 🔍 HALLAZGOS CLAVE (actualizar mientras avanzas)
1. [Hallazgo importante 1]
2. [Hallazgo importante 2]
3. [Agregar más según se descubran]

## ⚠️ BLOQUEOS O ISSUES
- [Si hay algún bloqueo documentarlo aquí]
```

---

## 📌 QUICK REFERENCE - Comandos por Tipo de Error

### 🔧 Errores de Configuración
```bash
Read: [archivo .env o config]
Grep: "VARIABLE_NAME" .env*
/analyze --env --config
Edit: [archivo config] # Agregar/modificar variable
```

### 💾 Errores de Base de Datos
```bash
/analyze --database --schema
Bash: psql -c "DESCRIBE table"
/troubleshoot --query
/migrate --fix --backup
```

### 🌐 Errores de Red/Conectividad
```bash
Bash: docker network ls
Bash: docker inspect [container]
/analyze --network
Bash: curl http://[service]:[port]/health
```

### 🔐 Errores de Permisos/Seguridad
```bash
Bash: ls -la [archivo]
Read: [archivo de permisos]
/scan --permissions
Edit: [archivo] # Ajustar permisos
```

### 🐛 Errores de Lógica/Código
```bash
Read: [archivo con error]:[líneas]
/analyze --code --logic
/troubleshoot --execution
Edit: [archivo] # Corregir lógica
```

### 🚀 Errores de Performance
```bash
/analyze --performance --profile
Bash: top/htop # Monitorear recursos
/improve --performance
/test --performance --benchmark
```

---

## 🎯 RECORDATORIOS CRÍTICOS

1. **DOCUMENTAR TODO**: Ningún comando sin documentar su resultado
2. **NO INTERPRETAR PREMATURAMENTE**: Recopilar datos antes de concluir
3. **SEGUIR EL PROCESO**: No saltar fases aunque parezca obvio
4. **ACTUALIZAR TASKS**: Mantener TodoWrite sincronizado
5. **GUARDAR EVIDENCIA**: Outputs completos, no resúmenes
6. **VERIFICAR CHECKPOINTS**: No avanzar sin validar
7. **USAR HERRAMIENTAS REALES**: Solo comandos que existen

---

## 📚 RECURSOS ADICIONALES

- [Guía SuperClaude](.claudedocs/guides/GUIA_SUPERCLAUDE.md)
- [Debugging No Destructivo](.claudedocs/guides/debugging-no-destructivo.md)
- [Historial de Debugging](.claudedocs/debugging/)

---

*Template PRP-Debug SuperClaude v2.0*
*Para debugging sistemático y exhaustivo*
*Última actualización: 2025-01-19*