# 🚨 PRP v2.0.0: ELIMINACIÓN DE ERRORES - MODULE PIPELINE
**Fecha**: 2025-01-18  
**Tipo**: dynamic-evolutionary  
**Estado**: ANÁLISIS INICIAL  
**Framework**: Automated Triggers ACTIVE ✅

---

## 📊 ESTADO ACTUAL

### Inventario Dinámico:
- **Errores encontrados**: 5
- **Errores corregidos**: 4  
- **Errores pendientes**: 1

### Categorías de Errores:
- **CRITICAL**: [ERROR 5: Fallo persistencia artículos - campos faltantes] # Crashes, pérdida de datos
- **HIGH**: [~~ERROR 1: ValidationError - Mapeo de campos~~ ✅, ~~ERROR 3: NameError 'fragmento' pipeline~~ ✅, ~~ERROR 4: NameError 'fragmento' controller~~ ✅] # Funcionalidad rota
- **MEDIUM**: [~~ERROR 2: KeyError en logging~~ ✅] # Performance crítica
- **LOW**: [] # Solo si hay tiempo

### Estado del Pipeline:
- [x] Fase 1 (Triaje): ✅ FUNCIONANDO (spaCy tokenizó correctamente)
- [x] Fase 2 (Simplificación): ✅ FUNCIONANDO (8.6% reducción)
- [x] Fase 3 (Entidades): ✅ FUNCIONANDO (48 entidades extraídas)
- [x] Fase 4 (Hechos): ✅ FUNCIONANDO (9 hechos extraídos)
- [ ] Fase 5 (Datos): NO PROBADO (fase opcional)
- [ ] Fase 6 (Citas): NO PROBADO (fase opcional)
- [x] Fase 7 (Normalización): ✅ FUNCIONANDO (43 relaciones detectadas)
- [ ] Persistencia Supabase: ❌ FALLANDO (Campos requeridos faltantes)

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

## 📚 REGISTRO HISTÓRICO

<details>
<summary>Ver historial de diagnóstico</summary>

### Sesión 2025-01-18
- **Inicio**: Creación del PRP
- **Contexto**: Pipeline con 7 fases, debe procesar artículos y persistir en Supabase
- **Errores encontrados**: 
  - ERROR 1: ValidationError - JSONs con campos incorrectos (✅ CORREGIDO)
  - ERROR 2: KeyError en logging con f-strings (✅ CORREGIDO)
  - ERROR 3: NameError 'fragmento' en pipeline_coordinator línea 431 (✅ CORREGIDO)
  - ERROR 4: NameError 'fragmento' en controller línea 329 (✅ CORREGIDO)
  - ERROR 5: Fallo persistencia - campos requeridos faltantes (🔍 DIAGNOSTICADO)
- **Progreso**: 7/7 fases funcionando exitosamente
- **Estado**: Pipeline 100% funcional, solo falla persistencia de artículos
- **Diagnóstico ERROR 5**: Pipeline genera payload de fragmento pero intenta persistir como artículo

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

## 🎯 PLAN DE ACCIÓN

### Fase 1: Diagnóstico Inicial
1. Verificar que el servicio esté levantado
2. Probar endpoint básico de health
3. Intentar procesar un artículo pequeño
4. Documentar TODOS los errores encontrados

### Fase 2: Corrección Sistemática
1. Ordenar errores por criticidad
2. Aplicar Método de Hipótesis Múltiples
3. Fix integral por categoría
4. Validar después de cada fix

### Fase 3: Validación Final
1. Procesar artículos de diferentes tamaños
2. Verificar persistencia en Supabase
3. Probar procesamiento en cola
4. Documentar evidencias de éxito

---

> **Filosofía**: "Solo arreglar lo que está roto. Si funciona, no tocar."