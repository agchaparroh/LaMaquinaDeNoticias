# Scripts para Extracción de Textos Brutos

Este directorio contiene los scripts necesarios para ejecutar una instancia separada de Scrapy que extrae artículos periodísticos sin procesamiento para optimización de prompts.

## Arquitectura del Sistema

El sistema de extracción de textos brutos funciona de manera independiente del pipeline principal de La Máquina de Noticias:

1. **Contenedores Docker separados**: Scrapyd y ScrapydWeb en puertos 6801 y 5001
2. **Pipeline personalizado**: `JsonWriterTextoBrutoPipeline` que guarda JSON sin comprimir
3. **Directorio de salida dedicado**: `docs/Optimización_Prompts/TEXTOS BRUTOS/`
4. **Spiders filtrados**: Solo se ejecutan los que extraen contenido completo

## Archivos

### docker-compose.textos-brutos.yml
Configuración de Docker Compose para levantar los servicios Scrapyd y ScrapydWeb en puertos separados:
- Scrapyd: Puerto 6801
- ScrapydWeb: Puerto 5001
- Volumen mapeado a: `docs/Optimización_Prompts/TEXTOS BRUTOS`

### run-all-spiders-textos-brutos.sh
Script para ejecutar todos los spiders disponibles y extraer artículos. 

**Spiders válidos que extraen contenido completo:**
- el_nacional_latinoamerica
- el_pais_latinoamerica
- infobae_america_latina

**Nota:** Los spiders de centroamerica360 y la_gaceta fueron excluidos porque extraen páginas de listado en lugar de contenido individual de artículos.

### json_writer_texto_bruto.py
Pipeline personalizado que:
- Guarda archivos JSON sin compresión gzip (a diferencia del pipeline normal que usa gzip)
- Acepta tanto objetos ArticuloInItem como diccionarios
- Guarda en el directorio configurado en SCRAPY_OUTPUT_DIR
- Genera nombres de archivo con formato: `{spider_name}_{timestamp}_{contador}.json`
- Convierte objetos datetime a formato ISO para compatibilidad JSON
- Mantiene estadísticas de items exportados, omitidos y errores

Este archivo se monta en el contenedor Docker en la ruta correcta para que Scrapy lo encuentre.

## Uso

1. Levantar los contenedores:
```bash
docker-compose -f docs/Optimización_Prompts/scripts/docker-compose.textos-brutos.yml up -d
```

2. Hacer deploy del proyecto (si es necesario):
```bash
docker exec -it scrapyd_textos_brutos scrapyd-deploy -p scraper_core
```

3. Ejecutar todos los spiders:
```bash
./docs/Optimización_Prompts/scripts/run-all-spiders-textos-brutos.sh
```

Los artículos extraídos se guardarán en `docs/Optimización_Prompts/TEXTOS BRUTOS/`

## Limpieza

Para detener y limpiar completamente el sistema:

```bash
# Detener contenedores
docker stop scrapyd_textos_brutos scrapydweb_textos_brutos

# Eliminar contenedores
docker rm scrapyd_textos_brutos scrapydweb_textos_brutos

# Eliminar volúmenes (opcional - esto borrará logs y datos persistentes)
docker volume rm lamaquinadenoticias_scrapyd_textos_eggs
docker volume rm lamaquinadenoticias_scrapyd_textos_logs
docker volume rm lamaquinadenoticias_scrapydweb_textos_data
```