# Análisis Arquitectónico Correcto - Module Connector
**Fecha:** 2025-07-16
**Hora:** 12:45 UTC
**Análisis:** Arquitectura de Volúmenes y Flujo de Datos

## Aclaración Arquitectónica

Tienes razón en cuestionar dónde debe estar `shared_data:/data`. El análisis correcto es:

### Flujo de Datos Diseñado
```
Spider (scrapyd) → JsonWriterPipeline → /data/scrapy_output/pending → Connector → Pipeline
```

### Configuración Actual de Volúmenes
```yaml
# ✅ Correcto - Connector LEE de /data/scrapy_output/pending
module_connector:
  volumes:
    - shared_data:/data

# ✅ Correcto - Para procesamiento local si es necesario  
module_scraper:
  volumes:
    - shared_data:/data

# ❌ Problema - Scrapyd ESCRIBE a /data/scrapy_output/pending pero no tiene acceso
scrapyd:
  volumes:
    - # NO tiene shared_data:/data
```

## Problema Identificado

**El problema NO es que el connector no tenga el volumen.** El problema es que:

1. **Scrapyd ejecuta los spiders** y por tanto el `JsonWriterPipeline`
2. **JsonWriterPipeline intenta escribir** a `/data/scrapy_output/pending`
3. **Scrapyd NO tiene acceso** al volumen `shared_data:/data`
4. **Connector espera archivos** en `/data/scrapy_output/pending` (que sí tiene acceso)

## Evidencia del Problema

### Configuración Correcta del Connector
```python
# config.py línea 8
SCRAPER_OUTPUT_DIR = os.getenv('SCRAPER_OUTPUT_DIR', '/pruebas_pipeline/scrapy_output/pending')

# .env línea 86
SCRAPER_OUTPUT_DIR="/data/scrapy_output/pending"
```

### Logs del Connector
```
2025-07-16 08:53:50 | INFO | - Input directory: /data/scrapy_output/pending
2025-07-16 08:53:50 | INFO | Directory structure verified:
2025-07-16 08:53:50 | INFO |   - Input: /data/scrapy_output/pending ✅
2025-07-16 08:53:50 | INFO | Starting to monitor directory: /data/scrapy_output/pending
```

### Problema en Scrapyd
```
2025-07-16 11:28:45 [json_writer] ERROR: Error creating output directory: [Errno 13] Permission denied: '/data'
```

## Solución Correcta

El volumen `shared_data:/data` debe estar en **ambos contenedores**:

### 1. Connector (Ya está correcto)
```yaml
module_connector:
  volumes:
    - shared_data:/data  # ✅ Ya existe - LEE archivos
```

### 2. Scrapyd (Falta agregar)
```yaml
scrapyd:
  volumes:
    - ./src/module_scraper:/app
    - ./src/module_scraper/scrapyd.conf:/etc/scrapyd/scrapyd.conf:ro
    - scrapyd_eggs:/var/lib/scrapyd/eggs
    - scrapyd_logs:/var/lib/scrapyd/logs
    + - shared_data:/data  # ⚠️ NECESARIO - ESCRIBE archivos
```

## Diagrama de Arquitectura Correcta

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Scrapyd       │    │   Connector     │    │   Pipeline      │
│                 │    │                 │    │                 │
│ JsonWriterPipe  │───▶│ Monitor files   │───▶│ Process items   │
│ WRITES to       │    │ READS from      │    │                 │
│ /data/scrapy_   │    │ /data/scrapy_   │    │                 │
│ output/pending  │    │ output/pending  │    │                 │
│                 │    │                 │    │                 │
│ Needs:          │    │ Has:            │    │                 │
│ shared_data:/   │    │ shared_data:/   │    │                 │
│ data ❌         │    │ data ✅         │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Por Qué module_scraper También Tiene el Volumen

El contenedor `module_scraper` probablemente está diseñado para:
1. **Desarrollo local:** Ejecutar spiders directamente (no via scrapyd)
2. **Debugging:** Acceso directo a archivos generados
3. **Herramientas:** Utilitarios para procesar archivos

Pero en **producción**, los spiders se ejecutan en `scrapyd`, no en `module_scraper`.

## Conclusión

Tu observación es correcta en el sentido de que el connector debe tener acceso al volumen `shared_data:/data` para leer archivos, pero el problema es que **scrapyd también necesita acceso** para escribir esos archivos.

**Solución:**
- Connector: `shared_data:/data` (ya existe) ✅
- Scrapyd: `shared_data:/data` (falta agregar) ❌

El diagnóstico original es correcto: falta el volumen en `scrapyd`.