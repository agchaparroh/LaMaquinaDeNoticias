# La Máquina de Noticias - Claude Code Project Context

## 🌐 Idioma de Trabajo / Working Language

**IMPORTANTE**: Este proyecto se desarrolla principalmente en **ESPAÑOL**. Claude Code debe:
- Responder en español por defecto
- Usar terminología técnica en español cuando sea posible
- Mantener los comentarios de código en español
- Documentar en español (excepto cuando se requiera específicamente en inglés)

**IMPORTANT**: This project is primarily developed in **SPANISH**. Claude Code should:
- Respond in Spanish by default
- Use Spanish technical terminology when possible
- Keep code comments in Spanish
- Document in Spanish (except when specifically required in English)

## 🎯 Project Overview

**La Máquina de Noticias** is a modular system for automated news collection, processing, and analysis. It's designed for journalists to extract structured knowledge from large volumes of text using artificial intelligence.

**Current Status**: MVP FUNCTIONAL ✅
- 6 fully implemented modules covering the complete flow from collection to presentation
- Production-ready with Docker containerization
- Integrated with Supabase for data persistence

## 🏗️ Architecture

The project follows a **microservices architecture** with Docker containers communicating via REST APIs:

```
🕷️ module_scraper → 🔗 module_connector → ⚙️ module_pipeline → 🔧 module_dashboard_backend → 📱 module_dashboard_frontend
                                                    ↓
                                            🗄️ Supabase (PostgreSQL + Storage)
                                                    ↓
                                            🤖 AI/LLMs (Groq/Anthropic)
```

### Key Modules

| Module | Technology | Port | Purpose |
|--------|------------|------|---------|
| **module_scraper** | Python 3.10 + Scrapy + Playwright | N/A | Web scraping and news collection |
| **module_connector** | Python 3.9 + AsyncIO | N/A | Data transfer between services |
| **module_pipeline** | Python 3.9 + FastAPI + spaCy | 8003 | AI/ML processing with LLMs |
| **module_dashboard_review_backend** | Python 3.9 + FastAPI | 8004 | Backend API for editorial dashboard |
| **module_dashboard_review_frontend** | React 18 + TypeScript + Vite | 3001→80 | Frontend UI for journalists |
| **nginx_reverse_proxy** | Nginx 1.25 Alpine | 80, 443 | Reverse proxy and load balancer |

### Upcoming Services (Sistema Renovado de Scraping)

| Service | Technology | Port | Purpose | Status |
|---------|------------|------|---------|--------|
| **Scrapyd** | Python + Twisted | 6800 | Spider deployment server | 📅 Planned |
| **ScrapydWeb** | Python + Flask | 5000 | Management dashboard | 📅 Planned |
| **Spider Factory** | Python + FastAPI | 8005 | Intelligent spider generation | 📅 Planned |
| **Redis** | Redis 7 Alpine | 6379 | Multi-level cache system | 📅 Planned |

## 📁 Project Structure

```
LaMaquinaDeNoticias/
├── .env.example                          # Global environment variables template
├── docker-compose.yml                    # Docker orchestration
├── requirements.txt                      # Consolidated Python dependencies
│
├── src/                                  # Source code for all modules
│   ├── module_scraper/                   # Web scraping module
│   ├── module_connector/                 # Data transfer service
│   ├── module_pipeline/                  # AI/ML processing
│   ├── module_dashboard_review_backend/  # Dashboard API
│   ├── module_dashboard_review_frontend/ # Dashboard UI
│   └── nginx_reverse_proxy/              # Reverse proxy
│
├── BaseDeDatos_SUPABASE/                 # Database configuration
│   ├── migrations/                       # SQL migration system
│   ├── documentación/                    # Database documentation
│   └── scripts/                          # Utility scripts
│
├── tests/                                # Integration tests
│   ├── e2e/                              # End-to-end tests
│   ├── integration/                      # Inter-service tests
│   └── resilience/                       # Fault tolerance tests
│
└── docs/                                 # Project documentation
    ├── GOALS.md                          # Project goals and roadmap
    └── Plan_Inicial/                     # Initial planning docs
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.9+
- Supabase account with project credentials
- Groq API key (required for AI processing)

### Setup Commands

```bash
# 1. Clone and configure environment
git clone <repo-url>
cd LaMaquinaDeNoticias

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your real credentials

