#!/bin/bash

# =============================================================================
# SCRIPT MAESTRO DE LINTING - LA MÁQUINA DE NOTICIAS
# =============================================================================
# Ejecuta todas las herramientas de formateo y linting del proyecto
# Uso: ./run-linting.sh [--check|--fix] [--python|--typescript|--all]
# =============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
MODE="check"  # check o fix
TARGET="all"  # all, python, typescript
VERBOSE=false
EXIT_CODE=0

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    EXIT_CODE=1
}

usage() {
    cat << EOF
Uso: $0 [opciones]

OPCIONES:
    --check         Solo verificar formato (no modificar archivos) [default]
    --fix           Aplicar correcciones automáticamente
    --python        Solo ejecutar linting de Python
    --typescript    Solo ejecutar linting de TypeScript
    --all           Ejecutar todo el linting [default]
    --verbose       Output detallado
    --help          Mostrar esta ayuda

EJEMPLOS:
    $0                          # Verificar todo
    $0 --fix                    # Corregir todo automáticamente
    $0 --check --python         # Solo verificar Python
    $0 --fix --typescript       # Solo corregir TypeScript

HERRAMIENTAS EJECUTADAS:
    Python:     black, isort, ruff (o flake8), mypy
    TypeScript: prettier, eslint
EOF
    exit 0
}

# =============================================================================
# PARSEO DE ARGUMENTOS
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --check)
            MODE="check"
            shift
            ;;
        --fix)
            MODE="fix"
            shift
            ;;
        --python)
            TARGET="python"
            shift
            ;;
        --typescript)
            TARGET="typescript"
            shift
            ;;
        --all)
            TARGET="all"
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            usage
            ;;
        *)
            echo "Opción desconocida: $1"
            usage
            ;;
    esac
done

# =============================================================================
# FUNCIONES DE LINTING PYTHON
# =============================================================================

check_python_tools() {
    log "Verificando herramientas de Python..."
    
    local missing_tools=()
    
    if ! command -v black &> /dev/null; then
        missing_tools+=("black")
    fi
    
    if ! command -v isort &> /dev/null; then
        missing_tools+=("isort")
    fi
    
    if ! command -v ruff &> /dev/null && ! command -v flake8 &> /dev/null; then
        missing_tools+=("ruff o flake8")
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        error "Herramientas faltantes: ${missing_tools[*]}"
        echo "Instalar con: pip install black isort ruff mypy"
        return 1
    fi
    
    success "Herramientas de Python disponibles"
}

