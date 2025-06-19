# FLUJO PRINCIPAL - Generación de Spiders para La Máquina de Noticias

## 🎯 PROPÓSITO
Generar **spiders especializados** que conviertan secciones de medios digitales en fuentes tipo RSS, completamente integrados con la arquitectura de La Máquina de Noticias.

## 📋 REQUISITOS PREVIOS

### **1. Configuración de Supabase**
```env
# En config/.env.test o config/.env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-anon-key
SUPABASE_SERVICE_ROLE_KEY=tu-service-role-key
```

### **2. Estructura del proyecto**
```
module_scraper/
├── .scrapy/
│   └── crawl_once/              # Directorio para scrapy-crawl-once
├── scraper_core/
│   ├── items/
│   │   └── articulo.py          # ArticuloInItem
│   ├── pipelines/
│   │   ├── validation.py        # DataValidationPipeline
│   │   ├── cleaning.py          # DataCleaningPipeline
│   │   └── storage.py           # SupabaseStoragePipeline
│   └── spiders/
│       └── base/
│           └── base_article.py  # BaseArticleSpider
```

## 📥 INPUT DEL USUARIO

### **Información requerida:**
```yaml
url_seccion: "https://elpais.com/internacional"
nombre_medio: "El País"
pais_publicacion: "España"
tipo_medio: "diario"  # diario/agencia/revista
rss_disponible: "No"  # Sí/No
url_rss: ""  # Solo si rss_disponible = Sí
```

## 🔄 PROCESO PASO A PASO

### **PASO 1: Análisis Inicial**
```python
# Determinar estrategia basada en disponibilidad de RSS
if rss_disponible:
    estrategia = "rss_feed"
    analisis_requerido = False
else:
    # Análisis mínimo con Firecrawl
    estrategia = determinar_estrategia_scraping(url_seccion)
    analisis_requerido = True
```

### **PASO 2: Configuración Base del Spider**
```python
# Configuración que todos los spiders deben tener
configuracion_base = {
    "hereda_de": "BaseArticleSpider",
    "items": "ArticuloInItem",
    "pipelines": [
        "DataValidationPipeline",
        "DataCleaningPipeline",
        "SupabaseStoragePipeline"
    ],
    "custom_settings": {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 3.0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CLOSESPIDER_ITEMCOUNT': 50,  # Límite por ejecución
        
        # Configuración scrapy-crawl-once
        'CRAWL_ONCE_ENABLED': True,
        'CRAWL_ONCE_PATH': 'crawl_once/section_{nombre_seccion}',
        'CRAWL_ONCE_DEFAULT': False,
    }
}
```

### **PASO 3: Análisis de la Sección (si no hay RSS)**
```python
# Solo si no hay RSS disponible
if analisis_requerido:
    # 1. Obtener página de sección
    seccion_data = firecrawl_scrape(url_seccion)
    
    # 2. Detectar patrón de URLs de artículos
    patron_articulos = detectar_patron_urls(seccion_data)
    
    # 3. Verificar si necesita JavaScript
    requiere_js = verificar_contenido_dinamico(seccion_data)
    
    # 4. Obtener muestra de artículo
    if patron_articulos:
        articulo_muestra = firecrawl_scrape(patron_articulos[0])
        selectores = extraer_selectores(articulo_muestra)
```

### **PASO 4: Generación del Spider**

#### **Opción A: Spider con RSS**
```python
class ElpaisInternacionalRssSpider(BaseArticleSpider):
    name = 'elpais_internacional_rss'
    allowed_domains = ['elpais.com']
    
    # Configuración RSS
    feed_url = 'https://elpais.com/rss/internacional'
    
    custom_settings = {
        **BaseArticleSpider.custom_settings,
        'CRAWL_ONCE_ENABLED': True,
        'CRAWL_ONCE_PATH': 'crawl_once/section_internacional_rss',
    }
    
    def parse_feed(self, response):
        """Parsear feed RSS"""
        # Los artículos del RSS se marcan con crawl_once
        for entry in feed.entries:
            yield self.make_request(
                entry.link,
                self.parse_article,
                meta={
                    'crawl_once': True,  # Activar deduplicación
                    'rss_data': entry_data
                }
            )
```

#### **Opción B: Spider Scraping**
```python
class ElpaisInternacionalSpider(BaseArticleSpider):
    name = 'elpais_internacional'
    allowed_domains = ['elpais.com']
    start_urls = ['https://elpais.com/internacional']
    
    # Patrón para filtrar solo artículos de la sección
    section_pattern = re.compile(r'/internacional/')
    
    custom_settings = {
        **BaseArticleSpider.custom_settings,
        'CRAWL_ONCE_ENABLED': True,
        'CRAWL_ONCE_PATH': 'crawl_once/section_internacional',
    }
    
    def parse(self, response):
        """Extraer lista de artículos de la sección"""
        article_links = response.css('article a::attr(href)').getall()
        
        for link in article_links:
            if self.section_pattern.search(link):
                yield response.follow(
                    link, 
                    self.parse_article,
                    meta={'crawl_once': True}  # No reprocesar
                )
```