# 3. Install global dependencies
pip install -r requirements.txt

# 4. Configure spaCy models
python -m spacy download es_core_news_lg
python -m spacy download en_core_web_sm

# 5. Configure Playwright
playwright install

# 6. Start services
docker-compose up -d
```

## ⚙️ Environment Configuration

### Required Variables (must be set for basic functionality)

```env
# Supabase Database
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_ANON_KEY="eyJhbG..."
SUPABASE_SERVICE_ROLE_KEY="eyJhbG..."
SUPABASE_DB_PASSWORD="your-secure-password"

# AI/LLMs (required for pipeline)
GROQ_API_KEY="gsk_your-api-key"

# Basic Configuration
SCRAPER_TARGET_URLS="url1,url2,url3"  # Target URLs for scraping
LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
ENVIRONMENT="development"  # development, staging, production
```

### Optional Variables

```env
# Additional AI APIs
ANTHROPIC_API_KEY=""     # For advanced features
OPENAI_API_KEY=""        # OpenAI models
PERPLEXITY_API_KEY=""    # Research capabilities

# Spider Factory & Scraping
FIRECRAWL_API_KEY=""     # Required for Spider Factory web analysis
REDIS_URL="redis://redis:6379"  # Cache for Spider Factory

# Monitoring
SENTRY_DSN=""            # Error tracking
SLACK_WEBHOOK=""         # Notifications

# ScrapydWeb Configuration
SCRAPYDWEB_USERNAME="admin"      # Change in production
SCRAPYDWEB_PASSWORD=""           # Set secure password

# SMTP for Spidermon Alerts
SMTP_HOST=""
SMTP_PORT="587"
SMTP_USER=""
SMTP_PASSWORD=""
SMTP_FROM=""
SMTP_TO=""
```

## 🔧 Common Commands

### Docker Operations

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f [service-name]

# Restart a service
docker-compose restart [service-name]

# Enter container shell
docker-compose exec [service-name] /bin/bash
```

### Development Commands

```bash
# Run tests for a specific module
cd src/module_pipeline
make test

# Run tests with coverage
make test-cov

# Format code
make format

# Lint code
make lint

# Start development server (module_pipeline example)
make dev
```

### Database Operations

```bash
# Run database migrations
cd BaseDeDatos_SUPABASE/migrations
./deploy.sh --backup --verbose

# Check migration status
./migration_utils.sh status

# Rollback migrations
./rollback.sh
```

## 🧪 Testing

Each module has its own test suite. Common test commands:

```bash
# Run all tests for a module
cd src/[module-name]
pytest

# Run specific test file
pytest tests/test_specific.py -v

# Run with coverage
pytest --cov=src --cov-report=html

# Run integration tests
cd tests
python run_integration_tests.py

# Run end-to-end tests
python run_e2e_tests.py
```

## 📊 Service Endpoints

| Service | Internal URL | External URL | API Docs |
|---------|-------------|--------------|----------|
| Pipeline API | module_pipeline:8003 | http://localhost:8003 | /docs |
| Dashboard API | module_dashboard_review_backend:8004 | http://localhost:8004 | /docs |
| Frontend UI | module_dashboard_review_frontend:80 | http://localhost:3001 | N/A |

### Health Checks

```bash
# Pipeline health
curl http://localhost:8003/health

# Dashboard API health
curl http://localhost:8004/health

# Detailed health status
curl http://localhost:8003/health/detailed
```

## 🗄️ Database Schema

The system uses PostgreSQL (via Supabase) with the following key tables:

- **articulos**: Main articles table
- **fragmentos**: Article fragments for processing
- **entidades**: Named entities (people, organizations, locations)
- **hechos**: Extracted facts and claims
- **citas**: Quotes and citations
- **relaciones**: Relationships between entities
- **embeddings**: Vector embeddings for semantic search

Key features:
- Uses pgvector for semantic search (384 dimensions)
- Partitioned tables for scalability
- Materialized views for performance
- Automated monitoring and alerts

## 🔍 Common Workflows

### 1. Processing a News Article

