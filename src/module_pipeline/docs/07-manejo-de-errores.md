# ⚠️ Manejo de Errores

# Sistema Robusto de Manejo de Errores del `module_pipeline`

## 📝 Resumen Ejecutivo

El sistema de manejo de errores del `module_pipeline` implementa:

- **Excepciones Personalizadas**: Jerarquía plana con `PipelineException` como base
- **Decoradores de Retry**: `@retry_groq_api` y `@retry_supabase_rpc` con configuración específica
- **Fallback Handlers**: Un handler específico por cada posible fallo en cada fase
- **Logging Estructurado**: Con Loguru, contexto enriquecido y support codes
- **Degradación Elegante**: El pipeline nunca falla completamente

### 🔗 Referencias Rápidas

- **Código de Implementación**: `/src/utils/error_handling.py`
- **Documentación de Excepciones**: `/docs/excepciones-personalizadas.md`
- **Configuración de Retry**: `/docs/retry_decorators_config.md`
- **Test de Verificación**: `/tests/test_retry_decorators_verify.py`

## 1. Principios de Diseño Obligatorios

El desarrollador DEBE implementar el `module_pipeline` siguiendo estos principios:

- **Regla del "Nunca Fallar Completamente"**: Si una fase falla, el pipeline debe continuar con datos por defecto
- **Regla de "Configuración Mínima"**: El sistema debe funcionar solo con GROQ_API_KEY, SUPABASE_URL y SUPABASE_KEY
- **Regla de "Un Artículo = Una Transacción"**: El fallo de un artículo no debe afectar el procesamiento de otros
- **Regla de "Logs Accionables"**: Cada error debe loggear suficiente información para ser debuggeado
- **Regla de "Degradación Visible"**: Cuando se usan fallbacks, debe quedar registrado claramente

## 2. Estrategia de Fallbacks por Fase

### Instrucciones Específicas por Fase:

**Fase 1 (Triaje):**
- Si Groq falla → Aceptar artículo automáticamente (no descartar)
  - Handler: `handle_groq_relevance_error_fase1()`
- Si traducción falla → Procesar en idioma original
  - Handler: `handle_groq_translation_fallback_fase1()`
- Si detección de idioma falla → Asumir español
- Si spaCy falla → Preprocesamiento degradado, aceptar artículo
  - Handler: `handle_spacy_load_error_fase1()`
- NUNCA descartar un artículo por fallo técnico

**Fase 2 (Elementos Básicos):**
- Si Groq falla → Crear un hecho básico usando el titular del artículo
  - Handler: `handle_groq_extraction_error_fase2()`
- Si extracción de entidades falla → Crear entidad genérica con el nombre del medio
- Si JSON es inválido → Un reintento, luego usar datos mínimos
  - Handler: `handle_json_parsing_error_fase2()`

**Fase 3 (Citas y Datos):**
- Si Groq falla → Continuar sin citas ni datos cuantitativos (no es error crítico)
  - Handler: `handle_groq_citas_error_fase3()`
- Si no se extraen citas → Continuar normalmente

**Fase 4 (Relaciones y Normalización):**
- Si búsqueda de entidades en BD falla → Crear todas las entidades como nuevas
  - Handler: `handle_normalization_error_fase4()`
- Si extracción de relaciones falla → Continuar sin relaciones
  - Handler: `handle_groq_relations_error_fase4()`

**Fase 4.5 (Importancia):**
- Si modelo ML no existe → Usar importancia por defecto (valor: 5)
  - Handler: `handle_importance_ml_error()`
- Si consulta a tendencias_contexto_diario falla → Usar importancia por defecto

**Fase 5 (Persistencia):**
- Si RPC completa falla → Guardar en tabla de errores para revisión manual
  - Handler: `handle_persistence_error_fase5()`
- NUNCA perder datos completamente

### Fallback Handlers Implementados

Todos los handlers están en `/src/utils/error_handling.py` y:
- Retornan estructuras de datos mínimas válidas
- Loggean el uso de fallback con contexto completo
- Incluyen metadata indicando que se usó fallback
- Preservan el flujo del pipeline

## 3. Configuración Robusta

### Variables de Entorno Obligatorias:

**Mínimo Absoluto (3 variables):**
- `GROQ_API_KEY` (sin default, requerida)
- `SUPABASE_URL` (sin default, requerida)  
- `SUPABASE_KEY` (sin default, requerida)

