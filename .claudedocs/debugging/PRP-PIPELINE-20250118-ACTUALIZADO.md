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

#### ERROR 1: ValidationError - Campo 'titulo' vs 'titular'
- **Diagnóstico**: Completo con verificación en Supabase
- **Solución**: Mapeo robusto de campos
- **Estado**: ✅ RESUELTO

#### ERROR 2: KeyError en logging con f-strings
- **Diagnóstico**: Análisis de sintaxis loguru
- **Solución**: Usar parámetros estructurados
- **Estado**: ✅ RESUELTO

#### ERROR 3: NameError 'fragmento' en pipeline_coordinator
- **Diagnóstico**: Variable mal nombrada
- **Solución**: Cambiar a 'fragmento_unificado'
- **Estado**: ✅ RESUELTO

#### ERROR 4: NameError 'fragmento' en controller.py
- **Diagnóstico**: Contexto diferente, variable 'articulo'
- **Solución**: Usar nombre correcto de variable
- **Estado**: ✅ RESUELTO

#### ERROR 5: Fallo persistencia - campos faltantes
- **Diagnóstico**: Extenso con 7 hipótesis verificadas
- **Solución**: Implementación Opción A completa
- **Estado**: ✅ CÓDIGO IMPLEMENTADO (pero reveló ERROR 6)

#### ERROR 6: AttributeError 'clasificacion_contenido'
- **Diagnóstico**: Campo inexistente en modelo
- **Solución**: Usar valor por defecto "neutral"
- **Estado**: ✅ RESUELTO

#### ERROR 7: 'datetime.datetime' object has no attribute 'strip'
- **Diagnóstico Inicial**: 
  - Hipótesis A: fecha_publicacion sin convertir a string ✅ CONFIRMADA
  - Hipótesis B: Otros campos datetime sin convertir
  - Hipótesis C: Problema en validate_date_optional
- **Solución**: Añadir .isoformat() en línea 313
- **Estado**: 🔄 FIX APLICADO, PENDIENTE VERIFICACIÓN

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