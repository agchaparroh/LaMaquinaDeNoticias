#!/bin/bash
# Test simplificado de flujo de IDs

echo "=========================================="
echo "TEST SIMPLIFICADO DE FLUJO DE IDs"
echo "Fecha: $(date +"%Y-%m-%d %H:%M:%S")"
echo "=========================================="
echo ""

# 1. Ejecutar spider y capturar ID
echo "1. Ejecutando spider..."
SCRAPER_OUTPUT=$(docker exec lamacquina_scraper scrapy crawl infobae_america_latina -s CLOSESPIDER_ITEMCOUNT=1 2>&1)
ARTICLE_ID=$(echo "$SCRAPER_OUTPUT" | grep -oP "ID del artículo guardado: \K\d+" | tail -1)
echo "   ID capturado del scraper: $ARTICLE_ID"

# 2. Esperar procesamiento
echo ""
echo "2. Esperando procesamiento..."
sleep 10

# 3. Verificar JSON generado
echo ""
echo "3. Verificando JSON generado..."
JSON_FILE=$(docker exec lamacquina_connector ls -1t /app/scraper_output/*.json.gz 2>/dev/null | head -1)
if [ -n "$JSON_FILE" ]; then
    JSON_ID=$(docker exec lamacquina_connector sh -c "gunzip -c $JSON_FILE | jq -r '.articulo_id // \"null\"'" 2>/dev/null)
    echo "   articulo_id en JSON: $JSON_ID"
else
    echo "   ❌ No se encontró archivo JSON"
fi

# 4. Verificar logs del connector
echo ""
echo "4. Verificando connector..."
CONNECTOR_LOG=$(docker logs --tail 50 lamacquina_connector 2>&1 | grep -E "ID: ART-|articulo_id" | tail -5)
echo "$CONNECTOR_LOG" | while IFS= read -r line; do
    echo "   $line"
done

# 5. Verificar logs del pipeline
echo ""
echo "5. Verificando pipeline..."
sleep 10
PIPELINE_LOG=$(docker logs --tail 100 lamacquina_pipeline 2>&1 | grep -E "articulo_id|ART-|fragmento_id|usando ID|persistido exitosamente" | tail -10)
echo "$PIPELINE_LOG" | while IFS= read -r line; do
    echo "   $line"
done

# 6. Resumen
echo ""
echo "=========================================="
echo "RESUMEN"
echo "=========================================="
echo "Scraper ID: ${ARTICLE_ID:-NO ENCONTRADO}"
echo "JSON ID: ${JSON_ID:-NO ENCONTRADO}"
echo ""