# GUÍA RÁPIDA - Generador de Spiders

## 🚀 INICIO RÁPIDO

### **Input del usuario:**
```yaml
url_seccion: "https://elpais.com/internacional"
nombre_medio: "El País"
pais_publicacion: "España"
tipo_medio: "diario"
rss_disponible: "No"  # o "Sí" con url_rss
```

### **Decisión rápida:**
```
¿RSS disponible?
├─ SÍ → RSS Spider (sin análisis)
└─ NO → ¿Necesita JS? 
         ├─ SÍ → Playwright Spider
         └─ NO → Scraping Spider
```

## 📋 CHEAT SHEET

### **Clases y herencia:**
```python
# ✅ CORRECTO
from scraper_core.spiders.base.base_article import BaseArticleSpider
class MiSpider(BaseArticleSpider):

# ❌ INCORRECTO
class MiSpider(scrapy.Spider):
```

### **Items obligatorios:**
```python
# ✅ CORRECTO
from scraper_core.items import ArticuloInItem
item = ArticuloInItem()
item['titular'] = '...'  # NO 'titulo'

# ❌ INCORRECTO
item = {}  # No usar dict
```

### **Pipelines requeridos:**
```python
'ITEM_PIPELINES': {
    'scraper_core.pipelines.validation.DataValidationPipeline': 100,
    'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
    'scraper_core.pipelines.storage.SupabaseStoragePipeline': 300,
}
```

### **Deduplicación con scrapy-crawl-once:**
```python
# En custom_settings
'CRAWL_ONCE_ENABLED': True,
'CRAWL_ONCE_PATH': '.scrapy/crawl_once/',
'CRAWL_ONCE_DEFAULT': False,

# En cada request
meta={'crawl_once': True}
```

## 🔧 CONFIGURACIONES POR ESTRATEGIA

### **RSS Spider:**
```python
# Configuración
name = 'medio_seccion_rss'
download_delay = 2.0
items_limit = 50
frecuencia = '*/30 * * * *'  # 30 min

# Métodos principales
def parse_feed(self, response)
def parse_article(self, response)
```

### **Scraping Spider:**
```python
# Configuración
name = 'medio_seccion'
download_delay = 3.0
items_limit = 30
frecuencia = '0 * * * *'  # 1 hora

# Métodos principales
def parse(self, response)
def parse_article(self, response)
```

### **Playwright Spider:**
```python
# Configuración
name = 'medio_seccion_playwright'
download_delay = 5.0
items_limit = 20
frecuencia = '0 */2 * * *'  # 2 horas

# Meta Playwright
meta = {
    "playwright": True,
    "playwright_page_methods": [...],
    "crawl_once": True  # También en Playwright
}
```

## 📊 CAMPOS CRÍTICOS

### **Siempre requeridos:**
```python
item['url'] = response.url
item['titular'] = '...'  # MIN 10 chars
item['medio'] = 'Nombre Medio'
item['pais_publicacion'] = 'País'
item['tipo_medio'] = 'diario'  # diario/agencia/revista
item['fecha_publicacion'] = datetime_or_string
item['contenido_texto'] = '...'  # MIN 100 chars
item['fuente'] = self.name
```

### **Con defaults:**
```python
item['autor'] = 'Redacción'  # Si no hay
item['idioma'] = 'es'
item['es_opinion'] = False
item['es_oficial'] = False
```

## 🚨 ERRORES COMUNES

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `ImportError` | Path incorrecto | Verificar PYTHONPATH |
| `ValidationError` | Campos faltantes | Llenar campos requeridos |
| Sin deduplicación | scrapy-crawl-once no configurado | Configurar `CRAWL_ONCE_*` |
| Sin almacenamiento | Sin Supabase env | Configurar `.env` |
| Contenido vacío | Necesita JS | Usar Playwright |

## 📝 COMANDOS ÚTILES

```bash
# Probar spider
scrapy crawl nombre_spider -s CLOSESPIDER_ITEMCOUNT=3

# Ver items extraídos
scrapy crawl nombre_spider -o test.json -s CLOSESPIDER_ITEMCOUNT=5

# Debug completo
scrapy crawl nombre_spider -L DEBUG

# Verificar sintaxis
python -m py_compile path/to/spider.py

# Ver base de datos scrapy-crawl-once
ls -la .scrapy/crawl_once/

# Limpiar deduplicación si es necesario
rm .scrapy/crawl_once/nombre_spider.sqlite
```

## 🔍 VALIDACIONES RÁPIDAS

### **Filtro de sección:**
```python
# URLs válidas para sección
✅ /internacional/noticia-123
✅ /internacional/2024/01/articulo

# URLs a excluir
❌ /otra-seccion/noticia
❌ /archivo/internacional
❌ /tags/internacional
```

### **Activar deduplicación:**
```python
# En cada request de artículo
yield scrapy.Request(
    url,
    callback=self.parse_article,
    meta={'crawl_once': True}  # IMPORTANTE
)
```

### **Contenido mínimo:**
```python
# Validación básica
if len(item['titular']) < 10:
    return None
if len(item['contenido_texto']) < 100:
    return None
```

## 📅 FRECUENCIAS ESTÁNDAR

```bash
# RSS - Cada 30 minutos
*/30 * * * * scrapy crawl spider_rss

# Scraping - Cada hora
0 * * * * scrapy crawl spider_scraping

# Playwright - Cada 2 horas
0 */2 * * * scrapy crawl spider_playwright
```

## 🎯 FLUJO COMPLETO RESUMIDO

1. **Recibir input** → Validar campos
2. **Decidir estrategia** → RSS/Scraping/Playwright
3. **Generar spider** → Heredar de BaseArticleSpider
4. **Configurar** → Pipelines, scrapy-crawl-once, límites
5. **Probar** → 3-5 items
6. **Programar** → Cron según estrategia

## 💡 TIPS FINALES

- **Siempre** heredar de `BaseArticleSpider`
- **Siempre** usar `ArticuloInItem`
- **Siempre** configurar scrapy-crawl-once
- **Siempre** activar `crawl_once` en requests
- **Siempre** filtrar por sección
- **Nunca** procesar > 50 items/ejecución
- **Nunca** delay < 2 segundos

---

**Para proceso detallado →** `MAIN_WORKFLOW.md`  
**Para generar código →** `CODE_GENERATION.md`  
**Para errores →** `ERROR_HANDLING.md`
