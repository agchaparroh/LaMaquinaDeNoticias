# **ANÁLISIS COMPLETO: SCHEMA CITAS TEXTUALES**

## **RESUMEN EJECUTIVO**

Schema de citas textuales mapeado completamente en TODAS las etapas del pipeline. Se identifican **inconsistencias moderadas** en nombres de campos y **campos no utilizados** en modelos Pydantic.

**⚠️ ACTUALIZACIÓN IMPORTANTE**: El RPC `actualizar_articulo_procesado.sql` fue actualizado. Ahora es la **FUENTE DE VERDAD ABSOLUTA** para evaluar mismatches. PayloadBuilder envía campos que NO coinciden con el RPC actualizado.

---

## **1. MODELOS PYDANTIC - ENTRADA**

### **1.1. MetadatosCita (`src/module_pipeline/src/models/metadatos.py`)**

```json
{
  "fecha": "2023-03-14",                             // Optional[str] YYYY-MM-DD
  "contexto": "Durante rueda de prensa matinal",     // Optional[str]
  "relevancia": 4,                                   // Optional[int] 1-5
  
  // CAMPOS ADICIONALES (no documentados pero usados)
  "cita_textual": "Implementaremos medidas inmediatas", // Optional[str] - texto duplicado
  "entidad_emisora_id": 3,                           // Optional[int] - ID referencia
  "hecho_relacionado_id": 2,                         // Optional[int] - ID referencia  
  "fecha_cita": "2023-03-14"                         // Optional[str] - fecha alternativa
}
```

### **1.2. CitaTextual (`src/module_pipeline/src/models/procesamiento.py`)**

```json
{
  "id_cita": 1,                                      // int - ID secuencial
  "id_fragmento_origen": "ART-123",                  // str - ID del fragmento
  "texto_cita": "Implementaremos medidas inmediatas", // str - Min 5 chars
  "persona_citada": "Nicolás Maduro",                // Optional[str] - Nombre emisor
  "id_entidad_citada": 3,                            // Optional[int] - ID entidad emisora
  "offset_inicio_cita": 250,                         // Optional[int] - Posición inicial
  "offset_fin_cita": 290,                            // Optional[int] - Posición final
  "contexto_cita": "Durante rueda de prensa",        // Optional[str] - Contexto breve
  "metadata_cita": MetadatosCita                     // Object definido arriba
}
```

### **1.3. CitaTextualExtraidaItem (`src/module_pipeline/src/models/persistencia.py`)**

```json
{
  // CAMPOS PRINCIPALES (para RPC)
  "id_temporal_cita": "CITA-123",                    // str - ID temporal único
  "texto_cita": "Implementaremos medidas inmediatas", // str - Contenido textual
  "entidad_emisora_id_temporal": "3",                // Optional[str] - ID temporal entidad
  "nombre_entidad_emisora": "Nicolás Maduro",        // Optional[str] - Nombre entidad
  "cargo_entidad_emisora": "Presidente",             // Optional[str] - ❌ NO USADO
  "fecha_cita": "2023-03-14T10:30:00Z",              // Optional[str] - ISO 8601
  "contexto_cita": "Durante rueda de prensa",        // Optional[str] - Contexto
  "relevancia_cita": 8,                              // Optional[int] 1-10
  "hecho_principal_relacionado_id_temporal": "2"     // Optional[str] - ID hecho relacionado
}
```

---

## **2. PROMPTS LLM - SCHEMA ESPERADO**

### **2.1. Prompt Principal (`prompts/Citas.md`)**

```json
{
  "citas_textuales": [
    {
      "id": 1,                                       // int - ID secuencial único
      "cita": "Implementaremos medidas inmediatas para controlar la inflación", // str - Texto exacto
      "entidad_id": 3,                               // int - ID entidad emisora (referencia)
      "hecho_id": 2,                                 // int - ID hecho relacionado (referencia)
      "fecha": "2023-03-14",                         // str YYYY-MM-DD
      "contexto": "Declarado durante rueda de prensa matinal", // str - Contexto
      "relevancia": 4                                // int - Relevancia 1-5
    }
  ]
}
```

