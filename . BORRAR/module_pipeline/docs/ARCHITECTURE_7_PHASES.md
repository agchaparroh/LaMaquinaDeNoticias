# Arquitectura Adaptativa del Pipeline de 7 Fases

## Resumen Ejecutivo

Este documento define la arquitectura completa para la ampliación del pipeline de procesamiento de 4 a 7 fases, implementando procesamiento adaptativo, chunking inteligente y paralelización estratégica.

## Principios de Diseño

1. **Construcción sobre cimientos**: Toda la funcionalidad existente se preserva y extiende
2. **Simplicidad robusta**: Soluciones simples y probadas sobre complejidad innecesaria
3. **Adaptabilidad**: Flujo dinámico basado en características del contenido
4. **Escalabilidad**: Manejo eficiente de artículos largos mediante chunking
5. **Mantenibilidad**: Arquitectura modular con responsabilidades claras

## Arquitectura General

### Flujo de Procesamiento

```
ENTRADA → [FASE 1: Triaje + Análisis] → Decisión Adaptativa
                    ↓
         [FASE 2: Simplificación] → ¿Requiere Chunking?
                    ↓                        ↓
         [FASES 3-6: Extracción]      [Chunking Service]
                    ↓                        ↓
         [Consolidación Cross-Chunk] ←──────┘
                    ↓
         [FASE 7: Normalización + Relaciones]
                    ↓
              PERSISTENCIA
```

## Componentes Principales

### 1. Controlador de Flujo Adaptativo

**Ubicación**: `src/module_pipeline/src/services/adaptive_flow_controller.py`

```python
class AdaptiveFlowController:
    """
    Toma decisiones dinámicas sobre el flujo del pipeline basándose
    en el análisis de contenido de la Fase 1.
    """
    
    def __init__(self, config: PipelineConfig):
        self.chunking_thresholds = {
            'entities': config.CHUNKING_ENTITIES_THRESHOLD,
            'characters': config.CHUNKING_CHARS_THRESHOLD,
            'quotes': config.CHUNKING_QUOTES_THRESHOLD,
            'data': config.CHUNKING_DATA_THRESHOLD
        }
    
    def evaluate_content(self, analysis: AnalisisComponentes) -> FlowDecision:
        """
        Evalúa métricas del contenido y decide:
        - Qué fases ejecutar
        - Si requiere chunking
        - Qué modelo LLM usar
        """
        decision = FlowDecision()
        
        # Decisiones de chunking
        decision.chunk_entities = analysis.conteo_entidades > self.chunking_thresholds['entities']
        decision.chunk_facts = analysis.longitud_caracteres > self.chunking_thresholds['characters']
        decision.chunk_quotes = analysis.es_entrevista or analysis.conteo_citas > self.chunking_thresholds['quotes']
        decision.chunk_data = analysis.conteo_datos > self.chunking_thresholds['data']
        
        # Decisiones de fases condicionales
        decision.execute_data_phase = analysis.conteo_datos > 0
        decision.execute_quotes_phase = analysis.conteo_citas > 0
        
        return decision
```

### 2. Servicio de Chunking Inteligente

**Ubicación**: `src/module_pipeline/src/services/chunking_service.py`

```python
class ChunkingService:
    """
    Divide contenido largo en chunks manejables preservando contexto.
    """
    
    def __init__(self, config: ChunkingConfig):
        self.max_chunk_size = config.MAX_CHUNK_SIZE
        self.overlap_size = config.OVERLAP_SIZE
        self.context_window = config.CONTEXT_WINDOW
    
    def create_chunks(
        self, 
        text: str, 
        chunk_type: ChunkType,
        preserve_boundaries: bool = True
    ) -> List[TextChunk]:
        """
        Crea chunks inteligentes basados en:
        - Límites de oraciones/párrafos
        - Ventanas de contexto superpuestas
        - Preservación de elementos completos
        """
        chunks = []
        
        if preserve_boundaries:
            # Usar spaCy para detectar límites naturales
            doc = self.nlp(text)
            sentences = list(doc.sents)
            chunks = self._create_sentence_aware_chunks(sentences)
        else:
            # Chunking simple por caracteres con overlap
            chunks = self._create_overlapping_chunks(text)
        
        return chunks
    
    def _preserve_chunk_context(self, chunk: TextChunk) -> TextChunk:
        """
        Añade contexto a cada chunk para mejorar comprensión del LLM.
        """
        chunk.context = {
            'chunk_index': chunk.index,
            'total_chunks': chunk.total,
            'has_previous': chunk.index > 0,
            'has_next': chunk.index < chunk.total - 1,
            'overlap_text': chunk.overlap_text
        }
        return chunk
```

