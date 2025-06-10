-- sql-funciones-triggers.sql
-- Funciones y Triggers para la Máquina de Noticias (con modificaciones de CP-001 a CP-009 aplicadas)

-- 1. Trigger para sincronizar cache_entidades
CREATE OR REPLACE FUNCTION sync_cache_entidades()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        DELETE FROM cache_entidades WHERE id = OLD.id;
    ELSIF (TG_OP = 'UPDATE') THEN
        -- No actualizar cache_entidades si la entidad ha sido fusionada
        IF NEW.fusionada_en_id IS NOT NULL THEN
            DELETE FROM cache_entidades WHERE id = NEW.id;
        ELSE
            UPDATE cache_entidades
            SET nombre = NEW.nombre,
                alias = NEW.alias,
                tipo = NEW.tipo
            WHERE id = NEW.id;
        END IF;
    ELSIF (TG_OP = 'INSERT') THEN
        -- No insertar en cache_entidades si la entidad ya está fusionada
        IF NEW.fusionada_en_id IS NULL THEN
            INSERT INTO cache_entidades (id, nombre, alias, tipo)
            VALUES (NEW.id, NEW.nombre, NEW.alias, NEW.tipo)
            ON CONFLICT (id) DO UPDATE -- Por si acaso, aunque INSERT no debería tener conflicto
            SET nombre = EXCLUDED.nombre,
                alias = EXCLUDED.alias,
                tipo = EXCLUDED.tipo;
        END IF;
    END IF;
    RETURN NULL; -- El resultado no importa para triggers AFTER
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_sync_cache_entidades
AFTER INSERT OR UPDATE OR DELETE ON entidades
FOR EACH ROW EXECUTE FUNCTION sync_cache_entidades();

-- 2. Trigger para actualizar fecha último hecho en hilos
-- MODIFICACIÓN: Simplificado para solo actualizar fecha_ultimo_hecho.
-- La lógica de lista_elementos_ids_actualizada se delega al flujo Prefect. (CP-003 Confirmado)
CREATE OR REPLACE FUNCTION update_hilo_fecha_ultimo_hecho()
RETURNS TRIGGER AS $$
DECLARE
    v_hilo_id INTEGER;
    v_max_fecha DATE;
BEGIN
    IF (TG_OP = 'DELETE') THEN
        v_hilo_id := OLD.hilo_id;
    ELSE -- INSERT or UPDATE
        v_hilo_id := NEW.hilo_id;
    END IF;

    -- Calcular la nueva fecha máxima para el hilo afectado
    -- Esta lógica asume que la tabla hechos tiene un índice en (id, fecha_ocurrencia)
    -- y que el planificador puede usarlo eficientemente para el JOIN con hecho_hilo.
    SELECT MAX(COALESCE(upper(h.fecha_ocurrencia)::date, lower(h.fecha_ocurrencia)::date))
    INTO v_max_fecha
    FROM hecho_hilo hh
    JOIN hechos h ON hh.hecho_id = h.id AND hh.fecha_ocurrencia_hecho = h.fecha_ocurrencia -- Crucial para join con partición
    WHERE hh.hilo_id = v_hilo_id;

    -- Actualizar la tabla hilos_narrativos
    UPDATE hilos_narrativos
    SET fecha_ultimo_hecho = v_max_fecha
    -- YA NO SE ACTUALIZA lista_elementos_ids_actualizada AQUÍ
    WHERE id = v_hilo_id;

    RETURN NULL; -- El resultado no importa para triggers AFTER
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_hilo_fecha
AFTER INSERT OR UPDATE OR DELETE ON hecho_hilo
FOR EACH ROW EXECUTE FUNCTION update_hilo_fecha_ultimo_hecho();

-- 3. Trigger para actualizar estado eventos programados
CREATE OR REPLACE FUNCTION actualizar_estado_eventos_programados()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.es_evento_futuro = true AND NOT EXISTS (SELECT 1 FROM eventos_programados WHERE hecho_id = NEW.id AND fecha_ocurrencia_hecho = NEW.fecha_ocurrencia) THEN
        INSERT INTO eventos_programados (hecho_id, fecha_ocurrencia_hecho, fecha_programada, estado)
        VALUES (NEW.id, NEW.fecha_ocurrencia, NEW.fecha_ocurrencia, COALESCE(NEW.estado_programacion, 'programado'))
        ON CONFLICT (hecho_id, fecha_ocurrencia_hecho) DO UPDATE SET
            fecha_programada = EXCLUDED.fecha_programada,
            estado = COALESCE(NEW.estado_programacion, eventos_programados.estado), -- No sobrescribir si el estado del hecho es NULL
            ultima_verificacion = now();
    ELSIF NEW.es_evento_futuro = true AND (NEW.fecha_ocurrencia <> OLD.fecha_ocurrencia OR NEW.estado_programacion IS DISTINCT FROM OLD.estado_programacion) THEN
        UPDATE eventos_programados
        SET fecha_programada = NEW.fecha_ocurrencia,
            estado = COALESCE(NEW.estado_programacion, estado),
            ultima_verificacion = now()
        WHERE hecho_id = NEW.id AND fecha_ocurrencia_hecho = NEW.fecha_ocurrencia; -- Asegurar que actualizamos el correcto si la fecha cambia
    ELSIF NEW.es_evento_futuro = false AND OLD.es_evento_futuro = true THEN
        -- Si deja de ser futuro, marcar como realizado (o requiere revisión)
        UPDATE eventos_programados
        SET estado = 'realizado' -- O quizás 'requiere_revision'
        WHERE hecho_id = NEW.id AND fecha_ocurrencia_hecho = OLD.fecha_ocurrencia; -- Usar OLD.fecha_ocurrencia aquí
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trig_actualizar_eventos
AFTER UPDATE ON hechos
FOR EACH ROW
WHEN (OLD.es_evento_futuro IS DISTINCT FROM NEW.es_evento_futuro OR
      (NEW.es_evento_futuro = true AND (OLD.fecha_ocurrencia IS DISTINCT FROM NEW.fecha_ocurrencia OR OLD.estado_programacion IS DISTINCT FROM NEW.estado_programacion)))
EXECUTE FUNCTION actualizar_estado_eventos_programados();

-- 4. Trigger para inserción de eventos programados iniciales
CREATE OR REPLACE FUNCTION insertar_evento_programado_inicial()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.es_evento_futuro = true THEN
        INSERT INTO eventos_programados (hecho_id, fecha_ocurrencia_hecho, fecha_programada, estado)
        VALUES (NEW.id, NEW.fecha_ocurrencia, NEW.fecha_ocurrencia, COALESCE(NEW.estado_programacion, 'programado'));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trig_insertar_evento_inicial
AFTER INSERT ON hechos
FOR EACH ROW
WHEN (NEW.es_evento_futuro = true)
EXECUTE FUNCTION insertar_evento_programado_inicial();

-- 5. Función RPC para búsqueda de entidades por similitud (Fase 4)
CREATE OR REPLACE FUNCTION buscar_entidad_similar(nombre_busqueda TEXT, tipo_entidad TEXT, umbral_similitud FLOAT DEFAULT 0.7)
RETURNS TABLE (id BIGINT, nombre VARCHAR, tipo VARCHAR, score FLOAT) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ce.id,
        ce.nombre,
        ce.tipo,
        similarity(ce.nombre, nombre_busqueda) AS score
    FROM
        cache_entidades ce
    WHERE
        ce.tipo = tipo_entidad
        AND similarity(ce.nombre, nombre_busqueda) >= umbral_similitud
    ORDER BY
        score DESC
    LIMIT 5;
END;
$$ LANGUAGE plpgsql;

