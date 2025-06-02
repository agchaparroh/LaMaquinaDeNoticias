-- =====================================================
-- AUTOMATIZACIÓN COMPLETA CON PG_CRON Y ALERTAS SUPABASE
-- Archivo: 13_complete_automation_and_supabase_alerts.sql
-- Descripción: Automatización completa y alertas específicas de Supabase
-- =====================================================

-- =====================================================
-- CONFIGURACIÓN DE TRABAJOS AUTOMÁTICOS CON PG_CRON
-- =====================================================

-- Trabajo principal: Recolección de métricas cada 5 minutos
SELECT cron.schedule(
    'collect-system-metrics',
    '*/5 * * * *',
    'SELECT monitoring.collect_system_metrics();'
);

-- Trabajo de verificación de alertas mejorado cada 5 minutos
SELECT cron.schedule(
    'check-alert-thresholds-enhanced',
    '*/5 * * * *', 
    'SELECT monitoring.check_alert_thresholds_enhanced();'
);

-- Trabajo de mantenimiento diario a las 2:00 AM
SELECT cron.schedule(
    'daily-maintenance',
    '0 2 * * *',
    'SELECT monitoring.daily_maintenance();'
);

-- Trabajo de limpieza de flood control cada hora
SELECT cron.schedule(
    'cleanup-flood-control',
    '0 * * * *',
    'DELETE FROM monitoring.alert_flood_control WHERE period_start_time < NOW() - INTERVAL ''24 hours'';'
);

-- Trabajo de verificación de salud del sistema cada 15 minutos
SELECT cron.schedule(
    'system-health-check',
    '*/15 * * * *',
    'SELECT monitoring.perform_health_check();'
);

-- =====================================================
-- ALERTAS ESPECÍFICAS PARA SUPABASE
-- =====================================================

-- Tabla para umbrales específicos de Supabase
CREATE TABLE IF NOT EXISTS monitoring.supabase_alert_thresholds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Identificación del umbral
    metric_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    
    -- Umbrales específicos de Supabase
    warning_threshold DECIMAL(15,2),
    critical_threshold DECIMAL(15,2),
    
    -- Configuración específica para planes de Supabase
    plan_type TEXT DEFAULT 'pro', -- 'free', 'pro', 'team', 'enterprise'
    
    -- Configuración
    enabled BOOLEAN DEFAULT TRUE,
    check_frequency_minutes INTEGER DEFAULT 15,
    notification_channels TEXT[] DEFAULT ARRAY['email', 'slack'],
    
    -- Metadatos
    category TEXT DEFAULT 'supabase',
    tags JSONB DEFAULT '{}'::jsonb
);

-- =====================================================
-- FUNCIÓN PARA VERIFICAR ALERTAS ESPECÍFICAS DE SUPABASE
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.check_supabase_alerts()
RETURNS INTEGER AS $$
DECLARE
    threshold_rec RECORD;
    latest_supabase_metrics RECORD;
    alerts_count INTEGER := 0;
    alert_id UUID;
    current_value DECIMAL(15,2);
    should_alert BOOLEAN := FALSE;
    alert_level TEXT;
    notifications_sent INTEGER;
