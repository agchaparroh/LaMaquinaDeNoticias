# PLAN DE SOLUCIÓN COMPLETA: Consistencia Absoluta en Nomenclatura

## Resumen de Inconsistencias Encontradas

### 1. ENTIDADES ❌
- **Pipeline**: `nombre`, `tipo`, `descripcion`
- **RPC**: `nombre_entidad`, `tipo_entidad`, `descripcion_entidad`
- **Impacto**: Error "null value in column 'nombre'"

### 2. HECHOS ✅
- Consistente: ambos usan sufijo `_hecho`

### 3. CITAS ✅
- Consistente: ambos usan sufijo `_cita`

### 4. DATOS CUANTITATIVOS ⚠️
- **Pipeline**: Envía `descripcion_dato`
- **RPC**: Espera `indicador_dato` y `categoria_dato`
- **Impacto**: Posibles valores NULL en campos requeridos

## Plan de Implementación

### FASE 1: Corrección de Entidades (CRÍTICA)

#### Archivo: `/BaseDeDatos_SUPABASE/funciones/actualizar_articulo_procesado.sql`
**Líneas a modificar: 117-126**

```sql
-- CAMBIAR DE:
VALUES (
    v_entidad->>'nombre_entidad',      -- ❌
    v_entidad->>'tipo_entidad',        -- ❌
    v_entidad->>'descripcion_entidad', -- ❌
    CASE 
        WHEN v_entidad ? 'alias' 
        THEN ARRAY(SELECT jsonb_array_elements_text(v_entidad->'alias'))
        ELSE NULL 
    END,
    COALESCE((v_entidad->>'relevancia_entidad')::INTEGER, 5),
    v_entidad->'metadata_entidad'
)

-- A:
VALUES (
    v_entidad->>'nombre',              -- ✅
    v_entidad->>'tipo',                -- ✅
    v_entidad->>'descripcion',         -- ✅
    CASE 
        WHEN v_entidad ? 'alias' 
        THEN ARRAY(SELECT jsonb_array_elements_text(v_entidad->'alias'))
        ELSE NULL 
    END,
    COALESCE((v_entidad->>'relevancia_entidad_articulo')::INTEGER, 5), -- ✅ Campo correcto
    v_entidad->'metadata_entidad'
)
```

### FASE 2: Corrección de Datos Cuantitativos

#### Opción A: Modificar Pipeline (RECOMENDADA)
**Archivo**: `/src/module_pipeline/src/pipeline/pipeline_coordinator.py`
**Líneas aproximadas: 850-860**

```python
# Agregar mapeo de campos en pipeline_coordinator.py
datos_data.append({
    "id_temporal_dato": f"{articulo_id}_dato_{idx}",
    "indicador_dato": dato.descripcion_dato,  # Mapear descripcion → indicador
    "categoria_dato": getattr(dato, 'categoria', 'general'),  # Usar campo si existe
    "valor_dato": dato.valor_dato,
    "unidad_dato": dato.unidad_dato,
    "tendencia_dato": getattr(dato, 'tendencia', None),  # Agregar campo
    "fecha_dato": dato.fecha_dato,
    "contexto_dato": dato.contexto_dato,
    "relevancia_dato": dato.relevancia_dato,
    "hecho_principal_relacionado_id_temporal": dato.hecho_principal_relacionado_id_temporal
})
```

#### Opción B: Modificar RPC (Alternativa)
**Archivo**: `/BaseDeDatos_SUPABASE/funciones/actualizar_articulo_procesado.sql`
**Líneas: 322-323**

```sql
-- CAMBIAR DE:
v_dato->>'indicador_dato',
v_dato->>'categoria_dato',

-- A:
COALESCE(v_dato->>'indicador_dato', v_dato->>'descripcion_dato'),
COALESCE(v_dato->>'categoria_dato', 'general'),
```

### FASE 3: Actualización de Modelo Pydantic

**Archivo**: `/src/module_pipeline/src/models/persistencia.py`
**Agregar campos deprecados para transición suave**

```python
class DatoCuantitativoExtraidoItem(PersistenciaBaseModel):
    # ... campos existentes ...
    
    # Agregar para compatibilidad con RPC
    indicador_dato: Optional[str] = Field(default=None, description="Alias para descripcion_dato")
    categoria_dato: Optional[str] = Field(default=None, description="Categoría del dato")
    tendencia_dato: Optional[str] = Field(default=None, description="Tendencia observada")
    
    @model_validator(mode='before')
    def set_indicador_from_descripcion(cls, values):
        if 'indicador_dato' not in values and 'descripcion_dato' in values:
            values['indicador_dato'] = values['descripcion_dato']
        return values
```

## Orden de Implementación

1. **INMEDIATO**: Actualizar RPC para entidades (soluciona error actual)
2. **SIGUIENTE**: Implementar mapeo de datos cuantitativos
3. **OPCIONAL**: Actualizar modelo Pydantic para mayor robustez

## Comandos de Despliegue

```bash
# 1. Actualizar función RPC en Supabase
supabase db diff --use-migra -f fix_entity_field_names

# 2. Reconstruir pipeline si se modifica código Python
docker-compose build module_pipeline

# 3. Ejecutar prueba completa
docker-compose run --rm module_pipeline python run_single_article.py test_article.json
```

## Validación Post-Implementación

1. Verificar que no hay errores de "null value"
2. Confirmar inserción correcta de entidades
3. Validar datos cuantitativos si se procesan
4. Revisar logs para warnings o errores

## Principio de Consistencia Futura

**REGLA**: Los nombres de campos en el payload JSON deben coincidir EXACTAMENTE con los nombres de columnas en la base de datos, siguiendo el principio de "Database as Single Source of Truth".

### Convención Propuesta:
- Entidades: Sin sufijo (nombre, tipo, descripcion)
- Hechos: Con sufijo (descripcion_hecho, tipo_hecho)
- Citas: Con sufijo (texto_cita, contexto_cita)
- Datos: Con sufijo (indicador_dato, valor_dato)

Esta convención ya existe parcialmente pero debe documentarse y aplicarse consistentemente.