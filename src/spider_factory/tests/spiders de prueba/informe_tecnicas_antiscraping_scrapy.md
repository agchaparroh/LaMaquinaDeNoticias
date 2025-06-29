# Informe: Técnicas de Evasión de Medidas Anti-Scraping en Scrapy

**Fecha:** 27 de junio de 2025  
**Fuente:** Documentación oficial de Scrapy (Context7)  
**Enfoque:** Técnicas defensivas para evadir protecciones anti-scraping

## Resumen Ejecutivo

La documentación oficial de Scrapy proporciona múltiples herramientas y middlewares diseñados para evadir las medidas de protección anti-scraping implementadas por sitios web. Este informe analiza las técnicas documentadas oficialmente para la evasión de detección automatizada.

## 1. Gestión de User-Agent

### 1.1 UserAgentMiddleware
Scrapy incluye el `UserAgentMiddleware` que permite a las arañas sobrescribir el User-Agent predeterminado:

```python
# Configuración en spider
class MySpider(scrapy.Spider):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

### 1.2 Configuración Global
```python
# settings.py
USER_AGENT = "MyBot/1.0 (+https://example.com/bot)"
```

**Importancia:** Los sitios web utilizan el User-Agent para identificar bots. La rotación o personalización de este header es fundamental para la evasión.

## 2. Control de Velocidad y Timing

### 2.1 Download Delay
```python
# Configuración de delay por spider
class MySpider(CrawlSpider):
    download_delay = 2  # 2 segundos entre requests
```

### 2.2 Randomización de Delays
```python
# settings.py
RANDOMIZE_DOWNLOAD_DELAY = True  # Default: True
```

Esta configuración introduce variabilidad entre 0.5 * DOWNLOAD_DELAY y 1.5 * DOWNLOAD_DELAY, reduciendo la detectabilidad por análisis estadístico.

## 3. Gestión de Proxies

### 3.1 HttpProxyMiddleware
```python
# Por request
request = scrapy.Request(
    url="http://example.com",
    meta={'proxy': 'http://proxy.example.com:8080'}
)

# Con autenticación
meta={'proxy': 'http://user:pass@proxy.example.com:8080'}
```

### 3.2 Variables de Entorno
Scrapy respeta automáticamente:
- `http_proxy`
- `https_proxy` 
- `no_proxy`

## 4. Gestión de Headers

### 4.1 Headers Predeterminados
```python
# settings.py
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
    'Accept-Encoding': 'gzip, deflate',
    'User-Agent': 'Mozilla/5.0...'
}
```

### 4.2 Referer Middleware
El `RefererMiddleware` automáticamente establece el header Referer:

```python
# Configuración de políticas de referrer
REFERRER_POLICY = 'scrapy.spidermiddlewares.referer.DefaultReferrerPolicy'
```

Políticas disponibles:
- `no-referrer`
- `no-referrer-when-downgrade`
- `same-origin`
- `origin`
- `strict-origin`

## 5. Gestión de Cookies

### 5.1 CookiesMiddleware
```python
# Múltiples sesiones de cookies
for i, url in enumerate(urls):
    yield scrapy.Request(url, meta={'cookiejar': i})

# Mantener cookiejar
def parse_page(self, response):
    return scrapy.Request(
        "http://example.com/next",
        meta={'cookiejar': response.meta['cookiejar']}
    )
```

### 5.2 Debug de Cookies
```python
# settings.py
COOKIES_DEBUG = True  # Para monitorear cookies
```

## 6. Fingerprinting de Requests

### 6.1 Request Fingerprinter Personalizado
```python
from scrapy.utils.request import fingerprint

class CustomRequestFingerprinter:
    def fingerprint(self, request):
        return fingerprint(request, include_headers=['X-ID'])
```

### 6.2 Override por Request
```python
class RequestFingerprinter:
    def fingerprint(self, request):
        if 'fingerprint' in request.meta:
            return request.meta['fingerprint']
        return fingerprint(request)
```

## 7. Robots.txt y Compliance

### 7.1 RobotsTxtMiddleware
```python
# settings.py
ROBOTSTXT_OBEY = True  # Default: False
ROBOTSTXT_USER_AGENT = None  # Usa el User-Agent del request
```

### 7.2 Bypass por Request
```python
request = scrapy.Request(
    url="http://example.com",
    meta={'dont_obey_robotstxt': True}
)
```

## 8. Autenticación HTTP

### 8.1 HttpAuthMiddleware
```python
class MySpider(CrawlSpider):
    http_user = "username"
    http_pass = "password"
    http_auth_domain = "secure.example.com"
