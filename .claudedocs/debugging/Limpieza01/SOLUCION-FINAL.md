# SOLUCIÓN FINAL: Error "null value in column 'nombre' of relation 'entidades'"

## Diagnóstico Completo

### El Problema
Error: `null value in column "nombre" of relation "entidades" violates not-null constraint`

### Causa Raíz
Existe una inconsistencia de nomenclatura entre:
1. **Pipeline** (pipeline_coordinator.py): Envía campos SIN sufijo: `nombre`, `tipo`, `descripcion`
2. **RPC** (actualizar_articulo_procesado.sql): Espera campos CON sufijo: `nombre_entidad`, `tipo_entidad`, `descripcion_entidad`

### Flujo de Datos
```
DB (entidades)      → Prompt         → Pipeline       → RPC
nombre              → nombre         → nombre         → busca nombre_entidad ❌
tipo                → tipo           → tipo           → busca tipo_entidad ❌
descripcion         → descripcion    → descripcion    → busca descripcion_entidad ❌
```

## Solución Implementada

### Opción Correcta: Modificar la RPC
La solución correcta es modificar la función RPC `actualizar_articulo_procesado` para que espere los mismos campos que la base de datos (sin sufijo "_entidad").

### Cambios Requeridos en actualizar_articulo_procesado.sql

**ANTES** (línea 117):
```sql
INSERT INTO entidades (nombre, tipo, descripcion, alias, relevancia, metadata)
VALUES (
    v_entidad->>'nombre_entidad',      -- ❌ Busca con sufijo
    v_entidad->>'tipo_entidad',        -- ❌ Busca con sufijo
    v_entidad->>'descripcion_entidad', -- ❌ Busca con sufijo
    ARRAY(SELECT jsonb_array_elements_text(v_entidad->'alias')),
    COALESCE((v_entidad->>'relevancia_entidad')::INTEGER, 5),
    v_entidad->'metadata_entidad'
)
```

**DESPUÉS**:
```sql
INSERT INTO entidades (nombre, tipo, descripcion, alias, relevancia, metadata)
VALUES (
    v_entidad->>'nombre',              -- ✅ Sin sufijo
    v_entidad->>'tipo',                -- ✅ Sin sufijo
    v_entidad->>'descripcion',         -- ✅ Sin sufijo
    ARRAY(SELECT jsonb_array_elements_text(v_entidad->'alias')),
    COALESCE((v_entidad->>'relevancia_entidad')::INTEGER, 5),
    v_entidad->'metadata_entidad'
)
```

### Por qué esta es la solución correcta

1. **Mantiene consistencia con la base de datos**: La tabla `entidades` usa campos sin sufijo
2. **Consistencia con el modelo Pydantic**: `EntidadAutonomaItem` espera campos sin sufijo
3. **Minimiza cambios**: Solo requiere modificar la RPC, no el código Python
4. **Respeta la fuente de verdad**: Como se indicó, "la tabla entidades en supabase debe ser fuente de verdad absoluta"

## Estado Actual

- Pipeline: Envía campos sin sufijo ✅
- Modelo Pydantic: Espera campos sin sufijo ✅
- Base de datos: Tiene campos sin sufijo ✅
- RPC: Espera campos con sufijo ❌ (NECESITA ACTUALIZACIÓN)

## Próximos Pasos

1. Actualizar la función RPC `actualizar_articulo_procesado` en Supabase
2. Ejecutar prueba completa del pipeline
3. Documentar la arquitectura para evitar futuras inconsistencias