# La Máquina de Noticias - Claude Code Project Context

## 📍 Ubicación del Proyecto / Project Location

**Ruta Windows**: `C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\`
**Ruta WSL**: `/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/`

## 📂 Sistema de Gestión de Proyectos CPMS

- **CPMS Workspace**: `CPMS-Workspace/` (dentro del proyecto)
- **Documentación CPMS**: Ver `CPMS-Workspace/docs/CPMS-Sistema-Gestion-Proyectos-Claude.md`
- **Para cargar proyectos CPMS**: "Carga proyecto [nombre] desde CPMS-Workspace/projects"

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
| **spider_factory** | Python 3.9 + FastAPI + Redis | 8005 | Intelligent spider generation |
| **module_spider_factory_frontend** | React 18 + TypeScript + Vite | 3002→80 | UI for spider generation |

### Upcoming Services (Sistema Renovado de Scraping)

| Service | Technology | Port | Purpose | Status |
|---------|------------|------|---------|--------|
| **Scrapyd** | Python + Twisted | 6800 | Spider deployment server | 📅 Planned |
| **ScrapydWeb** | Python + Flask | 5000 | Management dashboard | 📅 Planned |
| **Redis** | Redis 7 Alpine | 6379 | Multi-level cache system | 📅 Planned |

## 📁 Project Structure

```
LaMaquinaDeNoticias/
├── .env.example                          # Global environment variables template
├── docker-compose.yml                    # Docker orchestration
├── requirements.txt                      # Consolidated Python dependencies
│
├── CPMS-Workspace/                       # Sistema de gestión de proyectos
│   ├── CLAUDE.md                         # Instrucciones globales
│   ├── docs/                             # Documentación CPMS
│   ├── templates/                        # Plantillas para proyectos
│   └── projects/                         # Proyectos CPMS gestionados
│
├── src/                                  # Source code for all modules
│   ├── module_scraper/                   # Web scraping module
│   ├── module_connector/                 # Data transfer service
│   ├── module_pipeline/                  # AI/ML processing
│   ├── module_dashboard_review_backend/  # Dashboard API
│   ├── module_dashboard_review_frontend/ # Dashboard UI
│   ├── nginx_reverse_proxy/              # Reverse proxy
│   ├── spider_factory/                   # Intelligent spider generation
│   └── module_spider_factory_frontend/   # Spider Factory UI
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

# Spider Factory (required for spider generation)
FIRECRAWL_API_KEY="fc_your-api-key"  # For web analysis
SPIDER_FACTORY_REDIS_HOST="redis"  # Shared Redis instance
```

### Optional Variables

```env
# Additional AI APIs
ANTHROPIC_API_KEY=""     # For advanced features
OPENAI_API_KEY=""        # OpenAI models
PERPLEXITY_API_KEY=""    # Research capabilities

# Scraping System
REDIS_URL="redis://redis:6379"  # Shared cache system

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
| Spider Factory API | spider_factory:8000 | http://localhost:8005 | /docs |
| Spider Factory UI | module_spider_factory_frontend:80 | http://localhost:3002 | N/A |

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
- **Scraping System Renovation**: `Investigación/Conclusiones` folder contains all key decisions
- **CPMS Documentation**: `CPMS-Workspace/docs/CPMS-Sistema-Gestion-Proyectos-Claude.md`

## 🔐 Security Notes

- Never commit `.env` files or expose API keys
- Use `SUPABASE_SERVICE_ROLE_KEY` only for administrative tasks
- Keep `SUPABASE_ANON_KEY` for client-side operations
- All services run as non-root users in containers
- Enable CORS only for trusted origins