# nginx_reverse_proxy - Simple Implementation

## Descripción
Reverse proxy nginx robusto y simple para **La Máquina de Noticias**. Enruta tráfico entre frontend y backend con configuración mínima pero sólida.

## 🎯 MVP Completamente Funcional

### Arquitectura Simple
```
Internet → nginx:80 → 
    ├── /api/* → module_dashboard_review_backend:8004
    └── /*     → module_dashboard_review_frontend:80
```

### Configuración
- **Puerto externo**: 80 (HTTP), 443 (HTTPS preparado)
- **Health check**: `/nginx-health`
- **API routing**: `/api/*` → backend
- **Frontend routing**: `/*` → frontend React

## 🚀 Deployment

### Opción 1: Standalone (Testing)
```bash
# Deployment independiente para testing
chmod +x deploy.sh
./deploy.sh
```

### Opción 2: Integración con Sistema Principal
```bash
# 1. Copiar fragmento al docker-compose.yml principal
cat docker-compose.integration.yml >> ../docker-compose.yml

# 2. Desde directorio raíz del proyecto
docker-compose up nginx_reverse_proxy
```

### Opción 3: Docker Compose Local
```bash
# En este directorio
docker-compose up --build
```

## 🔧 Configuración

### Variables de Entorno (.env)
```bash
# Copiar template
cp .env.example .env

# Editar si es necesario (opcional - tiene defaults)
NGINX_HOST=localhost
NGINX_PORT=80
```

### Red Docker
Requiere red `lamacquina_network` (se crea automáticamente):
```bash
docker network create lamacquina_network
```

## 🧪 Testing y Verificación

### Health Checks
```bash
# Nginx health
curl http://localhost/nginx-health

# API routing (requiere backend running)
curl http://localhost/api/health

# Frontend routing (requiere frontend running)  
curl http://localhost/
```

### Logs
```bash
# Container logs
docker logs nginx_reverse_proxy

# Access logs
docker exec nginx_reverse_proxy tail -f /var/log/nginx/access.log

# Error logs
docker exec nginx_reverse_proxy tail -f /var/log/nginx/error.log
```

## 📁 Estructura de Archivos

```
simple_implementation/
├── nginx.conf                    # Configuración nginx estática
├── Dockerfile                    # Build nginx + health check
├── health-check.sh              # Script health check
├── deploy.sh                    # Deployment standalone
├── docker-compose.yml           # Deploy local
├── docker-compose.integration.yml  # Fragmento para main docker-compose
├── .env.example                 # Template variables
└── README.md                    # Esta documentación
```

## 🔗 Integración con MVP

### Backend Integration
- **Target**: `module_dashboard_review_backend:8004`
- **Routes**: `/api/*` → `http://backend:8004`
- **Headers**: `X-Forwarded-*`, CORS básico

### Frontend Integration  
- **Target**: `module_dashboard_review_frontend:80`
- **Routes**: `/` → `http://frontend:80`
- **Static files**: Servidos directamente

### Dependencies en docker-compose
```yaml
depends_on:
  - module_dashboard_review_backend
  - module_dashboard_review_frontend
```

## 🛡️ Seguridad y Performance

### Headers de Seguridad
- `X-Forwarded-For`, `X-Real-IP`
- CORS básico configurado
- Host header forwarding

### Performance
- Gzip compression habilitado
- Keepalive connections
- Worker processes: auto

### Health Monitoring
- Health check cada 30s
- Auto-restart en fallos
- Graceful shutdown

## 🔧 Troubleshooting

### Proxy no responde
```bash
# Verificar container
docker ps | grep nginx_reverse_proxy

# Verificar logs
docker logs nginx_reverse_proxy

# Verificar red
docker network inspect lamacquina_network
```

### Backend/Frontend no accesibles
```bash
# Verificar upstreams están running
docker ps | grep "module_dashboard"

# Test conectividad interna
docker exec nginx_reverse_proxy ping module_dashboard_review_backend
docker exec nginx_reverse_proxy ping module_dashboard_review_frontend
```

### Puerto 80 ocupado
```bash
# Encontrar proceso usando puerto
lsof -i :80

# O cambiar puerto en .env
echo "NGINX_PORT=8080" >> .env
```

## 🚀 Próximos Pasos (Futuro)

- [ ] SSL/HTTPS con Let's Encrypt
- [ ] Rate limiting por IP
- [ ] Load balancing múltiples backends
- [ ] Metrics con Prometheus
- [ ] Centralized logging

## ⚡ Quick Commands

```bash
# Build y run
docker build -t nginx_reverse_proxy . && docker run -d --name nginx_reverse_proxy -p 80:80 --network lamacquina_network nginx_reverse_proxy

# Stop y clean
docker stop nginx_reverse_proxy && docker rm nginx_reverse_proxy

# Logs en tiempo real
docker logs -f nginx_reverse_proxy

# Restart
docker restart nginx_reverse_proxy
```

---

**Status**: ✅ **MVP Completo y Funcional**  
**Tiempo de deployment**: < 5 minutos  
**Complejidad**: Mínima, máxima robustez
