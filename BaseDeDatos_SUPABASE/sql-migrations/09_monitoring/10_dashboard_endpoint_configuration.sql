-- =====================================================
-- CONFIGURACIÓN DE ENDPOINTS PARA DASHBOARD
-- Archivo: 10_dashboard_endpoint_configuration.sql
-- Descripción: Configuración de endpoints y permisos para el dashboard
-- =====================================================

-- =====================================================
-- CONFIGURACIÓN DE ROL PARA DASHBOARD
-- =====================================================

-- Crear rol específico para el dashboard si no existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'dashboard_reader') THEN
        CREATE ROLE dashboard_reader;
        RAISE NOTICE 'Rol dashboard_reader creado';
    ELSE
        RAISE NOTICE 'Rol dashboard_reader ya existe';
    END IF;
END $$;

-- Otorgar permisos mínimos necesarios para el dashboard
GRANT USAGE ON SCHEMA monitoring TO dashboard_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA monitoring TO dashboard_reader;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA monitoring TO dashboard_reader;

-- Otorgar permisos específicos para funciones del dashboard
GRANT EXECUTE ON FUNCTION monitoring.get_complete_dashboard_data() TO dashboard_reader;
GRANT EXECUTE ON FUNCTION monitoring.get_realtime_performance_metrics() TO dashboard_reader;
GRANT EXECUTE ON FUNCTION monitoring.get_alerts_summary_widget() TO dashboard_reader;
GRANT EXECUTE ON FUNCTION monitoring.get_critical_services_status() TO dashboard_reader;
GRANT EXECUTE ON FUNCTION monitoring.get_resource_usage_chart_data(INTEGER, INTEGER) TO dashboard_reader;
GRANT EXECUTE ON FUNCTION monitoring.get_alerts_trend_chart_data(INTEGER) TO dashboard_reader;
GRANT EXECUTE ON FUNCTION monitoring.get_webhook_data() TO dashboard_reader;

-- =====================================================
-- VISTAS SIMPLIFICADAS PARA ENDPOINTS REST
-- =====================================================

-- Vista para endpoint de métricas principales
CREATE OR REPLACE VIEW monitoring.dashboard_main_metrics AS
SELECT 
    'main_metrics'::text as endpoint_type,
    monitoring.get_complete_dashboard_data() as data,
    NOW() as generated_at;

-- Vista para endpoint de métricas en tiempo real
CREATE OR REPLACE VIEW monitoring.dashboard_realtime_metrics AS
SELECT 
    'realtime_metrics'::text as endpoint_type,
    monitoring.get_realtime_performance_metrics() as data,
    NOW() as generated_at;

-- Vista para endpoint de alertas
CREATE OR REPLACE VIEW monitoring.dashboard_alerts AS
SELECT 
    'alerts'::text as endpoint_type,
    monitoring.get_alerts_summary_widget() as data,
    NOW() as generated_at;

-- Vista para endpoint de servicios críticos
CREATE OR REPLACE VIEW monitoring.dashboard_services AS
SELECT 
    'critical_services'::text as endpoint_type,
    monitoring.get_critical_services_status() as data,
    NOW() as generated_at;

-- Otorgar permisos a las vistas
GRANT SELECT ON monitoring.dashboard_main_metrics TO dashboard_reader;
GRANT SELECT ON monitoring.dashboard_realtime_metrics TO dashboard_reader;
GRANT SELECT ON monitoring.dashboard_alerts TO dashboard_reader;
GRANT SELECT ON monitoring.dashboard_services TO dashboard_reader;

-- =====================================================
-- FUNCIÓN PARA CONFIGURAR CORS Y HEADERS DE API
-- =====================================================

-- Función para configurar headers apropiados para el dashboard
CREATE OR REPLACE FUNCTION monitoring.get_dashboard_headers()
RETURNS TABLE (
    header_name TEXT,
    header_value TEXT
) AS $$
BEGIN
    RETURN QUERY VALUES
        ('Content-Type', 'application/json'),
        ('Cache-Control', 'no-cache, no-store, must-revalidate'),
        ('Pragma', 'no-cache'),
        ('Expires', '0'),
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type, Authorization');
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIONES SIMPLIFICADAS PARA ENDPOINTS ESPECÍFICOS
-- =====================================================

