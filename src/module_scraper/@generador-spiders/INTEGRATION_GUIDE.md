# GUÍA DE INTEGRACIÓN - La Máquina de Noticias

## 🎯 OBJETIVO
Asegurar que los spiders generados se integren perfectamente con la arquitectura existente de La Máquina de Noticias.

## 📋 CHECKLIST DE INTEGRACIÓN

### **1. Verificación del entorno**
- [ ] Variables de entorno de Supabase configuradas
- [ ] Estructura de directorios correcta
- [ ] Dependencias instaladas (`requirements.txt`)
- [ ] Base de datos con tabla `articulos` creada
- [ ] scrapy-crawl-once instalado

### **2. Verificación del código generado**
- [ ] Hereda de `BaseArticleSpider`
- [ ] Importa `ArticuloInItem` correctamente
- [ ] Configura los 3 pipelines del proyecto
- [ ] Implementa filtrado por sección
- [ ] Configura scrapy-crawl-once para deduplicación

### **3. Verificación de funcionamiento**
- [ ] Spider se ejecuta sin errores
- [ ] Items pasan validación
- [ ] Datos se almacenan en Supabase
- [ ] Logs se generan correctamente
- [ ] No procesa artículos duplicados

## 🔧 PASOS DE INTEGRACIÓN

### **PASO 1: Preparar el entorno**

```bash
# 1. Navegar al directorio del proyecto
cd /path/to/LaMaquinaDeNoticias/src/module_scraper

# 2. Verificar/crear archivo de configuración
cp config/.env.test.example config/.env.test

# 3. Editar configuración con credenciales
# SUPABASE_URL=https://xxxxx.supabase.co
# SUPABASE_KEY=xxxxx
# SUPABASE_SERVICE_ROLE_KEY=xxxxx

# 4. Instalar dependencias (incluye scrapy-crawl-once)
pip install -r requirements.txt
```

### **PASO 2: Ubicar el spider generado**

```bash
# El spider debe ir en:
scraper_core/spiders/{medio}_{seccion}_spider.py

# Ejemplo:
scraper_core/spiders/elpais_internacional_spider.py
```

### **PASO 3: Verificar imports y herencia**

```python
# ✅ Verificar que el spider tenga estos imports
from scraper_core.spiders.base.base_article import BaseArticleSpider
from scraper_core.items import ArticuloInItem
from scraper_core.spiders.base.utils import parse_date_string

# ✅ Verificar herencia correcta
class ElpaisInternacionalSpider(BaseArticleSpider):
    # NO heredar directamente de scrapy.Spider
```

### **PASO 4: Configurar pipelines y middlewares**

```python
# En custom_settings del spider
custom_settings = {
    **BaseArticleSpider.custom_settings,
    
    # Configuración scrapy-crawl-once
    'CRAWL_ONCE_ENABLED': True,
    'CRAWL_ONCE_PATH': '.scrapy/crawl_once/',
    'CRAWL_ONCE_DEFAULT': False,
    
    # Pipelines del proyecto
    'ITEM_PIPELINES': {
        'scraper_core.pipelines.validation.DataValidationPipeline': 100,
        'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
        'scraper_core.pipelines.storage.SupabaseStoragePipeline': 300,
    }
}
```

### **PASO 5: Prueba inicial**

```bash
# Test de sintaxis
python -m py_compile scraper_core/spiders/elpais_internacional_spider.py

# Test de importación
python -c "from scraper_core.spiders.elpais_internacional_spider import ElpaisInternacionalSpider"

# Test de ejecución (limitado)
scrapy crawl elpais_internacional -s CLOSESPIDER_ITEMCOUNT=3 -L DEBUG
```

## 📊 ESTRUCTURA DE DATOS

### **Campos obligatorios de ArticuloInItem:**
```python
# El spider DEBE llenar estos campos
item['url'] = response.url
item['titular'] = 'Título del artículo'
item['medio'] = 'El País'
item['area_geografica'] = 'España'
item['tipo_medio'] = 'diario'  # diario/agencia/revista
item['fecha_publicacion'] = datetime_object_or_string
item['contenido_texto'] = 'Contenido extraído'
item['fuente'] = self.name  # Nombre del spider
```

### **Campos adicionales importantes:**
```python
item['contenido_html'] = response.text  # HTML original
item['autor'] = 'Nombre Autor' or 'Redacción'
item['idioma'] = 'es'
item['seccion'] = 'internacional'
item['fecha_recopilacion'] = datetime.utcnow()
item['metadata'] = {
    'spider_type': 'scraping',
    'extraction_method': 'html_parsing'
}
```

## 🗄️ INTEGRACIÓN CON SUPABASE

### **Verificar tabla articulos:**
```sql
-- La tabla debe existir con esta estructura
CREATE TABLE articulos (
    id BIGSERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    storage_path TEXT,
    fuente TEXT NOT NULL,
    medio TEXT NOT NULL,
    medio_url_principal TEXT,
    area_geografica TEXT NOT NULL,
    tipo_medio TEXT NOT NULL,
    titular TEXT NOT NULL,
    fecha_publicacion TIMESTAMPTZ,
    autor TEXT,
    idioma TEXT DEFAULT 'es',
    seccion TEXT,
    etiquetas_fuente TEXT[],
    es_opinion BOOLEAN DEFAULT FALSE,
    es_oficial BOOLEAN DEFAULT FALSE,
    resumen TEXT,
    categorias_asignadas TEXT[],
    puntuacion_relevancia INTEGER,
    fecha_recopilacion TIMESTAMPTZ DEFAULT NOW(),
    fecha_procesamiento TIMESTAMPTZ,
    estado_procesamiento TEXT DEFAULT 'pendiente',
    error_detalle TEXT,
    contenido_texto TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### **Verificar bucket de storage:**
```python
# El pipeline guarda HTML comprimido en:
# Bucket: 'articulos'
# Path: '{medio}/{fecha}/{hash}.html.gz'
```

## 🕷️ SISTEMA DE DEDUPLICACIÓN CON SCRAPY-CRAWL-ONCE

### **Configuración scrapy-crawl-once:**
```python
# CRÍTICO: Sin esto, procesará duplicados
custom_settings = {
    'CRAWL_ONCE_ENABLED': True,
    'CRAWL_ONCE_PATH': '.scrapy/crawl_once/',
    'CRAWL_ONCE_DEFAULT': False,  # Control explícito
}

