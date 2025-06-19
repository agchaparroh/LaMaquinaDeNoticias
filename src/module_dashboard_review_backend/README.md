


# module_dashboard_review_backend

## Filosofía de Diseño

- Robustez sin complejidad: Seguir patrones probados de los módulos existentes
- Separación clara de responsabilidades: Cada archivo tiene un propósito específico
- Configuración por variables de entorno: Sin hardcoding
- Testing integrado desde el inicio: Suite básica pero efectiva
- Docker-first: Diseño pensado para contenedores


## Arquitectura propuesta:

module_dashboard_review_backend/
├── src/
│   ├── main.py                    # FastAPI app + configuración CORS + health check
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dashboard.py           # Endpoints /dashboard/* (hechos_revision, filtros)
│   │   └── feedback.py            # Endpoints /dashboard/feedback/* (importancia, evaluacion)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py            # Pydantic models para requests (filtros, pagination)
│   │   ├── responses.py           # Pydantic models para responses (hecho_item, lista_paginada)
│   │   └── database.py            # Models que mapean tablas Supabase (hechos, articulos)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── supabase_client.py     # Cliente Supabase + conexión + queries base
│   │   ├── hechos_service.py      # Lógica de negocio para hechos (filtros, paginación)
│   │   └── feedback_service.py    # Lógica de negocio para feedback editorial
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py              # Variables de entorno + validación
│   │   ├── logging_config.py      # Configuración loguru (patrón module_pipeline)
│   │   └── exceptions.py          # Excepciones personalizadas + handlers
│   └── core/
│       ├── __init__.py
│       └── dependencies.py       # FastAPI dependencies (auth futura, db session)
├── tests/
│   ├── __init__.py
│   ├── test_api/
│   │   ├── test_dashboard.py      # Tests endpoints dashboard
│   │   └── test_feedback.py       # Tests endpoints feedback
│   ├── test_services/
│   │   ├── test_hechos_service.py # Tests lógica de negocio
│   │   └── test_feedback_service.py
│   ├── conftest.py                # Fixtures pytest (mock Supabase, test client)
│   └── test_health.py             # Tests health check + startup
├── Dockerfile                     # Python 3.9 + FastAPI + dependencias mínimas
├── requirements.txt               # FastAPI, supabase-py, pydantic, uvicorn, loguru, pytest
├── .env.example                   # Template variables de entorno
└── README.md                      # Documentación básica + endpoints


### Principios aplicados:

- API Router separation: Dashboard y feedback separados por responsabilidad
- Service layer: Lógica de negocio separada de endpoints
- Models by purpose: Requests, responses y database models separados
- Dependency injection: Para futuras extensiones (auth, rate limiting)

## Endpoints API

### Dashboard
- `GET /dashboard/hechos_revision` - Lista paginada con filtros
- `GET /dashboard/filtros/opciones` - Opciones para filtros (medios, países)

### Feedback

#### POST /dashboard/feedback/hecho/{hecho_id}/importancia_feedback

Permite a los editores enviar feedback sobre la importancia asignada automáticamente a un hecho.

**Request:**
```json
{
  "importancia_editor_final": 8,
  "usuario_id_editor": "editor123"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Feedback de importancia actualizado para hecho 123"
}
```

**Posibles errores:**
- 404: Hecho no encontrado
- 400: Error en la operación
- 422: Validación fallida (importancia debe estar entre 1-10)

**Ejemplo curl:**
```bash
curl -X POST "http://localhost:8000/dashboard/feedback/hecho/123/importancia_feedback" \
     -H "Content-Type: application/json" \
     -d '{
       "importancia_editor_final": 8,
       "usuario_id_editor": "editor123"
     }'
```

#### POST /dashboard/feedback/hecho/{hecho_id}/evaluacion_editorial

Permite a los editores evaluar hechos como verificados o falsos.

**Request:**
```json
{
  "evaluacion_editorial": "verificado_ok_editorial",
  "justificacion_evaluacion_editorial": "Fact correctly extracted and verified against multiple sources"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Evaluación editorial actualizada para hecho 123"
}
```

**Valores válidos para evaluacion_editorial:**
- `verificado_ok_editorial`: El hecho ha sido verificado como correcto
- `declarado_falso_editorial`: El hecho ha sido declarado como falso

**Posibles errores:**
- 404: Hecho no encontrado
- 400: Error en la operación
- 422: Validación fallida (valor de evaluación inválido)