**Escalas definidas:**
- **relevancia:** 1-5 (escala del prompt)
- **entidad_id:** Referencia a entidades extraídas en Fase 3
- **hecho_id:** Referencia a hechos extraídos en Fase 4

---

## **3. FASE 6 - PROCESAMIENTO (`src/pipeline/fase_6_citas.py`)**

### **3.1. Input Schema**
```json
{
  "hechos_extraidos": "Array de HechoProcesado de Fase 4",
  "entidades_extraidas": "Array de EntidadProcesada de Fase 3",
  "texto_simplificado": "contenido del artículo procesado"
}
```

### **3.2. Output Schema**
```json
{
  "citas_textuales_extraidas": [
    {
      "id_cita": 1,
      "id_fragmento_origen": "ART-123",
      "texto_cita": "Implementaremos medidas inmediatas",     // MAPEO: cita → texto_cita
      "persona_citada": "Nicolás Maduro",                    // INFERIDO o EXTRAÍDO
      "id_entidad_citada": 3,                                // MAPEO: entidad_id → id_entidad_citada
      "offset_inicio_cita": 250,
      "offset_fin_cita": 290,
      "contexto_cita": "Durante rueda de prensa",            // MAPEO: contexto → contexto_cita
      "metadata_cita": {
        "fecha": "2023-03-14",                               // MAPEO: fecha → fecha
        "contexto": "Durante rueda de prensa matinal",       // DUPLICADO de contexto_cita
        "relevancia": 4,                                     // MAPEO: relevancia → relevancia
        "entidad_emisora_id": 3,                             // DUPLICADO de id_entidad_citada
        "hecho_relacionado_id": 2,                           // MAPEO: hecho_id → hecho_relacionado_id
        "fecha_cita": "2023-03-14"                           // DUPLICADO de fecha
      }
    }
  ]
}
```

### **3.3. Función de Conversión (inferida)**
```python
def _procesar_citas_extraidas(citas_raw, id_fragmento):
    for cita in citas_raw:
        metadatos = MetadatosCita(
            fecha=cita.get("fecha"),                         # MAPEO: fecha → fecha
            contexto=cita.get("contexto"),                   # MAPEO: contexto → contexto
            relevancia=cita.get("relevancia", 3),            # MAPEO: relevancia → relevancia
            entidad_emisora_id=cita.get("entidad_id"),       # MAPEO: entidad_id → entidad_emisora_id
            hecho_relacionado_id=cita.get("hecho_id"),       # MAPEO: hecho_id → hecho_relacionado_id
            fecha_cita=cita.get("fecha")                     # DUPLICADO
        )
        
        cita_procesada = CitaTextual(
            id_cita=cita.get("id", 0),
            id_fragmento_origen=id_fragmento,
            texto_cita=cita.get("cita", ""),                 # MAPEO: cita → texto_cita
            id_entidad_citada=cita.get("entidad_id"),        # MAPEO: entidad_id → id_entidad_citada
            contexto_cita=cita.get("contexto"),              # MAPEO: contexto → contexto_cita
            metadata_cita=metadatos
        )
```

---

## **4. CONSOLIDACIÓN (`src/services/consolidation_service.py`)**

### **4.1. Input Schema (si chunking activo)**
```json
{
  "citas_por_chunk": [
    [Array_CitaTextual_chunk_1],
    [Array_CitaTextual_chunk_2],
    [Array_CitaTextual_chunk_3]
  ]
}
```

### **4.2. Algoritmo de Consolidación (líneas 447-517)**
```python
def consolidar_citas_textuales(self, citas_por_chunk):
    """
    Elimina duplicados entre chunks usando:
    - Similitud de texto >= 95% (texto_cita)
    - Comparación de entidad emisora (id_entidad_citada)
    - Reasignación de IDs secuenciales (1, 2, 3...)
    """
    # Preserva estructura completa de CitaTextual
    # Actualiza referencias cruzadas a entidades y hechos
    # Reasigna id_cita secuencial
```

### **4.3. Output Schema**
```json
{
  "citas_consolidadas": [Array_CitaTextual_sin_duplicados_con_ids_reasignados]
}
```

---

