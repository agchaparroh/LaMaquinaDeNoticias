-- =====================================================
-- SISTEMA DE RESUMEN DIARIO Y MEJORAS AUTOMATIZACIÓN
-- Archivo: 12_daily_reporting_and_enhanced_automation.sql
-- Descripción: Resumen diario automático y mejoras al sistema de alertas
-- =====================================================

-- =====================================================
-- TABLA PARA REPORTES DIARIOS
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.daily_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_date DATE NOT NULL UNIQUE,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Métricas del día
    metrics_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Resumen de alertas
    alerts_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Resumen de rendimiento
    performance_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Recomendaciones
    recommendations TEXT[],
    
    -- Estado general
    overall_health_score DECIMAL(3,1) CHECK (overall_health_score BETWEEN 0 AND 10),
    health_status TEXT CHECK (health_status IN ('healthy', 'warning', 'critical')),
    
    -- Metadatos
    report_version TEXT DEFAULT '1.0',
    generated_by TEXT DEFAULT 'system'
);

-- =====================================================
-- FUNCIÓN PARA GENERAR RESUMEN DIARIO
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.generate_daily_report(
    p_target_date DATE DEFAULT CURRENT_DATE - INTERVAL '1 day'
)
RETURNS UUID AS $$
DECLARE
    report_id UUID := gen_random_uuid();
    metrics_data JSONB;
    alerts_data JSONB;
    performance_data JSONB;
    recommendations TEXT[] := ARRAY[]::TEXT[];
    health_score DECIMAL(3,1) := 10.0;
    health_status TEXT := 'healthy';
    
    -- Variables para cálculos
    avg_cpu DECIMAL(5,2);
    max_cpu DECIMAL(5,2);
    avg_memory DECIMAL(5,2);
    max_memory DECIMAL(5,2);
    avg_connections DECIMAL(5,2);
    max_connections DECIMAL(5,2);
    avg_cache_hit DECIMAL(5,2);
    
    critical_alerts INTEGER;
    warning_alerts INTEGER;
    total_alerts INTEGER;
    
    notification_success_rate DECIMAL(5,2);
    total_notifications INTEGER;
    failed_notifications INTEGER;