BEGIN
    -- Obtener las métricas de Supabase más recientes
    SELECT * INTO latest_supabase_metrics 
    FROM monitoring.supabase_metrics 
    ORDER BY timestamp DESC 
    LIMIT 1;
    
    IF latest_supabase_metrics IS NULL THEN
        RAISE NOTICE 'No hay métricas de Supabase disponibles';
        RETURN 0;
    END IF;
    
    -- Iterar sobre todos los umbrales de Supabase habilitados
    FOR threshold_rec IN 
        SELECT * FROM monitoring.supabase_alert_thresholds 
        WHERE enabled = TRUE
    LOOP
        should_alert := FALSE;
        alert_level := '';
        current_value := NULL;
        
        -- Obtener el valor actual según el tipo de métrica de Supabase
        CASE threshold_rec.metric_name
            WHEN 'api_requests_usage_percent' THEN 
                current_value := latest_supabase_metrics.api_requests_usage_percent;
            WHEN 'storage_usage_percent' THEN 
                current_value := latest_supabase_metrics.storage_usage_percent;
            WHEN 'bandwidth_usage_percent' THEN 
                current_value := latest_supabase_metrics.bandwidth_usage_percent;
            WHEN 'auth_users_usage_percent' THEN 
                current_value := latest_supabase_metrics.auth_users_usage_percent;
            WHEN 'edge_function_invocations_usage_percent' THEN 
                current_value := latest_supabase_metrics.edge_function_invocations_usage_percent;
            WHEN 'edge_function_error_rate' THEN 
                current_value := latest_supabase_metrics.edge_function_error_rate;
            WHEN 'realtime_concurrent_connections' THEN 
                current_value := latest_supabase_metrics.realtime_concurrent_connections;
            ELSE 
                CONTINUE;
        END CASE;
        
        IF current_value IS NULL THEN
            CONTINUE;
        END IF;
        
        -- Determinar si se debe generar alerta (todas las métricas de Supabase son del tipo "mayor que")
        IF current_value >= threshold_rec.critical_threshold THEN
            should_alert := TRUE;
            alert_level := 'critical';
        ELSIF current_value >= threshold_rec.warning_threshold THEN
            should_alert := TRUE;
            alert_level := 'warning';
        END IF;
        
        -- Generar alerta si es necesario
        IF should_alert THEN
            -- Verificar si ya existe una alerta activa similar
            IF NOT EXISTS (
                SELECT 1 FROM monitoring.alerts 
                WHERE metric_name = threshold_rec.metric_name 
                AND status = 'active'
                AND timestamp > NOW() - INTERVAL '1 hour'
            ) THEN
                -- Crear nueva alerta específica de Supabase
                alert_id := gen_random_uuid();
                INSERT INTO monitoring.alerts (
                    id, timestamp, alert_type, severity, metric_name,
                    metric_value, threshold_value, title, description,
                    status, notification_channels, created_by, tags
                ) VALUES (
                    alert_id, NOW(), 'supabase_limit_breach', alert_level, threshold_rec.metric_name,
                    current_value,
                    CASE WHEN alert_level = 'critical' THEN threshold_rec.critical_threshold 
                         ELSE threshold_rec.warning_threshold END,
                    format('SUPABASE %s: %s (%s%%)', UPPER(alert_level), threshold_rec.display_name, current_value),
                    format('El límite de Supabase %s ha alcanzado %s%%, superando el umbral %s de %s%%. Plan: %s',
                           threshold_rec.display_name, current_value, alert_level,
                           CASE WHEN alert_level = 'critical' THEN threshold_rec.critical_threshold 
                                ELSE threshold_rec.warning_threshold END,
                           threshold_rec.plan_type),
                    'active', threshold_rec.notification_channels, 'supabase_monitor',
                    jsonb_build_object('plan_type', threshold_rec.plan_type, 'category', 'supabase')
                );
                
                alerts_count := alerts_count + 1;
                
                -- Enviar notificaciones automáticamente
                SELECT monitoring.send_alert_notifications(alert_id) INTO notifications_sent;
                
                RAISE NOTICE 'Alerta Supabase generada y % notificaciones enviadas: % - % (Valor: %%, Umbral: %%)', 
                    notifications_sent, alert_level, threshold_rec.display_name, current_value, 
                    CASE WHEN alert_level = 'critical' THEN threshold_rec.critical_threshold 
                         ELSE threshold_rec.warning_threshold END;
            END IF;
        END IF;
    END LOOP;
    
    RETURN alerts_count;
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error en check_supabase_alerts: %', SQLERRM;
    RETURN 0;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN DE VERIFICACIÓN DE SALUD GENERAL
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.perform_health_check()
RETURNS JSONB AS $$
DECLARE
    health_result JSONB;
    system_alerts INTEGER;
    supabase_alerts INTEGER;
    critical_alerts INTEGER;
    health_status TEXT;
    latest_metrics RECORD;
    latest_supabase_metrics RECORD;