**Con Defaults Seguros:**
- `API_TIMEOUT=60` (generoso para evitar timeouts)
- `MAX_RETRIES=2` (máximo)
- `IMPORTANCE_DEFAULT=5` (valor neutro)
- `MODEL_ID=llama-3.1-8b-instant`
- `WORKER_COUNT=3`

### Carga de Recursos Opcional:

**Modelo ML de Importancia:**
- Si no existe → Usar importancia por defecto
- Si falla la carga → Loggear warning y continuar

**Prompts Externos:**
- Si fallan → Usar prompts embebidos en el código
- Nunca fallar por prompts faltantes

**spaCy (Opcional):**
- Si no está instalado → Continuar sin spaCy
- Solo loggear warning

## 4. Manejo de Errores de APIs

### Para Groq API:

**Reintentos con Decorador @retry_groq_api:**
- Máximo 2 reintentos con pausa de 5 segundos + jitter (0-1s)
- Timeout de 60 segundos
- Logging automático de intentos (WARNING) y éxitos (INFO)
- Conversión automática a GroqAPIError con support_code
- Después de fallos → Usar fallback inmediatamente

**JSON Malformado:**
- Usar `json_repair.loads()` antes de parsear
- Si falla → Un reintento
- Si falla segunda vez → Fallback

### Para Supabase:

**Reintentos con Decorador @retry_supabase_rpc:**
- Solo 1 reintento para errores de conexión (ConnectionError, TimeoutError)
- 0 reintentos para errores de validación (ValueError)
- Timeout de 30 segundos
- Diferenciación automática de tipos de error
- Conversión a SupabaseRPCError con contexto

## 5. Validación con Pydantic

### Validación Básica:

**Después de cada fase:**
- Validar estructura con modelos Pydantic simples
- Si `ValidationError` → Usar datos por defecto mínimos
- Loggear qué se reemplazó

**Manejo de Fechas:**
- Usar `python-dateutil` para parsing robusto
- Si falla → Usar fecha actual

## 6. Logging Simple con Loguru

### Configuración Básica:

**Setup:**
- Usar solo Loguru (no mixing)
- Un archivo de log simple: `pipeline.log`
- Rotación automática por tamaño (10MB)

**Niveles:**
- **INFO:** Inicio/fin de procesamiento, uso de fallbacks
- **WARNING:** Fallos que se resuelven con reintentos
- **ERROR:** Fallos que requieren fallbacks críticos

**Variables:**
- `LOG_LEVEL=INFO`
- `LOG_DIR=./logs`

## 7. Persistencia Simple

### Estrategia de 2 Niveles:

**Nivel 1:** Intentar RPC completa (`insertar_articulo_completo`)
**Nivel 2:** Si falla → Guardar en tabla `pipeline_errores` con:
- Timestamp
- Datos JSON completos
- Motivo del fallo

**No implementar:** Guardado tabla por tabla (demasiado complejo)

## 8. Verificaciones de Arranque

### Al Iniciar el Sistema:

1. **Verificar Supabase** → Si falla, no arrancar (crítico)
2. **Verificar Groq** → Si falla, loggear warning pero arrancar
3. **Cargar recursos opcionales** → Si fallan, continuar sin ellos

### Health Check Simple:

Endpoint `/health` debe reportar:
- Estado: "healthy" o "degraded"
- Conectividad con Supabase
- Número de workers activos
- Tamaño actual de la cola

## 9. Sistema de Registro de Errores

### 9.1. Tabla `articulos_error_persistente`

El sistema registra errores persistentes para facilitar el reintento o la intervención manual.

**Información registrada:**
- Detalles del error específico por fase
- Estado del procesamiento al momento del fallo
- Información para reintento o análisis posterior
- Timestamp del error
- Stack trace completo del error

### 9.2. Campos de Error en Modelos de Entrada

**Para artículos (`ArticuloInItem`):**
- `error_detalle`: Registra detalles del error durante el procesamiento

**Para fragmentos (`FragmentoProcesableItem`):**
- `error_detalle_fragmento`: Registra errores específicos del procesamiento del fragmento

## 9. Sistema de Logging y Observabilidad (Usar Loguru)

### 9.1. Configuración Obligatoria de Loguru:

**Setup Inicial:**
- Usar Loguru como único sistema de logging (no mixing con logging estándar)
- Configurar con contexto automático: `logger.bind()` para cada artículo
- Usar structured logging con campos consistentes
- Configurar rotación automática de archivos

### 9.2. Niveles de Log Requeridos:

