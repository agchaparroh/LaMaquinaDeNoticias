#!/bin/bash

# =============================================================================
# HEALTH CHECK SCRIPT - LA MÁQUINA DE NOTICIAS
# =============================================================================
# Script para verificar el estado de salud de todos los servicios
# Uso: ./health-check.sh [staging|production] [--detailed]
#
# Opciones:
#   --detailed       Mostrar información detallada de cada servicio
#   --json          Salida en formato JSON
#   --timeout=N     Timeout en segundos para cada check (default: 10)
#
# Ejemplos:
#   ./health-check.sh staging
#   ./health-check.sh production --detailed
#   ./health-check.sh staging --json
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
DETAILED=false
JSON_OUTPUT=false
TIMEOUT=10
PROJECT_ROOT="/opt/lamaquina"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

log() {
    if [[ "$JSON_OUTPUT" == false ]]; then
        echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
    fi
}

success() {
    if [[ "$JSON_OUTPUT" == false ]]; then
        echo -e "${GREEN}✅ $1${NC}"
    fi
}

warning() {
    if [[ "$JSON_OUTPUT" == false ]]; then
        echo -e "${YELLOW}⚠️  $1${NC}"
    fi
}

error() {
    if [[ "$JSON_OUTPUT" == false ]]; then
        echo -e "${RED}❌ $1${NC}"
    fi
}

usage() {
    cat << EOF
Uso: $0 [staging|production] [opciones]

Ambientes:
    staging     Verificar ambiente de staging
    production  Verificar ambiente de producción

Opciones:
    --detailed      Mostrar información detallada
    --json          Salida en formato JSON
    --timeout=N     Timeout en segundos (default: 10)
    --help          Mostrar esta ayuda

Ejemplos:
    $0 staging
    $0 production --detailed
    $0 staging --json --timeout=5
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
            --detailed)
                DETAILED=true
                shift
                ;;
            --json)
                JSON_OUTPUT=true
                shift
                ;;
            --timeout=*)
                TIMEOUT="${1#*=}"
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
        BASE_URL="http://localhost"
    elif [[ "$ENVIRONMENT" == "production" ]]; then
        PROJECT_ROOT="/opt/lamaquina-production"
        COMPOSE_PROJECT="lamaquina_production"
        BASE_URL="https://$(hostname)"
    fi
}

# =============================================================================
# FUNCIONES DE HEALTH CHECK
# =============================================================================

# Estructura para almacenar resultados
declare -A CHECK_RESULTS
declare -A CHECK_DETAILS
declare -A CHECK_RESPONSE_TIMES

