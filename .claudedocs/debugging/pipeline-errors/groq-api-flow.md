# Flujo de Groq API en el Pipeline

## Resumen de Alto Nivel

El pipeline hace **8-9 llamadas a Groq API** por artículo (sin chunking):
- Fase 1: Una llamada para triaje + posible llamada para traducción
- Fases 2-6: Una llamada cada una
- Fase 7A: Usa Supabase (NO Groq)
- Fase 7B: Dos llamadas (7B.1 y 7B.2)

## Flujo de Llamadas

```
Artículo → Fase 1 (Groq triaje + traducción opcional) → Fase 2 (Groq) → ... → Fase 7A (Supabase) → Fase 7B.1 (Groq) → Fase 7B.2 (Groq)
```

## Modelos LLM

- **Modelo por defecto**: `llama-3.1-8b-instant`
- **Modelo grande**: `llama3-70b-8192` (se activa si tokens estimados > 8000)
- **Estimación de tokens**: `longitud_texto / 4`

## Llamadas por Fase

### 1. Triaje (SÍ usa Groq)
- **Procesamiento inicial**: spaCy para limpieza y detección de idioma
- **Llamada Groq**: Evaluación de relevancia con prompt desde `prompts/Importancia.md`
- **Temperature**: 0.1
- **Max tokens**: 1000
- **Input**: Texto limpio + metadata (título, medio, país, fecha)
- **Output**: `{decision: PROCESAR/DESCARTAR, justificacion, tipo_articulo, puntuacion_triaje, elementos_clave}`
- **Traducción opcional**: Si idioma != "es" y decision != "DESCARTAR", hace otra llamada Groq

### 2. Simplificación  
- **Input**: Texto original completo
- **Temperature**: 0.3 (más creativa)
- **Prompt**: Simplificar manteniendo información esencial
- **Output**: `{texto_simplificado, metricas}`

### 3. Entidades
- **Input**: Texto simplificado (de fase 2)
- **Temperature**: 0.1
- **Prompt**: Extraer personas, organizaciones, lugares
- **Output**: `[{id, nombre, tipo, rol}]`

### 4. Hechos
- **Input**: Texto simplificado + entidades extraídas
- **Temperature**: 0.1
- **Prompt**: Extraer acontecimientos y vincular con IDs de entidades
- **Output**: `[{id, descripcion, categoria, entidades_involucradas}]`

### 5. Citas (NOTA: Orden cambiado vs numeración de archivos)
- **Input**: Texto original + entidades extraídas ({{Fase3_Entidades}})
- **Temperature**: 0.1
- **Prompt**: Extraer citas textuales exactas
- **Output**: `[{id, texto, autor, entidad_autor_id}]`

### 6. Datos
- **Input**: Texto simplificado + hechos extraídos ({{Fase4_Hechos}})
- **Temperature**: 0.1
- **Prompt**: Extraer datos cuantitativos y métricas
- **Output**: `[{id, indicador, valor, unidad, periodo}]`

### 7A. Normalización de Entidades (NO usa Groq)
- **Procesamiento**: Búsqueda en Supabase por similitud
- **Output**: Entidades normalizadas con UUIDs de la BD

### 7B.1 Relaciones Estructurales
- **Input**: Variable {{HECHOS_Y_ENTIDADES_CONTEXTO}} - JSON mínimo con solo IDs, nombres y tipos
- **Temperature**: 0.1
- **Max tokens**: 4000
- **Optimización**: NO incluye descripciones completas ni metadata
- **Tipos de relaciones**: CAUSAL, CONDICIONAL, OPOSICION, COOPERACION, AFILIACION, TEMPORAL
- **Output**: `{relaciones_hechos: [{hecho_id_1, hecho_id_2, tipo_relacion, fuerza}], relaciones_entidades: [{entidad_id_1, entidad_id_2, tipo_relacion, relevancia}]}`

