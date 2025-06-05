# Análisis de Versiones de Dependencias Compartidas
## Module Pipeline - Compatibilidad con Ecosistema La Máquina de Noticias

**Fecha:** $(date)
**Propósito:** Identificar versiones compatibles para librerías compartidas entre module_connector, module_scraper y module_pipeline

## Tabla Comparativa de Versiones

| Librería | module_connector | module_scraper | module_pipeline (actual) | Versión Recomendada | Justificación |
|----------|------------------|----------------|-------------------------|---------------------|---------------|
| **supabase** | ❌ No presente | 2.4.6 | 2.15.2 | **2.15.2** | Mantener versión más reciente para compatibilidad con RPCs |
| **pydantic** | 2.11.5 | 2.10.3 | 2.11.5 | **2.11.5** | Versión más reciente con mejor rendimiento |
| **tenacity** | 9.1.2 | 8.2.3 | 9.1.2 | **9.1.2** | Versión más reciente con mejores features de retry |
| **loguru** | 0.7.3 | ❌ No presente | 0.7.3 | **0.7.3** | Mantener versión actual, scraper no usa loguru |
| **python-dotenv** | 1.1.0 | 1.0.1 | 1.1.0 | **1.1.0** | Versión más reciente |

## Análisis Detallado

### 🟢 Supabase (2.15.2)
- **Decisión:** Mantener versión 2.15.2 en module_pipeline
- **Razón:** 
  - module_scraper usa 2.4.6 (versión antigua)
  - module_pipeline necesita RPCs más avanzadas (insertar_articulo_completo, buscar_entidad_similar)
  - Versión 2.15.2 es backward compatible
  - No hay conflicto porque module_connector no usa supabase

### 🟡 Pydantic (2.11.5)
- **Decisión:** Usar 2.11.5 (misma que module_connector)
- **Razón:**
  - module_connector: 2.11.5 (más reciente)
  - module_scraper: 2.10.3 (más antigua)
  - 2.11.5 es backward compatible con 2.10.3
  - Mejor rendimiento y características en 2.11.5
  - **CRÍTICO:** Mantener compatibilidad con ArticuloInItem del module_connector

### 🟢 Tenacity (9.1.2)
- **Decisión:** Usar 9.1.2 (misma que module_connector)
- **Razón:**
  - module_connector: 9.1.2 (más reciente)
  - module_scraper: 8.2.3 (más antigua)
  - 9.1.2 tiene mejores features de retry y exponential backoff
  - Backward compatible

### 🟢 Loguru (0.7.3)
- **Decisión:** Mantener 0.7.3
- **Razón:**
  - Solo usado por module_connector y module_pipeline
  - module_scraper no usa loguru (usa logging estándar)
  - Sin conflictos

### 🟢 Python-dotenv (1.1.0)
- **Decisión:** Usar 1.1.0 (misma que module_connector)
- **Razón:**
  - Versión más reciente
  - Backward compatible con 1.0.1

## Librerías Específicas (sin conflictos)

### Module Pipeline únicamente:
- **fastapi==0.116.2** ✅ Sin conflictos
- **groq==0.26.0** ✅ Sin conflictos  
- **spacy==3.8.7** ✅ Sin conflictos
- **numpy>=1.21.0,<2.0.0** ✅ Sin conflictos (restrictivo por spaCy)

### Module Connector únicamente:
- **aiohttp==3.12.6** ➡️ module_pipeline usa **httpx==0.27.2** (sin conflictos)

### Module Scraper únicamente:
- **scrapy, playwright, etc.** ➡️ No relevantes para module_pipeline

## Conflictos Identificados

### ❌ Conflicto Potencial: HTTPx vs AioHTTP
- **module_connector:** usa aiohttp==3.12.6
- **module_pipeline:** usa httpx==0.27.2
- **Resolución:** Sin conflicto real - son librerías diferentes para propósitos similares
- **Acción:** Mantener httpx en module_pipeline (usado por supabase-py)

### ❌ Versión Supabase Divergente
- **module_scraper:** 2.4.6 (antigua)
- **module_pipeline:** 2.15.2 (reciente)
- **Resolución:** Acceptable - sin integración directa entre estos módulos
- **Acción:** Documentar para futura sincronización del ecosistema

## Matriz de Compatibilidad

| Integración | Estado | Librerías Críticas | Riesgo |
|-------------|--------|-------------------|--------|
| module_connector ↔ module_pipeline | ✅ Compatible | pydantic, tenacity, loguru | 🟢 Bajo |
| module_scraper ↔ module_pipeline | ⚠️ Funcional | supabase (versiones diferentes) | 🟡 Medio |
| module_connector ↔ module_scraper | ✅ Compatible | pydantic, python-dotenv | 🟢 Bajo |

## Decisiones Finales

### Versiones a usar en module_pipeline:
```txt
# Librerías compartidas (versiones coordinadas)
supabase==2.15.2           # Mantener versión avanzada (RPCs)
pydantic==2.11.5           # Sincronizar con module_connector  
tenacity==9.1.2            # Sincronizar con module_connector
loguru==0.7.3              # Sincronizar con module_connector
python-dotenv==1.1.0       # Sincronizar con module_connector

# Librerías específicas (sin cambios)
fastapi==0.116.2
uvicorn[standard]==0.35.1
groq==0.26.0
httpx==0.27.2
# ... resto sin cambios
```

## Acciones Requeridas

1. ✅ **Actualizar requirements.txt** con versiones sincronizadas
2. ⚠️ **Monitorear** compatibilidad entre supabase 2.4.6 (scraper) y 2.15.2 (pipeline)
3. 📋 **Documentar** para equipo: necesidad de sincronización futura del ecosistema
4. 🧪 **Testear** integración después de actualización

## Notas de Compatibilidad

- **Python 3.8+:** Todas las versiones son compatibles
- **Breaking Changes:** Ninguno identificado en el rango de versiones
- **Performance:** Mejoras esperadas con versiones más recientes
- **APIs:** Sin cambios en interfaces públicas entre versiones seleccionadas
