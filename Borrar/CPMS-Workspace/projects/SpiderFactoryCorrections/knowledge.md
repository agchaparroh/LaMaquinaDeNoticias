# Base de Conocimiento - Spider Factory Corrections

## 🚨 INFORMACIÓN CRÍTICA - LEER PRIMERO

### Arquitectura Docker/NGINX - NO MODIFICAR

```yaml
# ESTAS CONFIGURACIONES SON SAGRADAS - NO CAMBIAR:
spider_factory_backend:
  # NO exponer puerto 8000 externamente
  # NO cambiar nombre del servicio
  # Puerto interno SIEMPRE 8000
  environment:
    - API_PORT=8000
  networks:
    - lamacquina_network  # NO cambiar nombre de red
```

**Rutas NGINX (NO cambiar):**
```
/spider-factory/api/* → http://spider_factory_backend:8000/*
/spider-factory/ws/* → ws://spider_factory_backend:8000/ws/*
```

**Testing SIEMPRE a través de NGINX:**
```bash
# ✅ CORRECTO
curl http://localhost/spider-factory/api/analyze

# ❌ INCORRECTO - Nunca directo al backend
curl http://localhost:8000/analyze
```

### Retrocompatibilidad Obligatoria

**El frontend actual espera estos campos - NO ROMPER:**
```python
# AnalysisRequest actual
{
    "url": "https://example.com",
    "name": "Example Site"  # Campo legacy - mantener
}

# GenerateSpiderRequest actual
{
    "spider_name": "example_spider",  # Campo legacy - mantener
    "analysis_result": {...}
}
```

**Estrategia de migración:**
1. Fase 1: Agregar campos nuevos como OPCIONALES
2. Fase 2: Frontend actualiza para enviar nuevos campos
3. Fase 3: Campos viejos se vuelven opcionales
4. Fase 4: Deprecar campos viejos (meses después)

## 📋 Decisiones Clave del Plan Original

### Nomenclatura de Spiders

**SIEMPRE `{medio}_{seccion}` en snake_case:**
```python
# ✅ CORRECTO
"el_pais_internacional"
"la_nacion_economia"
"bbc_mundo_tecnologia"

# ❌ INCORRECTO
"elpais"
"spider_noticias"
"internacional_elpais"
```

### Directorio de Salida

**OBLIGATORIO:**
```python
SPIDER_OUTPUT_PATH = "/src/module_scraper/scraper_core/spiders/"
# NO a src/spider_factory/output/
# NO a /tmp/spiders/
```

### Campos Obligatorios en Items

**TODOS los spiders deben incluir:**
```python
item['url'] = response.url
item['titular'] = title  # NO 'titulo'
item['medio'] = "{{ medio }}"
item['medio_url_principal'] = "https://{{ domain }}"
item['area_geografica'] = "{{ area_geografica }}"
item['tipo_medio'] = "{{ tipo_medio }}"  # diario|revista|agencia
item['seccion'] = "{{ seccion }}"
item['fecha_publicacion'] = parsed_date
item['contenido_texto'] = clean_text
item['contenido_html'] = raw_html
item['fuente'] = self.name
item['metadata'] = {
    'spider_type': 'rss|scraping|playwright',
    'extraction_method': method_used,
    'section_filter': 'applied|none',
}
```

### Áreas Geográficas Válidas

**SOLO estas 28 opciones:**
```python
AREAS_GEOGRAFICAS_VALIDAS = [
    # Regiones
    'HISPANIDAD', 'HISPANOAMERICA', 'CENTROAMERICA', 'CARIBE_HISPANO',
    'SUDAMERICA', 'TERRITORIOS_OCUPADOS', 'DIASPORA_HISPANA_USA',
    'GLOBAL', 'PAISES_NO_HISPANOS',
    
    # Países
    'ARGENTINA', 'BOLIVIA', 'CHILE', 'COLOMBIA', 'COSTA_RICA',
    'CUBA', 'ECUADOR', 'EL_SALVADOR', 'ESPAÑA', 'FILIPINAS',
    'GUATEMALA', 'GUINEA_ECUATORIAL', 'HONDURAS', 'MÉXICO',
    'NICARAGUA', 'PANAMÁ', 'PARAGUAY', 'PERÚ', 'PUERTO_RICO',
    'REPÚBLICA_DOMINICANA', 'SAHARA_OCCIDENTAL', 'URUGUAY', 'VENEZUELA'
]
```