lint_python() {
    log "🐍 Ejecutando linting de Python..."
    
    # Encontrar módulos Python
    local python_modules=(
        "src/module_scraper"
        "src/module_connector" 
        "src/module_pipeline"
        "src/module_dashboard_review_backend"
        "src/spider_factory"
    )
    
    local python_dirs=()
    for module in "${python_modules[@]}"; do
        if [ -d "$module" ]; then
            python_dirs+=("$module")
        fi
    done
    
    if [ ${#python_dirs[@]} -eq 0 ]; then
        warning "No se encontraron módulos Python para procesar"
        return 0
    fi
    
    log "Módulos encontrados: ${python_dirs[*]}"
    
    # 1. BLACK - Formateo
    log "Ejecutando Black (formateo)..."
    for dir in "${python_dirs[@]}"; do
        if [ "$MODE" = "fix" ]; then
            if [ "$VERBOSE" = true ]; then
                black --verbose "$dir" || error "Black falló en $dir"
            else
                black "$dir" || error "Black falló en $dir"
            fi
        else
            if [ "$VERBOSE" = true ]; then
                black --check --diff --verbose "$dir" || error "Black check falló en $dir"
            else
                black --check --diff "$dir" || error "Black check falló en $dir"
            fi
        fi
    done
    
    # 2. ISORT - Organización de imports
    log "Ejecutando isort (imports)..."
    for dir in "${python_dirs[@]}"; do
        if [ "$MODE" = "fix" ]; then
            if [ "$VERBOSE" = true ]; then
                isort --verbose "$dir" || error "isort falló en $dir"
            else
                isort "$dir" || error "isort falló en $dir"
            fi
        else
            if [ "$VERBOSE" = true ]; then
                isort --check-only --diff --verbose "$dir" || error "isort check falló en $dir"
            else
                isort --check-only --diff "$dir" || error "isort check falló en $dir"
            fi
        fi
    done
    
    # 3. RUFF o FLAKE8 - Linting
    log "Ejecutando linting..."
    if command -v ruff &> /dev/null; then
        log "Usando Ruff (linter moderno)..."
        for dir in "${python_dirs[@]}"; do
            if [ "$MODE" = "fix" ]; then
                ruff check --fix "$dir" || error "Ruff falló en $dir"
            else
                ruff check "$dir" || error "Ruff check falló en $dir"
            fi
        done
    else
        log "Usando Flake8..."
        for dir in "${python_dirs[@]}"; do
            flake8 "$dir" || error "Flake8 falló en $dir"
        done
    fi
    
    # 4. MYPY - Type checking (opcional, solo check)
    if command -v mypy &> /dev/null; then
        log "Ejecutando MyPy (type checking)..."
        for dir in "${python_dirs[@]}"; do
            if [ -f "$dir/py.typed" ] || [ -f "$dir/src/py.typed" ]; then
                mypy "$dir" || warning "MyPy encontró problemas en $dir (no crítico)"
            fi
        done
    fi
    
    if [ $EXIT_CODE -eq 0 ]; then
        success "Linting de Python completado"
    fi
}

# =============================================================================
# FUNCIONES DE LINTING TYPESCRIPT
# =============================================================================

check_typescript_tools() {
    log "Verificando herramientas de TypeScript..."
    
    # Verificar que existe Node.js
    if ! command -v npm &> /dev/null; then
        error "npm no está instalado"
        return 1
    fi
    
    success "Node.js y npm disponibles"
}

lint_typescript() {
    log "📜 Ejecutando linting de TypeScript..."
    
    # Encontrar módulos TypeScript
    local ts_modules=(
        "src/module_dashboard_review_frontend"
        "src/module_spider_factory_frontend"
    )
    
    local ts_dirs=()
    for module in "${ts_modules[@]}"; do
        if [ -d "$module" ] && [ -f "$module/package.json" ]; then
            ts_dirs+=("$module")
        fi
    done
    
    if [ ${#ts_dirs[@]} -eq 0 ]; then
        warning "No se encontraron módulos TypeScript para procesar"
        return 0
    fi
    
    log "Módulos encontrados: ${ts_dirs[*]}"
    
    for dir in "${ts_dirs[@]}"; do
        log "Procesando $dir..."
        cd "$dir"
        
        # Verificar que node_modules existe
        if [ ! -d "node_modules" ]; then
            log "Instalando dependencias en $dir..."
            npm install
        fi
        
        # 1. PRETTIER - Formateo
        log "Ejecutando Prettier..."
        if [ "$MODE" = "fix" ]; then
            npm run format || error "Prettier falló en $dir"
        else
            npm run format:check || error "Prettier check falló en $dir"
        fi
        
        # 2. ESLINT - Linting
        log "Ejecutando ESLint..."
        if [ "$MODE" = "fix" ]; then
            npm run lint:fix || error "ESLint falló en $dir"
        else
            npm run lint || error "ESLint check falló en $dir"
        fi
        
        # Volver al directorio raíz
        cd - > /dev/null
    done
    
    if [ $EXIT_CODE -eq 0 ]; then
        success "Linting de TypeScript completado"
    fi
}

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

main() {
    echo "==========================================="
    echo "🔧 LINTING - LA MÁQUINA DE NOTICIAS"
    echo "==========================================="
    echo "Modo: $MODE"
    echo "Target: $TARGET"
    echo "==========================================="
    echo
    
    # Verificar herramientas
    if [ "$TARGET" = "all" ] || [ "$TARGET" = "python" ]; then
        check_python_tools || exit 1
    fi
    
    if [ "$TARGET" = "all" ] || [ "$TARGET" = "typescript" ]; then
        check_typescript_tools || exit 1
    fi
    
    # Ejecutar linting
    if [ "$TARGET" = "all" ] || [ "$TARGET" = "python" ]; then
        lint_python
    fi
    
    if [ "$TARGET" = "all" ] || [ "$TARGET" = "typescript" ]; then
        lint_typescript
    fi
    
    echo
    echo "==========================================="
    if [ $EXIT_CODE -eq 0 ]; then
        success "¡Linting completado exitosamente!"
        if [ "$MODE" = "check" ]; then
            echo "✨ El código cumple con todos los estándares"
        else
            echo "✨ El código ha sido formateado automáticamente"
        fi
    else
        error "Linting falló - revisar errores arriba"
        echo "💡 Ejecutar con --fix para corregir automáticamente"
    fi
    echo "==========================================="
    
    exit $EXIT_CODE
}

# Ejecutar función principal
main "$@"