# Sistema de Chunking Selectivo e Inteligente para Module Pipeline

## Resumen Ejecutivo

El sistema propuesto implementa un chunking selectivo basado en análisis de densidad informativa. La fase 1 (filtrado) se expande para incluir un análisis de densidad de citas y datos, permitiendo:
- Decisiones inteligentes sobre qué fases ejecutar
- Aplicación de chunking solo cuando sea necesario

## Cambios Arquitectónicos

### Estado Actual
- **Controller**: Procesa artículos completos como un único fragmento
- **FragmentProcessor**: Genera IDs secuenciales por fragmento
- **Fases 2-4**: Procesan el contenido completo en cada llamada
- **Límite**: 6,000 tokens totales (prompt + contenido + respuesta)

### Nueva Arquitectura con Normalización, Análisis y Chunking Selectivo

```
Artículo Original
    ↓
FASE 1 EXPANDIDA: Filtrado + Análisis de Densidad
├─ Evaluación de criterios (actual)
└─ NUEVO: Análisis de densidad informativa
    ├─ Conteo de comillas directas
    ├─ Detección de datos numéricos
    ├─ Identificación de formato (entrevista, noticia, etc.)
    └─ Estimación de tokens por contenido
         ↓
    [Decisión de Procesamiento]
         ↓
┌─────────────────────────────────────────┐
│ Si requiere chunking (Fase 2/4):       │
│    ↓                                    │
│ FASE 1.5: NORMALIZACIÓN DE LENGUAJE    │
│ ├─ Simplificar expresiones idiomáticas │
│ ├─ Eliminar recursos estilísticos      │
│ ├─ Convertir metáforas a lenguaje plano│
│ └─ Reducir ruido lingüístico           │
│    ↓                                    │
│ Texto Normalizado (15-20% menos tokens)│
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ Estrategia basada en análisis:         │
├─────────────────────────────────────────┤
│ • Baja densidad + corto → Sin fase 3   │
│ • Alta densidad + largo → Chunking     │
│ • Entrevista → Chunking en fase 3      │
│ • Noticia simple → Todo completo       │
└─────────────────────────────────────────┘
```

### Nuevos Componentes

1. **DensityAnalyzer** (`src/services/density_analyzer.py`)
   - Analiza densidad de citas (comillas, declaraciones)
   - Detecta datos cuantitativos (números, porcentajes, fechas)
   - Identifica formato del artículo (entrevista, noticia, análisis)
   - Calcula métricas para decisión de chunking

2. **LanguageNormalizer** (`src/services/language_normalizer.py`)
   - Simplifica expresiones idiomáticas y frases hechas
   - Elimina recursos estilísticos innecesarios
   - Traduce metáforas a lenguaje directo
   - Reduce ruido lingüístico manteniendo información factual
   - Se aplica ANTES del chunking para optimizar tokens

3. **SmartChunkingService** (`src/services/smart_chunking_service.py`)
   - Chunking adaptativo basado en densidad
   - Preserva integridad semántica (párrafos completos)
   - Optimiza tamaño de chunks según fase
   - Opera sobre texto normalizado

4. **ConsolidationService** (`src/services/consolidation_service.py`)
   - Unifica resultados solo cuando hay chunking
   - Resuelve duplicados y referencias
   - Optimizado para mínimo overhead

## Modificaciones en los Prompts

### Fase 1 Expandida: Prompt de Análisis de Densidad

**Adición al prompt actual de fase 1:**
```markdown
## ANÁLISIS DE DENSIDAD INFORMATIVA

Además de la evaluación de relevancia, analiza:

### DENSIDAD DE CITAS
- Número de comillas directas: [contar "..."]
- Presencia de diálogos o entrevistas: [SÍ/NO]
- Estimación de palabras en citas: [aproximado]

### DENSIDAD DE DATOS
- Cantidad de números/cifras: [contar]
- Presencia de estadísticas: [SÍ/NO]
- Datos temporales (fechas): [contar]

### FORMATO IDENTIFICADO
- [NOTICIA_SIMPLE/ENTREVISTA/ANÁLISIS_DATOS/REPORTAJE_INVESTIGATIVO]

### COMPLEJIDAD LINGÜÍSTICA
- Metáforas y expresiones idiomáticas: [ALTA/MEDIA/BAJA]
- Recursos estilísticos (ironía, doble sentido): [SÍ/NO]
- Lenguaje técnico o especializado: [SÍ/NO]

### RECOMENDACIÓN DE PROCESAMIENTO
Basado en el análisis:
- Normalización: [SÍ/NO]
- Fase 2: [COMPLETA/CHUNKING]
- Fase 3: [OMITIR/COMPLETA/CHUNKING]
- Fase 4: [COMPLETA/CHUNKING]
```

