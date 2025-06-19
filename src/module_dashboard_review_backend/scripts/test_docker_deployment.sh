#!/bin/bash
# test_docker_deployment.sh
# Script de pruebas para verificar el despliegue Docker del módulo Dashboard Review Backend
# La Máquina de Noticias

set -e  # Exit on error

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funciones de utilidad
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Variables
CONTAINER_NAME="module_dashboard_review_backend"
IMAGE_NAME="module_dashboard_review_backend"
PORT="8004"
NETWORK_NAME="lamacquina_network"

echo "=== 🐳 Pruebas de Docker para Dashboard Review Backend ==="
echo ""

# 1. Test Docker build process
echo "1️⃣ Probando construcción de imagen Docker..."
if docker build -t $IMAGE_NAME . > /dev/null 2>&1; then
    print_success "Imagen construida exitosamente"
    
    # Verificar tamaño de imagen
    IMAGE_SIZE=$(docker images $IMAGE_NAME --format "{{.Size}}")
    print_info "Tamaño de imagen: $IMAGE_SIZE"
else
    print_error "Error al construir imagen"
    exit 1
fi

# 2. Verificar que la red existe o crearla
echo ""
echo "2️⃣ Verificando red Docker..."
if docker network inspect $NETWORK_NAME > /dev/null 2>&1; then
    print_success "Red $NETWORK_NAME existe"
else
    print_info "Creando red $NETWORK_NAME..."
    docker network create $NETWORK_NAME
    print_success "Red creada"
fi

# 3. Test container starts correctly
echo ""
echo "3️⃣ Probando inicio del contenedor..."

# Detener contenedor existente si está corriendo
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Iniciar contenedor para testing
if docker run -d \
    --name $CONTAINER_NAME \
    --network $NETWORK_NAME \
    -p $PORT:$PORT \
    --env-file .env \
    $IMAGE_NAME > /dev/null 2>&1; then
    print_success "Contenedor iniciado"
else
    print_error "Error al iniciar contenedor"
    exit 1
fi

# Esperar a que el servicio esté listo
echo ""
print_info "Esperando a que el servicio esté listo..."
sleep 10

# Verificar logs
echo ""
echo "4️⃣ Verificando logs del contenedor..."
if docker logs $CONTAINER_NAME 2>&1 | grep -q "Dashboard Review API started successfully"; then
    print_success "Logs muestran inicio exitoso"
else
    print_error "No se encontró mensaje de inicio en logs"
    docker logs $CONTAINER_NAME
fi

# 4. Test health check functionality
echo ""
echo "5️⃣ Probando endpoint de health check..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/health)
if [ "$HEALTH_RESPONSE" = "200" ]; then
    print_success "Health check básico respondió con 200 OK"
    
    # Mostrar respuesta JSON
    HEALTH_JSON=$(curl -s http://localhost:$PORT/health)
    print_info "Respuesta: $HEALTH_JSON"
else
    print_error "Health check falló con código: $HEALTH_RESPONSE"
fi

# Test detailed health check
echo ""
print_info "Probando health check detallado..."
DETAILED_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/health/detailed)
if [ "$DETAILED_RESPONSE" = "200" ]; then
    print_success "Health check detallado respondió con 200 OK"
else
    print_error "Health check detallado falló con código: $DETAILED_RESPONSE"
fi

# 5. Test container health check command
echo ""
echo "6️⃣ Probando comando de health check del contenedor..."
if docker exec $CONTAINER_NAME curl -f http://localhost:$PORT/health > /dev/null 2>&1; then
    print_success "Health check interno del contenedor funciona"
else
    print_error "Health check interno del contenedor falló"
fi

# 6. Verify non-root user security
echo ""
echo "7️⃣ Verificando seguridad de usuario no-root..."
USER_ID=$(docker exec $CONTAINER_NAME id -u)
USERNAME=$(docker exec $CONTAINER_NAME whoami)
if [ "$USER_ID" = "1000" ] && [ "$USERNAME" = "appuser" ]; then
    print_success "Contenedor ejecutándose como usuario no-root (appuser:1000)"
else
    print_error "Contenedor NO está ejecutándose como appuser"
    print_info "Usuario actual: $USERNAME (UID: $USER_ID)"
fi

# 7. Test environment variables
echo ""
echo "8️⃣ Verificando variables de entorno..."
API_PORT_CHECK=$(docker exec $CONTAINER_NAME printenv API_PORT)
if [ "$API_PORT_CHECK" = "8004" ]; then
    print_success "Variable API_PORT configurada correctamente"
else
    print_error "Variable API_PORT no está configurada"
fi

# 8. Test port binding
echo ""
echo "9️⃣ Verificando binding de puerto..."
if netstat -an | grep -q ":$PORT.*LISTEN" || ss -tlnp | grep -q ":$PORT"; then
    print_success "Puerto $PORT está escuchando"
else
    print_error "Puerto $PORT no está escuchando"
fi

# 9. Test restart behavior
echo ""
echo "🔟 Probando comportamiento de restart..."
docker stop $CONTAINER_NAME > /dev/null 2>&1
sleep 2
docker start $CONTAINER_NAME > /dev/null 2>&1
sleep 5

HEALTH_AFTER_RESTART=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/health)
if [ "$HEALTH_AFTER_RESTART" = "200" ]; then
    print_success "Contenedor se reinició correctamente"
else
    print_error "Contenedor no respondió después del restart"
fi

# 10. Test error scenarios
echo ""
echo "1️⃣1️⃣ Probando escenarios de error..."

# Test puerto ocupado
print_info "Simulando puerto ocupado..."
docker stop $CONTAINER_NAME > /dev/null 2>&1
docker rm $CONTAINER_NAME > /dev/null 2>&1

# Intentar usar un puerto ya en uso
nc -l localhost $PORT &
NC_PID=$!
sleep 1

if docker run -d --name ${CONTAINER_NAME}_test -p $PORT:$PORT $IMAGE_NAME > /dev/null 2>&1; then
    print_error "Contenedor se inició cuando el puerto estaba ocupado"
    docker stop ${CONTAINER_NAME}_test > /dev/null 2>&1
    docker rm ${CONTAINER_NAME}_test > /dev/null 2>&1
else
    print_success "Contenedor manejó correctamente el puerto ocupado"
fi

kill $NC_PID 2>/dev/null || true

# Limpiar contenedores de prueba
docker stop ${CONTAINER_NAME}_test 2>/dev/null || true
docker rm ${CONTAINER_NAME}_test 2>/dev/null || true

# Resumen final
echo ""
echo "=== 📊 Resumen de Pruebas ==="
echo "Todas las pruebas críticas completadas."
echo ""
print_info "Para pruebas adicionales con docker-compose:"
echo "  docker-compose up -d"
echo "  docker-compose ps"
echo "  docker-compose logs -f $CONTAINER_NAME"
echo ""
print_info "Para limpiar:"
echo "  docker stop $CONTAINER_NAME"
echo "  docker rm $CONTAINER_NAME"
echo "  docker rmi $IMAGE_NAME"
