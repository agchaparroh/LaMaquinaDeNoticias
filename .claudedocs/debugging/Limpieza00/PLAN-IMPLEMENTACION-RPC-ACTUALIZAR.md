# Plan de Implementación: RPC actualizar_articulo_procesado

## Objetivo

Resolver el conflicto entre el scraper y el pipeline creando un nuevo RPC que respete la separación de responsabilidades del sistema.

## Problema Actual

- El scraper inserta artículos nuevos en la base de datos usando `upsert` directo
- El pipeline intenta insertar el mismo artículo usando RPC `insertar_articulo_completo`
- La RPC falla porque el artículo ya existe (violación de constraint UNIQUE)
- El mismatch estructural entre lo que genera el pipeline y lo que espera la RPC

## Solución Propuesta

Crear un nuevo RPC `actualizar_articulo_procesado` específico para el pipeline que:
- Actualice artículos existentes (no inserte nuevos)
- Use el ID del artículo como identificador principal
- Tenga fallback a URL si es necesario
- Solo modifique campos del procesamiento
- Inserte los elementos extraídos (hechos, entidades, etc.)

## Implementación Detallada

### 1. Crear el RPC en Supabase

#### Archivo: `actualizar_articulo_procesado.sql`

```sql
CREATE OR REPLACE FUNCTION actualizar_articulo_procesado(datos_json JSONB)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    -- Variables principales
    v_articulo_id BIGINT;
    v_url TEXT;
    
    -- IDs generados para elementos
    v_hecho_id BIGINT;
    v_entidad_id BIGINT;
    v_cita_id BIGINT;
    v_dato_id BIGINT;
    v_fecha_ocurrencia_hecho TSTZRANGE;
    
    -- Elementos iterables
    v_hecho JSONB;
    v_entidad JSONB;
    v_cita JSONB;
    v_dato JSONB;
    v_relacion JSONB;
    
    -- Contadores
    v_num_hechos_insertados INT := 0;
    v_num_entidades_insertadas INT := 0;
    v_num_entidades_nuevas INT := 0;
    v_num_citas_insertadas INT := 0;
    v_num_datos_insertados INT := 0;
    v_num_relaciones_insertadas INT := 0;
    
    -- Mapeo de IDs temporales
    temp_hecho_id_map HSTORE := ''::HSTORE;
    temp_entidad_id_map HSTORE := ''::HSTORE;
    
BEGIN
    -- 1. Obtener el artículo a actualizar
    -- Primero intentar por ID (más eficiente)
    v_articulo_id := (datos_json->>'articulo_id')::BIGINT;
    v_url := datos_json->>'url';
    
    -- Si tenemos ID, verificar que existe
    IF v_articulo_id IS NOT NULL THEN
        IF NOT EXISTS (SELECT 1 FROM articulos WHERE id = v_articulo_id) THEN
            -- ID no válido, intentar por URL
            v_articulo_id := NULL;
        END IF;
    END IF;
    
    -- Si no tenemos ID válido, buscar por URL
    IF v_articulo_id IS NULL AND v_url IS NOT NULL THEN
        SELECT id INTO v_articulo_id 
        FROM articulos 
        WHERE url = v_url;
    END IF;
    
    -- Si no encontramos el artículo, error
    IF v_articulo_id IS NULL THEN
        RETURN jsonb_build_object(
            'status', 'error',
            'mensaje', 'Artículo no encontrado. Se requiere articulo_id o url válidos',
            'codigo_sql', 'NOT_FOUND'
        );
    END IF;
    
    -- 2. Actualizar campos del procesamiento en el artículo
    UPDATE articulos SET
        -- Campos del procesamiento
        estado_procesamiento = 'completado',
        fecha_procesamiento = now(),
        
        -- Resultados del pipeline
        resumen = datos_json->>'resumen_generado_pipeline',
        categorias_asignadas = CASE 
            WHEN datos_json ? 'categorias_asignadas_ia' 
            THEN ARRAY(SELECT jsonb_array_elements_text(datos_json->'categorias_asignadas_ia'))
            ELSE NULL 
        END,
        puntuacion_relevancia = (datos_json->>'score_relevancia')::INTEGER,
        
        -- Embeddings si vienen
        embedding_articulo = CASE
            WHEN datos_json ? 'embedding_articulo_vector'
            THEN (datos_json->>'embedding_articulo_vector')::vector
            ELSE embedding_articulo
        END,
        
        -- Metadata adicional del procesamiento
        metadata_procesamiento = jsonb_build_object(
            'version_pipeline', datos_json->>'version_pipeline_aplicada',
            'palabras_clave_ia', datos_json->'palabras_clave_ia',
            'sentimiento_general', datos_json->>'sentimiento_general_articulo',
            'fecha_procesamiento_pipeline', datos_json->>'fecha_procesamiento_pipeline'
        )
        
    WHERE id = v_articulo_id;
    
    -- 3. Procesar e insertar entidades
    IF datos_json ? 'entidades_autonomas' THEN
        FOR v_entidad IN SELECT * FROM jsonb_array_elements(datos_json->'entidades_autonomas')
        LOOP
            -- Verificar si ya existe por db_id
            IF v_entidad ? 'db_id' AND v_entidad->>'db_id' IS NOT NULL THEN
                v_entidad_id := (v_entidad->>'db_id')::BIGINT;
                v_num_entidades_insertadas := v_num_entidades_insertadas + 1;
            ELSE
                -- Insertar nueva entidad
                INSERT INTO entidades (
                    nombre,
                    tipo,
                    descripcion,
                    alias,
                    relevancia,
                    metadata
                )
                VALUES (
                    v_entidad->>'nombre_entidad',
                    v_entidad->>'tipo_entidad',
                    v_entidad->>'descripcion_entidad',
                    CASE 
                        WHEN v_entidad ? 'alias' 
                        THEN ARRAY(SELECT jsonb_array_elements_text(v_entidad->'alias'))
                        ELSE NULL 
                    END,
                    COALESCE((v_entidad->>'relevancia_entidad')::INTEGER, 5),
                    v_entidad->'metadata_entidad'
                )
                RETURNING id INTO v_entidad_id;
                
                v_num_entidades_nuevas := v_num_entidades_nuevas + 1;
                v_num_entidades_insertadas := v_num_entidades_insertadas + 1;
            END IF;
            
            -- Mapear ID temporal
            temp_entidad_id_map := temp_entidad_id_map || 
                hstore((v_entidad->>'id_temporal_entidad')::TEXT, v_entidad_id::TEXT);
        END LOOP;
    END IF;
    
    -- 4. Procesar e insertar hechos
    IF datos_json ? 'hechos_extraidos' THEN
        FOR v_hecho IN SELECT * FROM jsonb_array_elements(datos_json->'hechos_extraidos')
        LOOP
            -- Construir fecha de ocurrencia
            v_fecha_ocurrencia_hecho := tstzrange(
                CASE 
                    WHEN v_hecho ? 'fecha_ocurrencia_hecho_inicio' 
                    THEN (v_hecho->>'fecha_ocurrencia_hecho_inicio')::TIMESTAMPTZ
                    ELSE (SELECT fecha_publicacion FROM articulos WHERE id = v_articulo_id)
                END,
                CASE 
                    WHEN v_hecho ? 'fecha_ocurrencia_hecho_fin' 
                    THEN (v_hecho->>'fecha_ocurrencia_hecho_fin')::TIMESTAMPTZ
                    ELSE (SELECT fecha_publicacion FROM articulos WHERE id = v_articulo_id)
                END
            );
            
            -- Insertar hecho
            INSERT INTO hechos (
                contenido,
                fecha_ocurrencia,
                tipo_hecho,
                importancia,
                pais,
                region,
                ciudad,
                etiquetas,
                fecha_ingreso
            )
            VALUES (
                v_hecho->>'descripcion_hecho',
                v_fecha_ocurrencia_hecho,
                COALESCE(v_hecho->>'tipo_hecho', 'evento'),
                COALESCE((v_hecho->>'relevancia_hecho')::INTEGER, 5),
                CASE 
                    WHEN v_hecho->'metadata_hecho' ? 'pais' 
                    THEN ARRAY(SELECT jsonb_array_elements_text(v_hecho->'metadata_hecho'->'pais'))
                    ELSE ARRAY[]::VARCHAR[] 
                END,
                CASE 
                    WHEN v_hecho->'metadata_hecho' ? 'region' 
                    THEN ARRAY(SELECT jsonb_array_elements_text(v_hecho->'metadata_hecho'->'region'))
                    ELSE NULL 
                END,
                CASE 
                    WHEN v_hecho->'metadata_hecho' ? 'ciudad' 
                    THEN ARRAY(SELECT jsonb_array_elements_text(v_hecho->'metadata_hecho'->'ciudad'))
                    ELSE NULL 
                END,
                CASE 
                    WHEN v_hecho->'metadata_hecho' ? 'etiquetas' 
                    THEN ARRAY(SELECT jsonb_array_elements_text(v_hecho->'metadata_hecho'->'etiquetas'))
                    ELSE NULL 
                END,
                now()
            )
            RETURNING id INTO v_hecho_id;
            
            -- Insertar relación hecho-artículo
            INSERT INTO hecho_articulo (
                hecho_id,
                fecha_ocurrencia_hecho,
                articulo_id,
                es_fuente_primaria,
                confirma_hecho
            )
            VALUES (
                v_hecho_id,
                v_fecha_ocurrencia_hecho,
                v_articulo_id,
                true,
                true
            );
            
            -- Mapear ID temporal
            temp_hecho_id_map := temp_hecho_id_map || 
                hstore((v_hecho->>'id_temporal_hecho')::TEXT, v_hecho_id::TEXT);
            
            v_num_hechos_insertados := v_num_hechos_insertados + 1;
            
            -- Procesar entidades del hecho
            IF v_hecho ? 'entidades_del_hecho' THEN
                FOR v_entidad IN SELECT * FROM jsonb_array_elements(v_hecho->'entidades_del_hecho')
                LOOP
                    -- Obtener ID real de la entidad
                    v_entidad_id := (temp_entidad_id_map->(v_entidad->>'id_temporal_entidad'))::BIGINT;
                    
                    IF v_entidad_id IS NOT NULL THEN
                        -- Insertar relación hecho-entidad
                        INSERT INTO hecho_entidad (
                            hecho_id,
                            fecha_ocurrencia_hecho,
                            entidad_id,
                            tipo_relacion,
                            relevancia_en_hecho
                        )
                        VALUES (
                            v_hecho_id,
                            v_fecha_ocurrencia_hecho,
                            v_entidad_id,
                            COALESCE(v_entidad->>'tipo_relacion', 'mencionada'),
                            COALESCE((v_entidad->>'relevancia_en_hecho')::INTEGER, 5)
                        )
                        ON CONFLICT (hecho_id, fecha_ocurrencia_hecho, entidad_id, tipo_relacion) 
                        DO NOTHING;
                        
                        v_num_relaciones_insertadas := v_num_relaciones_insertadas + 1;
                    END IF;
                END LOOP;
            END IF;
        END LOOP;
    END IF;
    
    -- 5. Procesar citas textuales
    IF datos_json ? 'citas_textuales_extraidas' THEN
        FOR v_cita IN SELECT * FROM jsonb_array_elements(datos_json->'citas_textuales_extraidas')
        LOOP
            -- Obtener IDs reales
            v_entidad_id := NULL;
            IF v_cita ? 'id_temporal_entidad_emisora' THEN
                v_entidad_id := (temp_entidad_id_map->(v_cita->>'id_temporal_entidad_emisora'))::BIGINT;
            END IF;
            
            v_hecho_id := NULL;
            IF v_cita ? 'id_temporal_hecho_principal' THEN
                v_hecho_id := (temp_hecho_id_map->(v_cita->>'id_temporal_hecho_principal'))::BIGINT;
            END IF;
            
            -- Insertar cita
            INSERT INTO citas_textuales (
                cita,
                entidad_emisora_id,
                articulo_id,
                hecho_contexto_id,
                fecha_cita,
                contexto,
                relevancia
            )
            VALUES (
                v_cita->>'texto_cita',
                v_entidad_id,
                v_articulo_id,
                v_hecho_id,
                CASE 
                    WHEN v_cita ? 'fecha_cita' 
                    THEN (v_cita->>'fecha_cita')::TIMESTAMPTZ
                    ELSE (SELECT fecha_publicacion FROM articulos WHERE id = v_articulo_id)
                END,
                v_cita->>'contexto_cita',
                COALESCE((v_cita->>'relevancia_cita')::INTEGER, 3)
            );
            
            v_num_citas_insertadas := v_num_citas_insertadas + 1;
        END LOOP;
    END IF;
    
    -- 6. Procesar datos cuantitativos
    IF datos_json ? 'datos_cuantitativos_extraidos' THEN
        FOR v_dato IN SELECT * FROM jsonb_array_elements(datos_json->'datos_cuantitativos_extraidos')
        LOOP
            -- Obtener ID real del hecho relacionado
            v_hecho_id := NULL;
            IF v_dato ? 'id_temporal_hecho_principal' THEN
                v_hecho_id := (temp_hecho_id_map->(v_dato->>'id_temporal_hecho_principal'))::BIGINT;
            END IF;
            
            -- Insertar dato cuantitativo
            INSERT INTO datos_cuantitativos (
                hecho_id,
                articulo_id,
                indicador,
                categoria,
                valor_numerico,
                unidad,
                periodo_referencia_inicio,
                periodo_referencia_fin,
                tendencia
            )
            VALUES (
                v_hecho_id,
                v_articulo_id,
                v_dato->>'indicador_dato',
                v_dato->>'categoria_dato',
                (v_dato->>'valor_dato')::NUMERIC,
                v_dato->>'unidad_dato',
                CASE 
                    WHEN v_dato ? 'periodo_inicio' 
                    THEN (v_dato->>'periodo_inicio')::DATE
                    ELSE NULL 
                END,
                CASE 
                    WHEN v_dato ? 'periodo_fin' 
                    THEN (v_dato->>'periodo_fin')::DATE
                    ELSE NULL 
                END,
                v_dato->>'tendencia_dato'
            );
            
            v_num_datos_insertados := v_num_datos_insertados + 1;
        END LOOP;
    END IF;
    
    -- 7. Procesar relaciones
    -- Relaciones hecho-hecho
    IF datos_json ? 'relaciones_hechos' THEN
        FOR v_relacion IN SELECT * FROM jsonb_array_elements(datos_json->'relaciones_hechos')
        LOOP
            DECLARE
                v_hecho_origen_id BIGINT;
                v_hecho_destino_id BIGINT;
                v_fecha_origen TSTZRANGE;
                v_fecha_destino TSTZRANGE;
            BEGIN
                -- Obtener IDs reales
                v_hecho_origen_id := (temp_hecho_id_map->(v_relacion->>'id_hecho_origen'))::BIGINT;
                v_hecho_destino_id := (temp_hecho_id_map->(v_relacion->>'id_hecho_destino'))::BIGINT;
                
                IF v_hecho_origen_id IS NOT NULL AND v_hecho_destino_id IS NOT NULL THEN
                    -- Obtener fechas
                    SELECT fecha_ocurrencia INTO v_fecha_origen 
                    FROM hechos WHERE id = v_hecho_origen_id;
                    
                    SELECT fecha_ocurrencia INTO v_fecha_destino 
                    FROM hechos WHERE id = v_hecho_destino_id;
                    
                    -- Insertar relación
                    INSERT INTO hecho_relacionado (
                        hecho_origen_id,
                        fecha_ocurrencia_origen,
                        hecho_destino_id,
                        fecha_ocurrencia_destino,
                        tipo_relacion,
                        fuerza_relacion,
                        descripcion_relacion
                    )
                    VALUES (
                        v_hecho_origen_id,
                        v_fecha_origen,
                        v_hecho_destino_id,
                        v_fecha_destino,
                        v_relacion->>'tipo_relacion',
                        COALESCE((v_relacion->>'fuerza_relacion')::INTEGER, 5),
                        v_relacion->>'descripcion_relacion'
                    )
                    ON CONFLICT DO NOTHING;
                    
                    v_num_relaciones_insertadas := v_num_relaciones_insertadas + 1;
                END IF;
            END;
        END LOOP;
    END IF;
    
    -- Relaciones entidad-entidad
    IF datos_json ? 'relaciones_entidades' THEN
        FOR v_relacion IN SELECT * FROM jsonb_array_elements(datos_json->'relaciones_entidades')
        LOOP
            DECLARE
                v_entidad_origen_id BIGINT;
                v_entidad_destino_id BIGINT;
            BEGIN
                -- Obtener IDs reales
                v_entidad_origen_id := (temp_entidad_id_map->(v_relacion->>'id_entidad_origen'))::BIGINT;
                v_entidad_destino_id := (temp_entidad_id_map->(v_relacion->>'id_entidad_destino'))::BIGINT;
                
                IF v_entidad_origen_id IS NOT NULL AND v_entidad_destino_id IS NOT NULL 
                   AND v_entidad_origen_id <> v_entidad_destino_id THEN
                    -- Insertar relación
                    INSERT INTO entidad_relacion (
                        entidad_origen_id,
                        entidad_destino_id,
                        tipo_relacion,
                        descripcion,
                        fuerza_relacion
                    )
                    VALUES (
                        v_entidad_origen_id,
                        v_entidad_destino_id,
                        v_relacion->>'tipo_relacion',
                        v_relacion->>'descripcion_relacion',
                        COALESCE((v_relacion->>'fuerza_relacion')::INTEGER, 5)
                    )
                    ON CONFLICT (entidad_origen_id, entidad_destino_id, tipo_relacion) 
                    DO NOTHING;
                    
                    v_num_relaciones_insertadas := v_num_relaciones_insertadas + 1;
                END IF;
            END;
        END LOOP;
    END IF;
    
    -- 8. Procesar contradicciones
    IF datos_json ? 'contradicciones_detectadas' THEN
        FOR v_relacion IN SELECT * FROM jsonb_array_elements(datos_json->'contradicciones_detectadas')
        LOOP
            DECLARE
                v_hecho_principal_id BIGINT;
                v_hecho_contradictorio_id BIGINT;
                v_fecha_principal TSTZRANGE;
                v_fecha_contradictoria TSTZRANGE;
            BEGIN
                -- Obtener IDs reales
                v_hecho_principal_id := (temp_hecho_id_map->(v_relacion->>'id_hecho_principal'))::BIGINT;
                v_hecho_contradictorio_id := (temp_hecho_id_map->(v_relacion->>'id_hecho_contradictorio'))::BIGINT;
                
                IF v_hecho_principal_id IS NOT NULL AND v_hecho_contradictorio_id IS NOT NULL THEN
                    -- Obtener fechas
                    SELECT fecha_ocurrencia INTO v_fecha_principal 
                    FROM hechos WHERE id = v_hecho_principal_id;
                    
                    SELECT fecha_ocurrencia INTO v_fecha_contradictoria 
                    FROM hechos WHERE id = v_hecho_contradictorio_id;
                    
                    -- Insertar contradicción
                    INSERT INTO contradicciones (
                        hecho_principal_id,
                        fecha_ocurrencia_principal,
                        hecho_contradictorio_id,
                        fecha_ocurrencia_contradictoria,
                        tipo_contradiccion,
                        grado_contradiccion,
                        descripcion
                    )
                    VALUES (
                        v_hecho_principal_id,
                        v_fecha_principal,
                        v_hecho_contradictorio_id,
                        v_fecha_contradictoria,
                        v_relacion->>'tipo_contradiccion',
                        COALESCE((v_relacion->>'grado_contradiccion')::INTEGER, 3),
                        v_relacion->>'descripcion_contradiccion'
                    );
                    
                    v_num_relaciones_insertadas := v_num_relaciones_insertadas + 1;
                END IF;
            END;
        END LOOP;
    END IF;
    
    -- Retornar resultado exitoso
    RETURN jsonb_build_object(
        'status', 'exito',
        'articulo_id', v_articulo_id,
        'hechos_insertados', v_num_hechos_insertados,
        'entidades_insertadas', v_num_entidades_insertadas,
        'entidades_nuevas', v_num_entidades_nuevas,
        'citas_insertadas', v_num_citas_insertadas,
        'datos_insertados', v_num_datos_insertados,
        'relaciones_insertadas', v_num_relaciones_insertadas
    );
    
EXCEPTION
    WHEN OTHERS THEN
        -- Capturar cualquier error
        RETURN jsonb_build_object(
            'status', 'error',
            'mensaje', SQLERRM,
            'codigo_sql', SQLSTATE,
            'articulo_id', v_articulo_id
        );
END;
$$;
```

