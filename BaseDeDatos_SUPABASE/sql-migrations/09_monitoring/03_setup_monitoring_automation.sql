-- =====================================================
-- SISTEMA DE MONITOREO - AUTOMATIZACIÓN CON PG_CRON
-- Archivo: 03_setup_monitoring_automation.sql
-- Descripción: Configurar trabajos automáticos para recolección de métricas
-- =====================================================

-- Verificar que pg_cron esté disponible
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
        RAISE EXCEPTION 'La extensión pg_cron no está instalada. Es requerida para la automatización del monitoreo.';
    END IF;
    
    RAISE NOTICE 'Extensión pg_cron disponible ✓';
END $$;

-- =====================================================
-- CONFIGURAR TRABAJOS AUTOMÁTICOS
-- =====================================================

-- 1. Trabajo principal: Recolección de métricas cada 5 minutos
SELECT cron.schedule(
    'collect-system-metrics',      -- Nombre del trabajo
    '*/5 * * * *',                 -- Cada 5 minutos
    'SELECT monitoring.collect_system_metrics();'
);

-- 2. Trabajo de limpieza: Ejecutar diariamente a las 2:00 AM
SELECT cron.schedule(
    'cleanup-monitoring-data',
    '0 2 * * *',                   -- Diariamente a las 2:00 AM
    'SELECT monitoring.cleanup_old_data(30, 90, 7);' -- 30 días métricas, 90 días alertas, 7 días jobs
);

-- 3. Trabajo de análisis de consultas lentas: Cada hora
SELECT cron.schedule(
    'update-slow-queries-analysis',
    '0 * * * *',                   -- Cada hora en punto
    $slow_query_update$
    DO $$
    DECLARE
        slow_count INTEGER;
    BEGIN
        -- Contar consultas lentas
        SELECT COUNT(*) INTO slow_count
        FROM monitoring.get_slow_queries(1000, 50);
        
        -- Actualizar métrica si hay datos recientes
        UPDATE monitoring.system_metrics 
        SET slow_queries_count = slow_count,
            avg_query_time_ms = (
                SELECT AVG(mean_time_ms) 
                FROM monitoring.get_slow_queries(100, 100)
            )
        WHERE timestamp = (
            SELECT MAX(timestamp) 
            FROM monitoring.system_metrics
            WHERE timestamp > NOW() - INTERVAL '10 minutes'
        );
    END $$;
    $slow_query_update$
);

-- 4. Trabajo de mantenimiento de particiones: Semanal
SELECT cron.schedule(
    'maintenance-monitoring-partitions',
    '0 3 * * 0',                   -- Domingos a las 3:00 AM
    $partition_maintenance$
    DO $$
    DECLARE
        next_month DATE;
        partition_name TEXT;
        sql_command TEXT;
    BEGIN
        -- Crear partición para el próximo mes si no existe
        next_month := date_trunc('month', NOW() + INTERVAL '1 month');
        partition_name := 'monitoring.system_metrics_y' || 
                         to_char(next_month, 'YYYY') || 'm' || 
                         to_char(next_month, 'MM');
        
        sql_command := format(
            'CREATE TABLE IF NOT EXISTS %s PARTITION OF monitoring.system_metrics FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            next_month,
            next_month + INTERVAL '1 month'
        );
        
        EXECUTE sql_command;
        
        RAISE NOTICE 'Partición creada o verificada: %', partition_name;
    END $$;
    $partition_maintenance$
);

-- 5. Trabajo de verificación de salud del sistema: Cada 30 minutos
SELECT cron.schedule(
    'system-health-check',
    '*/30 * * * *',                -- Cada 30 minutos
    $health_check$
    DO $$
    DECLARE
        status_info JSONB;
        critical_alerts INTEGER;
    BEGIN
        -- Obtener estado del sistema
        SELECT monitoring.get_system_status() INTO status_info;
        
        critical_alerts := (status_info->'alerts'->>'critical')::INTEGER;
        
        -- Log del estado actual
        RAISE NOTICE 'Estado del sistema: % (Alertas críticas: %)', 
                     status_info->>'overall_status', critical_alerts;
        
        -- Si hay demasiadas alertas críticas, generar alerta especial
        IF critical_alerts >= 3 THEN
            INSERT INTO monitoring.alerts (
                timestamp, alert_type, severity, metric_name,
                metric_value, title, description, status,
                notification_channels, created_by
            ) VALUES (
                NOW(), 'system_health', 'critical', 'multiple_critical_alerts',
                critical_alerts, 
                format('Sistema con %s alertas críticas activas', critical_alerts),
                'El sistema tiene múltiples alertas críticas activas que requieren atención inmediata',
                'active', ARRAY['email', 'slack'], 'system'
            );
        END IF;
    END $$;
    $health_check$
);

