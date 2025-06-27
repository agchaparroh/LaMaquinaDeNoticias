# PLAN DETALLADO DE CORRECCIÓN - BACKEND SPIDER FACTORY 2.0

## 📋 RESUMEN EJECUTIVO

Este plan detalla todas las correcciones necesarias para alinear el backend de Spider Factory con el plan original documentado en SPIDER_FACTORY_2.0_PLAN_DETALLADO.md. Se organiza por archivo y prioridad, con acciones específicas para cada componente.

---

## 🎯 OBJETIVOS PRINCIPALES

1. Alinear completamente con el plan original
2. Corregir todos los campos faltantes críticos
3. Implementar funcionalidades omitidas
4. Garantizar compatibilidad con La Máquina de Noticias
5. Preparar el sistema para producción

---

## 1. CORRECCIONES EN MODELOS Y ESTRUCTURAS DE DATOS

### 📄 **models.py**

#### 1.1 Actualizar `GenerateSpiderRequest` (líneas ~102-168)
**Cambios necesarios:**
- Agregar campo `seccion: str` (OBLIGATORIO)
- Agregar campo `area_geografica: str` (OBLIGATORIO)
- Agregar campo `tipo_medio: Literal["diario", "revista", "agencia"]` (OBLIGATORIO)
- Agregar campo `frecuencia_minutos: Optional[int] = 60`
- Cambiar `spider_name` para que se genere automáticamente como `{medio}_{seccion}`
- Eliminar validación manual de `spider_name` pattern
- Agregar campo `comentarios: Optional[str] = None`

#### 1.2 Crear nuevo modelo `DuplicateCheckRequest`
**Estructura necesaria:**
- `medio: str` - Nombre del medio
- `seccion: str` - Sección específica
- Lógica para formar el nombre `{medio}_{seccion}` internamente
- Validación de caracteres permitidos

#### 1.3 Actualizar `AnalysisRequest` (líneas ~50-75)
**Cambios necesarios:**
- Renombrar `section_name` a `seccion`
- Agregar `medio: str`
- Agregar `area_geografica: str`
- Agregar `tipo_medio: str`
- Agregar `rss_url: Optional[HttpUrl] = None`

### 📄 **batch_processor.py**

#### 1.4 Redefinir completamente `BatchSite` (líneas ~25-31)
**Nueva estructura según plan:**
```python
class BatchSite(BaseModel):
    medio: str
    seccion: str  
    url: HttpUrl
    area_geografica: str
    tipo_medio: Literal["diario", "revista", "agencia"]
    frecuencia_minutos: Optional[int] = 60
    rss_url: Optional[HttpUrl] = None
    comentarios: Optional[str] = None
```

#### 1.5 Actualizar procesamiento CSV (líneas ~88-106)
**Cambios necesarios:**
- Cambiar `required_columns` a `['medio', 'seccion', 'url', 'area_geografica', 'tipo_medio']`
- Actualizar mapeo de columnas CSV
- Validar que `tipo_medio` sea uno de los valores permitidos
- Manejar `frecuencia_minutos` como entero opcional
- Procesar `rss_url` como URL válida o None
- Generar spider_name como `{medio}_{seccion}`

---

## 2. CORRECCIONES EN LÓGICA DE NEGOCIO

### 📄 **analyzer.py**

#### 2.1 Actualizar `AnalysisResult` para incluir metadata
**Agregar campos:**
- `area_geografica: str`
- `tipo_medio: str`
- `seccion: str`
- `medio: str`
- `comentarios: Optional[str]`
- `frecuencia_minutos: int`

#### 2.2 Modificar proceso de análisis
**Cambios en método `analyze()`:**
- Aceptar y propagar metadata del medio
- Incluir metadata en resultado de análisis
- Guardar metadata cuando se cachea resultado
- Si tiene RSS, no hacer análisis con Firecrawl

#### 2.3 Implementar decisión inteligente según plan
**Flujo de decisión:**
1. ¿Tiene RSS? → Estrategia RSS directa
2. ¿Está en cache? → Usar cache (0 requests)
3. ¿Hay patrón conocido? → Aplicar patrón (0 requests)
4. Si no → Análisis con Firecrawl (1 request)

### 📄 **patterns.py**

