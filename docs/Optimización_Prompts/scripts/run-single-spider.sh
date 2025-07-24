#!/bin/bash
# Script para ejecutar un spider individual

if [ -z "$1" ]; then
    echo "Uso: $0 <nombre_del_spider>"
    echo ""
    echo "Spiders disponibles:"
    echo "  - el_nacional_latinoamerica"
    echo "  - el_pais_latinoamerica"
    echo "  - infobae_america_latina"
    exit 1
fi

SPIDER_NAME=$1

echo "Ejecutando spider: $SPIDER_NAME"
echo "Fecha: $(date)"

# Ejecutar el spider
curl http://localhost:6801/schedule.json \
    -d project=scraper_core \
    -d spider=$SPIDER_NAME \
    -d _version=v1.3 \
    -d setting=ITEM_PIPELINES='{"scraper_core.pipelines.json_writer_texto_bruto.JsonWriterTextoBrutoPipeline":900}' \
    -d setting=SCRAPY_OUTPUT_DIR='/output'

if [ $? -eq 0 ]; then
    echo "Spider $SPIDER_NAME ejecutado exitosamente"
else
    echo "Error al ejecutar spider $SPIDER_NAME"
fi