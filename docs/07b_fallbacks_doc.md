# Mecanismos de Fallback Específicos del Pipeline

Además de las excepciones generales y el manejo de errores estándar, el pipeline implementa mecanismos de fallback específicos para ciertas etapas críticas, asegurando la resiliencia y la degradación elegante del servicio cuando sea posible. Estos fallbacks suelen implicar la continuación del procesamiento con datos parciales o predeterminados y el registro detallado del evento.

## Fallbacks en Fase 1: Triaje (`fase_1_triaje.py`)

La Fase 1 de Triaje es crucial para la selección inicial de fragmentos de noticias. Se han implementado los siguientes mecanismos de fallback:

### 1. Fallo en la Carga del Modelo SpaCy

*   **Handler**: `handle_spacy_load_error_fase1` (en `src.module_pipeline.src.utils.error_handling`)
*   **Disparador**: Ocurre si el modelo de lenguaje spaCy (ej. `es_core_news_sm`) no puede ser cargado debido a que no está descargado, está corrupto o por otros errores de la biblioteca spaCy.
*   **Comportamiento**:
    *   Se registra un error detallado sobre el fallo en la carga del modelo.
    *   Se invoca al handler, que devuelve un objeto `ResultadoFase1Triaje` predefinido.
    *   Este objeto típicamente contendrá:
        *   `es_relevante`: `True` (el artículo se **acepta por defecto** para permitir el procesamiento posterior a pesar del fallo en el preprocesamiento).
        *   `decision_triaje`: `"FALLBACK_ACEPTADO_ERROR_PREPROCESO"`
        *   `justificacion_triaje`: Un mensaje indicando el fallo en la carga del modelo spaCy, que el preprocesamiento fue degradado y el artículo aceptado automáticamente.
        *   `texto_para_siguiente_fase`: El `texto_original_fragmento` (texto original sin limpiar), ya que la limpieza del texto falló o fue incompleta.
        *   Otros campos con valores predeterminados (ej. `categoria_principal="INDETERMINADO"`, `palabras_clave_triaje=[]`, `puntuacion_triaje=0.0`).
    *   La información sobre el error (incluyendo el nombre del modelo y detalles de la excepción) se almacena en el campo `metadatos_specificos_triaje` del resultado, y un resumen en `notas_adicionales`.
    *   El logging primario de este evento de fallback se realiza a nivel `WARNING`, utilizando un log estructurado.

### 2. Fallo en la Evaluación de Relevancia con API Groq

*   **Handler**: `handle_groq_relevance_error_fase1` (en `src.module_pipeline.src.utils.error_handling`)
*   **Disparador**: Ocurre si la llamada a la API de Groq para la evaluación de la relevancia de un fragmento falla (ej. la API no responde, devuelve un error, o la respuesta es `None` después de reintentos). Esto también se aplica si la `GROQ_API_KEY` no está configurada.
*   **Comportamiento**:
    *   Se registra un error (`ERROR`) detallado sobre el fallo en la API de Groq, utilizando un log estructurado.
    *   Se invoca al handler, que también devuelve un objeto `ResultadoFase1Triaje`.
    *   Este objeto contendrá:
        *   `es_relevante`: `True` (el artículo se **acepta por defecto** a pesar del fallo en la evaluación de relevancia).
        *   `decision_triaje`: `"FALLBACK_ACEPTADO_ERROR_LLM"`
        *   `justificacion_triaje`: Un mensaje indicando el fallo en la API de Groq y que el artículo fue aceptado automáticamente.
        *   `texto_para_siguiente_fase`: El `texto_limpio` que se había generado antes de la llamada a Groq, ya que la limpieza (si ocurrió) fue exitosa.
    *   Los detalles del error de la API se almacenan en `metadatos_specificos_triaje`, y un resumen en `notas_adicionales`.

### 3. Fallo en la Traducción con API Groq (Degradación Elegante)

*   **Handler**: `handle_groq_translation_fallback_fase1` (en `src.module_pipeline.src.utils.error_handling`)
*   **Disparador**: Ocurre si el fragmento de texto está en un idioma diferente al español y la llamada a la API de Groq para su traducción falla o devuelve una respuesta vacía.
*   **Comportamiento**:
    *   Esto se considera una "degradación elegante" más que un error que detiene el procesamiento del fragmento para la fase.
    *   Se registra una advertencia (WARNING) indicando que la traducción falló y que se utilizará el texto original.
    *   El handler devuelve un diccionario con el estado del fallback y un mensaje.
    *   El `texto_para_siguiente_fase` en el `ResultadoFase1Triaje` final se establecerá como el `texto_limpio` original (no traducido).
    *   El evento de fallback (ej. "Traducción de 'en' falló. Se usará texto original.") se añade a la lista `notas_adicionales` en el objeto `MetadatosFase1Triaje`.
    *   El logging de este evento de fallback se realiza a nivel `WARNING` utilizando un log estructurado.