### 3. Sistema de Consolidación Cross-Chunk

**Ubicación**: `src/module_pipeline/src/services/consolidation_service.py`

```python
class ConsolidationService:
    """
    Consolida elementos extraídos de múltiples chunks eliminando duplicados
    y unificando referencias.
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.entity_matcher = EntityMatcher()
        self.fact_merger = FactMerger()
    
    def consolidate_entities(
        self, 
        entities_by_chunk: Dict[int, List[EntidadProcesada]]
    ) -> List[EntidadProcesada]:
        """
        Consolida entidades usando:
        - Coincidencia exacta de nombres
        - Similitud fuzzy (Levenshtein)
        - Análisis de contexto
        """
        consolidated = []
        entity_groups = self._group_similar_entities(entities_by_chunk)
        
        for group in entity_groups:
            # Fusionar información de entidades similares
            merged_entity = self._merge_entity_group(group)
            consolidated.append(merged_entity)
        
        return consolidated
    
    def consolidate_facts(
        self, 
        facts_by_chunk: Dict[int, List[HechoProcesado]]
    ) -> List[HechoProcesado]:
        """
        Consolida hechos considerando:
        - Superposición semántica
        - Temporalidad
        - Entidades involucradas
        """
        # Implementación similar pero específica para hechos
        pass
```

### 4. Modelos de Datos Extendidos

**Nuevos modelos para soportar 7 fases**:

```python
# src/module_pipeline/src/models/analisis.py
class AnalisisComponentes(BaseModel):
    """Resultado del análisis spaCy en Fase 1."""
    conteo_datos: int
    conteo_citas: int
    conteo_entidades: int
    longitud_caracteres: int
    es_entrevista: bool
    metricas_adicionales: Dict[str, Any]

# src/module_pipeline/src/models/simplificacion.py
class ResultadoSimplificacion(PipelineBaseModel):
    """Resultado de la Fase 2: Simplificación."""
    id_fragmento: UUID
    texto_original: str
    texto_simplificado: str
    transformaciones_aplicadas: List[str]
    metricas_simplificacion: Dict[str, float]

# src/module_pipeline/src/models/chunking.py
class TextChunk(BaseModel):
    """Representa un chunk de texto."""
    index: int
    total: int
    text: str
    start_offset: int
    end_offset: int
    overlap_text: Optional[str]
    context: Dict[str, Any]

# src/module_pipeline/src/models/relaciones.py
class RelacionHechoEntidad(BaseModel):
    """Relación entre hecho y entidad (Fase 7B.1)."""
    hecho_id: int
    entidad_id: int
    tipo_relacion: str
    relevancia_en_hecho: int

class RelacionHechoHecho(BaseModel):
    """Relación temporal entre hechos (Fase 7B.2)."""
    hecho_origen_id: int
    hecho_destino_id: int
    tipo_relacion: str
    fuerza_relacion: int
    descripcion_relacion: str
```

### 5. Configuración Dinámica

**Sistema de configuración basado en variables de entorno**:

```python
# src/module_pipeline/src/config/pipeline_config.py
class PipelineConfig:
    """Configuración central del pipeline."""
    
    # Umbrales de chunking
    CHUNKING_ENTITIES_THRESHOLD: int = int(os.getenv('PIPELINE_CHUNKING_ENTITIES_THRESHOLD', '30'))
    CHUNKING_CHARS_THRESHOLD: int = int(os.getenv('PIPELINE_CHUNKING_CHARS_THRESHOLD', '6000'))
    CHUNKING_QUOTES_THRESHOLD: int = int(os.getenv('PIPELINE_CHUNKING_QUOTES_THRESHOLD', '30'))
    CHUNKING_DATA_THRESHOLD: int = int(os.getenv('PIPELINE_CHUNKING_DATA_THRESHOLD', '30'))
    
    # Modelos LLM
    GROQ_MODEL_DEFAULT: str = os.getenv('PIPELINE_GROQ_MODEL_DEFAULT', 'llama-3.1-8b-instant')
    GROQ_MODEL_LARGE: str = os.getenv('PIPELINE_GROQ_MODEL_LARGE', 'llama-3.1-70b-versatile')
    GROQ_MODEL_TOKEN_THRESHOLD: int = int(os.getenv('PIPELINE_GROQ_MODEL_TOKEN_THRESHOLD', '8000'))
    
    # Consolidación
    CONSOLIDATION_SIMILARITY_THRESHOLD: float = float(os.getenv('PIPELINE_CONSOLIDATION_SIMILARITY_THRESHOLD', '0.85'))
    
    # Paralelización
    CHUNK_PARALLEL_ENABLED: bool = os.getenv('PIPELINE_CHUNK_PARALLEL_ENABLED', 'true').lower() == 'true'
    MAX_CONCURRENT_CHUNKS: int = int(os.getenv('PIPELINE_MAX_CONCURRENT_CHUNKS', '5'))
```

### 6. Estrategia de Paralelización

**Dos niveles de paralelización**:

1. **Chunk Parallelization** (Fases 3-6):
   ```python
   async def process_chunks_parallel(chunks: List[TextChunk], phase_function):
       if not config.CHUNK_PARALLEL_ENABLED:
           return await process_chunks_sequential(chunks, phase_function)
       
       # Limitar concurrencia
       sem = asyncio.Semaphore(config.MAX_CONCURRENT_CHUNKS)
       
       async def process_with_limit(chunk):
           async with sem:
               return await phase_function(chunk)
       
       # Procesar en paralelo
       results = await asyncio.gather(*[
           process_with_limit(chunk) for chunk in chunks
       ])
       return results
   ```

2. **Relation Detection Parallelization** (Fase 7B):
   ```python
   async def detect_relations_parallel(elements):
       # Ejecutar 7B.1 y 7B.2 en paralelo
       structural_task = detect_structural_relations(elements)
       temporal_task = detect_temporal_relations(elements)
       
       structural_rels, temporal_rels = await asyncio.gather(
           structural_task,
           temporal_task
       )
       
       return merge_relations(structural_rels, temporal_rels)
   ```

## Estructura de Archivos Actualizada

```
src/module_pipeline/
├── src/
│   ├── config/
│   │   └── pipeline_config.py          # Nueva configuración central
│   ├── pipeline/
│   │   ├── fase_1_triaje.py           # Extendida con análisis spaCy
│   │   ├── fase_2_simplificacion.py   # NUEVA
│   │   ├── fase_3_entidades.py        # NUEVA (reemplaza parte de fase_2)
│   │   ├── fase_4_hechos.py           # NUEVA (reemplaza parte de fase_2)
│   │   ├── fase_5_datos.py            # NUEVA (reemplaza parte de fase_3)
│   │   ├── fase_6_citas.py            # NUEVA (reemplaza parte de fase_3)
│   │   └── fase_7_relaciones.py       # NUEVA (extiende fase_4)
│   ├── services/
│   │   ├── adaptive_flow_controller.py # NUEVO
│   │   ├── chunking_service.py        # NUEVO
│   │   ├── consolidation_service.py   # NUEVO
│   │   └── parallel_executor.py       # NUEVO
│   ├── models/
│   │   ├── analisis.py                # NUEVO
│   │   ├── simplificacion.py          # NUEVO
│   │   ├── chunking.py                # NUEVO
│   │   └── relaciones.py              # NUEVO
│   └── controller.py                  # Actualizado para 7 fases
```

