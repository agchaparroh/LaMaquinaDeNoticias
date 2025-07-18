# VERDAD ABSOLUTA DESDE SUPABASE

## ESTRUCTURA REAL DE LA TABLA `articulos`

### Campos confirmados en la base de datos:

| Campo | Tipo | Nullable | Observaciones |
|-------|------|----------|---------------|
| `titular` | text | NO | ✅ CONFIRMADO: El campo se llama `titular`, NO `titulo` |
| `area_geografica` | varchar | NO | ✅ CONFIRMADO: Se usa `area_geografica`, NO `pais` |
| `pais_publicacion` | varchar | YES | Campo separado para país de publicación |
| `contenido_texto` | text | YES | Contenido del artículo |
| `medio` | varchar | NO | Nombre del medio |
| `tipo_medio` | varchar | NO | Tipo de medio |
| `url` | text | YES | URL del artículo |
| `autor` | varchar | YES | Autor del artículo |
| `idioma` | varchar | NO | Idioma del artículo |
| `fecha_publicacion` | timestamptz | NO | Fecha de publicación |
| `fecha_recopilacion` | timestamptz | NO | Fecha de recopilación |
| `es_opinion` | boolean | NO | Si es opinión |
| `es_oficial` | boolean | NO | Si es oficial |

### Campos que NO existen en la tabla:
- ❌ `titulo` - NO EXISTE, el campo correcto es `titular`
- ❌ `pais` - NO EXISTE, el campo correcto es `area_geografica`
- ❌ `articulo_id` - NO EXISTE, el campo es `id`
- ❌ `contenido_html` - NO EXISTE en la tabla articulos
- ❌ `medio_url_principal` - NO EXISTE en la tabla articulos
- ❌ `fuente_original` - NO EXISTE en la tabla articulos
- ❌ `metadata` - NO EXISTE en la tabla articulos

## DATOS REALES EN PRODUCCIÓN

Ejemplo de artículos reales en Supabase:
```
id: 1203
titular: "Carlos Antonio Vélez deseó suerte a Quintero..."
area_geografica: "HISPANOAMERICA"
pais_publicacion: null
medio: "Infobae"
tipo_medio: "otro"
```

## CONCLUSIÓN DEFINITIVA

1. **La base de datos usa `titular`, NO `titulo`**
2. **La base de datos usa `area_geografica`, NO `pais`**
3. **El JSON del scraper está mal** - usa nomenclatura incorrecta
4. **El pipeline está bien** - espera los campos correctos de la BD

## FUNCIÓN DE INSERCIÓN EN SUPABASE

La función `insertar_articulo_completo` que usa el scraper espera:
```sql
datos_json->'articulo_metadata'->>'titular'  -- NO 'titulo'
datos_json->'articulo_metadata'->>'medio'
datos_json->'articulo_metadata'->>'pais_publicacion'
datos_json->'articulo_metadata'->>'tipo_medio'
-- etc.
```

## CORRECCIÓN NECESARIA

El problema está en el JSON de prueba que NO coincide con lo que espera Supabase:

1. **El JSON de prueba tiene `titulo`** pero Supabase espera `titular`
2. **El JSON de prueba tiene `articulo_id`** pero en Supabase es `id`
3. **El JSON tiene campos extra** que no van a la tabla articulos:
   - `contenido_html`
   - `medio_url_principal` 
   - `fuente_original`

### ORIGEN DEL PROBLEMA

Los JSONs de prueba parecen ser de una versión antigua del scraper o fueron generados manualmente con campos incorrectos. El scraper real DEBE enviar `titular` porque así lo espera la función de Supabase.

### SOLUCIÓN

1. **Opción A**: Actualizar los JSONs de prueba para usar la nomenclatura correcta (`titular` en lugar de `titulo`)
2. **Opción B**: Agregar lógica de mapeo en el controller para manejar JSONs legacy con campos incorrectos