## **5. PAYLOADBUILDER - CONVERSIÓN FINAL (`src/pipeline/pipeline_coordinator.py`)**

### **5.1. Input Schema**
```json
{
  "citas_textuales_extraidas": "Array de CitaTextual consolidadas"
}
```

### **5.2. Función de Conversión (líneas 679-686 y 819-827)**
```python
def construir_payload_citas():
    citas_data = []
    for cita in citas_textuales_extraidas:
        cita_item = {
            "id_temporal_cita": str(cita.id_cita),                    # CONVERSIÓN: int → str
            "texto_cita": cita.texto_cita,                           # MAPEO: directo
            "entidad_emisora_id_temporal": str(cita.id_entidad_citada) if cita.id_entidad_citada else None, # CONVERSIÓN + MAPEO
            "nombre_entidad_emisora": cita.persona_citada,           # MAPEO: persona_citada → nombre_entidad_emisora
            "contexto_cita": cita.contexto_cita,                     # MAPEO: directo
            "fecha_cita": cita.metadata_cita.fecha,                  # EXTRACCIÓN: metadata.fecha → fecha_cita
            "relevancia_cita": cita.metadata_cita.relevancia,        # EXTRACCIÓN: metadata.relevancia → relevancia_cita
            # ❌ CAMPO FALTANTE: hecho_principal_relacionado_id_temporal no se genera
        }
        citas_data.append(cita_item)
```

### **5.3. Transformación de Campos Críticos**
```python
# CitaTextual → PayloadBuilder data
id_cita                      → id_temporal_cita (str conversion)
texto_cita                   → texto_cita ✅
id_entidad_citada            → entidad_emisora_id_temporal (str conversion)
persona_citada               → nombre_entidad_emisora
contexto_cita                → contexto_cita ✅
metadata_cita.fecha          → fecha_cita
metadata_cita.relevancia     → relevancia_cita
metadata_cita.hecho_relacionado_id → ❌ NO MAPEADO a hecho_principal_relacionado_id_temporal
```

### **5.4. Output Schema Final**
```json
{
  "citas_textuales_extraidas": [
    {
      "id_temporal_cita": "1",                       // str conversion de id_cita
      "texto_cita": "Implementaremos medidas inmediatas",
      "entidad_emisora_id_temporal": "3",            // str conversion de id_entidad_citada
      "nombre_entidad_emisora": "Nicolás Maduro",
      "contexto_cita": "Durante rueda de prensa",
      "fecha_cita": "2023-03-14",                    // ❌ NO ISO 8601 - string plano
      "relevancia_cita": 4,                          // ❌ ESCALA 1-5 en lugar de 1-10
      // ❌ CAMPO FALTANTE: hecho_principal_relacionado_id_temporal
      // ❌ CAMPO FALTANTE: cargo_entidad_emisora (definido en modelo pero no usado)
    }
  ]
}
```

---

## **6. RPC SUPABASE - PERSISTENCIA (`actualizar_articulo_procesado.sql`) [ACTUALIZADO]**

### **6.1. Input Schema Esperado (DESPUÉS DE ACTUALIZACIÓN)**
```json
{
  "citas_textuales_extraidas": [
    {
      "cita": "Implementaremos medidas inmediatas",          // RPC ahora espera: cita
      "id_temporal_entidad_emisora": "3",                   // RPC ahora espera: id_temporal_entidad_emisora (sin cambios)
      "id_temporal_hecho_contexto": "2",                    // RPC ahora espera: id_temporal_hecho_contexto
      "fecha_cita": "2023-03-14T10:30:00Z",                // RPC ahora espera: fecha_cita (sin cambios)
      "contexto": "Durante rueda de prensa",                // RPC ahora espera: contexto
      "relevancia": 4                                       // RPC ahora espera: relevancia
    }
  ]
}
```

