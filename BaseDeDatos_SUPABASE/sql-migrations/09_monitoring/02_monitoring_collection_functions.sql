-- =====================================================
-- SISTEMA DE MONITOREO - FUNCIONES DE RECOLECCIÓN
-- Archivo: 02_monitoring_collection_functions.sql
-- Descripción: Funciones para recopilar métricas del sistema
-- =====================================================

-- =====================================================
-- FUNCIÓN PRINCIPAL DE RECOLECCIÓN DE MÉTRICAS
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.collect_system_metrics()
RETURNS UUID AS $$
DECLARE
    job_id UUID := gen_random_uuid();
    start_time TIMESTAMPTZ := NOW();
    metrics_collected INTEGER := 0;
    alerts_generated INTEGER := 0;
    error_count INTEGER := 0;
    execution_start_time TIMESTAMPTZ;
    current_metrics RECORD;
BEGIN
    execution_start_time := clock_timestamp();
    
    -- Registrar inicio del trabajo
    INSERT INTO monitoring.collection_jobs (
        id, started_at, job_type, status
    ) VALUES (
        job_id, start_time, 'system_metrics', 'running'
    );

    -- Recopilar métricas básicas del sistema
    SELECT 
        -- Métricas de conexiones
        (SELECT count(*) FROM pg_stat_activity) as total_connections,
        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
        (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle') as idle_connections,
        (SELECT setting::integer FROM pg_settings WHERE name = 'max_connections') as max_connections,
        
        -- Métricas de base de datos
        (SELECT pg_database_size(current_database()) / 1024 / 1024) as database_size_mb,
        
        -- Métricas de cache
        (SELECT 
            CASE WHEN (blks_hit + blks_read) > 0 
            THEN round(100.0 * blks_hit / (blks_hit + blks_read), 2) 
            ELSE 100.0 END
         FROM pg_stat_database WHERE datname = current_database()) as cache_hit_ratio,
         
        -- Métricas de transacciones
        (SELECT xact_commit FROM pg_stat_database WHERE datname = current_database()) as transactions_committed,
        (SELECT xact_rollback FROM pg_stat_database WHERE datname = current_database()) as transactions_rolled_back,
        
        -- Métricas de I/O
        (SELECT blks_read FROM pg_stat_database WHERE datname = current_database()) as total_reads,
        (SELECT blks_hit FROM pg_stat_database WHERE datname = current_database()) as total_writes,
        
        -- Métricas de locks
        (SELECT count(*) FROM pg_locks) as current_locks,
        (SELECT deadlocks FROM pg_stat_database WHERE datname = current_database()) as deadlocks_total
        
    INTO current_metrics;

    -- Insertar métricas recolectadas
    INSERT INTO monitoring.system_metrics (
        timestamp,
        total_connections,
        active_connections,
        idle_connections,
        max_connections,
        connection_usage_percent,
        database_size_mb,
        cache_hit_ratio,
        buffer_cache_hit_ratio,
        transactions_committed,
        transactions_rolled_back,
        total_reads,
        total_writes,
        current_locks,
        deadlocks_total,
        collection_time_ms,
        collector_version
    ) VALUES (
        NOW(),
        current_metrics.total_connections,
        current_metrics.active_connections,
        current_metrics.idle_connections,
        current_metrics.max_connections,
        CASE WHEN current_metrics.max_connections > 0 
             THEN round(100.0 * current_metrics.total_connections / current_metrics.max_connections, 2)
             ELSE 0 END,
        current_metrics.database_size_mb,
        current_metrics.cache_hit_ratio,
        current_metrics.cache_hit_ratio, -- Usar mismo valor para buffer cache
        current_metrics.transactions_committed,
        current_metrics.transactions_rolled_back,
        current_metrics.total_reads,
        current_metrics.total_writes,
        current_metrics.current_locks,
        current_metrics.deadlocks_total,
        EXTRACT(milliseconds FROM (clock_timestamp() - execution_start_time))::INTEGER,
        '1.0.0'
    );
    
    metrics_collected := 1;
    
    -- Verificar umbrales y generar alertas
    SELECT monitoring.check_alert_thresholds() INTO alerts_generated;
    
    -- Actualizar registro del trabajo como completado
    UPDATE monitoring.collection_jobs SET
        completed_at = NOW(),
        status = 'completed',
        metrics_collected = metrics_collected,
        alerts_generated = alerts_generated,
        errors_count = error_count,
        execution_time_ms = EXTRACT(milliseconds FROM (NOW() - start_time))::INTEGER
    WHERE id = job_id;
    
    RETURN job_id;
    
EXCEPTION WHEN OTHERS THEN
    error_count := 1;
    -- Registrar error en el trabajo
    UPDATE monitoring.collection_jobs SET
        completed_at = NOW(),
        status = 'failed',
        metrics_collected = metrics_collected,
        alerts_generated = alerts_generated,
        errors_count = error_count,
        execution_time_ms = EXTRACT(milliseconds FROM (NOW() - start_time))::INTEGER,
        error_message = SQLERRM,
        error_details = jsonb_build_object(
            'error_state', SQLSTATE,
            'error_message', SQLERRM,
            'error_context', 'collect_system_metrics'
        )
    WHERE id = job_id;
    
    -- Re-lanzar la excepción para logging
    RAISE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA VERIFICAR UMBRALES Y GENERAR ALERTAS
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.check_alert_thresholds()
RETURNS INTEGER AS $$
DECLARE
    threshold_rec RECORD;
    latest_metrics RECORD;
    alerts_count INTEGER := 0;
    alert_id UUID;
    current_value DECIMAL(15,2);
    should_alert BOOLEAN := FALSE;
    alert_level TEXT;
BEGIN
    -- Obtener las métricas más recientes
    SELECT * INTO latest_metrics 
    FROM monitoring.system_metrics 
    ORDER BY timestamp DESC 
    LIMIT 1;
    
    IF latest_metrics IS NULL THEN
        RETURN 0;
    END IF;
    
    -- Iterar sobre todos los umbrales habilitados
    FOR threshold_rec IN 
        SELECT * FROM monitoring.alert_thresholds 
        WHERE enabled = TRUE
    LOOP
        should_alert := FALSE;
        alert_level := '';
        current_value := NULL;
        
        -- Obtener el valor actual según el tipo de métrica
        CASE threshold_rec.metric_name
            WHEN 'cpu_usage_percent' THEN 
                current_value := latest_metrics.cpu_usage_percent;
            WHEN 'memory_usage_percent' THEN 
                current_value := latest_metrics.memory_usage_percent;
            WHEN 'storage_usage_percent' THEN 
                current_value := latest_metrics.storage_usage_percent;
            WHEN 'connection_usage_percent' THEN 
                current_value := latest_metrics.connection_usage_percent;
            WHEN 'cache_hit_ratio' THEN 
                current_value := latest_metrics.cache_hit_ratio;
            WHEN 'avg_query_time_ms' THEN 
                current_value := latest_metrics.avg_query_time_ms;
            WHEN 'slow_queries_count' THEN 
                current_value := latest_metrics.slow_queries_count;
            WHEN 'deadlocks_total' THEN 
                current_value := latest_metrics.deadlocks_total;
            ELSE 
                CONTINUE; -- Saltar métricas no reconocidas
        END CASE;
        
        -- Saltar si no hay valor
        IF current_value IS NULL THEN
            CONTINUE;
        END IF;
        
        -- Determinar si se debe generar alerta
        IF threshold_rec.metric_name = 'cache_hit_ratio' THEN
            -- Para cache hit ratio, alerta cuando es MENOR que el umbral
            IF current_value <= threshold_rec.critical_threshold THEN
                should_alert := TRUE;
                alert_level := 'critical';
            ELSIF current_value <= threshold_rec.warning_threshold THEN
                should_alert := TRUE;
                alert_level := 'warning';
            END IF;
        ELSE
            -- Para otras métricas, alerta cuando es MAYOR que el umbral
            IF current_value >= threshold_rec.critical_threshold THEN
                should_alert := TRUE;
                alert_level := 'critical';
            ELSIF current_value >= threshold_rec.warning_threshold THEN
                should_alert := TRUE;
                alert_level := 'warning';
            END IF;
        END IF;
        
        -- Generar alerta si es necesario
        IF should_alert THEN
            -- Verificar si ya existe una alerta activa para esta métrica
            IF NOT EXISTS (
                SELECT 1 FROM monitoring.alerts 
                WHERE metric_name = threshold_rec.metric_name 
                AND status = 'active'
                AND timestamp > NOW() - INTERVAL '1 hour'
            ) THEN
                -- Crear nueva alerta
                alert_id := gen_random_uuid();
                INSERT INTO monitoring.alerts (
                    id,
                    timestamp,
                    alert_type,
                    severity,
                    metric_name,
                    metric_value,
                    threshold_value,
                    title,
                    description,
                    status,
                    notification_channels,
                    created_by
                ) VALUES (
                    alert_id,
                    NOW(),
                    'threshold_breach',
                    alert_level,
                    threshold_rec.metric_name,
                    current_value,
                    CASE WHEN alert_level = 'critical' THEN threshold_rec.critical_threshold 
                         ELSE threshold_rec.warning_threshold END,
                    format('%s: %s (%s%%)', alert_level, threshold_rec.display_name, current_value),
                    format('La métrica %s ha alcanzado un valor de %s, superando el umbral %s de %s',
                           threshold_rec.display_name, 
                           current_value,
                           alert_level,
                           CASE WHEN alert_level = 'critical' THEN threshold_rec.critical_threshold 
                                ELSE threshold_rec.warning_threshold END),
                    'active',
                    threshold_rec.notification_channels,
                    'system'
                );
                
                alerts_count := alerts_count + 1;
                
                -- Log de la alerta generada
                RAISE NOTICE 'Alerta generada: % - % (Valor: %, Umbral: %)', 
                    alert_level, threshold_rec.display_name, current_value, 
                    CASE WHEN alert_level = 'critical' THEN threshold_rec.critical_threshold 
                         ELSE threshold_rec.warning_threshold END;
            END IF;
        END IF;
    END LOOP;
    
    RETURN alerts_count;
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error en check_alert_thresholds: %', SQLERRM;
    RETURN 0;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA OBTENER CONSULTAS LENTAS
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.get_slow_queries(
    p_min_duration_ms INTEGER DEFAULT 1000,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    query_id BIGINT,
    query TEXT,
    calls BIGINT,
    total_time_ms NUMERIC,
    mean_time_ms NUMERIC,
    max_time_ms NUMERIC,
    stddev_time_ms NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.queryid,
        s.query,
        s.calls,
        s.total_exec_time as total_time_ms,
        s.mean_exec_time as mean_time_ms,
        s.max_exec_time as max_time_ms,
        s.stddev_exec_time as stddev_time_ms
    FROM pg_stat_statements s
    WHERE s.mean_exec_time >= p_min_duration_ms
    ORDER BY s.mean_exec_time DESC
    LIMIT p_limit;
    
EXCEPTION WHEN OTHERS THEN
    -- Si pg_stat_statements no está disponible, retornar vacío
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA LIMPIAR DATOS ANTIGUOS
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.cleanup_old_data(
    p_metrics_retention_days INTEGER DEFAULT 30,
    p_alerts_retention_days INTEGER DEFAULT 90,
    p_jobs_retention_days INTEGER DEFAULT 7
)
RETURNS TEXT AS $$
DECLARE
    deleted_metrics INTEGER;
    deleted_alerts INTEGER;
    deleted_jobs INTEGER;
    result_message TEXT;
BEGIN
    -- Limpiar métricas antiguas
    DELETE FROM monitoring.system_metrics 
    WHERE timestamp < NOW() - INTERVAL '1 day' * p_metrics_retention_days;
    GET DIAGNOSTICS deleted_metrics = ROW_COUNT;
    
    -- Limpiar alertas resueltas antiguas
    DELETE FROM monitoring.alerts 
    WHERE status IN ('resolved', 'suppressed')
    AND timestamp < NOW() - INTERVAL '1 day' * p_alerts_retention_days;
    GET DIAGNOSTICS deleted_alerts = ROW_COUNT;
    
    -- Limpiar trabajos antiguos
    DELETE FROM monitoring.collection_jobs 
    WHERE started_at < NOW() - INTERVAL '1 day' * p_jobs_retention_days;
    GET DIAGNOSTICS deleted_jobs = ROW_COUNT;
    
    result_message := format(
        'Limpieza completada: %s métricas, %s alertas, %s trabajos eliminados',
        deleted_metrics, deleted_alerts, deleted_jobs
    );
    
    RAISE NOTICE '%', result_message;
    RETURN result_message;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA OBTENER RESUMEN DE ESTADO
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.get_system_status()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    latest_metrics RECORD;
    active_alerts INTEGER;
    critical_alerts INTEGER;
BEGIN
    -- Obtener métricas más recientes
    SELECT * INTO latest_metrics 
    FROM monitoring.system_metrics 
    ORDER BY timestamp DESC 
    LIMIT 1;
    
    -- Contar alertas activas
    SELECT 
        COUNT(*) FILTER (WHERE severity = 'critical') as critical_count,
        COUNT(*) as total_count
    INTO critical_alerts, active_alerts
    FROM monitoring.alerts 
    WHERE status = 'active';
    
    -- Construir resultado
    result := jsonb_build_object(
        'timestamp', NOW(),
        'overall_status', CASE 
            WHEN critical_alerts > 0 THEN 'critical'
            WHEN active_alerts > 0 THEN 'warning'
            ELSE 'healthy'
        END,
        'alerts', jsonb_build_object(
            'total_active', active_alerts,
            'critical', critical_alerts
        ),
        'metrics', CASE 
            WHEN latest_metrics IS NOT NULL THEN
                jsonb_build_object(
                    'timestamp', latest_metrics.timestamp,
                    'cpu_usage', latest_metrics.cpu_usage_percent,
                    'memory_usage', latest_metrics.memory_usage_percent,
                    'storage_usage', latest_metrics.storage_usage_percent,
                    'connection_usage', latest_metrics.connection_usage_percent,
                    'cache_hit_ratio', latest_metrics.cache_hit_ratio,
                    'database_size_mb', latest_metrics.database_size_mb,
                    'total_connections', latest_metrics.total_connections,
                    'active_connections', latest_metrics.active_connections
                )
            ELSE NULL
        END
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON FUNCTION monitoring.collect_system_metrics() IS 'Función principal que recolecta todas las métricas del sistema y las almacena en la tabla system_metrics';
COMMENT ON FUNCTION monitoring.check_alert_thresholds() IS 'Verifica si las métricas más recientes superan los umbrales configurados y genera alertas';
COMMENT ON FUNCTION monitoring.get_slow_queries(INTEGER, INTEGER) IS 'Obtiene las consultas más lentas del sistema usando pg_stat_statements';
COMMENT ON FUNCTION monitoring.cleanup_old_data(INTEGER, INTEGER, INTEGER) IS 'Limpia datos antiguos para mantener el rendimiento del sistema de monitoreo';
COMMENT ON FUNCTION monitoring.get_system_status() IS 'Retorna un resumen JSON del estado actual del sistema';

-- Verificación final
DO $$
BEGIN
    RAISE NOTICE 'Funciones de recolección de monitoreo creadas exitosamente';
    RAISE NOTICE 'Funciones principales: collect_system_metrics, check_alert_thresholds';
    RAISE NOTICE 'Funciones auxiliares: get_slow_queries, cleanup_old_data, get_system_status';
END $$;
