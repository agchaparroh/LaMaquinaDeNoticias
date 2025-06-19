# Integración con Docker Compose Principal

Este documento describe cómo integrar el módulo `module_dashboard_review_backend` con el sistema principal de La Máquina de Noticias.

## 📋 Opciones de Integración

### Opción 1: Integración Directa (Recomendada para Producción)

Si el módulo Dashboard está dentro del proyecto principal de LaMaquinaDeNoticias:

1. **Copiar el módulo al directorio principal:**
   ```bash
   cp -r Dashboard/module_dashboard_review_backend LaMaquinaDeNoticias/src/
   ```

2. **El servicio ya está definido en el docker-compose.yml principal:**
   ```yaml
   module_dashboard_review_backend:
     build:
       context: ./src/module_dashboard_review_backend
       dockerfile: Dockerfile
     container_name: lamacquina_dashboard_review_backend
     command: uvicorn main:app --host 0.0.0.0 --port 8004 --reload
     volumes:
       - ./src/module_dashboard_review_backend:/app
     ports:
       - "8004:8004"
     env_file:
       - .env
     networks:
       - lamacquina_network
     restart: unless-stopped
   ```

### Opción 2: Desarrollo Independiente

Para desarrollar el módulo de forma independiente mientras se conecta al sistema principal:

1. **Crear la red compartida (si no existe):**
   ```bash
   docker network create lamacquina_network
   ```

2. **Desde el directorio del módulo Dashboard:**
   ```bash
   cd Dashboard/module_dashboard_review_backend
   docker-compose up -d
   ```

3. **Verificar la conexión a la red:**
   ```bash
   docker network inspect lamacquina_network
   ```

### Opción 3: Docker Compose Override

Para desarrollo con ambos proyectos separados, crear un `docker-compose.override.yml`:

```yaml
# docker-compose.override.yml en LaMaquinaDeNoticias
version: '3.9'

services:
  module_dashboard_review_backend:
    build:
      context: ../../Dashboard/module_dashboard_review_backend
      dockerfile: Dockerfile
```

## 🔧 Configuración de Variables de Entorno

El módulo requiere las siguientes variables en el archivo `.env`:

```bash
# === REQUERIDAS ===
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# === OPCIONALES (con valores por defecto) ===
API_HOST=0.0.0.0
API_PORT=8004
CORS_ORIGINS=http://localhost:3001
LOG_LEVEL=INFO
ENVIRONMENT=production
```

## 🚀 Comandos de Despliegue

### Iniciar todo el sistema (desde LaMaquinaDeNoticias):
```bash
docker-compose up -d
```

### Iniciar solo el módulo Dashboard:
```bash
# Desde LaMaquinaDeNoticias
docker-compose up -d module_dashboard_review_backend

# O desde Dashboard/module_dashboard_review_backend
docker-compose up -d
```

### Reconstruir después de cambios:
```bash
docker-compose up -d --build module_dashboard_review_backend
```

## 🔍 Verificación de la Integración

1. **Verificar que el contenedor está corriendo:**
   ```bash
   docker ps | grep module_dashboard_review_backend
   ```

2. **Verificar los logs:**
   ```bash
   docker logs module_dashboard_review_backend
   ```

3. **Verificar el health check:**
   ```bash
   curl http://localhost:8004/health
   ```

4. **Verificar la conexión a la red:**
   ```bash
   docker exec module_dashboard_review_backend ping module_pipeline
   ```

## 📊 Dependencias con Otros Módulos

Actualmente, `module_dashboard_review_backend` **NO** tiene dependencias directas con otros módulos del sistema. Sin embargo:

- **Lee de la misma base de datos** Supabase que `module_pipeline` escribe
- **Comparte la red** `lamacquina_network` para futuras integraciones
- **Será consumido por** `module_dashboard_review_frontend` (puerto 3001)

## 🛠️ Troubleshooting

### Error: Network lamacquina_network not found
```bash
docker network create lamacquina_network
```

### Error: Port 8004 already in use
```bash
# Verificar qué está usando el puerto
lsof -i :8004
# O cambiar el puerto en docker-compose.yml y .env
```

### Error: Cannot connect to Supabase
- Verificar las variables SUPABASE_URL y SUPABASE_KEY en .env
- Verificar que el contenedor puede acceder a internet
- Revisar los logs con `docker logs module_dashboard_review_backend`

## 📝 Notas Adicionales

- El módulo está diseñado para ser **stateless** y puede escalarse horizontalmente
- Los health checks están configurados para integrarse con balanceadores de carga
- El comando en docker-compose usa `--reload` para desarrollo; remover en producción
- Los límites de recursos están configurados en el docker-compose.yml del módulo

---

Para más información sobre la arquitectura general, consultar:
- `/Docs/README.md` - Documentación general del sistema
- `/Docs/dashboard_backend_doc.md` - Especificaciones del módulo
