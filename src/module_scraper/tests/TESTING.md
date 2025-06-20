# Plan de Testing - La Máquina de Noticias

## 📋 Resumen de Tests Implementados

### ✅ Tests Completados

#### 1. **Tests Universales de Spiders** (`test_spiders/`)
- **test_universal_spider.py**: Valida TODOS los spiders automáticamente
  - Herencia correcta de BaseArticleSpider
  - Atributos requeridos del medio
  - Configuración técnica (delays, timeouts)
  - Generación de items válidos
  - Uso de pipelines correctos
  
- **test_generator_compliance.py**: Conformidad con @generador-spiders
  - Límites técnicos por tipo de spider
  - Filtrado por sección
  - Deduplicación configurada
  - Manejo de errores sin crashear

- **test_base_article.py**: Tests de la clase base
  - Métodos de extracción
  - Rotación de user agents
  - Validación de datos

#### 2. **Tests End-to-End** (`e2e/`)
- **test_complete_flow.py**: Flujo completo de extracción
  - Spider → Pipelines → Storage (mockeado)
  - Procesamiento de múltiples items
  - Manejo de items inválidos
  - Integración con pipelines reales

#### 3. **Tests de Middlewares** (`test_middlewares/`)
- **test_middlewares.py**: 
  - Playwright middleware (renderizado JS)
  - Rate limit monitoring
  - User agent rotation
  - Detección de contenido vacío
  - Lógica de reintentos

#### 4. **Tests de Error Handling** (`test_error_handling/`)
- **test_error_handling.py**: Casos edge y errores
  - Errores de red (DNS, Timeout)
  - Errores HTTP (404, 500, etc.)
  - HTML malformado
  - Encoding problemático
  - Valores None/null
  - Unicode y emojis

#### 5. **Tests Existentes** (Ya implementados)
- **test_pipelines/**: Validación y limpieza
- **test_supabase_integration.py**: Integración con BD
- **unit/**: Tests unitarios de componentes

## 🚀 Cómo Ejecutar los Tests

### Ejecutar todos los tests:
```bash
# Desde module_scraper/
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=scraper_core --cov-report=html
```

### Ejecutar categorías específicas:
```bash
# Solo tests de spiders
pytest tests/test_spiders/ -v

# Solo tests E2E
pytest tests/e2e/ -v

# Solo tests de error handling
pytest tests/test_error_handling/ -v

# Solo tests de middlewares
pytest tests/test_middlewares/ -v
```

### Ejecutar el validador universal de spiders:
```bash
# Validar todos los spiders
python tests/test_spiders/run_spider_tests.py --report

# Validar un spider específico
python tests/test_spiders/run_spider_tests.py --spider infobae
```

## 📊 Cobertura de Testing

### Áreas Cubiertas:
- ✅ **Estructura de Spiders**: Validación automática universal
- ✅ **Flujo E2E**: Desde extracción hasta almacenamiento
- ✅ **Middlewares**: Playwright, rate limiting, user agents
- ✅ **Error Handling**: Casos edge, errores de red, HTML malo
- ✅ **Pipelines**: Validación, limpieza, storage
- ✅ **Integración**: Supabase, componentes del sistema

### Características de los Tests:
- **Simples**: Sin complicaciones innecesarias
- **Automáticos**: Se aplican a todos los spiders nuevos
- **Con Mocks**: No requieren conexiones reales
- **Rápidos**: Ejecutan en segundos
- **Mantenibles**: Fáciles de actualizar

## 🎯 Filosofía de Testing

1. **Test Universal**: Un solo test valida TODOS los spiders
2. **Sin Scheduling**: NO validamos frecuencias o cron
3. **Pragmáticos**: Tests que agregan valor real
4. **Con Mocks**: Evitamos dependencias externas
5. **Casos Reales**: Basados en problemas comunes

## 📈 Métricas de Calidad

Los tests verifican:
- **20+ aspectos** de cada spider automáticamente
- **Flujo completo** desde spider hasta storage
- **Casos edge comunes** (HTML malo, errores de red)
- **Integración** entre componentes

## 🔄 Próximos Pasos

Para mejorar la cobertura podrías considerar:
1. Tests de performance (si es crítico)
2. Tests de spiders específicos con datos reales
3. Tests de integración con Supabase real (en CI/CD)
4. Monitoring en producción

---

**Nota**: Todos los tests están diseñados para ser simples, razonables y agregar valor real al proyecto sin complicaciones innecesarias.