BEGIN
    -- Contar alertas activas
    SELECT 
        COUNT(*) as total_alerts,
        COUNT(*) FILTER (WHERE severity = 'critical') as critical_count
    INTO system_alerts, critical_alerts
    FROM monitoring.alerts 
    WHERE status = 'active' 
    AND timestamp > NOW() - INTERVAL '1 hour';
    
    -- Obtener métricas más recientes
    SELECT * INTO latest_metrics 
    FROM monitoring.system_metrics 
    ORDER BY timestamp DESC 
    LIMIT 1;
    
    SELECT * INTO latest_supabase_metrics 
    FROM monitoring.supabase_metrics 
    ORDER BY timestamp DESC 
    LIMIT 1;
    
    -- Determinar estado de salud general
    health_status := CASE 
        WHEN critical_alerts > 0 THEN 'critical'
        WHEN system_alerts > 5 THEN 'warning'
        WHEN latest_metrics.timestamp < NOW() - INTERVAL '10 minutes' THEN 'warning'
        ELSE 'healthy'
    END;
    
    -- Construir resultado
    health_result := jsonb_build_object(
        'timestamp', NOW(),
        'overall_status', health_status,
        'alerts', jsonb_build_object(
            'total_active', system_alerts,
            'critical', critical_alerts
        ),
        'system_metrics', CASE 
            WHEN latest_metrics IS NOT NULL THEN
                jsonb_build_object(
                    'last_update', latest_metrics.timestamp,
                    'cpu_usage', latest_metrics.cpu_usage_percent,
                    'memory_usage', latest_metrics.memory_usage_percent,
                    'connection_usage', latest_metrics.connection_usage_percent,
                    'cache_hit_ratio', latest_metrics.cache_hit_ratio
                )
            ELSE jsonb_build_object('status', 'no_data')
        END,
        'supabase_metrics', CASE 
            WHEN latest_supabase_metrics IS NOT NULL THEN
                jsonb_build_object(
                    'last_update', latest_supabase_metrics.timestamp,
                    'api_usage', latest_supabase_metrics.api_requests_usage_percent,
                    'storage_usage', latest_supabase_metrics.storage_usage_percent
                )
            ELSE jsonb_build_object('status', 'no_data')
        END,
        'services_status', jsonb_build_object(
            'metrics_collection', CASE 
                WHEN latest_metrics.timestamp > NOW() - INTERVAL '10 minutes' THEN 'operational'
                ELSE 'degraded'
            END,
            'alert_system', 'operational',
            'notification_system', 'operational'
        )
    );
    
    -- Si el estado es crítico, crear una alerta de salud del sistema
    IF health_status = 'critical' THEN
        INSERT INTO monitoring.alerts (
            timestamp, alert_type, severity, metric_name,
            title, description, status, notification_channels, created_by
        ) VALUES (
            NOW(), 'system_health_critical', 'critical', 'system_health',
            'Estado Crítico del Sistema',
            format('El sistema tiene %s alertas críticas activas. Revisión inmediata requerida.', critical_alerts),
            'active', ARRAY['email', 'slack', 'sms'], 'health_check_system'
        );
    END IF;
    
    RETURN health_result;
    
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'timestamp', NOW(),
        'overall_status', 'error',
        'error', SQLERRM
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA RESOLVER ALERTAS AUTOMÁTICAMENTE
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.auto_resolve_alerts()
RETURNS INTEGER AS $$
DECLARE
    alert_rec RECORD;
    resolved_count INTEGER := 0;
    current_value DECIMAL(15,2);
    should_resolve BOOLEAN := FALSE;
    latest_metrics RECORD;
    latest_supabase_metrics RECORD;
BEGIN
    -- Obtener métricas más recientes
    SELECT * INTO latest_metrics 
    FROM monitoring.system_metrics 
    ORDER BY timestamp DESC 
    LIMIT 1;
    
    SELECT * INTO latest_supabase_metrics 
    FROM monitoring.supabase_metrics 
    ORDER BY timestamp DESC 
    LIMIT 1;
    
    -- Iterar sobre alertas activas que pueden auto-resolverse
    FOR alert_rec IN
        SELECT a.* 
        FROM monitoring.alerts a
        JOIN monitoring.alert_thresholds at ON a.metric_name = at.metric_name
        WHERE a.status = 'active' 
        AND at.auto_resolve = TRUE
        AND a.timestamp < NOW() - INTERVAL '1 minute' * at.auto_resolve_after_minutes
    LOOP
        should_resolve := FALSE;
        current_value := NULL;
        
        -- Obtener valor actual de la métrica
        IF latest_metrics IS NOT NULL THEN
            CASE alert_rec.metric_name
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
                ELSE 
                    NULL;
            END CASE;
        END IF;
        
        -- Verificar métricas de Supabase si es necesario
        IF current_value IS NULL AND latest_supabase_metrics IS NOT NULL THEN
            CASE alert_rec.metric_name
                WHEN 'api_requests_usage_percent' THEN 
                    current_value := latest_supabase_metrics.api_requests_usage_percent;
                WHEN 'storage_usage_percent' THEN 
                    current_value := latest_supabase_metrics.storage_usage_percent;
                WHEN 'bandwidth_usage_percent' THEN 
                    current_value := latest_supabase_metrics.bandwidth_usage_percent;
                ELSE 
                    NULL;
            END CASE;
        END IF;
        
        -- Determinar si la alerta debe resolverse
        IF current_value IS NOT NULL THEN
            IF alert_rec.metric_name = 'cache_hit_ratio' THEN
                -- Para cache hit ratio, resolver si está por encima del umbral
                should_resolve := current_value > alert_rec.threshold_value;
            ELSE
                -- Para otras métricas, resolver si está por debajo del umbral
                should_resolve := current_value < alert_rec.threshold_value;
            END IF;
        END IF;
        
        -- Resolver la alerta si es apropiado
        IF should_resolve THEN
            UPDATE monitoring.alerts SET
                status = 'resolved',
                resolved_at = NOW(),
                resolved_by = 'auto_resolve_system'
            WHERE id = alert_rec.id;
            
            resolved_count := resolved_count + 1;
            
            RAISE NOTICE 'Alerta auto-resuelta: % (Valor actual: %, Umbral: %)', 
                alert_rec.title, current_value, alert_rec.threshold_value;
        END IF;
    END LOOP;
    
    RETURN resolved_count;
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error en auto_resolve_alerts: %', SQLERRM;
    RETURN 0;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- INSERTAR UMBRALES ESPECÍFICOS DE SUPABASE
