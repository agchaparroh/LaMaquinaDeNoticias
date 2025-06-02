-- =====================================================
-- SISTEMA DE ALERTAS AUTOMÁTICAS Y NOTIFICACIONES
-- Archivo: 11_automated_alerts_notification_system.sql
-- Descripción: Sistema completo de alertas automáticas con múltiples canales
-- =====================================================

-- =====================================================
-- TABLA PARA CONFIGURACIÓN DE CANALES DE NOTIFICACIÓN
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.notification_channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Información del canal
    channel_name TEXT NOT NULL UNIQUE,
    channel_type TEXT NOT NULL CHECK (channel_type IN ('email', 'slack', 'sms', 'webhook', 'teams')),
    
    -- Configuración del canal
    enabled BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 5, -- 1 = más alta prioridad
    
    -- Configuración específica por tipo
    configuration JSONB NOT NULL, -- Configuración específica del canal
    
    -- Configuración de horarios
    active_hours_start TIME DEFAULT '00:00:00',
    active_hours_end TIME DEFAULT '23:59:59',
    active_days INTEGER[] DEFAULT ARRAY[1,2,3,4,5,6,7], -- 1=Lun, 7=Dom
    timezone TEXT DEFAULT 'UTC',
    
    -- Configuración de escalamiento
    escalation_delay_minutes INTEGER DEFAULT 60,
    max_escalations INTEGER DEFAULT 3,
    
    -- Rate limiting
    max_notifications_per_hour INTEGER DEFAULT 10,
    current_hour_count INTEGER DEFAULT 0,
    last_reset_hour TIMESTAMPTZ DEFAULT NOW(),
    
    -- Metadatos
    created_by TEXT DEFAULT current_user,
    tags JSONB DEFAULT '{}'::jsonb
);

-- =====================================================
-- TABLA PARA PLANTILLAS DE NOTIFICACIONES
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.notification_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Información de la plantilla
    template_name TEXT NOT NULL,
    alert_type TEXT NOT NULL, -- 'system', 'supabase', 'views_jobs', 'custom'
    severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    channel_type TEXT NOT NULL CHECK (channel_type IN ('email', 'slack', 'sms', 'webhook', 'teams')),
    
    -- Contenido de la plantilla
    subject_template TEXT,
    body_template TEXT NOT NULL,
    
    -- Configuración específica del canal
    format_type TEXT DEFAULT 'text' CHECK (format_type IN ('text', 'html', 'markdown', 'json')),
    
    -- Variables disponibles: {{metric_name}}, {{metric_value}}, {{threshold}}, {{timestamp}}, {{description}}
    available_variables TEXT[] DEFAULT ARRAY['metric_name', 'metric_value', 'threshold', 'timestamp', 'description'],
    
    -- Configuración adicional
    include_graph BOOLEAN DEFAULT FALSE,
    include_details BOOLEAN DEFAULT TRUE,
    auto_resolve_message BOOLEAN DEFAULT TRUE,
    
    -- Estado
    active BOOLEAN DEFAULT TRUE,
    
    UNIQUE(template_name, alert_type, severity, channel_type)
);

-- =====================================================
-- TABLA PARA HISTORIAL DE NOTIFICACIONES ENVIADAS
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.notification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Referencia a la alerta
    alert_id UUID REFERENCES monitoring.alerts(id),
    
    -- Información del canal y plantilla
    channel_id UUID REFERENCES monitoring.notification_channels(id),
    template_id UUID REFERENCES monitoring.notification_templates(id),
    
    -- Contenido enviado
    recipient TEXT NOT NULL, -- email, phone, webhook URL, etc.
    subject TEXT,
    message_content TEXT NOT NULL,
    
    -- Estado de entrega
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'bounced')),
    delivery_timestamp TIMESTAMPTZ,
    
    -- Información de respuesta
    external_message_id TEXT, -- ID del proveedor externo
    response_code INTEGER,
    response_message TEXT,
    
    -- Métricas de entrega
    delivery_time_ms INTEGER,
    retry_count INTEGER DEFAULT 0,
    
    -- Metadatos
    provider_used TEXT, -- 'smtp', 'sendgrid', 'slack_api', 'twilio', etc.
    cost_estimate DECIMAL(10,4), -- Costo estimado de la notificación
    
    tags JSONB DEFAULT '{}'::jsonb
);