BEGIN
    -- =====================================================
    -- RECOPILAR MÉTRICAS DEL DÍA
    -- =====================================================
    
    SELECT 
        AVG(cpu_usage_percent) as avg_cpu,
        MAX(cpu_usage_percent) as max_cpu,
        AVG(memory_usage_percent) as avg_memory,
        MAX(memory_usage_percent) as max_memory,
        AVG(connection_usage_percent) as avg_connections,
        MAX(connection_usage_percent) as max_connections,
        AVG(cache_hit_ratio) as avg_cache_hit
    INTO avg_cpu, max_cpu, avg_memory, max_memory, avg_connections, max_connections, avg_cache_hit
    FROM monitoring.system_metrics 
    WHERE timestamp::date = p_target_date;
    
    -- Construir resumen de métricas
    metrics_data := jsonb_build_object(
        'cpu', jsonb_build_object(
            'average', COALESCE(avg_cpu, 0),
            'maximum', COALESCE(max_cpu, 0),
            'status', CASE 
                WHEN COALESCE(max_cpu, 0) >= 90 THEN 'critical'
                WHEN COALESCE(max_cpu, 0) >= 75 THEN 'warning'
                ELSE 'healthy'
            END
        ),
        'memory', jsonb_build_object(
            'average', COALESCE(avg_memory, 0),
            'maximum', COALESCE(max_memory, 0),
            'status', CASE 
                WHEN COALESCE(max_memory, 0) >= 95 THEN 'critical'
                WHEN COALESCE(max_memory, 0) >= 80 THEN 'warning'
                ELSE 'healthy'
            END
        ),
        'connections', jsonb_build_object(
            'average', COALESCE(avg_connections, 0),
            'maximum', COALESCE(max_connections, 0),
            'status', CASE 
                WHEN COALESCE(max_connections, 0) >= 95 THEN 'critical'
                WHEN COALESCE(max_connections, 0) >= 80 THEN 'warning'
                ELSE 'healthy'
            END
        ),
        'cache_performance', jsonb_build_object(
            'average_hit_ratio', COALESCE(avg_cache_hit, 100),
            'status', CASE 
                WHEN COALESCE(avg_cache_hit, 100) < 80 THEN 'critical'
                WHEN COALESCE(avg_cache_hit, 100) < 90 THEN 'warning'
                ELSE 'healthy'
            END
        )
    );
    
    -- =====================================================
    -- RECOPILAR DATOS DE ALERTAS
    -- =====================================================
    
    SELECT 
        COUNT(*) FILTER (WHERE severity = 'critical') as critical_count,
        COUNT(*) FILTER (WHERE severity = 'warning') as warning_count,
        COUNT(*) as total_count
    INTO critical_alerts, warning_alerts, total_alerts
    FROM monitoring.alerts 
    WHERE timestamp::date = p_target_date;
    
    -- Construir resumen de alertas
    alerts_data := jsonb_build_object(
        'total', COALESCE(total_alerts, 0),
        'by_severity', jsonb_build_object(
            'critical', COALESCE(critical_alerts, 0),
            'warning', COALESCE(warning_alerts, 0)
        ),
        'top_metrics', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'metric', metric_name,
                    'count', count
                )
            )
            FROM (
                SELECT metric_name, COUNT(*) as count
                FROM monitoring.alerts 
                WHERE timestamp::date = p_target_date
                GROUP BY metric_name
                ORDER BY COUNT(*) DESC
                LIMIT 5
            ) top_metrics
        ),
        'status', CASE 
            WHEN COALESCE(critical_alerts, 0) > 5 THEN 'critical'
            WHEN COALESCE(total_alerts, 0) > 10 THEN 'warning'
            ELSE 'healthy'
        END
    );
    
    -- =====================================================
    -- RECOPILAR DATOS DE RENDIMIENTO
    -- =====================================================
    
    SELECT 
        COUNT(*) as total_notifications,
        COUNT(*) FILTER (WHERE status = 'failed') as failed_notifications
    INTO total_notifications, failed_notifications
    FROM monitoring.notification_history 
    WHERE timestamp::date = p_target_date;
    
    -- Calcular tasa de éxito de notificaciones
    notification_success_rate := CASE 
        WHEN total_notifications > 0 THEN 
            ROUND(100.0 * (total_notifications - COALESCE(failed_notifications, 0)) / total_notifications, 2)
        ELSE 100.0 
    END;
    
    performance_data := jsonb_build_object(
        'notifications', jsonb_build_object(
            'total_sent', COALESCE(total_notifications, 0),
            'failed', COALESCE(failed_notifications, 0),
            'success_rate', notification_success_rate,
            'status', CASE 
                WHEN notification_success_rate < 80 THEN 'critical'
                WHEN notification_success_rate < 95 THEN 'warning'
                ELSE 'healthy'
            END
        ),
        'collection_jobs', (
            SELECT jsonb_build_object(
                'total_jobs', COUNT(*),
                'failed_jobs', COUNT(*) FILTER (WHERE status = 'failed'),
                'avg_execution_time_ms', AVG(execution_time_ms),
                'status', CASE 
                    WHEN COUNT(*) FILTER (WHERE status = 'failed') > 0 THEN 'warning'
                    ELSE 'healthy'
                END
            )
            FROM monitoring.collection_jobs 
            WHERE started_at::date = p_target_date
        )
    );
    
    -- =====================================================
    -- GENERAR RECOMENDACIONES
    -- =====================================================
    
    -- Recomendaciones basadas en CPU
    IF COALESCE(max_cpu, 0) >= 90 THEN
        recommendations := array_append(recommendations, 
            'CPU: Uso crítico detectado (' || max_cpu || '%). Considerar escalado vertical o análisis de consultas.');
        health_score := health_score - 2.0;
    ELSIF COALESCE(avg_cpu, 0) >= 75 THEN
        recommendations := array_append(recommendations, 
            'CPU: Uso elevado sostenido (' || avg_cpu || '%). Monitorear tendencias.');
        health_score := health_score - 1.0;
    END IF;
    
    -- Recomendaciones basadas en memoria
    IF COALESCE(max_memory, 0) >= 95 THEN
        recommendations := array_append(recommendations, 
            'Memoria: Uso crítico (' || max_memory || '%). Revisión urgente de cache y consultas.');
        health_score := health_score - 2.5;
    ELSIF COALESCE(avg_memory, 0) >= 80 THEN
        recommendations := array_append(recommendations, 
            'Memoria: Uso elevado (' || avg_memory || '%). Optimizar configuración de memoria.');
        health_score := health_score - 1.0;
    END IF;
    
    -- Recomendaciones basadas en conexiones
    IF COALESCE(max_connections, 0) >= 95 THEN
        recommendations := array_append(recommendations, 
            'Conexiones: Límite casi alcanzado (' || max_connections || '%). Revisar pool de conexiones.');
        health_score := health_score - 1.5;
    END IF;
    
    -- Recomendaciones basadas en cache
    IF COALESCE(avg_cache_hit, 100) < 80 THEN
        recommendations := array_append(recommendations, 
            'Cache: Baja eficiencia (' || avg_cache_hit || '%). Revisar configuración y consultas.');
        health_score := health_score - 2.0;
    END IF;
    
    -- Recomendaciones basadas en alertas
    IF COALESCE(critical_alerts, 0) > 5 THEN
        recommendations := array_append(recommendations, 
            'Alertas: Muchas alertas críticas (' || critical_alerts || '). Revisión urgente requerida.');
        health_score := health_score - 2.0;
    END IF;
    
    -- Recomendaciones de notificaciones
    IF notification_success_rate < 90 THEN
        recommendations := array_append(recommendations, 
            'Notificaciones: Tasa de fallo elevada (' || (100 - notification_success_rate) || '%). Revisar configuración.');
        health_score := health_score - 1.0;
    END IF;
    
    -- Si no hay recomendaciones, agregar mensaje positivo
    IF array_length(recommendations, 1) IS NULL THEN
        recommendations := array_append(recommendations, 
            'Sistema funcionando dentro de parámetros normales. Continuar monitoreo rutinario.');
    END IF;
    
    -- =====================================================
    -- DETERMINAR ESTADO DE SALUD GENERAL
    -- =====================================================
    
    -- Asegurar que el score esté en rango válido
    health_score := GREATEST(0.0, LEAST(10.0, health_score));
    
    health_status := CASE 
        WHEN health_score >= 8.0 THEN 'healthy'
        WHEN health_score >= 6.0 THEN 'warning'
        ELSE 'critical'
    END;
    
    -- =====================================================
    -- INSERTAR REPORTE
    -- =====================================================
    
    INSERT INTO monitoring.daily_reports (
        id, report_date, generated_at,
        metrics_summary, alerts_summary, performance_summary,
        recommendations, overall_health_score, health_status,
        report_version, generated_by
    ) VALUES (
        report_id, p_target_date, NOW(),
        metrics_data, alerts_data, performance_data,
        recommendations, health_score, health_status,
        '1.0', 'system'
    ) ON CONFLICT (report_date) DO UPDATE SET
        generated_at = NOW(),
        metrics_summary = EXCLUDED.metrics_summary,
        alerts_summary = EXCLUDED.alerts_summary,
        performance_summary = EXCLUDED.performance_summary,
        recommendations = EXCLUDED.recommendations,
        overall_health_score = EXCLUDED.overall_health_score,
        health_status = EXCLUDED.health_status;
    
    -- Enviar resumen por email si el estado es crítico
    IF health_status = 'critical' THEN
        PERFORM monitoring.send_daily_report_alert(report_id);
    END IF;
    
    RAISE NOTICE 'Reporte diario generado para %: Estado %, Score %', 
        p_target_date, health_status, health_score;
    
    RETURN report_id;
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error generando reporte diario para %: %', p_target_date, SQLERRM;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA ENVIAR ALERTA DE REPORTE CRÍTICO
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.send_daily_report_alert(
    p_report_id UUID
)
RETURNS VOID AS $$
DECLARE
    report_rec RECORD;
    alert_id UUID := gen_random_uuid();
    message_content TEXT;
