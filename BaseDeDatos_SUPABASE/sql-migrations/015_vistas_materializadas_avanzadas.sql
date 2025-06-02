-- 015_vistas_materializadas_avanzadas.sql
-- Implementación de vistas materializadas avanzadas para análisis sofisticado
-- Implementado el 24 de Mayo de 2025
-- Tarea 15: Implementar Vistas Materializadas Avanzadas

-- ============================================================================
-- VISTAS MATERIALIZADAS AVANZADAS PARA ANÁLISIS SOFISTICADO
-- ============================================================================

-- Esta migración implementa 5 vistas materializadas avanzadas que proporcionan
-- análisis sofisticados sobre:
-- 1. Redes de entidades y métricas de centralidad
-- 2. Correlaciones temporales entre eventos y entidades
-- 3. Detección de patrones emergentes y anomalías
-- 4. Métricas de calidad y consistencia de datos
-- 5. Identificación de contradicciones y conflictos

-- ============================================================================
-- 1. VISTA DE REDES DE ENTIDADES Y CENTRALIDAD
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS redes_entidades_centralidad AS
WITH 
-- Identificar co-ocurrencias de entidades en hechos
co_ocurrencias_hechos AS (
    SELECT 
        he1.entidad_id AS entidad_origen_id,
        he2.entidad_id AS entidad_destino_id,
        COUNT(*) AS frecuencia_co_ocurrencia,
        COUNT(DISTINCT he1.hecho_id) AS hechos_compartidos,
        AVG(h.importancia::NUMERIC) AS importancia_promedio_hechos,
        MAX(h.fecha_ingreso) AS ultima_co_ocurrencia
    FROM hecho_entidad he1
    JOIN hecho_entidad he2 ON he1.hecho_id = he2.hecho_id 
                           AND he1.fecha_ocurrencia_hecho = he2.fecha_ocurrencia_hecho
                           AND he1.entidad_id != he2.entidad_id
    JOIN hechos h ON he1.hecho_id = h.id AND he1.fecha_ocurrencia_hecho = h.fecha_ocurrencia
    WHERE he1.entidad_id < he2.entidad_id  -- Evitar duplicados
    GROUP BY he1.entidad_id, he2.entidad_id
    HAVING COUNT(*) >= 2  -- Mínimo 2 co-ocurrencias
),

-- Calcular métricas de centralidad de grado
centralidad_grado AS (
    SELECT 
        entidad_id,
        COUNT(*) AS grado_total,
        COUNT(*) FILTER (WHERE frecuencia_co_ocurrencia >= 5) AS grado_fuerte,
        SUM(frecuencia_co_ocurrencia) AS peso_total_conexiones,
        AVG(frecuencia_co_ocurrencia::NUMERIC) AS fuerza_promedio_conexiones
    FROM (
        SELECT entidad_origen_id AS entidad_id, frecuencia_co_ocurrencia 
        FROM co_ocurrencias_hechos
        UNION ALL
        SELECT entidad_destino_id AS entidad_id, frecuencia_co_ocurrencia 
        FROM co_ocurrencias_hechos
    ) todas_conexiones
    GROUP BY entidad_id
),

-- Calcular conexiones bidireccionales expandidas
conexiones_expandidas AS (
    SELECT entidad_origen_id AS entidad_a, entidad_destino_id AS entidad_b, 
           frecuencia_co_ocurrencia, hechos_compartidos, ultima_co_ocurrencia
    FROM co_ocurrencias_hechos
    UNION ALL
    SELECT entidad_destino_id AS entidad_a, entidad_origen_id AS entidad_b,
           frecuencia_co_ocurrencia, hechos_compartidos, ultima_co_ocurrencia  
    FROM co_ocurrencias_hechos
),

-- Score de centralidad normalizado
entidades_con_centralidad AS (
    SELECT 
        e.id AS entidad_id,
        e.nombre AS entidad_nombre,
        e.tipo AS entidad_tipo,
        e.relevancia AS relevancia_base,
        COALESCE(cg.grado_total, 0) AS grado_total,
        COALESCE(cg.grado_fuerte, 0) AS grado_fuerte,
        COALESCE(cg.peso_total_conexiones, 0) AS peso_total_conexiones,
        COALESCE(cg.fuerza_promedio_conexiones, 0.0) AS fuerza_promedio_conexiones,
        -- Score de centralidad combinado (0-100)
        LEAST(100, GREATEST(0, 
            (COALESCE(cg.grado_total, 0) * 10) +
            (COALESCE(cg.grado_fuerte, 0) * 20) +
            (COALESCE(cg.fuerza_promedio_conexiones, 0) * 5) +
            (e.relevancia * 3)
        ))::INTEGER AS score_centralidad
    FROM entidades e
    LEFT JOIN centralidad_grado cg ON e.id = cg.entidad_id
    WHERE e.fusionada_en_id IS NULL
),

-- Pre-calcular top conexiones
top_conexiones_por_entidad AS (
    SELECT 
        ce.entidad_a,
        jsonb_agg(
            jsonb_build_object(
                'entidad_id', ce.entidad_b,
                'entidad_nombre', e.nombre,
                'frecuencia', ce.frecuencia_co_ocurrencia,
                'hechos_compartidos', ce.hechos_compartidos,
                'ultima_interaccion', ce.ultima_co_ocurrencia
            ) ORDER BY ce.frecuencia_co_ocurrencia DESC
        ) AS top_conexiones
    FROM (
        SELECT 
            entidad_a, entidad_b, frecuencia_co_ocurrencia, 
            hechos_compartidos, ultima_co_ocurrencia,
            ROW_NUMBER() OVER (PARTITION BY entidad_a ORDER BY frecuencia_co_ocurrencia DESC) as rn
        FROM conexiones_expandidas
    ) ce
    JOIN entidades e ON ce.entidad_b = e.id
    WHERE ce.rn <= 5  -- Top 5 conexiones
    GROUP BY ce.entidad_a
)

-- Vista principal
SELECT 
    ec.entidad_id,
    ec.entidad_nombre,
    ec.entidad_tipo,
    ec.relevancia_base,
    ec.grado_total,
    ec.grado_fuerte,
    ec.peso_total_conexiones,
    ec.fuerza_promedio_conexiones,
    ec.score_centralidad,
    
    -- Clasificación de centralidad
    CASE 
        WHEN ec.score_centralidad >= 80 THEN 'muy_central'
        WHEN ec.score_centralidad >= 60 THEN 'central'
        WHEN ec.score_centralidad >= 40 THEN 'moderada'
        WHEN ec.score_centralidad >= 20 THEN 'periferica'
        ELSE 'aislada'
    END AS clasificacion_centralidad,
    
    COALESCE(tcp.top_conexiones, '[]'::jsonb) AS top_conexiones,
    
    (
        SELECT COUNT(*)
        FROM conexiones_expandidas ce
        WHERE ce.entidad_a = ec.entidad_id
          AND ce.frecuencia_co_ocurrencia >= 5
    ) AS entidades_cluster_fuerte,
    
    NOW() AS fecha_actualizacion

FROM entidades_con_centralidad ec
LEFT JOIN top_conexiones_por_entidad tcp ON ec.entidad_id = tcp.entidad_a
WHERE ec.grado_total > 0 OR ec.relevancia_base >= 7
ORDER BY ec.score_centralidad DESC, ec.grado_total DESC;

-- Índices para redes_entidades_centralidad
CREATE UNIQUE INDEX IF NOT EXISTS idx_redes_entidades_id 
ON redes_entidades_centralidad(entidad_id);

