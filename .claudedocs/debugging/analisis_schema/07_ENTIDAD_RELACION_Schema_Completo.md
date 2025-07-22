# **ANÁLISIS COMPLETO: SCHEMA ENTIDAD_RELACION (Relaciones entre Entidades)**

## **RESUMEN EJECUTIVO**

Schema de relaciones entidad-entidad mapeado completamente. Similar a hecho_relacionado, se identifica que aunque la Fase 7B.1 detecta estas relaciones, el `pipeline_coordinator.py` tiene un TODO y NO las extrae para pasarlas al PayloadBuilder.

---

## **1. MODELOS PYDANTIC - ENTRADA**

### **1.1. RelacionEntidadesItem (`src/module_pipeline/src/models/persistencia.py`)**

```json
{
  "entidad_origen_id_temporal": "ENT-1",             // str - ID temporal entidad origen
  "entidad_destino_id_temporal": "ENT-2",            // str - ID temporal entidad destino
  "tipo_relacion": "empleado_de",                    // str - Tipo de relación
  "descripcion_relacion": "Director ejecutivo",      // Optional[str] - Descripción
  "contexto_relacion": "Desde 2020",                 // Optional[str] - Contexto
  "fecha_inicio_relacion": "2020-01-15T00:00:00Z",   // Optional[str] - ISO 8601
  "fecha_fin_relacion": null,                        // Optional[str] - ISO 8601
  "fuerza_relacion": 9                               // Optional[int] 1-10
}
```

**Tipos de relación en modelo (ejemplos):**
- `empleado_de`
- `subsidiaria_de`
- `aliado_con`

---

## **2. PROMPTS LLM - SCHEMA ESPERADO**

### **2.1. Prompt Principal (`prompts/7B.1_Relaciones-Estructurales.md`)**

```json
{
  "hecho_entidad": [                                 // Relaciones hecho-entidad
    // ... analizado en documento anterior ...
  ],
  "entidad_relacion": [
    {
      "entidad_origen_id": 1,                        // int - ID secuencial entidad origen
      "entidad_destino_id": 2,                       // int - ID secuencial entidad destino
      "tipo_relacion": "miembro_de",                 // str - enum específico
      "descripcion": "Director ejecutivo",           // str - Descripción
      "fecha_inicio": null,                          // str YYYY-MM-DD o null
      "fecha_fin": null,                             // str YYYY-MM-DD o null
      "fuerza_relacion": 7                           // int - Fuerza 1-10
    }
  ]
}
```

**Tipos de relación permitidos exactos:**
- `miembro_de`
- `subsidiaria_de`
- `aliado_con`
- `opositor_a`
- `sucesor_de`
- `predecesor_de`
- `casado_con`
- `familiar_de`
- `empleado_de`

---

## **3. FASE 7B.1 - DETECCIÓN DE RELACIONES ESTRUCTURALES (`src/pipeline/fase_7_normalizacion.py`)**

### **3.1. Input Schema**
```json
{
  "entidades_normalizadas": "Array de EntidadProcesada con normalización",
  "hechos_normalizados": "Array de HechoProcesado con normalización"
}
```

### **3.2. Output Schema**
```json
{
  "relaciones_completas": {
    "relaciones_estructurales": {
      "hecho_entidad": [...],
      "entidad_relacion": [                          // ✅ Relaciones detectadas por LLM
        {
          "entidad_origen_id": 1,
          "entidad_destino_id": 2,
          "tipo_relacion": "empleado_de",
          "descripcion": "Director ejecutivo",
          "fecha_inicio": "2020-01-15",
          "fecha_fin": null,
          "fuerza_relacion": 9
        }
      ]
    },
    "relaciones_temporales": {
      "hecho_relacionado": [...],
      "contradicciones": [...]
    }
  }
}
```

### **3.3. Almacenamiento en ResultadoFase4Normalizacion**
```json
{
  "metadata_normalizacion": {
    "relaciones_completas": {
      "relaciones_estructurales": {
        "entidad_relacion": [...]                    // ✅ Aquí se guardan
      }
    }
  }
}
```

---

## **4. PIPELINE COORDINATOR - EXTRACCIÓN (NO IMPLEMENTADA)**

### **4.1. Código Actual (`src/pipeline/pipeline_coordinator.py` líneas 852-854)**
```python
# ❌ TODO NO IMPLEMENTADO
relaciones_hechos=None,  # TODO: Implementar cuando estén disponibles
relaciones_entidades=None,  # TODO: Implementar cuando estén disponibles
contradicciones_detectadas=None  # TODO: Implementar cuando estén disponibles
```