#### 2.4 Rediseñar estructura de `Pattern`
**Nuevos campos necesarios:**
- `area_geografica: str`
- `tipo_medio: str`
- `comentarios: Optional[str]`
- `secciones: Dict[str, Dict]` para múltiples secciones por dominio
- `ultimo_uso: datetime`
- `contador_exitos: int`
- `contador_fallos: int`

#### 2.5 Implementar métodos faltantes en `PatternStorage`
**Métodos a crear:**
```python
async def search_by_domain(self, domain: str) -> List[Pattern]
async def search_by_strategy(self, strategy: AnalysisStrategy) -> List[Pattern]
async def get_all_patterns(self, limit: int = 100) -> List[Pattern]
async def save_domain_metadata(self, domain, area_geografica, tipo_medio, comentarios)
async def get_domain_metadata(self, domain) -> Dict
async def save_section_pattern(self, domain, section, pattern)
async def increment_usage_counter(self, domain, section)
async def get_popular_patterns(self, limit: int = 10) -> List[Pattern]
```

#### 2.6 Actualizar estructura de claves Redis
**Nuevo esquema según plan:**
```
# Patrones por dominio con metadata
"patterns:{dominio}" → {
    "internacional": '{"strategy": "scraping", "selectors": {...}}',
    "economia": '{"strategy": "scraping", "selectors": {...}}',
    "area_geografica": "ESPAÑA",
    "tipo_medio": "diario",
    "comentarios": "Actualiza por las mañanas"
}

# Contadores de uso
"pattern_usage" → {
    "elpais.com:internacional": 45,
    "lanacion.com.ar:economia": 23
}

# Cache de análisis con TTL
"analysis:{md5_hash}" → {
    "strategy": "scraping",
    "selectors": {...},
    "confidence": 0.8,
    "timestamp": "2024-12-16T10:00:00"
}
TTL: 7 días (604800 segundos)
```

### 📄 **generator.py**

#### 2.7 Actualizar método `generate_spider()`
**Cambios necesarios:**
- Aceptar parámetros: medio, seccion, area_geografica, tipo_medio, frecuencia_minutos
- Generar `spider_name` como `{medio}_{seccion}` (snake_case)
- Pasar `generation_date` al contexto: `datetime.now().strftime('%Y-%m-%d %H:%M:%S')`
- Calcular `base_url` desde el dominio
- Cambiar directorio de salida a `/src/module_scraper/scraper_core/spiders/`
- Agregar todos los campos al contexto del template

#### 2.8 Implementar formateo automático con Black
**Después de generar código:**
```python
try:
    import black
    formatted_code = black.format_str(spider_code, mode=black.Mode())
except:
    # Si Black no está disponible, usar código sin formatear
    formatted_code = spider_code
```

#### 2.9 Agregar validación de spider generado
**Validaciones:**
- Sintaxis Python correcta
- Campos obligatorios presentes
- Nombre único (no sobrescribir existente sin confirmación)

---

## 3. CORRECCIONES EN TEMPLATES

### 📄 **templates/spiders/base_spider.j2** (CREAR SI NO EXISTE)

#### 3.1 Crear template base con campos comunes
**Contenido necesario:**
- Header con comentario de identificación
- Imports comunes
- Configuración scrapy-crawl-once
- Campos obligatorios del item

### 📄 **templates/spiders/rss_spider.j2**

#### 3.2 Actualizar para incluir campos obligatorios
**En el yield del item:**
```python
item['url'] = entry.link
item['titular'] = entry.title  # NO "titulo"
item['medio'] = "{{ medio }}"
item['medio_url_principal'] = "https://{{ domain }}"
item['area_geografica'] = "{{ area_geografica }}"
item['tipo_medio'] = "{{ tipo_medio }}"
item['seccion'] = "{{ seccion }}"
item['fecha_publicacion'] = # parsear fecha
item['contenido_texto'] = # extraer texto
item['contenido_html'] = # HTML completo
item['fuente'] = self.name
item['metadata'] = {
    'spider_type': 'rss',
    'extraction_method': 'feedparser',
    'section_filter': 'none',
}
```

#### 3.3 Cambiar nomenclatura del spider
```python
name = "{{ medio|lower|replace(' ', '_') }}_{{ seccion|lower|replace(' ', '_') }}"
```

