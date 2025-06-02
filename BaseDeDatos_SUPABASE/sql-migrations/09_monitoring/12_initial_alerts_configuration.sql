-- =====================================================
-- CONFIGURACIÓN INICIAL DEL SISTEMA DE ALERTAS
-- Archivo: 12_initial_alerts_configuration.sql
-- Descripción: Configuración inicial con ejemplos de canales, plantillas y escalamiento
-- =====================================================

-- =====================================================
-- CONFIGURACIÓN DE CANALES DE NOTIFICACIÓN
-- =====================================================

-- Canal de email para administradores
INSERT INTO monitoring.notification_channels (
    channel_name, channel_type, enabled, priority,
    configuration, active_hours_start, active_hours_end,
    active_days, max_notifications_per_hour, escalation_delay_minutes,
    tags
) VALUES (
    'admin_email', 'email', TRUE, 1,
    jsonb_build_object(
        'recipient_email', 'admin@empresa.com',
        'smtp_server', 'smtp.gmail.com',
        'smtp_port', 587,
        'smtp_username', 'notifications@empresa.com',
        'smtp_password', '***',
        'smtp_tls', true
    ),
    '00:00:00', '23:59:59', ARRAY[1,2,3,4,5,6,7], 20, 30,
    jsonb_build_object('type', 'admin', 'criticality', 'high')
),
(
    'oncall_email', 'email', TRUE, 2,
    jsonb_build_object(
        'recipient_email', 'oncall@empresa.com',
        'smtp_server', 'smtp.gmail.com',
        'smtp_port', 587,
        'smtp_username', 'notifications@empresa.com',
        'smtp_password', '***',
        'smtp_tls', true
    ),
    '00:00:00', '23:59:59', ARRAY[1,2,3,4,5,6,7], 50, 15,
    jsonb_build_object('type', 'oncall', 'criticality', 'high')
);

-- Canal de Slack para el equipo de desarrollo
INSERT INTO monitoring.notification_channels (
    channel_name, channel_type, enabled, priority,
    configuration, active_hours_start, active_hours_end,
    active_days, max_notifications_per_hour,
    tags
) VALUES (
    'dev_team_slack', 'slack', TRUE, 3,
    jsonb_build_object(
        'webhook_url', 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX',
        'channel_id', '#alerts-dev',
        'bot_token', 'xoxb-your-bot-token-here',
        'username', 'MonitoringBot',
        'icon_emoji', ':warning:'
    ),
    '08:00:00', '20:00:00', ARRAY[1,2,3,4,5], 30,
    jsonb_build_object('type', 'team', 'department', 'development')
),
(
    'critical_slack', 'slack', TRUE, 1,
    jsonb_build_object(
        'webhook_url', 'https://hooks.slack.com/services/T00000000/B00000000/YYYYYYYYYYYYYYYYYYYYYYYY',
        'channel_id', '#critical-alerts',
        'bot_token', 'xoxb-your-bot-token-here',
        'username', 'CriticalAlerts',
        'icon_emoji', ':rotating_light:'
    ),
    '00:00:00', '23:59:59', ARRAY[1,2,3,4,5,6,7], 10,
    jsonb_build_object('type', 'critical', 'priority', 'highest')
);

-- Canal SMS para emergencias (usando Twilio como ejemplo)
INSERT INTO monitoring.notification_channels (
    channel_name, channel_type, enabled, priority,
    configuration, active_hours_start, active_hours_end,
    active_days, max_notifications_per_hour,
    tags
) VALUES (
    'emergency_sms', 'sms', TRUE, 1,
    jsonb_build_object(
        'provider', 'twilio',
        'account_sid', 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        'auth_token', 'your_auth_token_here',
        'from_number', '+1234567890',
        'phone_number', '+1987654321'
    ),
    '00:00:00', '23:59:59', ARRAY[1,2,3,4,5,6,7], 5,
    jsonb_build_object('type', 'emergency', 'cost_per_message', 0.0075)
);

-- Canal webhook para integración con sistemas externos
INSERT INTO monitoring.notification_channels (
    channel_name, channel_type, enabled, priority,
    configuration, active_hours_start, active_hours_end,
    active_days, max_notifications_per_hour,
    tags
) VALUES (
    'external_webhook', 'webhook', TRUE, 4,
    jsonb_build_object(
        'webhook_url', 'https://api.external-system.com/alerts',
        'method', 'POST',
        'headers', jsonb_build_object(
            'Content-Type', 'application/json',
            'Authorization', 'Bearer your_api_token_here'
        ),
        'timeout_seconds', 10,
        'retry_count', 3
    ),
    '00:00:00', '23:59:59', ARRAY[1,2,3,4,5,6,7], 100,
    jsonb_build_object('type', 'integration', 'external_system', 'monitoring_hub')
);

