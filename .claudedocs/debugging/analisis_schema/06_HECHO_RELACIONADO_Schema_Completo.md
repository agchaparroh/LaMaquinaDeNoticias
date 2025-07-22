# **ANÁLISIS COMPLETO: SCHEMA HECHO_RELACIONADO (Relaciones entre Hechos)**

## **RESUMEN EJECUTIVO**

Schema de relaciones hecho-hecho mapeado completamente. Se identifica otro **PROBLEMA CRÍTICO**: aunque la Fase 7B.2 detecta relaciones entre hechos correctamente, el `pipeline_coordinator.py` tiene un TODO y NO extrae estas relaciones para pasarlas al PayloadBuilder.

---

## **1. MODELOS PYDANTIC - ENTRADA**

### **1.1. RelacionHechosItem (`src/module_pipeline/src/models/persistencia.py`)**

```json
{
  "hecho_origen_id_temporal": "HECHO-1",             // str - ID temporal del primer hecho
  "hecho_destino_id_temporal": "HECHO-2",            // str - ID temporal del segundo hecho
  "tipo_relacion": "causa-efecto",                   // str - Tipo de relación
  "descripcion_relacion": "El anuncio causó protestas", // Optional[str] - Descripción
  "direccion_relacion": "origen_a_destino",          // Optional[str] - Dirección
  "fecha_inicio_relacion": "2023-03-14T00:00:00Z",   // Optional[str] - ISO 8601
  "fecha_fin_relacion": null,                        // Optional[str] - ISO 8601
  "fuerza_relacion": 8                               // Optional[int] 1-10
}
```

**Tipos de relación en modelo:**
- `causa-efecto`
- `temporal_secuencial`
- `aclaracion`

---

## **2. PROMPTS LLM - SCHEMA ESPERADO**

### **2.1. Prompt Principal (`prompts/7B.2_Relaciones-Temporales.md`)**

```json
{
  "hecho_relacionado": [
    {
      "hecho_origen_id": 1,                          // int - ID secuencial hecho origen
      "hecho_destino_id": 2,                         // int - ID secuencial hecho destino
      "tipo_relacion": "causa",                      // str - enum específico
      "fuerza_relacion": 8,                          // int - Fuerza 1-10
      "descripcion_relacion": "El anuncio del presidente causó las protestas" // str
    }
  ],
  "contradicciones": [
    {
      "hecho_principal_id": 1,
      "hecho_contradictorio_id": 3,
      "tipo_contradiccion": "contenido",             // str - enum específico
      "grado_contradiccion": 4,                      // int - Grado 1-5
      "descripcion": "Cifras contradictorias sobre asistentes"
    }
  ]
}
```

**Tipos de relación permitidos exactos:**
- **hecho_relacionado:** `causa`, `consecuencia`, `contexto_historico`, `respuesta_a`, `aclaracion_de`, `version_alternativa`, `seguimiento_de`
- **contradicciones:** `fecha`, `contenido`, `entidades`, `ubicacion`, `valor`, `completa`

---

## **3. FASE 7B.2 - DETECCIÓN DE RELACIONES TEMPORALES (`src/pipeline/fase_7_normalizacion.py`)**

### **3.1. Input Schema**
```json
{
  "hechos_normalizados": "Array de HechoProcesado con normalización",
  "relaciones_preliminares": "Relaciones detectadas en fases anteriores"
}
```

### **3.2. Output Schema**
```json
{
  "relaciones": {
    "hecho_relacionado": [                           // ✅ Relaciones detectadas por LLM
      {
        "hecho_origen_id": 1,
        "hecho_destino_id": 2,
        "tipo_relacion": "causa",
        "fuerza_relacion": 8,
        "descripcion_relacion": "El anuncio causó protestas"
      }
    ],
    "contradicciones": [                             // ✅ Contradicciones detectadas
      {
        "hecho_principal_id": 1,
        "hecho_contradictorio_id": 3,
        "tipo_contradiccion": "contenido",
        "grado_contradiccion": 4,
        "descripcion": "Cifras contradictorias"
      }
    ]
  },
  "metadatos": {
    "modelo": "llama-3.1-8b-instant",
    "duracion_ms": 1234,
    "tokens_prompt": 5678,
    "tokens_respuesta": 910
  }
}
```