### 2. Modificar el Pipeline

#### 2.1 Actualizar SupabaseService

En `src/module_pipeline/src/services/supabase_service.py`:

```python
@retry_supabase_rpc(connection_retries=1)
def actualizar_articulo_procesado(self, payload: Union[Dict[str, Any], BaseModel]) -> Optional[Dict[str, Any]]:
    """
    Llama a la RPC actualizar_articulo_procesado para actualizar un artículo existente
    con los resultados del procesamiento del pipeline.
    
    Args:
        payload: Diccionario con los datos del procesamiento.
                Debe incluir 'articulo_id' y/o 'url' para identificar el artículo.
        
    Returns:
        Dict con el resultado de la actualización o None si falla
        {
            "status": "exito",
            "articulo_id": int,
            "hechos_insertados": int,
            "entidades_insertadas": int,
            "citas_insertadas": int,
            "datos_insertados": int,
            "relaciones_insertadas": int
        }
        
    Raises:
        Exception: Si falla la llamada RPC después de los reintentos
    """
    try:
        self.logger.info("Llamando RPC actualizar_articulo_procesado")
        
        # Validar que tengamos al menos un identificador
        payload_dict = self._validar_estructura_payload(payload, 'articulo')
        
        if not payload_dict.get('articulo_id') and not payload_dict.get('url'):
            raise ValueError("Se requiere articulo_id o url para actualizar el artículo")
        
        # Log de identificadores
        if payload_dict.get('articulo_id'):
            self.logger.info(f"Actualizando artículo por ID: {payload_dict['articulo_id']}")
        else:
            self.logger.info(f"Actualizando artículo por URL: {payload_dict['url'][:50]}...")
        
        # Llamar RPC
        response = self.client.rpc(
            'actualizar_articulo_procesado',
            {'datos_json': payload_dict}
        ).execute()
        
        if response.data:
            result = response.data
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
            
            # Verificar estado
            if result.get('status') == 'error':
                self.logger.error(
                    f"Error en RPC: {result.get('mensaje')}. "
                    f"Código: {result.get('codigo_sql')}"
                )
                return None
            
            # Log de éxito
            self.logger.info(
                f"Artículo actualizado exitosamente. "
                f"ID: {result.get('articulo_id')}, "
                f"Hechos: {result.get('hechos_insertados', 0)}, "
                f"Entidades: {result.get('entidades_insertadas', 0)}, "
                f"Citas: {result.get('citas_insertadas', 0)}"
            )
            
            return result
        else:
            self.logger.warning("RPC actualizar_articulo_procesado no retornó datos")
            return None
            
    except Exception as e:
        self.logger.error(f"Error en actualizar_articulo_procesado: {e}")
        raise
```

