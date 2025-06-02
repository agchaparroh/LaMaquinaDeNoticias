-- =====================================================
-- INTEGRACIÓN DE MONITOREO SUPABASE CON AUTOMATIZACIÓN
-- Archivo: 06_supabase_monitoring_automation.sql
-- Descripción: Integrar el monitoreo de Supabase con pg_cron y sistemas existentes
-- =====================================================

-- =====================================================
-- TRABAJOS AUTOMÁTICOS PARA SUPABASE
-- =====================================================

-- Trabajo de recolección de métricas de Supabase cada 15 minutos
SELECT cron.schedule(
    'collect-supabase-metrics',
    '*/15 * * * *',                -- Cada 15 minutos
    'SELECT monitoring.collect_supabase_metrics();'
);

-- Trabajo de verificación de límites de Supabase cada 10 minutos
SELECT cron.schedule(
    'check-supabase-limits',
    '*/10 * * * *',                -- Cada 10 minutos
    'SELECT monitoring.check_supabase_limits();'
);

-- Trabajo de limpieza específica para métricas de Supabase (semanal)
SELECT cron.schedule(
    'cleanup-supabase-data',
    '0 4 * * 1',                   -- Lunes a las 4:00 AM
    $cleanup_supabase$
    DO $$
    DECLARE
        deleted_supabase_metrics INTEGER;
        deleted_edge_function_metrics INTEGER;
    BEGIN
        -- Limpiar métricas de Supabase más antiguas de 60 días
        DELETE FROM monitoring.supabase_metrics 
        WHERE timestamp < NOW() - INTERVAL '60 days';
        GET DIAGNOSTICS deleted_supabase_metrics = ROW_COUNT;
        
        -- Limpiar métricas de Edge Functions más antiguas de 30 días
        DELETE FROM monitoring.edge_function_metrics 
        WHERE timestamp < NOW() - INTERVAL '30 days';
        GET DIAGNOSTICS deleted_edge_function_metrics = ROW_COUNT;
        
        RAISE NOTICE 'Limpieza Supabase: % métricas generales, % métricas de Edge Functions eliminadas',
                     deleted_supabase_metrics, deleted_edge_function_metrics;
    END $$;
    $cleanup_supabase$
);

-- =====================================================
-- FUNCIÓN PARA RECOLECCIÓN COMBINADA
-- =====================================================

-- Función que ejecuta tanto recolección sistema como Supabase
CREATE OR REPLACE FUNCTION monitoring.collect_all_metrics()
RETURNS JSONB AS $$
DECLARE
    system_job_id UUID;
    supabase_job_id UUID;
    system_alerts INTEGER;
    supabase_alerts INTEGER;
    result JSONB;
BEGIN
    -- Ejecutar recolección de métricas del sistema
    SELECT monitoring.collect_system_metrics() INTO system_job_id;
    
    -- Ejecutar recolección de métricas de Supabase
    SELECT monitoring.collect_supabase_metrics() INTO supabase_job_id;
    
    -- Verificar alertas
    SELECT monitoring.check_alert_thresholds() INTO system_alerts;
    SELECT monitoring.check_supabase_limits() INTO supabase_alerts;
    
    -- Construir resultado
    result := jsonb_build_object(
        'timestamp', NOW(),
        'system_collection', jsonb_build_object(
            'job_id', system_job_id,
            'alerts_generated', system_alerts
        ),
        'supabase_collection', jsonb_build_object(
            'job_id', supabase_job_id,
            'alerts_generated', supabase_alerts
        ),
        'total_alerts_generated', system_alerts + supabase_alerts
    );
    
    RETURN result;
    
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'timestamp', NOW(),
        'status', 'failed',
        'error', SQLERRM
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VISTAS COMBINADAS PARA DASHBOARD UNIFICADO
-- =====================================================

-- Vista unificada de estado del sistema completo
CREATE OR REPLACE VIEW monitoring.unified_system_status AS
SELECT 
    'system' as metric_source,
    sm.timestamp,
    sm.cpu_usage_percent,
    sm.memory_usage_percent,
    sm.storage_usage_percent,
    sm.connection_usage_percent,
    sm.cache_hit_ratio,
    sm.database_size_mb,
    sm.total_connections,
    sm.active_connections,
    NULL::TEXT as plan_type,
    NULL::DECIMAL as api_requests_usage_percent,
    NULL::DECIMAL as bandwidth_usage_percent,
    NULL::DECIMAL as edge_function_error_rate,
    CASE 
        WHEN sm.cpu_usage_percent > 90 OR sm.memory_usage_percent > 95 OR sm.storage_usage_percent > 95 THEN 'critical'
        WHEN sm.cpu_usage_percent > 75 OR sm.memory_usage_percent > 80 OR sm.storage_usage_percent > 85 THEN 'warning'
        ELSE 'healthy'
    END as health_status
