# FASE 2: Tests de Integración por Capas - Module Scraper

## 🎯 OBJETIVO
Crear tests automáticos que verifiquen que **todos los componentes del sistema trabajen correctamente en conjunto**, desde el request inicial hasta el almacenamiento final en Supabase.

## 📋 TAREAS ESPECÍFICAS

### **2.1 Test de Middleware Stack Completo**
```python
# Crear: tests/integration/test_middleware_stack.py
Objetivo: Verificar que TODOS los middlewares cooperan sin conflictos

MIDDLEWARES A PROBAR JUNTOS:
- RobotsTxtMiddleware (scrapy built-in)
- RandomUserAgentMiddleware (scrapy-user-agents) 
- CrawlOnceMiddleware (scrapy-crawl-once)
- PlaywrightCustomDownloaderMiddleware (custom)
- AutoThrottleMiddleware (scrapy built-in)

TEST CASES:
1. Request normal → todos middlewares procesan correctamente
2. Request con playwright=True → stack respeta configuración
3. Request duplicado → CrawlOnce bloquea apropiadamente  
4. Request con user-agent custom → RandomUserAgent no interfiere
5. Multiple requests → rate limiting funciona sin romper otros middlewares

VERIFICACIONES:
✅ Ningún middleware cancela requests inesperadamente
✅ Meta information se preserva entre middlewares
✅ Prioridades de ejecución son respetadas
✅ No hay memory leaks o resource locks
✅ Logging funciona en cada middleware
```

### **2.2 Test de Spider + Middleware Integration**
```python
# Crear: tests/integration/test_spider_middleware.py
Objetivo: Verificar BaseArticleSpider funciona con todos middlewares activos

ESCENARIOS A PROBAR:
1. ESCENARIO SIMPLE:
   - URL: http://httpbin.org/html (contenido estático)
   - Expected: No Playwright, user-agent rotated, contenido extraído

2. ESCENARIO JAVASCRIPT:
   - URL: https://quotes.toscrape.com/js/ (requiere JS)
   - Expected: Detección contenido vacío → Playwright → contenido extraído

3. ESCENARIO ROBOTS.TXT:
   - URL con robots.txt restrictivo
   - Expected: Request bloqueado apropiadamente

4. ESCENARIO DUPLICADO:
   - Misma URL 2 veces
   - Expected: Segunda vez bloqueada por CrawlOnce

5. ESCENARIO ERROR:
   - URL que retorna 404/500
   - Expected: Error handling correcto, no crash del spider

VERIFICACIONES:
✅ parse_article se ejecuta con response correcta
✅ Middleware effects son aplicados (user-agent, etc.)
✅ Error handling funciona en cada escenario
✅ Items son generados apropiadamente
✅ Meta information llega al spider correctamente
```

### **2.3 Test de Pipeline Data Processing Chain**
```python
# Crear: tests/integration/test_pipeline_chain.py
Objetivo: Verificar que los pipelines procesan datos en el orden correcto

PIPELINE ORDER A PROBAR:
1. DataCleaningPipeline (priority: 200)
2. DataValidationPipeline (priority: 300) 
3. SupabaseStoragePipeline (priority: 400)

TEST ITEMS:
1. ITEM VÁLIDO COMPLETO:
   - Todos los campos requeridos
   - Datos limpios y válidos
   - Expected: Pasa todos pipelines → almacenado en DB

2. ITEM CON DATOS SUCIOS:
   - HTML tags en texto
   - Espacios extra, caracteres raros
   - Expected: Cleaning pipeline limpia → validation pasa → storage exitoso

3. ITEM CON DATOS FALTANTES:
   - Campos requeridos ausentes
   - Expected: Cleaning pasa → validation falla → no llega a storage

4. ITEM CON DATOS INVÁLIDOS:
   - URLs malformadas, fechas incorrectas
   - Expected: Cleaning intenta → validation falla → no storage

5. ITEM CON ERROR DE STORAGE:
   - Mock Supabase connection failure
   - Expected: Cleaning + validation pasan → storage falla gracefully

VERIFICACIONES:
✅ Items pasan por pipelines en orden correcto
✅ Cleaning pipeline transforma datos apropiadamente
✅ Validation pipeline rechaza items inválidos
✅ Storage pipeline maneja errores correctamente
✅ Failed items no corrompen el pipeline para items siguientes
```

### **2.4 Test End-to-End Complete Flow**
```python
# Crear: tests/integration/test_end_to_end.py
Objetivo: Verificar flujo completo desde request hasta storage

FLUJO COMPLETO A PROBAR:
Request → Middleware Stack → Spider → Item Generation → Pipeline Chain → Storage

CASOS COMPLETOS:
1. FLUJO EXITOSO NORMAL:
   - URL simple → spider extrae → pipelines procesan → DB storage
   - Verificar: Data integrity desde response hasta DB

2. FLUJO CON PLAYWRIGHT:
   - URL JS-heavy → empty detection → Playwright retry → content extracted → stored
   - Verificar: playwright_retried meta se maneja correctamente

3. FLUJO CON ERRORES RECUPERABLES:
   - URL con timeouts → retries → eventual success → storage
   - Verificar: Error recovery no afecta data quality

4. FLUJO CON FALLOS DEFINITIVOS:
   - URL definitivamente inaccesible → graceful failure → no storage
   - Verificar: System stability maintained

VERIFICACIONES CRÍTICAS:
✅ Data integrity mantenida en todo el flujo
✅ No memory leaks en flujos largos
✅ Error handling no interrumpe otros requests
✅ Statistics/metrics son actualizadas correctamente
✅ Logging captura eventos importantes en cada paso
```

