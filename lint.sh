#!/bin/bash
# Script de linting - La Máquina de Noticias
# Alternativa a Makefile para sistemas sin make

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Función de ayuda
show_help() {
    echo -e "${GREEN}La Máquina de Noticias - Comandos de Linting${NC}"
    echo "  ./lint.sh format-file <path>  - Formatear archivo específico"
    echo "  ./lint.sh lint-file <path>    - Verificar archivo específico"
    echo "  ./lint.sh format-all          - Formatear todo el proyecto"
    echo "  ./lint.sh lint-all            - Verificar todo el proyecto"
    echo "  ./lint.sh install-tools       - Instalar herramientas de linting"
}

# Formatear archivo específico
format_file() {
    local file="$1"
    if [ -z "$file" ]; then
        echo -e "${YELLOW}Uso: ./lint.sh format-file <path>${NC}"
        exit 1
    fi
    
    if [[ "$file" =~ \.(py)$ ]]; then
        echo -e "${GREEN}Formateando Python: $file${NC}"
        black "$file" 2>/dev/null || true
        ruff check --fix "$file" --select I 2>/dev/null || true
    elif [[ "$file" =~ \.(js|jsx|ts|tsx)$ ]]; then
        echo -e "${GREEN}Formateando JS/TS: $file${NC}"
        dir=$(dirname "$file")
        if [ -f "$dir/../package.json" ]; then
            (cd "$dir/.." && npm run format -- "$file" 2>/dev/null) || true
        fi
    fi
}

# Verificar archivo específico
lint_file() {
    local file="$1"
    if [ -z "$file" ]; then
        echo -e "${YELLOW}Uso: ./lint.sh lint-file <path>${NC}"
        exit 1
    fi
    
    if [[ "$file" =~ \.(py)$ ]]; then
        echo -e "${GREEN}Verificando Python: $file${NC}"
        ruff check "$file" 2>/dev/null || true
    elif [[ "$file" =~ \.(js|jsx|ts|tsx)$ ]]; then
        echo -e "${GREEN}Verificando JS/TS: $file${NC}"
        dir=$(dirname "$file")
        if [ -f "$dir/../package.json" ]; then
            (cd "$dir/.." && npm run lint -- "$file" 2>/dev/null) || true
        fi
    fi
}

# Formatear todo el proyecto
format_all() {
    echo -e "${GREEN}Formateando archivos Python...${NC}"
    black src/ tests/ 2>/dev/null || echo -e "${YELLOW}Black no instalado${NC}"
    ruff check --fix src/ tests/ --select I 2>/dev/null || echo -e "${YELLOW}Ruff no instalado${NC}"
    
    echo -e "${GREEN}Formateando archivos JS/TS...${NC}"
    for dir in src/module_dashboard_review_frontend src/module_spider_factory_frontend; do
        if [ -d "$dir" ]; then
            echo "  Procesando $dir..."
            (cd "$dir" && npm run format 2>/dev/null) || true
        fi
    done
}

# Verificar todo el proyecto
lint_all() {
    echo -e "${GREEN}Verificando archivos Python...${NC}"
    ruff check src/ tests/ 2>/dev/null || echo -e "${YELLOW}Ruff no instalado${NC}"
    
    echo -e "${GREEN}Verificando archivos JS/TS...${NC}"
    for dir in src/module_dashboard_review_frontend src/module_spider_factory_frontend; do
        if [ -d "$dir" ]; then
            echo "  Procesando $dir..."
            (cd "$dir" && npm run lint 2>/dev/null) || true
        fi
    done
}

# Instalar herramientas
install_tools() {
    echo -e "${GREEN}Instalando herramientas de linting...${NC}"
    echo -e "${YELLOW}Instalando herramientas Python...${NC}"
    pip install black ruff --upgrade
    
    echo -e "${YELLOW}Instalando dependencias en módulos JS/TS...${NC}"
    for dir in src/module_dashboard_review_frontend src/module_spider_factory_frontend; do
        if [ -d "$dir" ]; then
            echo "  Instalando en $dir..."
            (cd "$dir" && npm install)
        fi
    done
    echo -e "${GREEN}✅ Herramientas instaladas${NC}"
}

# Main
case "$1" in
    format-file)
        format_file "$2"
        ;;
    lint-file)
        lint_file "$2"
        ;;
    format-all)
        format_all
        ;;
    lint-all)
        lint_all
        ;;
    install-tools)
        install_tools
        ;;
    *)
        show_help
        ;;
esac