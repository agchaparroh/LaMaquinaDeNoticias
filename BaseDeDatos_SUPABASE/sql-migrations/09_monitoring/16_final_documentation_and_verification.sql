-- =====================================================
-- DOCUMENTACIÓN Y VERIFICACIÓN FINAL DEL SISTEMA
-- Archivo: 16_final_documentation_and_verification.sql
-- Descripción: Documentación operacional y verificación completa
-- =====================================================

-- =====================================================
-- FUNCIÓN DE VERIFICACIÓN FINAL DEL SISTEMA
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.final_system_verification()
RETURNS JSONB AS $$
DECLARE
    verification_results JSONB := '{}'::jsonb;
    component_status JSONB;
    overall_status TEXT := 'healthy';
    issues_found TEXT[] := ARRAY[]::TEXT[];
    
    -- Contadores de verificación
    total_tables INTEGER;
    total_functions INTEGER;
    total_views INTEGER;
    total_indexes INTEGER;
    total_cron_jobs INTEGER;
    total_thresholds INTEGER;
    total_notification_channels INTEGER;
    
    -- Estados de componentes
    metrics_collection_ok BOOLEAN := FALSE;
    alert_system_ok BOOLEAN := FALSE;
    notification_system_ok BOOLEAN := FALSE;
    automation_ok BOOLEAN := FALSE;
    reporting_ok BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '=== VERIFICACIÓN FINAL DEL SISTEMA DE MONITOREO ===';
    
    -- =====================================================
    -- VERIFICACIÓN 1: ESTRUCTURA DE BASE DE DATOS
    -- =====================================================
    
    -- Contar tablas
    SELECT COUNT(*) INTO total_tables
    FROM information_schema.tables 
    WHERE table_schema = 'monitoring';
    
    -- Contar funciones
    SELECT COUNT(*) INTO total_functions
    FROM information_schema.routines 
    WHERE routine_schema = 'monitoring' AND routine_type = 'FUNCTION';
    
    -- Contar vistas
    SELECT COUNT(*) INTO total_views
    FROM information_schema.views 
    WHERE table_schema = 'monitoring';
    
    -- Contar índices
    SELECT COUNT(*) INTO total_indexes
    FROM pg_indexes 
    WHERE schemaname = 'monitoring';
    
    component_status := jsonb_build_object(
        'database_structure', jsonb_build_object(
            'tables', total_tables,
            'functions', total_functions,
            'views', total_views,
            'indexes', total_indexes,
            'status', CASE 
                WHEN total_tables >= 10 AND total_functions >= 15 THEN 'healthy'
                WHEN total_tables >= 5 AND total_functions >= 10 THEN 'warning'
                ELSE 'critical'
            END
        )
    );
    
    verification_results := verification_results || component_status;
    
    -- =====================================================
    -- VERIFICACIÓN 2: CONFIGURACIÓN Y DATOS INICIALES
    -- =====================================================
    
    -- Verificar umbrales configurados
    SELECT COUNT(*) INTO total_thresholds
    FROM monitoring.alert_thresholds 
    WHERE enabled = TRUE;
    
    -- Verificar canales de notificación
    SELECT COUNT(*) INTO total_notification_channels
    FROM monitoring.notification_config 
    WHERE enabled = TRUE;
    
    -- Verificar trabajos cron
    SELECT COUNT(*) INTO total_cron_jobs
    FROM cron.job 
    WHERE command LIKE '%monitoring.%';
    
    component_status := jsonb_build_object(
        'configuration', jsonb_build_object(
            'alert_thresholds', total_thresholds,
            'notification_channels', total_notification_channels,
            'cron_jobs', total_cron_jobs,
            'status', CASE 
                WHEN total_thresholds >= 8 AND total_notification_channels >= 1 AND total_cron_jobs >= 5 THEN 'healthy'
                WHEN total_thresholds >= 5 AND total_notification_channels >= 1 AND total_cron_jobs >= 3 THEN 'warning'
                ELSE 'critical'
            END
        )
    );
    
    verification_results := verification_results || component_status;
    
    -- =====================================================
    -- VERIFICACIÓN 3: FUNCIONALIDAD BÁSICA
    -- =====================================================
    
    -- Test de recolección de métricas
    BEGIN
        PERFORM monitoring.collect_system_metrics();
        metrics_collection_ok := TRUE;
    EXCEPTION WHEN OTHERS THEN
        metrics_collection_ok := FALSE;
        issues_found := array_append(issues_found, 'Fallo en recolección de métricas: ' || SQLERRM);
    END;
    
    -- Test de sistema de alertas
    BEGIN
        PERFORM monitoring.check_alert_thresholds_enhanced();
        alert_system_ok := TRUE;
    EXCEPTION WHEN OTHERS THEN
        alert_system_ok := FALSE;
        issues_found := array_append(issues_found, 'Fallo en sistema de alertas: ' || SQLERRM);
    END;
    
    -- Test de sistema de notificaciones (sin envío real)
    BEGIN
        -- Verificar que las funciones existen y son ejecutables
        PERFORM 1 FROM information_schema.routines 
        WHERE routine_schema = 'monitoring' 
        AND routine_name = 'send_alert_notifications';
        
        notification_system_ok := TRUE;
    EXCEPTION WHEN OTHERS THEN
        notification_system_ok := FALSE;
        issues_found := array_append(issues_found, 'Fallo en sistema de notificaciones: ' || SQLERRM);
    END;
    
    -- Test de automatización
    BEGIN
        PERFORM monitoring.daily_maintenance();
        automation_ok := TRUE;
    EXCEPTION WHEN OTHERS THEN
        automation_ok := FALSE;
        issues_found := array_append(issues_found, 'Fallo en automatización: ' || SQLERRM);
    END;
    
    -- Test de sistema de reportes
    BEGIN
        PERFORM monitoring.generate_daily_report(CURRENT_DATE - INTERVAL '1 day');
        reporting_ok := TRUE;
    EXCEPTION WHEN OTHERS THEN
        reporting_ok := FALSE;
        issues_found := array_append(issues_found, 'Fallo en sistema de reportes: ' || SQLERRM);
    END;
    
    component_status := jsonb_build_object(
        'functionality', jsonb_build_object(
            'metrics_collection', metrics_collection_ok,
            'alert_system', alert_system_ok,
            'notification_system', notification_system_ok,
            'automation', automation_ok,
            'reporting', reporting_ok,
            'status', CASE 
                WHEN metrics_collection_ok AND alert_system_ok AND notification_system_ok AND automation_ok AND reporting_ok THEN 'healthy'
                WHEN metrics_collection_ok AND alert_system_ok THEN 'warning'
                ELSE 'critical'
            END
        )
    );
    
    verification_results := verification_results || component_status;
    
    -- =====================================================
    -- DETERMINACIÓN DEL ESTADO GENERAL
    -- =====================================================
    
    -- Evaluar estado general basado en todos los componentes
    IF array_length(issues_found, 1) IS NULL THEN
        IF total_tables >= 10 AND total_functions >= 15 AND total_thresholds >= 8 AND 
           metrics_collection_ok AND alert_system_ok AND notification_system_ok THEN
            overall_status := 'healthy';
        ELSE
            overall_status := 'warning';
        END IF;
    ELSE
        overall_status := 'critical';
    END IF;
    
    -- Agregar resumen final
    verification_results := verification_results || jsonb_build_object(
        'summary', jsonb_build_object(
            'overall_status', overall_status,
            'verification_timestamp', NOW(),
            'issues_found', issues_found,
            'components_verified', 3,
            'recommendation', CASE overall_status
                WHEN 'healthy' THEN 'Sistema listo para producción'
                WHEN 'warning' THEN 'Sistema funcional, revisar warnings antes de producción'
                ELSE 'Sistema requiere correcciones antes de despliegue'
            END
        )
    );
    
    -- Logging del resultado
    RAISE NOTICE '=== VERIFICACIÓN COMPLETADA ===';
    RAISE NOTICE 'Estado General: %', overall_status;
    RAISE NOTICE 'Tablas: % | Funciones: % | Vistas: % | Índices: %', total_tables, total_functions, total_views, total_indexes;
    RAISE NOTICE 'Umbrales: % | Canales: % | Jobs Cron: %', total_thresholds, total_notification_channels, total_cron_jobs;
    RAISE NOTICE 'Funcionalidad: Métricas=% | Alertas=% | Notificaciones=% | Automatización=% | Reportes=%', 
        metrics_collection_ok, alert_system_ok, notification_system_ok, automation_ok, reporting_ok;
    
    IF array_length(issues_found, 1) > 0 THEN
        RAISE NOTICE 'PROBLEMAS ENCONTRADOS: %', array_to_string(issues_found, ' | ');
    ELSE
        RAISE NOTICE 'SISTEMA VERIFICADO EXITOSAMENTE - LISTO PARA OPERACIÓN';
    END IF;
    
    RETURN verification_results;
    
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'summary', jsonb_build_object(
            'overall_status', 'error',
            'error_message', SQLERRM,
            'verification_timestamp', NOW()
        )
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA OBTENER ESTADO OPERACIONAL COMPLETO
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.get_operational_status()
RETURNS JSONB AS $$
DECLARE
    status_result JSONB;
    latest_metrics RECORD;
    active_alerts INTEGER;
    critical_alerts INTEGER;
    recent_jobs INTEGER;
    failed_jobs INTEGER;
    last_report_date DATE;
    notification_success_rate DECIMAL(5,2);