-- Endpoint para obtener solo métricas de sistema
CREATE OR REPLACE FUNCTION monitoring.get_system_metrics_only()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'timestamp', NOW(),
        'system_metrics', (
            SELECT jsonb_build_object(
                'cpu_usage_percent', cpu_usage_percent,
                'memory_usage_percent', memory_usage_percent,
                'storage_usage_percent', storage_usage_percent,
                'connection_usage_percent', connection_usage_percent,
                'cache_hit_ratio', cache_hit_ratio,
                'database_size_mb', database_size_mb,
                'total_connections', total_connections,
                'active_connections', active_connections,
                'last_updated', timestamp
            )
            FROM monitoring.system_metrics 
            ORDER BY timestamp DESC 
            LIMIT 1
        )
    ) INTO result;
    
    RETURN COALESCE(result, '{"error": "No data available"}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- Endpoint para obtener solo alertas críticas
CREATE OR REPLACE FUNCTION monitoring.get_critical_alerts_only()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'timestamp', NOW(),
        'critical_alerts', COALESCE(jsonb_agg(
            jsonb_build_object(
                'id', id,
                'title', title,
                'severity', severity,
                'metric_name', metric_name,
                'metric_value', metric_value,
                'hours_active', ROUND(EXTRACT(epoch FROM (NOW() - timestamp)) / 3600, 1),
                'description', description
            ) ORDER BY timestamp DESC
        ), '[]'::jsonb),
        'total_critical', COUNT(*)
    ) INTO result
    FROM monitoring.alerts 
    WHERE status = 'active' 
    AND severity = 'critical';
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Endpoint para estado de salud simplificado
CREATE OR REPLACE FUNCTION monitoring.get_health_status_simple()
RETURNS JSONB AS $$
DECLARE
    critical_alerts INTEGER;
    latest_metrics RECORD;
    overall_status TEXT;
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
    overall_status := CASE 
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
        'status', overall_status,
        'critical_alerts', critical_alerts,
        'system_ok', latest_metrics IS NOT NULL,
        'data_freshness_minutes', CASE 
            WHEN latest_metrics.timestamp IS NOT NULL 
            THEN ROUND(EXTRACT(epoch FROM (NOW() - latest_metrics.timestamp)) / 60)
            ELSE NULL 
        END
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- CONFIGURACIÓN DE LIMPIEZA Y OPTIMIZACIÓN PARA DASHBOARD
-- =====================================================

-- Función para limpiar datos antiguos específicamente para el dashboard
CREATE OR REPLACE FUNCTION monitoring.cleanup_dashboard_cache()
RETURNS TEXT AS $$
DECLARE
    cleanup_result TEXT;
BEGIN
    -- Limpiar métricas muy antiguas que no se usan en el dashboard
    DELETE FROM monitoring.system_metrics 
    WHERE timestamp < NOW() - INTERVAL '7 days';
    
    DELETE FROM monitoring.supabase_metrics 
    WHERE timestamp < NOW() - INTERVAL '7 days';
    
    -- Limpiar alertas resueltas muy antiguas
    DELETE FROM monitoring.alerts 
    WHERE status = 'resolved' 
    AND resolved_at < NOW() - INTERVAL '30 days';
    
    -- Limpiar trabajos de recolección antiguos
    DELETE FROM monitoring.collection_jobs 
    WHERE started_at < NOW() - INTERVAL '3 days';
    
    -- Actualizar estadísticas de las tablas
    ANALYZE monitoring.system_metrics;
    ANALYZE monitoring.supabase_metrics;
    ANALYZE monitoring.alerts;
    
    cleanup_result := format(
        'Limpieza completada para dashboard a las %s',
        NOW()::text
    );
    
    RAISE NOTICE '%', cleanup_result;
    RETURN cleanup_result;
END;
$$ LANGUAGE plpgsql;

-- Trabajo de limpieza específico para el dashboard
SELECT cron.schedule(
    'cleanup-dashboard-cache',
    '0 6 * * *',                   -- Diariamente a las 6:00 AM
    'SELECT monitoring.cleanup_dashboard_cache();'
);

-- =====================================================
-- CONFIGURACIÓN DE RATE LIMITING PARA ENDPOINTS
-- =====================================================

-- Tabla para tracking de rate limiting
CREATE TABLE IF NOT EXISTS monitoring.api_rate_limiting (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_ip INET,
    endpoint_name TEXT NOT NULL,
    request_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    request_count INTEGER DEFAULT 1,
    
    UNIQUE(client_ip, endpoint_name, DATE(request_timestamp))
);

-- Función para verificar rate limiting
CREATE OR REPLACE FUNCTION monitoring.check_rate_limit(
    p_client_ip INET,
    p_endpoint_name TEXT,
    p_max_requests_per_hour INTEGER DEFAULT 1000
)
RETURNS BOOLEAN AS $$
DECLARE
    current_hour_requests INTEGER;
BEGIN
    -- Contar requests en la última hora
    SELECT COUNT(*) INTO current_hour_requests
    FROM monitoring.api_rate_limiting
    WHERE client_ip = p_client_ip
    AND endpoint_name = p_endpoint_name
    AND request_timestamp > NOW() - INTERVAL '1 hour';
    
    -- Registrar esta request
    INSERT INTO monitoring.api_rate_limiting (client_ip, endpoint_name)
    VALUES (p_client_ip, p_endpoint_name)
    ON CONFLICT (client_ip, endpoint_name, DATE(request_timestamp))
    DO UPDATE SET 
        request_count = monitoring.api_rate_limiting.request_count + 1,
        request_timestamp = NOW();
    
    -- Retornar si está dentro del límite
    RETURN current_hour_requests < p_max_requests_per_hour;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- CONFIGURACIÓN DE LOGS PARA EL DASHBOARD
