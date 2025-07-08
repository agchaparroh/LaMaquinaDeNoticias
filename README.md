# La Máquina de Noticias

**Sistema modular para recopilación, procesamiento y análisis automatizado de noticias.** Herramienta diseñada para periodistas que permite extracción de conocimiento estructurado desde grandes volúmenes de texto utilizando inteligencia artificial.

## 🎯 **Estado del Proyecto: MVP FUNCIONAL** ✅

**La Máquina de Noticias** ha alcanzado un **Producto Mínimo Viable (MVP)** completamente funcional con **8 módulos implementados** que cubren el flujo completo desde recopilación hasta presentación, incluyendo **Spider Factory** para generación inteligente de spiders.

> 📋 **Ver [GOALS.md](docs/GOALS.md)** para objetivos detallados, roadmap y lecciones aprendidas del MVP.

---

## 🏗️ **Arquitectura MVP - Microservicios Docker**

**Cada módulo es un contenedor Docker independiente y autónomo, conectado mediante APIs.**

```mermaid
graph TD
    A[🕷️ module_scraper] --> B[🔗 module_connector]
    B --> C[⚙️ module_pipeline] 
    C --> D[🔧 module_dashboard_review_backend]
    D --> E[📱 module_dashboard_review_frontend]
    F[🌐 nginx_reverse_proxy] --> D
    F --> E
    F --> I
    F --> J
    G[(🗄️ Supabase)] <--> A
    G <--> C
    G <--> D
    G <--> I
    H[🤖 Groq/Anthropic] <--> C
    I[🤖 spider_factory] --> A
    J[📱 module_spider_factory_frontend] --> I
    K[📡 Scrapyd] --> A
    L[🎛️ ScrapydWeb] --> K
    M[🔄 Redis] <--> I
    M <--> K
```

### **Principios de Diseño MVP**

- **Independencia Total**: Cada contenedor está construido en docker de forma autónoma, por lo que cada uno selecciona sus tecnologías óptimas... sin crear problemas por incompatibilidad entre módulos
- **Comunicación por Red**: Intercambio únicamente por APIs REST/HTTP  
- **Autonomía de Configuración**: Variables de entorno específicas por módulo
- **Seguridad Uniforme**: Prácticas consistentes (usuarios no-root, health checks)

---

## 📋 **Módulos Implementados en el MVP**

| **Módulo** | **Tecnología** | **Puerto** | **Estado** | **Función** |
|------------|----------------|------------|------------|-------------|
| **module_scraper** | Python 3.10 + Scrapy + Playwright | N/A | ✅ **Implementado** | Recopilación automática de noticias |
| **module_connector** | Python 3.9 + AsyncIO | N/A | ✅ **Implementado** | Conector entre scraper y pipeline |
| **module_pipeline** | Python 3.9 + FastAPI + spaCy + ML | 8003 | ✅ **Implementado** | Procesamiento con IA/LLMs |
| **module_dashboard_review_backend** | Python 3.9 + FastAPI | 8004 | ✅ **Implementado** | API backend dashboard editorial |
| **module_dashboard_review_frontend** | React 18 + TypeScript + Vite | 3001→80 | ✅ **Implementado** | UI dashboard para periodistas |
| **nginx_reverse_proxy** | Nginx 1.25 Alpine | 80, 443 | ✅ **Implementado** | Proxy reverso y balanceador |
| **spider_factory** | Python 3.9 + FastAPI + Redis | 8000 | ✅ **Implementado** | Generación inteligente de spiders |
| **module_spider_factory_frontend** | React 18 + TypeScript + Vite | 3002→80 | ✅ **Implementado** | UI para generación de spiders |

### **Servicios de Infraestructura Adicionales**

| **Servicio** | **Tecnología** | **Puerto** | **Estado** | **Función** |
|--------------|----------------|------------|------------|-------------|
| **scrapyd** | Python + Twisted | 6800 | ✅ **Implementado** | Servidor de despliegue de spiders |
| **scrapydweb** | Python + Flask | 5000 | ✅ **Implementado** | Dashboard de gestión Scrapy |
| **redis** | Redis 7 Alpine | 6379 | ✅ **Implementado** | Sistema de caché multinivel |

### **Flujo de Datos MVP**

