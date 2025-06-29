# API Documentation - Spider Factory 2.0

Base URL: `http://localhost/spider-factory/api`

## Authentication

Currently, the API does not require authentication. This may change in future versions.

## Rate Limiting

- **Global limit**: 10 requests per minute per IP
- **Batch operations**: Limited to 100 items per request

## Endpoints

### 1. Health Check

Check if the service is running and healthy.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "redis": "connected",
  "timestamp": "2024-12-27T12:00:00Z"
}
```

### 2. Analyze Website

Analyze a website to determine the best extraction strategy.

**Endpoint:** `POST /analyze`

**Request Body:**
```json
{
  "url": "https://elpais.com/internacional",
  "medio": "El País",
  "seccion": "Internacional",
  "area_geografica": "ESPAÑA",
  "tipo_medio": "diario",
  "frecuencia_minutos": 60,
  "rss_url": "https://elpais.com/internacional/rss"
}
```

**Response:**
```json
{
  "url": "https://elpais.com/internacional",
  "domain": "elpais.com",
  "strategy": "RSS",
  "confidence": 0.98,
  "rss_url": "https://elpais.com/internacional/rss",
  "selectors": null,
  "needs_javascript": false,
  "url_patterns": [],
  "sample_articles": [],
  "from_cache": false,
  "medio": "El País",
  "seccion": "Internacional",
  "area_geografica": "ESPAÑA",
  "tipo_medio": "diario"
}
```

### 3. Generate Spider

Generate a new spider based on analysis results.

**Endpoint:** `POST /generate`

**Request Body:**
```json
{
  "medio": "El País",
  "seccion": "Internacional",
  "area_geografica": "ESPAÑA",
  "tipo_medio": "diario",
  "url": "https://elpais.com/internacional",
  "frecuencia_minutos": 60,
  "comentarios": "Spider para noticias internacionales"
}
```

**Response:**
```json
{
  "spider_name": "el_pais_internacional",
  "file_path": "/src/module_scraper/scraper_core/spiders/el_pais_internacional.py",
  "code": "# -*- coding: utf-8 -*-\n...",
  "analysis_result": {
    "strategy": "RSS",
    "confidence": 0.98,
    "rss_url": "https://elpais.com/internacional/rss"
  }
}
```

### 4. Check Duplicate

Check if a spider already exists for a medio/seccion combination.

**Endpoint:** `POST /check-duplicate`

**Request Body:**
```json
{
  "medio": "El País",
  "seccion": "Internacional"
}
```

**Response:**
```json
{
  "exists": true,
  "spider_name": "el_pais_internacional",
  "file_path": "/src/module_scraper/scraper_core/spiders/el_pais_internacional.py",
  "similar_spiders": ["el_pais_deportes", "el_pais_economia"],
  "message": "Spider already exists"
}
```

## Valid Values

### area_geografica
```
GLOBAL, ESPAÑA, MEXICO, ARGENTINA, COLOMBIA, CHILE, PERU, VENEZUELA, 
ECUADOR, BOLIVIA, PARAGUAY, URUGUAY, BRASIL, COSTA_RICA, PANAMA, 
GUATEMALA, HONDURAS, EL_SALVADOR, NICARAGUA, REPUBLICA_DOMINICANA, 
PUERTO_RICO, CUBA, USA, CANADA, EUROPA, ASIA, AFRICA, OCEANIA
```

### tipo_medio
- `diario`
- `revista`
- `agencia`