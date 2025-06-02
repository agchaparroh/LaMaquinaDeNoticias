#!/bin/bash
# =====================================================
# SCRIPT PRINCIPAL DE ORQUESTACIÓN DE MIGRACIÓN
# =====================================================
# Archivo: deploy.sh
# Propósito: Coordinar la ejecución completa de migración
# Uso: ./deploy.sh [opciones]

set -euo pipefail  # Modo estricto

# =====================================================
# CONFIGURACIÓN Y VARIABLES GLOBALES
# =====================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
CONFIG_FILE="$SCRIPT_DIR/config/migration_config.sql"
DEPLOYMENT_LOG="$LOG_DIR/deployment_$(date +%Y%m%d_%H%M%S).log"

# Crear directorio de logs
mkdir -p "$LOG_DIR"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Variables por defecto
DRY_RUN=false
STOP_ON_ERROR=true
CATEGORY=""
START_FROM=""
STOP_AT=""
SKIP_VALIDATIONS=false
FORCE_CONTINUE=false
VERBOSE=false
PARALLEL_EXECUTION=false
BACKUP_BEFORE_DEPLOY=false

# Categorías en orden de ejecución
MIGRATION_CATEGORIES=(
    "01_schema"
    "02_types_domains" 
    "03_tables"
    "04_indexes"
    "05_functions"
    "06_triggers"
    "07_materialized_views"
    "08_reference_data"
)

# =====================================================
# FUNCIONES DE UTILIDAD
# =====================================================

# Función de logging
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$DEPLOYMENT_LOG"
}

# Función para mostrar banners
show_banner() {
    local title="$1"
    local color="$2"
    echo -e "\n${color}=================================="
    echo -e "🚀 $title"
    echo -e "==================================${NC}\n"
}

# Función de ayuda
show_help() {
    cat << EOF
🚀 SCRIPT PRINCIPAL DE ORQUESTACIÓN - MÁQUINA DE NOTICIAS

DESCRIPCIÓN:
    Coordina la ejecución completa de migración de base de datos.
    Ejecuta scripts en orden correcto con validaciones automáticas.

USO:
    ./deploy.sh [OPCIONES]

OPCIONES:
    --dry-run                Mostrar qué se ejecutaría sin hacer cambios reales
    --category CATEGORIA     Ejecutar solo una categoría específica
    --start-from CATEGORIA   Iniciar desde una categoría específica
    --stop-at CATEGORIA      Detenerse en una categoría específica
    --skip-validations       Omitir validaciones pre/post migración
    --force                  Continuar incluso si hay advertencias
    --verbose                Output detallado de todas las operaciones
    --parallel               Ejecutar scripts independientes en paralelo (experimental)
    --backup                 Crear backup completo antes de iniciar
    --stop-on-error          Detener en el primer error (default: true)
    --continue-on-error      Continuar en caso de errores no críticos
    --help                   Mostrar esta ayuda

CATEGORÍAS DISPONIBLES:
    01_schema               Extensiones y esquemas básicos
    02_types_domains        Tipos y dominios personalizados
    03_tables               Tablas principales y particiones
    04_indexes              Índices B-tree, GIN y vectoriales
    05_functions            Funciones PL/pgSQL y RPC
    06_triggers             Triggers y automatizaciones
    07_materialized_views   Vistas materializadas
    08_reference_data       Datos de referencia y testing

EJEMPLOS:
    # Ver qué haría una migración completa
    ./deploy.sh --dry-run

    # Ejecutar migración completa con backup
    ./deploy.sh --backup --verbose

    # Ejecutar solo creación de tablas
    ./deploy.sh --category 03_tables

    # Ejecutar desde índices hasta el final
    ./deploy.sh --start-from 04_indexes

    # Migración hasta funciones (no incluye triggers ni vistas)
    ./deploy.sh --stop-at 05_functions

    # Migración forzada ignorando advertencias
    ./deploy.sh --force --continue-on-error

VARIABLES DE ENTORNO:
    PGHOST                  Host PostgreSQL (default: localhost)
    PGPORT                  Puerto PostgreSQL (default: 5432)
    PGDATABASE              Base de datos (requerido)
    PGUSER                  Usuario PostgreSQL (requerido)
    PGPASSWORD              Password PostgreSQL
    MIGRATION_TIMEOUT       Timeout en segundos (default: 300)

LOGS:
    Los logs se guardan automáticamente en: logs/deployment_YYYYMMDD_HHMMSS.log

EOF
}

