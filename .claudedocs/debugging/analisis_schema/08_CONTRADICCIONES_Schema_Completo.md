# **ANÁLISIS COMPLETO: SCHEMA CONTRADICCIONES (Contradicciones entre Hechos)**

## **RESUMEN EJECUTIVO**

Schema de contradicciones mapeado completamente. Al igual que las relaciones anteriores, la Fase 7B.2 detecta contradicciones correctamente pero el `pipeline_coordinator.py` tiene un TODO y NO las extrae para pasarlas al PayloadBuilder.

---

## **1. MODELOS PYDANTIC - ENTRADA**

### **1.1. ContradiccionDetectadaItem (`src/module_pipeline/src/models/persistencia.py`)**

```json
{
  "hecho_principal_id_temporal": "HECHO-1",          // str - ID temporal primer hecho
  "hecho_contradictorio_id_temporal": "HECHO-3",     // str - ID temporal hecho contradictorio
  "tipo_contradiccion": "temporal",                  // Optional[str] - Tipo
  "grado_contradiccion": 4,                          // Optional[int] 1-5
  "descripcion_contradiccion": "Fechas contradictorias sobre el evento" // Optional[str]
}
```

**Tipos de contradicción en modelo (ejemplos):**
- `temporal`
- `logica`
- `factual`

---

## **2. PROMPTS LLM - SCHEMA ESPERADO**

### **2.1. Prompt Principal (`prompts/7B.2_Relaciones-Temporales.md`)**

```json
{
  "hecho_relacionado": [                             // Relaciones causa-efecto, etc.
    // ... analizado en documento anterior ...
  ],
  "contradicciones": [
    {
      "hecho_principal_id": 1,                       // int - ID secuencial hecho principal
      "hecho_contradictorio_id": 3,                  // int - ID secuencial hecho contradictorio
      "tipo_contradiccion": "contenido",             // str - enum específico
      "grado_contradiccion": 4,                      // int - Grado 1-5
      "descripcion": "Cifras contradictorias sobre número de asistentes" // str
    }
  ]
}
```

**Tipos de contradicción permitidos exactos:**
- `fecha`
- `contenido`
- `entidades`
- `ubicacion`
- `valor`
- `completa`

---

## **3. FASE 7B.2 - DETECCIÓN DE CONTRADICCIONES (`src/pipeline/fase_7_normalizacion.py`)**

### **3.1. Input Schema**
```json
{
  "hechos_normalizados": "Array de HechoProcesado con normalización"
}
```

### **3.2. Output Schema**
```json
{
  "relaciones": {
    "hecho_relacionado": [...],
    "contradicciones": [                             // ✅ Contradicciones detectadas por LLM
      {
        "hecho_principal_id": 1,
        "hecho_contradictorio_id": 3,
        "tipo_contradiccion": "contenido",
        "grado_contradiccion": 4,
        "descripcion": "Cifras contradictorias sobre asistentes"
      }
    ]
  },
  "metadatos": {
    "modelo": "llama-3.1-8b-instant",
    "duracion_ms": 1234
  }
}
```

### **3.3. Almacenamiento en ResultadoFase4Normalizacion**
```json
{
  "metadata_normalizacion": {
    "relaciones_completas": {
      "relaciones_temporales": {
        "hecho_relacionado": [...],
        "contradicciones": [...]                     // ✅ Aquí se guardan
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
# CÓDIGO FALTANTE - Extraer contradicciones del resultado_fase7
if resultado_fase7.metadata_normalizacion:
    relaciones = resultado_fase7.metadata_normalizacion.get("relaciones_completas", {})
    
    # Extraer relaciones temporales
    relaciones_temporales = relaciones.get("relaciones_temporales", {})
    contradicciones_detectadas = relaciones_temporales.get("contradicciones", [])
```

---

## **5. PAYLOADBUILDER - CONVERSIÓN (`src/services/payload_builder.py`)**

### **5.1. Input Schema (si se implementara)**
```json
{
  "contradicciones_detectadas_data": [
    {
      "hecho_principal_id": 1,                       // int - ID secuencial
      "hecho_contradictorio_id": 3,                  // int - ID secuencial
      "tipo_contradiccion": "contenido",
      "grado_contradiccion": 4,
      "descripcion": "Cifras contradictorias"
    }
  ]
}
```