check_docker_services() {
    log "Verificando servicios Docker..."
    
    local services=(
        "module_pipeline"
        "module_dashboard_review_backend"
        "module_dashboard_review_frontend"
        "module_spider_factory_frontend"
        "spider_factory_backend"
        "module_scraper"
        "scrapyd"
        "scrapydweb"
        "nginx_reverse_proxy"
        "redis"
    )
    
    local healthy_count=0
    local total_count=${#services[@]}
    
    for service in "${services[@]}"; do
        local container_name="${COMPOSE_PROJECT}_${service}"
        
        if docker ps --filter "name=${container_name}" --filter "status=running" | grep -q "${container_name}"; then
            CHECK_RESULTS["docker_${service}"]="healthy"
            CHECK_DETAILS["docker_${service}"]="Container running"
            healthy_count=$((healthy_count + 1))
            
            if [[ "$DETAILED" == true ]]; then
                # Obtener información adicional del contenedor
                local uptime=$(docker inspect "${container_name}" --format='{{.State.StartedAt}}' 2>/dev/null || echo "unknown")
                local image=$(docker inspect "${container_name}" --format='{{.Config.Image}}' 2>/dev/null || echo "unknown")
                CHECK_DETAILS["docker_${service}"]="Running since: ${uptime}, Image: ${image}"
            fi
        else
            CHECK_RESULTS["docker_${service}"]="unhealthy"
            CHECK_DETAILS["docker_${service}"]="Container not running or not found"
        fi
    done
    
    local docker_health_percentage=$((healthy_count * 100 / total_count))
    CHECK_RESULTS["docker_overall"]="$docker_health_percentage"
    CHECK_DETAILS["docker_overall"]="$healthy_count/$total_count services running"
}

check_http_endpoints() {
    log "Verificando endpoints HTTP..."
    
    local endpoints=(
        "pipeline_api:http://localhost:8003/health"
        "dashboard_api:http://localhost:8004/health"
        "frontend_dashboard:http://localhost:3001"
        "frontend_spider_factory:http://localhost:3002"
        "scrapydweb:http://localhost:5000"
        "scrapyd:http://localhost:6800/daemonstatus.json"
    )
    
    for endpoint_def in "${endpoints[@]}"; do
        local endpoint_name=$(echo "$endpoint_def" | cut -d: -f1)
        local endpoint_url=$(echo "$endpoint_def" | cut -d: -f2-)
        
        local start_time=$(date +%s.%N)
        local http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$endpoint_url" 2>/dev/null || echo "000")
        local end_time=$(date +%s.%N)
        local response_time=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
        
        CHECK_RESPONSE_TIMES["$endpoint_name"]="$response_time"
        
        if [[ "$http_code" =~ ^2[0-9][0-9]$ ]]; then
            CHECK_RESULTS["http_${endpoint_name}"]="healthy"
            CHECK_DETAILS["http_${endpoint_name}"]="HTTP $http_code (${response_time}s)"
        else
            CHECK_RESULTS["http_${endpoint_name}"]="unhealthy"
            CHECK_DETAILS["http_${endpoint_name}"]="HTTP $http_code or timeout"
        fi
    done
}

check_database_connectivity() {
    log "Verificando conectividad de base de datos..."
    
    # Verificar que el pipeline puede conectarse a Supabase
    local pipeline_health=$(curl -s --max-time "$TIMEOUT" "http://localhost:8003/health" 2>/dev/null || echo "{}")
    
    if echo "$pipeline_health" | grep -q "database.*connected"; then
        CHECK_RESULTS["database_connectivity"]="healthy"
        CHECK_DETAILS["database_connectivity"]="Pipeline reports database connected"
    elif echo "$pipeline_health" | grep -q "healthy"; then
        CHECK_RESULTS["database_connectivity"]="healthy"
        CHECK_DETAILS["database_connectivity"]="Pipeline healthy (assuming DB connected)"
    else
        CHECK_RESULTS["database_connectivity"]="unhealthy"
        CHECK_DETAILS["database_connectivity"]="Cannot verify database connectivity"
    fi
}

check_redis_connectivity() {
    log "Verificando conectividad de Redis..."
    
    local redis_container="${COMPOSE_PROJECT}_redis"
    
    if docker exec "$redis_container" redis-cli ping 2>/dev/null | grep -q "PONG"; then
        CHECK_RESULTS["redis_connectivity"]="healthy"
        CHECK_DETAILS["redis_connectivity"]="Redis responding to PING"
        
        if [[ "$DETAILED" == true ]]; then
            local redis_info=$(docker exec "$redis_container" redis-cli info memory 2>/dev/null | head -5 || echo "No info available")
            CHECK_DETAILS["redis_connectivity"]="Redis PONG, Memory info: $redis_info"
        fi
    else
        CHECK_RESULTS["redis_connectivity"]="unhealthy"
        CHECK_DETAILS["redis_connectivity"]="Redis not responding"
    fi
}

check_spider_factory() {
    log "Verificando Spider Factory..."
    
    local sf_health=$(curl -s --max-time "$TIMEOUT" "http://localhost:8000/health" 2>/dev/null || echo "{}")
    
    if echo "$sf_health" | grep -q "healthy"; then
        CHECK_RESULTS["spider_factory"]="healthy"
        CHECK_DETAILS["spider_factory"]="Spider Factory API responding"
    else
        CHECK_RESULTS["spider_factory"]="unhealthy"
        CHECK_DETAILS["spider_factory"]="Spider Factory API not responding"
    fi
}

check_scrapyd_status() {
    log "Verificando estado de Scrapyd..."
    
    local scrapyd_status=$(curl -s --max-time "$TIMEOUT" "http://localhost:6800/daemonstatus.json" 2>/dev/null || echo "{}")
    
    if echo "$scrapyd_status" | grep -q "status.*ok"; then
        CHECK_RESULTS["scrapyd_status"]="healthy"
        
        if [[ "$DETAILED" == true ]]; then
            local running_spiders=$(echo "$scrapyd_status" | jq -r '.running // 0' 2>/dev/null || echo "unknown")
            local pending_spiders=$(echo "$scrapyd_status" | jq -r '.pending // 0' 2>/dev/null || echo "unknown")
            CHECK_DETAILS["scrapyd_status"]="OK, Running: $running_spiders, Pending: $pending_spiders"
        else
            CHECK_DETAILS["scrapyd_status"]="Scrapyd daemon OK"
        fi
    else
        CHECK_RESULTS["scrapyd_status"]="unhealthy"
        CHECK_DETAILS["scrapyd_status"]="Scrapyd daemon not responding properly"
    fi
}

check_system_resources() {
    log "Verificando recursos del sistema..."
    
    # Verificar uso de CPU
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}' 2>/dev/null || echo "unknown")
    
    # Verificar uso de memoria
    local memory_info=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}' 2>/dev/null || echo "unknown")
    
    # Verificar uso de disco
    local disk_usage=$(df "$PROJECT_ROOT" | tail -1 | awk '{print $5}' | sed 's/%//' 2>/dev/null || echo "unknown")
    
    CHECK_RESULTS["system_resources"]="healthy"
    CHECK_DETAILS["system_resources"]="CPU: ${cpu_usage}%, Memory: ${memory_info}%, Disk: ${disk_usage}%"
    
    # Alertas por uso excesivo de recursos
    if [[ "$cpu_usage" != "unknown" ]] && (( $(echo "$cpu_usage > 80" | bc -l 2>/dev/null || echo 0) )); then
        CHECK_RESULTS["system_resources"]="warning"
    fi
    
    if [[ "$memory_info" != "unknown" ]] && (( $(echo "$memory_info > 85" | bc -l 2>/dev/null || echo 0) )); then
        CHECK_RESULTS["system_resources"]="warning"
    fi
    
    if [[ "$disk_usage" != "unknown" ]] && [[ "$disk_usage" -gt 90 ]]; then
        CHECK_RESULTS["system_resources"]="warning"
    fi
}

