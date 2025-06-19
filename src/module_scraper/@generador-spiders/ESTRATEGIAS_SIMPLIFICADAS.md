# ESTRATEGIAS SIMPLIFICADAS - La Máquina de Noticias

## 🎯 OBJETIVO
Determinar rápidamente qué tipo de spider generar basándose en las características de la sección objetivo.

## 🔍 ÁRBOL DE DECISIÓN SIMPLE

```
¿El usuario proporciona URL RSS?
├─ SÍ → Generar RSS Spider
│   ├─ Template: rss_spider
│   ├─ Análisis: No requerido
│   └─ Complejidad: Baja
│
└─ NO → Analizar la sección
    │
    ├─ ¿Contenido carga con JavaScript?
    │   ├─ SÍ → Generar Playwright Spider
    │   │   ├─ Template: playwright_spider
    │   │   ├─ Análisis: 3-4 requests
    │   │   └─ Complejidad: Alta
    │   │
    │   └─ NO → Generar Scraping Spider
    │       ├─ Template: scraping_spider
    │       ├─ Análisis: 2-3 requests
    │       └─ Complejidad: Media
```

## 📊 MATRIZ DE ESTRATEGIAS

| Característica | RSS Spider | Scraping Spider | Playwright Spider |
|----------------|------------|-----------------|-------------------|
| **RSS disponible** | ✅ Sí | ❌ No | ❌ No |
| **JavaScript requerido** | N/A | ❌ No | ✅ Sí |
| **Velocidad extracción** | ⚡ Rápida | 🔄 Media | 🐢 Lenta |
| **Consumo recursos** | 🟢 Bajo | 🟡 Medio | 🔴 Alto |
| **Frecuencia ejecución** | 30 min | 60 min | 120 min |
| **Items por ejecución** | 50 | 30 | 20 |
| **Complejidad mantenimiento** | 🟢 Baja | 🟡 Media | 🔴 Alta |

## 🚀 ESTRATEGIA 1: RSS SPIDER

### **Cuándo usar:**
```python
if usuario_input.get('rss_disponible') == 'Sí':
    return 'rss_spider'
```

### **Características:**
- ✅ Usa feed RSS oficial
- ✅ Mínimo consumo de recursos
- ✅ Alta confiabilidad
- ✅ Actualizaciones frecuentes

### **Configuración recomendada:**
```python
config = {
    'strategy': 'rss',
    'download_delay': 2.0,
    'items_limit': 50,
    'frequency': '*/30 * * * *',  # Cada 30 minutos
    'analysis_required': False
}
```

### **Ventajas:**
1. No requiere análisis de selectores
2. Estructura de datos consistente
3. Menor probabilidad de cambios
4. Respeta implícitamente el sitio

## 🔧 ESTRATEGIA 2: SCRAPING SPIDER

### **Cuándo usar:**
```python
if not rss_disponible and not requires_javascript:
    return 'scraping_spider'
```

### **Análisis requerido:**
```python
# 1. Obtener página de sección
section_html = firecrawl_scrape(url_seccion)

# 2. Detectar enlaces de artículos
article_patterns = detect_article_links(section_html)

# 3. Obtener muestra de artículo
if article_patterns:
    sample_article = firecrawl_scrape(article_patterns[0])
    selectors = extract_selectors(sample_article)
```

### **Configuración recomendada:**
```python
config = {
    'strategy': 'scraping',
    'download_delay': 3.0,
    'items_limit': 30,
    'frequency': '0 * * * *',  # Cada hora
    'analysis_required': True,
    'requests_needed': 2-3
}
```

### **Consideraciones:**
- Requiere detectar selectores CSS
- Susceptible a cambios en el sitio
- Necesita filtrado estricto por sección

## 🎭 ESTRATEGIA 3: PLAYWRIGHT SPIDER

### **Cuándo usar:**
```python
if not rss_disponible and requires_javascript:
    return 'playwright_spider'
```

### **Indicadores de JavaScript:**
```python
def requires_javascript(html_content):
    """Detectar si la página requiere JavaScript."""
    indicators = [
        'react-root',
        'vue-app',
        'angular',
        '__NEXT_DATA__',
        'window.__INITIAL_STATE__',
        '<noscript>',
        'lazy-load',
        'infinite-scroll'
    ]
    
    # Verificar indicadores
    for indicator in indicators:
        if indicator in html_content:
            return True
    
    # Verificar si hay poco contenido HTML
    if len(html_content) < 10000:
        return True
        
    # Verificar ausencia de artículos
    if not detect_article_links(html_content):
        return True
        
    return False
```