### **6.2. Mapeo de Campos en RPC ACTUALIZADO (líneas 287-298)**
```sql
INSERT INTO citas_textuales (
    cita,                        -- Mapea de: cita
    entidad_emisora_id,          -- Mapea de: temp_entidad_id_map lookup
    articulo_id,                 -- v_articulo_id
    hecho_contexto_id,           -- Mapea de: temp_hecho_id_map lookup
    fecha_cita,                  -- Mapea de: fecha_cita (TIMESTAMPTZ conversion)
    contexto,                    -- Mapea de: contexto
    relevancia                   -- Mapea de: relevancia (default 3)
)
VALUES (
    v_cita->>'cita',                                     -- Busca: cita
    v_entidad_id,                                        -- Lookup desde temp_entidad_id_map
    v_articulo_id,
    v_hecho_id,                                          -- Lookup desde temp_hecho_id_map
    CASE WHEN v_cita ? 'fecha_cita'                      -- Busca: fecha_cita
        THEN (v_cita->>'fecha_cita')::TIMESTAMPTZ
        ELSE (SELECT fecha_publicacion FROM articulos WHERE id = v_articulo_id)
    END,
    v_cita->>'contexto',                                 -- Busca: contexto
    COALESCE((v_cita->>'relevancia')::INTEGER, 3)       -- Busca: relevancia
)
```

### **6.3. Resolución de IDs ACTUALIZADA (líneas 267-274)**
```sql
-- Obtener ID real de entidad emisora
v_entidad_id := NULL;
IF v_cita ? 'id_temporal_entidad_emisora' THEN                    -- Busca: id_temporal_entidad_emisora
    v_entidad_id := (temp_entidad_id_map->>(v_cita->>'id_temporal_entidad_emisora'))::BIGINT;
END IF;

-- Obtener ID real del hecho contexto  
v_hecho_id := NULL;
IF v_cita ? 'id_temporal_hecho_contexto' THEN                     -- Busca: id_temporal_hecho_contexto
    v_hecho_id := (temp_hecho_id_map->>(v_cita->>'id_temporal_hecho_contexto'))::BIGINT;
END IF;
```

### **6.4. Tabla Supabase Schema Real**
```sql
CREATE TABLE citas_textuales (
    id BIGSERIAL PRIMARY KEY,
    cita TEXT NOT NULL,                                  -- ✅ Campo real: cita
    entidad_emisora_id BIGINT REFERENCES entidades(id), -- ✅ Campo real: entidad_emisora_id
    articulo_id BIGINT REFERENCES articulos(id),        -- ✅ Campo real: articulo_id
    hecho_contexto_id BIGINT,                           -- ✅ Campo real: hecho_contexto_id
    fecha_cita TIMESTAMP WITH TIME ZONE,                -- ✅ Campo real: fecha_cita
    contexto TEXT,                                      -- ✅ Campo real: contexto
    relevancia INTEGER NOT NULL CHECK (relevancia BETWEEN 1 AND 5) DEFAULT 3, -- ✅ Campo real: relevancia
    fecha_ingreso TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    embedding vector(384)
);
```

---

## **7. REFERENCIAS CRUZADAS - OTROS SCHEMAS**

### **7.1. Referencia a Entidades (`prompts/Citas.md`)**
```json
{
  "citas_textuales": [
    {
      "id": 1,
      "entidad_id": 3,                                 // ❌ REFERENCIA: Busca entidad por ID secuencial
      "cita": "Texto de la cita"
    }
  ]
}
```

### **7.2. Referencia a Hechos (`prompts/Citas.md`)**
```json
{
  "citas_textuales": [
    {
      "id": 1,
      "hecho_id": 2,                                   // ❌ REFERENCIA: Busca hecho por ID secuencial
      "cita": "Texto de la cita"
    }
  ]
}
```

### **7.3. Referencias desde otros schemas**
Ni hechos ni datos referencian citas directamente en sus prompts.

---

## **8. VALIDACIONES (`src/utils/schema_validator.py`)**

