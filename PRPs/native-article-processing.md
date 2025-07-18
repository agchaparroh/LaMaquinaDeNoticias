name: "Native Article Processing - Complete Implementation Spec (UPDATED)"
description: |
  Implement native article processing in the pipeline, eliminating unnecessary article-to-fragment conversion.
  Articles should be processed as first-class entities throughout the entire pipeline, maintaining their
  rich metadata and using article-specific persistence. Fragment processing path remains intact but inactive.
  
  **UPDATE NOTE**: This PRP has been updated based on comprehensive environment investigation conducted on 2025-01-18.
  Several existing components were discovered that significantly simplify the implementation.

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
- Use Union types and isinstance checks for type differentiation (following existing patterns)
- Maintain backward compatibility with existing fragment processing
- No code duplication - shared logic remains shared
- Leverage existing advanced services (adaptive flow, chunking, consolidation)

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

### Existing Infrastructure (DISCOVERED)
1. **Payload Builder**: `construir_payload_articulo()` method ALREADY EXISTS (line 269)
2. **Persistence Models**: `ArticuloPersistenciaPayload` and `FragmentoPersistenciaPayload` complete
3. **Supabase RPCs**: Both `insertar_articulo_completo` and `insertar_fragmento_completo` functional
4. **Advanced Services**: Already implemented and working:
   - `adaptive_flow_controller.py`: Dynamic flow decisions
   - `chunking_service.py`: Intelligent text chunking
   - `consolidation_service.py`: Cross-chunk consolidation (already uses isinstance())
   - `entity_normalizer.py`: Entity normalization
   - `spacy_analyzer.py`: Linguistic analysis
5. **Code Patterns**: Union types and isinstance() already used in multiple places

### Key Files Structure
```
src/module_pipeline/
├── src/
│   ├── controller.py          # Entry point, performs conversion (LINES 184-236)
│   ├── models/
│   │   ├── entrada.py         # Need ArticuloProcesableItem (ArticuloInItem exists)
│   │   ├── procesamiento.py   # Phase result models (complete)
│   │   └── persistencia.py    # Payload models (complete)
│   ├── pipeline/
│   │   ├── pipeline_coordinator.py  # Main orchestrator (needs Union types)
│   │   └── fase_*.py          # 7 processing phases (need isinstance())
│   └── services/
│       ├── payload_builder.py # HAS construir_payload_articulo() method
│       ├── supabase_service.py # Has both RPCs working
│       ├── adaptive_flow_controller.py # ALREADY EXISTS
│       ├── chunking_service.py # ALREADY EXISTS
│       └── consolidation_service.py # ALREADY EXISTS & uses isinstance()
```

### Database Considerations
- Articles table expects full metadata (medio, autor, fecha_publicacion)
- Fragment table expects position info (indice_secuencial, documento_id)
- Both share extracted elements structure (facts, entities, quotes)
- Both RPCs tested and functional

## Implementation Blueprint (UPDATED)

### Task 1: Create Article Processing Model
Goal Description: Create ArticuloProcesableItem model that preserves all article metadata while conforming to pipeline processing requirements. This model will serve as the primary data structure for article processing throughout the pipeline.
SuperClaude Command: /build --model --uc --think-hard --test src/module_pipeline/src/models/entrada.py
Persona: --persona-architect
Previous Consult: Review ArticuloInItem and FragmentoProcesableItem models for structure patterns
Expected_Output: New ArticuloProcesableItem class with all ArticuloInItem fields plus processing-specific attributes
Precautions: Ensure backward compatibility, maintain Pydantic validation patterns, avoid field name conflicts
Validation Criteria: Model validates test articles, supports JSON serialization, includes all required article metadata

### Task 2: Update Pipeline Coordinator for Dual Type Support
Goal Description: Modify pipeline_coordinator.py to accept both ArticuloProcesableItem and FragmentoProcesableItem using Union types, maintaining type awareness throughout all processing phases. Follow existing isinstance() patterns from consolidation_service.py.
SuperClaude Command: /improve --architecture --uc --test src/module_pipeline/src/pipeline/pipeline_coordinator.py
Persona: --persona-senior-dev
Previous Consult: Analyze current FragmentoProcesableItem usage and method signatures, study consolidation_service.py isinstance() patterns
Expected_Output: Updated ejecutar_pipeline_completo() accepting Union types with proper type detection
Precautions: Preserve existing fragment logic, avoid breaking changes, maintain error handling
Validation Criteria: Both article and fragment inputs process correctly, type information propagates to all phases

### Task 3: Adapt All Pipeline Phases for Article Processing
Goal Description: Update all 7 phase processors to handle both ArticuloProcesableItem and FragmentoProcesableItem, accessing appropriate fields based on input type while maintaining processing quality. Map article.contenido_texto to fragment.texto_original access patterns.
SuperClaude Command: /improve --batch --uc --parallel "src/module_pipeline/src/pipeline/fase_*.py"
Persona: --persona-backend
Previous Consult: Map field differences between article.contenido_texto and fragment.texto_original, analyze existing phase interfaces
Expected_Output: All phases handle both types seamlessly with isinstance() checks
Precautions: Maintain extraction quality, handle field access safely, preserve phase interfaces
Validation Criteria: All phases process both types, no AttributeErrors, extraction results unchanged

