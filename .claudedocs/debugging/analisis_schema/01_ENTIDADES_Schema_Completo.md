# **ANÁLISIS COMPLETO: SCHEMA ENTIDADES**

## **RESUMEN EJECUTIVO**

Schema de entidades mapeado completamente en TODAS las etapas del pipeline. Se identifican **3 transformaciones principales** y **múltiples inconsistencias** en nombres de campos.

**⚠️ ACTUALIZACIÓN IMPORTANTE**: El RPC `actualizar_articulo_procesado.sql` fue actualizado para eliminar sufijos `_entidad` de los campos. Ahora es la **FUENTE DE VERDAD ABSOLUTA** para evaluar mismatches. PayloadBuilder y Procesamiento aún tienen campos con sufijos que NO coinciden con el RPC actualizado.

---

## **1. MODELOS PYDANTIC - ENTRADA**

### **1.1. MetadatosEntidad (`src/module_pipeline/src/models/metadatos.py`)**

```json
{
  "tipo": "PERSONA",                                  // String con patrón regex
  "alias": ["alias1", "alias2"],                      // List[str] default=[]
  "fecha_nacimiento": "2023-03-14",                   // String YYYY-MM-DD opcional
  "fecha_disolucion": "2023-03-14",                   // String YYYY-MM-DD opcional
  "descripcion_estructurada": ["punto1", "punto2"]   // List[str] separados por guiones
}
```

**Tipos permitidos:** `PERSONA|ORGANIZACION|INSTITUCION|LUGAR|EVENTO|NORMATIVA|CONCEPTO`

### **1.2. EntidadBase (`src/module_pipeline/src/models/procesamiento.py`)**

```json
{
  "id_entidad": 1,                                    // int - ID secuencial
  "texto_entidad": "Nicolás Maduro",                  // str - Nombre de la entidad
  "tipo_entidad": "PERSONA",                          // str - Tipo validado
  "relevancia_entidad": 0.8,                          // float 0.0-1.0
  "offset_inicio_entidad": 100,                       // Optional[int] posición en texto
  "offset_fin_entidad": 115,                          // Optional[int] posición en texto
  "metadata_entidad": MetadatosEntidad                // Object arriba definido
}
```

### **1.3. EntidadProcesada (`src/module_pipeline/src/models/procesamiento.py`)**

```json
{
  // Hereda todos los campos de EntidadBase +
  "id_fragmento_origen": "ART-123",                   // str - ID del fragmento
  "id_entidad_normalizada": "ENT-456",               // Optional[str] ID en BD
  "nombre_entidad_normalizada": "Nicolás Maduro Oficial", // Optional[str] nombre canónico
  "uri_wikidata": "https://wikidata.org/123",        // Optional[HttpUrl]
  "similitud_normalizacion": 0.95,                   // Optional[float] score
  "prompt_utilizado_normalizacion": "prompt_text"    // Optional[str] debug info
}
```

---

## **2. PROMPTS LLM - SCHEMA ESPERADO**

### **2.1. Prompt Principal (`prompts/Entidades.md`)**

```json
{
  "entidades": [
    {
      "id": 1,                                        // int - ID secuencial único
      "nombre": "Nicolás Maduro",                     // str - Nombre canónico
      "alias": [],                                    // Array[str] - Nombres alternativos
      "tipo": "PERSONA",                              // str - Enum específico
      "descripcion": "- presidente de Venezuela",     // str - Formato con guiones
      "fecha_nacimiento": null,                       // str YYYY-MM-DD o null
      "fecha_disolucion": null                        // str YYYY-MM-DD o null
    }
  ]
}
```

**Tipos permitidos exactos:**
- `PERSONA`
- `ORGANIZACION` 
- `INSTITUCION`
- `LUGAR`
- `EVENTO`
- `NORMATIVA`
- `CONCEPTO`

---

## **3. FASE 3 - PROCESAMIENTO (`src/pipeline/fase_3_entidades.py`)**

### **3.1. Input Schema**
```json
{
  "texto_simplificado": "contenido del artículo procesado en Fase 2"
}
```

### **3.2. Output Schema**
```json
{
  "entidades_extraidas": [
    {
      "id_entidad": 1,
      "texto_entidad": "Nicolás Maduro",
      "tipo_entidad": "PERSONA",
      "relevancia_entidad": 0.8,
      "offset_inicio_entidad": 100,
      "offset_fin_entidad": 115,
      "id_fragmento_origen": "ART-123",
      "metadata_entidad": {
        "tipo": "PERSONA",
        "alias": ["Maduro"],
        "fecha_nacimiento": "1962-11-23",
        "fecha_disolucion": null,
        "descripcion_estructurada": ["presidente de Venezuela"]
      }
    }
  ]
}
```