#### 2.2 Modificar Controller

En `src/module_pipeline/src/controller.py`, método `_persistir_resultado_7_fases`:

```python
def _persistir_resultado_7_fases(
    self,
    resultado_pipeline: Dict[str, Any],
    tipo_contenido: str,
    supabase_service: SupabaseService
) -> Dict[str, Any]:
    """
    Persiste el resultado del procesamiento de las 7 fases en Supabase.
    
    Para artículos usa el nuevo RPC actualizar_articulo_procesado.
    Para fragmentos mantiene el comportamiento actual.
    """
    try:
        payload_dict = resultado_pipeline["payload"]
        
        # Detectar si es artículo o fragmento
        es_articulo = False
        articulo_id = None
        
        # ... (lógica de detección existente) ...
        
        if es_articulo:
            # CAMBIO: Usar nuevo RPC para artículos
            logger.info("Actualizando artículo procesado")
            
            # Asegurar que tenemos el ID del artículo
            if articulo_id:
                payload_dict["articulo_id"] = articulo_id
            
            # Asegurar que tenemos la URL (fallback)
            if "url" not in payload_dict and hasattr(self, '_current_article_url'):
                payload_dict["url"] = self._current_article_url
            
            # Llamar al nuevo RPC
            resultado_persistencia = supabase_service.actualizar_articulo_procesado(payload_dict)
            
        else:
            # Mantener comportamiento actual para fragmentos
            logger.info("Persistiendo como fragmento")
            resultado_persistencia = supabase_service.insertar_fragmento_completo(payload_dict)
        
        # Procesar resultado
        if resultado_persistencia:
            return {
                "exitosa": True,
                "articulo_id": resultado_persistencia.get('articulo_id'),
                "elementos_insertados": {
                    "hechos": resultado_persistencia.get('hechos_insertados', 0),
                    "entidades": resultado_persistencia.get('entidades_insertadas', 0),
                    "citas": resultado_persistencia.get('citas_insertadas', 0),
                    "datos": resultado_persistencia.get('datos_insertados', 0),
                    "relaciones": resultado_persistencia.get('relaciones_insertadas', 0)
                }
            }
        else:
            return {
                "exitosa": False,
                "mensaje": "La persistencia no retornó resultado"
            }
            
    except Exception as e:
        logger.error(f"Error en persistencia: {str(e)}")
        return {
            "exitosa": False,
            "mensaje": str(e)
        }
```

