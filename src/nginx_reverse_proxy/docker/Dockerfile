# Dockerfile - Nginx Reverse Proxy
# Imagen optimizada para Dashboard La Máquina de Noticias

FROM nginx:1.25-alpine

# Metadata
LABEL maintainer="La Máquina de Noticias"
LABEL description="Nginx reverse proxy for Dashboard modules"
LABEL version="1.0.0"

# Install dependencies for health checks and debugging
RUN apk add --no-cache \
    curl \
    bash \
    && rm -rf /var/cache/apk/*

# Copy nginx configuration from new location
COPY config/nginx.conf /etc/nginx/nginx.conf

# Create health check script
RUN cat > /usr/local/bin/health-check.sh << 'EOF'
#!/bin/bash
set -e

# Check nginx is running
if ! pgrep nginx > /dev/null; then
    echo "❌ Nginx process not running"
    exit 1
fi

# Check nginx internal health endpoint
if ! curl -f -s -o /dev/null http://localhost/nginx-health; then
    echo "❌ Nginx health endpoint failed"
    exit 1
fi

# Check if we can reach backend (optional - don't fail if backend is down)
if curl -f -s -o /dev/null --max-time 5 http://module_dashboard_review_backend:8004/health; then
    echo "✅ Backend reachable"
else
    echo "⚠️ Backend not reachable (may be starting up)"
fi

# Check if we can reach frontend (optional - don't fail if frontend is down)
if curl -f -s -o /dev/null --max-time 5 http://module_dashboard_review_frontend:80; then
    echo "✅ Frontend reachable"
else
    echo "⚠️ Frontend not reachable (may be starting up)"
fi

echo "✅ Nginx proxy is healthy"
exit 0
EOF

# Make health check script executable
RUN chmod +x /usr/local/bin/health-check.sh

# Create nginx user and set permissions
RUN addgroup -g 101 nginx || true \
    && adduser -D -H -u 101 -G nginx nginx || true

# Create log directory and set permissions
RUN mkdir -p /var/log/nginx \
    && chown -R nginx:nginx /var/log/nginx \
    && chown -R nginx:nginx /var/cache/nginx \
    && chown -R nginx:nginx /etc/nginx

# Security: Remove default nginx files
RUN rm -f /etc/nginx/conf.d/default.conf \
    && rm -rf /usr/share/nginx/html/*

# Create minimal error page
RUN cat > /usr/share/nginx/html/50x.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Error</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        h1 { color: #d32f2f; }
    </style>
</head>
<body>
    <h1>Service Temporarily Unavailable</h1>
    <p>The dashboard is currently experiencing issues. Please try again in a few moments.</p>
</body>
</html>
EOF

# Set correct permissions for error page
RUN chown nginx:nginx /usr/share/nginx/html/50x.html

# Expose ports
EXPOSE 80 443

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD /usr/local/bin/health-check.sh

# Run as nginx user
USER nginx

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
