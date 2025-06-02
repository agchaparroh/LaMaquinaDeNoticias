-- =====================================================
-- SISTEMA DE MONITOREO - VISTAS Y REPORTES
-- Archivo: 04_monitoring_views_and_reports.sql
-- Descripción: Vistas y reportes para análisis del sistema de monitoreo
-- =====================================================

-- =====================================================
-- VISTAS PARA DASHBOARD DE MÉTRICAS
-- =====================================================

-- Vista para métricas en tiempo real (últimas 24 horas)
CREATE OR REPLACE VIEW monitoring.metrics_realtime AS
SELECT 
    timestamp,
    cpu_usage_percent,
    memory_usage_percent,
    storage_usage_percent,
    connection_usage_percent,
    cache_hit_ratio,
    database_size_mb,
    total_connections,
    active_connections,
    idle_connections,
    slow_queries_count,
    avg_query_time_ms,
    current_locks,
    deadlocks_total,
    collection_time_ms,
    CASE 
        WHEN cpu_usage_percent > 90 OR memory_usage_percent > 95 OR storage_usage_percent > 95 THEN 'critical'
        WHEN cpu_usage_percent > 75 OR memory_usage_percent > 80 OR storage_usage_percent > 85 THEN 'warning'
        ELSE 'healthy'
    END as health_status
FROM monitoring.system_metrics
WHERE timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- Vista para tendencias por hora (últimos 7 días)
CREATE OR REPLACE VIEW monitoring.metrics_hourly_trends AS
SELECT 
    date_trunc('hour', timestamp) as hour,
    ROUND(AVG(cpu_usage_percent), 2) as avg_cpu_usage,
    ROUND(AVG(memory_usage_percent), 2) as avg_memory_usage,
    ROUND(AVG(storage_usage_percent), 2) as avg_storage_usage,
    ROUND(AVG(connection_usage_percent), 2) as avg_connection_usage,
    ROUND(AVG(cache_hit_ratio), 2) as avg_cache_hit_ratio,
    MAX(database_size_mb) as max_database_size_mb,
    ROUND(AVG(total_connections), 0) as avg_total_connections,
    ROUND(AVG(active_connections), 0) as avg_active_connections,
    SUM(slow_queries_count) as total_slow_queries,
    ROUND(AVG(avg_query_time_ms), 2) as avg_query_time_ms,
    MAX(current_locks) as max_concurrent_locks,
    SUM(deadlocks_total) as total_deadlocks,
    COUNT(*) as metrics_count
FROM monitoring.system_metrics
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY date_trunc('hour', timestamp)
ORDER BY hour DESC;

-- Vista para resumen diario (último mes)
CREATE OR REPLACE VIEW monitoring.metrics_daily_summary AS
SELECT 
    date_trunc('day', timestamp)::DATE as date,
    ROUND(AVG(cpu_usage_percent), 2) as avg_cpu_usage,
    MAX(cpu_usage_percent) as max_cpu_usage,
    ROUND(AVG(memory_usage_percent), 2) as avg_memory_usage,
    MAX(memory_usage_percent) as max_memory_usage,
    ROUND(AVG(storage_usage_percent), 2) as avg_storage_usage,
    MAX(storage_usage_percent) as max_storage_usage,
    ROUND(AVG(connection_usage_percent), 2) as avg_connection_usage,
    MAX(connection_usage_percent) as max_connection_usage,
    ROUND(AVG(cache_hit_ratio), 2) as avg_cache_hit_ratio,
    MIN(cache_hit_ratio) as min_cache_hit_ratio,
    MAX(database_size_mb) as end_of_day_database_size_mb,
    ROUND(AVG(total_connections), 0) as avg_total_connections,
    MAX(total_connections) as peak_connections,
    SUM(slow_queries_count) as daily_slow_queries,
    ROUND(AVG(avg_query_time_ms), 2) as avg_query_time_ms,
    MAX(avg_query_time_ms) as worst_query_time_ms,
    COUNT(*) as metrics_collected,
    -- Calcular tiempo de disponibilidad (asumiendo recolección cada 5 min)
    ROUND(COUNT(*) * 5.0 / (24 * 60) * 100, 2) as uptime_percentage
FROM monitoring.system_metrics
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY date_trunc('day', timestamp)::DATE
ORDER BY date DESC;

