# ERROR: entidad_relacion_tipo_relacion_check constraint violation

## Fecha: 2025-01-22 11:45
## Estado: 🔴 ACTIVO
## Impacto: CRÍTICO - Impide persistencia completa en Supabase

## DESCRIPCIÓN DEL ERROR

El pipeline procesa exitosamente las 7 fases pero falla en la persistencia con el siguiente error:
```
new row for relation "entidad_relacion" violates check constraint "entidad_relacion_tipo_relacion_check"
```

## CAUSA RAÍZ

El pipeline genera tipos de relación entre entidades que NO están permitidos por el constraint de la base de datos.

### Tipos VÁLIDOS según el constraint:
- `miembro_de`
- `subsidiaria_de`
- `aliado_con`
- `opositor_a`
- `sucesor_de`
- `predecesor_de`
- `casado_con`
- `familiar_de`
- `empleado_de`

### Tipos INVÁLIDOS generados por el pipeline:
- `ubicacion`
- `mencionado`
- `organizador`

## EVIDENCIA

### Artículo 3146 (centroamerica360_region):
```json
"relaciones_entidades": [
  {"tipo_relacion": "ubicacion", ...},
  {"tipo_relacion": "mencionado", ...}
]
```

### Artículo 3166 (centroamerica360_politica):
```json
"relaciones_entidades": [
  {"tipo_relacion": "miembro_de", ...},  // VÁLIDO
  {"tipo_relacion": "organizador", ...}  // INVÁLIDO
]
```

## ARCHIVOS AFECTADOS

1. **Fase 7 - Detección de Relaciones**:
   - `/src/module_pipeline/src/pipeline/fase_7_normalizacion.py`
   - Función: `_detectar_relaciones_estructurales()`

2. **Prompt de Relaciones**:
   - `/src/module_pipeline/prompts/RelacionesEstructurales.md`
   - Debe actualizar los tipos de relación permitidos

## IMPACTO

- ❌ Artículos procesados correctamente pero quedan en estado "pendiente"
- ❌ No se persisten entidades, hechos, datos ni citas
- ❌ Criterio 1 del PRP no se cumple: "PERSISTENCIA EXITOSA EN SUPABASE"

## SOLUCIÓN PROPUESTA

1. **Opción A - Actualizar el Pipeline**:
   - Modificar el prompt de relaciones estructurales para usar solo tipos válidos
   - Mapear tipos inválidos a válidos (ej: "ubicacion" → "miembro_de")

2. **Opción B - Actualizar la Base de Datos**:
   - Agregar los nuevos tipos al constraint
   - Requiere migración de base de datos

## PRÓXIMOS PASOS

1. Revisar el prompt de relaciones estructurales
2. Implementar mapeo de tipos inválidos a válidos
3. Re-ejecutar pruebas con artículos de prueba
4. Verificar persistencia exitosa