-- 6. Función RPC para Persistencia Atómica (insertar_articulo_completo)
CREATE OR REPLACE FUNCTION insertar_articulo_completo(datos_json JSONB)
RETURNS JSONB -- Devuelve un JSON con estado y IDs/contadores
LANGUAGE plpgsql
AS $$
DECLARE
    -- IDs generados
    v_articulo_id BIGINT;
    v_hecho_id BIGINT;
    v_entidad_id BIGINT;
    v_cita_id BIGINT;
    v_dato_id BIGINT;
    v_fecha_ocurrencia_hecho TSTZRANGE; -- Para relaciones con hechos particionados

    -- Elementos iterables
    v_hecho JSONB;
    v_entidad JSONB;
    v_cita JSONB;
    v_dato JSONB;
    v_rel_hecho_entidad JSONB;
    v_rel_hecho_hecho JSONB;
    v_rel_entidad_entidad JSONB;
    v_contradiccion JSONB;
    v_posible_duplicado JSONB;
    v_hilo_sugerido JSONB; -- Procesamiento de hilos sugeridos es más complejo, puede necesitar lógica separada

    -- Contadores para respuesta
    v_num_hechos_insertados INT := 0;
    v_num_entidades_insertadas INT := 0; -- O encontradas
    v_num_entidades_nuevas INT := 0;
    v_num_citas_insertadas INT := 0;
    v_num_datos_insertados INT := 0;
    v_num_rel_he_insertadas INT := 0;
    v_num_rel_hh_insertadas INT := 0;
    v_num_rel_ee_insertadas INT := 0;
    v_num_contradicciones_insertadas INT := 0;
    v_num_duplicados_registrados INT := 0;

    -- Mapeo de IDs temporales del JSON a IDs reales de la BD
    temp_hecho_id_map HSTORE := ''::HSTORE;
    temp_entidad_id_map HSTORE := ''::HSTORE;