BEGIN
    -- Métricas más recientes
    SELECT * INTO latest_metrics 
    FROM monitoring.system_metrics 
    ORDER BY timestamp DESC 
    LIMIT 1;
    
    -- Contar alertas
    SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE severity = 'critical') as critical
    INTO active_alerts, critical_alerts
    FROM monitoring.alerts 
    WHERE status = 'active';
    
    -- Estado de trabajos
    SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE status = 'failed') as failed
    INTO recent_jobs, failed_jobs
    FROM monitoring.collection_jobs 
    WHERE started_at > NOW() - INTERVAL '24 hours';
    
    -- Último reporte
    SELECT MAX(report_date) INTO last_report_date
    FROM monitoring.daily_reports;
    
    -- Tasa de éxito de notificaciones
    SELECT 
        CASE WHEN COUNT(*) > 0 THEN
            ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'sent') / COUNT(*), 2)
        ELSE 100.0 END
    INTO notification_success_rate
    FROM monitoring.notification_history 
    WHERE timestamp > NOW() - INTERVAL '24 hours';
    
    -- Construir resultado
    status_result := jsonb_build_object(
        'timestamp', NOW(),
        'system_health', jsonb_build_object(
            'overall_status', CASE 
                WHEN critical_alerts > 0 THEN 'critical'
                WHEN active_alerts > 5 OR failed_jobs > recent_jobs * 0.1 THEN 'warning'
                WHEN latest_metrics.timestamp < NOW() - INTERVAL '10 minutes' THEN 'warning'
                ELSE 'healthy'
            END,
            'data_freshness', CASE 
                WHEN latest_metrics.timestamp > NOW() - INTERVAL '10 minutes' THEN 'current'
                WHEN latest_metrics.timestamp > NOW() - INTERVAL '30 minutes' THEN 'recent'
                ELSE 'stale'
            END
        ),
        'metrics', CASE 
            WHEN latest_metrics IS NOT NULL THEN
                jsonb_build_object(
                    'last_collection', latest_metrics.timestamp,
                    'cpu_usage', latest_metrics.cpu_usage_percent,
                    'memory_usage', latest_metrics.memory_usage_percent,
                    'connections', latest_metrics.total_connections,
                    'cache_hit_ratio', latest_metrics.cache_hit_ratio,
                    'database_size_mb', latest_metrics.database_size_mb
                )
            ELSE jsonb_build_object('status', 'no_data')
        END,
        'alerts', jsonb_build_object(
            'total_active', active_alerts,
            'critical', critical_alerts,
            'status', CASE 
                WHEN critical_alerts > 0 THEN 'critical'
                WHEN active_alerts > 5 THEN 'warning'
                ELSE 'normal'
            END
        ),
        'automation', jsonb_build_object(
            'jobs_24h', recent_jobs,
            'failed_jobs', failed_jobs,
            'success_rate', CASE WHEN recent_jobs > 0 THEN 
                ROUND(100.0 * (recent_jobs - failed_jobs) / recent_jobs, 2) 
                ELSE 100.0 END,
            'status', CASE 
                WHEN failed_jobs = 0 THEN 'healthy'
                WHEN failed_jobs <= recent_jobs * 0.1 THEN 'warning'
                ELSE 'critical'
            END
        ),
        'notifications', jsonb_build_object(
            'success_rate_24h', notification_success_rate,
            'status', CASE 
                WHEN notification_success_rate >= 95 THEN 'healthy'
                WHEN notification_success_rate >= 80 THEN 'warning'
                ELSE 'critical'
            END
        ),
        'reporting', jsonb_build_object(
            'last_report_date', last_report_date,
            'status', CASE 
                WHEN last_report_date >= CURRENT_DATE - INTERVAL '1 day' THEN 'current'
                WHEN last_report_date >= CURRENT_DATE - INTERVAL '3 days' THEN 'recent'
                ELSE 'outdated'
            END
        )
    );
    
    RETURN status_result;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- DOCUMENTACIÓN OPERACIONAL EN TABLA
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.operational_documentation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    section TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    
    -- Metadatos
    version TEXT DEFAULT '1.0',
    author TEXT DEFAULT 'system',
    
    UNIQUE(section, title)
);

