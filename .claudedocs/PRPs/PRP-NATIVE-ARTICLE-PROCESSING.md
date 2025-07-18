# PRP: Native Article Processing - La Máquina de Noticias Pipeline
**Version**: 1.0.0  
**Date**: 2025-01-18  
**Status**: DRAFT  
**Type**: Feature Enhancement  
**Priority**: HIGH  

---

## Executive Summary

This PRP defines the complete architecture and implementation plan for native article processing within the La Máquina de Noticias pipeline. Currently, the pipeline processes articles as single fragments, missing opportunities for optimized processing based on article characteristics. This proposal outlines a comprehensive approach to differentiate between articles and fragments throughout the pipeline while maintaining backward compatibility.

---

## Current State Analysis

### 1. Pipeline Architecture Overview

The pipeline currently consists of 7 phases:

1. **Phase 1 - Triage**: SpaCy analysis for relevance and content structure
2. **Phase 2 - Simplification**: Optional text simplification using Groq LLM
3. **Phase 3 - Entities**: Entity extraction using Groq LLM
4. **Phase 4 - Facts**: Fact extraction using Groq LLM
5. **Phase 5 - Data**: Quantitative data extraction (conditional)
6. **Phase 6 - Quotes**: Quote extraction (conditional)
7. **Phase 7 - Normalization**: Entity normalization and relationship detection

### 2. Current Article-to-Fragment Conversion

```python
# In controller.py, lines 183-198
# Articles are converted to fragments with special ID prefix
if articulo_data.get('articulo_id'):
    id_fragmento = f"ART-{articulo_data['articulo_id']}"
else:
    id_fragmento = str(uuid.uuid4())

fragmento_data = {
    "id_fragmento": id_fragmento,
    "texto_original": contenido,
    "id_articulo_fuente": str(articulo_id),
    "orden_en_articulo": 0,  # Single fragment
    "metadata_adicional": {
        "es_articulo_completo": True,
        "fragmentado": False,
        # ... article metadata
    }
}
```

### 3. Type System Usage

The codebase uses several type patterns:

- **Union Types**: `Union[Dict[str, Any], BaseModel]` for payload flexibility
- **Type Checks**: `isinstance()` checks for Pydantic model vs dict
- **ID Management**: String-based IDs with prefixes (ART-{id} for articles)

### 4. Persistence Layer

Two main RPC endpoints handle persistence:
- `insertar_articulo_completo`: For complete articles
- `insertar_fragmento_completo`: For document fragments

The decision is made at persistence time based on metadata:
```python
# controller.py, lines 580-604
es_articulo = fragmento.metadata_adicional.get('es_articulo_completo', False)
if es_articulo:
    resultado_persistencia = supabase_service.insertar_articulo_completo(payload_dict)
else:
    resultado_persistencia = supabase_service.insertar_fragmento_completo(payload_dict)
```

### 5. Data Flow Analysis

```
API Endpoint → Controller → PipelineCoordinator → 7 Phases → PayloadBuilder → Supabase RPC
     ↓             ↓              ↓                    ↓            ↓              ↓
ArticuloInItem  Convert to   Process as        Extract data  Build payload  Persist
                Fragment      Fragment                        (article/fragment)
```

### 6. Current Issues and Opportunities

1. **Type Information Loss**: Article type is only preserved in metadata
2. **Processing Inefficiency**: Articles always go through fragment conversion
3. **Limited Optimization**: No article-specific processing paths
4. **Metadata Redundancy**: Article information duplicated in fragment metadata
5. **ID Management Complexity**: String prefixes instead of proper type differentiation

---

## Proposed Architecture

### 1. Type-Safe Processing Model

