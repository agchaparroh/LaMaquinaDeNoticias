# **ANÁLISIS COMPLETO: SCHEMA HECHOS**

## **RESUMEN EJECUTIVO**

Schema de hechos mapeado completamente en TODAS las etapas del pipeline. Se identifican **4 transformaciones principales** con múltiples inconsistencias en nombres de campos y estructuras de fechas.

**⚠️ ACTUALIZACIÓN IMPORTANTE**: El RPC `actualizar_articulo_procesado.sql` fue actualizado. Ahora es la **FUENTE DE VERDAD ABSOLUTA** para evaluar mismatches. PayloadBuilder envía campos que NO coinciden completamente con el RPC actualizado.

---

## **1. MODELOS PYDANTIC - ENTRADA**

### **1.1. MetadatosHecho (`src/module_pipeline/src/models/metadatos.py`)**

```json
{
  "precision_temporal": "exacta",                     // Optional[str] - enum específico
  "tipo_hecho": "SUCESO",                            // Optional[str] - enum específico  
  "pais": ["España", "Francia"],                     // List[str] default=[]
  "region": ["Cataluña", "Ile-de-France"],           // List[str] default=[]
  "ciudad": ["Barcelona", "París"],                  // List[str] default=[]
  "es_futuro": false,                                // Optional[bool]
  "estado_programacion": "confirmado",               // Optional[str] - enum específico
  "fecha_inicio": "2023-03-14",                      // Optional[str] YYYY-MM-DD
  "fecha_fin": "2023-03-15"                          // Optional[str] YYYY-MM-DD
}
```

**Enums precisos:**
- **precision_temporal:** `exacta|dia|semana|mes|trimestre|año|decada|periodo|indefinido`
- **tipo_hecho:** `SUCESO|ANUNCIO|DECLARACION|BIOGRAFIA|CONCEPTO|NORMATIVA|EVENTO`
- **estado_programacion:** `programado|confirmado|cancelado|modificado|realizado`

### **1.2. HechoProcesado (`src/module_pipeline/src/models/procesamiento.py`)**

```json
{
  "id_hecho": 1,                                     // int - ID secuencial
  "texto_original_del_hecho": "El presidente anunció nuevas medidas", // str - Texto extraído
  "confianza_extraccion": 0.9,                       // float 0.0-1.0
  "offset_inicio_hecho": 150,                        // Optional[int] posición en texto
  "offset_fin_hecho": 200,                           // Optional[int] posición final
  "id_fragmento_origen": "ART-123",                  // str - ID del fragmento
  "id_articulo_fuente": "456",                       // Optional[str] ID artículo
  "vinculado_a_entidades": [1, 3, 5],                // List[int] IDs entidades relacionadas
  "prompt_utilizado": "prompt_hechos_v3.md",         // Optional[str] debug info
  "respuesta_llm_bruta": {},                         // Optional[Dict] respuesta completa
  "metadata_hecho": MetadatosHecho                   // Object definido arriba
}
```

### **1.3. HechoExtraidoItem (`src/module_pipeline/src/models/persistencia.py`) [ACTUALIZADO 2025-01-21]**