#### 3.4 Agregar configuración completa
```python
custom_settings = {
    # Configuración existente...
    'CRAWL_ONCE_ENABLED': True,
    'CRAWL_ONCE_PATH': f'.scrapy/crawl_once/{{ medio|lower }}_{{ seccion|lower }}',
    'CRAWL_ONCE_DEFAULT': False,
    # Comentario para Scrapyd
    # SCHEDULE_FREQUENCY = {{ frecuencia_minutos }}
}
```

### 📄 **templates/spiders/scraping_spider.j2** y **playwright_spider.j2**

#### 3.5 Implementar método `_is_section_article()`
```python
def _is_section_article(self, url: str) -> bool:
    """Valida si la URL pertenece a la sección objetivo"""
    excluded_patterns = [
        r'/archivo/', r'/hemeroteca/', r'/newsletter/',
        r'/multimedia/', r'/video/', r'/podcast/',
        r'/tags?/', r'/autor/', r'/busca[rd]?/',
    ]
    for pattern in excluded_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return False
    
    # Verificar que pertenece a la sección
    section_pattern = re.compile(r'/{{ seccion|lower }}/'.replace(' ', '[-_]?'))
    return bool(section_pattern.search(url))
```

#### 3.6 Agregar todos los campos obligatorios
**Igual que en RSS spider, pero adaptado al contexto**

#### 3.7 Agregar header de identificación
```python
"""
Spider generado automáticamente por Spider Factory 2.0
Medio: {{ medio }}
Sección: {{ seccion }}
Fecha: {{ generation_date }}
Estrategia: {{ strategy }}

GENERADO AUTOMÁTICAMENTE - NO EDITAR MANUALMENTE
Los cambios manuales se perderán en la próxima generación
"""
```

---

## 4. CORRECCIONES EN API

### 📄 **api.py**

#### 4.1 Corregir error de importación (línea ~248)
**Cambiar:**
```python
# DE:
strategy=ScrapingStrategy(request.analysis_result.get("strategy", "scraping")),
# A:
strategy=AnalysisStrategy(request.analysis_result.get("strategy", "scraping")),
```

#### 4.2 Implementar endpoint `/api/check-duplicate`
**Nuevo endpoint:**
```python
@app.post("/api/check-duplicate", response_model=DuplicateCheckResponse)
async def check_duplicate(request: DuplicateCheckRequest):
    """Verifica si un spider medio_seccion ya existe"""
    spider_name = f"{request.medio.lower().replace(' ', '_')}_{request.seccion.lower().replace(' ', '_')}"
    file_path = Path(settings.SPIDER_OUTPUT_PATH) / f"{spider_name}.py"
    
    exists = file_path.exists()
    similar_spiders = []  # Buscar spiders similares
    
    return DuplicateCheckResponse(
        exists=exists,
        spider_name=spider_name if exists else None,
        file_path=str(file_path) if exists else None,
        similar_spiders=similar_spiders,
        message="Spider ya existe" if exists else "Nombre disponible"
    )
```

#### 4.3 Actualizar endpoint `/generate`
**Modificaciones necesarias:**
- Recibir campos: medio, seccion, area_geografica, tipo_medio, frecuencia_minutos
- Validar todos los campos obligatorios
- Generar spider_name automáticamente
- Pasar toda la metadata al generador

#### 4.4 Actualizar endpoint `/batch/analyze`
**Cambios en procesamiento:**
- Validar nuevo formato CSV
- Procesar campos obligatorios
- Generar nombres como `{medio}_{seccion}`
- Limitar a 100 items máximo
- Implementar procesamiento paralelo (5-10 simultáneos)

#### 4.5 Agregar validaciones y límites
**Implementar:**
- Rate limiting: máximo 10 requests por minuto por IP
- Tamaño máximo de batch: 100 items
- Timeout para análisis: 30 segundos
- Validación de URLs válidas

### 📄 **websocket_manager.py**

#### 4.6 Implementar método `send_to_session()`
```python
async def send_to_session(self, session_id: str, data: Dict[str, Any]):
    """Envía mensaje a todos los websockets de una sesión"""
    if session_id in self.active_connections:
        for websocket in self.active_connections[session_id]:
            try:
                await websocket.send_json(data)
            except:
                # Manejar desconexión
                await self.disconnect(websocket, session_id)
```

---

## 5. CORRECCIONES EN CONFIGURACIÓN

### 📄 **config.py**

#### 5.1 Corregir referencias de variables (líneas 213, 226)
**Cambiar todas las referencias:**
- DE: `config.api_host` → A: `settings.api_host`
- DE: `print(f"Spider Factory Config: {config}")` → A: `print(f"Spider Factory Config: {settings}")`