### **4.2. Código que DEBERÍA existir**
```python
# CÓDIGO FALTANTE - Extraer relaciones del resultado_fase7
if resultado_fase7.metadata_normalizacion:
    relaciones = resultado_fase7.metadata_normalizacion.get("relaciones_completas", {})
    
    # Extraer relaciones estructurales
    relaciones_estructurales = relaciones.get("relaciones_estructurales", {})
    relaciones_entidades = relaciones_estructurales.get("entidad_relacion", [])
```

---

## **5. PAYLOADBUILDER - CONVERSIÓN (`src/services/payload_builder.py`)**

### **5.1. Input Schema (si se implementara)**
```json
{
  "relaciones_entidades_data": [
    {
      "entidad_origen_id": 1,                        // int - ID secuencial
      "entidad_destino_id": 2,                       // int - ID secuencial
      "tipo_relacion": "empleado_de",
      "descripcion": "Director ejecutivo",
      "fecha_inicio": "2020-01-15",
      "fecha_fin": null,
      "fuerza_relacion": 9
    }
  ]
}
```

### **5.2. Función de Conversión (línea 437)**
```python
def construir_payload_articulo_from_model():
    if relaciones_entidades_data is not None:
        payload_data["relaciones_entidades"] = [
            RelacionEntidadesItem(**item) for item in relaciones_entidades_data
        ]
```

### **5.3. Validación de Integridad (necesaria)**
```python
def validar_integridad_referencial_entidades():
    """Valida que todos los IDs temporales en relaciones existan"""
    ids_entidades_validos = {e["id"] for e in payload_data.get("entidades_autonomas", [])}
    
    for relacion in payload_data.get("relaciones_entidades", []):
        if relacion.entidad_origen_id_temporal not in ids_entidades_validos:
            raise ValueError(f"Relación referencia entidad origen inexistente: {relacion.entidad_origen_id_temporal}")
        if relacion.entidad_destino_id_temporal not in ids_entidades_validos:
            raise ValueError(f"Relación referencia entidad destino inexistente: {relacion.entidad_destino_id_temporal}")
```

### **5.4. Transformación de Campos Necesaria**
```python
# IDs secuenciales → IDs temporales
entidad_origen_id (int)        → entidad_origen_id_temporal (str)
entidad_destino_id (int)       → entidad_destino_id_temporal (str)
tipo_relacion                  → tipo_relacion
descripcion                    → descripcion_relacion
fecha_inicio                   → fecha_inicio_relacion (ISO 8601)
fecha_fin                      → fecha_fin_relacion (ISO 8601)
fuerza_relacion                → fuerza_relacion
```

---

## **6. RPC SUPABASE - PERSISTENCIA (`actualizar_articulo_procesado.sql`)**

### **6.1. Input Schema Esperado**
```json
{
  "relaciones_entidades": [
    {
      "id_entidad_origen": "ENT-1",                  // ❌ RPC busca id_entidad_origen
      "id_entidad_destino": "ENT-2",                 // ❌ RPC busca id_entidad_destino
      "tipo_relacion": "empleado_de",                // ✅ RPC busca tipo_relacion
      "descripcion_relacion": "Director ejecutivo",  // ✅ RPC busca descripcion_relacion
      "fuerza_relacion": 9                           // ✅ RPC busca fuerza_relacion
    }
  ]
}
```

