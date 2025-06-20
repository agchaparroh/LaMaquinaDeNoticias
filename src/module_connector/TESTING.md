# Plan de Testing - Module Connector

## Resumen Ejecutivo

Este documento detalla el plan de testing completo para el módulo `module_connector`, que actúa como puente entre `module_scraper` y `module_pipeline` en el sistema "La Máquina de Noticias".

## Objetivos de Testing

1. **Cobertura de código**: Alcanzar >85% de cobertura
2. **Confiabilidad**: Garantizar procesamiento robusto de archivos
3. **Resiliencia**: Manejo correcto de errores y casos edge
4. **Performance**: Tests ejecutables en <30 segundos
5. **Mantenibilidad**: Tests claros y bien documentados

## Estrategia de Testing

### 1. Tests Unitarios (40% del esfuerzo)

#### Configuración (test_config.py)
- ✅ Carga de variables de entorno
- ✅ Valores por defecto
- ✅ Conversión de tipos
- ✅ Validación de configuración completa

#### Modelos (test_models.py)
- ✅ Validación de ArticuloInItem
- ✅ Campos requeridos vs opcionales
- ✅ Parsing de fechas
- ✅ Función prepare_articulo
- ✅ Manejo de campos extra

#### Funciones Auxiliares (test_helpers.py)
- ✅ Setup de logging
- ✅ Inicialización de Sentry
- ✅ Movimiento de archivos
- ✅ Manejo de errores

### 2. Tests de Integración (50% del esfuerzo)

#### Procesamiento de Archivos (test_file_processing.py)
- ✅ Archivos .json.gz válidos
- ✅ Archivos corruptos
- ✅ JSON malformado
- ✅ Artículos mixtos (válidos/inválidos)
- ✅ Contenido Unicode
- ✅ Procesamiento de pendientes

#### Comunicación API (test_api_client.py)
- ✅ Envío exitoso (202)
- ✅ Errores de validación (400)
- ✅ Errores de servidor (500/503)
- ✅ Lógica de reintentos
- ✅ Timeouts y errores de conexión
- ✅ Envío en lote

#### Flujo Completo (test_workflow.py)
- ✅ Workflow end-to-end
- ✅ Monitoreo continuo
- ✅ Procesamiento al inicio
- ✅ Shutdown graceful
- ✅ Manejo de permisos
- ✅ Recuperación ante errores

### 3. Tests de Casos Edge (10% del esfuerzo)

- ✅ Archivos que desaparecen durante procesamiento
- ✅ Nombres de archivo duplicados
- ✅ Directorio no existente
- ✅ Espacio en disco lleno (simulado)
- ✅ Interrupciones del proceso

## Herramientas y Dependencias

### Dependencias de Testing
```txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
aioresponses==0.7.4
pytest-env==1.1.1
freezegun==1.2.2
```

### Herramientas de Análisis
- **pytest-cov**: Análisis de cobertura
- **pytest-html**: Reportes HTML
- **pytest-xdist**: Ejecución paralela (opcional)

## Métricas de Calidad

### Cobertura de Código
- **Meta**: >85% de cobertura total
- **Crítico**: 100% en funciones de procesamiento de archivos
- **Importante**: >90% en validación de modelos
- **Deseable**: >80% en funciones auxiliares

### Tiempo de Ejecución
- Tests unitarios: <5 segundos
- Tests de integración: <20 segundos
- Suite completa: <30 segundos

### Mantenibilidad
- Cada test con docstring descriptivo
- Fixtures reutilizables en conftest.py
- Nombres de tests descriptivos
- Agrupación lógica de tests

## Plan de Implementación

### Fase 1: Tests Críticos ✅
- Configuración básica
- Modelo ArticuloInItem
- Procesamiento de archivos válidos
- Comunicación básica con API

### Fase 2: Tests de Robustez ✅
- Manejo de errores
- Reintentos y timeouts
- Casos edge de archivos
- Movimiento con duplicados

### Fase 3: Tests Completos ✅
- Workflows end-to-end
- Monitoreo continuo
- Integración completa
- Documentación

## Ejecución y CI/CD

### Comandos de Ejecución

```bash
# Tests completos con cobertura
pytest tests/ --cov=src --cov-report=term-missing -v

# Solo tests críticos (marcados)
pytest tests/ -m critical -v

# Tests en paralelo (requiere pytest-xdist)
pytest tests/ -n auto -v
```

### Integración Continua

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: pytest tests/ --cov=src --cov-fail-under=85
```

## Mantenimiento de Tests

### Al Añadir Features
1. Escribir tests antes del código (TDD)
2. Cubrir casos positivos y negativos
3. Actualizar documentación de tests
4. Verificar que no se rompen tests existentes

### Al Corregir Bugs
1. Escribir test que reproduzca el bug
2. Verificar que el test falla
3. Implementar la corrección
4. Verificar que el test pasa
5. Añadir test de regresión

### Revisión Periódica
- Mensual: Revisar tests flaky
- Trimestral: Actualizar dependencias
- Semestral: Auditoría de cobertura

## Riesgos y Mitigaciones

### Riesgos Identificados
1. **Tests flaky por timing**: Usar mocks en lugar de sleeps
2. **Dependencias externas**: Mockear todas las llamadas externas
3. **Diferencias OS**: Usar pathlib para rutas
4. **Tests lentos**: Optimizar fixtures y usar caché

### Mitigaciones
- Todos los tests deben ser determinísticos
- No depender de servicios externos reales
- Usar fixtures para datos de prueba
- Limpiar recursos después de cada test

## Conclusión

El plan de testing implementado proporciona:
- ✅ Alta cobertura de código (objetivo >85%)
- ✅ Tests rápidos y confiables
- ✅ Fácil mantenimiento y extensión
- ✅ Documentación completa
- ✅ Integración con CI/CD

Los tests están listos para ser ejecutados y garantizan la calidad y confiabilidad del módulo connector.
