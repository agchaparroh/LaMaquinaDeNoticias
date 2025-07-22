# 📋 Especificación Técnica Minimalista para PRP

> **Propósito**: Template esencial con SOLO la información técnica necesaria para generar un PRP preciso.
  *Anotación*: Un PRP (Product Requirements Prompt) es como ese "plan de construcción" pero para software.
>**Precauciones**: Evita alucinaciones. Rellena **únicamente lo que conozcas** con certeza.

---

## 1. ¿Qué vamos a construir?

```markdown
### Nombre
module_orchestration + Scripts de Monitorización Base (Fase 1)

### Descripción funcional
Sistema nervioso central para automatización y monitorización de tareas de fondo usando Prefect. Define, programa, ejecuta y observa procesos que no son directamente iniciados por el usuario. Incluye scripts para monitorización de salud del sistema, reintento de procesos fallidos, y generación de reportes diarios. No contiene lógica de negocio en sí mismo, sino que orquesta la ejecución de la lógica contenida en module_maintenance_scripts.

### Problema técnico que resuelve
Garantizar que las tareas de mantenimiento, análisis periódicos, chequeos de salud y reintentos se ejecuten de manera fiable, ordenada, en el momento adecuado y con visibilidad completa sobre su estado y resultados.
```

---

## 2. Funcionalidades

```markdown
### Qué SÍ incluye
1. **module_orchestration**: Definición de flujos (@flow) y tareas (@task) de Prefect que orquestan scripts de mantenimiento
2. **health_checker.py**: Monitorización del estado general de componentes del sistema
3. **error_retry_job.py**: Gestión del reintento de procesamiento para artículos/fragmentos fallidos
4. **daily_snapshot.py**: Creación de resumen diario del estado y actividad del sistema
5. **Configuración Prefect**: Agente de Prefect, programación con CronSchedule/IntervalSchedule, comunicación con API Prefect Cloud/Server

### Qué NO incluye
- Generación de embeddings (Fase 2)
- Gestión de duplicados de hechos (Fase 2)
- Normalización de entidades (Fase 2)
- Constructor de contexto de tendencias (Fase 3)
- Entrenamiento de modelos ML (Fase 4)
- Vinculación con Wikidata (Fase 5)
```

---

## 3. Casos de uso técnicos

```markdown
### Caso 1: Monitorización de Salud del Sistema
Input: Configuración de endpoints y umbrales en variables de entorno
Proceso: health_checker.py verifica estado de contenedores Docker, endpoints API, uso de disco, conexión a BD
Output: Actualización de system_status y creación de alertas en alert_inbox si se detectan problemas o se superan umbrales
Validación: Estados actualizados en system_status, alertas creadas cuando corresponde

### Caso 2: Reintento de Artículos Fallidos  
Input: Registros en articulos_error_persistente listos para reintento
Proceso: error_retry_job.py obtiene datos originales y los reenvía a la API del module_pipeline
Output: Actualización del estado del registro de error (resuelto, intervención requerida, o nuevo reintento)
Validación: Artículos fallidos son procesados o marcados apropiadamente

### Caso 3: Snapshot Diario del Sistema
Input: Ejecución programada diaria
Proceso: daily_snapshot.py recopila estadísticas de system_status, alert_inbox, y conteos de tablas principales
Output: Creación/actualización de registro en system_status_daily_snapshot
Validación: Registro diario creado con estadísticas del sistema
```

---

## 4. Arquitectura y contexto técnico

```markdown
### Stack actual
- Orquestación: Prefect Server Local (Python)
- Scripts: Python con asyncio, supabase-py, asyncpg, loguru, requests, httpx, argparse
- Database: Supabase (PostgreSQL)
- Infra: Docker containers independientes
- Comunicación: APIs REST/HTTP entre módulos

### Arquitectura de Contenedores (DECISIÓN: DOS CONTENEDORES)
**module_orchestration:**
- Prefect Server Local + Prefect Agent
- Definiciones de flows (@flow) y tasks (@task)
- Programación (CronSchedule/IntervalSchedule)
- Persistencia metadata Prefect en volumen Docker
- Deploy automático código-driven (prefect deploy)

**module_maintenance_scripts:**
- Scripts Python individuales (health_checker.py, error_retry_job.py, daily_snapshot.py)
- Lógica de negocio de mantenimiento
- Configuración distribuida por script
- Bibliotecas específicas (ML/embedding en futuras fases)

### Integraciones necesarias
| Sistema | Tipo | Para qué |
|---------|------|----------|
| Prefect Server Local | API Interna | Definición y ejecución de flujos |
| Supabase/PostgreSQL | Conexión directa | Lectura/escritura de datos |
| module_pipeline | HTTP POST | Reenvío de artículos fallidos |
| Contenedores Docker | API/Commands | Verificación de estado |

### Archivos/módulos que se modificarán
- src/module_orchestration/ (nuevo directorio - flows y configuración Prefect)
- src/module_maintenance_scripts/ (nuevo directorio - lógica de scripts)
- docker-compose.yml (INTEGRADO - añadir 2 nuevos servicios)
- Variables de entorno del sistema (.env compartido)

### Restricciones técnicas importantes
- Debe mantener compatibilidad con MVP existente
- Arquitectura dos contenedores: orchestration (ligero) + scripts (evolutivo)
- Integración en docker-compose.yml existente del MVP
- Red Docker adaptada a realidad existente en implementación actual
- Acceso completo de lectura/escritura a la Base de Datos
- Acceso de red a API del Pipeline y servicios monitorizados
```

