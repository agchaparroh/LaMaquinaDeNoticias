# 🚨 PRP: Error Elimination - module_pipeline
> **Fecha**: 2025-01-18  
> **Tipo**: debugging-no-destructivo  
> **Prioridad**: CRITICAL

## 🎯 ACCIÓN INMEDIATA - Diagnóstico inicial del pipeline

### Paso Actual:
```bash
# 1. Verificar estado de servicios y containers
docker ps | grep -E "pipeline|supabase|groq"

# 2. Health check del módulo
curl -X GET http://localhost:8003/health -v

# 3. Verificar logs de errores recientes
docker logs module-pipeline --tail 100 2>&1 | grep -E "ERROR|CRITICAL|Exception"
```

## 📊 ESTADO ACTUAL
- **Errores encontrados**: 1
- **Errores resueltos**: 0  
- **Error en progreso**: E001 - UUID malformado
- **Tiempo estimado**: 2-4 horas

## 🤖 AUTOMATED TRIGGERS ACTIVOS

### Trigger Pattern Matching:
Si el error contiene: `["keyword argument", "has no attribute", "cannot import", "NameError", "signature mismatch", "TypeError", "AttributeError"]`

**PROTOCOLO AUTOMÁTICO:**
1. ⛔ **STOP** - No hacer fix parcial
2. 🔍 **Task tool**: buscar patrón en TODA la codebase
3. 📊 **Mapear scope**: identificar TODOS los archivos afectados
4. 🔧 **MultiEdit**: aplicar cambios de una vez
5. ✅ **Test final**: validación completa

## 🏁 CRITERIOS DE FINALIZACIÓN

### ✅ Éxito (TODOS requeridos):
- [ ] Procesamiento exitoso de artículo tamaño medio + persistencia en Supabase
- [ ] Evidencias del procesamiento exitoso de artículos de diferentes tamaños
- [ ] Éxito en el procesamiento de varios artículos en cola
- [ ] Manejo correcto de errores con graceful degradation

### 🚨 Escalamiento (si ALGUNO ocurre):
- [ ] >10 errores críticos encontrados
- [ ] Cualquier error >1 hora de debug
- [ ] Problemas de infraestructura
- [ ] Performance degradada >50%

## 📚 REGISTRO HISTÓRICO
<details>
<summary>Ver historial de errores resueltos</summary>

### Pendiente de actualizar...

</details>

## ⚖️ NORMAS DE DEBUGGING (Recordatorio)
1. **Robustez**: Soluciones sostenibles, no parches
2. **Simplicidad**: No sobreingeniería, lo simple es mejor
3. **No destructivo**: Entender 100% antes de cambiar

## 📋 ARTÍCULOS DE PRUEBA DISPONIBLES
- test_articles/json/: Artículos de diferentes tamaños para pruebas
  - Pequeño: ~1KB
  - Medio: ~5KB  
  - Grande: ~10KB+