#### 5.2 Agregar configuraciones faltantes
```python
# Cache
CACHE_TTL_DAYS = 7  # TTL de cache en días
CACHE_TTL_SECONDS = CACHE_TTL_DAYS * 86400  # 604800 segundos

# Batch processing
MAX_BATCH_SIZE = 100
CONCURRENT_REQUESTS = 10
BATCH_TIMEOUT = 300  # 5 minutos

# Paths
SPIDER_OUTPUT_PATH = str(Path(BASE_DIR).parent.parent / "module_scraper" / "scraper_core" / "spiders")

# Rate limiting
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW = 60  # segundos

# Redis connection pool
REDIS_MAX_CONNECTIONS = 50
```

#### 5.3 Agregar validación de configuración al iniciar
```python
def validate_config():
    """Valida configuración al iniciar"""
    # Verificar API key de Firecrawl
    if not FIRECRAWL_API_KEY:
        logger.warning("Firecrawl API key no configurada")
    
    # Verificar directorio de salida
    if not Path(SPIDER_OUTPUT_PATH).exists():
        logger.error(f"Directorio de spiders no existe: {SPIDER_OUTPUT_PATH}")
    
    # Verificar Redis
    try:
        redis_client = get_redis_client()
        redis_client.ping()
    except:
        logger.error("No se puede conectar a Redis")
```

---

## 6. IMPLEMENTACIONES NUEVAS REQUERIDAS

### 6.1 Sistema de logs con Loguru
**Crear archivo: `logging_config.py`**
```python
from loguru import logger
import sys

def setup_logging():
    # Remover handler por defecto
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}",
        level="INFO"
    )
    
    # File handler con rotación
    logger.add(
        "logs/spider_factory_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="7 days",
        level="DEBUG"
    )
    
    # Error file
    logger.add(
        "logs/errors_{time:YYYY-MM-DD}.log",
        level="ERROR",
        rotation="00:00",
        retention="30 days"
    )
```

### 6.2 Sistema de métricas
**Crear archivo: `metrics.py`**
```python
class Metrics:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def increment_spider_generated(self, medio, seccion, strategy):
        # Incrementar contadores
        
    async def record_generation_time(self, tiempo):
        # Guardar tiempo de generación
        
    async def record_cache_hit(self, hit: bool):
        # Registrar hit/miss de cache
        
    async def get_stats(self) -> Dict:
        # Retornar estadísticas
```

### 6.3 Sistema de notificaciones
**Crear archivo: `notifications.py`**
```python
class NotificationSystem:
    async def notify_spider_failure(self, spider_name, error):
        # Notificar fallo repetido
        
    async def notify_structure_change(self, medio, cambios):
        # Alertar cambios en estructura
        
    async def send_slack(self, message):
        # Integración Slack opcional
```

### 6.4 Cache warming
**Agregar a `patterns.py`:**
```python
async def warm_cache(self):
    """Pre-carga patrones populares al iniciar"""
    popular_patterns = await self.get_popular_patterns(limit=20)
    for pattern in popular_patterns:
        # Cargar en memoria
        logger.info(f"Cache warmed: {pattern.domain}")
```

---

## 7. MIGRACIONES Y COMPATIBILIDAD

### 7.1 Completar `migrate_spider.py`
**Funcionalidad necesaria:**
```python
class SpiderMigrator:
    def detect_spider_type(self, file_path):
        # Detectar si es RSS, scraping o playwright
        
    def backup_spider(self, file_path):
        # Crear backup antes de migrar
        
    def migrate_to_v2(self, file_path, metadata):
        # Agregar campos obligatorios faltantes
        # Preservar configuraciones custom
        # Actualizar nomenclatura
        
    def validate_migration(self, file_path):
        # Verificar que tiene todos los campos
```

### 7.2 Script de validación
**Crear archivo: `validate_spiders.py`**
```python
def validate_all_spiders():
    """Valida todos los spiders existentes"""
    # Listar todos los .py en directorio
    # Verificar campos obligatorios
    # Generar reporte
    
def generate_compatibility_report():
    """Genera reporte de compatibilidad"""
    # Spiders válidos
    # Spiders que necesitan actualización
    # Campos faltantes por spider
```

---

## 8. TESTING

