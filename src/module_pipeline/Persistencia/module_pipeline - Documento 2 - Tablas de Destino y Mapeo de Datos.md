# Documento 2: Tablas de Destino y Mapeo de Datos en Supabase

## 1. Introducción

Este documento detalla las tablas de la base de datos Supabase que son directamente afectadas por las RPCs de persistencia del `module_pipeline` (`insertar_articulo_completo` e `insertar_fragmento_completo`). Para cada tabla, se describe su propósito y cómo los campos de los payloads JSONB (definidos en el "Documento 1 - RPCs y Payloads de Persistencia") se mapean a sus columnas.

Comprender este mapeo es fundamental para entender qué información se almacena, dónde y con qué estructura.

## 2. Mapeo de Payloads a Tablas

### 2.1. Tabla: `articulos`

*   **Propósito:** Almacena la información central de cada artículo de noticias procesado, incluyendo metadatos originales, contenido textual, y los principales resultados del análisis del pipeline.
*   **Poblada por RPC:** `insertar_articulo_completo`
*   **Mapeo de Campos desde `p_articulo_data`:**

    | Columna en `articulos`         | Campo en `p_articulo_data`                                  | Tipo de Dato (SQL) | Notas                                                                 |
    |--------------------------------|-------------------------------------------------------------|--------------------|-----------------------------------------------------------------------|
    | `id`                           | (Generado por la BD)                                        | `BIGSERIAL`        | Clave primaria.                                                       |
    | `url_original`                 | `url`                                                       | `TEXT`             |                                                                       |
    | `storage_path`                 | `storage_path`                                              | `TEXT`             |                                                                       |
    | `fuente_original`              | `fuente_original`                                           | `TEXT`             |                                                                       |
    | `medio`                        | `medio`                                                     | `TEXT`             |                                                                       |
    | `medio_url_principal`          | `medio_url_principal`                                       | `TEXT`             |                                                                       |
    | `pais_publicacion`             | `pais_publicacion`                                          | `TEXT`             |                                                                       |
    | `tipo_medio`                   | `tipo_medio`                                                | `TEXT`             |                                                                       |
    | `titular`                      | `titular`                                                   | `TEXT`             |                                                                       |
    | `fecha_publicacion`            | `fecha_publicacion`                                         | `TIMESTAMPTZ`      |                                                                       |
    | `autor`                        | `autor`                                                     | `TEXT`             |                                                                       |
    | `idioma_original`              | `idioma_original`                                           | `VARCHAR(10)`      |                                                                       |
    | `seccion`                      | `seccion`                                                   | `TEXT`             |                                                                       |
    | `etiquetas_fuente`             | `etiquetas_fuente`                                          | `TEXT[]`           | Array de strings.                                                     |
    | `es_opinion`                   | `es_opinion`                                                | `BOOLEAN`          |                                                                       |
    | `es_oficial`                   | `es_oficial`                                                | `BOOLEAN`          |                                                                       |
    | `contenido_texto_original`     | `contenido_texto_original`                                  | `TEXT`             |                                                                       |
    | `contenido_html_original`      | `contenido_html_original`                                   | `TEXT`             |                                                                       |
    | `metadata_original_json`       | `metadata_original`                                         | `JSONB`            |                                                                       |
    | `resumen_ia`                   | `resumen_generado`                                          | `TEXT`             |                                                                       |
    | `categorias_ia`                | `categorias_asignadas_ia`                                   | `TEXT[]`           | Array de strings.                                                     |
    | `keywords_ia`                  | `palabras_clave_ia`                                         | `TEXT[]`           | Array de strings.                                                     |
    | `idioma_ia`                    | `idioma_detectado_ia`                                       | `VARCHAR(10)`      |                                                                       |
    | `sentimiento_general_ia`       | `sentimiento_articulo.etiqueta`                             | `TEXT`             |                                                                       |
    | `sentimiento_puntuacion_ia`    | `sentimiento_articulo.puntuacion`                           | `REAL`             |                                                                       |
    | `relevancia_ia`                | `puntuacion_relevancia_ia`                                  | `REAL`             |                                                                       |
    | `estado_procesamiento_pipeline`| `estado_procesamiento_final`                                | `VARCHAR(50)`      |                                                                       |
    | `fecha_procesamiento_pipeline` | `fecha_procesamiento_pipeline`                              | `TIMESTAMPTZ`      |                                                                       |
    | `error_procesamiento_detalle`  | `error_detalle_pipeline`                                    | `TEXT`             |                                                                       |
    | `embedding`                    | `embedding_articulo_vector`                                 | `vector`           | (Asumiendo uso de pgvector). Generado por trigger o en la misma RPC. |
    | `fecha_creacion`               | (Generado por la BD, `DEFAULT now()`)                       | `TIMESTAMPTZ`      |                                                                       |
    | `fecha_actualizacion`          | (Generado por la BD, `DEFAULT now()`, actualizado por trigger)| `TIMESTAMPTZ`      |                                                                       |
    | `documento_extenso_id`         | (N/A para `insertar_articulo_completo`)                     | `BIGINT`           | `NULL` para artículos. FK a `documentos_extensos`.                    |

