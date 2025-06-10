-- =====================================================
-- AUTOMATIZACIÓN Y ALERTAS PARA VISTAS Y JOBS
-- Archivo: 08_views_jobs_automation_and_alerts.sql
-- Descripción: Automatización y alertas para vistas materializadas y jobs pg_cron
-- =====================================================

-- =====================================================
-- TRABAJOS AUTOMÁTICOS PARA MONITOREO DE VISTAS Y JOBS
-- =====================================================

-- Trabajo para recolectar métricas de vistas materializadas cada 30 minutos
SELECT cron.schedule(
    'collect-materialized-views-metrics',
    '*/30 * * * *',                -- Cada 30 minutos
    'SELECT monitoring.collect_materialized_view_metrics();'
);

-- Trabajo para recolectar métricas de jobs pg_cron cada 15 minutos
SELECT cron.schedule(
    'collect-pg-cron-metrics',
    '*/15 * * * *',                -- Cada 15 minutos
    'SELECT monitoring.collect_pg_cron_metrics();'
);

-- Trabajo para refrescar vistas materializadas críticas cada 4 horas
SELECT cron.schedule(
    'refresh-critical-materialized-views',
    '0 */4 * * *',                 -- Cada 4 horas
    $refresh_critical_views$
    DO $$
    DECLARE
        view_rec RECORD;
        refresh_id UUID;
        critical_views TEXT[] := ARRAY[
            'agenda_eventos_proximos',
            'resumen_hilos_activos',
            'entidades_relevantes_recientes',
            'estadisticas_globales',
            'tendencias_temas'
        ];
    BEGIN
        -- Refrescar vistas materializadas críticas del sistema Máquina de Noticias
        FOREACH view_name IN ARRAY critical_views
        LOOP
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_matviews WHERE matviewname = view_name) THEN
                    SELECT monitoring.refresh_materialized_view_with_logging(
                        'public', 
                        view_name, 
                        TRUE  -- Concurrently para evitar bloqueos
                    ) INTO refresh_id;
                    
                    RAISE NOTICE 'Vista materializada % refrescada exitosamente (ID: %)', view_name, refresh_id;
                ELSE
                    RAISE NOTICE 'Vista materializada % no encontrada, omitiendo', view_name;
                END IF;
                
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Error refrescando vista %: %', view_name, SQLERRM;
                
                -- Generar alerta por fallo en refresco
                INSERT INTO monitoring.alerts (
                    timestamp, alert_type, severity, metric_name,
                    metric_value, title, description, status,
                    notification_channels, created_by, tags
                ) VALUES (
                    NOW(), 'materialized_view_refresh_failed', 'warning', 
                    'view_refresh_error',
                    1, 
                    format('Fallo al refrescar vista materializada: %s', view_name),
                    format('La vista materializada %s falló al refrescarse automáticamente: %s', view_name, SQLERRM),
                    'active', ARRAY['email'], 'view_refresh_monitor',
                    jsonb_build_object('view_name', view_name, 'error_type', 'refresh_failure')
                );
            END;
        END LOOP;
    END $$;
    $refresh_critical_views$
);

