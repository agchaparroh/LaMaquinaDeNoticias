# **ANÁLISIS COMPLETO: SCHEMA DATOS CUANTITATIVOS**

## **RESUMEN EJECUTIVO**

Schema de datos cuantitativos mapeado completamente en TODAS las etapas del pipeline. Se identifican **múltiples inconsistencias críticas** en nombres de campos entre PayloadBuilder y RPC Supabase.

**⚠️ ACTUALIZACIÓN IMPORTANTE**: El RPC `actualizar_articulo_procesado.sql` fue actualizado. Ahora es la **FUENTE DE VERDAD ABSOLUTA** para evaluar mismatches. PayloadBuilder envía campos que NO coinciden con el RPC actualizado.

---

## **1. MODELOS PYDANTIC - ENTRADA**

### **1.1. MetadatosDato (`src/module_pipeline/src/models/metadatos.py`)**

```json
{
  "categoria": "económico",                           // Optional[str] - enum específico
  "tipo_periodo": "trimestral",                       // Optional[str] - enum específico
  "tendencia": "aumento",                             // Optional[str] - enum específico
  "valor_anterior": 12.5,                             // Optional[float]
  "variacion_absoluta": 2.7,                          // Optional[float]
  "variacion_porcentual": 21.6,                       // Optional[float]
  "ambito_geografico": ["España", "Cataluña"],        // List[str] default=[]
  "periodo": PeriodoReferencia                        // Object con inicio/fin
}
```

**Enums precisos:**
- **categoria:** `económico|demográfico|electoral|social|presupuestario|sanitario|ambiental|conflicto|otro`
- **tipo_periodo:** `anual|trimestral|mensual|semanal|diario|puntual|acumulado`
- **tendencia:** `aumento|disminución|estable`

### **1.2. DatosCuantitativos (`src/module_pipeline/src/models/procesamiento.py`)**

```json
{
  "id_dato_cuantitativo": 1,                          // int - ID secuencial
  "id_fragmento_origen": "ART-123",                   // str - ID del fragmento
  "descripcion_dato": "Inflación interanual",         // str - Indicador del dato
  "valor_dato": 15.2,                                 // float - Valor numérico
  "unidad_dato": "porcentaje",                        // Optional[str] - Unidad
  "fecha_dato": "2023-01-01 - 2023-03-31",           // Optional[str] - Período concatenado
  "fuente_especifica_dato": "INE",                    // Optional[str] - Fuente específica
  "offset_inicio_dato": 300,                          // Optional[int] - Posición en texto
  "offset_fin_dato": 350,                             // Optional[int] - Posición final
  "metadata_dato": MetadatosDato                      // Object definido arriba
}
```

### **1.3. DatoCuantitativoExtraidoItem (`src/module_pipeline/src/models/persistencia.py`)**

```json
{
  // CAMPOS PRINCIPALES (para RPC)
  "id_temporal_dato": "DATO-123",                     // str - ID temporal único
  "descripcion_dato": "Inflación interanual",         // str - Descripción
  "valor_dato": 15.2,                                 // Union[float, int, str, None]
  "unidad_dato": "porcentaje",                        // Optional[str] - Unidad
  "fecha_dato": "2023-03-31T00:00:00Z",               // Optional[str] - ISO 8601
  "contexto_dato": "Datos del primer trimestre",      // Optional[str] - Contexto
  "relevancia_dato": 8,                               // Optional[int] 1-10
  "hecho_principal_relacionado_id_temporal": "HECHO-456", // Optional[str] - ID hecho
  
  // CAMPOS AGREGADOS (coinciden con DB)
  "categoria": "económico",                           // Optional[str]
  "tipo_periodo": "trimestral",                       // Optional[str]
  "tendencia": "aumento",                             // Optional[str]
  "valor_anterior": 12.5,                             // Optional[float]
  "variacion_absoluta": 2.7,                          // Optional[float]
  "variacion_porcentual": 21.6,                       // Optional[float]
  "periodo_referencia_inicio": "2023-01-01",          // Optional[str] YYYY-MM-DD
  "periodo_referencia_fin": "2023-03-31"              // Optional[str] YYYY-MM-DD
}
```

