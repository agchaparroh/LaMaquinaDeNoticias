# Error Analysis: Referential Integrity Validation Failure

## Error Details
- **Error**: "Validación fallida para payload articulo: 12 errores encontrados"
- **Type**: Referential integrity validation errors
- **Location**: PayloadBuilder validation during article payload construction
- **Impact**: Prevents article persistence to Supabase

## Symptoms
- 12 validation errors all related to fact relationship IDs not existing
- Relationships reference fact IDs 1-8 but these are not found in the facts collection
- Phase 4 successfully extracts 8 facts
- Phase 7 successfully detects 6 temporal relations
- Validation fails when building the final payload

## Hypotheses

### Hypothesis A: Missing id_temporal_hecho field (Most Probable - 70%)
**Evidence For:**
- Similar issue just fixed with entities missing 'id_temporal' field
- PayloadBuilder expects 'id_temporal_hecho' field in facts
- Relationships use numeric IDs (1, 2, 3...) in 'id_hecho_origen/destino'
- Entity fix pattern suggests facts have same issue

**Evidence Against:**
- Phase 4 reports successful extraction of 8 facts
- No explicit errors during fact extraction

**How to Verify:**
```bash
# Check phase 4 fact extraction code for id_temporal_hecho assignment
grep -n "id_temporal_hecho" src/pipeline/fase_4_hechos.py
# Check what fields facts actually have
docker-compose logs --tail=1000 module-pipeline | grep -A10 "hechos_extraidos"
```

### Hypothesis B: ID Field Mismatch (Moderate - 20%)
**Evidence For:**
- Entities have both 'id' and 'id_temporal' fields
- Relationships might reference 'id' while validation expects 'id_temporal_hecho'
- Could be using wrong field name in relationships

**Evidence Against:**
- Error specifically mentions IDs 1-8 which suggests numeric IDs are being used
- Validation code clearly looks for 'id_temporal_hecho'

**How to Verify:**
```bash
# Check phase 7 normalization code for how it assigns relationship IDs
grep -A5 -B5 "id_hecho_origen\|id_hecho_destino" src/pipeline/fase_7_normalizacion.py
```

### Hypothesis C: Facts Not Included in Payload (Less Probable - 10%)
**Evidence For:**
- Validation can't find any fact IDs
- Could be facts are extracted but not passed to payload builder

**Evidence Against:**
- Logs show 8 facts were extracted
- Other phases seem to complete successfully

**How to Verify:**
```bash
# Check how facts are passed to payload builder
grep -A10 "hechos_extraidos" src/pipeline/pipeline_coordinator.py
```