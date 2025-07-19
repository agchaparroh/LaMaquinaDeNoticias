# PRP (Problem Resolution Protocol) - Pipeline Module - ACTUALIZADO
## La Máquina de Noticias - Protocolo de Resolución de Problemas

### 🎯 OBJETIVO
Diagnosticar y resolver TODOS los problemas del módulo pipeline de forma sistemática, documentada y sin sesgos.

### ⚠️ PRINCIPIOS FUNDAMENTALES ACTUALIZADOS

1. **DIAGNÓSTICO COMPLETO ANTES DE SOLUCIÓN**
   - NUNCA aplicar una solución sin diagnóstico exhaustivo
   - Evitar sesgo de confirmación
   - Verificar TODAS las hipótesis posibles
   - Documentar evidencia completa

2. **REGISTRO DETALLADO DE ERRORES**
   - Cada error nuevo debe ser registrado inmediatamente
   - Incluir contexto completo, stack trace, logs
   - Documentar hipótesis descartadas
   - Mantener historial de intentos fallidos

3. **MÉTODO DE HIPÓTESIS MÚLTIPLES OBLIGATORIO**
   - Generar mínimo 3 hipótesis por error
   - Verificar cada hipótesis con evidencia
   - Documentar por qué se descarta cada una
   - Solo implementar solución cuando hay certeza

### 📋 PROTOCOLO DE DIAGNÓSTICO ACTUALIZADO

#### PASO 1: CAPTURA COMPLETA DEL ERROR
```
1. Mensaje de error exacto
2. Stack trace completo
3. Contexto de ejecución (qué se estaba procesando)
4. Estado del sistema (logs, memoria, CPU)
5. Diferencias con ejecuciones anteriores
```

#### PASO 2: ANÁLISIS MULTI-DIMENSIONAL
```
1. Análisis temporal: ¿Cuándo empezó a fallar?
2. Análisis causal: ¿Qué cambió antes del error?
3. Análisis de dependencias: ¿Qué componentes interactúan?
4. Análisis de datos: ¿Qué datos específicos causan el fallo?
5. Análisis de código: ¿Qué asunciones hace el código?
```

#### PASO 3: GENERACIÓN DE HIPÓTESIS
```
Para cada error:
- Hipótesis A: [Causa más obvia]
  - Evidencia a favor:
  - Evidencia en contra:
  - Forma de verificar:
  
- Hipótesis B: [Causa alternativa]
  - Evidencia a favor:
  - Evidencia en contra:
  - Forma de verificar:
  
- Hipótesis C: [Causa menos probable pero posible]
  - Evidencia a favor:
  - Evidencia en contra:
  - Forma de verificar:
```

#### PASO 4: VERIFICACIÓN SISTEMÁTICA
```
1. Crear script de verificación específico
2. Probar cada hipótesis aisladamente
3. Documentar resultados de cada prueba
4. Identificar la causa raíz con certeza
5. Validar que no hay causas múltiples
```

#### PASO 5: IMPLEMENTACIÓN CUIDADOSA
```
1. Diseñar solución mínima y específica
2. Predecir efectos secundarios
3. Implementar con comentarios explicativos
4. Crear test para prevenir regresión
5. Documentar la solución aplicada
```

### 📊 REGISTRO DE ERRORES ACTUALIZADO

#### [REGISTRO LIMPIADO - NUEVA SESIÓN DE DEBUGGING]
- **Fecha de limpieza**: 2025-07-19
- **Errores previos archivados en**: Historia de errores anteriores
- **Nueva carpeta de debugging**: .claudedocs/debugging/Limpieza01

---

## 🎯 CASO RESUELTO #1: ERROR CAMPOS ENTIDADES
**Fecha resolución**: 2025-07-19  
**Estado**: ✅ **RESUELTO PERMANENTEMENTE**

### 📋 PROBLEMA ORIGINAL
```
Error: null value in column "nombre" of relation "entidades" violates not-null constraint
Código: 23502
```

### 🔍 DIAGNÓSTICO APLICADO (SIGUIENDO PRP)

#### PASO 1: CAPTURA COMPLETA DEL ERROR
- **Error exacto**: Pipeline enviaba campos `nombre_entidad`, `tipo_entidad` pero RPC esperaba `nombre`, `tipo`
- **Contexto**: Procesamiento de artículo con entidades extraídas
- **Comportamiento anómalo**: Código mostraba campos sin sufijo pero runtime ejecutaba con sufijo

#### PASO 2: ANÁLISIS MULTI-DIMENSIONAL
- **Temporal**: Error sistemático en todas las ejecuciones
- **Causal**: Mismatch entre esquema de datos del pipeline y RPC
- **Dependencias**: pipeline_coordinator.py → payload_builder.py → Supabase RPC
- **Datos**: Todas las entidades afectadas, no específico a contenido
- **Código**: Dos esquemas diferentes para entidades en el mismo archivo

#### PASO 3: GENERACIÓN DE HIPÓTESIS

**Hipótesis A: Error en RPC de Supabase**
- ✅ Evidencia a favor: RPC esperaba campos con sufijo
- ❌ Evidencia en contra: El modelo Pydantic usaba campos sin sufijo
- 🔍 Verificación: Actualizar RPC para campos sin sufijo