-- Trabajo de verificación de salud de jobs críticos cada hora
SELECT cron.schedule(
    'check-critical-jobs-health',
    '0 * * * *',                   -- Cada hora en punto
    $check_jobs_health$
    DO $$
    DECLARE
        job_rec RECORD;
        alert_threshold INTEGER := 3; -- Máximo de fallos consecutivos permitidos
        critical_job_patterns TEXT[] := ARRAY[
            '%monitoring%',
            '%collect%',
            '%backup%',
            '%critical%'
        ];
    BEGIN
        -- Verificar estado de jobs críticos
        FOR job_rec IN 
            SELECT DISTINCT
                jm.job_id,
                jm.job_name,
                jm.failed_runs_last_24h,
                jm.consecutive_failures,
                jm.last_error_message,
                jm.health_status,
                jm.active
            FROM monitoring.pg_cron_job_metrics jm
            WHERE jm.timestamp = (
                SELECT MAX(timestamp) 
                FROM monitoring.pg_cron_job_metrics jm2 
                WHERE jm2.job_id = jm.job_id
            )
            AND (
                jm.job_name LIKE ANY(critical_job_patterns) OR
                jm.job_class IN ('monitoring', 'critical')
            )
            AND jm.active = TRUE
        LOOP
            -- Generar alerta para jobs con muchos fallos
            IF job_rec.failed_runs_last_24h >= alert_threshold THEN
                -- Verificar si ya existe una alerta activa para este job
                IF NOT EXISTS (
                    SELECT 1 FROM monitoring.alerts 
                    WHERE metric_name = 'pg_cron_job_failures'
                    AND tags->>'job_id' = job_rec.job_id::TEXT
                    AND status = 'active'
                    AND timestamp > NOW() - INTERVAL '24 hours'
                ) THEN
                    INSERT INTO monitoring.alerts (
                        timestamp, alert_type, severity, metric_name,
                        metric_value, title, description, status,
                        notification_channels, created_by, tags
                    ) VALUES (
                        NOW(), 'pg_cron_job_failing', 'critical', 
                        'pg_cron_job_failures',
                        job_rec.failed_runs_last_24h, 
                        format('Job crítico fallando: %s', job_rec.job_name),
                        format('El job pg_cron "%s" ha fallado %s veces en las últimas 24 horas. Último error: %s', 
                               job_rec.job_name, job_rec.failed_runs_last_24h, 
                               COALESCE(job_rec.last_error_message, 'Sin mensaje de error')),
                        'active', ARRAY['email', 'slack'], 'job_health_monitor',
                        jsonb_build_object(
                            'job_id', job_rec.job_id, 
                            'job_name', job_rec.job_name,
                            'failure_count', job_rec.failed_runs_last_24h
                        )
                    );
                    
                    RAISE NOTICE 'Alerta generada para job fallando: % (% fallos)', 
                                 job_rec.job_name, job_rec.failed_runs_last_24h;
                END IF;
            END IF;
            
            -- Alerta para jobs inactivos cuando deberían estar activos
            IF NOT job_rec.active AND job_rec.job_name LIKE '%monitoring%' THEN
                IF NOT EXISTS (
                    SELECT 1 FROM monitoring.alerts 
                    WHERE metric_name = 'pg_cron_job_disabled'
                    AND tags->>'job_id' = job_rec.job_id::TEXT
                    AND status = 'active'
                    AND timestamp > NOW() - INTERVAL '24 hours'
                ) THEN
                    INSERT INTO monitoring.alerts (
                        timestamp, alert_type, severity, metric_name,
                        metric_value, title, description, status,
                        notification_channels, created_by, tags
                    ) VALUES (
                        NOW(), 'pg_cron_job_disabled', 'warning', 
                        'pg_cron_job_disabled',
                        0, 
                        format('Job crítico deshabilitado: %s', job_rec.job_name),
                        format('El job pg_cron "%s" está deshabilitado pero debería estar activo para el monitoreo del sistema', 
                               job_rec.job_name),
                        'active', ARRAY['email'], 'job_health_monitor',
                        jsonb_build_object(
                            'job_id', job_rec.job_id, 
                            'job_name', job_rec.job_name
                        )
                    );
                END IF;
            END IF;
        END LOOP;
    END $$;
    $check_jobs_health$
);

-- =====================================================
-- FUNCIÓN PARA VERIFICAR SALUD DE VISTAS MATERIALIZADAS
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.check_materialized_views_health()
RETURNS INTEGER AS $$
DECLARE
    view_rec RECORD;
    alerts_generated INTEGER := 0;
    stale_threshold_hours INTEGER := 6; -- Considerar vista obsoleta después de 6 horas sin actualizar
    empty_view_threshold INTEGER := 1000; -- Alertar si vista que normalmente tiene datos está vacía
