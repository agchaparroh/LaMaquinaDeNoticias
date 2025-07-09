#!/bin/bash

# Script para alternar entre modo desarrollo y producción
# Uso: ./toggle-dev-mode.sh [enable|disable|toggle|status]

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar el estado actual
show_status() {
    echo -e "${BLUE}📊 Estado actual:${NC}"
    
    if [ ! -f .env ]; then
        echo -e "  ${RED}✗ No existe archivo .env${NC}"
        return
    fi
    
    if grep -q "DEVELOPMENT_MODE=true" .env 2>/dev/null; then
        echo -e "  ${GREEN}✓ DEVELOPMENT_MODE=true${NC}"
        echo "  📁 Los datos se guardarán en: ./pruebas_pipeline/"
        
        # Mostrar configuración adicional de desarrollo
        local scraper_dir=$(grep "^SCRAPER_OUTPUT_DIR=" .env | cut -d'=' -f2 | tr -d '"')
        local export_enabled=$(grep "^ENABLE_PIPELINE_EXPORT=" .env | cut -d'=' -f2 | tr -d '"')
        
        echo -e "\n  ${BLUE}Configuración de desarrollo:${NC}"
        echo -e "  - SCRAPER_OUTPUT_DIR: ${GREEN}${scraper_dir}${NC}"
        echo -e "  - ENABLE_PIPELINE_EXPORT: ${GREEN}${export_enabled}${NC}"
        echo -e "  - Pipeline guarda en: ${GREEN}/pruebas_pipeline/development_outputs/${NC}"
    else
        echo -e "  ${YELLOW}✗ DEVELOPMENT_MODE=false${NC}"
        echo "  ☁️  Los datos se guardarán en: Supabase"
        
        # Mostrar configuración adicional de producción
        local scraper_dir=$(grep "^SCRAPER_OUTPUT_DIR=" .env | cut -d'=' -f2 | tr -d '"')
        local export_enabled=$(grep "^ENABLE_PIPELINE_EXPORT=" .env | cut -d'=' -f2 | tr -d '"')
        
        echo -e "\n  ${BLUE}Configuración de producción:${NC}"
        echo -e "  - SCRAPER_OUTPUT_DIR: ${YELLOW}${scraper_dir}${NC}"
        echo -e "  - ENABLE_PIPELINE_EXPORT: ${YELLOW}${export_enabled}${NC}"
        echo -e "  - Datos persisten en: ${YELLOW}Supabase${NC}"
    fi
}

# Función para activar modo desarrollo
enable_dev_mode() {
    if [ ! -f .env ]; then
        echo -e "${RED}❌ Error: No existe archivo .env${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}🔧 Activando modo desarrollo...${NC}"
    
    # Activar DEVELOPMENT_MODE
    if grep -q "^DEVELOPMENT_MODE=" .env; then
        sed -i 's/^DEVELOPMENT_MODE=.*/DEVELOPMENT_MODE=true/' .env
    else
        echo "DEVELOPMENT_MODE=true" >> .env
    fi
    
    # Cambiar rutas a modo desarrollo (usar pruebas_pipeline)
    sed -i 's|^SCRAPER_OUTPUT_DIR=.*|SCRAPER_OUTPUT_DIR="/pruebas_pipeline/scrapy_output/pending"|' .env
    sed -i 's|^DEVELOPMENT_OUTPUT_DIR=.*|DEVELOPMENT_OUTPUT_DIR="/pruebas_pipeline/development_outputs"|' .env
    
    # Activar exportación de pipeline para desarrollo
    if grep -q "^ENABLE_PIPELINE_EXPORT=" .env; then
        sed -i 's/^ENABLE_PIPELINE_EXPORT=.*/ENABLE_PIPELINE_EXPORT=true/' .env
    else
        echo "ENABLE_PIPELINE_EXPORT=true" >> .env
    fi
    
    # Asegurarse de que EXPORT_DIRECTORY apunte al lugar correcto
    if grep -q "^EXPORT_DIRECTORY=" .env; then
        sed -i 's|^EXPORT_DIRECTORY=.*|EXPORT_DIRECTORY="/pruebas_pipeline/scrapy_output/pending"|' .env
    else
        echo "EXPORT_DIRECTORY=/pruebas_pipeline/scrapy_output/pending" >> .env
    fi
    
    echo -e "${GREEN}✓ Modo desarrollo activado${NC}"
    echo -e "${GREEN}✓ Rutas configuradas para pruebas_pipeline/${NC}"
    echo -e "${GREEN}✓ Exportación JSON habilitada${NC}"
}

