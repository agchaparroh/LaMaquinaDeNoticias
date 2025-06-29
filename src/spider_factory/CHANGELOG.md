# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-12-27

### 🚨 BREAKING CHANGES

- **Nomenclatura de spiders**: Ahora obligatoriamente `{medio}_{seccion}` (ej: `el_pais_internacional`)
- **Campos obligatorios**: Todos los spiders deben incluir: `medio`, `seccion`, `area_geografica`, `tipo_medio`
- **Campo titular**: Cambio de `item['titulo']` a `item['titular']` en todos los spiders
- **Directorio de salida**: Los spiders se generan en `/src/module_scraper/scraper_core/spiders/`
- **Validación de áreas geográficas**: Solo se aceptan valores de la lista `AREAS_GEOGRAFICAS_VALIDAS`

### ✨ Added

- **Sistema de cache inteligente** con Redis y TTL de 7 días
- **Redis connection pooling** con hasta 50 conexiones concurrentes
- **Sistema de métricas en tiempo real** con KPIs de rendimiento
- **Endpoint `/api/check-duplicate`** para verificar spiders existentes
- **Procesamiento batch mejorado** con límite de 100 items
- **Rate limiting** de 10 requests por minuto por IP
- **WebSocket** para actualizaciones en tiempo real
- **Scripts de migración** para spiders existentes
- **Logging con Loguru** con rotación diaria y separación de errores
- **Validación de campos obligatorios** en modelos Pydantic
- **Detección automática de estrategia** (RSS, Scraping, Playwright)
- **Sistema de patrones reutilizables** por dominio
- **Métricas de performance** con validación de KPIs

### 🔧 Changed

- Actualización a **Pydantic v2** con nuevos validadores
- Mejora en la **gestión de errores** con logging detallado
- **Templates refactorizados** para incluir campos obligatorios
- **API endpoints** actualizados con retrocompatibilidad
- **Configuración centralizada** en `config.py`
- **Análisis más inteligente** con flujo de decisión optimizado

### 🐛 Fixed

- Error de importación `ScrapingStrategy` → `AnalysisStrategy`
- Referencias incorrectas a `config.` → `settings.`
- Problemas con paths relativos en imports
- Manejo de errores en conexión Redis
- Validación de URLs en modelos Pydantic
- Formateo de código con Black opcional

### 🔒 Security

- Validación estricta de entrada en todos los endpoints
- Rate limiting para prevenir abuso
- Sanitización de nombres de spiders
- No exposición de puertos internos (solo a través de NGINX)

### 📊 Performance

- **Reducción de tiempo 97%** vs proceso manual
- **< 5 segundos** para análisis con RSS
- **~20 segundos** para análisis completo primera vez
- **< 2 segundos** para análisis desde cache
- **Procesamiento paralelo** en batch con ThreadPoolExecutor

### 🔄 Migration

- Script `migrate_spider.py` para migración individual
- Script `validate_spiders.py` para validación masiva
- Script `batch_migrate.py` para migración en lote
- Backup automático antes de cada migración
- Modo `--dry-run` para simular cambios

## [1.1.0] - 2024-11-15

### Added
- Soporte inicial para Playwright en sitios con JavaScript
- Detección básica de feeds RSS
- Mejoras en la UI del frontend

### Fixed
- Problemas de conexión con Redis
- Timeout en análisis de sitios grandes

## [1.0.0] - 2024-10-01

### Added
- Versión inicial de Spider Factory
- Generación básica de spiders Scrapy
- Análisis simple de sitios web
- API REST básica
- Integración con module_scraper

---

## Guía de Actualización

### De 1.x a 2.0

1. **Backup de spiders existentes**:
   ```bash
   cp -r /src/module_scraper/scraper_core/spiders /backups/spiders_v1
   ```

2. **Validar spiders actuales**:
   ```bash
   python3 src/validate_spiders.py --report
   ```

3. **Migrar spiders**:
   ```bash
   python3 src/batch_migrate.py --spiders-dir /src/module_scraper/scraper_core/spiders
   ```

4. **Actualizar CSVs** con las nuevas columnas:
   - `area_geografica`
   - `tipo_medio`
   - `frecuencia_minutos`

5. **Actualizar llamadas a la API** con los nuevos campos obligatorios

### Verificación Post-Migración

```bash
# Verificar que todos los spiders son válidos
python3 src/validate_spiders.py

# Test de generación
curl -X POST http://localhost/spider-factory/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "medio": "Test",
    "seccion": "Test",
    "area_geografica": "GLOBAL",
    "tipo_medio": "diario",
    "url": "https://example.com"
  }'
```