BEGIN
    -- Verificar vistas materializadas potencialmente problemáticas
    FOR view_rec IN 
        SELECT DISTINCT
            vm.schema_name,
            vm.view_name,
            vm.row_count,
            vm.size_mb,
            vm.health_status,
            vm.last_refresh_timestamp,
            vm.last_error_message
        FROM monitoring.materialized_view_metrics vm
        WHERE vm.timestamp = (
            SELECT MAX(timestamp) 
            FROM monitoring.materialized_view_metrics vm2 
            WHERE vm2.schema_name = vm.schema_name 
            AND vm2.view_name = vm.view_name
        )
        AND vm.view_exists = TRUE
    LOOP
        -- Alerta para vistas con problemas de salud
        IF view_rec.health_status IN ('critical', 'warning') THEN
            -- Verificar si ya existe una alerta activa para esta vista
            IF NOT EXISTS (
                SELECT 1 FROM monitoring.alerts 
                WHERE metric_name = 'materialized_view_health'
                AND tags->>'view_name' = (view_rec.schema_name || '.' || view_rec.view_name)
                AND status = 'active'
                AND timestamp > NOW() - INTERVAL '2 hours'
            ) THEN
                INSERT INTO monitoring.alerts (
                    timestamp, alert_type, severity, metric_name,
                    metric_value, title, description, status,
                    notification_channels, created_by, tags
                ) VALUES (
                    NOW(), 'materialized_view_health_issue', 
                    CASE WHEN view_rec.health_status = 'critical' THEN 'critical' ELSE 'warning' END,
                    'materialized_view_health',
                    CASE WHEN view_rec.row_count IS NOT NULL THEN view_rec.row_count ELSE 0 END, 
                    format('Problema de salud en vista materializada: %s.%s', 
                           view_rec.schema_name, view_rec.view_name),
                    format('La vista materializada %s.%s tiene estado de salud "%s". %s', 
                           view_rec.schema_name, view_rec.view_name, view_rec.health_status,
                           CASE WHEN view_rec.last_error_message IS NOT NULL 
                                THEN 'Error: ' || view_rec.last_error_message 
                                ELSE 'Revisar métricas para más detalles.' END),
                    'active', ARRAY['email'], 'view_health_monitor',
                    jsonb_build_object(
                        'view_name', view_rec.schema_name || '.' || view_rec.view_name,
                        'health_status', view_rec.health_status,
                        'row_count', view_rec.row_count,
                        'size_mb', view_rec.size_mb
                    )
                );
                
                alerts_generated := alerts_generated + 1;
            END IF;
        END IF;
        
        -- Alerta para vistas que no se han actualizado recientemente
        IF view_rec.last_refresh_timestamp IS NOT NULL 
           AND view_rec.last_refresh_timestamp < NOW() - INTERVAL '1 hour' * stale_threshold_hours
           AND view_rec.view_name IN ('agenda_eventos_proximos', 'resumen_hilos_activos', 'entidades_relevantes_recientes') THEN
            
            IF NOT EXISTS (
                SELECT 1 FROM monitoring.alerts 
                WHERE metric_name = 'materialized_view_stale'
                AND tags->>'view_name' = (view_rec.schema_name || '.' || view_rec.view_name)
                AND status = 'active'
                AND timestamp > NOW() - INTERVAL '6 hours'
            ) THEN
                INSERT INTO monitoring.alerts (
                    timestamp, alert_type, severity, metric_name,
                    metric_value, title, description, status,
                    notification_channels, created_by, tags
                ) VALUES (
                    NOW(), 'materialized_view_stale', 'warning',
                    'materialized_view_stale',
                    EXTRACT(hours FROM (NOW() - view_rec.last_refresh_timestamp)), 
                    format('Vista materializada obsoleta: %s.%s', 
                           view_rec.schema_name, view_rec.view_name),
                    format('La vista materializada %s.%s no se ha actualizado en %.1f horas (última actualización: %s)', 
                           view_rec.schema_name, view_rec.view_name,
                           EXTRACT(hours FROM (NOW() - view_rec.last_refresh_timestamp)),
                           view_rec.last_refresh_timestamp),
                    'active', ARRAY['email'], 'view_freshness_monitor',
                    jsonb_build_object(
                        'view_name', view_rec.schema_name || '.' || view_rec.view_name,
                        'hours_since_refresh', EXTRACT(hours FROM (NOW() - view_rec.last_refresh_timestamp)),
                        'last_refresh', view_rec.last_refresh_timestamp
                    )
                );
                
                alerts_generated := alerts_generated + 1;
            END IF;
        END IF;
    END LOOP;
    
    RETURN alerts_generated;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VISTAS PARA MONITOREO DE VISTAS Y JOBS
