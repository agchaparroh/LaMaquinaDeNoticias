# ⚠️ Manejo de Errores

# Sistema Integral de Manejo de Errores del `module_pipeline`

## 1. Errores por Fase de Procesamiento

### 1.1. Fase 1 (Triaje/Preprocesamiento)
- **Descarte incorrecto:** Artículos relevantes marcados como irrelevantes o viceversa
- **Errores de detección de idioma:** Identificación incorrecta del idioma del contenido
- **Traducción fallida:** Fallos en el proceso de traducción automática
- **Evaluación de relevancia:** Fallo en la evaluación de relevancia por parte del LLM

### 1.2. Fases 2/3/4 (Procesamiento LLM)
- **Errores de API de Groq:** Timeouts, rate limits, errores internos del servicio
- **Respuestas del LLM problemáticas:** Respuestas vacías, incompletas o en formato JSON inválido
- **Fallos de parsing:** Errores en la limpieza/parseo del JSON (`json_cleaner`)
- **Errores de validación Pydantic:** LLM no sigue la estructura esperada de datos
- **Extracción incompleta:** Información incorrecta o incompleta extraída por el LLM

### 1.3. Fase 4 (Normalización/Vinculación)
- **Errores de base de datos:** Fallos al consultar `cache_entidades` o RPCs de búsqueda
- **Identificación de entidades:** Falsos positivos/negativos en entidades existentes
- **Detección de duplicados:** Fallo en la identificación de posibles duplicados

### 1.4. Fase 4.5 (Evaluación ML)
- **Carga del modelo ML:** Errores en la carga del modelo de machine learning
- **Consulta de tendencias:** Fallo en la consulta a `tendencias_contexto_diario`
- **Características malformadas:** Datos de entrada fuera del formato esperado del modelo
- **Predicciones inválidas:** Valores de importancia fuera del rango esperado

### 1.5. Fase 5 (Persistencia)
- **Errores de RPC:** Fallos en la ejecución de funciones RPC de base de datos
- **Violación de constraints:** Restricciones de base de datos violadas
- **Timeouts de base de datos:** Operaciones que exceden el tiempo límite
- **Errores de transacción:** Fallos en la atomicidad de las operaciones

## 2. Errores Generales del Sistema

### 2.1. Problemas de Rendimiento
- **Cuello de botella:** Velocidad de procesamiento limitada por API de Groq y número de workers
- **Saturación de cola:** Avalancha de artículos que llena la cola de procesamiento
- **Consumo excesivo de API:** Alto consumo de tokens/créditos de la API de Groq

### 2.2. Errores de Sistema
- **Excepciones no controladas:** Errores inesperados en cualquier fase
- **Gestión de estado inconsistente:** Inconsistencias cuando un artículo falla a mitad del pipeline
- **Problemas de conectividad:** Fallos de red con servicios externos

## 3. Sistema de Registro de Errores

### 3.1. Tabla `articulos_error_persistente`

El sistema registra errores persistentes para facilitar el reintento o la intervención manual.

**Información registrada:**
- Detalles del error específico por fase
- Estado del procesamiento al momento del fallo
- Información para reintento o análisis posterior
- Timestamp del error
- Stack trace completo del error

### 3.2. Campos de Error en Modelos de Entrada

**Para artículos (`ArticuloInItem`):**
- `error_detalle`: Registra detalles del error durante el procesamiento

**Para fragmentos (`FragmentoProcesableItem`):**
- `error_detalle_fragmento`: Registra errores específicos del procesamiento del fragmento

## 4. Sistema de Logging

### 4.1. Configuración de Logging
**Biblioteca:** Loguru (`0.7.3`)

**Variables de entorno:**
- `LOG_LEVEL=INFO`: Nivel de logging del sistema
- `LOG_DIR=./logs`: Directorio de almacenamiento de logs
- `ENABLE_DETAILED_LOGGING=false`: Logging detallado para debugging

### 4.2. Tipos de Logs

**Logs de API:**
- **Requests:** Todas las solicitudes HTTP loggeadas con nivel INFO
- **Errores de procesamiento:** Loggeados con nivel ERROR
- **Formato consistente:** Estructura uniforme con el resto del sistema

**Logs de Procesamiento:**
- **Errores por fase:** Registro detallado de fallos en cada etapa del pipeline
- **Timeouts y servicios externos:** Fallos de conectividad y tiempo de respuesta
- **Validación de datos:** Errores en la validación de entrada y salida

### 4.3. Estructura de Logs
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "ERROR",
  "module": "module_pipeline",
  "fase": "fase_2",
  "articulo_id": "art_123",
  "error_type": "groq_api_timeout",
  "message": "Timeout en llamada a API de Groq",
  "details": {
    "timeout_seconds": 30,
    "retry_attempt": 2,
    "max_retries": 3
  }
}
```

## 5. Monitoreo de Errores

### 5.1. Sentry (Opcional)
**Variables de entorno:**
- `USE_SENTRY=false`: Activación del monitoreo con Sentry
- `SENTRY_DSN=https://your-sentry-dsn-here@sentry.io/project`: URL de configuración

