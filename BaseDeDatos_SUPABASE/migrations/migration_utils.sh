#!/bin/bash
# =====================================================
# SCRIPT DE UTILIDADES DE MIGRACIÓN
# =====================================================
# Archivo: migration_utils.sh
# Propósito: Utilidades y herramientas de soporte para migración
# Uso: ./migration_utils.sh [comando] [opciones]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Función de ayuda
show_help() {
    cat << EOF
🛠️  UTILIDADES DE MIGRACIÓN - MÁQUINA DE NOTICIAS

DESCRIPCIÓN:
    Herramientas de soporte para gestión y mantenimiento de migraciones.

USO:
    ./migration_utils.sh [COMANDO] [OPCIONES]

COMANDOS DISPONIBLES:
    status              Mostrar estado actual de migración
    history             Ver historial de migraciones
    validate            Validar integridad del sistema de migración
    cleanup             Limpiar logs y archivos temporales
    backup              Crear backup manual de base de datos
    restore             Restaurar desde backup específico
    check-deps          Verificar dependencias y prerrequisitos
    generate-report     Generar reporte completo de migración
    fix-permissions     Corregir permisos de archivos de migración
    verify-structure    Verificar estructura de directorios
    reset-tracking      Resetear tabla de tracking (PELIGROSO)

EJEMPLOS:
    # Ver estado actual
    ./migration_utils.sh status

    # Ver últimas 10 migraciones
    ./migration_utils.sh history --limit 10

    # Validar sistema completo
    ./migration_utils.sh validate --deep

    # Limpiar logs antiguos
    ./migration_utils.sh cleanup --days 30

    # Crear backup manual
    ./migration_utils.sh backup --name manual_backup

    # Generar reporte completo
    ./migration_utils.sh generate-report --format html

OPCIONES GLOBALES:
    --verbose           Output detallado
    --quiet             Output mínimo
    --dry-run           Mostrar qué haría sin ejecutar
    --help              Mostrar ayuda específica del comando

EOF
}

# Función para logging
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message"
}

# Comando: status
cmd_status() {
    echo -e "${BLUE}📊 ESTADO ACTUAL DE MIGRACIÓN${NC}"
    echo "================================="
    
    # Información de conexión
    echo -e "${YELLOW}Conexión:${NC}"
    echo "  Host: ${PGHOST:-localhost}:${PGPORT:-5432}"
    echo "  Database: ${PGDATABASE:-not_set}"
    echo "  User: ${PGUSER:-not_set}"
    echo "  Environment: ${MIGRATION_ENV:-not_set}"
    echo ""
    
    # Estado de migración
    if psql -c "SELECT 1;" &>/dev/null; then
        echo -e "${GREEN}✅ Conexión a BD: OK${NC}"
        
        # Verificar si existe tabla de tracking
        if psql -t -c "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'migration_history');" 2>/dev/null | grep -q "t"; then
            echo -e "${GREEN}✅ Sistema de tracking: OK${NC}"
            
            # Estadísticas de migración
            echo ""
            echo -e "${YELLOW}Estadísticas de Migración:${NC}"
            psql -c "
                SELECT 
                    category as \"Categoría\",
                    COUNT(*) as \"Scripts\",
                    COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) as \"Exitosos\",
                    COUNT(CASE WHEN status = 'FAILED' THEN 1 END) as \"Fallidos\",
                    MAX(executed_at)::DATE as \"Última Ejecución\"
                FROM migration_history 
                GROUP BY category 
                ORDER BY category;
            " 2>/dev/null || echo "  No hay datos de migración disponibles"
            
        else
            echo -e "${RED}❌ Sistema de tracking: NO INICIADO${NC}"
        fi
    else
        echo -e "${RED}❌ Conexión a BD: FALLO${NC}"
    fi
    
    # Estado de archivos
    echo ""
    echo -e "${YELLOW}Estado de Archivos:${NC}"
    local script_count=0
    for category in 01_schema 02_types_domains 03_tables 04_indexes 05_functions 06_triggers 07_materialized_views 08_reference_data; do
        if [[ -d "$SCRIPT_DIR/$category" ]]; then
            local files_in_category=$(find "$SCRIPT_DIR/$category" -name "*.sql" | wc -l)
            script_count=$((script_count + files_in_category))
            echo "  $category: $files_in_category scripts"
        fi
    done
    echo "  Total scripts: $script_count"
}