# Función para verificar prerrequisitos
check_prerequisites() {
    log "INFO" "Verificando prerrequisitos del sistema..."
    
    # Verificar psql
    if ! command -v psql &> /dev/null; then
        log "ERROR" "psql no está disponible. Instale PostgreSQL client."
        exit 1
    fi
    
    # Verificar variables de entorno
    if [[ -z "${PGDATABASE:-}" ]]; then
        log "ERROR" "Variable PGDATABASE no está configurada"
        exit 1
    fi
    
    if [[ -z "${PGUSER:-}" ]]; then
        log "ERROR" "Variable PGUSER no está configurada"
        exit 1
    fi
    
    # Verificar conexión
    if ! timeout 10 psql -c "SELECT 1;" &> /dev/null; then
        log "ERROR" "No se puede conectar a la base de datos"
        log "ERROR" "Host: ${PGHOST:-localhost}, Puerto: ${PGPORT:-5432}, DB: $PGDATABASE, Usuario: $PGUSER"
        exit 1
    fi
    
    # Verificar estructura de directorios
    for category in "${MIGRATION_CATEGORIES[@]}"; do
        if [[ ! -d "$SCRIPT_DIR/$category" ]]; then
            log "WARNING" "Directorio $category no encontrado, creando..."
            mkdir -p "$SCRIPT_DIR/$category"
        fi
    done
    
    log "INFO" "✅ Prerrequisitos verificados exitosamente"
}

# Función para crear backup
create_backup() {
    if [[ "$BACKUP_BEFORE_DEPLOY" == true ]]; then
        log "INFO" "Creando backup de la base de datos..."
        
        local backup_file="$LOG_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
        
        if pg_dump "$PGDATABASE" > "$backup_file" 2>/dev/null; then
            log "INFO" "✅ Backup creado: $backup_file"
        else
            log "ERROR" "❌ Error creando backup"
            if [[ "$FORCE_CONTINUE" == false ]]; then
                exit 1
            fi
        fi
    fi
}

# Función para ejecutar validaciones pre-migración
execute_pre_validations() {
    if [[ "$SKIP_VALIDATIONS" == true ]]; then
        log "INFO" "⚠️ Validaciones pre-migración omitidas por --skip-validations"
        return 0
    fi
    
    show_banner "VALIDACIONES PRE-MIGRACIÓN" "$CYAN"
    log "INFO" "Ejecutando validaciones pre-migración..."
    
    local validation_query="SELECT * FROM execute_automated_validations('pre');"
    local validation_failed=false
    
    if ! psql -c "$validation_query" 2>/dev/null; then
        validation_failed=true
        log "ERROR" "❌ Error ejecutando validaciones pre-migración"
    fi
    
    # Verificar resultados de validaciones
    local validation_status
    validation_status=$(psql -t -c "
        SELECT overall_status 
        FROM execute_automated_validations('pre') 
        WHERE validation_type = 'pre'
        LIMIT 1;
    " 2>/dev/null | tr -d ' ')
    
    case "$validation_status" in
        "PASSED")
            log "INFO" "✅ Todas las validaciones pre-migración pasaron exitosamente"
            return 0
            ;;
        "WARNING")
            log "WARNING" "⚠️ Validaciones pre-migración completadas con advertencias"
            if [[ "$FORCE_CONTINUE" == false ]]; then
                log "ERROR" "Use --force para continuar a pesar de las advertencias"
                exit 1
            fi
            return 0
            ;;
        "FAILED"|*)
            log "ERROR" "❌ Validaciones pre-migración fallaron"
            if [[ "$FORCE_CONTINUE" == false ]]; then
                exit 1
            fi
            return 1
            ;;
    esac
}