### **5.2. Función de Conversión (línea 441)**
```python
def construir_payload_articulo_from_model():
    if contradicciones_detectadas_data is not None:
        payload_data["contradicciones_detectadas"] = [
            ContradiccionDetectadaItem(**item) for item in contradicciones_detectadas_data
        ]
```

### **5.3. Validación de Integridad (necesaria)**
```python
def validar_integridad_referencial_contradicciones():
    """Valida que todos los IDs temporales en contradicciones existan"""
    ids_hechos_validos = {h["id_temporal_hecho"] for h in payload_data.get("hechos_extraidos", [])}
    
    for contradiccion in payload_data.get("contradicciones_detectadas", []):
        if contradiccion.hecho_principal_id_temporal not in ids_hechos_validos:
            raise ValueError(f"Contradicción referencia hecho principal inexistente")
        if contradiccion.hecho_contradictorio_id_temporal not in ids_hechos_validos:
            raise ValueError(f"Contradicción referencia hecho contradictorio inexistente")
```

### **5.4. Transformación de Campos Necesaria**
```python
# IDs secuenciales → IDs temporales
hecho_principal_id (int)         → hecho_principal_id_temporal (str)
hecho_contradictorio_id (int)    → hecho_contradictorio_id_temporal (str)
tipo_contradiccion               → tipo_contradiccion (mapeo de nombres)
grado_contradiccion              → grado_contradiccion
descripcion                      → descripcion_contradiccion
```

---

## **6. RPC SUPABASE - PERSISTENCIA (`actualizar_articulo_procesado.sql`)**

### **6.1. Input Schema Esperado**
```json
{
  "contradicciones_detectadas": [
    {
      "id_hecho_principal": "HECHO-1",               // ❌ RPC busca id_hecho_principal
      "id_hecho_contradictorio": "HECHO-3",          // ❌ RPC busca id_hecho_contradictorio
      "tipo_contradiccion": "contenido",             // ✅ RPC busca tipo_contradiccion
      "grado_contradiccion": 4,                      // ✅ RPC busca grado_contradiccion
      "descripcion_contradiccion": "Cifras contradictorias" // ✅ RPC busca descripcion_contradiccion
    }
  ]
}
```

### **6.2. Procesamiento de Contradicciones (líneas 431-476)**
```sql
-- Procesar contradicciones
IF datos_json ? 'contradicciones_detectadas' THEN
    FOR v_relacion IN SELECT * FROM jsonb_array_elements(datos_json->'contradicciones_detectadas')
    LOOP
        DECLARE
            v_hecho_principal_id BIGINT;
            v_hecho_contradictorio_id BIGINT;
            v_fecha_principal TSTZRANGE;
            v_fecha_contradictoria TSTZRANGE;
        BEGIN
            -- Obtener IDs reales
            v_hecho_principal_id := (temp_hecho_id_map->>(v_relacion->>'id_hecho_principal'))::BIGINT;       -- ❌ Busca id_hecho_principal
            v_hecho_contradictorio_id := (temp_hecho_id_map->>(v_relacion->>'id_hecho_contradictorio'))::BIGINT; -- ❌ Busca id_hecho_contradictorio
            
            IF v_hecho_principal_id IS NOT NULL AND v_hecho_contradictorio_id IS NOT NULL THEN
                -- Obtener fechas
                SELECT fecha_ocurrencia INTO v_fecha_principal 
                FROM hechos WHERE id = v_hecho_principal_id;
                
                SELECT fecha_ocurrencia INTO v_fecha_contradictoria 
                FROM hechos WHERE id = v_hecho_contradictorio_id;
                
                -- Insertar contradicción
                INSERT INTO contradicciones (
                    hecho_principal_id,
                    fecha_ocurrencia_principal,
                    hecho_contradictorio_id,
                    fecha_ocurrencia_contradictoria,
                    tipo_contradiccion,
                    grado_contradiccion,
                    descripcion
                )
                VALUES (
                    v_hecho_principal_id,
                    v_fecha_principal,
                    v_hecho_contradictorio_id,
                    v_fecha_contradictoria,
                    v_relacion->>'tipo_contradiccion',                            -- ✅ Busca tipo_contradiccion
                    COALESCE((v_relacion->>'grado_contradiccion')::INTEGER, 3),   -- ✅ Busca grado_contradiccion
                    v_relacion->>'descripcion_contradiccion'                      -- ✅ Busca descripcion_contradiccion
                );
            END IF;
        END;
    END LOOP;
END IF;
```

