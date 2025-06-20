# Tests de Spiders - La Máquina de Noticias

## 📋 Descripción

Este directorio contiene tests exhaustivos para verificar que todos los spiders del proyecto cumplen con:
1. Los estándares del proyecto La Máquina de Noticias
2. Las pautas establecidas por el @generador-spiders
3. El comportamiento tipo RSS artificial requerido

## 🎯 Objetivo

Garantizar que todos los spiders (actuales y futuros) funcionen correctamente y cumplan con las especificaciones del sistema, facilitando la adición de nuevos medios sin comprometer la calidad.

## 📁 Estructura

```
test_spiders/
├── __init__.py                    # Exporta funciones principales
├── test_universal_spider.py       # Test universal para TODOS los spiders
├── test_generator_compliance.py   # Verificación de conformidad con @generador-spiders
├── test_base_article.py          # Tests para la clase base BaseArticleSpider
├── run_spider_tests.py           # Script para ejecutar tests fácilmente
└── README.md                     # Este archivo
```

## 🧪 Tests Incluidos

### 1. **Test Universal (`test_universal_spider.py`)**

Verifica que TODOS los spiders cumplan con:
- ✅ Herencia correcta de `BaseArticleSpider`
- ✅ Atributos requeridos (`medio_nombre`, `pais`, `tipo_medio`, etc.)
- ✅ Configuración adecuada (rate limits, concurrencia, timeouts)
- ✅ Uso de pipelines correctos
- ✅ Generación de items válidos con todos los campos
- ✅ Filtrado por sección
- ✅ Manejo de errores
- ✅ Respeto a robots.txt

### 2. **Test de Conformidad (`test_generator_compliance.py`)**

Verifica cumplimiento específico con @generador-spiders:
- ✅ Límites según tipo de spider (RSS/Scraping/Playwright)
- ✅ Comportamiento tipo RSS artificial
- ✅ Configuración de deduplicación
- ✅ Metadata requerida
- ✅ Rate limiting conservador
- ✅ Filtrado estricto de URLs
- ✅ Resilencia a errores

### 3. **Test de Base (`test_base_article.py`)**

Verifica la funcionalidad de `BaseArticleSpider`:
- ✅ Extracción de título, contenido, fecha, autor
- ✅ Manejo de diferentes formatos HTML
- ✅ Extracción de datos estructurados (JSON-LD)
- ✅ Validación de artículos
- ✅ Rotación de user agents
- ✅ Logging y estadísticas

## 🚀 Uso

### Ejecutar Todos los Tests

```bash
# Desde el directorio module_scraper
python tests/test_spiders/run_spider_tests.py

# O usando pytest directamente
pytest tests/test_spiders/ -v
```

### Ejecutar Tests Específicos

```bash
# Solo tests universales
python tests/test_spiders/run_spider_tests.py --universal

# Solo tests de conformidad
python tests/test_spiders/run_spider_tests.py --compliance

# Validar un spider específico
python tests/test_spiders/run_spider_tests.py --spider infobae

# Generar reporte completo
python tests/test_spiders/run_spider_tests.py --report
```

### Con Análisis de Cobertura

```bash
# Ejecutar con cobertura
python tests/test_spiders/run_spider_tests.py --coverage

# O con pytest
pytest tests/test_spiders/ --cov=scraper_core.spiders --cov-report=html
```

## 📊 Interpretación de Resultados

### Estados de Conformidad

- **COMPLIANT** ✅: El spider cumple todos los requisitos (90%+ de puntuación)
- **MOSTLY_COMPLIANT** ⚠️: El spider cumple la mayoría de requisitos (70-89%)
- **NON_COMPLIANT** ❌: El spider requiere correcciones importantes (<70%)

### Ejemplo de Salida

```
=== Validando Spider: infobae_spider ===

✓ Herencia correcta de BaseArticleSpider
✓ Atributos requeridos presentes
✓ Configuración correcta
✓ Usa pipelines requeridos
✓ Genera items con campos requeridos
✓ Implementa filtrado por sección
✓ Tiene deduplicación configurada
✓ Respeta límites de rate
✓ Incluye metadata apropiada
✓ Maneja errores correctamente

Estado: COMPLIANT
Puntuación: 100/100 (100.0%)
```

## 🔧 Agregar Tests para Nuevos Spiders

Los tests son **universales** y se aplican automáticamente a todos los spiders. Al crear un nuevo spider que herede de `BaseArticleSpider`, será testeado automáticamente.

### Requisitos para Pasar los Tests

1. **Heredar de BaseArticleSpider**
   ```python
   class MiNuevoSpider(BaseArticleSpider):
   ```

2. **Definir atributos requeridos**
   ```python
   medio_nombre = 'Mi Medio'
   pais = 'Argentina'
   tipo_medio = 'diario'
   target_section = 'economia'
   ```

3. **Configuración apropiada**
   ```python
   custom_settings = {
       **BaseArticleSpider.custom_settings,
       'DOWNLOAD_DELAY': 3.0,
       'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
       'CLOSESPIDER_ITEMCOUNT': 30,
       # etc...
   }
   ```

4. **Implementar métodos requeridos**
   - `parse()` o `parse_feed()` para RSS
   - `parse_article()` que retorne `ArticuloInItem`
   - `_is_section_article()` para filtrado

## 🐛 Debugging de Fallos

### Si un spider falla los tests:

1. **Revisar el mensaje de error**
   ```bash
   AssertionError: mi_spider debe heredar de BaseArticleSpider
   ```

2. **Ejecutar validación específica**
   ```bash
   python tests/test_spiders/run_spider_tests.py --spider mi_spider
   ```

3. **Verificar en código**
   ```python
   from tests.test_spiders import validate_spider
   from scraper_core.spiders.mi_spider import MiSpider
   
   validate_spider(MiSpider)
   ```

## 📈 Métricas de Calidad

Los tests verifican más de **20 aspectos** de cada spider:

- Estructura y herencia
- Configuración y settings
- Generación de items
- Manejo de errores
- Comportamiento tipo RSS
- Filtrado y deduplicación
- Rate limiting
- Metadata y documentación

## 🔄 Integración Continua

Estos tests deben ejecutarse:
- Antes de cada commit
- En el pipeline de CI/CD
- Después de generar nuevos spiders
- Periódicamente para detectar regresiones

## 📚 Documentación Relacionada

- [Generador de Spiders](../../@generador-spiders/README.md)
- [BaseArticleSpider](../../scraper_core/spiders/base/README.md)
- [Guía de Desarrollo](../../docs/development/)

## ❓ FAQ

**P: ¿Por qué mi spider pasa los tests pero no funciona en producción?**
R: Los tests verifican estructura y configuración, pero no conexión real. Prueba el spider manualmente con:
```bash
scrapy crawl mi_spider -L DEBUG
```

**P: ¿Cómo excluir un spider de los tests?**
R: Añádelo a `EXCLUDED_SPIDERS` en `test_universal_spider.py` (no recomendado).

**P: ¿Los tests son lentos?**
R: Los tests no ejecutan scraping real, son rápidos (~segundos). Si son lentos, revisa que no estés importando módulos pesados.

---

**Última actualización:** Junio 2025
**Mantenido por:** Equipo La Máquina de Noticias