FROM monitoring.system_metrics sm
WHERE sm.timestamp > NOW() - INTERVAL '24 hours'

UNION ALL

SELECT 
    'supabase' as metric_source,
    sp.timestamp,
    NULL::DECIMAL as cpu_usage_percent,
    NULL::DECIMAL as memory_usage_percent,
    sp.storage_usage_percent,
    NULL::DECIMAL as connection_usage_percent,
    NULL::DECIMAL as cache_hit_ratio,
    sp.storage_used_gb * 1024 as database_size_mb, -- Convertir GB a MB
    NULL::INTEGER as total_connections,
    NULL::INTEGER as active_connections,
    sp.plan_type,
    sp.api_requests_usage_percent,
    sp.bandwidth_usage_percent,
    sp.edge_function_error_rate,
    CASE 
        WHEN sp.api_requests_usage_percent > 95 OR sp.storage_usage_percent > 95 OR sp.bandwidth_usage_percent > 95 THEN 'critical'
        WHEN sp.api_requests_usage_percent > 85 OR sp.storage_usage_percent > 85 OR sp.bandwidth_usage_percent > 85 THEN 'warning'
        ELSE 'healthy'
    END as health_status
FROM monitoring.supabase_metrics sp
WHERE sp.timestamp > NOW() - INTERVAL '24 hours'

ORDER BY timestamp DESC;

-- Vista de alertas combinadas con priorización
CREATE OR REPLACE VIEW monitoring.prioritized_alerts_dashboard AS
SELECT 
    a.id,
    a.timestamp,
    a.severity,
    a.metric_name,
    a.metric_value,
    a.threshold_value,
    a.title,
    a.description,
    EXTRACT(hours FROM (NOW() - a.timestamp)) as hours_active,
    a.notification_sent,
    a.notification_channels,
    CASE 
        WHEN a.metric_name IN ('api_requests_limit', 'storage_limit', 'bandwidth_limit') THEN 'supabase_limit'
        WHEN a.metric_name LIKE '%edge_function%' THEN 'supabase_edge'
        WHEN a.metric_name LIKE '%api_%' THEN 'supabase_api'
        WHEN a.metric_name IN ('cpu_usage_percent', 'memory_usage_percent') THEN 'system_resource'
        WHEN a.metric_name IN ('connection_usage_percent', 'cache_hit_ratio') THEN 'database_performance'
        ELSE 'other'
    END as alert_category,
    -- Prioridad basada en severidad y categoría
    CASE 
        WHEN a.severity = 'critical' AND a.metric_name IN ('api_requests_limit', 'storage_limit') THEN 1
        WHEN a.severity = 'critical' AND a.metric_name IN ('cpu_usage_percent', 'memory_usage_percent') THEN 2
        WHEN a.severity = 'critical' THEN 3
        WHEN a.severity = 'warning' AND a.metric_name IN ('api_requests_limit', 'storage_limit') THEN 4
        WHEN a.severity = 'warning' THEN 5
        ELSE 6
    END as priority_order,
    a.tags
FROM monitoring.alerts a
WHERE a.status = 'active'
ORDER BY priority_order, a.timestamp DESC;

-- =====================================================
-- FUNCIONES PARA DASHBOARD UNIFICADO
-- =====================================================

-- Función para obtener métricas combinadas para dashboard
CREATE OR REPLACE FUNCTION monitoring.get_unified_dashboard_metrics()
RETURNS JSONB AS $$
DECLARE
    system_status JSONB;
    supabase_status JSONB;
    combined_alerts RECORD;
    result JSONB;
