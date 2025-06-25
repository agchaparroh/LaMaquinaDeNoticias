# 🚀 Spider Factory 2.0 - Guía Rápida

## Instalación en 3 pasos

### 1. Clonar y configurar

```bash
# Clonar repositorio
git clone [repository-url]
cd LaMaquinaDeNoticias/src/spider_factory

# Crear archivo de configuración
make create-env

# Editar .env y agregar tu API key de Firecrawl
nano .env
```

### 2. Construir y levantar

```bash
# Construir imágenes Docker
make build

# Levantar todos los servicios
make up

# Ver logs (opcional)
make logs
```

### 3. Acceder a la aplicación

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🎯 Uso Rápido

### Opción 1: Interfaz Web

1. Abrir http://localhost:3000
2. Click en "Nuevo Spider"
3. Pegar URL del sitio de noticias
4. Click en "Analizar"
5. Revisar resultados y "Generar Spider"
6. Descargar archivo .py generado

### Opción 2: API REST

```bash
# Analizar sitio
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example-news.com"}'

# Generar spider con el resultado
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_result": { ... },
    "spider_name": "example_spider",
    "site_name": "Example News"
  }'
```

### Opción 3: Carga Masiva

1. Crear archivo CSV:
```csv
url,name,category
https://site1.com,Site 1,tech
https://site2.com,Site 2,sports
```

2. Subir vía interfaz web o API:
```bash
curl -X POST "http://localhost:8000/batch/analyze" \
  -F "file=@sites.csv" \
  -F "session_id=batch001"
```

## 🛠️ Comandos Útiles

```bash
# Ver logs del backend
make logs-backend

# Abrir shell en backend
make shell-backend

# Ver estadísticas de Redis
make shell-redis

# Detener todo
make down

# Limpiar archivos generados
make clean
```

## 🔧 Desarrollo Local

Para desarrollo sin Docker:

```bash
# Levantar solo Redis
make dev

# Instalar dependencias
make install

# Terminal 1: Backend
make run-backend

# Terminal 2: Frontend
make run-frontend
```

## 📊 Verificar Estado

```bash
# Health check
make check-health

# Ver contenedores
make ps

# Estadísticas en vivo
make stats
```

## 🆘 Solución de Problemas

### Error: Puerto en uso
```bash
# Verificar qué usa el puerto
lsof -i :8000
lsof -i :3000

# Cambiar puertos en docker-compose.yml
```

### Error: Redis no conecta
```bash
# Verificar Redis
make shell-redis
> PING
# Debe responder PONG
```

### Error: API key inválida
```bash
# Verificar .env
cat .env | grep FIRECRAWL

# Reiniciar backend
make prod-restart
```

## 📚 Más Información

- README completo: [README.md](README.md)
- Documentación API: http://localhost:8000/docs
- Reportar bugs: [Issues](https://github.com/...)

---

**¿Necesitas ayuda?** Abre un issue en el repositorio.