### 7B.2 Relaciones Temporales y Contradicciones
- **Input**: {{HECHOS_CONTEXTO}} + {{TEXTO_SIMPLIFICADO}} **recortado a 3000 caracteres**
- **Temperature**: 0.1
- **Max tokens**: 4000
- **Optimización**: Texto limitado para ahorrar tokens
- **Tipos de relaciones temporales**: SIMULTANEO, SECUENCIAL, CAUSAL_TEMPORAL
- **Output**: `{relaciones_temporales: [{hecho_id_1, hecho_id_2, tipo_relacion, orden_temporal}], contradicciones_detectadas: [{hecho_id_1, hecho_id_2, tipo_contradiccion, descripcion}]}`

## Sistema de Chunking

Se activa cuando se superan estos umbrales:
- **Entidades**: >30 entidades
- **Caracteres**: >6000 caracteres  
- **Citas**: >30 citas
- **Datos**: >30 datos cuantitativos

Configuración:
- **Tamaño chunk**: 3000 caracteres
- **Overlap**: 200 caracteres
- **Procesamiento paralelo**: Hasta 5 chunks simultáneos
- **Efecto**: Multiplica las llamadas a Groq por número de chunks

## Optimizaciones de Tokens

1. **Recorte de contexto**:
   - Fase 7B.2: Texto simplificado limitado a 3000 caracteres
   - Prompts incluyen solo campos esenciales

2. **Selección de campos mínimos**:
   - Fases 7B: Solo IDs, nombres y tipos (no descripciones completas)
   - Contexto del documento: Solo título, fuente, país, fecha

3. **Selección automática de modelo**:
   - Si tokens estimados > 8000, cambia a `llama3-70b-8192`

## Configuración de Parámetros

```python
# Configuración típica
{
    "model": "llama-3.1-8b-instant",  # o llama3-70b-8192
    "temperature": 0.1,               # 0.3 solo para simplificación
    "max_tokens": 6000,               # 4000 para fases 7B
    "response_format": {"type": "json_object"}
}
```

## Archivos Clave

- `src/module_pipeline/src/services/llm_service.py` - Cliente y configuración Groq
- `src/module_pipeline/src/pipeline/fase_*.py` - Lógica y prompts por fase
- `src/module_pipeline/src/pipeline/fase_7_normalizacion.py` - Procesos 7A, 7B.1, 7B.2
- `src/module_pipeline/src/services/chunking_service.py` - Sistema de chunking
- `src/module_pipeline/prompts/*.md` - Prompts detallados para cada fase:
  - `Importancia.md` - Fase 1: Sistema de puntuación y criterios de exclusión
  - `Simplificación.md` - Fase 2: Transformaciones de lenguaje
  - `Entidades.md` - Fase 3: Extracción de personas, organizaciones, lugares
  - `Hechos.md` - Fase 4: Extracción de acontecimientos
  - `Citas.md` - Fase 5: Citas textuales (nota: numeración invertida con Datos)
  - `Datos.md` - Fase 6: Datos cuantitativos
  - `7B.1_Relaciones-Estructurales.md` - Relaciones entre hechos y entidades
  - `7B.2_Relaciones-Temporales.md` - Relaciones temporales y contradicciones

## Variables de Contexto en Prompts

Las siguientes variables se sustituyen en los prompts antes de enviar a Groq:
- `{{TITULO}}`, `{{FUENTE}}`, `{{PAIS}}`, `{{FECHA_FUENTE}}` - Metadata del artículo
- `{{CONTENIDO}}` o `{{CONTENIDO_ORIGINAL}}` - Texto a procesar
- `{{Fase3_Entidades}}` - Resultados de fase 3 (usado en fases 5 y 6)
- `{{Fase4_Hechos}}` - Resultados de fase 4 (usado en fase 6)
- `{{HECHOS_Y_ENTIDADES_CONTEXTO}}` - JSON mínimo para fase 7B.1
- `{{TEXTO_SIMPLIFICADO}}` - Texto recortado para fase 7B.2