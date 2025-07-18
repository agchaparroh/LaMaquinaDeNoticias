#!/bin/bash
# Test de Flujo Completo de IDs - La Máquina de Noticias
# Fecha: $(date +"%Y-%m-%d %H:%M:%S")

echo "=========================================="
echo "TEST DE FLUJO COMPLETO DE IDs"
echo "=========================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Timestamp para identificar esta prueba
TEST_ID=$(date +"%Y%m%d_%H%M%S")
echo -e "${YELLOW}Test ID: ${TEST_ID}${NC}"
echo ""

# 1. Limpiar directorios de trabajo
echo -e "${YELLOW}1. Limpiando directorios de trabajo...${NC}"
docker exec lamacquina_connector rm -rf /app/scraper_output/*.json.gz 2>/dev/null || true
docker exec lamacquina_connector rm -rf /app/pipeline_pending/*.json.gz 2>/dev/null || true
echo -e "${GREEN}✓ Directorios limpiados${NC}"
echo ""

# 2. Ejecutar spider con un solo artículo
echo -e "${YELLOW}2. Ejecutando spider infobae_america_latina con límite de 1 artículo...${NC}"
docker exec lamacquina_scraper scrapy crawl infobae_america_latina -s CLOSESPIDER_ITEMCOUNT=1 2>&1 | tee /tmp/scraper_test_${TEST_ID}.log

# Esperar a que el archivo se genere
echo -e "${YELLOW}Esperando generación de archivo JSON.gz...${NC}"
sleep 5

# 3. Buscar el ID del artículo en los logs del scraper
echo ""
echo -e "${YELLOW}3. Buscando ID del artículo en logs del scraper...${NC}"
ARTICLE_ID=$(grep -oP "Article ID \K\d+" /tmp/scraper_test_${TEST_ID}.log | tail -1)
if [ -n "$ARTICLE_ID" ]; then
    echo -e "${GREEN}✓ ID encontrado: ${ARTICLE_ID}${NC}"
else
    echo -e "${RED}✗ No se encontró ID del artículo${NC}"
fi

# 4. Verificar archivo JSON generado
echo ""
echo -e "${YELLOW}4. Verificando archivo JSON generado...${NC}"
JSON_FILE=$(docker exec lamacquina_connector ls -1t /app/scraper_output/*.json.gz 2>/dev/null | head -1)
if [ -n "$JSON_FILE" ]; then
    echo -e "${GREEN}✓ Archivo encontrado: ${JSON_FILE}${NC}"
    
    # Verificar contenido del JSON
    echo -e "${YELLOW}Verificando campo articulo_id en JSON...${NC}"
    docker exec lamacquina_connector sh -c "gunzip -c ${JSON_FILE} | jq '.articulo_id' 2>/dev/null || echo 'null'" | tee /tmp/json_id_${TEST_ID}.txt
    JSON_ID=$(cat /tmp/json_id_${TEST_ID}.txt | grep -v null | head -1)
    if [ -n "$JSON_ID" ] && [ "$JSON_ID" != "null" ]; then
        echo -e "${GREEN}✓ articulo_id presente en JSON: ${JSON_ID}${NC}"
    else
        echo -e "${RED}✗ articulo_id NO encontrado en JSON${NC}"
    fi
else
    echo -e "${RED}✗ No se encontró archivo JSON.gz${NC}"
fi

# 5. Monitorear logs del connector
echo ""
echo -e "${YELLOW}5. Monitoreando procesamiento del connector...${NC}"
sleep 10  # Dar tiempo al connector para procesar

# Capturar logs del connector
docker logs --tail 100 lamacquina_connector 2>&1 | tee /tmp/connector_test_${TEST_ID}.log

# Buscar el ID en los logs del connector
CONNECTOR_ID=$(grep -oP "ID: ART-\K\d+" /tmp/connector_test_${TEST_ID}.log | tail -1)
if [ -n "$CONNECTOR_ID" ]; then
    echo -e "${GREEN}✓ Connector procesó artículo con ID: ART-${CONNECTOR_ID}${NC}"
else
    echo -e "${RED}✗ Connector no muestra ID del artículo${NC}"
fi

# 6. Verificar logs del pipeline
echo ""
echo -e "${YELLOW}6. Verificando procesamiento en pipeline...${NC}"
sleep 15  # Dar tiempo al pipeline para procesar

# Capturar logs del pipeline
docker logs --tail 200 lamacquina_pipeline 2>&1 | tee /tmp/pipeline_test_${TEST_ID}.log

# Buscar uso del ID en el pipeline
if [ -n "$CONNECTOR_ID" ]; then
    PIPELINE_ID=$(grep -E "ART-${CONNECTOR_ID}|articulo_id.*${CONNECTOR_ID}" /tmp/pipeline_test_${TEST_ID}.log | head -1)
    if [ -n "$PIPELINE_ID" ]; then
        echo -e "${GREEN}✓ Pipeline procesó artículo con ID correcto${NC}"
    else
        echo -e "${RED}✗ Pipeline no muestra el ID esperado${NC}"
    fi
fi

# Buscar errores de persistencia
PERSIST_ERROR=$(grep -i "error.*persistir\|error.*insertar" /tmp/pipeline_test_${TEST_ID}.log | tail -1)
if [ -n "$PERSIST_ERROR" ]; then
    echo -e "${RED}✗ Error de persistencia encontrado:${NC}"
    echo "$PERSIST_ERROR"
else
    PERSIST_SUCCESS=$(grep -i "persistido exitosamente\|guardado exitosamente" /tmp/pipeline_test_${TEST_ID}.log | tail -1)
    if [ -n "$PERSIST_SUCCESS" ]; then
        echo -e "${GREEN}✓ Persistencia exitosa${NC}"
    else
        echo -e "${YELLOW}⚠ Estado de persistencia desconocido${NC}"
    fi
fi

# 7. Resumen final
echo ""
echo "=========================================="
echo "RESUMEN DEL TEST"
echo "=========================================="
echo -e "ID en Scraper:    ${ARTICLE_ID:-${RED}NO ENCONTRADO${NC}}"
echo -e "ID en JSON:       ${JSON_ID:-${RED}NO ENCONTRADO${NC}}"
echo -e "ID en Connector:  ${CONNECTOR_ID:-${RED}NO ENCONTRADO${NC}}"
echo -e "ID en Pipeline:   ${PIPELINE_ID:+${GREEN}PROCESADO${NC}}${PIPELINE_ID:-${RED}NO ENCONTRADO${NC}}"
echo -e "Persistencia:     ${PERSIST_SUCCESS:+${GREEN}EXITOSA${NC}}${PERSIST_ERROR:+${RED}ERROR${NC}}${PERSIST_SUCCESS:-${PERSIST_ERROR:-${YELLOW}DESCONOCIDA${NC}}}"
echo ""
echo "Logs guardados en:"
echo "  - /tmp/scraper_test_${TEST_ID}.log"
echo "  - /tmp/connector_test_${TEST_ID}.log"
echo "  - /tmp/pipeline_test_${TEST_ID}.log"
echo ""