### **3.3. Función de Conversión**
```python
def _procesar_entidades_extraidas(entidades_raw, id_fragmento, fragment_processor):
    for entidad in entidades_raw:
        metadatos = MetadatosEntidad(
            tipo=entidad.get("tipo", "DESCONOCIDO"),
            alias=entidad.get("alias", []),
            fecha_nacimiento=entidad.get("fecha_nacimiento"),
            fecha_disolucion=entidad.get("fecha_disolucion"),
            descripcion_estructurada=entidad.get("descripcion", "").split(" - ")
        )
        
        entidad_procesada = EntidadProcesada(
            id_entidad=entidad.get("id", 0),
            texto_entidad=entidad.get("nombre", ""),           # MAPEO: nombre → texto_entidad
            tipo_entidad=entidad.get("tipo", "DESCONOCIDO"),   # MAPEO: tipo → tipo_entidad
            relevancia_entidad=0.8,
            id_fragmento_origen=id_fragmento,
            metadata_entidad=metadatos
        )
```

---

## **4. FASE 7 - NORMALIZACIÓN (`src/pipeline/fase_7_normalizacion.py`)**

### **4.1. Input Schema**
```json
{
  "entidades_extraidas": "Array de EntidadProcesada de Fase 3"
}
```

### **4.2. EntityNormalizer Input/Output**
```python
# Input a normalizar_entidad()
{
    "nombre_entidad": "Juan Pérez",
    "tipo_entidad": "PERSONA",
    "umbral_propio": 0.7
}

# Output de normalización
{
    "id_entidad_normalizada": 123,
    "nombre_normalizado": "Juan Pérez Oficial", 
    "tipo_normalizado": "PERSONA",
    "score_similitud": 0.95,
    "es_nueva": False
}
```

### **4.3. Output Schema Final**
```json
{
  "entidades_normalizadas": [
    {
      // Todos los campos de EntidadProcesada +
      "id_entidad_normalizada": "123",
      "nombre_entidad_normalizada": "Nicolás Maduro Oficial",
      "similitud_normalizacion": 0.95,
      "uri_wikidata": "https://wikidata.org/entity/Q58132",
      "prompt_utilizado_normalizacion": "normalización automática"
    }
  ]
}
```

---

## **5. PAYLOADBUILDER - CONVERSIÓN FINAL (`src/services/payload_builder.py`)**

### **5.1. Input Schema**
```json
{
  "entidades_autonomas_data": "Array de EntidadProcesada normalizadas"
}
```

### **5.2. Función de Conversión**
```python
def construir_payload_articulo_from_model():
    if entidades_autonomas_data is not None:
        payload_data["entidades_autonomas"] = [
            EntidadAutonomaItem(**item) for item in entidades_autonomas_data
        ]
```

### **5.3. EntidadAutonomaItem Schema (`src/models/persistencia.py`)**

```json
{
  // CAMPOS PRINCIPALES (coinciden con BD Supabase)
  "id": "ENT-123",                                    // str - UUID único
  "nombre": "Nicolás Maduro",                         // str - Nombre final
  "tipo": "PERSONA",                                  // str - Tipo final
  "descripcion": "presidente de Venezuela",           // Optional[str]
  "alias": ["Maduro", "Nicolás"],                     // List[str] default=[]
  "fecha_nacimiento": "1962-11-23",                   // Optional[str] YYYY-MM-DD
  "fecha_disolucion": null,                           // Optional[str] YYYY-MM-DD
  
  // CAMPOS ADICIONALES (lógica de negocio)
  "relevancia_entidad_articulo": 8,                   // Optional[int] 1-10
  "metadata_entidad": {},                             // Dict[str, Any] default={}
  "embedding_entidad_vector": [0.1, 0.2, 0.3],       // Optional[List[float]]
  
  // CAMPOS DEPRECATED (compatibilidad temporal)
  "id_temporal_entidad": "temp-123",                  // Optional[str] DEPRECATED
  "nombre_entidad": "Nicolás Maduro",                 // Optional[str] DEPRECATED  
  "tipo_entidad": "PERSONA"                           // Optional[str] DEPRECATED
}
```

---

## **6. RPC SUPABASE - PERSISTENCIA (`actualizar_articulo_procesado.sql`) [ACTUALIZADO]**

### **6.1. Input Schema Esperado (DESPUÉS DE ACTUALIZACIÓN)**
```json
{
  "entidades_autonomas": [
    {
      "id": "ENT-123",
      "nombre": "Nicolás Maduro",                      // RPC ahora espera: nombre
      "tipo": "PERSONA",                              // RPC ahora espera: tipo
      "descripcion": "presidente de Venezuela",        // RPC ahora espera: descripcion
      "alias": ["Maduro"],                            // RPC ahora espera: alias
      "relevancia": 8,                                // RPC ahora espera: relevancia
      "metadata": {},                                 // RPC ahora espera: metadata
      "id_temporal": "1"                              // Para mapeo interno
    }
  ]
}
```