BEGIN
    SELECT * INTO report_rec 
    FROM monitoring.daily_reports 
    WHERE id = p_report_id;
    
    IF report_rec IS NULL THEN
        RETURN;
    END IF;
    
    -- Construir mensaje del reporte
    message_content := format(
        'REPORTE DIARIO - ESTADO CRÍTICO
        
Fecha: %s
Estado de Salud: %s (Score: %s/10)

ALERTAS DEL DÍA:
- Total: %s
- Críticas: %s
- Warnings: %s

MÉTRICAS PRINCIPALES:
- CPU Máximo: %s%%
- Memoria Máxima: %s%%
- Conexiones Máximas: %s%%
- Cache Hit Ratio: %s%%

RECOMENDACIONES:
%s

Generado automáticamente por el Sistema de Monitoreo.',
        report_rec.report_date,
        UPPER(report_rec.health_status),
        report_rec.overall_health_score,
        report_rec.alerts_summary->'total',
        report_rec.alerts_summary->'by_severity'->>'critical',
        report_rec.alerts_summary->'by_severity'->>'warning',
        report_rec.metrics_summary->'cpu'->>'maximum',
        report_rec.metrics_summary->'memory'->>'maximum',
        report_rec.metrics_summary->'connections'->>'maximum',
        report_rec.metrics_summary->'cache_performance'->>'average_hit_ratio',
        array_to_string(report_rec.recommendations, E'\n- ', '- ')
    );
    
    -- Crear alerta especial para el reporte
    INSERT INTO monitoring.alerts (
        id, timestamp, alert_type, severity, metric_name,
        title, description, status, notification_channels, created_by
    ) VALUES (
        alert_id, NOW(), 'daily_report_critical', 'critical', 'daily_health_score',
        format('Reporte Diario Crítico - %s', report_rec.report_date),
        message_content, 'active', 
        ARRAY['email', 'slack'], 'daily_report_system'
    );
    
    -- Enviar notificaciones
    PERFORM monitoring.send_alert_notifications(alert_id);
    
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN MEJORADA PARA VERIFICAR ALERTAS CON NOTIFICACIONES
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.check_alert_thresholds_enhanced()
RETURNS INTEGER AS $$
DECLARE
    threshold_rec RECORD;
    latest_metrics RECORD;
    alerts_count INTEGER := 0;
    alert_id UUID;
    current_value DECIMAL(15,2);
    should_alert BOOLEAN := FALSE;
    alert_level TEXT;
    notifications_sent INTEGER;
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
                CONTINUE;
        END CASE;
        
        IF current_value IS NULL THEN
            CONTINUE;
        END IF;
        
        -- Determinar si se debe generar alerta
        IF threshold_rec.metric_name = 'cache_hit_ratio' THEN
            IF current_value <= threshold_rec.critical_threshold THEN
                should_alert := TRUE;
                alert_level := 'critical';
            ELSIF current_value <= threshold_rec.warning_threshold THEN
                should_alert := TRUE;
                alert_level := 'warning';
            END IF;
        ELSE
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
            -- Verificar si ya existe una alerta activa similar
            IF NOT EXISTS (
                SELECT 1 FROM monitoring.alerts 
                WHERE metric_name = threshold_rec.metric_name 
                AND status = 'active'
                AND timestamp > NOW() - INTERVAL '1 hour'
            ) THEN
                -- Crear nueva alerta
                alert_id := gen_random_uuid();
                INSERT INTO monitoring.alerts (
                    id, timestamp, alert_type, severity, metric_name,
                    metric_value, threshold_value, title, description,
                    status, notification_channels, created_by
                ) VALUES (
                    alert_id, NOW(), 'threshold_breach', alert_level, threshold_rec.metric_name,
                    current_value,
                    CASE WHEN alert_level = 'critical' THEN threshold_rec.critical_threshold 
                         ELSE threshold_rec.warning_threshold END,
                    format('%s: %s (%s)', UPPER(alert_level), threshold_rec.display_name, current_value),
                    format('La métrica %s ha alcanzado un valor de %s, superando el umbral %s de %s',
                           threshold_rec.display_name, current_value, alert_level,
                           CASE WHEN alert_level = 'critical' THEN threshold_rec.critical_threshold 
                                ELSE threshold_rec.warning_threshold END),
                    'active', threshold_rec.notification_channels, 'enhanced_system'
                );
                
                alerts_count := alerts_count + 1;
                
                -- NUEVA: Enviar notificaciones automáticamente
                SELECT monitoring.send_alert_notifications(alert_id) INTO notifications_sent;
                
                RAISE NOTICE 'Alerta generada y % notificaciones enviadas: % - % (Valor: %, Umbral: %)', 
                    notifications_sent, alert_level, threshold_rec.display_name, current_value, 
                    CASE WHEN alert_level = 'critical' THEN threshold_rec.critical_threshold 
                         ELSE threshold_rec.warning_threshold END;
            END IF;
        END IF;
    END LOOP;
    
    RETURN alerts_count;
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error en check_alert_thresholds_enhanced: %', SQLERRM;
    RETURN 0;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA LIMPIEZA DIARIA AUTOMATIZADA
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.daily_maintenance()
RETURNS TEXT AS $$
DECLARE
    cleanup_result TEXT;
    report_result UUID;
    maintenance_summary TEXT;