### **3.3. Almacenamiento en ResultadoFase4Normalizacion**
```json
{
  "metadata_normalizacion": {
    "relaciones_completas": {
      "relaciones_estructurales": {
        "hecho_entidad": [...],
        "entidad_relacion": [...]
      },
      "relaciones_temporales": {                     // ✅ Aquí se guardan
        "hecho_relacionado": [...],
        "contradicciones": [...]
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
    
    # Extraer relaciones temporales
    relaciones_temporales = relaciones.get("relaciones_temporales", {})
    relaciones_hechos = relaciones_temporales.get("hecho_relacionado", [])
    contradicciones_detectadas = relaciones_temporales.get("contradicciones", [])
    
    # Extraer relaciones estructurales
    relaciones_estructurales = relaciones.get("relaciones_estructurales", {})
    relaciones_entidades = relaciones_estructurales.get("entidad_relacion", [])
```

---

## **5. PAYLOADBUILDER - CONVERSIÓN (`src/services/payload_builder.py`)**

### **5.1. Input Schema (si se implementara)**
```json
{
  "relaciones_hechos_data": [
    {
      "hecho_origen_id": 1,                          // int - ID secuencial
      "hecho_destino_id": 2,                         // int - ID secuencial
      "tipo_relacion": "causa",
      "fuerza_relacion": 8,
      "descripcion_relacion": "El anuncio causó protestas"
    }
  ]
}
```

### **5.2. Función de Conversión (línea 433)**
```python
def construir_payload_articulo_from_model():
    if relaciones_hechos_data is not None:
        payload_data["relaciones_hechos"] = [
            RelacionHechosItem(**item) for item in relaciones_hechos_data
        ]
```

### **5.3. Validación de Integridad (líneas 123-134)**
```python
def validar_integridad_referencial():
    """Valida que todos los IDs temporales en relaciones existan"""
    ids_hechos_validos = {h["id_temporal_hecho"] for h in payload_data.get("hechos_extraidos", [])}
    
    for relacion in payload_data.get("relaciones_hechos", []):
        if relacion.hecho_origen_id_temporal not in ids_hechos_validos:
            raise ValueError(f"Relación referencia hecho origen inexistente: {relacion.hecho_origen_id_temporal}")
        if relacion.hecho_destino_id_temporal not in ids_hechos_validos:
            raise ValueError(f"Relación referencia hecho destino inexistente: {relacion.hecho_destino_id_temporal}")
```

### **5.4. Transformación de Campos Necesaria**
```python
# IDs secuenciales → IDs temporales
hecho_origen_id (int)          → hecho_origen_id_temporal (str)
hecho_destino_id (int)         → hecho_destino_id_temporal (str)
tipo_relacion                  → tipo_relacion (mapeo de nombres)
fuerza_relacion                → fuerza_relacion
descripcion_relacion           → descripcion_relacion
```

---

## **6. RPC SUPABASE - PERSISTENCIA (`actualizar_articulo_procesado.sql`)**

### **6.1. Input Schema Esperado**
```json
{
  "relaciones_hechos": [
    {
      "id_hecho_origen": "HECHO-1",                  // ❌ RPC busca id_hecho_origen
      "id_hecho_destino": "HECHO-2",                 // ❌ RPC busca id_hecho_destino
      "tipo_relacion": "causa",                      // ✅ RPC busca tipo_relacion
      "fuerza_relacion": 8,                          // ✅ RPC busca fuerza_relacion
      "descripcion_relacion": "El anuncio causó protestas" // ✅ RPC busca descripcion_relacion
    }
  ]
}
```

### **6.2. Procesamiento de Relaciones (líneas 344-390)**
```sql
-- Procesar relaciones hecho-hecho
IF datos_json ? 'relaciones_hechos' THEN
    FOR v_relacion IN SELECT * FROM jsonb_array_elements(datos_json->'relaciones_hechos')
    LOOP
        DECLARE
            v_hecho_origen_id BIGINT;
            v_hecho_destino_id BIGINT;
            v_fecha_origen TSTZRANGE;
            v_fecha_destino TSTZRANGE;
        BEGIN
            -- Obtener IDs reales
            v_hecho_origen_id := (temp_hecho_id_map->>(v_relacion->>'id_hecho_origen'))::BIGINT;  -- ❌ Busca id_hecho_origen
            v_hecho_destino_id := (temp_hecho_id_map->>(v_relacion->>'id_hecho_destino'))::BIGINT; -- ❌ Busca id_hecho_destino
            
            IF v_hecho_origen_id IS NOT NULL AND v_hecho_destino_id IS NOT NULL THEN
                -- Obtener fechas
                SELECT fecha_ocurrencia INTO v_fecha_origen 
                FROM hechos WHERE id = v_hecho_origen_id;
                
                SELECT fecha_ocurrencia INTO v_fecha_destino 
                FROM hechos WHERE id = v_hecho_destino_id;
                
                -- Insertar relación
                INSERT INTO hecho_relacionado (
                    hecho_origen_id,
                    fecha_ocurrencia_origen,
                    hecho_destino_id,
                    fecha_ocurrencia_destino,
                    tipo_relacion,
                    fuerza_relacion,
                    descripcion_relacion
                )
                VALUES (
                    v_hecho_origen_id,
                    v_fecha_origen,
                    v_hecho_destino_id,
                    v_fecha_destino,
                    v_relacion->>'tipo_relacion',                             -- ✅ Busca tipo_relacion
                    COALESCE((v_relacion->>'fuerza_relacion')::INTEGER, 5),  -- ✅ Busca fuerza_relacion
                    v_relacion->>'descripcion_relacion'                      -- ✅ Busca descripcion_relacion
                )
                ON CONFLICT DO NOTHING;
            END IF;
        END;
    END LOOP;
END IF;
```