-- =====================================================

-- Vista de estado actual de vistas materializadas
CREATE OR REPLACE VIEW monitoring.materialized_views_status AS
SELECT 
    vm.schema_name,
    vm.view_name,
    vm.full_view_name,
    vm.health_status,
    vm.row_count,
    vm.size_mb,
    vm.indexes_count,
    vm.last_refresh_timestamp,
    CASE 
        WHEN vm.last_refresh_timestamp IS NULL THEN 'never_refreshed'
        WHEN vm.last_refresh_timestamp < NOW() - INTERVAL '6 hours' THEN 'stale'
        WHEN vm.last_refresh_timestamp < NOW() - INTERVAL '2 hours' THEN 'aging'
        ELSE 'fresh'
    END as freshness_status,
    EXTRACT(hours FROM (NOW() - vm.last_refresh_timestamp)) as hours_since_refresh,
    vm.last_error_message,
    vm.timestamp as last_checked
FROM monitoring.materialized_view_metrics vm
WHERE vm.timestamp = (
    SELECT MAX(timestamp) 
    FROM monitoring.materialized_view_metrics vm2 
    WHERE vm2.schema_name = vm.schema_name 
    AND vm2.view_name = vm.view_name
)
AND vm.view_exists = TRUE
ORDER BY 
    CASE vm.health_status 
        WHEN 'critical' THEN 1 
        WHEN 'warning' THEN 2 
        ELSE 3 
    END,
    vm.schema_name, vm.view_name;

-- Vista de estado actual de jobs pg_cron
CREATE OR REPLACE VIEW monitoring.pg_cron_jobs_status AS
SELECT 
    jm.job_id,
    jm.job_name,
    jm.schedule,
    jm.job_class,
    jm.active,
    jm.health_status,
    jm.last_run_status,
    jm.last_run_started_at,
    jm.last_run_finished_at,
    jm.last_run_duration_ms,
    jm.runs_last_24h,
    jm.successful_runs_last_24h,
    jm.failed_runs_last_24h,
    CASE 
        WHEN jm.failed_runs_last_24h = 0 THEN 100.0
        ELSE ROUND((jm.successful_runs_last_24h::decimal / jm.runs_last_24h) * 100, 2)
    END as success_rate_24h,
    jm.avg_duration_last_24h_ms,
    jm.consecutive_failures,
    jm.last_error_message,
    CASE 
        WHEN NOT jm.active THEN 'disabled'
        WHEN jm.failed_runs_last_24h > 3 THEN 'failing'
        WHEN jm.runs_last_24h = 0 THEN 'not_running'
        WHEN jm.failed_runs_last_24h > 0 THEN 'occasional_failures'
        ELSE 'healthy'
    END as operational_status,
    jm.timestamp as last_checked
FROM monitoring.pg_cron_job_metrics jm
WHERE jm.timestamp = (
    SELECT MAX(timestamp) 
    FROM monitoring.pg_cron_job_metrics jm2 
    WHERE jm2.job_id = jm.job_id
)
ORDER BY 
    CASE jm.health_status 
        WHEN 'critical' THEN 1 
        WHEN 'warning' THEN 2 
        WHEN 'disabled' THEN 3
        ELSE 4 
    END,
    CASE jm.job_class 
        WHEN 'critical' THEN 1 
        WHEN 'monitoring' THEN 2 
        WHEN 'maintenance' THEN 3 
        ELSE 4 
    END,
    jm.job_name;

