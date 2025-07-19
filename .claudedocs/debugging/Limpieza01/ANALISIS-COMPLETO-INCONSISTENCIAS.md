# ANÁLISIS COMPLETO: Inconsistencias de Nomenclatura Pipeline vs RPC

## Resumen Ejecutivo

Tras un análisis exhaustivo del flujo de datos, se han identificado inconsistencias de nomenclatura entre:
- **Pipeline** (pipeline_coordinator.py): Cómo se envían los datos
- **RPC** (actualizar_articulo_procesado.sql): Qué campos espera recibir

## 1. ENTIDADES ❌ INCONSISTENTE

### Lo que envía el Pipeline:
```json
{
  "id": "1",
  "nombre": "EEUU",                    // ❌ Sin sufijo
  "tipo": "ORGANIZACION",              // ❌ Sin sufijo
  "descripcion": "Entidad extraída...", // ❌ Sin sufijo
  "relevancia_entidad_articulo": 8,
  "metadata_entidad": {...}
}
```

### Lo que espera la RPC:
```sql
v_entidad->>'nombre_entidad'      -- ❌ Con sufijo
v_entidad->>'tipo_entidad'        -- ❌ Con sufijo  
v_entidad->>'descripcion_entidad' -- ❌ Con sufijo
v_entidad->>'relevancia_entidad'  -- ⚠️  Nota: campo diferente
v_entidad->'metadata_entidad'     -- ✅ Coincide
```

### Tabla en BD:
- Columnas: `nombre`, `tipo`, `descripcion` (sin sufijo)

## 2. HECHOS ✅ CONSISTENTE

### Lo que envía el Pipeline:
```json
{
  "id_temporal_hecho": "1",
  "descripcion_hecho": "Trump anuncia...",  // ✅ Con sufijo
  "tipo_hecho": "DECLARACION",              // ✅ Con sufijo
  "relevancia_hecho": 8,                    // ✅ Con sufijo
  "fecha_ocurrencia_hecho_inicio": "2025-07-09",
  "metadata_hecho": {...}                   // ✅ Con sufijo
}
```

### Lo que espera la RPC:
```sql
v_hecho->>'descripcion_hecho'  -- ✅ Coincide
v_hecho->>'tipo_hecho'         -- ✅ Coincide
v_hecho->>'relevancia_hecho'   -- ✅ Coincide
```

### Tabla en BD:
- Columnas: `contenido`, `tipo_hecho`, `importancia`
- Nota: La RPC hace mapeo correcto de `descripcion_hecho` → `contenido`

## 3. CITAS TEXTUALES ✅ CONSISTENTE

### Lo que envía el Pipeline:
```json
{
  "id_temporal_cita": "1",
  "texto_cita": "Vamos a lograr la paz",    // ✅ Con sufijo
  "contexto_cita": "En rueda de prensa...", // ✅ Con sufijo
  "relevancia_cita": 5                      // ✅ Con sufijo
}
```

### Lo que espera la RPC:
```sql
v_cita->>'texto_cita'      -- ✅ Coincide
v_cita->>'contexto_cita'   -- ✅ Coincide
v_cita->>'relevancia_cita' -- ✅ Coincide
```

### Tabla en BD:
- Columnas: `cita`, `contexto`, `relevancia`
- La RPC hace mapeo correcto de `texto_cita` → `cita`

## 4. DATOS CUANTITATIVOS ⚠️ PARCIALMENTE INCONSISTENTE

### Lo que envía el Pipeline:
```json
{
  "id_temporal_dato": "1",
  "descripcion_dato": "Número de rehenes",  // ⚠️ Campo diferente
  "valor_dato": 10,                         // ✅ Coincide
  "unidad_dato": "personas",                // ✅ Coincide
  "fecha_dato": "2025-07-09"
}
```

### Lo que espera la RPC:
```sql
v_dato->>'indicador_dato'  -- ❌ No enviado por pipeline
v_dato->>'categoria_dato'  -- ❌ No enviado por pipeline
v_dato->>'valor_dato'      -- ✅ Coincide
v_dato->>'unidad_dato'     -- ✅ Coincide
v_dato->>'tendencia_dato'  -- ❌ No enviado por pipeline
```

### Tabla en BD:
- Columnas: `indicador`, `categoria`, `valor_numerico`, `unidad`, `tendencia`
- Problema: El pipeline envía `descripcion_dato` pero la RPC espera `indicador_dato` y `categoria_dato`

## Análisis de Impacto

### 1. **Errores Actuales**
- ❌ **Entidades**: Error "null value in column 'nombre'" porque la RPC busca campos con sufijo que no existen

### 2. **Errores Potenciales**
- ⚠️ **Datos Cuantitativos**: Posibles valores NULL en `indicador` y `categoria` si estas columnas son NOT NULL

### 3. **Sin Errores (pero inconsistente)**
- ✅ **Hechos**: Funciona porque usa sufijos consistentemente
- ✅ **Citas**: Funciona porque usa sufijos consistentemente

## Recomendaciones

### Opción 1: Modificar RPC (Recomendada para Entidades)
```sql
-- Cambiar en actualizar_articulo_procesado.sql:
-- DE:
v_entidad->>'nombre_entidad'
v_entidad->>'tipo_entidad'
v_entidad->>'descripcion_entidad'

-- A:
v_entidad->>'nombre'
v_entidad->>'tipo'
v_entidad->>'descripcion'
```

### Opción 2: Mejorar Pipeline para Datos Cuantitativos
```python
# En pipeline_coordinator.py, cambiar:
datos_data.append({
    "indicador_dato": dato.descripcion_dato,  # Mapear descripcion → indicador
    "categoria_dato": "general",              # Valor por defecto
    "valor_dato": dato.valor_dato,
    "unidad_dato": dato.unidad_dato,
    "tendencia_dato": None                    # Agregar campo faltante
})
```

## Principio de Diseño Violado

La inconsistencia principal es que:
- **Entidades**: Usa campos SIN sufijo (coincide con BD) ✅
- **Hechos, Citas, Datos**: Usan campos CON sufijo (no coinciden con BD) ❌

Esto viola el principio de **consistencia** en el diseño de APIs.