# Spider Factory 2.0

Sistema inteligente de generación automática de spiders para La Máquina de Noticias.

## 🚀 Características Principales

- **Análisis Inteligente**: Detecta automáticamente la mejor estrategia de extracción (RSS, Scraping, Playwright)
- **Generación Automática**: Crea spiders optimizados según el tipo de sitio web
- **Cache Inteligente**: Sistema de cache con TTL de 7 días para optimizar análisis repetidos
- **Gestión de Patrones**: Aprende y reutiliza patrones de extracción exitosos
- **Métricas en Tiempo Real**: Monitoreo de KPIs y rendimiento del sistema
- **API RESTful**: Integración sencilla con otros módulos del sistema

## 📋 Campos Obligatorios (v2.0)

Todos los spiders generados incluyen los siguientes campos obligatorios:

### Campos de Clase
- `name`: Formato `{medio}_{seccion}` (ej: `el_pais_internacional`)
- `medio`: Nombre del medio de comunicación
- `seccion`: Sección específica del medio
- `area_geografica`: Una de las 28 áreas geográficas válidas
- `tipo_medio`: `diario`, `revista` o `agencia`

### Campos de Items
- `titular`: Título del artículo (NO usar 'titulo')
- `medio`: Nombre del medio
- `medio_url_principal`: URL principal del artículo
- `area_geografica`: Área geográfica del medio
- `tipo_medio`: Tipo de medio
- `seccion`: Sección del artículo
- `fecha_publicacion`: Fecha de publicación
- `contenido_texto`: Contenido en texto plano
- `contenido_html`: Contenido en HTML
- `fuente`: Origen del contenido (`spider_factory_2.0`)
- `metadata`: Información adicional del spider

## 🛠️ Instalación

### Requisitos
- Python 3.9+
- Redis 6.0+
- Docker y Docker Compose

### Configuración

1. Clonar el repositorio
2. Configurar variables de entorno:

```bash
# .env
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
FIRECRAWL_API_KEY=your_api_key_here
SPIDER_OUTPUT_PATH=/src/module_scraper/scraper_core/spiders
```

3. Iniciar servicios:

```bash
docker-compose up -d spider_factory_backend redis nginx_reverse_proxy
```

## 📖 Uso

### API Endpoints

#### Analizar un sitio web
```bash
curl -X POST http://localhost/spider-factory/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://elpais.com/internacional",
    "medio": "El País",
    "seccion": "Internacional",
    "area_geografica": "ESPAÑA",
    "tipo_medio": "diario",
    "frecuencia_minutos": 60
  }'
```

#### Generar un spider
```bash
curl -X POST http://localhost/spider-factory/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "medio": "El País",
    "seccion": "Internacional",
    "area_geografica": "ESPAÑA",
    "tipo_medio": "diario",
    "url": "https://elpais.com/internacional",
    "frecuencia_minutos": 60
  }'
```

#### Verificar duplicados
```bash
curl -X POST http://localhost/spider-factory/api/check-duplicate \
  -H "Content-Type: application/json" \
  -d '{
    "medio": "El País",
    "seccion": "Internacional"
  }'
```

#### Procesamiento en batch (CSV)
```bash
curl -X POST http://localhost/spider-factory/api/batch/analyze \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sites.csv"
```

### Formato CSV

El archivo CSV debe incluir las siguientes columnas:

```csv
medio,seccion,url,area_geografica,tipo_medio,frecuencia_minutos,rss_url
El País,Internacional,https://elpais.com/internacional,ESPAÑA,diario,60,
La Nación,Economía,https://lanacion.com.ar/economia,ARGENTINA,diario,120,https://lanacion.com.ar/economia/rss
```

### Áreas Geográficas Válidas

```python
AREAS_GEOGRAFICAS_VALIDAS = [
    'GLOBAL', 'ESPAÑA', 'MEXICO', 'ARGENTINA', 'COLOMBIA', 'CHILE', 
    'PERU', 'VENEZUELA', 'ECUADOR', 'BOLIVIA', 'PARAGUAY', 'URUGUAY',
    'BRASIL', 'COSTA_RICA', 'PANAMA', 'GUATEMALA', 'HONDURAS', 
    'EL_SALVADOR', 'NICARAGUA', 'REPUBLICA_DOMINICANA', 'PUERTO_RICO',
    'CUBA', 'USA', 'CANADA', 'EUROPA', 'ASIA', 'AFRICA', 'OCEANIA'
]
```

## 🔧 Migración de Spiders Existentes

Para migrar spiders existentes a la versión 2.0:

### 1. Validar spiders existentes
```bash
python3 src/validate_spiders.py --report
```

### 2. Migrar un spider individual
```bash
# Modo dry-run (sin cambios)
python3 src/migrate_spider.py /path/to/spider.py --dry-run

# Migración real
python3 src/migrate_spider.py /path/to/spider.py
```

### 3. Migración en batch
```bash
python3 src/batch_migrate.py --spiders-dir /path/to/spiders/
```

## 📊 Métricas y KPIs

### Endpoints de métricas

- `/api/metrics` - Métricas generales del sistema
- `/api/metrics/summary` - Resumen ejecutivo
- `/api/metrics/performance` - Validación de KPIs

### KPIs Objetivo

- **Tiempo RSS**: < 5 segundos
- **Tiempo primera vez**: ~20 segundos
- **Tiempo con cache**: < 2 segundos
- **Reducción vs manual**: 97%

## 🐛 Troubleshooting

### Error: "Campo 'titulo' no encontrado"
**Problema**: El spider usa 'titulo' en lugar de 'titular'
**Solución**: Ejecutar migración o cambiar manualmente `item['titulo']` por `item['titular']`

### Error: "Área geográfica inválida"
**Problema**: El área geográfica no está en la lista válida
**Solución**: Usar una de las 28 áreas geográficas válidas listadas arriba

### Error: "Spider ya existe"
**Problema**: Ya existe un spider con el nombre `{medio}_{seccion}`
**Solución**: Verificar con `/api/check-duplicate` antes de generar

### Cache no funciona
**Problema**: Redis no está conectado o configurado
**Solución**: Verificar que Redis esté corriendo: `docker-compose ps redis`

## 🔗 Integración con Scrapyd

Los spiders generados son compatibles con Scrapyd. Para programar ejecución automática:

```python
from src.scrapyd_integration import register_spider_in_scrapyd

# Registrar spider para ejecución cada 60 minutos
register_spider_in_scrapyd(
    spider_name="el_pais_internacional",
    frecuencia_minutos=60
)
```

## 🏗️ Arquitectura

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│     Frontend    │────▶│    NGINX     │────▶│   Backend   │
│  (Puerto 3000)  │     │ (Puerto 80)  │     │ (Puerto 8000)│
└─────────────────┘     └──────────────┘     └─────────────┘
                                                     │
                                                     ▼
                                              ┌─────────────┐
                                              │    Redis    │
                                              │ (Puerto 6379)│
                                              └─────────────┘
```

## 🚦 Health Check

```bash
curl http://localhost/spider-factory/api/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "redis": "connected",
  "timestamp": "2024-12-27T12:00:00Z"
}
```

## 📝 Logs

Los logs se encuentran en:
- Aplicación: `logs/spider_factory_YYYY-MM-DD.log`
- Errores: `logs/errors_YYYY-MM-DD.log`
- Docker: `docker-compose logs -f spider_factory_backend`

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'feat: Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Propiedad de La Máquina de Noticias. Todos los derechos reservados.