# **ANÁLISIS COMPLETO: SCHEMA HECHO_ENTIDAD (Relaciones)**

## **RESUMEN EJECUTIVO**

Schema de relaciones hecho-entidad mapeado completamente. Se identifica un **PROBLEMA CRÍTICO**: las relaciones detectadas en Fase 7B.1 NO se están asignando al campo `vinculado_a_entidades` de cada hecho, resultando en pérdida total de estas relaciones.

---

## **1. MODELOS PYDANTIC - ENTRADA**

### **1.1. HechoProcesado (`src/module_pipeline/src/models/procesamiento.py`)**

```json
{
  "id_hecho": 1,
  "texto_original_del_hecho": "El presidente anunció medidas",
  "vinculado_a_entidades": [2, 3, 5],                // List[int] - IDs secuenciales de EntidadProcesada
  // ... otros campos ...
}
```

### **1.2. EntidadEnHechoItem (`src/module_pipeline/src/models/persistencia.py`)**

```json
{
  "id_temporal_entidad": "2",                        // str - ID temporal de la entidad
  "nombre_entidad": "Nicolás Maduro",                // str - Nombre de la entidad
  "tipo_entidad": "PERSONA",                         // str - Tipo (PERSONA, ORGANIZACION, etc.)
  "rol_en_hecho": "protagonista"                     // str - Rol específico en el hecho
}
```

### **1.3. ResultadoFase4Normalizacion (Almacena relaciones detectadas)**

```json
{
  "metadata_normalizacion": {
    "relaciones_completas": {
      "relaciones_estructurales": {
        "hecho_entidad": [                           // Array de relaciones detectadas
          {
            "hecho_id": 1,
            "entidad_id": 2,
            "tipo_relacion": "protagonista",
            "relevancia_en_hecho": 9
          }
        ],
        "entidad_relacion": [...]                    // Otras relaciones entidad-entidad
      }
    }
  }
}
```

---

## **2. PROMPTS LLM - SCHEMA ESPERADO**

### **2.1. Prompt Principal (`prompts/7B.1_Relaciones-Estructurales.md`)**

```json
{
  "hecho_entidad": [
    {
      "hecho_id": 1,                                 // int - ID secuencial del hecho
      "entidad_id": 2,                               // int - ID secuencial de la entidad
      "tipo_relacion": "protagonista",               // str - enum específico
      "relevancia_en_hecho": 9                      // int - Relevancia 1-10
    }
  ],
  "entidad_relacion": [                              // Relaciones entidad-entidad (otro schema)
    {
      "entidad_origen_id": 1,
      "entidad_destino_id": 2,
      "tipo_relacion": "miembro_de",
      "descripcion": "Director ejecutivo",
      "fecha_inicio": null,
      "fecha_fin": null,
      "fuerza_relacion": 7
    }
  ]
}
```

**Tipos de relación permitidos exactos:**
- **hecho_entidad:** `protagonista`, `mencionado`, `afectado`, `declarante`, `ubicacion`, `contexto`, `victima`, `agresor`, `organizador`, `participante`, `otro`
- **entidad_relacion:** `miembro_de`, `subsidiaria_de`, `aliado_con`, `opositor_a`, `sucesor_de`, `predecesor_de`, `casado_con`, `familiar_de`, `empleado_de`

---

## **3. FASE 7B.1 - DETECCIÓN DE RELACIONES (`src/pipeline/fase_7b_relaciones.py`)**

### **3.1. Input Schema**
```json
{
  "hechos_normalizados": "Array de HechoProcesado con normalización",
  "entidades_normalizadas": "Array de EntidadProcesada con normalización",
  "relaciones_preliminares": "Relaciones detectadas en fases anteriores"
}
```

### **3.2. Output Schema**
```json
{
  "relaciones_completas": {
    "relaciones_estructurales": {
      "hecho_entidad": [                             // ✅ Relaciones detectadas por LLM
        {
          "hecho_id": 1,
          "entidad_id": 2,
          "tipo_relacion": "protagonista",
          "relevancia_en_hecho": 9
        }
      ],
      "entidad_relacion": [...]
    },
    "relaciones_temporales": {
      "hecho_relacionado": [...],
      "contradicciones": [...]
    }
  }
}
```

