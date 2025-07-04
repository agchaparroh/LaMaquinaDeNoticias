#!/bin/bash

# =============================================================================
# ROLLBACK SCRIPT - LA MÁQUINA DE NOTICIAS
# =============================================================================
# Script para ejecutar rollback a una versión anterior
# Uso: ./rollback.sh [staging|production] [options]
#
# Opciones:
#   --backup-id=ID    ID específico del backup para rollback
#   --list-backups    Listar backups disponibles
#   --auto            Rollback automático al backup más reciente
#   --force           Forzar rollback sin confirmación
#
# Ejemplos:
#   ./rollback.sh staging --auto
#   ./rollback.sh production --backup-id=20231201_143022
#   ./rollback.sh staging --list-backups
# =============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración por defecto
ENVIRONMENT=""
BACKUP_ID=""
LIST_BACKUPS=false
AUTO_ROLLBACK=false
FORCE_ROLLBACK=false
PROJECT_ROOT="/opt/lamaquina"
BACKUP_DIR="/opt/backups/lamaquina"

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

usage() {
    cat << EOF
Uso: $0 [staging|production] [opciones]

Ambientes:
    staging     Rollback en ambiente de staging
    production  Rollback en ambiente de producción

Opciones:
    --backup-id=ID      ID específico del backup para rollback
    --list-backups      Listar backups disponibles
    --auto              Rollback automático al backup más reciente
    --force             Forzar rollback sin confirmación
    --help              Mostrar esta ayuda

Ejemplos:
    $0 staging --auto
    $0 production --backup-id=20231201_143022_production
    $0 staging --list-backups
    $0 production --force --auto
EOF
    exit 1
}

# =============================================================================
# PARSEO DE ARGUMENTOS
# =============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            staging|production)
                ENVIRONMENT="$1"
                shift
                ;;
            --backup-id=*)
                BACKUP_ID="${1#*=}"
                shift
                ;;
            --list-backups)
                LIST_BACKUPS=true
                shift
                ;;
            --auto)
                AUTO_ROLLBACK=true
                shift
                ;;
            --force)
                FORCE_ROLLBACK=true
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

    if [[ -z "$ENVIRONMENT" ]]; then
        error "Debe especificar un ambiente: staging o production"
    fi
}

# =============================================================================
# CONFIGURACIÓN POR AMBIENTE
# =============================================================================

configure_environment() {
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        PROJECT_ROOT="/opt/lamaquina-staging"
        COMPOSE_PROJECT="lamaquina_staging"
    elif [[ "$ENVIRONMENT" == "production" ]]; then
        PROJECT_ROOT="/opt/lamaquina-production"
        COMPOSE_PROJECT="lamaquina_production"
    else
        error "Ambiente inválido: $ENVIRONMENT"
    fi
    
    # Verificar que el directorio del proyecto existe
    if [[ ! -d "$PROJECT_ROOT" ]]; then
        error "Directorio del proyecto no encontrado: $PROJECT_ROOT"
    fi
    
    # Verificar que el directorio de backups existe
    if [[ ! -d "$BACKUP_DIR" ]]; then
        error "Directorio de backups no encontrado: $BACKUP_DIR"
    fi
}

# =============================================================================
# FUNCIONES DE BACKUP
# =============================================================================