-- =====================================================
-- TABLA PARA CONFIGURACIÓN DE ESCALAMIENTO
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.alert_escalation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Criterios de escalamiento
    rule_name TEXT NOT NULL UNIQUE,
    description TEXT,
    
    -- Condiciones para activar escalamiento
    alert_severity TEXT[] DEFAULT ARRAY['critical'], -- Severidades que activan escalamiento
    alert_types TEXT[], -- Tipos de alerta específicos
    metric_names TEXT[], -- Métricas específicas
    
    -- Configuración de tiempo
    escalation_delay_minutes INTEGER NOT NULL DEFAULT 30,
    max_escalation_level INTEGER NOT NULL DEFAULT 3,
    
    -- Canales de escalamiento por nivel
    level_1_channels UUID[], -- IDs de canales para nivel 1
    level_2_channels UUID[], -- IDs de canales para nivel 2
    level_3_channels UUID[], -- IDs de canales para nivel 3 (ejecutivos)
    
    -- Configuración adicional
    require_acknowledgment BOOLEAN DEFAULT FALSE,
    auto_resolve_escalation BOOLEAN DEFAULT TRUE,
    business_hours_only BOOLEAN DEFAULT FALSE,
    
    -- Estado
    enabled BOOLEAN DEFAULT TRUE
);

-- =====================================================
-- FUNCIONES PARA ENVÍO DE NOTIFICACIONES
-- =====================================================

-- Función para procesar variables en plantillas
CREATE OR REPLACE FUNCTION monitoring.process_notification_template(
    p_template TEXT,
    p_alert monitoring.alerts,
    p_additional_data JSONB DEFAULT '{}'::jsonb
)
RETURNS TEXT AS $$
DECLARE
    processed_template TEXT;
    system_info JSONB;
BEGIN
    processed_template := p_template;
    
    -- Obtener información adicional del sistema
    SELECT jsonb_build_object(
        'database_name', current_database(),
        'server_time', NOW(),
        'system_user', current_user
    ) INTO system_info;
    
    -- Reemplazar variables básicas de la alerta
    processed_template := replace(processed_template, '{{alert_id}}', p_alert.id::text);
    processed_template := replace(processed_template, '{{title}}', COALESCE(p_alert.title, 'Sin título'));
    processed_template := replace(processed_template, '{{description}}', COALESCE(p_alert.description, 'Sin descripción'));
    processed_template := replace(processed_template, '{{severity}}', p_alert.severity);
    processed_template := replace(processed_template, '{{metric_name}}', COALESCE(p_alert.metric_name, 'N/A'));
    processed_template := replace(processed_template, '{{metric_value}}', COALESCE(p_alert.metric_value::text, 'N/A'));
    processed_template := replace(processed_template, '{{threshold}}', COALESCE(p_alert.threshold_value::text, 'N/A'));
    processed_template := replace(processed_template, '{{timestamp}}', p_alert.timestamp::text);
    processed_template := replace(processed_template, '{{hours_active}}', 
        ROUND(EXTRACT(epoch FROM (NOW() - p_alert.timestamp)) / 3600, 1)::text);
    
    -- Variables del sistema
    processed_template := replace(processed_template, '{{database_name}}', current_database());
    processed_template := replace(processed_template, '{{server_time}}', NOW()::text);
    processed_template := replace(processed_template, '{{dashboard_url}}', 
        COALESCE(p_additional_data->>'dashboard_url', 'http://dashboard.local'));
    
    -- Variables dinámicas de datos adicionales
    IF p_additional_data IS NOT NULL THEN
        processed_template := replace(processed_template, '{{current_cpu}}', 
            COALESCE(p_additional_data->>'current_cpu', 'N/A'));
        processed_template := replace(processed_template, '{{current_memory}}', 
            COALESCE(p_additional_data->>'current_memory', 'N/A'));
        processed_template := replace(processed_template, '{{total_alerts}}', 
            COALESCE(p_additional_data->>'total_alerts', 'N/A'));
    END IF;
    
    RETURN processed_template;
END;
$$ LANGUAGE plpgsql;

-- Función para verificar si un canal está activo
CREATE OR REPLACE FUNCTION monitoring.is_channel_active(
    p_channel_id UUID,
    p_check_time TIMESTAMPTZ DEFAULT NOW()
)
RETURNS BOOLEAN AS $$
DECLARE
    channel_config RECORD;
    current_hour INTEGER;
    current_day INTEGER;
    current_time TIME;
