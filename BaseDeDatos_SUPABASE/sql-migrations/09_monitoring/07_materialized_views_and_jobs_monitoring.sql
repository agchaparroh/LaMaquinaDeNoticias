-- =====================================================
-- MONITOREO DE VISTAS MATERIALIZADAS Y JOBS PG_CRON
-- Archivo: 07_materialized_views_and_jobs_monitoring.sql
-- Descripción: Monitoreo específico para vistas materializadas y trabajos programados
-- =====================================================

-- =====================================================
-- TABLA PARA MÉTRICAS DE VISTAS MATERIALIZADAS
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.materialized_view_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Información de la vista materializada
    schema_name TEXT NOT NULL,
    view_name TEXT NOT NULL,
    full_view_name TEXT GENERATED ALWAYS AS (schema_name || '.' || view_name) STORED,
    
    -- Estado y metadatos
    view_exists BOOLEAN NOT NULL DEFAULT TRUE,
    is_populated BOOLEAN,
    has_data BOOLEAN,
    
    -- Métricas de tamaño y contenido
    row_count BIGINT,
    size_bytes BIGINT,
    size_mb DECIMAL(10,2) GENERATED ALWAYS AS (ROUND(size_bytes::decimal / 1024 / 1024, 2)) STORED,
    
    -- Información de índices
    indexes_count INTEGER DEFAULT 0,
    indexes_size_bytes BIGINT DEFAULT 0,
    
    -- Tiempos de operación
    last_refresh_timestamp TIMESTAMPTZ,
    refresh_duration_ms BIGINT,
    estimated_refresh_frequency_hours INTEGER,
    
    -- Dependencias y relaciones
    depends_on_tables TEXT[],
    depends_on_views TEXT[],
    
    -- Métricas de uso y rendimiento
    scan_count BIGINT DEFAULT 0,
    sequential_scans BIGINT DEFAULT 0,
    index_scans BIGINT DEFAULT 0,
    
    -- Estado de salud
    health_status TEXT DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'warning', 'critical', 'unknown')),
    last_error_message TEXT,
    
    -- Metadatos de recolección
    collection_time_ms INTEGER,
    collector_version TEXT DEFAULT '1.0.0',
    
    UNIQUE(schema_name, view_name, timestamp)
);

-- =====================================================
-- TABLA PARA MÉTRICAS DE TRABAJOS PG_CRON
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.pg_cron_job_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Información del trabajo
    job_id BIGINT NOT NULL,
    job_name TEXT NOT NULL,
    schedule TEXT NOT NULL,
    command TEXT,
    database_name TEXT,
    username TEXT,
    
    -- Estado actual
    active BOOLEAN NOT NULL DEFAULT TRUE,
    job_class TEXT DEFAULT 'regular', -- 'regular', 'monitoring', 'maintenance', 'critical'
    
    -- Información de ejecución reciente
    last_run_started_at TIMESTAMPTZ,
    last_run_finished_at TIMESTAMPTZ,
    last_run_status TEXT, -- 'succeeded', 'failed', 'running', 'scheduled'
    last_run_duration_ms BIGINT,
    
    -- Estadísticas de ejecución (últimas 24h)
    runs_last_24h INTEGER DEFAULT 0,
    successful_runs_last_24h INTEGER DEFAULT 0,
    failed_runs_last_24h INTEGER DEFAULT 0,
    avg_duration_last_24h_ms BIGINT,
    
    -- Información de errores
    last_error_message TEXT,
    consecutive_failures INTEGER DEFAULT 0,
    total_failures_last_week INTEGER DEFAULT 0,
    
    -- Próxima ejecución programada
    next_scheduled_run TIMESTAMPTZ,
    
    -- Métricas de rendimiento
    performance_trend TEXT DEFAULT 'stable', -- 'improving', 'stable', 'degrading'
    resource_usage_category TEXT DEFAULT 'normal', -- 'light', 'normal', 'heavy'
    
    -- Estado de salud
    health_status TEXT DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'warning', 'critical', 'unknown', 'disabled')),
    
    -- Metadatos de recolección
    collection_time_ms INTEGER,
    collector_version TEXT DEFAULT '1.0.0',
    
    UNIQUE(job_id, timestamp)
);

