# ArticuloInItem y ArticuloInItemLoader - Guía de Uso

## Resumen

El sistema de Items y ItemLoaders proporciona una forma estructurada y consistente de procesar artículos periodísticos en el módulo de scraping. 

- **ArticuloInItem**: Define la estructura de datos para artículos periodísticos
- **ArticuloInItemLoader**: Procesa y normaliza los datos extraídos

## ArticuloInItem

### Campos Disponibles

#### Campos Principales
- `url`: URL original del artículo
- `storage_path`: Ruta en Supabase Storage (generada automáticamente)
- `medio`: Nombre del medio de comunicación
- `pais_publicacion`: País de publicación
- `tipo_medio`: Tipo de medio (diario, agencia, televisión, radio, digital, oficial, blog, otro)
- `titular`: Título del artículo
- `fecha_publicacion`: Fecha de publicación (datetime)
- `autor`: Autor(es) del artículo
- `idioma`: Código ISO del idioma (default: 'es')
- `seccion`: Sección del medio
- `etiquetas_fuente`: Lista de etiquetas del medio original
- `es_opinion`: Boolean - ¿Es artículo de opinión?
- `es_oficial`: Boolean - ¿Es fuente oficial?

#### Campos de Contenido
- `contenido_texto`: Texto completo del artículo (sin HTML)
- `contenido_html`: HTML original del artículo

#### Campos Generados por Pipeline

- `resumen`: Resumen generado en Fase 2
- `categorias_asignadas`: Categorías asignadas en Fase 2
- `puntuacion_relevancia`: Puntuación 0-10 asignada en Fase 2

#### Campos de Control

- `fecha_recopilacion`: Timestamp de cuando se hizo el scraping 
- `fecha_procesamiento`: Timestamp de fin de procesamiento
- `estado_procesamiento`: Estado actual (pendiente, procesando, completado, error_*)
- `error_detalle`: Detalle del error si existe
- `metadata`: Campo JSONB para datos adicionales

### Validación

El item incluye un método `validate()` que verifica campos requeridos:
- titular
- medio
- pais_publicacion
- tipo_medio
- fecha_publicacion
- contenido_texto

## ArticuloInItemLoader

### Procesadores Incluidos

#### Limpieza de Texto
- `clean_text()`: Elimina espacios extra, normaliza Unicode
- `extract_text_from_html()`: Extrae texto limpio de HTML

#### Normalización de Fechas
- `normalize_date()`: Soporta múltiples formatos:
  - ISO: `2024-01-15T10:30:00Z`
  - Español: `15/01/2024`, `15 de enero de 2024`
  - Inglés: `January 15, 2024`, `01/15/2024`

#### URLs
- `normalize_url()`: Elimina parámetros de tracking (utm_*, fbclid, etc.)

#### Validaciones
- `validate_medio_type()`: Asegura tipos válidos de medio
- `validate_language()`: Normaliza códigos de idioma
- `process_tags()`: Procesa etiquetas como lista, elimina duplicados

### Uso Básico

```python
from scraper_core.items import ArticuloInItem
from scraper_core.itemloaders import ArticuloInItemLoader

# En un spider
def parse_article(self, response):
    loader = ArticuloInItemLoader(item=ArticuloInItem(), response=response)
    
    # Usar selectores CSS
    loader.add_css('titular', 'h1.title::text')
    loader.add_css('contenido_texto', 'div.article-body')
    loader.add_css('autor', 'span.author::text')
    
    # Usar XPath
    loader.add_xpath('fecha_publicacion', '//time/@datetime')
    
    # Valores directos
    loader.add_value('medio', 'El País')
    loader.add_value('pais_publicacion', 'España')
    loader.add_value('tipo_medio', 'diario')
    
    # Cargar item
    item = loader.load_item()
    
    if item.validate():
        yield item
```

### Storage Path

El `storage_path` se genera automáticamente en formato:
```
{medio}/{año}/{mes}/{día}/{titulo_slug}.html.gz
```

Ejemplo: `el-pais/2024/01/15/economia-espanola-crece.html.gz`

### Procesamiento Automático

El loader aplica automáticamente:

1. **Títulos**: Elimina HTML, limpia espacios
2. **Autores**: Elimina prefijos como "Por", "By", limita a 200 caracteres
3. **Fechas**: Convierte a datetime object
4. **URLs**: Elimina parámetros de tracking
5. **Etiquetas**: Convierte a lista, elimina duplicados
6. **Booleanos**: Asegura tipo bool para es_opinion, es_oficial
7. **Puntuación**: Valida rango 0-10

### Valores por Defecto

- `idioma`: 'es'
- `estado_procesamiento`: 'pendiente'
- `es_opinion`: False
- `es_oficial`: False
- `fecha_recopilacion`: datetime.now()

## Ejemplos Avanzados

### Procesamiento Condicional

```python
# Detectar tipo de artículo
is_opinion = bool(response.css('.opinion-section').get())
loader.add_value('es_opinion', is_opinion)

# Detectar fuente oficial
if 'gobierno' in response.url or response.css('.official-source'):
    loader.add_value('es_oficial', True)
```

### Metadata Personalizada

```python
metadata = {
    'scraping_version': '1.0',
    'spider_name': self.name,
    'response_status': response.status,
    'encoding': response.encoding
}
loader.add_value('metadata', metadata)
```

### Manejo de Errores

```python
try:
    loader.add_css('contenido_texto', 'article.content')
except Exception as e:
    loader.add_value('error_detalle', str(e))
    loader.add_value('estado_procesamiento', 'error_extraccion')
```

## Integración con Pipeline

Los items procesados por el loader están listos para:

1. **Validación**: Verificar campos requeridos
2. **Almacenamiento**: Guardar en Supabase Storage
3. **Base de Datos**: Insertar en tabla `articulos`
4. **Procesamiento IA**: Análisis de contenido en fases posteriores

## Troubleshooting

### Item no válido
- Verificar que todos los campos requeridos estén presentes
- Usar `item.validate()` antes de yield

### Fechas no reconocidas
- Verificar formato en `normalize_date()`
- Agregar nuevo formato si es necesario

### Storage path inválido
- Verificar que cumple con el regex de validación
- Formato: `{medio}/YYYY/MM/DD/{slug}.html.gz`

### Encoding issues
- El loader normaliza Unicode automáticamente
- Para casos especiales, usar `response.encoding` en metadata
