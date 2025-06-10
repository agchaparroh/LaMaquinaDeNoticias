-- =====================================================
-- SISTEMA DE ALERTAS AUTOMÁTICAS - COMPONENTES AVANZADOS
-- Archivo: 11_automated_alerts_system.sql
-- Descripción: Sistema completo de alertas automáticas con notificaciones
-- =====================================================

-- =====================================================
-- TABLA DE CONFIGURACIÓN DE NOTIFICACIONES
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.notification_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Configuración del canal
    channel_type TEXT NOT NULL CHECK (channel_type IN ('email', 'slack', 'sms', 'webhook')),
    channel_name TEXT NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    
    -- Configuración específica del canal
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Filtros para este canal
    severity_filter TEXT[] DEFAULT ARRAY['warning', 'critical'],
    category_filter TEXT[] DEFAULT ARRAY['system', 'database', 'supabase'],
    
    -- Control de frecuencia
    max_alerts_per_hour INTEGER DEFAULT 10,
    cooldown_minutes INTEGER DEFAULT 30,
    
    -- Estado
    last_notification_sent TIMESTAMPTZ,
    notifications_sent_today INTEGER DEFAULT 0,
    
    UNIQUE(channel_type, channel_name)
);

-- =====================================================
-- TABLA DE HISTORIAL DE NOTIFICACIONES
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.notification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Referencia a la alerta
    alert_id UUID NOT NULL REFERENCES monitoring.alerts(id),
    
    -- Información del canal
    channel_type TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    
    -- Estado de la notificación
    status TEXT NOT NULL CHECK (status IN ('sent', 'failed', 'skipped', 'throttled')),
    
    -- Detalles
    message_content TEXT,
    response_data JSONB,
    error_message TEXT,
    
    -- Métricas
    send_time_ms INTEGER,
    retry_count INTEGER DEFAULT 0
);

-- =====================================================
-- TABLA DE REGLAS ANTI-FLOOD
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.alert_flood_control (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Identificación de la regla
    metric_name TEXT NOT NULL,
    channel_type TEXT NOT NULL,
    
    -- Configuración anti-flood
    max_alerts_per_period INTEGER DEFAULT 3,
    period_minutes INTEGER DEFAULT 60,
    escalation_threshold INTEGER DEFAULT 5,
    
    -- Estado actual
    alerts_in_current_period INTEGER DEFAULT 0,
    period_start_time TIMESTAMPTZ DEFAULT NOW(),
    
    -- Escalación
    escalated BOOLEAN DEFAULT FALSE,
    escalated_at TIMESTAMPTZ,
    
    UNIQUE(metric_name, channel_type)
);

-- =====================================================
-- FUNCIÓN PRINCIPAL DE ENVÍO DE NOTIFICACIONES
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.send_alert_notifications(
    p_alert_id UUID
)
RETURNS INTEGER AS $$
DECLARE
    alert_rec RECORD;
    config_rec RECORD;
    notifications_sent INTEGER := 0;
    flood_check_result BOOLEAN;
    notification_id UUID;
    message_content TEXT;
    notification_start_time TIMESTAMPTZ;
