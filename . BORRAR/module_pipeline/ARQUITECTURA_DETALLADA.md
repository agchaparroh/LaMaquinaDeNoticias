# Arquitectura Detallada del Module Pipeline: Flujo de Transformación de Datos

## El Viaje de un Artículo a través del Pipeline

Este documento detalla cómo un artículo de noticias se transforma paso a paso desde texto crudo hasta conocimiento estructurado, explicando cada herramienta involucrada y las transformaciones específicas que ocurren.

## 1. Punto de Entrada: El Artículo Original

### Datos de Entrada

Un artículo llega al sistema con esta estructura:

```json
{
  "medio": "El País",
  "area_geografica": "España", 
  "tipo_medio": "Diario Digital",
  "titular": "El gobierno anuncia nuevas medidas económicas ante la inflación",
  "fecha_publicacion": "2024-01-15T10:30:00Z",
  "contenido_texto": "Madrid - El presidente del gobierno, Pedro Sánchez, anunció hoy un paquete de medidas económicas valorado en 10.000 millones de euros para combatir la inflación, que alcanzó el 5.7% en diciembre. \"No vamos a permitir que las familias españolas pierdan poder adquisitivo\", declaró Sánchez en rueda de prensa...",
  "autor": "María González",
  "url": "https://elpais.com/economia/2024-01-15/...",
  "seccion": "Economía"
}
```

### Primera Decisión del Sistema

El `PipelineController` evalúa la longitud del contenido:

- **Si > 50 caracteres**: Crea un job asíncrono
  ```python
  job_id = str(uuid4())  # "d4f3a8b1-9c2e-4f6d-8e3a-1b2c3d4e5f6g"
  job_tracker.create_job(job_id, "articulo", articulo_data)
  # Retorna inmediatamente: {"job_id": "d4f3a8b1-9c2e-4f6d-8e3a-1b2c3d4e5f6g"}
  ```

- **Si ≤ 50 caracteres**: Procesa síncronamente

### Creación del FragmentProcessor

Cada artículo/fragmento recibe su propio `FragmentProcessor`:

```python
processor = FragmentProcessor(fragment_id)
# Inicializa contadores en 0:
# - next_hecho_id → 1, 2, 3...
# - next_entidad_id → 1, 2, 3...
# - next_cita_id → 1, 2, 3...
# - next_dato_id → 1, 2, 3...
```

## 2. FASE 1: Preprocesamiento y Triaje

### 2.1 Carga del Modelo spaCy

**Herramienta**: spaCy con modelo `es_core_news_lg` (modelo grande de español)

```python
# Sistema singleton con caché
if "es_core_news_lg" not in _NLP_MODELS_CACHE:
    _NLP_MODELS_CACHE["es_core_news_lg"] = spacy.load("es_core_news_lg")
```

### 2.2 Tokenización y Limpieza

**Entrada**: 
```
"Madrid - El presidente del gobierno,    Pedro Sánchez,     anunció hoy!!!! un paquete..."
```

**Proceso de Transformación**:

```python
doc = nlp_model(texto_original)
# spaCy crea objetos Token con propiedades:
# Token("Madrid", pos=PROPN, is_space=False, is_punct=False)
# Token("-", pos=PUNCT, is_space=False, is_punct=True)
# Token(" ", pos=SPACE, is_space=True, is_punct=False)
```

**Reglas de Limpieza Aplicadas**:

1. **Espacios múltiples → espacio único**
   ```
   "Pedro    Sánchez" → "Pedro Sánchez"
   ```

2. **Puntuación repetida → única**
   ```
   "anunció hoy!!!!" → "anunció hoy!"
   ```

3. **Preservación de saltos de línea**
   ```
   "Primera línea\n\nSegunda línea" → SE MANTIENE
   ```

**Salida de Limpieza**:
```
"Madrid - El presidente del gobierno, Pedro Sánchez, anunció hoy! un paquete..."
```

### 2.3 Evaluación de Relevancia con Groq

**Preparación del Prompt**:

```python
# Se carga plantilla: prompts/Prompt_1_filtrado.md
prompt = plantilla.replace("{{TEXTO_LIMPIO}}", texto_limpio)
                 .replace("{{FECHA_ACTUAL}}", "2024-01-15")
```

**Llamada a Groq API**:

```python
# Configuración
model: "llama-3.1-8b-instant"
temperature: 0.1  # Baja para consistencia
max_tokens: 500   # Respuesta corta esperada
timeout: 30s

# System prompt
"Eres un evaluador de relevancia periodística..."

# User prompt
"Evalúa este texto según 5 criterios..."
```

**Respuesta del LLM** (ejemplo):
```
Criterio 1 - Relevancia temporal: 5/5 (evento actual)
Criterio 2 - Impacto social: 5/5 (afecta a toda la población)
Criterio 3 - Interés noticioso: 4/5 (tema económico importante)
Criterio 4 - Calidad informativa: 4/5 (incluye datos y declaraciones)
Criterio 5 - Contenido verificable: 5/5 (fuentes oficiales citadas)

Puntuación total: 23/25
Decisión: PROCESAR
```

**Transformación a Modelo Estructurado**:

```python
ResultadoFase1Triaje(
    id_fragmento=UUID("..."),
    es_relevante=True,
    decision_triaje="PROCESAR",
    puntuacion_triaje=23.0,
    confianza_triaje=0.92,  # 23/25
    texto_para_siguiente_fase="Madrid - El presidente del gobierno...",  # Texto limpio
    metadatos_specificos_triaje=MetadatosFase1Triaje(
        nombre_modelo_triaje="es_core_news_lg",
        tokens_prompt_triaje=156,
        tokens_respuesta_triaje=89,
        duracion_llamada_ms_triaje=2341,
        texto_limpio_utilizado="Madrid - El presidente...",
        idioma_detectado_original="es"
    )
)
```

## 3. FASE 2: Extracción de Elementos Básicos

### 3.1 Preparación del Contexto

**Datos que se ensamblan para el prompt**:

```python
contexto = {
    "TITULO_O_DOCUMENTO": "El gobierno anuncia nuevas medidas económicas ante la inflación",
    "FUENTE_O_TIPO": "Diario Digital",
    "PAIS_ORIGEN": "España",
    "FECHA_FUENTE": "2024-01-15",
    "CONTENIDO": texto_limpio_fase1  # El texto ya limpio
}
```

### 3.2 Prompt Estructurado para Extracción

Se usa `Prompt_2_elementos_basicos.md` que instruye al LLM a extraer:

- **Entidades**: Personas, organizaciones, lugares, eventos, normativas, conceptos
- **Hechos**: Sucesos, anuncios, declaraciones con contexto temporal y geográfico

### 3.3 Respuesta del LLM y Parsing

**Respuesta Cruda** (puede incluir markdown):
```markdown
```json
{
  "entidades": [
    {
      "id": 1,
      "nombre": "Pedro Sánchez",
      "tipo": "PERSONA",
      "descripcion": "- presidente del gobierno",
      "alias": ["Sánchez"]
    },
    {
      "id": 2,
      "nombre": "España",
      "tipo": "LUGAR",
      "descripcion": null
    }
  ],
  "hechos": [
    {
      "id": 1,
      "contenido": "El presidente del gobierno anunció un paquete de medidas económicas valorado en 10.000 millones de euros",
      "fecha": {"inicio": "2024-01-15", "fin": "2024-01-15"},
      "tipo_hecho": "ANUNCIO",
      "pais": ["España"],
      "ciudad": ["Madrid"]
    }
  ]
}
```
```

**Parser JSON Robusto**:

```python
# El parser maneja:
1. Elimina marcadores markdown (```json)
2. Repara JSON truncado (agrega } ] faltantes)
3. Escapa caracteres problemáticos
4. Valida estructura esperada

respuesta_json = parse_llm_json_response(respuesta_cruda)
```

### 3.4 Procesamiento y Validación

**Para cada Entidad**:

```python
# Sanitización
nombre_sanitizado = escape_html("Pedro Sánchez")  # Previene XSS

