#!/bin/bash
# integration.sh - Script para integrar nginx con el sistema principal
# Ejecutar desde el directorio raíz del proyecto

set -e

echo "🔗 Integrating nginx_reverse_proxy with main system"
echo "==================================================="

# Verificar que estamos en el directorio raíz del proyecto
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   (where the main docker-compose.yml is located)"
    exit 1
fi

# Verificar que el directorio nginx existe
if [ ! -d "nginx_reverse_proxy" ]; then
    echo "❌ Error: nginx_reverse_proxy directory not found"
    exit 1
fi

# Verificar que tiene la nueva estructura
if [ ! -f "nginx_reverse_proxy/docker/Dockerfile" ]; then
    echo "❌ Error: nginx_reverse_proxy not properly structured (missing docker/Dockerfile)"
    exit 1
fi

# Backup del docker-compose.yml actual
echo "📋 Creating backup of current docker-compose.yml..."
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)

# Verificar si nginx ya está en docker-compose.yml
if grep -q "nginx_reverse_proxy" docker-compose.yml; then
    echo "⚠️  nginx_reverse_proxy already exists in docker-compose.yml"
    echo "   If you want to update it, please remove it manually first"
    echo "   Backup created: docker-compose.yml.backup.*"
    exit 1
fi

# Añadir nginx service al docker-compose.yml
echo "➕ Adding nginx_reverse_proxy service to docker-compose.yml..."

# Crear fragment temporal
cat << EOF > /tmp/nginx_fragment.yml

  nginx_reverse_proxy:
    build:
      context: ./nginx_reverse_proxy
      dockerfile: docker/Dockerfile
    container_name: nginx_reverse_proxy
    ports:
      - "80:80"
      - "443:443"
    networks:
      - lamacquina_network
    depends_on:
      - module_dashboard_review_backend
      - module_dashboard_review_frontend
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "/usr/local/bin/health-check.sh"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    volumes:
      - nginx_logs:/var/log/nginx
    environment:
      - NGINX_HOST=\${NGINX_HOST:-localhost}
      - NGINX_PORT=\${NGINX_PORT:-80}
EOF

# Insertar el fragment después de la línea services:
sed -i '/^services:/r /tmp/nginx_fragment.yml' docker-compose.yml

# Añadir volume si no existe
if ! grep -q "nginx_logs:" docker-compose.yml; then
    echo "➕ Adding nginx_logs volume..."
    
    # Verificar si hay sección volumes
    if grep -q "^volumes:" docker-compose.yml; then
        # Añadir al final de volumes existente
        sed -i '/^volumes:/a \  nginx_logs:\n    driver: local' docker-compose.yml
    else
        # Crear sección volumes al final
        echo "" >> docker-compose.yml
        echo "volumes:" >> docker-compose.yml
        echo "  nginx_logs:" >> docker-compose.yml
        echo "    driver: local" >> docker-compose.yml
    fi
fi

# Cleanup
rm /tmp/nginx_fragment.yml

echo "✅ Integration completed!"
echo ""
echo "📋 Changes made:"
echo "   • Added nginx_reverse_proxy service to docker-compose.yml"
echo "   • Added nginx_logs volume"
echo "   • Created backup: docker-compose.yml.backup.*"
echo ""
echo "🚀 Next steps:"
echo "   1. Review changes: git diff docker-compose.yml"
echo "   2. Start system: docker-compose up --build"
echo "   3. Test access: curl http://localhost/nginx-health"
echo ""
echo "🔍 Services will be available at:"
echo "   • Frontend: http://localhost/"
echo "   • API: http://localhost/api/"
echo "   • Health: http://localhost/nginx-health"
echo ""
echo "🎉 nginx_reverse_proxy is now integrated!"
