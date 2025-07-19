# Análisis de Uso de RPCs - Conflicto entre Scraper y Pipeline

## Resumen Ejecutivo

**Hallazgo Principal**: El scraper NO usa la RPC `insertar_articulo_completo`. El conflicto ocurre porque ambos módulos intentan insertar/actualizar el mismo registro pero usando métodos diferentes:

- **Scraper**: Usa `upsert` directo a la tabla con `on_conflict='url'`
- **Pipeline**: Usa RPC `insertar_articulo_completo` que hace INSERT (no UPDATE)

## 1. Uso en el Módulo Scraper

### Método de Inserción
El scraper usa el método `upsert_articulo` en `supabase_client.py`:

```python
# src/module_scraper/scraper_core/utils/supabase_client.py
def upsert_articulo(self, articulo_item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # ...
    response = self.client.table(self.articulos_table_name).upsert(
        db_articulo_data_cleaned, 
        on_conflict='url'
    ).execute()
```

### Características:
- **NO usa RPC**: Usa operación `upsert` directa de Supabase
- **Conflict Resolution**: `on_conflict='url'` - actualiza si existe la URL
- **Estado inicial**: Establece `estado_procesamiento = 'pendiente'`
- **Campos que inserta**: Todos los campos básicos del artículo (metadata del scraping)

### Flujo:
1. `SupabaseStoragePipeline._upsert_articulo_with_retry()`
2. `SupabaseClient.upsert_articulo()`
3. `supabase.table('articulos').upsert(data, on_conflict='url')`

## 2. Uso en el Módulo Pipeline

### Método de Inserción
El pipeline usa la RPC `insertar_articulo_completo` en `supabase_service.py`:

```python
# src/module_pipeline/src/services/supabase_service.py
def insertar_articulo_completo(self, payload: Union[Dict[str, Any], BaseModel]) -> Optional[Dict[str, Any]]:
    # ...
    response = self.client.rpc(
        'insertar_articulo_completo',
        {'datos_json': payload_dict}
    ).execute()
```

### Características:
- **Usa RPC**: Función SQL compleja para inserción atómica
- **NO maneja conflictos**: La RPC hace INSERT directo, no UPDATE
- **Estado final**: Establece `estado_procesamiento = 'completado'`
- **Inserción compleja**: Inserta artículo + elementos extraídos + relaciones

### Análisis de la RPC:
```sql
-- BaseDeDatos_SUPABASE/documentación/Funciones-triggers.sql
CREATE OR REPLACE FUNCTION insertar_articulo_completo(datos_json JSONB)
-- ...
INSERT INTO articulos (
    url, storage_path, medio, -- etc...
    estado_procesamiento -- Se establece a 'completado'
)
SELECT
    j->'articulo_metadata'->>'url',
    -- ...
    'completado', -- estado_procesamiento fijo
```

**Problema identificado**: La RPC hace INSERT sin verificar si el registro ya existe.

## 3. RPCs Alternativas Existentes

### Búsqueda realizada:
- `actualizar_articulo_procesado` - NO EXISTE
- `update_articulo_procesado` - NO EXISTE  
- `actualizar_estado_articulo` - NO EXISTE

### RPCs encontradas:
- `insertar_articulo_completo` - Para artículos nuevos (INSERT only)
- `insertar_fragmento_completo` - Para fragmentos (INSERT only)
- `buscar_entidad_similar` - Para normalización de entidades
- `exec_sql` - RPC genérica (solo en tests)

## 4. Análisis del Conflicto

### Escenario del Error:
1. **Scraper**: Inserta artículo con `estado_procesamiento = 'pendiente'`
2. **Pipeline**: Intenta insertar el mismo artículo con `estado_procesamiento = 'completado'`
3. **Error**: Violación de constraint UNIQUE en `url`

### Por qué ocurre:
- El scraper usa UPSERT (INSERT ON CONFLICT UPDATE)
- El pipeline usa INSERT directo vía RPC
- La RPC no contempla que el artículo ya exista

## 5. Recomendaciones

### Opción 1: Modificar la RPC Existente (RECOMENDADA)
Actualizar `insertar_articulo_completo` para manejar conflictos:

```sql
-- En lugar de INSERT directo:
INSERT INTO articulos (...) 
VALUES (...)
ON CONFLICT (url) DO UPDATE SET
    estado_procesamiento = 'completado',
    fecha_procesamiento = now(),
    -- Actualizar solo campos del procesamiento
    resumen = EXCLUDED.resumen,
    categorias_asignadas = EXCLUDED.categorias_asignadas,
    puntuacion_relevancia = EXCLUDED.puntuacion_relevancia
RETURNING id INTO v_articulo_id;
```

**Ventajas**:
- Mantiene la atomicidad de la transacción
- No requiere cambios en el código del pipeline
- Resuelve el conflicto de manera elegante

### Opción 2: Crear Nueva RPC para Actualización
Crear `actualizar_articulo_procesado` específica para el pipeline:

```sql
CREATE OR REPLACE FUNCTION actualizar_articulo_procesado(datos_json JSONB)
-- Buscar el artículo existente por URL
-- Actualizar campos de procesamiento
-- Insertar elementos extraídos
```

**Desventajas**:
- Duplicación de lógica
- Requiere cambios en el pipeline para detectar si debe insertar o actualizar

### Opción 3: Cambiar el Flujo (NO RECOMENDADA)
Hacer que el scraper no inserte en `articulos`, solo en una tabla temporal.

**Desventajas**:
- Cambio arquitectónico mayor
- Afecta todo el sistema existente

## 6. Conclusión

El conflicto se debe a que:
1. El scraper hace UPSERT (actualiza si existe)
2. El pipeline hace INSERT (falla si existe)
3. Ambos operan sobre la misma tabla con la misma clave única (URL)

**Solución recomendada**: Modificar la RPC `insertar_articulo_completo` para usar `ON CONFLICT DO UPDATE` en lugar de fallar cuando el artículo ya existe.

Esto permitirá que:
- El scraper siga insertando artículos nuevos
- El pipeline actualice esos artículos cuando los procese
- No haya conflictos de constraint UNIQUE
- Se mantenga la integridad de datos