---

## **2. PROMPTS LLM - SCHEMA ESPERADO**

### **2.1. Prompt Principal (`prompts/Datos.md`)**

```json
{
  "datos_cuantitativos": [
    {
      "id": 1,                                        // int - ID secuencial único
      "hecho_id": 2,                                  // int - ID del hecho relacionado
      "indicador": "Inflación interanual",            // str - Concepto medido
      "categoria": "económico",                       // str - enum específico
      "valor": 15.2,                                  // number - Valor numérico exacto
      "unidad": "porcentaje",                         // str - Unidad de medida
      "ambito_geografico": ["España"],                // Array[str] - Ubicaciones
      "periodo_inicio": "2023-01-01",                 // str YYYY-MM-DD
      "periodo_fin": "2023-03-31",                    // str YYYY-MM-DD
      "tipo_periodo": "trimestral",                   // str - enum específico
      "valor_anterior": 12.5,                         // number o null
      "variacion_absoluta": 2.7,                      // number o null
      "variacion_porcentual": 21.6,                   // number o null
      "tendencia": "aumento"                          // str - enum específico
    }
  ]
}
```

**Enums permitidos exactos:**
- **categoria:** `económico`, `demográfico`, `electoral`, `social`, `presupuestario`, `sanitario`, `ambiental`, `conflicto`, `otro`
- **tipo_periodo:** `anual`, `trimestral`, `mensual`, `semanal`, `diario`, `puntual`, `acumulado`
- **tendencia:** `aumento`, `disminución`, `estable`

---

## **3. FASE 5 - PROCESAMIENTO (`src/pipeline/fase_5_datos.py`)**

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
  "datos_cuantitativos_extraidos": [
    {
      "id_dato_cuantitativo": 1,
      "id_fragmento_origen": "ART-123",
      "descripcion_dato": "Inflación interanual",        // MAPEO: indicador → descripcion_dato
      "valor_dato": 15.2,                                // MAPEO: valor → valor_dato (float conversion)
      "unidad_dato": "porcentaje",                       // MAPEO: unidad → unidad_dato
      "fecha_dato": "2023-01-01 - 2023-03-31",          // CONCATENACIÓN: periodo_inicio + " - " + periodo_fin
      "fuente_especifica_dato": null,
      "offset_inicio_dato": 300,
      "offset_fin_dato": 350,
      "metadata_dato": {
        "categoria": "económico",
        "tipo_periodo": "trimestral",
        "tendencia": "aumento",
        "valor_anterior": 12.5,
        "variacion_absoluta": 2.7,
        "variacion_porcentual": 21.6,
        "ambito_geografico": ["España"],
        "periodo": {
          "inicio": "2023-01-01",
          "fin": "2023-03-31"
        }
      }
    }
  ]
}
```

### **3.3. Función de Conversión (líneas 271-334)**
```python
def _procesar_datos_extraidos(datos_raw, id_fragmento, fragment_processor):
    for dato in datos_raw:
        # Convertir fechas
        fecha_inicio = dato.get("periodo_inicio")
        fecha_fin = dato.get("periodo_fin", fecha_inicio)
        
        # Crear objeto PeriodoReferencia
        periodo = PeriodoReferencia(
            inicio=fecha_inicio,
            fin=fecha_fin
        ) if fecha_inicio else None
        
        metadatos = MetadatosDato(
            categoria=dato.get("categoria"),                 # MAPEO: categoria → categoria
            tipo_periodo=dato.get("tipo_periodo"),           # MAPEO: tipo_periodo → tipo_periodo
            tendencia=dato.get("tendencia"),                 # MAPEO: tendencia → tendencia
            valor_anterior=dato.get("valor_anterior"),       # MAPEO: valor_anterior → valor_anterior
            variacion_absoluta=dato.get("variacion_absoluta"), # MAPEO directo
            variacion_porcentual=dato.get("variacion_porcentual"), # MAPEO directo
            ambito_geografico=dato.get("ambito_geografico", []), # MAPEO directo
            periodo=periodo
        )
        
        dato_procesado = DatosCuantitativos(
            id_dato_cuantitativo=dato.get("id", 0),
            id_fragmento_origen=id_fragmento,
            descripcion_dato=dato.get("indicador", ""),      # MAPEO: indicador → descripcion_dato
            valor_dato=float(dato.get("valor", 0)),          # CONVERSIÓN: valor → valor_dato (float)
            unidad_dato=dato.get("unidad"),                  # MAPEO: unidad → unidad_dato
            fecha_dato=f"{fecha_inicio} - {fecha_fin}" if fecha_inicio else None, # CONCATENACIÓN
            metadata_dato=metadatos
        )