1. **🤖 Generación**: `spider_factory` analiza sitios web con IA y genera spiders inteligentes
2. **📡 Despliegue**: Spiders generados se despliegan automáticamente en `scrapyd`
3. **🎛️ Gestión**: `scrapydweb` permite monitoreo y gestión visual de todos los spiders
4. **🕷️ Extracción**: `module_scraper` ejecuta spiders para recopilar noticias usando Scrapy + Playwright
5. **🔗 Conectividad**: `module_connector` transfiere datos entre scraper y pipeline  
6. **⚙️ Procesamiento**: `module_pipeline` aplica IA/ML para análisis con LLMs (Groq/Anthropic)
7. **🗄️ Almacenamiento**: Datos estructurados almacenados en Supabase (PostgreSQL + pgvector)
8. **📱 Presentación**: Dashboard web para periodistas accesible vía `nginx_reverse_proxy`

---

## 📁 **Estructura del Proyecto MVP**

```
LaMaquinaDeNoticias/
├── 📋 GOALS.md                          # Objetivos y roadmap del proyecto
├── 📋 README.md                         # Este archivo
├── 🐳 docker-compose.yml                # Orquestación de servicios MVP
├── 🔧 .env.example                      # Plantilla configuración
├── 📦 requirements.txt                  # Dependencias globales
│
├── 🗂️ src/                              # Módulos implementados
│   ├── 🕷️ module_scraper/               # Web scraping (Python 3.10)
│   │   ├── 🐳 Dockerfile                # Container scraper optimizado
│   │   ├── ⚙️ scrapy.cfg                # Configuración Scrapy
│   │   ├── 📋 requirements.txt          # Dependencias específicas
│   │   └── 📚 README.md                 # Documentación scraper
│   │
│   ├── 🔗 module_connector/             # Worker service (Python 3.9)
│   │   ├── 🐳 Dockerfile                # Container worker
│   │   ├── ⚙️ src/                      # Código fuente connector
│   │   └── 📋 requirements.txt          # Dependencias AsyncIO
│   │
│   ├── ⚙️ module_pipeline/              # ML processing (Python 3.9)
│   │   ├── 🐳 Dockerfile                # Container FastAPI + ML
│   │   ├── 🌐 src/                      # APIs y lógica ML
│   │   ├── 🧪 tests/                    # Tests comprehensivos
│   │   └── 📋 requirements.txt          # spaCy + LLMs + FastAPI
│   │
│   ├── 🔧 module_dashboard_review_backend/  # API Backend (Python 3.9)
│   │   ├── 🐳 Dockerfile                # Container FastAPI
│   │   ├── 🌐 src/                      # APIs dashboard
│   │   ├── 🧪 tests/                    # Tests API
│   │   └── 📋 requirements.txt          # FastAPI + Supabase
│   │
│   ├── 📱 module_dashboard_review_frontend/ # UI Frontend (React 18)
│   │   ├── 🐳 Dockerfile                # Multi-stage: Node + Nginx
│   │   ├── ⚛️ src/                      # Componentes React + TS
│   │   ├── 📦 package.json              # Dependencias Node
│   │   └── ⚙️ vite.config.ts            # Configuración build
│   │
│   ├── 🌐 nginx_reverse_proxy/          # Proxy + Load Balancer
│   │   ├── 🐳 docker/Dockerfile         # Container Nginx optimizado
│   │   ├── ⚙️ config/nginx.conf         # Configuración proxy
│   │   └── 📜 scripts/                  # Scripts deployment
│   │
│   ├── 🤖 spider_factory/               # Spider Generator (Python 3.9)
│   │   ├── 🐳 Dockerfile                # Container FastAPI + Redis
│   │   ├── 🌐 api.py                    # API REST generación spiders
│   │   ├── 🧠 analyzer.py               # Análisis inteligente sitios
│   │   ├── 📋 requirements.txt          # FastAPI + Redis + Jinja2
│   │   └── 📚 README.md                 # Documentación spider factory
│   │
│   └── 📱 module_spider_factory_frontend/ # UI Spider Factory (React 18)
│       ├── 🐳 Dockerfile                # Multi-stage: Node + Nginx
│       ├── ⚛️ src/                      # Componentes React + TS
│       ├── 📦 package.json              # Dependencias Node
│       └── ⚙️ vite.config.ts            # Configuración build
│
├── 🗄️ BaseDeDatos_SUPABASE/             # Configuración BD
│   ├── 📜 migrations/                   # Migraciones SQL
│   ├── 📜 scripts/                      # Scripts utilidad BD
│   └── 📚 GUIA_BD.md                    # Documentación BD
│
└── 🧪 tests/                            # Tests integración global
    └── test_supabase_integration.py     # Tests MVP completo
```

---

### **Endpoints Principales del MVP**

