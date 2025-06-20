# Module Pipeline - La Máquina de Noticias

Núcleo de procesamiento inteligente para extracción de información estructurada de artículos de noticias usando LLMs.

## 🏗️ Arquitectura

```
Pipeline de 4 Fases:
ArticuloInItem/FragmentoProcesableItem
    ↓
1️⃣ Triaje y Preprocesamiento
    ↓
2️⃣ Extracción de Elementos Básicos
    ↓
3️⃣ Extracción de Citas y Datos Cuantitativos
    ↓
4️⃣ Normalización, Vinculación y Relaciones
    ↓
Persistencia en Supabase
```

**Stack tecnológico:**
- **API**: FastAPI + Uvicorn (puerto 8003)
- **LLM**: Groq API 
- **NLP**: spaCy + sentence-transformers
- **BD**: Supabase/PostgreSQL con RPCs
- **Validación**: Pydantic v2
- **Contenedores**: Docker + Docker Compose
- **Monitoreo**: Prometheus (métricas disponibles)

## 📁 Estructura del Proyecto

```
module_pipeline/
├── src/                    # Código fuente
│   ├── main.py              # FastAPI application
│   ├── controller.py        # Pipeline controller
│   ├── config.py           # Configuration wrapper
│   ├── models/             # Pydantic models
│   ├── pipeline/           # Pipeline phases (4 fases)
│   ├── services/           # External integrations
│   ├── utils/              # Utilities and helpers
│   └── monitoring/         # Monitoring and metrics
├── tests/                  # Organized test suite
├── prompts/                # LLM prompts
├── monitoring/             # Configuraciones de monitoreo
│   └── prometheus.yml      # Configuración Prometheus
├── .github/workflows/      # CI/CD pipelines
├── Dockerfile             # Imagen Docker optimizada
├── docker-compose.yml     # Orquestación completa
├── Makefile              # Comandos de desarrollo
└── README.md             # Este archivo
```

## 🚀 Inicio Rápido

### Opción 1: Usando Makefile (Recomendado)
```bash
# Configuración inicial completa
make setup

# Editar .env con tus API keys
# GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY

# Ejecutar en desarrollo
make dev

# Ver ayuda completa
make help
```

### Opción 2: Usando Docker
```bash
# Copiar variables de entorno
cp .env.example .env
# Editar .env con tus claves

# Ejecutar con Docker Compose
make deploy
# O directamente: docker-compose up -d

# Verificar salud
make health
```

### Opción 3: Manual
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download es_core_news_lg
python -m spacy download en_core_web_sm
cp .env.example .env
# Editar .env
python src/main.py
```

## 🔧 Configuración

### Variables de Entorno Requeridas
```bash
# API Keys (OBLIGATORIAS)
GROQ_API_KEY=gsk_your_key_here
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=your_anon_key

# Configuración Opcional
API_HOST=0.0.0.0
API_PORT=8003
LOG_LEVEL=INFO
DEBUG_MODE=false
```

### Configuración Avanzada
Ver `.env.example` para lista completa de variables disponibles:
- Configuración de Workers y Queue
- Límites de contenido y timeouts
- Configuración de spaCy y embeddings
- Métricas y monitoreo
- Integración con servicios externos

## 🐳 Docker y Contenedores

### Docker Compose (Recomendado)
```bash
# Desarrollo completo con monitoreo
make deploy

# Solo pipeline (sin monitoreo)
make deploy-prod

# Ver logs
make logs

# Detener servicios
make down
```

### Servicios Incluidos
- **module-pipeline**: API principal (puerto 8003)
- **prometheus**: Métricas (puerto 9090) - opcional con `make deploy`

## 🧪 Testing

### Comandos Disponibles
```bash
# Tests básicos
make test

# Tests con cobertura
make test-cov

# Test específico
make test-specific TEST=tests/test_api/

# Linting y formato
make lint
make format
```

### Configuración de Tests
- **pytest.ini**: Configuración asyncio y paths
- **conftest.py**: Fixtures y mocks
- **Cobertura**: Mínimo 70% requerido en CI
- **Mocks**: Groq API, Supabase, datos de prueba

## 📡 API Endpoints

### Endpoints Principales
- `GET /health` - Health check básico
- `GET /health/detailed` - Health check con dependencias
- `POST /procesar_articulo` - Procesar artículo completo
- `POST /procesar_fragmento` - Procesar fragmento de documento
- `GET /status/{job_id}` - Estado de procesamiento asíncrono

### Endpoints de Observabilidad
- `GET /metrics` - Métricas Prometheus
- `GET /monitoring/dashboard` - Dashboard JSON
- `GET /monitoring/pipeline-status` - Estado de las 4 fases

### Documentación Interactiva
- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc

## 📊 Monitoreo y Observabilidad

### Métricas Disponibles (Formato Prometheus)
```
# Contadores (counters)
pipeline_articles_processed_total
pipeline_fragments_processed_total  
pipeline_processing_time_seconds_total
pipeline_errors_total

# Medidores (gauges)
pipeline_error_rate
pipeline_average_processing_time_seconds
jobs_total
jobs_{status}_total  # pending, processing, completed, failed
system_uptime_seconds
```

### Dashboards
```bash
# Prometheus
http://localhost:9090