# Función para desactivar modo desarrollo
disable_dev_mode() {
    if [ ! -f .env ]; then
        echo -e "${RED}❌ Error: No existe archivo .env${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}🔧 Desactivando modo desarrollo...${NC}"
    
    # Desactivar DEVELOPMENT_MODE
    if grep -q "^DEVELOPMENT_MODE=" .env; then
        sed -i 's/^DEVELOPMENT_MODE=.*/DEVELOPMENT_MODE=false/' .env
    else
        echo "DEVELOPMENT_MODE=false" >> .env
    fi
    
    # Cambiar rutas a modo producción (usar /data)
    sed -i 's|^SCRAPER_OUTPUT_DIR=.*|SCRAPER_OUTPUT_DIR="/data/scrapy_output/pending"|' .env
    sed -i 's|^DEVELOPMENT_OUTPUT_DIR=.*|DEVELOPMENT_OUTPUT_DIR="/data/development_outputs"|' .env
    
    # Desactivar exportación de pipeline en producción (opcional, depende de tu configuración)
    if grep -q "^ENABLE_PIPELINE_EXPORT=" .env; then
        sed -i 's/^ENABLE_PIPELINE_EXPORT=.*/ENABLE_PIPELINE_EXPORT=false/' .env
    else
        echo "ENABLE_PIPELINE_EXPORT=false" >> .env
    fi
    
    # Cambiar EXPORT_DIRECTORY a ruta de producción
    if grep -q "^EXPORT_DIRECTORY=" .env; then
        sed -i 's|^EXPORT_DIRECTORY=.*|EXPORT_DIRECTORY="/data/scrapy_output/pending"|' .env
    else
        echo "EXPORT_DIRECTORY=/data/scrapy_output/pending" >> .env
    fi
    
    echo -e "${YELLOW}✓ Modo producción activado${NC}"
    echo -e "${YELLOW}✓ Rutas configuradas para /data${NC}"
    echo -e "${YELLOW}✓ Datos se guardarán en Supabase${NC}"
}

# Función para alternar modo
toggle_mode() {
    if [ ! -f .env ]; then
        echo -e "${RED}❌ Error: No existe archivo .env${NC}"
        exit 1
    fi
    
    if grep -q "DEVELOPMENT_MODE=true" .env 2>/dev/null; then
        disable_dev_mode
    else
        enable_dev_mode
    fi
}

# Función principal
case "${1:-status}" in
    enable)
        enable_dev_mode
        ;;
    disable)
        disable_dev_mode
        ;;
    toggle)
        toggle_mode
        ;;
    status)
        show_status
        ;;
    *)
        echo "Uso: $0 [enable|disable|toggle|status]"
        echo ""
        echo "Comandos:"
        echo "  enable  - Activa DEVELOPMENT_MODE=true"
        echo "  disable - Activa DEVELOPMENT_MODE=false"
        echo "  toggle  - Alterna entre desarrollo/producción"
        echo "  status  - Muestra el estado actual (default)"
        echo ""
        show_status
        ;;
esac

echo ""
echo -e "${BLUE}ℹ️  Nota: Los cambios se aplicarán cuando reinicies los servicios${NC}"
echo -e "${BLUE}ℹ️  Info: En modo desarrollo, el modelo ArticuloInItem del pipeline aceptará campos extra para debugging${NC}"