### **Configuración recomendada:**
```python
config = {
    'strategy': 'playwright',
    'download_delay': 5.0,
    'items_limit': 20,
    'frequency': '0 */2 * * *',  # Cada 2 horas
    'analysis_required': True,
    'requests_needed': 3-4,
    'playwright_config': {
        'headless': True,
        'timeout': 30000,
        'wait_for_selector': '.article'
    }
}
```

### **Consideraciones:**
- Mayor consumo de recursos
- Más lento pero más confiable
- Maneja sitios modernos SPA

## 📋 PROCESO DE DECISIÓN

### **1. Información del usuario:**
```yaml
url_seccion: "https://elpais.com/internacional"
medio: "El País"
pais: "España"
tipo_medio: "diario"
rss_disponible: "No"  # Crítico para decisión
```

### **2. Si no hay RSS, análisis mínimo:**
```python
async def analizar_seccion(url_seccion):
    # Request 1: Página de sección
    section_data = await firecrawl_scrape(url_seccion)
    
    # Detectar necesidad de JavaScript
    needs_js = requires_javascript(section_data.content)
    
    # Request 2: Muestra de artículo (si no necesita JS)
    if not needs_js:
        article_links = detect_article_links(section_data.content)
        if article_links:
            article_data = await firecrawl_scrape(article_links[0])
            selectors = extract_selectors(article_data)
    
    return {
        'requires_javascript': needs_js,
        'selectors': selectors if not needs_js else None,
        'total_requests': 2 if not needs_js else 1
    }
```

### **3. Decisión final:**
```python
def decidir_estrategia(user_input, analysis=None):
    # Prioridad 1: RSS si está disponible
    if user_input.get('rss_disponible') == 'Sí':
        return {
            'strategy': 'rss',
            'reason': 'RSS disponible',
            'template': 'rss_spider'
        }
    
    # Prioridad 2: Verificar JavaScript
    if analysis and analysis.get('requires_javascript'):
        return {
            'strategy': 'playwright',
            'reason': 'Requiere JavaScript',
            'template': 'playwright_spider'
        }
    
    # Default: Scraping HTML
    return {
        'strategy': 'scraping',
        'reason': 'HTML estático',
        'template': 'scraping_spider'
    }
```

## 🎯 EJEMPLOS DE DECISIÓN

### **Ejemplo 1: El País Internacional**
```yaml
Input:
  url: "https://elpais.com/internacional"
  rss_disponible: "No"

Análisis:
  - HTML estático detectado
  - Selectores claros encontrados
  - No requiere JavaScript

Decisión: scraping_spider
Razón: Contenido HTML accesible
```

### **Ejemplo 2: Medio con RSS**
```yaml
Input:
  url: "https://ejemplo.com/economia"
  rss_disponible: "Sí"
  rss_url: "https://ejemplo.com/rss/economia"

Análisis: No requerido

Decisión: rss_spider
Razón: RSS disponible
```

### **Ejemplo 3: Sitio SPA moderno**
```yaml
Input:
  url: "https://modernnews.com/tech"
  rss_disponible: "No"

Análisis:
  - React detectado
  - Contenido carga dinámicamente
  - Requiere JavaScript

Decisión: playwright_spider
Razón: Aplicación JavaScript
```

## 📊 COMPARACIÓN DE RECURSOS

```python
RESOURCE_CONSUMPTION = {
    'rss': {
        'cpu': 'Bajo',
        'memoria': 'Mínima',
        'red': 'Mínima',
        'tiempo_promedio': '2-5 min'
    },
    'scraping': {
        'cpu': 'Medio',
        'memoria': 'Media',
        'red': 'Media',
        'tiempo_promedio': '5-15 min'
    },
    'playwright': {
        'cpu': 'Alto',
        'memoria': 'Alta',
        'red': 'Alta',
        'tiempo_promedio': '15-30 min'
    }
}
```

## 🚨 REGLAS DE ORO

1. **Siempre preferir RSS** si está disponible
2. **Minimizar uso de Playwright** (solo cuando es necesario)
3. **Análisis mínimo** para no agotar contexto
4. **Configuración conservadora** siempre
5. **Filtrado estricto** por sección

---

**📚 Siguiente paso:** Una vez decidida la estrategia, ir a `CODE_GENERATION.md`