```

**Nota de Seguridad:** Es crucial especificar `http_auth_domain` para evitar filtración de credenciales.

## 9. Gestión de Redirecciones

### 9.1 RedirectMiddleware
```python
# Bypass de redirects por request
request = scrapy.Request(
    url="http://example.com",
    meta={'dont_redirect': True}
)

# Configuración global
REDIRECT_ENABLED = False  # Para crawls amplios
```

### 9.2 Tracking de Redirects
```python
def parse(self, response):
    redirect_urls = response.meta.get('redirect_urls', [])
    redirect_reasons = response.meta.get('redirect_reasons', [])
```

## 10. HTTP Caching para Replay

### 10.1 HttpCacheMiddleware
```python
# settings.py
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0  # Cache permanente
HTTPCACHE_POLICY = 'scrapy.extensions.httpcache.DummyPolicy'
```

Útil para:
- Testing offline
- Reproducción exacta de crawls
- Reducción de carga en servidores

## 11. Técnicas Avanzadas de Evasión

### 11.1 Canonicalización de URLs
```python
class CanonicalizeUrl:
    def process_request(self, request, response, spider):
        curl = canonicalize_url(request.url, rules=spider.canonicalization_rules)
        return request.replace(url=curl)
```

### 11.2 AutoThrottle para Adaptación Dinámica
```python
# Prevenir ajustes de delay para requests específicos
request = Request(
    "https://example.com", 
    meta={"autothrottle_dont_adjust_delay": True}
)
```

### 11.3 Compression Handling
```python
# settings.py
COMPRESSION_ENABLED = True  # Maneja gzip, deflate, brotli, zstd
```

## 12. Middlewares de Filtrado

### 12.1 OffsiteMiddleware
```python
# Bypass para requests específicos
request = scrapy.Request(
    url="http://external.com",
    meta={'allow_offsite': True}
)
```

### 12.2 DupeFilter Personalizado
```python
from scrapy.dupefilters import RFPDupeFilter

class CustomDupeFilter(RFPDupeFilter):
    def __init__(self, path=None, debug=False, *, fingerprinter=None):
        super().__init__(path=path, debug=debug, fingerprinter=CustomRequestFingerprinter())
```

## 13. Configuraciones para Crawls Amplios

Para maximizar la evasión en crawls masivos:

```python
# settings.py
COOKIES_ENABLED = False        # Reduce overhead
RETRY_ENABLED = False          # Evita retrasos
REDIRECT_ENABLED = False       # Mantiene requests consistentes
DOWNLOAD_DELAY = 1             # Balance velocidad/stealth
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS = 16       # Aumentar paralelismo
CONCURRENT_REQUESTS_PER_DOMAIN = 8
```

## 14. Monitoreo y Debug

### 14.1 Headers Debugging
```python
# Verificación de headers recibidos
def headers_received(headers, body_length, request, spider):
    # Signal handler para monitorear headers
    pass
```

### 14.2 Memory Debugging
```python
# settings.py
MEMDEBUG_ENABLED = True  # Para detectar leaks
```

## Consideraciones de Seguridad

### Aspectos Éticos
- Respetar robots.txt cuando sea apropiado
- Implementar delays razonables
- No sobrecargar servidores objetivo
- Cumplir con términos de servicio

### Aspectos Técnicos
- Evitar filtración de credenciales
- Usar dominios específicos para autenticación
- Implementar rotación de proxies segura
- Monitorear logs para detectar bloqueos

## Conclusiones

La documentación oficial de Scrapy proporciona un conjunto completo de herramientas para la evasión de medidas anti-scraping:

1. **Control granular** sobre headers, timing y comportamiento
2. **Middlewares especializados** para casos específicos
3. **Configuraciones adaptables** para diferentes escenarios
4. **Herramientas de debugging** para optimización

La efectividad de estas técnicas depende de la implementación cuidadosa y la adaptación a las contramedidas específicas de cada sitio objetivo.

---

*Este informe se basa exclusivamente en la documentación oficial de Scrapy y está destinado únicamente para propósitos educativos y de investigación en seguridad defensiva.*