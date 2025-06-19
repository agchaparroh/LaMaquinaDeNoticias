# Pruebas de Docker

Este directorio contiene scripts para verificar el correcto funcionamiento del contenedor Docker.

## 🧪 Scripts Disponibles

### 1. test_docker_deployment.sh (Bash)
Script completo de pruebas que verifica:
- ✅ Construcción de imagen Docker
- ✅ Inicio del contenedor
- ✅ Health checks (básico y detallado)
- ✅ Seguridad (usuario no-root)
- ✅ Variables de entorno
- ✅ Binding de puertos
- ✅ Comportamiento de restart
- ✅ Manejo de errores

**Ejecución:**
```bash
# Dar permisos de ejecución
chmod +x scripts/test_docker_deployment.sh

# Ejecutar pruebas
./scripts/test_docker_deployment.sh
```

### 2. test_docker_integration.py (Python)
Script de pruebas más detallado con validaciones adicionales:
- ✅ Todas las pruebas del script bash
- ✅ Análisis de logs
- ✅ Pruebas de endpoints HTTP
- ✅ Validación de respuestas JSON
- ✅ Reporte detallado de resultados

**Ejecución:**
```bash
# Ejecutar con Python
python scripts/test_docker_integration.py
```

## 📋 Prerrequisitos

1. **Docker instalado y funcionando**
   ```bash
   docker --version
   docker ps
   ```

2. **Archivo .env configurado**
   ```bash
   cp .env.example .env
   # Editar .env con las credenciales de Supabase
   ```

3. **Puertos disponibles**
   - Puerto 8004 debe estar libre

## 🚀 Ejecución Rápida

Para ejecutar todas las pruebas:

```bash
# Opción 1: Script bash
./scripts/test_docker_deployment.sh

# Opción 2: Script Python (más detallado)
python scripts/test_docker_integration.py
```

## 🔍 Pruebas Manuales Adicionales

### Verificar construcción multi-arquitectura:
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t module_dashboard_review_backend .
```

### Verificar límites de recursos:
```bash
docker stats module_dashboard_review_backend
```

### Probar con docker-compose:
```bash
docker-compose up -d
docker-compose ps
docker-compose logs -f
```

### Verificar conectividad de red:
```bash
docker exec module_dashboard_review_backend ping module_pipeline
```

## 🛠️ Troubleshooting

### Si las pruebas fallan:

1. **Verificar logs detallados:**
   ```bash
   docker logs module_dashboard_review_backend --details
   ```

2. **Inspeccionar el contenedor:**
   ```bash
   docker inspect module_dashboard_review_backend
   ```

3. **Verificar red:**
   ```bash
   docker network inspect lamacquina_network
   ```

4. **Limpiar y reintentar:**
   ```bash
   docker stop module_dashboard_review_backend
   docker rm module_dashboard_review_backend
   docker rmi module_dashboard_review_backend
   ```

## 📊 Interpretación de Resultados

- **✅ Verde**: La prueba pasó correctamente
- **⚠️ Amarillo**: Advertencia, revisar pero no crítico
- **❌ Rojo**: Error crítico, debe solucionarse

Los scripts generan un resumen al final con el total de pruebas pasadas.

## 🔒 Pruebas de Seguridad

Las pruebas verifican:
- Usuario no-root (appuser con UID 1000)
- Variables sensibles no expuestas en logs
- Health checks sin información sensible

---

Para más información sobre el despliegue Docker, consultar:
- `/Dockerfile` - Configuración de la imagen
- `/docker-compose.yml` - Configuración de servicios
- `/DOCKER_INTEGRATION.md` - Guía de integración