# Función para ejecutar validaciones post-migración
execute_post_validations() {
    if [[ "$SKIP_VALIDATIONS" == true ]]; then
        log "INFO" "⚠️ Validaciones post-migración omitidas por --skip-validations"
        return 0
    fi
    
    show_banner "VALIDACIONES POST-MIGRACIÓN" "$CYAN"
    log "INFO" "Ejecutando validaciones post-migración..."
    
    local validation_query="SELECT * FROM execute_automated_validations('post', NULL, false, true);"
    
    if ! psql -c "$validation_query" 2>/dev/null; then
        log "ERROR" "❌ Error ejecutando validaciones post-migración"
        return 1
    fi
    
    local validation_status
    validation_status=$(psql -t -c "
        SELECT overall_status 
        FROM execute_automated_validations('post', NULL, false, true) 
        WHERE validation_type = 'post'
        LIMIT 1;
    " 2>/dev/null | tr -d ' ')
    
    case "$validation_status" in
        "PASSED")
            log "INFO" "✅ Todas las validaciones post-migración pasaron exitosamente"
            return 0
            ;;
        "WARNING")
            log "WARNING" "⚠️ Validaciones post-migración completadas con advertencias"
            return 0
            ;;
        "FAILED"|*)
            log "ERROR" "❌ Validaciones post-migración fallaron"
            return 1
            ;;
    esac
}

# Función para ejecutar scripts SQL en una categoría
execute_category_scripts() {
    local category="$1"
    local category_path="$SCRIPT_DIR/$category"
    
    if [[ ! -d "$category_path" ]]; then
        log "WARNING" "Directorio $category no existe, saltando..."
        return 0
    fi
    
    local scripts=($(find "$category_path" -name "*.sql" -type f | sort))
    
    if [[ ${#scripts[@]} -eq 0 ]]; then
        log "INFO" "No hay scripts SQL en $category, saltando..."
        return 0
    fi
    
    show_banner "EJECUTANDO CATEGORÍA: $category" "$BLUE"
    log "INFO" "Procesando ${#scripts[@]} scripts en $category..."
    
    local script_count=0
    local success_count=0
    local error_count=0
    
    for script in "${scripts[@]}"; do
        script_count=$((script_count + 1))
        local script_name=$(basename "$script")
        local start_time=$(date +%s)
        
        log "INFO" "[$script_count/${#scripts[@]}] Ejecutando: $script_name"
        
        if [[ "$DRY_RUN" == true ]]; then
            log "INFO" "DRY RUN: $script"
            success_count=$((success_count + 1))
            continue
        fi
        
        # Ejecutar script con timeout
        local timeout_duration=${MIGRATION_TIMEOUT:-300}
        
        if timeout "$timeout_duration" psql -f "$script" &>> "$DEPLOYMENT_LOG"; then
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))
            success_count=$((success_count + 1))
            log "INFO" "✅ $script_name completado en ${duration}s"
        else
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))
            error_count=$((error_count + 1))
            log "ERROR" "❌ $script_name falló después de ${duration}s"
            
            if [[ "$STOP_ON_ERROR" == true ]]; then
                log "ERROR" "Deteniendo ejecución debido a error en $script_name"
                exit 1
            fi
        fi
        
        # Pausa breve entre scripts para evitar sobrecarga
        sleep 0.5
    done
    
    log "INFO" "📊 Categoría $category completada: $success_count éxitos, $error_count errores"
    
    if [[ $error_count -gt 0 && "$FORCE_CONTINUE" == false ]]; then
        log "ERROR" "Hay errores en la categoría $category. Use --force para continuar."
        exit 1
    fi
    
    return $error_count
}

# Función para determinar qué categorías ejecutar
get_categories_to_execute() {
    local categories_to_run=()
    local start_found=false
    local stop_found=false
    
    # Si se especifica una categoría específica
    if [[ -n "$CATEGORY" ]]; then
        categories_to_run=("$CATEGORY")
        echo "${categories_to_run[@]}"
        return
    fi
    
    # Procesar todas las categorías con start-from y stop-at
    for category in "${MIGRATION_CATEGORIES[@]}"; do
        # Lógica de start-from
        if [[ -n "$START_FROM" ]]; then
            if [[ "$category" == "$START_FROM" ]]; then
                start_found=true
            fi
            if [[ "$start_found" == false ]]; then
                continue
            fi
        fi
        
        # Agregar categoría
        categories_to_run+=("$category")
        
        # Lógica de stop-at
        if [[ -n "$STOP_AT" && "$category" == "$STOP_AT" ]]; then
            stop_found=true
            break
        fi
    done
    
    echo "${categories_to_run[@]}"
}

# Función para mostrar progreso general
show_progress() {
    local current="$1"
    local total="$2"
    local category="$3"
    
    local percentage=$((current * 100 / total))
    local bar_length=30
    local filled_length=$((percentage * bar_length / 100))
    local empty_length=$((bar_length - filled_length))
    
    printf "\r${PURPLE}Progreso: ["
    printf "%*s" $filled_length | tr ' ' '='
    printf "%*s" $empty_length
    printf "] %d%% - %s${NC}" $percentage "$category"
}