### **6.3. Tabla Supabase Schema Real**
```sql
CREATE TABLE hecho_relacionado (
    hecho_origen_id BIGINT NOT NULL,                 -- ✅ Campo real: hecho_origen_id
    fecha_ocurrencia_origen TSTZRANGE NOT NULL,      -- ✅ Campo real: fecha_ocurrencia_origen
    hecho_destino_id BIGINT NOT NULL,                -- ✅ Campo real: hecho_destino_id
    fecha_ocurrencia_destino TSTZRANGE NOT NULL,     -- ✅ Campo real: fecha_ocurrencia_destino
    tipo_relacion VARCHAR(50) NOT NULL,              -- ✅ Campo real: tipo_relacion
    fuerza_relacion INTEGER NOT NULL DEFAULT 5,      -- ✅ Campo real: fuerza_relacion
    descripcion_relacion TEXT,                       -- ✅ Campo real: descripcion_relacion
    fecha_deteccion TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (hecho_origen_id, fecha_ocurrencia_origen, hecho_destino_id, fecha_ocurrencia_destino, tipo_relacion),
    CONSTRAINT check_different_related_hechos CHECK (hecho_origen_id <> hecho_destino_id OR fecha_ocurrencia_origen <> fecha_ocurrencia_destino)
);
```

**CHECK constraints:**
- `tipo_relacion IN ('causa', 'consecuencia', 'contexto_historico', 'respuesta_a', 'aclaracion_de', 'version_alternativa', 'seguimiento_de')`
- `fuerza_relacion BETWEEN 1 AND 10`

---

## **7. FLUJO COMPLETO - DONDE SE ROMPE**

### **7.1. Flujo Actual (ROTO)**
```
1. Fase 7B.2: Detecta relaciones hecho-hecho correctamente ✅
2. Almacena en metadata_normalizacion.relaciones_completas ✅
3. ❌ FALLA: pipeline_coordinator.py tiene TODO - NO extrae relaciones
4. PayloadBuilder: Recibe relaciones_hechos=None
5. RPC: No inserta ninguna relación hecho_relacionado
6. BD: Tabla hecho_relacionado queda VACÍA
```

### **7.2. Flujo Esperado (CORRECTO)**
```
1. Fase 7B.2: Detecta relaciones hecho-hecho
2. Almacena en metadata correctamente
3. ✅ pipeline_coordinator extrae relaciones del metadata
4. PayloadBuilder: Convierte IDs y crea RelacionHechosItem
5. RPC: Inserta relaciones en hecho_relacionado
6. BD: Tabla hecho_relacionado poblada correctamente
```

---

## **8. MAPEO COMPLETO DE TRANSFORMACIONES**

### **8.1. Transformación de IDs**
```
LLM Response         → Fase 7B.2           → PayloadBuilder (FALTA)      → RPC Supabase
===============      =================     ==========================    ================
"hecho_origen_id": 1  → Almacenado: 1     → "hecho_origen_id_temporal": "1"  → temp_hecho_id_map
"hecho_destino_id": 2 → Almacenado: 2     → "hecho_destino_id_temporal": "2" → temp_hecho_id_map
```

### **8.2. Transformación de Tipos de Relación**
```
LLM/Prompt                → PayloadBuilder           → RPC/BD
=====================     ======================    ==============
"causa"                → "causa-efecto" ❌         → "causa" ✅
"consecuencia"         → tipo_relacion           → tipo_relacion
"contexto_historico"   → tipo_relacion           → tipo_relacion
```

---

## **9. INCONSISTENCIAS CRÍTICAS IDENTIFICADAS**

### **9.1. TODO No Implementado ❌**
- pipeline_coordinator.py no extrae relaciones del resultado_fase7
- Marca explícitamente como TODO pendiente
- Resultado: relaciones detectadas pero nunca usadas