### 2.2. Tabla: `fragmentos`

*   **Propósito:** Almacena la información de cada fragmento individual procesado de un documento extenso.
*   **Poblada por RPC:** `insertar_fragmento_completo`
*   **Mapeo de Campos desde `p_fragmento_data` y Parámetros RPC:**

    | Columna en `fragmentos`        | Campo en `p_fragmento_data` / Parámetro RPC                 | Tipo de Dato (SQL) | Notas                                                                 |
    |--------------------------------|-------------------------------------------------------------|--------------------|-----------------------------------------------------------------------|
    | `id`                           | (Generado por la BD)                                        | `BIGSERIAL`        | Clave primaria.                                                       |
    | `documento_extenso_id`         | `p_documento_id` (parámetro de la RPC)                      | `BIGINT`           | FK a `documentos_extensos.id`. No nulo.                               |
    | `indice_secuencial`            | `indice_secuencial_fragmento`                               | `INTEGER`          |                                                                       |
    | `titulo_seccion`               | `titulo_seccion_fragmento`                                  | `TEXT`             |                                                                       |
    | `contenido_texto_original`     | `contenido_texto_original_fragmento`                        | `TEXT`             |                                                                       |
    | `num_pagina_inicio`            | `num_pagina_inicio_fragmento`                               | `INTEGER`          |                                                                       |
    | `num_pagina_fin`               | `num_pagina_fin_fragmento`                                  | `INTEGER`          |                                                                       |
    | `resumen_ia`                   | `resumen_generado_fragmento`                                | `TEXT`             |                                                                       |
    | `estado_procesamiento_pipeline`| `estado_procesamiento_final_fragmento`                      | `VARCHAR(50)`      |                                                                       |
    | `fecha_procesamiento_pipeline` | `fecha_procesamiento_pipeline_fragmento`                    | `TIMESTAMPTZ`      |                                                                       |
    | `embedding`                    | (Análogo a `articulos.embedding`, para el fragmento)        | `vector`           |                                                                       |
    | `fecha_creacion`               | (Generado por la BD, `DEFAULT now()`)                       | `TIMESTAMPTZ`      |                                                                       |
    | `fecha_actualizacion`          | (Generado por la BD, `DEFAULT now()`, actualizado por trigger)| `TIMESTAMPTZ`      |                                                                       |

    *Nota: Los elementos estructurados extraídos del fragmento (hechos, entidades, etc.) se vinculan a `fragmentos.id` de manera similar a como se vinculan con `articulos.id`.*

### 2.3. Tabla: `hechos`

