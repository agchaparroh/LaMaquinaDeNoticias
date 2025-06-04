# ⚙️ Control y Orquestación

# Procesamiento Asíncrono y Gestión de Cola

## 1. Frecuencia y Modo de Recepción

El procesamiento se activa bajo demanda cuando:
- El `module_connector` envía un artículo
- El `module_ingestion_engine` envía un fragmento para procesar

El procesamiento interno se gestiona mediante una cola asíncrona (`asyncio.Queue` en la implementación actual).

## 2. Interfaz de Comunicación

**Para artículos:** API HTTP (POST al endpoint `/procesar`).

**Para fragmentos:** Llamada a función asíncrona interna (podría evolucionar a cola de mensajes).

## 3. Variables de Entorno para Control

- `API_HOST`, `API_PORT`: Configuración del servidor FastAPI
- `WORKER_COUNT`, `QUEUE_MAX_SIZE`: Configuración del controlador asíncrono
- `DEBUG_MODE`: Flags de comportamiento del sistema

## 4. Gestión de Workers

El controlador (`controller.py`) gestiona la cola y los workers para el procesamiento asíncrono de artículos y fragmentos.

**Configuración recomendada:**
- **Workers concurrentes:** Configurable mediante `WORKER_COUNT` (default: 3)
- **Tamaño máximo de cola:** Configurable mediante `QUEUE_MAX_SIZE` (default: 100)
- **Cola asíncrona:** `asyncio.Queue`

## 5. Comportamiento del Sistema de Control

### 5.1. Aceptación Inmediata
Los endpoints deben:
- Validar la entrada de forma síncrona
- Enviar el elemento a una cola de procesamiento
- Responder inmediatamente con **202 Accepted**

### 5.2. Cola de Procesamiento
- Implementar una cola asíncrona (recomendado: `asyncio.Queue`)
- Configurar workers concurrentes para procesar elementos de la cola

### 5.3. Manejo de Sobrecarga
- Si la cola está llena, responder con **503 Service Unavailable**
- El cliente (module_connector) está configurado para reintentar automáticamente

## 6. Posibles Errores y Riesgos Relacionados con el Control

### 6.1. Errores Generales

- **Cuello de botella:** La velocidad de procesamiento depende de la API de Groq y del número de workers. Una avalancha de artículos podría llenar la cola.

- **Gestión de estado:** Inconsistencias si un artículo falla a mitad del pipeline.

### 6.2. Riesgos de Rendimiento

- **Saturación de la cola:** Cuando el volumen de entrada supera la capacidad de procesamiento
- **Dependencia de servicios externos:** Fallos o lentitud en la API de Groq pueden crear cuellos de botella
- **Gestión de memoria:** Acumulación de elementos en cola puede afectar el rendimiento del sistema

### 6.3. Estrategias de Mitigación

- **Monitoreo activo:** Seguimiento continuo del tamaño de cola y tiempo de procesamiento
- **Escalamiento dinámico:** Ajuste del número de workers según la carga
- **Circuit breakers:** Implementación de patrones de resistencia para servicios externos
- **Timeouts configurables:** Límites de tiempo para evitar bloqueos indefinidos
