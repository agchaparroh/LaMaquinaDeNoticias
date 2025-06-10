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
        *   `es_relevante`: `False`
        *   `decision_triaje`: `"ERROR_MODELO_LINGUISTICO"`
        *   `justificacion_triaje`: Un mensaje indicando el fallo crítico en la carga del modelo spaCy y que el preprocesamiento no pudo completarse.
        *   `texto_para_siguiente_fase`: `""` (cadena vacía, ya que la limpieza del texto probablemente falló).
        *   Otros campos con valores predeterminados (ej. `categoria_principal="INDETERMINADO"`, `palabras_clave_triaje=[]`, `puntuacion_triaje=0.0`).
    *   La información sobre el error (incluyendo el nombre del modelo y detalles de la excepción) se almacena en el campo `metadatos_specificos_triaje` del resultado.
    *   Específicamente, el campo `notas_adicionales` (una lista de strings) dentro de `MetadatosFase1Triaje` puede contener un resumen del error.

### 2. Fallo en la Evaluación de Relevancia con API Groq

*   **Handler**: `handle_groq_relevance_error_fase1` (en `src.module_pipeline.src.utils.error_handling`)
*   **Disparador**: Ocurre si la llamada a la API de Groq para la evaluación de la relevancia de un fragmento falla (ej. la API no responde, devuelve un error, o la respuesta es `None` después de reintentos).
*   **Comportamiento**:
    *   Se registra un error sobre el fallo en la API de Groq.
    *   Se invoca al handler, que también devuelve un objeto `ResultadoFase1Triaje`.
    *   Este objeto típicamente contendrá:
        *   `es_relevante`: `False` (como valor conservador por defecto).
        *   `decision_triaje`: `"ERROR_EVALUACION_RELEVANCIA"`
        *   `justificacion_triaje`: Un mensaje indicando el fallo crítico en la API de Groq y que la evaluación no pudo completarse.
        *   `texto_para_siguiente_fase`: El `texto_limpio` que se había generado antes de la llamada a Groq, ya que la limpieza fue exitosa.
    *   Los detalles del error de la API se almacenan en `metadatos_specificos_triaje`.
    *   El campo `notas_adicionales` en `MetadatosFase1Triaje` contendrá un resumen del error.

### 3. Fallo en la Traducción con API Groq (Degradación Elegante)

*   **Handler**: `handle_groq_translation_fallback_fase1` (en `src.module_pipeline.src.utils.error_handling`)
*   **Disparador**: Ocurre si el fragmento de texto está en un idioma diferente al español y la llamada a la API de Groq para su traducción falla o devuelve una respuesta vacía.
*   **Comportamiento**:
    *   Esto se considera una "degradación elegante" más que un error que detiene el procesamiento del fragmento para la fase.
    *   Se registra una advertencia (WARNING) indicando que la traducción falló y que se utilizará el texto original.
    *   El handler devuelve un diccionario con el estado del fallback y un mensaje.
    *   El `texto_para_siguiente_fase` en el `ResultadoFase1Triaje` final se establecerá como el `texto_limpio` original (no traducido).
    *   El evento de fallback (ej. "Traducción de 'en' falló. Se usará texto original.") se añade a la lista `notas_adicionales` en el objeto `MetadatosFase1Triaje`.

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

Estos logs son fundamentales para el monitoreo del sistema, la depuración y la identificación de problemas recurrentes con dependencias externas o componentes internos.

## Actualización de Modelos Pydantic

Para facilitar el registro de estos eventos de fallback de manera estructurada dentro de los resultados del pipeline:
*   Se ha añadido el campo `notas_adicionales: Optional[List[str]] = None` al modelo Pydantic `MetadatosFase1Triaje` (definido en `src.module_pipeline.src.models.procesamiento.py`).
*   Este campo es una lista opcional de strings que se utiliza para almacenar mensajes informativos sobre los fallbacks aplicados durante la Fase 1 (ej. "Fallo en carga de modelo Spacy: se aplicó fallback.", "Traducción de 'en' falló. Se usará texto original."). Esto hace que la ocurrencia de un fallback sea explícita en los datos de salida de la fase.