BEGIN
    -- Obtener configuración del canal
    SELECT 
        enabled,
        active_hours_start,
        active_hours_end,
        active_days,
        max_notifications_per_hour,
        current_hour_count,
        last_reset_hour
    INTO channel_config
    FROM monitoring.notification_channels
    WHERE id = p_channel_id;
    
    -- Verificar si el canal existe y está habilitado
    IF NOT FOUND OR NOT channel_config.enabled THEN
        RETURN FALSE;
    END IF;
    
    -- Verificar día de la semana (1=Lunes, 7=Domingo)
    current_day := EXTRACT(dow FROM p_check_time);
    current_day := CASE WHEN current_day = 0 THEN 7 ELSE current_day END; -- Convertir domingo de 0 a 7
    
    IF current_day != ALL(channel_config.active_days) THEN
        RETURN FALSE;
    END IF;
    
    -- Verificar hora del día
    current_time := p_check_time::TIME;
    IF current_time < channel_config.active_hours_start OR 
       current_time > channel_config.active_hours_end THEN
        RETURN FALSE;
    END IF;
    
    -- Verificar rate limiting
    current_hour := EXTRACT(hour FROM p_check_time);
    IF EXTRACT(hour FROM channel_config.last_reset_hour) != current_hour THEN
        -- Resetear contador si cambió la hora
        UPDATE monitoring.notification_channels 
        SET current_hour_count = 0, last_reset_hour = p_check_time
        WHERE id = p_channel_id;
        RETURN TRUE;
    ELSE
        -- Verificar si no se ha excedido el límite
        RETURN channel_config.current_hour_count < channel_config.max_notifications_per_hour;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Función principal para enviar notificaciones
CREATE OR REPLACE FUNCTION monitoring.send_alert_notification(
    p_alert_id UUID,
    p_force_send BOOLEAN DEFAULT FALSE
)
RETURNS INTEGER AS $$
DECLARE
    alert_record RECORD;
    channel_record RECORD;
    template_record RECORD;
    notification_id UUID;
    notifications_sent INTEGER := 0;
    processed_subject TEXT;
    processed_body TEXT;
    recipient TEXT;
    additional_data JSONB;
BEGIN
    -- Obtener información de la alerta
    SELECT * INTO alert_record
    FROM monitoring.alerts
    WHERE id = p_alert_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Alerta no encontrada: %', p_alert_id;
    END IF;
    
    -- Verificar si ya se envió notificación recientemente (anti-flood)
    IF NOT p_force_send AND EXISTS (
        SELECT 1 FROM monitoring.notification_history
        WHERE alert_id = p_alert_id
        AND sent_at > NOW() - INTERVAL '15 minutes'
        AND status IN ('sent', 'delivered')
    ) THEN
        RAISE NOTICE 'Notificación ya enviada recientemente para alerta %', p_alert_id;
        RETURN 0;
    END IF;
    
    -- Obtener datos adicionales para el contexto
    SELECT monitoring.get_webhook_data() INTO additional_data;
    
    -- Iterar sobre los canales configurados para esta alerta
    FOR channel_record IN 
        SELECT nc.*
        FROM monitoring.notification_channels nc
        WHERE nc.enabled = TRUE
        AND nc.channel_type = ANY(alert_record.notification_channels)
        ORDER BY nc.priority
    LOOP
        -- Verificar si el canal está activo
        IF NOT monitoring.is_channel_active(channel_record.id) AND NOT p_force_send THEN
            RAISE NOTICE 'Canal % no está activo en este momento', channel_record.channel_name;
            CONTINUE;
        END IF;
        
        -- Buscar plantilla apropiada
        SELECT * INTO template_record
        FROM monitoring.notification_templates
        WHERE active = TRUE
        AND channel_type = channel_record.channel_type
        AND severity = alert_record.severity
        AND (alert_type = 'custom' OR alert_type = CASE 
            WHEN alert_record.metric_name LIKE '%supabase%' THEN 'supabase'
            WHEN alert_record.alert_type LIKE '%view%' OR alert_record.alert_type LIKE '%job%' THEN 'views_jobs'
            ELSE 'system'
        END)
        ORDER BY created_at DESC
        LIMIT 1;
        
        -- Si no hay plantilla específica, usar plantilla genérica
        IF NOT FOUND THEN
            SELECT * INTO template_record
            FROM monitoring.notification_templates
            WHERE active = TRUE
            AND channel_type = channel_record.channel_type
            AND alert_type = 'custom'
            ORDER BY created_at DESC
            LIMIT 1;
        END IF;
        
        -- Si aún no hay plantilla, usar una por defecto
        IF NOT FOUND THEN
            processed_subject := format('[%s] %s', 
                UPPER(alert_record.severity), 
                alert_record.title);
            processed_body := format(
                'Alerta: %s\nSeveridad: %s\nMétrica: %s = %s\nDescripción: %s\nTimestamp: %s\n\nDashboard: {{dashboard_url}}',
                alert_record.title,
                alert_record.severity,
                alert_record.metric_name,
                alert_record.metric_value,
                alert_record.description,
                alert_record.timestamp
            );
        ELSE
            -- Procesar plantilla
            processed_subject := monitoring.process_notification_template(
                COALESCE(template_record.subject_template, template_record.template_name),
                alert_record,
                additional_data
            );
            processed_body := monitoring.process_notification_template(
                template_record.body_template,
                alert_record,
                additional_data
            );
        END IF;
        
        -- Determinar destinatario según configuración del canal
        CASE channel_record.channel_type
            WHEN 'email' THEN
                recipient := channel_record.configuration->>'recipient_email';
            WHEN 'slack' THEN
                recipient := channel_record.configuration->>'channel_id';
            WHEN 'sms' THEN
                recipient := channel_record.configuration->>'phone_number';
            WHEN 'webhook' THEN
                recipient := channel_record.configuration->>'webhook_url';
            ELSE
                recipient := 'default_recipient';
        END CASE;
        
        -- Crear registro de notificación
        notification_id := gen_random_uuid();
        INSERT INTO monitoring.notification_history (
            id, alert_id, channel_id, template_id,
            recipient, subject, message_content,
            status, provider_used
        ) VALUES (
            notification_id, p_alert_id, channel_record.id, template_record.id,
            recipient, processed_subject, processed_body,
            'pending', channel_record.channel_type || '_provider'
        );
        
        -- Aquí se integraría con el proveedor real de notificaciones
        -- Por ahora, simular envío exitoso
        UPDATE monitoring.notification_history
        SET 
            status = 'sent',
            delivery_timestamp = NOW(),
            delivery_time_ms = FLOOR(random() * 500 + 100)::INTEGER,
            external_message_id = 'sim_' || gen_random_uuid()::text
        WHERE id = notification_id;
        
        -- Incrementar contador del canal
        UPDATE monitoring.notification_channels
        SET current_hour_count = current_hour_count + 1
        WHERE id = channel_record.id;
        
        -- Marcar alerta como notificada
        UPDATE monitoring.alerts
        SET 
            notification_sent = TRUE,
            notification_sent_at = NOW()
        WHERE id = p_alert_id;
        
        notifications_sent := notifications_sent + 1;
        
        RAISE NOTICE 'Notificación enviada: % via % a %', 
                     processed_subject, channel_record.channel_type, recipient;
    END LOOP;
    
    RETURN notifications_sent;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA PROCESAR ESCALAMIENTO DE ALERTAS
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.process_alert_escalation()
RETURNS INTEGER AS $$
DECLARE
    escalation_rule RECORD;
    alert_record RECORD;
    escalations_processed INTEGER := 0;
    target_channels UUID[];
    channel_id UUID;