#### 2.3 Simplificaciones en PayloadBuilder (Opcional)

Dado que ya no necesitamos la estructura anidada compleja, podemos simplificar:

```python
def construir_payload_articulo_from_model(
    self,
    articulo_model: 'ArticuloProcesableItem',
    resultado_procesamiento: Dict[str, Any],
    # ... otros parámetros
) -> Dict[str, Any]:
    """
    Construye payload simplificado para actualizar_articulo_procesado.
    
    Ya no necesita:
    - Estructura anidada articulo_metadata
    - Campo storage_path
    - Validaciones complejas de RPC anterior
    """
    # Construir payload plano directamente
    payload = {
        # Identificadores
        "articulo_id": articulo_model.id_articulo,
        "url": articulo_model.url,
        
        # Resultados del procesamiento
        "resumen_generado_pipeline": resultado_procesamiento.get("resumen_generado_pipeline"),
        "categorias_asignadas_ia": resultado_procesamiento.get("categorias_asignadas_ia", []),
        "score_relevancia": resultado_procesamiento.get("score_relevancia"),
        "palabras_clave_ia": resultado_procesamiento.get("palabras_clave_generadas", []),
        "sentimiento_general_articulo": resultado_procesamiento.get("sentimiento_general_articulo"),
        "embedding_articulo_vector": resultado_procesamiento.get("embedding_articulo_vector"),
        "version_pipeline_aplicada": resultado_procesamiento.get("version_pipeline_aplicada"),
        "fecha_procesamiento_pipeline": resultado_procesamiento.get("fecha_procesamiento_pipeline"),
        
        # Elementos extraídos (ya vienen en el formato correcto)
        "hechos_extraidos": hechos_extraidos or [],
        "entidades_autonomas": entidades_extraidas or [],
        "citas_textuales_extraidas": citas_extraidas or [],
        "datos_cuantitativos_extraidos": datos_extraidos or [],
        "relaciones_hechos": relaciones_hechos or [],
        "relaciones_entidades": relaciones_entidades or [],
        "contradicciones_detectadas": contradicciones_detectadas or []
    }
    
    return payload
```