### **6.2. Mapeo de Campos en RPC ACTUALIZADO (líneas 122-131)**
```sql
INSERT INTO entidades (
    nombre,                                          -- Mapea de: nombre
    tipo,                                            -- Mapea de: tipo
    descripcion,                                     -- Mapea de: descripcion
    alias,                                           -- Mapea de: alias (array)
    relevancia,                                      -- Mapea de: relevancia
    metadata                                         -- Mapea de: metadata
)
VALUES (
    v_entidad->>'nombre',                            -- Busca: nombre
    v_entidad->>'tipo',                              -- Busca: tipo
    v_entidad->>'descripcion',                       -- Busca: descripcion
    CASE WHEN v_entidad ? 'alias' THEN ARRAY(...),
    COALESCE((v_entidad->>'relevancia')::INTEGER, 5), -- Busca: relevancia
    v_entidad->'metadata'                            -- Busca: metadata
)
```

### **6.3. Tabla Supabase Schema Real**
```sql
CREATE TABLE entidades (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(300) NOT NULL,                    -- ✅ Campo real: nombre
    tipo VARCHAR(50) NOT NULL,                       -- ✅ Campo real: tipo
    descripcion TEXT,                                -- ✅ Campo real: descripcion
    alias TEXT[],                                    -- ✅ Campo real: alias
    relevancia INTEGER NOT NULL DEFAULT 5,          -- ✅ Campo real: relevancia
    metadata JSONB                                   -- ✅ Campo real: metadata
);
```

---

## **7. REFERENCIAS CRUZADAS - OTROS SCHEMAS**

### **7.1. Datos Cuantitativos (`prompts/Datos.md`)**
```json
{
  "datos_cuantitativos": [
    {
      "id": 1,
      "hecho_id": 0,
      "entidad_relacionada_id": 3,                    // ❌ REFERENCIA: Busca entidad por ID secuencial
      "indicador": "Crecimiento del PIB",
      "categoria": "económico",
      "valor": 3.5,
      "unidad": "porcentaje"
    }
  ]
}
```

### **7.2. Citas Textuales (`prompts/Citas.md`)**
```json
{
  "citas_textuales": [
    {
      "id": 1,
      "cita": "Estamos viendo una desaceleración...",
      "entidad_id": 3,                                // ❌ REFERENCIA: Busca entidad por ID secuencial
      "hecho_id": 2,
      "fecha": "2023-03-14",
      "contexto": "Declarado en rueda de prensa",
      "relevancia": 4
    }
  ]
}
```

---

## **8. VALIDACIONES (`src/utils/schema_validator.py`)**

### **8.1. TipoEntidad Enum**
```python
class TipoEntidad(str, Enum):
    PERSONA = "PERSONA"
    ORGANIZACION = "ORGANIZACION" 
    INSTITUCION = "INSTITUCION"
    LUGAR = "LUGAR"
    EVENTO = "EVENTO"
    NORMATIVA = "NORMATIVA"
    CONCEPTO = "CONCEPTO"
```

### **8.2. Validaciones Aplicadas**
```python
def validar_entidades(self, entidades: List[Dict[str, Any]]) -> bool:
    for entidad in entidades:
        # 1. Validar ID secuencial único
        if not self.validar_id_secuencial(entidad["id"], "entidades"):
            return False
            
        # 2. Validar tipo enum
        if entidad["tipo"] not in [t.value for t in TipoEntidad]:
            self.errores.append(f"Tipo inválido: {entidad['tipo']}")
            return False
            
        # 3. Validar fechas YYYY-MM-DD
        for campo_fecha in ["fecha_nacimiento", "fecha_disolucion"]:
            if not self.validar_fecha(entidad[campo_fecha], campo_fecha):
                return False
```

---

## **9. MAPEO COMPLETO DE TRANSFORMACIONES**

### **9.1. Transformación de IDs**
```
LLM Response         → Procesamiento      → PayloadBuilder      → RPC Supabase
===============      =================   ===================   ================
"id": 1 (int)     → id_entidad: 1      → "id": "ENT-123"     → BIGSERIAL id (BD)
                  → id_temporal: "1"    → id_temporal: "1"    → [mapping interno]
```

### **9.2. Transformación de Nombres de Campos**
```
LLM Response         → Procesamiento         → PayloadBuilder         → RPC Supabase
===============      ===================     =====================    ================
"nombre": "Juan"  → texto_entidad: "Juan"  → "nombre": "Juan"       → nombre_entidad ❌
"tipo": "PERSONA" → tipo_entidad: "PERSONA"→ "tipo": "PERSONA"      → tipo_entidad ❌
                  → metadata_entidad: {}   → "metadata_entidad": {} → metadata_entidad ❌
```

