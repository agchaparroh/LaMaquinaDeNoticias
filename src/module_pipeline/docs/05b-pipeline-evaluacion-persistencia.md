# 🔄 Pipeline de Procesamiento - Evaluación y Persistencia (Fases 4.5-5)

# Fases de Evaluación y Persistencia

## Fase 4.5: Evaluación de Importancia Contextual
    
**Objetivo:** Asignar un valor de importancia (escala 1-10) al hecho procesado, considerando no solo sus características intrínsecas sino también el contexto de tendencias informativas actual.
    
**Entrada:** Hechos procesados de la Fase 4 (con su importancia preliminar si fue asignada), metadatos del artículo/documento.
    
### Proceso de Evaluación

1. **Activación:** Esta fase se ejecuta después de la extracción y normalización básica del hecho.
        
2. **Consulta de contexto:** Consulta la tabla `tendencias_contexto_diario` para obtener el registro de contexto de tendencias correspondiente a la fecha de procesamiento del artículo/fragmento.
        
3. **Aplicación del modelo ML:** Utiliza un modelo de machine learning clásico (previamente entrenado y versionado por el script `importancia_model_trainer.py` de la IA Nocturna).
        
4. **Características de entrada:** El modelo de ML toma como entrada un conjunto de características (features):
        
   **Características intrínsecas del hecho:**
   - Tipo de hecho
   - País(es) asociados
   - Número y tipo de entidades involucradas
   - Si es un evento futuro
   - Longitud del contenido textual
   - Importancia preliminar asignada en Fase 2 (como característica adicional)
   
   **Características contextuales (derivadas de `tendencias_contexto_diario`):**
   - Relevancia actual de las temáticas del hecho
   - Si las entidades principales del hecho están marcadas como 'calientes' o relevantes recientemente
   - Si el hecho se relaciona con eventos próximos de alta prioridad
   - Si se alinea con hilos narrativos actualmente activos y con alta relevancia editorial
            
5. **Predicción:** El modelo predice el valor de importancia para el hecho.
        
**Salida:** Hechos con el campo importancia actualizado por el modelo de ML. Este valor se pasa a la Fase 5 para ser insertado en el campo `hechos.importancia`. Adicionalmente, este valor se registrará como `importancia_asignada_sistema` en la tabla `feedback_importancia_hechos` durante la persistencia en Fase 5.
    
**Interacciones:** 
- Base de Datos (lectura de `tendencias_contexto_diario`)
- Modelo de ML (carga y predicción)

## Fase 5: Ensamblaje Final y Persistencia Atómica (ejecutar_fase_5)
    
**Objetivo:** Ensamblar todos los datos procesados en el formato correcto y persistirlos en la base de datos de forma atómica usando una función RPC.
    
**Entrada:** Datos del artículo/fragmento original, salida completa de Fase 4 y Fase 4.5 (incluyendo la importancia finalizada del hecho).
    
### Proceso de Persistencia

1. **Preparación de datos:** Se preparan los datos del hecho, incluyendo el campo importancia determinado en la Fase 4.5.
        
2. **Inicialización de campos de evaluación:** Para la inserción en la tabla hechos, se inicializa:
   - `evaluacion_editorial` a `'pendiente_revision_editorial'`
   - `consenso_fuentes` a `'pendiente_analisis_fuentes'` (CP-005)
   
   > **Nota:** Los campos `confiabilidad` y `menciones_contradictorias` ya no se insertan.
        
3. **Llamada a RPC:** Se ejecuta la RPC de base de datos correspondiente:
   - `insertar_articulo_completo` para artículos
   - `insertar_fragmento_completo` para fragmentos
        
4. **Registro de feedback:** Dentro de la RPC, además de insertar el hecho y sus elementos relacionados, se realiza una inserción en la tabla `feedback_importancia_hechos`, registrando el `hecho_id` y la `importancia_asignada_sistema` (que es el valor de importancia calculado en la Fase 4.5) (CP-004).
        