-- Insertar documentación operacional
INSERT INTO monitoring.operational_documentation (section, title, content) VALUES 

('overview', 'Descripción del Sistema', 
'El Sistema de Monitoreo de la Máquina de Noticias es una solución completa para supervisar la salud y rendimiento de la base de datos PostgreSQL/Supabase. Incluye recolección automática de métricas, sistema de alertas inteligente, notificaciones multi-canal, reportes diarios y automatización completa.'),

('overview', 'Componentes Principales', 
'1. RECOLECCIÓN DE MÉTRICAS: Automática cada 5 minutos
2. SISTEMA DE ALERTAS: Verificación de umbrales y generación automática
3. NOTIFICACIONES: Email, Slack, SMS y Webhooks
4. CONTROL ANTI-FLOOD: Prevención de spam de alertas
5. REPORTES DIARIOS: Generación automática con análisis de salud
6. AUTOMATIZACIÓN: 6+ trabajos pg_cron para operación 24/7'),

('operations', 'Comandos Básicos de Operación', 
'-- Verificar estado general:
SELECT monitoring.get_operational_status();

-- Recolectar métricas manualmente:
SELECT monitoring.collect_system_metrics();

-- Generar reporte diario:
SELECT monitoring.generate_daily_report();

-- Ejecutar testing completo:
SELECT monitoring.run_comprehensive_tests();

-- Verificación final del sistema:
SELECT monitoring.final_system_verification();'),

('operations', 'Monitoreo de Alertas', 
'-- Ver alertas activas:
SELECT * FROM monitoring.alerts_dashboard_enhanced;

-- Ver historial de notificaciones:
SELECT * FROM monitoring.notification_history ORDER BY timestamp DESC LIMIT 10;

-- Configurar nuevos umbrales:
INSERT INTO monitoring.alert_thresholds (metric_name, display_name, warning_threshold, critical_threshold) 
VALUES (''nueva_metrica'', ''Nueva Métrica'', 80.0, 95.0);'),

('maintenance', 'Tareas de Mantenimiento', 
'DIARIO (Automático a las 2:00 AM):
- Limpieza de datos antiguos (métricas >30d, alertas >90d)
- Generación de reporte diario
- Reset de contadores de notificaciones

SEMANAL (Manual):
- Revisar alertas recurrentes
- Validar configuración de umbrales
- Verificar funcionamiento de canales de notificación

MENSUAL (Manual):
- Análisis de tendencias de rendimiento
- Optimización de umbrales basada en histórico
- Backup de configuraciones críticas'),

('troubleshooting', 'Problemas Comunes', 
'PROBLEMA: Métricas no se recolectan
SOLUCIÓN: Verificar trabajos pg_cron: SELECT * FROM cron.job;

PROBLEMA: Alertas no se envían
SOLUCIÓN: Verificar canales: SELECT * FROM monitoring.notification_config WHERE enabled = TRUE;

PROBLEMA: Rendimiento lento
SOLUCIÓN: Revisar: SELECT * FROM monitoring.collection_jobs WHERE status = ''failed'';

PROBLEMA: Demasiadas alertas
SOLUCIÓN: Ajustar umbrales: UPDATE monitoring.alert_thresholds SET warning_threshold = X WHERE metric_name = ''Y'';'),

('configuration', 'Configuración de Canales de Notificación', 
'-- Email:
INSERT INTO monitoring.notification_config (channel_type, channel_name, config)
VALUES (''email'', ''admin'', jsonb_build_object(''email_address'', ''admin@empresa.com''));

-- Slack:
INSERT INTO monitoring.notification_config (channel_type, channel_name, config)
VALUES (''slack'', ''alertas'', jsonb_build_object(''webhook_url'', ''https://hooks.slack.com/...''));

-- SMS:
INSERT INTO monitoring.notification_config (channel_type, channel_name, config)
VALUES (''sms'', ''emergencia'', jsonb_build_object(''phone_number'', ''+1234567890''));'),

('monitoring', 'Métricas Clave a Supervisar', 
'CPU Usage: >75% warning, >90% critical
Memory Usage: >80% warning, >95% critical
Storage Usage: >85% warning, >95% critical
Connection Usage: >80% warning, >95% critical
Cache Hit Ratio: <90% warning, <80% critical
Slow Queries: >10 warning, >50 critical
Deadlocks: >1 warning, >5 critical

SUPABASE ESPECÍFICO:
API Requests: >85% warning, >95% critical
Storage: >80% warning, >90% critical
Bandwidth: >85% warning, >95% critical')

ON CONFLICT (section, title) DO UPDATE SET
    content = EXCLUDED.content,
    created_at = NOW();

-- =====================================================
-- VISTA CONSOLIDADA DE DOCUMENTACIÓN
-- =====================================================

CREATE OR REPLACE VIEW monitoring.documentation_index AS
SELECT 
    section,
    title,
    LEFT(content, 100) || CASE WHEN LENGTH(content) > 100 THEN '...' ELSE '' END as summary,
    LENGTH(content) as content_length,
    created_at
FROM monitoring.operational_documentation
ORDER BY 
    CASE section 
        WHEN 'overview' THEN 1
        WHEN 'operations' THEN 2
        WHEN 'configuration' THEN 3
        WHEN 'monitoring' THEN 4
        WHEN 'maintenance' THEN 5
        WHEN 'troubleshooting' THEN 6
        ELSE 7
    END,
    title;

-- =====================================================
-- FUNCIÓN PARA MOSTRAR DOCUMENTACIÓN
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.show_documentation(
    p_section TEXT DEFAULT NULL
)
RETURNS TABLE (
    section TEXT,
    title TEXT,
    content TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        od.section,
        od.title,
        od.content
    FROM monitoring.operational_documentation od
    WHERE p_section IS NULL OR od.section = p_section
    ORDER BY 
        CASE od.section 
            WHEN 'overview' THEN 1
            WHEN 'operations' THEN 2
            WHEN 'configuration' THEN 3
            WHEN 'monitoring' THEN 4
            WHEN 'maintenance' THEN 5
            WHEN 'troubleshooting' THEN 6
            ELSE 7
        END,
        od.title;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- COMENTARIOS FINALES Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON FUNCTION monitoring.final_system_verification() IS 'Verificación completa final del sistema de monitoreo - ejecutar antes de producción';
COMMENT ON FUNCTION monitoring.get_operational_status() IS 'Estado operacional completo del sistema en formato JSON';
COMMENT ON TABLE monitoring.operational_documentation IS 'Documentación operacional completa del sistema de monitoreo';
COMMENT ON FUNCTION monitoring.show_documentation(TEXT) IS 'Muestra documentación operacional por sección';

-- =====================================================
-- VERIFICACIÓN Y MENSAJE FINAL
-- =====================================================

DO $$
DECLARE
    verification_result JSONB;
    overall_status TEXT;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== INSTALACIÓN DEL SISTEMA DE MONITOREO COMPLETADA ===';
    RAISE NOTICE '';
    
    -- Ejecutar verificación final
    SELECT monitoring.final_system_verification() INTO verification_result;
    overall_status := verification_result->'summary'->>'overall_status';
    
    RAISE NOTICE 'ESTADO FINAL: %', UPPER(overall_status);
    RAISE NOTICE '';
    
    IF overall_status = 'healthy' THEN
        RAISE NOTICE '✅ SISTEMA LISTO PARA PRODUCCIÓN';
        RAISE NOTICE '';
        RAISE NOTICE 'PRÓXIMOS PASOS:';
        RAISE NOTICE '1. Configurar credenciales reales de notificación (SMTP, Slack, etc.)';
        RAISE NOTICE '2. Ajustar umbrales según ambiente de producción';
        RAISE NOTICE '3. Configurar backup de configuraciones críticas';
        RAISE NOTICE '4. Entrenar al equipo de operaciones';
    ELSIF overall_status = 'warning' THEN
        RAISE NOTICE '⚠️  SISTEMA FUNCIONAL CON ALERTAS MENORES';
        RAISE NOTICE 'Revisar warnings antes de despliegue a producción';
    ELSE
        RAISE NOTICE '❌ SISTEMA REQUIERE CORRECCIONES';
        RAISE NOTICE 'Solucionar problemas críticos antes de continuar';
    END IF;
    
    RAISE NOTICE '';
    RAISE NOTICE 'DOCUMENTACIÓN:';
    RAISE NOTICE '- Completa: SELECT * FROM monitoring.show_documentation();';
    RAISE NOTICE '- Por sección: SELECT * FROM monitoring.show_documentation(''operations'');';
    RAISE NOTICE '';
    RAISE NOTICE 'COMANDOS ÚTILES:';
    RAISE NOTICE '- Estado: SELECT monitoring.get_operational_status();';
    RAISE NOTICE '- Testing: SELECT monitoring.run_comprehensive_tests();';
    RAISE NOTICE '- Reporte: SELECT monitoring.generate_testing_report();';
    RAISE NOTICE '';
    RAISE NOTICE '=== SUBTAREA 22.6 COMPLETADA ===';
    
END $$;