# Registro en FragmentProcessor
id_asignado = processor.next_entidad_id("Pedro Sánchez")  # → 1

# Creación del modelo
EntidadProcesada(
    id_entidad=1,  # ID secuencial
    texto_entidad="Pedro Sánchez",
    tipo_entidad="PERSONA",
    relevancia_entidad=0.9,  # Calculada por presencia
    id_fragmento_origen=fragment_id,
    metadata_entidad=MetadatosEntidad(
        tipo="PERSONA",
        descripcion_estructurada=["presidente del gobierno"],
        alias=["Sánchez"]
    )
)
```

**Para cada Hecho**:

```python
# Similar proceso
id_hecho = processor.next_hecho_id("anuncio medidas")  # → 1

HechoProcesado(
    id_hecho=1,
    texto_original_del_hecho="El presidente del gobierno anunció...",
    confianza_extraccion=0.95,
    id_fragmento_origen=fragment_id,
    metadata_hecho=MetadatosHecho(
        tipo_hecho="ANUNCIO",
        pais=["España"],
        ciudad=["Madrid"],
        precision_temporal="dia",
        es_futuro=False
    )
)
```

### 3.5 Salida de Fase 2

```python
ResultadoFase2Extraccion(
    id_fragmento=fragment_id,
    hechos_extraidos=[hecho1, hecho2, ...],  # Lista de HechoProcesado
    entidades_extraidas=[entidad1, entidad2, ...],  # Lista de EntidadProcesada
    resumen_extraccion="Extraídos 3 hechos y 5 entidades con IDs secuenciales",
    metadata_extraccion={
        "modelo_usado": "llama-3.1-8b-instant",
        "tokens_prompt": 584,
        "tokens_respuesta": 1203,
        "num_hechos_extraidos": 3,
        "num_entidades_extraidas": 5
    }
)
```

## 4. FASE 3: Extracción de Citas y Datos Cuantitativos

### 4.1 Construcción del Contexto JSON_PASO_1

**Transformación de resultados previos**:

```python
json_paso_1 = {
    "hechos": [
        {
            "id": 1,
            "contenido": "El presidente anunció medidas por 10.000 millones",
            "tipo": "ANUNCIO"
        }
    ],
    "entidades": [
        {
            "id": 1,
            "nombre": "Pedro Sánchez",
            "tipo": "PERSONA"
        }
    ]
}
```

### 4.2 Instrucciones Específicas al LLM

El prompt `Prompt_3_citas_datos.md` pide:

- **Citas**: Con referencia a quien las dijo (usando IDs de entidades)
- **Datos**: Con valores numéricos y unidades (vinculados a hechos)

### 4.3 Extracción y Vinculación

**Respuesta del LLM**:

```json
{
  "citas_textuales": [
    {
      "id": 1,
      "cita": "No vamos a permitir que las familias españolas pierdan poder adquisitivo",
      "entidad_id": 1,  // Pedro Sánchez
      "hecho_id": 1,    // El anuncio
      "relevancia": 5
    }
  ],
  "datos_cuantitativos": [
    {
      "id": 1,
      "indicador": "Presupuesto del paquete de medidas",
      "valor": 10000,
      "unidad": "millones de euros",
      "hecho_id": 1,
      "categoria": "económico"
    },
    {
      "id": 2,
      "indicador": "Tasa de inflación",
      "valor": 5.7,
      "unidad": "%",
      "periodo": {"inicio": "2023-12-01", "fin": "2023-12-31"}
    }
  ]
}
```

### 4.4 Validación Cruzada

```python
# Verificar que entidad_id=1 existe en Fase 2
if cita.entidad_id not in {e.id_entidad for e in resultado_fase2.entidades_extraidas}:
    advertencias.append(f"Cita referencia entidad inexistente: {cita.entidad_id}")

