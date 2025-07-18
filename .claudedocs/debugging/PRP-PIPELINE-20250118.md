# 🚨 PRP v2.0.0: ELIMINACIÓN DE ERRORES - MODULE PIPELINE
**Fecha**: 2025-01-18  
**Tipo**: dynamic-evolutionary  
**Estado**: EN PROGRESO  
**Framework**: Automated Triggers ACTIVE ✅

---

## 🚨 ACCIÓN INMEDIATA - [E001: keyword argument 'nombre' en normalizar_entidad]

### 📋 Próximos Pasos Específicos:
1. ⛔ **STOP** - Fix parcial prohibido (AUTOMATED TRIGGER ACTIVADO)
2. 🔍 **Task tool** - COMPLETADO: Error en fase_7_normalizacion.py línea 384
3. 📊 **Scope**: Solo 1 archivo afectado (fase_7_normalizacion.py)
4. 🔧 **Fix integral**: Corregir llamada a normalizar_entidad con parámetros correctos
5. ✅ **Validación**: Continuar diagnóstico después del fix

---

## 📊 ESTADO ACTUAL

### Inventario Dinámico:
- **Errores encontrados**: 3 (+1 patrón similar)
- **Errores corregidos**: 3  
- **Errores pendientes**: 1

### Categorías de Errores:
- **CRITICAL**: [E003: Campos requeridos faltantes para Supabase - BLOQUEA PERSISTENCIA] # Crashes, pérdida de datos
- **HIGH**: [] # Funcionalidad rota
- **MEDIUM**: [] # Performance crítica
- **LOW**: [] # Solo si hay tiempo
- **FIXED**: 
  - [✅ E001: keyword argument 'nombre' en normalizar_entidad - fase_7_normalizacion.py:384]
  - [✅ E002: MetadatosHecho no tiene fecha_inicio - fase_7_normalizacion.py:156]
  - [✅ Patrón E002: MetadatosDato campos periodo_inicio/fin - fase_5_datos.py:299-300]

### Estado del Pipeline:
- [ ] Fase 1 (Triaje): NO PROBADO
- [ ] Fase 2 (Simplificación): NO PROBADO
- [ ] Fase 3 (Entidades): NO PROBADO
- [ ] Fase 4 (Hechos): NO PROBADO
- [ ] Fase 5 (Datos): NO PROBADO
- [ ] Fase 6 (Citas): NO PROBADO
- [ ] Fase 7 (Normalización): NO PROBADO
- [ ] Persistencia Supabase: NO PROBADO

---

## 🔬 MÉTODO DE HIPÓTESIS MÚLTIPLES - METODOLOGÍA UNIVERSAL

### 🎯 REGLA DE ORO
"Un error NUNCA tiene una sola causa posible. Quien asume la primera explicación, falla."

### 📊 PROCESO OBLIGATORIO PARA CUALQUIER PROBLEMA

#### 1️⃣ GENERAR TODAS LAS HIPÓTESIS POSIBLES (mínimo 4)
Antes de tocar CUALQUIER código, listar TODAS las posibles explicaciones.

#### 2️⃣ VERIFICAR CADA HIPÓTESIS SISTEMÁTICAMENTE
Para CADA hipótesis, verificar:
- **Código fuente**: modelos, transformaciones, flujo de datos
- **Base de datos**: esquemas, funciones, tipos de datos
- **Tests**: qué esperan, qué validan
- **Runtime**: logs, comportamiento real
- **Documentación**: READMEs, comentarios, prompts

#### 3️⃣ DOCUMENTAR EVIDENCIA
```
H1: [Hipótesis 1]
   ✓ Verificado: [qué se verificó]
   ✓ Resultado: [qué se encontró]
   → Conclusión: [confirmada/descartada]

H2: [Hipótesis 2]
   ✓ Verificado: [qué se verificó]
   ✗ Resultado: [qué NO se encontró]
   → Conclusión: [descartada]
```

#### 4️⃣ SÍNTESIS FINAL
Solo después de verificar TODAS las hipótesis:
- Causa raíz real identificada con certeza
- Solución correcta basada en evidencia
- Riesgos y efectos secundarios mapeados

