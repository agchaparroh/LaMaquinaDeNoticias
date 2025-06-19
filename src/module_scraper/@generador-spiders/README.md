# ÍNDICE MAESTRO - Generador de Spiders para La Máquina de Noticias

## 🎯 PROPÓSITO

Este sistema guía la generación de **spiders especializados** que convierten secciones específicas de medios digitales en fuentes de contenido similares a feeds RSS, integrándose completamente con la arquitectura de La Máquina de Noticias.

## 📖 ARQUITECTURA BASE

Los spiders generados se integran con:
- **Items**: `scraper_core.items.ArticuloInItem`
- **Clases Base**: `BaseArticleSpider`, `BaseSitemapSpider`, `BaseCrawlSpider`
- **Pipelines**: Validación → Limpieza → Almacenamiento (Supabase)
- **Storage**: PostgreSQL + Supabase Storage

## 🚀 FLUJO SIMPLIFICADO

```
Usuario proporciona:
├─ URL de sección (ej: https://elpais.com/internacional)
├─ Nombre del medio
├─ País de publicación
└─ RSS disponible (Sí/No)
    │
    ▼
Claude analiza y genera:
├─ Spider que hereda de BaseArticleSpider
├─ Configuración conservadora
├─ Integración con pipelines existentes
└─ Sistema de deduplicación
```

## 📑 DOCUMENTOS ESENCIALES

### **⚡ FLUJO PRINCIPAL:**
- **`MAIN_WORKFLOW.md`** - Proceso paso a paso
- **`ESTRATEGIAS_SIMPLIFICADAS.md`** - Decisión RSS vs Scraping

### **🎯 GENERACIÓN:**
- **`CODE_GENERATION.md`** - Crear el spider final
- **`TEMPLATES.md`** - Plantillas consistentes con el proyecto
- **`DEFAULTS_CONFIG.md`** - Configuraciones estándar

### **🛠️ SOPORTE:**
- **`ERROR_HANDLING.md`** - Manejo de casos problemáticos
- **`INTEGRATION_GUIDE.md`** - Integración con La Máquina de Noticias

## 🔧 REQUISITOS PREVIOS

### **Variables de entorno necesarias:**
```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-anon-key
SUPABASE_SERVICE_ROLE_KEY=tu-service-role-key
```

### **Estructura del proyecto:**
```
module_scraper/
├── scraper_core/
│   ├── items/
│   ├── pipelines/
│   ├── spiders/
│   │   └── base/
│   └── utils/
└── @generador-spiders/
```

## 🎯 CARACTERÍSTICAS DE LOS SPIDERS GENERADOS

### **✅ Comportamiento tipo RSS:**
- Monitoreo periódico de sección específica
- Extracción solo de artículos nuevos
- Deduplicación automática
- Filtrado estricto por sección

### **✅ Integración completa:**
- Herencia de `BaseArticleSpider`
- Uso de `ArticuloInItem` con todos los campos
- Procesamiento por pipelines existentes
- Almacenamiento en Supabase

### **✅ Configuración conservadora:**
- Respeto a robots.txt
- Rate limiting apropiado
- Límites por ejecución
- Manejo de errores robusto

## 📊 TIPOS DE SPIDER SOPORTADOS

| Tipo | Cuándo usar | Frecuencia | Items/ejecución |
|------|-------------|------------|-----------------|
| **RSS Especializado** | Feed RSS disponible | 30 min | 50 |
| **Scraping HTML** | Sin RSS, contenido estático | 60 min | 30 |
| **Scraping Playwright** | Sin RSS, requiere JavaScript | 120 min | 20 |

## 🔄 PROCESO DE GENERACIÓN

1. **Análisis de la sección** → Determinar estrategia
2. **Selección de template** → Basado en características
3. **Configuración específica** → Selectores y filtros
4. **Generación de código** → Spider completo
5. **Validación** → Compatibilidad con el proyecto

## ⚠️ PRINCIPIOS CLAVE

1. **Sin exploración fuera de la sección**: URLs estrictamente filtradas
2. **Solo contenido nuevo**: Sistema de deduplicación obligatorio
3. **Integración total**: Usar componentes existentes del proyecto
4. **Configuración conservadora**: Respetar límites y delays

## 📚 EJEMPLO DE USO

### **Input del usuario:**
```
URL: https://elpais.com/internacional
Medio: El País
País: España
RSS: No disponible
```

### **Output generado:**
```python
class ElpaisInternacionalSpider(BaseArticleSpider):
    name = 'elpais_internacional'
    # ... configuración completa
```

## 🚀 COMENZAR

1. Revisar **`MAIN_WORKFLOW.md`** para el proceso completo
2. Verificar configuración de Supabase
3. Generar spider según las guías
4. Integrar con el scheduler del proyecto

---

**🎯 OBJETIVO:** Convertir secciones web en feeds RSS automatizados, totalmente integrados con La Máquina de Noticias

**⚡ RESULTADO:** Spiders production-ready que respetan la arquitectura existente