# Comando: history
cmd_history() {
    local limit=20
    local format="table"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --limit) limit="$2"; shift 2 ;;
            --format) format="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    
    echo -e "${BLUE}📜 HISTORIAL DE MIGRACIONES (Últimos $limit)${NC}"
    echo "================================================"
    
    if psql -c "SELECT 1;" &>/dev/null; then
        psql -c "
            SELECT 
                script_name as \"Script\",
                category as \"Categoría\",
                status as \"Estado\",
                executed_at::TIMESTAMP(0) as \"Ejecutado\",
                execution_time_ms || 'ms' as \"Tiempo\"
            FROM migration_history 
            ORDER BY executed_at DESC 
            LIMIT $limit;
        " 2>/dev/null || echo "No hay historial disponible"
    else
        echo "❌ No se puede conectar a la base de datos"
    fi
}

# Comando: validate
cmd_validate() {
    local deep_validation=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --deep) deep_validation=true; shift ;;
            *) shift ;;
        esac
    done
    
    echo -e "${BLUE}🔍 VALIDACIÓN DEL SISTEMA DE MIGRACIÓN${NC}"
    echo "======================================"
    
    local errors=0
    
    # Validar estructura de directorios
    echo "Validando estructura de directorios..."
    for category in 01_schema 02_types_domains 03_tables 04_indexes 05_functions 06_triggers 07_materialized_views 08_reference_data; do
        if [[ -d "$SCRIPT_DIR/$category" ]]; then
            echo "  ✅ $category"
        else
            echo "  ❌ $category (faltante)"
            errors=$((errors + 1))
        fi
    done
    
    # Validar archivos críticos
    echo ""
    echo "Validando archivos críticos..."
    local critical_files=(
        "00_000_migration_control.sql"
        "config/migration_config.sql"
        "deploy.sh"
        "rollback.sh"
        "README.md"
    )
    
    for file in "${critical_files[@]}"; do
        if [[ -f "$SCRIPT_DIR/$file" ]]; then
            echo "  ✅ $file"
        else
            echo "  ❌ $file (faltante)"
            errors=$((errors + 1))
        fi
    done
    
    # Validar permisos de ejecución
    echo ""
    echo "Validando permisos de archivos..."
    local executable_files=("deploy.sh" "rollback.sh" "test_migration.sh" "migration_utils.sh")
    
    for file in "${executable_files[@]}"; do
        if [[ -x "$SCRIPT_DIR/$file" ]]; then
            echo "  ✅ $file (ejecutable)"
        else
            echo "  ⚠️  $file (sin permisos de ejecución)"
            chmod +x "$SCRIPT_DIR/$file" 2>/dev/null && echo "    → Permisos corregidos" || echo "    → Error corrigiendo permisos"
        fi
    done
    
    # Validar conexión y sistema de tracking
    if [[ "$deep_validation" == true ]]; then
        echo ""
        echo "Validación profunda..."
        
        if psql -c "SELECT 1;" &>/dev/null; then
            echo "  ✅ Conexión a base de datos"
            
            # Validar funciones críticas
            local functions=("register_migration_execution" "is_script_executed" "execute_automated_validations")
            for func in "${functions[@]}"; do
                if psql -t -c "SELECT EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = '$func');" 2>/dev/null | grep -q "t"; then
                    echo "  ✅ Función $func"
                else
                    echo "  ❌ Función $func (faltante)"
                    errors=$((errors + 1))
                fi
            done
        else
            echo "  ❌ Conexión a base de datos"
            errors=$((errors + 1))
        fi
    fi
    
    echo ""
    if [[ $errors -eq 0 ]]; then
        echo -e "${GREEN}✅ VALIDACIÓN EXITOSA - Sistema completamente funcional${NC}"
    else
        echo -e "${RED}❌ VALIDACIÓN FALLÓ - $errors errores encontrados${NC}"
    fi
    
    return $errors
}