| **Servicio** | **Endpoint Interno** | **Endpoint Externo** | **Documentación** |
|--------------|----------------------|----------------------|-------------------|
| Pipeline API | `module_pipeline:8003` | `localhost:8003` | `/docs` |
| Dashboard API | `module_dashboard_review_backend:8004` | `localhost:8004` | `/docs` |
| Frontend UI | `module_dashboard_review_frontend:80` | `localhost:3001` | N/A |
| Spider Factory API | `spider_factory_backend:8000` | `localhost:8005` | `/docs` |
| Spider Factory UI | `spider_factory_frontend:80` | `localhost:3002` | N/A |
| Scrapyd API | `scrapyd:6800` | `localhost:6800` | `/daemonstatus.json` |
| ScrapydWeb UI | `scrapydweb:5000` | `localhost:5000` | Dashboard completo |
| Redis Cache | `redis:6379` | `localhost:6379` | N/A |

---

## ⚙️ **Configuración Consolidada**

### **🚀 Setup Rápido (5 minutos)**

```bash
# 1. Clonar y configurar entorno
git clone <repo-url>
cd LaMaquinaDeNoticias

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales reales

# 3. Instalar dependencias globales
pip install -r requirements.txt

# 4. Configurar modelos de spaCy
python -m spacy download es_core_news_lg
python -m spacy download en_core_web_sm

# 5. Configurar Playwright
playwright install

# 6. Levantar servicios
docker-compose up -d
```

### **📋 Variables de Entorno Principales**

**⚠️ REQUERIDAS (obligatorias para funcionamiento básico):**
```env
# === SUPABASE (Base de datos) ===
PROJECT_URL="https://tu-proyecto.supabase.co"
SUPABASE_ANON_KEY="eyJhbG..."  # Clave anónima
SUPABASE_SERVICE_ROLE_KEY="eyJhbG..."  # Clave de servicio
SUPABASE_DB_PASSWORD="tu-password-seguro"

# === IA/LLMs (Procesamiento) ===
GROQ_API_KEY="gsk_tu-api-key"  # Requerida para module_pipeline

# === CONFIGURACIÓN BÁSICA ===
SCRAPER_TARGET_URLS="url1,url2,url3"  # URLs objetivo scraping
LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR

# === SPIDER FACTORY ===
FIRECRAWL_API_KEY="fc-tu-api-key"  # Para análisis de sitios web
SPIDER_FACTORY_REDIS_HOST="redis"  # Redis compartido

# === SCRAPYD Y SCRAPING AVANZADO ===
SCRAPYDWEB_USERNAME="admin"      # Usuario ScrapydWeb (cambiar en producción)
SCRAPYDWEB_PASSWORD=""           # Contraseña segura requerida
REDIS_URL="redis://redis:6379"  # Sistema de caché compartido
```

**🔧 OPCIONALES (funcionalidades avanzadas):**
```env
# APIs adicionales de IA
ANTHROPIC_API_KEY=""     # Claude (TaskMaster, funciones avanzadas)
OPENAI_API_KEY=""        # GPT models
PERPLEXITY_API_KEY=""    # Research capabilities

# Monitoreo y alertas
SENTRY_DSN=""            # Error tracking
SLACK_WEBHOOK=""         # Notificaciones

# ScrapydWeb Dashboard Avanzado
SMTP_HOST=""             # SMTP para alertas Spidermon
SMTP_PORT="587"          # Puerto SMTP
SMTP_USER=""             # Usuario SMTP
SMTP_PASSWORD=""         # Contraseña SMTP

# Configuración de entorno
ENVIRONMENT="development"  # development, staging, production
DEBUG_MODE="false"       # Solo para desarrollo
```

### **🗂️ Configuración por Módulo**

**El proyecto utiliza configuración HÍBRIDA:**

- **🌐 Variables Globales** (`.env` raíz): Compartidas entre módulos
  - Credenciales Supabase
  - APIs de IA (Groq, Anthropic, etc.)
  - Configuración de logging
  - URLs de comunicación inter-servicios

- **⚙️ Variables Específicas** (cada `src/module_*/.env.example`):
  - **module_scraper**: Configuración Scrapy, Playwright, timeouts, rate limiting
  - **module_connector**: Directorios, polling intervals, async workers
  - **module_pipeline**: Configuración ML, modelos, límites de contenido, prompts de IA
  - **module_dashboard_review_backend**: CORS, puerto API, autenticación
  - **module_dashboard_review_frontend**: Variables VITE_*, URLs de endpoints
  - **nginx_reverse_proxy**: Configuración de proxy, SSL, rate limiting
  - **spider_factory**: Redis, límites de análisis, timeouts, técnicas de evasión
  - **module_spider_factory_frontend**: URLs de API y WebSocket, configuración UI
  - **scrapyd**: Configuración de workers, logs, proyectos
  - **scrapydweb**: Dashboard, autenticación, integración SMTP

