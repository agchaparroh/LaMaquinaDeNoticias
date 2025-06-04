# 📤 Salida (Output)

# Especificación de Salidas del `module_pipeline`

## 1. Tipos de Salida

El `module_pipeline` genera múltiples tipos de salida:

1. **Datos estructurados persistidos** en la base de datos
2. **Registro de estado del procesamiento** (éxito, error, descartado) en las tablas `articulos` o `documentos_extensos`
3. **Registro de errores persistentes** en `articulos_error_persistente`
4. **Registros de posibles duplicados** en `posibles_duplicados_hechos`
5. **Actualización de métricas** en `system_status`
6. **Respuesta HTTP** a la llamada API inicial (para el endpoint `/procesar`)

## 2. Formato de las Salidas

1. **Registros en tablas PostgreSQL** (datos estructurados)
2. **Campos actualizados en tablas PostgreSQL** (estado de procesamiento)
3. **Registros en tablas PostgreSQL** (errores persistentes)
4. **Registros en tablas PostgreSQL** (duplicados)
5. **Campos JSONB actualizados** en `system_status` (métricas)
6. **Respuesta JSON** (confirmación de recepción API)

## 3. Destinos de las Salidas

### 3.1. Base de Datos (Supabase/PostgreSQL)

**Tablas de datos estructurados:**
- `hechos`, `entidades`, `citas_textuales`, `datos_cuantitativos`
- `hecho_entidad`, `hecho_articulo`, `hecho_relacionado`
- `entidad_relacion`, `contradicciones`
- `cache_entidades` (indirectamente vía trigger)

**Tablas de control:**
- `articulos`, `documentos_extensos` (estado de procesamiento)
- `articulos_error_persistente` (errores)
- `posibles_duplicados_hechos` (duplicados)
- `system_status` (métricas)

### 3.2. Cliente API
- `module_connector` o iniciador de la solicitud API

## 4. Frecuencia y Modo de Entrega

- **Salidas a base de datos:** Ocurren al final del procesamiento de cada artículo/fragmento (Fase 5)
- **Respuesta API:** Inmediata tras la recepción (para el endpoint asíncrono `/procesar`)

## 5. Interfaz de Comunicación

- **Base de datos (1-5):** Interacción mediante la biblioteca `supabase-py` y llamadas a funciones RPC SQL
- **Respuesta HTTP (6):** Respuesta JSON estándar

## 6. RPCs Principales para Persistencia

### 6.1. RPC: `insertar_articulo_completo`

**Función SQL:** `insertar_articulo_completo(p_articulo_data JSONB)`

**Propósito:** Persiste toda la información procesada y extraída de un único artículo de noticias. Esta función se ejecuta al final del pipeline si el artículo ha pasado todas las fases de procesamiento y validación.

**Parámetro Principal:** `p_articulo_data` (tipo `JSONB`)

### 6.2. RPC: `insertar_fragmento_completo`

**Función SQL:** `insertar_fragmento_completo(p_fragmento_data JSONB, p_documento_id BIGINT)`

**Propósito:** Persiste toda la información procesada y extraída de un fragmento de un documento extenso (como un libro o un informe largo).

**Parámetros:**
- `p_fragmento_data` (tipo `JSONB`)
- `p_documento_id` (tipo `BIGINT`): El ID del documento maestro al que pertenece este fragmento

## 7. Estructura de Datos de Salida

### 7.1. Elementos Principales
- **Hechos extraídos:** Descripciones de eventos, situaciones o declaraciones específicas
- **Entidades autónomas:** Personas, organizaciones, lugares, conceptos nombrados
- **Citas textuales:** Fragmentos exactos de texto atribuidos a entidades específicas
- **Datos cuantitativos:** Información numérica estructurada

### 7.2. Relaciones Estructuradas
- **Relaciones entre hechos:** Vínculos como causa-efecto, secuencia temporal
- **Relaciones entre entidades:** Conexiones como empleado_de, miembro_de, ubicado_en
- **Contradicciones detectadas:** Inconsistencias identificadas entre hechos

### 7.3. Metadatos de Procesamiento
- **Estado de procesamiento:** Indicadores de éxito/error del pipeline
- **Fecha de procesamiento:** Timestamp de finalización
- **Importancia asignada:** Valor calculado por el modelo ML (escala 1-10)
- **Categorías y resúmenes:** Generados por el LLM

## 8. Respuestas de API

### 8.1. Respuesta de Éxito (202 Accepted)
```json
{
  "estado": "aceptado",
  "mensaje": "Artículo enviado a procesamiento",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 8.2. Respuesta de Error de Validación (400 Bad Request)
```json
{
  "error": "validation_error",
  "mensaje": "Error en la validación del artículo",
  "detalles": [
    "Campo 'titular' es requerido",
    "Campo 'contenido_texto' es requerido"
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 8.3. Respuesta de Error Interno (500 Internal Server Error)
```json
{
  "error": "internal_error",
  "mensaje": "Error interno del pipeline",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 8.4. Respuesta de Servicio No Disponible (503 Service Unavailable)
```json
{
  "error": "service_unavailable",
  "mensaje": "Pipeline temporalmente sobrecargado, reintente más tarde",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 9. Métricas del Sistema (Endpoint `/metrics`)

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

## 10. Estado del Sistema (Endpoint `/health`)

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

## 11. Consideraciones de Calidad de Datos

### 11.1. Integridad Referencial
- Todos los elementos extraídos mantienen referencias consistentes a sus fuentes originales
- Los IDs temporales se mapean correctamente a IDs de base de datos definitivos

### 11.2. Trazabilidad
- Cada elemento extraído puede rastrearse hasta su posición exacta en el texto original
- Los metadatos de procesamiento permiten auditar el flujo completo

### 11.3. Validación de Salida
- Verificación de estructura JSON antes de persistencia
- Validación de constraints de base de datos
- Comprobación de integridad de relaciones entre entidades

## 12. Manejo de Volúmenes Grandes

### 12.1. Optimizaciones de Persistencia
- **Transacciones atómicas:** Garantía de consistencia en operaciones complejas
- **Batch operations:** Agrupación de inserciones relacionadas
- **Connection pooling:** Gestión eficiente de conexiones de base de datos

### 12.2. Monitoreo de Rendimiento
- **Tiempo de persistencia por artículo/fragmento**
- **Throughput de elementos procesados por minuto**
- **Utilización de recursos de base de datos**