-- =====================================================
-- TABLA PARA REGISTRO DE REFRESCOS DE VISTAS
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.view_refresh_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    -- Información de la vista
    schema_name TEXT NOT NULL,
    view_name TEXT NOT NULL,
    full_view_name TEXT GENERATED ALWAYS AS (schema_name || '.' || view_name) STORED,
    
    -- Tipo de refresco
    refresh_type TEXT NOT NULL DEFAULT 'manual', -- 'manual', 'automatic', 'scheduled'
    triggered_by TEXT DEFAULT 'system',
    
    -- Resultado de la operación
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    rows_affected BIGINT,
    
    -- Métricas de rendimiento
    execution_time_ms BIGINT,
    cpu_time_ms BIGINT,
    memory_used_mb DECIMAL(10,2),
    
    -- Información de errores
    error_code TEXT,
    error_message TEXT,
    error_details JSONB,
    
    -- Comparación con ejecución anterior
    previous_row_count BIGINT,
    row_count_change BIGINT GENERATED ALWAYS AS (COALESCE(rows_affected, 0) - COALESCE(previous_row_count, 0)) STORED,
    performance_vs_previous TEXT, -- 'faster', 'similar', 'slower'
    
    -- Contexto adicional
    system_load_during_refresh DECIMAL(5,2),
    concurrent_operations INTEGER DEFAULT 0,
    
    tags JSONB DEFAULT '{}'::jsonb
);

-- =====================================================
-- FUNCIONES PARA RECOLECCIÓN DE MÉTRICAS DE VISTAS MATERIALIZADAS
-- =====================================================

