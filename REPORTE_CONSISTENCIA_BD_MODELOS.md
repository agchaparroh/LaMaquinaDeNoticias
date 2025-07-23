# Reporte de Consistencia: Base de Datos vs Modelos Pydantic

Fecha de análisis: 2025-01-23

## Tabla: entidades

### Campos BD → Modelo (EntidadBase/EntidadProcesada):
- `id` → `id_entidad` ❌ (BD: bigint, Modelo: int secuencial)
- `nombre` → `nombre` ✅
- `tipo` → `tipo` ✅
- `descripcion` → `descripcion` ✅
- `alias` → `alias` ✅
- `relevancia` → `relevancia` ✅
- `metadata` → `metadata_entidad` ⚠️ (BD: jsonb genérico, Modelo: MetadatosEntidad estructurado)
- `fusionada_en_id` → ❌ (Campo no existe en modelo)

### Campos en Modelo no presentes en BD:
- `offset_inicio_entidad` ⚠️
- `offset_fin_entidad` ⚠️
- `id_fragmento_origen` ⚠️ (solo en EntidadProcesada)
- `id_entidad_normalizada` ⚠️ (solo en EntidadProcesada)
- `nombre_entidad_normalizada` ⚠️ (solo en EntidadProcesada)
- `uri_wikidata` ⚠️ (solo en EntidadProcesada)
- `similitud_normalizacion` ⚠️ (solo en EntidadProcesada)
- `prompt_utilizado_normalizacion` ⚠️ (solo en EntidadProcesada)
- `fecha_creacion` ⚠️ (heredado de PipelineBaseModel)
- `fecha_actualizacion` ⚠️ (heredado de PipelineBaseModel)

### Observaciones:
- El modelo usa IDs secuenciales (int) mientras que la BD usa bigint
- El modelo tiene campos adicionales para tracking del procesamiento
- La BD tiene `fusionada_en_id` para manejo de entidades duplicadas que no está en el modelo

---

## Tabla: hechos

### Campos BD → Modelo (HechoBase/HechoProcesado):
- `id` → `id_hecho` ❌ (BD: bigint, Modelo: int secuencial)
- `contenido` → `contenido` ✅
- `fecha_ocurrencia` → `fecha_inicio`/`fecha_fin` ❌ (BD: tstzrange, Modelo: dos strings separados)
- `precision_temporal` → `precision_temporal` ✅
- `importancia` → `importancia` ✅
- `tipo_hecho` → `tipo_hecho` ✅
- `pais` → `pais` ✅
- `region` → `region` ✅
- `ciudad` → `ciudad` ✅
- `evaluacion_editorial` → ❌ (Campo no existe en modelo)
- `consenso_fuentes` → ❌ (Campo no existe en modelo)
- `estado_programacion` → En `metadata_hecho.estado_programacion` ⚠️
- `confiabilidad_programacion` → ❌ (Campo no existe en modelo)
- `etiquetas` → `etiquetas` ✅
- `fecha_ingreso` → ❌ (Campo no existe en modelo)
- `documento_id` → ❌ (Campo no existe en modelo)
- `fragmento_id` → `id_fragmento_origen` ⚠️ (solo en HechoProcesado)

### Campos en Modelo no presentes en BD:
- `fecha_inicio` ⚠️ (parte de fecha_ocurrencia en BD)
- `fecha_fin` ⚠️ (parte de fecha_ocurrencia en BD)
- `metadata_hecho` ⚠️ (estructura específica vs jsonb genérico)
- `id_articulo_fuente` ⚠️ (solo en HechoProcesado)
- `vinculado_a_entidades` ⚠️ (solo en HechoProcesado)
- `prompt_utilizado` ⚠️ (solo en HechoProcesado)
- `respuesta_llm_bruta` ⚠️ (solo en HechoProcesado)
- `fecha_creacion` ⚠️ (heredado de PipelineBaseModel)
- `fecha_actualizacion` ⚠️ (heredado de PipelineBaseModel)

### Constraints:
- CHECK precision_temporal ✅ (valores coinciden)
- CHECK importancia 1-10 ✅
- CHECK tipo_hecho ✅ (valores coinciden)

### Observaciones:
- **CRÍTICO**: La BD usa `tstzrange` para fechas mientras el modelo usa dos campos string separados
- Faltan campos importantes de la BD en el modelo: evaluación editorial, consenso de fuentes
- El modelo tiene campos adicionales para tracking del procesamiento LLM

---

## Tabla: citas_textuales