```json
{
  // CAMPOS PRINCIPALES (esperados por RPC)
  "id_temporal": "1",                                // str - ID temporal único
  "contenido": "El presidente anunció nuevas medidas", // str - Contenido/descripción del hecho
  "tipo_hecho": "ANUNCIO",                           // Optional[str] tipo
  "fecha_ocurrencia_inicio": "2023-03-14T10:00:00Z", // Optional[str] ISO 8601
  "fecha_ocurrencia_fin": "2023-03-14T12:00:00Z",    // Optional[str] ISO 8601
  "importancia": 8,                                  // Optional[int] 1-10
  "precision_temporal": "exacta",                    // Optional[str] enum (nivel raíz)
  "metadata": {                                      // Optional[Dict] metadatos adicionales
    "pais": ["Venezuela"],
    "region": ["Caracas Capital"],
    "ciudad": ["Caracas"],
    "etiquetas": ["economía", "gobierno"]
  },
  
  // CAMPOS ADICIONALES (no procesados por RPC pero útiles para lógica interna)
  "subtipo_hecho": "gubernamental",                  // Optional[str] subtipo
  "lugar_ocurrencia_hecho": "Caracas, Venezuela",   // Optional[str] lugar
  "contexto_adicional_hecho": "Rueda de prensa matinal", // Optional[str]
  "es_evento_futuro": false,                         // Optional[bool]
  "estado_programacion": "realizado",                // Optional[str] enum
  "detalle_complejo_hecho": {},                      // Optional[Dict[str, Any]]
  "embedding_hecho_vector": [0.1, 0.2, 0.3],        // Optional[List[float]]
  "entidades_del_hecho": [EntidadEnHechoItem]        // Optional[List] relaciones
}
```

---

## **2. PROMPTS LLM - SCHEMA ESPERADO**

### **2.1. Prompt Principal (`prompts/Hechos.md`)**

```json
{
  "hechos": [
    {
      "id": 1,                                       // int - ID secuencial único
      "contenido": "El presidente Nicolás Maduro anunció nuevas medidas económicas", // str
      "fecha_inicio": "2023-03-14",                  // str YYYY-MM-DD
      "fecha_fin": "2023-03-14",                     // str YYYY-MM-DD o null
      "precision_temporal": "exacta",                // str - enum específico
      "tipo_hecho": "ANUNCIO",                       // str - enum específico
      "pais": ["Venezuela"],                         // Array[str] países
      "region": ["Caracas Capital"],                 // Array[str] regiones
      "ciudad": ["Caracas"],                         // Array[str] ciudades
      "es_futuro": false,                            // boolean
      "estado_programacion": null                    // str enum o null
    }
  ]
}
```

**Enums permitidos exactos:**
- **precision_temporal:** `exacta`, `dia`, `semana`, `mes`, `trimestre`, `año`, `decada`, `periodo`
- **tipo_hecho:** `SUCESO`, `ANUNCIO`, `DECLARACION`, `BIOGRAFIA`, `CONCEPTO`, `NORMATIVA`, `EVENTO`
- **estado_programacion:** `programado`, `confirmado`, `cancelado`, `modificado`, `realizado`

---

## **3. FASE 4 - PROCESAMIENTO (`src/pipeline/fase_4_hechos.py`)**

### **3.1. Input Schema**
```json
{
  "texto_simplificado": "contenido del artículo procesado y entidades extraídas en fases anteriores"
}
```

### **3.2. Output Schema**
```json
{
  "hechos_extraidos": [
    {
      "id_hecho": 1,
      "texto_original_del_hecho": "El presidente anunció nuevas medidas",
      "confianza_extraccion": 0.9,
      "offset_inicio_hecho": 150,
      "offset_fin_hecho": 200,
      "id_fragmento_origen": "ART-123",
      "id_articulo_fuente": "456",
      "vinculado_a_entidades": [1, 3],
      "prompt_utilizado": "prompt_hechos_v3.md",
      "respuesta_llm_bruta": {},
      "metadata_hecho": {
        "precision_temporal": "exacta",
        "tipo_hecho": "ANUNCIO",
        "pais": ["Venezuela"],
        "region": ["Caracas Capital"],
        "ciudad": ["Caracas"],
        "es_futuro": false,
        "estado_programacion": null,
        "fecha_inicio": "2023-03-14",
        "fecha_fin": "2023-03-14"
      }
    }
  ]
}
```