**INFO (con logger.bind()):** 
- Inicio y fin de procesamiento: `logger.bind(articulo_id=id, medio=medio).info("Procesamiento iniciado")`
- Tiempo de procesamiento por fase con métricas
- Uso de fallbacks con contexto: `logger.bind(fase=2, razon="groq_timeout").info("Usando fallback")`

**WARNING:**
- Fallos de API que se resuelven con reintentos
- Uso de json-repair para reparar JSON
- Recursos opcionales no disponibles (modelo ML, spaCy)
- Circuit breakers activados

**ERROR:**
- Fallos que requieren fallbacks críticos
- Errores de persistencia con stack trace completo
- ValidationError de Pydantic no recuperables
- Pérdida de datos o procesamiento incompleto

### 9.3. Configuración de Archivos de Log:

- Usar `logger.add()` para configurar rotación por tamaño y tiempo
- Logs separados por nivel (info.log, error.log)
- Formato JSON para logs de producción
- Retención configurable via variable de entorno

**Variables de entorno:**
- `LOG_LEVEL=INFO`: Nivel de logging del sistema
- `LOG_DIR=./logs`: Directorio de almacenamiento de logs
- `ENABLE_DETAILED_LOGGING=false`: Logging detallado para debugging

### 9.4. Estructura de Logs (Implementado con format_error_for_logging)
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

### 9.5. Métricas Mínimas Requeridas:

- Artículos procesados total
- Artículos completados exitosamente
- Artículos completados con fallbacks
- Artículos fallidos completamente
- Tiempo promedio de procesamiento
- Errores por fase (contador)

## 10. Monitoreo de Errores

### 10.1. Sentry (Opcional)
**Variables de entorno:**
- `USE_SENTRY=false`: Activación del monitoreo con Sentry
- `SENTRY_DSN=https://your-sentry-dsn-here@sentry.io/project`: URL de configuración

**Características:**
- Tracking automático de excepciones
- Agrupación inteligente de errores similares
- Alertas en tiempo real
- Análisis de rendimiento

### 10.2. Notificaciones
**Variable de entorno:** `ENABLE_NOTIFICATIONS=false`

**Canales de notificación:**
- Email para errores críticos
- Webhooks para integración con sistemas de monitoreo
- Alertas de Slack/Discord para el equipo de desarrollo

## 11. Respuestas de Error en la API (Implementado con create_error_response)

### 11.1. Error de Validación (400 Bad Request)
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

### 11.2. Error Interno (500 Internal Server Error)
```json
{
  "error": "internal_error",
  "mensaje": "Error interno del pipeline",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123",
  "support_code": "ERR_PIPE_001"
}
```

### 11.3. Servicio No Disponible (503 Service Unavailable)
```json
{
  "error": "service_unavailable",
  "mensaje": "Pipeline temporalmente sobrecargado, reintente más tarde",
  "timestamp": "2024-01-15T10:30:00Z",
  "retry_after": 300,
  "request_id": "req_abc123"
}
```

## 12. Gestión de Estado de Procesamiento

### 12.1. Estados de Artículos
El `module_pipeline` actualiza el campo `estado_procesamiento` para reflejar el progreso:

**Estados de progreso:**
- `"procesando_fase1"`, `"procesando_fase2"`, `"procesando_fase3"`
- `"procesando_fase4"`, `"procesando_fase4.5"`, `"procesando_fase5"`
- `"completado"`

**Estados de error:**
- `"error_fase1"`, `"error_fase2"`, `"error_fase3"`
- `"error_fase4"`, `"error_fase4.5"`, `"error_fase5"`
- `"error_critico"`

### 12.2. Estados de Fragmentos
Para fragmentos, se utiliza `estado_procesamiento_fragmento` con estados similares:
- `"procesando_fase1_fragmento"` hasta `"procesando_fase5_fragmento"`
- `"completado_fragmento"`
- `"error_fragmento"`

## 13. Comportamiento de Arranque del Sistema

### Verificaciones al Inicio:

1. **Verificar conectividad a Groq** → Si falla, loggear warning pero continuar
2. **Verificar conectividad a Supabase** → Si falla, fallar el arranque (crítico)
3. **Cargar modelo ML si existe** → Si falla, loggear warning y continuar sin modelo
4. **Cargar prompts externos** → Si fallan, usar prompts embebidos
5. **Verificar spaCy si está habilitado** → Si falla, continuar sin spaCy

### Health Check:

El endpoint `/health` debe reportar:
- Estado de conectividad con servicios externos
- Disponibilidad de recursos opcionales (modelo ML, spaCy)
- Número de workers activos
- Tamaño actual de la cola

