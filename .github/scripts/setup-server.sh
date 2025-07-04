#!/bin/bash

# =============================================================================
# SCRIPT DE CONFIGURACIÓN AUTOMÁTICA DEL SERVIDOR
# =============================================================================
# Configura automáticamente un servidor para La Máquina de Noticias
# Uso: ./setup-server.sh [staging|production] [--repo-url=URL]
#
# IMPORTANTE: Ejecutar DESDE el servidor, no desde tu máquina local
# Ejemplo en el servidor:
#   wget https://raw.githubusercontent.com/tu-usuario/repo/main/.github/scripts/setup-server.sh
#   chmod +x setup-server.sh
#   sudo ./setup-server.sh staging --repo-url=https://github.com/tu-usuario/LaMaquinaDeNoticias.git
# =============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
ENVIRONMENT=""
REPO_URL=""
PROJECT_ROOT=""
DEPLOY_USER="deploy"

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
Uso: $0 [staging|production] --repo-url=URL

Argumentos:
    staging|production    Tipo de ambiente a configurar
    --repo-url=URL       URL del repositorio Git

Ejemplo:
    $0 staging --repo-url=https://github.com/usuario/LaMaquinaDeNoticias.git

IMPORTANTE: 
- Ejecutar DESDE el servidor como root o con sudo
- Tener acceso a internet para descargar dependencias
- El repositorio debe ser público o tener SSH configurado
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
            --repo-url=*)
                REPO_URL="${1#*=}"
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
    
    if [[ -z "$REPO_URL" ]]; then
        error "Debe especificar la URL del repositorio con --repo-url"
    fi
    
    # Configurar rutas según ambiente
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        PROJECT_ROOT="/opt/lamaquina-staging"
    else
        PROJECT_ROOT="/opt/lamaquina-production"
    fi
}

# =============================================================================
# FUNCIONES DE INSTALACIÓN
# =============================================================================

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Este script debe ejecutarse como root (usar sudo)"
    fi
}

install_system_dependencies() {
    log "Instalando dependencias del sistema..."
    
    # Actualizar paquetes
    apt update && apt upgrade -y
    
    # Instalar dependencias básicas
    apt install -y \
        curl \
        wget \
        git \
        unzip \
        jq \
        bc \
        htop \
        nano \
        tree \
        net-tools \
        ca-certificates \
        gnupg \
        lsb-release
    
    success "Dependencias del sistema instaladas"
}

install_docker() {
    log "Instalando Docker..."
    
    # Verificar si Docker ya está instalado
    if command -v docker &> /dev/null; then
        success "Docker ya está instalado: $(docker --version)"
        return 0
    fi
    
    # Instalar Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Iniciar y habilitar Docker
    systemctl start docker
    systemctl enable docker
    
    success "Docker instalado: $(docker --version)"
}

install_docker_compose() {
    log "Instalando Docker Compose..."
    
    # Verificar si Docker Compose ya está instalado
    if command -v docker-compose &> /dev/null; then
        success "Docker Compose ya está instalado: $(docker-compose --version)"
        return 0
    fi
    
    # Obtener última versión
    local latest_version=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | jq -r '.tag_name')
    
    # Descargar Docker Compose
    curl -L "https://github.com/docker/compose/releases/download/${latest_version}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # Dar permisos de ejecución
    chmod +x /usr/local/bin/docker-compose
    
    # Crear symlink para compatibilidad
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    success "Docker Compose instalado: $(docker-compose --version)"
}

install_git_lfs() {
    log "Instalando Git LFS..."
    
    # Verificar si Git LFS ya está instalado
    if command -v git-lfs &> /dev/null; then
        success "Git LFS ya está instalado: $(git lfs version)"
        return 0
    fi
    
    # Instalar Git LFS
    apt install -y git-lfs
    
    success "Git LFS instalado: $(git lfs version)"
}

create_deploy_user() {
    log "Configurando usuario deploy..."
    
    # Crear usuario deploy si no existe
    if ! id "$DEPLOY_USER" &>/dev/null; then
        useradd -m -s /bin/bash "$DEPLOY_USER"
        success "Usuario $DEPLOY_USER creado"
    else
        success "Usuario $DEPLOY_USER ya existe"
    fi
    
    # Añadir al grupo docker
    usermod -aG docker "$DEPLOY_USER"
    
    # Configurar sudo sin password para docker (opcional)
    echo "$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/local/bin/docker-compose, /usr/bin/docker-compose" > /etc/sudoers.d/deploy-docker
    
    success "Usuario $DEPLOY_USER configurado con acceso a Docker"
}

create_project_structure() {
    log "Creando estructura de directorios..."
    
    # Crear directorios principales
    mkdir -p "$PROJECT_ROOT"
    mkdir -p "/opt/backups/lamaquina"
    
    # Dar permisos al usuario deploy
    chown -R "$DEPLOY_USER:docker" "$PROJECT_ROOT"
    chown -R "$DEPLOY_USER:docker" "/opt/backups/lamaquina"
    
    # Permisos de directorio
    chmod 755 "$PROJECT_ROOT"
    chmod 755 "/opt/backups/lamaquina"
    
    success "Estructura de directorios creada"
}

