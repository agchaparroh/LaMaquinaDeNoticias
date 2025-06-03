# Especificación de la API REST del `module_pipeline`

## 1. Información General

El `module_pipeline` debe exponer una API REST usando **FastAPI** que permita recibir y procesar artículos de noticias y fragmentos de documentos.

**Configuración del servidor:**
- **Host:** `0.0.0.0` (configurable via `API_HOST`)
- **Puerto:** `8000` (configurable via `API_PORT`) 
- **Framework:** FastAPI
- **Servidor ASGI:** Uvicorn

## 2. Endpoints Requeridos

### 2.1. POST `/procesar` - Procesamiento de Artículos

**Propósito:** Recibe un artículo completo para procesamiento a través del pipeline completo (6 fases).

**Entrada:**
- **Content-Type:** `application/json`
- **Estructura del payload:**

```json
{
  "articulo": {
    // Estructura completa de ArticuloInItem según models.py del module_connector
    "url": "string (opcional)",
    "storage_path": "string (opcional)",
    "fuente": "string (opcional)",
    "medio": "string (requerido)",
    "medio_url_principal": "string (opcional)",
    "pais_publicacion": "string (requerido)",
    "tipo_medio": "string (requerido)",
    "titular": "string (requerido)",
    "fecha_publicacion": "string ISO (requerido, YYYY-MM-DDTHH:MM:SSZ)",
    "autor": "string (opcional)",
    "idioma": "string (opcional)",
    "seccion": "string (opcional)",
    "etiquetas_fuente": ["string (opcional)"],
    "es_opinion": "boolean (opcional, default: false)",
    "es_oficial": "boolean (opcional, default: false)",
    "resumen": "string (opcional, será sobrescrito por el pipeline)",
    "categorias_asignadas": ["string (opcional, será sobrescrito)"],
    "puntuacion_relevancia": "float (opcional, será sobrescrito)",
    "fecha_recopilacion": "string ISO (opcional)",
    "fecha_procesamiento": "string ISO (opcional, será establecido por el pipeline)",
    "estado_procesamiento": "string (opcional, será actualizado por el pipeline)",
    "error_detalle": "string (opcional)",
    "contenido_texto": "string (requerido)",
    "contenido_html": "string (opcional)",
    "metadata": "object (opcional)"
  }
}
```

**Respuestas:**

