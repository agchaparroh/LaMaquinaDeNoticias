name: "Ampliación Pipeline de Procesamiento: De 4 a 7 Fases - Implementación Integral"
description: |

## Purpose
Ampliar el pipeline de procesamiento de artículos periodísticos de 4 a 7 fases, implementando procesamiento adaptativo, chunking inteligente y separación de extracciones para mayor precisión y escalabilidad, construyendo sobre la arquitectura existente sin destruirla.

## Core Principles
1. **Construcción sobre cimientos**: Preservar y extender la arquitectura existente
2. **Simplicidad robusta**: Evitar sobreingeniería, preferir soluciones simples y probadas
3. **Implementación integral**: Sistema completo, no incremental
4. **Sostenibilidad**: Diseño mantenible a largo plazo
5. **Validación continua**: Tests en cada componente
6. **Comandos explícitos**: Cada tarea especifica comando SuperClaude exacto

---

## Goal
Transformar el pipeline actual de 4 fases secuenciales en un sistema de 7 fases con:
- Procesamiento adaptativo basado en análisis spaCy
- Chunking inteligente para contenido extenso
- Simplificación lingüística para mejor comprensión del LLM
- Separación de extracciones (entidades, hechos, datos, citas)
- Consolidación cross-chunk robusta
- Detección paralela de relaciones estructurales y temporales

## Why
- **Calidad mejorada**: Mayor precisión en extracciones al separar por tipo
- **Escalabilidad**: Manejo eficiente de artículos largos mediante chunking
- **Adaptabilidad**: Flujo dinámico según características del contenido
- **Optimización LLM**: Texto simplificado mejora comprensión y reduce errores
- **Mantenibilidad**: Arquitectura modular facilita mejoras futuras

## What
Sistema de pipeline inteligente que:
- Analiza contenido con spaCy para decisiones adaptativas
- Simplifica lenguaje periodístico antes de procesamiento
- Divide contenido largo en chunks manejables
- Extrae elementos por tipo en fases separadas
- Consolida resultados cross-chunk sin duplicados
- Detecta relaciones complejas entre elementos

### Success Criteria
- [ ] Pipeline procesa artículos con 7 fases funcionando correctamente
- [ ] Chunking automático activado por umbrales configurables
- [ ] Consolidación elimina >95% de duplicados cross-chunk
- [ ] Tests unitarios con >90% cobertura en nuevas fases
- [ ] Rendimiento: <30s para artículos típicos (3000-5000 chars)
- [ ] Rendimiento: 60-70% mejora en artículos largos con chunking paralelo
- [ ] Sistema de configuración dinámico funcionando con todas las variables
- [ ] Relaciones 7B.1 y 7B.2 ejecutan en paralelo con asyncio.gather()
- [ ] Compatibilidad total con API y persistencia existentes
- [ ] Documentación completa de nuevas funcionalidades

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Core project files
- file: src/module_pipeline/src/controller.py
  why: Controller principal a extender para 7 fases
  
