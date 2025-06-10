-- =====================================================
-- MONITOREO ESPECÍFICO DE SUPABASE
-- Archivo: 05_supabase_specific_monitoring.sql
-- Descripción: Monitoreo de servicios y límites específicos de Supabase
-- =====================================================

-- =====================================================
-- TABLA PARA MÉTRICAS ESPECÍFICAS DE SUPABASE
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.supabase_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Información del plan y límites
    plan_name TEXT,
    plan_type TEXT, -- 'free', 'pro', 'team', 'enterprise'
    
    -- Límites y uso del plan
    api_requests_limit BIGINT,
    api_requests_used BIGINT,
    api_requests_usage_percent DECIMAL(5,2),
    
    storage_limit_gb DECIMAL(10,2),
    storage_used_gb DECIMAL(10,2),
    storage_usage_percent DECIMAL(5,2),
    
    bandwidth_limit_gb DECIMAL(10,2),
    bandwidth_used_gb DECIMAL(10,2),
    bandwidth_usage_percent DECIMAL(5,2),
    
    -- Edge Functions métricas
    edge_function_invocations BIGINT DEFAULT 0,
    edge_function_errors BIGINT DEFAULT 0,
    edge_function_error_rate DECIMAL(5,2),
    edge_function_avg_duration_ms DECIMAL(10,2),
    
    -- Autenticación
    auth_users_count BIGINT,
    auth_daily_active_users BIGINT,
    auth_monthly_active_users BIGINT,
    
    -- API Performance
    api_avg_response_time_ms DECIMAL(10,2),
    api_success_rate DECIMAL(5,2),
    api_rate_limit_hits BIGINT DEFAULT 0,
    
    -- Real-time
    realtime_connections_count INTEGER DEFAULT 0,
    realtime_messages_sent BIGINT DEFAULT 0,
    
    -- Storage específico
    storage_objects_count BIGINT DEFAULT 0,
    storage_buckets_count INTEGER DEFAULT 0,
    
    -- Backups y Snapshots (para planes que lo soporten)
    backup_last_run TIMESTAMPTZ,
    backup_status TEXT,
    backup_size_mb BIGINT,
    
    -- Información de región y disponibilidad
    region TEXT,
    availability_status TEXT DEFAULT 'available',
    
    -- Metadatos de recolección
    collection_time_ms INTEGER,
    collector_version TEXT DEFAULT '1.0.0',
    data_source TEXT DEFAULT 'supabase_api', -- 'supabase_api', 'manual', 'estimated'
    
    CONSTRAINT valid_supabase_percentages CHECK (
        api_requests_usage_percent BETWEEN 0 AND 100 AND
        storage_usage_percent BETWEEN 0 AND 100 AND
        bandwidth_usage_percent BETWEEN 0 AND 100 AND
        edge_function_error_rate BETWEEN 0 AND 100 AND
        api_success_rate BETWEEN 0 AND 100
    )
);

-- Crear particionado por fecha para métricas de Supabase
CREATE TABLE IF NOT EXISTS monitoring.supabase_metrics_y2024m05
PARTITION OF monitoring.supabase_metrics 
FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');

CREATE TABLE IF NOT EXISTS monitoring.supabase_metrics_y2024m06 
PARTITION OF monitoring.supabase_metrics 
FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');

-- =====================================================
-- TABLA PARA MÉTRICAS DE EDGE FUNCTIONS
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.edge_function_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Información de la función
    function_name TEXT NOT NULL,
    function_version TEXT,
    
    -- Métricas de ejecución
    invocations_count BIGINT DEFAULT 0,
    errors_count BIGINT DEFAULT 0,
    timeouts_count BIGINT DEFAULT 0,
    cold_starts_count BIGINT DEFAULT 0,
    
    -- Métricas de rendimiento
    avg_duration_ms DECIMAL(10,2),
    min_duration_ms DECIMAL(10,2),
    max_duration_ms DECIMAL(10,2),
    p95_duration_ms DECIMAL(10,2),
    
    -- Métricas de memoria y recursos
    avg_memory_used_mb DECIMAL(10,2),
    max_memory_used_mb DECIMAL(10,2),
    memory_limit_mb DECIMAL(10,2),
    
    -- Códigos de respuesta HTTP
    http_2xx_count BIGINT DEFAULT 0,
    http_4xx_count BIGINT DEFAULT 0,
    http_5xx_count BIGINT DEFAULT 0,
    
    -- Origen de las llamadas
    requests_from_client BIGINT DEFAULT 0,
    requests_from_server BIGINT DEFAULT 0,
    requests_from_edge BIGINT DEFAULT 0,
    
    -- Información adicional
    deployment_id TEXT,
    last_deployment_at TIMESTAMPTZ,
    
    collection_time_ms INTEGER,
    collector_version TEXT DEFAULT '1.0.0'
);

