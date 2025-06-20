# Plan de Testing - nginx_reverse_proxy

## Resumen Ejecutivo

Este documento describe el plan de testing completo para el módulo nginx_reverse_proxy, que actúa como proxy reverso para el sistema La Máquina de Noticias.

## Objetivos de Testing

1. **Validar configuración**: Asegurar que nginx está correctamente configurado
2. **Verificar routing**: Confirmar que las peticiones se redirigen correctamente
3. **Probar seguridad**: Validar headers de seguridad y rate limiting
4. **Confirmar performance**: Verificar optimizaciones como gzip y caching
5. **Probar integración**: Asegurar funcionamiento con Docker y red del sistema
6. **Validar errores**: Confirmar manejo correcto de casos edge
7. **Tests avanzados**: Performance, concurrencia, recuperación y carga

## Estrategia de Testing

### 1. Tests Unitarios (Sin Docker)
Estos tests validan la configuración estática sin necesidad de ejecutar containers.

#### test_configuration.py
- ✅ Validación de sintaxis nginx.conf
- ✅ Existencia de archivos requeridos (.env, Dockerfile, etc.)
- ✅ Variables de entorno definidas
- ✅ Upstreams configurados
- ✅ Rate limiting configurado
- ✅ Headers de seguridad presentes
- ✅ Compresión gzip habilitada

### 2. Tests de Integración (Con Docker)

#### test_routing.py
- ✅ Health check endpoint (/nginx-health)
- ✅ Routing API con eliminación de prefix /api
- ✅ Routing frontend
- ✅ Headers CORS en rutas API
- ✅ Manejo de preflight OPTIONS
- ✅ Forwarding de headers
- ✅ Soporte para diferentes métodos HTTP
- ✅ Límites de tamaño de body

#### test_security.py
- ✅ Headers de seguridad presentes
- ✅ Rate limiting funcional (API: 100rpm, General: 300rpm)
- ✅ Recuperación después de burst
- ✅ CORS solo en rutas API
- ✅ Restricción de métodos HTTP
- ✅ No exposición de información sensible
- ✅ Manejo de conexiones concurrentes

#### test_docker.py
- ✅ Build de imagen Docker
- ✅ Health checks del container
- ✅ Generación de logs
- ✅ Conectividad de red
- ✅ Recuperación después de restart
- ✅ Ejecución con usuario no-root
- ✅ Montaje correcto de volúmenes

#### test_performance.py
- ✅ Compresión gzip activa
- ✅ Headers Vary con gzip
- ✅ Conexiones keepalive
- ✅ Headers de cache para estáticos
- ✅ Tiempos de respuesta adecuados
- ✅ Configuración de buffering
- ✅ Optimizaciones TCP

#### test_error_handling.py
- ✅ Manejo cuando backend está caído
- ✅ Manejo cuando frontend está caído
- ✅ Páginas de error personalizadas
- ✅ Manejo de timeouts
- ✅ Respuesta a métodos inválidos
- ✅ Manejo de requests malformados
- ✅ Failover de upstreams

### 3. Tests Avanzados (Nuevos)

#### test_advanced_performance.py
- ✅ Medición de percentiles de latencia (p50, p95, p99)
- ✅ Eficiencia de connection pooling
- ✅ Comparación rendimiento estático vs dinámico
- ✅ Ratio de compresión gzip real
- ✅ Efectividad del cache
- ✅ Medición de requests por segundo (RPS)
- ✅ Utilización de ancho de banda
- ✅ Tiempo de respuesta bajo carga moderada

#### test_concurrency.py
- ✅ Manejo de 100+ requests simultáneos
- ✅ Comportamiento al límite de conexiones
- ✅ Fairness del rate limiting entre clientes
- ✅ Aislamiento entre requests concurrentes
- ✅ Requests a diferentes rutas simultáneamente
- ✅ Uso de memoria bajo concurrencia
- ✅ Límites de file descriptors

#### test_recovery.py
- ✅ Recuperación cuando backend vuelve
- ✅ Recuperación cuando frontend vuelve
- ✅ Manejo de fallos parciales de upstreams
- ✅ Recuperación tras reload de nginx
- ✅ Reconexión automática a servicios
- ✅ Recuperación del pool de conexiones
- ✅ Persistencia del estado de rate limiting
- ✅ Recuperación de health checks

#### test_load.py
- ✅ Carga incremental (ramp up)
- ✅ Carga sostenida por períodos largos
- ✅ Manejo de picos de tráfico (spikes)
- ✅ Patrones de carga mixtos
- ✅ Degradación graceful bajo sobrecarga
- ✅ Recuperación post-sobrecarga

#### test_real_integration.py
- ✅ Integración con backend real
- ✅ Serving de frontend real
- ✅ Flujo completo de requests
- ✅ Integración con red Docker
- ✅ Service discovery
- ✅ Comunicación entre containers
- ✅ Flujo de datos reales

## Herramientas de Testing

### Frameworks y Librerías
- **pytest**: Framework principal de testing
- **pytest-cov**: Cobertura de código
- **pytest-xdist**: Ejecución paralela
- **pytest-benchmark**: Benchmarking
- **requests**: Cliente HTTP
- **docker**: API de Docker para Python
- **locust**: Framework de load testing
- **aiohttp**: Requests asíncronos