### Flujo de Decisión para Análisis

```
1. ¿Tiene RSS? → Usar RSS (0 requests, <5s)
2. ¿Está en cache? → Usar cache (0 requests, <2s)
3. ¿Hay patrón conocido? → Aplicar patrón (0 requests, <2s)
4. Análisis con Firecrawl → (1 request, ~20s)
```

### KPIs de Tiempo

- **RSS**: < 5 segundos
- **Primera vez**: ~20 segundos
- **Con cache**: < 2 segundos
- **Reducción vs manual**: 97% (20 min → 20s)

## 🛠️ Patrones y Convenciones

### Estructura Redis

```python
# Patrones por dominio
"patterns:{dominio}" → {
    "internacional": '{"strategy": "scraping", "selectors": {...}}',
    "economia": '{"strategy": "scraping", "selectors": {...}}',
    "area_geografica": "ESPAÑA",
    "tipo_medio": "diario",
    "comentarios": "Actualiza por las mañanas"
}

# Cache de análisis
"analysis:{md5_hash}" → {resultado}  # TTL: 7 días

# Contadores de uso
"pattern_usage" → sorted set
```

### Validación con Pydantic

```python
from pydantic import BaseModel, validator, Field
from typing import Literal, Optional

class BatchSite(BaseModel):
    medio: str = Field(..., min_length=1, max_length=100)
    seccion: str = Field(..., min_length=1, max_length=50)
    url: HttpUrl
    area_geografica: str
    tipo_medio: Literal["diario", "revista", "agencia"]
    frecuencia_minutos: Optional[int] = Field(60, ge=5, le=1440)
    
    @validator('area_geografica')
    def validate_area(cls, v):
        if v not in AREAS_GEOGRAFICAS_VALIDAS:
            raise ValueError(f"Área geográfica inválida: {v}")
        return v
    
    @validator('medio', 'seccion')
    def clean_names(cls, v):
        # Remover caracteres especiales
        return re.sub(r'[^\w\s-]', '', v).strip()
```

### Logging con Loguru

```python
from loguru import logger

# Configuración estándar
logger.add(
    "logs/spider_factory_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}"
)

# Uso
logger.info(f"Generando spider: {medio}_{seccion}")
logger.error(f"Error en análisis: {e}", exc_info=True)
logger.debug(f"Cache hit para: {url}")
```

### Manejo de Errores

```python
# Patrón estándar para endpoints
@app.post("/api/analyze")
async def analyze_site(request: AnalysisRequest):
    try:
        # Validación entrada
        if not request.url:
            raise HTTPException(400, "URL requerida")
        
        # Lógica
        result = await analyzer.analyze(request)
        
        # Log éxito
        logger.info(f"Análisis exitoso: {request.url}")
        return result
        
    except ValidationError as e:
        logger.warning(f"Validación falló: {e}")
        raise HTTPException(400, str(e))
    
    except FirecrawlError as e:
        logger.error(f"Firecrawl error: {e}")
        raise HTTPException(503, "Servicio temporalmente no disponible")
    
    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
        raise HTTPException(500, "Error interno del servidor")
```

## 📝 Comandos Útiles

### Desarrollo Local

```bash
# Instalar dependencias
cd src/spider_factory
pip install -r requirements.txt

# Verificar sintaxis
python -m py_compile src/*.py

# Ejecutar tests
pytest tests/ -v --cov=src

# Formatear código
black src/ tests/

# Lint
flake8 src/ --max-line-length=100

# Type checking
mypy src/ --ignore-missing-imports
```

### Docker y Testing