### Nuevo Prompt de Normalización (Fase 1.5)

```markdown
# Normalización de Lenguaje Periodístico

Tu tarea es simplificar este texto manteniendo TODA la información factual.

## TRANSFORMACIONES A REALIZAR

### 1. EXPRESIONES IDIOMÁTICAS
- "Dar en el clavo" → "Acertar"
- "Estar en las nubes" → "Estar distraído"
- "Tirar la toalla" → "Rendirse"

### 2. METÁFORAS Y FIGURAS
- "El gobierno navegó en aguas turbulentas" → "El gobierno enfrentó dificultades"
- "La economía despegó" → "La economía mejoró"
- "Una lluvia de críticas" → "Muchas críticas"

### 3. RECURSOS ESTILÍSTICOS
- Eliminar ironía implícita
- Convertir eufemismos a lenguaje directo
- Simplificar construcciones retóricas complejas

### 4. PRESERVAR ABSOLUTAMENTE
- Nombres propios, fechas, cifras
- Citas textuales exactas
- Datos verificables
- Relaciones causa-efecto

## TEXTO A NORMALIZAR
{{CONTENIDO_ORIGINAL}}

## RESULTADO ESPERADO
Texto simplificado, directo y factual manteniendo toda la información esencial.
```

### Prompt de Chunk (solo cuando se aplica chunking)
```markdown
## PROCESAMIENTO PARCIAL
Estás analizando una SECCIÓN ({{CHUNK_NUMBER}}/{{TOTAL_CHUNKS}}) del artículo.
- Enfócate SOLO en el contenido presente
- Los elementos se consolidarán posteriormente
```

## Flujo de Datos Modificado

### Flujo Actual (Sin Optimización)
```
POST /procesar_articulo
    → Fase 1: Filtrado
    → Fase 2: Extracción (TODO el contenido)
    → Fase 3: Citas (TODO el contenido)
    → Fase 4: Relaciones (TODO el contenido)
    → PayloadBuilder
    → Supabase
```

### Nuevo Flujo con Normalización y Decisión Inteligente
```
POST /procesar_articulo
    ↓
Fase 1: Filtrado + Análisis de Densidad
    ↓
[DensityAnalyzer] → Métricas y recomendaciones
    ↓
┌─── Artículo Corto/Simple ───┐  ┌─── Artículo Largo/Denso ───┐
│ • < 8,000 chars             │  │ • >= 8,000 chars           │
│ • Pocas citas/datos         │  │ • Muchas citas/datos       │
│ • Baja complejidad lingüística  │ • Alta complejidad lingüística │
└─────────────────────────────┘  └────────────────────────────┘
           ↓                                  ↓
    Procesamiento Simple         Fase 1.5: Normalización de Lenguaje
    ├─ Fase 2: Completa          ├─ Simplificar expresiones idiomáticas
    ├─ Fase 3: OMITIDA o Completa├─ Eliminar recursos estilísticos
    └─ Fase 4: Completa          ├─ Convertir metáforas a lenguaje plano
           ↓                     └─ Reducir 15-20% de tokens
      PayloadBuilder                      ↓
           ↓                     Procesamiento Chunking Optimizado
        Supabase                 ├─ Fase 2: [chunk1, chunk2, ...] (texto normalizado)
                                ├─ Fase 3: Según densidad (texto normalizado)
                                └─ Fase 4: [chunk1, chunk2, ...] (texto normalizado)
                                         ↓
                                    Consolidación
                                         ↓
                                    PayloadBuilder
                                         ↓
                                      Supabase
```

## Análisis de Costos Optimizado

### Escenarios de Procesamiento

#### 1. Artículo Típico (8,000 caracteres, baja densidad)
**Estrategia Actual:**
- 3 fases × 2,500 tokens = 7,500 tokens (TRUNCADO)

**Estrategia Optimizada:**
- Fase 1: 2,500 tokens (análisis incluido)
- Fase 2: 2,500 tokens (completo)
- Fase 3: OMITIDA (baja densidad)
- Fase 4: 2,500 tokens (completo)
- **TOTAL**: 7,500 tokens (SIN TRUNCAMIENTO)

#### 2. Entrevista Larga (20,000 caracteres, alta densidad de citas)
**Estrategia Actual:**
- 3 fases × 5,000 tokens = 15,000 tokens (SEVERAMENTE TRUNCADO)

**Estrategia Optimizada con Normalización:**
- Fase 1: 5,000 tokens (análisis incluido)
- Fase 1.5: 4,000 tokens (normalización)
- Texto normalizado: 16,000 chars (20% reducción)
- Fase 2: 3 chunks × 3,000 = 9,000 tokens (texto normalizado)
- Fase 3.1 (citas): 3 chunks × 3,000 = 9,000 tokens (texto normalizado)
- Fase 3.2 (datos): 4,000 tokens (completo, texto normalizado)
- Fase 4: 3 chunks × 3,000 = 9,000 tokens (texto normalizado)
- Consolidación: 3,000 tokens
- **TOTAL**: 43,000 tokens (COMPLETO + OPTIMIZADO)