*   **Propósito:** Almacena cada hecho individual extraído de un artículo o fragmento.
*   **Poblada por RPC:** `insertar_articulo_completo`, `insertar_fragmento_completo` (a través del array `hechos_extraidos`).
*   **Mapeo de Campos desde `p_articulo_data.hechos_extraidos[]` o `p_fragmento_data.hechos_extraidos[]`:**

    | Columna en `hechos`            | Campo en `hechos_extraidos[]`                               | Tipo de Dato (SQL) | Notas                                                                 |
    |--------------------------------|-------------------------------------------------------------|--------------------|-----------------------------------------------------------------------|
    | `id`                           | (Generado por la BD)                                        | `BIGSERIAL`        | Clave primaria.                                                       |
    | `articulo_id`                  | ID del artículo recién insertado (si aplica)                | `BIGINT`           | FK a `articulos.id`. Nulable.                                         |
    | `fragmento_id`                 | ID del fragmento recién insertado (si aplica)               | `BIGINT`           | FK a `fragmentos.id`. Nulable.                                        |
    | `descripcion_hecho`            | `descripcion_hecho`                                         | `TEXT`             |                                                                       |
    | `fecha_ocurrencia_estimada`    | `fecha_ocurrencia_estimada`                                 | `TIMESTAMPTZ`      |                                                                       |
    | `lugar_principal_ocurrencia`   | `lugar_principal_ocurrencia`                                | `TEXT`             | (Podría ser `JSONB` si la estructura es más compleja)                 |
    | `tipo_hecho`                   | `tipo_hecho`                                                | `TEXT`             |                                                                       |
    | `relevancia_hecho`             | `relevancia_hecho`                                          | `INTEGER`          |                                                                       |
    | `contexto_adicional`           | `contexto_adicional_hecho`                                  | `TEXT`             |                                                                       |
    | `detalle_complejo_json`        | `detalle_complejo_hecho`                                    | `JSONB`            |                                                                       |
    | `embedding`                    | `embedding_hecho_vector`                                    | `vector`           |                                                                       |
    | `id_temporal_payload`          | `id_temporal_hecho`                                         | `TEXT`             | Almacenado para referencia/trazabilidad si es necesario.            |
    | `fecha_creacion`               | (Generado por la BD)                                        | `TIMESTAMPTZ`      |                                                                       |

### 2.4. Tabla: `entidades`

*   **Propósito:** Almacena información sobre entidades únicas (personas, organizaciones, lugares, etc.) extraídas. Se busca evitar duplicados mediante `cache_entidades` y lógica en la RPC o triggers.
*   **Poblada por RPC:** `insertar_articulo_completo`, `insertar_fragmento_completo` (a través de los arrays `hechos_extraidos[].entidades_del_hecho[]` y `entidades_autonomas[]`).
*   **Mapeo de Campos (ejemplo para una entidad proveniente de `entidades_autonomas[]`):**

    | Columna en `entidades`         | Campo en `entidades_autonomas[]` o `entidades_del_hecho[]`    | Tipo de Dato (SQL) | Notas                                                                 |
    |--------------------------------|-------------------------------------------------------------|--------------------|-----------------------------------------------------------------------|
    | `id`                           | (Generado por la BD o resuelto desde `cache_entidades`)     | `BIGSERIAL`        | Clave primaria.                                                       |
    | `nombre_entidad`               | `nombre_entidad`                                            | `TEXT`             |                                                                       |
    | `tipo_entidad`                 | `tipo_entidad`                                              | `VARCHAR(50)`      |                                                                       |
    | `subtipo_entidad`              | `subtipo_entidad`                                           | `VARCHAR(50)`      |                                                                       |
    | `metadata_json`                | `metadata_entidad` (de `entidades_autonomas`)               | `JSONB`            |                                                                       |
    | `embedding`                    | `embedding_entidad_vector` (de `entidades_autonomas`)       | `vector`           |                                                                       |
    | `fecha_creacion`               | (Generado por la BD)                                        | `TIMESTAMPTZ`      |                                                                       |
    | `fecha_actualizacion`          | (Actualizado por trigger o lógica RPC)                      | `TIMESTAMPTZ`      |                                                                       |

    *Nota: La inserción en `entidades` probablemente involucre una lógica de "upsert" o verificación contra `cache_entidades` para obtener/crear el `entidad_id` único.*

### 2.5. Tabla: `hecho_entidad`

