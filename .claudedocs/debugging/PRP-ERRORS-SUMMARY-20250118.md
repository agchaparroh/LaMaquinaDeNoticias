# Resumen de Errores Encontrados - PRP Pipeline 2025-01-18

## Estado del Pipeline

### ✅ Errores Corregidos (4/5)
1. **ERROR 1: ValidationError - Campo 'titulo' vs 'titular'**
2. **ERROR 2: KeyError en logging - f-strings con llaves**
3. **ERROR 3: NameError 'fragmento' en pipeline_coordinator.py**
4. **ERROR 4: NameError 'fragmento' en controller.py línea 329**

### ❌ Error Pendiente (1/5)
5. **ERROR 5: Fallo en persistencia - Campos requeridos faltantes**

## Detalle de Errores Encontrados

### ERROR 1: ValidationError - Mapeo de campos
- **Archivo**: `controller.py`
- **Línea**: 195-200
- **Problema**: JSON de prueba tenía 'titulo' pero modelo esperaba 'titular'
- **Solución**: Mapeo robusto de campos con fallback
- **Estado**: ✅ CORREGIDO

### ERROR 2: KeyError en logging
- **Archivo**: `fase_1_triaje.py`
- **Línea**: 95
- **Problema**: f-string con llaves en loguru: `f"texto: {texto[:100]}..."` 
- **Solución**: Usar parámetros estructurados de loguru
- **Estado**: ✅ CORREGIDO

### ERROR 3: NameError 'fragmento'
- **Archivo**: `pipeline_coordinator.py`
- **Línea**: 431
- **Problema**: Variable nombrada 'fragmento_unificado' pero usada como 'fragmento'
- **Solución**: Cambiar a nombre correcto de variable
- **Estado**: ✅ CORREGIDO

### ERROR 4: NameError 'fragmento' en controller
- **Archivo**: `controller.py`
- **Línea**: 329
- **Problema**: Usaba 'fragmento' pero la variable era 'articulo'
- **Solución**: Usar nombre correcto de variable
- **Estado**: ✅ CORREGIDO

### ERROR 5: Fallo en persistencia de artículos
- **Archivo**: Múltiples (`pipeline_coordinator.py`, `payload_builder.py`, `supabase_service.py`)
- **Problema**: Pipeline genera payload de fragmento pero intenta persistir como artículo
- **Causa raíz**: 
  - Pipeline siempre llama `construir_payload_fragmento` (línea 626)
  - Conversión ArticuloProcesableItem → FragmentoProcesableItem pierde campos
  - Nombres de campos incompatibles (sufijo _fragmento)
- **Estado**: ❌ PENDIENTE - Diagnóstico completo documentado

## Arquitectura Descubierta

### Diseño Híbrido Actual
- Artículos se procesan internamente como fragmentos
- Se pierde información crítica durante la conversión
- Intento de persistir como artículo falla por campos faltantes

### Flujo Actual
```
ArticuloInItem → ArticuloProcesableItem → FragmentoProcesableItem → 
7 Fases → Payload Fragmento → Intento persistir como Artículo → ERROR
```

## Próximos Pasos

1. **Implementar solución para ERROR 5**:
   - Modificar pipeline para generar payload correcto según tipo
   - Preservar ArticuloProcesableItem hasta el final
   - Corregir bug en construir_payload_articulo_from_model

2. **Validación completa**:
   - Procesar artículos de diferentes tamaños
   - Verificar persistencia en Supabase
   - Probar procesamiento en cola

3. **Actualizar Docker**:
   - Reconstruir imagen con ERROR 5 corregido
   - Deploy en producción

## Lecciones Aprendidas

1. **Conversión de tipos pierde información crítica**
2. **Diseño híbrido artículo/fragmento necesita revisión**
3. **Validación temprana de campos evitaría errores tardíos**
4. **Tests end-to-end habrían detectado estos problemas**