### 🛑 PROHIBICIONES ABSOLUTAS
- ❌ **PROHIBIDO** asumir la primera explicación
- ❌ **PROHIBIDO** hacer cambios sin verificar TODAS las hipótesis
- ❌ **PROHIBIDO** confiar en intuición sin evidencia
- ❌ **PROHIBIDO** saltarse verificación de Supabase para errores de datos

### 📦 EJEMPLOS DE APLICACIÓN

**ERROR: "has no attribute 'fecha_inicio'"**
- H1: No existe en modelo Python → verificar modelo
- H2: Existe en BD con otro nombre/formato → verificar esquema Supabase
- H3: Se pierde en transformación → verificar pipeline completo
- H4: Error de tipado/importación → verificar imports y tipos
- H5: Campo opcional no inicializado → verificar inicialización

**PROBLEMA: "Pipeline es lento"**
- H1: LLM calls toman mucho tiempo → medir tiempos
- H2: Queries Supabase ineficientes → analizar queries
- H3: Falta de concurrencia → revisar paralelización
- H4: Transformaciones costosas → perfilar código
- H5: Problema de red/infraestructura → verificar latencia

### 🤖 TRIGGERS AUTOMÁTICOS
- `"keyword argument"` → Método Hipótesis Múltiples
- `"has no attribute"` → Método Hipótesis Múltiples + Supabase PRIMERO
- `"cannot import"` → Método Hipótesis Múltiples
- `"NameError"` → Método Hipótesis Múltiples
- `"missing required field"` → Método Hipótesis Múltiples + Supabase PRIMERO

---

## 🏁 CRITERIOS DE FINALIZACIÓN

### ✅ Criterios de Éxito (TODOS deben cumplirse):
- [ ] **Procesamiento exitoso** de artículo mediano con persistencia en Supabase
- [ ] **Evidencia** de procesamiento de artículos de diferentes tamaños
- [ ] **Procesamiento en cola** de varios artículos exitoso
- [ ] **Manejo de errores** con graceful fallback funcionando
- [ ] **Sin errores CRITICAL/HIGH** activos
- [ ] **Automated Triggers** validado en al menos 1 error

### 🚨 Criterios de Escalamiento:
- [ ] >10 errores críticos encontrados → PARAR Y REEVALUAR
- [ ] Cualquier error individual >1 hora → ESCALAR
- [ ] Problemas de infraestructura (Docker, BD, APIs) → REVISAR SETUP
- [ ] Performance >50% peor que baseline → ANÁLISIS PROFUNDO

### 🧪 Test de Validación Final:
```bash
# Test con artículo mediano
curl -X POST http://localhost:8000/api/v1/pipeline/process-article \
  -H "Content-Type: application/json" \
  -d @test_articles/json/article_infobae_20250708_191908_mas-de-30-muertos-y-un-centenar-de-heridos-durante_663a5cfe.json

# Criterios de éxito:
# - HTTP 200/202
# - persistencia.exitosa: true
# - Sin errores en logs
# - Datos en Supabase verificables
```

---

## 📚 REGISTRO HISTÓRICO Y LECCIONES APRENDIDAS

<details>
<summary>Ver historial de diagnóstico y fixes</summary>

### Sesión 2025-01-18
- **Inicio**: Creación del PRP
- **Contexto**: Pipeline con 7 fases, debe procesar artículos y persistir en Supabase

### 🎯 EJEMPLOS DE APLICACIÓN DEL MÉTODO

### CASO E001: Lo que NO hacer vs Lo CORRECTO
**MAL DIAGNÓSTICO (lo que hice):**
1. Vi "keyword argument 'nombre'" en fase_7_normalizacion.py:384
2. Asumí que debía cambiar a "nombre_entidad"
3. Hice el cambio inmediatamente SIN verificar
4. No verifiqué si `normalizar_entidad` existía en Supabase
5. No revisé los tests ni el flujo real