### **3.3. Función de Conversión**
```python
def _procesar_hechos_extraidos(hechos_raw, id_fragmento, fragment_processor):
    for hecho in hechos_raw:
        # Convertir fechas
        fecha_inicio = hecho.get("fecha_inicio")
        fecha_fin = hecho.get("fecha_fin", fecha_inicio)
        
        metadatos = MetadatosHecho(
            tipo_hecho=hecho.get("tipo_hecho", "SUCESO"),        # MAPEO: tipo_hecho → tipo_hecho
            precision_temporal=hecho.get("precision_temporal", "dia"),
            pais=hecho.get("pais", []),
            region=hecho.get("region", []),
            ciudad=hecho.get("ciudad", []),
            es_futuro=hecho.get("es_futuro", False),
            estado_programacion=hecho.get("estado_programacion"),
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        
        hecho_procesado = HechoProcesado(
            id_hecho=hecho.get("id", 0),
            texto_original_del_hecho=hecho.get("contenido", ""), # MAPEO: contenido → texto_original_del_hecho
            confianza_extraccion=0.9,
            id_fragmento_origen=id_fragmento,
            vinculado_a_entidades=[],
            metadata_hecho=metadatos
        )
```

---

## **4. CONSOLIDACIÓN (`src/services/consolidation_service.py`)**

### **4.1. Input Schema (si chunking activo)**
```json
{
  "hechos_por_chunk": [
    [Array_HechoProcesado_chunk_1],
    [Array_HechoProcesado_chunk_2],
    [Array_HechoProcesado_chunk_3]
  ]
}
```

### **4.2. Algoritmo de Consolidación**
```python
def consolidar_hechos(self, hechos_por_chunk):
    """
    Elimina duplicados entre chunks usando:
    - Similitud de texto (texto_original_del_hecho)
    - Comparación de fechas (metadata_hecho.fecha_inicio/fin)
    - Similitud geográfica (pais/region/ciudad)
    """
    # Preserva estructura completa de HechoProcesado
    # Solo elimina duplicados, no modifica campos
```

### **4.3. Output Schema**
```json
{
  "hechos_consolidados": [Array_HechoProcesado_sin_duplicados]
}
```

---

## **5. PAYLOADBUILDER - CONVERSIÓN FINAL (`src/services/payload_builder.py`)**

### **5.1. Input Schema**
```json
{
  "hechos_extraidos_data": "Array de HechoProcesado consolidados"
}
```

### **5.2. Función de Conversión**
```python
def construir_payload_articulo_from_model():
    if hechos_extraidos_data is not None:
        payload_data["hechos_extraidos"] = [
            HechoExtraidoItem(**item) for item in hechos_extraidos_data
        ]
```

### **5.3. Transformación de Campos Críticos**
```python
# HechoProcesado → HechoExtraidoItem
id_hecho                    → id_temporal_hecho (str conversion)
texto_original_del_hecho    → descripcion_hecho  
metadata_hecho.tipo_hecho   → tipo_hecho
metadata_hecho.fecha_inicio → fecha_ocurrencia_hecho_inicio (ISO 8601)
metadata_hecho.fecha_fin    → fecha_ocurrencia_hecho_fin (ISO 8601)
```

### **5.4. Output Schema Final [ACTUALIZADO 2025-01-21]**
```json
{
  "hechos_extraidos": [
    {
      "id_temporal": "1",                            // str conversion de id_hecho
      "contenido": "El presidente anunció nuevas medidas",
      "tipo_hecho": "ANUNCIO",
      "fecha_ocurrencia_inicio": "2023-03-14T00:00:00Z",
      "fecha_ocurrencia_fin": "2023-03-14T23:59:59Z",
      "importancia": 8,
      "precision_temporal": "exacta",
      "metadata": {
        "pais": ["Venezuela"],
        "region": ["Caracas Capital"],
        "ciudad": ["Caracas"],
        "etiquetas": []
      },
      "es_evento_futuro": false,
      "estado_programacion": null,
      "lugar_ocurrencia_hecho": "Caracas, Venezuela",
      "entidades_del_hecho": [
        {
          "id_temporal_entidad": "1",                // ⚠️ REFERENCIA: Busca entidad por ID secuencial
          "tipo_relacion": "protagonista",
          "relevancia_en_hecho": 9
        }
      ]
    }
  ]
}
```