### 3. Pruebas

#### 3.1 Test Unitario para el RPC

```python
def test_actualizar_articulo_procesado():
    """Prueba el nuevo RPC actualizar_articulo_procesado."""
    
    # 1. Insertar artículo de prueba (simular scraper)
    articulo = supabase.table('articulos').insert({
        'url': 'https://test.com/noticia-prueba',
        'titular': 'Noticia de Prueba',
        'medio': 'Test Media',
        'storage_path': 'test/2025/01/19/hash.html.gz',
        'estado_procesamiento': 'pendiente'
    }).execute()
    
    articulo_id = articulo.data[0]['id']
    
    # 2. Preparar payload de actualización
    payload = {
        'articulo_id': articulo_id,
        'url': 'https://test.com/noticia-prueba',  # fallback
        'resumen_generado_pipeline': 'Resumen de prueba',
        'score_relevancia': 8,
        'hechos_extraidos': [{
            'id_temporal_hecho': 'h1',
            'descripcion_hecho': 'Hecho de prueba',
            'tipo_hecho': 'evento'
        }],
        'entidades_autonomas': [{
            'id_temporal_entidad': 'e1',
            'nombre_entidad': 'Entidad Prueba',
            'tipo_entidad': 'PERSONA'
        }]
    }
    
    # 3. Llamar RPC
    resultado = supabase.rpc('actualizar_articulo_procesado', {
        'datos_json': payload
    }).execute()
    
    # 4. Verificar resultado
    assert resultado.data['status'] == 'exito'
    assert resultado.data['articulo_id'] == articulo_id
    assert resultado.data['hechos_insertados'] == 1
    assert resultado.data['entidades_insertadas'] == 1
    
    # 5. Verificar actualización
    articulo_actualizado = supabase.table('articulos').select('*').eq(
        'id', articulo_id
    ).execute()
    
    assert articulo_actualizado.data[0]['estado_procesamiento'] == 'completado'
    assert articulo_actualizado.data[0]['resumen'] == 'Resumen de prueba'
    assert articulo_actualizado.data[0]['storage_path'] == 'test/2025/01/19/hash.html.gz'  # No modificado
```