```bash
# The flow is automated, but you can monitor it:
# 1. Scraper collects article → saved to Supabase
# 2. Connector detects new article → sends to pipeline
# 3. Pipeline processes with AI → extracts entities, facts, quotes
# 4. Results saved to Supabase → available in dashboard
```

### 2. Viewing Processing Status

```bash
# Check pipeline status
curl http://localhost:8003/monitoring/pipeline-status

# View metrics
curl http://localhost:8003/metrics

# Access dashboard
open http://localhost:3001
```

### 3. Debugging Issues

```bash
# Check service logs
docker-compose logs -f module_pipeline

# Run health checks
curl http://localhost:8003/health/detailed

# Check database connection
cd src/module_pipeline
python scripts/test_connections.py
```

## 🚨 Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError` | Dependencies not installed | `pip install -r requirements.txt` |
| `Connection refused Supabase` | Invalid credentials | Verify `.env` file |
| `Groq API Error` | Invalid API key | Check `GROQ_API_KEY` |
| `Port already in use` | Port conflict | Change ports in `docker-compose.yml` |
| `Permission denied` | Docker permissions | Use `sudo docker-compose` |

## 📚 Key Documentation References

- **Project Goals & Roadmap**: `docs/GOALS.md`
- **Database Guide**: `BaseDeDatos_SUPABASE/GUIA_BD.md`
- **Module-specific docs**: `src/module_*/README.md`
- **Migration Guide**: `BaseDeDatos_SUPABASE/migrations/MIGRATION_GUIDE.md`
- **API Documentation**: Access `/docs` endpoint on running services
- **Scraping System Renovation**: `Investigación/Conclusiones/TODO_SISTEMA_SCRAPING_RENOVADO.md`
- **Architecture Decisions**: `Investigación/Conclusiones/` folder contains all key decisions

## 🔐 Security Notes

- Never commit `.env` files or expose API keys
- Use `SUPABASE_SERVICE_ROLE_KEY` only for administrative tasks
- Keep `SUPABASE_ANON_KEY` for client-side operations
- All services run as non-root users in containers
- Enable CORS only for trusted origins

## 🕷️ Sistema de Scraping Avanzado

### Estado Actual del module_scraper

El módulo de scraping tiene una arquitectura sofisticada basada en Scrapy:

```
module_scraper/
├── scraper_core/
│   ├── spiders/
│   │   ├── base/
│   │   │   └── base_article.py      # Clase base con funcionalidad común
│   │   └── [spiders individuales]   # ~10 spiders específicos por medio
│   ├── pipelines/                   # DataCleaning, DataValidation, SupabaseStorage
│   ├── middlewares/                 # Playwright, rate limiting, deduplicación
│   └── monitors/                    # Spidermon ya implementado
└── @generador-spiders/              # Sistema actual (a deprecar)
```

**Características actuales**:
- **BaseArticleSpider**: Maneja rotación de user-agents, respeta robots.txt, soporte Playwright
- **scrapy-crawl-once**: Sistema de deduplicación de URLs
- **Spidermon**: Monitoreo básico implementado

### 🚀 Renovación en Progreso

Se está implementando un sistema renovado según `Investigación/Conclusiones/TODO_SISTEMA_SCRAPING_RENOVADO.md`:

#### 1. **ScrapydWeb + Spidermon** (Gestión y Monitoreo)
- **Scrapyd**: Servidor de deployment de spiders (puerto 6800)
- **ScrapydWeb**: Dashboard centralizado (puerto 5000)
- **Spidermon mejorado**: 4 monitores específicos
  - StructureChangeMonitor
  - CriticalFieldsMonitor
  - ResponseTimeMonitor
  - HTTPErrorRateMonitor

#### 2. **Spider Factory 2.0** (Generación Inteligente)
- **Smart Analyzer**: Análisis automático de sitios web con Firecrawl
- **Cache multinivel**: L1 (memoria), L2 (Redis), L3 (patterns)
- **Template System**: 90% código común, 10% personalización
- **Auto-deploy**: Integración directa con Scrapyd
- **Puerto**: 8005