```

---

## **4. CONSOLIDACIÓN (`src/services/consolidation_service.py`)**

### **4.1. Input Schema (si chunking activo)**
```json
{
  "datos_por_chunk": [
    [Array_DatosCuantitativos_chunk_1],
    [Array_DatosCuantitativos_chunk_2],
    [Array_DatosCuantitativos_chunk_3]
  ]
}
```

### **4.2. Algoritmo de Consolidación**
```python
def consolidar_datos_cuantitativos(self, datos_por_chunk):
    """
    Elimina duplicados entre chunks usando:
    - Similitud de indicador (descripcion_dato)
    - Comparación de valores numéricos (valor_dato)
    - Similitud de períodos (fecha_dato)
    """
    # Preserva estructura completa de DatosCuantitativos
    # Solo elimina duplicados, no modifica campos
```

---

## **5. PAYLOADBUILDER - CONVERSIÓN FINAL (`src/services/payload_builder.py`)**

### **5.1. Input Schema**
```json
{
  "datos_cuantitativos_data": "Array de DatosCuantitativos consolidados"
}
```

### **5.2. Función de Conversión (línea 427)**
```python
def construir_payload_articulo_from_model():
    if datos_cuantitativos_data is not None:
        payload_data["datos_cuantitativos_extraidos"] = [
            DatoCuantitativoExtraidoItem(**item) for item in datos_cuantitativos_data
        ]