# Métricas JSON
curl http://localhost:8003/monitoring/dashboard | jq
```

### Health Checks
- Health checks automáticos cada 30s
- Métricas exportadas en formato Prometheus
- Verificación de dependencias (Groq API, Supabase)

## 🔀 Pipeline de Procesamiento

### Fase 1: Triaje y Preprocesamiento
- **Función**: Limpieza, detección de idioma, evaluación de relevancia
- **Tecnología**: spaCy, validaciones custom

### Fase 2: Extracción de Elementos Básicos
- **Función**: Hechos principales y entidades
- **Tecnología**: Groq LLM

### Fase 3: Extracción de Citas y Datos
- **Función**: Citas textuales y datos cuantitativos
- **Tecnología**: Groq LLM con prompts especializados

### Fase 4: Normalización y Relaciones
- **Función**: Vinculación de entidades, detección de relaciones
- **Tecnología**: Supabase RPCs + Groq para análisis

## 🛠️ Comandos de Desarrollo

### Makefile Completo
```bash
# Configuración
make setup          # Configuración inicial
make install-deps   # Reinstalar dependencias

# Desarrollo
make dev            # Servidor desarrollo
make dev-docker     # Desarrollo con Docker

# Testing
make test           # Tests básicos
make test-cov       # Tests con cobertura
make lint           # Verificar código
make format         # Formatear código

# Docker
make build          # Construir imagen
make deploy         # Desplegar completo
make deploy-prod    # Solo pipeline

# Operaciones
make logs           # Ver logs
make health         # Verificar salud
make metrics        # Ver métricas
make status         # Estado del pipeline
```

## 🔄 CI/CD Pipeline

### GitHub Actions
- **Triggers**: Push a main/develop, PRs a main
- **Jobs**: Testing, Security, Docker, Deploy, Notify
- **Matrix Testing**: Python 3.9, 3.10, 3.11
- **Security**: Safety check, dependency review
- **Deploy**: Automático en main branch

### Workflow Incluye
- ✅ Tests unitarios con cobertura >70%
- ✅ Linting con Black, flake8, mypy
- ✅ Security scanning con Safety
- ✅ Docker build y test
- ✅ Deploy automático a producción
- ✅ Notificaciones de estado

## 🗄️ Modelos de Datos

### Entrada
- `FragmentoProcesableItem`: Fragmentos de documentos (min 50 chars)
- `ArticuloInItem`: Artículos completos desde module_connector

### Procesamiento
- `HechoBase/HechoProcesado`: Hechos extraídos con metadatos
- `EntidadBase/EntidadProcesada`: Entidades identificadas y normalizadas
- `CitaTextual`: Citas directas con speaker y contexto
- `DatosCuantitativos`: Datos numéricos estructurados
- `ResultadoFaseX`: Resultados por cada fase del pipeline

### Persistencia
- Payloads JSONB optimizados para Supabase RPCs
- `insertar_articulo_completo()`: Persistencia de artículos
- `insertar_fragmento_completo()`: Persistencia de fragmentos

## 🔗 Integraciones

### Groq API
- **Cliente**: Resiliente con retry logic y circuit breaker
- **Configuración**: Timeouts configurables, rate limiting
- **Prompts**: Externalizados en `/prompts/` para fácil mantenimiento

### Supabase
- **Cliente**: Singleton con pool de conexiones
- **RPCs**: Llamadas especializadas para cada fase
- **Normalización**: `buscar_entidad_similar` para deduplicación
- **Persistencia**: Transacciones ACID para consistencia

### spaCy
- **Modelos**: `es_core_news_lg`, `en_core_web_sm`
- **Funciones**: NER, POS tagging, sentence segmentation
- **Optimización**: Carga lazy de modelos para performance

## 🔍 Troubleshooting

### Problemas Comunes

**Error: spaCy model not found**
```bash
python -m spacy download es_core_news_lg
python -m spacy download en_core_web_sm
```

**Error: Groq API key invalid**
- Verificar `.env` tiene `GROQ_API_KEY` válida
- Obtener nueva clave en https://console.groq.com/

**Error: Supabase connection failed**
- Verificar `SUPABASE_URL` y `SUPABASE_KEY` en `.env`
- Comprobar que el proyecto Supabase esté activo

**Container no inicia**
```bash
# Ver logs detallados
docker-compose logs module-pipeline

# Verificar variables de entorno
docker-compose config
```

### Logs y Debug
```bash
# Logs en tiempo real
make logs

# Logs específicos
docker-compose logs -f module-pipeline

# Debug mode
export DEBUG_MODE=true
make dev
```

### Performance
- **Threshold asíncrono**: 10,000 caracteres
- **Timeouts**: Groq 60s, Supabase 30s
- **Retry**: 2 intentos automáticos
- **Pool connections**: 10 conexiones Supabase

## 📚 Documentación Adicional

- **Arquitectura técnica**: `src/docs/CONCURRENCY_ANALYSIS.md`
- **Tests**: `tests/README.md`
- **API Reference**: http://localhost:8003/docs
- **Métricas**: http://localhost:8003/metrics

---

## 🚀 Próximos Pasos

1. **Configurar** variables de entorno en `.env`
2. **Ejecutar** `make setup` para configuración inicial
3. **Probar** con `make dev` y verificar http://localhost:8003/health
4. **Monitorear** métricas en http://localhost:8003/metrics
5. **Integrar** con module_connector para procesamiento completo

---

**La Máquina de Noticias** - Transformando información no estructurada en conocimiento conectado.

*Versión: 1.0.0 | Puerto: 8003 | Docker: ✅ | CI/CD: ✅ | Monitoreo: ✅*