```python
from enum import Enum
from typing import Union, Protocol

class ContentType(Enum):
    ARTICLE = "article"
    FRAGMENT = "fragment"

class ProcessableContent(Protocol):
    """Protocol for any content that can be processed by the pipeline"""
    content_type: ContentType
    id: str
    text: str
    metadata: Dict[str, Any]
    
    def get_processing_context(self) -> Dict[str, Any]:
        """Returns context needed for processing"""
        ...

class ArticleContent:
    """Native article representation"""
    content_type = ContentType.ARTICLE
    
    def __init__(self, article: ArticuloInItem):
        self.id = f"ART-{article.articulo_id}" if article.articulo_id else str(uuid4())
        self.article_data = article
        self.text = article.contenido_texto
        self.metadata = {
            "medio": article.medio,
            "titular": article.titular,
            "fecha_publicacion": article.fecha_publicacion,
            # ... other article fields
        }
    
    def get_processing_context(self) -> Dict[str, Any]:
        return {
            "titulo": self.article_data.titular,
            "fecha_publicacion": str(self.article_data.fecha_publicacion),
            "fuente": self.article_data.medio,
            "pais": self.article_data.area_geografica,
            "tipo_medio": self.article_data.tipo_medio
        }

class FragmentContent:
    """Native fragment representation"""
    content_type = ContentType.FRAGMENT
    
    def __init__(self, fragment: FragmentoProcesableItem):
        self.id = fragment.id_fragmento
        self.fragment_data = fragment
        self.text = fragment.texto_original
        self.metadata = fragment.metadata_adicional or {}
    
    def get_processing_context(self) -> Dict[str, Any]:
        return {
            "titulo": self.metadata.get('titular', 'Sin título'),
            "fecha_publicacion": self.metadata.get('fecha_publicacion', ''),
            "fuente": self.metadata.get('medio', 'Desconocido'),
            "pais": self.metadata.get('area_geografica', 'España'),
            "tipo_medio": self.metadata.get('tipo_medio', 'Desconocido')
        }
```

### 2. Enhanced Pipeline Coordinator

```python
class PipelineCoordinator:
    def ejecutar_pipeline_completo(
        self,
        content: Union[ArticleContent, FragmentContent],
        modelo_spacy: Optional[str] = None,
        request_id: Optional[str] = None,
        groq_api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process any content type through the pipeline.
        """
        # Type-specific preprocessing
        if content.content_type == ContentType.ARTICLE:
            return self._process_article_optimized(content, **kwargs)
        else:
            return self._process_fragment_standard(content, **kwargs)
    
    def _process_article_optimized(
        self, 
        article: ArticleContent,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Optimized processing path for articles.
        """
        # Article-specific optimizations:
        # 1. Skip simplification for short articles
        # 2. Parallel entity/fact extraction for medium articles
        # 3. Smart chunking for long articles
        # 4. Article-level caching for repeated processing
        
        text_length = len(article.text)
        
        if text_length < 1000:  # Short article
            return self._process_short_article(article, **kwargs)
        elif text_length < 5000:  # Medium article
            return self._process_medium_article_parallel(article, **kwargs)
        else:  # Long article
            return self._process_long_article_chunked(article, **kwargs)
```

### 3. Processing Strategy by Article Size

#### Short Articles (<1000 chars)
- Skip Phase 2 (Simplification)
- Single-pass extraction
- No chunking needed
- Direct persistence

#### Medium Articles (1000-5000 chars)
- Conditional simplification
- Parallel extraction where possible
- Smart entity consolidation
- Optimized persistence

#### Long Articles (>5000 chars)
- Mandatory chunking
- Progressive processing
- Cross-chunk consolidation
- Batch persistence

### 4. Enhanced Controller Interface

```python
class PipelineController:
    async def process_content(
        self,
        content_data: Dict[str, Any],
        content_type: ContentType
    ) -> Dict[str, Any]:
        """
        Unified content processing with type awareness.
        """
        # Create appropriate content object
        if content_type == ContentType.ARTICLE:
            content = ArticleContent(ArticuloInItem(**content_data))
        else:
            content = FragmentContent(FragmentoProcesableItem(**content_data))
        
        # Process through pipeline
        resultado = self.pipeline_coordinator.ejecutar_pipeline_completo(
            content=content,
            request_id=content_data.get('request_id'),
            groq_api_key=os.getenv("GROQ_API_KEY"),
        )
        
        # Handle persistence with type awareness
        return self._persist_by_type(resultado, content)
```