**Salida:** 
- Estado de la persistencia (éxito/error)
- Contadores de elementos insertados/procesados
- Actualización del estado del artículo/documento en la BD
- Registro de errores persistentes si falla
    
**Interacciones:** Base de Datos (llamada a RPC `insertar_articulo_completo` o `insertar_fragmento_completo`).

## Conexiones con Servicios Externos

### Modelo de Machine Learning
**Configuración:**
- `IMPORTANCE_MODEL_PATH`: Ruta al archivo del modelo de importancia
- `IMPORTANCE_MODEL_VERSION`: Versión del modelo en uso

**Propósito:** Asignar valores de importancia contextual a los hechos procesados basándose en características intrínsecas y contextuales.

### Base de Datos Supabase
**Variables de entorno:**
- `SUPABASE_URL`: URL del proyecto Supabase
- `SUPABASE_KEY`: Clave anónima de Supabase
- `SUPABASE_SERVICE_ROLE_KEY`: Clave de rol de servicio

**Interacciones principales:**
- Lectura de `tendencias_contexto_diario` (Fase 4.5)
- Llamadas a RPCs de persistencia (Fase 5)
- Consulta de `cache_entidades` (Fase 4)

## Posibles Errores y Riesgos - Fases 4.5-5

### Fase 4.5 (Evaluación ML)
- **Errores en la carga del modelo de ML:** Archivo corrupto o incompatible
- **Fallo en la consulta a `tendencias_contexto_diario`:** Conexión de BD o datos faltantes
- **Características malformadas para el modelo:** Datos de entrada fuera del formato esperado
- **Predicciones fuera de rango esperado:** Valores de importancia inválidos

### Fase 5 (Persistencia)
- **Errores en la ejecución de la función RPC:** Violación de constraints, timeouts, lógica interna de la RPC
- **Fallo al registrar errores persistentes:** Problemas en el sistema de logging de errores
- **Inconsistencias transaccionales:** Fallos parciales en la atomicidad de las operaciones

## Configuración Avanzada

### Variables de Entorno para Evaluación y Persistencia
```bash
# Configuración específica para el modelo de importancia (Fase 4.5)
IMPORTANCE_MODEL_PATH=./models/importance_model.pkl
IMPORTANCE_MODEL_VERSION=1.0

# Configuración de base de datos avanzada
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
```

### Optimizaciones de Rendimiento
- **Pool de conexiones:** Configuración optimizada para múltiples workers concurrentes
- **Batch processing:** Agrupación de operaciones de persistencia cuando sea posible
- **Retry logic:** Reintentos automáticos para fallos transitorios de BD

## Adaptación para Fragmentos

La adaptación para procesar fragmentos de documentos implica:

1. **Metadatos adicionales:** Pasar `documento_id`, `fragmento_id` a través de las fases
2. **RPC específica:** Usar `insertar_fragmento_completo` en lugar de `insertar_articulo_completo`
3. **Contextualización:** Considerar el contexto del documento original en la evaluación de importancia
4. **Agregación:** Potencial agregación de métricas a nivel de documento

## Integración con el Modelo de "Tres Memorias"

### Lecturas
- **Memoria Superficial:** Consulta de `cache_entidades` para optimización
- **Memoria Relacional:** Lectura de `tendencias_contexto_diario` para contexto

### Escrituras
- **Memoria Relacional:** Persistencia de todos los datos estructurados extraídos
- **Memoria Superficial:** Actualización indirecta de cachés mediante triggers de BD

## Métricas y Monitoreo

### Métricas de Fase 4.5
- Tiempo de evaluación de importancia por hecho
- Distribución de valores de importancia asignados
- Tasa de éxito en consultas a `tendencias_contexto_diario`

### Métricas de Fase 5
- Tiempo de persistencia por artículo/fragmento
- Tasa de éxito de transacciones de BD
- Número de elementos persistidos por categoría (hechos, entidades, citas, etc.)
