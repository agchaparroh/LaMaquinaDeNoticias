#!/bin/bash

# =============================================================================
# GIT LFS MANAGER - LA MÁQUINA DE NOTICIAS
# =============================================================================
# Script para manejo inteligente de Git LFS en el servidor
# Uso: ./lfs-manager.sh [check|pull|status|cleanup] [options]
#
# Comandos:
#   check      Verificar si hay archivos LFS en el repositorio
#   pull       Descargar archivos LFS con optimizaciones
#   status     Mostrar estado de archivos LFS
#   cleanup    Limpiar archivos LFS antiguos
#
# Opciones:
#   --timeout=N    Timeout en segundos (default: 300)
#   --force        Forzar operaciones sin confirmación
#   --verbose      Mostrar información detallada
#
# Ejemplos:
#   ./lfs-manager.sh check
#   ./lfs-manager.sh pull --timeout=600
#   ./lfs-manager.sh cleanup --force
# =============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración por defecto
COMMAND=""
TIMEOUT=300
FORCE=false
VERBOSE=false

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

verbose() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${BLUE}🔍 $1${NC}"
    fi
}

usage() {
    cat << EOF
Uso: $0 [comando] [opciones]

Comandos:
    check      Verificar si hay archivos LFS en el repositorio
    pull       Descargar archivos LFS con optimizaciones
    status     Mostrar estado de archivos LFS
    cleanup    Limpiar archivos LFS antiguos

Opciones:
    --timeout=N    Timeout en segundos (default: 300)
    --force        Forzar operaciones sin confirmación
    --verbose      Mostrar información detallada
    --help         Mostrar esta ayuda

Ejemplos:
    $0 check
    $0 pull --timeout=600 --verbose
    $0 status
    $0 cleanup --force
EOF
    exit 1
}

# =============================================================================
# PARSEO DE ARGUMENTOS
# =============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            check|pull|status|cleanup)
                COMMAND="$1"
                shift
                ;;
            --timeout=*)
                TIMEOUT="${1#*=}"
                shift
                ;;
            --force)
                FORCE=true
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
                error "Opción desconocida: $1"
                ;;
        esac
    done

    if [[ -z "$COMMAND" ]]; then
        error "Debe especificar un comando: check, pull, status, o cleanup"
    fi
}

# =============================================================================
# FUNCIONES DE VALIDACIÓN
# =============================================================================

validate_git_repo() {
    if [[ ! -d ".git" ]]; then
        error "No está en un repositorio Git"
    fi
    
    verbose "Repositorio Git validado"
}

validate_lfs_installed() {
    if ! command -v git-lfs &> /dev/null; then
        error "Git LFS no está instalado"
    fi
    
    verbose "Git LFS está instalado: $(git lfs version)"
}

# =============================================================================
# FUNCIONES PRINCIPALES
# =============================================================================

check_lfs_files() {
    log "Verificando archivos LFS en el repositorio..."
    
    # Verificar si hay configuración LFS
    if [[ ! -f ".gitattributes" ]]; then
        warning "No se encontró archivo .gitattributes"
        return 1
    fi
    
    # Verificar archivos LFS configurados
    local lfs_patterns=$(grep "filter=lfs" .gitattributes 2>/dev/null || true)
    if [[ -z "$lfs_patterns" ]]; then
        warning "No se encontraron patrones LFS en .gitattributes"
        return 1
    fi
    
    verbose "Patrones LFS encontrados:"
    verbose "$lfs_patterns"
    
    # Listar archivos LFS en el repositorio
    local lfs_files=$(git lfs ls-files 2>/dev/null || true)
    if [[ -z "$lfs_files" ]]; then
        success "No hay archivos LFS rastreados en este momento"
        return 0
    fi
    
    local file_count=$(echo "$lfs_files" | wc -l)
    success "Encontrados $file_count archivos LFS"
    
    if [[ "$VERBOSE" == true ]]; then
        echo
        echo "📁 Archivos LFS:"
        echo "$lfs_files" | head -10
        if [[ $file_count -gt 10 ]]; then
            echo "... y $((file_count - 10)) más"
        fi
    fi
    
    return 0
}

get_lfs_status() {
    log "Obteniendo estado de archivos LFS..."
    
    # Verificar si hay archivos LFS
    if ! check_lfs_files >/dev/null 2>&1; then
        warning "No hay archivos LFS para verificar"
        return 0
    fi
    
    # Estado de archivos LFS
    echo
    echo "📊 ESTADO DE ARCHIVOS LFS:"
    echo "=========================="
    
    # Archivos rastreados
    local tracked_files=$(git lfs ls-files | wc -l)
    echo "Archivos rastreados: $tracked_files"
    
    # Archivos no descargados (pointers)
    local pointer_files=0
    if command -v git &> /dev/null; then
        pointer_files=$(git lfs ls-files | while read -r file; do
            if [[ -f "$file" ]] && [[ $(file "$file" | grep -c "ASCII text" || true) -gt 0 ]]; then
                if grep -q "oid sha256" "$file" 2>/dev/null; then
                    echo "$file"
                fi
            fi
        done | wc -l)
    fi
    
    echo "Archivos como pointer: $pointer_files"
    echo "Archivos descargados: $((tracked_files - pointer_files))"
    
    # Tamaño total
    if [[ "$VERBOSE" == true ]]; then
        echo
        echo "💾 INFORMACIÓN DE TAMAÑO:"
        git lfs ls-files -s 2>/dev/null | head -5 || true
    fi
    
    # Información del cache local
    if [[ -d ".git/lfs" ]]; then
        local cache_size=$(du -sh .git/lfs 2>/dev/null | cut -f1 || echo "unknown")
        echo "Caché local LFS: $cache_size"
    fi
}

