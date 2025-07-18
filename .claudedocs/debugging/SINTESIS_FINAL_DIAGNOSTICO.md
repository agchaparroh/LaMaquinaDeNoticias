# SÍNTESIS FINAL DEL DIAGNÓSTICO COMPLETO

## HIPÓTESIS CONFIRMADAS:

### ✅ H2: Error en transformación (CONFIRMADA)
- Controller línea 202 busca `articulo_data['titular']` pero debería buscar `titulo`
- Crea campo `pais` cuando modelo espera `area_geografica`
- Incluye campos que el modelo rechaza

### ✅ H6: Configuración de Pydantic (CONFIRMADA)
- ArticuloProcesableItem hereda `extra="forbid"`
- Rechaza cualquier campo no definido en el modelo
- Causa los errores "Extra inputs are not permitted"

### ✅ H7: Construcción del diccionario (CONFIRMADA)
- El diccionario se construye mal con campos incorrectos
- Intenta leer campos que no existen
- Crea campos con nombres equivocados

### ✅ H8: Flujo desde endpoint (CONFIRMADA)
- ArticuloInItem no valida correctamente porque espera `titular` pero recibe `titulo`
- Con `extra="allow"`, el campo pasa como extra
- El controller recibe datos mal estructurados

## HIPÓTESIS DESCARTADAS:

### ❌ H1: Incompatibilidad JSON vs Modelo
- Sí hay incompatibilidad, pero es un síntoma, no la causa raíz

### ❌ H3: Endpoint sin validar
- El endpoint SÍ valida, pero la validación es permisiva

### ❌ H4: Múltiples versiones del modelo
- Solo existe una versión de ArticuloProcesableItem

### ❌ H5: JSON obsoleto
- Los JSONs son actuales, todos tienen la misma estructura

## CAUSA RAÍZ IDENTIFICADA:

### PROBLEMA PRINCIPAL: Desalineación entre Scraper y Pipeline

1. **El scraper genera JSONs con nomenclatura específica**:
   - Campo `titulo` (no `titular`)
   - Campo `articulo_id`
   - Campos extra como `contenido_html`, `medio_url_principal`

2. **El pipeline espera nomenclatura diferente**:
   - Campo `titular` (no `titulo`)
   - Campo `area_geografica` (no `pais`)
   - No acepta campos extra por `extra="forbid"`

3. **El mapeo en controller.py está mal implementado**:
   - Busca campos con nombres incorrectos
   - Crea campos que el modelo rechaza
   - No maneja la diferencia de nomenclatura

4. **ArticuloInItem es permisivo pero no transforma**:
   - Acepta campos extra en desarrollo
   - No mapea `titulo` a `titular`
   - Pasa el problema al siguiente nivel

## SOLUCIÓN REQUERIDA:

Necesitamos corregir el mapeo en el controller para:
1. Leer `titulo` del JSON (no `titular`)
2. Mapear correctamente a los campos esperados por ArticuloProcesableItem
3. NO incluir campos que el modelo no acepta
4. Manejar el caso donde el JSON viene del scraper con nomenclatura diferente