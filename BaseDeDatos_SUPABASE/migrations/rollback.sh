#!/bin/bash
# =====================================================
# SCRIPT DE ROLLBACK AUTOMÁTICO
# =====================================================
# Archivo: rollback.sh
# Propósito: Ejecutar rollbacks de manera segura y controlada
# Uso: ./rollback.sh [opciones]

set -euo pipefail  # Modo estricto

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROLLBACK_DIR="$SCRIPT_DIR/rollbacks"
LOG_DIR="$SCRIPT_DIR/logs"
CONFIG_FILE="$SCRIPT_DIR/config/migration_config.sql"

# Crear directorio de logs si no existe
mkdir -p "$LOG_DIR"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables por defecto
DRY_RUN=false
LIST_ONLY=false
TARGET_SCRIPT=""
SINGLE_SCRIPT=""
FORCE=false
CONFIRM=false
VERBOSE=false

# Función de logging
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_DIR/rollback_$(date +%Y%m%d).log"
}

# Función de ayuda
show_help() {
    cat << EOF
🔄 SISTEMA DE ROLLBACK - MÁQUINA DE NOTICIAS

DESCRIPCIÓN:
    Script para ejecutar rollbacks de migración de manera segura.
    Permite rollback completo, parcial o individual con validaciones.

USO:
    ./rollback.sh [OPCIONES]

OPCIONES:
    --list                  Listar rollbacks disponibles
    --dry-run              Mostrar qué se ejecutaría (modo simulación)
    --to SCRIPT            Rollback hasta un script específico
    --single SCRIPT        Rollback de un solo script
    --force                Forzar rollback ignorando dependencias
    --confirm              Confirmar rollback destructivo (REQUERIDO para ejecución real)
    --verbose              Output detallado
    --help                 Mostrar esta ayuda

EJEMPLOS:
    # Listar rollbacks disponibles
    ./rollback.sh --list

    # Ver qué haría un rollback completo
    ./rollback.sh --dry-run

    # Ver rollback hasta un script específico
    ./rollback.sh --to 02_001_create_types_domains.sql --dry-run

    # Ejecutar rollback real hasta un punto específico
    ./rollback.sh --to 02_001_create_types_domains.sql --confirm

    # Rollback de un solo script (peligroso)
    ./rollback.sh --single 03_001_create_tables.sql --force --confirm

    # Rollback completo con confirmación
    ./rollback.sh --confirm

VARIABLES DE ENTORNO:
    PGHOST              Host de PostgreSQL (default: localhost)
    PGPORT              Puerto de PostgreSQL (default: 5432)
    PGDATABASE          Base de datos (requerido)
    PGUSER              Usuario de PostgreSQL (requerido)
    PGPASSWORD          Password de PostgreSQL

ADVERTENCIAS:
    ⚠️  Los rollbacks son DESTRUCTIVOS e IRREVERSIBLES
    ⚠️  Siempre ejecutar --dry-run antes de confirmar
    ⚠️  Crear backups antes de rollbacks en producción
    ⚠️  Coordinar con el equipo en entornos compartidos

EOF
}

# Función para verificar prerrequisitos
check_prerequisites() {
    log "INFO" "Verificando prerrequisitos..."
    
    # Verificar que psql esté disponible
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
    
    # Verificar conexión a la base de datos
    if ! psql -c "SELECT 1;" &> /dev/null; then
        log "ERROR" "No se puede conectar a la base de datos"
        log "ERROR" "Host: ${PGHOST:-localhost}, Puerto: ${PGPORT:-5432}, DB: $PGDATABASE, Usuario: $PGUSER"
        exit 1
    fi
    
    log "INFO" "✓ Prerrequisitos verificados"
}

# Función para listar rollbacks disponibles
list_rollbacks() {
    log "INFO" "Consultando rollbacks disponibles..."
    
    echo -e "${GREEN}📋 ROLLBACKS DISPONIBLES${NC}"
    echo "========================================"
    
    psql -c "
        SELECT 
            script_name,
            category,
            executed_at::DATE as fecha,
            CASE WHEN is_safe THEN '✅ Seguro' ELSE '⚠️ Dependencias' END as estado,
            dependent_objects as deps
        FROM list_available_rollbacks()
        ORDER BY executed_at DESC;
    " 2>/dev/null || {
        log "ERROR" "No se pudo consultar rollbacks disponibles"
        exit 1
    }
}

# Función para dry run
dry_run() {
    local target_script="$1"
    
    log "INFO" "Ejecutando dry run - Rollback hasta: ${target_script:-COMPLETO}"
    
    echo -e "${YELLOW}🔍 DRY RUN - SIMULACIÓN DE ROLLBACK${NC}"
    echo "========================================"
    echo -e "${YELLOW}Modo: SIMULACIÓN (no se realizarán cambios)${NC}"
    echo -e "Target: ${target_script:-ROLLBACK COMPLETO}"
    echo ""
    
    local query
    if [ -z "$target_script" ]; then
        query="SELECT * FROM execute_master_rollback();"
    else
        query="SELECT * FROM execute_master_rollback('$target_script');"
    fi
    
    psql -c "$query" 2>/dev/null || {
        log "ERROR" "Error en dry run"
        exit 1
    }
}