BEGIN
    notification_start_time := clock_timestamp();
    
    -- Obtener información de la alerta
    SELECT * INTO alert_rec 
    FROM monitoring.alerts 
    WHERE id = p_alert_id;
    
    IF alert_rec IS NULL THEN
        RAISE NOTICE 'Alerta no encontrada: %', p_alert_id;
        RETURN 0;
    END IF;
    
    -- Construir contenido del mensaje
    message_content := format(
        'ALERTA %s: %s
        
Métrica: %s
Valor actual: %s
Umbral: %s
Timestamp: %s
        
Descripción: %s',
        UPPER(alert_rec.severity),
        alert_rec.title,
        alert_rec.metric_name,
        alert_rec.metric_value,
        alert_rec.threshold_value,
        alert_rec.timestamp,
        COALESCE(alert_rec.description, 'Sin descripción adicional')
    );
    
    -- Iterar sobre canales de notificación habilitados
    FOR config_rec IN
        SELECT * FROM monitoring.notification_config 
        WHERE enabled = TRUE 
        AND alert_rec.severity = ANY(severity_filter)
        AND EXISTS (
            SELECT 1 FROM monitoring.alert_thresholds at 
            WHERE at.metric_name = alert_rec.metric_name 
            AND at.category = ANY(config_rec.category_filter)
        )
    LOOP
        -- Verificar control de flood
        SELECT monitoring.check_flood_control(
            alert_rec.metric_name, 
            config_rec.channel_type
        ) INTO flood_check_result;
        
        IF NOT flood_check_result THEN
            -- Registrar notificación omitida por flood control
            INSERT INTO monitoring.notification_history (
                alert_id, channel_type, channel_name, status, 
                message_content, error_message
            ) VALUES (
                p_alert_id, config_rec.channel_type, config_rec.channel_name, 
                'throttled', message_content, 'Bloqueado por control anti-flood'
            );
            CONTINUE;
        END IF;
        
        -- Verificar cooldown del canal
        IF config_rec.last_notification_sent IS NOT NULL 
           AND config_rec.last_notification_sent > NOW() - INTERVAL '1 minute' * config_rec.cooldown_minutes THEN
            
            INSERT INTO monitoring.notification_history (
                alert_id, channel_type, channel_name, status, 
                message_content, error_message
            ) VALUES (
                p_alert_id, config_rec.channel_type, config_rec.channel_name, 
                'skipped', message_content, 'Canal en período de cooldown'
            );
            CONTINUE;
        END IF;
        
        -- Enviar notificación según el tipo de canal
        CASE config_rec.channel_type
            WHEN 'email' THEN
                PERFORM monitoring.send_email_notification(
                    p_alert_id, config_rec.id, message_content
                );
            WHEN 'slack' THEN
                PERFORM monitoring.send_slack_notification(
                    p_alert_id, config_rec.id, message_content
                );
            WHEN 'sms' THEN
                PERFORM monitoring.send_sms_notification(
                    p_alert_id, config_rec.id, message_content
                );
            WHEN 'webhook' THEN
                PERFORM monitoring.send_webhook_notification(
                    p_alert_id, config_rec.id, message_content
                );
            ELSE
                RAISE NOTICE 'Tipo de canal no reconocido: %', config_rec.channel_type;
                CONTINUE;
        END CASE;
        
        -- Actualizar estado del canal
        UPDATE monitoring.notification_config SET
            last_notification_sent = NOW(),
            notifications_sent_today = notifications_sent_today + 1,
            updated_at = NOW()
        WHERE id = config_rec.id;
        
        notifications_sent := notifications_sent + 1;
    END LOOP;
    
    -- Actualizar alerta con información de notificación
    UPDATE monitoring.alerts SET
        notification_sent = CASE WHEN notifications_sent > 0 THEN TRUE ELSE FALSE END,
        notification_sent_at = CASE WHEN notifications_sent > 0 THEN NOW() ELSE NULL END
    WHERE id = p_alert_id;
    
    RETURN notifications_sent;
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error enviando notificaciones para alerta %: %', p_alert_id, SQLERRM;
    RETURN 0;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN DE CONTROL ANTI-FLOOD
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.check_flood_control(
    p_metric_name TEXT,
    p_channel_type TEXT
)
RETURNS BOOLEAN AS $$
DECLARE
    control_rec RECORD;
    current_time TIMESTAMPTZ := NOW();
