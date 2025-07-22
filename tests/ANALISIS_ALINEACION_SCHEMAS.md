# Análisis de Alineación de Schemas JSON del Pipeline con la Función SQL

## Resumen Ejecutivo

Este documento presenta el análisis sistemático de la alineación entre los schemas JSON generados por el pipeline de procesamiento y la función SQL `actualizar_articulo_procesado.sql`.

### Estado General: ✅ ALINEADO CON OBSERVACIONES

El sistema está funcionalmente alineado. Los datos fluyen correctamente desde las fases del pipeline hasta la base de datos a través del PayloadBuilder, que realiza las transformaciones necesarias.

## Análisis Detallado por Componente

### 1. Función SQL `actualizar_articulo_procesado.sql`

La función espera los siguientes campos principales:
- `articulo_id` o `url` (para identificar el artículo)
- `resumen` 
- `categorias_asignadas` (array)
- `puntuacion_relevancia` (integer)
- `area_geografica` (opcional)
- Arrays de elementos extraídos:
  - `entidades_autonomas`
  - `hechos_extraidos`
  - `citas_textuales_extraidas`
  - `datos_cuantitativos_extraidos`
  - `relaciones_hechos`
  - `relaciones_entidades`
  - `contradicciones_detectadas`

### 2. Mapeo de Entidades (Fase 3)

**Schema del Pipeline:**
```json
{
  "id": 1,
  "nombre": "string",
  "alias": ["string"],
  "tipo": "PERSONA|ORGANIZACION|...",
  "descripcion": "string",
  "fecha_nacimiento": "YYYY-MM-DD|null",
  "fecha_disolucion": "YYYY-MM-DD|null"
}
```

**Mapeo en PayloadBuilder (líneas 420-432):**
- `id_entidad` → `id`
- `texto_entidad` → `nombre` 
- `tipo_entidad` → `tipo`
- `relevancia_entidad` → `relevancia` (convierte de 0-1 float a 1-10 int)
- `metadata_entidad` → `metadata`

**SQL espera:**
- `nombre` ✅
- `tipo` ✅
- `descripcion` ✅
- `alias` (array) ✅
- `relevancia` (integer) ✅
- `metadata` (jsonb) ✅
- `id_temporal` ✅
- `id_entidad_normalizada` (opcional) ✅

### 3. Mapeo de Hechos (Fase 4)

**Schema del Pipeline:**
```json
{
  "id": 1,
  "contenido": "string",
  "fecha_inicio": "YYYY-MM-DD",
  "fecha_fin": "YYYY-MM-DD",
  "precision_temporal": "exacta|dia|...",
  "tipo_hecho": "SUCESO|ANUNCIO|...",
  "pais": ["string"],
  "region": ["string"],
  "ciudad": ["string"],
  "es_futuro": boolean,
  "estado_programacion": "programado|..."
}
```

**SQL espera:**
- `contenido` ✅
- `fecha_ocurrencia_inicio` ← `fecha_inicio` ✅
- `fecha_ocurrencia_fin` ← `fecha_fin` ✅
- `precision_temporal` ✅ (con default 'desconocido')
- `tipo_hecho` ✅ (con default 'SUCESO')
- `importancia` ← no viene del pipeline, usa default 5 ⚠️
- `pais`, `region`, `ciudad` se mapean desde `metadata` ✅
- `id_temporal` ✅

### 4. Mapeo de Datos Cuantitativos (Fase 5)

**Schema del Pipeline:**
```json
{
  "id": 1,
  "hecho_id": 0,
  "indicador": "string",
  "categoria": "económico|demográfico|...",
  "valor": number,
  "unidad": "string",
  "ambito_geografico": ["string"],
  "periodo_inicio": "YYYY-MM-DD",
  "periodo_fin": "YYYY-MM-DD",
  "tendencia": "aumento|disminución|estable|null"
}
```

**Mapeo en PayloadBuilder (líneas 444-473):**
- `hecho_principal_relacionado_id_temporal` → `id_temporal_hecho`
- `descripcion_dato` → `indicador`
- `valor_dato` → `valor_numerico`
- `unidad_dato` → `unidad`

