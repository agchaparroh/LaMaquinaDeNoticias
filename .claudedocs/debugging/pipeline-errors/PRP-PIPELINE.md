# PRP (Problem Resolution Protocol) - Pipeline Module - ACTUALIZADO
## La Máquina de Noticias - Protocolo de Resolución de Problemas

### 🎯 OBJETIVO
Diagnosticar y resolver TODOS los problemas del módulo pipeline de forma sistemática, documentada y sin sesgos.

### 📚 RECURSOS IMPORTANTES:

- **Explicación del sistema**: Ver [COMO_FUNCIONA](./COMO_FUNCIONA) para entender el flujo completo del artículo desde la extracción hasta la persistencia.

### 🚨 CRITERIOS DE ÉXITO FUNDAMENTALES - RECORDATORIO CRÍTICO

- [ ] ÉXITO EN EL PROCESAMIENTO DE UN ARTÍCULO DE TAMAÑO MEDIO Y PERSISTENCIA EXITOSA EN SUPABASE. 

**¿Cómo probarlo?**

Ejecutar el spider centroamérica360_politica (con tilde) en scrapyd con un límite de un solo artículo y monitorizar el procesamiento a través del pipeline

**Precaución:**

Recuerda que, para que la prueba sea considerada un éxito, debe haber persistencia completa en Supabase, tanto del artículo como de TODOS los ítems extraídos.

### 📋 PROTOCOLO COMPLETO DE ACTUACIÓN PRP

#### 🟢 FASE 0: SIN ERRORES DETECTADOS
**Objetivo**: Verificar que el sistema cumple los criterios de éxito y detectar posibles problemas.

0. docker ps + docker ps -a | head -20

1. **Ejecutar spider de prueba**:
   ```bash
   cd /home/ec2-user/projects/LaMaquinaDeNoticias
   scrapy crawl infobae_america_latina -a test_mode=true
   ```

2. **Monitorizar el sistema completo**:
   - Ver logs del pipeline: `docker-compose logs -f module-pipeline`
   - Verificar base de datos: revisar que se persistan hechos, entidades, datos y citas
   - Comprobar métricas: CPU, memoria, errores en logs

3. **Si todo funciona correctamente**: 
   - Documentar el éxito en este archivo
   - Continuar monitorizando periódicamente

4. **Si se detecta un error**: 
   - **IMPORTANTE**: Solo considerar ERRORES PARALIZANTES (que impiden el funcionamiento del sistema o el cumplimiento de los criterios de éxito)
   - Warnings, errores manejados gracefully o errores menores NO requieren iniciar el protocolo PRP
   - Si es un error paralizante → Proceder inmediatamente a FASE 1

---

#### 🔴 FASE 1: ERROR DETECTADO - DIAGNÓSTICO
**Principio fundamental**: NUNCA tocar código hasta entender completamente el problema.

1. **CAPTURA INMEDIATA** (5-10 minutos):
   - Copiar mensaje de error exacto
   - Guardar stack trace completo
   - Documentar: ¿Qué se estaba procesando cuando falló?
   - Capturar logs de los últimos 5 minutos
   - Anotar cualquier cambio reciente en el sistema

2. **COMUNICAR AL USUARIO**:
   ```
   "He detectado el error [descripción breve]. 
   Voy a iniciar el protocolo PRP de diagnóstico.
   Primero voy a [acción específica] para entender la causa."
   ```

3. **ANÁLISIS MULTI-DIMENSIONAL** (15-30 minutos):
   - **Temporal**: ¿Primera vez? ¿Intermitente? ¿Después de qué cambio?
   - **Alcance**: ¿Afecta a todo o solo algunos casos?
   - **Dependencias**: ¿Qué componentes están involucrados?
   - **Datos**: ¿Falla con datos específicos o con todos?
   - **Contexto**: ¿Carga del sistema? ¿Concurrencia?

4. **GENERAR 3 HIPÓTESIS MÍNIMO**:
   ```markdown
   Hipótesis A: [La más probable - 60-80%]
   - A favor: [evidencias concretas]
   - En contra: [lo que no cuadra]
   - Cómo verificar: [comando o test específico]
   
   Hipótesis B: [Alternativa - 20-30%]
   - A favor: [evidencias]
   - En contra: [contradicciones]
   - Cómo verificar: [método]
   
   Hipótesis C: [Menos probable pero posible - 10%]
   - A favor: [indicios]
   - En contra: [dudas]
   - Cómo verificar: [approach]
   ```

5. **VERIFICAR SISTEMÁTICAMENTE**:
   - Probar CADA hipótesis con evidencia
   - Documentar resultado de cada prueba
   - NO pasar a solución hasta tener certeza

**Anti-sesgo**: Si tu primera idea es "debe ser X porque la última vez era X", PARA. Genera otras 2 hipótesis diferentes.

---

#### 🔧 FASE 2: IMPLEMENTACIÓN DE SOLUCIÓN
**Solo proceder cuando**: Tienes evidencia clara de la causa raíz.

1. **COMUNICAR PLAN**:
   ```
   "He identificado que el problema es [causa raíz].
   Voy a implementar [solución específica].
   Esto debería [efecto esperado]."
   ```