---

## **6. RPC SUPABASE - PERSISTENCIA (`actualizar_articulo_procesado.sql`) [ACTUALIZADO]**

### **6.1. Input Schema Esperado (DESPUÉS DE ACTUALIZACIÓN)**
```json
{
  "hechos_extraidos": [
    {
      "id_temporal": "1",                              // Para mapeo interno
      "contenido": "El presidente anunció nuevas medidas", // RPC ahora espera: contenido
      "tipo_hecho": "ANUNCIO",                         // RPC ahora espera: tipo_hecho
      "fecha_ocurrencia_inicio": "2023-03-14T00:00:00Z", // RPC ahora espera: fecha_ocurrencia_inicio
      "fecha_ocurrencia_fin": "2023-03-14T23:59:59Z",    // RPC ahora espera: fecha_ocurrencia_fin
      "importancia": 8,                                // RPC ahora espera: importancia
      "precision_temporal": "exacta",                  // RPC ahora espera: precision_temporal
      "metadata": {                                    // RPC ahora espera: metadata
        "pais": ["Venezuela"],
        "region": ["Caracas Capital"],
        "ciudad": ["Caracas"],
        "etiquetas": ["economía", "gobierno"]
      }
    }
  ]
}
```

### **6.2. Mapeo de Campos en RPC ACTUALIZADO (líneas 177-196)**
```sql
INSERT INTO hechos (
    contenido,                    -- Mapea de: contenido
    fecha_ocurrencia,            -- Construido de fecha_ocurrencia_inicio/fin
    precision_temporal,          -- Mapea de: precision_temporal
    tipo_hecho,                  -- Mapea de: tipo_hecho
    importancia,                 -- Mapea de: importancia
    pais,                        -- Mapea de: metadata->'pais'
    region,                      -- Mapea de: metadata->'region'  
    ciudad,                      -- Mapea de: metadata->'ciudad'
    etiquetas,                   -- Mapea de: metadata->'etiquetas'
    fecha_ingreso                -- now()
)
VALUES (
    v_hecho->>'contenido',                           -- Busca: contenido
    v_fecha_ocurrencia_hecho,                        -- TSTZRANGE construido
    COALESCE(v_hecho->>'precision_temporal', 'desconocido'), -- Busca: precision_temporal
    COALESCE(v_hecho->>'tipo_hecho', 'SUCESO'),      -- Busca: tipo_hecho
    COALESCE((v_hecho->>'importancia')::INTEGER, 5), -- Busca: importancia
    CASE WHEN v_hecho->'metadata' ? 'pais'           -- Busca: metadata
        THEN ARRAY(...),
    CASE WHEN v_hecho->'metadata' ? 'region'         -- Busca: metadata
        THEN ARRAY(...),
    CASE WHEN v_hecho->'metadata' ? 'ciudad'         -- Busca: metadata
        THEN ARRAY(...),
    now()
)
```

### **6.3. Construcción de TSTZRANGE ACTUALIZADA (líneas 150-161)**
```sql
v_fecha_ocurrencia_hecho := tstzrange(
    CASE 
        WHEN v_hecho ? 'fecha_ocurrencia_inicio' 
        THEN (v_hecho->>'fecha_ocurrencia_inicio')::TIMESTAMPTZ
        ELSE (SELECT fecha_publicacion FROM articulos WHERE id = v_articulo_id)
    END,
    CASE 
        WHEN v_hecho ? 'fecha_ocurrencia_fin' 
        THEN (v_hecho->>'fecha_ocurrencia_fin')::TIMESTAMPTZ
        ELSE (SELECT fecha_publicacion FROM articulos WHERE id = v_articulo_id)
    END
);
```