- **202 Accepted:** Artículo aceptado y enviado a procesamiento asíncrono
```json
{
  "estado": "aceptado",
  "mensaje": "Artículo enviado a procesamiento",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

- **400 Bad Request:** Error de validación del artículo
```json
{
  "error": "validation_error",
  "mensaje": "Error en la validación del artículo",
  "detalles": ["Campo 'titular' es requerido", "Campo 'contenido_texto' es requerido"],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

- **500 Internal Server Error:** Error interno del pipeline
```json
{
  "error": "internal_error",
  "mensaje": "Error interno del pipeline",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

- **503 Service Unavailable:** Pipeline sobrecargado (cola llena)
```json
{
  "error": "service_unavailable",
  "mensaje": "Pipeline temporalmente sobrecargado, reintente más tarde",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2.2. POST `/procesar_fragmento` - Procesamiento de Fragmentos

**Propósito:** Recibe un fragmento de documento extenso para procesamiento.

**Entrada:**
- **Content-Type:** `application/json`
- **Estructura del payload:**

```json
{
  "fragmento": {
    // Estructura de FragmentoProcesableItem según la documentación técnica
    "documento_id": "string (requerido)",
    "fragmento_id": "string (requerido)",
    "texto_fragmento": "string (requerido)",
    "numero_fragmento": "integer (requerido)",
    "total_fragmentos": "integer (requerido)",
    "offset_inicio_fragmento": "integer (opcional)",
    "offset_fin_fragmento": "integer (opcional)",
    "titulo_documento_original": "string (opcional)",
    "tipo_documento_original": "string (opcional)",
    "fuente_documento_original": "string (opcional)",
    "autor_documento_original": "string (opcional)",
    "fecha_publicacion_documento_original": "string ISO (opcional)",
    "idioma_documento_original": "string (opcional)",
    "storage_path_documento_original": "string (opcional)",
    "url_documento_original": "string (opcional)",
    "metadata_documento_original": "object (opcional)",
    "fecha_ingesta_fragmento": "string ISO (requerido)",
    "estado_procesamiento_fragmento": "string (default: 'pendiente_pipeline')",
    "error_detalle_fragmento": "string (opcional)"
  }
}
```

**Respuestas:** Mismo formato que `/procesar`

### 2.3. GET `/health` - Health Check

**Propósito:** Verificar el estado del pipeline.

**Respuesta:**
- **200 OK:**
```json
{
  "estado": "healthy",
  "version": "1.0.0",
  "workers_activos": 3,
  "cola_pendiente": 15,
  "cola_maxima": 100,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2.4. GET `/metrics` - Métricas del Sistema

**Propósito:** Obtener métricas operacionales del pipeline.

**Respuesta:**
- **200 OK:**
```json
{
  "articulos_procesados_total": 1523,
  "fragmentos_procesados_total": 756,
  "articulos_exitosos_total": 1445,
  "articulos_fallidos_total": 78,
  "fase_1_exitosos": 1523,
  "fase_2_exitosos": 1485,
  "fase_3_exitosos": 1465,
  "fase_4_exitosos": 1450,
  "fase_5_exitosos": 1445,
  "tiempo_promedio_procesamiento": 23.4,
  "workers_activos": 3,
  "cola_actual": 12,
  "uptime_segundos": 86400,
  "ultima_actualizacion": "2024-01-15T10:30:00Z"
}
```

## 3. Comportamiento Asíncrono

El pipeline debe implementar **procesamiento asíncrono** con las siguientes características:

1. **Aceptación inmediata:** Los endpoints `/procesar` y `/procesar_fragmento` deben:
   - Validar la entrada de forma síncrona
   - Enviar el elemento a una cola de procesamiento
   - Responder inmediatamente con **202 Accepted**

2. **Cola de procesamiento:** 
   - Implementar una cola asíncrona (recomendado: `asyncio.Queue`)
   - Configurar workers concurrentes para procesar elementos de la cola
   - Número de workers configurable via `WORKER_COUNT` (default: 3)
   - Tamaño máximo de cola configurable via `QUEUE_MAX_SIZE` (default: 100)

3. **Manejo de sobrecarga:**
   - Si la cola está llena, responder con **503 Service Unavailable**
   - El cliente (module_connector) está configurado para reintentar automáticamente

## 4. Variables de Entorno Requeridas

El servidor debe leer estas variables de entorno (con sus valores por defecto):

```bash
# === CONFIGURACIÓN DEL SERVIDOR ===
API_HOST=0.0.0.0
API_PORT=8000
DEBUG_MODE=false

# === CONFIGURACIÓN DEL PROCESAMIENTO ===
WORKER_COUNT=3
QUEUE_MAX_SIZE=100

# === OTRAS VARIABLES REQUERIDAS ===
# (Ver documentación técnica para lista completa de variables de Groq, Supabase, etc.)
```

## 5. Configuración con Uvicorn

El servidor debe iniciarse con:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=DEBUG_MODE,
        access_log=True
    )
```

## 6. Logging y Monitoreo

- **Todas las requests** deben loggearse con nivel INFO
- **Errores de procesamiento** deben loggearse con nivel ERROR
- **Métricas de rendimiento** deben registrarse para el endpoint `/metrics`
- **Formato de logs** debe ser consistente con el resto del sistema (usar Loguru)

## 7. Validación de Entrada

- Usar **Pydantic** para validar los modelos de entrada
- **Campos requeridos** deben validarse estrictamente
- **Errores de validación** deben retornar 400 con detalles específicos del error
- **Contenido de texto** debe tener límites mínimos y máximos (configurables via `MIN_CONTENT_LENGTH`, `MAX_CONTENT_LENGTH`)

## 8. Integración con el module_connector

El `module_connector` está configurado para:
- **URL base:** `http://localhost:8001` (configurable via `PIPELINE_API_URL`)
- **Endpoint usado:** `POST /procesar`
- **Reintentos:** Máximo 3 intentos con backoff exponencial
- **Timeout:** 30 segundos por request
- **Manejo de respuestas:**
  - 202: Éxito
  - 400: No reintenta (error permanente)
  - 500/503: Reintenta automáticamente

Esta especificación asegura la compatibilidad completa con el `module_connector` existente y define claramente todos los endpoints que debe implementar el desarrollador.
