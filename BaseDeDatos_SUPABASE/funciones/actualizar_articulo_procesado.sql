-- Función RPC: actualizar_articulo_procesado
-- Propósito: Actualizar artículos existentes con resultados del procesamiento del pipeline
-- Autor: Sistema
-- Fecha: 2025-01-19

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
    
    -- Mapeo de IDs temporales (usando JSONB en lugar de HSTORE)
    temp_hecho_id_map JSONB := '{}'::JSONB;
    temp_entidad_id_map JSONB := '{}'::JSONB;
    
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
        
        -- Embeddings si vienen (por ahora comentado porque no tenemos la extensión pgvector)
        -- embedding_articulo = CASE
        --     WHEN datos_json ? 'embedding_articulo_vector'
        --     THEN (datos_json->>'embedding_articulo_vector')::vector
        --     ELSE embedding_articulo
        -- END,
        
        -- Metadata adicional del procesamiento
        error_detalle = NULL  -- Limpiar cualquier error previo
        
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
                jsonb_build_object((v_entidad->>'id_temporal_entidad')::TEXT, v_entidad_id::TEXT);
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
                jsonb_build_object((v_hecho->>'id_temporal_hecho')::TEXT, v_hecho_id::TEXT);
            
            v_num_hechos_insertados := v_num_hechos_insertados + 1;
            
            -- Procesar entidades del hecho
            IF v_hecho ? 'entidades_del_hecho' THEN
                FOR v_entidad IN SELECT * FROM jsonb_array_elements(v_hecho->'entidades_del_hecho')
                LOOP
                    -- Obtener ID real de la entidad
                    v_entidad_id := (temp_entidad_id_map->>(v_entidad->>'id_temporal_entidad'))::BIGINT;
                    
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
                v_entidad_id := (temp_entidad_id_map->>(v_cita->>'id_temporal_entidad_emisora'))::BIGINT;
            END IF;
            
            v_hecho_id := NULL;
            IF v_cita ? 'id_temporal_hecho_principal' THEN
                v_hecho_id := (temp_hecho_id_map->>(v_cita->>'id_temporal_hecho_principal'))::BIGINT;
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
                v_hecho_id := (temp_hecho_id_map->>(v_dato->>'id_temporal_hecho_principal'))::BIGINT;
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
    
    -- 7. Procesar relaciones hecho-hecho
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
                v_hecho_origen_id := (temp_hecho_id_map->>(v_relacion->>'id_hecho_origen'))::BIGINT;
                v_hecho_destino_id := (temp_hecho_id_map->>(v_relacion->>'id_hecho_destino'))::BIGINT;
                
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
    
    -- 8. Procesar relaciones entidad-entidad
    IF datos_json ? 'relaciones_entidades' THEN
        FOR v_relacion IN SELECT * FROM jsonb_array_elements(datos_json->'relaciones_entidades')
        LOOP
            DECLARE
                v_entidad_origen_id BIGINT;
                v_entidad_destino_id BIGINT;
            BEGIN
                -- Obtener IDs reales
                v_entidad_origen_id := (temp_entidad_id_map->>(v_relacion->>'id_entidad_origen'))::BIGINT;
                v_entidad_destino_id := (temp_entidad_id_map->>(v_relacion->>'id_entidad_destino'))::BIGINT;
                
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
    
    -- 9. Procesar contradicciones
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
                v_hecho_principal_id := (temp_hecho_id_map->>(v_relacion->>'id_hecho_principal'))::BIGINT;
                v_hecho_contradictorio_id := (temp_hecho_id_map->>(v_relacion->>'id_hecho_contradictorio'))::BIGINT;
                
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