BEGIN
    -- Limpiar datos antiguos
    SELECT monitoring.cleanup_old_data(30, 90, 7) INTO cleanup_result;
    
    -- Generar reporte del día anterior
    SELECT monitoring.generate_daily_report(CURRENT_DATE - INTERVAL '1 day') INTO report_result;
    
    -- Resetear contadores diarios de notificaciones
    UPDATE monitoring.notification_config SET
        notifications_sent_today = 0,
        updated_at = NOW()
    WHERE notifications_sent_today > 0;
    
    -- Resetear contadores de flood control antiguos
    DELETE FROM monitoring.alert_flood_control 
    WHERE period_start_time < NOW() - INTERVAL '24 hours';
    
    maintenance_summary := format(
        'Mantenimiento diario completado: %s | Reporte generado: %s | Contadores reseteados',
        cleanup_result, 
        CASE WHEN report_result IS NOT NULL THEN 'Sí' ELSE 'Error' END
    );
    
    RAISE NOTICE '%', maintenance_summary;
    RETURN maintenance_summary;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VISTAS PARA REPORTES Y DASHBOARD
-- =====================================================

CREATE OR REPLACE VIEW monitoring.daily_reports_summary AS
SELECT 
    report_date,
    health_status,
    overall_health_score,
    alerts_summary->'total' as total_alerts,
    alerts_summary->'by_severity'->>'critical' as critical_alerts,
    metrics_summary->'cpu'->>'maximum' as max_cpu_usage,
    metrics_summary->'memory'->>'maximum' as max_memory_usage,
    array_length(recommendations, 1) as recommendations_count,
    generated_at