BEGIN
    -- Validación del formato de storage_path
    IF NOT (datos_json->'articulo_metadata'->>'storage_path' ~ '^[^/]+/\d{4}/\d{2}/\d{2}/[^/]+\.(html|txt)\.gz$') THEN
        RETURN jsonb_build_object(
            'status', 'error',
            'mensaje', 'Formato de storage_path inválido. Debe seguir el patrón: {nombre_medio}/{año}/{mes}/{dia}/{hash_url}.{formato}.gz',
            'codigo_sql', 'CHECK_VIOLATION'
        );
    END IF;

    -- 1. Insertar Artículo
    INSERT INTO articulos (
        url, storage_path, medio, pais_publicacion, tipo_medio,
        titular, fecha_publicacion, autor, idioma, seccion,
        etiquetas_fuente, es_opinion, es_oficial,
        resumen, categorias_asignadas, puntuacion_relevancia, -- Estos campos pueden venir del pipeline
        fecha_recopilacion, -- Este debería venir del ArticuloIn o ser DEFAULT now()
        fecha_procesamiento, estado_procesamiento, error_detalle -- Actualizar al final
    )
    SELECT
        j->'articulo_metadata'->>'url',
        j->'articulo_metadata'->>'storage_path', -- Asumiendo que viene en el JSON
        j->'articulo_metadata'->>'medio',
        j->'articulo_metadata'->>'pais_publicacion',
        j->'articulo_metadata'->>'tipo_medio',
        j->'articulo_metadata'->>'titular',
        (j->'articulo_metadata'->>'fecha_publicacion')::TIMESTAMPTZ,
        j->'articulo_metadata'->>'autor',
        j->'articulo_metadata'->>'idioma',
        j->'articulo_metadata'->>'seccion',
        ARRAY(SELECT jsonb_array_elements_text(j->'articulo_metadata'->'etiquetas_fuente')),
        (j->'articulo_metadata'->>'es_opinion')::BOOLEAN,
        (j->'articulo_metadata'->>'es_oficial')::BOOLEAN,
        j->'articulo_metadata'->>'resumen', -- Si se genera resumen
        ARRAY(SELECT jsonb_array_elements_text(j->'articulo_metadata'->'categorias_asignadas')), -- Si se asignan categorías
        (j->'articulo_metadata'->>'puntuacion_relevancia')::INTEGER, -- Si se calcula relevancia
        COALESCE((j->'articulo_metadata'->>'fecha_recopilacion')::TIMESTAMPTZ, now()), -- fecha_recopilacion
        now(), -- fecha_procesamiento
        'completado', -- estado_procesamiento
        NULL -- error_detalle
    FROM (SELECT datos_json AS j) AS src
    RETURNING id INTO v_articulo_id;

    -- 2. Insertar o encontrar Entidades y mapear IDs
    FOR v_entidad IN SELECT * FROM jsonb_array_elements(datos_json->'entidades')
    LOOP
        -- Si la entidad ya tiene un ID de BD asignado (fue encontrada en la Fase 4)
        IF v_entidad ? 'db_id' AND v_entidad->>'db_id' IS NOT NULL THEN
             v_entidad_id := (v_entidad->>'db_id')::BIGINT;

             -- Actualizar alias si se encontraron nuevos
             IF v_entidad ? 'alias' AND jsonb_array_length(v_entidad->'alias') > 0 THEN
                 UPDATE entidades
                 SET alias = array_cat(
                    alias,
                    ARRAY(
                        SELECT e
                        FROM jsonb_array_elements_text(v_entidad->'alias') AS e
                        WHERE e <> ALL(alias) -- Solo añadir los que no existen ya
                    )
                 )
                 WHERE id = v_entidad_id;
             END IF;

             v_num_entidades_insertadas := v_num_entidades_insertadas + 1;
        ELSE
             -- Insertar nueva entidad
             INSERT INTO entidades (
                 nombre,
                 tipo,
                 descripcion,
                 alias,
                 fecha_nacimiento,
                 fecha_disolucion,
                 relevancia,
                 metadata
             )
             VALUES (
                 v_entidad->>'nombre',
                 v_entidad->>'tipo',
                 v_entidad->>'descripcion',
                 CASE
                    WHEN v_entidad ? 'alias' AND jsonb_array_length(v_entidad->'alias') > 0
                    THEN ARRAY(SELECT jsonb_array_elements_text(v_entidad->'alias'))
                    ELSE NULL::TEXT[]
                 END,
                 CASE
                    WHEN v_entidad ? 'fecha_nacimiento' AND v_entidad->>'fecha_nacimiento' IS NOT NULL AND v_entidad->>'fecha_nacimiento' <> ''
                    THEN (v_entidad->>'fecha_nacimiento')::TSTZRANGE
                    ELSE NULL
                 END,
                 CASE
                    WHEN v_entidad ? 'fecha_disolucion' AND v_entidad->>'fecha_disolucion' IS NOT NULL AND v_entidad->>'fecha_disolucion' <> ''
                    THEN (v_entidad->>'fecha_disolucion')::TSTZRANGE
                    ELSE NULL
                 END,
                 COALESCE((v_entidad->>'relevancia')::INTEGER, 5), -- Default 5 si no viene
                 CASE
                    WHEN v_entidad ? 'metadata'
                    THEN v_entidad->'metadata'
                    ELSE NULL::JSONB
                 END
             )
             RETURNING id INTO v_entidad_id;

             v_num_entidades_nuevas := v_num_entidades_nuevas + 1;
             v_num_entidades_insertadas := v_num_entidades_insertadas + 1;
        END IF;

        -- Mapear ID temporal del JSON a ID de la BD
        temp_entidad_id_map := temp_entidad_id_map || hstore((v_entidad->>'id')::TEXT, v_entidad_id::TEXT);
    END LOOP;

    -- 3. Insertar Hechos y mapear IDs
    FOR v_hecho IN SELECT * FROM jsonb_array_elements(datos_json->'hechos')
    LOOP
        -- Calcular y validar fecha_ocurrencia
        v_fecha_ocurrencia_hecho := NULL;

        IF v_hecho ? 'fecha' AND v_hecho->'fecha' ? 'inicio' AND v_hecho->'fecha' ? 'fin' THEN
            -- Manejar formato de fecha que viene como objeto con inicio/fin
            BEGIN
                v_fecha_ocurrencia_hecho := tstzrange(
                    CASE
                        WHEN v_hecho->'fecha'->>'inicio' IS NULL OR v_hecho->'fecha'->>'inicio' = ''
                        THEN NULL
                        ELSE (v_hecho->'fecha'->>'inicio')::TIMESTAMPTZ
                    END,
                    CASE
                        WHEN v_hecho->'fecha'->>'fin' IS NULL OR v_hecho->'fecha'->>'fin' = ''
                        THEN NULL
                        ELSE (v_hecho->'fecha'->>'fin')::TIMESTAMPTZ
                    END
                );
            EXCEPTION WHEN OTHERS THEN
                -- Si falla, intentar interpretar como string o usar fecha del artículo
                v_fecha_ocurrencia_hecho := tstzrange(
                    (SELECT fecha_publicacion FROM articulos WHERE id = v_articulo_id),
                    (SELECT fecha_publicacion FROM articulos WHERE id = v_articulo_id)
                );
            END;
        ELSE
            -- Si no hay estructura de fecha, usar la fecha de publicación del artículo
            v_fecha_ocurrencia_hecho := tstzrange(
                (SELECT fecha_publicacion FROM articulos WHERE id = v_articulo_id),
                (SELECT fecha_publicacion FROM articulos WHERE id = v_articulo_id)
            );
        END IF;

        -- Insertar hecho
        INSERT INTO hechos (
            contenido,
            fecha_ocurrencia,
            precision_temporal,
            tipo_hecho,
            pais,
            region,
            ciudad,
            etiquetas,
            es_evento_futuro,
            estado_programacion,
            fecha_ingreso,
            importancia,
            -- INICIO MODIFICACIÓN CP-005
            evaluacion_editorial,
            consenso_fuentes
            -- FIN MODIFICACIÓN CP-005
        )
        VALUES (
            v_hecho->>'contenido',
            v_fecha_ocurrencia_hecho,
            COALESCE(v_hecho->>'precision_temporal', 'dia'), -- Default 'dia' si no se especifica
            v_hecho->>'tipo_hecho',
            CASE
                WHEN v_hecho ? 'pais' AND jsonb_array_length(v_hecho->'pais') > 0
                THEN ARRAY(SELECT jsonb_array_elements_text(v_hecho->'pais'))
                ELSE ARRAY[]::VARCHAR[]
            END,
            CASE
                WHEN v_hecho ? 'region' AND jsonb_array_length(v_hecho->'region') > 0
                THEN ARRAY(SELECT jsonb_array_elements_text(v_hecho->'region'))
                ELSE NULL
            END,
            CASE
                WHEN v_hecho ? 'ciudad' AND jsonb_array_length(v_hecho->'ciudad') > 0
                THEN ARRAY(SELECT jsonb_array_elements_text(v_hecho->'ciudad'))
                ELSE NULL
            END,
            CASE
                WHEN v_hecho ? 'etiquetas' AND jsonb_array_length(v_hecho->'etiquetas') > 0
                THEN ARRAY(SELECT LOWER(e::TEXT) FROM jsonb_array_elements_text(v_hecho->'etiquetas') AS e)
                ELSE NULL
            END,
            COALESCE((v_hecho->>'es_futuro')::BOOLEAN, false),
            NULLIF(v_hecho->>'estado_programacion', ''),
            now(),
            COALESCE((v_hecho->>'importancia')::INTEGER, 5), -- Este valor será determinado por Fase de Evaluación de Importancia Contextual (CP-004)
            -- INICIO MODIFICACIÓN CP-005
            'pendiente_revision_editorial', -- evaluacion_editorial
            'pendiente_analisis_fuentes'  -- consenso_fuentes
            -- FIN MODIFICACIÓN CP-005
            -- Campos eliminados: confiabilidad (CP-005), menciones_contradictorias (CP-005), notas_editoriales (CP-001), posicion_promedio (CP-006), tendencia_score, ultimo_analisis_tendencia (CP-007)
        )
        RETURNING id INTO v_hecho_id;

        -- Mapear ID temporal del JSON a ID de la BD
        temp_hecho_id_map := temp_hecho_id_map || hstore((v_hecho->>'id')::TEXT, v_hecho_id::TEXT);

        -- Relación Hecho-Artículo (automática)
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
            true, -- Primera fuente para este hecho
            true  -- Confirma el hecho, es su fuente original
        );

        v_num_hechos_insertados := v_num_hechos_insertados + 1;
    END LOOP;

    -- 4. Insertar Citas Textuales
    IF datos_json ? 'citas_textuales' AND jsonb_array_length(datos_json->'citas_textuales') > 0 THEN
        FOR v_cita IN SELECT * FROM jsonb_array_elements(datos_json->'citas_textuales')
        LOOP
            -- Obtener ID real de entidad emisora
            v_entidad_id := NULL;
            IF v_cita ? 'entidad_id' AND v_cita->>'entidad_id' IS NOT NULL AND (v_cita->>'entidad_id')::TEXT <> '0' THEN
                v_entidad_id := (temp_entidad_id_map->(v_cita->>'entidad_id'))::BIGINT;
            END IF;

            -- Obtener ID real del hecho de contexto
            v_hecho_id := NULL;
            IF v_cita ? 'hecho_id' AND v_cita->>'hecho_id' IS NOT NULL AND (v_cita->>'hecho_id')::TEXT <> '0' THEN
                v_hecho_id := (temp_hecho_id_map->(v_cita->>'hecho_id'))::BIGINT;
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
                v_cita->>'cita',
                v_entidad_id,
                v_articulo_id,
                v_hecho_id,
                CASE
                    WHEN v_cita ? 'fecha' AND v_cita->>'fecha' IS NOT NULL AND v_cita->>'fecha' <> ''
                    THEN (v_cita->>'fecha')::TIMESTAMPTZ
                    ELSE NULL
                END,
                v_cita->>'contexto',
                COALESCE((v_cita->>'relevancia')::INTEGER, 3) -- Default 3 si no viene
            )
            RETURNING id INTO v_cita_id;

            v_num_citas_insertadas := v_num_citas_insertadas + 1;
        END LOOP;
    END IF;

    -- 5. Insertar Datos Cuantitativos
    IF datos_json ? 'datos_cuantitativos' AND jsonb_array_length(datos_json->'datos_cuantitativos') > 0 THEN
        FOR v_dato IN SELECT * FROM jsonb_array_elements(datos_json->'datos_cuantitativos')
        LOOP
            -- Obtener ID real del hecho relacionado
            v_hecho_id := NULL;
            IF v_dato ? 'hecho_id' AND v_dato->>'hecho_id' IS NOT NULL AND (v_dato->>'hecho_id')::TEXT <> '0' THEN
                v_hecho_id := (temp_hecho_id_map->(v_dato->>'hecho_id'))::BIGINT;
            END IF;

            -- Insertar dato cuantitativo
            INSERT INTO datos_cuantitativos (
                hecho_id,
                articulo_id,
                indicador,
                categoria,
                valor_numerico,
                unidad,
                ambito_geografico,
                periodo_referencia_inicio,
                periodo_referencia_fin,
                tipo_periodo,
                valor_anterior,
                variacion_absoluta,
                variacion_porcentual,
                tendencia
            )
            VALUES (
                v_hecho_id,
                v_articulo_id,
                v_dato->>'indicador',
                v_dato->>'categoria',
                (v_dato->>'valor')::NUMERIC,
                v_dato->>'unidad',
                CASE
                    WHEN v_dato ? 'ambito_geografico' AND jsonb_array_length(v_dato->'ambito_geografico') > 0
                    THEN ARRAY(SELECT jsonb_array_elements_text(v_dato->'ambito_geografico'))
                    ELSE ARRAY[]::VARCHAR[]
                END,
                CASE
                    WHEN v_dato->'periodo' ? 'inicio' AND v_dato->'periodo'->>'inicio' IS NOT NULL AND v_dato->'periodo'->>'inicio' <> ''
                    THEN (v_dato->'periodo'->>'inicio')::DATE
                    ELSE NULL
                END,
                CASE
                    WHEN v_dato->'periodo' ? 'fin' AND v_dato->'periodo'->>'fin' IS NOT NULL AND v_dato->'periodo'->>'fin' <> ''
                    THEN (v_dato->'periodo'->>'fin')::DATE
                    ELSE NULL
                END,
                v_dato->>'tipo_periodo',
                CASE
                    WHEN v_dato ? 'valor_anterior' AND v_dato->>'valor_anterior' IS NOT NULL AND v_dato->>'valor_anterior' <> ''
                    THEN (v_dato->>'valor_anterior')::NUMERIC
                    ELSE NULL
                END,
                CASE
                    WHEN v_dato ? 'variacion_absoluta' AND v_dato->>'variacion_absoluta' IS NOT NULL AND v_dato->>'variacion_absoluta' <> ''
                    THEN (v_dato->>'variacion_absoluta')::NUMERIC
                    ELSE NULL
                END,
                CASE
                    WHEN v_dato ? 'variacion_porcentual' AND v_dato->>'variacion_porcentual' IS NOT NULL AND v_dato->>'variacion_porcentual' <> ''
                    THEN (v_dato->>'variacion_porcentual')::NUMERIC
                    ELSE NULL
                END,
                v_dato->>'tendencia'
            )
            RETURNING id INTO v_dato_id;

            v_num_datos_insertados := v_num_datos_insertados + 1;
        END LOOP;
    END IF;

    -- 6. Insertar Relaciones Hecho-Entidad
    IF datos_json ? 'relaciones' AND datos_json->'relaciones' ? 'hecho_entidad' AND
       jsonb_array_length(datos_json->'relaciones'->'hecho_entidad') > 0 THEN

        FOR v_rel_hecho_entidad IN SELECT * FROM jsonb_array_elements(datos_json->'relaciones'->'hecho_entidad')
        LOOP
            -- Obtener IDs reales mapeados
            v_hecho_id := (temp_hecho_id_map->(v_rel_hecho_entidad->>'hecho_id'))::BIGINT;
            v_entidad_id := (temp_entidad_id_map->(v_rel_hecho_entidad->>'entidad_id'))::BIGINT;

            -- Verificar si la entidad ha sido fusionada, y si es así, usar el ID de destino
            SELECT COALESCE(fusionada_en_id, id) INTO v_entidad_id
            FROM entidades
            WHERE id = v_entidad_id;

            IF v_hecho_id IS NOT NULL AND v_entidad_id IS NOT NULL THEN
                -- Obtener fecha_ocurrencia del hecho para la relación
                SELECT fecha_ocurrencia INTO v_fecha_ocurrencia_hecho
                FROM hechos
                WHERE id = v_hecho_id;

                -- Insertar relación
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
                    v_rel_hecho_entidad->>'tipo_relacion',
                    COALESCE((v_rel_hecho_entidad->>'relevancia_en_hecho')::INTEGER, 5)
                )
                ON CONFLICT (hecho_id, fecha_ocurrencia_hecho, entidad_id, tipo_relacion) DO NOTHING; -- Evitar duplicados

                v_num_rel_he_insertadas := v_num_rel_he_insertadas + 1;
            END IF;
        END LOOP;
    END IF;

    -- 7. Insertar Relaciones Hecho-Hecho
    IF datos_json ? 'relaciones' AND datos_json->'relaciones' ? 'hecho_relacionado' AND
       jsonb_array_length(datos_json->'relaciones'->'hecho_relacionado') > 0 THEN

        FOR v_rel_hecho_hecho IN SELECT * FROM jsonb_array_elements(datos_json->'relaciones'->'hecho_relacionado')
        LOOP
            -- Obtener IDs reales mapeados
            DECLARE
                v_hecho_origen_id BIGINT := (temp_hecho_id_map->(v_rel_hecho_hecho->>'hecho_origen_id'))::BIGINT;
                v_hecho_destino_id BIGINT := (temp_hecho_id_map->(v_rel_hecho_hecho->>'hecho_destino_id'))::BIGINT;
                v_fecha_ocurrencia_origen TSTZRANGE;
                v_fecha_ocurrencia_destino TSTZRANGE;
            BEGIN
                -- Solo continuar si los dos hechos existen
                IF v_hecho_origen_id IS NOT NULL AND v_hecho_destino_id IS NOT NULL THEN
                    -- Obtener fechas de ocurrencia
                    SELECT fecha_ocurrencia INTO v_fecha_ocurrencia_origen
                    FROM hechos
                    WHERE id = v_hecho_origen_id;

                    SELECT fecha_ocurrencia INTO v_fecha_ocurrencia_destino
                    FROM hechos
                    WHERE id = v_hecho_destino_id;

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
                        v_fecha_ocurrencia_origen,
                        v_hecho_destino_id,
                        v_fecha_ocurrencia_destino,
                        v_rel_hecho_hecho->>'tipo_relacion',
                        COALESCE((v_rel_hecho_hecho->>'fuerza_relacion')::INTEGER, 5),
                        v_rel_hecho_hecho->>'descripcion_relacion'
                    )
                    ON CONFLICT (hecho_origen_id, fecha_ocurrencia_origen, hecho_destino_id, fecha_ocurrencia_destino, tipo_relacion) DO NOTHING;

                    v_num_rel_hh_insertadas := v_num_rel_hh_insertadas + 1;
                END IF;
            END;
        END LOOP;
    END IF;

    -- 8. Insertar Relaciones Entidad-Entidad
    IF datos_json ? 'relaciones' AND datos_json->'relaciones' ? 'entidad_relacion' AND
       jsonb_array_length(datos_json->'relaciones'->'entidad_relacion') > 0 THEN

        FOR v_rel_entidad_entidad IN SELECT * FROM jsonb_array_elements(datos_json->'relaciones'->'entidad_relacion')
        LOOP
            -- Obtener IDs reales mapeados
            DECLARE
                v_entidad_origen_id BIGINT := (temp_entidad_id_map->(v_rel_entidad_entidad->>'entidad_origen_id'))::BIGINT;
                v_entidad_destino_id BIGINT := (temp_entidad_id_map->(v_rel_entidad_entidad->>'entidad_destino_id'))::BIGINT;
            BEGIN
                -- Verificar si las entidades han sido fusionadas y usar el ID de destino
                SELECT COALESCE(fusionada_en_id, id) INTO v_entidad_origen_id
                FROM entidades
                WHERE id = v_entidad_origen_id;

                SELECT COALESCE(fusionada_en_id, id) INTO v_entidad_destino_id
                FROM entidades
                WHERE id = v_entidad_destino_id;

                -- Solo continuar si las dos entidades existen
                IF v_entidad_origen_id IS NOT NULL AND v_entidad_destino_id IS NOT NULL AND v_entidad_origen_id <> v_entidad_destino_id THEN
                    -- Insertar relación
                    INSERT INTO entidad_relacion (
                        entidad_origen_id,
                        entidad_destino_id,
                        tipo_relacion,
                        descripcion,
                        fecha_inicio,
                        fecha_fin,
                        fuerza_relacion
                    )
                    VALUES (
                        v_entidad_origen_id,
                        v_entidad_destino_id,
                        v_rel_entidad_entidad->>'tipo_relacion',
                        v_rel_entidad_entidad->>'descripcion',
                        CASE
                            WHEN v_rel_entidad_entidad ? 'fecha_inicio' AND v_rel_entidad_entidad->>'fecha_inicio' IS NOT NULL AND v_rel_entidad_entidad->>'fecha_inicio' <> ''
                            THEN (v_rel_entidad_entidad->>'fecha_inicio')::TIMESTAMPTZ
                            ELSE NULL
                        END,
                        CASE
                            WHEN v_rel_entidad_entidad ? 'fecha_fin' AND v_rel_entidad_entidad->>'fecha_fin' IS NOT NULL AND v_rel_entidad_entidad->>'fecha_fin' <> ''
                            THEN (v_rel_entidad_entidad->>'fecha_fin')::TIMESTAMPTZ
                            ELSE NULL
                        END,
                        COALESCE((v_rel_entidad_entidad->>'fuerza_relacion')::INTEGER, 5)
                    )
                    ON CONFLICT (entidad_origen_id, entidad_destino_id, tipo_relacion) DO NOTHING;

                    v_num_rel_ee_insertadas := v_num_rel_ee_insertadas + 1;
                END IF;
            END;
        END LOOP;
    END IF;

    -- 9. Insertar Contradicciones
    IF datos_json ? 'relaciones' AND datos_json->'relaciones' ? 'contradicciones' AND
       jsonb_array_length(datos_json->'relaciones'->'contradicciones') > 0 THEN

        FOR v_contradiccion IN SELECT * FROM jsonb_array_elements(datos_json->'relaciones'->'contradicciones')
        LOOP
            -- Obtener IDs reales mapeados
            DECLARE
                v_hecho_principal_id BIGINT := (temp_hecho_id_map->(v_contradiccion->>'hecho_principal_id'))::BIGINT;
                v_hecho_contradictorio_id BIGINT := (temp_hecho_id_map->(v_contradiccion->>'hecho_contradictorio_id'))::BIGINT;
                v_fecha_ocurrencia_principal TSTZRANGE;
                v_fecha_ocurrencia_contradictoria TSTZRANGE;
            BEGIN
                -- Solo continuar si los dos hechos existen
                IF v_hecho_principal_id IS NOT NULL AND v_hecho_contradictorio_id IS NOT NULL THEN
                    -- Obtener fechas de ocurrencia
                    SELECT fecha_ocurrencia INTO v_fecha_ocurrencia_principal
                    FROM hechos
                    WHERE id = v_hecho_principal_id;

                    SELECT fecha_ocurrencia INTO v_fecha_ocurrencia_contradictoria
                    FROM hechos
                    WHERE id = v_hecho_contradictorio_id;

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
                        v_fecha_ocurrencia_principal,
                        v_hecho_contradictorio_id,
                        v_fecha_ocurrencia_contradictoria,
                        v_contradiccion->>'tipo_contradiccion',
                        COALESCE((v_contradiccion->>'grado_contradiccion')::INTEGER, 3),
                        v_contradiccion->>'descripcion'
                    );

                    v_num_contradicciones_insertadas := v_num_contradicciones_insertadas + 1;
                END IF;
            END;
        END LOOP;
    END IF;

    -- 10. Registrar Posibles Duplicados
    IF datos_json ? 'posibles_duplicados' THEN
        FOR v_hecho_nuevo_id_temp, v_hecho_existente_ids IN
            SELECT k, v FROM jsonb_each(datos_json->'posibles_duplicados')
        LOOP
            DECLARE
                v_hecho_nuevo_id BIGINT := (temp_hecho_id_map->v_hecho_nuevo_id_temp)::BIGINT;
                v_fecha_ocurrencia_nuevo TSTZRANGE;
                v_hecho_existente_id BIGINT;
                v_fecha_ocurrencia_existente TSTZRANGE;
            BEGIN
                IF v_hecho_nuevo_id IS NOT NULL THEN
                    SELECT fecha_ocurrencia INTO v_fecha_ocurrencia_nuevo
                    FROM hechos
                    WHERE id = v_hecho_nuevo_id;

                    FOR v_hecho_existente_id_temp IN
                        SELECT jsonb_array_elements_text(v_hecho_existente_ids)
                    LOOP
                        v_hecho_existente_id := v_hecho_existente_id_temp::BIGINT;

                        SELECT fecha_ocurrencia INTO v_fecha_ocurrencia_existente
                        FROM hechos
                        WHERE id = v_hecho_existente_id;

                        INSERT INTO posibles_duplicados_hechos (
                            hecho_nuevo_id,
                            fecha_ocurrencia_nuevo,
                            hecho_existente_id,
                            fecha_ocurrencia_existente
                        )
                        VALUES (
                            v_hecho_nuevo_id,
                            v_fecha_ocurrencia_nuevo,
                            v_hecho_existente_id,
                            v_fecha_ocurrencia_existente
                        );

                        v_num_duplicados_registrados := v_num_duplicados_registrados + 1;
                    END LOOP;
                END IF;
            END;
        END LOOP;
    END IF;

    -- 11. Vinculación con Hilos Narrativos (pendiente de implementación detallada)
    -- Si hay hilos sugeridos, procesarlos aquí

    -- Finalización Exitosa
    RETURN jsonb_build_object(
        'status', 'exito',
        'articulo_id', v_articulo_id,
        'num_hechos_insertados', v_num_hechos_insertados,
        'num_entidades_procesadas', v_num_entidades_insertadas,
        'num_entidades_nuevas', v_num_entidades_nuevas,
        'num_citas_insertadas', v_num_citas_insertadas,
        'num_datos_insertados', v_num_datos_insertados,
        'num_rel_he_insertadas', v_num_rel_he_insertadas,
        'num_rel_hh_insertadas', v_num_rel_hh_insertadas,
        'num_rel_ee_insertadas', v_num_rel_ee_insertadas,
        'num_contradicciones_insertadas', v_num_contradicciones_insertadas,
        'num_duplicados_registrados', v_num_duplicados_registrados
    );