-- =====================================================
-- FUNCIONES PARA GESTIONAR TRABAJOS
-- =====================================================

-- Función para obtener estado de trabajos de monitoreo
CREATE OR REPLACE FUNCTION monitoring.get_cron_jobs_status()
RETURNS TABLE (
    jobid BIGINT,
    schedule TEXT,
    command TEXT,
    nodename TEXT,
    nodeport INTEGER,
    database TEXT,
    username TEXT,
    active BOOLEAN,
    jobname TEXT
) AS $$
BEGIN
    RETURN QUERY
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
    WHERE j.jobname IN (
        'collect-system-metrics',
        'cleanup-monitoring-data', 
        'update-slow-queries-analysis',
        'maintenance-monitoring-partitions',
        'system-health-check'
    )
    ORDER BY j.jobname;
END;
$$ LANGUAGE plpgsql;

-- Función para pausar/reanudar trabajos de monitoreo
CREATE OR REPLACE FUNCTION monitoring.toggle_monitoring_jobs(p_enable BOOLEAN DEFAULT TRUE)
RETURNS TEXT AS $$
DECLARE
    job_rec RECORD;
    jobs_affected INTEGER := 0;
    action_text TEXT := CASE WHEN p_enable THEN 'habilitados' ELSE 'deshabilitados' END;
BEGIN
    FOR job_rec IN 
        SELECT jobid, jobname FROM cron.job 
        WHERE jobname IN (
            'collect-system-metrics',
            'cleanup-monitoring-data', 
            'update-slow-queries-analysis',
            'maintenance-monitoring-partitions',
            'system-health-check'
        )
    LOOP
        UPDATE cron.job 
        SET active = p_enable 
        WHERE jobid = job_rec.jobid;
        
        jobs_affected := jobs_affected + 1;
        RAISE NOTICE 'Trabajo % %', job_rec.jobname, action_text;
    END LOOP;
    
    RETURN format('%s trabajos de monitoreo %s', jobs_affected, action_text);
END;
$$ LANGUAGE plpgsql;

-- Función para ejecutar recolección manual
CREATE OR REPLACE FUNCTION monitoring.manual_collection()
RETURNS JSONB AS $$
DECLARE
    job_id UUID;
    result JSONB;
    start_time TIMESTAMPTZ := NOW();
BEGIN
    -- Ejecutar recolección manual
    SELECT monitoring.collect_system_metrics() INTO job_id;
    
    -- Obtener resultado del trabajo
    SELECT jsonb_build_object(
        'job_id', job_id,
        'started_at', start_time,
        'completed_at', NOW(),
        'status', 'completed',
        'execution_time_ms', EXTRACT(milliseconds FROM (NOW() - start_time))::INTEGER,
        'latest_metrics', monitoring.get_system_status()
    ) INTO result;
    
    RETURN result;
    
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'job_id', job_id,
        'started_at', start_time,
        'completed_at', NOW(),
        'status', 'failed',
        'error', SQLERRM,
        'execution_time_ms', EXTRACT(milliseconds FROM (NOW() - start_time))::INTEGER
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VISTAS PARA MONITOREO DE LA AUTOMATIZACIÓN
-- =====================================================

-- Vista para ver el historial reciente de trabajos
CREATE OR REPLACE VIEW monitoring.recent_job_history AS
SELECT 
    cj.id,
    cj.started_at,
    cj.completed_at,
    cj.job_type,
    cj.status,
    cj.metrics_collected,
    cj.alerts_generated,
    cj.errors_count,
    cj.execution_time_ms,
    cj.error_message,
    CASE 
        WHEN cj.execution_time_ms > 30000 THEN 'slow'
        WHEN cj.execution_time_ms > 10000 THEN 'normal'
        ELSE 'fast'
    END as performance_category
FROM monitoring.collection_jobs cj
WHERE cj.started_at > NOW() - INTERVAL '24 hours'
ORDER BY cj.started_at DESC;