-- =====================================================
-- TABLA PARA ALERTAS ESPECÍFICAS DE SUPABASE
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.supabase_alert_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Configuración del alerta
    alert_name TEXT NOT NULL UNIQUE,
    alert_description TEXT,
    metric_type TEXT NOT NULL, -- 'plan_limit', 'edge_function', 'api_performance', 'auth'
    
    -- Umbrales específicos de Supabase
    warning_threshold DECIMAL(15,2),
    critical_threshold DECIMAL(15,2),
    
    -- Configuración específica
    plan_types TEXT[] DEFAULT ARRAY['free', 'pro', 'team', 'enterprise'], -- Planes a los que aplica
    check_frequency_minutes INTEGER DEFAULT 15,
    
    -- Notificaciones
    enabled BOOLEAN DEFAULT TRUE,
    notification_channels TEXT[] DEFAULT ARRAY['email'],
    
    -- Configuración avanzada
    require_consecutive_breaches INTEGER DEFAULT 2,
    auto_resolve BOOLEAN DEFAULT TRUE,
    
    tags JSONB DEFAULT '{}'::jsonb
);

-- =====================================================
-- FUNCIONES PARA RECOLECCIÓN DE MÉTRICAS DE SUPABASE
-- =====================================================

-- Función para simular obtención de métricas de Supabase
-- NOTA: En producción, esto se conectaría a las APIs reales de Supabase
CREATE OR REPLACE FUNCTION monitoring.collect_supabase_metrics()
RETURNS UUID AS $$
DECLARE
    job_id UUID := gen_random_uuid();
    start_time TIMESTAMPTZ := NOW();
    execution_start_time TIMESTAMPTZ;
    
    -- Variables para métricas simuladas (en producción vendrían de APIs)
    auth_users_total BIGINT;
    db_size_mb BIGINT;
    estimated_api_calls BIGINT;
    current_connections INTEGER;