### Task 4: Verify Article Payload Builder Integration (UPDATED)
Goal Description: Verify that existing construir_payload_articulo() method works correctly with new ArticuloProcesableItem model and update payload building logic to handle the new article type. The method already exists at line 269 of payload_builder.py.
SuperClaude Command: /improve --verify --test src/module_pipeline/src/services/payload_builder.py
Persona: --persona-backend
Previous Consult: Study existing construir_payload_articulo() implementation and ArticuloPersistenciaPayload model
Expected_Output: Updated payload building logic that correctly maps ArticuloProcesableItem fields to ArticuloPersistenciaPayload
Precautions: Preserve all article metadata, handle optional fields gracefully, maintain field mappings
Validation Criteria: Generated payload validates against ArticuloPersistenciaPayload schema, includes all metadata

### Task 5: Remove Article-to-Fragment Conversion in Controller  
Goal Description: Modify controller.py process_article() to create ArticuloProcesableItem directly and pass it through the pipeline without converting to FragmentoProcesableItem. Remove conversion logic from lines 184-236.
SuperClaude Command: /improve --refactor --test --uc src/module_pipeline/src/controller.py
Persona: --persona-lead-dev
Previous Consult: Review current conversion logic (lines 184-236) and identify dependencies
Expected_Output: Direct article processing without intermediate fragment conversion
Precautions: Maintain API compatibility, preserve error handling, keep fragment path functional
Validation Criteria: Articles process without conversion, /procesar_articulo endpoint unchanged, no regressions

### Task 6: Update Persistence Layer for Article Detection (UPDATED)
Goal Description: Modify _persistir_resultado_7_fases() to properly detect article vs fragment type from the processed result and route to correct RPC. Replace metadata-based detection (es_articulo_completo) with proper type detection using isinstance().
SuperClaude Command: /improve --integration --test src/module_pipeline/src/controller.py::_persistir_resultado_7_fases
Persona: --persona-backend
Previous Consult: Analyze current es_articulo detection logic (lines 579-604) and RPC routing
Expected_Output: Correct RPC selection based on actual content type, not metadata flags
Precautions: Handle both article and fragment persistence, maintain transaction integrity
Validation Criteria: Articles persist via insertar_articulo_completo, fragments via insertar_fragmento_completo

### Task 7: Verify Supporting Services Compatibility (UPDATED)
Goal Description: Verify that existing advanced services (adaptive_flow_controller, chunking_service, consolidation_service, entity_normalizer, spacy_analyzer) work correctly with ArticuloProcesableItem. Update only fragment_processor.py if needed for article ID handling.
SuperClaude Command: /improve --verify --test "src/module_pipeline/src/utils/fragment_processor.py src/module_pipeline/src/services/"
Persona: --persona-senior-dev
Previous Consult: Review service interfaces and article-specific requirements, note that consolidation_service already uses isinstance()
Expected_Output: Verified compatibility with existing services, minimal changes to fragment_processor.py if needed
Precautions: Maintain service contracts, handle type detection properly, avoid breaking fragments
Validation Criteria: All services work with both types, no "ART-" prefix workarounds needed

### Task 8: Create Comprehensive Integration Tests (UPDATED)
Goal Description: Develop end-to-end integration tests that verify complete article processing flow from API input through persistence, ensuring both article and fragment paths function correctly. Leverage existing test infrastructure and patterns.
SuperClaude Command: /test --integration --coverage --strict src/module_pipeline/tests/test_integration_article_processing.py
Persona: --persona-qa
Previous Consult: Review existing integration test patterns and test data structures in tests/ directory
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

# Verify payload builder works with both types
pytest src/module_pipeline/tests/test_services/test_payload_builder.py -xvs
```

### Phase 2: Integration Testing
```bash
# Test complete article flow
pytest src/module_pipeline/tests/test_integration.py::test_article_processing_e2e -xvs

# Verify fragment path still works
pytest src/module_pipeline/tests/test_integration.py::test_fragment_processing_e2e -xvs

# Run existing integration tests
pytest src/module_pipeline/tests/test_controller_integration.py -xvs
```

### Phase 3: Performance Validation
```bash
# Compare processing times
python scripts/benchmark_processing.py --compare-modes

# Check memory usage
python scripts/profile_pipeline.py --mode=article

# Verify advanced services performance
pytest src/module_pipeline/tests/test_services/ -k "performance" -xvs
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

## Implementation Order (UPDATED)
1. Models first (ArticuloProcesableItem)
2. Pipeline coordinator type support
3. Phase processors in parallel
4. Verify payload builder integration (not implement from scratch)
5. Controller update (remove conversion)
6. Verify supporting services compatibility
7. Comprehensive testing

## Risk Mitigation
- **Type confusion**: Strong typing with Pydantic models
- **Processing errors**: Graceful fallback to fragment processing
- **Performance**: Profile before/after each major change
- **Data integrity**: Transaction-based persistence unchanged
- **Service compatibility**: Existing advanced services already handle complex scenarios

## Confidence Score: 9.5/10 (UPDATED)
High confidence due to:
- Clear separation of concerns
- Existing dual-path architecture (RPCs)
- In-place modifications minimize risk
- Strong type system guides implementation
- **Advanced services already implemented and working**
- **Payload builder and persistence models complete**
- **Union types and isinstance() patterns established**

## Key Simplifications Discovered
1. **PayloadBuilder**: Method already exists, just needs verification
2. **Persistence**: Both RPCs working, just need better type detection
3. **Advanced Services**: Comprehensive suite already implemented
4. **Code Patterns**: Union types and isinstance() already used
5. **Test Infrastructure**: Robust testing framework in place

This updated PRP reflects the actual state of the codebase and provides a more accurate and efficient implementation path.