# Función para ejecutar rollback real
execute_rollback() {
    local target_script="$1"
    local force_flag="$2"
    
    log "WARNING" "INICIANDO ROLLBACK REAL - OPERACIÓN DESTRUCTIVA"
    
    echo -e "${RED}⚠️  EJECUTANDO ROLLBACK REAL${NC}"
    echo "========================================"
    echo -e "${RED}Esta operación es DESTRUCTIVA e IRREVERSIBLE${NC}"
    echo -e "Target: ${target_script:-ROLLBACK COMPLETO}"
    echo -e "Forzar: ${force_flag}"
    echo ""
    
    # Confirmación adicional para rollbacks completos
    if [ -z "$target_script" ]; then
        echo -e "${RED}¿Está seguro de que desea ejecutar un ROLLBACK COMPLETO?${NC}"
        echo "Escriba 'CONFIRMAR ROLLBACK COMPLETO' para continuar:"
        read -r confirmation
        
        if [ "$confirmation" != "CONFIRMAR ROLLBACK COMPLETO" ]; then
            log "INFO" "Rollback cancelado por el usuario"
            echo "Operación cancelada."
            exit 0
        fi
    fi
    
    # Ejecutar validaciones pre-rollback
    log "INFO" "Ejecutando validaciones pre-rollback..."
    
    local validation_query="SELECT * FROM validate_pre_rollback('${target_script:-ALL}');"
    local validation_failed=false
    
    echo -e "${BLUE}📋 Validaciones Pre-Rollback:${NC}"
    
    if ! psql -c "$validation_query" 2>/dev/null; then
        validation_failed=true
    fi
    
    if [ "$validation_failed" = true ] && [ "$force_flag" != "TRUE" ]; then
        echo -e "${RED}❌ Validaciones fallaron. Use --force para continuar de todas formas.${NC}"
        exit 1
    fi
    
    # Crear backup de migration_history
    log "INFO" "Creando backup de migration_history..."
    
    local backup_query="
        DROP TABLE IF EXISTS migration_history_backup_$(date +%Y%m%d_%H%M%S);
        CREATE TABLE migration_history_backup_$(date +%Y%m%d_%H%M%S) AS 
        SELECT * FROM migration_history;
    "
    
    psql -c "$backup_query" &>/dev/null || {
        log "WARNING" "No se pudo crear backup de migration_history"
    }
    
    # Ejecutar rollback
    log "INFO" "Ejecutando rollback..."
    
    local rollback_query
    if [ -z "$target_script" ]; then
        rollback_query="SELECT * FROM execute_master_rollback(NULL, FALSE, $force_flag);"
    else
        rollback_query="SELECT * FROM execute_master_rollback('$target_script', FALSE, $force_flag);"
    fi
    
    if psql -c "$rollback_query" 2>/dev/null; then
        log "INFO" "✅ Rollback completado exitosamente"
        echo -e "${GREEN}✅ ROLLBACK COMPLETADO EXITOSAMENTE${NC}"
    else
        log "ERROR" "❌ Error durante la ejecución del rollback"
        echo -e "${RED}❌ ERROR DURANTE EL ROLLBACK${NC}"
        exit 1
    fi
}

# Función para validar argumentos
validate_arguments() {
    if [ "$CONFIRM" = false ] && [ "$DRY_RUN" = false ] && [ "$LIST_ONLY" = false ]; then
        echo -e "${YELLOW}⚠️  Use --dry-run para ver qué se ejecutaría, o --confirm para ejecutar realmente${NC}"
        show_help
        exit 1
    fi
    
    if [ -n "$SINGLE_SCRIPT" ] && [ -n "$TARGET_SCRIPT" ]; then
        log "ERROR" "No se puede especificar --single y --to al mismo tiempo"
        exit 1
    fi
}

# Procesamiento de argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --list)
            LIST_ONLY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --to)
            TARGET_SCRIPT="$2"
            shift 2
            ;;
        --single)
            SINGLE_SCRIPT="$2"
            TARGET_SCRIPT="$2"  # Usar la misma lógica
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --confirm)
            CONFIRM=true
            shift
            ;;
        --verbose)
            VERBOSE=true
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

# Main execution
main() {
    log "INFO" "Iniciando script de rollback con argumentos: $*"
    
    # Validar argumentos
    validate_arguments
    
    # Verificar prerrequisitos
    check_prerequisites
    
    # Ejecutar según las opciones
    if [ "$LIST_ONLY" = true ]; then
        list_rollbacks
        
    elif [ "$DRY_RUN" = true ]; then
        dry_run "$TARGET_SCRIPT"
        
    elif [ "$CONFIRM" = true ]; then
        local force_sql_flag="FALSE"
        if [ "$FORCE" = true ]; then
            force_sql_flag="TRUE"
        fi
        execute_rollback "$TARGET_SCRIPT" "$force_sql_flag"
        
    else
        # No debería llegar aquí por validate_arguments
        show_help
        exit 1
    fi
    
    log "INFO" "Script de rollback completado"
}

# Ejecutar función principal con todos los argumentos
main "$@"
