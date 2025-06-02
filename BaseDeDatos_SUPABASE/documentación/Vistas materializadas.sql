-- sql-vistas-materializadas.sql
-- Definición de vistas materializadas para la caché de información frecuentemente consultada

-- 1. Agenda de Eventos Próximos
-- Esta vista materializada muestra los eventos futuros programados, organizados por horizonte temporal
-- Se consulta desde Dashboard y/o Módulo de Consulta
CREATE MATERIALIZED VIEW agenda_eventos_proximos AS
SELECT
    h.id AS hecho_id,
    h.contenido AS titulo_evento,
    ep.fecha_programada,
    ep.estado,
    h.pais,
    h.ciudad,
    h.tipo_hecho,
    h.etiquetas,
    array_agg(DISTINCT e.nombre ORDER BY e.nombre) FILTER (WHERE e.id IS NOT NULL) AS entidades_involucradas_nombres,
    h.importancia,
    ep.prioridad_cobertura,
    ep.url_evento,
    CASE
        WHEN lower(ep.fecha_programada) <= now() + interval '1 day' THEN 'inmediato'
        WHEN lower(ep.fecha_programada) <= now() + interval '7 days' THEN 'esta_semana'
        WHEN lower(ep.fecha_programada) <= now() + interval '30 days' THEN 'este_mes'
        WHEN lower(ep.fecha_programada) <= now() + interval '90 days' THEN 'proximo_trimestre'
        ELSE 'futuro'
    END AS horizonte_temporal
FROM
    eventos_programados ep
JOIN
    hechos h ON ep.hecho_id = h.id AND ep.fecha_ocurrencia_hecho = h.fecha_ocurrencia
LEFT JOIN
    hecho_entidad he ON h.id = he.hecho_id AND h.fecha_ocurrencia = he.fecha_ocurrencia_hecho
LEFT JOIN
    entidades e ON he.entidad_id = e.id
WHERE
    ep.estado IN ('programado', 'confirmado')
    AND upper(ep.fecha_programada) > now() -- Solo eventos realmente futuros
GROUP BY
    h.id, h.contenido, h.fecha_ocurrencia, ep.fecha_programada, ep.estado,
    h.pais, h.ciudad, h.tipo_hecho, h.etiquetas, h.importancia, ep.prioridad_cobertura,
    ep.url_evento
ORDER BY
    lower(ep.fecha_programada);

CREATE UNIQUE INDEX idx_agenda_eventos_id ON agenda_eventos_proximos(hecho_id, (lower(fecha_programada)));
CREATE INDEX idx_agenda_eventos_horizonte ON agenda_eventos_proximos(horizonte_temporal);
CREATE INDEX idx_agenda_eventos_paises_gin ON agenda_eventos_proximos USING gin(pais);

