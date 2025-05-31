# User Agent Rotation Testing

Este directorio contiene herramientas para probar la funcionalidad de rotación de user agents implementada con `scrapy-user-agents`.

## Archivos

### `useragent_test.py` (Spider)
Spider de prueba ubicado en `scraper_core/spiders/useragent_test.py` que:
- Hace múltiples requests a `httpbin.org/user-agent`
- Recolecta los user agents utilizados en cada request
- Genera un reporte detallado de la efectividad de la rotación

### `test_user_agents.py` (Script)
Script de testing que:
- Ejecuta automáticamente el spider de prueba
- Analiza los resultados
- Genera un reporte de efectividad
- Limpia archivos temporales

## Uso

### Ejecutar el test automatizado:
```bash
cd /path/to/module_scraper
python scripts/test_user_agents.py
```

### Ejecutar manualmente el spider:
```bash
cd /path/to/module_scraper
scrapy crawl useragent_test -s LOG_LEVEL=INFO -s HTTPCACHE_ENABLED=False
```

## Interpretación de Resultados

### ✅ Éxito
- **3+ user agents únicos**: La rotación funciona correctamente
- El middleware está correctamente configurado

### ⚠️ Advertencia
- **2 user agents únicos**: Rotación limitada, posible configuración subóptima

### ❌ Fallo
- **1 user agent único**: No hay rotación, verificar configuración del middleware

## Configuración Verificada

El test verifica que la siguiente configuración en `settings.py` funcione:

```python
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
}
```

## Notas

- El test usa `httpbin.org/user-agent` que es un servicio público para testing
- Se deshabilita el cache HTTP para este test específico
- Los resultados se guardan temporalmente en `test_results.json` y luego se limpian
- El spider hace 15 requests por defecto para tener una muestra significativa
