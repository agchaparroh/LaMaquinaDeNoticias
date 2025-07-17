# 🛡️ Guía de Debugging No Destructivo con SuperClaude

> **Para**: Claude Code (Opus 4) y desarrolladores humanos  
> **Propósito**: Resolver bugs sin crear más problemas  
> **Filosofía**: "Si funciona en producción, NO es un error"

---

## 📋 Índice

1. [Introducción](#introducción)
2. [Filosofía: Solo Problemas Paralizantes](#filosofía-solo-problemas-paralizantes)
3. [Las 5 Reglas de Oro](#las-5-reglas-de-oro)
4. [Workflow de Debugging](#workflow-de-debugging)
5. [Diagnóstico en Vivo](#diagnóstico-en-vivo)
6. [Comandos Esenciales](#comandos-esenciales)
7. [Técnicas por Tipo de Error](#técnicas-por-tipo-de-error)
8. [Protocolo de Eliminación de Errores](#protocolo-de-eliminación-de-errores)
9. [Recuperación de Desastres](#recuperación-de-desastres)
10. [Ejemplos Prácticos](#ejemplos-prácticos)
11. [Referencias Rápidas](#referencias-rápidas)

---

## 🎯 Introducción

### El Problema del Debugging Destructivo

Cuando debugueamos sin método, es fácil:
- 🔄 Perder el contexto de qué estamos arreglando
- 🐛 Crear nuevos bugs mientras arreglamos uno
- 📈 Hacer cambios que empeoran la situación
- 🤔 Olvidar cómo funcionaba el sistema originalmente
- ⚡ **Arreglar cosas que no están rotas** (over-engineering)

**Esta guía previene estos problemas mediante un enfoque sistemático y no destructivo.**

---

## 🚨 Filosofía: Solo Problemas Paralizantes

### 📌 Principio Fundamental

> **"Si funciona en producción, NO es un error"**

### 🔴 ¿Qué SÍ es un Problema Paralizante?

Solo debuggea cuando encuentres:

#### 1. **Servicio No Disponible**
   - Errores HTTP 500, 502, 503
   - Crashes del servidor
   - Timeouts sistemáticos

#### 2. **Funcionalidad Rota**
   - Features que no responden
   - Procesos que no completan
   - Acciones críticas bloqueadas

#### 3. **Pérdida/Corrupción de Datos**
   - Datos que desaparecen
   - Información incorrecta guardada
   - Inconsistencias en la base de datos

#### 4. **Bloqueo de Usuario**
   - Imposibilidad de hacer login
   - Flujos interrumpidos
   - Acciones críticas bloqueadas

#### 5. **Seguridad Comprometida**
   - Vulnerabilidad siendo explotada
   - Datos expuestos públicamente
   - Accesos no autorizados activos

### ✅ Lo que NO es un Problema Paralizante

**NO tocar si encuentras**:
- ⚠️ Warnings del linter
- 🎨 Code smells que funcionan
- 🚀 Performance "mejorable" pero funcional
- 📊 Tests con <100% cobertura (si pasan)
- 💭 Código "feo" pero funcional
- 📚 Deuda técnica sin impacto
- 📝 Logs verbosos sin errores
- ⚙️ Configuración subóptima pero funcional

### 🎯 La Regla de Tres Preguntas

Antes de debuggear, responde:
1. **¿Los usuarios reportan problemas?** → Si NO, no hay problema
2. **¿El servicio está funcionando?** → Si SÍ, no hay problema
3. **¿Los datos se procesan correctamente?** → Si SÍ, no hay problema

**Resultado: Si todo funciona = No tocar nada**

---

## 🔒 Las 5 Reglas de Oro

### 🏆 Regla 1: Siempre Crear un Checkpoint
```bash
# ANTES de cualquier cambio:
/git --checkpoint debug-[nombre-del-bug]
```

### 🔍 Regla 2: Entender Antes de Cambiar
```bash
# NUNCA cambies sin entender:
/analyze --code [archivo] --dependencies
/explain --how-it-works
```

### 🎯 Regla 3: Un Cambio a la Vez
```
Cambiar 1 cosa → Probar → ¿Funciona? → Commit
                          ↓
                    ¿No funciona? → Rollback
```

### 📝 Regla 4: Documentar Todo
```bash
# Estructura de documentación:
.claudedocs/debugging/BUG-[fecha]/
├── 1-sintomas.md      # Qué está pasando
├── 2-investigacion.md # Qué descubriste
├── 3-hipotesis.md     # Ideas para arreglar
└── 4-solucion.md      # Qué funcionó
```

### ✅ Regla 5: Validar Siempre
```bash
# Después de CADA cambio:
/test --affected        # Probar lo cambiado
/test --regression      # Verificar efectos secundarios
```

---

## 🔄 Workflow de Debugging

### 📋 Fase 1: Preparación (5 minutos)

#### Objetivo: Establecer base segura
```bash
# 1. Crear punto de restauración
/git --checkpoint debug-inicio

# 2. Cargar contexto completo
/load --context deep

# 3. Crear tracking
/task:create "Debug: [descripción del problema]"

# 4. Preparar documentación
mkdir -p .claudedocs/debugging/BUG-$(date +%Y%m%d-%H%M)
```

### 🔍 Fase 2: Investigación (15-30 minutos)

#### 2A. Análisis Estático
```bash
# Entender el error
/analyze --error "[mensaje]" --uc

# Revisar logs históricos
/analyze --logs --pattern "[error]" --time "1h"

# Analizar código relacionado
/troubleshoot --investigate --seq
```

#### 2B. Diagnóstico en Vivo 🔴 CRÍTICO
```bash
# Observar el servicio en acción
curl -X POST http://localhost:8000/endpoint \
  -H "Content-Type: application/json" \
  -d @test-data.json \
  -v  # Verbose para ver todo

# Monitorear en tiempo real
docker logs -f [container] --tail 50

# Seguir métricas mientras procesa
watch -n 1 'curl -s http://localhost:8000/metrics'
```

### 💡 Fase 3: Hipótesis (10 minutos)

```bash
# Generar plan de acción
/design --fix --minimal --plan

# Documentar ideas
echo "## Hipótesis 1: [descripción]" > ./debugging/BUG-*/3-hipotesis.md

# Evaluar complejidad
/prp --init "debug [problema]"
# Si es complejo → Escalar a PRP
```

### 🔧 Fase 4: Implementación (Variable)

```bash
# 1. Cambio mínimo y específico
/build --fix --minimal --validate

# 2. Test inmediato
/test --unit --affected

# 3. Si funciona → Guardar progreso
/git --commit "fix: [problema] - [solución]"

# 4. Si falla → Deshacer y repensar
/git --rollback
# Volver a Fase 3
```

### ✅ Fase 5: Validación (10 minutos)

```bash
# Tests exhaustivos
/test --comprehensive

# Verificar calidad
/scan --validate --quality

# Documentar solución
/document --fix --what-worked
```

---

## 🔍 Diagnóstico en Vivo

### 🚀 Por Qué es Crítico

El análisis estático no revela:
- **Condiciones de carrera**: Solo visibles con concurrencia real
- **Memory leaks**: Aparecen después de muchas operaciones
- **Timeouts**: Ocurren con datos de producción
- **Problemas de integración**: Fallos por latencia o límites externos

### 🎯 Estrategias de Diagnóstico en Vivo

#### 1. Preparar Casos de Prueba Realistas
```bash
# Datos variados
echo '{"data": "minimal"}' > test-minimal.json
echo '{"data": "[500 palabras...]"}' > test-normal.json
echo '{"data": "[5000 palabras...]"}' > test-heavy.json
```

#### 2. Observar Procesamiento Individual
```bash
# Medir tiempos y respuestas
curl -X POST http://localhost:8000/process \
  -d @test-normal.json \
  -w "\nTiempo total: %{time_total}s\n"
```

#### 3. Detectar Cuellos de Botella
```bash
# Analizar fases del proceso
docker logs [container] | grep "Fase.*completada"

# Monitorear recursos
docker stats [container] --no-stream
```

#### 4. Pruebas de Carga
```bash
# Simular concurrencia
for i in {1..10}; do
  curl -X POST http://localhost:8000/process \
    -d @test-$i.json &
done
```

### 🐛 Patrones Solo Visibles en Vivo

| Problema | Síntoma | Detección |
|----------|---------|-----------|
| Memory Leak | RAM crece constantemente | `docker stats` muestra aumento |
| Connection Pool | Falla tras N requests | Request #11 timeout |
| Rate Limiting | Rechazos intermitentes | 429 después de X llamadas |
| Degradación | Cada request más lenta | Tiempos incrementales |

---

## 🛠️ Comandos Esenciales

### 🔍 Investigación
```bash
/analyze --code [archivo]           # Entender código
/analyze --logs --pattern "[error]" # Buscar en logs
/troubleshoot --investigate         # Guía interactiva
/explain --error --c7               # Explicar con Context7
```

### 💾 Preservación
```bash
/git --checkpoint [nombre]     # Crear checkpoint
/git --status                  # Ver cambios
/git --rollback [checkpoint]   # Restaurar estado
```

### 🔧 Cambios Seguros
```bash
/build --fix --minimal         # Cambio mínimo
/test --affected               # Test específico
/test --regression             # Verificar efectos
```

### 📊 Gestión
```bash
/task:create "Debug: [desc]"   # Crear tarea
/task:update [id] "[status]"   # Actualizar
TodoWrite                      # Gestionar TODOs
```

---

## 🔍 Técnicas por Tipo de Error

### 🔴 TypeError: Cannot read property
```javascript
// Problema
user.name  // Error si user es null

// Diagnóstico
/analyze --error "Cannot read property" --trace

// Solución
if (user && user.name) {
    // usar user.name seguro
}
```

### 🔴 API Error 500
```bash
# 1. Logs del servidor
/analyze --logs --api --errors

# 2. Estado de la BD
/troubleshoot --database --connections

# 3. Configuración
/analyze --config --timeouts
```

### 🔴 Funciona Local, Falla en Producción
```bash
# 1. Comparar entornos
/analyze --env --diff local prod

# 2. Dependencias
/analyze --dependencies --versions

# 3. Permisos
/troubleshoot --permissions --prod
```

### 🔴 Performance Degradada
```bash
# 1. Encontrar bottleneck
/analyze --profile --bottleneck --seq

# 2. Métricas específicas
/analyze --performance --queries

# 3. Optimizar SOLO lo crítico
/improve --performance --targeted
```

---

## 🚀 Protocolo de Eliminación de Errores

### 📋 Cuándo Usar el Protocolo

Activa este protocolo cuando:
- Necesites garantizar que un módulo funcione perfectamente
- Quieras encontrar TODOS los problemas paralizantes
- Debas hacer una auditoría completa de salud

### 🎯 Paso 1: Crear PRP de Diagnóstico

```bash
# Generar PRP especializado
/prp --generate critical-issues-[module] --persona-qa

# El PRP buscará SOLO:
# ✓ Funcionalidades rotas
# ✓ Pérdida de datos
# ✓ Bloqueos de usuario
# ✓ Vulnerabilidades activas
# ✗ NO: warnings, code smells, optimizaciones
```

### 🔄 Paso 2: PRP Dinámico Evolutivo

```yaml
# Estructura del PRP
name: "Error Elimination Protocol - [module]"
type: "dynamic-evolutionary"

## Inventario Dinámico
errors_found: 0    # Auto-incrementa
errors_fixed: 0    # Actualizado al resolver
errors_pending: 0  # Calculado: found - fixed

## Categorías
- Critical: []     # Seguridad, crashes
- High: []         # Funcionalidad rota
- Medium: []       # Performance crítica
- Low: []          # Solo si hay tiempo
```

### 🔧 Paso 3: Ejecución Adaptativa

```bash
# Ejecutar protocolo
/prp --execute PRPs/error-elimination-[module].md

# Si encuentra nuevos errores:
# 1. Pausar
# 2. Actualizar PRP
# 3. Re-priorizar
# 4. Continuar
```

### ✅ Respuesta Sin Problemas

```markdown
## Diagnóstico Completo - [module]
Estado: ✅ FUNCIONANDO CORRECTAMENTE

### Problemas Paralizantes: 0

- ✅ Servicio disponible
- ✅ Funcionalidades operativas
- ✅ Datos íntegros
- ✅ Sin bloqueos de usuario
- ✅ Seguridad verificada

### Recomendación
**No se requiere acción.**

Encontré [N] oportunidades de mejora menores,
pero nada que impacte la operación actual.
```

---

## 🚨 Recuperación de Desastres

### 😵 "Perdí el Contexto"
```bash
# Recuperar orientación
/load --context deep
/read .claudedocs/debugging/BUG-*/
/task:status
/git --status
```

### 🐛 "Creé Más Bugs"
```bash
# 1. DETENTE
# No hagas más cambios

# 2. Volver al inicio
/git --rollback debug-inicio

# 3. Escalar
/prp --init "debug complejo con efectos secundarios"

# 4. Aprender
echo "## Lección aprendida" >> debugging/lecciones.md
```

### 🧪 "Los Tests Fallan"
```bash
# 1. NO ignores tests
# Protegen funcionalidad existente

# 2. Entender expectativas
/analyze --test [test-fallando]

# 3. Ajustar sin romper
/improve --fix --preserve-behavior
```

---

## 🎯 Ejemplos Prácticos

### 📘 Ejemplo 1: TypeError Simple

```bash
# Síntoma
"TypeError: Cannot read property 'name' of null"

# Proceso completo
/git --checkpoint debug-typeerror
/analyze --error "Cannot read property 'name'" --production
# → user.controller.js:45

/analyze --code user.controller.js:45
# → Hipótesis: user puede ser null

/build --fix --null-check
# → if (user && user.name)

/test --unit user.controller.test.js
/test --regression
/git --commit "fix: handle null user in getName"
```

### 📘 Ejemplo 2: Memory Leak Complejo

```bash
# Síntoma
"Servidor sin memoria tras 2 horas"

# Evaluación
/prp --init "debug memory leak"
# → "Recomendado: usar PRP"

# Ejecución sistemática
/prp --generate memory-leak-debug --persona-performance
/prp --execute PRPs/memory-leak-debug.md
```

---

## 📚 Referencias Rápidas

### 📝 Plantilla de Bug Report

```markdown
# Bug: [Nombre descriptivo]
Fecha: [YYYY-MM-DD]

## Síntomas
- Comportamiento observado
- Frecuencia
- Mensaje de error

## Causa Raíz
- Por qué ocurría
- Código afectado

## Solución
- Cambios realizados
- Por qué funciona

## Lecciones
- Qué aprendimos
- Cómo prevenirlo
```

### ✅ Checklist de Cierre

- [ ] Bug original resuelto
- [ ] Sin bugs nuevos
- [ ] Tests pasando
- [ ] Código commiteado
- [ ] Documentación actualizada
- [ ] Lecciones documentadas

### 💡 Principios Finales

1. **Paciencia**: Mejor lento que roto
2. **Tests**: Si fallan, hay razones
3. **Documentación**: Tu yo futuro agradecerá
4. **Escalamiento**: PRP cuando sea complejo
5. **Celebración**: Cada fix es aprendizaje

---

> *"El mejor debugging es el que no rompe nada más. Sigue esta guía y dormirás tranquilo."*

*Guía de Debugging No Destructivo v2.0 | La Máquina de Noticias*