-- 2. Resumen de Hilos Activos
-- Esta vista ofrece una visión consolidada de los hilos narrativos activos con métricas clave
-- Utilizada para el Dashboard o para proveer contexto inicial al Chat
CREATE MATERIALIZED VIEW resumen_hilos_activos AS
SELECT
    hn.id AS hilo_id,
    hn.titulo,
    hn.descripcion,
    hn.descripcion_hilo_curada, -- Campo para la descripción curada
    hn.fecha_inicio_seguimiento,
    hn.fecha_ultimo_hecho,
    hn.estado,
    hn.paises_principales,
    hn.etiquetas_principales,
    hn.relevancia_editorial,
    -- Métricas de elementos basadas en lista_elementos_ids_actualizada o por conteo directo
    COALESCE(
        jsonb_array_length(hn.lista_elementos_ids_actualizada->'hechos'), -- Usar la longitud del array en el JSONB
        (SELECT COUNT(DISTINCT hh_inner.hecho_id) FROM hecho_hilo hh_inner WHERE hh_inner.hilo_id = hn.id) -- Fallback si el JSONB es NULL o no tiene 'hechos'
    ) AS total_hechos,
    COALESCE(
        jsonb_array_length(hn.lista_elementos_ids_actualizada->'entidades'), -- Asumiendo que también se guardan entidades en la lista
        (SELECT COUNT(DISTINCT he_inner.entidad_id) FROM hecho_hilo hh_inner JOIN hecho_entidad he_inner ON hh_inner.hecho_id = he_inner.hecho_id AND hh_inner.fecha_ocurrencia_hecho = he_inner.fecha_ocurrencia_hecho WHERE hh_inner.hilo_id = hn.id)
    ) AS total_entidades_mencionadas,
    (SELECT COUNT(DISTINCT ha_inner.articulo_id) FROM hecho_hilo hh_inner JOIN hecho_articulo ha_inner ON hh_inner.hecho_id = ha_inner.hecho_id AND hh_inner.fecha_ocurrencia_hecho = ha_inner.fecha_ocurrencia_hecho WHERE hh_inner.hilo_id = hn.id) AS total_articulos,
    (now() - COALESCE(hn.fecha_ultimo_hecho, hn.fecha_inicio_seguimiento))::interval AS tiempo_desde_ultima_actividad,
    CASE
        WHEN now() - COALESCE(hn.fecha_ultimo_hecho, hn.fecha_inicio_seguimiento) <= interval '2 days' THEN 'muy_reciente'
        WHEN now() - COALESCE(hn.fecha_ultimo_hecho, hn.fecha_inicio_seguimiento) <= interval '7 days' THEN 'reciente'
        WHEN now() - COALESCE(hn.fecha_ultimo_hecho, hn.fecha_inicio_seguimiento) <= interval '30 days' THEN 'activo'
        WHEN now() - COALESCE(hn.fecha_ultimo_hecho, hn.fecha_inicio_seguimiento) <= interval '90 days' THEN 'seguimiento'
        ELSE 'inactivo'
    END AS nivel_actividad,
    hn.puntos_clave_novedades, -- Campo para resumen de novedades
    -- Top 5 entidades más mencionadas en este hilo
    (
        SELECT array_agg(e.nombre)
        FROM (
            SELECT ent.nombre, COUNT(*) as menciones
            FROM hecho_hilo hh2
            JOIN hecho_entidad he2 ON hh2.hecho_id = he2.hecho_id AND hh2.fecha_ocurrencia_hecho = he2.fecha_ocurrencia_hecho
            JOIN entidades ent ON he2.entidad_id = ent.id
            WHERE hh2.hilo_id = hn.id AND ent.fusionada_en_id IS NULL
            GROUP BY ent.nombre
            ORDER BY menciones DESC
            LIMIT 5
        ) e
    ) AS top_entidades,
    -- Últimos 3 hechos relevantes
    (
        SELECT array_agg(h_rel.contenido)
        FROM (
            SELECT h_inner.contenido
            FROM hecho_hilo hh3
            JOIN hechos h_inner ON hh3.hecho_id = h_inner.id AND hh3.fecha_ocurrencia_hecho = h_inner.fecha_ocurrencia
            WHERE hh3.hilo_id = hn.id AND (hh3.es_hito_clave = true OR h_inner.importancia >= 7)
            ORDER BY COALESCE(upper(h_inner.fecha_ocurrencia), lower(h_inner.fecha_ocurrencia)) DESC
            LIMIT 3
        ) h_rel
    ) AS ultimos_hechos_relevantes
FROM
    hilos_narrativos hn
-- No se necesita LEFT JOIN a hecho_hilo, hecho_entidad, hecho_articulo a nivel principal si las métricas se basan en lista_elementos_ids_actualizada o subconsultas
WHERE
    hn.estado IN ('activo', 'inactivo') -- No incluir resueltos o históricos
GROUP BY -- Asegurar que GROUP BY es correcto si se eliminan los joins principales
    hn.id, hn.titulo, hn.descripcion, hn.descripcion_hilo_curada, hn.puntos_clave_novedades,
    hn.fecha_inicio_seguimiento, hn.fecha_ultimo_hecho, hn.lista_elementos_ids_actualizada,
    hn.estado, hn.paises_principales, hn.etiquetas_principales, hn.relevancia_editorial
ORDER BY
    COALESCE(hn.fecha_ultimo_hecho, hn.fecha_inicio_seguimiento) DESC;

CREATE UNIQUE INDEX idx_resumen_hilos_id ON resumen_hilos_activos(hilo_id);
CREATE INDEX idx_resumen_hilos_actividad ON resumen_hilos_activos(nivel_actividad);
CREATE INDEX idx_resumen_hilos_relevancia ON resumen_hilos_activos(relevancia_editorial DESC);