list_available_backups() {
    log "Listando backups disponibles para $ENVIRONMENT..."
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        warning "No se encontró directorio de backups: $BACKUP_DIR"
        return 1
    fi
    
    local backups=($(ls -1t "$BACKUP_DIR" | grep "_${ENVIRONMENT}" 2>/dev/null || true))
    
    if [[ ${#backups[@]} -eq 0 ]]; then
        warning "No se encontraron backups para el ambiente: $ENVIRONMENT"
        return 1
    fi
    
    echo
    echo "📦 BACKUPS DISPONIBLES PARA $ENVIRONMENT:"
    echo "=========================================="
    
    local count=1
    for backup in "${backups[@]}"; do
        local backup_path="$BACKUP_DIR/$backup"
        local info_file="$backup_path/backup_info.txt"
        
        echo "[$count] $backup"
        
        if [[ -f "$info_file" ]]; then
            echo "    📅 $(grep "Backup created:" "$info_file" 2>/dev/null | cut -d: -f2- || echo "Fecha desconocida")"
            echo "    📝 $(grep "Git commit:" "$info_file" 2>/dev/null | cut -d: -f2- || echo "Commit desconocido")"
            echo "    🌿 $(grep "Git branch:" "$info_file" 2>/dev/null | cut -d: -f2- || echo "Branch desconocida")"
        else
            echo "    ⚠️  Sin información adicional"
        fi
        
        # Mostrar tamaño del backup
        local backup_size=$(du -sh "$backup_path" 2>/dev/null | cut -f1 || echo "unknown")
        echo "    💾 Tamaño: $backup_size"
        
        echo
        count=$((count + 1))
    done
    
    echo "Total: ${#backups[@]} backups encontrados"
}

find_latest_backup() {
    local latest_backup=$(ls -1t "$BACKUP_DIR" | grep "_${ENVIRONMENT}" | head -n 1 2>/dev/null || echo "")
    
    if [[ -z "$latest_backup" ]]; then
        error "No se encontró ningún backup para el ambiente: $ENVIRONMENT"
    fi
    
    echo "$latest_backup"
}

validate_backup() {
    local backup_id="$1"
    local backup_path="$BACKUP_DIR/$backup_id"
    
    log "Validando backup: $backup_id"
    
    # Verificar que el backup existe
    if [[ ! -d "$backup_path" ]]; then
        error "Backup no encontrado: $backup_path"
    fi
    
    # Verificar que es para el ambiente correcto
    if [[ "$backup_id" != *"_${ENVIRONMENT}" ]]; then
        error "El backup $backup_id no es para el ambiente $ENVIRONMENT"
    fi
    
    # Verificar que contiene los archivos necesarios
    if [[ ! -d "$backup_path/code" ]]; then
        error "Backup inválido: no contiene directorio de código"
    fi
    
    # Verificar integridad básica
    local expected_files=(
        "backup_info.txt"
        "code/.git"
        "code/docker-compose.yml"
    )
    
    for file in "${expected_files[@]}"; do
        if [[ ! -e "$backup_path/$file" ]]; then
            warning "Archivo esperado no encontrado en backup: $file"
        fi
    done
    
    success "Backup validado: $backup_id"
}

# =============================================================================
# FUNCIONES DE ROLLBACK
# =============================================================================

create_pre_rollback_backup() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local pre_rollback_backup="$BACKUP_DIR/${timestamp}_${ENVIRONMENT}_pre_rollback"
    
    log "Creando backup pre-rollback en: $pre_rollback_backup"
    
    mkdir -p "$pre_rollback_backup"
    
    # Backup del estado actual
    cp -r "$PROJECT_ROOT" "$pre_rollback_backup/code"
    
    # Información del backup
    cat > "$pre_rollback_backup/backup_info.txt" << EOF
Pre-rollback backup created: $(date)
Environment: $ENVIRONMENT
Original Git commit: $(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null || echo "unknown")
Original Git branch: $(cd "$PROJECT_ROOT" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
Rollback reason: Manual rollback initiated
EOF
    
    success "Backup pre-rollback creado: $pre_rollback_backup"
}

stop_services() {
    log "Parando servicios de $ENVIRONMENT..."
    
    cd "$PROJECT_ROOT"
    
    # Intentar parar servicios graciosamente
    if docker-compose -p "$COMPOSE_PROJECT" ps -q | grep -q .; then
        log "Parando servicios con docker-compose..."
        docker-compose -p "$COMPOSE_PROJECT" down --timeout 30 || warning "Error al parar algunos servicios"
    else
        log "No hay servicios corriendo"
    fi
    
    # Verificar que todos los contenedores se pararon
    local running_containers=$(docker ps --filter "label=com.docker.compose.project=$COMPOSE_PROJECT" -q)
    if [[ -n "$running_containers" ]]; then
        warning "Forzando parada de contenedores persistentes..."
        echo "$running_containers" | xargs docker stop --timeout 10 || true
    fi
    
    success "Servicios parados"
}

restore_code() {
    local backup_id="$1"
    local backup_path="$BACKUP_DIR/$backup_id"
    
    log "Restaurando código desde backup: $backup_id"
    
    # Limpiar directorio actual (con seguridad)
    if [[ "$PROJECT_ROOT" != "/" ]] && [[ "$PROJECT_ROOT" != "/opt" ]]; then
        log "Limpiando directorio: $PROJECT_ROOT"
        rm -rf "${PROJECT_ROOT:?}"/* || error "Error al limpiar directorio"
        rm -rf "${PROJECT_ROOT:?}"/.[!.]* 2>/dev/null || true  # Archivos ocultos
    else
        error "Ruta de proyecto insegura para limpiar: $PROJECT_ROOT"
    fi
    
    # Restaurar código
    log "Copiando código desde backup..."
    cp -r "$backup_path/code/"* "$PROJECT_ROOT/" || error "Error al restaurar código"
    cp -r "$backup_path/code/".* "$PROJECT_ROOT/" 2>/dev/null || true  # Archivos ocultos
    
    success "Código restaurado"
}

restore_volumes() {
    local backup_id="$1"
    local backup_path="$BACKUP_DIR/$backup_id"
    
    log "Restaurando volúmenes Docker..."
    
    # Lista de volúmenes a restaurar
    local volumes=(
        "redis_data"
        "scrapyd_logs"
        "scrapyd_eggs"
        "scrapydweb_data"
    )
    
    for volume in "${volumes[@]}"; do
        local volume_name="${COMPOSE_PROJECT}_${volume}"
        local backup_file="$backup_path/${volume}.tar.gz"
        
        if [[ -f "$backup_file" ]]; then
            log "Restaurando volumen: $volume_name"
            
            # Verificar si el volumen existe, crearlo si no
            if ! docker volume ls | grep -q "$volume_name"; then
                docker volume create "$volume_name"
            fi
            
            # Restaurar datos
            docker run --rm \
                -v "$backup_path":/backup \
                -v "$volume_name":/data \
                alpine sh -c "cd /data && rm -rf * && tar xzf /backup/${volume}.tar.gz" \
                || warning "Error al restaurar volumen: $volume_name"
                
            success "Volumen restaurado: $volume_name"
        else
            warning "Backup de volumen no encontrado: $backup_file"
        fi
    done
}

start_services() {
    log "Iniciando servicios..."
    
    cd "$PROJECT_ROOT"
    
    # Validar docker-compose.yml
    if ! docker-compose config -q; then
        error "docker-compose.yml inválido en el backup"
    fi
    
    # Construir y levantar servicios
    log "Construyendo imágenes..."
    docker-compose -p "$COMPOSE_PROJECT" build --no-cache || error "Error al construir imágenes"
    
    log "Levantando servicios..."
    docker-compose -p "$COMPOSE_PROJECT" up -d || error "Error al levantar servicios"
    
    # Esperar que los servicios estén listos
    log "Esperando que los servicios estén listos..."
    sleep 30
    
    success "Servicios iniciados"
}

verify_rollback() {
    log "Verificando rollback..."
    
    # Ejecutar health check si está disponible
    local health_script="$(dirname "$0")/health-check.sh"
    if [[ -f "$health_script" ]]; then
        log "Ejecutando health check..."
        if "$health_script" "$ENVIRONMENT" --timeout=15; then
            success "Health check pasó - rollback exitoso"
        else
            error "Health check falló - rollback puede tener problemas"
        fi
    else
        warning "Script de health check no encontrado, verificando manualmente..."
        
        # Verificaciones básicas
        local failed_checks=0
        
        # Verificar que los contenedores están corriendo
        local running_containers=$(docker-compose -p "$COMPOSE_PROJECT" ps --services --filter status=running | wc -l)
        local total_services=$(docker-compose -p "$COMPOSE_PROJECT" config --services | wc -l)
        
        if [[ "$running_containers" -ge $((total_services * 70 / 100)) ]]; then
            success "Al menos 70% de los servicios están corriendo"
        else
            warning "Menos del 70% de los servicios están corriendo"
            failed_checks=$((failed_checks + 1))
        fi
        
        # Verificar endpoints básicos
        local endpoints=("http://localhost:8003/health" "http://localhost:8004/health")
        for endpoint in "${endpoints[@]}"; do
            if curl -f -s --max-time 10 "$endpoint" >/dev/null; then
                success "Endpoint disponible: $endpoint"
            else
                warning "Endpoint no disponible: $endpoint"
                failed_checks=$((failed_checks + 1))
            fi
        done
        
        if [[ "$failed_checks" -eq 0 ]]; then
            success "Verificación manual exitosa"
        else
            warning "Verificación manual completada con $failed_checks advertencias"
        fi
    fi
}

# =============================================================================
# FUNCIÓN DE CONFIRMACIÓN
# =============================================================================

confirm_rollback() {
    if [[ "$FORCE_ROLLBACK" == true ]]; then
        return 0
    fi
    
    echo
    warning "¡ADVERTENCIA! Está a punto de ejecutar un ROLLBACK"
    echo "Ambiente: $ENVIRONMENT"
    echo "Backup: $BACKUP_ID"
    echo
    echo "Esto va a:"
    echo "1. Parar todos los servicios actuales"
    echo "2. Reemplazar el código actual con el del backup"
    echo "3. Restaurar volúmenes Docker desde el backup"
    echo "4. Reiniciar todos los servicios"
    echo
    
    read -p "¿Está seguro de que quiere continuar? (escriba 'yes' para confirmar): " confirm
    
    if [[ "$confirm" != "yes" ]]; then
        log "Rollback cancelado por el usuario"
        exit 0
    fi
    
    echo
    log "Rollback confirmado, procediendo..."
}

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

main() {
    echo "=========================================="
    echo "🔄 ROLLBACK - LA MÁQUINA DE NOTICIAS"
    echo "=========================================="
    echo
    
    parse_args "$@"
    configure_environment
    
    # Si solo se pide listar backups
    if [[ "$LIST_BACKUPS" == true ]]; then
        list_available_backups
        exit 0
    fi
    
    # Determinar qué backup usar
    if [[ "$AUTO_ROLLBACK" == true ]]; then
        BACKUP_ID=$(find_latest_backup)
        log "Rollback automático al backup más reciente: $BACKUP_ID"
    elif [[ -z "$BACKUP_ID" ]]; then
        error "Debe especificar --backup-id o usar --auto para rollback automático"
    fi
    
    # Validar backup
    validate_backup "$BACKUP_ID"
    
    # Mostrar información del backup
    local backup_path="$BACKUP_DIR/$BACKUP_ID"
    local info_file="$backup_path/backup_info.txt"
    
    if [[ -f "$info_file" ]]; then
        echo
        log "Información del backup:"
        cat "$info_file" | sed 's/^/  /'
        echo
    fi
    
    # Confirmar rollback
    confirm_rollback
    
    # Crear backup del estado actual
    create_pre_rollback_backup
    
    # Ejecutar rollback
    stop_services
    restore_code "$BACKUP_ID"
    restore_volumes "$BACKUP_ID"
    start_services
    
    # Verificar resultado
    verify_rollback
    
    success "¡Rollback completado exitosamente!"
    log "Ambiente: $ENVIRONMENT"
    log "Backup restaurado: $BACKUP_ID"
    log "Timestamp: $(date)"
    
    echo
    echo "=========================================="
    echo "✅ ROLLBACK EXITOSO"
    echo "=========================================="
    
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        echo "URL Staging: http://$(hostname):3001"
    elif [[ "$ENVIRONMENT" == "production" ]]; then
        echo "URL Producción: https://$(hostname)"
    fi
    
    echo "=========================================="
}

# Verificar dependencias básicas
if ! command -v docker &> /dev/null; then
    error "Docker no está instalado"
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose no está instalado"
fi

# Ejecutar función principal
main "$@"