pull_lfs_files() {
    log "Descargando archivos LFS..."
    
    # Verificar si hay archivos LFS para descargar
    if ! check_lfs_files >/dev/null 2>&1; then
        success "No hay archivos LFS para descargar"
        return 0
    fi
    
    # Mostrar información previa
    local lfs_count=$(git lfs ls-files | wc -l)
    log "Preparando descarga de $lfs_count archivos LFS (timeout: ${TIMEOUT}s)"
    
    # Función de descarga con timeout
    local start_time=$(date +%s)
    
    verbose "Iniciando git lfs pull..."
    
    # Usar timeout para evitar cuelgues
    if timeout "$TIMEOUT" git lfs pull; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        success "Archivos LFS descargados exitosamente en ${duration}s"
    else
        local exit_code=$?
        warning "Descarga LFS interrumpida (timeout: ${TIMEOUT}s o error)"
        
        if [[ $exit_code -eq 124 ]]; then
            warning "Timeout alcanzado. Algunos archivos pueden no haberse descargado."
        else
            warning "Error durante la descarga (código: $exit_code)"
        fi
        
        # Intentar descarga parcial de archivos críticos
        attempt_partial_download
        
        return 1
    fi
    
    # Verificar resultado
    verify_lfs_download
}

attempt_partial_download() {
    log "Intentando descarga parcial de archivos críticos..."
    
    # Patrones de archivos críticos (ajustar según tu proyecto)
    local critical_patterns=(
        "*.model"
        "*.weights"
        "*.pkl"
        "*.joblib"
        "*.h5"
    )
    
    for pattern in "${critical_patterns[@]}"; do
        local critical_files=$(git lfs ls-files | grep "$pattern" | head -5 || true)
        if [[ -n "$critical_files" ]]; then
            verbose "Descargando archivos críticos: $pattern"
            echo "$critical_files" | while read -r file; do
                if [[ -n "$file" ]]; then
                    timeout 30 git lfs pull --include="$file" || warning "No se pudo descargar: $file"
                fi
            done
        fi
    done
}

verify_lfs_download() {
    log "Verificando descarga de archivos LFS..."
    
    local total_files=$(git lfs ls-files | wc -l)
    local pointer_files=0
    
    # Contar archivos que siguen siendo pointers
    git lfs ls-files | while read -r file; do
        if [[ -f "$file" ]] && grep -q "oid sha256" "$file" 2>/dev/null; then
            echo "$file"
        fi
    done > /tmp/lfs_pointers.txt
    
    pointer_files=$(wc -l < /tmp/lfs_pointers.txt)
    local downloaded_files=$((total_files - pointer_files))
    
    if [[ $pointer_files -eq 0 ]]; then
        success "Todos los archivos LFS descargados correctamente ($total_files/$total_files)"
    else
        warning "Descarga parcial: $downloaded_files/$total_files archivos descargados"
        
        if [[ "$VERBOSE" == true ]] && [[ $pointer_files -lt 10 ]]; then
            echo "Archivos no descargados:"
            cat /tmp/lfs_pointers.txt
        fi
    fi
    
    rm -f /tmp/lfs_pointers.txt
}

cleanup_lfs_cache() {
    log "Limpiando caché de Git LFS..."
    
    if [[ "$FORCE" == false ]]; then
        echo
        warning "Esta operación eliminará archivos LFS antiguos del caché local"
        read -p "¿Continuar? (y/N): " confirm
        if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
            log "Operación cancelada"
            return 0
        fi
    fi
    
    # Información previa
    if [[ -d ".git/lfs" ]]; then
        local cache_size_before=$(du -sh .git/lfs 2>/dev/null | cut -f1 || echo "unknown")
        log "Tamaño del caché antes: $cache_size_before"
    fi
    
    # Limpiar caché
    verbose "Ejecutando git lfs prune..."
    git lfs prune
    
    # Información posterior
    if [[ -d ".git/lfs" ]]; then
        local cache_size_after=$(du -sh .git/lfs 2>/dev/null | cut -f1 || echo "unknown")
        success "Limpieza completada. Tamaño del caché después: $cache_size_after"
    else
        success "Caché LFS limpiado completamente"
    fi
}

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

main() {
    echo "=========================================="
    echo "📦 GIT LFS MANAGER"
    echo "=========================================="
    echo
    
    parse_args "$@"
    
    # Validaciones
    validate_git_repo
    validate_lfs_installed
    
    # Ejecutar comando
    case "$COMMAND" in
        check)
            check_lfs_files
            ;;
        pull)
            pull_lfs_files
            ;;
        status)
            get_lfs_status
            ;;
        cleanup)
            cleanup_lfs_cache
            ;;
        *)
            error "Comando no reconocido: $COMMAND"
            ;;
    esac
    
    echo
    log "Operación '$COMMAND' completada"
}

# Verificar dependencias básicas
if ! command -v git &> /dev/null; then
    error "Git no está instalado"
fi

# Ejecutar función principal
main "$@"