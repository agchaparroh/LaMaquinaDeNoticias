# GENERACIÓN DE CÓDIGO - La Máquina de Noticias

## 🎯 OBJETIVO
Generar código Python completo y funcional de spiders que se integren perfectamente con la arquitectura existente del proyecto.

## 📋 CHECKLIST PRE-GENERACIÓN

### **Verificar información disponible:**
- [ ] URL de la sección objetivo
- [ ] Nombre del medio
- [ ] País de publicación
- [ ] Tipo de medio (diario/agencia/revista)
- [ ] RSS disponible (Sí/No)
- [ ] Análisis de la sección completado (si no hay RSS)

### **Verificar configuración del proyecto:**
- [ ] Variables de entorno de Supabase configuradas
- [ ] Pipelines del proyecto disponibles
- [ ] BaseArticleSpider accesible
- [ ] ArticuloInItem importable

## 🔍 SELECCIÓN DE ESTRATEGIA

```python
def seleccionar_estrategia(info_usuario, analisis=None):
    """
    Determinar qué tipo de spider generar.
    """
    if info_usuario.get('rss_disponible') == 'Sí':
        return {
            'tipo': 'rss',
            'template': 'rss_spider',
            'frecuencia': '*/30 * * * *',
            'items_limite': 50
        }
    
    # Si no hay RSS, verificar si necesita JavaScript
    if analisis and analisis.get('requiere_javascript'):
        return {
            'tipo': 'playwright',
            'template': 'playwright_spider',
            'frecuencia': '0 */2 * * *',
            'items_limite': 20
        }
    
    # Por defecto, scraping HTML
    return {
        'tipo': 'scraping',
        'template': 'scraping_spider',
        'frecuencia': '0 * * * *',
        'items_limite': 30
    }
```

## 📝 ESTRUCTURA DEL CÓDIGO GENERADO

### **1. Imports y documentación:**
```python
# -*- coding: utf-8 -*-
"""
Spider para {seccion} de {medio}
Generado para La Máquina de Noticias

Tipo: {tipo_spider}
Frecuencia recomendada: {frecuencia}
Items por ejecución: {items_limite}
"""
import logging
from typing import Iterator, Dict, Any, Optional
from datetime import datetime
import re

from scrapy.http import Response, Request

from scraper_core.items import ArticuloInItem
from scraper_core.spiders.base.base_article import BaseArticleSpider
from scraper_core.spiders.base.utils import parse_date_string

logger = logging.getLogger(__name__)
```

### **2. Clase del Spider:**
```python
class {MediaCapitalized}{SeccionCapitalized}Spider(BaseArticleSpider):
    """
    Spider especializado para {seccion} de {medio}.
    
    Hereda de BaseArticleSpider que proporciona:
    - Rotación de user agents
    - Manejo de errores
    - Métodos de extracción
    - Validación básica
    """
    
    name = '{medio_lower}_{seccion_lower}'
    allowed_domains = ['{dominio}']
    start_urls = ['{url_seccion}']
    
    # Información del medio (obligatorio)
    medio_nombre = '{nombre_medio}'
    pais = '{pais}'
    tipo_medio = '{tipo_medio}'  # diario/agencia/revista
    target_section = '{seccion}'
    
    # Patrón para filtrar URLs de la sección
    section_pattern = re.compile(r'/{seccion_path}/')
    
    # Configuración específica
    custom_settings = {{
        **BaseArticleSpider.custom_settings,
        'DOWNLOAD_DELAY': {download_delay},
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CLOSESPIDER_ITEMCOUNT': {items_limite},
        'CLOSESPIDER_TIMEOUT': 1800,
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.RFPDupeFilter',
        'JOBDIR': './crawl_state_{name}',
        
        # Pipelines del proyecto
        'ITEM_PIPELINES': {{
            'scraper_core.pipelines.validation.DataValidationPipeline': 100,
            'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
            'scraper_core.pipelines.storage.SupabaseStoragePipeline': 300,
        }}
    }}
```

### **3. Métodos de parsing:**

