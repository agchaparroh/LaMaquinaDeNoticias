# 🚀 QUICK START - Generador de Spiders

## ¿Qué es esto?
Un sistema para generar **spiders especializados** que convierten secciones de medios digitales en fuentes tipo RSS, totalmente integrados con La Máquina de Noticias.

## 🎯 Inicio Rápido (30 segundos)

### **1. Información necesaria:**
```yaml
url_seccion: "https://elpais.com/internacional"
nombre_medio: "El País"
pais_publicacion: "España"
tipo_medio: "diario"  # diario/agencia/revista
rss_disponible: "No"   # Sí/No
```

### **2. Generar spider:**
```bash
python generate_spider.py \
    --url "https://elpais.com/internacional" \
    --medio "El País" \
    --pais "España" \
    --tipo "diario" \
    --rss "No"
```

### **3. Resultado:**
```
✅ Spider guardado en: scraper_core/spiders/elpais_internacional_spider.py
📄 Documentación guardada en: scraper_core/spiders/elpais_internacional_README.md
```

## 📋 Checklist Rápido

### **Antes de generar:**
- [ ] Tener URL de una sección específica (NO la home)
- [ ] Saber si hay RSS disponible
- [ ] Tener configuradas las variables de Supabase

### **Después de generar:**
- [ ] Probar con 3 artículos: `scrapy crawl nombre_spider -s CLOSESPIDER_ITEMCOUNT=3`
- [ ] Verificar que se guardan en Supabase
- [ ] Configurar cron para ejecución periódica

## 🔍 Tipos de Spider

| Tiene RSS | Necesita JS | Tipo Spider | Frecuencia |
|-----------|-------------|-------------|------------|
| ✅ Sí | N/A | RSS | 30 min |
| ❌ No | ❌ No | Scraping | 1 hora |
| ❌ No | ✅ Sí | Playwright | 2 horas |

## 💡 Ejemplos Comunes

### **Ejemplo 1: Medio con RSS**
```bash
python generate_spider.py \
    --url "https://www.bbc.com/mundo/topics/america_latina" \
    --medio "BBC Mundo" \
    --pais "Reino Unido" \
    --tipo "agencia" \
    --rss "Sí" \
    --rss-url "https://feeds.bbci.co.uk/mundo/america_latina/rss.xml"
```

### **Ejemplo 2: Medio sin RSS (HTML estático)**
```bash
python generate_spider.py \
    --url "https://www.clarin.com/economia" \
    --medio "Clarín" \
    --pais "Argentina" \
    --tipo "diario" \
    --rss "No"
```

### **Ejemplo 3: Medio con JavaScript**
```bash
python generate_spider.py \
    --url "https://www.infobae.com/tecno" \
    --medio "Infobae" \
    --pais "Argentina" \
    --tipo "diario" \
    --rss "No" \
    --strategy "playwright"
```

## 🛠️ Comandos Útiles

```bash
# Ver spiders disponibles
scrapy list

# Ejecutar spider
scrapy crawl nombre_spider

# Test rápido (3 items)
scrapy crawl nombre_spider -s CLOSESPIDER_ITEMCOUNT=3

# Ver items extraídos
scrapy crawl nombre_spider -o test.json -s CLOSESPIDER_ITEMCOUNT=5

# Debug completo
scrapy crawl nombre_spider -L DEBUG

# Ver logs
tail -f logs/nombre_spider.log
```

## 📊 Verificar en Base de Datos

```sql
-- Contar artículos
SELECT COUNT(*) FROM articulos WHERE fuente = 'nombre_spider';

-- Ver últimos artículos
SELECT titular, fecha_publicacion, url 
FROM articulos 
WHERE fuente = 'nombre_spider'
ORDER BY fecha_recopilacion DESC
LIMIT 10;

-- Estadísticas
SELECT 
    COUNT(*) as total,
    COUNT(DISTINCT url) as urls_unicas,
    MIN(fecha_recopilacion) as primera_vez,
    MAX(fecha_recopilacion) as ultima_vez
FROM articulos
WHERE fuente = 'nombre_spider';
```

## 🚨 Problemas Comunes

| Problema | Solución |
|----------|----------|
| `ImportError` | Verificar que estás en el directorio correcto |
| Sin artículos | Revisar selectores o usar `--strategy playwright` |
| Sin deduplicación | Verificar que existe `crawl_state_*` |
| Sin conexión DB | Configurar variables de entorno Supabase |

## 📅 Configurar Ejecución Periódica

```bash
# Editar crontab
crontab -e

# Agregar línea según tipo:
# RSS (cada 30 min)
*/30 * * * * cd /path && scrapy crawl spider_rss

# Scraping (cada hora)
0 * * * * cd /path && scrapy crawl spider_scraping

# Playwright (cada 2 horas)
0 */2 * * * cd /path && scrapy crawl spider_playwright
```

## 📚 Documentación Completa

- **Proceso detallado**: `MAIN_WORKFLOW.md`
- **Guía rápida**: `GUIA_RAPIDA.md`
- **Ejemplos completos**: `EJEMPLOS_COMPLETOS.md`
- **Solución de errores**: `ERROR_HANDLING.md`

## ✅ Validación Final

El spider generado:
1. ✅ Hereda de `BaseArticleSpider`
2. ✅ Usa `ArticuloInItem` correctamente
3. ✅ Se integra con pipelines del proyecto
4. ✅ Filtra por sección estrictamente
5. ✅ Implementa deduplicación
6. ✅ Almacena en Supabase
7. ✅ Respeta rate limits

---

**🎯 Objetivo:** Convertir cualquier sección web en un feed RSS automatizado  
**⚡ Tiempo:** < 2 minutos para generar un spider funcional  
**🚀 Resultado:** Spider production-ready integrado con el proyecto
