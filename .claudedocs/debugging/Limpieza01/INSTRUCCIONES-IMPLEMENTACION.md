# INSTRUCCIONES DE IMPLEMENTACIÓN: Corrección de Inconsistencias de Nomenclatura

## Resumen del Análisis
Tras un análisis exhaustivo (sin sesgo de confirmación), se encontraron inconsistencias de nomenclatura en:
1. **ENTIDADES**: ❌ Pipeline envía sin sufijo, RPC espera con sufijo (CRÍTICO - causa error actual)
2. **HECHOS**: ✅ Consistente
3. **CITAS**: ✅ Consistente  
4. **DATOS CUANTITATIVOS**: ⚠️ Pipeline envía campos diferentes a los que espera la RPC

## Archivos Creados
- `ANALISIS-COMPLETO-INCONSISTENCIAS.md`: Análisis detallado de todas las inconsistencias
- `PLAN-SOLUCION-COMPLETA.md`: Plan integral de solución
- `fix_entity_field_names.sql`: Migración SQL lista para aplicar

## PASO 1: Aplicar Corrección Inmediata (CRÍTICO)

### Opción A: Usando Supabase CLI (Recomendado)
```bash
# 1. Aplicar la migración
supabase migration new fix_entity_field_names
cp .claudedocs/debugging/Limpieza01/fix_entity_field_names.sql supabase/migrations/[timestamp]_fix_entity_field_names.sql

# 2. Aplicar a la base de datos
supabase db push
```

### Opción B: Aplicación Directa en Supabase Dashboard
1. Ir a Supabase Dashboard → SQL Editor
2. Copiar todo el contenido de `fix_entity_field_names.sql`
3. Ejecutar

## PASO 2: Verificar la Corrección
```bash
# Reconstruir el contenedor del pipeline
docker-compose build module_pipeline

# Ejecutar prueba con un artículo
docker-compose run --rm module_pipeline python run_single_article.py test_article_relevante.json
```

## PASO 3: Monitorear Resultados
Verificar en los logs:
1. No debe aparecer el error "null value in column 'nombre' of relation 'entidades'"
2. Las entidades deben insertarse correctamente
3. Si hay datos cuantitativos, verificar que se inserten (pueden tener valores NULL en indicador/categoria)

## PASO 4: Corrección de Datos Cuantitativos (Opcional)
Si se procesan datos cuantitativos, actualizar `pipeline_coordinator.py` línea ~850:
```python
datos_data.append({
    "id_temporal_dato": f"{articulo_id}_dato_{idx}",
    "indicador_dato": dato.descripcion_dato,  # Mapear
    "categoria_dato": "general",               # Valor por defecto
    "valor_dato": dato.valor_dato,
    "unidad_dato": dato.unidad_dato,
    "tendencia_dato": None,
    # ... resto de campos
})
```

## Cambios Principales en la RPC
La migración corrige:
1. **Línea 117-119**: Campos de entidades ahora sin sufijo
2. **Línea 125**: Usa `relevancia_entidad_articulo` en lugar de `relevancia_entidad`
3. **Línea 136**: Maneja tanto `id_temporal_entidad` como `id` para el mapeo
4. **Línea 322-323**: Datos cuantitativos con fallback a `descripcion_dato`

## Principio de Consistencia Absoluta
- **Fuente de Verdad**: Tabla `entidades` en Supabase
- **Regla**: Los campos JSON deben coincidir con las columnas de la BD
- **Aplicación**: Consistente en todo el flujo: prompt → pipeline → RPC → BD

## Notas Importantes
- La migración es backward-compatible con los datos existentes
- No afecta hechos, citas ni relaciones (ya son consistentes)
- Mejora el manejo de datos cuantitativos con valores por defecto

## Siguiente Iteración
Una vez verificado el funcionamiento, considerar:
1. Documentar la convención de nomenclatura en README
2. Agregar tests de integración
3. Crear script de validación de consistencia