**📁 Jerarquía de Configuración:**
```
1. Variables globales (.env raíz)          ← Compartidas
2. Variables específicas (src/module_*/)   ← Sobrescriben si existe conflicto
3. Variables de Docker Compose             ← Runtime específico
```

### **📦 Dependencias Consolidadas**

**El archivo `requirements.txt` global consolida TODAS las dependencias:**

- **✅ Ventajas**: Versiones sincronizadas, sin conflictos
- **⚙️ Uso**: `pip install -r requirements.txt` instala todo
- **🔄 Sincronización**: Cada módulo mantiene su `requirements.txt` específico

**📊 Categorías de dependencias:**
- Frameworks web (FastAPI, Uvicorn)
- Base de datos (Supabase, PostgreSQL)
- IA/ML (Groq, spaCy, sentence-transformers)
- Web scraping (Scrapy, Playwright, BeautifulSoup)
- Testing (pytest, pytest-asyncio)
- Utilidades (tenacity, loguru, pydantic)

### **🐳 Docker y Entornos**

**Configuración de entornos:**
```bash
# Desarrollo local
ENVIRONMENT=development
DEBUG_MODE=true
LOG_LEVEL=DEBUG

# Staging/Testing  
ENVIRONMENT=staging
DEBUG_MODE=false
LOG_LEVEL=INFO

# Producción
ENVIRONMENT=production
DEBUG_MODE=false
LOG_LEVEL=WARNING
```

**Variables Docker específicas:**
```env
# Comunicación inter-servicios
PIPELINE_API_URL=http://module_pipeline:8003
DASHBOARD_API_URL=http://module_dashboard_review_backend:8004
FRONTEND_URL=http://module_dashboard_review_frontend:80
```

---

### **🔍 Validación de Configuración**

**Verificar configuración básica:**
```bash
# Test conexión Supabase
curl -H "apikey: $SUPABASE_ANON_KEY" "$SUPABASE_URL/rest/v1/"

# Test API Pipeline
curl http://localhost:8003/health

# Test API Dashboard
curl http://localhost:8004/health

# Test Spider Factory
curl http://localhost:8005/health

# Test Scrapyd
curl http://localhost:6800/daemonstatus.json

# Test ScrapydWeb
curl http://localhost:5000

# Test Redis
redis-cli -h localhost -p 6379 ping

# Test Frontend
curl http://localhost:3001
```

**Logs de verificación:**
```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs específicos
docker-compose logs -f module_pipeline
docker-compose logs -f module_scraper
docker-compose logs -f spider_factory_backend
docker-compose logs -f scrapyd
docker-compose logs -f scrapydweb
```

### **❗ Troubleshooting Común**

| **Problema** | **Causa** | **Solución** |
|--------------|-----------|-------------|
| `ModuleNotFoundError` | Dependencias no instaladas | `pip install -r requirements.txt` |
| `Connection refused Supabase` | Credenciales incorrectas | Verificar `.env` y credenciales |
| `Groq API Error` | API key inválida | Verificar `GROQ_API_KEY` |
| `Firecrawl API Error` | API key inválida | Verificar `FIRECRAWL_API_KEY` |
| `Redis connection failed` | Redis no iniciado | `docker-compose up redis` |
| `Scrapyd not responding` | Servicio no iniciado | `docker-compose restart scrapyd` |
| `Spider generation fails` | Spider Factory no configurado | Verificar configuración Redis y APIs |
| `Port already in use` | Puerto ocupado | Cambiar puertos en `docker-compose.yml` |
| `Permission denied` | Problemas Docker | `sudo docker-compose up` |

---

## 📚 **Documentación MVP**

| **Documento** | **Propósito** | **Audiencia** |
|---------------|---------------|---------------|
| **[GOALS.md](GOALS.md)** | Objetivos, MVP status, roadmap | Product & Development |
| **[README.md](README.md)** | Quick start y overview | Todos los usuarios |
| **src/module_*/README.md** | Documentación técnica específica | Desarrolladores |
| **BaseDeDatos_SUPABASE/GUIA_BD.md** | Schema y configuración BD | Backend developers |
| **src/module_*/.env.example** | Configuración específica por módulo | DevOps/Deployment |
| **.env.example** | Configuración global consolidada | Administradores |