### **3.3. PROBLEMA CRÍTICO - Asignación NO Implementada**
```python
# ❌ CÓDIGO FALTANTE - Las relaciones detectadas NO se asignan a los hechos:
def asignar_relaciones_a_hechos(hechos, relaciones_hecho_entidad):
    """FUNCIÓN QUE DEBERÍA EXISTIR PERO NO EXISTE"""
    for relacion in relaciones_hecho_entidad:
        hecho = buscar_hecho_por_id(hechos, relacion["hecho_id"])
        if hecho:
            hecho.vinculado_a_entidades.append(relacion["entidad_id"])
```

---

## **4. PAYLOADBUILDER - CONVERSIÓN (`src/pipeline/pipeline_coordinator.py`)**

### **4.1. Input Schema**
```json
{
  "hechos_extraidos": [
    {
      "id_hecho": 1,
      "vinculado_a_entidades": [2, 3, 5]            // ❌ SIEMPRE VACÍO por el problema anterior
    }
  ]
}
```

### **4.2. Función de Conversión (líneas 651-658)**
```python
# Construcción de entidades_del_hecho para cada hecho
"entidades_del_hecho": [
    {
        "id_temporal_entidad": str(ent_id),         # CONVERSIÓN: int → str
        "nombre": f"Entidad_{ent_id}",              # ❌ NOMBRE GENÉRICO - no real
        "tipo": "MENCIONADA",                       # ❌ TIPO HARDCODED - no real
        "rol_en_hecho": "relacionada"               # ❌ ROL HARDCODED - no real
    } for ent_id in hecho.vinculado_a_entidades     # ❌ LISTA VACÍA
]
```

### **4.3. Output Schema Final [ACTUALIZADO 2025-01-21]**
```json
{
  "hechos_extraidos": [
    {
      "id_temporal": "1",                           // ACTUALIZADO: sin sufijo _hecho
      "contenido": "El presidente anunció medidas",  // ACTUALIZADO: contenido en lugar de descripcion_hecho
      "entidades_del_hecho": []                      // ❌ SIEMPRE VACÍO por el problema
    }
  ]
}
```

---

## **5. RPC SUPABASE - PERSISTENCIA (`actualizar_articulo_procesado.sql`)**

### **5.1. Input Schema Esperado [ACTUALIZADO 2025-01-21]**
```json
{
  "hechos_extraidos": [
    {
      "id_temporal": "1",                          // ACTUALIZADO: sin sufijo _hecho
      "contenido": "El presidente anunció medidas", // ACTUALIZADO: campo contenido
      "tipo_hecho": "ANUNCIO",                     // ACTUALIZADO: campos alineados con RPC
      "importancia": 8,                             // ACTUALIZADO: importancia en lugar de relevancia
      "entidades_del_hecho": [
        {
          "id_temporal_entidad": "2",                // ✅ RPC busca id_temporal_entidad
          "tipo_relacion": "protagonista",           // ✅ RPC busca tipo_relacion
          "relevancia_en_hecho": 9                   // ✅ RPC busca relevancia_en_hecho
        }
      ]
    }
  ]
}
```

### **5.2. Procesamiento de Relaciones (líneas 221-250)**
```sql
-- Procesar entidades del hecho
IF v_hecho ? 'entidades_del_hecho' THEN
    FOR v_entidad IN SELECT * FROM jsonb_array_elements(v_hecho->'entidades_del_hecho')
    LOOP
        -- Obtener ID real de la entidad
        v_entidad_id := (temp_entidad_id_map->>(v_entidad->>'id_temporal_entidad'))::BIGINT;
        
        IF v_entidad_id IS NOT NULL THEN
            -- Insertar relación hecho-entidad
            INSERT INTO hecho_entidad (
                hecho_id,
                fecha_ocurrencia_hecho,
                entidad_id,
                tipo_relacion,
                relevancia_en_hecho
            )
            VALUES (
                v_hecho_id,                          -- ID real del hecho
                v_fecha_ocurrencia_hecho,            -- TSTZRANGE del hecho
                v_entidad_id,                        -- ID real de la entidad (lookup)
                COALESCE(v_entidad->>'tipo_relacion', 'mencionada'), -- ✅ Default: mencionada
                COALESCE((v_entidad->>'relevancia_en_hecho')::INTEGER, 5) -- ✅ Default: 5
            )
            ON CONFLICT (hecho_id, fecha_ocurrencia_hecho, entidad_id, tipo_relacion) 
            DO NOTHING;
        END IF;
    END LOOP;
END IF;
```

