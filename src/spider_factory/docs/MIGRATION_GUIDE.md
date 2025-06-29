# Guía de Migración a Spider Factory 2.0

Esta guía detalla el proceso de migración de spiders existentes a la versión 2.0 de Spider Factory.

## 📋 Cambios Principales en v2.0

### 1. Nomenclatura de Spiders
- **Antes**: Cualquier nombre válido (ej: `elpais-news`, `noticias_argentina`)
- **Ahora**: Formato obligatorio `{medio}_{seccion}` (ej: `el_pais_internacional`)

### 2. Campos Obligatorios
Todos los spiders deben incluir estos campos en la clase:
```python
class MedioSeccionSpider(scrapy.Spider):
    name = "medio_seccion"
    medio = "Nombre del Medio"
    seccion = "Sección"
    area_geografica = "ESPAÑA"  # De lista válida
    tipo_medio = "diario"  # diario|revista|agencia
```

### 3. Cambio de 'titulo' a 'titular'
- **Antes**: `item['titulo'] = "..."`
- **Ahora**: `item['titular'] = "..."`

### 4. Configuración Scrapy-Crawl-Once
Todos los spiders deben incluir:
```python
custom_settings = {
    'CRAWL_ONCE_ENABLED': True,
    'CRAWL_ONCE_PATH': f'.scrapy/crawl_once/{name}',
    'CRAWL_ONCE_DEFAULT': False,
}
```

## 🚀 Proceso de Migración Paso a Paso

### Paso 1: Backup de Spiders Existentes

```bash
# Crear directorio de backup
mkdir -p /backups/spiders_$(date +%Y%m%d)

# Copiar todos los spiders
cp -r /src/module_scraper/scraper_core/spiders/*.py /backups/spiders_$(date +%Y%m%d)/

# Verificar backup
ls -la /backups/spiders_$(date +%Y%m%d)/ | wc -l
```

### Paso 2: Ejecutar Validación

```bash
# Validar todos los spiders y generar reporte
python3 /src/spider_factory/src/validate_spiders.py \
  --spiders-dir /src/module_scraper/scraper_core/spiders \
  --report \
  --output validation_report.json

# Ver resumen en consola
python3 /src/spider_factory/src/validate_spiders.py \
  --spiders-dir /src/module_scraper/scraper_core/spiders
```

Ejemplo de salida:
```
============================================================
RESUMEN DE VALIDACIÓN DE SPIDERS
============================================================
Total de spiders analizados: 45
✅ Válidos: 12
❌ Inválidos: 30
⚠️  Con advertencias: 3

Problemas comunes encontrados:
  - uses_titulo: 25 spiders
  - invalid_area: 15 spiders
  - missing_custom_settings: 28 spiders
```

### Paso 3: Migración Individual (Recomendado para pocos spiders)

Para migrar un spider específico:

```bash
# Ver cambios sin aplicar (dry-run)
python3 /src/spider_factory/src/migrate_spider.py \
  /src/module_scraper/scraper_core/spiders/elpais_news.py \
  --dry-run

# Si los cambios se ven bien, aplicar migración
python3 /src/spider_factory/src/migrate_spider.py \
  /src/module_scraper/scraper_core/spiders/elpais_news.py
```

Si el script no puede detectar medio/sección:
```bash
python3 /src/spider_factory/src/migrate_spider.py \
  /src/module_scraper/scraper_core/spiders/spider_antiguo.py \
  --medio "El País" \
  --seccion "Internacional"
```

### Paso 4: Migración en Batch (Recomendado para muchos spiders)

```bash
# Generar script de migración
python3 /src/spider_factory/src/batch_migrate.py \
  --spiders-dir /src/module_scraper/scraper_core/spiders \
  --generate-script \
  --script-output migrate_all.sh

# Revisar el script generado
cat migrate_all.sh

# Ejecutar migración en batch (con 5 workers paralelos)
python3 /src/spider_factory/src/batch_migrate.py \
  --spiders-dir /src/module_scraper/scraper_core/spiders \
  --workers 5
```

### Paso 5: Actualizar Archivos CSV

Los archivos CSV para batch processing deben incluir las nuevas columnas:

**Formato anterior:**
```csv
name,url
elpais-news,https://elpais.com
```

