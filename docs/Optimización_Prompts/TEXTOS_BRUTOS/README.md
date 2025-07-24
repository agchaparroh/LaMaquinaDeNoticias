# Sistema de Extracción de Textos Brutos

Este directorio almacena los artículos periodísticos extraídos en formato JSON sin procesamiento adicional.

## Configuración

Se ha creado una instancia separada de Scrapyd específicamente para extraer textos brutos:

- **Puerto Scrapyd**: 6801 (en lugar del 6800 normal)
- **Puerto ScrapydWeb**: 5001 (en lugar del 5000 normal)
- **Red aislada**: `textos_brutos_network`
- **Sin conexión** con el pipeline principal de procesamiento

## Cómo usar

### 1. Levantar el sistema

```bash
# Levantar solo el sistema de textos brutos
docker-compose -f docker-compose.textos-brutos.yml up -d

# Ver los logs
docker-compose -f docker-compose.textos-brutos.yml logs -f
```

### 2. Acceder a ScrapydWeb

- URL: http://localhost:5001
- Usuario: admin
- Contraseña: textos_brutos

### 3. Ejecutar spiders

Los spiders se ejecutan igual que en el sistema principal, pero los resultados se guardan directamente en este directorio como archivos JSON.

### 4. Deploy de spiders

```bash
# Desde el directorio src/module_scraper
cd src/module_scraper
scrapyd-deploy -p scraper_core http://localhost:6801/
```

### 5. Ejecutar un spider específico

```bash
# Vía curl
curl http://localhost:6801/schedule.json -d project=scraper_core -d spider=el_pais_latinoamerica

# O desde ScrapydWeb en http://localhost:5001
```

## Estructura de archivos

Los archivos se guardan con el formato:
```
{nombre_spider}_{YYYYMMDD_HHMMSS}.json
```

Ejemplo: `el_pais_latinoamerica_20250724_143022.json`

## Diferencias con el sistema principal

1. **Solo pipeline JsonWriter**: No hay limpieza, validación ni almacenamiento en base de datos
2. **Red aislada**: No se comunica con otros servicios
3. **Configuración optimizada**: Mayor concurrencia y menor delay para extracción más rápida
4. **Salida local**: Todo se guarda en este directorio

## Detener el sistema

```bash
docker-compose -f docker-compose.textos-brutos.yml down
```

## Notas importantes

- Los archivos JSON contienen TODOS los campos extraídos por los spiders
- No hay validación de datos, pueden contener campos vacíos o malformados
- Ideal para análisis de contenido y optimización de prompts