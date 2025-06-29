# Base de Conocimiento - Spider Factory 2.0

## Decisiones Arquitectónicas

### [2024-12-16]: Usar solo Redis para cache
**Contexto**: Se consideró un sistema de cache multinivel (L1-memoria, L2-Redis, L3-PostgreSQL)
**Decisión**: Usar únicamente Redis
**Razón**: 
- Redis es suficientemente rápido (1-2ms)
- Simplifica la arquitectura considerablemente
- Reduce puntos de fallo
**Alternativas consideradas**: Sistema multinivel con 3 capas

### [2024-12-16]: Firecrawl para análisis, Scrapy para producción
**Contexto**: Necesitamos analizar sitios desconocidos
**Decisión**: Usar Firecrawl solo en la fase de análisis
**Razón**:
- Firecrawl maneja JavaScript automáticamente
- Proporciona HTML, Markdown y screenshots en 1 request
- Los spiders generados usan Scrapy (consistencia con module_scraper)
**Alternativas consideradas**: Usar Scrapy para todo

### [2024-12-16]: Nomenclatura simple de spiders
**Contexto**: Se consideró añadir sufijos por tecnología (_rss, _playwright)
**Decisión**: Todos los spiders se nombran {medio}_{seccion}
**Razón**: Simplicidad y consistencia
**Alternativas consideradas**: Sufijos por estrategia

### [2024-12-16]: Stack frontend consistente con dashboard
**Contexto**: Se consideró HTMX + Alpine.js + Tailwind
**Decisión**: React + TypeScript + Material-UI + Vite
**Razón**: Mantener consistencia con module_dashboard_review_frontend
**Alternativas consideradas**: Stack más ligero con HTMX

---

## Problemas Comunes y Soluciones

### Problema: Campo "titulo" vs "titular"
**Fecha**: 2024-12-16
**Síntoma**: Los items no se guardan correctamente
**Causa**: El campo en ArticuloInItem es "titular", no "titulo"
**Solución**: Usar siempre "titular" en los templates
**Prevención**: Documentar claramente los campos obligatorios

---

## Patrones Útiles

### Deduplicación con scrapy-crawl-once
**Cuándo usar**: Siempre, en todos los spiders
**Implementación**:
```python
custom_settings = {
    'CRAWL_ONCE_ENABLED': True,
    'CRAWL_ONCE_PATH': f'.scrapy/crawl_once/section_{name}',
    'CRAWL_ONCE_DEFAULT': False,
}

# En cada request:
yield self.make_request(url, callback, meta={'crawl_once': True})
```

### Filtrado de sección
**Cuándo usar**: En todos los spiders de scraping/playwright
**Implementación**:
```python
def _is_section_article(self, url: str) -> bool:
    excluded_patterns = [
        r'/archivo/', r'/hemeroteca/', r'/newsletter/',
        r'/multimedia/', r'/video/', r'/podcast/',
        r'/tags?/', r'/autor/', r'/busca[rd]?/',
    ]
    for pattern in excluded_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return False
    return bool(self.section_pattern.search(url))
```

---

## Comandos Frecuentes

```bash
# Desarrollo backend
cd src/spider_factory
pip install -r requirements.txt
uvicorn api:app --reload

# Desarrollo frontend
cd src/module_spider_factory_frontend
npm install
npm run dev

# Testing de spider generado
cd src/module_scraper
scrapy crawl {medio}_{seccion} -L INFO

# Redis
docker run -d -p 6379:6379 redis:alpine
redis-cli ping

# Verificar spider en Scrapyd
curl http://localhost:6800/listspiders.json?project=lamaquina
```

---

## Referencias Importantes

### Documentación Context7
**Ubicación**: `/docs/Expansiones/DOCUMENTACION_OFICIAL-CONTEXT7`

**Contenido**:
1. Scrapy - Framework de web scraping
2. FastAPI - Framework web
3. Redis - Base de datos en memoria
4. Jinja2 - Motor de templates
5. Black - Formateador de código
6. React - Librería UI
7. Vite - Build tool
8. Material-UI - Componentes UI
9. Axios - Cliente HTTP

### Compatibilidad con module_scraper

**Campos obligatorios del Item**:
- `url`
- `titular` (NO "titulo")
- `medio`
- `medio_url_principal`
- `area_geografica`
- `tipo_medio`
- `fecha_publicacion`
- `contenido_texto`
- `contenido_html`
- `fuente` (nombre del spider)

**Ubicación de spiders generados**:
```
src/module_scraper/scraper_core/spiders/{medio}_{seccion}.py
```

**Herencia obligatoria**:
Todos los spiders DEBEN heredar de `BaseArticleSpider`

---

## Notas de Implementación

### Prioridad de análisis
1. Si tiene RSS → No analizar, generar spider RSS
2. Si está en cache → Usar análisis previo
3. Si hay patrón conocido → Aplicar patrón
4. Si no → Análisis con Firecrawl

### Frecuencia de ejecución
- Configurable por el usuario
- No hardcodear en templates
- Campo en UI y CSV

### Integración con Scrapyd
- Los spiders se activan automáticamente al guardar el archivo
- No requiere deploy manual
- Scrapy detecta cualquier .py en el directorio spiders/