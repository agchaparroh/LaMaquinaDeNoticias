# Guía de Administración - La Máquina de Noticias

Esta guía está dirigida a administradores del sistema que necesitan gestionar spiders, configurar alertas y mantener el sistema funcionando.

## 📋 Índice
1. [Gestión de Spiders](#gestión-de-spiders)
2. [Configuración de Alertas](#configuración-de-alertas)
3. [Monitoreo y Métricas](#monitoreo-y-métricas)
4. [Mantenimiento del Sistema](#mantenimiento-del-sistema)
5. [Gestión de Usuarios](#gestión-de-usuarios)
6. [Backup y Recuperación](#backup-y-recuperación)

---

## 🕷️ Gestión de Spiders

### Desplegar un nuevo spider

Cuando el equipo de desarrollo crea un nuevo spider, debes desplegarlo:

```bash
# 1. Navegar al directorio del módulo
cd /ruta/a/LaMaquinaDeNoticias/src/module_scraper

# 2. Desplegar el proyecto
scrapyd-deploy default -p scraper_core

# 3. Verificar que se desplegó
curl http://localhost:6800/listversions.json?project=scraper_core
```

### Ejecutar spider manualmente

#### Opción 1: Desde ScrapydWeb (Recomendado)
1. Acceder a http://localhost:5000
2. Ir a "Deploy"
3. Seleccionar:
   - Project: `scraper_core`
   - Spider: El que necesites (ej: `elpais_spider`)
4. Click en "Run"

#### Opción 2: Por línea de comandos
```bash
# Ejecutar spider específico
curl http://localhost:6800/schedule.json \
  -d project=scraper_core \
  -d spider=nombre_del_spider

# Verificar que está ejecutándose
curl http://localhost:6800/listjobs.json?project=scraper_core
```

### Detener spider en ejecución

#### Desde ScrapydWeb:
1. Ir a "Jobs"
2. Buscar el spider activo
3. Click en "Cancel"

#### Por comando:
```bash
# Necesitas el job_id (visible en ScrapydWeb)
curl http://localhost:6800/cancel.json \
  -d project=scraper_core \
  -d job=JOB_ID_AQUI
```

### Ver logs de un spider

#### En ScrapydWeb:
1. Ir a "Jobs" → Click en el spider
2. Click en "Log" para ver registro completo

#### Por comando:
```bash
# Logs en tiempo real
docker-compose logs -f module_scraper | grep "nombre_spider"

# Logs históricos
docker-compose exec module_scraper cat /app/logs/nombre_spider.log
```

---

## 🔔 Configuración de Alertas

### Configurar alertas por Email

1. **Editar archivo `.env`**:
```env
# Servidor SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=contraseña-de-aplicación  # No uses tu contraseña normal
SMTP_FROM=alertas@lamaquina.com
SMTP_TO=admin@tuempresa.com,equipo@tuempresa.com  # Múltiples con comas
```

2. **Reiniciar servicios**:
```bash
docker-compose restart module_scraper
```

### Configurar webhook para integraciones

Para recibir alertas en Slack, Discord, o tu sistema personalizado:

```env
# En .env
SPIDERMON_WEBHOOK_URL=https://hooks.slack.com/services/TU/WEBHOOK/AQUI
```

Formato del webhook que envía Spidermon:
```json
{
  "timestamp": "2024-01-20T10:30:00Z",
  "spider": {
    "name": "elpais_spider",
    "project": "lamaquina_scraper"
  },
  "status": "error",
  "stats": {
    "items_scraped": 45,
    "pages_downloaded": 50,
    "duration_seconds": 120,
    "http_errors": {"403": 5, "500": 2}
  },
  "monitors_failed": [
    {
      "monitor": "HTTPErrorRateMonitor",
      "message": "Tasa de error HTTP: 14%",
      "severity": "critical"
    }
  ]
}
```

### Ajustar umbrales de alerta

Editar en `.env` para cambiar cuándo se disparan las alertas:

```env
# Umbrales de Spidermon
SPIDERMON_MIN_ITEMS_SCRAPED=10        # Mínimo de items esperados
SPIDERMON_MAX_CRITICAL_ERRORS=0       # Errores críticos permitidos
SPIDERMON_MAX_ERROR_MESSAGES=5        # Mensajes de error permitidos
SPIDERMON_MAX_RESPONSE_TIME=5000      # Tiempo máximo respuesta (ms)
```

---

## 📊 Monitoreo y Métricas

### Métricas clave a vigilar

#### 1. **Tasa de éxito de extracción**
- **Dónde verla**: ScrapydWeb → Stats
- **Valor ideal**: >95%
- **Si baja**: Revisar logs de spiders fallidos

#### 2. **Items por ejecución**
- **Dónde verla**: Jobs → columna "Items"
- **Valor esperado**: Varía por spider (ej: 50-200 para diarios grandes)
- **Si es 0**: El spider no está extrayendo, revisar selectores

#### 3. **Tiempo de respuesta**
- **Dónde verla**: En logs, buscar "download_latency"
- **Valor normal**: <3 segundos
- **Si es alto**: Sitio lento o problemas de red

#### 4. **Errores HTTP**
- **Códigos problemáticos**:
  - `403`: Acceso prohibido (posible bloqueo)
  - `429`: Demasiadas peticiones (rate limiting)
  - `500-504`: Errores del servidor

### Comandos útiles para diagnóstico

```bash
# Ver estado general de Scrapyd
curl http://localhost:6800/daemonstatus.json | python -m json.tool

# Contar items extraídos hoy
docker-compose exec postgres psql -U postgres -d lamaquina -c \
  "SELECT COUNT(*) FROM articulos WHERE fecha_recopilacion > NOW() - INTERVAL '24 hours';"

# Ver spiders con más errores
docker-compose logs module_scraper | grep ERROR | grep -o "spider=\w*" | sort | uniq -c | sort -rn

# Verificar uso de recursos
docker stats module_scraper scrapyd scrapydweb
```

---

## 🔧 Mantenimiento del Sistema

### Tareas diarias

1. **Revisar panel ScrapydWeb**
   - Verificar spiders en rojo
   - Comprobar que las programaciones se ejecutaron

2. **Verificar espacio en disco**
```bash
df -h | grep -E "(/$|/var/lib/docker)"
```

### Tareas semanales

1. **Limpiar logs antiguos**
```bash
# Logs de más de 7 días
find /app/logs -name "*.log" -mtime +7 -delete
```

2. **Revisar rendimiento**
   - Analizar spiders más lentos
   - Optimizar los que consumen más recursos

3. **Actualizar documentación**
   - Documentar nuevos spiders
   - Actualizar configuraciones

### Tareas mensuales

1. **Backup de configuración**
```bash
# Backup de configuraciones importantes
tar -czf backup_scraper_$(date +%Y%m%d).tar.gz \
  scrapyd.conf \
  scrapydweb/scrapydweb_settings_v10.py \
  scraper_core/settings.py \
  .env
```

2. **Revisar y actualizar dependencias**
```bash
# Ver paquetes desactualizados
docker-compose exec module_scraper pip list --outdated
```

---

## 👥 Gestión de Usuarios

### Cambiar contraseña de ScrapydWeb

1. Generar nueva contraseña segura
2. Actualizar en `.env`:
```env
SCRAPYDWEB_PASSWORD=nueva_contraseña_segura
```
3. Reiniciar servicio:
```bash
docker-compose restart scrapydweb
```

### Agregar usuarios adicionales (requiere modificación de código)

ScrapydWeb no soporta múltiples usuarios nativamente. Opciones:
- Usar un proxy reverso con autenticación (nginx)
- Implementar autenticación externa (LDAP, OAuth)

---

## 💾 Backup y Recuperación

### Backup de datos críticos

#### 1. Base de datos SQLite de ScrapydWeb
```bash
# Crear backup
docker-compose exec scrapydweb sqlite3 /app/data/scrapydweb.db ".backup /app/data/backup.db"

# Copiar a host
docker cp lamaquina_scrapydweb:/app/data/backup.db ./backups/
```

#### 2. Configuraciones
```bash
# Script de backup completo
#!/bin/bash
BACKUP_DIR="./backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Configuraciones
cp -r src/module_scraper/scrapyd.conf $BACKUP_DIR/
cp -r src/module_scraper/scrapydweb $BACKUP_DIR/
cp .env $BACKUP_DIR/

# Base de datos
docker-compose exec scrapydweb sqlite3 /app/data/scrapydweb.db ".backup /tmp/scrapydweb_backup.db"
docker cp lamaquina_scrapydweb:/tmp/scrapydweb_backup.db $BACKUP_DIR/

echo "Backup completado en $BACKUP_DIR"
```

### Restauración

#### Restaurar configuración:
```bash
# Detener servicios
docker-compose stop scrapyd scrapydweb

# Restaurar archivos
cp backups/20240120/scrapyd.conf src/module_scraper/
cp -r backups/20240120/scrapydweb/* src/module_scraper/scrapydweb/
cp backups/20240120/.env .

# Restaurar base de datos
docker cp backups/20240120/scrapydweb_backup.db lamaquina_scrapydweb:/tmp/
docker-compose exec scrapydweb sqlite3 /app/data/scrapydweb.db ".restore /tmp/scrapydweb_backup.db"

# Reiniciar servicios
docker-compose up -d scrapyd scrapydweb
```

---

## 🚨 Acciones de emergencia

### Si todos los spiders fallan:
1. Verificar conectividad a internet
2. Revisar si Scrapyd está funcionando
3. Verificar credenciales de Supabase
4. Reiniciar servicios

### Si un sitio bloquea las extracciones:
1. Reducir velocidad (aumentar DOWNLOAD_DELAY)
2. Rotar user agents
3. Considerar usar proxies
4. Contactar al equipo de desarrollo

### Comandos de emergencia:
```bash
# Reiniciar todo el sistema de scraping
docker-compose restart module_scraper scrapyd scrapydweb

# Ver logs en tiempo real
docker-compose logs -f --tail=100 module_scraper

# Detener TODOS los spiders activos
curl http://localhost:6800/listjobs.json?project=scraper_core | \
  jq -r '.running[].id' | \
  xargs -I {} curl http://localhost:6800/cancel.json -d project=scraper_core -d job={}
```

---

📖 **Siguiente**: [Especificaciones Técnicas](TECHNICAL_SPECIFICATIONS.md) - Detalles técnicos del sistema