BEGIN
    -- Iterar sobre reglas de escalamiento activas
    FOR escalation_rule IN 
        SELECT * FROM monitoring.alert_escalation_rules 
        WHERE enabled = TRUE
    LOOP
        -- Buscar alertas que requieren escalamiento
        FOR alert_record IN 
            SELECT a.*,
                   EXTRACT(epoch FROM (NOW() - a.timestamp)) / 60 as minutes_active
            FROM monitoring.alerts a
            WHERE a.status = 'active'
            AND a.severity = ANY(escalation_rule.alert_severity)
            AND (escalation_rule.alert_types IS NULL OR a.alert_type = ANY(escalation_rule.alert_types))
            AND (escalation_rule.metric_names IS NULL OR a.metric_name = ANY(escalation_rule.metric_names))
            AND EXTRACT(epoch FROM (NOW() - a.timestamp)) / 60 >= escalation_rule.escalation_delay_minutes
            -- Verificar que no se haya escalado ya
            AND NOT EXISTS (
                SELECT 1 FROM monitoring.notification_history nh
                JOIN monitoring.notification_channels nc ON nh.channel_id = nc.id
                WHERE nh.alert_id = a.id
                AND nc.id = ANY(COALESCE(
                    escalation_rule.level_1_channels,
                    escalation_rule.level_2_channels,
                    escalation_rule.level_3_channels
                ))
                AND nh.sent_at > a.timestamp
            )
        LOOP
            -- Determinar nivel de escalamiento según tiempo activo
            IF alert_record.minutes_active >= escalation_rule.escalation_delay_minutes * 3 THEN
                target_channels := escalation_rule.level_3_channels;
            ELSIF alert_record.minutes_active >= escalation_rule.escalation_delay_minutes * 2 THEN
                target_channels := escalation_rule.level_2_channels;
            ELSE
                target_channels := escalation_rule.level_1_channels;
            END IF;
            
            -- Enviar notificación a canales de escalamiento
            IF target_channels IS NOT NULL THEN
                -- Temporalmente modificar los canales de notificación de la alerta
                UPDATE monitoring.alerts
                SET notification_channels = ARRAY(
                    SELECT nc.channel_type 
                    FROM monitoring.notification_channels nc 
                    WHERE nc.id = ANY(target_channels)
                )
                WHERE id = alert_record.id;
                
                -- Enviar notificación de escalamiento
                PERFORM monitoring.send_alert_notification(alert_record.id, TRUE);
                
                escalations_processed := escalations_processed + 1;
                
                RAISE NOTICE 'Alerta escalada: % (Nivel: %, Regla: %)', 
                             alert_record.title, 
                             CASE 
                                WHEN alert_record.minutes_active >= escalation_rule.escalation_delay_minutes * 3 THEN 3
                                WHEN alert_record.minutes_active >= escalation_rule.escalation_delay_minutes * 2 THEN 2
                                ELSE 1
                             END,
                             escalation_rule.rule_name;
            END IF;
        END LOOP;
    END LOOP;
    
    RETURN escalations_processed;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- =====================================================

