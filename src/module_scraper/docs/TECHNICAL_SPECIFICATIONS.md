# Especificaciones Técnicas - Sistema Scrapyd + ScrapydWeb + Spidermon

## 📋 Índice
1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Componentes y Versiones](#componentes-y-versiones)
3. [Configuración de Red](#configuración-de-red)
4. [APIs y Endpoints](#apis-y-endpoints)
5. [Esquemas de Datos](#esquemas-de-datos)
6. [Sistema de Monitoreo](#sistema-de-monitoreo)
7. [Flujo de Datos](#flujo-de-datos)

---

## 🏗️ Arquitectura del Sistema

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                        Docker Network                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐     ┌──────────────┐    ┌──────────────┐  │
│  │   Scrapyd   │────►│  ScrapydWeb  │    │   Spidermon  │  │
│  │  Port 6800  │     │  Port 5000   │    │  (Integrado) │  │
│  └──────┬──────┘     └──────┬───────┘    └──────┬───────┘  │
│         │                    │                    │          │
│         ▼                    ▼                    ▼          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Module Scraper (Scrapy)                 │    │
│  │            - Spiders                                 │    │
│  │            - Pipelines                               │    │
│  │            - Middlewares                             │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                   │
└───────────────────────────┼───────────────────────────────────┘
                            ▼
                    ┌──────────────┐
                    │   Supabase   │
                    │  PostgreSQL  │
                    └──────────────┘
```

### Arquitectura por Capas

1. **Capa de Presentación**
   - ScrapydWeb: Dashboard web para usuarios
   - API REST de Scrapyd: Para integraciones

2. **Capa de Aplicación**
   - Scrapyd: Servidor de ejecución de spiders
   - Scrapy: Framework de scraping
   - Spidermon: Sistema de monitoreo

3. **Capa de Datos**
   - SQLite: Base de datos local de ScrapydWeb
   - Supabase PostgreSQL: Almacenamiento principal
   - Archivos de log: Registro de actividades

---

## 🔧 Componentes y Versiones

### Stack Tecnológico

| Componente | Versión | Descripción | Puerto |
|------------|---------|-------------|--------|
| **Scrapyd** | 1.4.3 | Servidor de deployment de spiders | 6800 |
| **ScrapydWeb** | 1.4.0 | Dashboard de gestión visual | 5000 |
| **Scrapy** | 2.11.0 | Framework de web scraping | N/A |
| **Spidermon** | 1.18.0 | Framework de monitoreo | N/A |
| **Python** | 3.10 | Lenguaje base | N/A |
| **SQLite** | 3.x | BD de ScrapydWeb | N/A |

### Dependencias Principales

```python
# requirements.txt relevantes
scrapy==2.11.0
scrapyd==1.4.3
scrapyd-client==1.2.3
scrapydweb==1.4.0
spidermon[monitoring]==1.18.0
scrapy-playwright==0.0.33
python-dotenv==1.0.0
tenacity==8.2.3
```

### Configuración de Scrapyd

```ini
# scrapyd.conf
[scrapyd]
bind_address = 0.0.0.0
http_port = 6800
max_proc = 4
max_proc_per_cpu = 2
eggs_dir = /app/eggs
logs_dir = /app/logs
dbs_dir = /app/dbs
jobs_to_keep = 100
finished_to_keep = 100
```

### Configuración de ScrapydWeb

```python
# Extracto de scrapydweb_settings_v10.py
SCRAPYDWEB_BIND = '0.0.0.0'
SCRAPYDWEB_PORT = 5000
ENABLE_AUTH = True
USERNAME = os.getenv('SCRAPYDWEB_USERNAME', 'admin')
DATABASE_URL = 'sqlite:////app/data/scrapydweb.db'
SCRAPYD_SERVERS = ['scrapyd:6800']
```

---

## 🌐 Configuración de Red

### Red Docker

```yaml
# docker-compose.yml
networks:
  lamaquina_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Comunicación entre Servicios

| Origen | Destino | Puerto | Protocolo | Propósito |
|--------|---------|--------|-----------|-----------|
| ScrapydWeb | Scrapyd | 6800 | HTTP | Control de spiders |
| Module Scraper | Scrapyd | 6800 | HTTP | Deployment |
| Scrapyd | Module Scraper | N/A | IPC | Ejecución |
| Spidermon | SMTP Server | 587 | SMTP | Alertas email |
| Spidermon | Webhook URL | 443 | HTTPS | Alertas webhook |

### Volúmenes Persistentes

```yaml
volumes:
  scrapyd_data:    # Datos de spiders
  scrapyd_logs:    # Logs de ejecución
  scrapyd_dbs:     # Bases de datos de estado
  scrapydweb_data: # BD SQLite y configuración
```

---

## 🔌 APIs y Endpoints

### Scrapyd API

#### Endpoints principales:

| Método | Endpoint | Descripción | Parámetros |
|--------|----------|-------------|------------|
| GET | `/daemonstatus.json` | Estado del servidor | - |
| GET | `/listprojects.json` | Lista proyectos | - |
| GET | `/listversions.json` | Versiones de proyecto | `project` |
| GET | `/listspiders.json` | Lista spiders | `project` |
| GET | `/listjobs.json` | Lista trabajos | `project` |
| POST | `/schedule.json` | Ejecutar spider | `project`, `spider`, `settings` |
| POST | `/cancel.json` | Cancelar trabajo | `project`, `job` |

#### Ejemplos de uso:

```bash
# Estado del daemon
curl http://localhost:6800/daemonstatus.json

# Respuesta esperada:
{
  "status": "ok",
  "running": 2,
  "pending": 0,
  "finished": 10,
  "node_name": "lamaquina_scrapyd"
}

# Ejecutar spider
curl http://localhost:6800/schedule.json \
  -d project=scraper_core \
  -d spider=elpais_spider \
  -d setting=DOWNLOAD_DELAY=2

# Respuesta:
{
  "status": "ok",
  "jobid": "6487ec79947edab326d6db28a2d86511e8247444"
}
```

### ScrapydWeb API

ScrapydWeb no expone una API REST formal, pero ofrece:

- Autenticación HTTP Basic
- Endpoints HTML para interacción web
- WebSocket para actualizaciones en tiempo real

---

## 📊 Esquemas de Datos

### Schema de Validación (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ArticuloInItem",
  "type": "object",
  "required": [
    "url",
    "medio",
    "titular",
    "contenido_texto",
    "fecha_recopilacion"
  ],
  "properties": {
    "url": {
      "type": "string",
      "format": "uri",
      "pattern": "^https?://.*"
    },
    "medio": {
      "type": "string",
      "minLength": 2,
      "maxLength": 256
    },
    "titular": {
      "type": "string",
      "minLength": 5,
      "maxLength": 500
    },
    "contenido_texto": {
      "type": "string",
      "minLength": 100
    }
  }
}
```

### Estructura de Item Scrapy

```python
class ArticuloInItem(scrapy.Item):
    # Identificación
    url = scrapy.Field()
    storage_path = scrapy.Field()
    fuente = scrapy.Field()
    
    # Metadatos del medio
    medio = scrapy.Field()
    medio_url_principal = scrapy.Field()
    area_geografica = scrapy.Field()
    tipo_medio = scrapy.Field()
    
    # Contenido
    titular = scrapy.Field()
    contenido_texto = scrapy.Field()
    contenido_html = scrapy.Field()
    
    # Timestamps
    fecha_publicacion = scrapy.Field()
    fecha_recopilacion = scrapy.Field()
    fecha_procesamiento = scrapy.Field()
```

---

## 🚨 Sistema de Monitoreo

### Monitores Implementados

#### 1. **StructureChangeMonitor**
- **Propósito**: Detectar cambios en estructura HTML
- **Umbral**: >10% campos vacíos
- **Campos vigilados**: titulo, contenido_texto, url, medio

#### 2. **CriticalFieldsMonitor**
- **Propósito**: Verificar campos obligatorios
- **Umbrales específicos**:
  - titulo: máx 5% vacío
  - url: 0% (siempre requerido)
  - medio: 0%
  - fecha_recopilacion: 0%

#### 3. **ResponseTimeMonitor**
- **Propósito**: Detectar sitios lentos
- **Umbral**: >5000ms promedio
- **Métricas**: latencia promedio, varianza

#### 4. **HTTPErrorRateMonitor**
- **Propósito**: Detectar bloqueos o problemas
- **Umbral**: >10% respuestas con error
- **Códigos monitoreados**: 403, 429, 500-504

### Sistema de Alertas

#### Canales disponibles:

1. **Email (SMTP)**
```python
SendEmailAlert:
  - Servidor SMTP configurable
  - Soporte TLS
  - Múltiples destinatarios
  - Formato HTML/texto
```

2. **Webhook**
```python
SendWebhookAlert:
  - POST JSON a URL configurada
  - Headers personalizados
  - Payload estructurado
  - Timeout configurable
```

3. **Logs estructurados**
```python
LogStructuredAlert:
  - Formato JSON
  - Niveles: INFO, WARNING, ERROR
  - Integrable con ELK/Grafana
```

### Flujo de Monitoreo

```
Spider Termina
    │
    ▼
Spidermon Extension
    │
    ├─→ Ejecuta Monitores
    │     ├─→ StructureChangeMonitor
    │     ├─→ CriticalFieldsMonitor
    │     ├─→ ResponseTimeMonitor
    │     └─→ HTTPErrorRateMonitor
    │
    ├─→ ¿Errores detectados?
    │     │
    │     ├─ SÍ → Ejecutar Acciones
    │     │         ├─→ SendEmailAlert
    │     │         ├─→ SendWebhookAlert
    │     │         └─→ LogStructuredAlert
    │     │
    │     └─ NO → Log éxito
    │
    └─→ Guardar métricas
```

---

## 🔄 Flujo de Datos

### Ciclo de vida de una extracción:

1. **Inicio**
   - Usuario/Timer solicita ejecución via ScrapydWeb
   - ScrapydWeb envía petición a Scrapyd API

2. **Deployment**
   - Scrapyd verifica proyecto y versión
   - Carga spider desde eggs directory
   - Asigna recursos (proceso)

3. **Ejecución**
   - Spider inicia con configuración
   - Scrapy procesa URLs
   - Items pasan por pipelines

4. **Monitoreo**
   - Spidermon recolecta estadísticas
   - Valida items contra schema
   - Ejecuta monitores al finalizar

5. **Almacenamiento**
   - Items válidos → Supabase
   - Logs → Sistema de archivos
   - Métricas → SQLite (ScrapydWeb)

6. **Alertas**
   - Si hay errores → Notificaciones
   - Actualización dashboard
   - Registro en logs

### Diagrama de secuencia simplificado:

```
Usuario → ScrapydWeb → Scrapyd → Spider → Scrapy
                                    │
                                    ├─→ Pipelines → Supabase
                                    │
                                    └─→ Spidermon → Alertas
```

---

## 🔐 Consideraciones de Seguridad

1. **Autenticación**
   - ScrapydWeb: HTTP Basic Auth
   - Scrapyd: Sin auth por defecto (usar firewall)

2. **Red**
   - Servicios en red Docker aislada
   - Exposición mínima de puertos
   - Comunicación interna por nombres de servicio

3. **Datos sensibles**
   - Variables de entorno para credenciales
   - No logs de datos sensibles
   - Rotación de contraseñas

---

📖 **Siguiente**: [Sistema de Monitoreo y Alertas](MONITORING_ALERTS.md) - Detalles del sistema de vigilancia