**Hipótesis B: Error en pipeline_coordinator.py**
- ✅ Evidencia a favor: Código mostraba campos correctos pero runtime ejecutaba incorrectos
- ✅ Evidencia a favor: Había logging que confirmaba campos sin sufijo
- 🔍 Verificación: Buscar lugares con esquemas inconsistentes

**Hipótesis C: Problema de serialización/cache**
- ❌ Evidencia en contra: Error persistía después de limpiar .pyc
- ❌ Evidencia en contra: Rebuilds de Docker no lo resolvían

#### PASO 4: VERIFICACIÓN SISTEMÁTICA
1. **Script de análisis**: `fix_pipeline_fields.py` para buscar patrones
2. **Búsqueda exhaustiva**: Grep de todos los campos con sufijo
3. **Descubrimiento clave**: DOS lugares en pipeline_coordinator.py con esquemas diferentes:
   - `entidades_del_hecho` (líneas 642-649, 773-780): CON sufijo
   - `entidades_data` (líneas 783-789): SIN sufijo

#### PASO 5: IMPLEMENTACIÓN CUIDADOSA

**Causa raíz identificada**: 
- Las entidades anidadas en hechos (`entidades_del_hecho`) usaban sufijos
- Al procesarse, se mezclaban con entidades principales
- El payload_builder recibía entidades con formatos mixtos

**Solución implementada**:
1. **Corrección permanente**: Cambiar `nombre_entidad` → `nombre` y `tipo_entidad` → `tipo` en líneas 645-646 y 776-777
2. **Eliminación de workaround**: Remover transformación temporal del payload_builder
3. **Consistencia absoluta**: Todos los esquemas ahora usan campos sin sufijo

**Verificación de solución**:
- ✅ Test exitoso sin transformación temporal
- ✅ Logs confirman campos correctos: `['id', 'nombre', 'tipo', ...]`
- ✅ No más logs de transformación automática

### 📈 MÉTRICAS ALCANZADAS
- ✅ **Diagnóstico Completo**: 3 hipótesis verificadas sistemáticamente
- ✅ **Calidad de Solución**: Corrección de causa raíz, sin workarounds
- ✅ **Prevención**: Consistencia absoluta en toda la arquitectura

### 🔄 LECCIONES APRENDIDAS
1. **ULTRATHINK funcionó**: El análisis exhaustivo encontró la causa real
2. **Importancia de buscar patrones**: El mismo error aparecía en DOS lugares
3. **Transformaciones temporales útiles**: Permitieron validar solución antes de implementar permanente
4. **Esquemas mixtos son peligrosos**: Un archivo con dos formatos diferentes causa confusión

---

## 🚨 PROBLEMA ACTIVO #2: ERROR PRECISION_TEMPORAL
**Estado**: ⏳ **PENDIENTE RESOLUCIÓN**

### 📋 PROBLEMA DETECTADO
```
Error: null value in column "precision_temporal" of relation "hechos_futuros" violates not-null constraint
Código: 23502
```

### 🔍 ANÁLISIS INICIAL
- **Contexto**: Después de resolver problema de entidades, apareció este nuevo error
- **Tabla afectada**: `hechos_futuros` requiere campo `precision_temporal` obligatorio
- **Próximos pasos**: Aplicar mismo método PRP para diagnóstico completo

---

### 🚨 PROTOCOLO ANTI-SESGO

1. **Antes de cada fix, preguntarse:**
   - ¿He verificado TODAS las hipótesis?
   - ¿Hay alguna asunción que no he cuestionado?
   - ¿He buscado evidencia que CONTRADIGA mi hipótesis?
   - ¿Entiendo COMPLETAMENTE por qué falla?

2. **Señales de alerta de sesgo:**
   - Aplicar fix "obvio" sin verificar
   - Asumir que el error es "simple"
   - No considerar efectos secundarios
   - No verificar el contexto completo

3. **Verificación cruzada:**
   - Confirmar con logs
   - Verificar con datos de prueba diferentes
   - Validar asunciones del código
   - Comprobar documentación y esquemas

### 📈 MÉTRICAS DE ÉXITO

1. **Diagnóstico Completo**: 
   - Mínimo 3 hipótesis por error
   - Evidencia documentada para cada una
   - Verificación antes de implementar

2. **Calidad de Soluciones**:
   - Sin regresiones
   - Sin efectos secundarios
   - Código documentado
   - Tests agregados

3. **Prevención**:
   - Patrones de error identificados
   - Mejoras proactivas implementadas
   - Documentación actualizada

### 🔄 PROCESO CONTINUO

Este PRP es un documento vivo que debe actualizarse con:
- Cada nuevo error encontrado
- Lecciones aprendidas
- Mejoras al proceso de diagnóstico
- Patrones identificados

**RECORDATORIO CRÍTICO**: Una solución rápida sin diagnóstico completo SIEMPRE lleva a más problemas. La paciencia y el rigor en el diagnóstico ahorran tiempo a largo plazo.