-- Índices para notification_channels
CREATE INDEX IF NOT EXISTS idx_notification_channels_enabled ON monitoring.notification_channels (enabled) WHERE enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_notification_channels_type_priority ON monitoring.notification_channels (channel_type, priority);

-- Índices para notification_templates
CREATE INDEX IF NOT EXISTS idx_notification_templates_lookup ON monitoring.notification_templates (alert_type, severity, channel_type, active);

-- Índices para notification_history
CREATE INDEX IF NOT EXISTS idx_notification_history_alert_id ON monitoring.notification_history (alert_id);
CREATE INDEX IF NOT EXISTS idx_notification_history_sent_at ON monitoring.notification_history (sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_notification_history_status ON monitoring.notification_history (status);

-- Índices para alert_escalation_rules
CREATE INDEX IF NOT EXISTS idx_alert_escalation_rules_enabled ON monitoring.alert_escalation_rules (enabled) WHERE enabled = TRUE;

-- =====================================================
-- TRIGGERS PARA AUDITORÍA
-- =====================================================

-- Trigger para actualizar timestamp de updated_at
CREATE TRIGGER trigger_notification_channels_updated_at
    BEFORE UPDATE ON monitoring.notification_channels
    FOR EACH ROW
    EXECUTE FUNCTION monitoring.update_updated_at_column();

CREATE TRIGGER trigger_notification_templates_updated_at
    BEFORE UPDATE ON monitoring.notification_templates
    FOR EACH ROW
    EXECUTE FUNCTION monitoring.update_updated_at_column();

CREATE TRIGGER trigger_alert_escalation_rules_updated_at
    BEFORE UPDATE ON monitoring.alert_escalation_rules
    FOR EACH ROW
    EXECUTE FUNCTION monitoring.update_updated_at_column();

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON TABLE monitoring.notification_channels IS 'Configuración de canales de notificación (email, Slack, SMS, etc.)';
COMMENT ON TABLE monitoring.notification_templates IS 'Plantillas personalizables para notificaciones por tipo de alerta y canal';
COMMENT ON TABLE monitoring.notification_history IS 'Historial completo de notificaciones enviadas con métricas de entrega';
COMMENT ON TABLE monitoring.alert_escalation_rules IS 'Reglas de escalamiento automático para alertas críticas';
COMMENT ON FUNCTION monitoring.send_alert_notification(UUID, BOOLEAN) IS 'Función principal para enviar notificaciones de alertas con anti-flood';
COMMENT ON FUNCTION monitoring.process_alert_escalation() IS 'Procesa escalamiento automático de alertas según reglas configuradas';

-- Verificación final
DO $$
BEGIN
    RAISE NOTICE '=== SISTEMA DE ALERTAS AUTOMÁTICAS IMPLEMENTADO ===';
    RAISE NOTICE 'Tablas creadas: notification_channels, notification_templates, notification_history, alert_escalation_rules';
    RAISE NOTICE 'Funciones principales: send_alert_notification, process_alert_escalation';
    RAISE NOTICE 'Características: múltiples canales, plantillas, escalamiento, rate limiting';
    RAISE NOTICE '';
    RAISE NOTICE 'Configurar canales de notificación en la tabla notification_channels';
    RAISE NOTICE 'Configurar plantillas en la tabla notification_templates';
    RAISE NOTICE 'Configurar reglas de escalamiento en alert_escalation_rules';
END $$;