**SQL espera:**
- `hecho_id` ← se resuelve del mapeo de IDs temporales ✅
- `indicador` ✅
- `categoria` ✅
- `valor_numerico` ✅
- `unidad` ✅
- `ambito_geografico` (array) ✅
- `periodo_referencia_inicio/fin` ✅
- `tendencia` ✅

### 5. Mapeo de Citas Textuales (Fase 6)

**Schema del Pipeline:**
```json
{
  "id": 1,
  "cita": "string",
  "entidad_id": 0,
  "hecho_id": 0,
  "fecha": "YYYY-MM-DD",
  "contexto": "string",
  "relevancia": 1-5
}
```

**SQL espera:**
- `cita` ✅
- `entidad_emisora_id` ← se resuelve del mapeo de IDs temporales ✅
- `hecho_contexto_id` ← se resuelve del mapeo de IDs temporales ✅
- `fecha_cita` ✅
- `contexto` ✅
- `relevancia` ✅

### 6. Mapeo de Relaciones (Fase 7)

**Relaciones Hecho-Entidad:**
```json
{
  "hecho_id": 0,
  "entidad_id": 0,
  "tipo_relacion": "protagonista|mencionado|...",
  "relevancia_en_hecho": 1-10
}
```

**Relaciones Entidad-Entidad:**
```json
{
  "entidad_origen_id": 0,
  "entidad_destino_id": 0,
  "tipo_relacion": "miembro_de|subsidiaria_de|...",
  "descripcion": "string",
  "fuerza_relacion": 1-10
}
```

**SQL procesa correctamente ambos tipos** ✅

## Discrepancias Encontradas

### 1. Campo `importancia` en Hechos
- **Problema:** El pipeline no genera este campo
- **Solución actual:** SQL usa default 5
- **Recomendación:** Agregar lógica de cálculo de importancia en fase 4

### 2. Conversión de Relevancia en Entidades
- **Problema:** Pipeline genera float 0-1, SQL espera integer 1-10
- **Solución actual:** PayloadBuilder convierte multiplicando por 10
- **Estado:** ✅ Resuelto

### 3. Campos de Metadata en Hechos
- **Problema:** Pipeline genera `pais`, `region`, `ciudad` como campos directos
- **Solución actual:** SQL los extrae de `metadata`
- **Recomendación:** Estandarizar ubicación de campos geográficos

### 4. IDs Temporales
- **Observación:** Sistema robusto de mapeo de IDs temporales
- **Estado:** ✅ Funciona correctamente

## Validaciones Implementadas

El PayloadBuilder implementa validaciones exhaustivas:

1. **Integridad Referencial** (líneas 113-167)
   - Verifica que todos los IDs temporales referenciados existan
   - Valida relaciones entre entidades y hechos

2. **Tipos de Datos** (líneas 169-236)
   - Valida fechas en formato ISO
   - Verifica arrays y tipos numéricos
   - Valida URIs de Wikidata

3. **Checksum** (líneas 42-54)
   - Genera MD5 para verificar integridad del payload

## Conclusiones

1. **Alineación General:** ✅ El sistema está bien alineado
2. **Transformaciones:** PayloadBuilder maneja correctamente las diferencias
3. **Validaciones:** Sistema robusto de validación previene errores
4. **Áreas de Mejora:** 
   - Agregar campo `importancia` al pipeline
   - Estandarizar ubicación de campos geográficos
   - Considerar generar `id_entidad_normalizada` en fase 7

## Recomendaciones

1. **Corto Plazo:**
   - Documentar las transformaciones del PayloadBuilder
   - Agregar logs más detallados en el mapeo

2. **Mediano Plazo:**
   - Implementar cálculo de `importancia` en hechos
   - Revisar necesidad de todos los campos opcionales

3. **Largo Plazo:**
   - Considerar unificar schemas entre pipeline y base de datos
   - Implementar validación de schemas con JSON Schema

## Archivos Analizados

1. `/BaseDeDatos_SUPABASE/funciones/actualizar_articulo_procesado.sql`
2. `/src/module_pipeline/src/services/payload_builder.py`
3. `/src/module_pipeline/src/pipeline/fase_*.py` (fases 1-7)
4. `/src/module_pipeline/prompts/*.md` (prompts de cada fase)
5. `/JSON_SCHEMAS_ANALYSIS.md` (análisis previo generado)