# MANEJO DE ERRORES - La Máquina de Noticias

## 🎯 OBJETIVO
Proporcionar soluciones para errores comunes durante la generación y ejecución de spiders, manteniendo la consistencia con la arquitectura del proyecto.

## 🚨 ERRORES DURANTE LA GENERACIÓN

### **1. Error: Falta información del usuario**
```python
# Problema
user_input = {
    'url_seccion': 'https://elpais.com/internacional',
    # Falta: medio, pais, tipo_medio
}

# Solución
def validar_input_usuario(input_data):
    """Validar que tenemos toda la información necesaria."""
    required_fields = [
        'url_seccion',
        'nombre_medio',
        'pais_publicacion',
        'tipo_medio',
        'rss_disponible'
    ]
    
    missing = [f for f in required_fields if not input_data.get(f)]
    
    if missing:
        raise ValueError(f"Faltan campos requeridos: {missing}")
    
    # Validar tipo_medio
    valid_tipos = ['diario', 'agencia', 'revista', 'television', 'radio']
    if input_data['tipo_medio'] not in valid_tipos:
        raise ValueError(f"tipo_medio debe ser uno de: {valid_tipos}")
    
    return True
```

### **2. Error: URL de sección inválida**
```python
# Problema: URLs que no son secciones
invalid_urls = [
    'https://elpais.com',  # Home, no sección
    'https://elpais.com/articulo-individual',  # Artículo
    'https://elpais.com/tag/economia',  # Tag, no sección
]

# Solución
def validar_url_seccion(url):
    """Verificar que es una URL de sección válida."""
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    
    # Debe tener al menos un nivel de path
    if not path_parts or not path_parts[0]:
        raise ValueError("URL debe ser de una sección, no la home")
    
    # Excluir patrones no válidos
    invalid_patterns = ['tag', 'autor', 'buscar', 'search', 'archivo']
    if any(p in path_parts[0] for p in invalid_patterns):
        raise ValueError(f"URL no parece ser una sección: {url}")
    
    return True
```

### **3. Error: Análisis con Firecrawl falla**
```python
# Problema: Firecrawl no puede acceder al sitio
try:
    result = firecrawl_scrape(url_seccion)
except Exception as e:
    # Manejo del error
    pass

# Solución con fallbacks
async def analizar_con_fallbacks(url_seccion):
    """Intentar análisis con múltiples estrategias."""
    
    # Intento 1: Firecrawl normal
    try:
        return await firecrawl_scrape(url_seccion)
    except Exception as e:
        logger.warning(f"Firecrawl falló: {e}")
    
    # Intento 2: Firecrawl con opciones diferentes
    try:
        return await firecrawl_scrape(
            url_seccion,
            wait=5000,
            formats=['html', 'links']
        )
    except Exception as e:
        logger.warning(f"Segundo intento falló: {e}")
    
    # Fallback: Generar con configuración genérica
    logger.info("Usando configuración genérica sin análisis")
    return {
        'fallback': True,
        'content': '',
        'links': []
    }
```

## 🐛 ERRORES DURANTE LA EJECUCIÓN

### **1. Error: ImportError de módulos**
```python
# Error común
ImportError: cannot import name 'ArticuloInItem' from 'scraper_core.items'

# Soluciones:
# 1. Verificar estructura del proyecto
assert os.path.exists('scraper_core/items/articulo.py')
assert os.path.exists('scraper_core/items/__init__.py')

# 2. Verificar que __init__.py exporta la clase
# En scraper_core/items/__init__.py:
from .articulo import ArticuloInItem
__all__ = ['ArticuloInItem']

# 3. Verificar PYTHONPATH
import sys
project_root = '/path/to/LaMaquinaDeNoticias/src/module_scraper'
if project_root not in sys.path:
    sys.path.insert(0, project_root)
```

### **2. Error: Pipelines no se ejecutan**
```python
# Problema: Items no pasan por pipelines
# Síntoma: No hay validación ni almacenamiento

# Verificación 1: Configuración en settings
custom_settings = {
    'ITEM_PIPELINES': {
        'scraper_core.pipelines.validation.DataValidationPipeline': 100,
        'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
        'scraper_core.pipelines.storage.SupabaseStoragePipeline': 300,
    }
}

# Verificación 2: Items son del tipo correcto
def parse_article(self, response):
    # ✅ Correcto
    item = ArticuloInItem()
    
    # ❌ Incorrecto
    item = {}  # Los pipelines esperan ArticuloInItem
    
    return item

# Verificación 3: No hay excepciones en pipelines
# Revisar logs para errores como:
# - Campos faltantes en validación
# - Errores de conexión a Supabase
```