### 8.1 Tests unitarios para analyzer.py
**Archivo: `tests/test_analyzer.py`**
- Mock de Firecrawl API
- Test de flujo de decisión (RSS/Cache/Patrón/Análisis)
- Test de guardado en cache
- Test de manejo de errores

### 8.2 Tests unitarios para generator.py
**Archivo: `tests/test_generator.py`**
- Test de generación con diferentes estrategias
- Test de nomenclatura {medio}_{seccion}
- Test de formateo con Black
- Test de validación de código

### 8.3 Tests unitarios para patterns.py
**Archivo: `tests/test_patterns.py`**
- Mock de Redis
- Test de guardado/recuperación de patrones
- Test de búsqueda por dominio/estrategia
- Test de contadores de uso

### 8.4 Tests de integración
**Archivo: `tests/test_integration.py`**
- Test de flujo completo: análisis → generación → guardado
- Test de procesamiento batch
- Test de WebSocket updates
- Test de compatibilidad con module_scraper

---

## 9. DOCUMENTACIÓN

### 9.1 Documentación OpenAPI
**Para cada endpoint agregar:**
```python
@app.post(
    "/api/check-duplicate",
    response_model=DuplicateCheckResponse,
    summary="Verifica duplicados de spiders",
    description="Verifica si ya existe un spider para el medio y sección especificados",
    responses={
        200: {"description": "Verificación completada"},
        400: {"description": "Datos inválidos"},
        500: {"description": "Error del servidor"}
    }
)
```

### 9.2 Ejemplos en cada endpoint
```python
class DuplicateCheckRequest(BaseModel):
    # ... campos ...
    
    class Config:
        schema_extra = {
            "example": {
                "medio": "El País",
                "seccion": "Internacional"
            }
        }
```

---

## 📅 CRONOGRAMA DE IMPLEMENTACIÓN

### Fase 1: Modelos y Estructuras
- [ ] Actualizar todos los modelos en models.py
- [ ] Corregir BatchSite en batch_processor.py
- [ ] Implementar validaciones de campos
- [ ] Crear modelos faltantes

### Fase 2: Templates y Generación
- [ ] Actualizar todos los templates con campos obligatorios
- [ ] Implementar nomenclatura {medio}_{seccion}
- [ ] Agregar scrapy-crawl-once
- [ ] Corregir generator.py
- [ ] Cambiar directorio de salida

### Fase 3: API y Endpoints
- [ ] Corregir errores de importación
- [ ] Implementar endpoint check-duplicate
- [ ] Actualizar generate con nuevos campos
- [ ] Actualizar batch processing
- [ ] Implementar WebSocket completo

### Fase 4: Cache y Patrones
- [ ] Rediseñar estructura de Pattern
- [ ] Implementar métodos faltantes
- [ ] Configurar TTL de 7 días
- [ ] Implementar cache warming
- [ ] Actualizar claves Redis

### Fase 5: Testing y Validación
- [ ] Escribir tests unitarios
- [ ] Tests de integración
- [ ] Validar compatibilidad
- [ ] Documentación completa
- [ ] Testing con datos reales

---

## 🎯 CRITERIOS DE ÉXITO

1. ✅ Todos los spiders incluyen campos obligatorios
2. ✅ Nomenclatura: `{medio}_{seccion}`
3. ✅ CSV formato: `medio,seccion,url,area_geografica,tipo_medio,frecuencia_minutos,rss_url`
4. ✅ Spiders en: `/src/module_scraper/scraper_core/spiders/`
5. ✅ Cache con TTL de 7 días
6. ✅ Metadata completa por dominio
7. ✅ Tests pasando al 100%
8. ✅ Compatible con La Máquina de Noticias
9. ✅ Documentación OpenAPI completa
10. ✅ Sin errores de importación o sintaxis

---

## 🚨 RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Incompatibilidad con spiders existentes | Alta | Alto | Script de migración automática |
| Cambios rompen el frontend | Media | Alto | Mantener retrocompatibilidad en API |
| Performance con batches grandes | Media | Medio | Límites y procesamiento asíncrono |
| Errores en templates | Baja | Alto | Tests exhaustivos de generación |

---

## 10. ÁREAS GEOGRÁFICAS Y VALIDACIONES

