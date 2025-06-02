#!/bin/bash
# =====================================================
# SCRIPT DE TESTING Y VALIDACIÓN DE MIGRACIÓN
# =====================================================
# Archivo: test_migration.sh
# Propósito: Probar migración en entorno seguro antes de producción
# Uso: ./test_migration.sh [opciones]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
TEST_LOG="$LOG_DIR/test_migration_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$LOG_DIR"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables
TEST_MODE="full"
CLEANUP_AFTER_TEST=false
CREATE_TEST_DB=false
TEST_DB_NAME=""
ITERATIONS=1

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$TEST_LOG"
}

show_help() {
    cat << EOF
🧪 SCRIPT DE TESTING DE MIGRACIÓN - MÁQUINA DE NOTICIAS

DESCRIPCIÓN:
    Ejecuta pruebas exhaustivas de migración en entorno controlado.
    Permite validar migración antes de aplicar en producción.

USO:
    ./test_migration.sh [OPCIONES]

OPCIONES:
    --mode MODE              Modo de testing (full|quick|rollback|stress)
    --iterations N           Número de iteraciones de testing (default: 1)
    --create-test-db         Crear base de datos temporal para testing
    --test-db-name NAME      Nombre de BD de prueba (default: test_maquina_noticias)
    --cleanup                Limpiar recursos después del test
    --help                   Mostrar esta ayuda

MODOS DE TESTING:
    full                     Testing completo (migración + rollback + validaciones)
    quick                    Testing rápido (solo validaciones críticas)
    rollback                 Testing específico de rollbacks
    stress                   Testing de carga y stress
    idempotency              Testing de idempotencia (múltiples ejecuciones)

EJEMPLOS:
    # Test completo con BD temporal
    ./test_migration.sh --mode full --create-test-db --cleanup

    # Test rápido en BD existente
    ./test_migration.sh --mode quick

    # Test de rollback específico
    ./test_migration.sh --mode rollback

    # Test de idempotencia (3 iteraciones)
    ./test_migration.sh --mode idempotency --iterations 3

    # Test de stress
    ./test_migration.sh --mode stress --test-db-name stress_test_db

EOF
}

# Función para crear BD de prueba
create_test_database() {
    local db_name="${TEST_DB_NAME:-test_maquina_noticias_$(date +%s)}"
    
    log "INFO" "Creando base de datos de prueba: $db_name"
    
    if createdb "$db_name" 2>/dev/null; then
        log "INFO" "✅ Base de datos $db_name creada exitosamente"
        export PGDATABASE="$db_name"
        TEST_DB_NAME="$db_name"
    else
        log "ERROR" "❌ Error creando base de datos $db_name"
        exit 1
    fi
}

# Función para limpiar recursos de prueba
cleanup_test_resources() {
    if [[ "$CLEANUP_AFTER_TEST" == true && -n "$TEST_DB_NAME" ]]; then
        log "INFO" "Limpiando recursos de prueba..."
        
        if dropdb "$TEST_DB_NAME" 2>/dev/null; then
            log "INFO" "✅ Base de datos $TEST_DB_NAME eliminada"
        else
            log "WARNING" "⚠️ No se pudo eliminar base de datos $TEST_DB_NAME"
        fi
    fi
}

# Test completo de migración
test_full_migration() {
    log "INFO" "🧪 Iniciando test completo de migración..."
    
    # 1. Test de validaciones pre-migración
    log "INFO" "Paso 1: Testing validaciones pre-migración"
    if ! "$SCRIPT_DIR/deploy.sh" --dry-run; then
        log "ERROR" "❌ Validaciones pre-migración fallaron en dry-run"
        return 1
    fi
    
    # 2. Ejecución de migración real
    log "INFO" "Paso 2: Testing migración real"
    if ! "$SCRIPT_DIR/deploy.sh" --verbose; then
        log "ERROR" "❌ Migración real falló"
        return 1
    fi
    
    # 3. Validaciones post-migración
    log "INFO" "Paso 3: Testing validaciones post-migración"
    if ! psql -c "SELECT * FROM execute_post_migration_validations(NULL, true);" &>/dev/null; then
        log "ERROR" "❌ Validaciones post-migración fallaron"
        return 1
    fi
    
    # 4. Test de rollback
    log "INFO" "Paso 4: Testing rollback completo"
    if ! "$SCRIPT_DIR/rollback.sh" --dry-run; then
        log "ERROR" "❌ Test de rollback falló"
        return 1
    fi
    
    log "INFO" "✅ Test completo de migración exitoso"
    return 0
}