**DIAGNÓSTICO CORRECTO (lo que debí hacer):**
1. FASE 1: Entender que `normalizar_entidad` se llama como RPC en Supabase
2. FASE 2: Verificar en Supabase → Descubrir que NO EXISTE tal función
3. FASE 2: Buscar el flujo real → Encontrar que usa `buscar_entidad_similar`
4. FASE 2: Confirmar parámetros correctos: `nombre_entidad`, `tipo_entidad`
5. FASE 2: Verificar retorno esperado: `es_nueva` no `encontrada`
6. FASE 3: Planear cambio completo con todos los campos correctos
7. FASE 3: Ejecutar solo después de validación completa

**LECCIÓN**: Un diagnóstico apresurado casi rompe más el sistema. Solo la intervención del usuario evitó un desastre mayor.

### CASO E002: Aplicación del Método ✅ RESUELTO
**Error**: 'MetadatosHecho' object has no attribute 'fecha_inicio'

**HIPÓTESIS GENERADAS**:
- H1: MetadatosHecho no tiene campos fecha_inicio/fecha_fin
- H2: Supabase usa otro formato para las fechas
- H3: La transformación de fechas ocurre en otro lugar
- H4: Los campos son opcionales y no siempre existen
- H5: Hay un mismatch entre lo que devuelve el LLM y lo que espera el código

**VERIFICACIONES REALIZADAS**:
- H1: ✓ Confirmado - MetadatosHecho NO tenía estos campos
- H2: ✓ Confirmado - Supabase usa 'fecha_ocurrencia' tipo tstzrange
- H3: ✗ Descartado - Transformación sí ocurre en pipeline_coordinator
- H4: ✓ Confirmado - Los campos son opcionales
- H5: ✓ Confirmado - LLM devuelve fecha.inicio/fin, código esperaba fecha_inicio/fin

**SOLUCIÓN IMPLEMENTADA**:
1. Añadidos campos fecha_inicio y fecha_fin a MetadatosHecho en metadatos.py
2. Actualizada fase_4_hechos.py para extraer y asignar las fechas del JSON
3. Actualizado pipeline_coordinator.py para transformar fechas a ISO 8601

**PATRÓN DETECTADO Y RESUELTO**:
- Mismo problema en fase_5_datos.py con MetadatosDato
- Intentaba asignar periodo_inicio/fin directamente en lugar de usar objeto PeriodoReferencia
- Campos 'indicador' y 'hecho_id_relacionado' no existen en el modelo
- Solución: Crear objeto PeriodoReferencia con las fechas y eliminar campos inexistentes

</details>

---

## 📋 CONFIGURACIÓN Y SALVAGUARDAS

### Checkpoints Git:
- `debug-20250118-0202` (branch actual)
- Crear checkpoint antes de cada fix

### Archivos Críticos:
- `/src/module_pipeline/src/controller.py` - Orquestador principal
- `/src/module_pipeline/src/pipeline/pipeline_coordinator.py` - Coordinador 7 fases
- `/src/module_pipeline/src/utils/fragment_processor.py` - Gestión de IDs
- `/src/module_pipeline/src/services/supabase_service.py` - Persistencia

### Variables de Entorno Requeridas:
- `GROQ_API_KEY` - Para LLM
- `SUPABASE_URL` - URL de la BD
- `SUPABASE_ANON_KEY` - Key de acceso

### Artículos de Prueba:
- **Pequeño**: `article_infobae_20250709_000710_*.json` (~500 palabras)
- **Mediano**: `article_infobae_20250708_191908_*.json` (~1000 palabras)
- **Grande**: `article_infobae_20250708_235500_*.json` (~2000 palabras)

---

## 🎯 PLAN DE ACCIÓN INMEDIATO

### Fase 1: Diagnóstico Inicial (ACTUAL)
1. Verificar que el servicio esté levantado
2. Probar endpoint básico de health
3. Intentar procesar un artículo pequeño
4. Documentar TODOS los errores encontrados

### Fase 2: Corrección Sistemática
1. Ordenar errores por criticidad
2. Aplicar Automated Triggers
3. Fix integral por categoría
4. Validar después de cada fix

### Fase 3: Validación Final
1. Procesar artículos de diferentes tamaños
2. Verificar persistencia en Supabase
3. Probar procesamiento en cola
4. Documentar evidencias de éxito

---

> **Filosofía**: "Solo arreglar lo que está roto. Si funciona, no tocar."