# Comando: cleanup
cmd_cleanup() {
    local days=7
    local dry_run=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --days) days="$2"; shift 2 ;;
            --dry-run) dry_run=true; shift ;;
            *) shift ;;
        esac
    done
    
    echo -e "${BLUE}🧹 LIMPIEZA DE ARCHIVOS TEMPORALES${NC}"
    echo "=================================="
    echo "Eliminando archivos de más de $days días..."
    
    # Limpiar logs antiguos
    if [[ "$dry_run" == true ]]; then
        echo "DRY RUN - Archivos que se eliminarían:"
        find "$LOG_DIR" -name "*.log" -mtime +$days -type f 2>/dev/null || true
    else
        local deleted_files=$(find "$LOG_DIR" -name "*.log" -mtime +$days -type f -delete -print 2>/dev/null | wc -l)
        echo "  ✅ Eliminados $deleted_files archivos de log"
    fi
    
    # Limpiar backups antiguos (si existen)
    if [[ -d "$LOG_DIR" ]]; then
        if [[ "$dry_run" == true ]]; then
            find "$LOG_DIR" -name "backup_*.sql" -mtime +$days -type f 2>/dev/null || true
        else
            local deleted_backups=$(find "$LOG_DIR" -name "backup_*.sql" -mtime +$days -type f -delete -print 2>/dev/null | wc -l)
            echo "  ✅ Eliminados $deleted_backups archivos de backup"
        fi
    fi
    
    echo "✅ Limpieza completada"
}

# Comando: backup
cmd_backup() {
    local backup_name="manual_$(date +%Y%m%d_%H%M%S)"
    local compress=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --name) backup_name="$2"; shift 2 ;;
            --compress) compress=true; shift ;;
            *) shift ;;
        esac
    done
    
    echo -e "${BLUE}💾 CREANDO BACKUP MANUAL${NC}"
    echo "========================"
    
    if [[ -z "${PGDATABASE:-}" ]]; then
        echo "❌ Error: PGDATABASE no está configurado"
        return 1
    fi
    
    mkdir -p "$LOG_DIR"
    local backup_file="$LOG_DIR/backup_${backup_name}.sql"
    
    echo "Creando backup de $PGDATABASE..."
    echo "Archivo: $backup_file"
    
    if pg_dump "$PGDATABASE" > "$backup_file"; then
        local file_size=$(du -h "$backup_file" | cut -f1)
        echo "✅ Backup creado exitosamente ($file_size)"
        
        if [[ "$compress" == true ]]; then
            echo "Comprimiendo backup..."
            if gzip "$backup_file"; then
                echo "✅ Backup comprimido: ${backup_file}.gz"
            fi
        fi
    else
        echo "❌ Error creando backup"
        return 1
    fi
}

# Comando: check-deps
cmd_check_deps() {
    echo -e "${BLUE}🔧 VERIFICACIÓN DE DEPENDENCIAS${NC}"
    echo "==============================="
    
    local errors=0
    
    # Verificar herramientas requeridas
    local required_tools=("psql" "pg_dump" "createdb" "dropdb")
    
    echo "Verificando herramientas PostgreSQL..."
    for tool in "${required_tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            local version=$(${tool} --version 2>/dev/null | head -n1)
            echo "  ✅ $tool: $version"
        else
            echo "  ❌ $tool: No encontrado"
            errors=$((errors + 1))
        fi
    done
    
    # Verificar herramientas opcionales
    echo ""
    echo "Verificando herramientas opcionales..."
    local optional_tools=("git" "curl" "jq" "gzip")
    
    for tool in "${optional_tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            echo "  ✅ $tool: Disponible"
        else
            echo "  ⚠️  $tool: No disponible (opcional)"
        fi
    done
    
    # Verificar variables de entorno
    echo ""
    echo "Verificando variables de entorno..."
    local env_vars=("PGHOST" "PGPORT" "PGDATABASE" "PGUSER")
    
    for var in "${env_vars[@]}"; do
        if [[ -n "${!var:-}" ]]; then
            echo "  ✅ $var: ${!var}"
        else
            echo "  ⚠️  $var: No configurada"
        fi
    done
    
    echo ""
    if [[ $errors -eq 0 ]]; then
        echo -e "${GREEN}✅ TODAS LAS DEPENDENCIAS VERIFICADAS${NC}"
    else
        echo -e "${RED}❌ $errors DEPENDENCIAS FALTANTES${NC}"
    fi
    
    return $errors
}