# =============================================================================
# FUNCIONES DE REPORTE
# =============================================================================

generate_summary() {
    local total_checks=0
    local healthy_checks=0
    local warning_checks=0
    local unhealthy_checks=0
    
    for check in "${!CHECK_RESULTS[@]}"; do
        # Saltar checks agregados (como docker_overall)
        if [[ "$check" == *"_overall" ]]; then
            continue
        fi
        
        total_checks=$((total_checks + 1))
        
        case "${CHECK_RESULTS[$check]}" in
            "healthy")
                healthy_checks=$((healthy_checks + 1))
                ;;
            "warning")
                warning_checks=$((warning_checks + 1))
                ;;
            "unhealthy")
                unhealthy_checks=$((unhealthy_checks + 1))
                ;;
        esac
    done
    
    local health_percentage=$((healthy_checks * 100 / total_checks))
    
    CHECK_RESULTS["overall_health"]="$health_percentage"
    CHECK_DETAILS["overall_health"]="$healthy_checks/$total_checks checks healthy"
}

output_json() {
    cat << EOF
{
  "timestamp": "$TIMESTAMP",
  "environment": "$ENVIRONMENT",
  "overall_health_percentage": ${CHECK_RESULTS["overall_health"]},
  "summary": "${CHECK_DETAILS["overall_health"]}",
  "checks": {
EOF

    local first=true
    for check in "${!CHECK_RESULTS[@]}"; do
        if [[ "$check" == "overall_health" ]]; then
            continue
        fi
        
        if [[ "$first" == false ]]; then
            echo ","
        fi
        first=false
        
        local response_time="${CHECK_RESPONSE_TIMES[$check]:-null}"
        if [[ "$response_time" != "null" ]]; then
            response_time="\"$response_time\""
        fi
        
        cat << EOF
    "$check": {
      "status": "${CHECK_RESULTS[$check]}",
      "details": "${CHECK_DETAILS[$check]}",
      "response_time": $response_time
    }
EOF
    done

    echo ""
    echo "  }"
    echo "}"
}

output_human() {
    echo "=========================================="
    echo "🏥 HEALTH CHECK - LA MÁQUINA DE NOTICIAS"
    echo "=========================================="
    echo "Ambiente: $ENVIRONMENT"
    echo "Timestamp: $TIMESTAMP"
    echo "Health Score: ${CHECK_RESULTS["overall_health"]}%"
    echo "=========================================="
    echo
    
    # Agrupar por categorías
    echo "📦 SERVICIOS DOCKER:"
    for check in "${!CHECK_RESULTS[@]}"; do
        if [[ "$check" == docker_* ]] && [[ "$check" != "docker_overall" ]]; then
            local service_name=$(echo "$check" | sed 's/docker_//')
            local status="${CHECK_RESULTS[$check]}"
            local details="${CHECK_DETAILS[$check]}"
            
            case "$status" in
                "healthy")
                    success "$service_name: $details"
                    ;;
                "warning")
                    warning "$service_name: $details"
                    ;;
                "unhealthy")
                    error "$service_name: $details"
                    ;;
            esac
        fi
    done
    
    echo
    echo "🌐 ENDPOINTS HTTP:"
    for check in "${!CHECK_RESULTS[@]}"; do
        if [[ "$check" == http_* ]]; then
            local endpoint_name=$(echo "$check" | sed 's/http_//')
            local status="${CHECK_RESULTS[$check]}"
            local details="${CHECK_DETAILS[$check]}"
            
            case "$status" in
                "healthy")
                    success "$endpoint_name: $details"
                    ;;
                "warning")
                    warning "$endpoint_name: $details"
                    ;;
                "unhealthy")
                    error "$endpoint_name: $details"
                    ;;
            esac
        fi
    done
    
    echo
    echo "🔧 SERVICIOS INTERNOS:"
    for check in "${!CHECK_RESULTS[@]}"; do
        if [[ "$check" != docker_* ]] && [[ "$check" != http_* ]] && [[ "$check" != "overall_health" ]]; then
            local service_name="$check"
            local status="${CHECK_RESULTS[$check]}"
            local details="${CHECK_DETAILS[$check]}"
            
            case "$status" in
                "healthy")
                    success "$service_name: $details"
                    ;;
                "warning")
                    warning "$service_name: $details"
                    ;;
                "unhealthy")
                    error "$service_name: $details"
                    ;;
            esac
        fi
    done
    
    echo
    echo "=========================================="
    
    local health_score="${CHECK_RESULTS["overall_health"]}"
    
    if [[ "$health_score" -ge 90 ]]; then
        success "Sistema SALUDABLE (${health_score}%)"
    elif [[ "$health_score" -ge 70 ]]; then
        warning "Sistema con ADVERTENCIAS (${health_score}%)"
    else
        error "Sistema CON PROBLEMAS (${health_score}%)"
    fi
    
    echo "=========================================="
}

# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

main() {
    parse_args "$@"
    configure_environment
    
    if [[ "$JSON_OUTPUT" == false ]]; then
        log "Iniciando health check para: $ENVIRONMENT"
    fi
    
    # Ejecutar todos los checks
    check_docker_services
    check_http_endpoints
    check_database_connectivity
    check_redis_connectivity
    check_spider_factory
    check_scrapyd_status
    check_system_resources
    
    # Generar resumen
    generate_summary
    
    # Mostrar resultados
    if [[ "$JSON_OUTPUT" == true ]]; then
        output_json
    else
        output_human
    fi
    
    # Exit code basado en el health score
    local health_score="${CHECK_RESULTS["overall_health"]}"
    if [[ "$health_score" -ge 70 ]]; then
        exit 0
    else
        exit 1
    fi
}

# Verificar dependencias
if ! command -v curl &> /dev/null; then
    error "curl no está instalado"
fi

if ! command -v docker &> /dev/null; then
    error "docker no está instalado"
fi

# Ejecutar función principal
main "$@"