-- =====================================================
-- VISTAS PARA ANÁLISIS DE ALERTAS
-- =====================================================

-- Vista de alertas activas con información detallada
CREATE OR REPLACE VIEW monitoring.active_alerts_dashboard AS
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
    -- Obtener el valor actual de la métrica
    CASE a.metric_name
        WHEN 'cpu_usage_percent' THEN (SELECT cpu_usage_percent FROM monitoring.system_metrics ORDER BY timestamp DESC LIMIT 1)
        WHEN 'memory_usage_percent' THEN (SELECT memory_usage_percent FROM monitoring.system_metrics ORDER BY timestamp DESC LIMIT 1)
        WHEN 'storage_usage_percent' THEN (SELECT storage_usage_percent FROM monitoring.system_metrics ORDER BY timestamp DESC LIMIT 1)
        WHEN 'connection_usage_percent' THEN (SELECT connection_usage_percent FROM monitoring.system_metrics ORDER BY timestamp DESC LIMIT 1)
        WHEN 'cache_hit_ratio' THEN (SELECT cache_hit_ratio FROM monitoring.system_metrics ORDER BY timestamp DESC LIMIT 1)
        ELSE NULL
    END as current_metric_value,
    -- Determinar si la alerta debería resolverse automáticamente
    CASE 
        WHEN a.metric_name = 'cache_hit_ratio' THEN
            CASE WHEN (SELECT cache_hit_ratio FROM monitoring.system_metrics ORDER BY timestamp DESC LIMIT 1) > a.threshold_value THEN TRUE ELSE FALSE END
        ELSE
            CASE WHEN (
                CASE a.metric_name
                    WHEN 'cpu_usage_percent' THEN (SELECT cpu_usage_percent FROM monitoring.system_metrics ORDER BY timestamp DESC LIMIT 1)
                    WHEN 'memory_usage_percent' THEN (SELECT memory_usage_percent FROM monitoring.system_metrics ORDER BY timestamp DESC LIMIT 1)
                    WHEN 'storage_usage_percent' THEN (SELECT storage_usage_percent FROM monitoring.system_metrics ORDER BY timestamp DESC LIMIT 1)
                    WHEN 'connection_usage_percent' THEN (SELECT connection_usage_percent FROM monitoring.system_metrics ORDER BY timestamp DESC LIMIT 1)
                    ELSE NULL
                END
            ) < a.threshold_value THEN TRUE ELSE FALSE END
    END as should_auto_resolve
FROM monitoring.alerts a
WHERE a.status = 'active'
ORDER BY 
    CASE a.severity 
        WHEN 'critical' THEN 1 
        WHEN 'warning' THEN 2 
        ELSE 3 
    END,
    a.timestamp DESC;

-- Vista de historial de alertas con estadísticas
CREATE OR REPLACE VIEW monitoring.alerts_history_summary AS
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as total_alerts,
    COUNT(*) FILTER (WHERE severity = 'critical') as critical_alerts,
    COUNT(*) FILTER (WHERE severity = 'warning') as warning_alerts,
    COUNT(*) FILTER (WHERE severity = 'info') as info_alerts,
    COUNT(*) FILTER (WHERE status = 'resolved') as resolved_alerts,
    COUNT(*) FILTER (WHERE status = 'active') as still_active_alerts,
    -- Top 3 métricas con más alertas
    (SELECT json_agg(metric_stats ORDER BY alert_count DESC)
     FROM (
         SELECT metric_name, COUNT(*) as alert_count
         FROM monitoring.alerts a2 
         WHERE DATE(a2.timestamp) = DATE(a.timestamp)
         GROUP BY metric_name
         ORDER BY COUNT(*) DESC
         LIMIT 3
     ) metric_stats
    ) as top_problematic_metrics,
    ROUND(AVG(EXTRACT(hours FROM (COALESCE(resolved_at, NOW()) - timestamp))), 2) as avg_resolution_time_hours
FROM monitoring.alerts a
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- =====================================================
-- VISTAS PARA ANÁLISIS DE RENDIMIENTO
-- =====================================================