### **6.2. Procesamiento de Relaciones (líneas 393-428)**
```sql
-- Procesar relaciones entidad-entidad
IF datos_json ? 'relaciones_entidades' THEN
    FOR v_relacion IN SELECT * FROM jsonb_array_elements(datos_json->'relaciones_entidades')
    LOOP
        DECLARE
            v_entidad_origen_id BIGINT;
            v_entidad_destino_id BIGINT;
        BEGIN
            -- Obtener IDs reales
            v_entidad_origen_id := (temp_entidad_id_map->>(v_relacion->>'id_entidad_origen'))::BIGINT;  -- ❌ Busca id_entidad_origen
            v_entidad_destino_id := (temp_entidad_id_map->>(v_relacion->>'id_entidad_destino'))::BIGINT; -- ❌ Busca id_entidad_destino
            
            IF v_entidad_origen_id IS NOT NULL AND v_entidad_destino_id IS NOT NULL 
               AND v_entidad_origen_id <> v_entidad_destino_id THEN
                -- Insertar relación
                INSERT INTO entidad_relacion (
                    entidad_origen_id,
                    entidad_destino_id,
                    tipo_relacion,
                    descripcion,                     -- ❌ Campo 'descripcion' no 'descripcion_relacion'
                    fuerza_relacion
                )
                VALUES (
                    v_entidad_origen_id,
                    v_entidad_destino_id,
                    v_relacion->>'tipo_relacion',                             -- ✅ Busca tipo_relacion
                    v_relacion->>'descripcion_relacion',                     -- ✅ Busca descripcion_relacion
                    COALESCE((v_relacion->>'fuerza_relacion')::INTEGER, 5)   -- ✅ Busca fuerza_relacion
                )
                ON CONFLICT (entidad_origen_id, entidad_destino_id, tipo_relacion) 
                DO NOTHING;
            END IF;
        END;
    END LOOP;
END IF;
```

### **6.3. Tabla Supabase Schema Real**
```sql
CREATE TABLE entidad_relacion (
    entidad_origen_id BIGINT NOT NULL REFERENCES entidades(id),  -- ✅ Campo real: entidad_origen_id
    entidad_destino_id BIGINT NOT NULL REFERENCES entidades(id), -- ✅ Campo real: entidad_destino_id
    tipo_relacion VARCHAR(50) NOT NULL,              -- ✅ Campo real: tipo_relacion
    descripcion TEXT,                                -- ✅ Campo real: descripcion
    fecha_inicio TIMESTAMP WITH TIME ZONE,           -- ✅ Campo real: fecha_inicio
    fecha_fin TIMESTAMP WITH TIME ZONE,              -- ✅ Campo real: fecha_fin
    fuerza_relacion INTEGER NOT NULL DEFAULT 5,      -- ✅ Campo real: fuerza_relacion
    PRIMARY KEY (entidad_origen_id, entidad_destino_id, tipo_relacion),
    CONSTRAINT check_different_related_entities CHECK (entidad_origen_id <> entidad_destino_id)
);
```

**CHECK constraints:**
- `tipo_relacion IN ('miembro_de', 'subsidiaria_de', 'aliado_con', 'opositor_a', 'sucesor_de', 'predecesor_de', 'casado_con', 'familiar_de', 'empleado_de')`
- `fuerza_relacion BETWEEN 1 AND 10`

---

## **7. FLUJO COMPLETO - DONDE SE ROMPE**

### **7.1. Flujo Actual (ROTO)**
```
1. Fase 7B.1: Detecta relaciones entidad-entidad correctamente ✅
2. Almacena en metadata_normalizacion.relaciones_completas ✅
3. ❌ FALLA: pipeline_coordinator.py tiene TODO - NO extrae relaciones
4. PayloadBuilder: Recibe relaciones_entidades=None
5. RPC: No inserta ninguna relación entidad_relacion
6. BD: Tabla entidad_relacion queda VACÍA
```

### **7.2. Flujo Esperado (CORRECTO)**
```
1. Fase 7B.1: Detecta relaciones entidad-entidad
2. Almacena en metadata correctamente
3. ✅ pipeline_coordinator extrae relaciones del metadata
4. PayloadBuilder: Convierte IDs y crea RelacionEntidadesItem
5. RPC: Inserta relaciones en entidad_relacion
6. BD: Tabla entidad_relacion poblada correctamente
```

---

## **8. MAPEO COMPLETO DE TRANSFORMACIONES**

### **8.1. Transformación de IDs**
```
LLM Response           → Fase 7B.1             → PayloadBuilder (FALTA)        → RPC Supabase
=================      ===================     ==============================  ================
"entidad_origen_id": 1  → Almacenado: 1       → "entidad_origen_id_temporal": "1"  → temp_entidad_id_map
"entidad_destino_id": 2 → Almacenado: 2       → "entidad_destino_id_temporal": "2" → temp_entidad_id_map
```

### **8.2. Transformación de Campos**
```
LLM/Prompt                → PayloadBuilder              → RPC
=====================     ==========================   ====================
"descripcion"          → "descripcion_relacion"       → "descripcion_relacion" ✅
"fecha_inicio"         → "fecha_inicio_relacion"      → NO procesado ❌
"fecha_fin"            → "fecha_fin_relacion"         → NO procesado ❌
```