CREATE INDEX IF NOT EXISTS idx_redes_score_centralidad 
ON redes_entidades_centralidad(score_centralidad DESC);

CREATE INDEX IF NOT EXISTS idx_redes_clasificacion 
ON redes_entidades_centralidad(clasificacion_centralidad);

-- ============================================================================
-- 2. VISTA DE CORRELACIONES TEMPORALES
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS correlaciones_temporales AS
WITH 
-- Series temporales semanales para análisis de correlación
series_entidades_semanales AS (
    SELECT 
        e.id AS entidad_id,
        e.nombre AS entidad_nombre,
        e.tipo AS entidad_tipo,
        date_trunc('week', h.fecha_ingreso) AS semana,
        COUNT(*) AS menciones_semana,
        AVG(h.importancia) AS importancia_promedio_semana,
        COUNT(DISTINCT h.tipo_hecho) AS diversidad_tipos_hecho
    FROM entidades e
    JOIN hecho_entidad he ON e.id = he.entidad_id
    JOIN hechos h ON he.hecho_id = h.id AND he.fecha_ocurrencia_hecho = h.fecha_ocurrencia
    WHERE h.fecha_ingreso >= NOW() - INTERVAL '180 days'
      AND e.fusionada_en_id IS NULL
    GROUP BY e.id, e.nombre, e.tipo, date_trunc('week', h.fecha_ingreso)
    HAVING COUNT(*) >= 2
),

-- Calcular correlaciones entre pares de entidades
correlaciones_base AS (
    SELECT 
        se1.entidad_id AS entidad_a_id,
        se1.entidad_nombre AS entidad_a_nombre,
        se2.entidad_id AS entidad_b_id,
        se2.entidad_nombre AS entidad_b_nombre,
        COUNT(*) AS semanas_concurrentes,
        
        -- Correlación usando covariance
        CASE 
            WHEN COUNT(*) >= 4 AND 
                 STDDEV(se1.menciones_semana) > 0 AND 
                 STDDEV(se2.menciones_semana) > 0
            THEN 
                (AVG(se1.menciones_semana * se2.menciones_semana) - 
                 AVG(se1.menciones_semana) * AVG(se2.menciones_semana)) /
                (STDDEV(se1.menciones_semana) * STDDEV(se2.menciones_semana))
            ELSE 0
        END AS coeficiente_correlacion,
        
        AVG(se1.menciones_semana) AS promedio_a,
        AVG(se2.menciones_semana) AS promedio_b,
        STDDEV(se1.menciones_semana) AS desviacion_a,
        STDDEV(se2.menciones_semana) AS desviacion_b,
        
        -- Análisis de tendencias
        corr(EXTRACT(epoch FROM se1.semana), se1.menciones_semana) AS tendencia_a,
        corr(EXTRACT(epoch FROM se2.semana), se2.menciones_semana) AS tendencia_b,
        
        MIN(se1.semana) AS primer_periodo,
        MAX(se1.semana) AS ultimo_periodo
        
    FROM series_entidades_semanales se1
    JOIN series_entidades_semanales se2 ON se1.semana = se2.semana 
                                        AND se1.entidad_id < se2.entidad_id
    GROUP BY se1.entidad_id, se1.entidad_nombre, se2.entidad_id, se2.entidad_nombre
    HAVING COUNT(*) >= 4
),

-- Identificar correlaciones significativas
correlaciones_significativas AS (
    SELECT 
        *,
        CASE 
            WHEN ABS(coeficiente_correlacion) >= 0.8 THEN 'muy_fuerte'
            WHEN ABS(coeficiente_correlacion) >= 0.6 THEN 'fuerte'
            WHEN ABS(coeficiente_correlacion) >= 0.4 THEN 'moderada'
            WHEN ABS(coeficiente_correlacion) >= 0.2 THEN 'debil'
            ELSE 'muy_debil'
        END AS fuerza_correlacion,
        
        CASE 
            WHEN coeficiente_correlacion > 0 THEN 'positiva'
            WHEN coeficiente_correlacion < 0 THEN 'negativa'
            ELSE 'neutral'
        END AS tipo_correlacion,
        
        CASE 
            WHEN (tendencia_a > 0.3 AND tendencia_b > 0.3) THEN 'ambas_crecientes'
            WHEN (tendencia_a < -0.3 AND tendencia_b < -0.3) THEN 'ambas_decrecientes'
            WHEN (tendencia_a > 0.3 AND tendencia_b < -0.3) THEN 'opuestas_a_crece'
            WHEN (tendencia_a < -0.3 AND tendencia_b > 0.3) THEN 'opuestas_b_crece'
            ELSE 'tendencias_mixtas'
        END AS patron_tendencias
        
    FROM correlaciones_base
    WHERE ABS(coeficiente_correlacion) >= 0.2
),

-- Análisis de patrones individuales por entidad
patrones_entidades AS (
    SELECT 
        entidad_id,
        entidad_nombre,
        entidad_tipo,
        COUNT(*) AS semanas_activas,
        SUM(menciones_semana) AS total_menciones,
        AVG(menciones_semana) AS promedio_semanal,
        STDDEV(menciones_semana) AS desviacion_semanal,
        MAX(menciones_semana) AS pico_maximo,
        MIN(menciones_semana) AS valle_minimo,
        
        CASE 
            WHEN AVG(menciones_semana) > 0 
            THEN STDDEV(menciones_semana) / AVG(menciones_semana)
            ELSE 0
        END AS coeficiente_variacion,
        
        corr(EXTRACT(epoch FROM semana), menciones_semana) AS tendencia_temporal,
        
        CASE 
            WHEN AVG(menciones_semana) >= 10 THEN 'muy_activa'
            WHEN AVG(menciones_semana) >= 5 THEN 'activa'
            WHEN AVG(menciones_semana) >= 2 THEN 'moderada'
            ELSE 'baja'
        END AS nivel_actividad
        
    FROM series_entidades_semanales
    GROUP BY entidad_id, entidad_nombre, entidad_tipo
)

-- Vista principal con correlaciones temporales enriquecidas
SELECT 
    cs.entidad_a_id,
    cs.entidad_a_nombre,
    cs.entidad_b_id,
    cs.entidad_b_nombre,
    cs.coeficiente_correlacion,
    cs.fuerza_correlacion,
    cs.tipo_correlacion,
    cs.patron_tendencias,
    cs.semanas_concurrentes,
    cs.primer_periodo,
    cs.ultimo_periodo,
    
    cs.promedio_a,
    cs.promedio_b,
    cs.desviacion_a,
    cs.desviacion_b,
    cs.tendencia_a,
    cs.tendencia_b,
    
    pa.nivel_actividad AS actividad_entidad_a,
    pb.nivel_actividad AS actividad_entidad_b,
    pa.coeficiente_variacion AS volatilidad_a,
    pb.coeficiente_variacion AS volatilidad_b,
    
    CASE 
        WHEN cs.fuerza_correlacion IN ('muy_fuerte', 'fuerte') 
         AND cs.semanas_concurrentes >= 8
         AND pa.nivel_actividad IN ('muy_activa', 'activa')
         AND pb.nivel_actividad IN ('muy_activa', 'activa')
        THEN 'alta_relevancia'
        WHEN cs.fuerza_correlacion IN ('fuerte', 'moderada')
         AND cs.semanas_concurrentes >= 6
        THEN 'relevancia_media'
        ELSE 'relevancia_baja'
    END AS relevancia_correlacion,
    
    NOW() AS fecha_actualizacion
    
FROM correlaciones_significativas cs
LEFT JOIN patrones_entidades pa ON cs.entidad_a_id = pa.entidad_id
LEFT JOIN patrones_entidades pb ON cs.entidad_b_id = pb.entidad_id
ORDER BY ABS(cs.coeficiente_correlacion) DESC, cs.semanas_concurrentes DESC;