# En cada request de artículo:
yield scrapy.Request(
    url,
    callback=self.parse_article,
    meta={'crawl_once': True}  # Activar deduplicación
)
```

### **Base de datos de deduplicación:**
```
module_scraper/
├── .scrapy/
│   └── crawl_once/
│       ├── elpais_internacional.sqlite
│       ├── infobae_america_latina_rss.sqlite
│       └── ...
```

## 📅 PROGRAMACIÓN PERIÓDICA

### **Configurar cron:**
```bash
# Editar crontab
crontab -e

# Agregar entrada según estrategia:
# RSS - cada 30 minutos
*/30 * * * * cd /path/to/project && /usr/bin/python3 -m scrapy crawl elpais_internacional_rss >> logs/elpais_internacional_rss.log 2>&1

# Scraping - cada hora
0 * * * * cd /path/to/project && /usr/bin/python3 -m scrapy crawl elpais_internacional >> logs/elpais_internacional.log 2>&1

# Playwright - cada 2 horas
0 */2 * * * cd /path/to/project && /usr/bin/python3 -m scrapy crawl elpais_internacional_playwright >> logs/elpais_internacional_playwright.log 2>&1
```

### **Monitoreo de logs:**
```bash
# Ver últimas ejecuciones
tail -f logs/elpais_internacional.log

# Buscar errores
grep ERROR logs/elpais_internacional.log

# Estadísticas de items
grep "item_scraped_count" logs/elpais_internacional.log
```

## 🔍 VERIFICACIÓN FINAL

### **1. Verificar items en base de datos:**
```sql
-- En Supabase SQL Editor
SELECT COUNT(*) FROM articulos WHERE fuente = 'elpais_internacional';

-- Ver últimos artículos
SELECT titular, fecha_publicacion, url 
FROM articulos 
WHERE fuente = 'elpais_internacional'
ORDER BY fecha_recopilacion DESC
LIMIT 10;
```

### **2. Verificar deduplicación:**
```bash
# Ver base de datos de URLs procesadas
ls -la .scrapy/crawl_once/

# Ejecutar spider nuevamente
scrapy crawl elpais_internacional -s CLOSESPIDER_ITEMCOUNT=10

# Verificar en logs que no procesa URLs repetidas
grep "crawl-once" logs/elpais_internacional.log
```

### **3. Verificar storage:**
```sql
-- Verificar que storage_path se llena
SELECT storage_path 
FROM articulos 
WHERE fuente = 'elpais_internacional' 
AND storage_path IS NOT NULL
LIMIT 5;
```

## 🚨 TROUBLESHOOTING COMÚN

### **Spider no encuentra la clase base:**
```bash
# Agregar al inicio del spider
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### **Pipelines no se ejecutan:**
```bash
# Verificar en logs
grep "DataValidationPipeline" logs/spider.log
grep "SupabaseStoragePipeline" logs/spider.log
```

### **Sin conexión a Supabase:**
```python
# Test de conexión
from scraper_core.utils.supabase_client import get_supabase_client
client = get_supabase_client()
response = client.table('articulos').select("count").execute()
print(f"Artículos en DB: {response.data}")
```

### **scrapy-crawl-once no funciona:**
```python
# Verificar que esté en settings.py
SPIDER_MIDDLEWARES = {
    'scrapy_crawl_once.CrawlOnceMiddleware': 100,
}

DOWNLOADER_MIDDLEWARES = {
    'scrapy_crawl_once.CrawlOnceMiddleware': 50,
}

# Verificar permisos de escritura
import os
crawl_once_path = '.scrapy/crawl_once/'
os.makedirs(crawl_once_path, exist_ok=True)
```

## 📈 MÉTRICAS DE ÉXITO

### **KPIs del spider integrado:**
1. **Tasa de éxito**: > 90% de artículos extraídos
2. **Deduplicación**: 0% de duplicados en DB
3. **Validación**: > 95% pasan validación
4. **Storage**: 100% con HTML almacenado
5. **Tiempo ejecución**: < 30 minutos

### **Consulta de métricas:**
```sql
-- Métricas por spider
SELECT 
    fuente,
    COUNT(*) as total_articulos,
    COUNT(DISTINCT url) as urls_unicas,
    AVG(LENGTH(contenido_texto)) as promedio_contenido,
    MIN(fecha_recopilacion) as primera_ejecucion,
    MAX(fecha_recopilacion) as ultima_ejecucion
FROM articulos
WHERE fuente = 'elpais_internacional'
GROUP BY fuente;

-- Verificar que no hay duplicados
SELECT url, COUNT(*) as veces
FROM articulos
WHERE fuente = 'elpais_internacional'
GROUP BY url
HAVING COUNT(*) > 1;
```

---

**📚 Documentos relacionados:**
- `MAIN_WORKFLOW.md` - Proceso principal
- `ERROR_HANDLING.md` - Manejo de errores
- `EJEMPLOS_COMPLETOS.md` - Casos de uso reales