EXCEPTION
    WHEN OTHERS THEN
        -- Capturar cualquier error, la transacción se revierte automáticamente
        RETURN jsonb_build_object(
            'status', 'error',
            'mensaje', SQLERRM,
            'codigo_sql', SQLSTATE,
            'articulo_id_parcial', v_articulo_id -- Devolver ID si se llegó a insertar
        );
END;
$$;

-- 7. Nueva función RPC para inserción de fragmentos
CREATE OR REPLACE FUNCTION insertar_fragmento_completo(datos_json JSONB)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    -- Variables para IDs
    v_documento_id BIGINT;
    v_fragmento_id BIGINT;
    v_hecho_id BIGINT;
    v_entidad_id BIGINT;
    v_cita_id BIGINT;
    v_dato_id BIGINT;
    v_fecha_ocurrencia_hecho TSTZRANGE;

    -- Variables para elementos iterables
    v_hecho JSONB;
    v_entidad JSONB;
    v_cita JSONB;
    v_dato JSONB;
    v_rel_hecho_entidad JSONB;
    v_rel_entidad_fragmento JSONB;

    -- Contadores para respuesta
    v_num_hechos_insertados INT := 0;
    v_num_entidades_insertadas INT := 0;
    v_num_entidades_nuevas INT := 0;
    v_num_citas_insertadas INT := 0;
    v_num_datos_insertados INT := 0;
    v_num_rel_he_insertadas INT := 0;
    v_num_rel_ef_insertadas INT := 0;

    -- Mapeo de IDs temporales
    temp_hecho_id_map HSTORE := ''::HSTORE;
    temp_entidad_id_map HSTORE := ''::HSTORE;

