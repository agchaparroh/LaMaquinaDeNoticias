# Auditoría de Manejo de Errores - Subtarea 24.1
**Fecha:** 2025-01-09
**Módulo:** module_pipeline

## Resumen Ejecutivo

Se identificaron múltiples puntos de mejora en el manejo de errores a través de los servicios externos. Los principales hallazgos incluyen:

1. **Ningún servicio usa las excepciones personalizadas** definidas en `error_handling.py`
2. **Inconsistencia en el sistema de logging** (algunos usan loguru, otros logging estándar)
3. **Decoradores de retry personalizados no están siendo utilizados**
4. **Falta de manejo específico de errores** en puntos críticos

## Checklist de Puntos Críticos Sin Manejo de Errores Apropiado

### 🔴 groq_service.py

| Punto Crítico | Estado Actual | Acción Requerida |
|--------------|---------------|------------------|
| Excepciones en `__init__` | Lanza ValueError genérico | Usar `ValidationError` de error_handling.py |
| Decorador retry | Usa tenacity genérico | Cambiar a `@retry_groq_api` personalizado |
| Manejo de excepciones | No convierte a `GroqAPIError` | Wrap excepciones en `GroqAPIError` con contexto |
| Fallback en `send_prompt` | Retorna None | Implementar fallback estructurado según docs |

### 🔴 supabase_service.py  

| Punto Crítico | Estado Actual | Acción Requerida |
|--------------|---------------|------------------|
| Sistema de logging | Usa logging.getLogger | Migrar a loguru |
| Excepciones en `__init__` | Lanza ValueError genérico | Usar `ValidationError` de error_handling.py |
| Decorador retry | Usa tenacity genérico | Cambiar a `@retry_supabase_rpc` personalizado |
| Manejo de excepciones RPC | Exception genérica | Convertir a `SupabaseRPCError` con contexto |
| Método `test_connection` | Sin manejo de errores específico | Agregar try-except con logging estructurado |

### 🔴 entity_normalizer.py

| Punto Crítico | Estado Actual | Acción Requerida |
|--------------|---------------|------------------|
| Método `normalizar_entidad` | Sin decorador retry | Agregar `@retry_supabase_rpc` |
| Excepción en catch | raise genérico | Convertir a `ProcessingError` o `SupabaseRPCError` |
| Fallback strategy | No implementada | Implementar handle_normalization_error_fase4 |
| Validación de entrada | Ninguna | Agregar validación de nombre_entidad vacío/None |

### 🟡 job_tracker_service.py

| Punto Crítico | Estado Actual | Acción Requerida |
|--------------|---------------|------------------|
| Sistema de logging | Usa get_logger() custom | Considerar migración a loguru directo |
| Excepciones personalizadas | No usa | Crear JobTrackerError heredando de PipelineException |
| Métodos sin try-except | `get_stats`, `set_retention_minutes` | Agregar manejo de errores |
| Thread safety errors | No captura errores de locks | Agregar manejo de threading.Lock errors |

## Identificación de Usos de Logging Estándar que Deberían Usar Loguru

1. **supabase_service.py** - Todo el archivo usa `logging.getLogger(__name__)`
   - Líneas: 35, 44, 56, 61, 73, 126, 139, 186, 201, etc.
   - **Acción:** Reemplazar con `from loguru import logger`

2. **job_tracker_service.py** - Usa wrapper `get_logger()` de logging_config
   - Líneas: Todas las instancias de `self.logger`
   - **Acción:** Evaluar si mantener el wrapper o usar loguru directamente

## Lugares Donde Faltan Decoradores de Retry

### Métodos que requieren @retry_groq_api:
- `groq_service._create_chat_completion_with_retry()` - Ya tiene retry pero debería usar el personalizado
- `groq_service.send_prompt()` - El método completo debería tener el decorador

### Métodos que requieren @retry_supabase_rpc:
- `supabase_service.insertar_articulo_completo()`
- `supabase_service.insertar_fragmento_completo()`
- `supabase_service.buscar_entidad_similar()`
- `entity_normalizer.normalizar_entidad()`

### Métodos que podrían beneficiarse de @retry_with_backoff:
- `supabase_service.test_connection()`
- Cualquier operación de I/O futura

## Verificación de Try-Except con Logging Apropiado

### ✅ Con logging apropiado:
- groq_service.py: Todos los bloques except tienen logger calls
- entity_normalizer.py: Try-except con logger.error

### ❌ Sin logging apropiado o faltante:
- supabase_service.py: Logging presente pero no usa loguru
- job_tracker_service.py: Algunos métodos sin try-except (`get_stats`, `set_retention_minutes`)

## Recomendaciones de Implementación (Prioridad)

### 🔥 Alta Prioridad:
1. Migrar supabase_service.py a loguru
2. Implementar decoradores personalizados en todos los servicios
3. Convertir excepciones genéricas a excepciones personalizadas de error_handling.py

### 🟡 Media Prioridad:
4. Agregar validaciones de entrada faltantes
5. Implementar fallbacks estructurados según documentación
6. Agregar try-except en métodos de job_tracker_service

### 🟢 Baja Prioridad:
7. Evaluar unificación del sistema de logging (directo vs wrapper)
8. Agregar más contexto a los logs existentes
9. Implementar métricas de fallback para monitoring

## Código de Ejemplo - Patrón Recomendado

```python
from loguru import logger
from ..utils.error_handling import (
    GroqAPIError, SupabaseRPCError, ProcessingError,
    retry_groq_api, retry_supabase_rpc,
    ErrorPhase
)

class ServicioMejorado:
    def __init__(self):
        self.logger = logger.bind(service="ServicioMejorado")
    
    @retry_groq_api(max_attempts=2, wait_seconds=5)
    async def llamar_groq(self, prompt: str, article_id: str):
        try:
            # Lógica de llamada
            response = await self.client.call(prompt)
            return response
        except GroqException as e:
            # Convertir a excepción personalizada
            raise GroqAPIError(
                message=f"Error llamando Groq: {str(e)}",
                phase=ErrorPhase.FASE_2_EXTRACCION,
                retry_count=2,
                article_id=article_id
            ) from e
```

## Conclusión

El sistema actual tiene una base sólida pero no está aprovechando las herramientas de manejo de errores ya implementadas en `error_handling.py`. La adopción consistente de estas herramientas mejorará significativamente la robustez y mantenibilidad del sistema.