-- =====================================================
-- PLANTILLAS DE NOTIFICACIÓN
-- =====================================================

-- Plantilla de email para alertas críticas del sistema
INSERT INTO monitoring.notification_templates (
    template_name, alert_type, severity, channel_type,
    subject_template, body_template, format_type,
    include_details, auto_resolve_message
) VALUES (
    'critical_system_email', 'system', 'critical', 'email',
    '[CRÍTICO] {{title}} - Máquina de Noticias',
    '🚨 ALERTA CRÍTICA DEL SISTEMA 🚨

Estimado equipo de sistemas,

Se ha detectado una alerta crítica en el sistema "Máquina de Noticias":

📊 DETALLES DE LA ALERTA:
• Título: {{title}}
• Métrica: {{metric_name}}
• Valor actual: {{metric_value}}
• Umbral crítico: {{threshold}}
• Tiempo activa: {{hours_active}} horas
• Severidad: {{severity}}

📝 DESCRIPCIÓN:
{{description}}

⚡ ACCIÓN REQUERIDA:
Esta alerta requiere atención inmediata. Por favor, revise el dashboard y tome las medidas correctivas necesarias.

🔗 ENLACES ÚTILES:
• Dashboard: {{dashboard_url}}
• Runbook: {{dashboard_url}}/runbooks
• Escalamiento: Si no se resuelve en 30 minutos, se escalará automáticamente

📅 INFORMACIÓN TÉCNICA:
• Base de datos: {{database_name}}
• Timestamp: {{timestamp}}
• ID de alerta: {{alert_id}}

Saludos,
Sistema de Monitoreo Automático',
    'html', TRUE, TRUE
);

-- Plantilla de Slack para alertas warning
INSERT INTO monitoring.notification_templates (
    template_name, alert_type, severity, channel_type,
    subject_template, body_template, format_type,
    include_details, auto_resolve_message
) VALUES (
    'warning_slack', 'system', 'warning', 'slack',
    NULL,
    '{
    "text": "⚠️ Alerta de Warning - Máquina de Noticias",
    "attachments": [
        {
            "color": "warning",
            "title": "{{title}}",
            "fields": [
                {
                    "title": "Métrica",
                    "value": "{{metric_name}}: {{metric_value}}",
                    "short": true
                },
                {
                    "title": "Umbral",
                    "value": "{{threshold}}",
                    "short": true
                },
                {
                    "title": "Tiempo activa",
                    "value": "{{hours_active}} horas",
                    "short": true
                },
                {
                    "title": "Severidad",
                    "value": "{{severity}}",
                    "short": true
                }
            ],
            "text": "{{description}}",
            "actions": [
                {
                    "type": "button",
                    "text": "Ver Dashboard",
                    "url": "{{dashboard_url}}"
                }
            ]
        }
    ]
}',
    'json', TRUE, TRUE
);

-- Plantilla de SMS para alertas críticas (formato corto)
INSERT INTO monitoring.notification_templates (
    template_name, alert_type, severity, channel_type,
    subject_template, body_template, format_type,
    include_details, auto_resolve_message
) VALUES (
    'critical_sms', 'system', 'critical', 'sms',
    NULL,
    'CRÍTICO: {{title}}
{{metric_name}}: {{metric_value}}
Activa: {{hours_active}}h
Dashboard: {{dashboard_url}}',
    'text', FALSE, FALSE
);