BEGIN
    -- 1. Validar y obtener fragmento y documento
    v_documento_id := (datos_json->>'documento_id')::BIGINT;
    v_fragmento_id := (datos_json->>'fragmento_id')::BIGINT;

    -- Validar que el documento exista
    IF NOT EXISTS (SELECT 1 FROM documentos_extensos WHERE id = v_documento_id) THEN
        RETURN jsonb_build_object(
            'status', 'error',
            'mensaje', 'Documento no encontrado con ID: ' || v_documento_id,
            'codigo_sql', 'NOT_FOUND'
        );
    END IF;

    -- Validar que el fragmento exista y pertenezca al documento indicado
    IF NOT EXISTS (SELECT 1 FROM fragmentos_extensos WHERE id = v_fragmento_id AND documento_id = v_documento_id) THEN
        RETURN jsonb_build_object(
            'status', 'error',
            'mensaje', 'Fragmento no encontrado o no pertenece al documento indicado',
            'codigo_sql', 'NOT_FOUND'
        );
    END IF;

    -- 2. Procesamiento de entidades similar a insertar_articulo_completo
    IF datos_json ? 'entidades' AND jsonb_array_length(datos_json->'entidades') > 0 THEN
        FOR v_entidad IN SELECT * FROM jsonb_array_elements(datos_json->'entidades')
        LOOP
            -- Código similar a insertar_articulo_completo para entidades
            -- (Manejo de entidades nuevas/existentes, fusión, alias, etc.)
            IF v_entidad ? 'db_id' AND v_entidad->>'db_id' IS NOT NULL THEN
                 v_entidad_id := (v_entidad->>'db_id')::BIGINT;
                 IF v_entidad ? 'alias' AND jsonb_array_length(v_entidad->'alias') > 0 THEN
                     UPDATE entidades SET alias = array_cat(alias, ARRAY(SELECT e FROM jsonb_array_elements_text(v_entidad->'alias') AS e WHERE e <> ALL(alias))) WHERE id = v_entidad_id;
                 END IF;
                 v_num_entidades_insertadas := v_num_entidades_insertadas + 1;
            ELSE
                 INSERT INTO entidades (nombre, tipo, descripcion, alias, fecha_nacimiento, fecha_disolucion, relevancia, metadata)
                 VALUES (v_entidad->>'nombre', v_entidad->>'tipo', v_entidad->>'descripcion',
                         CASE WHEN v_entidad ? 'alias' AND jsonb_array_length(v_entidad->'alias') > 0 THEN ARRAY(SELECT jsonb_array_elements_text(v_entidad->'alias')) ELSE NULL::TEXT[] END,
                         CASE WHEN v_entidad ? 'fecha_nacimiento' AND v_entidad->>'fecha_nacimiento' IS NOT NULL AND v_entidad->>'fecha_nacimiento' <> '' THEN (v_entidad->>'fecha_nacimiento')::TSTZRANGE ELSE NULL END,
                         CASE WHEN v_entidad ? 'fecha_disolucion' AND v_entidad->>'fecha_disolucion' IS NOT NULL AND v_entidad->>'fecha_disolucion' <> '' THEN (v_entidad->>'fecha_disolucion')::TSTZRANGE ELSE NULL END,
                         COALESCE((v_entidad->>'relevancia')::INTEGER, 5),
                         CASE WHEN v_entidad ? 'metadata' THEN v_entidad->'metadata' ELSE NULL::JSONB END
                 ) RETURNING id INTO v_entidad_id;
                 v_num_entidades_nuevas := v_num_entidades_nuevas + 1;
                 v_num_entidades_insertadas := v_num_entidades_insertadas + 1;
            END IF;
            temp_entidad_id_map := temp_entidad_id_map || hstore((v_entidad->>'id')::TEXT, v_entidad_id::TEXT);
        END LOOP;
    END IF;

    -- 3. Procesamiento de hechos
    IF datos_json ? 'hechos' AND jsonb_array_length(datos_json->'hechos') > 0 THEN
        FOR v_hecho IN SELECT * FROM jsonb_array_elements(datos_json->'hechos')
        LOOP
            -- Calcular fecha_ocurrencia (similar a insertar_articulo_completo, usando fecha_publicacion del documento como fallback)
            v_fecha_ocurrencia_hecho := NULL;
            IF v_hecho ? 'fecha' AND v_hecho->'fecha' ? 'inicio' AND v_hecho->'fecha' ? 'fin' THEN
                BEGIN
                    v_fecha_ocurrencia_hecho := tstzrange(
                        CASE WHEN v_hecho->'fecha'->>'inicio' IS NULL OR v_hecho->'fecha'->>'inicio' = '' THEN NULL ELSE (v_hecho->'fecha'->>'inicio')::TIMESTAMPTZ END,
                        CASE WHEN v_hecho->'fecha'->>'fin' IS NULL OR v_hecho->'fecha'->>'fin' = '' THEN NULL ELSE (v_hecho->'fecha'->>'fin')::TIMESTAMPTZ END
                    );
                EXCEPTION WHEN OTHERS THEN
                    v_fecha_ocurrencia_hecho := tstzrange(
                        (SELECT fecha_publicacion FROM documentos_extensos WHERE id = v_documento_id),
                        (SELECT fecha_publicacion FROM documentos_extensos WHERE id = v_documento_id)
                    );
                END;
            ELSE
                v_fecha_ocurrencia_hecho := tstzrange(
                    (SELECT fecha_publicacion FROM documentos_extensos WHERE id = v_documento_id),
                    (SELECT fecha_publicacion FROM documentos_extensos WHERE id = v_documento_id)
                );
            END IF;

            -- Insertar hecho con referencia al documento y fragmento
            INSERT INTO hechos (
                contenido, fecha_ocurrencia, precision_temporal, tipo_hecho, pais, etiquetas, importancia,
                documento_id, fragmento_id,
                -- INICIO MODIFICACIÓN CP-005
                evaluacion_editorial,
                consenso_fuentes
                -- FIN MODIFICACIÓN CP-005
            )
            VALUES (
                v_hecho->>'contenido', v_fecha_ocurrencia_hecho, COALESCE(v_hecho->>'precision_temporal', 'dia'),
                v_hecho->>'tipo_hecho',
                CASE WHEN v_hecho ? 'pais' AND jsonb_array_length(v_hecho->'pais') > 0 THEN ARRAY(SELECT jsonb_array_elements_text(v_hecho->'pais')) ELSE ARRAY[]::VARCHAR[] END,
                CASE WHEN v_hecho ? 'etiquetas' AND jsonb_array_length(v_hecho->'etiquetas') > 0 THEN ARRAY(SELECT LOWER(e::TEXT) FROM jsonb_array_elements_text(v_hecho->'etiquetas') AS e) ELSE NULL END,
                COALESCE((v_hecho->>'importancia')::INTEGER, 5), -- Este valor será determinado por Fase de Evaluación de Importancia Contextual (CP-004)
                v_documento_id, v_fragmento_id,
                -- INICIO MODIFICACIÓN CP-005
                'pendiente_revision_editorial', -- evaluacion_editorial
                'pendiente_analisis_fuentes'  -- consenso_fuentes
                -- FIN MODIFICACIÓN CP-005
                -- Campos eliminados: confiabilidad (CP-005), menciones_contradictorias (CP-005), notas_editoriales (CP-001), posicion_promedio (CP-006), tendencia_score, ultimo_analisis_tendencia (CP-007)
            )
            RETURNING id INTO v_hecho_id;

            temp_hecho_id_map := temp_hecho_id_map || hstore((v_hecho->>'id')::TEXT, v_hecho_id::TEXT);
            v_num_hechos_insertados := v_num_hechos_insertados + 1;
        END LOOP;
    END IF;

    -- 4. Procesamiento de citas textuales
    IF datos_json ? 'citas_textuales' AND jsonb_array_length(datos_json->'citas_textuales') > 0 THEN
        FOR v_cita IN SELECT * FROM jsonb_array_elements(datos_json->'citas_textuales')
        LOOP
            v_entidad_id := NULL;
            IF v_cita ? 'entidad_id' AND v_cita->>'entidad_id' IS NOT NULL AND (v_cita->>'entidad_id')::TEXT <> '0' THEN
                v_entidad_id := (temp_entidad_id_map->(v_cita->>'entidad_id'))::BIGINT;
            END IF;
            v_hecho_id := NULL;
            IF v_cita ? 'hecho_id' AND v_cita->>'hecho_id' IS NOT NULL AND (v_cita->>'hecho_id')::TEXT <> '0' THEN
                v_hecho_id := (temp_hecho_id_map->(v_cita->>'hecho_id'))::BIGINT;
            END IF;

            INSERT INTO citas_textuales (
                cita, entidad_emisora_id, hecho_contexto_id, fecha_cita, contexto, relevancia,
                documento_id, fragmento_id
            )
            VALUES (
                v_cita->>'cita', v_entidad_id, v_hecho_id,
                CASE WHEN v_cita ? 'fecha' AND v_cita->>'fecha' IS NOT NULL AND v_cita->>'fecha' <> '' THEN (v_cita->>'fecha')::TIMESTAMPTZ ELSE NULL END,
                v_cita->>'contexto', COALESCE((v_cita->>'relevancia')::INTEGER, 3),
                v_documento_id, v_fragmento_id
            )
            RETURNING id INTO v_cita_id;
            v_num_citas_insertadas := v_num_citas_insertadas + 1;
        END LOOP;
    END IF;

    -- 5. Procesamiento de datos cuantitativos (similar a insertar_articulo_completo, pero con documento_id y fragmento_id)
    IF datos_json ? 'datos_cuantitativos' AND jsonb_array_length(datos_json->'datos_cuantitativos') > 0 THEN
        FOR v_dato IN SELECT * FROM jsonb_array_elements(datos_json->'datos_cuantitativos')
        LOOP
            v_hecho_id := NULL;
            IF v_dato ? 'hecho_id' AND v_dato->>'hecho_id' IS NOT NULL AND (v_dato->>'hecho_id')::TEXT <> '0' THEN
                v_hecho_id := (temp_hecho_id_map->(v_dato->>'hecho_id'))::BIGINT;
            END IF;
            INSERT INTO datos_cuantitativos (
                hecho_id, indicador, categoria, valor_numerico, unidad, ambito_geografico,
                periodo_referencia_inicio, periodo_referencia_fin, tipo_periodo,
                documento_id, fragmento_id
            )
            VALUES (
                v_hecho_id, v_dato->>'indicador', v_dato->>'categoria', (v_dato->>'valor')::NUMERIC, v_dato->>'unidad',
                CASE WHEN v_dato ? 'ambito_geografico' AND jsonb_array_length(v_dato->'ambito_geografico') > 0 THEN ARRAY(SELECT jsonb_array_elements_text(v_dato->'ambito_geografico')) ELSE ARRAY[]::VARCHAR[] END,
                CASE WHEN v_dato->'periodo' ? 'inicio' AND v_dato->'periodo'->>'inicio' IS NOT NULL AND v_dato->'periodo'->>'inicio' <> '' THEN (v_dato->'periodo'->>'inicio')::DATE ELSE NULL END,
                CASE WHEN v_dato->'periodo' ? 'fin' AND v_dato->'periodo'->>'fin' IS NOT NULL AND v_dato->'periodo'->>'fin' <> '' THEN (v_dato->'periodo'->>'fin')::DATE ELSE NULL END,
                v_dato->>'tipo_periodo',
                v_documento_id, v_fragmento_id
            )
            RETURNING id INTO v_dato_id;
            v_num_datos_insertados := v_num_datos_insertados + 1;
        END LOOP;
    END IF;

    -- 6. Procesar relaciones hecho-entidad (similar a insertar_articulo_completo)
    IF datos_json ? 'relaciones' AND datos_json->'relaciones' ? 'hecho_entidad' AND
       jsonb_array_length(datos_json->'relaciones'->'hecho_entidad') > 0 THEN
        FOR v_rel_hecho_entidad IN SELECT * FROM jsonb_array_elements(datos_json->'relaciones'->'hecho_entidad')
        LOOP
            v_hecho_id := (temp_hecho_id_map->(v_rel_hecho_entidad->>'hecho_id'))::BIGINT;
            v_entidad_id := (temp_entidad_id_map->(v_rel_hecho_entidad->>'entidad_id'))::BIGINT;
            SELECT COALESCE(fusionada_en_id, id) INTO v_entidad_id FROM entidades WHERE id = v_entidad_id;

            IF v_hecho_id IS NOT NULL AND v_entidad_id IS NOT NULL THEN
                SELECT fecha_ocurrencia INTO v_fecha_ocurrencia_hecho FROM hechos WHERE id = v_hecho_id;
                INSERT INTO hecho_entidad (hecho_id, fecha_ocurrencia_hecho, entidad_id, tipo_relacion, relevancia_en_hecho)
                VALUES (v_hecho_id, v_fecha_ocurrencia_hecho, v_entidad_id, v_rel_hecho_entidad->>'tipo_relacion', COALESCE((v_rel_hecho_entidad->>'relevancia_en_hecho')::INTEGER, 5))
                ON CONFLICT (hecho_id, fecha_ocurrencia_hecho, entidad_id, tipo_relacion) DO NOTHING;
                v_num_rel_he_insertadas := v_num_rel_he_insertadas + 1;
            END IF;
        END LOOP;
    END IF;

    -- 7. Procesar relaciones entidad-fragmento
    IF datos_json ? 'relaciones' AND datos_json->'relaciones' ? 'entidad_fragmento' AND
       jsonb_array_length(datos_json->'relaciones'->'entidad_fragmento') > 0 THEN
        FOR v_rel_entidad_fragmento IN SELECT * FROM jsonb_array_elements(datos_json->'relaciones'->'entidad_fragmento')
        LOOP
            v_entidad_id := (temp_entidad_id_map->(v_rel_entidad_fragmento->>'entidad_id'))::BIGINT;
            SELECT COALESCE(fusionada_en_id, id) INTO v_entidad_id FROM entidades WHERE id = v_entidad_id;

            IF v_entidad_id IS NOT NULL THEN
                INSERT INTO entidad_fragmento (entidad_id, fragmento_id, documento_id)
                VALUES (v_entidad_id, v_fragmento_id, v_documento_id)
                ON CONFLICT (entidad_id, fragmento_id, documento_id) DO NOTHING;
                v_num_rel_ef_insertadas := v_num_rel_ef_insertadas + 1;
            END IF;
        END LOOP;
    END IF;

    -- 8. Actualizar embedding del fragmento y estado del documento si es necesario
    IF datos_json ? 'embedding' AND datos_json->>'embedding' IS NOT NULL THEN
        UPDATE fragmentos_extensos
        SET embedding = (datos_json->>'embedding')::vector
        WHERE id = v_fragmento_id;
    END IF;

    -- Si todos los fragmentos del documento tienen embedding, marcar documento como procesado
    IF NOT EXISTS (SELECT 1 FROM fragmentos_extensos WHERE documento_id = v_documento_id AND embedding IS NULL) THEN
        UPDATE documentos_extensos
        SET procesado = true
        WHERE id = v_documento_id;
    END IF;

    -- Finalización Exitosa
    RETURN jsonb_build_object(
        'status', 'exito',
        'documento_id', v_documento_id,
        'fragmento_id', v_fragmento_id,
        'num_hechos_insertados', v_num_hechos_insertados,
        'num_entidades_procesadas', v_num_entidades_insertadas,
        'num_entidades_nuevas', v_num_entidades_nuevas,
        'num_citas_insertadas', v_num_citas_insertadas,
        'num_datos_insertados', v_num_datos_insertados,
        'num_rel_he_insertadas', v_num_rel_he_insertadas,
        'num_rel_ef_insertadas', v_num_rel_ef_insertadas
    );