### **3. Error: Campos requeridos faltantes**
```python
# Error: DataValidationPipeline rechaza items
ValidationError: Required field 'titular' missing

# Solución: Asegurar que todos los campos se llenan
def create_complete_item(self, response):
    """Crear item con todos los campos requeridos."""
    item = ArticuloInItem()
    
    # Campos absolutamente requeridos
    item['url'] = response.url
    item['titular'] = self.extract_article_title(response) or 'Sin título'
    item['medio'] = self.medio_nombre
    item['pais_publicacion'] = self.pais
    item['tipo_medio'] = self.tipo_medio
    item['fecha_publicacion'] = self.extract_publication_date(response) or datetime.utcnow()
    item['contenido_texto'] = self.extract_article_content(response) or ''
    
    # Validar antes de retornar
    if not item['contenido_texto'] or len(item['contenido_texto']) < 100:
        self.logger.warning(f"Contenido insuficiente: {response.url}")
        return None
        
    return item
```

### **4. Error: Supabase connection failed**
```python
# Error: SupabaseStoragePipeline no puede conectar
SupabaseError: Invalid API key

# Verificación 1: Variables de entorno
import os
required_vars = [
    'SUPABASE_URL',
    'SUPABASE_KEY', 
    'SUPABASE_SERVICE_ROLE_KEY'
]

for var in required_vars:
    if not os.getenv(var):
        print(f"ERROR: {var} no está configurada")

# Verificación 2: Archivo .env cargado
# En scrapy.cfg o settings.py:
from dotenv import load_dotenv
load_dotenv('config/.env')  # o config/.env.test

# Verificación 3: Permisos en Supabase
# - Verificar que la tabla 'articulos' existe
# - Verificar permisos RLS si están habilitados
# - Verificar que el bucket 'articulos' existe
```

### **5. Error: Duplicados no se detectan**
```python
# Problema: El spider procesa los mismos artículos repetidamente

# Solución 1: Verificar JOBDIR configurado
custom_settings = {
    'DUPEFILTER_CLASS': 'scrapy.dupefilters.RFPDupeFilter',
    'JOBDIR': f'./crawl_state_{spider_name}',  # CRÍTICO
}

# Solución 2: Verificar permisos de escritura
import os
jobdir = './crawl_state_test'
os.makedirs(jobdir, exist_ok=True)
test_file = os.path.join(jobdir, 'test.txt')
with open(test_file, 'w') as f:
    f.write('test')
os.remove(test_file)

# Solución 3: Limpiar estado corrupto
def reset_spider_state(spider_name):
    """Resetear estado del spider si está corrupto."""
    import shutil
    jobdir = f'./crawl_state_{spider_name}'
    if os.path.exists(jobdir):
        shutil.rmtree(jobdir)
        logger.info(f"Estado reseteado para {spider_name}")
```

## 🔧 ERRORES DE EXTRACCIÓN

### **1. Selectores no encuentran contenido**
```python
# Problema: Selectores retornan None o vacío

# Solución: Implementar fallbacks progresivos
def extract_with_fallbacks(self, response, field_type):
    """Extraer con múltiples estrategias."""
    
    # Estrategia 1: Selectores específicos del medio
    if hasattr(self, f'{field_type}_selectors'):
        selectors = getattr(self, f'{field_type}_selectors')
        for selector in selectors:
            result = response.css(selector).get()
            if result and result.strip():
                return result.strip()
    
    # Estrategia 2: Usar métodos de BaseArticleSpider
    if field_type == 'title':
        return self.extract_article_title(response)
    elif field_type == 'content':
        return self.extract_article_content(response)
    elif field_type == 'date':
        return self.extract_publication_date(response)
    
    # Estrategia 3: Selectores genéricos
    generic_selectors = {
        'title': ['h1::text', 'title::text'],
        'content': ['article ::text', 'main ::text'],
        'date': ['time::text', '.date::text']
    }
    
    for selector in generic_selectors.get(field_type, []):
        result = response.css(selector).get()
        if result and result.strip():
            return result.strip()
    
    return None
```