*   **Propósito:** Tabla de unión para la relación muchos-a-muchos entre `hechos` y `entidades`.
*   **Poblada por RPC:** `insertar_articulo_completo`, `insertar_fragmento_completo` (iterando sobre `hechos_extraidos[].entidades_del_hecho[]`).
*   **Mapeo de Campos:**

    | Columna en `hecho_entidad`     | Origen del Dato                                             | Tipo de Dato (SQL) | Notas                                                                 |
    |--------------------------------|-------------------------------------------------------------|--------------------|-----------------------------------------------------------------------|
    | `hecho_id`                     | ID del hecho recién insertado (FK a `hechos.id`)            | `BIGINT`           |                                                                       |
    | `entidad_id`                   | ID de la entidad resuelta/insertada (FK a `entidades.id`)   | `BIGINT`           |                                                                       |
    | `rol_en_hecho`                 | `entidades_del_hecho[].rol_en_hecho`                         | `TEXT`             |                                                                       |
    | `relevancia_entidad_en_hecho`  | `entidades_del_hecho[].relevancia_entidad_en_hecho`          | `INTEGER`          |                                                                       |
    | `id_temporal_hecho_payload`    | `hechos_extraidos[].id_temporal_hecho`                      | `TEXT`             | Para referencia.                                                      |
    | `id_temporal_entidad_payload`  | `entidades_del_hecho[].id_temporal_entidad`                 | `TEXT`             | Para referencia.                                                      |
    | `fecha_creacion`               | (Generado por la BD)                                        | `TIMESTAMPTZ`      |                                                                       |

    *Clave Primaria Compuesta: (`hecho_id`, `entidad_id`, `rol_en_hecho`) o similar para permitir múltiples roles de una entidad en un hecho.*

### 2.6. Tabla: `hecho_articulo` (o `hecho_fuente_contenido`)

*   **Propósito:** Tabla de unión para la relación muchos-a-muchos entre `hechos` y su fuente de contenido (`articulos` o `fragmentos`).
*   **Poblada por RPC:** `insertar_articulo_completo`, `insertar_fragmento_completo`.
*   **Mapeo de Campos:**

    | Columna                        | Origen del Dato                                             | Tipo de Dato (SQL) | Notas                                                                 |
    |--------------------------------|-------------------------------------------------------------|--------------------|-----------------------------------------------------------------------|
    | `hecho_id`                     | ID del hecho recién insertado (FK a `hechos.id`)            | `BIGINT`           |                                                                       |
    | `articulo_id`                  | ID del artículo recién insertado (FK a `articulos.id`)      | `BIGINT`           | Nulable.                                                              |
    | `fragmento_id`                 | ID del fragmento recién insertado (FK a `fragmentos.id`)    | `BIGINT`           | Nulable.                                                              |
    | `fecha_creacion`               | (Generado por la BD)                                        | `TIMESTAMPTZ`      |                                                                       |

    *Nota: Debe haber una restricción `CHECK` para asegurar que solo `articulo_id` o `fragmento_id` esté poblado, pero no ambos.*

### 2.7. Tabla: `citas_textuales`

*   **Propósito:** Almacena las citas textuales extraídas.
*   **Poblada por RPC:** `insertar_articulo_completo`, `insertar_fragmento_completo` (a través del array `citas_textuales_extraidas[]`).
*   **Mapeo de Campos:**

    | Columna en `citas_textuales`   | Campo en `citas_textuales_extraidas[]`                      | Tipo de Dato (SQL) | Notas                                                                 |
    |--------------------------------|-------------------------------------------------------------|--------------------|-----------------------------------------------------------------------|
    | `id`                           | (Generado por la BD)                                        | `BIGSERIAL`        | Clave primaria.                                                       |
    | `articulo_id`                  | ID del artículo (si aplica)                                 | `BIGINT`           | FK a `articulos.id`. Nulable.                                         |
    | `fragmento_id`                 | ID del fragmento (si aplica)                                | `BIGINT`           | FK a `fragmentos.id`. Nulable.                                        |
    | `texto_cita`                   | `texto_cita`                                                | `TEXT`             |                                                                       |
    | `persona_citada_nombre`        | `persona_citada`                                            | `TEXT`             |                                                                       |
    | `persona_citada_entidad_id`    | (ID resuelto de `entidades` si `persona_citada` es una entidad conocida) | `BIGINT`    | FK a `entidades.id`. Nulable.                                         |
    | `cargo_persona_citada`         | `cargo_persona_citada`                                      | `TEXT`             |                                                                       |
    | `fecha_cita`                   | `fecha_cita`                                                | `TIMESTAMPTZ`      |                                                                       |
    | `contexto_cita`                | `contexto_cita`                                             | `TEXT`             |                                                                       |
    | `relevancia_cita`              | `relevancia_cita`                                           | `INTEGER`          |                                                                       |
    | `hecho_principal_relacionado_id`| (ID resuelto de `hechos` a partir de `hecho_principal_relacionado_id_temporal`) | `BIGINT` | FK a `hechos.id`. Nulable.                                       |
    | `id_temporal_payload`          | `id_temporal_cita`                                          | `TEXT`             |                                                                       |
    | `fecha_creacion`               | (Generado por la BD)                                        | `TIMESTAMPTZ`      |                                                                       |