#### 3.2 Test de Integración

```bash
# 1. Procesar artículo de prueba
curl -X POST http://localhost:8003/procesar_articulo \
  -H "Content-Type: application/json" \
  -d @test_article_relevante.json

# 2. Verificar resultado
curl http://localhost:8003/status/{job_id}

# 3. Verificar en base de datos
# - Artículo actualizado con estado 'completado'
# - Hechos insertados con relaciones
# - Entidades normalizadas
# - Citas y datos cuantitativos
```

### 4. Ventajas de esta Implementación

1. **Separación Clara de Responsabilidades**
   - Scraper: Inserta artículos nuevos
   - Pipeline: Actualiza con resultados del procesamiento

2. **Resiliencia**
   - Búsqueda por ID (eficiente)
   - Fallback a URL si es necesario
   - Manejo explícito de errores

3. **Simplicidad**
   - No hay estructura anidada compleja
   - No hay validación de storage_path
   - Payload directo del pipeline

4. **Atomicidad**
   - Toda la operación en una transacción
   - Rollback automático si algo falla

5. **Mantenibilidad**
   - RPC independiente y específica
   - Fácil de modificar sin afectar otros sistemas
   - Documentación clara del propósito

### 5. Consideraciones Finales

- El RPC antiguo `insertar_articulo_completo` permanece sin cambios
- No hay breaking changes en el sistema
- La migración es gradual y reversible
- Los logs permiten debugging detallado
- La solución es escalable para futuros cambios