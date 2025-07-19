# Análisis Completo del Flujo de Entidades

## 1. FUENTE DE VERDAD: Tabla `entidades` en Supabase

```sql
Columnas de la tabla entidades:
- id (bigint, NOT NULL)
- nombre (varchar, NOT NULL)    ← Campo crítico
- tipo (varchar, NOT NULL)
- descripcion (text, NULL)
- alias (ARRAY, NULL)
- fecha_nacimiento (tstzrange, NULL)
- fecha_disolucion (tstzrange, NULL)
- wikidata_id (varchar, NULL)
- relevancia (integer, NOT NULL, default: 5)
- metadata (jsonb, NULL)
- embedding (vector, NULL)
- fusionada_en_id (bigint, NULL)
```

## 2. PROMPT DE EXTRACCIÓN (Entidades.md)

El prompt espera y genera:
```json
{
  "entidades": [
    {
      "id": 1,
      "nombre": "Nicolás Maduro",     ← Coincide con DB
      "alias": [],                    ← Coincide con DB
      "tipo": "PERSONA",              ← Coincide con DB
      "descripcion": "- presidente",  ← Coincide con DB
      "fecha_nacimiento": null,       ← Coincide con DB
      "fecha_disolucion": null        ← Coincide con DB
    }
  ]
}
```
**Estado**: ✅ CORRECTO - Nomenclatura coincide con base de datos

## 3. FASE 3 - EXTRACCIÓN (fase_3_entidades.py)

```python
# Líneas 268-275
entidad_procesada = EntidadProcesada(
    id_entidad=entidad.get("id", 0),
    texto_entidad=entidad.get("nombre", ""),  ← Lee "nombre" del prompt
    tipo_entidad=entidad.get("tipo", "DESCONOCIDO"),
    relevancia_entidad=0.8,
    id_fragmento_origen=id_fragmento,
    metadata_entidad=metadatos
)
```
**Estado**: ✅ CORRECTO - Lee "nombre" y lo guarda en "texto_entidad"

## 4. MODELO EntidadProcesada (procesamiento.py)

```python
class EntidadBase(PipelineBaseModel):
    id_entidad: int
    texto_entidad: str  ← Guarda el nombre aquí
    tipo_entidad: str
    relevancia_entidad: float
    metadata_entidad: MetadatosEntidad

class EntidadProcesada(EntidadBase):
    id_entidad_normalizada: Optional[str] = None
    nombre_entidad_normalizada: Optional[str] = None  ← Para nombre normalizado
    uri_wikidata: Optional[HttpUrl] = None
    similitud_normalizacion: Optional[float] = None
```
**Estado**: ✅ DISEÑO CORRECTO - Separa nombre original de normalizado

## 5. FASE 7A - NORMALIZACIÓN (fase_7_normalizacion.py)

```python
# Líneas 385-393
resultado = normalizador.normalizar_entidad(
    nombre_entidad=entidad.texto_entidad,  ← Usa texto_entidad
    tipo_entidad=entidad.tipo_entidad
)
# Si encuentra normalización:
entidad.nombre_entidad_normalizada = resultado["nombre_normalizado"]
```
**Estado**: ✅ CORRECTO - Preserva nombre original y añade normalizado

## 6. PIPELINE COORDINATOR (pipeline_coordinator.py)

```python
# Líneas 654-667
entidades_data.append({
    "id": str(entidad.id_entidad),
    "nombre": entidad.nombre_entidad_normalizada or entidad.texto_entidad,  ← ERROR
    "tipo": entidad.tipo_entidad,  ← ERROR
    "descripcion": f"Entidad extraída...",  ← ERROR
    "relevancia_entidad_articulo": int(entidad.relevancia_entidad * 10),
    "metadata_entidad": {...}
})
```
**Estado**: ❌ ERROR - No coincide con RPC

## 7. MODELO EntidadAutonomaItem (persistencia.py)

```python
class EntidadAutonomaItem(PersistenciaBaseModel):
    id: str
    nombre: str  ← Espera "nombre" sin sufijo
    tipo: str    ← Espera "tipo" sin sufijo
    descripcion: Optional[str]
    alias: Optional[List[str]]
    # Campos adicionales...
```
**Estado**: ⚠️ INCONSISTENTE - Modelo no coincide con RPC

## 8. RPC actualizar_articulo_procesado.sql

```sql
INSERT INTO entidades (nombre, tipo, descripcion, alias, relevancia, metadata)
VALUES (
    v_entidad->>'nombre_entidad',      ← Busca con sufijo
    v_entidad->>'tipo_entidad',        ← Busca con sufijo
    v_entidad->>'descripcion_entidad', ← Busca con sufijo
    ARRAY(SELECT jsonb_array_elements_text(v_entidad->'alias')),
    COALESCE((v_entidad->>'relevancia_entidad')::INTEGER, 5),
    v_entidad->'metadata_entidad'
)
```
**Estado**: ❌ ERROR - Espera campos con sufijo "_entidad"

## DIAGNÓSTICO FINAL

### Inconsistencias Identificadas:

1. **Base de Datos y Prompt**: ✅ Consistentes (usan "nombre", "tipo", "descripcion")
2. **Fases 3 y 7**: ✅ Correctas (procesan datos internamente)
3. **Pipeline Coordinator**: ❌ Genera campos SIN sufijo
4. **Modelo EntidadAutonomaItem**: ⚠️ Espera campos SIN sufijo
5. **RPC SQL**: ❌ Espera campos CON sufijo "_entidad"

### El Problema:
Hay una **desconexión entre la representación interna y la persistencia**:
- Internamente se usa `texto_entidad` (correcto para procesamiento)
- Al persistir, la RPC espera `nombre_entidad` (inconsistente con DB)

### Solución Requerida:
La RPC debería esperar los mismos campos que la base de datos:
- `nombre` (no `nombre_entidad`)
- `tipo` (no `tipo_entidad`)
- `descripcion` (no `descripcion_entidad`)

Esto mantendría consistencia absoluta con la fuente de verdad (tabla entidades).