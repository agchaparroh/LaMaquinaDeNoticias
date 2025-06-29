# Proyecto CPMS3: Implementación de Técnicas de Evasión

## 📋 Descripción

Este proyecto implementa las 3 técnicas de evasión esenciales para mejorar la efectividad del sistema de scraping de La Máquina de Noticias:

1. **Headers HTTP Realistas** - Headers completos de navegador real
2. **User-Agent List Actualizado** - Lista moderna con rotación automática  
3. **Referer Middleware Inteligente** - Simulación de navegación natural

## 🎯 Objetivo

Mejorar la tasa de éxito del scraping del 40-50% actual al 80-85% mediante técnicas de evasión estándar y probadas.

## ⚠️ IMPORTANTE: Consulta Obligatoria de Context7

Este proyecto **REQUIERE** que el desarrollador (Claude) consulte la documentación oficial en Context7 antes de implementar cada fase. El plan incluye recordatorios específicos con los comandos exactos a ejecutar.

### Comandos Context7 Requeridos:

```bash
# Para Headers HTTP
mcp__context7__resolve-library-id --libraryName 'scrapy'
mcp__context7__get-library-docs \
  --context7CompatibleLibraryID '/scrapy/scrapy' \
  --topic 'DEFAULT_REQUEST_HEADERS DefaultHeadersMiddleware'

# Para User-Agent
mcp__context7__get-library-docs \
  --context7CompatibleLibraryID '/scrapy/scrapy' \
  --topic 'UserAgentMiddleware USER_AGENT'

# Para Referer
mcp__context7__get-library-docs \
  --context7CompatibleLibraryID '/scrapy/scrapy' \
  --topic 'RefererMiddleware REFERER_ENABLED spider middleware'
```

## 🚀 Cómo Ejecutar

### Opción 1: Con Enhanced Runner (RECOMENDADO)
```bash
# Validación completa antes de ejecutar
python ../../tools/enhanced_runner.py execution_plan.yaml

# Modo strict para máxima seguridad
python ../../tools/enhanced_runner.py execution_plan.yaml --strict

# Solo validar sin ejecutar
python ../../tools/enhanced_runner.py execution_plan.yaml --dry-run
```

### Opción 2: Con Runner Original
```bash
python ../../tools/runner.py execution_plan.yaml
```

## 📁 Archivos que se Modificarán

### Modificaciones:
- `src/module_scraper/scraper_core/settings.py` - Headers y middlewares
- `src/spider_factory/templates/spiders/base_spider.j2` - Soporte headers custom
- `src/spider_factory/src/config.py` - Headers de evasión

### Creaciones:
- `src/module_scraper/scraper_core/utils/user_agents.py` - Lista de UAs
- `src/module_scraper/scraper_core/middlewares/smart_referer_middleware.py`
- `src/spider_factory/tests/test_evasion_techniques.py` - Tests
- `src/spider_factory/docs/EVASION_TECHNIQUES_IMPLEMENTED.md` - Documentación

## 🧪 Verificación

Después de ejecutar, verificar con:

```bash
cd /mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias
python3 src/spider_factory/tests/test_evasion_techniques.py
```

Deberías ver:
```
Testing Técnicas de Evasión - Spider Factory
==================================================

=== Testing Headers HTTP ===
✓ Sec-Fetch-Dest: document
✓ Sec-Fetch-Mode: navigate
✓ Cache-Control: no-cache
✓ Accept-Encoding: gzip, deflate, br
✓ Headers HTTP configurados correctamente

=== Testing User Agents ===
✓ Desktop agents: 22
✓ Mobile agents: 6
✓ Total agents: 168

=== Testing Referer Configuration ===
✓ REFERER_ENABLED: True
✓ SmartRefererMiddleware: scraper_core.middlewares.smart_referer_middleware.SmartRefererMiddleware

Total: 3/3 tests pasaron
```

## 📊 Impacto Esperado

| Métrica | Antes | Después |
|---------|-------|---------|
| Tasa de éxito | 40-50% | 80-85% |
| Sitios bloqueados | 50-60% | 15-20% |
| Detección como bot | Alta | Baja |

## 🔧 Mantenimiento

- **User Agents**: Actualizar cada 3-6 meses
- **Headers**: Revisar anualmente
- **Referer**: No requiere mantenimiento

## 📝 Notas

- El plan es idempotente (se puede ejecutar múltiples veces)
- Incluye backups automáticos antes de modificaciones
- Los archivos "eliminados" van a staging, no se borran
- Compatible con la infraestructura actual

---

**CPMS3 Project** - Ejecución determinista con validación inteligente