### **6.3. Tabla Supabase Schema Real**
```sql
CREATE TABLE contradicciones (
    id SERIAL PRIMARY KEY,
    hecho_principal_id BIGINT NOT NULL,              -- ✅ Campo real: hecho_principal_id
    fecha_ocurrencia_principal TSTZRANGE NOT NULL,   -- ✅ Campo real: fecha_ocurrencia_principal
    hecho_contradictorio_id BIGINT NOT NULL,         -- ✅ Campo real: hecho_contradictorio_id
    fecha_ocurrencia_contradictoria TSTZRANGE NOT NULL, -- ✅ Campo real: fecha_ocurrencia_contradictoria
    tipo_contradiccion VARCHAR(50) NOT NULL,         -- ✅ Campo real: tipo_contradiccion
    grado_contradiccion INTEGER NOT NULL DEFAULT 3,  -- ✅ Campo real: grado_contradiccion
    descripcion TEXT,                                -- ✅ Campo real: descripcion
    fecha_deteccion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    ultimo_analisis TIMESTAMP WITH TIME ZONE DEFAULT now(),
    estado_resolucion VARCHAR(50) DEFAULT 'pendiente',
    CONSTRAINT check_different_hechos CHECK (
        hecho_principal_id <> hecho_contradictorio_id OR 
        fecha_ocurrencia_principal <> fecha_ocurrencia_contradictoria
    )
);
```

**CHECK constraints:**
- `tipo_contradiccion IN ('fecha', 'contenido', 'entidades', 'ubicacion', 'valor', 'completa')`
- `grado_contradiccion BETWEEN 1 AND 5`
- `estado_resolucion IN ('pendiente', 'analizada', 'resuelta', 'ignorada')`

---

## **7. FLUJO COMPLETO - DONDE SE ROMPE**

### **7.1. Flujo Actual (ROTO)**
```
1. Fase 7B.2: Detecta contradicciones correctamente ✅
2. Almacena en metadata_normalizacion.relaciones_completas ✅
3. ❌ FALLA: pipeline_coordinator.py tiene TODO - NO extrae contradicciones
4. PayloadBuilder: Recibe contradicciones_detectadas=None
5. RPC: No inserta ninguna contradicción
6. BD: Tabla contradicciones queda VACÍA
```

### **7.2. Flujo Esperado (CORRECTO)**
```
1. Fase 7B.2: Detecta contradicciones
2. Almacena en metadata correctamente
3. ✅ pipeline_coordinator extrae contradicciones del metadata
4. PayloadBuilder: Convierte IDs y crea ContradiccionDetectadaItem
5. RPC: Inserta contradicciones en tabla
6. BD: Tabla contradicciones poblada correctamente
```

---

## **8. MAPEO COMPLETO DE TRANSFORMACIONES**

### **8.1. Transformación de IDs**
```
LLM Response                → Fase 7B.2           → PayloadBuilder (FALTA)           → RPC Supabase
=====================       =================     ================================   ================
"hecho_principal_id": 1    → Almacenado: 1      → "hecho_principal_id_temporal": "1"     → temp_hecho_id_map
"hecho_contradictorio_id": 3 → Almacenado: 3    → "hecho_contradictorio_id_temporal": "3" → temp_hecho_id_map
```

### **8.2. Transformación de Tipos de Contradicción**
```
LLM/Prompt                → Modelo Pydantic          → RPC/BD
=====================     ======================    ==============
"fecha"                → "temporal" ❌             → "fecha" ✅
"contenido"            → "logica" ❌               → "contenido" ✅
"entidades"            → "factual" ❌              → "entidades" ✅
"ubicacion"            → tipo_contradiccion        → "ubicacion" ✅
"valor"                → tipo_contradiccion        → "valor" ✅
"completa"             → tipo_contradiccion        → "completa" ✅
```

---

## **9. INCONSISTENCIAS CRÍTICAS IDENTIFICADAS**