BEGIN
    -- Obtener o crear registro de control
    SELECT * INTO control_rec 
    FROM monitoring.alert_flood_control 
    WHERE metric_name = p_metric_name 
    AND channel_type = p_channel_type;
    
    IF control_rec IS NULL THEN
        -- Crear nuevo registro de control
        INSERT INTO monitoring.alert_flood_control (
            metric_name, channel_type, alerts_in_current_period, period_start_time
        ) VALUES (
            p_metric_name, p_channel_type, 1, current_time
        );
        RETURN TRUE;
    END IF;
    
    -- Verificar si el período actual ha expirado
    IF current_time > control_rec.period_start_time + INTERVAL '1 minute' * control_rec.period_minutes THEN
        -- Reiniciar contador para nuevo período
        UPDATE monitoring.alert_flood_control SET
            alerts_in_current_period = 1,
            period_start_time = current_time,
            escalated = FALSE,
            escalated_at = NULL
        WHERE id = control_rec.id;
        RETURN TRUE;
    END IF;
    
    -- Verificar si se ha alcanzado el límite
    IF control_rec.alerts_in_current_period >= control_rec.max_alerts_per_period THEN
        -- Verificar escalación
        IF control_rec.alerts_in_current_period >= control_rec.escalation_threshold 
           AND NOT control_rec.escalated THEN
            -- Escalar a canal crítico
            UPDATE monitoring.alert_flood_control SET
                escalated = TRUE,
                escalated_at = current_time
            WHERE id = control_rec.id;
            
            -- Enviar alerta de escalación
            PERFORM monitoring.create_escalation_alert(p_metric_name, p_channel_type);
        END IF;
        
        RETURN FALSE;
    END IF;
    
    -- Incrementar contador
    UPDATE monitoring.alert_flood_control SET
        alerts_in_current_period = alerts_in_current_period + 1
    WHERE id = control_rec.id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIONES DE ENVÍO POR CANAL (SIMULADAS)
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.send_email_notification(
    p_alert_id UUID,
    p_config_id UUID,
    p_message TEXT
)
RETURNS VOID AS $$
DECLARE
    config_rec RECORD;
    notification_id UUID := gen_random_uuid();
    start_time TIMESTAMPTZ := clock_timestamp();
BEGIN
    SELECT * INTO config_rec 
    FROM monitoring.notification_config 
    WHERE id = p_config_id;
    
    -- SIMULACIÓN: En producción, aquí iría la integración con servicio de email
    -- Por ejemplo: SendGrid, AWS SES, Mailgun, etc.
    
    -- Registrar envío exitoso (simulado)
    INSERT INTO monitoring.notification_history (
        id, alert_id, channel_type, channel_name, status,
        message_content, response_data, send_time_ms
    ) VALUES (
        notification_id, p_alert_id, 'email', config_rec.channel_name, 'sent',
        p_message, 
        jsonb_build_object(
            'to', config_rec.config->>'email_address',
            'subject', 'Alerta del Sistema de Monitoreo',
            'provider', 'simulated'
        ),
        EXTRACT(milliseconds FROM (clock_timestamp() - start_time))::INTEGER
    );
    
    RAISE NOTICE 'Email enviado a: % (simulado)', config_rec.config->>'email_address';
    
EXCEPTION WHEN OTHERS THEN
    -- Registrar fallo
    INSERT INTO monitoring.notification_history (
        alert_id, channel_type, channel_name, status,
        message_content, error_message
    ) VALUES (
        p_alert_id, 'email', config_rec.channel_name, 'failed',
        p_message, SQLERRM
    );
    RAISE;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION monitoring.send_slack_notification(
    p_alert_id UUID,
    p_config_id UUID,
    p_message TEXT
)
RETURNS VOID AS $$
DECLARE
    config_rec RECORD;
    notification_id UUID := gen_random_uuid();
    start_time TIMESTAMPTZ := clock_timestamp();
BEGIN
    SELECT * INTO config_rec 
    FROM monitoring.notification_config 
    WHERE id = p_config_id;
    
    -- SIMULACIÓN: En producción, aquí iría la integración con Slack API
    -- Webhook URL, Bot Token, etc.
    
    INSERT INTO monitoring.notification_history (
        id, alert_id, channel_type, channel_name, status,
        message_content, response_data, send_time_ms
    ) VALUES (
        notification_id, p_alert_id, 'slack', config_rec.channel_name, 'sent',
        p_message,
        jsonb_build_object(
            'channel', config_rec.config->>'channel',
            'webhook_url', config_rec.config->>'webhook_url',
            'provider', 'simulated'
        ),
        EXTRACT(milliseconds FROM (clock_timestamp() - start_time))::INTEGER
    );
    
    RAISE NOTICE 'Slack enviado a canal: % (simulado)', config_rec.config->>'channel';
    