### 2.8. Tabla: `datos_cuantitativos`

*   **Propósito:** Almacena datos numéricos o cuantitativos estructurados extraídos.
*   **Poblada por RPC:** `insertar_articulo_completo`, `insertar_fragmento_completo` (a través del array `datos_cuantitativos_extraidos[]`).
*   **Mapeo de Campos:**

    | Columna en `datos_cuantitativos`| Campo en `datos_cuantitativos_extraidos[]`                  | Tipo de Dato (SQL) | Notas                                                                 |
    |--------------------------------|-------------------------------------------------------------|--------------------|-----------------------------------------------------------------------|
    | `id`                           | (Generado por la BD)                                        | `BIGSERIAL`        | Clave primaria.                                                       |
    | `articulo_id`                  | ID del artículo (si aplica)                                 | `BIGINT`           | FK a `articulos.id`. Nulable.                                         |
    | `fragmento_id`                 | ID del fragmento (si aplica)                                | `BIGINT`           | FK a `fragmentos.id`. Nulable.                                        |
    | `descripcion_dato`             | `descripcion_dato`                                          | `TEXT`             |                                                                       |
    | `valor_dato_numerico`          | `valor_dato` (si es numérico)                               | `NUMERIC`          |                                                                       |
    | `valor_dato_texto`             | `valor_dato` (si es texto)                                  | `TEXT`             | (Usar una u otra columna según el tipo)                               |
    | `unidad_dato`                  | `unidad_dato`                                               | `TEXT`             |                                                                       |
    | `fecha_dato`                   | `fecha_dato`                                                | `TIMESTAMPTZ`      |                                                                       |
    | `fuente_especifica_dato`       | `fuente_especifica_dato`                                    | `TEXT`             |                                                                       |
    | `contexto_dato`                | `contexto_dato`                                             | `TEXT`             |                                                                       |
    | `relevancia_dato`              | `relevancia_dato`                                           | `INTEGER`          |                                                                       |
    | `hecho_principal_relacionado_id`| (ID resuelto de `hechos` a partir de `hecho_principal_relacionado_id_temporal`) | `BIGINT` | FK a `hechos.id`. Nulable.                                       |
    | `id_temporal_payload`          | `id_temporal_dato`                                          | `TEXT`             |                                                                       |
    | `fecha_creacion`               | (Generado por la BD)                                        | `TIMESTAMPTZ`      |                                                                       |

### 2.9. Tabla: `relaciones_hechos`

*   **Propósito:** Almacena relaciones identificadas entre diferentes hechos.
*   **Poblada por RPC:** `insertar_articulo_completo`, `insertar_fragmento_completo` (a través del array `relaciones_hechos[]`).
*   **Mapeo de Campos:**

    | Columna en `relaciones_hechos` | Campo en `relaciones_hechos[]`                              | Tipo de Dato (SQL) | Notas                                                                 |
    |--------------------------------|-------------------------------------------------------------|--------------------|-----------------------------------------------------------------------|
    | `id`                           | (Generado por la BD)                                        | `BIGSERIAL`        | Clave primaria.                                                       |
    | `hecho_origen_id`              | (ID resuelto de `hechos` a partir de `hecho_origen_id_temporal`)| `BIGINT`           | FK a `hechos.id`.                                                     |
    | `hecho_destino_id`             | (ID resuelto de `hechos` a partir de `hecho_destino_id_temporal`)| `BIGINT`           | FK a `hechos.id`.                                                     |
    | `tipo_relacion`                | `tipo_relacion`                                             | `TEXT`             |                                                                       |
    | `fuerza_relacion`              | `fuerza_relacion`                                           | `INTEGER`          |                                                                       |
    | `descripcion_relacion`         | `descripcion_relacion`                                      | `TEXT`             |                                                                       |
    | `articulo_id`                  | ID del artículo (si aplica, para contexto)                  | `BIGINT`           | FK a `articulos.id`. Nulable.                                         |
    | `fragmento_id`                 | ID del fragmento (si aplica, para contexto)                 | `BIGINT`           | FK a `fragmentos.id`. Nulable.                                        |
    | `fecha_creacion`               | (Generado por la BD)                                        | `TIMESTAMPTZ`      |                                                                       |

