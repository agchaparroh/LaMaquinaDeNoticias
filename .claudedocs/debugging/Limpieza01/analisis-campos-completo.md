# Análisis Completo de Campos: Pipeline vs RPC

## Campos de Entidades

### Lo que envía el Pipeline (pipeline_coordinator.py):
```python
{
    "id": str(entidad.id_entidad),
    "nombre": entidad.nombre_entidad_normalizada or entidad.texto_entidad,
    "tipo": entidad.tipo_entidad,
    "descripcion": f"Entidad extraída con relevancia {entidad.relevancia_entidad}",
    "relevancia_entidad_articulo": int(entidad.relevancia_entidad * 10),
    "metadata_entidad": {...}
}
```

### Lo que espera la RPC (actualizar_articulo_procesado.sql):
```sql
v_entidad->>'nombre_entidad',      -- ❌ DESAJUSTE (pipeline envía "nombre")
v_entidad->>'tipo_entidad',        -- ❌ DESAJUSTE (pipeline envía "tipo")
v_entidad->>'descripcion_entidad', -- ❌ DESAJUSTE (pipeline envía "descripcion")
ARRAY(SELECT jsonb_array_elements_text(v_entidad->'alias')),
(v_entidad->>'relevancia_entidad')::INTEGER,
v_entidad->'metadata_entidad'
```

### Lo que espera el modelo EntidadAutonomaItem:
```python
id: str
nombre: str           -- ✅ Coincide con pipeline
tipo: str            -- ✅ Coincide con pipeline
descripcion: Optional[str]  -- ✅ Coincide con pipeline
alias: Optional[List[str]]
relevancia_entidad_articulo: Optional[int]  -- ✅ Coincide con pipeline
```

## PROBLEMA IDENTIFICADO

Hay una **triple inconsistencia**:
1. **Pipeline** genera campos sin sufijo `_entidad` (nombre, tipo, descripcion)
2. **Modelo Pydantic** espera campos sin sufijo
3. **RPC SQL** espera campos CON sufijo `_entidad`

## Otros Campos a Verificar

### Hechos
- Pipeline envía: `descripcion_hecho`, `tipo_hecho`, `relevancia_hecho` ✅
- RPC espera: `descripcion_hecho`, `tipo_hecho`, `relevancia_hecho` ✅
- **Estado**: CORRECTO

### Citas
- Pipeline envía: `texto_cita`, `contexto_cita`, `relevancia_cita` ✅
- RPC espera: `texto_cita`, `contexto_cita`, `relevancia_cita` ✅
- **Estado**: CORRECTO

### Datos Cuantitativos
- Pipeline envía: `descripcion_dato`, `valor_dato`, `unidad_dato` ✅
- RPC espera: `indicador_dato`, `valor_dato`, `unidad_dato` ❓
- **Estado**: POSIBLE DESAJUSTE en `descripcion_dato` vs `indicador_dato`

## Solución Integral Requerida

El problema NO es solo el campo `nombre`. Necesitamos ajustar TODOS los campos de entidades:

```python
# En pipeline_coordinator.py, cambiar:
entidades_data.append({
    "id": str(entidad.id_entidad),
    "nombre_entidad": entidad.nombre_entidad_normalizada or entidad.texto_entidad,  # Añadir _entidad
    "tipo_entidad": entidad.tipo_entidad,  # Añadir _entidad
    "descripcion_entidad": f"Entidad extraída con relevancia {entidad.relevancia_entidad}",  # Añadir _entidad
    "relevancia_entidad": int(entidad.relevancia_entidad * 10),  # Cambiar de relevancia_entidad_articulo
    "metadata_entidad": {...}  # Ya está correcto
})
```

## Impacto del Cambio

Este cambio romperá la compatibilidad con el modelo EntidadAutonomaItem, por lo que también necesitaríamos:
1. Crear un mapeo intermedio, O
2. Actualizar el modelo para aceptar ambos nombres, O
3. Bypasear el modelo y enviar directamente el dict

## Recomendación Actualizada

**NO hacer un fix parcial**. El problema es sistémico y requiere:
1. Definir convención clara (con o sin sufijos)
2. Actualizar TODOS los componentes para seguir la misma convención
3. Considerar crear una capa de traducción si hay múltiples RPCs con diferentes expectativas