### **2. Contenido con JavaScript no se carga**
```python
# Error: Página vacía o incompleta

# Solución 1: Verificar si Playwright está configurado
if 'scrapy_playwright' not in self.custom_settings.get('DOWNLOAD_HANDLERS', {}):
    # Configurar Playwright
    self.custom_settings['DOWNLOAD_HANDLERS'] = {
        "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    }

# Solución 2: Esperar elementos específicos
yield scrapy.Request(
    url,
    meta={
        "playwright": True,
        "playwright_page_methods": [
            {"method": "wait_for_selector", 
             "args": [".article-content", {"timeout": 30000}]},
            {"method": "wait_for_load_state", "args": ["networkidle"]},
        ]
    }
)

# Solución 3: Fallback a BaseArticleSpider con Playwright
if not content and self.settings.getbool('USE_PLAYWRIGHT_FOR_EMPTY_CONTENT'):
    # BaseArticleSpider maneja esto automáticamente
    pass
```

## 📊 TABLA DE ERRORES COMUNES

| Error | Causa | Solución |
|-------|-------|----------|
| `ImportError: ArticuloInItem` | Path incorrecto | Verificar PYTHONPATH y estructura |
| `ValidationError: Required field` | Campo faltante | Llenar todos los campos requeridos |
| `SupabaseError: Connection` | Credenciales | Verificar variables de entorno |
| `No items scraped` | Selectores incorrectos | Usar fallbacks y métodos base |
| `Duplicates processed` | Sin JOBDIR | Configurar JOBDIR correctamente |
| `JavaScript content missing` | Sin Playwright | Configurar Playwright o usar template apropiado |

## 🚑 RECUPERACIÓN DE ERRORES

### **Estrategia de recuperación general:**
```python
class RobustSpider(BaseArticleSpider):
    """Spider con manejo robusto de errores."""
    
    def parse_article(self, response):
        try:
            # Intentar extracción normal
            item = self._extract_article(response)
            
            if not item:
                # Intentar con Playwright si está disponible
                if not response.meta.get('playwright_retry'):
                    return self._retry_with_playwright(response)
                    
            return item
            
        except Exception as e:
            self.logger.error(f"Error en {response.url}: {e}", exc_info=True)
            
            # Registrar error pero continuar
            self.crawler.stats.inc_value('articles_failed')
            
            # Opcional: Guardar para análisis posterior
            self._save_failed_url(response.url, str(e))
            
            return None
    
    def _retry_with_playwright(self, response):
        """Reintentar con renderizado JavaScript."""
        return scrapy.Request(
            response.url,
            callback=self.parse_article,
            meta={
                'playwright': True,
                'playwright_retry': True
            },
            dont_filter=True
        )
    
    def _save_failed_url(self, url, error):
        """Guardar URLs fallidas para análisis."""
        with open(f'failed_urls_{self.name}.txt', 'a') as f:
            f.write(f"{datetime.utcnow().isoformat()}\t{url}\t{error}\n")
```

## 📝 LOGS Y DEBUGGING

### **Configurar logging detallado:**
```python
# En settings.py o custom_settings
LOG_LEVEL = 'DEBUG'
LOG_FILE = f'logs/{spider_name}.log'

LOGGERS = {
    'scraper_core.pipelines': 'DEBUG',
    'scraper_core.spiders': 'DEBUG',
    'scrapy.core.engine': 'INFO',
}
```

### **Mensajes de log útiles:**
```python
# En el spider
self.logger.info(f"Iniciando extracción de {self.target_section}")
self.logger.debug(f"Selectores utilizados: {selectors}")
self.logger.warning(f"Sin contenido en {response.url}")
self.logger.error(f"Error crítico: {error}", exc_info=True)

# Estadísticas
self.crawler.stats.set_value('custom/articles_by_section', {})
self.crawler.stats.inc_value(f'custom/articles_by_section/{section}')
```

---

**📚 Documentos relacionados:**
- `MAIN_WORKFLOW.md` - Proceso principal
- `CODE_GENERATION.md` - Generación de código
- `INTEGRATION_GUIDE.md` - Guía de integración