clone_repository() {
    log "Clonando repositorio..."
    
    # Cambiar a usuario deploy para el clone
    sudo -u "$DEPLOY_USER" bash << EOF
        cd "$PROJECT_ROOT"
        
        # Limpiar directorio si existe contenido
        if [[ -d ".git" ]]; then
            echo "Repositorio ya existe, actualizando..."
            git fetch origin
        else
            echo "Clonando repositorio desde $REPO_URL..."
            git clone "$REPO_URL" .
        fi
        
        # Configurar Git LFS
        git lfs install
        
        # Checkout a la rama correcta
        if [[ "$ENVIRONMENT" == "staging" ]]; then
            git checkout develop 2>/dev/null || git checkout -b develop origin/develop
        else
            git checkout main 2>/dev/null || git checkout -b main origin/main
        fi
        
        echo "Repositorio configurado en rama: \$(git rev-parse --abbrev-ref HEAD)"
EOF
    
    success "Repositorio clonado y configurado"
}

configure_git_lfs() {
    log "Configurando Git LFS..."
    
    sudo -u "$DEPLOY_USER" bash << EOF
        cd "$PROJECT_ROOT"
        
        # Instalar Git LFS para el usuario
        git lfs install
        
        # Verificar si hay archivos LFS
        if git lfs ls-files | head -1 > /dev/null 2>&1; then
            echo "Archivos LFS detectados, descargando..."
            git lfs pull || echo "Advertencia: No se pudieron descargar todos los archivos LFS"
        else
            echo "No hay archivos LFS en este repositorio"
        fi
EOF
    
    success "Git LFS configurado"
}

setup_firewall() {
    log "Configurando firewall básico..."
    
    # Instalar ufw si no está instalado
    apt install -y ufw
    
    # Configuración básica del firewall
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    
    # Permitir SSH
    ufw allow ssh
    ufw allow 22
    
    # Permitir puertos de la aplicación
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        # Puertos para staging
        ufw allow 3001  # Dashboard frontend
        ufw allow 3002  # Spider factory frontend
        ufw allow 8003  # Pipeline API
        ufw allow 8004  # Dashboard API
        ufw allow 8005  # Spider factory API (mapped)
        ufw allow 5000  # ScrapydWeb
        ufw allow 6800  # Scrapyd
    else
        # Puertos para producción
        ufw allow 80    # HTTP
        ufw allow 443   # HTTPS
    fi
    
    # Habilitar firewall
    ufw --force enable
    
    success "Firewall configurado"
}

create_systemd_services() {
    log "Creando servicios systemd opcionales..."
    
    # Servicio para auto-start de la aplicación
    cat > /etc/systemd/system/lamaquina-${ENVIRONMENT}.service << EOF
[Unit]
Description=La Máquina de Noticias - ${ENVIRONMENT}
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${PROJECT_ROOT}
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=${DEPLOY_USER}
Group=docker

[Install]
WantedBy=multi-user.target
EOF
    
    # Recargar systemd
    systemctl daemon-reload
    
    success "Servicio systemd creado (opcional - no habilitado por defecto)"
    log "Para habilitar auto-start: systemctl enable lamaquina-${ENVIRONMENT}"
}

setup_log_rotation() {
    log "Configurando rotación de logs..."
    
    # Configurar logrotate para Docker
    cat > /etc/logrotate.d/docker << EOF
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=1M
    missingok
    delaycompress
    copytruncate
}
EOF
    
    # Configurar logrotate para backups
    cat > /etc/logrotate.d/lamaquina-backups << EOF