-- Plantilla para alertas de Supabase
INSERT INTO monitoring.notification_templates (
    template_name, alert_type, severity, channel_type,
    subject_template, body_template, format_type,
    include_details, auto_resolve_message
) VALUES (
    'supabase_critical_email', 'supabase', 'critical', 'email',
    '[SUPABASE CRÍTICO] {{title}} - Límites del Plan',
    '🔥 ALERTA CRÍTICA DE SUPABASE 🔥

El sistema ha detectado un problema crítico relacionado con los límites de Supabase:

📊 DETALLES:
• Problema: {{title}}
• Métrica: {{metric_name}}
• Uso actual: {{metric_value}}%
• Límite: {{threshold}}%
• Tiempo activa: {{hours_active}} horas

🎯 POSIBLES ACCIONES:
1. Revisar el uso actual en el dashboard de Supabase
2. Considerar upgrade del plan si es necesario
3. Optimizar consultas y uso de recursos
4. Implementar cache para reducir llamadas a la API

🔗 Enlaces importantes:
• Dashboard local: {{dashboard_url}}
• Supabase Dashboard: https://app.supabase.com
• Documentación de límites: https://supabase.com/docs/guides/platform/limits

⏰ Timestamp: {{timestamp}}
🏢 Base de datos: {{database_name}}

Sistema de Monitoreo Máquina de Noticias',
    'html', TRUE, TRUE
);

-- Plantilla webhook genérica (JSON)
INSERT INTO monitoring.notification_templates (
    template_name, alert_type, severity, channel_type,
    subject_template, body_template, format_type,
    include_details, auto_resolve_message
) VALUES (
    'webhook_generic', 'custom', 'critical', 'webhook',
    NULL,
    '{
    "event_type": "alert_triggered",
    "alert": {
        "id": "{{alert_id}}",
        "title": "{{title}}",
        "description": "{{description}}",
        "severity": "{{severity}}",
        "metric_name": "{{metric_name}}",
        "metric_value": {{metric_value}},
        "threshold": {{threshold}},
        "timestamp": "{{timestamp}}",
        "hours_active": {{hours_active}},
        "source_system": "maquina_noticias_monitoring",
        "database": "{{database_name}}",
        "dashboard_url": "{{dashboard_url}}"
    },
    "context": {
        "current_cpu": "{{current_cpu}}",
        "current_memory": "{{current_memory}}",
        "total_alerts": "{{total_alerts}}"
    }
}',
    'json', TRUE, TRUE
);

-- =====================================================
-- REGLAS DE ESCALAMIENTO
-- =====================================================

-- Regla de escalamiento para alertas críticas del sistema
INSERT INTO monitoring.alert_escalation_rules (
    rule_name, description,
    alert_severity, alert_types,
    escalation_delay_minutes, max_escalation_level,
    level_1_channels, level_2_channels, level_3_channels,
    require_acknowledgment, business_hours_only
) VALUES (
    'critical_system_escalation',
    'Escalamiento automático para alertas críticas del sistema que no se resuelven',
    ARRAY['critical'],
    ARRAY['threshold_breach', 'system_health'],
    30, -- Escalar después de 30 minutos
    3,
    -- Nivel 1: Equipo de guardia (30 min)
    ARRAY(SELECT id FROM monitoring.notification_channels WHERE channel_name IN ('oncall_email', 'dev_team_slack')),
    -- Nivel 2: Administradores y SMS (60 min)
    ARRAY(SELECT id FROM monitoring.notification_channels WHERE channel_name IN ('admin_email', 'critical_slack', 'emergency_sms')),
    -- Nivel 3: Todos los canales (90 min)
    ARRAY(SELECT id FROM monitoring.notification_channels WHERE enabled = TRUE),
    FALSE, -- No requiere confirmación
    FALSE  -- Activo 24/7
);

-- Regla de escalamiento para límites de Supabase
INSERT INTO monitoring.alert_escalation_rules (
    rule_name, description,
    alert_severity, metric_names,
    escalation_delay_minutes, max_escalation_level,
    level_1_channels, level_2_channels,
    business_hours_only
) VALUES (
    'supabase_limits_escalation',
    'Escalamiento para alertas de límites de Supabase que requieren acción comercial',
    ARRAY['critical', 'warning'],
    ARRAY['api_requests_limit', 'storage_limit', 'bandwidth_limit'],
    60, -- Escalar después de 1 hora
    2,
    -- Nivel 1: Equipo técnico
    ARRAY(SELECT id FROM monitoring.notification_channels WHERE channel_name IN ('dev_team_slack', 'admin_email')),
    -- Nivel 2: Incluir management para decisiones de upgrade
    ARRAY(SELECT id FROM monitoring.notification_channels WHERE tags->>'type' IN ('admin', 'critical')),
    TRUE -- Solo en horario laboral para decisiones comerciales
);

-- =====================================================
-- AUTOMATIZACIÓN CON PG_CRON
-- =====================================================