## Flujo de Ejecución Detallado

### 1. Fase 1: Triaje + Análisis (Mejorada)

```python
def ejecutar_fase_1_mejorada(fragmento):
    # 1A: Evaluación de relevancia (existente)
    relevancia = evaluar_relevancia_groq(fragmento)
    
    # 1B: Análisis de componentes (NUEVO)
    analisis = analizar_contenido_spacy(fragmento)
    
    # 1C: Decisión de flujo (NUEVO)
    flow_decision = controller.evaluate_content(analisis)
    
    return ResultadoFase1Extendido(
        relevancia=relevancia,
        analisis=analisis,
        flow_decision=flow_decision
    )
```

### 2. Fases 2-6: Procesamiento con Chunking Opcional

```python
async def ejecutar_fase_con_chunking(
    fase_num: int,
    texto: str,
    flow_decision: FlowDecision,
    fase_function: Callable
):
    # Determinar si requiere chunking
    needs_chunking = flow_decision.get_chunking_decision(fase_num)
    
    if needs_chunking:
        # Crear chunks
        chunks = chunking_service.create_chunks(texto, fase_num)
        
        # Procesar en paralelo si está habilitado
        if config.CHUNK_PARALLEL_ENABLED:
            results = await process_chunks_parallel(chunks, fase_function)
        else:
            results = process_chunks_sequential(chunks, fase_function)
        
        # Consolidar resultados
        consolidated = consolidation_service.consolidate(results, fase_num)
        return consolidated
    else:
        # Procesamiento simple sin chunking
        return await fase_function(texto)
```

### 3. Fase 7: Normalización y Relaciones Paralelas

```python
async def ejecutar_fase_7(elementos_consolidados):
    # 7A: Normalización (secuencial)
    elementos_normalizados = normalizar_entidades(elementos_consolidados)
    
    # 7B: Detección de relaciones (paralelo)
    relaciones = await detect_relations_parallel(elementos_normalizados)
    
    return ResultadoFase7(
        elementos_normalizados=elementos_normalizados,
        relaciones=relaciones
    )
```

## Consideraciones de Implementación

### Preservación de Funcionalidad

1. **spaCy existente**: Todas las funciones actuales se mantienen
2. **IDs secuenciales**: Sistema actual se extiende para soportar chunks
3. **Modelos Pydantic**: Se extienden, no se reemplazan
4. **API endpoints**: Sin cambios breaking

### Manejo de Errores

1. **Fallback por fase**: Cada fase tiene su propio manejo de errores
2. **Degradación elegante**: Si chunking falla, procesar completo
3. **Logging estructurado**: Contexto completo en cada operación

### Optimizaciones

1. **Caché de modelos spaCy**: Reutilizar modelos cargados
2. **Batch processing**: Agrupar llamadas LLM cuando sea posible
3. **Early termination**: Salir temprano si no es relevante

## Métricas y Monitoreo

### KPIs del Pipeline

1. **Throughput**: Artículos/minuto procesados
2. **Latencia por fase**: P50, P90, P99
3. **Tasa de chunking**: % de artículos que requieren chunking
4. **Precisión de consolidación**: % de duplicados eliminados
5. **Uso de recursos**: CPU, memoria, llamadas API

### Instrumentación

```python
@monitor_phase("fase_3_entidades")
async def ejecutar_fase_3(texto, context):
    with context.timer("extraction_time"):
        entities = await extract_entities(texto)
    
    context.record("entities_found", len(entities))
    context.record("chunking_used", context.used_chunking)
    
    return entities
```

## Conclusión

Esta arquitectura proporciona:

1. **Flexibilidad**: Adaptación dinámica según contenido
2. **Escalabilidad**: Manejo eficiente de contenido largo
3. **Mantenibilidad**: Separación clara de responsabilidades
4. **Performance**: Paralelización estratégica
5. **Confiabilidad**: Manejo robusto de errores

La implementación debe seguir el orden de las tareas del PRP, comenzando con el análisis spaCy mejorado y construyendo incrementalmente sobre la base existente.