### **9.3. Transformación de Metadatos**
```
LLM Response              → MetadatosEntidad           → Dict[str, Any]
=================         ========================      ==================
"alias": ["JP"]        → alias: ["JP"]              → metadata: {"aliases": [...]}
"descripcion": "- doc" → descripcion_estructurada   → "descripcion": "doc"
"fecha_nacimiento"     → fecha_nacimiento: "YYYY"   → "fecha_nacimiento": "YYYY"
```

---

## **10. INCONSISTENCIAS CRÍTICAS IDENTIFICADAS (CON RPC ACTUALIZADO COMO FUENTE DE VERDAD)**

### **10.1. Problema Principal: Field Name Mismatch**

| **Etapa** | **Campo Nombre** | **Campo Tipo** | **Campo Descripción** | **Campo Relevancia** | **Campo Metadata** |
|-----------|------------------|----------------|----------------------|---------------------|-------------------|
| LLM Response | `nombre` | `tipo` | `descripcion` | - | - |
| Procesamiento | `texto_entidad` ❌ | `tipo_entidad` ❌ | `metadata_entidad.descripcion_estructurada` ❌ | `relevancia_entidad` ❌ | `metadata_entidad` ❌ |
| PayloadBuilder | `nombre` ✅ | `tipo` ✅ | `descripcion` ✅ | `relevancia_entidad_articulo` ❌ | `metadata_entidad` ❌ |
| RPC ACTUALIZADO | `nombre` ✅ | `tipo` ✅ | `descripcion` ✅ | `relevancia` ✅ | `metadata` ✅ |
| Tabla BD | `nombre` ✅ | `tipo` ✅ | `descripcion` ✅ | `relevancia` ✅ | `metadata` ✅ |

### **10.2. Mismatches Específicos con RPC Actualizado**
- **Procesamiento**: Usa sufijo `_entidad` en TODOS los campos ❌
- **PayloadBuilder campos principales**: `nombre`, `tipo`, `descripcion` ✅ ALINEADOS
- **PayloadBuilder campos adicionales**: 
  - Envía `relevancia_entidad_articulo` pero RPC espera `relevancia` ❌
  - Envía `metadata_entidad` pero RPC espera `metadata` ❌
- **PayloadBuilder campos deprecated**: Aún contiene `nombre_entidad`, `tipo_entidad` ❌

### **10.3. Referencias Cruzadas Inconsistentes**
- Datos y Citas usan IDs secuenciales (1,2,3) en prompts
- PayloadBuilder convierte a UUIDs ("ENT-123")
- No existe mapeo claro entre IDs secuenciales y UUIDs finales

---

## **11. SOLUCIONES PENDIENTES (RPC YA ACTUALIZADO)**

### **11.1. ✅ RPC YA ALINEADO** 
El RPC `actualizar_articulo_procesado.sql` ya fue actualizado para esperar campos sin sufijos:
- `nombre` (antes `nombre_entidad`)
- `tipo` (antes `tipo_entidad`)
- `descripcion` (antes `descripcion_entidad`)
- `relevancia` (antes `relevancia_entidad`)
- `metadata` (antes `metadata_entidad`)

### **11.2. ❌ PENDIENTE: Alinear PayloadBuilder**
```python
# En EntidadAutonomaItem cambiar:
relevancia_entidad_articulo: Optional[int]  # → relevancia: Optional[int]
metadata_entidad: Dict[str, Any]           # → metadata: Dict[str, Any]

# REMOVER campos DEPRECATED:
id_temporal_entidad: Optional[str] = None    # ELIMINAR
nombre_entidad: Optional[str] = None         # ELIMINAR
tipo_entidad: Optional[str] = None           # ELIMINAR
```

### **11.3. ❌ PENDIENTE: Alinear Procesamiento**
```python
# En fase_3_entidades.py cambiar mapeos:
texto_entidad → nombre
tipo_entidad → tipo
metadata_entidad → metadata
relevancia_entidad → relevancia
```

### **11.4. ❌ PENDIENTE: Implementar ID Mapping**
```python
def crear_mapeo_ids_secuenciales_a_uuids(entidades_procesadas):
    """Crear mapeo para referencias cruzadas en datos y citas"""
    mapeo = {}
    for idx, entidad in enumerate(entidades_procesadas, 1):
        mapeo[idx] = entidad.id  # idx secuencial → UUID final
    return mapeo
```

**FUENTE DE VERDAD ACTUAL**: RPC `actualizar_articulo_procesado.sql` con campos sin sufijos.