-- Vista de análisis de rendimiento de consultas
CREATE OR REPLACE VIEW monitoring.query_performance_analysis AS
WITH recent_metrics AS (
    SELECT 
        timestamp,
        avg_query_time_ms,
        slow_queries_count,
        total_connections,
        cache_hit_ratio,
        LAG(avg_query_time_ms) OVER (ORDER BY timestamp) as prev_avg_query_time,
        LAG(slow_queries_count) OVER (ORDER BY timestamp) as prev_slow_queries
    FROM monitoring.system_metrics
    WHERE timestamp > NOW() - INTERVAL '24 hours'
    AND avg_query_time_ms IS NOT NULL
)
SELECT 
    timestamp,
    avg_query_time_ms,
    slow_queries_count,
    total_connections,
    cache_hit_ratio,
    -- Calcular tendencias
    CASE 
        WHEN prev_avg_query_time IS NOT NULL THEN
            ROUND(((avg_query_time_ms - prev_avg_query_time) / prev_avg_query_time * 100), 2)
        ELSE NULL
    END as query_time_change_percent,
    CASE 
        WHEN prev_slow_queries IS NOT NULL THEN
            slow_queries_count - prev_slow_queries
        ELSE NULL
    END as slow_queries_change,
    -- Clasificar rendimiento
    CASE 
        WHEN avg_query_time_ms > 5000 THEN 'very_poor'
        WHEN avg_query_time_ms > 1000 THEN 'poor'
        WHEN avg_query_time_ms > 500 THEN 'fair'
        WHEN avg_query_time_ms > 100 THEN 'good'
        ELSE 'excellent'
    END as performance_rating
FROM recent_metrics
ORDER BY timestamp DESC;

-- Vista de análisis de recursos del sistema
CREATE OR REPLACE VIEW monitoring.resource_utilization_analysis AS
SELECT 
    timestamp,
    cpu_usage_percent,
    memory_usage_percent,
    storage_usage_percent,
    connection_usage_percent,
    database_size_mb,
    -- Calcular score de utilización combinada
    ROUND((cpu_usage_percent + memory_usage_percent + storage_usage_percent + connection_usage_percent) / 4, 2) as combined_utilization_score,
    -- Identificar recurso más limitante
    CASE 
        WHEN GREATEST(cpu_usage_percent, memory_usage_percent, storage_usage_percent, connection_usage_percent) = cpu_usage_percent THEN 'CPU'
        WHEN GREATEST(cpu_usage_percent, memory_usage_percent, storage_usage_percent, connection_usage_percent) = memory_usage_percent THEN 'Memory'
        WHEN GREATEST(cpu_usage_percent, memory_usage_percent, storage_usage_percent, connection_usage_percent) = storage_usage_percent THEN 'Storage'
        WHEN GREATEST(cpu_usage_percent, memory_usage_percent, storage_usage_percent, connection_usage_percent) = connection_usage_percent THEN 'Connections'
        ELSE 'Unknown'
    END as bottleneck_resource,
    GREATEST(cpu_usage_percent, memory_usage_percent, storage_usage_percent, connection_usage_percent) as bottleneck_percentage,
    -- Calcular tendencia de crecimiento de BD
    database_size_mb - LAG(database_size_mb, 288) OVER (ORDER BY timestamp) as daily_growth_mb, -- 288 = 24h * 12 (cada 5 min)
    -- Estado general del sistema
    CASE 
        WHEN GREATEST(cpu_usage_percent, memory_usage_percent, storage_usage_percent, connection_usage_percent) > 95 THEN 'critical'
        WHEN GREATEST(cpu_usage_percent, memory_usage_percent, storage_usage_percent, connection_usage_percent) > 85 THEN 'warning'
        WHEN GREATEST(cpu_usage_percent, memory_usage_percent, storage_usage_percent, connection_usage_percent) > 70 THEN 'caution'
        ELSE 'healthy'
    END as system_health_status
FROM monitoring.system_metrics
WHERE timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- =====================================================
-- FUNCIONES PARA REPORTES AVANZADOS
-- =====================================================

-- Función para generar reporte de estado del sistema
CREATE OR REPLACE FUNCTION monitoring.generate_system_health_report(
    p_hours_back INTEGER DEFAULT 24
)
RETURNS JSONB AS $$
DECLARE
    report JSONB;
    metrics_stats RECORD;
    alerts_stats RECORD;
    performance_stats RECORD;