## 🔧 INTEGRACIÓN CON EL PROYECTO

### **1. Estructura de Items**
```python
# El spider debe llenar TODOS los campos requeridos
item = ArticuloInItem()
item['url'] = response.url
item['titular'] = self.extract_article_title(response)
item['contenido_texto'] = self.extract_article_content(response)
item['contenido_html'] = response.text
item['medio'] = self.medio_nombre
item['pais_publicacion'] = self.pais
item['tipo_medio'] = self.tipo_medio
item['fecha_publicacion'] = self.extract_publication_date(response)
item['autor'] = self.extract_author(response)
item['idioma'] = 'es'
item['seccion'] = self.target_section
item['fuente'] = self.name
```

### **2. Configuración de Pipelines**
```python
# En settings.py del spider
custom_settings = {
    **BaseArticleSpider.custom_settings,
    'ITEM_PIPELINES': {
        'scraper_core.pipelines.validation.DataValidationPipeline': 100,
        'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
        'scraper_core.pipelines.storage.SupabaseStoragePipeline': 300,
    }
}
```

### **3. Sistema de Deduplicación con scrapy-crawl-once**
```python
# Configuración para evitar duplicados
custom_settings = {
    'CRAWL_ONCE_ENABLED': True,
    'CRAWL_ONCE_PATH': f'crawl_once/section_{self.target_section}',
    'CRAWL_ONCE_DEFAULT': False,  # Control explícito
}

# En los requests a artículos
yield Request(
    url,
    callback=self.parse_article,
    meta={'crawl_once': True}  # Activar deduplicación
)
```

## 📊 CONFIGURACIÓN POR TIPO DE ESTRATEGIA

### **RSS Feed Spider**
- **Frecuencia**: Cada 30 minutos
- **Items por ejecución**: 50
- **Análisis requerido**: No
- **Complejidad**: Baja
- **Deduplicación**: `crawl_once/section_{seccion}_rss`

### **HTML Scraping Spider**
- **Frecuencia**: Cada 60 minutos
- **Items por ejecución**: 30
- **Análisis requerido**: 2-3 requests
- **Complejidad**: Media
- **Deduplicación**: `crawl_once/section_{seccion}`

### **Playwright Spider**
- **Frecuencia**: Cada 120 minutos
- **Items por ejecución**: 20
- **Análisis requerido**: 3-4 requests
- **Complejidad**: Alta
- **Deduplicación**: `crawl_once/section_{seccion}_playwright`

## 🚨 VALIDACIONES CRÍTICAS

### **1. Filtrado por sección**
```python
def is_section_article(self, url):
    """Validar que el artículo pertenece a la sección"""
    # Debe contener el path de la sección
    return self.section_pattern.search(url) is not None
```

### **2. Contenido válido**
```python
def validate_article_data(self, article_data):
    """Validar antes de yield"""
    required = ['titular', 'url', 'contenido_texto']
    return all(article_data.get(field) for field in required)
```

### **3. Límites de ejecución**
```python
# Siempre configurar límites
'CLOSESPIDER_ITEMCOUNT': 50,  # Máximo items
'CLOSESPIDER_TIMEOUT': 1800,  # 30 minutos máximo
'DEPTH_LIMIT': 2,  # No profundizar demasiado
```

## 📋 CHECKLIST DE GENERACIÓN

- [ ] Spider hereda de `BaseArticleSpider`
- [ ] Usa `ArticuloInItem` con todos los campos
- [ ] Configura los 3 pipelines del proyecto
- [ ] Implementa filtrado estricto por sección
- [ ] Configura scrapy-crawl-once correctamente
- [ ] Activa `crawl_once` en requests de artículos
- [ ] Respeta robots.txt
- [ ] Implementa rate limiting
- [ ] Maneja errores con métodos de la clase base
- [ ] Incluye logging apropiado

## 🎯 RESULTADO ESPERADO

### **Archivos generados:**
```
scraper_core/spiders/
└── elpais_internacional_spider.py  # Spider completo
```

### **Estructura de deduplicación:**
```
.scrapy/
└── crawl_once/
    └── section_internacional/      # Base de datos de URLs procesadas
```

### **Configuración para cron:**
```bash
# RSS (cada 30 min)
*/30 * * * * cd /path/to/project && scrapy crawl elpais_internacional_rss

# Scraping (cada hora)
0 * * * * cd /path/to/project && scrapy crawl elpais_internacional
```

### **Documentación incluida:**
- Docstring completo en el spider
- Configuración específica documentada
- Instrucciones de deployment

---

**🎯 OBJETIVO:** Spider funcional que convierte la sección en un feed RSS automatizado

**⚡ PRINCIPIO:** Integración total con la arquitectura existente

**📚 SIGUIENTE:** Consultar `CODE_GENERATION.md` para generar el código final
