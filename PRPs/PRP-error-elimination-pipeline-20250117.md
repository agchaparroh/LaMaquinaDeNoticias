# 🚨 PRP Dinámico Evolutivo: Error Elimination Protocol - Module Pipeline
**Tipo:** Dynamic-Evolutionary --ultrathink  
**Fecha:** 17-07-2025  
**Estado:** 🔴 ACTIVO  
**Módulo:** module_pipeline  
**Versión:** 1.0.0

---

## 📋 Inventario Dinámico de Errores

### Contadores en Tiempo Real
```yaml
errors_found: 1      # Auto-incrementa con cada descubrimiento
errors_fixed: 0      # Actualizado al resolver cada uno
errors_pending: 1    # Calculado: found - fixed
critical_blocks: 1   # Problemas que bloquean TODO el sistema
```

### 🔴 Errores Críticos Identificados
| ID | Severidad | Estado | Descripción | Impacto |
|----|-----------|--------|-------------|---------|
| E001 | CRITICAL | 🔴 PENDIENTE | AttributeError: 'dict' object has no attribute 'id_fragmento' | 100% artículos fallan |

### 🟡 Errores por Descubrir
- [ ] Otros errores en las 7 fases (no ejecutadas aún)
- [ ] Problemas de persistencia en Supabase
- [ ] Errores de integración con servicios externos
- [ ] Timeouts o límites de procesamiento

---

## 🎯 Objetivo Principal

**Restaurar el pipeline a funcionalidad completa** mediante:
1. Corrección sistemática de SOLO problemas paralizantes
2. Validación exhaustiva sin crear nuevos bugs
3. Documentación de cada cambio y su impacto
4. Garantía de estabilidad post-corrección

---

## 🔄 Fases de Ejecución Adaptativa

### FASE 1: Corrección del Error Crítico E001 [EN PROGRESO]

#### 1.1 Preparación
```bash
# Checkpoint de seguridad
/git --checkpoint prp-pipeline-fix-inicio

# Cargar contexto profundo
/load --context deep --module pipeline

# Crear tracking detallado
TodoWrite: "PRP Pipeline: Corregir E001 - AttributeError dict/object"
```

#### 1.2 Análisis Ultrathink
```yaml
Problema:
  - Ubicación: controller.py → pipeline_coordinator.py
  - Causa: Incompatibilidad de tipos (dict vs objeto)
  - Línea exacta: pipeline_coordinator.py:100
  
Análisis de Flujo:
  1. controller.process_article crea fragmento_data (dict)
  2. NO convierte a FragmentoProcesableItem
  3. Pasa dict directamente a pipeline_coordinator
  4. pipeline_coordinator espera objeto con atributos
  5. FALLO al acceder fragmento.id_fragmento
  
Contraste:
  - process_fragment SÍ convierte: FragmentoProcesableItem(**fragmento_data)
  - process_article NO convierte (error de implementación)
```

#### 1.3 Solución Mínima Validada
```python
# Cambio en controller.py, después de línea 214:
# AGREGAR conversión antes de llamar al pipeline
from .models.entrada import FragmentoProcesableItem

# Convertir dict a objeto Pydantic
fragmento = FragmentoProcesableItem(**fragmento_data)

# Modificar línea 225:
resultado_pipeline = self.pipeline_coordinator.ejecutar_pipeline_completo(
    fragmento=fragmento,  # Pasar objeto, no dict
    modelo_spacy="es_core_news_lg",
    request_id=request_id,
    groq_api_key=groq_api_key,
    contexto_articulo=contexto_articulo
)
```

#### 1.4 Plan de Validación
- [ ] Test unitario del cambio específico
- [ ] Ejecutar spider infobae nuevamente
- [ ] Verificar que pase a Fase 1 del pipeline
- [ ] Monitorear las 7 fases completas
- [ ] Confirmar persistencia en Supabase

### FASE 2: Búsqueda Sistemática de Otros Errores [PENDIENTE]

