#!/bin/bash

# =============================================================================
# SCRIPT DE DESPLIEGUE - LA MÁQUINA DE NOTICIAS
# =============================================================================
# Script para desplegar la aplicación en el servidor
# Uso: ./deploy.sh [staging|production] [options]
#
# Opciones:
#   --no-backup       No crear backup antes del deploy
#   --force          Forzar deploy sin validaciones
#   --rollback       Ejecutar rollback al deploy anterior
#
# Ejemplos:
#   ./deploy.sh staging
#   ./deploy.sh production --no-backup
#   ./deploy.sh production --rollback
# =============================================================================

set -e  # Salir en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración por defecto
ENVIRONMENT=""
NO_BACKUP=false
FORCE_DEPLOY=false
ROLLBACK=false
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
    staging     Deploy a ambiente de staging
    production  Deploy a ambiente de producción

Opciones:
    --no-backup     No crear backup antes del deploy
    --force         Forzar deploy sin validaciones
    --rollback      Ejecutar rollback al deploy anterior
    --help          Mostrar esta ayuda

Ejemplos:
    $0 staging
    $0 production --no-backup
    $0 production --rollback
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
            --no-backup)
                NO_BACKUP=true
                shift
                ;;
            --force)
                FORCE_DEPLOY=true
                shift
                ;;
            --rollback)
                ROLLBACK=true
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

    # Validar que se especificó un ambiente
    if [[ -z "$ENVIRONMENT" ]]; then
        error "Debe especificar un ambiente: staging o production"
    fi
}

# =============================================================================
# FUNCIONES DE VALIDACIÓN
# =============================================================================

validate_environment() {
    log "Validando ambiente: $ENVIRONMENT"
    
    # Configurar rutas según ambiente
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
    
    success "Ambiente validado: $ENVIRONMENT"
}

validate_docker() {
    log "Validando Docker y Docker Compose..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker no está instalado"
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose no está instalado"
    fi
    
    # Verificar que Docker está corriendo
    if ! docker info &> /dev/null; then
        error "Docker no está corriendo"
    fi
    
    success "Docker validado"
}

validate_git() {
    log "Validando repositorio Git..."
    
    cd "$PROJECT_ROOT"
    
    if [[ ! -d ".git" ]]; then
        error "No es un repositorio Git: $PROJECT_ROOT"
    fi
    
    # Verificar que no hay cambios sin commitear (a menos que sea force)
    if [[ "$FORCE_DEPLOY" == false ]]; then
        if ! git diff-index --quiet HEAD --; then
            error "Hay cambios sin commitear. Use --force para omitir esta validación"
        fi
    fi
    
    success "Repositorio Git validado"
}

# =============================================================================
# FUNCIONES DE BACKUP
# =============================================================================

create_backup() {
    if [[ "$NO_BACKUP" == true ]]; then
        warning "Saltando backup (--no-backup especificado)"
        return 0
    fi
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_path="$BACKUP_DIR/${timestamp}_${ENVIRONMENT}"
    
    log "Creando backup en: $backup_path"
    
    mkdir -p "$backup_path"
    
    # Backup del código
    log "Backup del código fuente..."
    cp -r "$PROJECT_ROOT" "$backup_path/code"
    
    # Backup de volúmenes Docker críticos
    log "Backup de volúmenes Docker..."
    
    # Redis data
    if docker volume ls | grep -q "${COMPOSE_PROJECT}_redis_data"; then
        docker run --rm \
            -v "${COMPOSE_PROJECT}_redis_data":/data \
            -v "$backup_path":/backup \
            alpine tar czf /backup/redis_data.tar.gz -C /data . || warning "No se pudo respaldar Redis"
    fi
    
    # Scrapyd logs
    if docker volume ls | grep -q "${COMPOSE_PROJECT}_scrapyd_logs"; then
        docker run --rm \
            -v "${COMPOSE_PROJECT}_scrapyd_logs":/data \
            -v "$backup_path":/backup \
            alpine tar czf /backup/scrapyd_logs.tar.gz -C /data . || warning "No se pudo respaldar logs de Scrapyd"
    fi
    
    # ScrapydWeb data
    if docker volume ls | grep -q "${COMPOSE_PROJECT}_scrapydweb_data"; then
        docker run --rm \
            -v "${COMPOSE_PROJECT}_scrapydweb_data":/data \
            -v "$backup_path":/backup \
            alpine tar czf /backup/scrapydweb_data.tar.gz -C /data . || warning "No se pudo respaldar datos de ScrapydWeb"
    fi
    
    # Información del backup
    cat > "$backup_path/backup_info.txt" << EOF
Backup created: $(date)
Environment: $ENVIRONMENT
Git commit: $(git rev-parse HEAD)
Git branch: $(git rev-parse --abbrev-ref HEAD)
Backup script version: 1.0
EOF
    
    success "Backup creado: $backup_path"
    echo "$backup_path" > /tmp/last_backup_path
}