-- Trabajo para procesar notificaciones automáticas cada 5 minutos
SELECT cron.schedule(
    'process-automatic-notifications',
    '*/5 * * * *',                 -- Cada 5 minutos
    $process_notifications$
    DO $$
    DECLARE
        unnotified_alerts RECORD;
        notifications_sent INTEGER;
        total_notifications INTEGER := 0;
    BEGIN
        -- Procesar alertas activas que no han sido notificadas
        FOR unnotified_alerts IN 
            SELECT id, title, severity
            FROM monitoring.alerts 
            WHERE status = 'active' 
            AND (notification_sent = FALSE OR notification_sent IS NULL)
            AND timestamp > NOW() - INTERVAL '24 hours' -- Solo alertas recientes
        LOOP
            BEGIN
                SELECT monitoring.send_alert_notification(unnotified_alerts.id) INTO notifications_sent;
                total_notifications := total_notifications + notifications_sent;
                
                RAISE NOTICE 'Notificaciones enviadas para alerta %: %', 
                             unnotified_alerts.title, notifications_sent;
                             
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Error procesando notificaciones para alerta %: %', 
                             unnotified_alerts.id, SQLERRM;
            END;
        END LOOP;
        
        IF total_notifications > 0 THEN
            RAISE NOTICE 'Total de notificaciones procesadas: %', total_notifications;
        END IF;
    END $$;
    $process_notifications$
);

-- Trabajo para procesar escalamiento cada 15 minutos
SELECT cron.schedule(
    'process-alert-escalation',
    '*/15 * * * *',                -- Cada 15 minutos
    $process_escalation$
    DO $$
    DECLARE
        escalations_processed INTEGER;
    BEGIN
        SELECT monitoring.process_alert_escalation() INTO escalations_processed;
        
        IF escalations_processed > 0 THEN
            RAISE NOTICE 'Escalamientos procesados: %', escalations_processed;
        END IF;
    END $$;
    $process_escalation$
);

-- Trabajo para limpieza del historial de notificaciones (semanal)
SELECT cron.schedule(
    'cleanup-notification-history',
    '0 3 * * 1',                   -- Lunes a las 3:00 AM
    $cleanup_notifications$
    DO $$
    DECLARE
        deleted_notifications INTEGER;
    BEGIN
        -- Limpiar notificaciones antiguas (más de 3 meses)
        DELETE FROM monitoring.notification_history 
        WHERE sent_at < NOW() - INTERVAL '3 months';
        GET DIAGNOSTICS deleted_notifications = ROW_COUNT;
        
        -- Resetear contadores de rate limiting
        UPDATE monitoring.notification_channels 
        SET current_hour_count = 0, last_reset_hour = NOW();
        
        RAISE NOTICE 'Limpieza de notificaciones: % registros eliminados', deleted_notifications;
    END $$;
    $cleanup_notifications$
);

-- =====================================================
-- FUNCIONES DE UTILIDAD PARA ADMINISTRACIÓN
-- =====================================================

-- Función para enviar notificación de prueba
CREATE OR REPLACE FUNCTION monitoring.send_test_notification(
    p_channel_name TEXT,
    p_test_message TEXT DEFAULT 'Mensaje de prueba del sistema de monitoreo'
)
RETURNS BOOLEAN AS $$
DECLARE
    test_alert_id UUID;
    notifications_sent INTEGER;
BEGIN
    -- Crear alerta de prueba temporal
    INSERT INTO monitoring.alerts (
        timestamp, alert_type, severity, metric_name,
        metric_value, title, description, status,
        notification_channels, created_by
    ) VALUES (
        NOW(), 'test', 'info', 'test_metric',
        0, 'Prueba de Notificación',
        p_test_message, 'active',
        ARRAY(SELECT channel_type FROM monitoring.notification_channels WHERE channel_name = p_channel_name),
        'test_function'
    ) RETURNING id INTO test_alert_id;
    
    -- Enviar notificación
    SELECT monitoring.send_alert_notification(test_alert_id, TRUE) INTO notifications_sent;
    
    -- Limpiar alerta de prueba
    DELETE FROM monitoring.alerts WHERE id = test_alert_id;
    DELETE FROM monitoring.notification_history WHERE alert_id = test_alert_id;
    
    RETURN notifications_sent > 0;
END;
$$ LANGUAGE plpgsql;

-- Función para obtener estadísticas de notificaciones
CREATE OR REPLACE FUNCTION monitoring.get_notification_stats(
    p_days_back INTEGER DEFAULT 7
)
RETURNS JSONB AS $$
DECLARE
    stats JSONB;
