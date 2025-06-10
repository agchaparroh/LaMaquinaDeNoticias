-- =====================================================
-- DASHBOARD API - FUNCIONES OPTIMIZADAS PARA FRONTEND
-- Archivo: 09_dashboard_api_functions.sql
-- Descripción: Funciones optimizadas para consumo desde dashboard visual
-- =====================================================

-- =====================================================
-- FUNCIÓN PRINCIPAL PARA DASHBOARD COMPLETO
-- =====================================================

-- Función que retorna todos los datos necesarios para el dashboard principal
CREATE OR REPLACE FUNCTION monitoring.get_complete_dashboard_data()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    system_data JSONB;
    supabase_data JSONB;
    views_jobs_data JSONB;
    alerts_data JSONB;
    trends_data JSONB;
BEGIN
    -- Obtener datos del sistema
    SELECT monitoring.get_system_status() INTO system_data;
    
    -- Obtener datos de Supabase
    SELECT monitoring.get_supabase_status() INTO supabase_data;
    
    -- Obtener datos de vistas y jobs
    SELECT monitoring.get_views_jobs_dashboard() INTO views_jobs_data;
    
    -- Obtener alertas activas prioritarias
    SELECT jsonb_agg(
        jsonb_build_object(
            'id', id,
            'severity', severity,
            'title', title,
            'hours_active', hours_active,
            'component_type', component_type,
            'affected_component', COALESCE(affected_view, affected_job)
        ) ORDER BY priority_order
    ) INTO alerts_data
    FROM monitoring.prioritized_alerts_dashboard
    LIMIT 10;
    
    -- Obtener datos de tendencias (últimas 24 horas, cada hora)
    SELECT jsonb_build_object(
        'hourly_metrics', jsonb_agg(
            jsonb_build_object(
                'hour', hour,
                'avg_cpu', avg_cpu_usage,
                'avg_memory', avg_memory_usage,
                'avg_connections', avg_connection_usage,
                'avg_cache_hit', avg_cache_hit_ratio
            ) ORDER BY hour DESC
        )
    ) INTO trends_data
    FROM monitoring.metrics_hourly_trends
    WHERE hour > NOW() - INTERVAL '24 hours'
    LIMIT 24;
    
    -- Combinar todos los datos
    result := jsonb_build_object(
        'timestamp', NOW(),
        'dashboard_version', '1.0.0',
        'refresh_interval_seconds', 30,
        'overall_status', CASE 
            WHEN (alerts_data::jsonb -> 0 ->> 'severity') = 'critical' THEN 'critical'
            WHEN jsonb_array_length(COALESCE(alerts_data, '[]'::jsonb)) > 0 THEN 'warning'
            ELSE 'healthy'
        END,
        'system', system_data,
        'supabase', supabase_data,
        'infrastructure', views_jobs_data,
        'active_alerts', COALESCE(alerts_data, '[]'::jsonb),
        'trends', trends_data,
        'summary', jsonb_build_object(
            'total_alerts', jsonb_array_length(COALESCE(alerts_data, '[]'::jsonb)),
            'system_health', system_data->>'overall_status',
            'supabase_health', supabase_data->>'overall_health',
            'infrastructure_health', views_jobs_data->>'overall_health',
            'last_updated', NOW()
        )
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIONES PARA MÉTRICAS ESPECÍFICAS DEL DASHBOARD
-- =====================================================

-- Función para obtener métricas de CPU y memoria en tiempo real
CREATE OR REPLACE FUNCTION monitoring.get_realtime_performance_metrics()
RETURNS JSONB AS $$
DECLARE
    latest_metrics RECORD;
    historical_data JSONB;
BEGIN
    -- Obtener métricas más recientes
    SELECT 
        cpu_usage_percent,
        memory_usage_percent,
        storage_usage_percent,
        connection_usage_percent,
        cache_hit_ratio,
        database_size_mb,
        total_connections,
        active_connections,
        timestamp
    INTO latest_metrics
    FROM monitoring.system_metrics 
    ORDER BY timestamp DESC 
    LIMIT 1;
    
    -- Obtener datos históricos de las últimas 6 horas (cada 30 minutos)
    SELECT jsonb_agg(
        jsonb_build_object(
            'timestamp', timestamp,
            'cpu', cpu_usage_percent,
            'memory', memory_usage_percent,
            'storage', storage_usage_percent,
            'connections', connection_usage_percent,
            'cache_hit', cache_hit_ratio
        ) ORDER BY timestamp DESC
    ) INTO historical_data
    FROM monitoring.system_metrics
    WHERE timestamp > NOW() - INTERVAL '6 hours'
    AND EXTRACT(minute FROM timestamp) IN (0, 30) -- Solo cada 30 minutos
    LIMIT 12;
    
    RETURN jsonb_build_object(
        'current', CASE 
            WHEN latest_metrics IS NOT NULL THEN
                jsonb_build_object(
                    'timestamp', latest_metrics.timestamp,
                    'cpu_usage_percent', latest_metrics.cpu_usage_percent,
                    'memory_usage_percent', latest_metrics.memory_usage_percent,
                    'storage_usage_percent', latest_metrics.storage_usage_percent,
                    'connection_usage_percent', latest_metrics.connection_usage_percent,
                    'cache_hit_ratio', latest_metrics.cache_hit_ratio,
                    'database_size_mb', latest_metrics.database_size_mb,
                    'total_connections', latest_metrics.total_connections,
                    'active_connections', latest_metrics.active_connections
                )
            ELSE NULL
        END,
        'historical', COALESCE(historical_data, '[]'::jsonb),
        'thresholds', jsonb_build_object(
            'cpu_warning', 75,
            'cpu_critical', 90,
            'memory_warning', 80,
            'memory_critical', 95,
            'storage_warning', 85,
            'storage_critical', 95,
            'connections_warning', 80,
            'connections_critical', 95
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Función para obtener resumen de alertas para widgets del dashboard
CREATE OR REPLACE FUNCTION monitoring.get_alerts_summary_widget()
RETURNS JSONB AS $$
DECLARE
    alerts_by_category JSONB;
    recent_alerts JSONB;
    alert_trends JSONB;
BEGIN
    -- Alertas agrupadas por categoría
    SELECT jsonb_object_agg(
        alert_category,
        jsonb_build_object(
            'total', count,
            'critical', critical_count,
            'warning', warning_count
        )
    ) INTO alerts_by_category
    FROM (
        SELECT 
            CASE 
                WHEN metric_name IN ('cpu_usage_percent', 'memory_usage_percent', 'storage_usage_percent') THEN 'system_resources'
                WHEN metric_name IN ('api_requests_limit', 'storage_limit', 'bandwidth_limit') THEN 'supabase_limits'
                WHEN alert_type LIKE '%materialized_view%' THEN 'views_jobs'
                WHEN alert_type LIKE '%pg_cron%' THEN 'views_jobs'
                ELSE 'other'
            END as alert_category,
            COUNT(*) as count,
            COUNT(*) FILTER (WHERE severity = 'critical') as critical_count,
            COUNT(*) FILTER (WHERE severity = 'warning') as warning_count
        FROM monitoring.alerts 
        WHERE status = 'active'
        GROUP BY alert_category
    ) grouped_alerts;
    
    -- Alertas recientes (últimas 5)
    SELECT jsonb_agg(
        jsonb_build_object(
            'id', id,
            'title', title,
            'severity', severity,
            'timestamp', timestamp,
            'hours_ago', ROUND(EXTRACT(epoch FROM (NOW() - timestamp)) / 3600, 1)
        ) ORDER BY timestamp DESC
    ) INTO recent_alerts
    FROM monitoring.alerts
    WHERE status = 'active'
    ORDER BY timestamp DESC
    LIMIT 5;
    
    -- Tendencia de alertas (últimos 7 días)
    SELECT jsonb_agg(
        jsonb_build_object(
            'date', date,
            'total', total_alerts,
            'critical', critical_alerts,
            'resolved', resolved_alerts
        ) ORDER BY date DESC
    ) INTO alert_trends
    FROM monitoring.alerts_history_summary
    WHERE date > CURRENT_DATE - INTERVAL '7 days'
    LIMIT 7;
    
    RETURN jsonb_build_object(
        'by_category', COALESCE(alerts_by_category, '{}'::jsonb),
        'recent_alerts', COALESCE(recent_alerts, '[]'::jsonb),
        'trend_7_days', COALESCE(alert_trends, '[]'::jsonb),
        'summary', jsonb_build_object(
            'total_active', (SELECT COUNT(*) FROM monitoring.alerts WHERE status = 'active'),
            'critical_active', (SELECT COUNT(*) FROM monitoring.alerts WHERE status = 'active' AND severity = 'critical'),
            'avg_resolution_time_hours', (
                SELECT ROUND(AVG(EXTRACT(hours FROM (resolved_at - timestamp))), 2)
                FROM monitoring.alerts 
                WHERE status = 'resolved' 
                AND resolved_at > NOW() - INTERVAL '7 days'
            )
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Función para obtener estado de servicios críticos
CREATE OR REPLACE FUNCTION monitoring.get_critical_services_status()
RETURNS JSONB AS $$
DECLARE
    database_status JSONB;
    supabase_services JSONB;
    infrastructure_status JSONB;
    monitoring_health JSONB;
BEGIN
    -- Estado de la base de datos
    SELECT jsonb_build_object(
        'status', CASE 
            WHEN connection_usage_percent > 95 OR cache_hit_ratio < 80 THEN 'critical'
            WHEN connection_usage_percent > 80 OR cache_hit_ratio < 90 THEN 'warning'
            ELSE 'healthy'
        END,
        'connections', jsonb_build_object(
            'active', active_connections,
            'total', total_connections,
            'usage_percent', connection_usage_percent
        ),
        'performance', jsonb_build_object(
            'cache_hit_ratio', cache_hit_ratio,
            'avg_query_time_ms', avg_query_time_ms,
            'slow_queries', slow_queries_count
        ),
        'size_mb', database_size_mb
    ) INTO database_status
    FROM monitoring.system_metrics 
    ORDER BY timestamp DESC 
    LIMIT 1;
    
    -- Estado de servicios de Supabase
    SELECT jsonb_build_object(
        'status', CASE 
            WHEN api_requests_usage_percent > 95 OR storage_usage_percent > 95 THEN 'critical'
            WHEN api_requests_usage_percent > 85 OR storage_usage_percent > 85 THEN 'warning'
            ELSE 'healthy'
        END,
        'api_usage_percent', api_requests_usage_percent,
        'storage_usage_percent', storage_usage_percent,
        'bandwidth_usage_percent', bandwidth_usage_percent,
        'edge_functions', jsonb_build_object(
            'error_rate', edge_function_error_rate,
            'avg_duration_ms', edge_function_avg_duration_ms
        ),
        'auth_users', auth_users_count
    ) INTO supabase_services
    FROM monitoring.supabase_metrics 
    ORDER BY timestamp DESC 
    LIMIT 1;
    
    -- Estado de infraestructura (vistas y jobs)
    SELECT jsonb_build_object(
        'materialized_views', jsonb_build_object(
            'total', total,
            'healthy', healthy,
            'stale', stale,
            'critical', critical
        ),
        'pg_cron_jobs', jsonb_build_object(
            'total', total,
            'healthy', healthy,
            'critical', critical,
            'disabled', disabled
        ),
        'status', overall_health
    ) INTO infrastructure_status
    FROM (
        SELECT 
            (materialized_views->>'total')::integer as total,
            (materialized_views->>'healthy')::integer as healthy,
            (materialized_views->>'stale')::integer as stale,
            (materialized_views->>'critical')::integer as critical,
            (pg_cron_jobs->>'total')::integer as total,
            (pg_cron_jobs->>'healthy')::integer as healthy,
            (pg_cron_jobs->>'critical')::integer as critical,
            (pg_cron_jobs->>'disabled')::integer as disabled,
            overall_health
        FROM monitoring.get_views_jobs_dashboard()
    ) vj;
    
    -- Estado del propio sistema de monitoreo
    SELECT jsonb_build_object(
        'status', CASE 
            WHEN failed_jobs_last_hour > 2 THEN 'critical'
            WHEN failed_jobs_last_hour > 0 THEN 'warning'
            ELSE 'healthy'
        END,
        'collections_last_hour', collections_last_hour,
        'failed_jobs_last_hour', failed_jobs_last_hour,
        'avg_collection_time_ms', avg_collection_time_ms,
        'last_collection', last_collection
    ) INTO monitoring_health
    FROM (
        SELECT 
            COUNT(*) as collections_last_hour,
            COUNT(*) FILTER (WHERE status = 'failed') as failed_jobs_last_hour,
            ROUND(AVG(execution_time_ms)) as avg_collection_time_ms,
            MAX(completed_at) as last_collection
        FROM monitoring.collection_jobs
        WHERE started_at > NOW() - INTERVAL '1 hour'
    ) monitoring_stats;
    
    RETURN jsonb_build_object(
        'database', COALESCE(database_status, jsonb_build_object('status', 'unknown')),
        'supabase', COALESCE(supabase_services, jsonb_build_object('status', 'unknown')),
        'infrastructure', COALESCE(infrastructure_status, jsonb_build_object('status', 'unknown')),
        'monitoring_system', COALESCE(monitoring_health, jsonb_build_object('status', 'unknown')),
        'overall_status', CASE 
            WHEN COALESCE((database_status->>'status'), 'unknown') = 'critical' OR
                 COALESCE((supabase_services->>'status'), 'unknown') = 'critical' OR
                 COALESCE((infrastructure_status->>'status'), 'unknown') = 'critical' OR
                 COALESCE((monitoring_health->>'status'), 'unknown') = 'critical' THEN 'critical'
            WHEN COALESCE((database_status->>'status'), 'unknown') = 'warning' OR
                 COALESCE((supabase_services->>'status'), 'unknown') = 'warning' OR
                 COALESCE((infrastructure_status->>'status'), 'unknown') = 'warning' OR
                 COALESCE((monitoring_health->>'status'), 'unknown') = 'warning' THEN 'warning'
            ELSE 'healthy'
        END
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA DATOS DE GRÁFICOS ESPECÍFICOS
-- =====================================================

-- Función para obtener datos de gráfico de tendencias de uso de recursos
CREATE OR REPLACE FUNCTION monitoring.get_resource_usage_chart_data(
    p_hours_back INTEGER DEFAULT 24,
    p_interval_minutes INTEGER DEFAULT 60
)
RETURNS JSONB AS $$
DECLARE
    chart_data JSONB;
BEGIN
    SELECT jsonb_build_object(
        'labels', jsonb_agg(to_char(hour, 'HH24:MI') ORDER BY hour),
        'datasets', jsonb_build_array(
            jsonb_build_object(
                'label', 'CPU %',
                'data', jsonb_agg(avg_cpu_usage ORDER BY hour),
                'borderColor', '#FF6384',
                'backgroundColor', 'rgba(255, 99, 132, 0.1)'
            ),
            jsonb_build_object(
                'label', 'Memoria %',
                'data', jsonb_agg(avg_memory_usage ORDER BY hour),
                'borderColor', '#36A2EB',
                'backgroundColor', 'rgba(54, 162, 235, 0.1)'
            ),
            jsonb_build_object(
                'label', 'Almacenamiento %',
                'data', jsonb_agg(avg_storage_usage ORDER BY hour),
                'borderColor', '#FFCE56',
                'backgroundColor', 'rgba(255, 206, 86, 0.1)'
            ),
            jsonb_build_object(
                'label', 'Conexiones %',
                'data', jsonb_agg(avg_connection_usage ORDER BY hour),
                'borderColor', '#4BC0C0',
                'backgroundColor', 'rgba(75, 192, 192, 0.1)'
            )
        )
    ) INTO chart_data
    FROM monitoring.metrics_hourly_trends
    WHERE hour > NOW() - INTERVAL '1 hour' * p_hours_back
    AND EXTRACT(minute FROM hour) = 0 -- Solo horas exactas
    ORDER BY hour;
    
    RETURN COALESCE(chart_data, jsonb_build_object('labels', '[]', 'datasets', '[]'));
END;
$$ LANGUAGE plpgsql;

-- Función para obtener datos de gráfico de alertas por día
CREATE OR REPLACE FUNCTION monitoring.get_alerts_trend_chart_data(
    p_days_back INTEGER DEFAULT 7
)
RETURNS JSONB AS $$
DECLARE
    chart_data JSONB;
BEGIN
    SELECT jsonb_build_object(
        'labels', jsonb_agg(to_char(date, 'DD/MM') ORDER BY date),
        'datasets', jsonb_build_array(
            jsonb_build_object(
                'label', 'Alertas Críticas',
                'data', jsonb_agg(critical_alerts ORDER BY date),
                'backgroundColor', '#FF6384'
            ),
            jsonb_build_object(
                'label', 'Alertas Warning',
                'data', jsonb_agg(warning_alerts ORDER BY date),
                'backgroundColor', '#FFCE56'
            ),
            jsonb_build_object(
                'label', 'Alertas Resueltas',
                'data', jsonb_agg(resolved_alerts ORDER BY date),
                'backgroundColor', '#4BC0C0'
            )
        )
    ) INTO chart_data
    FROM monitoring.alerts_history_summary
    WHERE date > CURRENT_DATE - INTERVAL '1 day' * p_days_back
    ORDER BY date;
    
    RETURN COALESCE(chart_data, jsonb_build_object('labels', '[]', 'datasets', '[]'));
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIONES PARA WEBHOOKS Y NOTIFICACIONES
-- =====================================================

-- Función para preparar datos para webhook (formato ligero)
CREATE OR REPLACE FUNCTION monitoring.get_webhook_data()
RETURNS JSONB AS $$
DECLARE
    critical_alerts INTEGER;
    system_health TEXT;
    latest_metrics RECORD;
BEGIN
    -- Contar alertas críticas
    SELECT COUNT(*) INTO critical_alerts
    FROM monitoring.alerts 
    WHERE status = 'active' AND severity = 'critical';
    
    -- Obtener métricas más recientes
    SELECT 
        cpu_usage_percent,
        memory_usage_percent,
        storage_usage_percent,
        connection_usage_percent,
        timestamp
    INTO latest_metrics
    FROM monitoring.system_metrics 
    ORDER BY timestamp DESC 
    LIMIT 1;
    
    -- Determinar estado general
    system_health := CASE 
        WHEN critical_alerts > 0 THEN 'critical'
        WHEN latest_metrics.cpu_usage_percent > 90 OR 
             latest_metrics.memory_usage_percent > 95 OR 
             latest_metrics.storage_usage_percent > 95 THEN 'critical'
        WHEN latest_metrics.cpu_usage_percent > 75 OR 
             latest_metrics.memory_usage_percent > 80 OR 
             latest_metrics.storage_usage_percent > 85 THEN 'warning'
        ELSE 'healthy'
    END;
    
    RETURN jsonb_build_object(
        'timestamp', NOW(),
        'system_health', system_health,
        'critical_alerts', critical_alerts,
        'key_metrics', CASE 
            WHEN latest_metrics IS NOT NULL THEN
                jsonb_build_object(
                    'cpu_usage', latest_metrics.cpu_usage_percent,
                    'memory_usage', latest_metrics.memory_usage_percent,
                    'storage_usage', latest_metrics.storage_usage_percent,
                    'connection_usage', latest_metrics.connection_usage_percent
                )
            ELSE NULL
        END
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- ÍNDICES PARA OPTIMIZACIÓN DE DASHBOARD
-- =====================================================

-- Índices adicionales para optimizar consultas del dashboard
CREATE INDEX IF NOT EXISTS idx_system_metrics_dashboard_latest 
ON monitoring.system_metrics (timestamp DESC) 
WHERE timestamp > NOW() - INTERVAL '24 hours';

CREATE INDEX IF NOT EXISTS idx_alerts_dashboard_active 
ON monitoring.alerts (status, severity, timestamp DESC) 
WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_collection_jobs_recent 
ON monitoring.collection_jobs (started_at DESC) 
WHERE started_at > NOW() - INTERVAL '1 hour';

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON FUNCTION monitoring.get_complete_dashboard_data() IS 'Función principal que retorna todos los datos necesarios para el dashboard completo';
COMMENT ON FUNCTION monitoring.get_realtime_performance_metrics() IS 'Métricas de rendimiento en tiempo real optimizadas para widgets de dashboard';
COMMENT ON FUNCTION monitoring.get_alerts_summary_widget() IS 'Resumen de alertas optimizado para widgets del dashboard';
COMMENT ON FUNCTION monitoring.get_critical_services_status() IS 'Estado de servicios críticos para indicadores de salud del dashboard';
COMMENT ON FUNCTION monitoring.get_resource_usage_chart_data(INTEGER, INTEGER) IS 'Datos formateados para gráficos de tendencias de recursos';
COMMENT ON FUNCTION monitoring.get_alerts_trend_chart_data(INTEGER) IS 'Datos formateados para gráficos de tendencias de alertas';
COMMENT ON FUNCTION monitoring.get_webhook_data() IS 'Datos ligeros optimizados para webhooks y notificaciones externas';

-- Verificación final
DO $$
BEGIN
    RAISE NOTICE '=== FUNCIONES API PARA DASHBOARD IMPLEMENTADAS ===';
    RAISE NOTICE 'Función principal: get_complete_dashboard_data()';
    RAISE NOTICE 'Funciones de widgets: get_realtime_performance_metrics(), get_alerts_summary_widget()';
    RAISE NOTICE 'Funciones de servicios: get_critical_services_status()';
    RAISE NOTICE 'Funciones de gráficos: get_resource_usage_chart_data(), get_alerts_trend_chart_data()';
    RAISE NOTICE 'Función de webhooks: get_webhook_data()';
    RAISE NOTICE '';
    RAISE NOTICE 'Para probar el dashboard completo:';
    RAISE NOTICE 'SELECT monitoring.get_complete_dashboard_data();';
    RAISE NOTICE '';
    RAISE NOTICE 'Para datos de gráfico de recursos:';
    RAISE NOTICE 'SELECT monitoring.get_resource_usage_chart_data(24, 60);';
END $$;
