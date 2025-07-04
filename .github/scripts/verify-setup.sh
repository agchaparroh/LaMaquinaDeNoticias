#!/bin/bash

# =============================================================================
# SCRIPT DE VERIFICACIÓN DE CONFIGURACIÓN CI/CD
# =============================================================================
# Verifica que todo esté configurado correctamente antes del primer deploy
# Uso: ./verify-setup.sh [staging|production|all]
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
CHECK_ALL=false

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
}

check_mark() {
    echo -e "${GREEN}✓${NC}"
}

cross_mark() {
    echo -e "${RED}✗${NC}"
}

# =============================================================================
# FUNCIONES DE VERIFICACIÓN
# =============================================================================

check_github_secrets() {
    local env=$1
    log "Verificando GitHub Secrets para $env..."
    
    echo "📋 GitHub Secrets requeridos para $env:"
    echo "======================================"
    
    if [[ "$env" == "staging" ]]; then
        local secrets=(
            "STAGING_SERVER_HOST"
            "STAGING_SERVER_USER"
            "STAGING_SSH_PRIVATE_KEY"
            "STAGING_SUPABASE_URL"
            "STAGING_SUPABASE_ANON_KEY"
            "STAGING_SUPABASE_SERVICE_ROLE_KEY"
            "STAGING_GROQ_API_KEY"
            "STAGING_FIRECRAWL_API_KEY"
            "STAGING_SCRAPYDWEB_PASSWORD"
        )
    else
        local secrets=(
            "PRODUCTION_SERVER_HOST"
            "PRODUCTION_SERVER_USER"
            "PRODUCTION_SSH_PRIVATE_KEY"
            "PRODUCTION_DOMAIN"
            "PRODUCTION_SUPABASE_URL"
            "PRODUCTION_SUPABASE_ANON_KEY"
            "PRODUCTION_SUPABASE_SERVICE_ROLE_KEY"
            "PRODUCTION_GROQ_API_KEY"
            "PRODUCTION_FIRECRAWL_API_KEY"
            "PRODUCTION_ANTHROPIC_API_KEY"
            "PRODUCTION_SCRAPYDWEB_PASSWORD"
            "PROD_APPROVERS"
        )
    fi
    
    echo "MANUAL: Verificar estos secrets en GitHub:"
    echo "Repositorio → Settings → Secrets and variables → Actions"
    echo
    
    for secret in "${secrets[@]}"; do
        echo "  [ ] $secret"
    done
    
    echo
    warning "Estos secrets deben configurarse manualmente en GitHub"
}

check_server_connectivity() {
    local env=$1
    log "Verificando conectividad al servidor $env..."
    
    echo "🔧 Comandos para probar conectividad:"
    echo "===================================="
    
    if [[ "$env" == "staging" ]]; then
        echo "# Probar SSH a staging:"
        echo "ssh deploy@\$STAGING_SERVER_HOST"
        echo
        echo "# Verificar Docker en staging:"
        echo "ssh deploy@\$STAGING_SERVER_HOST 'docker --version && docker-compose --version'"
        echo
        echo "# Verificar directorios en staging:"
        echo "ssh deploy@\$STAGING_SERVER_HOST 'ls -la /opt/lamaquina-staging'"
    else
        echo "# Probar SSH a producción:"
        echo "ssh deploy@\$PRODUCTION_SERVER_HOST"
        echo
        echo "# Verificar Docker en producción:"
        echo "ssh deploy@\$PRODUCTION_SERVER_HOST 'docker --version && docker-compose --version'"
        echo
        echo "# Verificar directorios en producción:"
        echo "ssh deploy@\$PRODUCTION_SERVER_HOST 'ls -la /opt/lamaquina-production'"
    fi
    
    echo
    warning "Ejecutar estos comandos manualmente para verificar conectividad"
}