### **6.4. Tabla Supabase Schema Real**
```sql
CREATE TABLE hechos (
    id BIGSERIAL,
    contenido TEXT NOT NULL,                         -- ✅ Campo real: contenido
    fecha_ocurrencia TSTZRANGE NOT NULL,             -- ✅ Campo real: fecha_ocurrencia
    precision_temporal VARCHAR(20) NOT NULL,         -- ✅ Campo real: precision_temporal
    importancia INTEGER NOT NULL DEFAULT 5,          -- ✅ Campo real: importancia
    tipo_hecho VARCHAR(50) NOT NULL,                 -- ✅ Campo real: tipo_hecho
    pais VARCHAR(100)[] NOT NULL,                    -- ✅ Campo real: pais
    region VARCHAR(100)[],                           -- ✅ Campo real: region
    ciudad VARCHAR(100)[],                           -- ✅ Campo real: ciudad
    etiquetas TEXT[],                                -- ✅ Campo real: etiquetas
    es_evento_futuro BOOLEAN DEFAULT false,          -- ✅ Campo real: es_evento_futuro
    estado_programacion VARCHAR(50),                 -- ✅ Campo real: estado_programacion
    fecha_ingreso TIMESTAMP WITH TIME ZONE DEFAULT now()
) PARTITION BY RANGE (lower(fecha_ocurrencia));
```

---

## **7. REFERENCIAS CRUZADAS - OTROS SCHEMAS**

### **7.1. Datos Cuantitativos (`prompts/Datos.md`)**
```json
{
  "datos_cuantitativos": [
    {
      "id": 1,
      "hecho_id": 2,                                 // ❌ REFERENCIA: Busca hecho por ID secuencial
      "entidad_relacionada_id": 3,
      "indicador": "Inflación anual",
      "categoria": "económico",
      "valor": 15.2,
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
      "cita": "Implementaremos medidas inmediatas",
      "entidad_id": 1,
      "hecho_id": 2,                                 // ❌ REFERENCIA: Busca hecho por ID secuencial
      "fecha": "2023-03-14",
      "contexto": "Declarado durante rueda de prensa",
      "relevancia": 8
    }
  ]
}
```

### **7.3. Entidades en Hechos (`prompts/Hechos.md` implícito)**
```json
{
  "entidades_del_hecho": [
    {
      "id_temporal_entidad": "1",                    // ❌ REFERENCIA: ID secuencial como string
      "tipo_relacion": "protagonista",
      "relevancia_en_hecho": 9
    }
  ]
}
```

---

## **8. VALIDACIONES (`src/utils/schema_validator.py`)**

### **8.1. TipoHecho Enum**
```python
class TipoHecho(str, Enum):
    SUCESO = "SUCESO"
    ANUNCIO = "ANUNCIO"
    DECLARACION = "DECLARACION"
    BIOGRAFIA = "BIOGRAFIA"
    CONCEPTO = "CONCEPTO"
    NORMATIVA = "NORMATIVA"
    EVENTO = "EVENTO"

class PrecisionTemporal(str, Enum):
    EXACTA = "exacta"
    DIA = "dia"
    SEMANA = "semana"
    MES = "mes"
    TRIMESTRE = "trimestre"
    AÑO = "año"
    DECADA = "decada"
    PERIODO = "periodo"
    INDEFINIDO = "indefinido"
```

### **8.2. Validaciones Aplicadas**
```python
def validar_hechos(self, hechos: List[Dict[str, Any]]) -> bool:
    for hecho in hechos:
        # 1. Validar ID secuencial único
        if not self.validar_id_secuencial(hecho["id"], "hechos"):
            return False
            
        # 2. Validar tipo enum
        if hecho["tipo_hecho"] not in [t.value for t in TipoHecho]:
            self.errores.append(f"Tipo hecho inválido: {hecho['tipo_hecho']}")
            return False
            
        # 3. Validar precision_temporal enum
        if hecho["precision_temporal"] not in [p.value for p in PrecisionTemporal]:
            self.errores.append(f"Precisión temporal inválida: {hecho['precision_temporal']}")
            return False
            
        # 4. Validar fechas YYYY-MM-DD
        for campo_fecha in ["fecha_inicio", "fecha_fin"]:
            if not self.validar_fecha(hecho[campo_fecha], campo_fecha):
                return False
```