### 10.1 Lista oficial de áreas geográficas
**Definir constante en `config.py`:**
```python
AREAS_GEOGRAFICAS_VALIDAS = [
    'HISPANIDAD', 'HISPANOAMERICA', 'CENTROAMERICA', 'CARIBE_HISPANO',
    'SUDAMERICA', 'TERRITORIOS_OCUPADOS', 'DIASPORA_HISPANA_USA',
    'GLOBAL', 'PAISES_NO_HISPANOS',
    'ARGENTINA', 'BOLIVIA', 'CHILE', 'COLOMBIA', 'COSTA_RICA',
    'CUBA', 'ECUADOR', 'EL_SALVADOR', 'ESPAÑA', 'FILIPINAS',
    'GUATEMALA', 'GUINEA_ECUATORIAL', 'HONDURAS', 'MÉXICO',
    'NICARAGUA', 'PANAMÁ', 'PARAGUAY', 'PERÚ', 'PUERTO_RICO',
    'REPÚBLICA_DOMINICANA', 'SAHARA_OCCIDENTAL', 'URUGUAY', 'VENEZUELA'
]
```

### 10.2 Validación en modelos
**Agregar validación en `BatchSite` y otros modelos:**
```python
@validator('area_geografica')
def validate_area_geografica(cls, v):
    if v not in AREAS_GEOGRAFICAS_VALIDAS:
        raise ValueError(f"Área geográfica inválida. Debe ser una de: {', '.join(AREAS_GEOGRAFICAS_VALIDAS)}")
    return v
```

---

## 11. INTEGRACIÓN CON FIRECRAWL Y SCRAPYD

### 11.1 Uso específico de Firecrawl
**En `analyzer.py`, especificar el uso de los 3 formatos:**
```python
async def analyze_with_firecrawl(self, url: str) -> Dict:
    """
    Analiza sitio web obteniendo HTML, Markdown y screenshots en 1 request
    """
    response = await self.firecrawl_client.scrape({
        'url': url,
        'formats': ['html', 'markdown', 'screenshot'],
        'wait': 2000,  # Esperar 2 segundos para JavaScript
    })
    
    # Usar HTML para detectar selectores
    # Usar Markdown para preview de contenido
    # Usar screenshot para validación visual (opcional)
    return self._process_firecrawl_response(response)
```

### 11.2 Integración con Scrapyd
**Agregar comentarios en templates para scheduling:**
```python
# En cada template de spider:
"""
SCRAPYD CONFIGURATION:
Schedule: Every {{ frecuencia_minutos }} minutes
Project: lamaquina
Spider: {{ medio|lower }}_{{ seccion|lower }}
Arguments: -a max_items=100
"""
```

**Crear archivo `scrapyd_integration.py`:**
```python
def register_spider_in_scrapyd(spider_name: str, frecuencia_minutos: int):
    """Registra spider en Scrapyd para ejecución automática"""
    # POST a scrapyd:6800/schedule.json
    # con project=lamaquina, spider=spider_name, settings...
```

---

## 12. REDIS CONNECTION POOLING

### 12.1 Implementación completa del pooling
**En `config.py` o archivo separado `redis_pool.py`:**
```python
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

class RedisConnectionPool:
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_pool(self):
        if self._pool is None:
            self._pool = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                max_connections=50,  # Pool de 50 conexiones
                decode_responses=True
            )
        return self._pool
    
    async def get_client(self):
        pool = await self.get_pool()
        return redis.Redis(connection_pool=pool)
```

---

## 13. SISTEMA DE MÉTRICAS Y KPIs

### 13.1 KPIs de tiempo específicos
**Crear archivo `performance_metrics.py`:**
```python
class PerformanceMetrics:
    # Objetivos de tiempo
    TARGET_RSS_TIME = 5  # segundos
    TARGET_FIRST_TIME = 20  # segundos
    TARGET_CACHE_TIME = 2  # segundos
    
    async def validate_generation_time(self, strategy: str, tiempo: float) -> bool:
        """Valida si el tiempo cumple con los KPIs"""
        if strategy == 'rss':
            return tiempo < self.TARGET_RSS_TIME
        elif strategy == 'cache':
            return tiempo < self.TARGET_CACHE_TIME
        else:
            return tiempo < self.TARGET_FIRST_TIME
    
    async def calculate_time_reduction(self) -> float:
        """Calcula reducción de tiempo vs proceso manual (20 minutos)"""
        avg_time = await self.get_average_generation_time()
        manual_time = 20 * 60  # 20 minutos en segundos
        return ((manual_time - avg_time) / manual_time) * 100
```