# Verificar que hecho_id=1 existe en Fase 2
if dato.hecho_id not in {h.id_hecho for h in resultado_fase2.hechos_extraidos}:
    advertencias.append(f"Dato referencia hecho inexistente: {dato.hecho_id}")
```

### 4.5 Modelos Resultantes

```python
CitaTextual(
    id_cita=1,
    texto_cita="No vamos a permitir que las familias españolas...",
    id_entidad_citada=1,  # Vinculado a Pedro Sánchez
    metadata_cita=MetadatosCita(
        relevancia=5,
        contexto="En rueda de prensa sobre medidas económicas"
    )
)

DatosCuantitativos(
    id_dato_cuantitativo=1,
    descripcion_dato="Presupuesto del paquete de medidas",
    valor_dato=10000.0,
    unidad_dato="millones de euros",
    metadata_dato=MetadatosDato(
        categoria="económico",
        tipo_periodo="puntual"
    )
)
```

## 5. FASE 4: Normalización y Detección de Relaciones

### 5.1 Normalización de Entidades con Supabase

**Proceso para cada entidad**:

```python
# 1. Generar embedding de la entidad
embedding = generate_embedding("Pedro Sánchez presidente gobierno")  # Vector 384D

# 2. Buscar en Supabase
respuesta = supabase.rpc("buscar_entidad_similar", {
    "p_tipo_entidad": "PERSONA",
    "p_embedding_busqueda": embedding,
    "p_umbral_similitud": 0.85
})

# Respuesta:
{
    "entidad_id": "550e8400-e29b-41d4-a716",
    "nombre_canonico": "Pedro Sánchez Pérez-Castejón",
    "similitud": 0.92,
    "uri_wikidata": "https://www.wikidata.org/wiki/Q6083139"
}
```

**Actualización de la entidad**:

```python
entidad.id_entidad_normalizada = UUID("550e8400-e29b-41d4-a716")
entidad.nombre_entidad_normalizada = "Pedro Sánchez Pérez-Castejón"
entidad.uri_wikidata = "https://www.wikidata.org/wiki/Q6083139"
entidad.similitud_normalizacion = 0.92
```

### 5.2 Detección de Relaciones con Groq

**Preparación para el LLM**:

```python
contexto_relaciones = {
    "hechos": [todos los hechos con sus IDs],
    "entidades": [todas las entidades normalizadas],
    "citas": [todas las citas],
    "datos": [todos los datos]
}
```

**Tipos de relaciones detectadas**:

1. **Hecho-Entidad**:
   ```python
   RelacionHechoEntidad(
       hecho_id=1,  # "Anuncio de medidas"
       entidad_id=1,  # "Pedro Sánchez"
       tipo_relacion="protagonista",
       relevancia_en_hecho=10
   )
   ```

2. **Hecho-Hecho**:
   ```python
   RelacionHechoHecho(
       hecho_origen_id=2,  # "Inflación alcanza 5.7%"
       hecho_destino_id=1,  # "Anuncio de medidas"
       tipo_relacion="causa",
       descripcion="La inflación motivó el anuncio"
   )
   ```

3. **Entidad-Entidad**:
   ```python
   RelacionEntidadEntidad(
       entidad_origen_id=1,  # "Pedro Sánchez"
       entidad_destino_id=3,  # "Gobierno de España"
       tipo_relacion="lidera",
       vigente=True
   )
   ```

## 6. Construcción del Payload Final

### 6.1 PayloadBuilder: Transformación de IDs

**De secuenciales a temporales únicos**:

```python
# Interno: id_hecho=1
# Payload: id_temporal_hecho="hecho_1_550e8400"

def _generar_id_temporal(tipo: str, id_secuencial: int, fragment_id: UUID) -> str:
    return f"{tipo}_{id_secuencial}_{str(fragment_id)[:8]}"