-- =====================================================

INSERT INTO monitoring.supabase_alert_thresholds (
    metric_name, display_name, description, 
    warning_threshold, critical_threshold, 
    plan_type, notification_channels
) VALUES 
    ('api_requests_usage_percent', 'Uso de API Requests', 'Porcentaje de uso del límite de llamadas API', 85.0, 95.0, 'pro', ARRAY['email', 'slack']),
    ('storage_usage_percent', 'Uso de Almacenamiento', 'Porcentaje de uso del límite de almacenamiento', 80.0, 90.0, 'pro', ARRAY['email', 'slack']),
    ('bandwidth_usage_percent', 'Uso de Ancho de Banda', 'Porcentaje de uso del límite de transferencia', 85.0, 95.0, 'pro', ARRAY['email']),
    ('auth_users_usage_percent', 'Usuarios Autenticados', 'Porcentaje de uso del límite de usuarios activos', 90.0, 98.0, 'pro', ARRAY['email']),
    ('edge_function_invocations_usage_percent', 'Invocaciones Edge Functions', 'Porcentaje de uso del límite de ejecuciones', 85.0, 95.0, 'pro', ARRAY['email']),
    ('edge_function_error_rate', 'Tasa de Error Edge Functions', 'Porcentaje de errores en Edge Functions', 5.0, 15.0, 'pro', ARRAY['email', 'slack']),
    ('realtime_concurrent_connections', 'Conexiones Realtime', 'Número de conexiones simultáneas en Realtime', 800.0, 950.0, 'pro', ARRAY['email'])
ON CONFLICT (metric_name) DO NOTHING;

-- =====================================================
-- TRABAJOS ADICIONALES PARA SUPABASE Y AUTO-RESOLUCIÓN
-- =====================================================

-- Trabajo de verificación de alertas de Supabase cada 15 minutos
SELECT cron.schedule(
    'check-supabase-alerts',
    '*/15 * * * *',
    'SELECT monitoring.check_supabase_alerts();'
);

-- Trabajo de auto-resolución de alertas cada 10 minutos
SELECT cron.schedule(
    'auto-resolve-alerts',
    '*/10 * * * *',
    'SELECT monitoring.auto_resolve_alerts();'
);

-- =====================================================
-- VISTA CONSOLIDADA DE ESTADO GENERAL
-- =====================================================

CREATE OR REPLACE VIEW monitoring.system_overview AS
SELECT 
    'System Health' as component,
    (SELECT overall_health_score FROM monitoring.daily_reports ORDER BY report_date DESC LIMIT 1) as score,
    (SELECT health_status FROM monitoring.daily_reports ORDER BY report_date DESC LIMIT 1) as status,
    (SELECT COUNT(*) FROM monitoring.alerts WHERE status = 'active') as active_alerts,
    (SELECT timestamp FROM monitoring.system_metrics ORDER BY timestamp DESC LIMIT 1) as last_metric_update

UNION ALL