BEGIN
    -- Estadísticas de métricas
    SELECT 
        COUNT(*) as total_metrics,
        ROUND(AVG(cpu_usage_percent), 2) as avg_cpu,
        MAX(cpu_usage_percent) as max_cpu,
        ROUND(AVG(memory_usage_percent), 2) as avg_memory,
        MAX(memory_usage_percent) as max_memory,
        ROUND(AVG(storage_usage_percent), 2) as avg_storage,
        MAX(storage_usage_percent) as max_storage,
        ROUND(AVG(connection_usage_percent), 2) as avg_connections,
        MAX(connection_usage_percent) as max_connections,
        ROUND(AVG(cache_hit_ratio), 2) as avg_cache_hit_ratio,
        MIN(cache_hit_ratio) as min_cache_hit_ratio
    INTO metrics_stats
    FROM monitoring.system_metrics
    WHERE timestamp > NOW() - INTERVAL '1 hour' * p_hours_back;
    
    -- Estadísticas de alertas
    SELECT 
        COUNT(*) as total_alerts,
        COUNT(*) FILTER (WHERE severity = 'critical') as critical_alerts,
        COUNT(*) FILTER (WHERE severity = 'warning') as warning_alerts,
        COUNT(*) FILTER (WHERE status = 'active') as active_alerts
    INTO alerts_stats
    FROM monitoring.alerts
    WHERE timestamp > NOW() - INTERVAL '1 hour' * p_hours_back;
    
    -- Estadísticas de rendimiento
    SELECT 
        ROUND(AVG(avg_query_time_ms), 2) as avg_query_time,
        MAX(avg_query_time_ms) as max_query_time,
        SUM(slow_queries_count) as total_slow_queries
    INTO performance_stats
    FROM monitoring.system_metrics
    WHERE timestamp > NOW() - INTERVAL '1 hour' * p_hours_back
    AND avg_query_time_ms IS NOT NULL;
    
    -- Construir reporte
    report := jsonb_build_object(
        'report_generated_at', NOW(),
        'period_hours', p_hours_back,
        'overall_status', CASE 
            WHEN alerts_stats.critical_alerts > 0 THEN 'critical'
            WHEN alerts_stats.warning_alerts > 0 THEN 'warning'
            ELSE 'healthy'
        END,
        'metrics_summary', jsonb_build_object(
            'total_data_points', metrics_stats.total_metrics,
            'cpu_usage', jsonb_build_object('avg', metrics_stats.avg_cpu, 'max', metrics_stats.max_cpu),
            'memory_usage', jsonb_build_object('avg', metrics_stats.avg_memory, 'max', metrics_stats.max_memory),
            'storage_usage', jsonb_build_object('avg', metrics_stats.avg_storage, 'max', metrics_stats.max_storage),
            'connection_usage', jsonb_build_object('avg', metrics_stats.avg_connections, 'max', metrics_stats.max_connections),
            'cache_performance', jsonb_build_object('avg_hit_ratio', metrics_stats.avg_cache_hit_ratio, 'min_hit_ratio', metrics_stats.min_cache_hit_ratio)
        ),
        'alerts_summary', jsonb_build_object(
            'total', alerts_stats.total_alerts,
            'critical', alerts_stats.critical_alerts,
            'warning', alerts_stats.warning_alerts,
            'currently_active', alerts_stats.active_alerts
        ),
        'performance_summary', jsonb_build_object(
            'avg_query_time_ms', performance_stats.avg_query_time,
            'max_query_time_ms', performance_stats.max_query_time,
            'total_slow_queries', performance_stats.total_slow_queries
        )
    );
    
    RETURN report;
END;
$$ LANGUAGE plpgsql;

-- Función para obtener métricas para dashboard en tiempo real
CREATE OR REPLACE FUNCTION monitoring.get_dashboard_metrics()
RETURNS JSONB AS $$
DECLARE
    latest_metrics RECORD;
    active_alerts INTEGER;
    critical_alerts INTEGER;
    system_status TEXT;