FROM monitoring.daily_reports
ORDER BY report_date DESC;

CREATE OR REPLACE VIEW monitoring.alerts_dashboard_enhanced AS
SELECT 
    a.id,
    a.timestamp,
    a.severity,
    a.metric_name,
    a.title,
    a.metric_value,
    a.threshold_value,
    a.status,
    a.notification_sent,
    COALESCE(
        (SELECT COUNT(*) FROM monitoring.notification_history nh WHERE nh.alert_id = a.id),
        0
    ) as notifications_sent_count,
    COALESCE(
        (SELECT COUNT(*) FROM monitoring.notification_history nh WHERE nh.alert_id = a.id AND nh.status = 'failed'),
        0
    ) as notifications_failed_count
FROM monitoring.alerts a
WHERE a.status = 'active'
ORDER BY 
    CASE a.severity 
        WHEN 'critical' THEN 1 
        WHEN 'warning' THEN 2 
        ELSE 3 
    END,
    a.timestamp DESC;

-- =====================================================
-- ÍNDICES ADICIONALES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_daily_reports_date ON monitoring.daily_reports (report_date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_reports_health_status ON monitoring.daily_reports (health_status);

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON TABLE monitoring.daily_reports IS 'Reportes diarios automáticos del estado del sistema';
COMMENT ON FUNCTION monitoring.generate_daily_report(DATE) IS 'Genera un reporte completo del estado del sistema para una fecha específica';
COMMENT ON FUNCTION monitoring.send_daily_report_alert(UUID) IS 'Envía una alerta cuando el reporte diario indica estado crítico';
COMMENT ON FUNCTION monitoring.check_alert_thresholds_enhanced() IS 'Versión mejorada que incluye envío automático de notificaciones';
COMMENT ON FUNCTION monitoring.daily_maintenance() IS 'Función de mantenimiento diario que limpia datos y genera reportes';

-- Verificación final
DO $$
BEGIN
    RAISE NOTICE 'Sistema de resumen diario y automatización mejorada implementado';
    RAISE NOTICE 'Componentes: reportes diarios, alertas automáticas, mantenimiento';
    RAISE NOTICE 'Funciones principales: generate_daily_report, send_alert_notifications';
    RAISE NOTICE 'Vistas: daily_reports_summary, alerts_dashboard_enhanced';
END $$;