### 5. Persistence Layer Enhancement

```python
class SupabaseService:
    def persist_content(
        self,
        payload: Union[Dict[str, Any], BaseModel],
        content_type: ContentType
    ) -> Optional[Dict[str, Any]]:
        """
        Type-aware persistence routing.
        """
        # Validate payload structure
        payload_dict = self._validar_estructura_payload(payload, content_type.value)
        
        # Route to appropriate RPC
        if content_type == ContentType.ARTICLE:
            return self._persist_article(payload_dict)
        else:
            return self._persist_fragment(payload_dict)
    
    def _persist_article(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enhanced article persistence with validation"""
        # Add article-specific validations
        self._validate_article_requirements(payload)
        
        # Call RPC with retry logic
        return self.insertar_articulo_completo(payload)
```

### 6. Type-Aware Payload Building

```python
class PayloadBuilder:
    def build_payload(
        self,
        content: ProcessableContent,
        processing_results: Dict[str, Any]
    ) -> Union[ArticuloPersistenciaPayload, FragmentoPersistenciaPayload]:
        """
        Build appropriate payload based on content type.
        """
        if content.content_type == ContentType.ARTICLE:
            return self._build_article_payload(content, processing_results)
        else:
            return self._build_fragment_payload(content, processing_results)
    
    def _build_article_payload(
        self,
        article: ArticleContent,
        results: Dict[str, Any]
    ) -> ArticuloPersistenciaPayload:
        """Build complete article payload with all required fields"""
        return ArticuloPersistenciaPayload(
            # Article metadata
            url=article.article_data.url,
            titular=article.article_data.titular,
            medio=article.article_data.medio,
            fecha_publicacion=str(article.article_data.fecha_publicacion),
            contenido_texto_original=article.text,
            
            # Processing results
            estado_procesamiento_final_pipeline="completado_ok",
            fecha_procesamiento_pipeline=datetime.utcnow().isoformat(),
            
            # Extracted elements
            hechos_extraidos=results.get("hechos", []),
            entidades_autonomas=results.get("entidades", []),
            citas_textuales_extraidas=results.get("citas", []),
            datos_cuantitativos_extraidos=results.get("datos", []),
            
            # Relationships
            relaciones_hechos=results.get("relaciones_hechos", []),
            relaciones_entidades=results.get("relaciones_entidades", []),
            contradicciones_detectadas=results.get("contradicciones", [])
        )
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1)
1. Implement `ProcessableContent` protocol and concrete classes
2. Add `ContentType` enum and type detection logic
3. Update models with type-aware interfaces
4. Create comprehensive unit tests for new types

### Phase 2: Pipeline Enhancement (Week 2)
1. Refactor `PipelineCoordinator` with type-aware processing
2. Implement size-based processing strategies
3. Add parallel processing for medium articles
4. Enhance chunking service for long articles

### Phase 3: Controller Integration (Week 3)
1. Update `PipelineController` with unified interface
2. Implement backward compatibility layer
3. Add performance monitoring
4. Create integration tests

### Phase 4: Persistence Optimization (Week 4)
1. Enhance `SupabaseService` with type routing
2. Optimize payload building
3. Add batch persistence for chunks
4. Implement transaction safety

### Phase 5: Testing & Optimization (Week 5)
1. Comprehensive end-to-end testing
2. Performance benchmarking
3. Error handling validation
4. Documentation updates

---

## Migration Strategy

### 1. Backward Compatibility
- Maintain existing endpoints during transition
- Auto-detect content type from input structure
- Gradual deprecation with clear timeline

### 2. Feature Flags
```python
FEATURE_FLAGS = {
    "NATIVE_ARTICLE_PROCESSING": False,  # Enable gradually
    "PARALLEL_EXTRACTION": False,        # Test in staging first
    "SMART_CHUNKING": True,             # Already tested
    "TYPE_AWARE_PERSISTENCE": False     # Requires DB validation
}
```

### 3. Rollout Plan
1. **Stage 1**: Deploy with all flags disabled
2. **Stage 2**: Enable in development environment
3. **Stage 3**: A/B test with 10% traffic
4. **Stage 4**: Gradual rollout to 100%
5. **Stage 5**: Remove old code paths

---

## Testing Strategy

### 1. Unit Tests
- Type detection and conversion
- Processing strategy selection
- Payload building for each type
- Error handling for edge cases

### 2. Integration Tests
```python
class TestNativeArticleProcessing:
    def test_short_article_processing(self):
        """Test optimized path for short articles"""
        article = create_test_article(length=500)
        result = controller.process_content(article, ContentType.ARTICLE)
        
        assert result["processing_strategy"] == "short_article"
        assert result["phases_skipped"] == ["simplification"]
        assert result["processing_time"] < 2.0  # seconds
    
    def test_long_article_chunking(self):
        """Test chunking for long articles"""
        article = create_test_article(length=10000)
        result = controller.process_content(article, ContentType.ARTICLE)
        
        assert result["processing_strategy"] == "long_article_chunked"
        assert result["chunks_processed"] > 1
        assert result["consolidation_applied"] == True