/opt/backups/lamaquina/*.log {
    rotate 30
    daily
    compress
    missingok
    delaycompress
    create 644 ${DEPLOY_USER} ${DEPLOY_USER}
}
EOF
    
    success "Rotación de logs configurada"
}

# =============================================================================
# FUNCIONES DE VERIFICACIÓN
# =============================================================================

verify_installation() {
    log "Verificando instalación..."
    
    echo "🔍 Verificación del sistema:"
    echo "=========================="
    
    # Verificar Docker
    if docker --version; then
        success "Docker funcionando"
    else
        error "Docker no funciona correctamente"
    fi
    
    # Verificar Docker Compose
    if docker-compose --version; then
        success "Docker Compose funcionando"
    else
        error "Docker Compose no funciona correctamente"
    fi
    
    # Verificar Git LFS
    if git lfs version; then
        success "Git LFS funcionando"
    else
        warning "Git LFS no funciona correctamente"
    fi
    
    # Verificar usuario deploy
    if id "$DEPLOY_USER" &>/dev/null; then
        success "Usuario $DEPLOY_USER existe"
        
        # Verificar grupos
        if groups "$DEPLOY_USER" | grep -q docker; then
            success "Usuario $DEPLOY_USER está en grupo docker"
        else
            warning "Usuario $DEPLOY_USER NO está en grupo docker"
        fi
    else
        error "Usuario $DEPLOY_USER no existe"
    fi
    
    # Verificar directorios
    if [[ -d "$PROJECT_ROOT" ]]; then
        success "Directorio del proyecto existe: $PROJECT_ROOT"
        
        # Verificar que es un repo Git
        if [[ -d "$PROJECT_ROOT/.git" ]]; then
            success "Repositorio Git configurado"
            
            # Mostrar información del repo
            local current_branch=$(cd "$PROJECT_ROOT" && sudo -u "$DEPLOY_USER" git rev-parse --abbrev-ref HEAD)
            local last_commit=$(cd "$PROJECT_ROOT" && sudo -u "$DEPLOY_USER" git rev-parse --short HEAD)
            log "Rama actual: $current_branch"
            log "Último commit: $last_commit"
        else
            error "No es un repositorio Git válido"
        fi
    else
        error "Directorio del proyecto no existe"
    fi
    
    # Verificar docker-compose.yml
    if [[ -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
        success "docker-compose.yml encontrado"
        
        # Verificar sintaxis
        if cd "$PROJECT_ROOT" && sudo -u "$DEPLOY_USER" docker-compose config -q; then
            success "docker-compose.yml es válido"
        else
            warning "docker-compose.yml tiene errores de sintaxis"
        fi
    else
        error "docker-compose.yml no encontrado"
    fi
    
    echo
    echo "🔧 Información del sistema:"
    echo "========================="
    echo "OS: $(lsb_release -d | cut -f2)"
    echo "Kernel: $(uname -r)"
    echo "Docker: $(docker --version)"
    echo "Docker Compose: $(docker-compose --version)"
    echo "Git LFS: $(git lfs version)"
    echo "Espacio en disco: $(df -h / | tail -1 | awk '{print $4}') libre"
    echo "Memoria: $(free -h | grep Mem | awk '{print $7}') libre"
}

print_next_steps() {
    log "Configuración del servidor completada"
    
    cat << EOF

🎉 SERVIDOR CONFIGURADO EXITOSAMENTE
===================================

Ambiente: $ENVIRONMENT
Directorio: $PROJECT_ROOT
Usuario: $DEPLOY_USER

📋 PRÓXIMOS PASOS:

1. **Configurar SSH Keys:**
   # En tu máquina local, copiar la public key:
   ssh-copy-id $DEPLOY_USER@$(hostname -I | awk '{print $1}')
   
   # O manualmente:
   sudo -u $DEPLOY_USER mkdir -p /home/$DEPLOY_USER/.ssh
   # Pegar tu public key en: /home/$DEPLOY_USER/.ssh/authorized_keys

2. **Probar conexión SSH:**
   ssh $DEPLOY_USER@$(hostname -I | awk '{print $1}')

3. **Configurar variables de entorno:**
   sudo -u $DEPLOY_USER nano $PROJECT_ROOT/.env
   # Copiar desde .env.example y configurar valores reales

4. **Primer deploy manual (opcional):**
   cd $PROJECT_ROOT
   sudo -u $DEPLOY_USER docker-compose build
   sudo -u $DEPLOY_USER docker-compose up -d

5. **Verificar servicios:**
   sudo -u $DEPLOY_USER docker-compose ps
   curl http://localhost:8003/health
   curl http://localhost:8004/health

6. **Habilitar auto-start (opcional):**
   systemctl enable lamaquina-$ENVIRONMENT

🔒 CONFIGURACIÓN DE SEGURIDAD:
- Firewall configurado con puertos necesarios
- Usuario $DEPLOY_USER creado sin privilegios de root
- Logs configurados con rotación automática

📊 MONITOREO:
- Logs: docker-compose logs -f
- Estado: docker-compose ps
- Recursos: htop

¡El servidor está listo para recibir deploys automáticos! 🚀
EOF
}

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

main() {
    echo "=========================================="
    echo "🛠️  CONFIGURACIÓN AUTOMÁTICA DEL SERVIDOR"
    echo "=========================================="
    echo "Ambiente: $ENVIRONMENT"
    echo "Repositorio: $REPO_URL"
    echo "Directorio: $PROJECT_ROOT"
    echo "=========================================="
    echo
    
    parse_args "$@"
    check_root
    
    # Instalación paso a paso
    install_system_dependencies
    install_docker
    install_docker_compose
    install_git_lfs
    create_deploy_user
    create_project_structure
    clone_repository
    configure_git_lfs
    setup_firewall
    create_systemd_services
    setup_log_rotation
    
    # Verificación final
    verify_installation
    
    # Instrucciones finales
    print_next_steps
    
    success "¡Configuración del servidor completada exitosamente!"
}

# Ejecutar función principal
main "$@"