-- Función para obtener lista de vistas materializadas del sistema
CREATE OR REPLACE FUNCTION monitoring.get_system_materialized_views()
RETURNS TABLE (
    schema_name TEXT,
    view_name TEXT,
    view_definition TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        schemaname::TEXT,
        matviewname::TEXT,
        definition::TEXT
    FROM pg_matviews
    WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
    ORDER BY schemaname, matviewname;
END;
$$ LANGUAGE plpgsql;

-- Función principal para recolectar métricas de vistas materializadas
CREATE OR REPLACE FUNCTION monitoring.collect_materialized_view_metrics()
RETURNS UUID AS $$
DECLARE
    job_id UUID := gen_random_uuid();
    start_time TIMESTAMPTZ := NOW();
    execution_start_time TIMESTAMPTZ;
    view_rec RECORD;
    view_stats RECORD;
    metrics_collected INTEGER := 0;
    errors_count INTEGER := 0;
BEGIN
    execution_start_time := clock_timestamp();
    
    -- Registrar inicio del trabajo
    INSERT INTO monitoring.collection_jobs (
        id, started_at, job_type, status
    ) VALUES (
        job_id, start_time, 'materialized_views', 'running'
    );

    -- Iterar sobre todas las vistas materializadas del sistema
    FOR view_rec IN 
        SELECT * FROM monitoring.get_system_materialized_views()
    LOOP
        BEGIN
            -- Obtener estadísticas de la vista materializada
            EXECUTE format('
                SELECT 
                    COUNT(*) as row_count,
                    pg_total_relation_size(%L) as size_bytes,
                    (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = %L AND tablename = %L) as indexes_count,
                    pg_indexes_size(%L) as indexes_size_bytes
                FROM %I.%I',
                view_rec.schema_name || '.' || view_rec.view_name,
                view_rec.schema_name,
                view_rec.view_name,
                view_rec.schema_name || '.' || view_rec.view_name,
                view_rec.schema_name,
                view_rec.view_name
            ) INTO view_stats;
            
            -- Insertar métricas de la vista materializada
            INSERT INTO monitoring.materialized_view_metrics (
                timestamp,
                schema_name,
                view_name,
                view_exists,
                is_populated,
                has_data,
                row_count,
                size_bytes,
                indexes_count,
                indexes_size_bytes,
                health_status,
                collection_time_ms
            ) VALUES (
                NOW(),
                view_rec.schema_name,
                view_rec.view_name,
                TRUE,
                TRUE, -- Si llegamos aquí, la vista existe y está poblada
                view_stats.row_count > 0,
                view_stats.row_count,
                view_stats.size_bytes,
                view_stats.indexes_count,
                view_stats.indexes_size_bytes,
                CASE 
                    WHEN view_stats.row_count = 0 THEN 'warning'
                    WHEN view_stats.size_bytes > 1073741824 THEN 'warning' -- > 1GB
                    ELSE 'healthy'
                END,
                EXTRACT(milliseconds FROM (clock_timestamp() - execution_start_time))::INTEGER
            );
            
            metrics_collected := metrics_collected + 1;
            
        EXCEPTION WHEN OTHERS THEN
            errors_count := errors_count + 1;
            
            -- Registrar vista con error
            INSERT INTO monitoring.materialized_view_metrics (
                timestamp,
                schema_name,
                view_name,
                view_exists,
                is_populated,
                has_data,
                health_status,
                last_error_message,
                collection_time_ms
            ) VALUES (
                NOW(),
                view_rec.schema_name,
                view_rec.view_name,
                FALSE,
                FALSE,
                FALSE,
                'critical',
                SQLERRM,
                EXTRACT(milliseconds FROM (clock_timestamp() - execution_start_time))::INTEGER
            );
            
            RAISE NOTICE 'Error recolectando métricas para vista %.%: %', 
                         view_rec.schema_name, view_rec.view_name, SQLERRM;
        END;
    END LOOP;
    
    -- Actualizar registro del trabajo como completado
    UPDATE monitoring.collection_jobs SET
        completed_at = NOW(),
        status = 'completed',
        metrics_collected = metrics_collected,
        errors_count = errors_count,
        execution_time_ms = EXTRACT(milliseconds FROM (NOW() - start_time))::INTEGER
    WHERE id = job_id;
    
    RETURN job_id;
    
EXCEPTION WHEN OTHERS THEN
    errors_count := errors_count + 1;
    -- Registrar error en el trabajo
    UPDATE monitoring.collection_jobs SET
        completed_at = NOW(),
        status = 'failed',
        metrics_collected = metrics_collected,
        errors_count = errors_count,
        execution_time_ms = EXTRACT(milliseconds FROM (NOW() - start_time))::INTEGER,
        error_message = SQLERRM,
        error_details = jsonb_build_object(
            'error_state', SQLSTATE,
            'error_message', SQLERRM,
            'error_context', 'collect_materialized_view_metrics'
        )
    WHERE id = job_id;
    
    RAISE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIONES PARA RECOLECCIÓN DE MÉTRICAS DE PG_CRON
-- =====================================================

-- Función para recolectar métricas de trabajos pg_cron
CREATE OR REPLACE FUNCTION monitoring.collect_pg_cron_metrics()
RETURNS UUID AS $$
DECLARE
    job_id UUID := gen_random_uuid();
    start_time TIMESTAMPTZ := NOW();
    execution_start_time TIMESTAMPTZ;
    cron_job_rec RECORD;
    job_stats RECORD;
    metrics_collected INTEGER := 0;
    errors_count INTEGER := 0;
BEGIN
    execution_start_time := clock_timestamp();
    
    -- Registrar inicio del trabajo
    INSERT INTO monitoring.collection_jobs (
        id, started_at, job_type, status
    ) VALUES (
        job_id, start_time, 'pg_cron_jobs', 'running'
    );

    -- Iterar sobre todos los trabajos de pg_cron
    FOR cron_job_rec IN 
        SELECT 
            j.jobid,
            j.schedule,
            j.command,
            j.nodename,
            j.nodeport,
            j.database,
            j.username,
            j.active,
            j.jobname
        FROM cron.job j
        ORDER BY j.jobid
    LOOP
        BEGIN
            -- Obtener estadísticas de ejecución del trabajo
            SELECT 
                COUNT(*) as total_runs_24h,
                COUNT(*) FILTER (WHERE status = 'succeeded') as successful_runs_24h,
                COUNT(*) FILTER (WHERE status = 'failed') as failed_runs_24h,
                ROUND(AVG(EXTRACT(milliseconds FROM (end_time - start_time)))) as avg_duration_ms,
                MAX(start_time) as last_run_started,
                MAX(end_time) as last_run_finished,
                (SELECT status FROM cron.job_run_details jrd WHERE jrd.jobid = cron_job_rec.jobid ORDER BY start_time DESC LIMIT 1) as last_status,
                (SELECT return_message FROM cron.job_run_details jrd WHERE jrd.jobid = cron_job_rec.jobid AND status = 'failed' ORDER BY start_time DESC LIMIT 1) as last_error
            INTO job_stats
            FROM cron.job_run_details jrd
            WHERE jrd.jobid = cron_job_rec.jobid
            AND jrd.start_time > NOW() - INTERVAL '24 hours';
            
            -- Determinar clase del trabajo
            DECLARE
                job_class TEXT := 'regular';
            BEGIN
                IF cron_job_rec.jobname LIKE '%monitoring%' OR cron_job_rec.jobname LIKE '%collect%' THEN
                    job_class := 'monitoring';
                ELSIF cron_job_rec.jobname LIKE '%cleanup%' OR cron_job_rec.jobname LIKE '%maintenance%' THEN
                    job_class := 'maintenance';
                ELSIF cron_job_rec.jobname LIKE '%backup%' OR cron_job_rec.jobname LIKE '%critical%' THEN
                    job_class := 'critical';
                END IF;
                
                -- Insertar métricas del trabajo pg_cron
                INSERT INTO monitoring.pg_cron_job_metrics (
                    timestamp,
                    job_id,
                    job_name,
                    schedule,
                    command,
                    database_name,
                    username,
                    active,
                    job_class,
                    last_run_started_at,
                    last_run_finished_at,
                    last_run_status,
                    last_run_duration_ms,
                    runs_last_24h,
                    successful_runs_last_24h,
                    failed_runs_last_24h,
                    avg_duration_last_24h_ms,
                    last_error_message,
                    consecutive_failures,
                    health_status,
                    collection_time_ms
                ) VALUES (
                    NOW(),
                    cron_job_rec.jobid,
                    COALESCE(cron_job_rec.jobname, 'unnamed_job_' || cron_job_rec.jobid),
                    cron_job_rec.schedule,
                    cron_job_rec.command,
                    cron_job_rec.database,
                    cron_job_rec.username,
                    cron_job_rec.active,
                    job_class,
                    job_stats.last_run_started,
                    job_stats.last_run_finished,
                    COALESCE(job_stats.last_status, 'scheduled'),
                    CASE WHEN job_stats.last_run_finished IS NOT NULL AND job_stats.last_run_started IS NOT NULL 
                         THEN EXTRACT(milliseconds FROM (job_stats.last_run_finished - job_stats.last_run_started))::BIGINT
                         ELSE NULL END,
                    COALESCE(job_stats.total_runs_24h, 0),
                    COALESCE(job_stats.successful_runs_24h, 0),
                    COALESCE(job_stats.failed_runs_24h, 0),
                    job_stats.avg_duration_ms,
                    job_stats.last_error,
                    COALESCE(job_stats.failed_runs_24h, 0), -- Simplified consecutive failures
                    CASE 
                        WHEN NOT cron_job_rec.active THEN 'disabled'
                        WHEN job_stats.failed_runs_24h > 3 THEN 'critical'
                        WHEN job_stats.failed_runs_24h > 0 THEN 'warning'
                        WHEN job_stats.total_runs_24h = 0 AND cron_job_rec.active THEN 'warning'
                        ELSE 'healthy'
                    END,
                    EXTRACT(milliseconds FROM (clock_timestamp() - execution_start_time))::INTEGER
                );
                
                metrics_collected := metrics_collected + 1;
            END;
            
        EXCEPTION WHEN OTHERS THEN
            errors_count := errors_count + 1;
            RAISE NOTICE 'Error recolectando métricas para trabajo pg_cron %: %', 
                         cron_job_rec.jobid, SQLERRM;
        END;
    END LOOP;
    
    -- Actualizar registro del trabajo como completado
    UPDATE monitoring.collection_jobs SET
        completed_at = NOW(),
        status = 'completed',
        metrics_collected = metrics_collected,
        errors_count = errors_count,
        execution_time_ms = EXTRACT(milliseconds FROM (NOW() - start_time))::INTEGER
    WHERE id = job_id;
    
    RETURN job_id;
    
EXCEPTION WHEN OTHERS THEN
    errors_count := errors_count + 1;
    -- Registrar error en el trabajo
    UPDATE monitoring.collection_jobs SET
        completed_at = NOW(),
        status = 'failed',
        metrics_collected = metrics_collected,
        errors_count = errors_count,
        execution_time_ms = EXTRACT(milliseconds FROM (NOW() - start_time))::INTEGER,
        error_message = SQLERRM,
        error_details = jsonb_build_object(
            'error_state', SQLSTATE,
            'error_message', SQLERRM,
            'error_context', 'collect_pg_cron_metrics'
        )
    WHERE id = job_id;
    
    RAISE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA REFRESCAR VISTA MATERIALIZADA CON LOGGING
-- =====================================================

-- Función para refrescar vista materializada con logging completo
CREATE OR REPLACE FUNCTION monitoring.refresh_materialized_view_with_logging(
    p_schema_name TEXT,
    p_view_name TEXT,
    p_concurrently BOOLEAN DEFAULT FALSE
)
RETURNS UUID AS $$
DECLARE
    refresh_id UUID := gen_random_uuid();
    start_time TIMESTAMPTZ := NOW();
    execution_start_time TIMESTAMPTZ;
    previous_count BIGINT;
    current_count BIGINT;
    refresh_command TEXT;
    full_view_name TEXT;
BEGIN
    execution_start_time := clock_timestamp();
    full_view_name := p_schema_name || '.' || p_view_name;
    
    -- Obtener conteo anterior
    EXECUTE format('SELECT COUNT(*) FROM %I.%I', p_schema_name, p_view_name) INTO previous_count;
    
    -- Registrar inicio del refresco
    INSERT INTO monitoring.view_refresh_history (
        id, started_at, schema_name, view_name, 
        refresh_type, triggered_by, status, previous_row_count
    ) VALUES (
        refresh_id, start_time, p_schema_name, p_view_name,
        'manual', current_user, 'running', previous_count
    );
    
    -- Construir comando de refresco
    refresh_command := format('REFRESH MATERIALIZED VIEW %s %I.%I',
                             CASE WHEN p_concurrently THEN 'CONCURRENTLY' ELSE '' END,
                             p_schema_name, p_view_name);
    
    -- Ejecutar refresco
    EXECUTE refresh_command;
    
    -- Obtener nuevo conteo
    EXECUTE format('SELECT COUNT(*) FROM %I.%I', p_schema_name, p_view_name) INTO current_count;
    
    -- Actualizar registro como completado
    UPDATE monitoring.view_refresh_history SET
        completed_at = NOW(),
        status = 'completed',
        rows_affected = current_count,
        execution_time_ms = EXTRACT(milliseconds FROM (NOW() - start_time))::INTEGER,
        performance_vs_previous = CASE 
            WHEN EXTRACT(milliseconds FROM (NOW() - start_time)) < 5000 THEN 'faster'
            WHEN EXTRACT(milliseconds FROM (NOW() - start_time)) > 30000 THEN 'slower'
            ELSE 'similar'
        END
    WHERE id = refresh_id;
    
    RAISE NOTICE 'Vista materializada %.% refrescada exitosamente. Filas: % -> %', 
                 p_schema_name, p_view_name, previous_count, current_count;
    
    RETURN refresh_id;
    
EXCEPTION WHEN OTHERS THEN
    -- Registrar error en el refresco
    UPDATE monitoring.view_refresh_history SET
        completed_at = NOW(),
        status = 'failed',
        execution_time_ms = EXTRACT(milliseconds FROM (NOW() - start_time))::INTEGER,
        error_code = SQLSTATE,
        error_message = SQLERRM,
        error_details = jsonb_build_object(
            'error_state', SQLSTATE,
            'error_message', SQLERRM,
            'view_name', full_view_name,
            'command_attempted', refresh_command
        )
    WHERE id = refresh_id;
    
    RAISE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- =====================================================

-- Índices para materialized_view_metrics
CREATE INDEX IF NOT EXISTS idx_mv_metrics_timestamp ON monitoring.materialized_view_metrics (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_mv_metrics_view_name ON monitoring.materialized_view_metrics (schema_name, view_name);
CREATE INDEX IF NOT EXISTS idx_mv_metrics_health_status ON monitoring.materialized_view_metrics (health_status) WHERE health_status != 'healthy';

-- Índices para pg_cron_job_metrics
CREATE INDEX IF NOT EXISTS idx_pg_cron_metrics_timestamp ON monitoring.pg_cron_job_metrics (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_pg_cron_metrics_job_id ON monitoring.pg_cron_job_metrics (job_id);
CREATE INDEX IF NOT EXISTS idx_pg_cron_metrics_health_status ON monitoring.pg_cron_job_metrics (health_status) WHERE health_status != 'healthy';
CREATE INDEX IF NOT EXISTS idx_pg_cron_metrics_job_class ON monitoring.pg_cron_job_metrics (job_class);

-- Índices para view_refresh_history
CREATE INDEX IF NOT EXISTS idx_view_refresh_started_at ON monitoring.view_refresh_history (started_at DESC);
CREATE INDEX IF NOT EXISTS idx_view_refresh_view_name ON monitoring.view_refresh_history (schema_name, view_name);
CREATE INDEX IF NOT EXISTS idx_view_refresh_status ON monitoring.view_refresh_history (status);

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON TABLE monitoring.materialized_view_metrics IS 'Métricas y estado de todas las vistas materializadas del sistema';
COMMENT ON TABLE monitoring.pg_cron_job_metrics IS 'Métricas y estado de todos los trabajos programados con pg_cron';
COMMENT ON TABLE monitoring.view_refresh_history IS 'Historial completo de operaciones de refresco de vistas materializadas';
COMMENT ON FUNCTION monitoring.collect_materialized_view_metrics() IS 'Recolecta métricas de todas las vistas materializadas del sistema';
COMMENT ON FUNCTION monitoring.collect_pg_cron_metrics() IS 'Recolecta métricas de todos los trabajos pg_cron y su estado';
COMMENT ON FUNCTION monitoring.refresh_materialized_view_with_logging(TEXT, TEXT, BOOLEAN) IS 'Refresca una vista materializada con logging completo de la operación';

-- Verificación final
DO $$
BEGIN
    RAISE NOTICE '=== MONITOREO DE VISTAS MATERIALIZADAS Y JOBS PG_CRON IMPLEMENTADO ===';
    RAISE NOTICE 'Tablas creadas: materialized_view_metrics, pg_cron_job_metrics, view_refresh_history';
    RAISE NOTICE 'Funciones principales: collect_materialized_view_metrics, collect_pg_cron_metrics';
    RAISE NOTICE 'Función de utilidad: refresh_materialized_view_with_logging';
    RAISE NOTICE '';
    RAISE NOTICE 'Para probar:';
    RAISE NOTICE '  - Métricas de vistas: SELECT monitoring.collect_materialized_view_metrics();';
    RAISE NOTICE '  - Métricas de jobs: SELECT monitoring.collect_pg_cron_metrics();';
    RAISE NOTICE '  - Refrescar vista: SELECT monitoring.refresh_materialized_view_with_logging(''public'', ''vista_ejemplo'');';
END $$;