- file: src/module_pipeline/src/pipeline/*.py
  why: Fases actuales como referencia de patrones
  
- file: src/module_pipeline/src/services/groq_service.py
  why: Servicio LLM a reutilizar sin cambios
  
- file: src/module_pipeline/src/utils/fragment_processor.py
  why: Sistema de IDs a extender para chunking
  
- file: docs/PipelineAmpliación/0.PipelineActualizado
  why: Especificación completa del sistema objetivo
  
- file: docs/PipelineAmpliación/*.md
  why: Prompts específicos para cada fase nueva
  
- file: src/module_pipeline/src/models/*.py
  why: Modelos Pydantic a extender/reutilizar
  
- file: .claude/CLAUDE.md
  why: Estándares y convenciones del proyecto
```

### Current Codebase Structure
```bash
src/module_pipeline/
├── src/
│   ├── controller.py              # Extender para 7 fases
│   ├── pipeline/                  # Agregar nuevas fases aquí
│   │   ├── fase_1_triaje.py      # Mejorar con análisis spaCy
│   │   ├── fase_2_simplificacion.py # Nueva fase
│   │   ├── fase_3_entidades.py  # Nueva fase
│   │   ├── fase_4_hechos.py     # Nueva fase
│   │   ├── fase_5_datos.py      # Nueva fase
│   │   ├── fase_6_citas.py      # Nueva fase
│   │   └── fase_7_normalizacion.py # Incluye relaciones
│   ├── services/                  # Agregar ChunkingService
│   │   ├── groq_service.py       # NO MODIFICAR - Reutilizar
│   │   ├── supabase_service.py   # NO MODIFICAR - Reutilizar
│   │   └── entity_normalizer.py  # Mantener funcionalidad
│   ├── utils/                     # Extender utilidades
│   │   └── fragment_processor.py  # Adaptar para chunking
│   └── models/                    # Extender modelos
│       ├── procesamiento.py       # Nuevos modelos por fase
│       └── metadatos.py          # Mantener compatibilidad
```

### Configuration & Environment Variables
```yaml
# Pipeline Configuration Variables
Pipeline_Thresholds:
  PIPELINE_CHUNKING_ENTITIES_THRESHOLD: 30
  PIPELINE_CHUNKING_CHARS_THRESHOLD: 6000
  PIPELINE_CHUNKING_QUOTES_THRESHOLD: 30
  PIPELINE_CHUNKING_DATA_THRESHOLD: 30
  
Model_Configuration:
  PIPELINE_GROQ_MODEL_DEFAULT: "llama-3.1-8b-instant"
  PIPELINE_GROQ_MODEL_LARGE: "llama-3.1-70b-versatile"
  PIPELINE_GROQ_MODEL_TOKEN_THRESHOLD: 8000
  
Processing_Configuration:
  PIPELINE_CONSOLIDATION_SIMILARITY_THRESHOLD: 0.85
  PIPELINE_MAX_RETRIES_PER_PHASE: 3
  PIPELINE_CHUNK_PARALLEL_ENABLED: true
  PIPELINE_MAX_CONCURRENT_CHUNKS: 5
```

### Known Gotchas & Requirements
```python
# CRITICAL: Preservar funcionalidades spaCy existentes en Fase 1
# CRITICAL: Mantener IDs secuenciales durante chunking
# CRITICAL: No romper API endpoints existentes
# CRITICAL: Groq token limits: 8k (8B model), usar 70B solo si necesario
# CRITICAL: Consolidación debe ser determinista y reproducible
# CRITICAL: Paralelizar 7B.1 y 7B.2 con asyncio.gather() simple
# CRITICAL: Chunk parallelization solo cuando se necesita chunking
# CRITICAL: Configuración debe validarse al inicio
```

## Implementation Blueprint

### Architecture Overview
```mermaid
graph TB
    subgraph "Controller"
        PC[PipelineController<br/>7 Phases + Adaptive]
        JT[JobTracker<br/>Existing]
    end
    
    subgraph "Phase 1: Analysis"
        F1A[Relevance Eval<br/>Groq]
        F1B[Content Analysis<br/>spaCy Enhanced]
        F1C[Flow Controller<br/>Adaptive Decisions]
    end
    
    subgraph "Phase 2-6: Processing"
        F2[Phase 2: Simplification]
        F3[Phase 3: Entities<br/>+Chunking if needed]
        F4[Phase 4: Facts<br/>+Chunking if needed]
        F5[Phase 5: Data<br/>Conditional]
        F6[Phase 6: Quotes<br/>Conditional]
    end
    
    subgraph "Phase 7: Finalization"
        F7A[Normalization<br/>Supabase]
        F7B[Relations<br/>7B.1 || 7B.2]
    end
    
    PC --> F1A
    F1A --> F1B
    F1B --> F1C
    F1C --> F2
    F2 --> F3
    F3 --> F4
    F4 --> F5
    F4 --> F6
    F6 --> F7A
    F7A --> F7B
    
    %% Chunking occurs inside phases when needed
    F3 -.->|if chunks| F3
    F4 -.->|if chunks| F4
    F5 -.->|if chunks| F5
    F6 -.->|if chunks| F6
```

### Task Breakdown
```yaml
# Each task includes explicit SuperClaude command for deterministic execution

Task 1: Analyze current spaCy implementation and preserve features
  Priority: high
  Dependencies: []
  SuperClaude Command: /analyze --code --nlp --features src/module_pipeline/src/pipeline/fase_1_triaje.py
  Persona: --persona-analyzer
  Validation: /test --unit src/module_pipeline/tests/test_pipeline/test_fase_1_triaje.py
  Expected_Output: Report of current spaCy features to preserve

Task 2: Design adaptive pipeline architecture
  Priority: high
  Dependencies: [Task 1]
  SuperClaude Command: /design --architecture --flow --patterns --think-hard
  Persona: --persona-architect
  Focus: 7-phase flow, chunking strategy, consolidation algorithm
  Validation: /review --architecture --evidence
  Expected_Output: Detailed architecture with flow diagrams

Task 3: Implement ChunkingService
  Priority: high
  Dependencies: [Task 2]
  SuperClaude Command: /build --service --chunking --tdd --patterns
  Persona: --persona-backend
  Files:
    - CREATE src/module_pipeline/src/services/chunking_service.py
    - MODIFY src/module_pipeline/src/utils/fragment_processor.py
  Validation: /test --unit --coverage
  Expected_Output: Chunking service with context preservation

Task 4: Analyze JSON Schema Coherence Across Phases
  Priority: high
  Dependencies: [Task 2]
  SuperClaude Command: /analyze --schemas --flow --optimization
  Persona: --persona-architect
  Files:
    - ANALYZE docs/PipelineAmpliación/*.md (all prompts)
    - ANALYZE src/module_pipeline/src/models/*.py (existing models)
    - CREATE src/module_pipeline/docs/SCHEMA_MAPPING.md
  Focus:
    - Map input/output formats for each phase from prompts
    - Identify minimal fields needed for context in each phase
    - Design coherent Pydantic model transformations
    - Optimize JSON fields to reduce token usage
    - Document field mappings and transformations
  Validation: /review --schemas --consistency
  Expected_Output: Complete schema mapping document with optimized models design

Task 5: Enhance Phase 1 with spaCy analysis
  Priority: high
  Dependencies: [Task 1, Task 3, Task 4]
  SuperClaude Command: /build --feature --nlp --enhance --tdd
  Persona: --persona-backend
  Files:
    - MODIFY src/module_pipeline/src/pipeline/fase_1_triaje.py
    - CREATE src/module_pipeline/src/models/analisis_componentes.py
  Validation: /test --unit --regression
  Expected_Output: Enhanced Phase 1 with content metrics

Task 6: Implement Phase 2 - Text Simplification
  Priority: high
  Dependencies: [Task 5]
  SuperClaude Command: /build --feature --nlp --simplification --tdd
  Persona: --persona-backend
  Files:
    - CREATE src/module_pipeline/src/pipeline/fase_2_simplificacion.py
    - USES docs/PipelineAmpliación/Simplificación.md
  Validation: /test --unit --quality
  Expected_Output: Simplification phase with language normalization

Task 7: Split extraction into Phases 3-6
  Priority: high
  Dependencies: [Task 6]
  SuperClaude Command: /build --feature --extraction --modular --tdd
  Persona: --persona-backend
  Files:
    - CREATE src/module_pipeline/src/pipeline/fase_3_entidades.py
    - CREATE src/module_pipeline/src/pipeline/fase_4_hechos.py
    - CREATE src/module_pipeline/src/pipeline/fase_5_datos.py
    - CREATE src/module_pipeline/src/pipeline/fase_6_citas.py
  Validation: /test --unit --integration
  Expected_Output: Four specialized extraction phases

Task 8: Implement cross-chunk consolidation
  Priority: high
  Dependencies: [Task 7]
  SuperClaude Command: /build --feature --consolidation --algorithms --tdd
  Persona: --persona-backend
  Files:
    - CREATE src/module_pipeline/src/services/consolidation_service.py
    - CREATE src/module_pipeline/src/utils/similarity_algorithms.py
  Focus:
    - Consolidation happens WITHIN each phase after processing all chunks
    - Merge duplicate entities/facts/quotes from different chunks
    - Maintain ID consistency and relationships
    - Simple similarity algorithms (exact match, fuzzy match)
  Validation: /test --unit --accuracy
  Expected_Output: Consolidation service with >95% dedup accuracy

Task 9: Enhance Phase 7 with parallel relations
  Priority: high
  Dependencies: [Task 8]
  SuperClaude Command: /build --feature --relations --parallel --tdd
  Persona: --persona-backend
  Files:
    - MODIFY src/module_pipeline/src/pipeline/fase_7_normalizacion.py
    - CREATE src/module_pipeline/src/pipeline/fase_7_relaciones.py
  Validation: /test --unit --concurrent
  Expected_Output: Parallel relation detection (structural + temporal)

Task 10: Update PipelineController for 7 phases
  Priority: high
  Dependencies: [Task 9]
  SuperClaude Command: /improve --refactor --controller --flow
  Persona: --persona-refactorer
  Files:
    - MODIFY src/module_pipeline/src/controller.py
    - MODIFY src/module_pipeline/src/pipeline/pipeline_coordinator.py
  Focus:
    - Orchestrate 7 phases with adaptive flow control
    - Implement conditional execution based on spaCy analysis
    - Handle chunk processing when thresholds exceeded
    - Simple parallel execution for relations (7B.1 and 7B.2)
  Validation: /test --integration --flow
  Expected_Output: Controller orchestrating 7 phases adaptively

Task 11: Extend Pydantic models for new phases
  Priority: medium
  Dependencies: [Task 4, Task 7]
  SuperClaude Command: /build --models --pydantic --validation
  Persona: --persona-backend
  Files:
    - MODIFY src/module_pipeline/src/models/procesamiento.py
    - MODIFY src/module_pipeline/src/models/metadatos.py
    - CREATE src/module_pipeline/src/models/simplificacion.py
  Focus:
    - Implement models based on Task 4 schema analysis
    - Ensure minimal fields for token optimization
    - Coherent transformations between phases
  Validation: /test --unit --models
  Expected_Output: Complete model coverage for 7 phases with optimized schemas

Task 12: Implement Chunk Parallel Processing
  Priority: medium
  Dependencies: [Task 3, Task 7]
  SuperClaude Command: /build --feature --async --chunks --simple
  Persona: --persona-backend
  Files:
    - MODIFY src/module_pipeline/src/services/chunking_service.py
    - MODIFY src/module_pipeline/src/pipeline/fase_3_entidades.py
    - MODIFY src/module_pipeline/src/pipeline/fase_4_hechos.py
    - MODIFY src/module_pipeline/src/pipeline/fase_5_datos.py
    - MODIFY src/module_pipeline/src/pipeline/fase_6_citas.py
  Focus: 
    - Process chunks in parallel within each phase using asyncio.gather()
    - Only activate when chunking is needed (thresholds exceeded)
    - Maintain chunk order and ID consistency
    - Simple implementation without complex coordination
  Validation: /test --async --chunks --performance
  Expected_Output: Parallel chunk processing reducing time 60-70% for long articles

Task 13: Add Dynamic Configuration System
  Priority: high
  Dependencies: [Task 2]
  SuperClaude Command: /build --config --dynamic --env --patterns
  Persona: --persona-backend
  Files:
    - MODIFY src/module_pipeline/src/config.py
    - CREATE src/module_pipeline/src/utils/config_loader.py
    - CREATE src/module_pipeline/.env.pipeline.example
  Configuration_Variables:
    - PIPELINE_CHUNKING_ENTITIES_THRESHOLD (default: 30)
    - PIPELINE_CHUNKING_CHARS_THRESHOLD (default: 6000)
    - PIPELINE_CHUNKING_QUOTES_THRESHOLD (default: 30)
    - PIPELINE_CHUNKING_DATA_THRESHOLD (default: 30)
    - PIPELINE_GROQ_MODEL_DEFAULT (default: llama-3.1-8b-instant)
    - PIPELINE_GROQ_MODEL_LARGE (default: llama-3.1-70b-versatile)
    - PIPELINE_GROQ_MODEL_TOKEN_THRESHOLD (default: 8000)
    - PIPELINE_CONSOLIDATION_SIMILARITY_THRESHOLD (default: 0.85)
    - PIPELINE_MAX_RETRIES_PER_PHASE (default: 3)
    - PIPELINE_CHUNK_PARALLEL_ENABLED (default: true)
    - PIPELINE_MAX_CONCURRENT_CHUNKS (default: 5)
  Validation: /test --config --env --dynamic
  Expected_Output: Configuration system reading from environment with defaults

Task 14: Integration testing suite
  Priority: high
  Dependencies: [Task 10, Task 11, Task 12]
  SuperClaude Command: /test --integration --e2e --comprehensive
  Persona: --persona-qa
  Files:
    - CREATE src/module_pipeline/tests/test_7_phases_flow.py
    - CREATE src/module_pipeline/tests/test_chunking_integration.py
    - CREATE src/module_pipeline/tests/test_consolidation.py
  Validation: /test --coverage --report
  Expected_Output: >90% test coverage, all scenarios passing

Task 15: Performance optimization
  Priority: medium
  Dependencies: [Task 14]
  SuperClaude Command: /improve --performance --profile --optimize
  Persona: --persona-performance
  Focus: Query optimization, caching strategies, efficient consolidation
  Validation: /test --performance --benchmark
  Expected_Output: <30s processing for typical articles

Task 16: Update monitoring and metrics
  Priority: medium
  Dependencies: [Task 14]
  SuperClaude Command: /build --monitoring --metrics --phases
  Persona: --persona-backend
  Files:
    - MODIFY src/module_pipeline/src/monitoring/metrics_collector.py
    - MODIFY src/module_pipeline/src/monitoring/alert_manager.py
  Validation: /test --monitoring --alerts
  Expected_Output: Metrics for all 7 phases

Task 17: Comprehensive documentation
  Priority: medium
  Dependencies: [Task 16]
  SuperClaude Command: /document --api --architecture --examples
  Persona: --persona-mentor
  Files:
    - UPDATE src/module_pipeline/README.md
    - CREATE src/module_pipeline/docs/7_PHASES_GUIDE.md
    - CREATE src/module_pipeline/docs/CHUNKING_STRATEGY.md
  Expected_Output: Complete documentation with examples

Task 18: Migration validation
  Priority: high
  Dependencies: [Task 17]
  SuperClaude Command: /test --migration --validation --regression
  Persona: --persona-qa
  Focus: Ensure backwards compatibility, API unchanged
  Validation: /scan --compatibility --api
  Expected_Output: Zero breaking changes confirmed
```

## Validation Loops

### Unit Testing Strategy
```bash
# Run after each implementation task
/test --unit --coverage src/module_pipeline/src/pipeline/
/test --unit --coverage src/module_pipeline/src/services/
/analyze --coverage --report
```

### Integration Testing
```bash
# Test complete flow with real articles
/test --integration --flow --real-data
/test --performance --load --concurrent
/analyze --bottlenecks --profile
```

### Quality Validation
```bash
# Ensure extraction quality
/test --quality --extraction --metrics
/analyze --accuracy --f1-score
/review --outputs --evidence
```

## Risk Mitigation

### Technical Risks
1. **Chunking complexity**: Start with simple overlapping windows
2. **ID consistency**: Extend FragmentProcessor carefully with tests
3. **Performance degradation**: Profile and optimize bottlenecks
4. **Consolidation accuracy**: Use multiple similarity metrics
5. **LLM token limits**: Implement smart truncation strategies

### Implementation Guidelines
- Test each phase in isolation before integration
- Maintain backwards compatibility at all times
- Use feature flags for gradual rollout if needed
- Monitor Groq API usage and costs
- Document all design decisions

## Success Metrics
- Processing accuracy: >95% for standard articles
- Performance: <30s for 5000 char articles (no chunking needed)
- Performance: 60-70% faster for long articles with parallel chunk processing
- Chunking efficiency: <20% overhead
- Consolidation accuracy: >95% deduplication
- Configuration flexibility: All thresholds adjustable without code changes
- Test coverage: >90% for new code
- Zero breaking changes to existing API

## Confidence Score: 9/10

High confidence based on:
- Clear specification in PipelineActualizado
- Existing robust architecture to build upon
- Well-defined prompts for each phase
- Proven patterns from current implementation
- Explicit SuperClaude commands for each task

Minor uncertainty only in consolidation algorithms complexity.