#### **Para RSS:**
```python
def start_requests(self) -> Iterator[Request]:
    """Iniciar con el feed RSS."""
    self.logger.info(f"Iniciando spider RSS para {self.medio_nombre} - {self.target_section}")
    yield self.make_request(self.feed_url, self.parse_feed)

def parse_feed(self, response: Response) -> Iterator[Request]:
    """Parsear feed RSS y extraer artículos."""
    # Implementación específica para RSS
    pass

def parse_article(self, response: Response) -> Optional[ArticuloInItem]:
    """Extraer contenido completo del artículo."""
    # Combinar datos RSS con extracción de contenido
    pass
```

#### **Para Scraping:**
```python
def parse(self, response: Response) -> Iterator[Request]:
    """Extraer enlaces de artículos de la sección."""
    article_links = self._extract_article_links(response)
    
    for link in article_links:
        if self._is_section_article(link):
            yield response.follow(link, self.parse_article)

def parse_article(self, response: Response) -> Optional[ArticuloInItem]:
    """Extraer datos del artículo usando BaseArticleSpider."""
    # Usar métodos heredados
    title = self.extract_article_title(response)
    content = self.extract_article_content(response)
    
    # Crear y validar item
    item = self._create_article_item(response, title, content)
    
    if self.validate_article_data(dict(item)):
        return item
    return None
```

### **4. Métodos auxiliares:**
```python
def _is_section_article(self, url: str) -> bool:
    """
    Verificar que la URL pertenece a la sección objetivo.
    Filtrado estricto para emular comportamiento RSS.
    """
    # Debe contener el patrón de la sección
    if not self.section_pattern.search(url):
        self.logger.debug(f"URL filtrada (no es de la sección): {url}")
        return False
    
    # Excluir patrones no deseados
    exclude_patterns = [
        '/archivo/', '/hemeroteca/', '/newsletter/',
        '/video/', '/galeria/', '/podcast/'
    ]
    
    url_lower = url.lower()
    for pattern in exclude_patterns:
        if pattern in url_lower:
            self.logger.debug(f"URL excluida por patrón {pattern}: {url}")
            return False
            
    return True

def _create_article_item(self, response: Response, title: str, 
                        content: str) -> ArticuloInItem:
    """
    Crear item con todos los campos requeridos.
    """
    item = ArticuloInItem()
    
    # Campos obligatorios
    item['url'] = response.url
    item['fuente'] = self.name
    item['titular'] = title
    item['contenido_texto'] = content
    item['contenido_html'] = response.text
    
    # Información del medio
    item['medio'] = self.medio_nombre
    item['medio_url_principal'] = f"https://{self.allowed_domains[0]}"
    item['pais_publicacion'] = self.pais
    item['tipo_medio'] = self.tipo_medio
    
    # Extraer metadata
    item['fecha_publicacion'] = self.extract_publication_date(response)
    item['autor'] = self.extract_author(response) or 'Redacción'
    item['idioma'] = 'es'
    item['seccion'] = self.target_section
    
    # Clasificación
    item['es_opinion'] = self._is_opinion(response)
    item['es_oficial'] = False
    
    # Timestamps
    item['fecha_recopilacion'] = datetime.utcnow()
    
    # Metadata
    metadata = self._extract_metadata(response)
    metadata.update({
        'spider_type': self.custom_settings.get('spider_type', 'scraping'),
        'section_filter': 'strict',
        'execution_number': self.crawler.stats.get_value('item_scraped_count', 0) + 1
    })
    item['metadata'] = metadata
    
    return item

def _is_opinion(self, response: Response) -> bool:
    """Detectar si es artículo de opinión."""
    indicators = ['/opinion/', '/columna/', '/editorial/', '/tribuna/']
    return any(ind in response.url.lower() for ind in indicators)
```

## 🎨 PERSONALIZACIÓN POR MEDIO

### **Selectores específicos detectados:**
```python
# Generar basado en el análisis
SELECTORES_DETECTADOS = {
    'article_links': [
        # Selectores encontrados en el análisis
        '{selector1}',
        '{selector2}',
        # Fallback genéricos
        'article a::attr(href)',
        '.article-list a::attr(href)',
    ],
    'title': [
        # Específicos del medio
        '{title_selector}',
        # Fallbacks de BaseArticleSpider
        'h1::text',
        '.article-title::text',
    ],
    # ... más selectores
}
```

## 📋 VALIDACIÓN DEL CÓDIGO

