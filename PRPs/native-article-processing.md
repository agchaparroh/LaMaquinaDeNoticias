name: "Native Article Processing - Complete Implementation Spec"
description: |
  Implement native article processing in the pipeline, eliminating unnecessary article-to-fragment conversion.
  Articles should be processed as first-class entities throughout the entire pipeline, maintaining their
  rich metadata and using article-specific persistence. Fragment processing path remains intact but inactive.

## Goal
Transform the current pipeline to process articles natively as `ArticuloInItem` throughout all phases, persisting them using `insertar_articulo_completo` RPC, while maintaining the fragment processing capability for future use.

## Why
- **Current issue**: 100% of processed content are news articles, yet they're unnecessarily converted to fragments
- **Lost semantics**: Article metadata and context are relegated to optional fields
- **Inefficiency**: Extra conversion steps and workarounds (e.g., ID mapping)
- **Future-ready**: Maintain clear separation for when document fragmentation is needed

## What
### User-visible behavior
- No changes to API endpoints (`/procesar_articulo` continues working identically)
- Same processing quality and extraction results
- Improved processing speed (no conversion overhead)
- Better error messages with article context

### Technical requirements
- Modify existing files in-place to support both article and fragment types
- Use Union types and isinstance checks for type differentiation
- Maintain backward compatibility with existing fragment processing
- No code duplication - shared logic remains shared

### Success Criteria
- [ ] Articles processed end-to-end without fragment conversion
- [ ] All 7 pipeline phases accept and process `ArticuloProcesableItem`
- [ ] Persistence uses `insertar_articulo_completo` for articles
- [ ] Fragment processing path remains functional (tested but not used)
- [ ] No regression in extraction quality or accuracy
- [ ] Performance improvement measurable (>10% faster for articles)
- [ ] All existing tests pass with minimal modifications

## All Needed Context

### Current Implementation Issues
```python
# controller.py:184-236 - Unnecessary conversion
fragmento_data = {
    "id_fragmento": f"ART-{articulo_data['articulo_id']}",  # Artificial ID
    "texto_original": contenido,
    "metadata_adicional": {
        "es_articulo_completo": True,  # Flag buried in metadata
        ...
    }
}
fragmento = FragmentoProcesableItem(**fragmento_data)
```

### Existing Patterns
1. **Type handling**: Already uses Union types in some services
2. **Conditionals**: `isinstance()` checks in consolidation service
3. **Dual RPCs**: Both `insertar_articulo_completo` and `insertar_fragmento_completo` exist
4. **Pydantic models**: Strong typing with validation

### Key Files Structure
```
src/module_pipeline/
├── src/
│   ├── controller.py          # Entry point, performs conversion
│   ├── models/
│   │   ├── entrada.py         # Need ArticuloProcesableItem
│   │   └── procesamiento.py   # Phase result models
│   ├── pipeline/
│   │   ├── pipeline_coordinator.py  # Main orchestrator
│   │   └── fase_*.py          # 7 processing phases
│   └── services/
│       ├── payload_builder.py # Needs article payload method
│       └── supabase_service.py # Already has both RPCs
```

### Database Considerations
- Articles table expects full metadata (medio, autor, fecha_publicacion)
- Fragment table expects position info (indice_secuencial, documento_id)
- Both share extracted elements structure (facts, entities, quotes)

## Implementation Blueprint

### Task 1: Create Article Processing Model
Goal Description: Create ArticuloProcesableItem model that preserves all article metadata while conforming to pipeline processing requirements. This model will serve as the primary data structure for article processing throughout the pipeline.
SuperClaude Command: /build --model --uc --think-hard --test src/module_pipeline/src/models/entrada.py
Persona: --persona-architect
Previous Consult: Review ArticuloInItem and FragmentoProcesableItem models for structure patterns
Expected_Output: New ArticuloProcesableItem class with all ArticuloInItem fields plus processing-specific attributes
Precautions: Ensure backward compatibility, maintain Pydantic validation patterns, avoid field name conflicts
Validation Criteria: Model validates test articles, supports JSON serialization, includes all required article metadata

### Task 2: Update Pipeline Coordinator for Dual Type Support
Goal Description: Modify pipeline_coordinator.py to accept both ArticuloProcesableItem and FragmentoProcesableItem using Union types, maintaining type awareness throughout all processing phases.
SuperClaude Command: /improve --architecture --uc --test src/module_pipeline/src/pipeline/pipeline_coordinator.py
Persona: --persona-senior-dev
Previous Consult: Analyze current FragmentoProcesableItem usage and method signatures
Expected_Output: Updated ejecutar_pipeline_completo() accepting Union types with proper type detection
Precautions: Preserve existing fragment logic, avoid breaking changes, maintain error handling
Validation Criteria: Both article and fragment inputs process correctly, type information propagates to all phases

### Task 3: Adapt All Pipeline Phases for Article Processing
Goal Description: Update all 7 phase processors to handle both ArticuloProcesableItem and FragmentoProcesableItem, accessing appropriate fields based on input type while maintaining processing quality.
SuperClaude Command: /improve --batch --uc --parallel "src/module_pipeline/src/pipeline/fase_*.py"
Persona: --persona-backend
Previous Consult: Map field differences between article.contenido_texto and fragment.texto_original
Expected_Output: All phases handle both types seamlessly with isinstance() checks
Precautions: Maintain extraction quality, handle field access safely, preserve phase interfaces
Validation Criteria: All phases process both types, no AttributeErrors, extraction results unchanged