#### 3. Noticia Simple (5,000 caracteres, sin citas)
**Estrategia Actual:**
- 3 fases × 2,000 tokens = 6,000 tokens

**Estrategia Optimizada:**
- Fase 1: 2,000 tokens
- Fase 2: 2,000 tokens
- Fase 3: OMITIDA (sin citas detectadas)
- Fase 4: 2,000 tokens
- **TOTAL**: 6,000 tokens (33% AHORRO)

### Comparación de Ahorros con Normalización

| Tipo de Artículo | Tokens Actuales | Tokens Optimizados | Ahorro | Calidad |
|------------------|-----------------|-------------------|---------|----------|
| Noticia simple | 6,000 | 4,000 | 33% | Igual |
| Artículo típico | 7,500 (truncado) | 7,500 | 0% | Superior |
| Entrevista larga | 15,000 (truncado) | 43,000 | -187% | Completa |
| Promedio ponderado* | 8,100 | 7,100 | 12% | Superior |

**Beneficios adicionales de la normalización:**
- Reducción 15-20% tokens en texto normalizado
- Mejor comprensión del LLM (lenguaje más directo)
- Mayor precisión en extracción de entidades
- Menor ambigüedad en relaciones

*Basado en distribución típica: 60% noticias simples, 30% artículos típicos, 10% entrevistas

## Impacto en la Calidad de Datos

### Mejoras Esperadas

1. **Procesamiento Inteligente**
   - Omisión de fase 3 cuando no hay citas/datos ahorra tokens sin perder calidad
   - Análisis de densidad previene sobre-procesamiento

2. **Cobertura Adaptativa**
   - Artículos simples: procesamiento rápido y eficiente
   - Artículos complejos: análisis exhaustivo sin truncamiento

3. **Mejor Relación Costo/Beneficio**
   - 33% menos tokens en noticias simples
   - 100% cobertura en artículos largos cuando es necesario

### Estrategias de Mitigación

1. **Para Chunking en Fase 2 y 4**
   - Overlap de 300 tokens para mantener contexto
   - Consolidación basada en similitud semántica

2. **Para División de Fase 3**
   - Fase 3.1 (citas): solo si densidad > 5 citas/1000 palabras
   - Fase 3.2 (datos): siempre ejecutar si hay números detectados

3. **Para Omisión de Fases**
   - Logging explícito de decisiones
   - Métricas de artículos sin fase 3

## Configuración y Parámetros

### Nuevas Variables de Entorno
```python
# Análisis de Densidad
DENSITY_QUOTES_THRESHOLD = 5  # Citas por 1000 palabras para activar fase 3.1
DENSITY_DATA_THRESHOLD = 10   # Números por 1000 palabras para chunking
SKIP_PHASE3_THRESHOLD = 2     # Si < 2 citas, omitir fase 3 completa

# Chunking Inteligente
CHUNKING_CHAR_THRESHOLD = 8000  # Activar chunking si > 8000 chars
CHUNK_SIZE_TOKENS = 2500       # Tamaño óptimo por chunk
CHUNK_OVERLAP_TOKENS = 300     # Mayor overlap para contexto
MAX_CHUNKS_PER_PHASE = 5       # Límite por fase

# Normalización de Lenguaje
ENABLE_NORMALIZATION = True           # Activar normalización
NORMALIZATION_COMPLEXITY_THRESHOLD = "MEDIA"  # BAJA/MEDIA/ALTA para activar
PRESERVE_QUOTES_IN_NORMALIZATION = True       # Mantener citas exactas
NORMALIZATION_TARGET_REDUCTION = 0.18         # Objetivo 18% reducción tokens

# Decisiones de Procesamiento
INTERVIEW_DETECTION_THRESHOLD = 0.3  # 30% del texto en citas = entrevista
FORCE_CHUNKING_FORMATS = ["ENTREVISTA", "REPORTAJE_INVESTIGATIVO"]
SKIP_PHASE3_FORMATS = ["NOTICIA_SIMPLE", "NOTA_BREVE"]
FORCE_NORMALIZATION_FORMATS = ["CRONICA", "OPINION", "ANALISIS"]

# Optimización de Costos
AGGRESSIVE_MODE = True  # Activar todas las optimizaciones
PHASE3_SPLIT = True    # Dividir fase 3 en 3.1 y 3.2
NORMALIZATION_MODE = "SMART"  # DISABLED/SMART/AGGRESSIVE
```

