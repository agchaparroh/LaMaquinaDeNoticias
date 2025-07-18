# Diagnóstico de Sistema de IDs - La Máquina de Noticias
**Fecha:** 2025-07-18
**Objetivo:** Verificar el funcionamiento del sistema de propagación de IDs desde el scraper hasta la persistencia en Supabase

## Resumen de Cambios Implementados

### 1. Scraper (module_scraper)
- **Archivo:** `src/module_scraper/scraper_core/pipelines/storage.py`
- **Cambio:** Extrae el ID del artículo después del upsert y lo añade al item
- **Líneas:** 256-269

### 2. Connector (module_connector) 
- **Archivo:** `src/module_connector/src/models.py`
- **Cambio:** Añadido campo `articulo_id: Optional[int]` al modelo
- **Líneas:** 17-18

### 3. Pipeline (module_pipeline)
- **Archivo:** `src/module_pipeline/src/controller.py`
- **Cambio:** Usa el `articulo_id` para generar el ID del fragmento
- **Líneas:** 187-196

## Estado del Sistema
- **Docker Compose:** Reiniciado con las nuevas imágenes
- **Servicios:** Iniciándose...

## Plan de Prueba
1. Ejecutar spider infobae con un artículo
2. Monitorizar logs del scraper para ver la captura del ID
3. Verificar que el JSON exportado contiene el `articulo_id`
4. Seguir el flujo en el connector
5. Observar el uso del ID en el pipeline
6. Confirmar persistencia exitosa en Supabase

## Logs de Ejecución

### Verificación de Estado de Servicios
```
Timestamp: 2025-07-18 04:30
Estado: Todos los contenedores iniciándose correctamente
```

### Resultados del Test End-to-End

#### ✅ Fase 1: Scraper - EXITOSO
- El scraper captura correctamente el ID de la base de datos
- Ejemplo: "ID del artículo guardado: 1100"
- El ID se añade exitosamente al item: "Article ID 1100 added to item for propagation through the pipeline"
- El JSON exportado contiene el campo `articulo_id`: confirmado con valor 1203

#### ✅ Fase 2: JSON Export - EXITOSO
- Los archivos JSON.gz contienen el campo `articulo_id`
- Verificación: `articulo_id: 1203` presente en el JSON exportado

#### ⚠️ Fase 3: Connector - PROBLEMA DETECTADO
- El connector está generando su propio ID (ej: "art_807079") en lugar de usar el `articulo_id`
- Código problemático en `models.py:145`: `data['id'] = f"art_{hash(data['url']) % 1000000:06d}"`
- El connector lee el campo `id` pero no el campo `articulo_id`

#### ❌ Fase 4: Pipeline - FALLA
- Pipeline reporta: "No se encontró articulo_id en datos, usando UUID: da37d4e5-90cb-4161-9d3f-e014ac4117e4"
- Error en persistencia: "Error en insertar_articulo_completo: Campos requeridos faltantes en payload articulo"

## Diagnóstico

### Problema Principal
El connector no está propagando el `articulo_id` al pipeline porque:
1. El connector busca el campo `id` en lugar de `articulo_id`
2. Si no encuentra `id`, genera uno nuevo basado en el hash de la URL
3. El `articulo_id` de la base de datos se pierde en esta traducción

### Solución Requerida
Modificar el connector para:
1. Preservar el campo `articulo_id` cuando está presente
2. Usar `articulo_id` como `id` si está disponible
3. Solo generar un ID nuevo si no hay `articulo_id`

## Estado Final
- ✅ Sistema de IDs implementado en scraper
- ✅ Propagación hasta JSON
- ❌ Propagación connector → pipeline requiere ajuste
- ❌ Persistencia en Supabase bloqueada por falta de ID

---
*Prueba ejecutada: 2025-07-18 04:30-04:35*