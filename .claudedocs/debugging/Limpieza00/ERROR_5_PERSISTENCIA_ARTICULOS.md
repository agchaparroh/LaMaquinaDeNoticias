# ERROR 5: FALLO EN PERSISTENCIA DE ARTÍCULOS

## RESUMEN EJECUTIVO

**Error**: `Campos requeridos faltantes en payload articulo`  
**Ubicación**: `supabase_service.insertar_articulo_completo` (línea 279)  
**Impacto**: Pipeline procesa exitosamente las 7 fases pero NO puede persistir artículos  
**Síntoma**: RPC de Supabase rechaza el payload por campos faltantes  

## CONTEXTO DEL ERROR

### Flujo Actual
1. ✅ Artículo entra como `ArticuloProcesableItem` 
2. ✅ Se convierte a `FragmentoProcesableItem` para procesamiento
3. ✅ 7 fases procesan correctamente (triaje, simplificación, entidades, hechos, normalización)
4. ✅ Se detecta que es artículo: `es_articulo_completo = True`
5. ✅ Se intenta persistir con `insertar_articulo_completo`
6. ❌ **FALLA**: Payload no tiene campos requeridos para artículo

### Evidencia del Log
```
2025-07-18 19:30:27.907 | Detectado artículo completo desde metadatos del pipeline
2025-07-18 19:30:27.911 | Persistiendo como artículo completo
2025-07-18 19:30:27.914 | ERROR: Campos requeridos faltantes en payload articulo
```

## HIPÓTESIS MÚLTIPLES (Ordenadas por Probabilidad)

### 🔴 H1: Pipeline genera payload de fragmento, no de artículo (90% probabilidad)
**Evidencia a verificar**:
- `_generar_payload_completo_7_fases` (línea 626) llama a `construir_payload_fragmento`
- Existe `construir_payload_articulo_from_model` pero NUNCA se usa
- El payload tiene campos con sufijo `_fragmento` (incompatible con artículos)

**Verificación necesaria**:
```bash
# Ver qué método de PayloadBuilder se llama
grep -n "construir_payload" pipeline_coordinator.py

# Ver estructura del payload generado
# Buscar en logs: "Checksum del payload"
```

### 🟡 H2: Campos del artículo se pierden en conversión (80% probabilidad)
**Evidencia a verificar**:
- ArticuloProcesableItem → FragmentoProcesableItem (línea 114)
- Solo se copian: id, texto, metadata_adicional
- Se pierden: url, titular, medio, autor, seccion, etc.

**Verificación necesaria**:
```python
# En pipeline_coordinator.py línea 114-120
# ¿Qué campos NO se están copiando?
# ¿Dónde están los campos del artículo original?
```

### 🟡 H3: Incompatibilidad de nomenclatura de campos (70% probabilidad)
**Evidencia a verificar**:
- Payload tiene: `resumen_generado_fragmento`, `estado_procesamiento_final_fragmento`
- RPC espera: `resumen_generado`, `estado_procesamiento_final` (sin sufijo)
- Mismatch total en nombres de campos

**Verificación necesaria**:
```sql
-- En Supabase, ver definición de insertar_articulo_completo
-- ¿Qué campos son obligatorios?
-- ¿Cuáles son los nombres exactos?
```

### 🟢 H4: RPC espera estructura diferente (60% probabilidad)
**Evidencia a verificar**:
- insertar_articulo_completo espera campos de ArticuloProcesableItem
- insertar_fragmento_completo espera campos de FragmentoPersistenciaPayload
- Son estructuras completamente diferentes

**Verificación necesaria**:
```python
# Comparar modelos:
# - FragmentoPersistenciaPayload
# - PayloadCompletoArticulo (si existe)
# - Parámetros de la RPC
```

### 🟢 H5: Metadata no preservada en el flujo (50% probabilidad)
**Evidencia a verificar**:
- metadata_adicional del FragmentoProcesableItem
- ¿Contiene los campos del artículo original?
- ¿Se propagan hasta el payload final?