**Formato nuevo:**
```csv
medio,seccion,url,area_geografica,tipo_medio,frecuencia_minutos,rss_url
El País,Internacional,https://elpais.com/internacional,ESPAÑA,diario,60,
La Nación,Economía,https://lanacion.com.ar/economia,ARGENTINA,diario,120,
```

Script para convertir CSV:
```python
import csv

# Leer CSV antiguo
with open('sites_old.csv', 'r') as f:
    reader = csv.DictReader(f)
    sites = list(reader)

# Escribir CSV nuevo
with open('sites_new.csv', 'w', newline='') as f:
    fieldnames = ['medio','seccion','url','area_geografica','tipo_medio','frecuencia_minutos','rss_url']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    
    for site in sites:
        # Extraer medio y sección del nombre
        parts = site['name'].split('-')
        writer.writerow({
            'medio': parts[0].title(),
            'seccion': parts[1].title() if len(parts) > 1 else 'General',
            'url': site['url'],
            'area_geografica': 'GLOBAL',  # Ajustar según corresponda
            'tipo_medio': 'diario',
            'frecuencia_minutos': '60',
            'rss_url': site.get('rss_url', '')
        })
```

### Paso 6: Verificación Post-Migración

```bash
# Validar nuevamente todos los spiders
python3 /src/spider_factory/src/validate_spiders.py \
  --spiders-dir /src/module_scraper/scraper_core/spiders

# Probar un spider migrado
cd /src/module_scraper
scrapy crawl el_pais_internacional -L INFO

# Verificar que se generan items correctamente
scrapy crawl el_pais_internacional -L INFO -o test_items.json
cat test_items.json | jq '.[0]'
```

### Paso 7: Actualizar Integración con Frontend

Actualizar llamadas a la API en el frontend:

```javascript
// Antes
const response = await fetch('/spider-factory/api/generate', {
  method: 'POST',
  body: JSON.stringify({
    name: 'elpais-news',
    url: 'https://elpais.com'
  })
});

// Ahora
const response = await fetch('/spider-factory/api/generate', {
  method: 'POST',
  body: JSON.stringify({
    medio: 'El País',
    seccion: 'Internacional',
    area_geografica: 'ESPAÑA',
    tipo_medio: 'diario',
    url: 'https://elpais.com/internacional',
    frecuencia_minutos: 60
  })
});
```

## ⚠️ Problemas Comunes y Soluciones

### Error: "uses_titulo"
**Problema**: El spider usa `item['titulo']` en lugar de `item['titular']`
**Solución**: La migración automática cambia esto. Si persiste, buscar y reemplazar manualmente.

### Error: "invalid_area"
**Problema**: El área geográfica no está en la lista válida
**Solución**: Revisar `AREAS_GEOGRAFICAS_VALIDAS` en config.py y actualizar.

### Error: "name_format"
**Problema**: El nombre no sigue el formato `{medio}_{seccion}`
**Solución**: La migración genera el nombre correcto automáticamente.

### Error al ejecutar spider migrado
**Problema**: ImportError o AttributeError
**Solución**: 
1. Verificar que todos los imports estén correctos
2. Asegurar que los campos de clase estén definidos
3. Revisar el backup y comparar cambios

## 🔄 Rollback en Caso de Problemas

Si algo sale mal, restaurar desde backup:

```bash
# Detener cualquier spider en ejecución
docker-compose stop module_scraper

# Restaurar backups
cp /backups/spiders_$(date +%Y%m%d)/*.py /src/module_scraper/scraper_core/spiders/

# Reiniciar servicios
docker-compose start module_scraper
```

## 📞 Soporte

Si encuentras problemas durante la migración:

1. Revisa los logs de migración en `backups/migrations/`
2. Ejecuta validación individual del spider problemático
3. Usa `--dry-run` para ver qué cambios se aplicarían
4. Consulta el CHANGELOG.md para más detalles de cambios

## ✅ Checklist de Migración

- [ ] Backup de todos los spiders existentes
- [ ] Ejecutar validación inicial y guardar reporte
- [ ] Migrar spiders (individual o batch)
- [ ] Actualizar archivos CSV con nuevas columnas
- [ ] Verificar spiders migrados con validación
- [ ] Probar al menos 3 spiders migrados
- [ ] Actualizar integración con frontend
- [ ] Actualizar documentación interna
- [ ] Monitorear métricas post-migración