```

### 3. Performance Tests
- Baseline current implementation
- Measure improvement per article size
- Validate resource usage
- Test concurrent processing

### 4. Error Scenarios
- Invalid content type
- Missing required fields
- Processing failures
- Persistence errors
- Timeout handling

---

## Monitoring & Metrics

### 1. Key Performance Indicators
- Processing time by content type and size
- Success rate per processing strategy
- Resource utilization (CPU, memory, API calls)
- Error rates by phase and type

### 2. Logging Enhancement
```python
logger.info(
    "Content processed",
    content_type=content.content_type.value,
    content_id=content.id,
    size_category=get_size_category(len(content.text)),
    processing_strategy=strategy_used,
    phases_executed=phases,
    processing_time_ms=elapsed_ms,
    elements_extracted={
        "facts": len(results.get("hechos", [])),
        "entities": len(results.get("entidades", [])),
        "quotes": len(results.get("citas", [])),
        "data": len(results.get("datos", []))
    }
)
```

### 3. Dashboard Metrics
- Real-time processing throughput by type
- Average processing time trends
- Error distribution by content type
- API usage optimization metrics

---

## Risk Analysis

### 1. Technical Risks
- **Risk**: Breaking changes to existing API
  - **Mitigation**: Comprehensive backward compatibility layer
  
- **Risk**: Performance regression for small articles
  - **Mitigation**: Benchmark and optimize critical paths
  
- **Risk**: Increased complexity
  - **Mitigation**: Clear separation of concerns, extensive documentation

### 2. Operational Risks
- **Risk**: Increased resource usage
  - **Mitigation**: Implement resource limits and monitoring
  
- **Risk**: Persistence failures with new payloads
  - **Mitigation**: Validate against Supabase schema, add retry logic

---

## Success Criteria

1. **Performance**: 30% reduction in average processing time for articles
2. **Reliability**: Maintain 99.9% success rate
3. **Scalability**: Handle 10x current load without degradation
4. **Maintainability**: Reduce code duplication by 40%
5. **Observability**: 100% of processing paths instrumented

---

## Documentation Requirements

1. **API Documentation**: Update all endpoints with type information
2. **Architecture Diagrams**: Create flow diagrams for each processing strategy
3. **Migration Guide**: Step-by-step instructions for existing integrations
4. **Performance Guide**: Best practices for optimal usage
5. **Troubleshooting Guide**: Common issues and solutions

---

## Conclusion

This PRP provides a comprehensive roadmap for implementing native article processing in the La Máquina de Noticias pipeline. The proposed architecture maintains backward compatibility while introducing significant performance optimizations and cleaner type handling throughout the system. The phased implementation approach ensures minimal disruption while delivering incremental value.

## Appendices

### A. Code Examples
[Detailed code examples for each component]

### B. Performance Benchmarks
[Current vs. expected performance metrics]

### C. Database Schema Changes
[Any required Supabase schema updates]

### D. API Contract Changes
[Detailed API documentation updates]