**Verificación necesaria**:
```python
# Rastrear metadata_adicional:
# 1. ArticuloProcesableItem.metadata_adicional
# 2. FragmentoProcesableItem.metadata_adicional  
# 3. Payload final
```

### 🔵 H6: Validación en Supabase es más estricta (40% probabilidad)
**Evidencia a verificar**:
- La RPC valida campos que Python no verifica
- Campos opcionales en Python pero obligatorios en PostgreSQL
- Tipos de datos incompatibles

**Verificación necesaria**:
```sql
-- Ver función insertar_articulo_completo en Supabase
-- Identificar validaciones y campos NOT NULL
```

### 🔵 H7: Error en mapeo de ArticuloProcesableItem (30% probabilidad)
**Evidencia a verificar**:
- El objeto ArticuloProcesableItem podría no tener todos los campos
- Controller podría no estar mapeando correctamente desde el JSON

**Verificación necesaria**:
```python
# En controller.py líneas 206-223
# ¿Están todos los campos requeridos?
# ¿Hay campos que faltan en el mapeo?
```

## DIAGNÓSTICO REQUERIDO

### PASO 1: Identificar payload generado vs esperado
```python
# 1. Capturar el payload que se está generando
# 2. Obtener esquema de insertar_articulo_completo desde Supabase
# 3. Comparar campo por campo
```

### PASO 2: Rastrear pérdida de información
```python
# Seguir los datos desde ArticuloProcesableItem hasta el payload:
# 1. ArticuloProcesableItem (controller.py:238)
# 2. FragmentoProcesableItem (pipeline_coordinator.py:114)
# 3. Payload final (_generar_payload_completo_7_fases)
# 4. Qué campos se pierden en cada paso
```

### PASO 3: Verificar método de construcción de payload
```python
# 1. ¿Por qué se usa construir_payload_fragmento?
# 2. ¿Cuándo debería usar construir_payload_articulo_from_model?
# 3. ¿Existe lógica condicional para elegir el método correcto?
```

## SOLUCIÓN ESPERADA (NO IMPLEMENTAR)

Basado en el diagnóstico, la solución probablemente requerirá:

1. **Opción A**: Modificar `_generar_payload_completo_7_fases` para que:
   - Detecte si es artículo (desde metadatos)
   - Use `construir_payload_articulo_from_model` en lugar de `construir_payload_fragmento`

2. **Opción B**: Preservar campos del artículo durante la conversión:
   - Copiar TODOS los campos a metadata_adicional
   - Recuperarlos al construir el payload

3. **Opción C**: Crear un método paralelo para artículos:
   - `_generar_payload_articulo_7_fases`
   - Que mantenga la estructura original del artículo

## IMPACTO Y PRIORIDAD

- **Prioridad**: CRÍTICA
- **Impacto**: Los artículos se procesan pero NO se guardan
- **Afecta**: 100% de los artículos procesados
- **Workaround**: No existe (la persistencia es esencial)

## CHECKLIST DE VERIFICACIÓN

- [ ] Obtener definición exacta de insertar_articulo_completo desde Supabase
- [ ] Capturar payload completo que se está enviando
- [ ] Identificar campos faltantes específicos
- [ ] Rastrear dónde se pierden los campos del artículo
- [ ] Verificar si construir_payload_articulo_from_model tiene los campos correctos
- [ ] Confirmar que ArticuloProcesableItem tiene todos los campos necesarios
- [ ] Revisar si hay transformación de nombres de campos

## NOTAS ADICIONALES

1. El pipeline funciona perfectamente hasta el momento de persistir
2. La detección de tipo (artículo vs fragmento) funciona correctamente
3. El problema es puramente de estructura de datos/payload
4. PayloadBuilder tiene métodos separados pero no se usan correctamente