-- 3. Entidades Relevantes Recientes
-- Esta vista muestra las entidades más mencionadas recientemente, con métricas de relevancia
-- Utilizada para dar contexto al Chat y para el Dashboard (sección tendencias)
CREATE MATERIALIZED VIEW entidades_relevantes_recientes AS
SELECT
    e.id AS entidad_id,
    e.nombre,
    e.tipo,
    COUNT(DISTINCT he.hecho_id) AS total_menciones_hechos,
    COUNT(DISTINCT a.id) + COUNT(DISTINCT de.id) AS total_fuentes, -- Incluye documentos y artículos
    COUNT(DISTINCT a.id) AS total_articulos,
    COUNT(DISTINCT de.id) AS total_documentos, -- Nuevo contador para documentos extensos
    COUNT(DISTINCT ct.id) AS total_citas,
    GREATEST(
        MAX(a.fecha_publicacion),
        MAX(de.fecha_publicacion) -- Considerar fecha_ingesta si fecha_publicacion de documentos es opcional
    ) AS ultima_mencion,
    e.relevancia AS relevancia_base,
    (0.5 * e.relevancia + 0.3 * COUNT(DISTINCT he.hecho_id) + 0.2 * COUNT(DISTINCT ct.id))::NUMERIC(5,2) AS score_relevancia,
    array_agg(DISTINCT h.tipo_hecho) FILTER (WHERE h.tipo_hecho IS NOT NULL) AS tipos_hecho_relacionados,
    array_agg(DISTINCT a.pais_publicacion) FILTER (WHERE a.pais_publicacion IS NOT NULL) AS paises_mencion,
    array_agg(DISTINCT unnest(h.etiquetas)) FILTER (WHERE h.etiquetas IS NOT NULL) AS etiquetas_asociadas
FROM
    entidades e
LEFT JOIN
    hecho_entidad he ON e.id = he.entidad_id
LEFT JOIN
    hechos h ON he.hecho_id = h.id AND he.fecha_ocurrencia_hecho = h.fecha_ocurrencia
LEFT JOIN
    hecho_articulo ha ON h.id = ha.hecho_id AND h.fecha_ocurrencia = ha.fecha_ocurrencia_hecho
LEFT JOIN
    articulos a ON ha.articulo_id = a.id
LEFT JOIN
    entidad_fragmento ef ON e.id = ef.entidad_id
LEFT JOIN
    fragmentos_extensos fe ON ef.fragmento_id = fe.id -- Unir con fragmentos para obtener el documento
LEFT JOIN
    documentos_extensos de ON fe.documento_id = de.id -- Luego con documentos_extensos
LEFT JOIN
    citas_textuales ct ON e.id = ct.entidad_emisora_id
WHERE
    (a.fecha_publicacion >= now() - interval '30 days' OR
     de.fecha_publicacion >= now() - interval '30 days' OR -- Considerar fecha_ingesta si es más fiable
     ct.fecha_ingreso >= now() - interval '30 days') -- Considerar citas recientes también
    AND e.fusionada_en_id IS NULL -- No incluir entidades que fueron fusionadas
GROUP BY
    e.id, e.nombre, e.tipo, e.relevancia
HAVING
    COUNT(DISTINCT he.hecho_id) >= 3 -- Solo entidades mencionadas en al menos 3 hechos recientes
ORDER BY
    score_relevancia DESC;

CREATE UNIQUE INDEX idx_entidades_rel_rec_id ON entidades_relevantes_recientes(entidad_id);
CREATE INDEX idx_entidades_rel_rec_score ON entidades_relevantes_recientes(score_relevancia DESC);
CREATE INDEX idx_entidades_rel_rec_tipo ON entidades_relevantes_recientes(tipo);