### 13.2 Métricas del plan original
**Agregar a `metrics.py`:**
```python
async def get_system_metrics(self) -> Dict:
    """Obtiene métricas según plan original"""
    return {
        # Tiempo de generación
        'tiempo_reduccion': await self.calculate_time_reduction(),  # Target: 97%
        'tiempo_promedio_rss': await self.get_avg_time('rss'),  # Target: <5s
        'tiempo_promedio_primera_vez': await self.get_avg_time('first'),  # Target: ~20s
        'tiempo_promedio_cache': await self.get_avg_time('cache'),  # Target: <2s
        
        # Precisión
        'precision_spiders': await self.get_spider_success_rate(),  # Target: >90%
        
        # Eficiencia
        'reduccion_requests': await self.get_request_reduction(),  # Target: 70%
        'cache_hit_rate': await self.get_cache_hit_rate(),
        
        # Throughput
        'spiders_por_dia': await self.get_daily_spider_count(),  # Target: 200+
        
        # Adopción
        'porcentaje_adopcion': await self.get_adoption_rate()  # Target: >80%
    }
```

---

## 14. CACHE WARMING DETALLADO

### 14.1 Implementación completa
**En `patterns.py`:**
```python
async def warm_cache_on_startup(self):
    """Pre-carga patrones populares al iniciar el sistema"""
    logger.info("Iniciando cache warming...")
    
    # Obtener top 20 patrones más usados
    popular_patterns = await self.redis.zrevrange(
        "pattern_usage", 0, 19, withscores=True
    )
    
    # Pre-cargar en Redis con pipeline para eficiencia
    pipe = self.redis.pipeline()
    for pattern_key, usage_count in popular_patterns:
        domain, section = pattern_key.split(':')
        pattern_data = await self.get_pattern(domain, section)
        if pattern_data:
            # Extender TTL para patrones populares
            pipe.expire(f"patterns:{domain}", 3600 * 24 * 14)  # 14 días
            
    await pipe.execute()
    logger.info(f"Cache warming completado: {len(popular_patterns)} patrones cargados")

# Llamar en startup de FastAPI
@app.on_event("startup")
async def startup_event():
    await pattern_storage.warm_cache_on_startup()
```

---

## 📝 NOTAS FINALES

- Este plan se alinea 100% con SPIDER_FACTORY_2.0_PLAN_DETALLADO.md
- Incluye TODOS los elementos mencionados en el plan original
- Cada cambio tiene una razón específica basada en el plan original
- La implementación debe ser incremental y testeable
- Mantener compatibilidad hacia atrás donde sea posible
- Documentar todos los cambios realizados

**Elementos agregados en esta versión:**
- ✅ KPIs de tiempo específicos (<5s RSS, ~20s primera vez, <2s cache)
- ✅ Detalles de Firecrawl (HTML, Markdown, screenshots en 1 request)
- ✅ Lista oficial de áreas geográficas para validación
- ✅ Integración con Scrapyd para scheduling automático
- ✅ Redis connection pooling con 50 conexiones
- ✅ Sistema de métricas completo (97% reducción, >90% precisión, etc.)
- ✅ Cache warming detallado para medios populares

---

## 15. ARQUITECTURA DOCKER Y NGINX - CONSIDERACIONES CRÍTICAS

### 15.1 Preservar la arquitectura actual
**La implementación DEBE respetar:**
- NGINX reverse proxy como único punto de entrada (puerto 80)
- Backend NO expone puertos directamente
- Frontend servido por su propio NGINX interno
- Todas las comunicaciones pasan por `lamacquina_network`

### 15.2 Rutas y endpoints a mantener
**NO cambiar las rutas existentes:**
```python
# api.py - Mantener estas rutas exactas
@app.post("/analyze")     # NGINX reescribe: /spider-factory/api/analyze → /analyze
@app.post("/generate")    # NGINX reescribe: /spider-factory/api/generate → /generate
@app.post("/batch")       # NGINX reescribe: /spider-factory/api/batch → /batch
@app.websocket("/ws/{session_id}")  # NGINX reescribe: /spider-factory/ws → /ws
```

