# CONFIGURACIONES POR DEFECTO - La Máquina de Noticias

## 🎯 OBJETIVO
Proporcionar configuraciones estándar y validaciones que garanticen la integración correcta con el proyecto existente.

## ⚙️ CONFIGURACIONES BASE OBLIGATORIAS

### **Settings heredados de BaseArticleSpider:**
```python
# Todos los spiders heredan estas configuraciones
base_settings = {
    'ROBOTSTXT_OBEY': True,
    'DOWNLOAD_DELAY': 1,  # Se sobrescribe según estrategia
    'RANDOMIZE_DOWNLOAD_DELAY': True,
    'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
    'RETRY_TIMES': 3,
    'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
    'DOWNLOAD_TIMEOUT': 30,
    'USE_PLAYWRIGHT_FOR_EMPTY_CONTENT': True,
}
```

### **Settings específicos por estrategia:**

#### **RSS Spider:**
```python
rss_settings = {
    'DOWNLOAD_DELAY': 2.0,  # Más rápido para RSS
    'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
    'CLOSESPIDER_ITEMCOUNT': 50,
    'CLOSESPIDER_TIMEOUT': 1800,
    
    # Configuración scrapy-crawl-once
    'CRAWL_ONCE_ENABLED': True,
    'CRAWL_ONCE_PATH': f'crawl_once/section_{spider_name}_rss',
    'CRAWL_ONCE_DEFAULT': False,  # Control explícito por request
    
    'FEED_EXPORT_ENCODING': 'utf-8',
}
```

#### **Scraping HTML Spider:**
```python
scraping_settings = {
    'DOWNLOAD_DELAY': 3.0,  # Conservador
    'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
    'CLOSESPIDER_ITEMCOUNT': 30,
    'CLOSESPIDER_TIMEOUT': 1800,
    
    # Configuración scrapy-crawl-once
    'CRAWL_ONCE_ENABLED': True,
    'CRAWL_ONCE_PATH': f'crawl_once/section_{spider_name}',
    'CRAWL_ONCE_DEFAULT': False,
    
    'DEPTH_LIMIT': 2,
    'HTTPCACHE_ENABLED': False,  # Siempre contenido fresco
}
```

#### **Playwright Spider:**
```python
playwright_settings = {
    'DOWNLOAD_DELAY': 5.0,  # Más lento por JavaScript
    'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
    'CLOSESPIDER_ITEMCOUNT': 20,
    'CLOSESPIDER_TIMEOUT': 1800,
    
    # Configuración scrapy-crawl-once
    'CRAWL_ONCE_ENABLED': True,
    'CRAWL_ONCE_PATH': f'crawl_once/section_{spider_name}_playwright',
    'CRAWL_ONCE_DEFAULT': False,
    
    'DEPTH_LIMIT': 2,
    
    # Configuración Playwright
    'DOWNLOAD_HANDLERS': {
        "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    },
    'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
    'PLAYWRIGHT_LAUNCH_OPTIONS': {
        'headless': True,
        'args': ['--disable-blink-features=AutomationControlled']
    },
    'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 30000,
}
```

## 📊 ESTRUCTURA DE ITEMS OBLIGATORIA

### **Campos requeridos de ArticuloInItem:**
```python
# Campos que DEBEN llenarse
REQUIRED_FIELDS = [
    'url',                    # URL del artículo
    'titular',                # Título (NO 'titulo')
    'medio',                  # Nombre del medio
    'area_geografica',        # Área geográfica
    'tipo_medio',             # diario/agencia/revista
    'fecha_publicacion',      # Fecha de publicación
    'contenido_texto',        # Texto extraído
]

# Campos con valores por defecto
DEFAULT_VALUES = {
    'autor': 'Redacción',
    'idioma': 'es',
    'es_opinion': False,
    'es_oficial': False,
    'estado_procesamiento': 'pendiente',
}

# Tipos de medio válidos
VALID_TIPOS_MEDIO = [
    'diario', 'agencia', 'television', 'radio', 
    'revista', 'blog', 'institucional', 'otro'
]
```

## 🔍 VALIDACIONES ESTÁNDAR

### **Validación de contenido:**
```python
# Implementadas en DataValidationPipeline
MIN_TITLE_LENGTH = 10
MIN_CONTENT_LENGTH = 100

def validate_article_data(article_dict):
    """
    Validación mínima antes de yield.
    El pipeline hace validación completa.
    """
    # Campos requeridos
    if not article_dict.get('titular'):
        return False
    
    if not article_dict.get('url'):
        return False
        
    # Longitud mínima
    content = article_dict.get('contenido_texto', '')
    if len(content) < MIN_CONTENT_LENGTH:
        return False
        
    return True
```