-- 4. Estadísticas Globales
-- Esta vista ofrece métricas generales del sistema para el Dashboard y reportes
CREATE MATERIALIZED VIEW estadisticas_globales AS
SELECT
    -- Métricas generales
    (SELECT COUNT(*) FROM articulos) AS total_articulos,
    (SELECT COUNT(*) FROM hechos) AS total_hechos,
    (SELECT COUNT(*) FROM entidades WHERE fusionada_en_id IS NULL) AS total_entidades, -- Solo activas
    (SELECT COUNT(*) FROM hilos_narrativos) AS total_hilos,
    (SELECT COUNT(*) FROM documentos_extensos) AS total_documentos_extensos,
    (SELECT COUNT(*) FROM fragmentos_extensos) AS total_fragmentos,

    -- Distribución por tipos de hecho
    (SELECT COUNT(*) FROM hechos WHERE tipo_hecho = 'SUCESO') AS total_sucesos,
    (SELECT COUNT(*) FROM hechos WHERE tipo_hecho = 'ANUNCIO') AS total_anuncios,
    (SELECT COUNT(*) FROM hechos WHERE tipo_hecho = 'DECLARACION') AS total_declaraciones,
    (SELECT COUNT(*) FROM hechos WHERE tipo_hecho = 'BIOGRAFIA') AS total_biografias,
    (SELECT COUNT(*) FROM hechos WHERE tipo_hecho = 'CONCEPTO') AS total_conceptos,
    (SELECT COUNT(*) FROM hechos WHERE tipo_hecho = 'NORMATIVA') AS total_normativas,
    (SELECT COUNT(*) FROM hechos WHERE tipo_hecho = 'EVENTO') AS total_eventos,

    -- Distribución por tipos de entidad
    (SELECT COUNT(*) FROM entidades WHERE tipo = 'PERSONA' AND fusionada_en_id IS NULL) AS total_personas,
    (SELECT COUNT(*) FROM entidades WHERE tipo = 'ORGANIZACION' AND fusionada_en_id IS NULL) AS total_organizaciones,
    (SELECT COUNT(*) FROM entidades WHERE tipo = 'INSTITUCION' AND fusionada_en_id IS NULL) AS total_instituciones,
    (SELECT COUNT(*) FROM entidades WHERE tipo = 'LUGAR' AND fusionada_en_id IS NULL) AS total_lugares,
    (SELECT COUNT(*) FROM entidades WHERE tipo = 'EVENTO' AND fusionada_en_id IS NULL) AS total_evento_entidades,
    (SELECT COUNT(*) FROM entidades WHERE tipo = 'NORMATIVA' AND fusionada_en_id IS NULL) AS total_normativa_entidades,
    (SELECT COUNT(*) FROM entidades WHERE tipo = 'CONCEPTO' AND fusionada_en_id IS NULL) AS total_concepto_entidades,
    (SELECT COUNT(*) FROM entidades WHERE tipo = 'OTRO' AND fusionada_en_id IS NULL) AS total_otras_entidades,
    (SELECT COUNT(*) FROM entidades WHERE fusionada_en_id IS NOT NULL) AS total_entidades_fusionadas,

    -- Estadísticas temporales
    (SELECT MIN(fecha_publicacion) FROM articulos) AS primer_articulo_fecha,
    (SELECT MAX(fecha_publicacion) FROM articulos) AS ultimo_articulo_fecha,
    (SELECT MIN(fecha_publicacion) FROM documentos_extensos) AS primer_documento_fecha,
    (SELECT MAX(fecha_publicacion) FROM documentos_extensos) AS ultimo_documento_fecha,
    (SELECT MIN(lower(fecha_ocurrencia)) FROM hechos) AS hecho_mas_antiguo,
    (SELECT MAX(upper(fecha_ocurrencia)) FROM hechos) AS hecho_mas_reciente,

    -- Actividad reciente (últimas 24h, 7 días, 30 días)
    (SELECT COUNT(*) FROM articulos WHERE fecha_procesamiento >= now() - interval '1 day') AS articulos_24h,
    (SELECT COUNT(*) FROM articulos WHERE fecha_procesamiento >= now() - interval '7 days') AS articulos_7d,
    (SELECT COUNT(*) FROM articulos WHERE fecha_procesamiento >= now() - interval '30 days') AS articulos_30d,

    (SELECT COUNT(*) FROM hechos WHERE fecha_ingreso >= now() - interval '1 day') AS hechos_24h,
    (SELECT COUNT(*) FROM hechos WHERE fecha_ingreso >= now() - interval '7 days') AS hechos_7d,
    (SELECT COUNT(*) FROM hechos WHERE fecha_ingreso >= now() - interval '30 days') AS hechos_30d,

    (SELECT COUNT(*) FROM documentos_extensos WHERE fecha_ingesta >= now() - interval '1 day') AS documentos_24h,
    (SELECT COUNT(*) FROM documentos_extensos WHERE fecha_ingesta >= now() - interval '7 days') AS documentos_7d,
    (SELECT COUNT(*) FROM documentos_extensos WHERE fecha_ingesta >= now() - interval '30 days') AS documentos_30d,

    -- Top países
    (
        SELECT jsonb_object_agg(pais, total)
        FROM (
            SELECT unnest(h_pais.pais) AS pais, COUNT(*) AS total
            FROM hechos h_pais
            WHERE h_pais.pais IS NOT NULL AND array_length(h_pais.pais, 1) > 0 -- Asegurar que no haya arrays vacíos o nulos
            GROUP BY pais
            ORDER BY total DESC
            LIMIT 10
        ) top_paises
    ) AS top_paises,

    -- Distribución por medios
    (
        SELECT jsonb_object_agg(medio, total)
        FROM (
            SELECT art_medio.medio, COUNT(*) AS total
            FROM articulos art_medio
            GROUP BY art_medio.medio
            ORDER BY total DESC
            LIMIT 10
        ) top_medios
    ) AS top_medios,

    -- Distribución por tipo de documento extenso
    (
        SELECT jsonb_object_agg(tipo_documento, total)
        FROM (
            SELECT doc_tipo.tipo_documento, COUNT(*) AS total
            FROM documentos_extensos doc_tipo
            GROUP BY doc_tipo.tipo_documento
            ORDER BY total DESC
        ) top_tipos_documento
    ) AS top_tipos_documento,

    -- Fechas de actualización y otra información de mantenimiento
    now() AS fecha_actualizacion;

