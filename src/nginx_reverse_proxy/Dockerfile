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
RUN printf '#!/bin/bash\nset -e\n\n# Check nginx is running\nif ! pgrep nginx > /dev/null; then\n    echo "❌ Nginx process not running"\n    exit 1\nfi\n\n# Check nginx internal health endpoint\nif ! curl -f -s -o /dev/null http://localhost/nginx-health; then\n    echo "❌ Nginx health endpoint failed"\n    exit 1\nfi\n\n# Check if we can reach backend (optional - don'"'"'t fail if backend is down)\nif curl -f -s -o /dev/null --max-time 5 http://module_dashboard_review_backend:8004/health; then\n    echo "✅ Backend reachable"\nelse\n    echo "⚠️ Backend not reachable (may be starting up)"\nfi\n\n# Check if we can reach frontend (optional - don'"'"'t fail if frontend is down)\nif curl -f -s -o /dev/null --max-time 5 http://module_dashboard_review_frontend:80; then\n    echo "✅ Frontend reachable"\nelse\n    echo "⚠️ Frontend not reachable (may be starting up)"\nfi\n\necho "✅ Nginx proxy is healthy"\nexit 0\n' > /usr/local/bin/health-check.sh && \
    chmod +x /usr/local/bin/health-check.sh

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
RUN printf '<!DOCTYPE html>\n<html>\n<head>\n    <title>Error</title>\n    <style>\n        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }\n        h1 { color: #d32f2f; }\n    </style>\n</head>\n<body>\n    <h1>Service Temporarily Unavailable</h1>\n    <p>The dashboard is currently experiencing issues. Please try again in a few moments.</p>\n</body>\n</html>\n' > /usr/share/nginx/html/50x.html

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