```bash
# Build imagen
docker-compose build spider_factory_backend

# Ver logs
docker-compose logs -f spider_factory_backend

# Ejecutar shell en container
docker-compose exec spider_factory_backend /bin/bash

# Test a través de NGINX
curl -X POST http://localhost/spider-factory/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","name":"test"}'

# WebSocket test
pip install websocket-client
wscat -c ws://localhost/spider-factory/ws/test-session
```

### Redis

```bash
# Conectar a Redis
docker-compose exec redis redis-cli

# Ver todas las claves
KEYS *

# Ver patrones
HGETALL patterns:elpais.com

# Ver cache
GET analysis:abc123

# Limpiar cache (cuidado!)
FLUSHDB

# Monitor en tiempo real
MONITOR
```

### Validación de Spiders

```bash
# Validar sintaxis de spider generado
cd /src/module_scraper
scrapy check el_pais_internacional

# Ejecutar spider localmente
scrapy crawl el_pais_internacional -L INFO

# Ver items generados
scrapy crawl el_pais_internacional -L ERROR -o test.json
```

## 🐛 Problemas Comunes y Soluciones

### Error: "Connection refused" a Redis

```python
# Problema: Redis no está levantado o mal configurado
# Solución:
docker-compose up -d redis
# Verificar en config.py:
REDIS_HOST = os.getenv("REDIS_HOST", "redis")  # NO "localhost" en Docker
```

### Error: "ScrapingStrategy not found"

```python
# Problema: Import incorrecto (bug conocido)
# Cambiar:
from models import ScrapingStrategy  # ❌
# Por:
from models import AnalysisStrategy  # ✅
```

### Error: "Permission denied" al escribir spider

```python
# Problema: Permisos en directorio de salida
# Solución en Dockerfile:
RUN mkdir -p /src/module_scraper/scraper_core/spiders && \
    chown -R appuser:appuser /src/module_scraper
```

### WebSocket no conecta

```nginx
# Problema: Headers faltantes en NGINX
# Agregar en nginx.conf:
location /spider-factory/ws {
    proxy_pass http://spider_factory_backend:8000/ws;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### Spiders generados sin formato

```python
# Problema: Black no instalado o falla
# Solución con try/except:
try:
    import black
    formatted_code = black.format_str(code, mode=black.Mode())
except Exception as e:
    logger.warning(f"No se pudo formatear: {e}")
    formatted_code = code  # Usar sin formato
```

## 🔧 Snippets Reutilizables

### Validación de Área Geográfica

```python
def validate_area_geografica(area: str) -> str:
    """Valida y normaliza área geográfica."""
    area_upper = area.upper().replace(" ", "_")
    if area_upper not in AREAS_GEOGRAFICAS_VALIDAS:
        sugerencias = difflib.get_close_matches(
            area_upper, AREAS_GEOGRAFICAS_VALIDAS, n=3
        )
        raise ValueError(
            f"Área '{area}' no válida. "
            f"¿Quisiste decir: {', '.join(sugerencias)}?"
        )
    return area_upper
```

### Cache con TTL

```python
async def get_or_set_cache(key: str, func, ttl: int = 604800):
    """Get from cache or compute and store."""
    # Intentar obtener de cache
    cached = await redis.get(f"cache:{key}")
    if cached:
        logger.debug(f"Cache hit: {key}")
        return json.loads(cached)
    
    # Computar y guardar
    logger.debug(f"Cache miss: {key}")
    result = await func()
    await redis.setex(
        f"cache:{key}",
        ttl,
        json.dumps(result)
    )
    return result
```

### Generación de Spider Name

```python
def generate_spider_name(medio: str, seccion: str) -> str:
    """Genera nombre de spider en formato estándar."""
    # Limpiar y normalizar
    medio_clean = re.sub(r'[^\w\s]', '', medio).strip()
    seccion_clean = re.sub(r'[^\w\s]', '', seccion).strip()
    
    # Convertir a snake_case
    medio_snake = medio_clean.lower().replace(' ', '_')
    seccion_snake = seccion_clean.lower().replace(' ', '_')
    
    return f"{medio_snake}_{seccion_snake}"
```

### Rate Limiting con SlowAPI

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/analyze")
@limiter.limit("10/minute")
async def analyze_site(request: Request, data: AnalysisRequest):
    # Lógica del endpoint
    pass
```

