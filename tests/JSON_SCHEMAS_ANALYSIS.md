# JSON Schemas Analysis - La Máquina de Noticias Pipeline

## Overview
This document analyzes all JSON schemas used throughout the pipeline phases (fase_1 through fase_7) in the news processing system.

## Phase 1: Triaje (Triage)
**File**: `src/module_pipeline/src/pipeline/fase_1_triaje.py`
**Prompt**: `src/module_pipeline/prompts/Importancia.md`

The triaje phase doesn't use structured JSON output. Instead, it uses text-based parsing with regex patterns to extract:
- EXCLUSIÓN: SÍ/NO
- TIPO DE ARTÍCULO
- Puntuaciones (0-5) for various criteria
- DECISIÓN: PROCESAR/CONSIDERAR/DESCARTAR
- JUSTIFICACIÓN
- ELEMENTOS CLAVE

## Phase 2: Simplificación (Simplification)
**File**: `src/module_pipeline/src/pipeline/fase_2_simplificacion.py`
**Prompt**: `src/module_pipeline/prompts/Simplificación.md`

This phase appears to return simplified text rather than structured JSON output.

## Phase 3: Entidades (Entities)
**File**: `src/module_pipeline/src/pipeline/fase_3_entidades.py`
**Prompt**: `src/module_pipeline/prompts/Entidades.md`
**Response Format**: `{"type": "json_object"}`

### JSON Schema:
```json
{
  "entidades": [
    {
      "id": 1,
      "nombre": "string",
      "alias": ["string"],
      "tipo": "PERSONA|ORGANIZACION|INSTITUCION|LUGAR|EVENTO|NORMATIVA|CONCEPTO",
      "descripcion": "string with - bullet points",
      "fecha_nacimiento": "YYYY-MM-DD|null",
      "fecha_disolucion": "YYYY-MM-DD|null"
    }
  ]
}
```

## Phase 4: Hechos (Facts)
**File**: `src/module_pipeline/src/pipeline/fase_4_hechos.py`
**Prompt**: `src/module_pipeline/prompts/Hechos.md`
**Response Format**: `{"type": "json_object"}`

### JSON Schema:
```json
{
  "hechos": [
    {
      "id": 1,
      "contenido": "string",
      "fecha_inicio": "YYYY-MM-DD",
      "fecha_fin": "YYYY-MM-DD",
      "precision_temporal": "exacta|dia|semana|mes|trimestre|año|decada|periodo",
      "tipo_hecho": "SUCESO|ANUNCIO|DECLARACION|BIOGRAFIA|CONCEPTO|NORMATIVA|EVENTO",
      "pais": ["string"],
      "region": ["string"],
      "ciudad": ["string"],
      "es_futuro": boolean,
      "estado_programacion": "programado|confirmado|cancelado|modificado|null"
    }
  ]
}
```

## Phase 5: Datos Cuantitativos (Quantitative Data)
**File**: `src/module_pipeline/src/pipeline/fase_5_datos.py`
**Prompt**: `src/module_pipeline/prompts/Datos.md`
**Response Format**: `{"type": "json_object"}`

### JSON Schema:
```json
{
  "datos_cuantitativos": [
    {
      "id": 1,
      "hecho_id": 0,
      "indicador": "string",
      "categoria": "económico|demográfico|electoral|social|presupuestario|sanitario|ambiental|conflicto|otro",
      "valor": number,
      "unidad": "string",
      "ambito_geografico": ["string"],
      "periodo_inicio": "YYYY-MM-DD",
      "periodo_fin": "YYYY-MM-DD",
      "tipo_periodo": "anual|trimestral|mensual|semanal|diario|puntual|acumulado",
      "valor_anterior": number|null,
      "variacion_absoluta": number|null,
      "variacion_porcentual": number|null,
      "tendencia": "aumento|disminución|estable|null"
    }
  ]
}
```

## Phase 6: Citas Textuales (Quotes)
**File**: `src/module_pipeline/src/pipeline/fase_6_citas.py`
**Prompt**: `src/module_pipeline/prompts/Citas.md`
**Response Format**: `{"type": "json_object"}`

### JSON Schema:
```json
{
  "citas_textuales": [
    {
      "id": 1,
      "cita": "string",
      "entidad_id": 0,
      "hecho_id": 0,
      "fecha": "YYYY-MM-DD",
      "contexto": "string",
      "relevancia": 1-5
    }
  ]
}
```

## Phase 7: Normalización (Normalization) - Relaciones
**File**: `src/module_pipeline/src/pipeline/fase_7_normalizacion.py`
**Prompts**: 
- `src/module_pipeline/prompts/7B.1_Relaciones-Estructurales.md`
- `src/module_pipeline/prompts/7B.2_Relaciones-Temporales.md`
**Response Format**: `{"type": "json_object"}`

### JSON Schema for Structural Relations:
```json
{
  "hecho_entidad": [
    {
      "hecho_id": 0,
      "entidad_id": 0,
      "tipo_relacion": "protagonista|mencionado|afectado|declarante|ubicacion|contexto|victima|agresor|organizador|participante|otro",
      "relevancia_en_hecho": 1-10
    }
  ],
  "entidad_relacion": [
    {
      "entidad_origen_id": 0,
      "entidad_destino_id": 0,
      "tipo_relacion": "miembro_de|subsidiaria_de|aliado_con|opositor_a|sucesor_de|predecesor_de|casado_con|familiar_de|empleado_de",
      "descripcion": "string",
      "fecha_inicio": "YYYY-MM-DD|null",
      "fecha_fin": "YYYY-MM-DD|null",
      "fuerza_relacion": 1-10
    }
  ]
}
```

## Payload Builder Mapping
**File**: `src/module_pipeline/src/services/payload_builder.py`

The PayloadBuilder service maps the extracted data to the final RPC payload structure. Key mappings include:

### Entities Mapping:
- `id_entidad` → `id`
- `texto_entidad` → `nombre`
- `tipo_entidad` → `tipo`
- `relevancia_entidad` → `relevancia` (converted from 0-1 float to 1-10 int)
- `metadata_entidad` → `metadata`

### Quantitative Data Mapping:
- `id_temporal_hecho` → from `hecho_principal_relacionado_id_temporal`
- `indicador` → from `descripcion_dato`
- `valor_numerico` → from `valor_dato`
- `unidad` → from `unidad_dato`

## Key Observations

1. **JSON Response Format**: Most phases (3-7) use Groq's structured output with `response_format={"type": "json_object"}` to ensure valid JSON responses.

2. **ID Management**: The system uses temporal IDs throughout the pipeline phases that are mapped to final IDs in the payload builder.

3. **Data Validation**: The `parse_llm_json_response` function in `json_parser.py` handles various JSON parsing edge cases, including:
   - Markdown code blocks
   - Truncated JSON
   - Malformed structures

4. **Error Handling**: Each phase has comprehensive error handling that falls back to empty results if parsing fails.

5. **Schema Evolution**: The schemas show a progression from simple entity extraction to complex relationship mapping across phases.

## Usage Pattern

Each phase typically follows this pattern:
1. Prepare prompt with context and previous phase results
2. Call Groq API with `response_format={"type": "json_object"}`
3. Parse response using `parse_llm_json_response`
4. Map extracted data to internal models
5. Pass results to next phase

The final payload is assembled by the PayloadBuilder, which performs field mapping and validation before sending to the RPC functions.