BEGIN
    SELECT jsonb_build_object(
        'period_days', p_days_back,
        'total_notifications', COUNT(*),
        'successful_notifications', COUNT(*) FILTER (WHERE status = 'sent'),
        'failed_notifications', COUNT(*) FILTER (WHERE status = 'failed'),
        'avg_delivery_time_ms', ROUND(AVG(delivery_time_ms)),
        'by_channel', jsonb_object_agg(
            nc.channel_type,
            jsonb_build_object(
                'count', channel_stats.notification_count,
                'success_rate', ROUND(channel_stats.success_rate, 2)
            )
        ),
        'by_severity', jsonb_object_agg(
            a.severity,
            severity_stats.notification_count
        )
    ) INTO stats
    FROM monitoring.notification_history nh
    JOIN monitoring.notification_channels nc ON nh.channel_id = nc.id
    LEFT JOIN monitoring.alerts a ON nh.alert_id = a.id
    CROSS JOIN LATERAL (
        SELECT 
            COUNT(*) as notification_count,
            (COUNT(*) FILTER (WHERE nh.status = 'sent') * 100.0 / COUNT(*)) as success_rate
        FROM monitoring.notification_history nh2
        WHERE nh2.channel_id = nh.channel_id
        AND nh2.sent_at > NOW() - INTERVAL '1 day' * p_days_back
    ) channel_stats
    CROSS JOIN LATERAL (
        SELECT COUNT(*) as notification_count
        FROM monitoring.notification_history nh3
        JOIN monitoring.alerts a2 ON nh3.alert_id = a2.id
        WHERE a2.severity = a.severity
        AND nh3.sent_at > NOW() - INTERVAL '1 day' * p_days_back
    ) severity_stats
    WHERE nh.sent_at > NOW() - INTERVAL '1 day' * p_days_back;
    
    RETURN COALESCE(stats, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON FUNCTION monitoring.send_test_notification(TEXT, TEXT) IS 'Envía una notificación de prueba a un canal específico';
COMMENT ON FUNCTION monitoring.get_notification_stats(INTEGER) IS 'Obtiene estadísticas de rendimiento del sistema de notificaciones';

-- Verificación final
DO $$
DECLARE
    channels_count INTEGER;
    templates_count INTEGER;
    rules_count INTEGER;
    jobs_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO channels_count FROM monitoring.notification_channels;
    SELECT COUNT(*) INTO templates_count FROM monitoring.notification_templates;
    SELECT COUNT(*) INTO rules_count FROM monitoring.alert_escalation_rules;
    SELECT COUNT(*) INTO jobs_count FROM cron.job WHERE jobname LIKE '%notification%' OR jobname LIKE '%escalation%';
    
    RAISE NOTICE '=== CONFIGURACIÓN INICIAL DE ALERTAS COMPLETADA ===';
    RAISE NOTICE 'Canales configurados: %', channels_count;
    RAISE NOTICE 'Plantillas creadas: %', templates_count;
    RAISE NOTICE 'Reglas de escalamiento: %', rules_count;
    RAISE NOTICE 'Trabajos automáticos: %', jobs_count;
    RAISE NOTICE '';
    RAISE NOTICE 'CONFIGURACIÓN INCLUYE:';
    RAISE NOTICE '  • Email: admin_email, oncall_email';
    RAISE NOTICE '  • Slack: dev_team_slack, critical_slack';
    RAISE NOTICE '  • SMS: emergency_sms';
    RAISE NOTICE '  • Webhook: external_webhook';
    RAISE NOTICE '';
    RAISE NOTICE 'PARA PROBAR:';
    RAISE NOTICE '  SELECT monitoring.send_test_notification(''admin_email'', ''Prueba del sistema'');';
    RAISE NOTICE '  SELECT monitoring.get_notification_stats(7);';
    RAISE NOTICE '';
    RAISE NOTICE 'PRÓXIMOS PASOS:';
    RAISE NOTICE '  1. Actualizar configuraciones con datos reales (emails, tokens, etc.)';
    RAISE NOTICE '  2. Configurar integraciones con proveedores externos';
    RAISE NOTICE '  3. Probar notificaciones en entorno de desarrollo';
    RAISE NOTICE '  4. Ajustar umbrales y plantillas según necesidades';
END $$;
