# Integración de Spider Factory 2.0 - COMPLETADA ✅

## 📋 Cambios Implementados

### 1. **Configuración de Puertos** ✅
- Backend API configurado en puerto 8005 (evita conflicto con 8000)
- Frontend configurado en puerto 3002 (evita conflicto con 3000)
- Redis compartido con el sistema principal

### 2. **Docker Compose** ✅
Agregados los siguientes servicios al `docker-compose.yml` principal:
- `spider_factory_backend`: API de generación de spiders
- `spider_factory_frontend`: Interfaz web
- `redis`: Cache compartido para todo el sistema

**Características**:
- Volúmenes compartidos entre spider_factory y module_scraper
- Red `lamacquina_network` para comunicación interna
- Variables de entorno integradas

### 3. **Script de Migración** ✅
Creado `migrate_spider.py` que:
- Convierte spiders de Scrapy estándar a BaseArticleSpider
- Adapta imports y custom_settings
- Agrega pipelines de Supabase
- Mapea campos al formato ArticuloItem
- Crea backups antes de migrar

**Uso**:
```bash
# Migrar todos los spiders
python migrate_spider.py

# Migrar un spider específico
python migrate_spider.py --spider mi_spider.py

# Especificar directorios
python migrate_spider.py --input ./generated_spiders --output ../module_scraper/scraper_core/spiders
```

### 4. **Variables de Entorno** ✅
- Creado `.env.example` en spider_factory
- Actualizado `.env.example` principal con configuración de Spider Factory
- Configuración para usar Redis compartido

### 5. **Archivos Creados/Modificados**

#### Nuevos archivos:
1. `/src/spider_factory/.env.example` - Variables de entorno del módulo
2. `/src/spider_factory/migrate_spider.py` - Script de migración
3. `/src/spider_factory/docs/INTEGRATION_COMPLETED.md` - Esta documentación

#### Archivos modificados:
1. `/docker-compose.yml` - Agregados servicios de Spider Factory y Redis
2. `/.env.example` - Agregada configuración de Spider Factory

## 🚀 Próximos Pasos

### 1. Configuración Nginx (Pendiente)
Agregar a `nginx_reverse_proxy/config/nginx.conf`:
```nginx
# Spider Factory API
location /spider-factory/api/ {
    proxy_pass http://spider_factory_backend:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# Spider Factory Frontend
location /spider-factory/ {
    proxy_pass http://spider_factory_frontend/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# WebSocket for Spider Factory
location /spider-factory/ws/ {
    proxy_pass http://spider_factory_backend:8000/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### 2. Probar la integración
```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Editar .env y agregar FIRECRAWL_API_KEY

# 2. Construir y levantar servicios
docker-compose up -d redis spider_factory_backend spider_factory_frontend

# 3. Verificar servicios
curl http://localhost:8005/health  # Backend API
curl http://localhost:3002         # Frontend
```

### 3. Flujo de trabajo integrado
1. Acceder a Spider Factory: http://localhost:3002
2. Generar un spider usando la interfaz
3. El spider se guarda en `generated_spiders/`
4. Ejecutar migración: `python migrate_spider.py`
5. Spider migrado disponible en module_scraper

## 📊 Estado de la Integración

| Componente | Estado | Notas |
|------------|--------|-------|
| Configuración de puertos | ✅ | 8005 (API), 3002 (UI) |
| Docker Compose | ✅ | Servicios agregados |
| Script de migración | ✅ | Funcional y probado |
| Variables de entorno | ✅ | .env.example actualizado |
| Nginx proxy | ⏳ | Pendiente configuración |
| Autenticación JWT | ⏳ | Pendiente integración |

## 🔧 Troubleshooting

### Error: Puerto en uso
```bash
# Verificar puertos
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Detener servicio conflictivo
docker stop [nombre_servicio]
```

### Error: Redis no conecta
```bash
# Verificar Redis
docker exec -it lamacquina_redis redis-cli ping

# Ver logs
docker logs lamacquina_redis
```

### Error: Migración falla
```bash
# Verificar sintaxis del spider
python syntax_check.py

# Ver log detallado
python migrate_spider.py --spider mi_spider.py --verbose
```

## ✅ Conclusión

Spider Factory 2.0 está integrado al ecosistema de La Máquina de Noticias con:
- Puertos configurados sin conflictos
- Docker Compose actualizado
- Script de migración funcional
- Documentación completa

El sistema está listo para desarrollo y pruebas locales.