```

### 6.2 Estructura Final para Supabase

```python
ArticuloPersistenciaPayload(
    # Metadatos del artículo
    url="https://elpais.com/...",
    medio="El País",
    titular="El gobierno anuncia...",
    fecha_publicacion="2024-01-15T10:30:00Z",
    contenido_texto_original="Madrid - El presidente...",
    
    # Resultados del pipeline
    estado_procesamiento_final_pipeline="completado_ok",
    fecha_procesamiento_pipeline="2024-01-15T10:32:45Z",
    
    # Elementos extraídos (con IDs temporales)
    hechos_extraidos=[
        {
            "id_temporal_hecho": "hecho_1_550e8400",
            "descripcion_hecho": "Anuncio de medidas económicas",
            "tipo_hecho": "ANUNCIO",
            "entidades_del_hecho": [
                {
                    "id_temporal_entidad": "entidad_1_550e8400",
                    "rol_en_hecho": "protagonista"
                }
            ]
        }
    ],
    
    entidades_autonomas=[
        {
            "id_temporal_entidad": "entidad_1_550e8400",
            "nombre_entidad": "Pedro Sánchez",
            "tipo_entidad": "PERSONA",
            "embedding_entidad_vector": [0.123, -0.456, ...]  # 384 dimensiones
        }
    ],
    
    # Relaciones
    relaciones_hechos=[...],
    relaciones_entidades=[...]
)
```

### 6.3 RPC Atómica a Supabase

```python
# Una sola llamada inserta todo
resultado = supabase.rpc("insertar_articulo_completo", {
    "p_articulo_data": payload.model_dump()
})

# Respuesta:
{
    "articulo_id": "7f8a9b0c-1d2e-3f4g-5h6i",
    "hechos_insertados": 3,
    "entidades_insertadas": 5,
    "citas_insertadas": 2,
    "datos_insertados": 2,
    "relaciones_insertadas": 7,
    "warnings": []
}
```

## 7. Manejo de Errores y Recuperación

### 7.1 Cascada de Fallbacks

1. **Si spaCy falla** → Usa limpieza regex básica
2. **Si Groq falla** → Acepta documento con metadata de error
3. **Si parsing JSON falla** → Intenta reparar, sino valores vacíos
4. **Si Supabase falla** → Reintenta con backoff exponencial

### 7.2 Preservación de Información

Incluso con errores, el sistema preserva:
- Texto original siempre disponible
- Metadatos de qué falló y por qué
- Resultados parciales de fases completadas

## 8. Métricas y Observabilidad

### 8.1 Métricas por Fase

```python
# Tiempo de procesamiento
fase_1_duration_ms: 156
fase_2_duration_ms: 2341
fase_3_duration_ms: 1876
fase_4_duration_ms: 892

# Tokens consumidos
total_tokens_prompt: 2,347
total_tokens_completion: 3,892

# Elementos extraídos
hechos_totales: 3
entidades_totales: 5
citas_totales: 2
datos_totales: 2
relaciones_totales: 7
```

### 8.2 Trazabilidad Completa

Cada elemento mantiene referencia a:
- `id_fragmento_origen`: De dónde vino
- `prompt_utilizado`: Qué se le preguntó al LLM
- `respuesta_llm_bruta`: Qué respondió exactamente
- `timestamp`: Cuándo se procesó

## Resumen: La Transformación Completa

**ENTRADA**: 
```
Artículo de noticias (JSON con texto no estructurado)
```

**TRANSFORMACIONES**:
1. **spaCy**: Texto → Tokens → Texto limpio normalizado
2. **Groq (Triaje)**: Texto → Evaluación de relevancia
3. **Groq (Extracción)**: Texto → Hechos + Entidades estructuradas
4. **Groq (Citas/Datos)**: Contexto → Citas vinculadas + Datos numéricos
5. **Supabase + Groq**: Entidades → Entidades normalizadas + Relaciones

**SALIDA**:
```
Grafo de conocimiento con:
- Hechos timestamped y geolocalizados
- Entidades normalizadas con URIs
- Citas atribuidas
- Datos cuantitativos contextualizados
- Red de relaciones tipadas
```

Cada transformación agrega capas de estructura y significado, convirtiendo texto plano en conocimiento consultable y analizable.