```

### **5.3. Transformación de Campos Críticos**
```python
# DatosCuantitativos → DatoCuantitativoExtraidoItem
id_dato_cuantitativo        → id_temporal_dato (str conversion)
descripcion_dato            → descripcion_dato ✅
valor_dato                  → valor_dato ✅
unidad_dato                 → unidad_dato ✅
fecha_dato                  → fecha_dato (¿conserva concatenación?)
metadata_dato.categoria     → categoria (field extraction)
metadata_dato.tipo_periodo  → tipo_periodo (field extraction)
metadata_dato.periodo.inicio → periodo_referencia_inicio
metadata_dato.periodo.fin   → periodo_referencia_fin
```

### **5.4. Output Schema Final**
```json
{
  "datos_cuantitativos_extraidos": [
    {
      "id_temporal_dato": "1",                         // str conversion de id_dato_cuantitativo
      "descripcion_dato": "Inflación interanual",
      "valor_dato": 15.2,
      "unidad_dato": "porcentaje",
      "fecha_dato": "2023-03-31T00:00:00Z",            // ¿Conversión ISO 8601?
      "contexto_dato": null,
      "relevancia_dato": 8,
      "hecho_principal_relacionado_id_temporal": "2",   // ❌ REFERENCIA: hecho_id secuencial
      "categoria": "económico",
      "tipo_periodo": "trimestral",
      "tendencia": "aumento",
      "valor_anterior": 12.5,
      "variacion_absoluta": 2.7,
      "variacion_porcentual": 21.6,
      "periodo_referencia_inicio": "2023-01-01",
      "periodo_referencia_fin": "2023-03-31"
    }
  ]
}
```

---

## **6. RPC SUPABASE - PERSISTENCIA (`actualizar_articulo_procesado.sql`) [ACTUALIZADO]**

### **6.1. Input Schema Esperado (DESPUÉS DE ACTUALIZACIÓN)**
```json
{
  "datos_cuantitativos_extraidos": [
    {
      "id_temporal_hecho": "2",                        // RPC ahora espera: id_temporal_hecho
      "indicador": "Inflación interanual",             // RPC ahora espera: indicador
      "categoria": "económico",                        // RPC ahora espera: categoria
      "valor_numerico": 15.2,                          // RPC ahora espera: valor_numerico
      "unidad": "porcentaje",                          // RPC ahora espera: unidad
      "ambito_geografico": ["España"],                 // RPC ahora espera: ambito_geografico (array)
      "periodo_referencia_inicio": "2023-01-01",       // RPC ahora espera: periodo_referencia_inicio
      "periodo_referencia_fin": "2023-03-31",          // RPC ahora espera: periodo_referencia_fin
      "tendencia": "aumento"                           // RPC ahora espera: tendencia
    }
  ]
}
```

### **6.2. Mapeo de Campos en RPC ACTUALIZADO (líneas 330-350)**
```sql
INSERT INTO datos_cuantitativos (
    hecho_id,                    -- Mapea de: temp_hecho_id_map lookup
    articulo_id,                 -- v_articulo_id
    indicador,                   -- Mapea de: indicador
    categoria,                   -- Mapea de: categoria
    valor_numerico,              -- Mapea de: valor_numerico (NUMERIC conversion)
    unidad,                      -- Mapea de: unidad
    ambito_geografico,           -- Mapea de: ambito_geografico (array)
    periodo_referencia_inicio,   -- Mapea de: periodo_referencia_inicio (DATE conversion)
    periodo_referencia_fin,      -- Mapea de: periodo_referencia_fin (DATE conversion)
    tendencia                    -- Mapea de: tendencia
)
VALUES (
    v_hecho_id,                                      -- Lookup desde mapeo temporal
    v_articulo_id,
    v_dato->>'indicador',                            -- Busca: indicador
    v_dato->>'categoria',                            -- Busca: categoria
    (v_dato->>'valor_numerico')::NUMERIC,            -- Busca: valor_numerico
    v_dato->>'unidad',                               -- Busca: unidad
    CASE WHEN v_dato ? 'ambito_geografico'           -- Busca: ambito_geografico
        THEN ARRAY(SELECT jsonb_array_elements_text(v_dato->'ambito_geografico'))
        ELSE ARRAY[]::VARCHAR[] END,
    CASE WHEN v_dato ? 'periodo_referencia_inicio'   -- Busca: periodo_referencia_inicio
        THEN (v_dato->>'periodo_referencia_inicio')::DATE
        ELSE NULL END,
    CASE WHEN v_dato ? 'periodo_referencia_fin'      -- Busca: periodo_referencia_fin
        THEN (v_dato->>'periodo_referencia_fin')::DATE
        ELSE NULL END,
    v_dato->>'tendencia'                             -- Busca: tendencia
)
```

### **6.3. Tabla Supabase Schema Real**
```sql
CREATE TABLE datos_cuantitativos (
    id BIGSERIAL PRIMARY KEY,
    hecho_id BIGINT,                                 -- ✅ Campo real: hecho_id
    articulo_id BIGINT REFERENCES articulos(id),     -- ✅ Campo real: articulo_id
    indicador VARCHAR(200) NOT NULL,                 -- ✅ Campo real: indicador
    categoria VARCHAR(50) NOT NULL,                  -- ✅ Campo real: categoria
    valor_numerico NUMERIC NOT NULL,                 -- ✅ Campo real: valor_numerico
    unidad VARCHAR(50) NOT NULL,                     -- ✅ Campo real: unidad
    ambito_geografico VARCHAR(100)[] NOT NULL,       -- ✅ Campo real: ambito_geografico
    periodo_referencia_inicio DATE,                  -- ✅ Campo real: periodo_referencia_inicio
    periodo_referencia_fin DATE,                     -- ✅ Campo real: periodo_referencia_fin
    tipo_periodo VARCHAR(50),                        -- ✅ Campo real: tipo_periodo
    valor_anterior NUMERIC,                          -- ✅ Campo real: valor_anterior
    variacion_absoluta NUMERIC,                      -- ✅ Campo real: variacion_absoluta
    variacion_porcentual NUMERIC,                    -- ✅ Campo real: variacion_porcentual
    tendencia VARCHAR(20),                           -- ✅ Campo real: tendencia
    fuente_especifica VARCHAR(150),                  -- ✅ Campo real: fuente_especifica
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## **7. REFERENCIAS CRUZADAS - OTROS SCHEMAS**

### **7.1. Referencia desde Hechos**
Los hechos NO referencian datos directamente en los prompts.

### **7.2. Referencia a Hechos (`prompts/Datos.md`)**
```json
{
  "datos_cuantitativos": [
    {
      "id": 1,
      "hecho_id": 2,                                 // ❌ REFERENCIA: Busca hecho por ID secuencial
      "indicador": "PIB trimestral",
      "valor": 3.2
    }
  ]
}
```

### **7.3. Referencia a Entidades (implícita)**
No hay referencias directas a entidades en el schema de datos, pero pueden mencionarse en el contexto.

---

## **8. VALIDACIONES (`src/utils/schema_validator.py`)**

### **8.1. CategoriaDato Enum**
```python
class CategoriaDato(str, Enum):
    ECONOMICO = "económico"
    DEMOGRAFICO = "demográfico"
    ELECTORAL = "electoral"
    SOCIAL = "social"
    PRESUPUESTARIO = "presupuestario"
    SANITARIO = "sanitario"
    AMBIENTAL = "ambiental"
    CONFLICTO = "conflicto"
    OTRO = "otro"

class TipoPeriodo(str, Enum):
    ANUAL = "anual"
    TRIMESTRAL = "trimestral"
    MENSUAL = "mensual"
    SEMANAL = "semanal"
    DIARIO = "diario"
    PUNTUAL = "puntual"
    ACUMULADO = "acumulado"

class Tendencia(str, Enum):
    AUMENTO = "aumento"
    DISMINUCION = "disminución"
    ESTABLE = "estable"
```

### **8.2. Validaciones Aplicadas**
```python
def validar_datos_cuantitativos(self, datos: List[Dict[str, Any]]) -> bool:
    for dato in datos:
        # 1. Validar ID secuencial único
        if not self.validar_id_secuencial(dato["id"], "datos"):
            return False
            
        # 2. Validar categoria enum
        if dato["categoria"] not in [c.value for c in CategoriaDato]:
            self.errores.append(f"Categoría inválida: {dato['categoria']}")
            return False
            
        # 3. Validar valor numérico
        if not isinstance(dato["valor"], (int, float)):
            self.errores.append(f"Valor debe ser numérico: {dato['valor']}")
            return False
            
        # 4. Validar fechas YYYY-MM-DD
        for campo_fecha in ["periodo_inicio", "periodo_fin"]:
            if not self.validar_fecha(dato[campo_fecha], campo_fecha):
                return False
                
        # 5. Validar referencia a hecho existente
        if not self.validar_referencia_id(dato["hecho_id"], "hechos"):
            return False
```

---

## **9. MAPEO COMPLETO DE TRANSFORMACIONES**

### **9.1. Transformación de IDs**
```
LLM Response         → Procesamiento           → PayloadBuilder            → RPC Supabase
===============      ====================      ========================    ================
"id": 1 (int)     → id_dato_cuantitativo: 1 → "id_temporal_dato": "1"   → BIGSERIAL id (BD)
"hecho_id": 2     → [referencia interna]    → "hecho_principal_relacionado_id_temporal": "2" → temp_hecho_id_map lookup
```

### **9.2. Transformación de Campos Principales**
```
LLM Response            → Procesamiento         → PayloadBuilder           → RPC Supabase
================        ===================     ======================     ================
"indicador": "PIB"   → descripcion_dato: "PIB" → "descripcion_dato": "PIB" → indicador_dato ❌
"categoria": "económico" → metadata.categoria   → "categoria": "económico"  → categoria_dato ❌
"valor": 15.2        → valor_dato: 15.2        → "valor_dato": 15.2        → valor_dato ✅
"unidad": "%"        → unidad_dato: "%"        → "unidad_dato": "%"        → unidad_dato ❌
"tendencia": "aumento" → metadata.tendencia    → "tendencia": "aumento"    → tendencia_dato ❌
```

### **9.3. Transformación de Fechas**
```
LLM Response              → Procesamiento              → PayloadBuilder                → RPC/BD
==================        ============================  ==============================  ==============
"periodo_inicio": "2023-01-01" → metadata.periodo.inicio → "periodo_referencia_inicio" → periodo_inicio ❌
"periodo_fin": "2023-03-31"     → metadata.periodo.fin   → "periodo_referencia_fin"    → periodo_fin ❌
                          → fecha_dato: "2023-01-01 - 2023-03-31" → "fecha_dato": ISO? → [no usado en RPC]
```

### **9.4. Transformación de Metadatos**
```
LLM Response                    → Procesamiento              → PayloadBuilder
========================        ===========================   =========================
"valor_anterior": 12.5       → metadata.valor_anterior    → "valor_anterior": 12.5
"variacion_absoluta": 2.7     → metadata.variacion_absoluta → "variacion_absoluta": 2.7
"variacion_porcentual": 21.6  → metadata.variacion_porcentual → "variacion_porcentual": 21.6
"ambito_geografico": [...]    → metadata.ambito_geografico → [¿campo perdido?]
```

---

## **10. INCONSISTENCIAS CRÍTICAS IDENTIFICADAS (CON RPC ACTUALIZADO COMO FUENTE DE VERDAD)**

### **10.1. Problema Principal: Field Name Mismatch**

| **Campo** | **PayloadBuilder** | **RPC ACTUALIZADO** | **Tabla BD** | **Status** |
|-----------|-------------------|---------------------|--------------|------------|
| Descripción | `descripcion_dato` ❌ | `indicador` ✅ | `indicador` | MISMATCH |
| Categoría | `categoria` ✅ | `categoria` ✅ | `categoria` | CORRECTO |
| Valor | `valor_dato` ❌ | `valor_numerico` ✅ | `valor_numerico` | MISMATCH |
| Unidad | `unidad_dato` ❌ | `unidad` ✅ | `unidad` | MISMATCH |
| Tendencia | `tendencia` ✅ | `tendencia` ✅ | `tendencia` | CORRECTO |
| Ámbito Geográfico | ❌ NO ENVÍA | `ambito_geografico` ✅ | `ambito_geografico` | FALTANTE |
| Período Inicio | `periodo_referencia_inicio` ✅ | `periodo_referencia_inicio` ✅ | `periodo_referencia_inicio` | CORRECTO |
| Período Fin | `periodo_referencia_fin` ✅ | `periodo_referencia_fin` ✅ | `periodo_referencia_fin` | CORRECTO |
| ID Hecho | `hecho_principal_relacionado_id_temporal` ❌ | `id_temporal_hecho` ✅ | temp_hecho_id_map | MISMATCH |

### **10.2. Campos Missing o No Procesados**
- `ambito_geografico` → PayloadBuilder NO lo envía pero RPC lo espera ❌
- `tipo_periodo` → PayloadBuilder envía pero RPC no procesa (no está en la tabla)
- `valor_anterior`, `variacion_absoluta`, `variacion_porcentual` → PayloadBuilder envía pero RPC no procesa (no están en el INSERT)

### **10.3. Mismatches Específicos con RPC Actualizado**
- **PayloadBuilder campo principal**: Envía `descripcion_dato` pero RPC espera `indicador` ❌
- **PayloadBuilder campo valor**: Envía `valor_dato` pero RPC espera `valor_numerico` ❌
- **PayloadBuilder campo unidad**: Envía `unidad_dato` pero RPC espera `unidad` ❌
- **PayloadBuilder referencia hecho**: Envía `hecho_principal_relacionado_id_temporal` pero RPC espera `id_temporal_hecho` ❌
- **PayloadBuilder ámbito geográfico**: NO envía el campo que RPC espera ❌

### **10.4. Fecha Management Inconsistente**
- Procesamiento: Concatena fechas como string "YYYY-MM-DD - YYYY-MM-DD"
- PayloadBuilder: ¿Convierte a ISO 8601?
- RPC: Busca campos separados `periodo_inicio/fin`

---

## **11. CAMPOS PERDIDOS EN LA TRANSFORMACIÓN**

### **11.1. Datos NO Persistidos**
- `offset_inicio_dato`, `offset_fin_dato` → No llegan a RPC
- `fuente_especifica_dato` → No llega a RPC
- `contexto_dato` → No procesado en RPC
- `relevancia_dato` → No procesado en RPC

### **11.2. Metadatos Perdidos**
- `ambito_geografico` → PayloadBuilder no lo envía o RPC no lo procesa
- `tipo_periodo` → PayloadBuilder envía pero RPC ignora
- Variaciones numéricas → PayloadBuilder envía pero RPC ignora

---

## **12. SOLUCIONES PENDIENTES (RPC YA ACTUALIZADO)**

### **12.1. ✅ RPC YA ALINEADO**
El RPC `actualizar_articulo_procesado.sql` ya fue actualizado para esperar campos sin sufijos:
- `indicador` (antes esperaba `indicador_dato`)
- `categoria` (antes esperaba `categoria_dato`)
- `valor_numerico` (antes esperaba `valor_dato`)
- `unidad` (antes esperaba `unidad_dato`)
- `tendencia` (antes esperaba `tendencia_dato`)
- `periodo_referencia_inicio/fin` (ya correctos)
- `ambito_geografico` (array, ya incluido)
- `id_temporal_hecho` (antes esperaba `id_temporal_hecho_principal`)

### **12.2. ❌ PENDIENTE: Alinear PayloadBuilder (DatoCuantitativoExtraidoItem)**
```python
# En PayloadBuilder cambiar:
descripcion_dato → indicador
valor_dato → valor_numerico
unidad_dato → unidad
hecho_principal_relacionado_id_temporal → id_temporal_hecho

# AGREGAR campo faltante:
ambito_geografico: List[str] = Field(default_factory=list)

# Los siguientes ya están correctos:
categoria ✅
tendencia ✅
periodo_referencia_inicio ✅
periodo_referencia_fin ✅
```

### **12.3. ❌ PENDIENTE: Alinear Procesamiento**
```python
# En fase_5_datos.py cambiar mapeos:
descripcion_dato → indicador
valor_dato → valor_numerico
unidad_dato → unidad
```

### **12.4. ❌ PENDIENTE: Agregar Campos Faltantes en RPC (OPCIONAL)**
```sql
-- El RPC actualizado NO procesa estos campos aunque PayloadBuilder los envía:
-- Si se desean persistir, agregar al INSERT:
tipo_periodo,                        -- v_dato->>'tipo_periodo'
valor_anterior,                      -- (v_dato->>'valor_anterior')::NUMERIC
variacion_absoluta,                  -- (v_dato->>'variacion_absoluta')::NUMERIC
variacion_porcentual,                -- (v_dato->>'variacion_porcentual')::NUMERIC
fuente_especifica                    -- v_dato->>'fuente_especifica'
```

### **12.5. ❌ PENDIENTE: Implementar ID Mapping**
```python
def crear_mapeo_ids_hechos_para_datos(hechos_procesados):
    """Crear mapeo para referencias cruzadas datos → hechos"""
    mapeo = {}
    for idx, hecho in enumerate(hechos_procesados, 1):
        mapeo[idx] = hecho.id_temporal  # idx secuencial → ID temporal
    return mapeo
```

**FUENTE DE VERDAD ACTUAL**: RPC `actualizar_articulo_procesado.sql` con campos sin sufijos y estructura específica.