### 4. Detección de Idioma Indeterminado ("und")

*   **Comportamiento**: No es un handler de error separado, sino una lógica dentro de `ejecutar_fase_1`.
*   **Disparador**: Si la función `_detectar_idioma` (utilizando el modelo spaCy) devuelve `"und"` (indeterminado) como código de idioma.
*   **Comportamiento**:
    *   El sistema asume que el idioma es español (`"es"`) para permitir que el procesamiento continúe.
    *   Se añade una nota informativa al campo `notas_adicionales` del objeto `MetadatosFase1Triaje` (ej. "Idioma asumido como 'es' por fallo en detección.").
    *   El procesamiento subsiguiente (como la evaluación de relevancia y la necesidad de traducción) se basará en este idioma asumido.

## Handler de Error Genérico para Fases Posteriores

*   **Handler**: `handle_generic_phase_error` (en `src.module_pipeline.src.utils.error_handling`)
*   **Propósito**: Esta es una utilidad más genérica diseñada para ser utilizada en fases posteriores del pipeline (Fase 2, 3, 4) en caso de errores de procesamiento no cubiertos por fallbacks más específicos.
*   **Comportamiento**:
    *   Registra un error sobre el fallo en la fase y paso especificados.
    *   Devuelve un diccionario que representa una estructura de error genérica para el resultado de esa fase, incluyendo:
        *   `status`: `"ERROR"`
        *   `phase_name`: El nombre de la fase donde ocurrió el error.
        *   `error_type`: Un tipo de error (ej. `"PROCESSING_ERROR"` o derivado de la excepción).
        *   `message`: Un mensaje descriptivo del fallo.
        *   `data`: Un diccionario vacío o una estructura mínima requerida para el modelo de salida de esa fase.

## Logging de Eventos de Fallback

Es crucial destacar que **todos los eventos de fallback y los errores que los desencadenan son registrados exhaustivamente utilizando `loguru.logger`**. Esto incluye:
*   Mensajes de `ERROR` cuando ocurren las excepciones originales (ej. fallo de carga de spaCy, error de API Groq).
*   Mensajes de `INFO` cuando se activa un mecanismo de fallback, indicando que el sistema está manejando la condición de error de forma controlada.
*   Mensajes de `WARNING` para situaciones como el fallback de traducción, donde el procesamiento continúa pero con una degradación del servicio.
*   Los handlers de fallback específicos (`handle_spacy_load_error_fase1`, `handle_groq_relevance_error_fase1`, `handle_groq_translation_fallback_fase1`) han sido actualizados para utilizar `format_error_for_logging` junto con clases de excepción personalizadas (`SpaCyModelLoadFallbackLog`, `GroqRelevanceFallbackLog`, `GroqTranslationFallbackLogEvent`). Esto asegura que los logs emitidos por estos handlers sean más detallados, estructurados y consistentes con el formato definido en la sección 9.4 del documento principal de manejo de errores.

Estos logs son fundamentales para el monitoreo del sistema, la depuración y la identificación de problemas recurrentes con dependencias externas o componentes internos.

## Mecanismos de Reintento (Retry)

### Reintentos para llamadas a API Groq en Fase 1

*   Las funciones `_llamar_groq_api_triaje` y `_llamar_groq_api_traduccion` en `fase_1_triaje.py` ahora utilizan el decorador `@retry_groq_api`.
*   Este decorador estandariza la política de reintentos para estas llamadas críticas:
    *   **Máximo de intentos**: 2 reintentos (además del intento inicial, sumando 3 intentos en total).
    *   **Pausa entre intentos**: Una pausa fija de 5 segundos.
    *   **Condiciones de reintento**: Se reintenta ante excepciones comunes de la API de Groq como `APIConnectionError`, `RateLimitError`, `APIStatusError`, `TimeoutError`, y `ConnectionError`.
*   Si todos los intentos fallan, se lanza una excepción `GroqAPIError` que es manejada por los mecanismos de fallback descritos anteriormente.

## Actualización de Modelos Pydantic

Para facilitar el registro de estos eventos de fallback de manera estructurada dentro de los resultados del pipeline:
*   Se ha añadido el campo `notas_adicionales: Optional[List[str]] = None` al modelo Pydantic `MetadatosFase1Triaje` (definido en `src.module_pipeline.src.models.procesamiento.py`).
*   Este campo es una lista opcional de strings que se utiliza para almacenar mensajes informativos sobre los fallbacks aplicados durante la Fase 1 (ej. "Fallo en carga de modelo Spacy: se aplicó fallback.", "Traducción de 'en' falló. Se usará texto original."). Esto hace que la ocurrencia de un fallback sea explícita en los datos de salida de la fase.