CREATE UNIQUE INDEX idx_estadisticas_globales_fecha ON estadisticas_globales((1)); -- Vista con una sola fila, el índice único necesita una expresión constante

-- 5. Análisis de Tendencias (Frecuencia de Temas)
-- Esta vista rastrea la evolución de etiquetas/temas en el tiempo
CREATE MATERIALIZED VIEW tendencias_temas AS
WITH etiquetas_expandidas AS (
    SELECT
        h.id AS hecho_id,
        h.fecha_ingreso,
        date_trunc('day', h.fecha_ingreso) AS dia_ingreso,
        lower(unnest(h.etiquetas)) AS etiqueta, -- Normalizar a minúsculas
        h.tipo_hecho,
        array_length(h.pais, 1) AS num_paises,
        h.importancia
    FROM hechos h
    WHERE h.fecha_ingreso >= now() - interval '90 days' -- Últimos 90 días
    AND h.etiquetas IS NOT NULL AND array_length(h.etiquetas, 1) > 0
),
etiquetas_diarias AS (
    SELECT
        dia_ingreso,
        etiqueta,
        COUNT(*) AS frecuencia,
        AVG(importancia) AS importancia_promedio,
        array_agg(DISTINCT tipo_hecho) AS tipos_hecho
    FROM etiquetas_expandidas
    GROUP BY dia_ingreso, etiqueta
),
etiquetas_semana_anterior AS (
    SELECT
        etiqueta,
        SUM(frecuencia) AS frecuencia_7d_anterior
    FROM etiquetas_diarias
    WHERE dia_ingreso BETWEEN (now() - interval '14 days')::date AND (now() - interval '8 days')::date -- Ajustar rangos para no solapar
    GROUP BY etiqueta
),
etiquetas_semana_actual AS (
    SELECT
        etiqueta,
        SUM(frecuencia) AS frecuencia_7d_actual
    FROM etiquetas_diarias
    WHERE dia_ingreso BETWEEN (now() - interval '7 days')::date AND (now() - interval '1 day')::date -- Hasta ayer
    GROUP BY etiqueta
)
SELECT
    e_agg.etiqueta,
    SUM(e_agg.frecuencia) AS frecuencia_90d,
    COALESCE(ea.frecuencia_7d_actual, 0) AS frecuencia_7d_actual,
    COALESCE(ep.frecuencia_7d_anterior, 0) AS frecuencia_7d_anterior,
    CASE
        WHEN COALESCE(ep.frecuencia_7d_anterior, 0) = 0 AND COALESCE(ea.frecuencia_7d_actual, 0) > 0 THEN 9999 -- Nueva aparición significativa
        WHEN COALESCE(ep.frecuencia_7d_anterior, 0) = 0 THEN 0 -- No había antes, no hay ahora
        ELSE ROUND(100.0 * (COALESCE(ea.frecuencia_7d_actual, 0) - COALESCE(ep.frecuencia_7d_anterior, 0)) / GREATEST(1, COALESCE(ep.frecuencia_7d_anterior, 0)))::INTEGER
    END AS cambio_porcentual,
    AVG(e_agg.importancia_promedio) AS importancia_promedio_90d,
    array_agg(DISTINCT e_tipos.tipos_hecho_flat) FILTER (WHERE e_tipos.tipos_hecho_flat IS NOT NULL) AS tipos_hecho_asociados_90d,
    COUNT(DISTINCT e_agg.dia_ingreso) AS dias_con_menciones_90d,
    MAX(e_agg.dia_ingreso) AS ultima_mencion_registrada