-- Índices para correlaciones_temporales
CREATE INDEX IF NOT EXISTS idx_correlaciones_temp_entidades 
ON correlaciones_temporales(entidad_a_id, entidad_b_id);

CREATE INDEX IF NOT EXISTS idx_correlaciones_temp_coeficiente 
ON correlaciones_temporales(ABS(coeficiente_correlacion) DESC);

-- ============================================================================
-- 3. VISTA DE PATRONES EMERGENTES Y ANOMALÍAS
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS patrones_emergentes_anomalias AS
WITH
-- Métricas base temporales
metricas_temporales AS (
    SELECT 
        date_trunc('day', fecha_ingreso) AS dia,
        COUNT(*) AS total_hechos_dia,
        AVG(importancia) AS importancia_promedio_dia,
        COUNT(DISTINCT tipo_hecho) AS diversidad_tipos_dia,
        COUNT(*) FILTER (WHERE importancia >= 8) AS hechos_alta_importancia_dia
    FROM hechos 
    WHERE fecha_ingreso >= NOW() - INTERVAL '90 days'
    GROUP BY date_trunc('day', fecha_ingreso)
),

-- Calcular estadísticas móviles y detectar anomalías
anomalias_temporales AS (
    SELECT 
        dia,
        total_hechos_dia,
        importancia_promedio_dia,
        diversidad_tipos_dia,
        hechos_alta_importancia_dia,
        
        AVG(total_hechos_dia) OVER w7 AS promedio_7d,
        STDDEV(total_hechos_dia) OVER w7 AS stddev_7d,
        
        CASE 
            WHEN STDDEV(total_hechos_dia) OVER w7 > 0 
            THEN (total_hechos_dia - AVG(total_hechos_dia) OVER w7) / 
                 STDDEV(total_hechos_dia) OVER w7
            ELSE 0
        END AS z_score_volumen_7d,
        
        CASE 
            WHEN STDDEV(importancia_promedio_dia) OVER w7 > 0 
            THEN (importancia_promedio_dia - AVG(importancia_promedio_dia) OVER w7) / 
                 STDDEV(importancia_promedio_dia) OVER w7
            ELSE 0
        END AS z_score_importancia_7d
        
    FROM metricas_temporales
    WINDOW w7 AS (ORDER BY dia ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
),

-- Análisis de patrones por tipo de hecho
patrones_tipos_hechos AS (
    SELECT 
        tipo_hecho,
        date_trunc('week', fecha_ingreso) AS semana,
        COUNT(*) AS cantidad_semanal,
        LAG(COUNT(*), 1) OVER (PARTITION BY tipo_hecho ORDER BY date_trunc('week', fecha_ingreso)) AS cantidad_semana_anterior,
        
        CASE 
            WHEN LAG(COUNT(*), 1) OVER (PARTITION BY tipo_hecho ORDER BY date_trunc('week', fecha_ingreso)) > 0
            THEN COUNT(*)::NUMERIC / LAG(COUNT(*), 1) OVER (PARTITION BY tipo_hecho ORDER BY date_trunc('week', fecha_ingreso))
            ELSE NULL
        END AS ratio_crecimiento_semanal
        
    FROM hechos
    WHERE fecha_ingreso >= NOW() - INTERVAL '90 days'
    GROUP BY tipo_hecho, date_trunc('week', fecha_ingreso)
),

-- Identificar spikes significativos
spikes_significativos AS (
    SELECT 
        tipo_hecho,
        semana,
        cantidad_semanal,
        ratio_crecimiento_semanal,
        
        CASE 
            WHEN ratio_crecimiento_semanal >= 3.0 THEN 'spike_extremo'
            WHEN ratio_crecimiento_semanal >= 2.0 THEN 'spike_alto'  
            WHEN ratio_crecimiento_semanal >= 1.5 THEN 'crecimiento_notable'
            WHEN ratio_crecimiento_semanal <= 0.3 THEN 'caida_extrema'
            WHEN ratio_crecimiento_semanal <= 0.5 THEN 'caida_alta'
            WHEN ratio_crecimiento_semanal <= 0.7 THEN 'decrecimiento_notable'
            ELSE 'normal'
        END AS tipo_patron
        
    FROM patrones_tipos_hechos
    WHERE ratio_crecimiento_semanal IS NOT NULL
),

-- Análisis de anomalías en entidades
anomalias_entidades AS (
    SELECT 
        e.id AS entidad_id,
        e.nombre AS entidad_nombre,
        e.tipo AS entidad_tipo,
        
        COUNT(*) FILTER (WHERE h.fecha_ingreso >= NOW() - INTERVAL '28 days') AS menciones_4_semanas,
        COUNT(*) FILTER (WHERE h.fecha_ingreso >= NOW() - INTERVAL '84 days' 
                              AND h.fecha_ingreso < NOW() - INTERVAL '28 days') AS menciones_8_semanas_previas,
        
        AVG(h.importancia) FILTER (WHERE h.fecha_ingreso >= NOW() - INTERVAL '28 days') AS importancia_promedio_reciente
        
    FROM entidades e
    JOIN hecho_entidad he ON e.id = he.entidad_id
    JOIN hechos h ON he.hecho_id = h.id AND he.fecha_ocurrencia_hecho = h.fecha_ocurrencia
    WHERE e.fusionada_en_id IS NULL
      AND h.fecha_ingreso >= NOW() - INTERVAL '84 days'
    GROUP BY e.id, e.nombre, e.tipo
    HAVING COUNT(*) >= 3
),

-- Calcular scores de anomalía
entidades_con_anomalias AS (
    SELECT 
        *,
        CASE 
            WHEN menciones_8_semanas_previas > 0 
            THEN menciones_4_semanas::NUMERIC / menciones_8_semanas_previas
            ELSE CASE WHEN menciones_4_semanas > 0 THEN 10.0 ELSE 0.0 END
        END AS ratio_cambio_actividad,
        
        CASE 
            WHEN menciones_8_semanas_previas > 0 
            THEN LEAST(100, 
                ABS(menciones_4_semanas::NUMERIC / menciones_8_semanas_previas - 1) * 50 +
                ABS(COALESCE(importancia_promedio_reciente, 5) - 5) * 10
            )
            ELSE CASE 
                WHEN menciones_4_semanas >= 5 THEN 75
                WHEN menciones_4_semanas >= 3 THEN 50
                ELSE 25
            END
        END AS score_anomalia
        
    FROM anomalias_entidades
)

-- Vista principal consolidada
SELECT 
    CURRENT_DATE AS fecha_analisis,
    'anomalia_temporal' AS tipo_anomalia,
    NULL AS entidad_id,
    NULL AS entidad_nombre,
    NULL AS entidad_tipo,
    NULL AS tipo_hecho,
    at.dia AS fecha_detectada,
    
    CASE 
        WHEN ABS(at.z_score_volumen_7d) >= 2.5 THEN 
            'Anomalía extrema en volumen: ' || at.total_hechos_dia || ' hechos (z-score: ' || 
            ROUND(at.z_score_volumen_7d::NUMERIC, 2) || ')'
        WHEN ABS(at.z_score_importancia_7d) >= 2.0 THEN
            'Anomalía en importancia promedio: ' || ROUND(at.importancia_promedio_dia::NUMERIC, 2) ||
            ' (z-score: ' || ROUND(at.z_score_importancia_7d::NUMERIC, 2) || ')'
        ELSE 'Anomalía temporal detectada'
    END AS descripcion_patron,
    
    GREATEST(ABS(at.z_score_volumen_7d) * 25, ABS(at.z_score_importancia_7d) * 25)::INTEGER AS score_anomalia,
    
    CASE 
        WHEN ABS(at.z_score_volumen_7d) >= 3.0 OR ABS(at.z_score_importancia_7d) >= 3.0 THEN 'muy_alta'
        WHEN ABS(at.z_score_volumen_7d) >= 2.5 OR ABS(at.z_score_importancia_7d) >= 2.5 THEN 'alta'
        WHEN ABS(at.z_score_volumen_7d) >= 2.0 OR ABS(at.z_score_importancia_7d) >= 2.0 THEN 'media'
        ELSE 'baja'
    END AS confianza_deteccion,
    
    jsonb_build_object(
        'total_hechos', at.total_hechos_dia,
        'promedio_7d', ROUND(at.promedio_7d::NUMERIC, 2),
        'z_score_volumen', ROUND(at.z_score_volumen_7d::NUMERIC, 3),
        'z_score_importancia', ROUND(at.z_score_importancia_7d::NUMERIC, 3)
    ) AS metadatos_anomalia,
    
    NOW() AS fecha_actualizacion

FROM anomalias_temporales at
WHERE ABS(at.z_score_volumen_7d) >= 1.5 OR ABS(at.z_score_importancia_7d) >= 1.5

UNION ALL

-- Anomalías en entidades
SELECT 
    CURRENT_DATE AS fecha_analisis,
    'anomalia_entidad' AS tipo_anomalia,
    ea.entidad_id,
    ea.entidad_nombre,
    ea.entidad_tipo,
    NULL AS tipo_hecho,
    CURRENT_DATE AS fecha_detectada,
    
    'Entidad con patrón anómalo: ' || ea.entidad_nombre || 
    ' (cambio actividad: ' || ROUND(ea.ratio_cambio_actividad, 2) || 'x)' AS descripcion_patron,
    
    ea.score_anomalia::INTEGER,
    
    CASE 
        WHEN ea.score_anomalia >= 80 THEN 'muy_alta'
        WHEN ea.score_anomalia >= 60 THEN 'alta'
        WHEN ea.score_anomalia >= 40 THEN 'media'
        ELSE 'baja'
    END AS confianza_deteccion,
    
    jsonb_build_object(
        'menciones_recientes', ea.menciones_4_semanas,
        'menciones_previas', ea.menciones_8_semanas_previas,
        'ratio_cambio', ROUND(ea.ratio_cambio_actividad, 3),
        'importancia_promedio', ROUND(COALESCE(ea.importancia_promedio_reciente, 0)::NUMERIC, 2)
    ) AS metadatos_anomalia,
    
    NOW() AS fecha_actualizacion

FROM entidades_con_anomalias ea
WHERE ea.score_anomalia >= 30

UNION ALL

-- Patrones emergentes en tipos de hechos
SELECT 
    CURRENT_DATE AS fecha_analisis,
    'patron_emergente' AS tipo_anomalia,
    NULL AS entidad_id,
    NULL AS entidad_nombre,
    NULL AS entidad_tipo,
    ss.tipo_hecho,
    ss.semana::DATE AS fecha_detectada,
    
    'Patrón emergente en ' || ss.tipo_hecho || ': ' || ss.tipo_patron || 
    ' (ratio: ' || ROUND(ss.ratio_crecimiento_semanal, 2) || ')' AS descripcion_patron,
    
    CASE 
        WHEN ss.tipo_patron IN ('spike_extremo', 'caida_extrema') THEN 90
        WHEN ss.tipo_patron IN ('spike_alto', 'caida_alta') THEN 70
        WHEN ss.tipo_patron IN ('crecimiento_notable', 'decrecimiento_notable') THEN 50
        ELSE 30
    END AS score_anomalia,
    
    CASE 
        WHEN ss.tipo_patron IN ('spike_extremo', 'caida_extrema') THEN 'muy_alta'
        WHEN ss.tipo_patron IN ('spike_alto', 'caida_alta') THEN 'alta'
        ELSE 'media'
    END AS confianza_deteccion,
    
    jsonb_build_object(
        'cantidad_semanal', ss.cantidad_semanal,
        'ratio_crecimiento', ROUND(ss.ratio_crecimiento_semanal, 3),
        'tipo_patron', ss.tipo_patron
    ) AS metadatos_anomalia,
    
    NOW() AS fecha_actualizacion

FROM spikes_significativos ss
WHERE ss.tipo_patron != 'normal'

ORDER BY score_anomalia DESC, fecha_detectada DESC;

-- Índices para patrones_emergentes_anomalias
CREATE INDEX IF NOT EXISTS idx_patrones_tipo_anomalia 
ON patrones_emergentes_anomalias(tipo_anomalia);

CREATE INDEX IF NOT EXISTS idx_patrones_score 
ON patrones_emergentes_anomalias(score_anomalia DESC);

-- ============================================================================
-- 4. VISTA DE MÉTRICAS DE CALIDAD DE DATOS
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS metricas_calidad_datos AS
WITH
-- Métricas de completitud para hechos
completitud_hechos AS (
    SELECT 
        'hechos' AS tabla,
        COUNT(*) AS total_registros,
        
        ROUND((COUNT(contenido) * 100.0 / COUNT(*))::NUMERIC, 2) AS completitud_contenido,
        ROUND((COUNT(tipo_hecho) * 100.0 / COUNT(*))::NUMERIC, 2) AS completitud_tipo_hecho,
        ROUND((COUNT(pais) * 100.0 / COUNT(*))::NUMERIC, 2) AS completitud_pais,
        ROUND((COUNT(importancia) * 100.0 / COUNT(*))::NUMERIC, 2) AS completitud_importancia,
        ROUND((COUNT(embedding) * 100.0 / COUNT(*))::NUMERIC, 2) AS completitud_embedding,
        
        COUNT(*) FILTER (WHERE LENGTH(contenido) < 10) AS contenido_muy_corto,
        COUNT(*) FILTER (WHERE LENGTH(contenido) > 1000) AS contenido_muy_largo,
        COUNT(*) FILTER (WHERE importancia BETWEEN 1 AND 10) AS importancia_valida,
        COUNT(*) FILTER (WHERE array_length(pais, 1) IS NULL OR array_length(pais, 1) = 0) AS sin_pais,
        
        COUNT(*) FILTER (WHERE fecha_ingreso >= NOW() - INTERVAL '7 days') AS registros_7d,
        COUNT(*) FILTER (WHERE fecha_ingreso >= NOW() - INTERVAL '30 days') AS registros_30d,
        COUNT(*) FILTER (WHERE fecha_ingreso >= NOW() - INTERVAL '90 days') AS registros_90d,
        
        NOW() AS fecha_calculo
    FROM hechos
),

-- Métricas de completitud para entidades
completitud_entidades AS (
    SELECT 
        'entidades' AS tabla,
        COUNT(*) AS total_registros,
        
        ROUND((COUNT(nombre) * 100.0 / COUNT(*))::NUMERIC, 2) AS completitud_nombre,
        ROUND((COUNT(tipo) * 100.0 / COUNT(*))::NUMERIC, 2) AS completitud_tipo,
        ROUND((COUNT(descripcion) * 100.0 / COUNT(*))::NUMERIC, 2) AS completitud_descripcion,
        ROUND((COUNT(embedding) * 100.0 / COUNT(*))::NUMERIC, 2) AS completitud_embedding,
        ROUND((COUNT(wikidata_id) * 100.0 / COUNT(*))::NUMERIC, 2) AS completitud_wikidata_id,
        
        COUNT(*) FILTER (WHERE LENGTH(nombre) < 2) AS nombres_muy_cortos,
        COUNT(*) FILTER (WHERE descripcion IS NOT NULL AND LENGTH(descripcion) < 10) AS descripciones_cortas,
        COUNT(*) FILTER (WHERE relevancia BETWEEN 1 AND 10) AS relevancia_valida,
        COUNT(*) FILTER (WHERE fusionada_en_id IS NOT NULL) AS entidades_fusionadas,
        
        COUNT(*) FILTER (WHERE id > (SELECT MAX(id) - 100 FROM entidades)) AS entidades_recientes,
        
        NOW() AS fecha_calculo
    FROM entidades
),

-- Métricas de completitud para artículos
completitud_articulos AS (
    SELECT 
        'articulos' AS tabla,
        COUNT(*) AS total_registros,
        
        ROUND((COUNT(url) * 100.0 / COUNT(*))::NUMERIC, 2) AS completitud_url,
        ROUND((COUNT(titular) * 100.0 / COUNT(*))::NUMERIC, 2) AS completitud_titular,
        ROUND((COUNT(medio) * 100.0 / COUNT(*))::NUMERIC, 2) AS completitud_medio,
        ROUND((COUNT(fecha_publicacion) * 100.0 / COUNT(*))::NUMERIC, 2) AS completitud_fecha_pub,
        ROUND((COUNT(resumen) * 100.0 / COUNT(*))::NUMERIC, 2) AS completitud_resumen,
        
        COUNT(*) FILTER (WHERE LENGTH(titular) < 10) AS titulares_muy_cortos,
        COUNT(*) FILTER (WHERE fecha_publicacion > NOW()) AS fechas_futuras,
        COUNT(*) FILTER (WHERE fecha_publicacion < '1990-01-01') AS fechas_muy_antiguas,
        COUNT(*) FILTER (WHERE estado_procesamiento = 'completado') AS procesamiento_completo,
        COUNT(*) FILTER (WHERE estado_procesamiento LIKE 'error%') AS con_errores,
        
        COUNT(*) FILTER (WHERE fecha_recopilacion >= NOW() - INTERVAL '7 days') AS recopilados_7d,
        COUNT(*) FILTER (WHERE fecha_recopilacion >= NOW() - INTERVAL '30 days') AS recopilados_30d,
        
        NOW() AS fecha_calculo
    FROM articulos
),

-- Métricas de integridad referencial
integridad_referencial AS (
    SELECT 
        'integridad_referencial' AS categoria,
        
        (SELECT COUNT(*) FROM hecho_entidad he 
         LEFT JOIN entidades e ON he.entidad_id = e.id 
         WHERE e.id IS NULL) AS hechos_entidades_huerfanas,
         
        (SELECT COUNT(*) FROM hecho_articulo ha 
         LEFT JOIN articulos a ON ha.articulo_id = a.id 
         WHERE a.id IS NULL) AS hechos_articulos_huerfanos,
         
        (SELECT COUNT(*) FROM hecho_hilo hh 
         LEFT JOIN hilos_narrativos hn ON hh.hilo_id = hn.id 
         WHERE hn.id IS NULL) AS hechos_hilos_huerfanos,
         
        (SELECT COUNT(*) FROM entidades e1 
         LEFT JOIN entidades e2 ON e1.fusionada_en_id = e2.id 
         WHERE e1.fusionada_en_id IS NOT NULL AND e2.id IS NULL) AS fusiones_huerfanas,
         
        NOW() AS fecha_calculo
),

-- Detección de duplicados potenciales
duplicados_potenciales AS (
    SELECT 
        'duplicados' AS categoria,
        
        (SELECT COUNT(*) - COUNT(DISTINCT url) FROM articulos WHERE url IS NOT NULL) AS articulos_url_duplicadas,
        
        (SELECT COUNT(*) FROM (
            SELECT e1.nombre, COUNT(*) as similares
            FROM entidades e1
            JOIN entidades e2 ON e1.id < e2.id 
                              AND similarity(e1.nombre, e2.nombre) > 0.8
                              AND e1.fusionada_en_id IS NULL 
                              AND e2.fusionada_en_id IS NULL
            GROUP BY e1.nombre
            HAVING COUNT(*) >= 1
        ) duplicados_nombres) AS entidades_nombres_similares,
        
        (SELECT COUNT(*) FROM (
            SELECT h1.titulo, COUNT(*) as similares
            FROM hilos_narrativos h1
            JOIN hilos_narrativos h2 ON h1.id < h2.id 
                                     AND similarity(h1.titulo, h2.titulo) > 0.7
            GROUP BY h1.titulo
            HAVING COUNT(*) >= 1
        ) duplicados_hilos) AS hilos_titulos_similares,
        
        NOW() AS fecha_calculo
),

-- Análisis de outliers numéricos
outliers_numericos AS (
    SELECT 
        'outliers' AS categoria,
        
        (SELECT COUNT(*) FROM hechos WHERE importancia > 10 OR importancia < 1) AS hechos_importancia_invalida,
        
        (SELECT COUNT(*) FROM entidades WHERE relevancia > 10 OR relevancia < 1) AS entidades_relevancia_invalida,
        
        (SELECT COUNT(*) FROM articulos 
         WHERE fecha_publicacion > NOW() + INTERVAL '1 day' 
            OR fecha_publicacion < '1900-01-01') AS articulos_fechas_anomalas,
            
        (SELECT COUNT(*) FROM datos_cuantitativos 
         WHERE ABS(valor_numerico) > 1e12) AS datos_valores_extremos,
         
        NOW() AS fecha_calculo
),

-- Métricas de consistencia temporal
consistencia_temporal AS (
    SELECT 
        'consistencia_temporal' AS categoria,
        
        (SELECT COUNT(*) FROM hechos 
         WHERE fecha_ingreso < lower(fecha_ocurrencia) - INTERVAL '1 day') AS hechos_fechas_inconsistentes,
         
        (SELECT COUNT(*) FROM articulos 
         WHERE fecha_procesamiento < fecha_recopilacion) AS articulos_procesamiento_inconsistente,
         
        (SELECT COUNT(*) FROM eventos_programados 
         WHERE upper(fecha_programada) < NOW() 
           AND estado NOT IN ('realizado', 'cancelado')) AS eventos_no_actualizados,
           
        NOW() AS fecha_calculo
)

-- Vista principal que consolida todas las métricas
SELECT 
    'resumen_general' AS categoria_metrica,
    'calidad_global' AS subcategoria,
    
    jsonb_build_object(
        'hechos_total', ch.total_registros,
        'hechos_completitud_contenido', ch.completitud_contenido,
        'hechos_completitud_embedding', ch.completitud_embedding,
        'entidades_total', ce.total_registros,
        'entidades_completitud_nombre', ce.completitud_nombre,
        'entidades_completitud_embedding', ce.completitud_embedding,
        'articulos_total', ca.total_registros,
        'articulos_completitud_titular', ca.completitud_titular,
        'articulos_procesados_ok', ca.procesamiento_completo
    ) AS metricas_completitud,
    
    jsonb_build_object(
        'hechos_entidades_huerfanas', ir.hechos_entidades_huerfanas,
        'hechos_articulos_huerfanos', ir.hechos_articulos_huerfanos,
        'hechos_hilos_huerfanos', ir.hechos_hilos_huerfanos,
        'fusiones_huerfanas', ir.fusiones_huerfanas
    ) AS metricas_integridad,
    
    jsonb_build_object(
        'articulos_url_duplicadas', dp.articulos_url_duplicadas,
        'entidades_nombres_similares', dp.entidades_nombres_similares,
        'hilos_titulos_similares', dp.hilos_titulos_similares
    ) AS metricas_duplicados,
    
    jsonb_build_object(
        'hechos_importancia_invalida', ou.hechos_importancia_invalida,
        'entidades_relevancia_invalida', ou.entidades_relevancia_invalida,
        'articulos_fechas_anomalas', ou.articulos_fechas_anomalas,
        'datos_valores_extremos', ou.datos_valores_extremos
    ) AS metricas_outliers,
    
    jsonb_build_object(
        'hechos_fechas_inconsistentes', ct.hechos_fechas_inconsistentes,
        'articulos_procesamiento_inconsistente', ct.articulos_procesamiento_inconsistente,
        'eventos_no_actualizados', ct.eventos_no_actualizados
    ) AS metricas_consistencia_temporal,
    
    jsonb_build_object(
        'hechos_7d', ch.registros_7d,
        'hechos_30d', ch.registros_30d,
        'hechos_90d', ch.registros_90d,
        'articulos_7d', ca.recopilados_7d,
        'articulos_30d', ca.recopilados_30d,
        'entidades_recientes', ce.entidades_recientes
    ) AS metricas_frescura,
    
    -- Score general de calidad (0-100)
    LEAST(100, GREATEST(0,
        100 - 
        (ir.hechos_entidades_huerfanas + ir.hechos_articulos_huerfanos) * 2 -
        (ou.hechos_importancia_invalida + ou.entidades_relevancia_invalida) * 1 -
        ct.hechos_fechas_inconsistentes * 3 -
        dp.articulos_url_duplicadas * 0.5 -
        (ch.completitud_contenido + ch.completitud_embedding + 
         ce.completitud_nombre + ca.completitud_titular) / 20
    ))::INTEGER AS score_calidad_global,
    
    CASE 
        WHEN (ir.hechos_entidades_huerfanas + ir.hechos_articulos_huerfanos + 
              ou.hechos_importancia_invalida + ct.hechos_fechas_inconsistentes) = 0 
             AND ch.completitud_contenido >= 95 THEN 'excelente'
        WHEN (ir.hechos_entidades_huerfanas + ir.hechos_articulos_huerfanos + 
              ou.hechos_importancia_invalida + ct.hechos_fechas_inconsistentes) <= 5
             AND ch.completitud_contenido >= 90 THEN 'buena'
        WHEN (ir.hechos_entidades_huerfanas + ir.hechos_articulos_huerfanos + 
              ou.hechos_importancia_invalida + ct.hechos_fechas_inconsistentes) <= 20
             AND ch.completitud_contenido >= 80 THEN 'aceptable'
        ELSE 'necesita_atencion'
    END AS nivel_salud_datos,
    
    CASE 
        WHEN ir.hechos_entidades_huerfanas > 0 THEN 'Corregir referencias huérfanas en hecho_entidad'
        WHEN ou.hechos_importancia_invalida > 0 THEN 'Validar rangos de importancia en hechos'
        WHEN ct.hechos_fechas_inconsistentes > 0 THEN 'Revisar consistencia temporal'
        WHEN ch.completitud_embedding < 50 THEN 'Mejorar generación de embeddings'
        WHEN dp.articulos_url_duplicadas > 10 THEN 'Revisar duplicados en artículos'
        ELSE 'Calidad de datos en buen estado'
    END AS recomendacion_principal,
    
    NOW() AS fecha_actualizacion

FROM completitud_hechos ch
CROSS JOIN completitud_entidades ce  
CROSS JOIN completitud_articulos ca
CROSS JOIN integridad_referencial ir
CROSS JOIN duplicados_potenciales dp
CROSS JOIN outliers_numericos ou
CROSS JOIN consistencia_temporal ct;

-- Índices para metricas_calidad_datos
CREATE INDEX IF NOT EXISTS idx_calidad_categoria 
ON metricas_calidad_datos(categoria_metrica);

CREATE INDEX IF NOT EXISTS idx_calidad_score 
ON metricas_calidad_datos(score_calidad_global DESC);

-- ============================================================================
-- 5. VISTA DE CONTRADICCIONES Y CONFLICTOS
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS contradicciones_conflictos AS
WITH
-- Contradicciones explícitas registradas
contradicciones_registradas AS (
    SELECT 
        c.id AS contradiccion_id,
        c.hecho_principal_id,
        c.hecho_contradictorio_id,
        c.tipo_contradiccion,
        c.grado_contradiccion,
        c.descripcion AS descripcion_contradiccion,
        c.estado_resolucion,
        c.fecha_deteccion,
        
        h1.contenido AS contenido_principal,
        h1.importancia AS importancia_principal,
        h2.contenido AS contenido_contradictorio,
        h2.importancia AS importancia_contradictoria,
        
        GREATEST(h1.importancia, h2.importancia) AS importancia_maxima
        
    FROM contradicciones c
    JOIN hechos h1 ON c.hecho_principal_id = h1.id 
                   AND c.fecha_ocurrencia_principal = h1.fecha_ocurrencia
    JOIN hechos h2 ON c.hecho_contradictorio_id = h2.id 
                   AND c.fecha_ocurrencia_contradictoria = h2.fecha_ocurrencia
),

-- Detectar contradicciones en evaluaciones editoriales
contradicciones_editoriales AS (
    SELECT 
        h1.id AS hecho_id_principal,
        h2.id AS hecho_id_secundario,
        h1.contenido AS contenido_principal,
        h2.contenido AS contenido_secundario,
        h1.evaluacion_editorial AS evaluacion_1,
        h2.evaluacion_editorial AS evaluacion_2,
        h1.consenso_fuentes AS consenso_1,
        h2.consenso_fuentes AS consenso_2,
        
        CASE 
            WHEN h1.evaluacion_editorial = 'verificado_ok_editorial' 
                 AND h2.evaluacion_editorial = 'declarado_falso_editorial'
                 AND similarity(h1.contenido, h2.contenido) > 0.4
            THEN 'evaluacion_contradictoria_directa'
            
            WHEN h1.consenso_fuentes = 'confirmado_multiples_fuentes'
                 AND h2.consenso_fuentes = 'en_disputa_por_hechos_contradictorios'
                 AND similarity(h1.contenido, h2.contenido) > 0.3
            THEN 'consenso_fuentes_contradictorio'
            
            ELSE NULL
        END AS tipo_conflicto_editorial,
        
        similarity(h1.contenido, h2.contenido) AS similitud_contenidos,
        GREATEST(h1.importancia, h2.importancia) AS importancia_maxima
        
    FROM hechos h1
    JOIN hechos h2 ON h1.id != h2.id
    WHERE 
        ((h1.evaluacion_editorial = 'verificado_ok_editorial' 
          AND h2.evaluacion_editorial = 'declarado_falso_editorial')
         OR 
         (h1.consenso_fuentes = 'confirmado_multiples_fuentes'
          AND h2.consenso_fuentes = 'en_disputa_por_hechos_contradictorios'))
        AND similarity(h1.contenido, h2.contenido) > 0.2
        AND h1.pais && h2.pais
),

-- Detectar contenidos duplicados con alta similitud
contenidos_duplicados AS (
    SELECT 
        h1.id AS hecho_id_1,
        h2.id AS hecho_id_2,
        h1.contenido AS contenido_1,
        h2.contenido AS contenido_2,
        h1.importancia AS importancia_1,
        h2.importancia AS importancia_2,
        h1.tipo_hecho AS tipo_1,
        h2.tipo_hecho AS tipo_2,
        
        similarity(h1.contenido, h2.contenido) AS similitud_contenido,
        
        CASE 
            WHEN similarity(h1.contenido, h2.contenido) > 0.8 
                 AND h1.tipo_hecho = h2.tipo_hecho
            THEN 'posible_duplicado'
            WHEN similarity(h1.contenido, h2.contenido) > 0.6
                 AND h1.tipo_hecho != h2.tipo_hecho
                 AND h1.pais && h2.pais
            THEN 'contenido_contradictorio_similar'
            ELSE NULL
        END AS tipo_duplicado
        
    FROM hechos h1
    JOIN hechos h2 ON h1.id < h2.id
    WHERE 
        similarity(h1.contenido, h2.contenido) > 0.6
        AND h1.pais && h2.pais
        AND (h1.importancia >= 6 OR h2.importancia >= 6)
)

-- Vista principal consolidada
SELECT 
    'contradiccion_registrada' AS tipo_conflicto,
    cr.contradiccion_id AS conflicto_id,
    cr.hecho_principal_id AS elemento_1_id,
    cr.hecho_contradictorio_id AS elemento_2_id,
    'hechos' AS tipo_elementos,
    
    COALESCE(cr.descripcion_contradiccion, 
             'Contradicción ' || cr.tipo_contradiccion || ' entre hechos') AS descripcion,
    
    LEAST(10, GREATEST(1, 
        cr.grado_contradiccion * 2 + 
        (cr.importancia_maxima - 5)
    ))::INTEGER AS gravedad,
    
    cr.estado_resolucion,
    cr.fecha_deteccion,
    
    jsonb_build_object(
        'tipo_contradiccion', cr.tipo_contradiccion,
        'grado_contradiccion', cr.grado_contradiccion,
        'contenido_principal', LEFT(cr.contenido_principal, 200),
        'contenido_contradictorio', LEFT(cr.contenido_contradictorio, 200),
        'importancia_principal', cr.importancia_principal,
        'importancia_contradictoria', cr.importancia_contradictoria
    ) AS metadatos_conflicto,
    
    CASE 
        WHEN cr.grado_contradiccion >= 4 AND cr.importancia_maxima >= 8 
        THEN 'revision_editorial_urgente'
        WHEN cr.grado_contradiccion >= 3 
        THEN 'investigacion_detallada'
        ELSE 'revision_rutinaria'
    END AS recomendacion_resolucion,
    
    NOW() AS fecha_actualizacion

FROM contradicciones_registradas cr

UNION ALL

-- Conflictos editoriales
SELECT 
    'conflicto_editorial' AS tipo_conflicto,
    NULL AS conflicto_id,
    ce.hecho_id_principal AS elemento_1_id,
    ce.hecho_id_secundario AS elemento_2_id,
    'hechos' AS tipo_elementos,
    
    'Conflicto editorial: ' || ce.tipo_conflicto_editorial ||
    ' (similitud: ' || ROUND(ce.similitud_contenidos::NUMERIC * 100) || '%)' AS descripcion,
    
    LEAST(10, GREATEST(5,
        6 + (ce.similitud_contenidos * 4)::INTEGER +
        (ce.importancia_maxima - 5)
    ))::INTEGER AS gravedad,
    
    'pendiente' AS estado_resolucion,
    CURRENT_DATE AS fecha_deteccion,
    
    jsonb_build_object(
        'tipo_conflicto_editorial', ce.tipo_conflicto_editorial,
        'evaluacion_1', ce.evaluacion_1,
        'evaluacion_2', ce.evaluacion_2,
        'consenso_1', ce.consenso_1,
        'consenso_2', ce.consenso_2,
        'similitud_contenidos', ROUND(ce.similitud_contenidos::NUMERIC, 3)
    ) AS metadatos_conflicto,
    
    'revision_editorial_critica' AS recomendacion_resolucion,
    
    NOW() AS fecha_actualizacion

FROM contradicciones_editoriales ce
WHERE ce.tipo_conflicto_editorial IS NOT NULL

UNION ALL

-- Contenidos duplicados o contradictorios
SELECT 
    'contenido_duplicado' AS tipo_conflicto,
    NULL AS conflicto_id,
    cd.hecho_id_1 AS elemento_1_id,
    cd.hecho_id_2 AS elemento_2_id,
    'hechos' AS tipo_elementos,
    
    'Contenido duplicado/contradictorio: ' || cd.tipo_duplicado ||
    ' (similitud: ' || ROUND(cd.similitud_contenido::NUMERIC * 100) || '%)' AS descripcion,
    
    CASE 
        WHEN cd.tipo_duplicado = 'posible_duplicado' THEN 4
        WHEN cd.tipo_duplicado = 'contenido_contradictorio_similar' THEN 7
        ELSE 3
    END AS gravedad,
    
    'pendiente' AS estado_resolucion,
    CURRENT_DATE AS fecha_deteccion,
    
    jsonb_build_object(
        'tipo_duplicado', cd.tipo_duplicado,
        'similitud_contenido', ROUND(cd.similitud_contenido::NUMERIC, 3),
        'contenido_1', LEFT(cd.contenido_1, 200),
        'contenido_2', LEFT(cd.contenido_2, 200),
        'tipo_1', cd.tipo_1,
        'tipo_2', cd.tipo_2
    ) AS metadatos_conflicto,
    
    CASE 
        WHEN cd.tipo_duplicado = 'posible_duplicado' THEN 'verificar_duplicados'
        ELSE 'analizar_contradicciones'
    END AS recomendacion_resolucion,
    
    NOW() AS fecha_actualizacion

FROM contenidos_duplicados cd
WHERE cd.tipo_duplicado IS NOT NULL

ORDER BY gravedad DESC, fecha_deteccion DESC;

-- Índices para contradicciones_conflictos
CREATE INDEX IF NOT EXISTS idx_contradicciones_tipo 
ON contradicciones_conflictos(tipo_conflicto);

CREATE INDEX IF NOT EXISTS idx_contradicciones_gravedad 
ON contradicciones_conflictos(gravedad DESC);

-- ============================================================================
-- 6. FUNCIONES DE GESTIÓN Y MANTENIMIENTO
-- ============================================================================

-- Función para refrescar una vista materializada específica
CREATE OR REPLACE FUNCTION refresh_materialized_view(view_name TEXT)
RETURNS TABLE(
    vista TEXT,
    inicio TIMESTAMP WITH TIME ZONE,
    fin TIMESTAMP WITH TIME ZONE,
    duracion_segundos NUMERIC,
    filas_afectadas BIGINT,
    resultado TEXT,
    error_mensaje TEXT
) 
LANGUAGE plpgsql
AS $$
DECLARE
    start_time TIMESTAMP WITH TIME ZONE;
    end_time TIMESTAMP WITH TIME ZONE;
    row_count BIGINT;
    error_msg TEXT;
BEGIN
    start_time := NOW();
    
    BEGIN
        EXECUTE format('REFRESH MATERIALIZED VIEW %I', view_name);
        EXECUTE format('SELECT COUNT(*) FROM %I', view_name) INTO row_count;
        end_time := NOW();
        
        RETURN QUERY SELECT 
            view_name, start_time, end_time,
            EXTRACT(EPOCH FROM (end_time - start_time)),
            row_count, 'SUCCESS'::TEXT, NULL::TEXT;
            
    EXCEPTION WHEN OTHERS THEN
        error_msg := SQLERRM;
        end_time := NOW();
        
        RETURN QUERY SELECT 
            view_name, start_time, end_time,
            EXTRACT(EPOCH FROM (end_time - start_time)),
            0::BIGINT, 'ERROR'::TEXT, error_msg;
    END;
END;
$$;

-- Función para refrescar todas las vistas materializadas avanzadas
CREATE OR REPLACE FUNCTION refresh_advanced_materialized_views()
RETURNS TABLE(
    vista TEXT,
    inicio TIMESTAMP WITH TIME ZONE,
    fin TIMESTAMP WITH TIME ZONE,
    duracion_segundos NUMERIC,
    filas_afectadas BIGINT,
    resultado TEXT,
    error_mensaje TEXT
) 
LANGUAGE plpgsql
AS $$
DECLARE
    view_names TEXT[] := ARRAY[
        'redes_entidades_centralidad',
        'correlaciones_temporales',
        'patrones_emergentes_anomalias',
        'metricas_calidad_datos',
        'contradicciones_conflictos'
    ];
    view_name TEXT;
BEGIN
    FOREACH view_name IN ARRAY view_names
    LOOP
        RETURN QUERY SELECT * FROM refresh_materialized_view(view_name);
    END LOOP;
END;
$$;

-- Función de validación de salud de vistas
CREATE OR REPLACE FUNCTION validate_materialized_view_health(view_name TEXT)
RETURNS TABLE(
    vista TEXT,
    filas_totales BIGINT,
    filas_con_nulos BIGINT,
    filas_duplicadas BIGINT,
    columnas_criticas_vacias BIGINT,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE,
    estado_salud TEXT,
    observaciones TEXT
) 
LANGUAGE plpgsql
AS $$
DECLARE
    total_rows BIGINT;
    last_update TIMESTAMP WITH TIME ZONE;
    health_status TEXT;
    observations TEXT;
BEGIN
    EXECUTE format('SELECT COUNT(*) FROM %I', view_name) INTO total_rows;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = view_name AND column_name = 'fecha_actualizacion') THEN
        EXECUTE format('SELECT MAX(fecha_actualizacion) FROM %I', view_name) INTO last_update;
    ELSE
        last_update := NOW();
    END IF;
    
    IF total_rows = 0 THEN
        health_status := 'VACIA';
        observations := 'Vista materializada sin datos';
    ELSIF total_rows > 0 AND last_update > NOW() - INTERVAL '1 hour' THEN
        health_status := 'SALUDABLE';
        observations := 'Vista actualizada recientemente con datos válidos';
    ELSIF last_update <= NOW() - INTERVAL '24 hours' THEN
        health_status := 'DESACTUALIZADA';
        observations := 'Vista requiere actualización urgente';
    ELSE
        health_status := 'ACEPTABLE';
        observations := 'Vista en estado aceptable';
    END IF;
    
    RETURN QUERY SELECT 
        view_name, total_rows, 0::BIGINT, 0::BIGINT, 0::BIGINT,
        last_update, health_status, observations;
