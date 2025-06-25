# Guía de Integración: Spider Factory 2.0 con La Máquina de Noticias

## 📋 Cambios Necesarios para Integración

### 1. **Configuración de Puertos**

Para evitar conflictos con el sistema principal, Spider Factory debe usar:

```env
# Backend API
SPIDER_FACTORY_API_PORT=8005  # (antes 8000)

# Frontend
SPIDER_FACTORY_FRONTEND_PORT=3002  # (antes 3000)

# Redis (usar el compartido del sistema)
REDIS_HOST=redis
REDIS_PORT=6379
```

### 2. **Docker Compose Integrado**

Agregar al `docker-compose.yml` principal:

```yaml
# Spider Factory Backend
spider_factory_backend:
  build:
    context: ./src/spider_factory
    dockerfile: Dockerfile
  container_name: lamacquina_spider_factory_backend
  ports:
    - "8005:8000"
  environment:
    - REDIS_HOST=redis
    - REDIS_PORT=6379
    - FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY}
  volumes:
    - ./src/spider_factory/generated_spiders:/app/generated_spiders
    - ./src/module_scraper/spiders:/app/output_spiders
  networks:
    - lamacquina_network
  depends_on:
    - redis
    
# Spider Factory Frontend
spider_factory_frontend:
  build:
    context: ./src/module_spider_factory_frontend
    dockerfile: Dockerfile
  container_name: lamacquina_spider_factory_frontend
  ports:
    - "3002:80"
  environment:
    - VITE_API_URL=http://spider_factory_backend:8000
    - VITE_WS_URL=ws://spider_factory_backend:8000
  networks:
    - lamacquina_network
  depends_on:
    - spider_factory_backend
```

### 3. **Adaptación de Templates**

Los templates de Spider Factory deben generar spiders compatibles con `BaseArticleSpider`:

```python
# En los templates, cambiar:
from scrapy import Spider

# Por:
from module_scraper.spiders.base_article_spider import BaseArticleSpider
```

### 4. **Variables de Entorno Compartidas**

Agregar al `.env` principal:

```env
# Spider Factory
FIRECRAWL_API_KEY=your_api_key_here
SPIDER_FACTORY_MAX_CONCURRENT_ANALYSES=5
SPIDER_FACTORY_ANALYSIS_TIMEOUT=30
```

### 5. **Configuración Nginx**

Agregar a `nginx_reverse_proxy/default.conf`:

```nginx
# Spider Factory API
location /spider-factory/api/ {
    proxy_pass http://spider_factory_backend:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# Spider Factory Frontend
location /spider-factory/ {
    proxy_pass http://spider_factory_frontend/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# WebSocket for Spider Factory
location /spider-factory/ws/ {
    proxy_pass http://spider_factory_backend:8000/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### 6. **Script de Migración de Spiders**

Crear `src/spider_factory/migrate_spider.py`:

```python
"""
Script para adaptar spiders generados al formato de module_scraper
"""
import os
import re
from pathlib import Path

def migrate_spider(input_path: str, output_path: str):
    """Adapta un spider generado al formato de module_scraper"""
    
    with open(input_path, 'r') as f:
        content = f.read()
    
    # Cambiar imports
    content = re.sub(
        r'from scrapy import Spider',
        'from module_scraper.spiders.base_article_spider import BaseArticleSpider',
        content
    )
    
    # Cambiar clase base
    content = re.sub(
        r'class (\w+)\(Spider\)',
        r'class \1(BaseArticleSpider)',
        content
    )
    
    # Agregar configuración de Supabase
    content = re.sub(
        r'custom_settings = {',
        '''custom_settings = {
        'ITEM_PIPELINES': {
            'module_scraper.pipelines.SupabasePipeline': 300,
        },''',
        content
    )
    
    with open(output_path, 'w') as f:
        f.write(content)
```

### 7. **Flujo de Trabajo Integrado**

1. Usuario genera spider en Spider Factory
2. Spider se guarda en `generated_spiders/`
3. Script de migración adapta el spider
4. Spider migrado se copia a `module_scraper/spiders/`
5. Se despliega en Scrapyd automáticamente

### 8. **Autenticación y Permisos**

Spider Factory debe integrarse con el sistema de autenticación existente:

- Usar los mismos tokens JWT
- Respetar roles y permisos
- Compartir sesiones de usuario

## 🚀 Pasos de Implementación

1. **Actualizar puertos** en archivos de configuración
2. **Modificar docker-compose.yml** principal
3. **Adaptar templates** de generación
4. **Crear script de migración**
5. **Configurar nginx** para ruteo
6. **Probar integración** completa

## 📝 Notas Importantes

- Spider Factory mantiene su autonomía pero se integra al ecosistema
- Los spiders generados son 100% compatibles con module_scraper
- Se comparte Redis para optimizar recursos
- La UI de Spider Factory es accesible desde el dashboard principal