---

## 5. Requisitos técnicos

```markdown
### Performance
- Según documentación: No se especifican métricas numéricas específicas
- health_checker.py debe ejecutarse frecuentemente (cada 15-30 minutos según documentación)
- error_retry_job.py debe ejecutarse frecuentemente (cada 5-10 minutos según documentación)

### Escalabilidad
- Según documentación: No se especifican números específicos de usuarios o volumen

### Seguridad
- Autenticación: Variables de entorno para configuración (sin API keys externas - Prefect Server Local)
- Autorización: Acceso a Base de Datos vía SUPABASE_URL, SUPABASE_KEY
- Datos sensibles: Gestión apropiada de credenciales en variables de entorno (.env compartido)
- Persistencia: Volumen Docker dedicado para metadata Prefect (separado de datos de negocio)
```

---

## 6. Criterios de aceptación técnicos

```markdown
### Tests requeridos
- Según documentación: No se especifican métricas de coverage específicas
- Verificación de funcionamiento de scripts individuales
- Validación de flujos Prefect

### Validaciones
- health_checker.py detecta problemas y actualiza system_status
- error_retry_job.py procesa artículos fallidos exitosamente  
- daily_snapshot.py genera resúmenes diarios
- Prefect ejecuta flujos según programación definida
- Visibilidad completa de estados y resultados en UI Prefect

### Definition of Done
- Flujos Prefect definidos con decoradores @flow/@task
- Agente Prefect configurado y en ejecución
- Scripts ejecutándose según programación:
  - health_checker: cada 15-30 minutos
  - error_retry_job: cada 5-10 minutos  
  - daily_snapshot: diario 06:00 AM
- Logging y monitorización funcional
```

---

## 7. Decisiones de Integración

