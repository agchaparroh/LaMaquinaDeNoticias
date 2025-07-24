#!/bin/bash
# Script para ejecutar TODOS los spiders disponibles y extraer textos brutos

echo "=== Extracción masiva de textos brutos ==="
echo "Fecha: $(date)"
echo ""

# Lista de spiders válidos (solo los que extraen contenido completo)
SPIDERS=(
    "el_nacional_latinoamerica"
    "el_pais_latinoamerica"
    "infobae_america_latina"
)

# Contador de spiders ejecutados
TOTAL_SPIDERS=${#SPIDERS[@]}
EXECUTED=0
FAILED=0

# Directorio de salida
OUTPUT_DIR="./docs/Optimización_Prompts/TEXTOS BRUTOS"

echo "Se ejecutarán $TOTAL_SPIDERS spiders"
echo "Los archivos se guardarán en: $OUTPUT_DIR"
echo ""

# Función para ejecutar un spider
run_spider() {
    local spider_name=$1
    echo "[$((EXECUTED + 1))/$TOTAL_SPIDERS] Ejecutando spider: $spider_name"
    
    # Ejecutar spider
    response=$(curl -s http://localhost:6801/schedule.json \
        -d project=scraper_core \
        -d spider=$spider_name \
        -d _version=v1.3 \
        -d setting=ITEM_PIPELINES='{"scraper_core.pipelines.json_writer_texto_bruto.JsonWriterTextoBrutoPipeline":900}' \
        -d setting=SCRAPY_OUTPUT_DIR=/output \
        -d setting=LOG_LEVEL=INFO)
    
    # Verificar si se programó correctamente
    if echo "$response" | grep -q '"status": "ok"'; then
        jobid=$(echo "$response" | grep -o '"jobid": "[^"]*"' | cut -d'"' -f4)
        echo "  ✓ Programado correctamente (Job ID: $jobid)"
        ((EXECUTED++))
    else
        echo "  ✗ Error al programar spider"
        echo "  Respuesta: $response"
        ((FAILED++))
    fi
    
    # Esperar un poco entre spiders para no saturar
    sleep 2
}

# Ejecutar todos los spiders
for spider in "${SPIDERS[@]}"; do
    run_spider "$spider"
done

echo ""
echo "=== Resumen de ejecución ==="
echo "Spiders ejecutados: $EXECUTED"
echo "Spiders fallidos: $FAILED"
echo ""

# Esperar a que terminen de ejecutarse
echo "Esperando 2 minutos para que terminen las extracciones..."
sleep 120

# Contar archivos generados
if [ -d "$OUTPUT_DIR" ]; then
    FILE_COUNT=$(find "$OUTPUT_DIR" -name "*.json" -type f | wc -l)
    echo ""
    echo "=== Resultados ==="
    echo "Total de archivos JSON generados: $FILE_COUNT"
    echo ""
    
    # Mostrar estadísticas por spider
    echo "Archivos por spider:"
    for spider in "${SPIDERS[@]}"; do
        count=$(find "$OUTPUT_DIR" -name "${spider}_*.json" -type f | wc -l)
        if [ $count -gt 0 ]; then
            echo "  - $spider: $count archivos"
        fi
    done
else
    echo "ERROR: No se encontró el directorio de salida"
fi

echo ""
echo "=== Fin de la extracción masiva ==="
echo ""

# Mostrar cómo monitorear el progreso
echo "Para monitorear el progreso en tiempo real:"
echo "  curl http://localhost:6801/listjobs.json?project=scraper_core | python3 -m json.tool"
echo ""
echo "Para ver los logs de un spider específico:"
echo "  Accede a http://localhost:5001"