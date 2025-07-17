# Reporte de Funcionalidades spaCy en el Pipeline Actual

## Resumen Ejecutivo

Este reporte documenta todas las funcionalidades de spaCy implementadas actualmente en la Fase 1 del pipeline de procesamiento de La Máquina de Noticias, que deben ser preservadas durante la ampliación de 4 a 7 fases.

## Funcionalidades spaCy Implementadas

### 1. Carga y Caché de Modelos

**Ubicación**: `src/module_pipeline/src/pipeline/fase_1_triaje.py`

- **Función**: `_cargar_modelo_spacy(modelo: str = "es_core_news_lg")`
- **Características**:
  - Sistema de caché singleton para modelos cargados
  - Soporte para múltiples modelos de spaCy
  - Fallback automático a `es_core_news_lg` si el modelo solicitado falla
  - Manejo robusto de errores con logging

### 2. Limpieza de Texto con Tokenización

**Ubicación**: `src/module_pipeline/src/pipeline/fase_1_triaje.py`

- **Función**: `_limpiar_texto(texto_original: str, nlp_model: Optional[Language])`
- **Características**:
  - Tokenización completa del texto usando spaCy
  - Normalización de espacios (consolidación de múltiples espacios)
  - Normalización de puntuación repetida (ej: "!!!!" -> "!")
  - Preservación inteligente de saltos de línea
  - Manejo de tokens especiales (is_space, is_punct)
  - Fallback a limpieza básica sin spaCy si el modelo no está disponible

### 3. Detección de Idioma

**Ubicación**: `src/module_pipeline/src/pipeline/fase_1_triaje.py`

- **Función**: `_detectar_idioma(texto_para_detectar: str, nlp_model: Optional[Language])`
- **Características**:
  - Detección basada en el modelo cargado (nlp_model.lang)
  - Soporte para idiomas: ["es", "en", "fr", "de", "it", "pt", "und"]
  - Fallback a "es" si la detección resulta en "und"
  - Logging de advertencias sobre limitaciones de detección monolingüe

### 4. Análisis de Contenido (NO IMPLEMENTADO COMPLETAMENTE)

**Observación**: Aunque el documento de ampliación menciona análisis con spaCy para:
- `conteo_datos`: Números + unidades detectados
- `conteo_citas`: Comillas + atribución detectadas
- `conteo_entidades`: NER básico
- `es_entrevista`: Patrones P/R detectados

**Estado actual**: Estas funcionalidades NO están implementadas en el código actual. El análisis de contenido mencionado en el PRP es una NUEVA funcionalidad a implementar.

### 5. Integración con el Pipeline

- **Modelo por defecto**: `es_core_news_lg`
- **Configuración flexible**: Permite especificar diferentes modelos
- **Manejo de errores**: Handler específico `handle_spacy_load_error_fase1`
- **Fallback policy**: Acepta artículos cuando spaCy falla

## Funcionalidades a Preservar

1. **Sistema de caché de modelos**: Mantener el diccionario `_NLP_MODELS_CACHE`
2. **Lógica de limpieza de texto**: Preservar toda la lógica de tokenización
3. **Detección de idioma**: Mantener el sistema actual
4. **Manejo de errores y fallbacks**: Preservar la política de aceptación
5. **Configuración de modelo flexible**: Mantener parámetro `modelo_spacy_nombre`

## Nuevas Funcionalidades a Implementar (Componente 1B)

Según el documento de ampliación, se debe implementar el análisis de contenido con spaCy:

```python
Analisis_Componentes(
    conteo_datos=5,           # Números + unidades detectados
    conteo_citas=3,           # Comillas + atribución detectadas  
    conteo_entidades=12,      # NER básico
    longitud_caracteres=4850,
    es_entrevista=False,      # Patrones P/R detectados
)
```

Estas métricas se usarán para decisiones adaptativas en el Controlador de Flujo (Componente 1C).

## Recomendaciones

1. **Preservar toda la lógica existente** de spaCy en las funciones actuales
2. **Añadir nuevas funciones** para el análisis de componentes sin modificar las existentes
3. **Extender la fase 1** con el nuevo análisis manteniendo compatibilidad hacia atrás
4. **Documentar claramente** qué funcionalidades son nuevas vs existentes

## Conclusión

La implementación actual de spaCy es sólida pero limitada a preprocesamiento básico. La ampliación requerirá añadir análisis de contenido más profundo mientras se preserva toda la funcionalidad existente.