### **9.1. TODO No Implementado ❌**
- pipeline_coordinator.py no extrae contradicciones del resultado_fase7
- Mismo problema que con todas las relaciones

### **9.2. Field Name Mismatch en RPC ❌**

| **Campo** | **PayloadBuilder (modelo)** | **RPC Supabase** | **Status** |
|-----------|---------------------------|------------------|------------|
| ID Principal | `hecho_principal_id_temporal` | `id_hecho_principal` ❌ | MISMATCH |
| ID Contradictorio | `hecho_contradictorio_id_temporal` | `id_hecho_contradictorio` ❌ | MISMATCH |
| Tipo | `tipo_contradiccion` | `tipo_contradiccion` ✅ | OK |
| Grado | `grado_contradiccion` | `grado_contradiccion` ✅ | OK |
| Descripción | `descripcion_contradiccion` | `descripcion_contradiccion` ✅ | OK |

### **9.3. Tipos de Contradicción Inconsistentes ❌**
- Modelo Pydantic: `temporal`, `logica`, `factual`
- Prompt/BD: `fecha`, `contenido`, `entidades`, `ubicacion`, `valor`, `completa`
- No hay mapeo entre ambos sets de valores

### **9.4. Campos No Utilizados**
- `fecha_deteccion`, `ultimo_analisis`, `estado_resolucion` → Definidos en BD pero no poblados desde pipeline

---

## **10. SOLUCIÓN REQUERIDA**

### **10.1. Implementar Extracción en pipeline_coordinator.py**
```python
# REEMPLAZAR el TODO con extracción real
contradicciones_detectadas = resultado_fase7.metadata_normalizacion
    .get("relaciones_completas", {})
    .get("relaciones_temporales", {})
    .get("contradicciones", [])
```

### **10.2. Alinear Nombres de Campos**
```python
# OPCIÓN A: Cambiar modelo ContradiccionDetectadaItem
class ContradiccionDetectadaItem(PersistenciaBaseModel):
    id_hecho_principal: str          # EN VEZ DE: hecho_principal_id_temporal
    id_hecho_contradictorio: str     # EN VEZ DE: hecho_contradictorio_id_temporal
    # ... resto igual ...

# OPCIÓN B: Cambiar RPC para buscar campos correctos
v_hecho_principal_id := (temp_hecho_id_map->>(v_relacion->>'hecho_principal_id_temporal'))::BIGINT;
v_hecho_contradictorio_id := (temp_hecho_id_map->>(v_relacion->>'hecho_contradictorio_id_temporal'))::BIGINT;
```

### **10.3. Mapear Tipos de Contradicción**
```python
# Crear mapeo de tipos
TIPO_CONTRADICCION_MAP = {
    "fecha": "fecha",              # Sin cambio
    "contenido": "contenido",      # Sin cambio
    "temporal": "fecha",           # Mapeo necesario
    "logica": "contenido",         # Mapeo necesario
    "factual": "valor"             # Mapeo necesario
}

def mapear_tipo_contradiccion(tipo_modelo):
    return TIPO_CONTRADICCION_MAP.get(tipo_modelo, tipo_modelo)
```

### **10.4. Conversión Completa de Contradicciones**
```python
def convertir_contradicciones(contradicciones_raw):
    """Convierte contradicciones del formato LLM al formato persistencia"""
    contradicciones_convertidas = []
    
    for cont in contradicciones_raw:
        contradicciones_convertidas.append({
            "id_hecho_principal": str(cont["hecho_principal_id"]),           # o hecho_principal_id_temporal
            "id_hecho_contradictorio": str(cont["hecho_contradictorio_id"]), # o hecho_contradictorio_id_temporal
            "tipo_contradiccion": mapear_tipo_contradiccion(cont["tipo_contradiccion"]),
            "grado_contradiccion": cont.get("grado_contradiccion", 3),
            "descripcion_contradiccion": cont.get("descripcion", "")
        })
    
    return contradicciones_convertidas
```

**CONCLUSIÓN**: Al igual que las otras relaciones, el schema está bien diseñado pero el **FLUJO ESTÁ INCOMPLETO**. Las contradicciones se detectan correctamente pero nunca se extraen del metadata debido al mismo TODO no implementado, resultando en pérdida total de detección de contradicciones.