```markdown
### Estructura de directorios definitiva
src/
├── module_orchestration/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── README.md
│   ├── src/
│   │   ├── __init__.py
│   │   ├── flows/
│   │   │   ├── __init__.py
│   │   │   ├── health_monitoring_flow.py
│   │   │   ├── error_retry_flow.py
│   │   │   └── daily_snapshot_flow.py
│   │   └── config.py
│   └── prefect.yaml
│
└── module_maintenance_scripts/
    ├── Dockerfile
    ├── requirements.txt
    ├── README.md
    └── src/
        ├── __init__.py
        ├── scripts/
        │   ├── health_checker.py
        │   ├── error_retry_job.py
        │   └── daily_snapshot.py
        └── utils/
            ├── __init__.py
            ├── docker_utils.py
            └── supabase_client.py

### Configuración Prefect definitiva
- Base de datos: Por decidir entre SQLite local o PostgreSQL en Supabase
- Puerto UI: 4200
- Almacenamiento: /opt/prefect/data y /opt/prefect/logs

### Comunicación entre contenedores
module_orchestration ejecuta scripts en module_maintenance_scripts usando Docker SDK Python:
- docker.from_env().containers.get('lamacquina_maintenance_scripts')
- container.exec_run(['python', '/app/src/scripts/health_checker.py'])

### Variables de entorno adicionales
# Nuevas variables necesarias
PREFECT_SERVER_API_HOST=0.0.0.0
PREFECT_SERVER_API_PORT=4200
PREFECT_UI_PORT=4200
MAINTENANCE_SCRIPTS_CONTAINER=lamacquina_maintenance_scripts
HEALTH_CHECK_INTERVAL_MINUTES=15
ERROR_RETRY_INTERVAL_MINUTES=5
DAILY_SNAPSHOT_HOUR=6

### Integración en docker-compose.yml
module_orchestration:
  build:
    context: ./src/module_orchestration
    dockerfile: Dockerfile
  container_name: lamacquina_orchestration
  volumes:
    - prefect_data:/opt/prefect/data
    - prefect_logs:/opt/prefect/logs
    - /var/run/docker.sock:/var/run/docker.sock:ro
  ports:
    - "4200:4200"
  env_file:
    - .env
  environment:
    - PREFECT_SERVER_API_HOST=0.0.0.0
    - PREFECT_SERVER_API_PORT=4200
    - PREFECT_UI_PORT=4200
  networks:
    - lamacquina_network
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:4200/api/health"]
    interval: 30s
    timeout: 10s
    retries: 3

module_maintenance_scripts:
  build:
    context: ./src/module_maintenance_scripts
    dockerfile: Dockerfile
  container_name: lamacquina_maintenance_scripts
  volumes:
    - ./src/module_maintenance_scripts:/app
  env_file:
    - .env
  networks:
    - lamacquina_network
  restart: unless-stopped
  depends_on:
    - module_pipeline
    - module_orchestration

### Política de reintentos
RETRY_POLICY = {
    "max_retries": 3,
    "retry_delay_seconds": 60,
    "exponential_backoff": True,
    "max_retry_delay": 300
}

ERROR_STATES = {
    "network_error": {"retryable": True, "alert": False},
    "database_error": {"retryable": True, "alert": True},
    "api_error": {"retryable": True, "alert": False},
    "logic_error": {"retryable": False, "alert": True}
}

### Tablas de BD existentes utilizadas
- system_status: Estado general del sistema
- alert_inbox: Alertas generadas
- articulos_error_persistente: Artículos con errores
- system_status_daily_snapshot: Snapshots diarios

### Integración con servicios existentes
- Networking: Red lamacquina_network
- Logging: Formato loguru (consistente con otros módulos)
- Healthchecks: Patrón curl (consistente)
- Naming: Prefijo lamacquina_ para contenedores
```

---

## 8. Información adicional relevante

```markdown
### Ejemplos de input/output
Según documentación: Los scripts acceden a datos cuando son ejecutados por el orquestador según programación definida. Outputs incluyen actualizaciones en Base de Datos, logs de ejecución, métricas actualizadas en JSONB en system_status.

### Errores a manejar
- Errores de Base de Datos (conexión, timeouts)
- Errores de Orquestación por Prefect (fallos en ejecución de flujos, problemas de concurrencia)
- Fallos en Dependencias Externas (API del Pipeline no disponible, servicios monitorizados no responden)
- Errores de Lógica en los algoritmos de los scripts

### Notas técnicas
- **Arquitectura decidida**: DOS contenedores independientes con responsabilidades separadas
- **Variables de entorno**: Sin PREFECT_API_URL/PREFECT_API_KEY (Server Local), mantener SUPABASE_URL, SUPABASE_KEY, LOG_LEVEL
- **PIPELINE_API_URL**: Requerida para error_retry_job.py
- **Persistencia Prefect**: Volumen Docker en module_orchestration (/opt/prefect/data, /opt/prefect/logs)
- **Deploy strategy**: Código-driven con `prefect deploy` automático
- **Configuración**: Distribuida por script, cada script gestiona su propia config
- **Integración**: Añadir servicios al docker-compose.yml existente del MVP
- **Networking**: Adaptado a la realidad existente en implementación actual
- **Permisos**: Sistema de archivos para logs, acceso Docker API para health_checker
- **Escalabilidad**: module_orchestration ligero y estable, module_maintenance_scripts evolutivo
```

---

## ✅ Checklist pre-PRP

**¿El documento describe claramente?**
- [x] QUÉ debe hacer el sistema (orquestación + 3 scripts específicos)
- [x] Casos de uso con inputs/outputs según documentación
- [x] Stack técnico y restricciones mencionados en documentación
- [x] Criterios de validación basados en documentación
- [x] Archivos/módulos mencionados en documentación

**¿El documento EVITA?**
- [x] Detalles de implementación no especificados
- [x] Métricas numéricas no mencionadas en documentación
- [x] Información no presente en documentación fuente
- [x] Timelines y presupuestos
- [x] Historias de usuario narrativas

---

**CERTIFICACIÓN**: ✅ Este documento contiene ÚNICAMENTE información extraída directamente de la documentación compartida, sin añadir especificaciones numéricas, ejemplos específicos o detalles que no estuvieran explícitamente mencionados en los documentos fuente.

*Template Minimalista v2.0 - Solo información técnica verificada en documentación*