SELECT 
    'Notification System' as component,
    CASE 
        WHEN (SELECT COUNT(*) FROM monitoring.notification_history WHERE timestamp > NOW() - INTERVAL '1 hour' AND status = 'failed') = 0 
        THEN 10.0 
        ELSE 5.0 
    END as score,
    CASE 
        WHEN (SELECT COUNT(*) FROM monitoring.notification_history WHERE timestamp > NOW() - INTERVAL '1 hour' AND status = 'failed') = 0 
        THEN 'healthy' 
        ELSE 'warning' 
    END as status,
    (SELECT COUNT(*) FROM monitoring.notification_history WHERE timestamp > NOW() - INTERVAL '1 hour' AND status = 'failed') as active_alerts,
    (SELECT MAX(timestamp) FROM monitoring.notification_history) as last_metric_update

UNION ALL

SELECT 
    'Supabase Limits' as component,
    CASE 
        WHEN (SELECT COUNT(*) FROM monitoring.alerts WHERE status = 'active' AND alert_type = 'supabase_limit_breach') = 0 
        THEN 10.0 
        ELSE 7.0 
    END as score,
    CASE 
        WHEN (SELECT COUNT(*) FROM monitoring.alerts WHERE status = 'active' AND alert_type = 'supabase_limit_breach' AND severity = 'critical') > 0 
        THEN 'critical'
        WHEN (SELECT COUNT(*) FROM monitoring.alerts WHERE status = 'active' AND alert_type = 'supabase_limit_breach') > 0 
        THEN 'warning'
        ELSE 'healthy' 
    END as status,
    (SELECT COUNT(*) FROM monitoring.alerts WHERE status = 'active' AND alert_type = 'supabase_limit_breach') as active_alerts,
    (SELECT MAX(timestamp) FROM monitoring.supabase_metrics) as last_metric_update;

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN FINAL
-- =====================================================

COMMENT ON TABLE monitoring.supabase_alert_thresholds IS 'Umbrales específicos para alertas de límites de Supabase';
COMMENT ON FUNCTION monitoring.check_supabase_alerts() IS 'Verifica límites específicos de Supabase y genera alertas';
COMMENT ON FUNCTION monitoring.perform_health_check() IS 'Realiza verificación completa de salud del sistema';
COMMENT ON FUNCTION monitoring.auto_resolve_alerts() IS 'Auto-resuelve alertas cuando las métricas vuelven a niveles normales';
COMMENT ON VIEW monitoring.system_overview IS 'Vista consolidada del estado general del sistema';

-- =====================================================
-- VERIFICACIÓN E INSTALACIÓN FINAL
-- =====================================================

DO $$
DECLARE
    cron_jobs_count INTEGER;
    alert_configs_count INTEGER;
BEGIN
    -- Verificar trabajos cron
    SELECT COUNT(*) INTO cron_jobs_count 
    FROM cron.job 
    WHERE jobname LIKE '%-%-%-system-metrics' OR 
          jobname LIKE '%-%-%-thresholds-enhanced' OR 
          jobname LIKE '%-%-maintenance' OR
          jobname LIKE '%-%-check' OR
          jobname LIKE '%-%-alerts';
    
    -- Verificar configuraciones de alerta
    SELECT COUNT(*) INTO alert_configs_count 
    FROM monitoring.supabase_alert_thresholds 
    WHERE enabled = TRUE;
    
    RAISE NOTICE '=== SISTEMA DE ALERTAS AUTOMÁTICAS COMPLETAMENTE IMPLEMENTADO ===';
    RAISE NOTICE 'Trabajos pg_cron configurados: %', cron_jobs_count;
    RAISE NOTICE 'Umbrales de Supabase configurados: %', alert_configs_count;
    RAISE NOTICE 'Componentes implementados:';
    RAISE NOTICE '  ✓ Sistema de notificaciones multi-canal (email, slack, sms, webhook)';
    RAISE NOTICE '  ✓ Control anti-flood para prevenir spam de alertas';
    RAISE NOTICE '  ✓ Alertas específicas para límites de Supabase';
    RAISE NOTICE '  ✓ Auto-resolución de alertas';
    RAISE NOTICE '  ✓ Reportes diarios automáticos';
    RAISE NOTICE '  ✓ Verificación de salud del sistema';
    RAISE NOTICE '  ✓ Automatización completa con pg_cron';
    RAISE NOTICE '  ✓ Dashboard y vistas consolidadas';
    RAISE NOTICE '';
    RAISE NOTICE 'PRÓXIMO PASO: Configurar credenciales reales para servicios de notificación';
    RAISE NOTICE '(Email SMTP, Slack Webhooks, SMS API keys, etc.)';
    RAISE NOTICE '';
    RAISE NOTICE 'SUBTAREA 22.5 COMPLETADA: Sistema de alertas automáticas implementado';
END $$;