-- Vista combinada de alertas de vistas y jobs
CREATE OR REPLACE VIEW monitoring.views_jobs_alerts_dashboard AS
SELECT 
    a.id,
    a.timestamp,
    a.severity,
    a.alert_type,
    a.metric_name,
    a.title,
    a.description,
    EXTRACT(hours FROM (NOW() - a.timestamp)) as hours_active,
    CASE 
        WHEN a.alert_type LIKE '%materialized_view%' THEN 'materialized_view'
        WHEN a.alert_type LIKE '%pg_cron%' THEN 'pg_cron_job'
        ELSE 'other'
    END as component_type,
    a.tags->>'view_name' as affected_view,
    a.tags->>'job_name' as affected_job,
    a.notification_sent,
    a.notification_channels,
    CASE 
        WHEN a.severity = 'critical' AND component_type = 'materialized_view' THEN 1
        WHEN a.severity = 'critical' AND component_type = 'pg_cron_job' THEN 2
        WHEN a.severity = 'warning' AND component_type = 'materialized_view' THEN 3
        WHEN a.severity = 'warning' AND component_type = 'pg_cron_job' THEN 4
        ELSE 5
    END as priority_order
FROM monitoring.alerts a
WHERE a.status = 'active'
AND (a.alert_type LIKE '%materialized_view%' OR a.alert_type LIKE '%pg_cron%')
ORDER BY priority_order, a.timestamp DESC;

-- =====================================================
-- FUNCIÓN PARA DASHBOARD COMBINADO DE VISTAS Y JOBS
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.get_views_jobs_dashboard()
RETURNS JSONB AS $$
DECLARE
    views_summary RECORD;
    jobs_summary RECORD;
    alerts_summary RECORD;
    result JSONB;