FROM etiquetas_diarias e_agg
LEFT JOIN etiquetas_semana_actual ea ON e_agg.etiqueta = ea.etiqueta
LEFT JOIN etiquetas_semana_anterior ep ON e_agg.etiqueta = ep.etiqueta
LEFT JOIN LATERAL (SELECT unnest(e_agg.tipos_hecho) AS tipos_hecho_flat) e_tipos ON true
GROUP BY e_agg.etiqueta, ea.frecuencia_7d_actual, ep.frecuencia_7d_anterior
HAVING SUM(e_agg.frecuencia) >= 3 -- Solo etiquetas con al menos 3 menciones en los 90 días
ORDER BY
    GREATEST(COALESCE(ea.frecuencia_7d_actual, 0), COALESCE(ep.frecuencia_7d_anterior, 0)) DESC,
    cambio_porcentual DESC;

CREATE UNIQUE INDEX idx_tendencias_temas_etiqueta ON tendencias_temas(etiqueta);
CREATE INDEX idx_tendencias_temas_frec ON tendencias_temas(frecuencia_7d_actual DESC);
CREATE INDEX idx_tendencias_temas_cambio ON tendencias_temas(cambio_porcentual DESC);

-- 6. Hilos Sugeridos para Artículos Recientes
-- Esta vista ayuda a vincular automáticamente nuevos hechos a hilos existentes
-- o a sugerir nuevos hilos basados en patrones emergentes
CREATE MATERIALIZED VIEW hilos_sugeridos_hechos AS
WITH hechos_recientes_sin_hilo AS (
    SELECT
        h.id AS hecho_id,
        h.fecha_ocurrencia,
        h.contenido,
        h.tipo_hecho,
        h.pais,
        h.etiquetas,
        array_agg(e.id) FILTER (WHERE e.id IS NOT NULL) AS entidades_ids,
        array_agg(e.nombre) FILTER (WHERE e.nombre IS NOT NULL) AS entidades_nombres,
        h.documento_id,
        h.fragmento_id
    FROM hechos h
    LEFT JOIN hecho_entidad he ON h.id = he.hecho_id AND h.fecha_ocurrencia = he.fecha_ocurrencia_hecho
    LEFT JOIN entidades e ON he.entidad_id = e.id AND e.fusionada_en_id IS NULL
    LEFT JOIN hecho_hilo hh ON h.id = hh.hecho_id AND h.fecha_ocurrencia = hh.fecha_ocurrencia_hecho
    WHERE
        h.fecha_ingreso >= now() - interval '7 days'
        AND hh.hecho_id IS NULL
    GROUP BY h.id, h.fecha_ocurrencia, h.contenido, h.tipo_hecho, h.pais, h.etiquetas, h.documento_id, h.fragmento_id
),
compatibilidad_hilos AS (
    SELECT
        h_rec.hecho_id,
        h_rec.fecha_ocurrencia,
        hn.id AS hilo_id,
        hn.titulo AS hilo_titulo,
        hn.descripcion_hilo_curada,
        hn.paises_principales,
        hn.etiquetas_principales,
        (
            (SELECT COUNT(*) FROM unnest(h_rec.entidades_ids) e_id WHERE EXISTS
                (SELECT 1 FROM jsonb_array_elements_text(COALESCE(hn.lista_elementos_ids_actualizada->'entidades','[]'::jsonb)) el_id WHERE el_id::BIGINT = e_id)
            ) * 2.0 +
            (SELECT COUNT(*) FROM unnest(h_rec.etiquetas) et WHERE et = ANY(hn.etiquetas_principales)) * 1.5 +
            (SELECT COUNT(*) FROM unnest(h_rec.pais) p WHERE p = ANY(hn.paises_principales)) * 1.0 +
            -- Considerar similitud textual con la descripción curada si se desea (ver comentario abajo)
            -- COALESCE(similarity(h_rec.contenido, hn.descripcion_hilo_curada), 0.0) * 1.0 +
            CASE WHEN jsonb_path_exists(
                hn.lista_elementos_ids_actualizada,
                ('$.hechos[*] ? (@ == ' || h_rec.hecho_id || ')')::jsonpath
            ) THEN 5.0 ELSE 0.0 END -- Este caso es menos probable si el hecho es realmente "sin_hilo"
                                     -- y lista_elementos_ids_actualizada se actualiza por criterios.
                                     -- Podría ser más útil si lista_elementos_ids_actualizada contiene elementos *potenciales*
        ) AS score
    FROM hechos_recientes_sin_hilo h_rec
    CROSS JOIN hilos_narrativos hn
    WHERE hn.estado = 'activo'
),
mejores_coincidencias AS (
    SELECT
        hecho_id,
        fecha_ocurrencia,
        jsonb_agg(
            jsonb_build_object(
                'hilo_id', hilo_id,
                'hilo_titulo', hilo_titulo,
                'descripcion_hilo_curada', descripcion_hilo_curada,
                'score', score
            )
            ORDER BY score DESC
        ) FILTER (WHERE score > 3) AS hilos_compatibles,
        MAX(score) AS max_score
    FROM compatibilidad_hilos
    GROUP BY hecho_id, fecha_ocurrencia
)
SELECT
    h_final.hecho_id,
    h_final.fecha_ocurrencia,
    h_final.contenido,
    h_final.tipo_hecho,
    h_final.pais,
    h_final.etiquetas,
    h_final.entidades_nombres,
    h_final.documento_id,
    h_final.fragmento_id,
    m.hilos_compatibles,
    m.max_score,
    CASE
        WHEN m.max_score >= 10 THEN 'alta'
        WHEN m.max_score >= 5 THEN 'media'
        WHEN m.max_score >= 3 THEN 'baja'
        ELSE 'ninguna'
    END AS compatibilidad,
    CASE
        WHEN m.max_score >= 8 THEN true
        ELSE false
    END AS vinculacion_automatica_recomendada
FROM hechos_recientes_sin_hilo h_final
LEFT JOIN mejores_coincidencias m ON h_final.hecho_id = m.hecho_id AND h_final.fecha_ocurrencia = m.fecha_ocurrencia
ORDER BY m.max_score DESC NULLS LAST;

CREATE UNIQUE INDEX idx_hilos_sugeridos_hecho_id ON hilos_sugeridos_hechos(hecho_id, fecha_ocurrencia); -- Añadir fecha_ocurrencia por la partición
CREATE INDEX idx_hilos_sugeridos_max_score ON hilos_sugeridos_hechos(max_score DESC NULLS LAST);
CREATE INDEX idx_hilos_sugeridos_compat ON hilos_sugeridos_hechos(compatibilidad);

-- Comentario sobre hilos_sugeridos_hechos:
-- El cálculo del 'score' podría beneficiarse de una similitud textual directa
-- entre el contenido del hecho y la 'descripcion_hilo_curada' del hilo, por ejemplo:
-- COALESCE(similarity(h_rec.contenido, hn.descripcion_hilo_curada), 0.0) * X_WEIGHT
-- Esto podría añadirse al cálculo del score en el CTE 'compatibilidad_hilos'.
-- La efectividad y el peso (X_WEIGHT) deberían probarse.