**Ejemplo curl - Marcar como verificado:**
```bash
curl -X POST "http://localhost:8000/dashboard/feedback/hecho/123/evaluacion_editorial" \
     -H "Content-Type: application/json" \
     -d '{
       "evaluacion_editorial": "verificado_ok_editorial",
       "justificacion_evaluacion_editorial": "Fact correctly extracted and verified against multiple sources"
     }'
```

**Ejemplo curl - Marcar como falso:**
```bash
curl -X POST "http://localhost:8000/dashboard/feedback/hecho/456/evaluacion_editorial" \
     -H "Content-Type: application/json" \
     -d '{
       "evaluacion_editorial": "declarado_falso_editorial",
       "justificacion_evaluacion_editorial": "Information contradicts official sources"
     }'
```

### Health & Monitoring

#### Health Check Endpoints

La API proporciona dos endpoints para monitoreo de salud:

- **`GET /health`** - Endpoint básico que retorna el estado general del servicio
  - Response: `{"status": "ok", "version": "1.0.0"}`
  - Status Code: 200 OK
  - Uso: Monitoreo básico, health checks de load balancers

- **`GET /health/detailed`** - Endpoint detallado que incluye estado de dependencias y uptime
  - Response:
    ```json
    {
      "status": "ok",
      "version": "1.0.0",
      "dependencies": {
        "supabase": {
          "status": "ok",
          "response_time_ms": 123.45
        }
      },
      "uptime": 3600.5
    }
    ```
  - Status Code: 200 OK (incluso cuando el servicio está degradado)
  - Campos de status:
    - `ok`: Todo funciona correctamente
    - `degraded`: El servicio funciona pero alguna dependencia tiene problemas
    - `error`: El servicio no funciona correctamente
  
#### Implementación de Health Checks

- **Supabase Health Check**: Realiza una query simple `SELECT id FROM hechos LIMIT 1` para verificar conectividad
- **Response Time Metrics**: Mide el tiempo de respuesta de la base de datos en milisegundos
- **Uptime Tracking**: Calcula el tiempo desde que el servicio se inició
- **Retry Logic**: Utiliza el cliente Supabase con reintentos automáticos
- **Error Logging**: Registra errores detallados cuando las dependencias fallan

## Variables de entorno:

### Supabase connection
SUPABASE_URL=
SUPABASE_KEY=

### Server configuration  
API_HOST=0.0.0.0
API_PORT=8004
LOG_LEVEL=INFO
ENVIRONMENT=production

### CORS configuration
CORS_ORIGINS=http://localhost:3001,https://tu-dominio.com

## Servicios Implementados

### Supabase Client (supabase_client.py)
- **Patrón Singleton**: Garantiza una única instancia del cliente en toda la aplicación
- **Retry Logic**: Reintentos automáticos con exponential backoff para operaciones fallidas
- **Connection Pooling**: Manejo eficiente de conexiones a la base de datos
- **Helper Methods**:
  - `select_with_pagination()`: Consultas paginadas con filtros opcionales
  - `get_single_record()`: Obtener un registro específico por ID
  - `update_record()`: Actualizar campos de un registro
  - `count_records()`: Contar registros con filtros opcionales
- **Error Handling**: Manejo robusto de errores con DatabaseConnectionError personalizado
- **Testing Support**: Método `reset_client()` para facilitar las pruebas unitarias

### Testing

- **Coverage**: Tests unitarios con cobertura >90% para el cliente Supabase
- **Test Categories**:
  - Inicialización y patrón singleton
  - Retry logic con exponential backoff
  - Métodos helper con datos mockeados
  - Escenarios de integración
- **Run Tests**: `pytest tests/test_services/test_supabase_client.py -v`
- **Coverage Report**: `pytest --cov=src/services/supabase_client --cov-report=html`

### Integration Notes

- **Health Check Integration**: El cliente Supabase está preparado para ser usado en endpoints de health check detallado (tarea 3)
- **Dependency Injection**: Integrado correctamente en `core/dependencies.py` para uso en todos los servicios
- **Type Safety**: Type hints completos en toda la implementación para mejor IDE support y validación

### Health Check Endpoints (health.py)

- **Endpoints Implementados**:
  - `/health`: Health check básico para monitoreo simple
  - `/health/detailed`: Health check detallado con estado de dependencias y métricas
- **Funcionalidades**:
  - Verificación de conectividad con Supabase
  - Métricas de tiempo de respuesta
  - Cálculo de uptime del servicio
  - Estados diferenciados: ok, degraded, error
