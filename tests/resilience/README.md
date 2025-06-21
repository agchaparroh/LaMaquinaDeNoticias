# Tests de Resiliencia

Esta carpeta contiene los tests de resiliencia que verifican el comportamiento del sistema ante fallos y su capacidad de recuperación.

## 📁 Estructura

```
tests/resilience/
├── __init__.py
├── test_pipeline_unavailable.py    # Manejo cuando Pipeline no responde
├── test_database_timeout.py        # Comportamiento con problemas de BD
└── test_service_restart.py         # Recuperación tras caídas
```

## 🛡️ Tests Implementados

### 1. test_pipeline_unavailable.py
Valida el comportamiento del Connector cuando el Pipeline no está disponible:

**Tests incluidos:**
- `test_connector_handles_pipeline_timeout()` - Manejo de timeouts con reintentos
- `test_connector_handles_connection_refused()` - Conexión rechazada al Pipeline
- `test_connector_handles_intermittent_failures()` - Recuperación ante fallos intermitentes
- `test_connector_continues_after_failures()` - Continuidad después de fallos
- `test_graceful_degradation_strategies()` - Circuit breaker y degradación elegante

**Características probadas:**
- ⏱️ Reintentos con backoff exponencial
- 🔄 Manejo de diferentes tipos de errores (timeout, 500, 503)
- 📥 Cola de respaldo para artículos no procesados
- ⚡ Circuit breaker pattern
- 🔍 Health checks proactivos

### 2. test_database_timeout.py
Valida el comportamiento cuando Supabase tiene problemas:

**Tests incluidos:**
- `test_database_read_timeout_with_cache_fallback()` - Caché como fallback en timeouts
- `test_database_write_timeout_with_retry_queue()` - Cola de reintentos para escrituras
- `test_connection_pool_management()` - Gestión del pool de conexiones
- `test_rate_limiting_handling()` - Manejo de rate limiting
- `test_transaction_rollback_on_partial_failure()` - Rollback de transacciones
- `test_degraded_mode_operations()` - Modo degradado de operación

**Características probadas:**
- 📦 Sistema de caché multinivel
- 🔄 Cola de reintentos para escrituras
- 🔌 Gestión inteligente del pool de conexiones
- 🚦 Respeto de rate limits
- 🔐 Transacciones atómicas con rollback
- 🔧 Modo degradado cuando BD no está saludable

### 3. test_service_restart.py
Valida la recuperación después de caídas de servicios:

**Tests incluidos:**
- `test_connector_recovery_after_crash()` - Recuperación y procesamiento de pendientes
- `test_pipeline_recovery_with_deduplication()` - Evitar duplicados tras reinicio
- `test_cascading_recovery()` - Recuperación ordenada de múltiples servicios
- `test_health_check_monitoring()` - Sistema de health checks
- `test_state_synchronization_after_restart()` - Sincronización de estado
- `test_graceful_shutdown_and_startup()` - Apagado y arranque elegante

**Características probadas:**
- 📂 Procesamiento de trabajo acumulado
- 🔍 Deduplicación para evitar reprocesamiento
- 🌊 Manejo de fallos en cascada
- 🏥 Monitoreo proactivo con health checks
- 🔄 Sincronización de estado post-reinicio
- 🎯 Apagado elegante sin pérdida de datos

## 🚀 Ejecutar Tests

### Todos los tests de resiliencia:
```bash
# Desde la carpeta tests/
pytest resilience/ -v -s

# O usando el script
python run_resilience_tests.py
```

### Un test específico:
```bash
pytest resilience/test_pipeline_unavailable.py -v -s
```

### Tests individuales:
```bash
# Solo circuit breaker
pytest resilience/test_pipeline_unavailable.py::test_graceful_degradation_strategies -v -s

# Solo manejo de caché
pytest resilience/test_database_timeout.py::test_database_read_timeout_with_cache_fallback -v -s
```

## 📊 Métricas de Resiliencia

Los tests verifican:
- **Tiempo de recuperación**: Qué tan rápido se recupera el sistema
- **Pérdida de datos**: Si se pierden datos durante fallos
- **Degradación elegante**: Funcionalidad reducida vs fallo total
- **Detección de problemas**: Qué tan rápido se detectan fallos

## 🔧 Patrones de Resiliencia Implementados

### 1. **Retry con Backoff Exponencial**
```python
# Espera: 1s, 2s, 4s, 8s...
retry_delay = base_delay * (2 ** attempt)
```

### 2. **Circuit Breaker**
```python
if consecutive_failures >= threshold:
    circuit_breaker_open = True
    # Dejar de intentar temporalmente
```

### 3. **Fallback a Caché**
```python
try:
    data = await get_from_database()
except TimeoutError:
    data = get_from_cache() or default_data
```

### 4. **Health Checks**
```python
health = await check_service_health()
if health < 0.6:
    enter_degraded_mode()
```

### 5. **Graceful Shutdown**
```python
1. Stop accepting new work
2. Complete pending tasks
3. Save state
4. Close connections
```

## ⚠️ Consideraciones

1. **Simulación vs Realidad**: Los tests simulan fallos. En producción, los tiempos y comportamientos pueden variar.

2. **Timeouts**: Los tests usan timeouts reducidos para ejecutarse rápido. Ajustar para producción.

3. **Persistencia**: Los tests simulan persistencia en memoria. En producción se usaría almacenamiento real.

4. **Concurrencia**: Algunos tests simplifican la concurrencia. El sistema real puede tener más complejidad.

## 🎯 Objetivos de Resiliencia

Estos tests aseguran que el sistema cumple con:

✅ **Alta Disponibilidad**: Continúa operando ante fallos parciales
✅ **Recuperación Automática**: Se recupera sin intervención manual
✅ **Sin Pérdida de Datos**: Preserva datos durante fallos
✅ **Degradación Elegante**: Reduce funcionalidad antes que fallar completamente
✅ **Observabilidad**: Detecta y reporta problemas proactivamente

## 🔍 Debugging

Para más información durante la ejecución:
```bash
# Con logs detallados
pytest resilience/ -v -s --log-cli-level=DEBUG

# Con captura de salida
pytest resilience/ -v -s --capture=no
```