EXCEPTION WHEN OTHERS THEN
    INSERT INTO monitoring.notification_history (
        alert_id, channel_type, channel_name, status,
        message_content, error_message
    ) VALUES (
        p_alert_id, 'slack', config_rec.channel_name, 'failed',
        p_message, SQLERRM
    );
    RAISE;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION monitoring.send_sms_notification(
    p_alert_id UUID,
    p_config_id UUID,
    p_message TEXT
)
RETURNS VOID AS $$
DECLARE
    config_rec RECORD;
    notification_id UUID := gen_random_uuid();
    start_time TIMESTAMPTZ := clock_timestamp();
    sms_message TEXT;
BEGIN
    SELECT * INTO config_rec 
    FROM monitoring.notification_config 
    WHERE id = p_config_id;
    
    -- Acortar mensaje para SMS (máximo 160 caracteres)
    sms_message := LEFT(p_message, 160);
    
    -- SIMULACIÓN: En producción, aquí iría la integración con servicio SMS
    -- Twilio, AWS SNS, etc.
    
    INSERT INTO monitoring.notification_history (
        id, alert_id, channel_type, channel_name, status,
        message_content, response_data, send_time_ms
    ) VALUES (
        notification_id, p_alert_id, 'sms', config_rec.channel_name, 'sent',
        sms_message,
        jsonb_build_object(
            'phone_number', config_rec.config->>'phone_number',
            'provider', 'simulated'
        ),
        EXTRACT(milliseconds FROM (clock_timestamp() - start_time))::INTEGER
    );
    
    RAISE NOTICE 'SMS enviado a: % (simulado)', config_rec.config->>'phone_number';
    
EXCEPTION WHEN OTHERS THEN
    INSERT INTO monitoring.notification_history (
        alert_id, channel_type, channel_name, status,
        message_content, error_message
    ) VALUES (
        p_alert_id, 'sms', config_rec.channel_name, 'failed',
        sms_message, SQLERRM
    );
    RAISE;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION monitoring.send_webhook_notification(
    p_alert_id UUID,
    p_config_id UUID,
    p_message TEXT
)
RETURNS VOID AS $$
DECLARE
    config_rec RECORD;
    notification_id UUID := gen_random_uuid();
    start_time TIMESTAMPTZ := clock_timestamp();
    webhook_payload JSONB;
BEGIN
    SELECT * INTO config_rec 
    FROM monitoring.notification_config 
    WHERE id = p_config_id;
    
    -- Construir payload JSON para webhook
    webhook_payload := jsonb_build_object(
        'alert_id', p_alert_id,
        'message', p_message,
        'timestamp', NOW(),
        'source', 'monitoring_system'
    );
    
    -- SIMULACIÓN: En producción, aquí iría HTTP POST al webhook
    
    INSERT INTO monitoring.notification_history (
        id, alert_id, channel_type, channel_name, status,
        message_content, response_data, send_time_ms
    ) VALUES (
        notification_id, p_alert_id, 'webhook', config_rec.channel_name, 'sent',
        webhook_payload::TEXT,
        jsonb_build_object(
            'webhook_url', config_rec.config->>'webhook_url',
            'method', 'POST',
            'provider', 'simulated'
        ),
        EXTRACT(milliseconds FROM (clock_timestamp() - start_time))::INTEGER
    );
    
    RAISE NOTICE 'Webhook enviado a: % (simulado)', config_rec.config->>'webhook_url';
    