---

## **9. INCONSISTENCIAS CRÍTICAS IDENTIFICADAS**

### **9.1. TODO No Implementado ❌**
- pipeline_coordinator.py no extrae relaciones del resultado_fase7
- Idéntico problema que con hecho_relacionado

### **9.2. Field Name Mismatch en RPC ❌**

| **Campo** | **PayloadBuilder (modelo)** | **RPC Supabase** | **Tabla BD** | **Status** |
|-----------|---------------------------|------------------|--------------|------------|
| ID Origen | `entidad_origen_id_temporal` | `id_entidad_origen` ❌ | `entidad_origen_id` | MISMATCH |
| ID Destino | `entidad_destino_id_temporal` | `id_entidad_destino` ❌ | `entidad_destino_id` | MISMATCH |
| Descripción | `descripcion_relacion` | `descripcion_relacion` ✅ | `descripcion` | OK (RPC mapea) |

### **9.3. Campos No Procesados ❌**
- `fecha_inicio_relacion` → Modelo lo define pero RPC no lo procesa
- `fecha_fin_relacion` → Modelo lo define pero RPC no lo procesa
- `contexto_relacion` → Modelo lo define pero RPC no lo procesa

### **9.4. Tipos de Relación Consistentes ✅**
- A diferencia de hecho_relacionado, los tipos coinciden entre prompt y BD

---

## **10. SOLUCIÓN REQUERIDA**

### **10.1. Implementar Extracción en pipeline_coordinator.py**
```python
# REEMPLAZAR los TODOs con extracción real del metadata
relaciones_entidades = resultado_fase7.metadata_normalizacion
    .get("relaciones_completas", {})
    .get("relaciones_estructurales", {})
    .get("entidad_relacion", [])
```

### **10.2. Alinear Nombres de Campos**
```python
# OPCIÓN A: Cambiar modelo RelacionEntidadesItem
class RelacionEntidadesItem(PersistenciaBaseModel):
    id_entidad_origen: str          # EN VEZ DE: entidad_origen_id_temporal
    id_entidad_destino: str         # EN VEZ DE: entidad_destino_id_temporal
    # ... resto igual ...

# OPCIÓN B: Cambiar RPC para buscar campos correctos
v_entidad_origen_id := (temp_entidad_id_map->>(v_relacion->>'entidad_origen_id_temporal'))::BIGINT;
v_entidad_destino_id := (temp_entidad_id_map->>(v_relacion->>'entidad_destino_id_temporal'))::BIGINT;
```

### **10.3. Agregar Procesamiento de Fechas en RPC**
```sql
-- AGREGAR en RPC después de línea 412:
fecha_inicio,
fecha_fin

-- Y en VALUES:
CASE WHEN v_relacion ? 'fecha_inicio_relacion' 
    THEN (v_relacion->>'fecha_inicio_relacion')::TIMESTAMP WITH TIME ZONE
    ELSE NULL END,
CASE WHEN v_relacion ? 'fecha_fin_relacion' 
    THEN (v_relacion->>'fecha_fin_relacion')::TIMESTAMP WITH TIME ZONE
    ELSE NULL END
```

### **10.4. Conversión Completa de Relaciones**
```python
def convertir_relaciones_entidades(relaciones_raw):
    """Convierte relaciones del formato LLM al formato persistencia"""
    relaciones_convertidas = []
    
    for rel in relaciones_raw:
        relaciones_convertidas.append({
            "id_entidad_origen": str(rel["entidad_origen_id"]),      # o entidad_origen_id_temporal
            "id_entidad_destino": str(rel["entidad_destino_id"]),    # o entidad_destino_id_temporal
            "tipo_relacion": rel["tipo_relacion"],
            "descripcion_relacion": rel.get("descripcion", ""),
            "fecha_inicio_relacion": convertir_a_iso8601(rel.get("fecha_inicio")),
            "fecha_fin_relacion": convertir_a_iso8601(rel.get("fecha_fin")),
            "fuerza_relacion": rel.get("fuerza_relacion", 5)
        })
    
    return relaciones_convertidas
```

**CONCLUSIÓN**: Similar a hecho_relacionado, el schema está bien diseñado pero el **FLUJO ESTÁ INCOMPLETO**. Las relaciones se detectan correctamente pero nunca se extraen del metadata debido al mismo TODO no implementado, resultando en pérdida total de relaciones entidad-entidad.