### **Filtrado de URLs:**
```python
def is_valid_article_url(url, section_name):
    """
    Validar que la URL es apropiada para extracción.
    """
    url_lower = url.lower()
    
    # Excluir patrones no deseados
    EXCLUDE_PATTERNS = [
        '/archivo/',          # Contenido antiguo
        '/hemeroteca/',       # Archivo histórico
        '/newsletter/',       # Suscripciones
        '/suscri',           # Variantes de suscripción
        '/login',            # Páginas de login
        '/registro',         # Páginas de registro
        '/multimedia/',      # Galerías multimedia
        '/galeria/',         # Galerías de fotos
        '/video/',           # Videos
        '/podcast/',         # Podcasts
        '/tag/',             # Páginas de tags
        '/autor/',           # Páginas de autor
        '/buscar',           # Búsquedas
        '/search',           # Búsquedas en inglés
        '.pdf',              # Documentos PDF
        '.doc',              # Documentos Word
        '#comments',         # Enlaces a comentarios
    ]
    
    for pattern in EXCLUDE_PATTERNS:
        if pattern in url_lower:
            return False
    
    # Debe contener la sección
    if section_name and f'/{section_name}' not in url_lower:
        return False
        
    return True
```

## 🕷️ USER AGENTS POOL

```python
# Heredados de BaseArticleSpider
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
]
```

## 📅 FRECUENCIAS DE EJECUCIÓN

```python
# Configuración para cron
EXECUTION_FREQUENCIES = {
    "rss": {
        "cron": "*/30 * * * *",
        "description": "Cada 30 minutos",
        "max_items": 50
    },
    "scraping": {
        "cron": "0 * * * *",
        "description": "Cada hora",
        "max_items": 30
    },
    "playwright": {
        "cron": "0 */2 * * *",
        "description": "Cada 2 horas",
        "max_items": 20
    }
}
```

## 🔧 PIPELINES CONFIGURATION

```python
# Configuración obligatoria de pipelines
ITEM_PIPELINES = {
    'scraper_core.pipelines.validation.DataValidationPipeline': 100,
    'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
    'scraper_core.pipelines.storage.SupabaseStoragePipeline': 300,
}

# Configuración de validación
VALIDATION_REQUIRED_FIELDS = [
    'url', 'titular', 'medio', 'area_geografica',
    'tipo_medio', 'fecha_publicacion', 'contenido_texto'
]
VALIDATION_MIN_CONTENT_LENGTH = 100
VALIDATION_MIN_TITLE_LENGTH = 10
VALIDATION_DROP_INVALID_ITEMS = False  # Pasar con error_detalle

# Configuración de limpieza
CLEANING_STRIP_HTML = True
CLEANING_NORMALIZE_WHITESPACE = True
CLEANING_REMOVE_EMPTY_LINES = True
CLEANING_STANDARDIZE_QUOTES = True
CLEANING_PRESERVE_HTML_CONTENT = True
```

## 🗄️ SUPABASE INTEGRATION

```python
# Variables de entorno requeridas
import os

# Deben estar configuradas en config/.env
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Configuración de storage
SUPABASE_BUCKET_NAME = 'articulos'
COMPRESSION_ENABLED = True
COMPRESSION_LEVEL = 6  # zlib compression level

# Estructura de la tabla articulos
ARTICULOS_TABLE_FIELDS = {
    'id': 'BIGSERIAL PRIMARY KEY',
    'url': 'TEXT UNIQUE NOT NULL',
    'storage_path': 'TEXT',
    'fuente': 'TEXT NOT NULL',
    'medio': 'TEXT NOT NULL',
    'medio_url_principal': 'TEXT',
    'area_geografica': 'TEXT NOT NULL',
    'tipo_medio': 'TEXT NOT NULL',
    'titular': 'TEXT NOT NULL',
    'fecha_publicacion': 'TIMESTAMPTZ',
    'autor': 'TEXT',
    'idioma': 'TEXT DEFAULT \'es\'',
    'seccion': 'TEXT',
    'etiquetas_fuente': 'TEXT[]',
    'es_opinion': 'BOOLEAN DEFAULT FALSE',
    'es_oficial': 'BOOLEAN DEFAULT FALSE',
    'resumen': 'TEXT',
    'categorias_asignadas': 'TEXT[]',
    'puntuacion_relevancia': 'INTEGER',
    'fecha_recopilacion': 'TIMESTAMPTZ DEFAULT NOW()',
    'fecha_procesamiento': 'TIMESTAMPTZ',
    'estado_procesamiento': 'TEXT DEFAULT \'pendiente\'',
    'error_detalle': 'TEXT',
    'contenido_texto': 'TEXT NOT NULL',
    'metadata': 'JSONB',
}
```