### **5.3. Tabla Supabase Schema Real**
```sql
CREATE TABLE hecho_entidad (
    hecho_id BIGINT NOT NULL,                        -- ✅ Campo real: hecho_id
    fecha_ocurrencia_hecho TSTZRANGE NOT NULL,       -- ✅ Campo real: fecha_ocurrencia_hecho
    entidad_id BIGINT NOT NULL REFERENCES entidades(id), -- ✅ Campo real: entidad_id
    tipo_relacion VARCHAR(50) NOT NULL,              -- ✅ Campo real: tipo_relacion
    relevancia_en_hecho INTEGER NOT NULL DEFAULT 5,  -- ✅ Campo real: relevancia_en_hecho
    PRIMARY KEY (hecho_id, fecha_ocurrencia_hecho, entidad_id, tipo_relacion)
);
```

**CHECK constraints:**
- `tipo_relacion IN ('protagonista', 'mencionado', 'afectado', 'declarante', 'ubicacion', 'contexto', 'victima', 'agresor', 'organizador', 'participante', 'otro')`
- `relevancia_en_hecho BETWEEN 1 AND 10`

---

## **6. FLUJO COMPLETO - DONDE SE ROMPE**

### **6.1. Flujo Actual (ROTO)**
```
1. Fase 4: Extrae hechos con vinculado_a_entidades = []
2. Fase 7B.1: Detecta relaciones hecho-entidad correctamente
3. ❌ FALLA: NO asigna relaciones a hecho.vinculado_a_entidades
4. PayloadBuilder: Lee vinculado_a_entidades vacío
5. RPC: No inserta ninguna relación hecho_entidad
6. BD: Tabla hecho_entidad queda VACÍA
```

### **6.2. Flujo Esperado (CORRECTO)**
```
1. Fase 4: Extrae hechos
2. Fase 7B.1: Detecta relaciones hecho-entidad
3. ✅ Asigna relaciones a cada hecho.vinculado_a_entidades
4. PayloadBuilder: Construye entidades_del_hecho con datos reales
5. RPC: Inserta relaciones en hecho_entidad
6. BD: Tabla hecho_entidad poblada correctamente
```

---

## **7. TRANSFORMACIONES NECESARIAS**

### **7.1. Asignación de Relaciones a Hechos**
```python
# DESPUÉS de Fase 7B.1
def asignar_relaciones_detectadas(resultado_normalizacion):
    relaciones = resultado_normalizacion.metadata_normalizacion.relaciones_completas
    hecho_entidad_rels = relaciones.relaciones_estructurales.hecho_entidad
    
    for rel in hecho_entidad_rels:
        hecho = buscar_hecho_por_id(rel["hecho_id"])
        if hecho:
            hecho.vinculado_a_entidades.append(rel["entidad_id"])
```

### **7.2. PayloadBuilder Mejorado**
```python
# EN VEZ DE nombres/tipos genéricos, usar datos reales
def construir_entidades_del_hecho(hecho, entidades_disponibles, relaciones):
    entidades_del_hecho = []
    
    # Buscar relaciones de este hecho en metadata
    for rel in relaciones.hecho_entidad:
        if rel["hecho_id"] == hecho.id_hecho:
            entidad = buscar_entidad_por_id(entidades_disponibles, rel["entidad_id"])
            if entidad:
                entidades_del_hecho.append({
                    "id_temporal_entidad": str(entidad.id_entidad),
                    "nombre_entidad": entidad.texto_entidad,        # NOMBRE REAL
                    "tipo_entidad": entidad.tipo_entidad,           # TIPO REAL
                    "tipo_relacion": rel["tipo_relacion"],          # RELACIÓN REAL
                    "relevancia_en_hecho": rel["relevancia_en_hecho"] # RELEVANCIA REAL
                })
    
    return entidades_del_hecho
```

---

## **8. MAPEO COMPLETO DE TRANSFORMACIONES**