## 🔧 HERRAMIENTAS Y SETUP

### **Base Test Class Template**
```python
# Base class para todos los integration tests
import unittest
from scrapy.utils.test import get_crawler
from scrapy.http import Request, HtmlResponse
from scrapy import Spider
from unittest.mock import Mock, patch

class IntegrationTestBase(unittest.TestCase):
    def setUp(self):
        self.crawler = get_crawler(settings_module='scraper_core.settings')
        self.spider = Spider('test_spider')
        self.spider.crawler = self.crawler
        
    def create_response(self, url, body=b'<html></html>', status=200):
        return HtmlResponse(url=url, body=body, status=status)
        
    def assert_middleware_chain_executed(self, request, expected_middlewares):
        # Helper to verify middleware execution
        pass
```

### **Mock Configurations**
```python
# Para tests que requieren servicios externos
TEST_SETTINGS = {
    'SUPABASE_URL': 'mock://test.supabase.co',
    'SUPABASE_SERVICE_ROLE_KEY': 'test_key_12345',
    'PLAYWRIGHT_TIMEOUT': 5000,  # Shorter for tests
    'LOG_LEVEL': 'DEBUG',
    'HTTPCACHE_ENABLED': False,  # Disable for predictable tests
}
```

## 📊 CRITERIOS DE ÉXITO

### **Test Pass Criteria**
- ✅ **100% de tests pasan** sin errores
- ✅ **No memory leaks** detectados durante tests
- ✅ **Performance acceptable** (< 10 seconds por test completo)
- ✅ **Error handling robusto** en todos los escenarios
- ✅ **Data integrity preservada** en todo el flujo

### **Integration Health Metrics**
- ✅ **Middleware execution order** respetado
- ✅ **Pipeline data flow** sin corruption
- ✅ **Error propagation** controlled y graceful
- ✅ **Resource cleanup** automático tras tests
- ✅ **Configuration consistency** mantenida

## 🚀 IMPLEMENTACIÓN

### **Orden de Desarrollo Recomendado:**
1. **Crear base test infrastructure** (IntegrationTestBase, mocks, helpers)
2. **Implementar test_middleware_stack.py** (fundación del sistema)
3. **Implementar test_spider_middleware.py** (integración spider-middleware)  
4. **Implementar test_pipeline_chain.py** (flujo de datos)
5. **Implementar test_end_to_end.py** (validación completa)

### **Ejecutar Tests:**
```bash
# Individual test files
python -m pytest tests/integration/test_middleware_stack.py -v
python -m pytest tests/integration/test_spider_middleware.py -v  
python -m pytest tests/integration/test_pipeline_chain.py -v
python -m pytest tests/integration/test_end_to_end.py -v

# All integration tests
python -m pytest tests/integration/ -v

# With coverage
python -m pytest tests/integration/ --cov=scraper_core --cov-report=html
```

### **Expected Output:**
```
PHASE 2 INTEGRATION TESTS RESULTS:
✅ Middleware Stack: 8/8 tests passed
✅ Spider-Middleware: 5/5 tests passed  
✅ Pipeline Chain: 5/5 tests passed
✅ End-to-End Flow: 4/4 tests passed

🎯 INTEGRATION STATUS: HEALTHY
📊 Total Coverage: 85%+
⚡ Average Test Time: 6.2 seconds
🔧 Issues Found: 0 critical, 2 minor warnings
```

## 🎯 DELIVERABLES

Al completar esta fase, tendrás:

1. **Suite completa de integration tests** (4 archivos)
2. **Reporte de integración** con issues encontrados
3. **Performance metrics** del sistema integrado
4. **Fixes implementados** para issues críticos
5. **Documentation updates** basada en hallazgos

## ⚠️ RED FLAGS A VIGILAR

Durante los tests, estar alerta a:
- **Requests que nunca completan** (deadlocks)
- **Memory usage que crece constantemente** (leaks)
- **Tests que fallan intermitentemente** (race conditions)
- **Configuraciones que se ignoran** (override issues)
- **Data corruption** en el pipeline chain

---

## 🎪 **PROMPT EJECUTABLE:**

**"Crea una suite completa de tests de integración para el module_scraper que verifique que todos los componentes (middlewares, spiders, pipelines, storage) trabajen correctamente en conjunto. Incluye tests para flujo normal, manejo de errores, Playwright integration, y validación end-to-end. Los tests deben ser robustos, rápidos, y proporcionar métricas claras de salud del sistema integrado."**

¡Que comience la FASE 2! 🚀