## 14. Testing de Robustez Requerido

### Tests Obligatorios:

**Test de Fallos de Groq:**
- Simular timeout de Groq → Verificar que usa fallbacks
- Simular JSON malformado → Verificar reintento y fallback
- Simular API no disponible → Verificar fallback inmediato

**Test de Fallos de BD:**
- Simular fallo de RPC → Verificar inserción básica
- Simular fallo de inserción básica → Verificar guardado en tabla errores
- Simular desconexión temporal → Verificar recuperación

**Test de Recursos Faltantes:**
- Arrancar sin modelo ML → Verificar uso de importancia por defecto
- Arrancar sin prompts externos → Verificar uso de prompts embebidos
- Arrancar sin spaCy → Verificar funcionamiento sin filtro adicional

**Test de Carga:**
- Procesar 100 artículos simultáneos → Verificar que todos se procesan
- Saturar cola → Verificar respuesta 503 adecuada
- Fallos intermitentes → Verificar que no afectan otros artículos

## 15. Criterios de Aceptación

El sistema se considera robusto cuando:

1. **Funciona con configuración mínima** (solo 3 variables de entorno)
2. **Nunca pierde artículos** (siempre persiste algo, aunque sea mínimo)
3. **Se recupera automáticamente** de fallos temporales
4. **Degrada elegantemente** cuando fallan componentes opcionales
5. **Proporciona logs útiles** para debugging
6. **Mantiene métricas claras** sobre su funcionamiento
7. **Responde a health checks** indicando su estado real

El desarrollador debe implementar estas especificaciones de manera que el sistema sea **confiable en producción** sin requerir intervención manual frecuente.

## 16. Excepciones Personalizadas Implementadas

### 16.1. Jerarquía de Excepciones

El sistema implementa una jerarquía plana de excepciones personalizadas:

- **PipelineException**: Excepción base con soporte para phases, support_codes y contexto
- **ValidationError**: Errores de validación de datos de entrada
- **GroqAPIError**: Errores específicos de la API de Groq
- **SupabaseRPCError**: Errores de llamadas RPC a Supabase
- **ProcessingError**: Errores durante el procesamiento
- **ServiceUnavailableError**: Servicio temporalmente no disponible
- **FallbackExecuted**: Señal de uso de fallback (no es error)

### 16.2. Decoradores de Retry Implementados

**@retry_groq_api**:
- Máximo 2 reintentos (3 intentos totales)
- Espera de 5 segundos + jitter aleatorio (0-1s)
- Convierte RetryError a GroqAPIError automáticamente
- Logging integrado con before_log y after_log

**@retry_supabase_rpc**:
- 1 reintento para errores de conexión
- 0 reintentos para errores de validación
- Espera de 2 segundos fija
- Diferencia automáticamente tipos de error

**@no_retry**:
- Decorador de documentación para operaciones no idempotentes

### 16.3. Documentación Adicional

Para información detallada sobre excepciones personalizadas, decoradores y guía de troubleshooting, consultar:
- `/docs/excepciones-personalizadas.md`: Documentación completa de excepciones
- `/docs/retry_decorators_config.md`: Configuración de decoradores de retry
- `/tests/test_retry_decorators_verify.py`: Script de verificación

## 17. Resumen de Implementación

### Componentes Clave Implementados:

1. **Sistema de Excepciones**:
   - 7 excepciones personalizadas principales
   - 5 excepciones de logging de fallback
   - Support codes automáticos para debugging

2. **Decoradores de Retry**:
   - `@retry_groq_api`: 2 reintentos, 5s + jitter
   - `@retry_supabase_rpc`: 1 reintento conexión, 0 validación
   - Logging automático integrado

3. **Fallback Handlers**:
   - 10 handlers específicos por fase/error
   - Retornan datos mínimos válidos
   - Preservan el flujo del pipeline

4. **Utilidades**:
   - `create_error_response()`: Respuestas API consistentes
   - `format_error_for_logging()`: Logs estructurados
   - `extract_validation_errors()`: Errores Pydantic legibles

### Próximos Pasos:

1. Monitorear métricas de errores en producción
2. Ajustar parámetros de retry según comportamiento real
3. Revisar y optimizar fallbacks basado en uso
4. Implementar alertas para patrones de error recurrentes

## 18. Estrategias de Recuperación (Legacy)

### 17.1. Reintentos Automáticos

**Para llamadas a Groq API:**
- `MAX_RETRIES=2`: Núm