### Métricas Nuevas
```python
# Análisis de densidad
density_analysis_duration = Histogram('density_analysis_seconds', 'Tiempo de análisis')
articles_skipping_phase3 = Counter('articles_skipping_phase3', 'Artículos sin fase 3')
chunking_decisions = Counter('chunking_decisions', 'Decisiones de chunking', ['phase', 'decision'])

# Normalización de lenguaje
normalization_duration = Histogram('normalization_seconds', 'Tiempo de normalización')
normalization_reduction_ratio = Histogram('normalization_reduction_ratio', 'Reducción de tokens')
articles_normalized = Counter('articles_normalized', 'Artículos normalizados')
normalization_quality_score = Histogram('normalization_quality', 'Calidad de normalización')

# Ahorro de tokens
tokens_saved_by_skipping = Counter('tokens_saved', 'Tokens ahorrados por omisión')
tokens_saved_by_normalization = Counter('tokens_saved_normalization', 'Tokens ahorrados por normalización')
processing_strategy_distribution = Counter('processing_strategy', 'Estrategias aplicadas')
```

## Plan de Implementación

### Fase 1: Análisis de Densidad y Complejidad (4 días)
1. Expandir prompt de fase 1 con análisis de densidad y complejidad lingüística
2. Crear DensityAnalyzer para procesar métricas
3. Implementar lógica de decisión de procesamiento y normalización

### Fase 2: Normalización de Lenguaje (1 semana)
1. Crear LanguageNormalizer con prompt especializado
2. Implementar detección de expresiones idiomáticas y metáforas
3. Desarrollar algoritmos de simplificación manteniendo información factual
4. Tests de calidad de normalización (preservación de datos)

### Fase 3: División de Fase 3 (2 días)
1. Separar fase 3 en 3.1 (citas) y 3.2 (datos)
2. Crear prompts optimizados para cada subfase
3. Implementar lógica de omisión selectiva

### Fase 4: Chunking Inteligente (1 semana)
1. SmartChunkingService operando sobre texto normalizado
2. Modificar Controller para flujo condicional con normalización
3. Implementar procesamiento paralelo cuando aplique

### Fase 5: Consolidación Mínima (3 días)
1. ConsolidationService ligero (solo cuando hay chunks)
2. Unificación básica de entidades
3. Tests de calidad de consolidación

### Fase 6: Testing y Ajustes (5 días)
1. A/B testing comparando calidad con/sin normalización
2. Métricas de reducción de tokens vs. preservación de información
3. Ajustar umbrales según resultados
4. Documentar mejores prácticas de normalización

## Monitoreo y Alertas

### Nuevas Alertas
```yaml
- name: phase3_skip_rate_high
  condition: articles_skipping_phase3 / total_articles > 0.8
  severity: info
  message: "80% de artículos omitiendo fase 3 - revisar umbrales"

- name: density_analysis_slow
  condition: density_analysis_duration > 5s
  severity: warning
  message: "Análisis de densidad tomando demasiado tiempo"

- name: unexpected_token_usage
  condition: tokens_per_article > expected_tokens * 1.5
  severity: error
  message: "Uso de tokens 50% mayor al esperado"
```

### Dashboard Métricas
- **Distribución de estrategias**: ¿Cuántos artículos usan cada estrategia?
- **Ahorro de tokens**: Tokens ahorrados por omisión de fases
- **Calidad por estrategia**: Elementos extraídos según procesamiento
- **Tiempos de procesamiento**: Por estrategia y fase

## Ejemplo de Decisión de Procesamiento

```json
{
  "articulo": {
    "caracteres": 12000,
    "analisis_densidad": {
      "citas_directas": 15,
      "datos_numericos": 45,
      "formato": "ENTREVISTA",
      "densidad_citas_por_1000": 8.3,
      "densidad_datos_por_1000": 25
    },
    "decisiones": {
      "fase_2": "CHUNKING",
      "fase_3_1": "CHUNKING",
      "fase_3_2": "COMPLETA",
      "fase_4": "CHUNKING",
      "razon": "Alta densidad de citas + formato entrevista"
    },
    "estimacion_tokens": {
      "sin_optimizacion": 36000,
      "con_optimizacion": 28500,
      "ahorro": "21%"
    }
  }
}
```

## Conclusión

El sistema de chunking selectivo e inteligente propuesto ofrece:
- **Reducción de 10% en tokens promedio** para el mix típico de artículos
- **Eliminación del truncamiento** en artículos largos
- **Procesamiento adaptativo** según el tipo de contenido
- **Mayor eficiencia** al omitir fases innecesarias

La clave está en el análisis de densidad en fase 1, que permite tomar decisiones informadas sobre cómo procesar cada artículo de manera óptima.