### **8.1. Validaciones Aplicadas (inferidas)**
```python
def validar_citas_textuales(self, citas: List[Dict[str, Any]]) -> bool:
    for cita in citas:
        # 1. Validar ID secuencial único
        if not self.validar_id_secuencial(cita["id"], "citas"):
            return False
            
        # 2. Validar texto de cita no vacío
        if not cita.get("cita") or len(cita["cita"]) < 5:
            self.errores.append(f"Cita muy corta: {cita['cita']}")
            return False
            
        # 3. Validar relevancia 1-5
        if not (1 <= cita.get("relevancia", 3) <= 5):
            self.errores.append(f"Relevancia inválida: {cita['relevancia']}")
            return False
            
        # 4. Validar fechas YYYY-MM-DD
        if not self.validar_fecha(cita.get("fecha"), "fecha"):
            return False
            
        # 5. Validar referencias a entidades y hechos existentes
        if not self.validar_referencia_id(cita["entidad_id"], "entidades"):
            return False
        if not self.validar_referencia_id(cita["hecho_id"], "hechos"):
            return False
```

---

## **9. MAPEO COMPLETO DE TRANSFORMACIONES**

### **9.1. Transformación de IDs**
```
LLM Response         → Procesamiento           → PayloadBuilder              → RPC Supabase
===============      ===================       ========================      ================
"id": 1 (int)     → id_cita: 1              → "id_temporal_cita": "1"     → BIGSERIAL id (BD)
"entidad_id": 3   → id_entidad_citada: 3    → "entidad_emisora_id_temporal": "3" → temp_entidad_id_map
"hecho_id": 2     → metadata.hecho_relacionado_id: 2 → ❌ NO MAPEADO → temp_hecho_id_map
```

### **9.2. Transformación de Contenido**
```
LLM Response              → Procesamiento         → PayloadBuilder           → RPC/BD
==================        ===================     =====================      ===============
"cita": "texto"        → texto_cita: "texto"    → "texto_cita": "texto"    → cita: "texto"
"contexto": "contexto" → contexto_cita: "contexto" → "contexto_cita": "contexto" → contexto: "contexto"
"relevancia": 4        → metadata.relevancia: 4 → "relevancia_cita": 4     → relevancia: 4
```

### **9.3. Transformación de Fechas**
```
LLM Response              → Procesamiento              → PayloadBuilder           → RPC/BD
==================        ===========================   ======================     ================
"fecha": "2023-03-14"  → metadata_cita.fecha: "2023-03-14" → "fecha_cita": "2023-03-14" → TIMESTAMPTZ
```

### **9.4. Transformación de Referencias**
```
LLM Response              → Procesamiento                 → PayloadBuilder              → RPC
==================        ==============================   =============================  =========
"entidad_id": 3        → id_entidad_citada: 3          → "entidad_emisora_id_temporal": "3" → temp_entidad_id_map
"hecho_id": 2          → metadata.hecho_relacionado_id: 2 → ❌ CAMPO PERDIDO            → ❌ NO LLEGA
```

---

## **10. INCONSISTENCIAS CRÍTICAS IDENTIFICADAS (CON RPC ACTUALIZADO COMO FUENTE DE VERDAD)**

### **10.1. Campo Mapping - ESTADO ACTUALIZADO 2025-01-21**

| **Campo** | **PayloadBuilder** | **RPC ACTUALIZADO** | **Tabla BD** | **Status** |
|-----------|-------------------|---------------------|--------------|------------|
| Texto | `cita` ✅ | `cita` ✅ | `cita` | CORRECTO |
| Entidad | `id_temporal_entidad_emisora` ✅ | `id_temporal_entidad_emisora` ✅ | `entidad_emisora_id` | CORRECTO |
| Hecho | `id_temporal_hecho_contexto` ✅ | `id_temporal_hecho_contexto` ✅ | `hecho_contexto_id` | CORRECTO |
| Contexto | `contexto` ✅ | `contexto` ✅ | `contexto` | CORRECTO |
| Fecha | `fecha_cita` ✅ | `fecha_cita` ✅ | `fecha_cita` | CORRECTO |
| Relevancia | `relevancia` ✅ | `relevancia` ✅ | `relevancia` | CORRECTO |

### **10.2. Estado de Alineación Actualizado (2025-01-21)**
- **CitaTextualExtraidaItem**: ✅ ACTUALIZADO - Campos alineados con RPC
- **Pipeline Coordinator**: ✅ ACTUALIZADO - Mapea correctamente a los nombres esperados por RPC
- **PayloadBuilder**: ✅ Ya procesa correctamente los campos
- **Fase 6 Citas**: ✅ No requirió cambios, procesa internamente
- **RPC**: ✅ Ya actualizado previamente como fuente de verdad