check_server_setup() {
    local env=$1
    log "Verificando configuración del servidor $env..."
    
    echo "📋 Checklist de configuración del servidor:"
    echo "=========================================="
    
    local items=(
        "Docker instalado y funcionando"
        "Docker Compose instalado"
        "Git LFS instalado y configurado"
        "Usuario 'deploy' creado"
        "Usuario 'deploy' en grupo docker"
        "Directorio del proyecto creado"
        "Repositorio clonado en el servidor"
        "SSH key configurada para usuario deploy"
        "Permisos correctos en directorios"
    )
    
    for item in "${items[@]}"; do
        echo "  [ ] $item"
    done
    
    echo
    echo "🔧 Script de verificación remota:"
    echo "================================"
    
    if [[ "$env" == "staging" ]]; then
        cat << 'EOF'
# Ejecutar en el servidor staging:
ssh deploy@$STAGING_SERVER_HOST << 'REMOTE_EOF'
echo "=== Verificación del servidor staging ==="
echo "Docker: $(docker --version 2>/dev/null || echo 'NO INSTALADO')"
echo "Docker Compose: $(docker-compose --version 2>/dev/null || echo 'NO INSTALADO')"
echo "Git LFS: $(git lfs version 2>/dev/null || echo 'NO INSTALADO')"
echo "Usuario actual: $(whoami)"
echo "Grupos: $(groups)"
echo "Directorio proyecto: $(ls -la /opt/lamaquina-staging 2>/dev/null || echo 'NO EXISTE')"
echo "Git status: $(cd /opt/lamaquina-staging && git status --porcelain 2>/dev/null || echo 'NO ES REPO GIT')"
REMOTE_EOF
EOF
    else
        cat << 'EOF'
# Ejecutar en el servidor producción:
ssh deploy@$PRODUCTION_SERVER_HOST << 'REMOTE_EOF'
echo "=== Verificación del servidor producción ==="
echo "Docker: $(docker --version 2>/dev/null || echo 'NO INSTALADO')"
echo "Docker Compose: $(docker-compose --version 2>/dev/null || echo 'NO INSTALADO')"
echo "Git LFS: $(git lfs version 2>/dev/null || echo 'NO INSTALADO')"
echo "Usuario actual: $(whoami)"
echo "Grupos: $(groups)"
echo "Directorio proyecto: $(ls -la /opt/lamaquina-production 2>/dev/null || echo 'NO EXISTE')"
echo "Git status: $(cd /opt/lamaquina-production && git status --porcelain 2>/dev/null || echo 'NO ES REPO GIT')"
REMOTE_EOF
EOF
    fi
}

check_local_git_config() {
    log "Verificando configuración Git local..."
    
    echo "🔧 Verificación Git local:"
    echo "========================="
    
    # Verificar que estamos en un repo Git
    if [[ ! -d ".git" ]]; then
        error "No estás en un repositorio Git"
        return 1
    fi
    
    success "Repositorio Git detectado"
    
    # Verificar ramas
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    echo "Rama actual: $current_branch"
    
    # Verificar que existen las ramas necesarias
    if git show-ref --verify --quiet refs/heads/main; then
        success "Rama 'main' existe"
    else
        warning "Rama 'main' no existe - crear antes del primer deploy"
    fi
    
    if git show-ref --verify --quiet refs/heads/develop; then
        success "Rama 'develop' existe"
    else
        warning "Rama 'develop' no existe - crear antes del primer deploy"
    fi
    
    # Verificar archivos CI/CD
    local ci_files=(
        ".github/workflows/ci-tests.yml"
        ".github/workflows/deploy-staging.yml"
        ".github/workflows/deploy-production.yml"
        ".github/scripts/deploy.sh"
        ".github/scripts/health-check.sh"
        ".github/scripts/rollback.sh"
        ".github/scripts/lfs-manager.sh"
        ".github/dependabot.yml"
    )
    
    echo
    echo "📁 Archivos CI/CD:"
    for file in "${ci_files[@]}"; do
        if [[ -f "$file" ]]; then
            echo "  $(check_mark) $file"
        else
            echo "  $(cross_mark) $file"
        fi
    done
    
    # Verificar Git LFS
    echo
    echo "📦 Git LFS:"
    if command -v git-lfs &> /dev/null; then
        success "Git LFS instalado: $(git lfs version)"
        
        if [[ -f ".gitattributes" ]]; then
            local lfs_files=$(git lfs ls-files | wc -l)
            if [[ $lfs_files -gt 0 ]]; then
                success "$lfs_files archivos LFS detectados"
            else
                log "No hay archivos LFS (esto es normal si no tienes archivos grandes)"
            fi
        else
            log "No hay archivo .gitattributes (normal si no usas LFS)"
        fi
    else
        warning "Git LFS no está instalado localmente"
    fi
}