### Task 4: Implement Article-Specific Payload Builder
Goal Description: Add construir_payload_articulo() method to payload_builder.py that correctly maps ArticuloProcesableItem fields to ArticuloPersistenciaPayload structure for database persistence.
SuperClaude Command: /build --feature --tdd --uc src/module_pipeline/src/services/payload_builder.py
Persona: --persona-backend
Previous Consult: Study ArticuloPersistenciaPayload model and existing construir_payload_fragmento() implementation
Expected_Output: New method that builds complete article payload with all metadata sections
Precautions: Preserve all article metadata, handle optional fields gracefully, maintain field mappings
Validation Criteria: Generated payload validates against ArticuloPersistenciaPayload schema, includes all metadata

### Task 5: Remove Article-to-Fragment Conversion in Controller
Goal Description: Modify controller.py process_article() to create ArticuloProcesableItem directly and pass it through the pipeline without converting to FragmentoProcesableItem.
SuperClaude Command: /improve --refactor --test --uc src/module_pipeline/src/controller.py
Persona: --persona-lead-dev
Previous Consult: Review current conversion logic (lines 184-236) and identify dependencies
Expected_Output: Direct article processing without intermediate fragment conversion
Precautions: Maintain API compatibility, preserve error handling, keep fragment path functional
Validation Criteria: Articles process without conversion, /procesar_articulo endpoint unchanged, no regressions

### Task 6: Update Persistence Layer for Article Detection
Goal Description: Modify _persistir_resultado_7_fases() to properly detect article vs fragment type from the processed result and route to correct RPC (insertar_articulo_completo vs insertar_fragmento_completo).
SuperClaude Command: /improve --integration --test src/module_pipeline/src/controller.py::_persistir_resultado_7_fases
Persona: --persona-backend
Previous Consult: Analyze current es_articulo detection logic and RPC routing
Expected_Output: Correct RPC selection based on actual content type, not ID patterns
Precautions: Handle both article and fragment persistence, maintain transaction integrity
Validation Criteria: Articles persist via insertar_articulo_completo, fragments via insertar_fragmento_completo

### Task 7: Adapt Supporting Services for Article Processing
Goal Description: Update fragment_processor.py, consolidation_service.py, and chunking_service.py to handle article IDs natively and skip inappropriate processing (e.g., no chunking for articles).
SuperClaude Command: /improve --batch --uc "src/module_pipeline/src/utils/fragment_processor.py src/module_pipeline/src/services/consolidation_service.py src/module_pipeline/src/services/chunking_service.py"
Persona: --persona-senior-dev
Previous Consult: Review service interfaces and article-specific requirements
Expected_Output: Services handle articles appropriately without "ART-" prefix workarounds
Precautions: Maintain service contracts, handle type detection properly, avoid breaking fragments
Validation Criteria: Article IDs process cleanly, no chunking for articles, consolidation works for both types

### Task 8: Create Comprehensive Integration Tests
Goal Description: Develop end-to-end integration tests that verify complete article processing flow from API input through persistence, ensuring both article and fragment paths function correctly.
SuperClaude Command: /test --integration --coverage --strict src/module_pipeline/tests/test_integration_article_processing.py
Persona: --persona-qa
Previous Consult: Review existing integration test patterns and test data structures
Expected_Output: Complete test suite covering article flow, fragment flow, and error cases
Precautions: Test both happy paths and edge cases, verify backward compatibility
Validation Criteria: 100% path coverage, both flows tested, performance benchmarks included

## Validation Loop

### Phase 1: Unit Testing
```bash
# Test new article model
pytest src/module_pipeline/tests/test_models.py::test_articulo_procesable_item -xvs

# Test updated phase processors
pytest src/module_pipeline/tests/test_pipeline/ -k "articulo" -xvs
```

### Phase 2: Integration Testing
```bash
# Test complete article flow
pytest src/module_pipeline/tests/test_integration.py::test_article_processing_e2e -xvs

# Verify fragment path still works
pytest src/module_pipeline/tests/test_integration.py::test_fragment_processing_e2e -xvs
```

### Phase 3: Performance Validation
```bash
# Compare processing times
python scripts/benchmark_processing.py --compare-modes

# Check memory usage
python scripts/profile_pipeline.py --mode=article
```

### Phase 4: Persistence Verification
```sql
-- Verify articles persist correctly
SELECT COUNT(*) FROM articulos WHERE fecha_procesamiento > NOW() - INTERVAL '1 hour';

-- Check extraction quality
SELECT a.articulo_id, COUNT(h.hecho_id) as hechos
FROM articulos a
JOIN hecho_articulo ha ON a.articulo_id = ha.articulo_id
JOIN hechos h ON ha.hecho_id = h.hecho_id
GROUP BY a.articulo_id;
```

## Implementation Order
1. Models first (ArticuloProcesableItem)
2. Pipeline coordinator type support
3. Phase processors in parallel
4. Payload builder
5. Controller update
6. Supporting services
7. Comprehensive testing

## Risk Mitigation
- **Type confusion**: Strong typing with Pydantic models
- **Processing errors**: Graceful fallback to fragment processing
- **Performance**: Profile before/after each major change
- **Data integrity**: Transaction-based persistence unchanged

## Confidence Score: 9/10
High confidence due to:
- Clear separation of concerns
- Existing dual-path architecture (RPCs)
- In-place modifications minimize risk
- Strong type system guides implementation