BEGIN
    -- Obtener estado del sistema
    SELECT monitoring.get_system_status() INTO system_status;
    
    -- Obtener estado de Supabase
    SELECT monitoring.get_supabase_status() INTO supabase_status;
    
    -- Obtener resumen de alertas combinadas
    SELECT 
        COUNT(*) as total_alerts,
        COUNT(*) FILTER (WHERE severity = 'critical') as critical_alerts,
        COUNT(*) FILTER (WHERE severity = 'warning') as warning_alerts,
        COUNT(*) FILTER (WHERE metric_name IN ('api_requests_limit', 'storage_limit', 'bandwidth_limit')) as supabase_limit_alerts,
        COUNT(*) FILTER (WHERE metric_name IN ('cpu_usage_percent', 'memory_usage_percent', 'storage_usage_percent')) as system_resource_alerts
    INTO combined_alerts
    FROM monitoring.alerts 
    WHERE status = 'active';
    
    -- Construir respuesta unificada
    result := jsonb_build_object(
        'timestamp', NOW(),
        'overall_health', CASE 
            WHEN combined_alerts.critical_alerts > 0 THEN 'critical'
            WHEN combined_alerts.warning_alerts > 0 THEN 'warning'
            ELSE 'healthy'
        END,
        'system_metrics', system_status,
        'supabase_metrics', supabase_status,
        'alerts_summary', jsonb_build_object(
            'total_active', combined_alerts.total_alerts,
            'critical', combined_alerts.critical_alerts,
            'warning', combined_alerts.warning_alerts,
            'by_category', jsonb_build_object(
                'supabase_limits', combined_alerts.supabase_limit_alerts,
                'system_resources', combined_alerts.system_resource_alerts
            )
        ),
        'recommendations', CASE 
            WHEN combined_alerts.supabase_limit_alerts > 0 THEN 
                jsonb_build_array('Revisar límites de plan de Supabase', 'Considerar upgrade de plan si es necesario')
            WHEN combined_alerts.system_resource_alerts > 0 THEN 
                jsonb_build_array('Revisar uso de recursos del sistema', 'Optimizar consultas si es necesario')
            ELSE 
                jsonb_build_array('Sistema funcionando correctamente')
        END
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA REPORTES EJECUTIVOS
-- =====================================================

-- Función para generar reporte ejecutivo completo
CREATE OR REPLACE FUNCTION monitoring.generate_executive_report(
    p_period_hours INTEGER DEFAULT 24
)
RETURNS JSONB AS $$
DECLARE
    report JSONB;
    system_summary RECORD;
    supabase_summary RECORD;
    alerts_summary RECORD;
    performance_summary RECORD;
BEGIN
    -- Resumen de métricas del sistema
    SELECT 
        COUNT(*) as data_points,
        ROUND(AVG(cpu_usage_percent), 2) as avg_cpu,
        MAX(cpu_usage_percent) as peak_cpu,
        ROUND(AVG(memory_usage_percent), 2) as avg_memory,
        MAX(memory_usage_percent) as peak_memory,
        ROUND(AVG(connection_usage_percent), 2) as avg_connections,
        MAX(connection_usage_percent) as peak_connections
    INTO system_summary
    FROM monitoring.system_metrics
    WHERE timestamp > NOW() - INTERVAL '1 hour' * p_period_hours;
    
    -- Resumen de métricas de Supabase
    SELECT 
        COUNT(*) as data_points,
        MAX(api_requests_usage_percent) as peak_api_usage,
        MAX(storage_usage_percent) as peak_storage_usage,
        MAX(bandwidth_usage_percent) as peak_bandwidth_usage,
        ROUND(AVG(edge_function_error_rate), 2) as avg_edge_error_rate,
        ROUND(AVG(api_avg_response_time_ms), 2) as avg_api_response_time
    INTO supabase_summary
    FROM monitoring.supabase_metrics
    WHERE timestamp > NOW() - INTERVAL '1 hour' * p_period_hours;
    
    -- Resumen de alertas
    SELECT 
        COUNT(*) as total_alerts,
        COUNT(*) FILTER (WHERE severity = 'critical') as critical_alerts,
        COUNT(*) FILTER (WHERE severity = 'warning') as warning_alerts,
        COUNT(*) FILTER (WHERE status = 'resolved') as resolved_alerts,
        ROUND(AVG(EXTRACT(hours FROM (COALESCE(resolved_at, NOW()) - timestamp))), 2) as avg_resolution_time_hours
    INTO alerts_summary
    FROM monitoring.alerts
    WHERE timestamp > NOW() - INTERVAL '1 hour' * p_period_hours;
    
    -- Resumen de rendimiento
    SELECT 
        ROUND(AVG(avg_query_time_ms), 2) as avg_query_time,
        MAX(avg_query_time_ms) as worst_query_time,
        SUM(slow_queries_count) as total_slow_queries,
        ROUND(AVG(cache_hit_ratio), 2) as avg_cache_hit_ratio
    INTO performance_summary
    FROM monitoring.system_metrics
    WHERE timestamp > NOW() - INTERVAL '1 hour' * p_period_hours
    AND avg_query_time_ms IS NOT NULL;
    
    -- Construir reporte ejecutivo
    report := jsonb_build_object(
        'report_info', jsonb_build_object(
            'generated_at', NOW(),
            'period_hours', p_period_hours,
            'report_type', 'executive_summary'
        ),
        'executive_summary', jsonb_build_object(
            'overall_health', CASE 
                WHEN alerts_summary.critical_alerts > 0 THEN 'requires_attention'
                WHEN alerts_summary.warning_alerts > 0 THEN 'monitoring_recommended'
                ELSE 'healthy'
            END,
            'key_metrics', jsonb_build_object(
                'system_uptime_percent', ROUND(GREATEST(system_summary.data_points * 5.0 / (p_period_hours * 60), 0) * 100, 2),
                'peak_cpu_usage', system_summary.peak_cpu,
                'peak_memory_usage', system_summary.peak_memory,
                'peak_api_usage', supabase_summary.peak_api_usage,
                'total_alerts', alerts_summary.total_alerts
            )
        ),
        'infrastructure_health', jsonb_build_object(
            'system_resources', jsonb_build_object(
                'cpu', jsonb_build_object('avg', system_summary.avg_cpu, 'peak', system_summary.peak_cpu),
                'memory', jsonb_build_object('avg', system_summary.avg_memory, 'peak', system_summary.peak_memory),
                'connections', jsonb_build_object('avg', system_summary.avg_connections, 'peak', system_summary.peak_connections)
            ),
            'database_performance', jsonb_build_object(
                'avg_query_time_ms', performance_summary.avg_query_time,
                'worst_query_time_ms', performance_summary.worst_query_time,
                'cache_hit_ratio', performance_summary.avg_cache_hit_ratio,
                'slow_queries_total', performance_summary.total_slow_queries
            )
        ),
        'supabase_services', jsonb_build_object(
            'usage_peaks', jsonb_build_object(
                'api_requests', supabase_summary.peak_api_usage,
                'storage', supabase_summary.peak_storage_usage,
                'bandwidth', supabase_summary.peak_bandwidth_usage
            ),
            'edge_functions', jsonb_build_object(
                'avg_error_rate', supabase_summary.avg_edge_error_rate,
                'avg_response_time_ms', supabase_summary.avg_api_response_time
            )
        ),
        'incident_management', jsonb_build_object(
            'alert_statistics', jsonb_build_object(
                'total', alerts_summary.total_alerts,
                'critical', alerts_summary.critical_alerts,
                'warning', alerts_summary.warning_alerts,
                'resolved', alerts_summary.resolved_alerts
            ),
            'response_metrics', jsonb_build_object(
                'avg_resolution_time_hours', alerts_summary.avg_resolution_time_hours
            )
        ),
        'recommendations', CASE 
            WHEN system_summary.peak_cpu > 90 OR system_summary.peak_memory > 95 THEN 
                jsonb_build_array(
                    'Considerar escalamiento de recursos del sistema',
                    'Revisar consultas y procesos que consumen más recursos',
                    'Implementar optimizaciones de rendimiento'
                )
            WHEN supabase_summary.peak_api_usage > 85 OR supabase_summary.peak_storage_usage > 85 THEN 
                jsonb_build_array(
                    'Evaluar upgrade del plan de Supabase',
                    'Optimizar uso de API para reducir llamadas',
                    'Revisar estrategias de almacenamiento'
                )
            WHEN alerts_summary.total_alerts > 0 THEN 
                jsonb_build_array(
                    'Revisar y resolver alertas pendientes',
                    'Ajustar umbrales de alertas si es necesario'
                )
            ELSE 
                jsonb_build_array(
                    'Sistema funcionando óptimamente',
                    'Continuar con monitoreo regular'
                )
        END
    );
    
    RETURN report;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- ACTUALIZAR TRABAJOS EXISTENTES
-- =====================================================

-- Modificar el trabajo de verificación de salud para incluir Supabase
SELECT cron.unschedule('system-health-check');

SELECT cron.schedule(
    'unified-system-health-check',
    '*/30 * * * *',                -- Cada 30 minutos
    $unified_health_check$
    DO $$
    DECLARE
        unified_status JSONB;
        critical_alerts INTEGER;
        supabase_critical INTEGER;
    BEGIN
        -- Obtener estado unificado del sistema
        SELECT monitoring.get_unified_dashboard_metrics() INTO unified_status;
        
        critical_alerts := (unified_status->'alerts_summary'->>'critical')::INTEGER;
        supabase_critical := (unified_status->'alerts_summary'->'by_category'->>'supabase_limits')::INTEGER;
        
        -- Log del estado actual
        RAISE NOTICE 'Estado unificado: % (Críticas: %, Supabase: %)', 
                     unified_status->>'overall_health', critical_alerts, supabase_critical;
        
        -- Si hay demasiadas alertas críticas, generar alerta especial
        IF critical_alerts >= 5 THEN
            INSERT INTO monitoring.alerts (
                timestamp, alert_type, severity, metric_name,
                metric_value, title, description, status,
                notification_channels, created_by, tags
            ) VALUES (
                NOW(), 'system_health', 'critical', 'multiple_critical_alerts',
                critical_alerts, 
                format('Sistema con %s alertas críticas activas', critical_alerts),
                'El sistema tiene múltiples alertas críticas activas que requieren atención inmediata',
                'active', ARRAY['email', 'slack'], 'unified_monitor',
                jsonb_build_object('alert_type', 'system_health', 'source', 'unified_monitoring')
            );
        END IF;
        
        -- Alerta específica para límites de Supabase
        IF supabase_critical >= 2 THEN
            INSERT INTO monitoring.alerts (
                timestamp, alert_type, severity, metric_name,
                metric_value, title, description, status,
                notification_channels, created_by, tags
            ) VALUES (
                NOW(), 'supabase_limits', 'warning', 'supabase_multiple_limits',
                supabase_critical, 
                format('Múltiples límites de Supabase en riesgo (%s)', supabase_critical),
                'Varios límites del plan de Supabase están cerca de agotarse. Considerar acciones preventivas.',
                'active', ARRAY['email'], 'unified_monitor',
                jsonb_build_object('alert_type', 'supabase_limits', 'source', 'unified_monitoring')
            );
        END IF;
    END $$;
    $unified_health_check$
);

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON FUNCTION monitoring.collect_all_metrics() IS 'Ejecuta recolección combinada de métricas del sistema y Supabase';
COMMENT ON VIEW monitoring.unified_system_status IS 'Vista unificada que combina métricas del sistema y Supabase para análisis integral';
COMMENT ON VIEW monitoring.prioritized_alerts_dashboard IS 'Dashboard de alertas con priorización automática basada en severidad y categoría';
COMMENT ON FUNCTION monitoring.get_unified_dashboard_metrics() IS 'Métricas combinadas optimizadas para dashboard unificado';
COMMENT ON FUNCTION monitoring.generate_executive_report(INTEGER) IS 'Genera reporte ejecutivo completo con métricas del sistema y Supabase';

-- Verificación final
DO $$
DECLARE
    new_jobs_count INTEGER;
    updated_jobs_count INTEGER;
BEGIN
    -- Contar trabajos relacionados con monitoreo
    SELECT COUNT(*) INTO new_jobs_count
    FROM cron.job 
    WHERE jobname LIKE '%supabase%' OR jobname LIKE '%unified%';
    
    SELECT COUNT(*) INTO updated_jobs_count
    FROM cron.job 
    WHERE jobname LIKE '%monitoring%' OR jobname LIKE '%system%' OR jobname LIKE '%cleanup%' OR jobname LIKE '%supabase%';
    
    RAISE NOTICE '=== INTEGRACIÓN DE MONITOREO SUPABASE COMPLETADA ===';
    RAISE NOTICE 'Nuevos trabajos pg_cron: %', new_jobs_count;
    RAISE NOTICE 'Total trabajos de monitoreo: %', updated_jobs_count;
    RAISE NOTICE 'Funciones combinadas: collect_all_metrics, get_unified_dashboard_metrics, generate_executive_report';
    RAISE NOTICE 'Vistas unificadas: unified_system_status, prioritized_alerts_dashboard';
    RAISE NOTICE '';
    RAISE NOTICE 'Comandos útiles:';
    RAISE NOTICE '  - Dashboard unificado: SELECT monitoring.get_unified_dashboard_metrics();';
    RAISE NOTICE '  - Reporte ejecutivo: SELECT monitoring.generate_executive_report(24);';
    RAISE NOTICE '  - Estado de trabajos: SELECT * FROM monitoring.get_cron_jobs_status();';
    RAISE NOTICE '  - Alertas priorizadas: SELECT * FROM monitoring.prioritized_alerts_dashboard;';
END $$;