2. **IMPLEMENTAR**:
   - Cambio mínimo necesario
   - Agregar comentarios explicando POR QUÉ
   - No aprovechar para "mejorar" otras cosas

3. **VERIFICAR**:
   - Reproducir el caso original - debe funcionar
   - Ejecutar spider completo
   - Verificar que no rompimos nada más
   - Comprobar persistencia en Supabase

4. **COMUNICAR RESULTADO**:
   ```
   "Solución implementada y verificada.
   [Resultado de las pruebas]
   El sistema ahora [comportamiento actual]."
   ```

---

#### ✅ FASE 3: POST-RESOLUCIÓN

1. **ACTUALIZAR REGISTROS**:
   - Crear archivo detallado en `.claudedocs/debugging/pipeline-errors/registros/ERROR-[FECHA]-[HORA].md`
   - Usar la plantilla completa con TODA la información recopilada
   - En ESTE documento solo agregar un resumen sucinto (2-3 líneas) con referencia al archivo completo
   - Formato del resumen: Estado, descripción breve y link al archivo detallado

2. **VERIFICAR CRITERIOS GLOBALES**:
   - [ ] ¿Procesa artículos medianos con éxito?
   - [ ] ¿Persiste correctamente en Supabase?
   - [ ] ¿Maneja múltiples artículos en cola?
   - [ ] ¿Los errores se manejan gracefully?

3. **SIGUIENTE ACCIÓN**:
   - Si hay más errores en cola → Volver a FASE 1
   - Si no hay errores → Volver a FASE 0 (monitorización)
   - Si todos los criterios se cumplen → Trabajo completado

---

#### ⚠️ RECORDATORIOS CRÍTICOS

**NUNCA**:
- Aplicar un fix sin entender la causa
- Asumir que sabes la solución sin verificar
- Hacer cambios "mientras estás ahí"
- Proceder sin comunicar al usuario

**SIEMPRE**:
- Documentar TODO el proceso
- Verificar hipótesis con evidencia
- Probar la solución exhaustivamente
- Actualizar este registro


### 📊 REGISTRO DE ERRORES - RESUMEN

#### 📁 Archivos de registro completos en: `.claudedocs/debugging/pipeline-errors/registros`

#### [NUEVA SESIÓN - 2025-01-21]

## 🎯 ESTADO ACTUAL

### ✅ Errores Resueltos
- **[2025-01-22]** | ✅ RESUELTO | RPC falla con "argument 1: key must not be null" - Faltaba campo id_temporal en entidades
  → Detalles completos: [./pipeline-errors/ERROR-20250122-0102.md] y [FIX-ID-TEMPORAL-20250122.md]
- **[2025-07-23]** | ✅ RESUELTO | Constraint violation "entidad_relacion_tipo_relacion_check" - Pipeline generaba tipos de relación no válidos
  → Error corregido que impedía persistencia en Supabase
- **[2025-07-23]** | ✅ RESUELTO | Error de tipo en Fase 7 normalización - Campo id_entidad_normalizada espera string pero recibe int
  → Error corregido, normalización y persistencia funcionan correctamente

### 🔴 Errores Activos
Ningún error activo detectado.

### 📝 Formato de registro sucinto:
```
- **[FECHA]** | Estado | Descripción breve (máx 2 líneas)
  → Detalles completos: [./pipeline-errors/ERROR-YYYYMMDD-HHMM.md]
```

### ✅ ÚLTIMA VERIFICACIÓN DE CRITERIOS GLOBALES [2025-07-23 23:58]
- [x] Pipeline activo y respondiendo al health check
- [✅] ¿Procesa artículos medianos con éxito? - SÍ - Procesamiento completo exitoso
  - Procesamiento exitoso de todas las fases: ✅ Triaje, ✅ Simplificación, ✅ Entidades (15), ✅ Hechos (9)
  - Fase 7A completada: 0 normalizadas, 15 no encontradas (comportamiento normal para entidades nuevas)
  - Fase 7B completada: 30 relaciones detectadas (18 hecho-entidad, 7 entidad-entidad, 4 hecho-hecho, 1 contradicción)
- [✅] ¿Persiste correctamente en Supabase? - SÍ - RPC actualizar_articulo_procesado exitoso
  - Artículo ID: 1 actualizado exitosamente
  - Hechos: 9, Entidades: 15, Citas: 0 persistidos correctamente
- [❓] ¿Maneja múltiples artículos en cola? - No verificado en esta prueba
- [✅] ¿Los errores se manejan gracefully? - Sí - Validación post-7B descartó 3 relaciones inválidas sin interrumpir el flujo

---

### 🔄 PROCESO CONTINUO

Este PRP es un documento vivo que debe actualizarse con:
- Cada nuevo error encontrado
- Lecciones aprendidas
- Mejoras al proceso de diagnóstico
- Patrones identificados

**RECORDATORIO CRÍTICO**: Una solución rápida sin diagnóstico completo SIEMPRE lleva a más problemas. La paciencia y el rigor en el diagnóstico ahorran tiempo a largo plazo.