### **9.2. Field Name Mismatch en RPC ❌**

| **Campo** | **PayloadBuilder (modelo)** | **RPC Supabase** | **Status** |
|-----------|---------------------------|------------------|------------|
| ID Origen | `hecho_origen_id_temporal` | `id_hecho_origen` ❌ | MISMATCH |
| ID Destino | `hecho_destino_id_temporal` | `id_hecho_destino` ❌ | MISMATCH |
| Tipo | `tipo_relacion` | `tipo_relacion` ✅ | OK |
| Fuerza | `fuerza_relacion` | `fuerza_relacion` ✅ | OK |
| Descripción | `descripcion_relacion` | `descripcion_relacion` ✅ | OK |

### **9.3. Tipos de Relación Inconsistentes ❌**
- Modelo Pydantic: `causa-efecto`, `temporal_secuencial`, `aclaracion`
- Prompt/BD: `causa`, `consecuencia`, `contexto_historico`, `respuesta_a`, `aclaracion_de`, `version_alternativa`, `seguimiento_de`
- No hay mapeo entre ambos sets de valores

### **9.4. Campos No Utilizados**
- `direccion_relacion` → Definido en modelo pero no usado
- `fecha_inicio_relacion`, `fecha_fin_relacion` → Definidos pero no usados

---

## **10. SOLUCIÓN REQUERIDA**

### **10.1. Implementar Extracción en pipeline_coordinator.py**
```python
# REEMPLAZAR los TODOs con:
def extraer_relaciones_de_metadata(resultado_fase7):
    """Extrae relaciones del metadata de normalización"""
    if not resultado_fase7.metadata_normalizacion:
        return None, None, None
        
    relaciones = resultado_fase7.metadata_normalizacion.get("relaciones_completas", {})
    
    # Relaciones temporales
    temporales = relaciones.get("relaciones_temporales", {})
    relaciones_hechos = temporales.get("hecho_relacionado", [])
    contradicciones = temporales.get("contradicciones", [])
    
    # Relaciones estructurales
    estructurales = relaciones.get("relaciones_estructurales", {})
    relaciones_entidades = estructurales.get("entidad_relacion", [])
    
    return relaciones_hechos, relaciones_entidades, contradicciones
```

### **10.2. Alinear Nombres de Campos**
```python
# OPCIÓN A: Cambiar modelo RelacionHechosItem
class RelacionHechosItem(PersistenciaBaseModel):
    id_hecho_origen: str          # EN VEZ DE: hecho_origen_id_temporal
    id_hecho_destino: str         # EN VEZ DE: hecho_destino_id_temporal
    # ... resto igual ...

# OPCIÓN B: Cambiar RPC para buscar campos correctos
v_hecho_origen_id := (temp_hecho_id_map->>(v_relacion->>'hecho_origen_id_temporal'))::BIGINT;
v_hecho_destino_id := (temp_hecho_id_map->>(v_relacion->>'hecho_destino_id_temporal'))::BIGINT;
```

### **10.3. Mapear Tipos de Relación**
```python
# Crear mapeo de tipos
TIPO_RELACION_MAP = {
    "causa": "causa",                    # Sin cambio
    "consecuencia": "consecuencia",      # Sin cambio
    "causa-efecto": "causa",             # Mapeo necesario
    "temporal_secuencial": "seguimiento_de",  # Mapeo necesario
    "aclaracion": "aclaracion_de"        # Mapeo necesario
}

def mapear_tipo_relacion(tipo_modelo):
    return TIPO_RELACION_MAP.get(tipo_modelo, tipo_modelo)
```

### **10.4. Conversión Completa de Relaciones**
```python
def convertir_relaciones_hechos(relaciones_raw, mapeo_ids):
    """Convierte relaciones del formato LLM al formato persistencia"""
    relaciones_convertidas = []
    
    for rel in relaciones_raw:
        relaciones_convertidas.append({
            "id_hecho_origen": str(rel["hecho_origen_id"]),      # o hecho_origen_id_temporal
            "id_hecho_destino": str(rel["hecho_destino_id"]),    # o hecho_destino_id_temporal
            "tipo_relacion": mapear_tipo_relacion(rel["tipo_relacion"]),
            "fuerza_relacion": rel.get("fuerza_relacion", 5),
            "descripcion_relacion": rel.get("descripcion_relacion", "")
        })
    
    return relaciones_convertidas
```

**CONCLUSIÓN**: El schema está bien diseñado pero el **FLUJO ESTÁ INCOMPLETO**. Las relaciones se detectan correctamente pero nunca se extraen del metadata debido a un TODO no implementado, resultando en pérdida total de relaciones hecho-hecho.