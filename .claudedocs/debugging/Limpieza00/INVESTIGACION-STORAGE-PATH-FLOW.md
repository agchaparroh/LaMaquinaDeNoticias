# Investigación del Flujo de storage_path en el Sistema

**Fecha:** 2025-07-19
**Investigador:** Claude
**Objetivo:** Entender el flujo completo de `storage_path` y confirmar/refutar la hipótesis de dos caminos paralelos

## Resumen Ejecutivo

La investigación confirma la hipótesis del usuario: **existe un flujo de dos caminos paralelos** en el sistema:

1. **Camino Scraper → Supabase:** El scraper inserta directamente los artículos en la base de datos con `storage_path` poblado
2. **Camino Scraper → Connector → Pipeline:** El scraper exporta archivos JSON para procesamiento posterior

El RPC `insertar_articulo_completo` está esperando un `storage_path` que **ya existe** en la base de datos, haciendo esta validación redundante e innecesaria en el contexto del pipeline.

## Hallazgos Detallados

### 1. Flujo del Scraper (Confirmado)

El scraper tiene **dos pipelines de salida paralelos**:

#### Pipeline 1: SupabaseStoragePipeline (Prioridad 400)
```python
# En scraper_core/pipelines/storage.py
# Línea 217-224: Genera y asigna storage_path
storage_file_path = f"{medio_slug}/{fecha_pub_path_part}/{file_name}"
adapter['storage_path'] = storage_file_path

# Línea 251: Hace upsert del artículo CON storage_path
upserted_data = self._upsert_articulo_with_retry(article_data_for_db)
```

**Evidencia clave:** El método `upsert_articulo` en `supabase_client.py` (línea 174) incluye `storage_path` en el insert/update:
```python
db_articulo_data = {
    "url": articulo_item_data.get('url'),
    "storage_path": articulo_item_data.get('storage_path'),  # ← SE INCLUYE AQUÍ
    # ... otros campos
}
```

#### Pipeline 2: JsonWriterPipeline (Prioridad 900)
- Exporta artículos a archivos `.json.gz` para el connector
- Se ejecuta DESPUÉS del SupabaseStoragePipeline
- Los artículos exportados YA tienen un `articulo_id` asignado por la BD

### 2. Flujo del Connector

El connector:
1. Lee archivos `.json.gz` del directorio de salida del scraper
2. Valida los artículos usando el modelo `ArticuloInItem`
3. Envía los artículos al pipeline vía API REST

**Observación importante:** El modelo `ArticuloInItem` en el connector incluye `storage_path` como campo opcional (línea 22 en `models.py`).

### 3. Flujo del Pipeline

El pipeline:
1. Recibe artículos del connector
2. En `payload_builder.py` (línea 306), **establece storage_path como None**:
   ```python
   metadatos_articulo = {
       "url": articulo_model.url,
       "storage_path": None,  # Se puede añadir si es necesario
       "fuente_original": None,
       # ...
   }
   ```
3. Intenta persistir en Supabase usando el RPC `insertar_articulo_completo`

### 4. El RPC y su Validación

El RPC `insertar_articulo_completo` (línea 195-201 en `Funciones-triggers.sql`):
```sql
-- Validación del formato de storage_path
IF NOT (datos_json->'articulo_metadata'->>'storage_path' ~ '^[^/]+/\d{4}/\d{2}/\d{2}/[^/]+\.(html|txt)\.gz$') THEN
    RETURN jsonb_build_object(
        'status', 'error',
        'mensaje', 'Formato de storage_path inválido...',
        'codigo_sql', 'CHECK_VIOLATION'
    );
END IF;
```

**El problema:** Esta validación asume que el pipeline está creando un NUEVO artículo, pero en realidad está ACTUALIZANDO uno existente.

### 5. Schema de la Base de Datos

En `Arquitectura de la base de datos.sql` (línea 135):
```sql
CREATE TABLE articulos (
    id BIGSERIAL PRIMARY KEY,
    url TEXT UNIQUE,
    storage_path TEXT NOT NULL UNIQUE,  -- ← NOT NULL y UNIQUE
    -- ...
```

**Confirmación:** `storage_path` es un campo obligatorio y único en la tabla.

## Evidencia del Flujo de Dos Caminos

### Evidencia 1: Orden de Ejecución de Pipelines
```python
ITEM_PIPELINES = {
    'scraper_core.pipelines.converter.ItemConverterPipeline': 100,
    'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
    'scraper_core.pipelines.validation.DataValidationPipeline': 300,
    'scraper_core.pipelines.SupabaseStoragePipeline': 400,  # ← INSERTA EN BD
    'scraper_core.pipelines.json_writer.JsonWriterPipeline': 900,  # ← EXPORTA PARA CONNECTOR
}
```

### Evidencia 2: Propagación del ID
En `storage.py` (líneas 256-267):
```python
if articulo_id:
    adapter['articulo_id'] = articulo_id
    logger.info(f"Article ID {articulo_id} added to item for propagation through the pipeline")
```

El ID del artículo se propaga al JSON exportado, confirmando que el artículo YA EXISTE en la BD.

### Evidencia 3: Estado del Artículo
En el informe de flujo (`informe_flujo_completo_2025-07-16.md`):
- Los artículos se guardan correctamente en Supabase desde el scraper
- El error ocurre cuando el pipeline intenta procesarlos posteriormente

## Conclusión

La hipótesis del usuario es **CORRECTA**:

1. **El artículo YA EXISTE en la base de datos** cuando el pipeline lo procesa
2. **El storage_path YA ESTÁ POBLADO** desde el scraper
3. **El RPC está validando innecesariamente** un campo que no debería modificar
4. **El pipeline establece storage_path como None** porque no lo necesita

## Recomendaciones

### Opción 1: Modificar el RPC (Recomendada)
Hacer que el RPC sea más inteligente:
- Si el artículo ya existe (basado en URL), no validar storage_path
- Solo validar storage_path si es una inserción nueva

### Opción 2: Modificar el Pipeline
- Incluir el storage_path del artículo existente en el payload
- Requeriría consultar el artículo existente antes de procesar

### Opción 3: Crear un RPC Separado
- `insertar_articulo_completo` para nuevos artículos (desde scraper)
- `actualizar_articulo_procesado` para artículos existentes (desde pipeline)

## Arquitectura Confirmada

```
┌─────────────┐
│   SCRAPER   │
└──────┬──────┘
       │
    ┌──┴──┐
    │     │
    ▼     ▼
┌─────────────────┐    ┌────────────────┐
│ SUPABASE STORAGE│    │ JSON EXPORT    │
│   PIPELINE      │    │   PIPELINE     │
│ (Prioridad 400) │    │ (Prioridad 900)│
└────────┬────────┘    └───────┬────────┘
         │                     │
         ▼                     ▼
┌─────────────────┐    ┌────────────────┐
│   SUPABASE DB   │    │ JSON FILES     │
│ (articulo con   │    │ (.json.gz)     │
│  storage_path)  │    └───────┬────────┘
└─────────────────┘            │
                               ▼
                       ┌────────────────┐
                       │   CONNECTOR    │
                       └───────┬────────┘
                               │
                               ▼
                       ┌────────────────┐
                       │   PIPELINE     │
                       │ (7 fases)      │
                       └───────┬────────┘
                               │
                               ▼
                       ┌────────────────┐
                       │ RPC insertar_  │
                       │articulo_completo│
                       │  (FALLA aquí)  │
                       └────────────────┘
```

El flujo muestra claramente los dos caminos paralelos y dónde ocurre el problema.