# QUICK_START.md - Instrucciones Rápidas

## ⚡ Start en 2 Minutos

### Opción 1: Deployment Standalone (Testing)
```bash
# Desde nginx_reverse_proxy/simple_implementation/
make deploy
# O manualmente:
chmod +x deploy.sh && ./deploy.sh
```

### Opción 2: Integración con Sistema Principal  
```bash
# Desde directorio raíz del proyecto:
cd nginx_reverse_proxy/simple_implementation
make integrate
cd ../..
docker-compose up nginx_reverse_proxy
```

## 🧪 Verificación Inmediata
```bash
curl http://localhost/nginx-health
```

## 📋 Comandos Útiles
```bash
make help          # Ver todos los comandos
make test           # Health checks
make logs           # Ver logs en tiempo real
make status         # Estado del container
```

## 🚨 Troubleshooting Rápido

**Puerto 80 ocupado:**
```bash
sudo lsof -i :80
```

**Container no inicia:**
```bash
make logs
```

**Backend/Frontend no conecta:**
```bash
docker ps | grep "module_dashboard"
```

---
✅ **MVP Completo** - Listo para producción