### 2.10. Tabla: `relaciones_entidades`

*   **Propósito:** Almacena relaciones identificadas entre diferentes entidades.
*   **Poblada por RPC:** `insertar_articulo_completo`, `insertar_fragmento_completo` (a través del array `relaciones_entidades[]`).
*   **Mapeo de Campos:**

    | Columna en `relaciones_entidades` | Campo en `relaciones_entidades[]`                           | Tipo de Dato (SQL) | Notas                                                                 |
    |-----------------------------------|-------------------------------------------------------------|--------------------|-----------------------------------------------------------------------|
    | `id`                              | (Generado por la BD)                                        | `BIGSERIAL`        | Clave primaria.                                                       |
    | `entidad_origen_id`             | (ID resuelto de `entidades` a partir de `entidad_origen_id_temporal`)| `BIGINT`       | FK a `entidades.id`.                                                  |
    | `entidad_destino_id`            | (ID resuelto de `entidades` a partir de `entidad_destino_id_temporal`)| `BIGINT`       | FK a `entidades.id`.                                                  |
    | `tipo_relacion`                   | `tipo_relacion`                                             | `TEXT`             |                                                                       |
    | `descripcion_relacion`            | `descripcion_relacion`                                      | `TEXT`             |                                                                       |
    | `fecha_inicio_relacion`           | `fecha_inicio_relacion`                                     | `TIMESTAMPTZ`      |                                                                       |
    | `fecha_fin_relacion`              | `fecha_fin_relacion`                                        | `TIMESTAMPTZ`      |                                                                       |
    | `fuerza_relacion`                 | `fuerza_relacion`                                           | `INTEGER`          |                                                                       |
    | `articulo_id`                     | ID del artículo (si aplica, para contexto)                  | `BIGINT`           | FK a `articulos.id`. Nulable.                                         |
    | `fragmento_id`                    | ID del fragmento (si aplica, para contexto)                 | `BIGINT`           | FK a `fragmentos.id`. Nulable.                                        |
    | `fecha_creacion`                  | (Generado por la BD)                                        | `TIMESTAMPTZ`      |                                                                       |

### 2.11. Tabla: `contradicciones`

*   **Propósito:** Almacena contradicciones identificadas entre hechos.
*   **Poblada por RPC:** `insertar_articulo_completo`, `insertar_fragmento_completo` (a través del array `contradicciones_detectadas[]`).
*   **Mapeo de Campos:**

    | Columna en `contradicciones`   | Campo en `contradicciones_detectadas[]`                     | Tipo de Dato (SQL) | Notas                                                                 |
    |--------------------------------|-------------------------------------------------------------|--------------------|-----------------------------------------------------------------------|
    | `id`                           | (Generado por la BD)                                        | `BIGSERIAL`        | Clave primaria.                                                       |
    | `hecho_principal_id`           | (ID resuelto de `hechos` a partir de `hecho_principal_id_temporal`)| `BIGINT`       | FK a `hechos.id`.                                                     |
    | `hecho_contradictorio_id`      | (ID resuelto de `hechos` a partir de `hecho_contradictorio_id_temporal`)| `BIGINT`   | FK a `hechos.id`.                                                     |
    | `tipo_contradiccion`           | `tipo_contradiccion`                                        | `TEXT`             |                                                                       |
    | `grado_contradiccion`          | `grado_contradiccion`                                       | `INTEGER`          |                                                                       |
    | `descripcion_contradiccion`    | `descripcion_contradiccion`                                 | `TEXT`             |                                                                       |
    | `articulo_id`                  | ID del artículo (si aplica, para contexto)                  | `BIGINT`           | FK a `articulos.id`. Nulable.                                         |
    | `fragmento_id`                 | ID del fragmento (si aplica, para contexto)                 | `BIGINT`           | FK a `fragmentos.id`. Nulable.                                        |
    | `fecha_creacion`               | (Generado por la BD)                                        | `TIMESTAMPTZ`      |                                                                       |