### **Tests automáticos a incluir:**
```python
def test_spider_configuration():
    """Verificar configuración correcta."""
    spider = {SpiderClass}()
    
    # Verificar herencia
    assert isinstance(spider, BaseArticleSpider)
    
    # Verificar configuración obligatoria
    assert spider.medio_nombre
    assert spider.pais
    assert spider.tipo_medio in VALID_TIPOS_MEDIO
    
    # Verificar pipelines
    pipelines = spider.custom_settings.get('ITEM_PIPELINES', {})
    assert 'DataValidationPipeline' in str(pipelines)
    assert 'DataCleaningPipeline' in str(pipelines)
    assert 'SupabaseStoragePipeline' in str(pipelines)

def test_section_filtering():
    """Verificar filtrado por sección."""
    spider = {SpiderClass}()
    
    # URLs válidas
    assert spider._is_section_article('https://medio.com/seccion/articulo')
    
    # URLs inválidas
    assert not spider._is_section_article('https://medio.com/otra-seccion/articulo')
    assert not spider._is_section_article('https://medio.com/archivo/articulo')
```

## 🚀 GENERACIÓN FINAL

### **Estructura del archivo generado:**
```
scraper_core/
└── spiders/
    └── {medio}_{seccion}_spider.py
```

### **Comando para probar:**
```bash
# Validar sintaxis
python -m py_compile scraper_core/spiders/{medio}_{seccion}_spider.py

# Ejecutar spider (modo debug)
scrapy crawl {medio}_{seccion} -L DEBUG -s CLOSESPIDER_ITEMCOUNT=5

# Verificar items generados
scrapy crawl {medio}_{seccion} -o test_items.json -s CLOSESPIDER_ITEMCOUNT=3
```

### **Configuración cron:**
```bash
# Agregar a crontab
{frecuencia} cd /path/to/project && scrapy crawl {medio}_{seccion} >> logs/{medio}_{seccion}.log 2>&1
```

## 📊 MÉTRICAS DE ÉXITO

### **El spider generado debe:**
1. ✅ Heredar correctamente de BaseArticleSpider
2. ✅ Llenar todos los campos requeridos de ArticuloInItem
3. ✅ Usar los 3 pipelines del proyecto
4. ✅ Implementar filtrado estricto por sección
5. ✅ Configurar deduplicación (JOBDIR)
6. ✅ Respetar rate limits y robots.txt
7. ✅ Manejar errores apropiadamente
8. ✅ Generar logs informativos

## 📝 DOCUMENTACIÓN A INCLUIR

### **En el docstring del spider:**
```python
"""
Spider para {seccion} de {medio}

Configuración:
- URL objetivo: {url_seccion}
- Estrategia: {tipo_spider}
- Frecuencia: {frecuencia_descripcion}
- Items máximos: {items_limite}

Ejecución:
    scrapy crawl {spider_name}

Monitoreo:
    - Logs: logs/{spider_name}.log
    - Estado: crawl_state_{spider_name}/
    - Items: Almacenados en Supabase

Generado: {fecha_generacion}
"""
```

### **README para el spider:**
```markdown
# Spider: {medio} - {seccion}

## Descripción
Spider especializado que convierte la sección {seccion} de {medio} 
en una fuente tipo RSS mediante extracción periódica.

## Configuración
- **Tipo**: {tipo_spider}
- **Frecuencia**: {frecuencia_descripcion}
- **URL Base**: {url_seccion}
- **Items por ejecución**: {items_limite}

## Ejecución

### Manual:
```bash
scrapy crawl {spider_name}
```

### Programada (cron):
```bash
{frecuencia} cd /path && scrapy crawl {spider_name}
```

## Validación
- Filtrado estricto por sección
- Deduplicación automática
- Validación por pipelines
- Almacenamiento en Supabase

## Mantenimiento
- Revisar logs periódicamente
- Ajustar selectores si cambia el sitio
- Monitorear tasa de éxito en Supabase
```

---

**📚 Documentos relacionados:**
- `MAIN_WORKFLOW.md` - Proceso principal
- `TEMPLATES.md` - Plantillas de código
- `DEFAULTS_CONFIG.md` - Configuraciones
- `ERROR_HANDLING.md` - Manejo de errores
