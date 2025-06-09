# 🔥 Excepciones Personalizadas del Module Pipeline

Este documento describe todas las excepciones personalizadas implementadas en el sistema de manejo de errores del `module_pipeline`.

## 📋 Tabla de Contenidos

1. [Jerarquía de Excepciones](#jerarquía-de-excepciones)
2. [Excepciones Base](#excepciones-base)
3. [Excepciones Específicas](#excepciones-específicas)
4. [Excepciones de Fallback](#excepciones-de-fallback)
5. [Uso de Excepciones](#uso-de-excepciones)
6. [Decoradores de Retry](#decoradores-de-retry)
7. [Guía de Troubleshooting](#guía-de-troubleshooting)

## 🏗️ Jerarquía de Excepciones

```
Exception
└── PipelineException (base)
    ├── ValidationError
    ├── GroqAPIError
    ├── SupabaseRPCError
    ├── ProcessingError
    ├── ServiceUnavailableError
    ├── FallbackExecuted
    └── Excepciones de Logging de Fallback
        ├── SpaCyModelLoadFallbackLog
        ├── GroqRelevanceFallbackLog
        ├── GroqTranslationFallbackLogEvent
        ├── GroqExtractionFallbackLog
        └── NormalizationFallbackLog
```

## 🎯 Excepciones Base

### PipelineException

Excepción base para todas las excepciones del pipeline. Implementa una jerarquía plana según el principio de simplicidad.

```python
class PipelineException(Exception):
    def __init__(
        self,
        message: str,
        error_type: ErrorType = ErrorType.INTERNAL_ERROR,
        phase: ErrorPhase = ErrorPhase.GENERAL,
        details: Optional[Dict[str, Any]] = None,
        article_id: Optional[str] = None,
        support_code: Optional[str] = None
    )
```

**Atributos:**
- `message`: Mensaje descriptivo del error
- `error_type`: Tipo de error (enum ErrorType)
- `phase`: Fase del pipeline donde ocurrió
- `details`: Información adicional estructurada
- `article_id`: ID del artículo en procesamiento
- `support_code`: Código único para debugging
- `timestamp`: Momento del error (UTC)

**Métodos:**
- `to_dict()`: Convierte la excepción a diccionario para logging/respuesta
- `_generate_support_code()`: Genera código único de soporte

## 🚨 Excepciones Específicas

### ValidationError

Error de validación de datos de entrada. Usado cuando los datos no cumplen con los esquemas Pydantic.

```python
ValidationError(
    message="Campo requerido faltante",
    validation_errors=[
        {"field": "titular", "error": "Required field missing"}
    ],
    phase=ErrorPhase.FASE_1_TRIAJE,
    article_id="art_123"
)
```

**Uso típico:**
- Validación de entrada de API
- Validación de esquemas Pydantic
- Datos mal formateados

### GroqAPIError

Error específico de la API de Groq. Incluye información sobre reintentos y timeouts.

```python
GroqAPIError(
    message="Timeout en llamada a Groq",
    phase=ErrorPhase.FASE_2_EXTRACCION,
    retry_count=2,
    timeout_seconds=60,
    status_code=503,
    article_id="art_123"
)
```

**Detalles automáticos:**
- `max_retries`: 2 (según documentación)
- `api_provider`: "groq"
- `timeout_seconds`: 60 (por defecto)

### SupabaseRPCError

Error específico de llamadas RPC a Supabase. Diferencia entre errores de conexión y validación.

```python
SupabaseRPCError(
    message="Error de conexión con Supabase",
    rpc_name="insertar_articulo_completo",
    phase=ErrorPhase.FASE_5_PERSISTENCIA,
    is_connection_error=True,
    retry_count=1,
    article_id="art_123"
)
```

**Comportamiento:**
- Errores de conexión: `max_retries` = 1
- Errores de validación: `max_retries` = 0

### ProcessingError

Error durante el procesamiento de datos en cualquier fase.

```python
ProcessingError(
    message="Error al procesar entidades",
    phase=ErrorPhase.FASE_4_NORMALIZACION,
    processing_step="entity_extraction",
    fallback_used=True,
    article_id="art_123"
)
```

### ServiceUnavailableError

Error cuando el servicio está temporalmente no disponible.

```python
ServiceUnavailableError(
    message="Pipeline temporalmente sobrecargado",
    retry_after=300,
    queue_size=150,
    workers_active=3
)
```

## 🔄 Excepciones de Fallback

### FallbackExecuted

No es un error real, sino una señal de que se usó un fallback. Se loggea como INFO.

```python
FallbackExecuted(
    message="Usando fallback por fallo en Groq",
    phase=ErrorPhase.FASE_2_EXTRACCION,
    fallback_reason="groq_timeout",
    fallback_action="usar_titulo_como_hecho",
    article_id="art_123"
)
```

### Excepciones de Logging de Fallback

Estas excepciones se usan para logging estructurado cuando se ejecutan fallbacks:

- **SpaCyModelLoadFallbackLog**: Fallo al cargar modelo spaCy
- **GroqRelevanceFallbackLog**: Fallo en evaluación de relevancia
- **GroqTranslationFallbackLogEvent**: Fallo en traducción
- **GroqExtractionFallbackLog**: Fallo en extracción
- **NormalizationFallbackLog**: Fallo en normalización

## 💻 Uso de Excepciones

### Ejemplo 1: Manejo en Servicio

```python
from utils.error_handling import GroqAPIError, ErrorPhase

class GroqService:
    @retry_groq_api(max_attempts=2)
    def send_prompt(self, prompt: str):
        try:
            # Llamada a API
            response = self.client.chat.completions.create(...)
            return response
        except APIConnectionError as e:
            # El decorador maneja el retry
            raise
        except Exception as e:
            # Convertir a excepción personalizada
            raise GroqAPIError(
                message=f"Error al procesar prompt: {str(e)}",
                phase=ErrorPhase.FASE_2_EXTRACCION,
                retry_count=0,
                article_id=self.current_article_id
            ) from e
```

### Ejemplo 2: Manejo en Pipeline

```python
from utils.error_handling import (
    handle_groq_extraction_error_fase2,
    GroqAPIError
)

try:
    resultado = groq_service.extraer_elementos(texto)
except GroqAPIError as e:
    logger.error(f"Fallo en extracción: {e.message}")
    # Usar fallback
    resultado = handle_groq_extraction_error_fase2(
        article_id=articulo.id,
        titulo=articulo.titular,
        medio=articulo.medio,
        exception=e
    )
```

### Ejemplo 3: Respuesta de API

```python
from utils.error_handling import (
    create_error_response,
    ValidationError
)

@app.post("/procesar-articulo")
async def procesar_articulo(articulo: ArticuloInItem):
    try:
        # Procesar...
        return resultado
    except ValidationError as e:
        return create_error_response(e)
    except PipelineException as e:
        return create_error_response(e)
```

## 🔧 Decoradores de Retry

### @retry_groq_api

Decorador específico para llamadas a la API de Groq.

```python
@retry_groq_api(
    max_attempts=2,      # Máximo 2 reintentos
    wait_seconds=5.0,    # 5 segundos entre reintentos
    add_jitter=True      # Añade 0-1 segundo aleatorio
)
def llamar_groq_api():
    # Código que llama a Groq
```

**Características:**
- Convierte `RetryError` a `GroqAPIError` automáticamente
- Loggea intentos con nivel WARNING
- Loggea éxitos después de retry con nivel INFO
- Soporta funciones síncronas y asíncronas

### @retry_supabase_rpc

Decorador específico para llamadas RPC a Supabase.

```python
@retry_supabase_rpc(
    connection_retries=1,  # 1 reintento para conexión
    validation_retries=0   # 0 reintentos para validación
)
def llamar_supabase_rpc():
    # Código que llama a Supabase
```

**Comportamiento diferenciado:**
- `ConnectionError`, `TimeoutError`: Reintenta según `connection_retries`
- `ValueError`: No reintenta (error de validación)
- Otros errores: No reintenta

### @no_retry

Decorador de documentación para indicar que una función NO debe reintentar.

```python
@no_retry
def operacion_critica():
    # Operación que no debe reintentarse
```

## 🔍 Guía de Troubleshooting

### 1. Error: "Groq API no disponible después de 2 reintentos"

**Síntomas:**
- `GroqAPIError` con `retry_count=2`
- Logs muestran múltiples intentos fallidos

**Causas posibles:**
- API de Groq caída
- Límite de rate alcanzado
- Problema de conectividad

**Solución:**
1. Verificar estado de API de Groq
2. Revisar límites de rate
3. El sistema usará fallback automáticamente

### 2. Error: "Error de conexión con Supabase después de 1 reintento"

**Síntomas:**
- `SupabaseRPCError` con `is_connection_error=True`
- Fallo en persistencia

**Causas posibles:**
- Supabase no disponible
- Credenciales incorrectas
- Timeout de red

**Solución:**
1. Verificar conectividad con Supabase
2. Validar credenciales en `.env`
3. Los datos se guardarán en tabla de errores

### 3. Error: "Campo 'titular' es requerido"

**Síntomas:**
- `ValidationError` con detalles de campos
- Respuesta 400 Bad Request

**Causas posibles:**
- Datos de entrada incompletos
- Formato incorrecto

**Solución:**
1. Revisar estructura de datos enviada
2. Validar contra esquema Pydantic
3. Completar campos requeridos

### 4. Uso excesivo de fallbacks

**Síntomas:**
- Logs muestran muchos `FallbackExecuted`
- Datos degradados frecuentemente

**Causas posibles:**
- Problemas con servicios externos
- Configuración incorrecta
- Timeouts muy bajos

**Solución:**
1. Revisar salud de servicios externos
2. Ajustar timeouts si es necesario
3. Verificar configuración de API keys

### 5. Support codes en logs

**Formato:** `ERR_PIPE_FASE_TIMESTAMP`

**Uso:**
- Buscar en logs por support code
- Correlacionar con timestamp
- Identificar contexto del error

**Ejemplo búsqueda:**
```bash
grep "ERR_PIPE_FASE_2_EXTRACCION_1704456789" pipeline.log
```

## 📊 Métricas de Errores

### Contadores recomendados:
- Errores por tipo (`ValidationError`, `GroqAPIError`, etc.)
- Errores por fase (`FASE_1_TRIAJE`, etc.)
- Fallbacks ejecutados por fase
- Reintentos exitosos vs fallidos
- Tiempo de recuperación después de errores

### Alertas sugeridas:
- Tasa de error > 5% en últimos 5 minutos
- Más de 10 `ServiceUnavailableError` consecutivos
- Fallo total de un servicio externo
- Cola de procesamiento > 80% capacidad

## 🔄 Flujo de Manejo de Errores

```
1. Ocurre excepción
   ↓
2. ¿Tiene decorador de retry?
   Sí → Reintentar según configuración
   No → Continuar al paso 3
   ↓
3. ¿Reintento exitoso?
   Sí → Continuar procesamiento normal
   No → Convertir a excepción personalizada
   ↓
4. ¿Existe fallback para esta fase?
   Sí → Ejecutar fallback y continuar
   No → Propagar excepción
   ↓
5. ¿Es error crítico?
   Sí → Guardar en tabla de errores
   No → Registrar y continuar
```

## 🚀 Mejores Prácticas

1. **Siempre** usar excepciones personalizadas en lugar de genéricas
2. **Incluir** `article_id` cuando esté disponible
3. **Loggear** con contexto suficiente para debugging
4. **Preferir** fallbacks sobre fallos totales
5. **Documentar** cualquier comportamiento especial
6. **Monitorear** métricas de errores y fallbacks
7. **Revisar** periódicamente logs de errores recurrentes

---

*Última actualización: Diciembre 2024*
*Versión: 1.0.0*