### Campos BD → Modelo (CitaTextual):
- `id` → `id_cita` ❌ (BD: bigint, Modelo: int secuencial)
- `cita` → `cita` ✅
- `entidad_emisora_id` → `entidad_emisora_id` ⚠️ (BD: bigint FK, Modelo: int opcional)
- `articulo_id` → ❌ (Campo no existe en modelo)
- `documento_id` → ❌ (Campo no existe en modelo)
- `fragmento_id` → `id_fragmento_origen` ⚠️
- `hecho_contexto_id` → `hecho_contexto_id` ⚠️ (BD: bigint, Modelo: int opcional)
- `fecha_cita` → `fecha_cita` ⚠️ (BD: timestamptz, Modelo: string)
- `contexto` → `contexto_cita` ⚠️ (nombres diferentes)
- `relevancia` → En `metadata_cita.relevancia` ⚠️
- `fecha_ingreso` → ❌ (Campo no existe en modelo)

### Campos en Modelo no presentes en BD:
- `persona_citada` ⚠️
- `offset_inicio_cita` ⚠️
- `offset_fin_cita` ⚠️
- `metadata_cita` ⚠️ (estructura específica)
- `fecha_creacion` ⚠️ (heredado de PipelineBaseModel)
- `fecha_actualizacion` ⚠️ (heredado de PipelineBaseModel)

### Constraints:
- CHECK relevancia 1-5 ⚠️ (En BD es directo, en modelo está en metadata)

### Observaciones:
- El modelo no tiene referencias a `articulo_id` y `documento_id` de la BD
- La relevancia está en diferente ubicación (campo directo vs metadata)
- Tipos de fecha incompatibles (timestamptz vs string)

---

## Tabla: datos_cuantitativos

### Campos BD → Modelo (DatosCuantitativos):
- `id` → `id_dato_cuantitativo` ❌ (BD: bigint, Modelo: int secuencial)
- `hecho_id` → `hecho_id` ⚠️ (BD: bigint, Modelo: int opcional)
- `articulo_id` → ❌ (Campo no existe en modelo)
- `documento_id` → ❌ (Campo no existe en modelo)
- `fragmento_id` → `id_fragmento_origen` ⚠️
- `indicador` → `indicador` ✅
- `categoria` → `categoria` ✅
- `valor_numerico` → `valor_numerico` ⚠️ (BD: numeric, Modelo: float)
- `unidad` → `unidad` ✅
- `ambito_geografico` → `ambito_geografico` ✅
- `periodo_referencia_inicio` → `periodo_referencia_inicio` ⚠️ (BD: date, Modelo: string)
- `periodo_referencia_fin` → `periodo_referencia_fin` ⚠️ (BD: date, Modelo: string)
- `tipo_periodo` → `tipo_periodo` ✅
- `tendencia` → `tendencia` ✅
- `fecha_registro` → ❌ (Campo no existe en modelo)

### Campos en Modelo no presentes en BD:
- `offset_inicio_dato` ⚠️
- `offset_fin_dato` ⚠️
- `metadata_dato` ⚠️ (estructura específica)
- `fecha_creacion` ⚠️ (heredado de PipelineBaseModel)
- `fecha_actualizacion` ⚠️ (heredado de PipelineBaseModel)

### Constraints:
- CHECK categoria (valores del enum) ✅
- CHECK tipo_periodo (valores del enum) ✅
- CHECK tendencia (valores del enum) ✅

### Observaciones:
- El modelo no tiene referencias a `articulo_id` y `documento_id` de la BD
- Tipos de datos numéricos diferentes (numeric vs float)
- Tipos de fecha diferentes (date vs string con pattern)

---

## Resumen de Discrepancias Críticas

### 1. **IDs Incompatibles**
- BD usa `bigint` para todos los IDs
- Modelos usan `int` secuencial (optimización para LLM)
- Necesita conversión en fase de normalización

### 2. **Fechas de Hechos**
- BD: `fecha_ocurrencia` como `tstzrange` (rango de timestamps)
- Modelo: `fecha_inicio` y `fecha_fin` como strings separados
- **CRÍTICO**: Requiere transformación compleja

### 3. **Campos Faltantes en Modelos**
- `evaluacion_editorial` (hechos)
- `consenso_fuentes` (hechos)
- `confiabilidad_programacion` (hechos)
- `articulo_id`, `documento_id` (en citas y datos)
- `fecha_ingreso`, `fecha_registro`
- `fusionada_en_id` (entidades)

### 4. **Tipos de Datos Incompatibles**
- Fechas: `timestamptz`/`date` (BD) vs `string` (modelos)
- Números: `numeric` (BD) vs `float` (modelos)
- IDs: `bigint` (BD) vs `int` (modelos)

### 5. **Metadata**
- BD espera `jsonb` genérico
- Modelos tienen estructuras Pydantic específicas (MetadatosHecho, etc.)
- Requiere serialización apropiada

### Recomendaciones

1. **Actualizar fase de normalización** para manejar conversiones de tipos
2. **Agregar campos faltantes** a los modelos o documentar por qué se omiten
3. **Implementar conversión de rangos de fecha** tstzrange ↔ fecha_inicio/fecha_fin
4. **Validar que metadata estructurada** se serialice correctamente a jsonb
5. **Considerar agregar campos de auditoría** (fecha_ingreso, etc.) a los modelos