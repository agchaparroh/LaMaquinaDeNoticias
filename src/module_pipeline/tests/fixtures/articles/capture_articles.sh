#!/bin/bash
# capture_articles.sh - Captura artículos del spider infobae para pruebas

# Configuración
SPIDER_NAME="infobae_america_latina"
MAX_ARTICLES=100
OUTPUT_DIR="src/module_pipeline/test_articles"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== Capturando artículos de $SPIDER_NAME ==="

# Paso 1: Detener el connector para que no procese los archivos
echo "1. Deteniendo module_connector..."
docker-compose stop module_connector

# Paso 2: Limpiar directorio de salida del scraper
echo "2. Limpiando directorio de salida..."
docker exec lamacquina_scraper rm -rf /data/scrapy_output/pending/*

# Paso 3: Ejecutar spider con límite de artículos
echo "3. Ejecutando spider (max $MAX_ARTICLES artículos)..."
docker exec lamacquina_scraper scrapy crawl $SPIDER_NAME -a max_items=$MAX_ARTICLES

# Paso 4: Esperar a que termine
echo "4. Esperando finalización..."
sleep 30

# Paso 5: Copiar archivos generados
echo "5. Copiando archivos..."
docker cp lamacquina_scraper:/data/scrapy_output/pending/. $OUTPUT_DIR/raw/

# Paso 6: Descomprimir archivos
echo "6. Descomprimiendo archivos JSON..."
cd $OUTPUT_DIR/json
for file in ../raw/*.json.gz; do
    if [ -f "$file" ]; then
        gunzip -c "$file" > "$(basename "$file" .gz)"
    fi
done

# Paso 7: Contar archivos
TOTAL_FILES=$(ls -1 *.json 2>/dev/null | wc -l)
echo "7. Total de archivos JSON extraídos: $TOTAL_FILES"

# Paso 8: Reiniciar connector
echo "8. Reiniciando module_connector..."
docker-compose start module_connector

echo "=== Proceso completado ==="
echo "Archivos guardados en: $OUTPUT_DIR/json/"