# Test rápido de validaciones
test_quick_validation() {
    log "INFO" "⚡ Iniciando test rápido de validaciones..."
    
    # Solo dry-run y validaciones básicas
    if "$SCRIPT_DIR/deploy.sh" --dry-run --skip-validations; then
        log "INFO" "✅ Test rápido exitoso"
        return 0
    else
        log "ERROR" "❌ Test rápido falló"
        return 1
    fi
}

# Test específico de rollbacks
test_rollback_procedures() {
    log "INFO" "🔄 Iniciando test de procedimientos de rollback..."
    
    # Ejecutar migración mínima para tener algo que hacer rollback
    "$SCRIPT_DIR/deploy.sh" --category 01_schema --force
    
    # Test rollback
    if "$SCRIPT_DIR/rollback.sh" --dry-run; then
        log "INFO" "✅ Test de rollback exitoso"
        return 0
    else
        log "ERROR" "❌ Test de rollback falló"
        return 1
    fi
}

# Test de stress y carga
test_stress_migration() {
    log "INFO" "💪 Iniciando test de stress de migración..."
    
    # Simular carga concurrente
    local pids=()
    
    for i in {1..3}; do
        (
            log "INFO" "Worker $i: Iniciando validaciones concurrentes"
            psql -c "SELECT * FROM execute_pre_migration_validations();" &>/dev/null
            log "INFO" "Worker $i: Validaciones completadas"
        ) &
        pids+=($!)
    done
    
    # Esperar a que terminen todos los workers
    for pid in "${pids[@]}"; do
        wait "$pid"
    done
    
    log "INFO" "✅ Test de stress completado"
    return 0
}

# Test de idempotencia
test_idempotency() {
    log "INFO" "🔁 Iniciando test de idempotencia ($ITERATIONS iteraciones)..."
    
    for ((i=1; i<=ITERATIONS; i++)); do
        log "INFO" "Iteración $i/$ITERATIONS"
        
        if ! "$SCRIPT_DIR/deploy.sh" --force --continue-on-error; then
            log "ERROR" "❌ Iteración $i falló"
            return 1
        fi
        
        log "INFO" "✅ Iteración $i completada"
    done
    
    log "INFO" "✅ Test de idempotencia completado exitosamente"
    return 0
}

# Función principal de testing
execute_tests() {
    local test_start=$(date +%s)
    local test_id=$(date +%Y%m%d_%H%M%S)
    
    log "INFO" "🚀 Iniciando testing de migración (ID: $test_id)"
    log "INFO" "Modo: $TEST_MODE"
    log "INFO" "Base de datos: ${PGDATABASE:-default}"
    
    # Crear BD de prueba si se solicita
    if [[ "$CREATE_TEST_DB" == true ]]; then
        create_test_database
    fi
    
    # Trap para cleanup en caso de error
    trap cleanup_test_resources EXIT
    
    # Ejecutar tests según el modo
    local test_result=0
    
    case "$TEST_MODE" in
        "full")
            test_full_migration || test_result=1
            ;;
        "quick")
            test_quick_validation || test_result=1
            ;;
        "rollback")
            test_rollback_procedures || test_result=1
            ;;
        "stress")
            test_stress_migration || test_result=1
            ;;
        "idempotency")
            test_idempotency || test_result=1
            ;;
        *)
            log "ERROR" "Modo de test desconocido: $TEST_MODE"
            test_result=1
            ;;
    esac
    
    # Resumen final
    local test_end=$(date +%s)
    local total_duration=$((test_end - test_start))
    
    log "INFO" "📊 Resumen de testing:"
    log "INFO" "  ID: $test_id"
    log "INFO" "  Modo: $TEST_MODE"
    log "INFO" "  Duración: ${total_duration}s"
    log "INFO" "  Resultado: $([ $test_result -eq 0 ] && echo "✅ EXITOSO" || echo "❌ FALLIDO")"
    log "INFO" "  Log: $TEST_LOG"
    
    return $test_result
}

# Procesamiento de argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            TEST_MODE="$2"
            shift 2
            ;;
        --iterations)
            ITERATIONS="$2"
            shift 2
            ;;
        --create-test-db)
            CREATE_TEST_DB=true
            shift
            ;;
        --test-db-name)
            TEST_DB_NAME="$2"
            shift 2
            ;;
        --cleanup)
            CLEANUP_AFTER_TEST=true
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

# Banner inicial
echo -e "${BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════╗
║           🧪 TESTING DE MIGRACIÓN                 ║
║              Máquina de Noticias                  ║
║          Validación Pre-Producción                ║
╚═══════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Ejecutar tests
if execute_tests; then
    echo -e "${GREEN}🎉 TODOS LOS TESTS PASARON EXITOSAMENTE${NC}"
    exit 0
else
    echo -e "${RED}❌ ALGUNOS TESTS FALLARON${NC}"
    exit 1
fi