BEGIN
    -- Resumen de vistas materializadas
    SELECT 
        COUNT(*) as total_views,
        COUNT(*) FILTER (WHERE health_status = 'healthy') as healthy_views,
        COUNT(*) FILTER (WHERE health_status = 'warning') as warning_views,
        COUNT(*) FILTER (WHERE health_status = 'critical') as critical_views,
        COUNT(*) FILTER (WHERE freshness_status = 'stale') as stale_views,
        ROUND(AVG(size_mb), 2) as avg_size_mb,
        SUM(row_count) as total_rows
    INTO views_summary
    FROM monitoring.materialized_views_status;
    
    -- Resumen de jobs pg_cron
    SELECT 
        COUNT(*) as total_jobs,
        COUNT(*) FILTER (WHERE health_status = 'healthy') as healthy_jobs,
        COUNT(*) FILTER (WHERE health_status = 'warning') as warning_jobs,
        COUNT(*) FILTER (WHERE health_status = 'critical') as critical_jobs,
        COUNT(*) FILTER (WHERE NOT active) as disabled_jobs,
        ROUND(AVG(success_rate_24h), 2) as avg_success_rate,
        SUM(failed_runs_last_24h) as total_failures_24h
    INTO jobs_summary
    FROM monitoring.pg_cron_jobs_status;
    
    -- Resumen de alertas activas
    SELECT 
        COUNT(*) as total_alerts,
        COUNT(*) FILTER (WHERE component_type = 'materialized_view') as view_alerts,
        COUNT(*) FILTER (WHERE component_type = 'pg_cron_job') as job_alerts,
        COUNT(*) FILTER (WHERE severity = 'critical') as critical_alerts
    INTO alerts_summary
    FROM monitoring.views_jobs_alerts_dashboard;
    
    -- Construir resultado
    result := jsonb_build_object(
        'timestamp', NOW(),
        'overall_health', CASE 
            WHEN alerts_summary.critical_alerts > 0 THEN 'critical'
            WHEN alerts_summary.total_alerts > 0 THEN 'warning'
            ELSE 'healthy'
        END,
        'materialized_views', jsonb_build_object(
            'total', views_summary.total_views,
            'healthy', views_summary.healthy_views,
            'warning', views_summary.warning_views,
            'critical', views_summary.critical_views,
            'stale', views_summary.stale_views,
            'total_rows', views_summary.total_rows,
            'avg_size_mb', views_summary.avg_size_mb
        ),
        'pg_cron_jobs', jsonb_build_object(
            'total', jobs_summary.total_jobs,
            'healthy', jobs_summary.healthy_jobs,
            'warning', jobs_summary.warning_jobs,
            'critical', jobs_summary.critical_jobs,
            'disabled', jobs_summary.disabled_jobs,
            'avg_success_rate', jobs_summary.avg_success_rate,
            'total_failures_24h', jobs_summary.total_failures_24h
        ),
        'active_alerts', jsonb_build_object(
            'total', alerts_summary.total_alerts,
            'critical', alerts_summary.critical_alerts,
            'view_related', alerts_summary.view_alerts,
            'job_related', alerts_summary.job_alerts
        )
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON FUNCTION monitoring.check_materialized_views_health() IS 'Verifica la salud de vistas materializadas y genera alertas para problemas detectados';
COMMENT ON VIEW monitoring.materialized_views_status IS 'Estado actual de todas las vistas materializadas con métricas de frescura y salud';
COMMENT ON VIEW monitoring.pg_cron_jobs_status IS 'Estado actual de todos los jobs pg_cron con métricas de rendimiento y éxito';
COMMENT ON VIEW monitoring.views_jobs_alerts_dashboard IS 'Dashboard de alertas activas relacionadas con vistas materializadas y jobs pg_cron';
COMMENT ON FUNCTION monitoring.get_views_jobs_dashboard() IS 'Dashboard combinado con resumen de estado de vistas materializadas y jobs pg_cron';

-- Verificación final
DO $$
DECLARE
    new_jobs_count INTEGER;
    views_count INTEGER;
    jobs_count INTEGER;
BEGIN
    -- Contar trabajos de automatización nuevos
    SELECT COUNT(*) INTO new_jobs_count
    FROM cron.job 
    WHERE jobname IN ('collect-materialized-views-metrics', 'collect-pg-cron-metrics', 
                      'refresh-critical-materialized-views', 'check-critical-jobs-health');
    
    -- Contar vistas materializadas del sistema
    SELECT COUNT(*) INTO views_count FROM pg_matviews WHERE schemaname NOT IN ('information_schema', 'pg_catalog');
    
    -- Contar jobs pg_cron activos
    SELECT COUNT(*) INTO jobs_count FROM cron.job WHERE active = TRUE;
    
    RAISE NOTICE '=== AUTOMATIZACIÓN DE VISTAS Y JOBS COMPLETADA ===';
    RAISE NOTICE 'Nuevos trabajos pg_cron: %', new_jobs_count;
    RAISE NOTICE 'Vistas materializadas detectadas: %', views_count;
    RAISE NOTICE 'Jobs pg_cron activos: %', jobs_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Funciones implementadas:';
    RAISE NOTICE '  - check_materialized_views_health(): Verificación de salud de vistas';
    RAISE NOTICE '  - get_views_jobs_dashboard(): Dashboard combinado';
    RAISE NOTICE '';
    RAISE NOTICE 'Vistas de monitoreo:';
    RAISE NOTICE '  - materialized_views_status: Estado de vistas materializadas';
    RAISE NOTICE '  - pg_cron_jobs_status: Estado de jobs pg_cron';
    RAISE NOTICE '  - views_jobs_alerts_dashboard: Alertas activas';
    RAISE NOTICE '';
    RAISE NOTICE 'Para probar: SELECT monitoring.get_views_jobs_dashboard();';
END $$;