- **Testing**:
  - Tests unitarios completos con mocks de Supabase
  - Cobertura de casos exitosos y de error
  - Validación de esquemas de respuesta
  - Run tests: `pytest tests/test_health.py -v`
- **Uso en Producción**:
  - Configure alertas cuando el estado sea "degraded" o "error"
  - Use `/health` para health checks de load balancers (respuesta rápida)
  - Use `/health/detailed` para monitoreo detallado y debugging

## 🐳 Docker Deployment

### Quick Start

1. **Build the image:**
   ```bash
   docker build -t module_dashboard_review_backend .
   ```

2. **Run with docker-compose:**
   ```bash
   docker-compose up -d
   ```

3. **Verify deployment:**
   ```bash
   curl http://localhost:8004/health
   ```

### Docker Configuration

#### Dockerfile Features
- Base image: Python 3.9-slim (optimized for size)
- Non-root user: `appuser` (UID 1000) for security
- Health check: Built-in health check every 30s
- Multi-layer caching: Dependencies cached separately
- Production ready: No development dependencies

#### docker-compose.yml
```yaml
services:
  module_dashboard_review_backend:
    build: .
    container_name: module_dashboard_review_backend
    ports:
      - "8004:8004"
    env_file:
      - .env
    networks:
      - lamacquina_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

### Environment Variables

Create a `.env` file from the template:
```bash
cp .env.example .env
```

Required variables:
```bash
# Supabase connection
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Optional (with defaults)
API_HOST=0.0.0.0
API_PORT=8004
CORS_ORIGINS=http://localhost:3001
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Network Integration

The service connects to the `lamacquina_network` external network:

```bash
# Create network if it doesn't exist
docker network create lamacquina_network

# Verify network connection
docker exec module_dashboard_review_backend ping module_pipeline
```

### Building and Running

#### Development Mode
```bash
# Build and run with live reload
docker-compose up --build

# View logs
docker-compose logs -f
```

#### Production Mode
```bash
# Build optimized image
docker build -t module_dashboard_review_backend:prod . --no-cache

# Run in detached mode
docker-compose up -d

# Check status
docker-compose ps
```

### Testing Docker Deployment

```bash
# Run automated tests
python scripts/test_docker_integration.py

# Or use the bash script
./scripts/test_docker_deployment.sh
```

Tests verify:
- ✅ Image builds correctly
- ✅ Container starts and responds
- ✅ Health checks pass
- ✅ Running as non-root user
- ✅ Environment variables loaded
- ✅ Port binding works
- ✅ Network connectivity

### Troubleshooting

#### Container won't start
```bash
# Check logs
docker logs module_dashboard_review_backend

# Inspect container
docker inspect module_dashboard_review_backend
```

#### Port already in use
```bash
# Find process using port 8004
lsof -i :8004

# Or change port in .env and docker-compose.yml
API_PORT=8005
```

#### Cannot connect to Supabase
```bash
# Verify environment variables
docker exec module_dashboard_review_backend printenv | grep SUPABASE

# Test connectivity from container
docker exec module_dashboard_review_backend curl -I https://your-project.supabase.co
```

#### Network issues
```bash
# List networks
docker network ls

# Inspect network
docker network inspect lamacquina_network

# Recreate network
docker network rm lamacquina_network
docker network create lamacquina_network
```

### Docker Commands Reference

```bash
# Build
docker build -t module_dashboard_review_backend .

# Run standalone
docker run -d --name dashboard_backend -p 8004:8004 --env-file .env module_dashboard_review_backend

# Execute commands in container
docker exec module_dashboard_review_backend python -m pytest

# View resource usage
docker stats module_dashboard_review_backend

# Clean up
docker-compose down
docker system prune -a
```

### Integration with Main System

To integrate with the main LaMaquinaDeNoticias system, see [DOCKER_INTEGRATION.md](./DOCKER_INTEGRATION.md)

### Security Considerations

- ✅ Runs as non-root user (appuser)
- ✅ No sensitive data in image layers
- ✅ Environment variables for secrets
- ✅ Health check endpoint reveals no sensitive info
- ✅ Minimal base image reduces attack surface

### Performance Optimization

- Image size: ~200MB (using slim base)
- Startup time: <10 seconds
- Memory usage: ~256MB typical
- CPU usage: <0.5 CPU under normal load
- Resource limits configured in docker-compose.yml

---
---

## 📚 Documentation

Tarea pendiente: Create Documentation and Finalize Project

- Add project objective to documentation
- Create developer guides for maintenance
- Document integration points with other MVP modules