# =============================================================================
# FUNCIONES DE ROLLBACK
# =============================================================================

execute_rollback() {
    log "Ejecutando rollback para $ENVIRONMENT..."
    
    # Encontrar el backup más reciente
    local latest_backup=$(ls -1t "$BACKUP_DIR" | grep "_${ENVIRONMENT}" | head -n 1)
    
    if [[ -z "$latest_backup" ]]; then
        error "No se encontró backup para rollback del ambiente: $ENVIRONMENT"
    fi
    
    local backup_path="$BACKUP_DIR/$latest_backup"
    
    log "Restaurando desde backup: $backup_path"
    
    # Parar servicios
    log "Parando servicios..."
    cd "$PROJECT_ROOT"
    docker-compose -p "$COMPOSE_PROJECT" down || warning "Error al parar servicios"
    
    # Restaurar código
    log "Restaurando código..."
    rm -rf "${PROJECT_ROOT:?}"/* || error "Error al limpiar directorio"
    cp -r "$backup_path/code/"* "$PROJECT_ROOT/" || error "Error al restaurar código"
    
    # Restaurar volúmenes si existen
    log "Restaurando volúmenes..."
    
    if [[ -f "$backup_path/redis_data.tar.gz" ]]; then
        docker run --rm \
            -v "$backup_path":/backup \
            -v "${COMPOSE_PROJECT}_redis_data":/data \
            alpine tar xzf /backup/redis_data.tar.gz -C /data || warning "Error al restaurar Redis"
    fi
    
    if [[ -f "$backup_path/scrapyd_logs.tar.gz" ]]; then
        docker run --rm \
            -v "$backup_path":/backup \
            -v "${COMPOSE_PROJECT}_scrapyd_logs":/data \
            alpine tar xzf /backup/scrapyd_logs.tar.gz -C /data || warning "Error al restaurar logs de Scrapyd"
    fi
    
    # Reiniciar servicios
    log "Reiniciando servicios..."
    cd "$PROJECT_ROOT"
    docker-compose -p "$COMPOSE_PROJECT" up -d || error "Error al reiniciar servicios"
    
    success "Rollback completado desde: $latest_backup"
}

# =============================================================================
# FUNCIONES DE DEPLOY
# =============================================================================

update_code() {
    log "Actualizando código desde Git..."
    
    cd "$PROJECT_ROOT"
    
    # Determinar rama según ambiente
    local branch="main"
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        branch="develop"
    fi
    
    log "Actualizando rama: $branch"
    
    git fetch origin
    git reset --hard "origin/$branch"
    
    local new_commit=$(git rev-parse HEAD)
    log "Nuevo commit: $new_commit"
    
    # Manejar archivos LFS
    handle_lfs_files
    
    success "Código actualizado"
}

handle_lfs_files() {
    log "Manejando archivos Git LFS..."
    
    # Usar script especializado si está disponible
    if [[ -f ".github/scripts/lfs-manager.sh" ]]; then
        log "Usando LFS Manager para manejo optimizado..."
        if ./.github/scripts/lfs-manager.sh check; then
            ./.github/scripts/lfs-manager.sh pull --timeout=300 || warning "Algunos archivos LFS no se pudieron descargar"
        else
            log "No hay archivos LFS para procesar"
        fi
    else
        # Fallback al método tradicional
        log "Usando método tradicional de LFS..."
        if git lfs ls-files | head -1 > /dev/null 2>&1; then
            log "LFS detectado, descargando archivos..."
            timeout 300 git lfs pull || warning "Error descargando algunos archivos LFS"
        else
            log "No se detectaron archivos LFS"
        fi
    fi
}

configure_environment() {
    log "Configurando variables de entorno para $ENVIRONMENT..."
    
    cd "$PROJECT_ROOT"
    
    # Verificar que existe .env.example
    if [[ ! -f ".env.example" ]]; then
        error "Archivo .env.example no encontrado"
    fi
    
    # Crear .env específico para el ambiente
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        create_staging_env
    elif [[ "$ENVIRONMENT" == "production" ]]; then
        create_production_env
    fi
    
    success "Variables de entorno configuradas"
}

create_staging_env() {
    cat > .env << 'EOF'
# === CONFIGURACIÓN STAGING ===
ENVIRONMENT=staging
DEBUG_MODE=false
LOG_LEVEL=INFO

# Configuración básica
SCRAPER_TARGET_URLS=https://example.com
SCRAPYDWEB_USERNAME=admin
SCRAPYDWEB_PASSWORD=staging_password_change_me

# URLs internas
PIPELINE_API_URL=http://module_pipeline:8003
DASHBOARD_API_URL=http://module_dashboard_review_backend:8004
REDIS_URL=redis://redis:6379
SPIDER_FACTORY_REDIS_HOST=redis

# IMPORTANTE: Agregar manualmente las variables secretas:
# SUPABASE_URL=
# SUPABASE_ANON_KEY=
# SUPABASE_SERVICE_ROLE_KEY=
# GROQ_API_KEY=
# FIRECRAWL_API_KEY=
EOF
    
    warning "IMPORTANTE: Debe configurar manualmente las variables secretas en .env"
}

create_production_env() {
    cat > .env << 'EOF'
# === CONFIGURACIÓN PRODUCCIÓN ===
ENVIRONMENT=production
DEBUG_MODE=false
LOG_LEVEL=WARNING

# Configuración básica
SCRAPER_TARGET_URLS=https://production-urls.com
SCRAPYDWEB_USERNAME=admin
SCRAPYDWEB_PASSWORD=production_password_change_me

# URLs internas
PIPELINE_API_URL=http://module_pipeline:8003
DASHBOARD_API_URL=http://module_dashboard_review_backend:8004
REDIS_URL=redis://redis:6379
SPIDER_FACTORY_REDIS_HOST=redis

# IMPORTANTE: Agregar manualmente las variables secretas:
# SUPABASE_URL=
# SUPABASE_ANON_KEY=
# SUPABASE_SERVICE_ROLE_KEY=
# GROQ_API_KEY=
# FIRECRAWL_API_KEY=
EOF
    
    warning "IMPORTANTE: Debe configurar manualmente las variables secretas en .env"
}

build_and_deploy() {
    log "Construyendo y desplegando servicios..."
    
    cd "$PROJECT_ROOT"
    
    # Validar docker-compose.yml
    docker-compose config -q || error "docker-compose.yml inválido"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        # Deploy gradual para producción
        deploy_production_gradual
    else
        # Deploy directo para staging
        deploy_staging_direct
    fi
    
    success "Servicios desplegados"
}

deploy_staging_direct() {
    log "Deploy directo para staging..."
    
    # Parar servicios
    docker-compose -p "$COMPOSE_PROJECT" down --remove-orphans || true
    
    # Construir y levantar
    docker-compose -p "$COMPOSE_PROJECT" build --no-cache
    docker-compose -p "$COMPOSE_PROJECT" up -d
    
    log "Esperando que los servicios estén listos..."
    sleep 30
}

deploy_production_gradual() {
    log "Deploy gradual para producción..."
    
    # 1. Backend services primero
    log "Actualizando servicios backend..."
    docker-compose -p "$COMPOSE_PROJECT" build --no-cache \
        module_pipeline module_dashboard_review_backend spider_factory_backend
    docker-compose -p "$COMPOSE_PROJECT" up -d \
        module_pipeline module_dashboard_review_backend spider_factory_backend
    
    sleep 15
    
    # 2. Frontend services
    log "Actualizando servicios frontend..."
    docker-compose -p "$COMPOSE_PROJECT" build --no-cache \
        module_dashboard_review_frontend module_spider_factory_frontend
    docker-compose -p "$COMPOSE_PROJECT" up -d \
        module_dashboard_review_frontend module_spider_factory_frontend
    
    sleep 10
    
    # 3. Infrastructure services
    log "Actualizando servicios de infraestructura..."
    docker-compose -p "$COMPOSE_PROJECT" build --no-cache \
        module_scraper scrapyd scrapydweb
    docker-compose -p "$COMPOSE_PROJECT" up -d \
        module_scraper scrapyd scrapydweb
    
    sleep 10
    
    # 4. Proxy al final
    log "Actualizando proxy..."
    docker-compose -p "$COMPOSE_PROJECT" build --no-cache nginx_reverse_proxy
    docker-compose -p "$COMPOSE_PROJECT" up -d nginx_reverse_proxy
    
    log "Esperando estabilización..."
    sleep 30
}

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

main() {
    echo "=========================================="
    echo "🚀 DEPLOY - LA MÁQUINA DE NOTICIAS"
    echo "=========================================="
    echo
    
    parse_args "$@"
    
    log "Iniciando deploy para ambiente: $ENVIRONMENT"
    
    # Ejecutar rollback si se solicitó
    if [[ "$ROLLBACK" == true ]]; then
        validate_environment
        execute_rollback
        log "Rollback completado"
        exit 0
    fi
    
    # Validaciones
    validate_environment
    validate_docker
    validate_git
    
    # Crear backup
    create_backup
    
    # Deploy
    update_code
    configure_environment
    build_and_deploy
    
    # Ejecutar health check
    log "Ejecutando health check..."
    if [[ -f "$(dirname "$0")/health-check.sh" ]]; then
        "$(dirname "$0")/health-check.sh" "$ENVIRONMENT"
    else
        warning "Script de health check no encontrado"
    fi
    
    success "¡Deploy completado exitosamente!"
    log "Ambiente: $ENVIRONMENT"
    log "Timestamp: $(date)"
    
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        log "URL Staging: http://$(hostname):3001"
    elif [[ "$ENVIRONMENT" == "production" ]]; then
        log "URL Producción: https://$(hostname)"
    fi
}

# Ejecutar función principal
main "$@"