EXCEPTION
    WHEN OTHERS THEN
        -- Capturar cualquier error
        RETURN jsonb_build_object(
            'status', 'error',
            'mensaje', SQLERRM,
            'codigo_sql', SQLSTATE,
            'documento_id', v_documento_id,
            'fragmento_id', v_fragmento_id
        );
END;
$$;

-- 8. Función para obtener información de hilos narrativos
-- MODIFICACIÓN: Lógica SQL para detalles de entidades y citas completada.
-- Se han añadido también algunos campos extra a los detalles (ej. titulo_documento).
CREATE OR REPLACE FUNCTION obtener_info_hilo(
    p_hilo_id INTEGER,
    p_incluir_detalles_elementos BOOLEAN DEFAULT TRUE,
    p_max_elementos_detalle INTEGER DEFAULT 50
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_hilo JSONB;
    v_elementos JSONB;
    v_lista_ids_hechos JSONB;
    v_lista_ids_entidades JSONB;
    v_lista_ids_citas JSONB;
    v_detalles_hechos JSONB := '[]'::JSONB;
    v_detalles_entidades JSONB := '[]'::JSONB;
    v_detalles_citas JSONB := '[]'::JSONB;
BEGIN
    -- 1. Obtener información básica del hilo
    SELECT jsonb_build_object(
        'id', id,
        'titulo', titulo,
        'descripcion', descripcion,
        'descripcion_hilo_curada', descripcion_hilo_curada,
        'fecha_inicio_seguimiento', fecha_inicio_seguimiento,
        'fecha_ultimo_hecho', fecha_ultimo_hecho,
        'estado', estado,
        'paises_principales', paises_principales,
        'etiquetas_principales', etiquetas_principales,
        'relevancia_editorial', relevancia_editorial,
        'criterios_consulta_estructurados', criterios_consulta_estructurados,
        'puntos_clave_novedades', puntos_clave_novedades
    )
    INTO v_hilo
    FROM hilos_narrativos
    WHERE id = p_hilo_id;

    IF v_hilo IS NULL THEN
        RETURN jsonb_build_object(
            'status', 'error',
            'mensaje', 'Hilo narrativo no encontrado con ID: ' || p_hilo_id
        );
    END IF;

    -- 2. Obtener lista_elementos_ids_actualizada
    SELECT lista_elementos_ids_actualizada
    INTO v_elementos
    FROM hilos_narrativos
    WHERE id = p_hilo_id;

    v_lista_ids_hechos := COALESCE(v_elementos->'hechos', '[]'::JSONB);
    v_lista_ids_entidades := COALESCE(v_elementos->'entidades', '[]'::JSONB);
    v_lista_ids_citas := COALESCE(v_elementos->'citas', '[]'::JSONB);

    -- 3. Si se solicitan detalles, obtener la información completa
    IF p_incluir_detalles_elementos THEN
        -- Obtener detalles de hechos
        IF jsonb_array_length(v_lista_ids_hechos) > 0 THEN
            WITH hechos_ids AS (
                SELECT value::BIGINT AS hecho_id
                FROM jsonb_array_elements_text(v_lista_ids_hechos)
                LIMIT p_max_elementos_detalle
            )
            SELECT jsonb_agg(
                jsonb_build_object(
                    'id', h.id,
                    'contenido', h.contenido,
                    'fecha_ocurrencia', jsonb_build_object(
                        'inicio', lower(h.fecha_ocurrencia),
                        'fin', upper(h.fecha_ocurrencia)
                    ),
                    'tipo_hecho', h.tipo_hecho,
                    'importancia', h.importancia,
                    'pais', h.pais,
                    'etiquetas', h.etiquetas,
                    -- INICIO MODIFICACIÓN CP-005
                    'evaluacion_editorial', h.evaluacion_editorial,
                    'consenso_fuentes', h.consenso_fuentes,
                    -- FIN MODIFICACIÓN CP-005
                    'fuente', CASE
                        WHEN h.documento_id IS NOT NULL THEN jsonb_build_object(
                            'tipo', 'documento',
                            'documento_id', h.documento_id,
                            'fragmento_id', h.fragmento_id,
                            'titulo_documento', (SELECT titulo FROM documentos_extensos WHERE id = h.documento_id)
                        )
                        ELSE (
                            SELECT jsonb_build_object(
                                'tipo', 'articulo',
                                'articulo_id', ha.articulo_id,
                                'medio', a.medio,
                                'titular', a.titular,
                                'fecha_publicacion', a.fecha_publicacion
                            )
                            FROM hecho_articulo ha
                            JOIN articulos a ON ha.articulo_id = a.id
                            WHERE ha.hecho_id = h.id AND ha.fecha_ocurrencia_hecho = h.fecha_ocurrencia -- Añadir condición de fecha para partición
                            ORDER BY a.fecha_publicacion DESC -- O alguna lógica para elegir la "mejor" fuente
                            LIMIT 1
                        )
                    END
                )
            )
            INTO v_detalles_hechos
            FROM hechos_ids hi
            JOIN hechos h ON hi.hecho_id = h.id;
        END IF;

        -- Obtener detalles de entidades
        IF jsonb_array_length(v_lista_ids_entidades) > 0 THEN
            WITH entidades_ids_cte AS (
                SELECT value::BIGINT AS entidad_id
                FROM jsonb_array_elements_text(v_lista_ids_entidades)
                LIMIT p_max_elementos_detalle
            )
            SELECT jsonb_agg(
                jsonb_build_object(
                    'id', e.id,
                    'nombre', e.nombre,
                    'tipo', e.tipo,
                    'descripcion', e.descripcion,
                    'alias', e.alias,
                    'relevancia', e.relevancia,
                    'wikidata_id', e.wikidata_id
                )
            )
            INTO v_detalles_entidades
            FROM entidades_ids_cte ei
            JOIN entidades e ON ei.entidad_id = e.id
            WHERE e.fusionada_en_id IS NULL; -- Solo entidades activas
        END IF;

        -- Obtener detalles de citas
        IF jsonb_array_length(v_lista_ids_citas) > 0 THEN
            WITH citas_ids_cte AS (
                SELECT value::BIGINT AS cita_id
                FROM jsonb_array_elements_text(v_lista_ids_citas)
                LIMIT p_max_elementos_detalle
            )
            SELECT jsonb_agg(
                jsonb_build_object(
                    'id', ct.id,
                    'cita', ct.cita,
                    'entidad_emisora_id', ct.entidad_emisora_id,
                    'entidad_emisora_nombre', (SELECT nombre FROM entidades WHERE id = ct.entidad_emisora_id AND fusionada_en_id IS NULL),
                    'fecha_cita', ct.fecha_cita,
                    'contexto', ct.contexto,
                    'relevancia', ct.relevancia,
                    'fuente', CASE
                        WHEN ct.documento_id IS NOT NULL THEN jsonb_build_object(
                            'tipo', 'documento',
                            'documento_id', ct.documento_id,
                            'fragmento_id', ct.fragmento_id,
                            'titulo_documento', (SELECT titulo FROM documentos_extensos WHERE id = ct.documento_id)
                        )
                        WHEN ct.articulo_id IS NOT NULL THEN (
                            SELECT jsonb_build_object(
                                'tipo', 'articulo',
                                'articulo_id', ct.articulo_id,
                                'medio', art.medio,
                                'titular', art.titular,
                                'fecha_publicacion', art.fecha_publicacion
                            )
                            FROM articulos art WHERE art.id = ct.articulo_id
                        )
                        ELSE NULL
                    END
                )
            )
            INTO v_detalles_citas
            FROM citas_ids_cte ci
            JOIN citas_textuales ct ON ci.cita_id = ct.id;
        END IF;
    END IF;

    -- 4. Construir y devolver la respuesta completa
    RETURN jsonb_build_object(
        'status', 'exito',
        'hilo', v_hilo,
        'elementos_ids', v_elementos,
        'detalles', jsonb_build_object(
            'hechos', COALESCE(v_detalles_hechos, '[]'::jsonb),
            'entidades', COALESCE(v_detalles_entidades, '[]'::jsonb),
            'citas', COALESCE(v_detalles_citas, '[]'::jsonb)
        ),
        'total_elementos', jsonb_build_object(
            'hechos', jsonb_array_length(v_lista_ids_hechos),
            'entidades', jsonb_array_length(v_lista_ids_entidades),
            'citas', jsonb_array_length(v_lista_ids_citas)
        )
    );
END;
$$;