# Comando: generate-report
cmd_generate_report() {
    local format="text"
    local output_file=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --format) format="$2"; shift 2 ;;
            --output) output_file="$2"; shift 2 ;;
            *) shift ;;
        esac
    done
    
    echo -e "${BLUE}📊 GENERANDO REPORTE DE MIGRACIÓN${NC}"
    echo "================================="
    
    local report_file="${output_file:-$LOG_DIR/migration_report_$(date +%Y%m%d_%H%M%S).txt}"
    
    {
        echo "REPORTE DE MIGRACIÓN - MÁQUINA DE NOTICIAS"
        echo "=========================================="
        echo "Generado: $(date)"
        echo "Usuario: $(whoami)"
        echo "Host: $(hostname)"
        echo ""
        
        echo "CONFIGURACIÓN ACTUAL:"
        echo "- Entorno: ${MIGRATION_ENV:-not_set}"
        echo "- Base de datos: ${PGDATABASE:-not_set}"
        echo "- Host: ${PGHOST:-localhost}:${PGPORT:-5432}"
        echo "- Usuario: ${PGUSER:-not_set}"
        echo ""
        
        echo "ESTRUCTURA DE ARCHIVOS:"
        find "$SCRIPT_DIR" -name "*.sql" | wc -l | xargs echo "- Scripts SQL totales:"
        find "$SCRIPT_DIR" -name "*.sh" | wc -l | xargs echo "- Scripts shell:"
        find "$LOG_DIR" -name "*.log" 2>/dev/null | wc -l | xargs echo "- Archivos de log:"
        echo ""
        
        if psql -c "SELECT 1;" &>/dev/null 2>&1; then
            echo "ESTADO DE BASE DE DATOS:"
            echo "- Conexión: ✅ OK"
            
            if psql -t -c "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'migration_history');" 2>/dev/null | grep -q "t"; then
                echo "- Sistema de tracking: ✅ Activo"
                echo ""
                echo "ESTADÍSTICAS DE MIGRACIÓN:"
                psql -c "
                    SELECT 
                        'Total scripts ejecutados: ' || COUNT(*)
                    FROM migration_history;
                    
                    SELECT 
                        'Scripts exitosos: ' || COUNT(*)
                    FROM migration_history WHERE status = 'SUCCESS';
                    
                    SELECT 
                        'Scripts fallidos: ' || COUNT(*)
                    FROM migration_history WHERE status = 'FAILED';
                    
                    SELECT 
                        'Última migración: ' || MAX(executed_at)::TEXT
                    FROM migration_history;
                " -t 2>/dev/null
            else
                echo "- Sistema de tracking: ❌ No iniciado"
            fi
        else
            echo "ESTADO DE BASE DE DATOS:"
            echo "- Conexión: ❌ Error"
        fi
        
    } > "$report_file"
    
    echo "✅ Reporte generado: $report_file"
    
    # Mostrar reporte en pantalla también
    echo ""
    echo "CONTENIDO DEL REPORTE:"
    echo "====================="
    cat "$report_file"
}

# Procesamiento de argumentos principal
COMMAND=""
ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        status|history|validate|cleanup|backup|restore|check-deps|generate-report|fix-permissions|verify-structure|reset-tracking)
            COMMAND="$1"
            shift
            ;;
        --help)
            if [[ -n "$COMMAND" ]]; then
                echo "Ayuda específica para comando: $COMMAND"
                # Aquí se podría implementar ayuda específica
            else
                show_help
                exit 0
            fi
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

# Banner inicial
echo -e "${PURPLE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════╗
║           🛠️  UTILIDADES DE MIGRACIÓN             ║
║              Máquina de Noticias                  ║
║           Herramientas de Soporte                 ║
╚═══════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Ejecutar comando
if [[ -z "$COMMAND" ]]; then
    echo "❌ Error: No se especificó comando"
    echo "Use --help para ver comandos disponibles"
    exit 1
fi

case "$COMMAND" in
    status) cmd_status "${ARGS[@]}" ;;
    history) cmd_history "${ARGS[@]}" ;;
    validate) cmd_validate "${ARGS[@]}" ;;
    cleanup) cmd_cleanup "${ARGS[@]}" ;;
    backup) cmd_backup "${ARGS[@]}" ;;
    check-deps) cmd_check_deps "${ARGS[@]}" ;;
    generate-report) cmd_generate_report "${ARGS[@]}" ;;
    *)
        echo "❌ Error: Comando '$COMMAND' no implementado aún"
        echo "Comandos disponibles: status, history, validate, cleanup, backup, check-deps, generate-report"
        exit 1
        ;;
esac