-- Vista para estadísticas de rendimiento de trabajos
CREATE OR REPLACE VIEW monitoring.job_performance_stats AS
SELECT 
    job_type,
    COUNT(*) as total_jobs,
    COUNT(*) FILTER (WHERE status = 'completed') as successful_jobs,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_jobs,
    ROUND(AVG(execution_time_ms), 2) as avg_execution_time_ms,
    MAX(execution_time_ms) as max_execution_time_ms,
    MIN(execution_time_ms) as min_execution_time_ms,
    SUM(metrics_collected) as total_metrics_collected,
    SUM(alerts_generated) as total_alerts_generated
FROM monitoring.collection_jobs
WHERE started_at > NOW() - INTERVAL '7 days'
GROUP BY job_type
ORDER BY total_jobs DESC;

-- =====================================================
-- CONFIGURACIONES FINALES
-- =====================================================

-- Crear tabla para configuración del sistema de monitoreo
CREATE TABLE IF NOT EXISTS monitoring.system_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by TEXT DEFAULT current_user
);

-- Insertar configuraciones por defecto
INSERT INTO monitoring.system_config (key, value, description) VALUES
    ('collection_enabled', 'true', 'Habilitar recolección automática de métricas'),
    ('collection_interval_minutes', '5', 'Intervalo de recolección en minutos'),
    ('retention_metrics_days', '30', 'Días de retención para métricas'),
    ('retention_alerts_days', '90', 'Días de retención para alertas'),
    ('retention_jobs_days', '7', 'Días de retención para trabajos'),
    ('alert_notifications_enabled', 'true', 'Habilitar notificaciones de alertas'),
    ('slow_query_threshold_ms', '1000', 'Umbral para considerar consultas lentas (ms)'),
    ('health_check_interval_minutes', '30', 'Intervalo de verificación de salud')
ON CONFLICT (key) DO NOTHING;

-- Trigger para actualizar timestamp en configuraciones
CREATE TRIGGER trigger_system_config_updated_at
    BEFORE UPDATE ON monitoring.system_config
    FOR EACH ROW
    EXECUTE FUNCTION monitoring.update_updated_at_column();

-- =====================================================
-- VERIFICACIÓN FINAL Y DOCUMENTACIÓN
-- =====================================================

-- Comentarios
COMMENT ON FUNCTION monitoring.get_cron_jobs_status() IS 'Obtiene el estado de todos los trabajos de monitoreo configurados en pg_cron';
COMMENT ON FUNCTION monitoring.toggle_monitoring_jobs(BOOLEAN) IS 'Habilita o deshabilita todos los trabajos de monitoreo automático';
COMMENT ON FUNCTION monitoring.manual_collection() IS 'Ejecuta una recolección manual de métricas y devuelve el resultado';
COMMENT ON VIEW monitoring.recent_job_history IS 'Historial de trabajos de monitoreo de las últimas 24 horas';
COMMENT ON VIEW monitoring.job_performance_stats IS 'Estadísticas de rendimiento de trabajos de los últimos 7 días';
COMMENT ON TABLE monitoring.system_config IS 'Configuración del sistema de monitoreo';

-- Verificación y reporte final
DO $$
DECLARE
    jobs_created INTEGER;
    config_count INTEGER;
BEGIN
    -- Contar trabajos creados
    SELECT COUNT(*) INTO jobs_created
    FROM cron.job 
    WHERE jobname IN (
        'collect-system-metrics',
        'cleanup-monitoring-data', 
        'update-slow-queries-analysis',
        'maintenance-monitoring-partitions',
        'system-health-check'
    );
    
    -- Contar configuraciones
    SELECT COUNT(*) INTO config_count
    FROM monitoring.system_config;
    
    RAISE NOTICE '=== AUTOMATIZACIÓN DEL SISTEMA DE MONITOREO CONFIGURADA ===';
    RAISE NOTICE 'Trabajos pg_cron creados: %', jobs_created;
    RAISE NOTICE 'Configuraciones del sistema: %', config_count;
    RAISE NOTICE 'Funciones de gestión: get_cron_jobs_status, toggle_monitoring_jobs, manual_collection';
    RAISE NOTICE 'Vistas de monitoreo: recent_job_history, job_performance_stats';
    RAISE NOTICE '';
    RAISE NOTICE 'Para verificar el estado: SELECT * FROM monitoring.get_cron_jobs_status();';
    RAISE NOTICE 'Para recolección manual: SELECT monitoring.manual_collection();';
    RAISE NOTICE 'Para pausar trabajos: SELECT monitoring.toggle_monitoring_jobs(FALSE);';
    RAISE NOTICE 'Para reanudar trabajos: SELECT monitoring.toggle_monitoring_jobs(TRUE);';
END $$;
