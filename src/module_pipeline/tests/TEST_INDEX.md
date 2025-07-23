# Índice de Tests - Module Pipeline 📋

Este documento proporciona un índice completo de todos los tests organizados por categoría.

## 📁 Estructura de Tests

### Unit Tests (`unit/`)

#### Controller Tests
- `test_controller_basic.py` - Tests básicos del controlador principal
- `test_fragment_processor.py` - Tests del procesador de fragmentos

#### Model Tests
- `test_articulo_procesable_basic.py` - Tests básicos del modelo ArticuloProcesable
- `test_articulo_procesable_item.py` - Tests completos del modelo ArticuloProcesableItem

#### Service Tests
- `test_chunking_service.py` - Tests del servicio de chunking inteligente
- `test_entity_normalizer.py` - Tests del normalizador de entidades
- `test_groq_service.py` - Tests del servicio Groq API
- `test_payload_builder.py` - Tests del constructor de payloads
- `test_payload_builder_article.py` - Tests específicos para payloads de artículos
- `test_supabase_service.py` - Tests del servicio Supabase

#### Utils Tests
- `test_error_handling.py` - Tests del manejo de errores
- `test_error_handling_unit.py` - Tests unitarios adicionales de errores
- `test_json_parser.py` - Tests del parser JSON para respuestas LLM
- `test_logging_config.py` - Tests de configuración de logging

#### Pipeline Phase Tests
- `test_fase_1_triaje.py` - Tests de la fase 1 (triaje)
- `test_fase_2_simplificacion.py` - Tests de la fase 2 (simplificación)
- `test_validador_relaciones.py` - Tests del validador de relaciones

### Integration Tests (`integration/`)
- `test_7_phases_flow.py` - Test del flujo completo de las 7 fases
- `test_article_processing.py` - Tests de procesamiento de artículos (movido de test_articles/)
- `test_chunking_integration.py` - Tests de integración del chunking
- `test_consolidation.py` - Tests de consolidación cross-chunk
- `test_controller_article_direct.py` - Tests directos del controlador con artículos
- `test_controller_integration.py` - Tests de integración del controlador
- `test_integration_native_article_processing.py` - Tests de procesamiento nativo
- `test_integration_real.py` - Tests de integración con datos reales
- `test_payload_builder_integration.py` - Tests de integración del payload builder
- `test_pipeline_coordinator_union.py` - Tests del coordinador del pipeline
- `test_pipeline_minimo.py` - Tests mínimos del pipeline
- `test_relaciones_coordinator.py` - Tests del coordinador de relaciones
- `test_relaciones_payload.py` - Tests de payloads de relaciones
- `test_rpc_datos_alignment.py` - Tests de alineación de datos RPC (movido desde raíz)
- `test_rpc_fragmento.py` - Tests de RPC de fragmentos (movido desde raíz)
- `test_services_compatibility.py` - Tests de compatibilidad entre servicios
- `test_supabase_connection.py` - Tests de conexión Supabase (movido desde raíz)

### API Tests (`api/`)
- `test_criterio_1_http.py` - Tests del criterio 1 HTTP
- `test_procesar_articulo.py` - Tests del endpoint procesar_articulo

### Performance Tests (`performance/`)
- `test_async_processing.py` - Tests de procesamiento asíncrono
- `test_concurrency.py` - Tests de concurrencia
- `test_multiple_articles.py` - Tests con múltiples artículos
- `test_performance_load.py` - Tests de carga
- `benchmark_performance.py` - Benchmarks de rendimiento (movido desde raíz)

### Functional Tests (`functional/`)
- `test_connections.py` - Tests de conexiones (movido de scripts/)
- `test_fix_validation.py` - Tests de validación de fixes (movido desde raíz)
- `test_job_tracking.py` - Tests del sistema de tracking de jobs
- `test_monitoring_system.py` - Tests del sistema de monitoreo
- `test_persistence_layer_detection.py` - Tests de detección de capa de persistencia
- `test_recovery.py` - Tests de recuperación de errores
- `test_verificar_id_fragmento.py` - Verificación de IDs de fragmento (movido desde raíz)

### Regression Tests (`regression/`)
- `test_debug_e012.py` - Tests para debug del error E012
- `test_e012_fix.py` - Tests del fix para E012
- `test_e012_political.py` - Tests de E012 en contexto político
- `test_error_handling_integral.py` - Tests integrales de manejo de errores
- `test_pipeline_e004.py` - Tests del error E004 del pipeline

### Test Fixtures (`fixtures/`)
- `articles/` - Artículos de prueba en JSON y raw (movidos de test_articles/)
  - Contiene ~100 archivos JSON de artículos reales para testing
  - Archivos raw comprimidos en formato .json.gz

## 🚀 Ejecutar Tests

### Por categoría
```bash
# Tests unitarios
pytest unit/ -v

# Tests de integración
pytest integration/ -v

# Tests de rendimiento
pytest performance/ -v

# Tests funcionales
pytest functional/ -v

# Tests de regresión
pytest regression/ -v
```

### Tests específicos
```bash
# Test del flujo completo
pytest integration/test_7_phases_flow.py -v

# Test de conexiones
python functional/test_connections.py

# Benchmark de rendimiento
python performance/benchmark_performance.py
```

## 📝 Notas sobre Tests Movidos

Los siguientes archivos fueron movidos desde otras ubicaciones:
- `scripts/test_connections.py` → `functional/test_connections.py`
- `test_supabase_connection.py` → `integration/test_supabase_connection.py`
- `test_rpc_*.py` → `integration/test_rpc_*.py`
- `test_fix_validation.py` → `functional/test_fix_validation.py`
- `verificar_id_fragmento.py` → `functional/test_verificar_id_fragmento.py`
- `benchmark_performance.py` → `performance/benchmark_performance.py`
- `test_articles/` → `fixtures/articles/` y `integration/test_article_processing.py`

Todos los imports han sido actualizados para reflejar las nuevas ubicaciones.