### **8.1. Transformación de IDs**
```
LLM Response         → Fase 7B.1           → Asignación (FALTA)    → PayloadBuilder
===============      =================     ====================    ================
"hecho_id": 1     → hecho_id: 1         → vinculado_a_entidades: [2,3] → "id_temporal_hecho": "1"
"entidad_id": 2   → entidad_id: 2       → append(2)                     → "id_temporal_entidad": "2"
```

### **8.2. Transformación de Relaciones**
```
LLM Response                    → Metadata Storage              → PayloadBuilder (ACTUAL)
===========================     =============================   ========================
"tipo_relacion": "protagonista" → relaciones_completas.hecho_entidad → "tipo": "MENCIONADA" ❌
"relevancia_en_hecho": 9        → almacenado correctamente          → "rol_en_hecho": "relacionada" ❌
```

---

## **9. INCONSISTENCIAS CRÍTICAS IDENTIFICADAS**

### **9.1. Ruptura Total del Flujo ❌**
- Relaciones detectadas en Fase 7B.1 NO se asignan a hechos
- Campo `vinculado_a_entidades` siempre vacío
- PayloadBuilder genera datos genéricos/hardcoded en lugar de reales

### **9.2. Pérdida de Información Rica ❌**
- `tipo_relacion` específico (protagonista, afectado, etc.) → se pierde
- `relevancia_en_hecho` real → se pierde
- Nombres y tipos reales de entidades → reemplazados por genéricos

### **9.3. Schema Mismatch en PayloadBuilder ❌**

| **Campo LLM** | **Campo PayloadBuilder** | **Campo RPC** | **Status** |
|--------------|-------------------------|----------------|------------|
| N/A | `nombre` | N/A | NO USADO |
| N/A | `tipo` | N/A | NO USADO |
| N/A | `rol_en_hecho` | N/A | NO USADO |
| `tipo_relacion` | ❌ NO MAPEADO | `tipo_relacion` ✅ | PERDIDO |
| `relevancia_en_hecho` | ❌ NO MAPEADO | `relevancia_en_hecho` ✅ | PERDIDO |

---

## **10. SOLUCIÓN REQUERIDA**

### **10.1. Implementar Asignación Post-Fase 7B.1**
```python
# En pipeline_coordinator.py o fase_7b_relaciones.py
def procesar_relaciones_detectadas(resultado_normalizacion, hechos, entidades):
    """Asigna las relaciones detectadas a los objetos correspondientes"""
    relaciones = resultado_normalizacion.metadata_normalizacion.relaciones_completas
    
    # Procesar hecho_entidad
    for rel in relaciones.relaciones_estructurales.hecho_entidad:
        hecho = next((h for h in hechos if h.id_hecho == rel["hecho_id"]), None)
        if hecho:
            hecho.vinculado_a_entidades.append(rel["entidad_id"])
            # También guardar metadata de la relación para PayloadBuilder
            hecho.metadata_relaciones = getattr(hecho, 'metadata_relaciones', {})
            hecho.metadata_relaciones[rel["entidad_id"]] = {
                "tipo_relacion": rel["tipo_relacion"],
                "relevancia_en_hecho": rel["relevancia_en_hecho"]
            }
```

### **10.2. Corregir PayloadBuilder**
```python
# Usar EntidadEnHechoItem correctamente
"entidades_del_hecho": [
    {
        "id_temporal_entidad": str(entidad.id_entidad),
        "tipo_relacion": metadata_rel.get("tipo_relacion", "mencionada"),
        "relevancia_en_hecho": metadata_rel.get("relevancia_en_hecho", 5)
    }
    for entidad_id in hecho.vinculado_a_entidades
    if (metadata_rel := hecho.metadata_relaciones.get(entidad_id))
]
```

### **10.3. Actualizar Modelo EntidadEnHechoItem**
```python
# Simplificar modelo para coincidir con RPC
class EntidadEnHechoItem(PersistenciaBaseModel):
    id_temporal_entidad: str
    tipo_relacion: Optional[str] = "mencionada"
    relevancia_en_hecho: Optional[int] = Field(5, ge=1, le=10)
    # REMOVER: nombre_entidad, tipo_entidad, rol_en_hecho (no usados)
```

**CONCLUSIÓN**: El schema está bien diseñado pero el **FLUJO ESTÁ COMPLETAMENTE ROTO**. Las relaciones se detectan correctamente pero nunca se asignan a los hechos, resultando en pérdida total de relaciones hecho-entidad.