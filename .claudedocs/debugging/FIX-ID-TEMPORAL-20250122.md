# Fix: id_temporal Missing in Entities - SOLVED

## Date: 2025-01-22
## Error: RPC 22023 - "argument 1: key must not be null"

## Root Cause
The PostgreSQL function `actualizar_articulo_procesado` expects an `id_temporal` field in entities to create temporary mappings:

```sql
-- Line 140-141 in actualizar_articulo_procesado.sql
temp_entidad_id_map := temp_entidad_id_map || 
    jsonb_build_object((v_entidad->>'id_temporal')::TEXT, v_entidad_id::TEXT);
```

When `id_temporal` was null or missing, PostgreSQL raised error 22023.

## Discovery Process
1. Initial hypothesis: `storage_path` was null (DISPROVED)
2. Added null filtering in `supabase_service.py` (DID NOT FIX)
3. Systematic analysis revealed `id_temporal` was missing in entities payload
4. Found that other elements (hechos, citas) include `id_temporal` but entities did not

## Solution
Added `id_temporal` field directly where entities are created:

### 1. Fixed in `pipeline_coordinator.py` (2 locations):
```python
# Lines 706 and 915
"id_temporal": str(entidad.id_entidad),  # IMPORTANTE: Requerido por la función SQL
```

### 2. Fixed in `controller.py` (for legacy fragments):
```python
# Line 1060
"id_temporal": str(entidad.id_entidad),  # IMPORTANTE: Requerido por la función SQL
```

### 3. Reverted changes in `payload_builder.py`
Removed the id_temporal logic that was added there, keeping the fix at the source where entities are created.

## Files Modified
1. `/home/ec2-user/projects/LaMaquinaDeNoticias/src/module_pipeline/src/pipeline/pipeline_coordinator.py`
   - Added `id_temporal` at line 706 and 915

2. `/home/ec2-user/projects/LaMaquinaDeNoticias/src/module_pipeline/src/controller.py`
   - Added `id_temporal` at line 1060

3. `/home/ec2-user/projects/LaMaquinaDeNoticias/src/module_pipeline/src/services/payload_builder.py`
   - Reverted changes (removed id_temporal logic)

## Verification
Created test script that confirms `id_temporal` is now included in entity data:
```bash
python3 tests/test_entity_id_temporal.py
```

Result: ✅ SUCCESS - id_temporal field is correctly included

## Key Insights
1. The PostgreSQL function uses `id_temporal` for creating mappings between temporary and real IDs
2. This field must be present for ALL elements (hechos, entidades, citas, datos)
3. The fix should be applied where data is created, not in the payload builder
4. Entities undergo normalization in Phase 7A, which relates `id_temporal` to `id_entidad_normalizada`

## Impact
- Low risk: Only adds a missing required field
- High benefit: Directly fixes the RPC error
- Consistent with existing patterns (hechos already use `id_temporal`)
- No changes to business logic or data flow