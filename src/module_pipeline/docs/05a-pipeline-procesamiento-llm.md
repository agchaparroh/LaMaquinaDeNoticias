# 🔄 Pipeline de Procesamiento - Procesamiento LLM (Fases 1-4)

# Flujo de Procesamiento Interno - Fases 1-4

El procesamiento se divide en fases secuenciales. Cada fase toma la salida de la anterior como entrada:

## 1. Fase 1: Preprocesamiento y Triaje (ejecutar_fase_1)
    
**Objetivo:** Limpiar el texto, detectar idioma, traducir si es necesario y evaluar la relevancia inicial (solo para artículos completos, los fragmentos siempre se procesan).
    
**Entrada:** Datos del artículo o fragmento.
    
**Salida:** Decisión de procesar/descartar, texto limpio/traducido (contenido_procesable), evaluación inicial (puntuación, tipo).
    
**Interacciones:** LLM Groq (para evaluación y traducción), spaCy (opcional, para prefiltrado).
    
**Prompt:** `Prompt_1_ filtrado.md`
    
## 2. Fase 2: Extracción de Elementos Básicos (ejecutar_fase_2)
    
**Objetivo:** Identificar y extraer los hechos principales y las entidades mencionadas en el texto.
    
**Entrada:** Texto procesable de Fase 1, metadatos del artículo/documento.
    
**Salida:** Lista de HechoBase y EntidadBase con IDs temporales. 

> **Nota:** En esta fase, el LLM podría intentar asignar una importancia preliminar al hecho, pero esta será refinada en la Fase 4.5.
    
**Interacciones:** LLM Groq.
    
**Prompt:** `Prompt_2_elementos_basicos.md`
    
## 3. Fase 3: Extracción de Citas y Datos Cuantitativos (ejecutar_fase_3)
    
**Objetivo:** Extraer citas textuales directas atribuidas a entidades y datos numéricos estructurados.
    
**Entrada:** Texto procesable, salida de Fase 2 (hechos y entidades con IDs temporales).
    
**Salida:** Lista de CitaTextual y DatosCuantitativos referenciando IDs temporales de hechos/entidades. Se añade articulo_id o documento_id/fragmento_id.
    
**Interacciones:** LLM Groq.
    
**Prompt:** `Prompt_3_citas_datos.md`
    
## 4. Fase 4: Normalización, Vinculación y Relaciones (ejecutar_fase_4)
    
**Objetivo:** Consolidar la información, vincular entidades a la base de datos, extraer relaciones entre elementos.
    
**Entrada:** Salidas de Fase 2 y Fase 3, contexto del artículo/fragmento.
    
**Salida:** Diccionario ResultadoFase4 conteniendo:
    
- **hechos:** Hechos formateados (HechoProcesado) con fechas TSTZRANGE. 
  > **Nota:** La importancia aquí es aún la preliminar de Fase 2.
        
- **entidades:** Entidades normalizadas (EntidadProcesada) con db_id si existen o marcadas como es_nueva.
        
- **citas, datos:** Listas de citas y datos (sin cambios desde Fase 3).
        
- **relaciones:** Estructura Relaciones (hecho-entidad, hecho-hecho, entidad-entidad, contradicciones) usando IDs temporales.
        
**Interacciones:**
- Base de Datos (tabla cache_entidades y RPC buscar_entidad_similar para normalización de entidades).
- Base de Datos (RPC para consultas especializadas).
- LLM Groq (para extraer relaciones y contradicciones).
            
**Prompt:** `Prompt_4_relaciones.md`

## Posibles Errores y Riesgos - Fases LLM

### Fase 1 (Triaje/Preprocesamiento)
- Descarte incorrecto de artículos relevantes o procesamiento de irrelevantes
- Errores en detección de idioma o traducción fallida
- Fallo en la evaluación de relevancia por parte del LLM

### Fases 2/3/4 (Procesamiento LLM)
- Errores de la API de Groq (timeouts, rate limits, errores internos)
- Respuestas del LLM vacías, incompletas o en formato JSON inválido
- Fallos en la limpieza/parseo del JSON (usando `json-repair`)
- Errores de validación Pydantic si el LLM no sigue la estructura esperada
- Extracción de información incorrecta o incompleta por el LLM

### Fase 4 (Normalización/Vinculación)
- Errores al consultar `cache_entidades` o RPCs de búsqueda en la BD
- Identificación incorrecta de entidades existentes (falsos positivos/negativos)
- Fallo en la detección de posibles duplicados

## Interacciones con Groq API

### Variables de Entorno para Groq (SDK v0.26.0)
- `GROQ_API_KEY`: Clave de API para acceso a Groq
- `MODEL_ID`: Identificador del modelo a utilizar (default: llama-3.1-8b-instant)
- `API_TIMEOUT`: Tiempo límite para solicitudes (default: 30s)
- `API_TEMPERATURE`: Configuración de temperatura del modelo (default: 0.1)
- `API_MAX_TOKENS`: Límite máximo de tokens por respuesta (default: 4000)
- `MAX_RETRIES`: Número máximo de reintentos (default: 3)
- `MAX_WAIT_SECONDS`: Tiempo máximo de espera entre reintentos (default: 60)

### Riesgos Relacionados
- **Consumo de API:** Alto consumo de tokens/créditos de la API de Groq
- **Dependencia de servicio externo:** Disponibilidad y rendimiento de la API de Groq
- **Límites de rate:** Restricciones de frecuencia de solicitudes

## Referencias a Prompts

Los prompts específicos para cada fase están almacenados en archivos externos:

- **Fase 1:** `Prompt_1_ filtrado.md`
- **Fase 2:** `Prompt_2_elementos_basicos.md`
- **Fase 3:** `Prompt_3_citas_datos.md`
- **Fase 4:** `Prompt_4_relaciones.md`

La configuración de cómo el LLM realiza estas extracciones se gestiona a través de archivos externos, permitiendo flexibilidad en la evolución y ajuste de los prompts sin modificar el código central del pipeline.

## Consideraciones de Rendimiento

### Optimizaciones Recomendadas
- **Paralelización:** Procesamiento concurrente de múltiples elementos cuando sea posible
- **Caché:** Reutilización de resultados de normalización de entidades
- **Batch processing:** Agrupación de solicitudes similares a la API de Groq
- **Circuit breakers:** Implementación de patrones de resistencia para fallos de servicios externos

### Monitoreo de Fases
- **Métricas por fase:** Seguimiento de tiempo de procesamiento y tasa de éxito
- **Alertas:** Notificaciones cuando las fases excedan umbrales de tiempo o error
- **Logging detallado:** Registro de eventos para debugging y optimización