**Características:**
- Tracking automático de excepciones
- Agrupación inteligente de errores similares
- Alertas en tiempo real
- Análisis de rendimiento

### 5.2. Notificaciones
**Variable de entorno:** `ENABLE_NOTIFICATIONS=false`

**Canales de notificación:**
- Email para errores críticos
- Webhooks para integración con sistemas de monitoreo
- Alertas de Slack/Discord para el equipo de desarrollo

## 6. Respuestas de Error en la API

### 6.1. Error de Validación (400 Bad Request)
```json
{
  "error": "validation_error",
  "mensaje": "Error en la validación del artículo",
  "detalles": [
    "Campo 'titular' es requerido",
    "Campo 'contenido_texto' es requerido"
  ],
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123"
}
```

### 6.2. Error Interno (500 Internal Server Error)
```json
{
  "error": "internal_error",
  "mensaje": "Error interno del pipeline",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123",
  "support_code": "ERR_PIPE_001"
}
```

### 6.3. Servicio No Disponible (503 Service Unavailable)
```json
{
  "error": "service_unavailable",
  "mensaje": "Pipeline temporalmente sobrecargado, reintente más tarde",
  "timestamp": "2024-01-15T10:30:00Z",
  "retry_after": 300,
  "request_id": "req_abc123"
}
```

## 7. Gestión de Estado de Procesamiento

### 7.1. Estados de Artículos
El `module_pipeline` actualiza el campo `estado_procesamiento` para reflejar el progreso:

**Estados de progreso:**
- `"procesando_fase1"`, `"procesando_fase2"`, `"procesando_fase3"`
- `"procesando_fase4"`, `"procesando_fase4.5"`, `"procesando_fase5"`
- `"completado"`

**Estados de error:**
- `"error_fase1"`, `"error_fase2"`, `"error_fase3"`
- `"error_fase4"`, `"error_fase4.5"`, `"error_fase5"`
- `"error_critico"`

### 7.2. Estados de Fragmentos
Para fragmentos, se utiliza `estado_procesamiento_fragmento` con estados similares:
- `"procesando_fase1_fragmento"` hasta `"procesando_fase5_fragmento"`
- `"completado_fragmento"`
- `"error_fragmento"`

## 8. Estrategias de Recuperación

### 8.1. Reintentos Automáticos

**Para llamadas a Groq API:**
- `MAX_RETRIES=3`: Número máximo de reintentos
- `MAX_WAIT_SECONDS=60`: Tiempo máximo de espera
- **Backoff exponencial:** Incremento progresivo del tiempo entre reintentos
- **Circuit breaker:** Suspensión temporal de llamadas tras fallos consecutivos

**Para operaciones de base de datos:**
- Reintentos automáticos para errores transitorios
- Verificación de conectividad antes de reintento
- Timeouts configurables por tipo de operación

### 8.2. Reintentos Manuales
- **Registro en `articulos_error_persistente`:** Permite reintento manual posterior
- **Análisis de errores:** Revisión para mejora de prompts y configuración
- **Intervención manual:** Para casos complejos que requieren ajuste humano

### 8.3. Estrategias de Degradación
- **Procesamiento parcial:** Guardar resultados parciales en caso de fallo
- **Modo de recuperación:** Continuar desde la última fase exitosa
- **Bypass temporal:** Omitir fases problemáticas con flagging apropiado

## 9. Configuración de Directorios y Logs

### 9.1. Estructura de Directorios
```
logs/
├── pipeline.log              # Log principal del pipeline
├── errors/
│   ├── fase_1_errors.log     # Errores específicos por fase
│   ├── fase_2_errors.log
│   └── ...
├── api/
│   ├── requests.log          # Logs de requests HTTP
│   └── responses.log         # Logs de responses HTTP
└── external/
    ├── groq_api.log          # Logs de interacción con Groq
    └── supabase.log          # Logs de base de datos
```

### 9.2. Rotación de Logs
- **Rotación diaria:** Archivos de log rotados cada 24 horas
- **Retención:** Mantener logs por 30 días por defecto
- **Compresión:** Logs antiguos comprimidos automáticamente
- **Limpieza automática:** Eliminación de logs más antiguos que el período de retención

## 10. Métricas de Error

### 10.1. Métricas por Fase
```json
{
  "error_metrics": {
    "fase_1": {
      "total_errors": 45,
      "error_rate": 0.02,
      "most_common_error": "language_detection_failed"
    },
    "fase_2": {
      "total_errors": 78,
      "error_rate": 0.04,
      "most_common_error": "groq_api_timeout"
    }
  }
}
```

### 10.2. Alertas Automáticas
- **Tasa de error elevada:** Alerta cuando la tasa supera umbrales configurados
- **Fallos consecutivos:** Notificación tras múltiples fallos seguidos
- **Recursos críticos:** Monitoreo de espacio en disco, memoria, etc.
- **Servicios externos:** Alertas por indisponibilidad de Groq o Supabase