## 🔄 SCRAPY-CRAWL-ONCE CONFIGURATION

```python
# Configuración de scrapy-crawl-once para deduplicación
CRAWL_ONCE_CONFIG = {
    # Habilitar el middleware
    'CRAWL_ONCE_ENABLED': True,
    
    # Path base para almacenar URLs procesadas
    # Se creará subcarpeta por sección: crawl_once/section_{nombre}
    'CRAWL_ONCE_PATH': 'crawl_once/section_{section_name}',
    
    # No activar por defecto en todos los requests
    'CRAWL_ONCE_DEFAULT': False,
    
    # TTL para secciones (desde settings.py)
    'CRAWL_ONCE_SECTION_TTL': 86400,  # 24 horas
}

# Activación en requests específicos
def make_article_request(url, callback):
    """Crear request con deduplicación activada"""
    return scrapy.Request(
        url,
        callback=callback,
        meta={
            'crawl_once': True,  # Activar deduplicación
            'crawl_once_key': url,  # Clave única (opcional, por defecto usa URL)
        }
    )
```

## 🚨 LOGGING CONFIGURATION

```python
# Configuración de logging
LOG_LEVEL = 'INFO'  # Por defecto, DEBUG para desarrollo

# Formato de logs
LOG_FORMAT = '%(levelname)s:%(name)s:%(message)s'

# Logs específicos por componente
LOGGERS = {
    'scraper_core.pipelines.validation': 'DEBUG',
    'scraper_core.pipelines.cleaning': 'DEBUG',
    'scraper_core.pipelines.storage': 'INFO',
    'scraper_core.utils.supabase_client': 'INFO',
    'scrapy_crawl_once': 'INFO',  # Logs de deduplicación
}

# Mensajes de log estándar
LOG_MESSAGES = {
    'spider_start': "Iniciando spider {name} para {section} de {media}",
    'article_found': "Artículo encontrado: {url}",
    'article_extracted': "Artículo extraído exitosamente: {url}",
    'article_invalid': "Artículo inválido descartado: {url} - Razón: {reason}",
    'section_filtered': "URL filtrada (no es de la sección): {url}",
    'crawl_once_skip': "Artículo ya procesado (crawl-once): {url}",
    'execution_complete': "Ejecución completada - Artículos nuevos: {count}",
}
```

## 🎯 NAMING CONVENTIONS

```python
def generate_spider_name(medio, seccion, strategy):
    """
    Generar nombre consistente para el spider.
    """
    # Limpiar y normalizar
    medio_clean = medio.lower().replace(' ', '').replace('.', '')
    seccion_clean = seccion.lower().replace(' ', '_')
    
    # Agregar sufijo según estrategia
    if strategy == 'rss':
        suffix = '_rss'
    elif strategy == 'playwright':
        suffix = '_playwright'
    else:
        suffix = ''  # Scraping básico sin sufijo
    
    return f"{medio_clean}_{seccion_clean}{suffix}"

def generate_crawl_once_path(spider_name, section):
    """
    Generar path para scrapy-crawl-once.
    """
    # Usar prefijo de sección como en settings.py
    section_prefix = "section"
    return f"crawl_once/{section_prefix}_{section}_{spider_name}"

# Ejemplos:
# Spider: elpais_internacional_rss
# Path: crawl_once/section_internacional_elpais_internacional_rss
```

## 📦 METADATA ESTÁNDAR

```python
def generate_spider_metadata(spider_info):
    """
    Generar metadata estándar para el spider.
    """
    return {
        'spider_type': spider_info['strategy'],
        'spider_version': '2.0',
        'generation_date': datetime.utcnow().isoformat(),
        'generated_by': 'spider_generator',
        'project': 'la_maquina_de_noticias',
        'execution_mode': 'periodic',
        'section_specific': True,
        'deduplication_method': 'scrapy-crawl-once',
        'deduplication_enabled': True,
        'pipelines_configured': True,
        'storage_backend': 'supabase',
    }
```

---

**📚 Documentos relacionados:**
- `MAIN_WORKFLOW.md` - Proceso principal
- `TEMPLATES.md` - Plantillas de código
- `CODE_GENERATION.md` - Generación final
- `ERROR_HANDLING.md` - Manejo de errores