#### 3. **Migración area_geografica**
Cambio fundamental en el modelo de datos:
```python
# Antes
pais_publicacion = "España"

# Después
area_geografica = "ESPAÑA"
cobertura_adicional = ["HISPANOAMERICA", "UNION_EUROPEA"]
```

**HISPANIDAD**: Concepto que agrupa 24 territorios con herencia hispana, incluyendo:
- España
- 19 países de Hispanoamérica
- Estados Unidos, Filipinas, Guinea Ecuatorial, Sahara Occidental

### 📋 Decisiones Arquitectónicas Clave

1. **Documentación Oficial Obligatoria**: Antes de implementar, consultar:
   - **Context7**: Para documentación de librerías (Scrapy, Spidermon)
   - **Firecrawl**: Para documentación web oficial
   - Regla: "Sin documentación oficial = NO implementar"

2. **Arquitectura Híbrida Pragmática** para Spider Factory:
   - Backend unificado inicialmente (FastAPI + UI simple)
   - Opción de separar frontend en el futuro si se justifica

3. **Política "Buen Ciudadano Web"**:
   - Respeto estricto de robots.txt
   - Rate limiting configurable
   - User-agent rotation
   - Delays aleatorios entre requests

### 🔧 Comandos Específicos de Scraping

```bash
# Scrapyd Operations
curl http://localhost:6800/daemonstatus.json      # Estado del servidor
curl http://localhost:6800/listprojects.json      # Proyectos disponibles
curl http://localhost:6800/listspiders.json       # Spiders del proyecto
scrapyd-deploy                                    # Deploy manual

# Spider Factory
curl http://localhost:8005/docs                   # API documentation
curl http://localhost:8005/api/analyze            # Analizar sitio web
curl http://localhost:8005/api/cache/stats        # Estadísticas de cache

# Redis Cache
redis-cli -h localhost -p 6379                    # Cliente Redis
redis-cli info stats                              # Estadísticas
redis-cli flushdb                                 # Limpiar cache (cuidado!)

# Ejecutar spider individual
cd src/module_scraper
scrapy crawl [spider_name] -L INFO

# Generar spider con el sistema actual (deprecated)
cd src/module_scraper/@generador-spiders
python generar_spider.py
```

### 🔌 Puertos Adicionales del Sistema de Scraping

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| Scrapyd | 6800 | API de deployment de spiders |
| ScrapydWeb | 5000 | Dashboard de gestión |
| Spider Factory | 8005 | Generación inteligente de spiders |
| Redis | 6379 | Cache multinivel |

## 🎯 Development Best Practices

1. **Module Independence**: Each module is self-contained with its own dependencies
2. **API Communication**: Inter-service communication only via REST APIs
3. **Error Handling**: Comprehensive error handling with retries
4. **Logging**: Consistent logging across all services
5. **Testing**: Write tests for new features before implementing
6. **Documentation**: Update relevant README files when making changes
7. **Scraping Ethics**: Always respect robots.txt and implement polite crawling

## 📈 Performance Considerations

- Pipeline processes articles asynchronously with configurable workers
- Database uses partitioning for large tables
- Materialized views for frequently accessed data
- Connection pooling configured for all services
- Rate limiting implemented in scraper module

## 🔄 Deployment Notes

- Each module can be deployed independently
- Use environment-specific `.env` files
- Database migrations are idempotent and safe to re-run
- Health checks ensure service availability
- Nginx handles SSL termination and load balancing

---

## 🔄 System Renovation Timeline

The scraping system is undergoing a major renovation (15 working days):

1. **Phase 0** (1 day): Research & Documentation
2. **Phase 1** (1 day): Preparation & Validation  
3. **Phase 2** (3 days): Scrapyd + ScrapydWeb Infrastructure
4. **Phase 3** (4 days): Spider Factory Core ⚠️ Most Complex
5. **Phase 4** (3 days): Spidermon Complete Integration
6. **Phase 5** (2 days): Migrations & Optimizations
7. **Phase 6** (2 days): Documentation & Handover

For detailed execution plan, see: `Investigación/Conclusiones/TODO_SISTEMA_SCRAPING_RENOVADO.md`

---

**Last Updated**: December 2024  
**Project Status**: MVP Functional, Scraping System Under Renovation  
**Documentation Version**: 2.0 - Enhanced with Scraping Context