BEGIN
    -- Obtener métricas más recientes
    SELECT * INTO latest_metrics 
    FROM monitoring.system_metrics 
    ORDER BY timestamp DESC 
    LIMIT 1;
    
    -- Contar alertas activas
    SELECT 
        COUNT(*) FILTER (WHERE severity = 'critical'),
        COUNT(*)
    INTO critical_alerts, active_alerts
    FROM monitoring.alerts 
    WHERE status = 'active';
    
    -- Determinar estado del sistema
    system_status := CASE 
        WHEN critical_alerts > 0 THEN 'critical'
        WHEN active_alerts > 0 THEN 'warning'
        WHEN latest_metrics.cpu_usage_percent > 90 OR 
             latest_metrics.memory_usage_percent > 95 OR 
             latest_metrics.storage_usage_percent > 95 THEN 'critical'
        WHEN latest_metrics.cpu_usage_percent > 75 OR 
             latest_metrics.memory_usage_percent > 80 OR 
             latest_metrics.storage_usage_percent > 85 THEN 'warning'
        ELSE 'healthy'
    END;
    
    -- Construir respuesta para dashboard
    RETURN jsonb_build_object(
        'timestamp', COALESCE(latest_metrics.timestamp, NOW()),
        'system_status', system_status,
        'metrics', CASE 
            WHEN latest_metrics IS NOT NULL THEN
                jsonb_build_object(
                    'cpu_usage_percent', latest_metrics.cpu_usage_percent,
                    'memory_usage_percent', latest_metrics.memory_usage_percent,
                    'storage_usage_percent', latest_metrics.storage_usage_percent,
                    'connection_usage_percent', latest_metrics.connection_usage_percent,
                    'cache_hit_ratio', latest_metrics.cache_hit_ratio,
                    'database_size_mb', latest_metrics.database_size_mb,
                    'total_connections', latest_metrics.total_connections,
                    'active_connections', latest_metrics.active_connections,
                    'slow_queries_count', latest_metrics.slow_queries_count,
                    'avg_query_time_ms', latest_metrics.avg_query_time_ms
                )
            ELSE jsonb_build_object('error', 'No metrics available')
        END,
        'alerts', jsonb_build_object(
            'total_active', active_alerts,
            'critical', critical_alerts
        ),
        'data_freshness', CASE 
            WHEN latest_metrics.timestamp IS NOT NULL THEN
                EXTRACT(minutes FROM (NOW() - latest_metrics.timestamp))
            ELSE NULL
        END
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON VIEW monitoring.metrics_realtime IS 'Métricas en tiempo real de las últimas 24 horas con estado de salud';
COMMENT ON VIEW monitoring.metrics_hourly_trends IS 'Tendencias por hora de los últimos 7 días para análisis de patrones';
COMMENT ON VIEW monitoring.metrics_daily_summary IS 'Resumen diario del último mes con estadísticas clave y uptime';
COMMENT ON VIEW monitoring.active_alerts_dashboard IS 'Dashboard de alertas activas con información detallada y recomendaciones de resolución';
COMMENT ON VIEW monitoring.alerts_history_summary IS 'Historial y estadísticas de alertas por día';
COMMENT ON VIEW monitoring.query_performance_analysis IS 'Análisis de rendimiento de consultas con tendencias y clasificaciones';
COMMENT ON VIEW monitoring.resource_utilization_analysis IS 'Análisis de utilización de recursos con identificación de cuellos de botella';
COMMENT ON FUNCTION monitoring.generate_system_health_report(INTEGER) IS 'Genera un reporte completo del estado del sistema en formato JSON';
COMMENT ON FUNCTION monitoring.get_dashboard_metrics() IS 'Obtiene métricas optimizadas para dashboard en tiempo real';

-- Verificación final
DO $$
BEGIN
    RAISE NOTICE '=== VISTAS Y REPORTES DE MONITOREO CREADOS ===';
    RAISE NOTICE 'Vistas de métricas: metrics_realtime, metrics_hourly_trends, metrics_daily_summary';
    RAISE NOTICE 'Vistas de alertas: active_alerts_dashboard, alerts_history_summary';
    RAISE NOTICE 'Vistas de análisis: query_performance_analysis, resource_utilization_analysis';
    RAISE NOTICE 'Funciones de reporte: generate_system_health_report, get_dashboard_metrics';
    RAISE NOTICE '';
    RAISE NOTICE 'Para dashboard: SELECT monitoring.get_dashboard_metrics();';
    RAISE NOTICE 'Para reporte: SELECT monitoring.generate_system_health_report(24);';
    RAISE NOTICE 'Para alertas activas: SELECT * FROM monitoring.active_alerts_dashboard;';
END $$;
