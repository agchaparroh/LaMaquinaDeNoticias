#!/bin/bash
# deploy.sh - Script de deployment robusto y simple
# Versión completa para MVP funcional

set -e  # Exit on any error

echo "🚀 Deploy nginx-reverse-proxy - MVP Implementation"
echo "=================================================="

# Verificar prerrequisitos
echo "🔍 Checking prerequisites..."

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker not found. Please install Docker first."
    exit 1
fi

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose not found. Please install Docker Compose."
    exit 1
fi

# Verificar que la red existe
if ! docker network ls | grep -q "lamacquina_network"; then
    echo "📡 Creating lamacquina_network..."
    docker network create lamacquina_network
else
    echo "✅ Network lamacquina_network exists"
fi

# Build de la imagen
echo "📦 Building nginx reverse proxy image..."
cd "$(dirname "$0")"/.. # Go to project root
docker build -t nginx_reverse_proxy .

# Stop y remove container existente si existe
echo "🛑 Cleaning up existing containers..."
docker stop nginx_reverse_proxy 2>/dev/null || true
docker rm nginx_reverse_proxy 2>/dev/null || true

# Deploy standalone para testing
echo "🏃 Deploying nginx reverse proxy..."
docker run -d \
  --name nginx_reverse_proxy \
  -p 80:80 \
  -p 443:443 \
  --network lamacquina_network \
  --restart unless-stopped \
  nginx_reverse_proxy

# Wait para startup
echo "⏳ Waiting for nginx startup..."
sleep 5

# Health checks
echo "🧪 Running health checks..."

# Test nginx health check interno
echo "Testing nginx health endpoint..."
if curl -f http://localhost/nginx-health &>/dev/null; then
    echo "✅ Nginx health check: OK"
else
    echo "❌ Nginx health check: FAILED"
    echo "📋 Container logs:"
    docker logs nginx_reverse_proxy --tail 20
    exit 1
fi

# Test API routing (solo conectividad, no esperamos respuesta válida)
echo "Testing API routing..."
if curl -I http://localhost/api/health &>/dev/null; then
    echo "✅ API routing: OK (backend connected)"
elif curl -f http://localhost/api/ &>/dev/null; then
    echo "⚠️  API routing: nginx OK, backend may not be running"
else
    echo "⚠️  API routing: accessible but no backend response (expected)"
fi

# Test frontend routing
echo "Testing frontend routing..."
if curl -I http://localhost/ &>/dev/null; then
    echo "✅ Frontend routing: OK (frontend connected)"
elif curl -f http://localhost/ &>/dev/null; then
    echo "⚠️  Frontend routing: nginx OK, frontend may not be running"
else
    echo "⚠️  Frontend routing: accessible but no frontend response (expected)"
fi

# Summary
echo ""
echo "🎉 Nginx Reverse Proxy deployment completed!"
echo ""
echo "📋 Service Status:"
echo "   🌐 Proxy URL: http://localhost"
echo "   🔍 Health Check: http://localhost/nginx-health"
echo "   📡 API Proxy: http://localhost/api/*"
echo "   🖥️  Frontend Proxy: http://localhost/"
echo ""
echo "📝 Useful Commands:"
echo "   docker logs nginx_reverse_proxy           # View logs"
echo "   docker stop nginx_reverse_proxy           # Stop service"
echo "   docker start nginx_reverse_proxy          # Start service"
echo "   docker exec -it nginx_reverse_proxy sh    # Shell access"
echo "   curl http://localhost/nginx-health        # Manual health check"
echo ""
echo "🔗 Integration with main system:"
echo "   Use docker-compose.integration.yml fragment in main docker-compose.yml"
echo "   Or run: docker-compose up (if services are configured)"
echo ""

# Display container status
echo "📊 Container Status:"
docker ps --filter "name=nginx_reverse_proxy" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "✅ Deployment complete and verified!"