BEGIN
    execution_start_time := clock_timestamp();
    
    -- Registrar inicio del trabajo
    INSERT INTO monitoring.collection_jobs (
        id, started_at, job_type, status
    ) VALUES (
        job_id, start_time, 'supabase_metrics', 'running'
    );

    -- Obtener datos reales de la base de datos para estimaciones
    SELECT 
        COALESCE((SELECT count(*) FROM auth.users), 0),
        COALESCE((SELECT pg_database_size(current_database()) / 1024 / 1024), 0),
        COALESCE((SELECT count(*) FROM pg_stat_activity), 0)
    INTO auth_users_total, db_size_mb, current_connections;
    
    -- Estimar API calls basándose en conexiones (simulación)
    estimated_api_calls := current_connections * 100;
    
    -- Insertar métricas de Supabase (con valores estimados/simulados)
    INSERT INTO monitoring.supabase_metrics (
        timestamp,
        plan_name,
        plan_type,
        api_requests_limit,
        api_requests_used,
        api_requests_usage_percent,
        storage_limit_gb,
        storage_used_gb,
        storage_usage_percent,
        bandwidth_limit_gb,
        bandwidth_used_gb,
        bandwidth_usage_percent,
        edge_function_invocations,
        edge_function_errors,
        edge_function_error_rate,
        edge_function_avg_duration_ms,
        auth_users_count,
        auth_daily_active_users,
        auth_monthly_active_users,
        api_avg_response_time_ms,
        api_success_rate,
        api_rate_limit_hits,
        realtime_connections_count,
        realtime_messages_sent,
        storage_objects_count,
        storage_buckets_count,
        region,
        availability_status,
        collection_time_ms,
        data_source
    ) VALUES (
        NOW(),
        'Pro Plan (Simulado)', -- En producción: obtener de API
        'pro',
        500000, -- Límite simulado de API calls
        estimated_api_calls,
        CASE WHEN estimated_api_calls > 0 THEN 
            LEAST(round(estimated_api_calls::decimal / 500000 * 100, 2), 100)
            ELSE 0 END,
        8.0, -- 8GB límite simulado
        ROUND(db_size_mb::decimal / 1024, 2), -- Convertir MB a GB
        CASE WHEN db_size_mb > 0 THEN 
            LEAST(round(db_size_mb::decimal / 1024 / 8 * 100, 2), 100)
            ELSE 0 END,
        250.0, -- 250GB bandwidth simulado
        ROUND(RANDOM() * 10 + 5, 2), -- Bandwidth simulado
        ROUND((RANDOM() * 10 + 5) / 250 * 100, 2),
        FLOOR(RANDOM() * 1000)::BIGINT, -- Edge functions simuladas
        FLOOR(RANDOM() * 10)::BIGINT,
        ROUND(RANDOM() * 5, 2),
        ROUND(RANDOM() * 500 + 100, 2),
        auth_users_total,
        FLOOR(auth_users_total * 0.3)::BIGINT, -- 30% DAU estimado
        auth_users_total, -- MAU = total users for simulation
        ROUND(RANDOM() * 100 + 50, 2), -- API response time simulado
        ROUND(95 + RANDOM() * 4, 2), -- Success rate 95-99%
        FLOOR(RANDOM() * 5)::BIGINT,
        current_connections,
        FLOOR(RANDOM() * 10000)::BIGINT,
        FLOOR(RANDOM() * 1000)::BIGINT,
        FLOOR(RANDOM() * 10 + 1)::INTEGER,
        'us-east-1', -- Región simulada
        'available',
        EXTRACT(milliseconds FROM (clock_timestamp() - execution_start_time))::INTEGER,
        'estimated' -- Indicar que son valores estimados
    );
    
    -- Actualizar registro del trabajo como completado
    UPDATE monitoring.collection_jobs SET
        completed_at = NOW(),
        status = 'completed',
        metrics_collected = 1,
        execution_time_ms = EXTRACT(milliseconds FROM (NOW() - start_time))::INTEGER
    WHERE id = job_id;
    
    RETURN job_id;
    
EXCEPTION WHEN OTHERS THEN
    -- Registrar error en el trabajo
    UPDATE monitoring.collection_jobs SET
        completed_at = NOW(),
        status = 'failed',
        errors_count = 1,
        execution_time_ms = EXTRACT(milliseconds FROM (NOW() - start_time))::INTEGER,
        error_message = SQLERRM,
        error_details = jsonb_build_object(
            'error_state', SQLSTATE,
            'error_message', SQLERRM,
            'error_context', 'collect_supabase_metrics'
        )
    WHERE id = job_id;
    
    RAISE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA VERIFICAR LÍMITES DE SUPABASE
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.check_supabase_limits()
RETURNS INTEGER AS $$
DECLARE
    latest_metrics RECORD;
    config_rec RECORD;
    alerts_generated INTEGER := 0;
    current_value DECIMAL(15,2);
    should_alert BOOLEAN := FALSE;
    alert_level TEXT;