check_docker_compose_config() {
    log "Verificando configuración Docker Compose..."
    
    if [[ ! -f "docker-compose.yml" ]]; then
        error "docker-compose.yml no encontrado"
        return 1
    fi
    
    # Verificar sintaxis
    if command -v docker-compose &> /dev/null; then
        if docker-compose config -q; then
            success "docker-compose.yml es válido"
        else
            error "docker-compose.yml tiene errores de sintaxis"
            return 1
        fi
    else
        warning "Docker Compose no está instalado localmente - no se puede verificar sintaxis"
    fi
    
    # Verificar servicios críticos
    local required_services=(
        "module_pipeline"
        "module_dashboard_review_backend" 
        "module_dashboard_review_frontend"
        "spider_factory_backend"
        "redis"
    )
    
    echo
    echo "🐳 Servicios Docker requeridos:"
    for service in "${required_services[@]}"; do
        if grep -q "^  $service:" docker-compose.yml; then
            echo "  $(check_mark) $service"
        else
            echo "  $(cross_mark) $service"
        fi
    done
}

generate_first_commit_guide() {
    log "Generando guía para el primer commit..."
    
    cat << 'EOF'

🚀 GUÍA PARA EL PRIMER COMMIT Y PRUEBA
=====================================

1. **Verificar que todo esté configurado:**
   - ✅ GitHub Secrets configurados
   - ✅ Servidores preparados y accesibles por SSH
   - ✅ SSH keys configuradas
   - ✅ Repositorios clonados en servidores

2. **Hacer el primer commit:**
   ```bash
   # Añadir archivos CI/CD
   git add .github/
   
   # Commit de la configuración CI/CD
   git commit -m "feat: add CI/CD configuration with GitHub Actions

   - Add comprehensive test workflows for all modules
   - Add staging and production deployment workflows
   - Add support scripts for deploy, health-check, and rollback
   - Add Git LFS optimization for large files
   - Add dependabot configuration for automated updates
   
   🤖 Generated with Claude Code"
   
   # Crear rama develop si no existe
   git checkout -b develop 2>/dev/null || git checkout develop
   
   # Push develop para probar staging
   git push -u origin develop
   ```

3. **Monitorear el primer workflow:**
   - Ve a tu repositorio en GitHub
   - Click en "Actions" 
   - Verifica que se ejecute "CI - Tests Automáticos"
   - Si está en verde, verifica que se ejecute "Deploy a Staging"

4. **Probar staging:**
   ```bash
   # Verificar que staging esté funcionando
   curl http://STAGING_SERVER_HOST:8003/health
   curl http://STAGING_SERVER_HOST:8004/health
   
   # Acceder al dashboard
   open http://STAGING_SERVER_HOST:3001
   ```

5. **Deploy a producción (cuando staging esté OK):**
   ```bash
   # Merge a main para production deploy
   git checkout main
   git merge develop
   git push origin main
   
   # Esto requerirá aprobación manual en GitHub
   ```

6. **Monitorear producción:**
   - Ve a GitHub Actions
   - Aprueba el deploy de producción cuando se solicite
   - Verifica que todos los health checks pasen

7. **URLs finales:**
   - Staging: http://STAGING_SERVER_HOST:3001
   - Producción: https://TU_DOMINIO.com

🎉 ¡CI/CD listo y funcionando!
EOF
}

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

main() {
    echo "=========================================="
    echo "🔍 VERIFICACIÓN CONFIGURACIÓN CI/CD"
    echo "=========================================="
    echo
    
    # Parsear argumentos
    case "${1:-all}" in
        staging)
            ENVIRONMENT="staging"
            ;;
        production)
            ENVIRONMENT="production"
            ;;
        all)
            CHECK_ALL=true
            ;;
        *)
            echo "Uso: $0 [staging|production|all]"
            exit 1
            ;;
    esac
    
    # Verificaciones locales
    check_local_git_config
    check_docker_compose_config
    
    echo
    echo "=========================================="
    
    # Verificaciones por ambiente
    if [[ "$CHECK_ALL" == true ]]; then
        check_github_secrets "staging"
        echo
        check_github_secrets "production"
        echo
        check_server_connectivity "staging"
        echo
        check_server_connectivity "production"
        echo
        check_server_setup "staging"
        echo
        check_server_setup "production"
    else
        check_github_secrets "$ENVIRONMENT"
        echo
        check_server_connectivity "$ENVIRONMENT"
        echo
        check_server_setup "$ENVIRONMENT"
    fi
    
    echo
    echo "=========================================="
    generate_first_commit_guide
    
    echo
    success "Verificación completada. Revisa los puntos marcados arriba."
    warning "Configura manualmente los elementos pendientes antes del primer deploy."
}

# Ejecutar función principal
main "$@"