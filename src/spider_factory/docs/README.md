# Spider Factory 2.0 🕷️🏭

Sistema inteligente de generación automática de spiders para scraping de sitios de noticias.

## 🚀 Características Principales

- **Análisis Inteligente**: Detecta automáticamente la mejor estrategia de extracción (RSS, Scraping, Playwright)
- **Generación Automática**: Crea spiders de Scrapy optimizados y listos para usar
- **Aprendizaje Continuo**: Almacena y reutiliza patrones exitosos
- **Procesamiento Masivo**: Analiza y genera spiders para múltiples sitios simultáneamente
- **Interfaz Web Moderna**: React + Material-UI con actualizaciones en tiempo real
- **API REST**: FastAPI con documentación automática
- **WebSocket**: Actualizaciones en tiempo real del progreso

## 📋 Requisitos

- Docker y Docker Compose
- Python 3.9+ (para desarrollo local)
- Node.js 18+ (para desarrollo frontend)
- Redis (incluido en Docker)

## 🐳 Instalación con Docker

### 1. Clonar el repositorio

```bash
git clone [repository-url]
cd LaMaquinaDeNoticias/src/spider_factory
```

### 2. Configurar variables de entorno

Crear archivo `.env` en la raíz:

```env
# API Keys
FIRECRAWL_API_KEY=your_firecrawl_api_key_here

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# API
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### 3. Construir y levantar servicios

```bash
docker-compose up --build
```

Esto levantará:
- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **Redis**: localhost:6379
- **Documentación API**: http://localhost:8000/docs

## 🛠️ Desarrollo Local

### Backend

```bash
cd src/spider_factory
pip install -r requirements.txt
python api.py
```

### Frontend

```bash
cd src/module_spider_factory_frontend
npm install
npm run dev
```

## 📖 Uso

### 1. Análisis Individual

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example-news.com",
    "force_analysis": false,
    "check_rss": true
  }'
```

### 2. Generación de Spider

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_result": { ... },
    "spider_name": "example_spider",
    "site_name": "Example News",
    "metadata": {
      "area_geografica": "internacional",
      "follow_pagination": true
    }
  }'
```

### 3. Procesamiento Masivo

Subir archivo CSV con formato:
```csv
url,name,category
https://site1.com,Site 1,tecnologia
https://site2.com,Site 2,deportes
```

## 🏗️ Arquitectura

```
spider_factory/
├── api.py                 # API FastAPI principal
├── analyzer.py            # Análisis inteligente de sitios
├── generator.py           # Generador de spiders
├── patterns.py            # Gestión de patrones
├── batch_processor.py     # Procesamiento masivo
├── websocket_manager.py   # Gestión WebSocket
├── config.py              # Configuración
└── templates/
    └── spiders/           # Templates Jinja2
        ├── rss_spider.j2
        ├── scraping_spider.j2
        └── playwright_spider.j2
```

## 📋 Estado del Proyecto

- [x] TASK-001: Setup Redis y configuración inicial
- [x] TASK-002: Crear estructura base de SmartAnalyzer
- [x] TASK-003: Implementar análisis con Firecrawl
- [x] TASK-004: Implementar búsqueda de patrones
- [x] TASK-005: Desarrollar PatternStorage con Redis
- [x] TASK-006: Crear SpiderGenerator base
- [x] TASK-007: Implementar templates Jinja2
- [x] TASK-008: API REST con FastAPI
- [x] TASK-009: Endpoints de análisis
- [x] TASK-010: Sistema de carga masiva
- [x] TASK-011: Setup proyecto React con Vite
- [x] TASK-012: Componentes base y tema Material-UI
- [x] TASK-013: Wizard de generación individual
- [x] TASK-014: Sistema de importación CSV
- [x] TASK-015: WebSocket para actualizaciones
- [x] TASK-016: Integración completa frontend-backend
- [x] TASK-017: Testing y polish de UI
- [x] TASK-018: Testing con medios reales
- [x] TASK-019: Corrección de bugs y optimización
- [x] TASK-020: Documentación y Docker

## 🔧 Configuración Avanzada

### Estrategias de Análisis

1. **RSS**: Para sitios con feeds RSS bien estructurados
2. **Scraping**: Para sitios con HTML estático
3. **Playwright**: Para sitios con contenido dinámico (JavaScript)

### Personalización de Spiders

Los spiders generados incluyen:
- Respeto a robots.txt
- Rate limiting automático
- Manejo de errores robusto
- Extracción de metadata (Open Graph, JSON-LD)
- Paginación inteligente
- Exportación a JSON

### Cache y Patrones

El sistema almacena en Redis:
- Resultados de análisis (TTL: 24h)
- Patrones exitosos
- Métricas de uso

## 📊 Monitoreo

### Health Check

```bash
curl http://localhost:8000/health
```

### Logs

```bash
# Backend logs
docker-compose logs -f backend

# Ver logs específicos
docker exec -it spider_factory_backend_1 tail -f logs/spider_factory.log
```

## 🧪 Testing

### Tests de Sintaxis

```bash
python syntax_check.py
```

### Test con Sitios Reales

```bash
python test_real_sites.py
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📝 Licencia

Este proyecto es parte de La Máquina de Noticias.

## 🆘 Troubleshooting

### Redis no conecta
```bash
# Verificar que Redis esté corriendo
docker-compose ps
docker-compose logs redis
```

### API no responde
```bash
# Verificar logs del backend
docker-compose logs backend
# Reiniciar servicio
docker-compose restart backend
```

### Frontend no carga
```bash
# Verificar variables de entorno
cat .env
# Reconstruir frontend
docker-compose build frontend
```

## 📞 Soporte

Para reportar bugs o solicitar features, abrir un issue en el repositorio.

---

**Versión**: 2.0.0  
**Proyecto**: La Máquina de Noticias