**Agregar nuevas rutas sin afectar las existentes:**
```python
@app.post("/check-duplicate")  # Nueva ruta
@app.get("/api/areas")         # Nueva ruta para lista de áreas
@app.get("/api/tipos-medio")   # Nueva ruta para tipos de medio
```

### 15.3 Enfoque de migración no destructiva
**Fase 1 - Campos opcionales (compatibilidad):**
```python
# models.py - Agregar campos como opcionales primero
class AnalysisRequest(BaseModel):
    url: HttpUrl
    name: str  # MANTENER por compatibilidad
    
    # Nuevos campos opcionales en fase 1
    medio: Optional[str] = None
    seccion: Optional[str] = None
    area_geografica: Optional[str] = None
    tipo_medio: Optional[Literal["diario", "revista", "agencia"]] = None
    frecuencia_minutos: Optional[int] = 60
    
    @validator('medio', pre=True, always=True)
    def set_medio_from_name(cls, v, values):
        # Si no hay medio, usar name como fallback
        return v or values.get('name')

class GenerateSpiderRequest(BaseModel):
    spider_name: str  # MANTENER por compatibilidad
    analysis_result: Dict[str, Any]
    
    # Nuevos campos opcionales
    medio: Optional[str] = None
    seccion: Optional[str] = None
    area_geografica: Optional[str] = None
    
    @validator('spider_name', pre=True)
    def generate_spider_name(cls, v, values):
        # Si hay medio y sección, generar automáticamente
        if 'medio' in values and 'seccion' in values and values['medio'] and values['seccion']:
            return f"{values['medio']}_{values['seccion']}".lower().replace(' ', '_')
        return v
```

**Fase 2 - Activación gradual:**
```python
# api.py - Manejar ambos formatos
@app.post("/analyze")
async def analyze_site(request: AnalysisRequest):
    # Usar nuevos campos si están presentes, sino fallback a los antiguos
    medio = request.medio or request.name
    seccion = request.seccion or "general"
    
    # Lógica actual sigue funcionando
    result = await analyzer.analyze(
        url=str(request.url),
        medio=medio,
        seccion=seccion,
        # ... resto de parámetros
    )
```

### 15.4 Configuración Docker a preservar
**NO cambiar en docker-compose.yml:**
```yaml
spider_factory_backend:
  # NO exponer puerto 8000 externamente
  # NO cambiar nombre del servicio
  # Mantener dependencia de redis
  environment:
    - API_PORT=8000  # Puerto interno
  networks:
    - lamacquina_network
```

### 15.5 Variables de entorno críticas
**Mantener en el backend:**
```python
# config.py
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
# NO usar URLs externas, todo es interno en Docker
```

### 15.6 Validación continua durante desarrollo
**Después de cada cambio:**
```bash
# 1. Verificar sintaxis Python
cd src/spider_factory
python -m py_compile src/*.py

# 2. Rebuild contenedor
docker-compose build spider_factory_backend

# 3. Verificar logs
docker-compose up spider_factory_backend
docker-compose logs -f spider_factory_backend

# 4. Test a través de NGINX (NO directo al backend)
curl -X POST http://localhost/spider-factory/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","name":"test"}'

# 5. Verificar WebSocket
wscat -c ws://localhost/spider-factory/ws/test-session
```

### 15.7 Puntos críticos a NO modificar
1. **NO cambiar** el puerto interno 8000 del backend
2. **NO exponer** puertos del backend al host
3. **NO cambiar** nombres de servicios en docker-compose
4. **NO modificar** la red `lamacquina_network`
5. **NO cambiar** rutas base de la API (`/analyze`, `/generate`, etc.)
6. **Mantener** retrocompatibilidad con campos existentes

### 15.8 Testing con arquitectura Docker
```bash
# Test completo del flujo
# 1. Iniciar servicios
docker-compose up -d nginx_reverse_proxy spider_factory_backend spider_factory_frontend redis

# 2. Verificar salud de servicios
docker-compose ps
curl http://localhost/nginx-health
curl http://localhost/spider-factory/api/health

# 3. Test de análisis (a través de NGINX)
curl -X POST http://localhost/spider-factory/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://elpais.com",
    "name": "El País",
    "medio": "El País",
    "seccion": "Internacional",
    "area_geografica": "ESPAÑA",
    "tipo_medio": "diario"
  }'

# 4. Logs para debugging
docker-compose logs -f nginx_reverse_proxy | grep spider-factory
docker-compose logs -f spider_factory_backend
```