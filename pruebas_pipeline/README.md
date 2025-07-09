# 📁 Directorio pruebas_pipeline - La Máquina de Noticias

## 📋 Tabla de Contenidos
- [Descripción General](#descripción-general)
- [Estructura del Directorio](#estructura-del-directorio)
- [Flujo de Trabajo](#flujo-de-trabajo)
- [Configuración](#configuración)
- [Guía de Uso](#guía-de-uso)
- [Casos de Prueba](#casos-de-prueba)
- [Monitoreo y Métricas](#monitoreo-y-métricas)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

## 🎯 Descripción General

El directorio `pruebas_pipeline` es el sistema de almacenamiento intermedio y debugging para el flujo de procesamiento de noticias en modo desarrollo. Permite probar todo el pipeline sin necesidad de Supabase, facilitando el desarrollo local y la identificación de problemas.

### Propósitos Principales:
- 🔄 **Flujo de datos**: Comunicación entre módulos mediante archivos
- 🐛 **Debugging**: Inspección detallada de cada fase del procesamiento
- 📊 **Métricas**: Análisis de rendimiento y calidad
- 💾 **Persistencia local**: Alternativa a Supabase para desarrollo

## 📂 Estructura del Directorio

```
pruebas_pipeline/
├── scrapy_output/                    # Salida del scraper
│   └── pending/                      # Artículos pendientes de procesar (.json.gz)
│
└── development_outputs/              # Resultados del pipeline (solo en DEVELOPMENT_MODE=true)
    ├── 01_articulos_extraidos/       # Artículos originales organizados
    │   ├── por_fecha/                # Agrupados por fecha (YYYY-MM-DD)
    │   └── por_spider/               # Agrupados por spider/fuente
    │       ├── centroamerica360_region/
    │       ├── europa_press_latam/
    │       └── infobae_america_latina/
    │
    ├── 02_fases_pipeline/            # Resultados de cada fase de procesamiento
    │   ├── fase_1_triaje/
    │   │   ├── contenido_limpio/     # Texto limpio sin HTML
    │   │   ├── idioma_detectado/     # Detección de idioma
    │   │   └── relevancia_evaluada/  # Score de relevancia
    │   │
    │   ├── fase_2_elementos_basicos/
    │   │   ├── entidades_identificadas/  # Personas, orgs, lugares
    │   │   ├── hechos_extraidos/        # Eventos y afirmaciones
    │   │   └── clasificacion_asignada/   # Categorías temáticas
    │   │
    │   ├── fase_3_citas_datos/
    │   │   ├── citas_textuales/          # Declaraciones con atribución
    │   │   ├── datos_cuantitativos/      # Números y estadísticas
    │   │   └── fuentes_referenciadas/    # Referencias y enlaces
    │   │
    │   └── fase_4_normalizacion/
    │       ├── entidades_vinculadas/     # Entidades normalizadas
    │       ├── relaciones_detectadas/    # Conexiones entre entidades
    │       └── metadatos_enriquecidos/   # Metadata adicional
    │
    ├── 03_resultados_finales/        # Procesamiento completo
    │   ├── exitosos/                 # Artículos procesados sin errores
    │   └── fallidos/                 # Artículos con errores
    │       └── logs_errores/         # Logs detallados de fallos
    │
    ├── 04_metricas_rendimiento/     # Análisis de performance
    │   ├── content_quality.json      # Calidad del contenido extraído
    │   ├── error_analysis.json       # Análisis de errores
    │   ├── pipeline_timing.json      # Tiempos de procesamiento
    │   └── spider_stats.json         # Estadísticas por spider
    │
    └── 05_comparativas/              # Análisis comparativos
        ├── antes_vs_despues/         # Comparación pre/post proceso
        ├── calidad_contenido/        # Evaluación de calidad
        └── efectividad_llm/          # Performance de IA/LLMs
```

## 🔄 Flujo de Trabajo

### 1. **Scraper → scrapy_output/pending/**
```python
# El scraper genera archivos comprimidos
article_europa_press_20250108_123456_titulo_abc123.json.gz
```

### 2. **Connector monitorea y procesa**
```bash
# El connector revisa cada 5 segundos
scrapy_output/pending/ → Lee archivo → Envía a Pipeline API → Mueve a completed/
```

### 3. **Pipeline procesa en 4 fases**
```
Fase 1: Triaje → Limpieza, idioma, relevancia
Fase 2: Extracción → Hechos, entidades, clasificación
Fase 3: Citas/Datos → Citas textuales, números, fuentes
Fase 4: Normalización → Vinculación, relaciones, enriquecimiento
```

### 4. **Almacenamiento según modo**
- **DEVELOPMENT_MODE=true**: Guarda en `development_outputs/`
- **DEVELOPMENT_MODE=false**: Persiste en Supabase

## ⚙️ Configuración

### Toggle de Modo Desarrollo

El proyecto incluye un script `toggle-dev-mode.sh` para cambiar fácilmente entre modo desarrollo y producción:

```bash
# Ver estado actual
./toggle-dev-mode.sh status

# Activar modo desarrollo (guarda en pruebas_pipeline/)
./toggle-dev-mode.sh enable

# Desactivar modo desarrollo (guarda en Supabase)
./toggle-dev-mode.sh disable

# Alternar entre modos
./toggle-dev-mode.sh toggle
```

**Importante**: Después de cambiar el modo, reinicia los servicios:
```bash
docker-compose -f docker-compose-dev.yml restart
```

### Variables de Entorno Requeridas

```bash
# .env en la raíz del proyecto

# Activar modo desarrollo (IMPORTANTE para usar pruebas_pipeline)
DEVELOPMENT_MODE=true  # Usa ./toggle-dev-mode.sh para cambiar esto

# Directorios del flujo
SCRAPER_OUTPUT_DIR=/pruebas_pipeline/scrapy_output/pending
DEVELOPMENT_OUTPUT_DIR=/pruebas_pipeline/development_outputs

# Configuración del connector
PIPELINE_PENDING_DIR=/pruebas_pipeline/pipeline_input/pending
PIPELINE_COMPLETED_DIR=/pruebas_pipeline/pipeline_input/completed
PIPELINE_ERROR_DIR=/pruebas_pipeline/pipeline_input/error

# Pipeline API
PIPELINE_API_URL=http://module_pipeline:8003

# Configuración del scraper
ENABLE_PIPELINE_EXPORT=true
EXPORT_COMPRESSION_LEVEL=6
```

### Configuración de Docker Compose

```yaml
# docker-compose-dev.yml disponible para desarrollo
volumes:
  - ./pruebas_pipeline:/pruebas_pipeline
```

## 📚 Guía de Uso

### 1. Preparar el Entorno

```bash
# Crear estructura de directorios si no existe
mkdir -p pruebas_pipeline/scrapy_output/pending
mkdir -p pruebas_pipeline/development_outputs/{01_articulos_extraidos,02_fases_pipeline,03_resultados_finales,04_metricas_rendimiento,05_comparativas}

# Verificar permisos
chmod -R 755 pruebas_pipeline/
```

### 2. Iniciar Servicios en Modo Desarrollo

```bash
# Activar modo desarrollo usando el script
./toggle-dev-mode.sh enable

# Iniciar servicios con docker-compose-dev.yml
docker-compose -f docker-compose-dev.yml up -d

# Verificar logs
docker-compose -f docker-compose-dev.yml logs -f module_pipeline
```

**Servicios incluidos en docker-compose-dev.yml:**
- `module_scraper` - Extracción de noticias
- `module_connector` - Conexión entre servicios
- `module_pipeline` - Procesamiento con IA
- `scrapyd` - Servidor de spiders (puerto 6800)
- `scrapydweb` - Dashboard de gestión (puerto 5000)
- `redis` - Cache (puerto 6379)
- `flaresolverr` - Bypass de Cloudflare (puerto 8191)

### 3. Ejecutar Spider de Prueba

```bash
# Opción 1: Ejecutar spider específico
docker-compose exec module_scraper scrapy crawl europa_press_latam

# Opción 2: Usar Scrapyd
curl http://localhost:6800/schedule.json \
  -d project=scraper_project \
  -d spider=europa_press_latam
```

### 4. Monitorear Procesamiento

```bash
# Ver archivos pendientes
ls -la pruebas_pipeline/scrapy_output/pending/

# Monitorear logs del connector
docker-compose -f docker-compose-dev.yml logs -f module_connector

# Verificar resultados
find pruebas_pipeline/development_outputs -name "*.json" -type f | head -10

# Verificar FlareSolverr (si necesitas bypass de Cloudflare)
curl http://localhost:8191/v1
```

## 🧪 Casos de Prueba

### Test 1: Procesamiento Básico
```bash
# 1. Crear archivo de prueba
cat > test_article.json << EOF
{
  "url": "https://example.com/test",
  "titular": "Noticia de prueba para pipeline",
  "contenido_texto": "Este es el contenido de prueba con entidades como Juan Pérez y Google.",
  "fecha_publicacion": "2025-01-08T10:00:00Z",
  "medio": "Test Media",
  "area_geografica": "América Latina",
  "tipo_medio": "digital"
}
EOF

# 2. Comprimir y colocar en pending
gzip -c test_article.json > pruebas_pipeline/scrapy_output/pending/test_article.json.gz

# 3. Observar procesamiento
watch -n 1 'ls -la pruebas_pipeline/scrapy_output/pending/'
```

### Test 2: Verificar Fases del Pipeline
```bash
# Después del procesamiento, verificar cada fase
find pruebas_pipeline/development_outputs/02_fases_pipeline -name "*.json" -exec echo {} \; -exec cat {} \; -exec echo -e "\n---\n" \;
```

### Test 3: Análisis de Errores
```bash
# Forzar un error con JSON malformado
echo "invalid json" | gzip > pruebas_pipeline/scrapy_output/pending/bad_article.json.gz

# Verificar error
cat pruebas_pipeline/development_outputs/04_metricas_rendimiento/error_analysis.json
```

## 📊 Monitoreo y Métricas

### Métricas Disponibles

1. **content_quality.json**
```json
{
  "metrics": [{
    "fragmento_id": "uuid",
    "timestamp": "2025-01-08T10:00:00Z",
    "entidades_count": 15,
    "hechos_count": 8,
    "citas_count": 3
  }]
}
```

2. **pipeline_timing.json**
```json
{
  "timing_metrics": [{
    "fragmento_id": "uuid",
    "processing_time": 2.5,
    "fase_1_time": 0.3,
    "fase_2_time": 1.2,
    "fase_3_time": 0.6,
    "fase_4_time": 0.4
  }]
}
```

### Scripts de Análisis

```bash
# Contar artículos procesados
find pruebas_pipeline/development_outputs/03_resultados_finales/exitosos -name "*.json" | wc -l

# Ver últimos errores
tail -n 50 pruebas_pipeline/development_outputs/04_metricas_rendimiento/error_analysis.json

# Estadísticas por spider
jq '.spiders' pruebas_pipeline/development_outputs/04_metricas_rendimiento/spider_stats.json
```

## 🔧 Troubleshooting

### Problema: Archivos no se procesan
```bash
# Verificar que el connector está activo
docker-compose ps module_connector

# Revisar logs
docker-compose logs --tail=100 module_connector

# Verificar permisos
ls -la pruebas_pipeline/scrapy_output/pending/
```

### Problema: Errores de pipeline
```bash
# Ver logs detallados del pipeline
docker-compose logs --tail=200 module_pipeline | grep ERROR

# Verificar health
curl http://localhost:8003/health
```

### Problema: Métricas vacías
```bash
# Inicializar archivos de métricas
echo '{}' > pruebas_pipeline/development_outputs/04_metricas_rendimiento/content_quality.json
echo '{}' > pruebas_pipeline/development_outputs/04_metricas_rendimiento/pipeline_timing.json
echo '{}' > pruebas_pipeline/development_outputs/04_metricas_rendimiento/spider_stats.json
echo '{"errors": []}' > pruebas_pipeline/development_outputs/04_metricas_rendimiento/error_analysis.json
```

## ❓ FAQ

### ¿Cómo cambio entre modo desarrollo y producción?
Modifica `DEVELOPMENT_MODE` en `.env`:
- `DEVELOPMENT_MODE=true`: Usa pruebas_pipeline
- `DEVELOPMENT_MODE=false`: Usa Supabase

### ¿Puedo reprocesar archivos fallidos?
Sí, mueve los archivos de `fallidos/` back a `scrapy_output/pending/`:
```bash
mv pruebas_pipeline/development_outputs/03_resultados_finales/fallidos/*.json.gz \
   pruebas_pipeline/scrapy_output/pending/
```

### ¿Cómo limpio los resultados antiguos?
```bash
# Limpiar resultados de más de 7 días
find pruebas_pipeline/development_outputs -name "*.json" -mtime +7 -delete
```

### ¿Puedo usar esto en producción?
No se recomienda. Este sistema está diseñado para desarrollo y debugging. En producción usa Supabase para persistencia confiable.

### ¿Cómo agrego un nuevo spider?
1. Crea el spider en `src/module_scraper/scraper_core/spiders/`
2. Asegúrate de que use `JsonGzExportPipeline`
3. Crea directorio: `mkdir -p pruebas_pipeline/development_outputs/01_articulos_extraidos/por_spider/tu_spider`

---

## 📞 Soporte

Para dudas o problemas:
1. Revisa los logs: `docker-compose logs`
2. Consulta la documentación principal: `/docs/`
3. Abre un issue en el repositorio

---

**Última actualización**: Enero 2025