BEGIN
    -- Obtener las métricas más recientes de Supabase
    SELECT * INTO latest_metrics 
    FROM monitoring.supabase_metrics 
    ORDER BY timestamp DESC 
    LIMIT 1;
    
    IF latest_metrics IS NULL THEN
        RETURN 0;
    END IF;
    
    -- Verificar cada configuración de alerta de Supabase
    FOR config_rec IN 
        SELECT * FROM monitoring.supabase_alert_configs 
        WHERE enabled = TRUE
        AND latest_metrics.plan_type = ANY(plan_types)
    LOOP
        should_alert := FALSE;
        alert_level := '';
        current_value := NULL;
        
        -- Obtener el valor actual según el tipo de métrica
        CASE config_rec.metric_type
            WHEN 'plan_limit' THEN
                CASE config_rec.alert_name
                    WHEN 'api_requests_limit' THEN current_value := latest_metrics.api_requests_usage_percent;
                    WHEN 'storage_limit' THEN current_value := latest_metrics.storage_usage_percent;
                    WHEN 'bandwidth_limit' THEN current_value := latest_metrics.bandwidth_usage_percent;
                    ELSE CONTINUE;
                END CASE;
            WHEN 'edge_function' THEN
                CASE config_rec.alert_name
                    WHEN 'edge_function_error_rate' THEN current_value := latest_metrics.edge_function_error_rate;
                    WHEN 'edge_function_avg_duration' THEN current_value := latest_metrics.edge_function_avg_duration_ms;
                    ELSE CONTINUE;
                END CASE;
            WHEN 'api_performance' THEN
                CASE config_rec.alert_name
                    WHEN 'api_response_time' THEN current_value := latest_metrics.api_avg_response_time_ms;
                    WHEN 'api_success_rate' THEN current_value := latest_metrics.api_success_rate;
                    ELSE CONTINUE;
                END CASE;
            ELSE 
                CONTINUE;
        END CASE;
        
        -- Saltar si no hay valor
        IF current_value IS NULL THEN
            CONTINUE;
        END IF;
        
        -- Determinar si se debe generar alerta
        IF config_rec.alert_name IN ('api_success_rate') THEN
            -- Para success rate, alerta cuando es MENOR que el umbral
            IF current_value <= config_rec.critical_threshold THEN
                should_alert := TRUE;
                alert_level := 'critical';
            ELSIF current_value <= config_rec.warning_threshold THEN
                should_alert := TRUE;
                alert_level := 'warning';
            END IF;
        ELSE
            -- Para otras métricas, alerta cuando es MAYOR que el umbral
            IF current_value >= config_rec.critical_threshold THEN
                should_alert := TRUE;
                alert_level := 'critical';
            ELSIF current_value >= config_rec.warning_threshold THEN
                should_alert := TRUE;
                alert_level := 'warning';
            END IF;
        END IF;
        
        -- Generar alerta si es necesario
        IF should_alert THEN
            -- Verificar si ya existe una alerta activa para esta métrica
            IF NOT EXISTS (
                SELECT 1 FROM monitoring.alerts 
                WHERE metric_name = config_rec.alert_name 
                AND status = 'active'
                AND timestamp > NOW() - INTERVAL '1 hour'
            ) THEN
                INSERT INTO monitoring.alerts (
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
                    created_by,
                    tags
                ) VALUES (
                    NOW(),
                    'supabase_limit_breach',
                    alert_level,
                    config_rec.alert_name,
                    current_value,
                    CASE WHEN alert_level = 'critical' THEN config_rec.critical_threshold 
                         ELSE config_rec.warning_threshold END,
                    format('Supabase %s: %s', alert_level, config_rec.alert_name),
                    format('La métrica %s ha alcanzado %s%%, superando el umbral %s de %s%%',
                           config_rec.alert_description, 
                           current_value,
                           alert_level,
                           CASE WHEN alert_level = 'critical' THEN config_rec.critical_threshold 
                                ELSE config_rec.warning_threshold END),
                    'active',
                    config_rec.notification_channels,
                    'supabase_monitor',
                    jsonb_build_object(
                        'plan_type', latest_metrics.plan_type,
                        'metric_type', config_rec.metric_type,
                        'region', latest_metrics.region
                    )
                );
                
                alerts_generated := alerts_generated + 1;
            END IF;
        END IF;
    END LOOP;
    
    RETURN alerts_generated;
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error en check_supabase_limits: %', SQLERRM;
    RETURN 0;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA OBTENER ESTADO DE SUPABASE
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.get_supabase_status()
RETURNS JSONB AS $$
DECLARE
    latest_metrics RECORD;
    active_alerts INTEGER;
    critical_alerts INTEGER;
    result JSONB;
