# La Máquina de Noticias

Sistema modular para recopilación, procesamiento y análisis de noticias. Herramienta diseñada para periodistas que permite extracción de conocimiento estructurado desde grandes volúmenes de texto.

## 🐳 Arquitectura de Contenedores Docker

**Cada módulo es un contenedor Docker independiente y autónomo, conectado mediante APIs.**

### Principios de Diseño

- **Independencia Total:** Cada contenedor selecciona sus tecnologías óptimas
- **Comunicación por Red:** Intercambio únicamente por APIs REST/HTTP  
- **Autonomía de Configuración:** Variables de entorno específicas por módulo
- **Seguridad Uniforme:** Prácticas consistentes (usuarios no-root, health checks)

### Ejemplos de Especialización Apropiada
- `module_scraper`: Python 3.10 (óptimo para Scrapy + Playwright)
- `module_pipeline`: Python 3.9 (estable para ML + spaCy)
- `module_connector`: Worker service (procesamiento de archivos)

## 📋 Módulos del Sistema

### Estado de Implementación

- [x] module_scraper - Sistema de recopilación de noticias (Scrapy)
- [x] module_connector - Conector entre scraper y pipeline  
- [x] module_pipeline - Pipeline principal de procesamiento con LLMs
- [ ] module_orchestration_agent - Orquestación y scheduling (Prefect)
- [ ] module_maintenance_scripts - Scripts de mantenimiento
- [ ] module_chat_interface_backend - API interfaz de investigación
- [ ] module_chat_interface_frontend - UI interfaz de investigación
- [ ] module_dashboard_review_backend - API dashboard periodistas
- [ ] module_dashboard_review_frontend - UI dashboard periodistas
- [ ] module_dev_interface_backend - API herramientas desarrollo
- [ ] module_dev_interface_frontend - UI herramientas desarrollo
- [ ] nginx_reverse_proxy - Proxy reverso y balanceador

## 🚀 Quick Start

### Prerrequisitos
- Docker y Docker Compose
- Variables de entorno configuradas en `.env`

### Ejecución
```bash
# Construir y ejecutar todos los servicios
docker-compose up --build

# Servicios disponibles:
# - module_pipeline: http://localhost:8003 (FastAPI server)
# - module_connector: Worker service (procesa archivos)
# - module_scraper: Scrapy crawler
```

## 📁 Estructura del Proyecto

```
├── src/                          # Módulos implementados
│   ├── module_scraper/           # Web scraping (Python 3.10)
│   ├── module_connector/         # Worker service (Python 3.9)
│   ├── module_pipeline/          # ML processing (Python 3.9)
│   └── [otros módulos]/          # Pendientes de implementación
├── BaseDeDatos_SUPABASE/         # Configuración y migraciones BD
├── docs/                         # Documentación técnica
├── Borrar/                       # Backup de código obsoleto
├── docker-compose.yml            # Orquestación de servicios
└── .env                          # Variables de entorno
```

## 🔗 Comunicación entre Servicios

Los contenedores se comunican usando nombres de servicios Docker:

```python
# ✅ Correcto - comunicación entre contenedores
PIPELINE_API_URL = "http://module_pipeline:8003"

# ❌ Incorrecto - no funciona entre contenedores  
PIPELINE_API_URL = "http://localhost:8003"
```

## 📚 Documentación

- `docs/filosofia_contenedores_docker.md` - Principios arquitecturales
- `BaseDeDatos_SUPABASE/` - Configuración base de datos Supabase
- `Limpieza/soluciones_implementadas.md` - Historial de problemas resueltos

## ⚙️ Configuración

Cada módulo mantiene su configuración específica:
- Variables compartidas: `SUPABASE_URL`, `SUPABASE_KEY`, `LOG_LEVEL`
- Variables específicas: `PLAYWRIGHT_TIMEOUT`, `API_PORT`, `PIPELINE_API_URL`

## 🛡️ Seguridad

- Variables sensibles en `.env` (excluido del repositorio)
- Usuarios no-root en todos los contenedores
- Health checks específicos por tipo de servicio
- Comunicación por red interna Docker

---

**Arquitectura:** Microservicios Docker independientes con especializaciones apropiadas por dominio tecnológico.