# =====================================================
# FUNCIÓN PRINCIPAL DE DESPLIEGUE
# =====================================================

execute_migration() {
    local deployment_start=$(date +%s)
    local deployment_id=$(date +%Y%m%d_%H%M%S)
    
    show_banner "INICIANDO MIGRACIÓN COMPLETA" "$GREEN"
    log "INFO" "ID de Despliegue: $deployment_id"
    log "INFO" "Modo: $([ "$DRY_RUN" == true ] && echo "DRY RUN" || echo "EJECUCIÓN REAL")"
    log "INFO" "Base de datos: $PGDATABASE en ${PGHOST:-localhost}:${PGPORT:-5432}"
    
    # Verificar prerrequisitos
    check_prerequisites
    
    # Crear backup si se solicita
    create_backup
    
    # Cargar configuración
    if [[ -f "$CONFIG_FILE" && "$DRY_RUN" == false ]]; then
        log "INFO" "Cargando configuración de migración..."
        if ! psql -f "$CONFIG_FILE" &>> "$DEPLOYMENT_LOG"; then
            log "WARNING" "Error cargando configuración (continuando...)"
        fi
    fi
    
    # Ejecutar validaciones pre-migración
    execute_pre_validations
    
    # Obtener categorías a ejecutar
    local categories_to_execute
    read -ra categories_to_execute <<< "$(get_categories_to_execute)"
    
    log "INFO" "Categorías a ejecutar: ${categories_to_execute[*]}"
    
    # Ejecutar migración por categorías
    local category_count=0
    local total_categories=${#categories_to_execute[@]}
    local total_errors=0
    
    for category in "${categories_to_execute[@]}"; do
        category_count=$((category_count + 1))
        show_progress $category_count $total_categories "$category"
        echo # Nueva línea después del progreso
        
        if ! execute_category_scripts "$category"; then
            total_errors=$((total_errors + 1))
        fi
    done
    
    echo # Línea final después del progreso
    
    # Ejecutar validaciones post-migración
    if ! execute_post_validations; then
        total_errors=$((total_errors + 1))
    fi
    
    # Resumen final
    local deployment_end=$(date +%s)
    local total_duration=$((deployment_end - deployment_start))
    
    show_banner "RESUMEN DE MIGRACIÓN" "$GREEN"
    log "INFO" "🎯 ID de Despliegue: $deployment_id"
    log "INFO" "⏱️ Duración total: ${total_duration}s"
    log "INFO" "📂 Categorías procesadas: $category_count/$total_categories"
    log "INFO" "❌ Errores totales: $total_errors"
    log "INFO" "📄 Log completo: $DEPLOYMENT_LOG"
    
    if [[ $total_errors -eq 0 ]]; then
        show_banner "🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE" "$GREEN"
        exit 0
    else
        show_banner "⚠️ MIGRACIÓN COMPLETADA CON ERRORES" "$YELLOW"
        exit 1
    fi
}

# =====================================================
# PROCESAMIENTO DE ARGUMENTOS
# =====================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --category)
            CATEGORY="$2"
            shift 2
            ;;
        --start-from)
            START_FROM="$2"
            shift 2
            ;;
        --stop-at)
            STOP_AT="$2"
            shift 2
            ;;
        --skip-validations)
            SKIP_VALIDATIONS=true
            shift
            ;;
        --force)
            FORCE_CONTINUE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --parallel)
            PARALLEL_EXECUTION=true
            shift
            ;;
        --backup)
            BACKUP_BEFORE_DEPLOY=true
            shift
            ;;
        --stop-on-error)
            STOP_ON_ERROR=true
            shift
            ;;
        --continue-on-error)
            STOP_ON_ERROR=false
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
done

# =====================================================
# EJECUCIÓN PRINCIPAL
# =====================================================

# Configurar logging verboso si se solicita
if [[ "$VERBOSE" == true ]]; then
    set -x
fi

# Mostrar banner inicial
echo -e "${GREEN}"
cat << 'EOF'
╔═══════════════════════════════════════════════════╗
║              🚀 MÁQUINA DE NOTICIAS               ║
║            Script de Migración v1.0               ║
║         Orquestación Automática Completa         ║
╚═══════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Ejecutar migración
execute_migration

# Final del script
log "INFO" "Script de orquestación completado"