---

## **9. MAPEO COMPLETO DE TRANSFORMACIONES**

### **9.1. Transformación de IDs**
```
LLM Response         → Procesamiento      → PayloadBuilder      → RPC Supabase
===============      =================   ===================   ================
"id": 1 (int)     → id_hecho: 1        → "id_temporal_hecho": "1" → BIGSERIAL id (BD)
                  → vinculado_entidades: [1,3] → entidades_del_hecho → [mapping interno]
```

### **9.2. Transformación de Contenido**
```
LLM Response              → Procesamiento                   → PayloadBuilder              → RPC/BD
==================        ==============================    ==========================    ==============
"contenido": "texto"   → texto_original_del_hecho: "texto" → "descripcion_hecho": "texto" → contenido: "texto"
```

### **9.3. Transformación de Fechas**
```
LLM Response              → Procesamiento              → PayloadBuilder                    → RPC/BD
==================        =========================     ================================    ================
"fecha_inicio": "2023-03-14" → metadata.fecha_inicio → "fecha_ocurrencia_hecho_inicio": ISO → TSTZRANGE
"fecha_fin": "2023-03-14"     → metadata.fecha_fin   → "fecha_ocurrencia_hecho_fin": ISO     construcción
```

### **9.4. Transformación de Metadatos**
```
LLM Response                 → Procesamiento              → PayloadBuilder
=====================        ===========================   =========================
"tipo_hecho": "ANUNCIO"   → metadata.tipo_hecho        → "tipo_hecho": "ANUNCIO"
"pais": ["Venezuela"]     → metadata.pais              → metadata_hecho: {"pais": [...]}
"es_futuro": false        → metadata.es_futuro         → "es_evento_futuro": false
```

---

## **10. INCONSISTENCIAS CRÍTICAS IDENTIFICADAS (CON RPC ACTUALIZADO COMO FUENTE DE VERDAD)**

### **10.1. Schema Alignment - ESTADO ACTUALIZADO 2025-01-21**

| **Etapa** | **Campo Principal** | **Campo Tipo** | **Campo Relevancia** | **Campo Fechas** | **Campo Metadata** |
|-----------|-------------------|----------------|----------------------|------------------|-------------------|
| LLM Response | `contenido` ✅ | `tipo_hecho` ✅ | N/A | `fecha_inicio/fin` ✅ | N/A |
| Procesamiento | `texto_original_del_hecho` (interno) | `metadata.tipo_hecho` ✅ | N/A | `metadata.fecha_inicio/fin` ✅ | `metadata_hecho` (interno) |
| Pipeline Coord | `contenido` ✅ | `tipo_hecho` ✅ | `importancia` ✅ | `fecha_ocurrencia_inicio/fin` ✅ | `metadata` ✅ |
| PayloadBuilder | `contenido` ✅ | `tipo_hecho` ✅ | `importancia` ✅ | `fecha_ocurrencia_inicio/fin` ✅ | `metadata` ✅ |
| RPC ACTUALIZADO | `contenido` ✅ | `tipo_hecho` ✅ | `importancia` ✅ | `fecha_ocurrencia_inicio/fin` ✅ | `metadata` ✅ |
| Tabla BD | `contenido` ✅ | `tipo_hecho` ✅ | `importancia` ✅ | `fecha_ocurrencia` (TSTZRANGE) ✅ | campos individuales ✅ |

**✅ PROBLEMA RESUELTO**: Todos los componentes ahora están alineados con el RPC actualizado.

