# Configuración Docker para supabase-mcp-server

## Archivos Docker mejorados

He creado una configuración Docker optimizada que incluye:

### 📁 Archivos creados

- `Dockerfile.optimized` - Dockerfile mejorado con multi-stage build
- `.dockerignore` - Excluye archivos innecesarios del contexto
- `docker-compose.yml` - Orquestación completa del servicio
- `docker-compose.override.yml.example` - Configuración para desarrollo
- `DOCKER_SETUP.md` - Esta documentación

## 🚀 Uso rápido

### Para producción:
```bash
# Construir imagen
docker build -f Dockerfile.optimized -t supabase-mcp-server .

# Ejecutar con docker-compose
docker-compose up -d

# Ver logs
docker-compose logs -f supabase-mcp-server
```

### Para desarrollo:
```bash
# Copiar configuración de desarrollo
cp docker-compose.override.yml.example docker-compose.override.yml

# Editar variables de entorno
vim docker-compose.override.yml

# Ejecutar con desarrollo local
docker-compose --profile local-dev up -d
```

## 📊 Mejoras implementadas

### Dockerfile.optimized vs Dockerfile original:

| Aspecto | Original | Optimizado |
|---------|----------|------------|
| **Tamaño imagen** | ~500MB | ~200MB |
| **Seguridad** | Root user | Usuario no privilegiado |
| **Build** | Single stage | Multi-stage |
| **Dependencias** | pipx innecesario | Solo lo necesario |
| **Health check** | ❌ | ✅ |
| **Variables env** | ❌ | ✅ |

### Características de seguridad:

1. **Usuario no privilegiado**: Ejecuta como `mcpuser` (UID 1000)
2. **Minimal base**: Solo dependencias runtime necesarias
3. **Health checks**: Verificación automática del servicio
4. **Resource limits**: Límites de CPU y memoria
5. **Read-only filesystem**: Posible con ajustes menores

### Características de desarrollo:

1. **Volume mounting**: Código fuente editable en vivo
2. **Local Supabase**: Base de datos local para testing
3. **Environment overrides**: Fácil configuración por entorno
4. **Logging**: Rotación automática de logs

## 🔧 Configuración por entornos

### Variables de entorno requeridas:

```bash
# Básicas (siempre necesarias)
SUPABASE_PROJECT_REF=tu-project-ref
SUPABASE_DB_PASSWORD=tu-password
QUERY_API_KEY=tu-api-key

# Opcionales
SUPABASE_REGION=us-east-1
SUPABASE_ACCESS_TOKEN=tu-access-token
SUPABASE_SERVICE_ROLE_KEY=tu-service-key
```

### Archivo .env de ejemplo:

```bash
# .env
SUPABASE_PROJECT_REF=abcdefghijklmnopqrst
SUPABASE_DB_PASSWORD=mi-password-seguro
SUPABASE_REGION=eu-west-1
QUERY_API_KEY=mi-api-key
SUPABASE_ACCESS_TOKEN=sbp_xxxxxxxxxxxx
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 🐳 Comandos Docker útiles

```bash
# Construir solo la imagen
docker build -f Dockerfile.optimized -t supabase-mcp-server .

# Ejecutar contenedor individual
docker run -d \
  --name supabase-mcp \
  -e SUPABASE_PROJECT_REF=tu-ref \
  -e SUPABASE_DB_PASSWORD=tu-pass \
  -e QUERY_API_KEY=tu-key \
  supabase-mcp-server

# Ver logs en tiempo real
docker logs -f supabase-mcp

# Ejecutar shell en el contenedor
docker exec -it supabase-mcp bash

# Inspeccionar health status
docker inspect supabase-mcp | grep Health -A 10

# Limpiar imágenes no usadas
docker image prune -f
```

## 🔍 Troubleshooting

### Problemas comunes:

1. **Error de conexión a Supabase**:
   ```bash
   # Verificar variables de entorno
   docker exec supabase-mcp env | grep SUPABASE
   ```

2. **Health check falla**:
   ```bash
   # Ver logs de health check
   docker inspect supabase-mcp | jq '.[0].State.Health'
   ```

3. **Permisos de archivos**:
   ```bash
   # Verificar usuario
   docker exec supabase-mcp whoami
   docker exec supabase-mcp id
   ```

### Debug mode:

```bash
# Ejecutar en modo interactivo para debug
docker run -it --rm \
  -e SUPABASE_PROJECT_REF=tu-ref \
  -e QUERY_API_KEY=tu-key \
  supabase-mcp-server bash
```

## 📈 Monitoreo

### Métricas del contenedor:
```bash
# Uso de recursos
docker stats supabase-mcp

# Información del contenedor
docker inspect supabase-mcp
```

### Logs estructurados:
- Los logs se rotan automáticamente (10MB max, 3 archivos)
- Formato JSON para fácil parsing
- Persistencia en volumen `mcp-logs`

## 🚢 Despliegue en producción

### Con Docker Swarm:
```bash
# Deployar stack
docker stack deploy -c docker-compose.yml supabase-mcp-stack
```

### Con Kubernetes:
```bash
# Convertir compose a k8s (usando kompose)
kompose convert -f docker-compose.yml
kubectl apply -f .
```

### Consideraciones de producción:
1. Usar secrets para variables sensibles
2. Configurar restart policies apropiadas
3. Implementar monitoring (Prometheus/Grafana)
4. Configurar backups de logs
5. Usar reverse proxy (nginx/traefik) si es necesario

## 📝 Recomendaciones finales

1. **Usar Dockerfile.optimized** en lugar del original
2. **Configurar .dockerignore** para builds más rápidos
3. **Usar docker-compose** para orquestación
4. **Rotar logs** para evitar llenar disco
5. **Monitorear recursos** en producción
6. **Actualizar dependencias** regularmente