#### 2.1 Protocolo de Barrido
```bash
# Solo después de corregir E001
/analyze --module pipeline --critical-only --seq
/test --comprehensive --fail-on-warning false
/scan --runtime-errors --production-like
```

#### 2.2 Categorías a Evaluar
- **CRITICAL**: Crashes, pérdida de datos, seguridad
- **HIGH**: Funcionalidad bloqueada, errores 500
- **MEDIUM**: Timeouts críticos, degradación severa
- **IGNORE**: Warnings, optimizaciones, code smells

### FASE 3: Validación de Integración [FUTURA]

#### 3.1 Tests End-to-End
```yaml
Escenarios Críticos:
  - Artículo mínimo (100 chars)
  - Artículo normal (1000 chars)
  - Artículo largo con chunking (10000 chars)
  - Múltiples artículos concurrentes
  - Recuperación tras error de API
```

#### 3.2 Monitoreo en Vivo
```bash
# Observar comportamiento real
docker logs -f lamacquina_pipeline --tail 0 &
curl -X POST http://localhost:8003/procesar_articulo -d @test-article.json
```

---

## 📊 Reglas de Evolución del PRP

### Auto-Actualización
1. **Si encuentro nuevo error crítico:**
   - Pausar ejecución actual
   - Agregar a inventario con ID único
   - Re-priorizar si es más crítico
   - Continuar con nuevo plan

2. **Si un fix crea nuevo problema:**
   - Rollback inmediato
   - Documentar en "Intentos Fallidos"
   - Buscar alternativa más segura

3. **Si todo funciona:**
   - Marcar fase como ✅ COMPLETADA
   - Avanzar a siguiente fase
   - Actualizar contadores

### Criterios de Éxito
- ✅ Pipeline procesa artículos (>95% éxito)
- ✅ Las 7 fases se ejecutan sin errores
- ✅ Datos persisten en Supabase
- ✅ Sin degradación de performance
- ✅ Sin nuevos bugs introducidos

---

## 🛡️ Salvaguardas

### Puntos de No Retorno
- NUNCA modificar esquemas de BD
- NUNCA cambiar APIs sin versioning
- NUNCA ignorar tests que fallan
- NUNCA hacer cambios "mientras estamos aquí".
- NO a la sobreingeniería: Soluciones simples y robustas
- No destructivo: Construir sobre lo existente
- Sostenibilidad: Evitar parches temporales

### Rollback Inmediato Si:
- Tests existentes empiezan a fallar
- Aparecen nuevos errores no relacionados
- Performance se degrada >20%
- Cualquier pérdida de datos

---

## 📝 Registro de Cambios

### Cambio #1 [PENDIENTE]
```yaml
Fecha: 2025-07-17
Error: E001 - AttributeError dict/object
Archivos: 
  - src/controller.py (líneas ~214-225)
Cambio: Agregar conversión FragmentoProcesableItem
Estado: Por implementar
Tests: Por ejecutar
```

---

## 🎯 Comando de Ejecución

```bash
# Ejecutar este PRP con máxima profundidad
/prp --execute m/home/ec2-user/projects/LaMaquinaDeNoticias/PRPs/PRP-error-elimination-pipeline-20250117.md --ultrathink

# El sistema:
# 1. Implementará cambios uno por uno
# 2. Validará exhaustivamente cada paso
# 3. Se detendrá ante cualquier problema
# 4. Actualizará este documento dinámicamente
```

---

## 📊 Métricas de Progreso

```yaml
Inicio:
  - Artículos procesados: 0%
  - Errores críticos: 1
  - Pipeline funcional: NO

Meta:
  - Artículos procesados: >95%
  - Errores críticos: 0
  - Pipeline funcional: SÍ

Actual:
  - Artículos procesados: 0%
  - Errores críticos: 1
  - Pipeline funcional: NO
```

---

> **Principio Rector**: "Arreglar solo lo roto, preservar todo lo que funciona"

*PRP v1.0.0 - Se actualiza automáticamente con cada descubrimiento*