### **10.2. Estado de Alineación Actualizado (2025-01-21)**
- **HechoExtraidoItem**: ✅ ACTUALIZADO - Campos alineados con RPC
- **Pipeline Coordinator**: ✅ ACTUALIZADO - Mapea correctamente a los nombres esperados por RPC
- **PayloadBuilder**: ✅ ACTUALIZADO - Recibe y procesa los campos correctos
- **Fase 4 Hechos**: ✅ ACTUALIZADO - Compatible con prompt que retorna fecha_inicio/fecha_fin directamente
- **RPC**: ✅ Ya actualizado previamente como fuente de verdad

### **10.3. Referencias Cruzadas Inconsistentes**
- Datos y Citas usan `hecho_id` con IDs secuenciales (1,2,3) en prompts
- PayloadBuilder convierte a `id_temporal_hecho` strings ("1","2","3")
- RPC actualizado espera `id_temporal` para mapeo interno
- No existe mapeo claro entre IDs secuenciales y IDs finales de BD

### **10.4. Metadatos Estructurados vs. Campos Planos**
- Procesamiento: `metadata_hecho` como objeto estructurado
- PayloadBuilder: `metadata_hecho` como Dict para RPC
- RPC ACTUALIZADO: Espera `metadata` (sin sufijo) con campos específicos (pais, region, ciudad, etiquetas)

---

## **11. FORTALEZAS Y DEBILIDADES ACTUALES**

### **11.1. ❌ Naming Consistency ROTA**
- PayloadBuilder → RPC: Campos YA NO coinciden después de actualización del RPC
- PayloadBuilder envía campos con sufijos que el RPC actualizado no espera

### **11.2. ✅ Enum Validation (Se mantiene)**
- Tipos de hechos y precisión temporal validados consistentemente
- Mismos enums en modelos Pydantic, prompts y BD

### **11.3. ⚠️ Fecha Management (Parcialmente roto)**
- Manejo robusto de rangos de fechas pero nombres de campos incorrectos
- PayloadBuilder usa sufijo `_hecho` que RPC actualizado no espera

---

## **12. SOLUCIONES IMPLEMENTADAS (2025-01-21)**

### **12.1. ✅ RPC ALINEADO**
El RPC `actualizar_articulo_procesado.sql` fue actualizado para esperar:
- `contenido` (antes esperaba `descripcion_hecho`)
- `importancia` (antes esperaba `relevancia_hecho`)
- `fecha_ocurrencia_inicio/fin` (antes esperaba con sufijo `_hecho`)
- `metadata` (antes esperaba `metadata_hecho`)
- `precision_temporal` como campo directo

### **12.2. ✅ COMPLETADO: HechoExtraidoItem Alineado**
```python
# Cambios implementados en HechoExtraidoItem:
id_temporal_hecho → id_temporal
descripcion_hecho → contenido
relevancia_hecho → importancia
fecha_ocurrencia_hecho_inicio → fecha_ocurrencia_inicio
fecha_ocurrencia_hecho_fin → fecha_ocurrencia_fin
metadata_hecho → metadata
# precision_temporal movido al nivel raíz
```

### **12.3. ✅ COMPLETADO: Pipeline Coordinator Alineado**
```python
# Mapeos actualizados en pipeline_coordinator.py:
"id_temporal": str(hecho.id_hecho)
"contenido": hecho.texto_original_del_hecho
"importancia": int(hecho.confianza_extraccion * 10)
"metadata": {
    "pais": [...],
    "region": [...],
    "ciudad": [...],
    "etiquetas": [...]
}
```

### **12.4. ⚠️ PENDIENTE: ID Mapping System**
```python
# Aún se requiere implementar sistema de mapeo para referencias cruzadas
def crear_mapeo_ids_hechos_secuenciales_a_temporales(hechos_procesados):
    """Crear mapeo para referencias cruzadas en datos y citas"""
    mapeo = {}
    for idx, hecho in enumerate(hechos_procesados, 1):
        mapeo[idx] = hecho.id_temporal  # idx secuencial → ID temporal
    return mapeo
```

**FUENTE DE VERDAD ACTUAL**: RPC `actualizar_articulo_procesado.sql` con campos sin sufijos y estructura específica.