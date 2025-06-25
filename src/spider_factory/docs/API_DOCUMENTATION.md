# 📚 Spider Factory 2.0 - Documentación API

## Base URL

```
http://localhost:8000
```

## Autenticación

Actualmente la API no requiere autenticación. En producción se recomienda implementar API keys o JWT.

## Endpoints

### 🏥 Health Check

Verificar el estado del sistema.

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-03-15T10:30:00",
  "version": "2.0.0",
  "services": {
    "redis": "healthy",
    "firecrawl": "configured",
    "generator": "healthy"
  }
}
```

### 🔍 Análisis de Sitio

Analizar un sitio web para determinar la mejor estrategia de scraping.

```http
POST /analyze
Content-Type: application/json
```

**Request:**
```json
{
  "url": "https://example-news.com",
  "force_analysis": false,
  "check_rss": true
}
```

**Response:**
```json
{
  "url": "https://example-news.com",
  "strategy": "rss",
  "confidence": 0.95,
  "rss_url": "https://example-news.com/feed",
  "selectors": {
    "title": "h1.article-title",
    "content": "div.article-body",
    "author": "span.author-name",
    "date": "time.publish-date"
  },
  "needs_javascript": false,
  "from_cache": false,
  "sample_articles": [
    {
      "title": "Sample Article",
      "url": "https://example-news.com/article-1"
    }
  ],
  "analysis_time": 2.34
}
```

### 🕷️ Generar Spider

Generar código de spider basado en análisis previo.

```http
POST /generate
Content-Type: application/json
```

**Request:**
```json
{
  "analysis_result": {
    "url": "https://example-news.com",
    "strategy": "rss",
    "confidence": 0.95,
    "rss_url": "https://example-news.com/feed",
    "selectors": {},
    "needs_javascript": false
  },
  "spider_name": "example_news",
  "site_name": "Example News",
  "metadata": {
    "area_geografica": "internacional",
    "follow_pagination": true,
    "max_pages": 10
  }
}
```

**Response:**
```json
{
  "spider_name": "example_news",
  "file_path": "generated_spiders/example_news.py",
  "code_preview": "import scrapy\nfrom scrapy import signals\n...",
  "is_valid": true,
  "generation_time": 0.45
}
```

### 📊 Análisis Masivo

Analizar múltiples sitios desde archivo CSV.

```http
POST /batch/analyze
Content-Type: multipart/form-data
```

**Request:**
```
file: [archivo CSV]
session_id: "batch_001"
```

**CSV Format:**
```csv
url,name,category
https://site1.com,Site 1,technology
https://site2.com,Site 2,sports
```

**Response:**
```json
{
  "batch_id": "batch_20240315_103000",
  "total_sites": 2,
  "processed": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "site": "Site 1",
      "url": "https://site1.com",
      "success": true,
      "analysis": {
        "strategy": "scraping",
        "confidence": 0.85
      }
    }
  ],
  "start_time": "2024-03-15T10:30:00",
  "end_time": "2024-03-15T10:30:05",
  "duration_seconds": 5.2
}
```

### 🔎 Buscar Patrones

Buscar patrones almacenados en el sistema.

```http
POST /patterns/search
Content-Type: application/json
```

**Request:**
```json
{
  "domain": "example.com",
  "strategy": "rss",
  "min_confidence": 0.7
}
```

**Response:**
```json
{
  "patterns": [
    {
      "domain": "example.com",
      "strategy": "rss",
      "confidence": 0.95,
      "selectors": {
        "title": "h1.title",
        "content": "div.content"
      },
      "last_updated": "2024-03-15T10:00:00",
      "times_used": 42,
      "success_rate": 0.98
    }
  ],
  "total": 1
}
```

### 📥 Descargar Spider

Descargar archivo de spider generado.

```http
GET /download/{spider_name}
```

**Response:**
- Content-Type: text/x-python
- Content-Disposition: attachment; filename="spider_name.py"

### 🔌 WebSocket

Conectar para recibir actualizaciones en tiempo real.

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/session_123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

**Mensajes:**
```json
{
  "type": "site_processing",
  "batch_id": "batch_001",
  "site_name": "Example News",
  "site_url": "https://example.com",
  "progress": 45.5
}
```

## Códigos de Estado

| Código | Descripción |
|--------|-------------|
| 200 | Éxito |
| 400 | Petición inválida |
| 404 | Recurso no encontrado |
| 409 | Conflicto (ej: spider ya existe) |
| 500 | Error interno del servidor |
| 503 | Servicio no disponible |

## Ejemplos con cURL

### Análisis simple
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://techcrunch.com"}'
```

### Generación con metadata
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_result": {...},
    "spider_name": "techcrunch_spider",
    "site_name": "TechCrunch",
    "metadata": {
      "area_geografica": "usa",
      "follow_pagination": true,
      "max_pages": 20,
      "excluded_urls": ["/tag/", "/author/"]
    }
  }'
```

### Carga masiva
```bash
curl -X POST http://localhost:8000/batch/analyze \
  -F "file=@sites.csv" \
  -F "session_id=my_batch"
```

## Límites y Cuotas

- Tamaño máximo de archivo CSV: 10MB
- Máximo sitios por batch: 100
- Timeout por análisis: 30 segundos
- Rate limit: 100 requests/hora (configurable)

## Manejo de Errores

Todos los errores siguen el formato:

```json
{
  "error": "HTTP 400",
  "detail": "Descripción del error",
  "timestamp": "2024-03-15T10:30:00"
}
```

## SDK Python

```python
import httpx

class SpiderFactoryClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def analyze(self, url):
        response = await self.client.post(
            f"{self.base_url}/analyze",
            json={"url": url}
        )
        return response.json()
    
    async def generate(self, analysis_result, spider_name, site_name):
        response = await self.client.post(
            f"{self.base_url}/generate",
            json={
                "analysis_result": analysis_result,
                "spider_name": spider_name,
                "site_name": site_name
            }
        )
        return response.json()
```

## Postman Collection

Importar [spider_factory.postman_collection.json](postman/spider_factory.postman_collection.json) para testing rápido.

---

**Documentación interactiva**: http://localhost:8000/docs