BEGIN
    -- Obtener métricas más recientes de Supabase
    SELECT * INTO latest_metrics 
    FROM monitoring.supabase_metrics 
    ORDER BY timestamp DESC 
    LIMIT 1;
    
    -- Contar alertas activas relacionadas con Supabase
    SELECT 
        COUNT(*) FILTER (WHERE severity = 'critical'),
        COUNT(*)
    INTO critical_alerts, active_alerts
    FROM monitoring.alerts 
    WHERE status = 'active'
    AND (metric_name LIKE '%supabase%' OR 
         metric_name IN ('api_requests_limit', 'storage_limit', 'bandwidth_limit', 
                        'edge_function_error_rate', 'api_response_time'));
    
    -- Construir resultado
    result := jsonb_build_object(
        'timestamp', COALESCE(latest_metrics.timestamp, NOW()),
        'plan_info', CASE 
            WHEN latest_metrics IS NOT NULL THEN
                jsonb_build_object(
                    'plan_name', latest_metrics.plan_name,
                    'plan_type', latest_metrics.plan_type,
                    'region', latest_metrics.region
                )
            ELSE jsonb_build_object('error', 'No plan info available')
        END,
        'usage_status', CASE 
            WHEN latest_metrics IS NOT NULL THEN
                jsonb_build_object(
                    'api_requests', jsonb_build_object(
                        'used', latest_metrics.api_requests_used,
                        'limit', latest_metrics.api_requests_limit,
                        'usage_percent', latest_metrics.api_requests_usage_percent
                    ),
                    'storage', jsonb_build_object(
                        'used_gb', latest_metrics.storage_used_gb,
                        'limit_gb', latest_metrics.storage_limit_gb,
                        'usage_percent', latest_metrics.storage_usage_percent
                    ),
                    'bandwidth', jsonb_build_object(
                        'used_gb', latest_metrics.bandwidth_used_gb,
                        'limit_gb', latest_metrics.bandwidth_limit_gb,
                        'usage_percent', latest_metrics.bandwidth_usage_percent
                    )
                )
            ELSE jsonb_build_object('error', 'No usage data available')
        END,
        'services_status', CASE 
            WHEN latest_metrics IS NOT NULL THEN
                jsonb_build_object(
                    'edge_functions', jsonb_build_object(
                        'invocations', latest_metrics.edge_function_invocations,
                        'error_rate', latest_metrics.edge_function_error_rate,
                        'avg_duration_ms', latest_metrics.edge_function_avg_duration_ms
                    ),
                    'auth', jsonb_build_object(
                        'total_users', latest_metrics.auth_users_count,
                        'daily_active_users', latest_metrics.auth_daily_active_users
                    ),
                    'api', jsonb_build_object(
                        'avg_response_time_ms', latest_metrics.api_avg_response_time_ms,
                        'success_rate', latest_metrics.api_success_rate
                    )
                )
            ELSE jsonb_build_object('error', 'No services data available')
        END,
        'alerts', jsonb_build_object(
            'total_active', active_alerts,
            'critical', critical_alerts
        ),
        'overall_health', CASE 
            WHEN critical_alerts > 0 THEN 'critical'
            WHEN active_alerts > 0 THEN 'warning'
            WHEN latest_metrics IS NULL THEN 'unknown'
            WHEN latest_metrics.api_requests_usage_percent > 90 OR 
                 latest_metrics.storage_usage_percent > 90 OR 
                 latest_metrics.bandwidth_usage_percent > 90 THEN 'warning'
            ELSE 'healthy'
        END
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- CONFIGURACIONES INICIALES PARA SUPABASE
-- =====================================================

-- Insertar configuraciones de alertas específicas de Supabase
INSERT INTO monitoring.supabase_alert_configs (
    alert_name, alert_description, metric_type,
    warning_threshold, critical_threshold,
    plan_types, check_frequency_minutes, notification_channels
) VALUES 
    ('api_requests_limit', 'Límite de requests API', 'plan_limit', 
     80.0, 95.0, ARRAY['free', 'pro', 'team'], 15, ARRAY['email', 'slack']),
    ('storage_limit', 'Límite de almacenamiento', 'plan_limit', 
     85.0, 95.0, ARRAY['free', 'pro', 'team'], 60, ARRAY['email']),
    ('bandwidth_limit', 'Límite de ancho de banda', 'plan_limit', 
     85.0, 95.0, ARRAY['free', 'pro', 'team'], 60, ARRAY['email']),
    ('edge_function_error_rate', 'Tasa de error en Edge Functions', 'edge_function', 
     5.0, 10.0, ARRAY['pro', 'team', 'enterprise'], 10, ARRAY['email']),
    ('api_response_time', 'Tiempo de respuesta API', 'api_performance', 
     200.0, 500.0, ARRAY['free', 'pro', 'team', 'enterprise'], 5, ARRAY['email']),
    ('api_success_rate', 'Tasa de éxito API', 'api_performance', 
     95.0, 90.0, ARRAY['free', 'pro', 'team', 'enterprise'], 5, ARRAY['email'])
ON CONFLICT (alert_name) DO NOTHING;

-- =====================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- =====================================================

-- Índices para supabase_metrics
CREATE INDEX IF NOT EXISTS idx_supabase_metrics_timestamp ON monitoring.supabase_metrics (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_supabase_metrics_plan_type ON monitoring.supabase_metrics (plan_type);
CREATE INDEX IF NOT EXISTS idx_supabase_metrics_usage ON monitoring.supabase_metrics (api_requests_usage_percent, storage_usage_percent, bandwidth_usage_percent);

-- Índices para edge_function_metrics
CREATE INDEX IF NOT EXISTS idx_edge_function_metrics_timestamp ON monitoring.edge_function_metrics (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_edge_function_metrics_function_name ON monitoring.edge_function_metrics (function_name);
CREATE INDEX IF NOT EXISTS idx_edge_function_metrics_errors ON monitoring.edge_function_metrics (errors_count) WHERE errors_count > 0;

-- Índices para supabase_alert_configs
CREATE INDEX IF NOT EXISTS idx_supabase_alert_configs_enabled ON monitoring.supabase_alert_configs (enabled) WHERE enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_supabase_alert_configs_metric_type ON monitoring.supabase_alert_configs (metric_type);

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON TABLE monitoring.supabase_metrics IS 'Métricas específicas de Supabase incluyendo límites del plan, uso de servicios y rendimiento';
COMMENT ON TABLE monitoring.edge_function_metrics IS 'Métricas detalladas de Edge Functions por función individual';
COMMENT ON TABLE monitoring.supabase_alert_configs IS 'Configuración de alertas específicas para servicios y límites de Supabase';
COMMENT ON FUNCTION monitoring.collect_supabase_metrics() IS 'Recolecta métricas específicas de Supabase (actualmente simuladas, en producción usaría APIs reales)';
COMMENT ON FUNCTION monitoring.check_supabase_limits() IS 'Verifica límites de plan de Supabase y genera alertas específicas';
COMMENT ON FUNCTION monitoring.get_supabase_status() IS 'Obtiene estado completo de servicios y uso de Supabase en formato JSON';

-- Verificación final
DO $$
BEGIN
    RAISE NOTICE '=== MONITOREO ESPECÍFICO DE SUPABASE IMPLEMENTADO ===';
    RAISE NOTICE 'Tablas creadas: supabase_metrics, edge_function_metrics, supabase_alert_configs';
    RAISE NOTICE 'Funciones: collect_supabase_metrics, check_supabase_limits, get_supabase_status';
    RAISE NOTICE 'Configuraciones de alerta: 6 alertas específicas de Supabase';
    RAISE NOTICE '';
    RAISE NOTICE 'NOTA IMPORTANTE: Las métricas actualmente son simuladas/estimadas.';
    RAISE NOTICE 'En producción, integrar con:';
    RAISE NOTICE '  - Supabase Management API para métricas reales';
    RAISE NOTICE '  - Supabase Analytics para datos de uso';
    RAISE NOTICE '  - APIs de Edge Functions para métricas detalladas';
    RAISE NOTICE '';
    RAISE NOTICE 'Para probar: SELECT monitoring.get_supabase_status();';
END $$;