### Configuración de Locust
Se incluye `locustfile.py` con tres tipos de usuarios simulados:
- **DashboardUser**: Usuario típico del dashboard
- **APIUser**: Cliente API intensivo
- **MobileUser**: Usuario móvil con patrones específicos

## Ejecución de Tests

### Script de Ejecución Completa
```bash
# Ejecutar todos los tests
python run_all_tests.py

# Solo tests de performance
python run_all_tests.py --type performance

# Con cobertura y reporte HTML
python run_all_tests.py --coverage --report

# Tests de carga con Locust
python run_all_tests.py --load-test
```

### Comandos Individuales
```bash
# Tests unitarios rápidos
pytest tests/unit/ -v

# Tests de integración específicos
pytest tests/integration/test_concurrency.py -v

# Con cobertura
pytest tests/ --cov=. --cov-report=html

# En paralelo
pytest tests/ -n auto -v
```

### Tests de Carga con Locust
```bash
# Iniciar Locust UI
locust -f locustfile.py --host=http://localhost

# Modo headless
locust -f locustfile.py --host=http://localhost --headless -u 100 -r 10 -t 5m
```

## Métricas de Éxito

### Performance
- Latencia p99 < 100ms para health checks
- Latencia p99 < 500ms para API calls
- Throughput > 1000 RPS para contenido estático
- Throughput > 500 RPS para API
- Compresión gzip > 30% de reducción

### Concurrencia
- Soportar 500+ conexiones simultáneas
- 0% pérdida de requests bajo carga normal
- Aislamiento 100% entre requests
- Memoria estable bajo alta concurrencia

### Recuperación
- Tiempo de recuperación < 30s tras fallo de upstream
- 0% pérdida de estado tras reload
- Reconexión automática en < 10s
- Recovery completo post-sobrecarga < 60s

### Carga
- Soportar 1000+ usuarios concurrentes
- Degradación graceful más allá del límite
- Error rate < 2% bajo carga sostenida
- RPS estable durante 1+ minutos

## Casos Edge Cubiertos

1. **Servicios caídos**: Backend/Frontend no disponibles
2. **Rate limiting**: Exceso de peticiones
3. **Carga alta**: Múltiples conexiones concurrentes
4. **Timeouts**: Peticiones lentas
5. **Requests malformados**: Headers inválidos
6. **Métodos no soportados**: TRACE, CONNECT, etc.
7. **Bodies grandes**: Más allá del límite configurado
8. **Fallos intermitentes**: Servicios que van y vienen
9. **Memory leaks**: Verificación de liberación de recursos
10. **File descriptor exhaustion**: Límites del sistema

## Mantenimiento de Tests

### Agregar Nuevos Tests
1. Identificar categoría apropiada
2. Seguir convenciones de nombres existentes
3. Usar fixtures disponibles
4. Documentar propósito y validaciones
5. Considerar impacto en tiempo de ejecución

### Actualizar Tests Existentes
1. Mantener compatibilidad hacia atrás
2. Actualizar documentación si cambia comportamiento
3. Verificar que fixtures siguen siendo válidos
4. Revisar umbrales de performance

## Integración CI/CD

### Pipeline Recomendado
```yaml
stages:
  - unit_tests        # < 30s
  - integration_tests # < 3min
  - performance_tests # < 5min
  - load_tests       # < 10min (opcional)
  - report_generation
```

### Requisitos CI
- Docker y Docker Compose
- Python 3.8+
- 4GB RAM mínimo
- Red `lamacquina_network`
- Puertos 80, 8004, 8080 disponibles

## Reportes y Análisis

### Tipos de Reportes
1. **Cobertura HTML**: Análisis detallado de cobertura
2. **Reporte de Tests**: Resumen de ejecución con timestamps
3. **Métricas de Performance**: Latencias, throughput, percentiles
4. **Análisis de Carga**: Gráficos de Locust con RPS, tiempos, errores

### Interpretación de Resultados
- **Latencia p99**: Importante para SLAs
- **Error rate**: Debe ser < 1% en condiciones normales
- **Memory usage**: No debe crecer indefinidamente
- **Recovery time**: Crítico para alta disponibilidad

## Troubleshooting Tests

### Problemas Comunes

#### Tests de integración fallan
```bash
# Verificar Docker
docker ps
docker network ls

# Recrear red si es necesario
docker network create lamacquina_network

# Verificar puertos libres
netstat -tulpn | grep -E ':(80|8004|8080)'
```

#### Tests muy lentos
- Usar `pytest -n auto` para paralelización
- Ejecutar categorías específicas
- Verificar recursos de Docker
- Considerar reducir iteraciones en tests de carga

#### Falsos positivos en concurrencia
- Aumentar timeouts en ambientes lentos
- Verificar que no hay otros procesos consumiendo recursos
- Revisar límites del sistema (`ulimit -n`)

## Conclusión

El plan de testing ampliado proporciona cobertura exhaustiva del módulo nginx_reverse_proxy, incluyendo:
- ✅ Validación funcional completa
- ✅ Tests de performance avanzados
- ✅ Pruebas de concurrencia exhaustivas
- ✅ Escenarios de recuperación
- ✅ Tests de carga realistas
- ✅ Integración con servicios reales

Los tests aseguran que nginx puede manejar las demandas de producción con confianza y proporcionar un servicio confiable como componente crítico del sistema.