-- =====================================================

-- Tabla para logs de acceso al dashboard
CREATE TABLE IF NOT EXISTS monitoring.dashboard_access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    client_ip INET,
    user_agent TEXT,
    endpoint_called TEXT,
    response_time_ms INTEGER,
    status_code INTEGER,
    error_message TEXT,
    
    -- Índices para consultas rápidas
    INDEX_timestamp TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_dashboard_access_logs_timestamp 
ON monitoring.dashboard_access_logs (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_dashboard_access_logs_endpoint 
ON monitoring.dashboard_access_logs (endpoint_called);

-- Función para registrar acceso al dashboard
CREATE OR REPLACE FUNCTION monitoring.log_dashboard_access(
    p_client_ip INET,
    p_user_agent TEXT,
    p_endpoint TEXT,
    p_response_time_ms INTEGER DEFAULT NULL,
    p_status_code INTEGER DEFAULT 200,
    p_error_message TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO monitoring.dashboard_access_logs (
        client_ip, user_agent, endpoint_called, 
        response_time_ms, status_code, error_message
    ) VALUES (
        p_client_ip, p_user_agent, p_endpoint,
        p_response_time_ms, p_status_code, p_error_message
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- OTORGAR PERMISOS FINALES
-- =====================================================

-- Otorgar permisos a las nuevas funciones
GRANT EXECUTE ON FUNCTION monitoring.get_system_metrics_only() TO dashboard_reader;
GRANT EXECUTE ON FUNCTION monitoring.get_critical_alerts_only() TO dashboard_reader;
GRANT EXECUTE ON FUNCTION monitoring.get_health_status_simple() TO dashboard_reader;
GRANT EXECUTE ON FUNCTION monitoring.check_rate_limit(INET, TEXT, INTEGER) TO dashboard_reader;
GRANT EXECUTE ON FUNCTION monitoring.log_dashboard_access(INET, TEXT, TEXT, INTEGER, INTEGER, TEXT) TO dashboard_reader;

-- Otorgar permisos a las tablas de logs
GRANT SELECT, INSERT ON monitoring.api_rate_limiting TO dashboard_reader;
GRANT SELECT, INSERT ON monitoring.dashboard_access_logs TO dashboard_reader;

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON ROLE dashboard_reader IS 'Rol específico para acceso de solo lectura del dashboard de monitoreo';
COMMENT ON VIEW monitoring.dashboard_main_metrics IS 'Endpoint principal para métricas completas del dashboard';
COMMENT ON VIEW monitoring.dashboard_realtime_metrics IS 'Endpoint para métricas en tiempo real del dashboard';
COMMENT ON FUNCTION monitoring.get_system_metrics_only() IS 'Endpoint simplificado para métricas del sistema únicamente';
COMMENT ON FUNCTION monitoring.get_critical_alerts_only() IS 'Endpoint para obtener solo alertas críticas';
COMMENT ON FUNCTION monitoring.get_health_status_simple() IS 'Endpoint simplificado para estado de salud del sistema';
COMMENT ON TABLE monitoring.dashboard_access_logs IS 'Logs de acceso al dashboard para auditoría y monitoreo de uso';

-- Verificación final
DO $$
BEGIN
    RAISE NOTICE '=== CONFIGURACIÓN DE ENDPOINTS PARA DASHBOARD COMPLETADA ===';
    RAISE NOTICE 'Rol creado: dashboard_reader';
    RAISE NOTICE 'Vistas de endpoint: dashboard_main_metrics, dashboard_realtime_metrics, dashboard_alerts, dashboard_services';
    RAISE NOTICE 'Funciones simplificadas: get_system_metrics_only, get_critical_alerts_only, get_health_status_simple';
    RAISE NOTICE 'Sistema de rate limiting configurado';
    RAISE NOTICE 'Logs de acceso configurados';
    RAISE NOTICE '';
    RAISE NOTICE 'Endpoints disponibles para el dashboard:';
    RAISE NOTICE '  - GET /rest/v1/monitoring.dashboard_main_metrics (datos completos)';
    RAISE NOTICE '  - GET /rest/v1/rpc/get_system_metrics_only (solo sistema)';
    RAISE NOTICE '  - GET /rest/v1/rpc/get_critical_alerts_only (solo alertas críticas)';
    RAISE NOTICE '  - GET /rest/v1/rpc/get_health_status_simple (estado simple)';
    RAISE NOTICE '';
    RAISE NOTICE 'Configurar en Supabase:';
    RAISE NOTICE '  1. Crear usuario dashboard_reader';
    RAISE NOTICE '  2. Configurar Row Level Security si es necesario';
    RAISE NOTICE '  3. Actualizar URL base en el dashboard HTML';
END $$;