### Verificación de Spider Duplicado

```python
async def check_spider_exists(medio: str, seccion: str) -> Dict:
    """Verifica si ya existe un spider."""
    spider_name = generate_spider_name(medio, seccion)
    file_path = Path(SPIDER_OUTPUT_PATH) / f"{spider_name}.py"
    
    if file_path.exists():
        # Leer primera línea para ver fecha
        with open(file_path, 'r') as f:
            first_lines = f.readlines()[:10]
            generation_date = None
            for line in first_lines:
                if "Fecha:" in line:
                    generation_date = line.split("Fecha:")[1].strip()
                    break
        
        return {
            "exists": True,
            "spider_name": spider_name,
            "file_path": str(file_path),
            "generation_date": generation_date,
            "message": f"Spider {spider_name} ya existe"
        }
    
    return {
        "exists": False,
        "spider_name": spider_name,
        "message": "Spider no existe, puede crearse"
    }
```

## 🔍 Queries Redis Útiles

```bash
# Listar todos los dominios con patrones
redis-cli --scan --pattern "patterns:*"

# Ver patrones más usados
redis-cli zrevrange pattern_usage 0 9 WITHSCORES

# Contar análisis en cache
redis-cli --scan --pattern "analysis:*" | wc -l

# Ver metadata de un dominio
redis-cli hget patterns:elpais.com area_geografica

# Buscar patrones por tipo de medio
for key in $(redis-cli --scan --pattern "patterns:*"); do
  tipo=$(redis-cli hget $key tipo_medio)
  if [ "$tipo" = "diario" ]; then
    echo $key
  fi
done
```

## 📊 Métricas para Monitorear

### KPIs Principales

1. **Tiempo de generación por estrategia**
   - RSS: objetivo < 5s
   - Cache: objetivo < 2s
   - Primera vez: objetivo ~20s

2. **Cache hit rate**
   - Objetivo: > 70% después de 1 semana

3. **Precisión de spiders**
   - Objetivo: > 90% de artículos correctos

4. **Adopción**
   - Objetivo: > 80% de medios usando el sistema

### Queries de Monitoreo

```python
async def get_system_health():
    """Obtiene métricas de salud del sistema."""
    return {
        "cache_size": await redis.dbsize(),
        "patterns_count": await redis.hlen("patterns:*"),
        "avg_generation_time": await redis.get("metrics:avg_time"),
        "total_spiders_generated": await redis.get("metrics:total"),
        "last_24h_requests": await redis.get("metrics:requests_24h"),
        "cache_hit_rate": await calculate_hit_rate(),
        "active_websockets": websocket_manager.active_count(),
        "redis_memory": await redis.info("memory"),
    }
```

## 🚀 Checklist Pre-Deployment

- [ ] Todos los tests pasando (coverage > 80%)
- [ ] Sin errores de import o sintaxis
- [ ] Documentación actualizada
- [ ] Campos legacy mantenidos para compatibilidad
- [ ] Testing completo a través de NGINX
- [ ] Redis con connection pooling configurado
- [ ] Logs rotando correctamente
- [ ] Métricas expuestas en /metrics
- [ ] Rate limiting activo
- [ ] Validación de spiders existentes pasada
- [ ] Frontend sigue funcionando sin cambios
- [ ] KPIs de tiempo cumplidos
- [ ] Backup de spiders existentes realizado

## 📚 Referencias

- Plan original: `SPIDER_FACTORY_2.0_PLAN_DETALLADO.md`
- Plan de corrección: `PLAN_CORRECCION_BACKEND.md`
- Documentación FastAPI: https://fastapi.tiangolo.com/
- Documentación Pydantic v2: https://docs.pydantic.dev/latest/
- Redis commands: https://redis.io/commands/
- Scrapy items: https://docs.scrapy.org/en/latest/topics/items.html

---

**RECORDATORIO FINAL:** La arquitectura Docker/NGINX es sagrada. Mantener retrocompatibilidad es crítico. Testear siempre a través de NGINX, nunca directo al backend.