### **10.3. Escalas de Relevancia Inconsistentes**
- **Prompt:** Escala 1-5
- **Tabla BD:** CHECK constraint 1-5 ✅ CORRECTO
- **Modelo persistencia:** Documenta 1-10 ❌ INCONSISTENTE

### **10.4. Campos Duplicados en Metadatos**
- `metadata_cita.fecha` vs `metadata_cita.fecha_cita` (duplicado)
- `metadata_cita.contexto` vs `contexto_cita` (duplicado)
- `metadata_cita.entidad_emisora_id` vs `id_entidad_citada` (duplicado)

### **10.5. Formato de Fechas**
- PayloadBuilder: String YYYY-MM-DD plano (NO ISO 8601)
- RPC: Espera TIMESTAMPTZ conversion
- Conversión funciona pero podría ser más robusta

---

## **11. CAMPOS NO UTILIZADOS**

### **11.1. Campos Definidos pero NO Usados**
- `cargo_entidad_emisora` → Definido en CitaTextualExtraidaItem pero nunca poblado
- `metadata_cita.cita_textual` → Duplicado innecesario de texto_cita
- Metadatos duplicados mencionados en 10.4

### **11.2. Campos que se Pierden**
- `offset_inicio_cita`, `offset_fin_cita` → No llegan a RPC
- `hecho_relacionado_id` → Se pierde en PayloadBuilder

---

## **12. FORTALEZAS Y DEBILIDADES ACTUALES**

### **12.1. ❌ Naming Consistency ROTA**
- PayloadBuilder → RPC: Campos YA NO coinciden después de actualización del RPC
- PayloadBuilder envía campos con sufijos `_cita` que el RPC actualizado no espera

### **12.2. ✅ Reference Resolution (Se mantiene para entidades)**
- Mapeo de entidades funciona correctamente via `temp_entidad_id_map`
- IDs temporales se resuelven a IDs reales en BD
- ❌ PERO falta implementar referencia a hechos

### **12.3. ✅ Data Validation (Se mantiene)**
- Restricciones de relevancia 1-5 correctas
- Validación de texto mínimo

---

## **13. SOLUCIONES IMPLEMENTADAS (2025-01-21)**

### **13.1. ✅ RPC ALINEADO**
El RPC `actualizar_articulo_procesado.sql` fue actualizado para esperar:
- `cita` (antes esperaba `texto_cita`)
- `contexto` (antes esperaba `contexto_cita`)
- `relevancia` (antes esperaba `relevancia_cita`)
- `id_temporal_hecho_contexto` (antes esperaba `id_temporal_hecho_principal`)

### **13.2. ✅ COMPLETADO: CitaTextualExtraidaItem Alineado**
```python
# Cambios implementados en CitaTextualExtraidaItem:
texto_cita → cita
contexto_cita → contexto
relevancia_cita → relevancia
# Añadido campo id_temporal_hecho_contexto
# Corregida escala de relevancia a 1-5
# Removido cargo_entidad_emisora (no usado)
```

### **13.3. ✅ COMPLETADO: Pipeline Coordinator Alineado**
```python
# Mapeos actualizados en pipeline_coordinator.py:
"cita": cita.texto_cita
"contexto": cita.contexto_cita
"relevancia": cita.metadata_cita.relevancia
"id_temporal_hecho_contexto": str(cita.metadata_cita.hecho_relacionado_id)
```

### **13.4. ⚠️ PENDIENTE: Limpiar MetadatosCita**
```python
# Aún se requiere limpiar duplicados en MetadatosCita:
class MetadatosCita(BaseModel):
    fecha: Optional[str]                  # MANTENER
    relevancia: Optional[int]             # MANTENER (1-5)
    hecho_relacionado_id: Optional[int]   # MANTENER
    # REMOVER: cita_textual, fecha_cita, entidad_emisora_id (duplicados)
```

**FUENTE DE VERDAD ACTUAL**: RPC `actualizar_articulo_procesado.sql` con campos sin sufijos y estructura específica.