EXCEPTION WHEN OTHERS THEN
    INSERT INTO monitoring.notification_history (
        alert_id, channel_type, channel_name, status,
        message_content, error_message
    ) VALUES (
        p_alert_id, 'webhook', config_rec.channel_name, 'failed',
        webhook_payload::TEXT, SQLERRM
    );
    RAISE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA CREAR ALERTA DE ESCALACIÓN
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.create_escalation_alert(
    p_metric_name TEXT,
    p_channel_type TEXT
)
RETURNS UUID AS $$
DECLARE
    alert_id UUID := gen_random_uuid();
BEGIN
    INSERT INTO monitoring.alerts (
        id, timestamp, alert_type, severity, metric_name,
        title, description, status, notification_channels, created_by
    ) VALUES (
        alert_id, NOW(), 'flood_escalation', 'critical', p_metric_name,
        format('ESCALACIÓN: Demasiadas alertas para %s', p_metric_name),
        format('Se han generado demasiadas alertas para la métrica %s en el canal %s. Sistema en modo de supresión.',
               p_metric_name, p_channel_type),
        'active', ARRAY['email'], 'flood_control_system'
    );
    
    RETURN alert_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_notification_config_enabled 
ON monitoring.notification_config (enabled) WHERE enabled = TRUE;

CREATE INDEX IF NOT EXISTS idx_notification_history_alert_id 
ON monitoring.notification_history (alert_id);

CREATE INDEX IF NOT EXISTS idx_notification_history_timestamp 
ON monitoring.notification_history (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_flood_control_metric_channel 
ON monitoring.alert_flood_control (metric_name, channel_type);

-- =====================================================
-- CONFIGURACIÓN INICIAL DE CANALES
-- =====================================================

-- Canal de email por defecto
INSERT INTO monitoring.notification_config (
    channel_type, channel_name, config, severity_filter, max_alerts_per_hour
) VALUES (
    'email', 'admin_alerts', 
    jsonb_build_object(
        'email_address', 'admin@ejemplo.com',
        'smtp_server', 'smtp.ejemplo.com'
    ),
    ARRAY['warning', 'critical'], 15
) ON CONFLICT (channel_type, channel_name) DO NOTHING;

-- Canal de Slack para alertas críticas
INSERT INTO monitoring.notification_config (
    channel_type, channel_name, config, severity_filter, max_alerts_per_hour
) VALUES (
    'slack', 'critical_alerts', 
    jsonb_build_object(
        'webhook_url', 'https://hooks.slack.com/services/ejemplo',
        'channel', '#alertas-criticas'
    ),
    ARRAY['critical'], 10
) ON CONFLICT (channel_type, channel_name) DO NOTHING;

-- Canal de SMS para emergencias
INSERT INTO monitoring.notification_config (
    channel_type, channel_name, config, severity_filter, max_alerts_per_hour, cooldown_minutes
) VALUES (
    'sms', 'emergency', 
    jsonb_build_object(
        'phone_number', '+1234567890',
        'provider', 'twilio'
    ),
    ARRAY['critical'], 5, 60
) ON CONFLICT (channel_type, channel_name) DO NOTHING;

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON TABLE monitoring.notification_config IS 'Configuración de canales de notificación para alertas';
COMMENT ON TABLE monitoring.notification_history IS 'Historial de todas las notificaciones enviadas';
COMMENT ON TABLE monitoring.alert_flood_control IS 'Control anti-flood para prevenir exceso de alertas';

COMMENT ON FUNCTION monitoring.send_alert_notifications(UUID) IS 'Función principal para enviar notificaciones de alertas a todos los canales configurados';
COMMENT ON FUNCTION monitoring.check_flood_control(TEXT, TEXT) IS 'Verifica si una alerta debe ser suprimida por control anti-flood';

-- Verificación final
DO $$
BEGIN
    RAISE NOTICE 'Sistema de alertas automáticas implementado exitosamente';
    RAISE NOTICE 'Componentes: notificaciones multi-canal, control anti-flood, escalación';
    RAISE NOTICE 'Canales soportados: email, slack, sms, webhook';
    RAISE NOTICE 'Configuración inicial: 3 canales de ejemplo creados';
END $$;