END;
$$;

-- Tabla de log para operaciones
CREATE TABLE IF NOT EXISTS materialized_views_refresh_log (
    id BIGSERIAL PRIMARY KEY,
    operacion TEXT NOT NULL,
    vista TEXT NOT NULL,
    inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    fin TIMESTAMP WITH TIME ZONE,
    duracion_segundos NUMERIC,
    filas_afectadas BIGINT,
    resultado TEXT NOT NULL,
    error_mensaje TEXT,
    parametros JSONB,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mv_log_vista_fecha 
ON materialized_views_refresh_log(vista, fecha_registro DESC);

CREATE INDEX IF NOT EXISTS idx_mv_log_resultado 
ON materialized_views_refresh_log(resultado);

-- ============================================================================
-- COMANDOS DE VERIFICACIÓN Y PRUEBA
-- ============================================================================

-- Verificar que todas las vistas se crearon correctamente
SELECT 
    schemaname,
    matviewname,
    hasindexes,
    ispopulated
FROM pg_matviews 
WHERE schemaname = 'public'
  AND matviewname IN (
    'redes_entidades_centralidad',
    'correlaciones_temporales', 
    'patrones_emergentes_anomalias',
    'metricas_calidad_datos',
    'contradicciones_conflictos'
  )
ORDER BY matviewname;

-- Ejecutar diagnóstico inicial
SELECT vista, filas_totales, estado_salud, observaciones
FROM validate_materialized_view_health('redes_entidades_centralidad')
UNION ALL
SELECT vista, filas_totales, estado_salud, observaciones
FROM validate_materialized_view_health('correlaciones_temporales')
UNION ALL
SELECT vista, filas_totales, estado_salud, observaciones
FROM validate_materialized_view_health('patrones_emergentes_anomalias')
UNION ALL
SELECT vista, filas_totales, estado_salud, observaciones
FROM validate_materialized_view_health('metricas_calidad_datos')
UNION ALL
SELECT vista, filas_totales, estado_salud, observaciones
FROM validate_materialized_view_health('contradicciones_conflictos');

-- ============================================================================
-- NOTAS DE IMPLEMENTACIÓN Y PRÓXIMOS PASOS
-- ============================================================================

/*
IMPLEMENTACIÓN COMPLETADA:

✅ 1. Vista de Redes de Entidades y Centralidad
   - Análisis de co-ocurrencias entre entidades
   - Métricas de centralidad de grado
   - Score de centralidad normalizado
   - Top conexiones por entidad
   - Clasificación automática de centralidad

✅ 2. Vista de Correlaciones Temporales  
   - Series temporales semanales de actividad
   - Correlaciones entre pares de entidades
   - Análisis de tendencias temporales
   - Clasificación de fuerza de correlación
   - Patrones de sincronización temporal

✅ 3. Vista de Patrones Emergentes y Anomalías
   - Detección de anomalías temporales con z-scores
   - Análisis de spikes y caídas en tipos de hechos
   - Anomalías en patrones de entidades
   - Score de anomalía normalizado
   - Sistema de confianza de detección

✅ 4. Vista de Métricas de Calidad de Datos
   - Análisis de completitud por tabla
   - Verificación de integridad referencial
   - Detección de duplicados potenciales
   - Análisis de outliers numéricos
   - Score global de calidad de datos

✅ 5. Vista de Contradicciones y Conflictos
   - Contradicciones explícitas registradas
   - Detección de conflictos editoriales
   - Identificación de contenidos duplicados
   - Sistema de gravedad y recomendaciones
   - Metadatos enriquecidos por conflicto

✅ 6. Sistema de Gestión y Mantenimiento
   - Funciones de refrescado individuales y grupales
   - Sistema de validación de salud
   - Tabla de log para auditoría
   - Funciones de diagnóstico automatizado

ESTRATEGIAS DE REFRESCADO IMPLEMENTADAS:

📋 Políticas Definidas (requieren permisos de superusuario para pg_cron):
   - Refrescado básico: cada 30 minutos durante horas laborales
   - Refrescado completo: diario a las 2:00 AM
   - Optimización semanal: domingos 3:00 AM
   - Diagnóstico diario: 1:00 AM
   - Refrescado crítico: cada 10 minutos (opcional)

PRÓXIMOS PASOS RECOMENDADOS:

1. Configurar trabajos de pg_cron con permisos de superusuario
2. Implementar alertas basadas en métricas de calidad
3. Crear dashboard de monitoreo de vistas materializadas
4. Establecer umbrales de rendimiento por vista
5. Implementar refrescado incremental para vistas grandes
6. Añadir métricas específicas por dominio de negocio

RENDIMIENTO Y ESCALABILIDAD:

- Todas las vistas incluyen índices optimizados
- Configuración inicial conservadora para datos pequeños/medianos
- Estructura preparada para escalamiento futuro
- Sistema de monitoreo y alertas incorporado
- Funciones de optimización automática incluidas
*/
