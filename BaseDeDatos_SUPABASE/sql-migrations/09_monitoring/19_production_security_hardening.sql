-- =====================================================
-- PREPARACIÓN PARA PRODUCCIÓN - SECURITY HARDENING
-- Archivo: 19_production_security_hardening.sql
-- Descripción: Configuraciones de seguridad para producción
-- =====================================================

-- =====================================================
-- CONFIGURACIÓN DE ROLES Y PERMISOS DE SEGURIDAD
-- =====================================================

-- Crear roles específicos para producción
DO $$
BEGIN
    -- Rol de solo lectura para monitoring
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'monitoring_reader') THEN
        CREATE ROLE monitoring_reader;
    END IF;
    
    -- Rol de operador para acciones básicas
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'monitoring_operator') THEN
        CREATE ROLE monitoring_operator;
    END IF;
    
    -- Rol de administrador para configuración
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'monitoring_admin') THEN
        CREATE ROLE monitoring_admin;
    END IF;
    
    -- Rol de servicio para aplicaciones
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'monitoring_service') THEN
        CREATE ROLE monitoring_service LOGIN;
    END IF;
    
    RAISE NOTICE 'Roles de seguridad creados exitosamente';
END $$;

-- =====================================================
-- ASIGNACIÓN DE PERMISOS POR ROL
-- =====================================================

-- MONITORING_READER: Solo lectura
GRANT USAGE ON SCHEMA monitoring TO monitoring_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA monitoring TO monitoring_reader;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA monitoring TO monitoring_reader;
GRANT EXECUTE ON FUNCTION monitoring.get_operational_status() TO monitoring_reader;
GRANT EXECUTE ON FUNCTION monitoring.get_system_status() TO monitoring_reader;

-- MONITORING_OPERATOR: Operaciones básicas
GRANT monitoring_reader TO monitoring_operator;
GRANT EXECUTE ON FUNCTION monitoring.collect_system_metrics() TO monitoring_operator;
GRANT EXECUTE ON FUNCTION monitoring.check_alert_thresholds_enhanced() TO monitoring_operator;
GRANT EXECUTE ON FUNCTION monitoring.perform_health_check() TO monitoring_operator;
GRANT EXECUTE ON FUNCTION monitoring.auto_resolve_alerts() TO monitoring_operator;

-- MONITORING_ADMIN: Configuración y administración
GRANT monitoring_operator TO monitoring_admin;
GRANT INSERT, UPDATE, DELETE ON monitoring.alert_thresholds TO monitoring_admin;
GRANT INSERT, UPDATE, DELETE ON monitoring.notification_config TO monitoring_admin;
GRANT INSERT, UPDATE, DELETE ON monitoring.supabase_alert_thresholds TO monitoring_admin;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA monitoring TO monitoring_admin;

-- MONITORING_SERVICE: Para aplicaciones automatizadas
GRANT monitoring_operator TO monitoring_service;
GRANT INSERT ON monitoring.system_metrics TO monitoring_service;
GRANT INSERT ON monitoring.alerts TO monitoring_service;
GRANT INSERT ON monitoring.notification_history TO monitoring_service;
GRANT UPDATE ON monitoring.alerts TO monitoring_service;

-- =====================================================
-- TABLA DE AUDITORÍA DE SEGURIDAD
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.security_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Información del evento
    event_type TEXT NOT NULL, -- 'login', 'permission_change', 'config_change', 'data_access'
    user_name TEXT NOT NULL,
    user_role TEXT,
    
    -- Detalles del evento
    action_performed TEXT NOT NULL,
    resource_accessed TEXT,
    ip_address INET,
    user_agent TEXT,
    
    -- Resultado
    success BOOLEAN NOT NULL,
    error_message TEXT,
    
    -- Contexto adicional
    session_id TEXT,
    additional_data JSONB DEFAULT '{}'::jsonb
);

-- =====================================================
-- FUNCIÓN DE AUDITORÍA AUTOMÁTICA
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.log_security_event(
    p_event_type TEXT,
    p_action TEXT,
    p_resource TEXT DEFAULT NULL,
    p_success BOOLEAN DEFAULT TRUE,
    p_error_message TEXT DEFAULT NULL,
    p_additional_data JSONB DEFAULT '{}'::jsonb
)
RETURNS UUID AS $$
DECLARE
    audit_id UUID := gen_random_uuid();
    current_user_name TEXT := current_user;
    current_user_role TEXT;
    client_ip INET;
BEGIN
    -- Obtener rol del usuario actual
    SELECT string_agg(rolname, ',') INTO current_user_role
    FROM pg_auth_members m
    JOIN pg_roles r ON m.roleid = r.oid
    WHERE m.member = (SELECT oid FROM pg_roles WHERE rolname = current_user_name);
    
    -- Intentar obtener IP del cliente (puede no estar disponible)
    BEGIN
        client_ip := inet_client_addr();
    EXCEPTION WHEN OTHERS THEN
        client_ip := NULL;
    END;
    
    -- Insertar evento de auditoría
    INSERT INTO monitoring.security_audit_log (
        id, timestamp, event_type, user_name, user_role,
        action_performed, resource_accessed, ip_address,
        success, error_message, additional_data
    ) VALUES (
        audit_id, NOW(), p_event_type, current_user_name, current_user_role,
        p_action, p_resource, client_ip,
        p_success, p_error_message, p_additional_data
    );
    
    -- Log crítico si es un evento de seguridad importante
    IF p_event_type IN ('permission_change', 'config_change') OR NOT p_success THEN
        RAISE NOTICE 'SECURITY EVENT: % - % by % (Success: %)', 
            p_event_type, p_action, current_user_name, p_success;
    END IF;
    
    RETURN audit_id;
    
EXCEPTION WHEN OTHERS THEN
    -- En caso de error en auditoría, registrar en logs de PostgreSQL
    RAISE WARNING 'Error logging security event: %', SQLERRM;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- TRIGGERS DE AUDITORÍA AUTOMÁTICA
-- =====================================================

-- Trigger para cambios en configuración de alertas
CREATE OR REPLACE FUNCTION monitoring.audit_alert_config_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        PERFORM monitoring.log_security_event(
            'config_change',
            'Modified alert threshold: ' || NEW.metric_name,
            'alert_thresholds',
            TRUE,
            NULL,
            jsonb_build_object(
                'old_warning', OLD.warning_threshold,
                'new_warning', NEW.warning_threshold,
                'old_critical', OLD.critical_threshold,
                'new_critical', NEW.critical_threshold
            )
        );
    ELSIF TG_OP = 'INSERT' THEN
        PERFORM monitoring.log_security_event(
            'config_change',
            'Created alert threshold: ' || NEW.metric_name,
            'alert_thresholds'
        );
    ELSIF TG_OP = 'DELETE' THEN
        PERFORM monitoring.log_security_event(
            'config_change',
            'Deleted alert threshold: ' || OLD.metric_name,
            'alert_thresholds'
        );
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_audit_alert_thresholds
    AFTER INSERT OR UPDATE OR DELETE ON monitoring.alert_thresholds
    FOR EACH ROW EXECUTE FUNCTION monitoring.audit_alert_config_changes();

-- Trigger para cambios en configuración de notificaciones
CREATE OR REPLACE FUNCTION monitoring.audit_notification_config_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        PERFORM monitoring.log_security_event(
            'config_change',
            'Modified notification config: ' || NEW.channel_type || '/' || NEW.channel_name,
            'notification_config',
            TRUE,
            NULL,
            jsonb_build_object(
                'enabled_changed', OLD.enabled != NEW.enabled,
                'config_changed', OLD.config != NEW.config
            )
        );
    ELSIF TG_OP = 'INSERT' THEN
        PERFORM monitoring.log_security_event(
            'config_change',
            'Created notification config: ' || NEW.channel_type || '/' || NEW.channel_name,
            'notification_config'
        );
    ELSIF TG_OP = 'DELETE' THEN
        PERFORM monitoring.log_security_event(
            'config_change',
            'Deleted notification config: ' || OLD.channel_type || '/' || OLD.channel_name,
            'notification_config'
        );
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_audit_notification_config
    AFTER INSERT OR UPDATE OR DELETE ON monitoring.notification_config
    FOR EACH ROW EXECUTE FUNCTION monitoring.audit_notification_config_changes();

-- =====================================================
-- CONFIGURACIONES DE SEGURIDAD DE POSTGRESQL
-- =====================================================

-- Función para aplicar configuraciones de seguridad
CREATE OR REPLACE FUNCTION monitoring.apply_security_settings()
RETURNS TEXT AS $$
DECLARE
    settings_applied TEXT[] := ARRAY[]::TEXT[];
    current_setting_value TEXT;
BEGIN
    -- Log del inicio de aplicación de configuraciones
    PERFORM monitoring.log_security_event(
        'config_change',
        'Applying security settings',
        'postgresql_config'
    );
    
    -- Verificar configuraciones críticas de seguridad
    -- (Nota: En Supabase muchas están manejadas automáticamente)
    
    -- Verificar ssl
    SELECT setting INTO current_setting_value FROM pg_settings WHERE name = 'ssl';
    IF current_setting_value != 'on' THEN
        settings_applied := array_append(settings_applied, 
            'WARNING: SSL not enabled - should be handled by Supabase');
    ELSE
        settings_applied := array_append(settings_applied, 'SSL: enabled');
    END IF;
    
    -- Verificar log_statement (para auditoría)
    SELECT setting INTO current_setting_value FROM pg_settings WHERE name = 'log_statement';
    settings_applied := array_append(settings_applied, 
        'log_statement: ' || current_setting_value);
    
    -- Verificar shared_preload_libraries
    SELECT setting INTO current_setting_value FROM pg_settings WHERE name = 'shared_preload_libraries';
    settings_applied := array_append(settings_applied, 
        'shared_preload_libraries: ' || current_setting_value);
    
    -- Aplicar configuraciones específicas del esquema monitoring
    
    -- Revocar permisos públicos innecesarios
    REVOKE ALL ON SCHEMA monitoring FROM PUBLIC;
    REVOKE ALL ON ALL TABLES IN SCHEMA monitoring FROM PUBLIC;
    REVOKE ALL ON ALL FUNCTIONS IN SCHEMA monitoring FROM PUBLIC;
    settings_applied := array_append(settings_applied, 'Public permissions revoked');
    
    -- Configurar row level security en tablas sensibles
    ALTER TABLE monitoring.security_audit_log ENABLE ROW LEVEL SECURITY;
    
    -- Política para que solo admins puedan ver logs de auditoría
    DROP POLICY IF EXISTS audit_log_admin_policy ON monitoring.security_audit_log;
    CREATE POLICY audit_log_admin_policy ON monitoring.security_audit_log
        FOR ALL TO monitoring_admin
        USING (true);
    
    settings_applied := array_append(settings_applied, 'Row Level Security enabled');
    
    -- Log de finalización
    PERFORM monitoring.log_security_event(
        'config_change',
        'Security settings applied successfully',
        'postgresql_config',
        TRUE,
        NULL,
        jsonb_build_object('settings', settings_applied)
    );
    
    RETURN array_to_string(settings_applied, E'\n');
    
EXCEPTION WHEN OTHERS THEN
    PERFORM monitoring.log_security_event(
        'config_change',
        'Error applying security settings',
        'postgresql_config',
        FALSE,
        SQLERRM
    );
    RAISE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN DE VERIFICACIÓN DE SEGURIDAD
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.security_health_check()
RETURNS JSONB AS $$
DECLARE
    security_status JSONB := '{}'::jsonb;
    role_check JSONB;
    permission_check JSONB;
    audit_check JSONB;
    config_check JSONB;
    issues_found TEXT[] := ARRAY[]::TEXT[];
BEGIN
    -- Verificar roles de seguridad
    SELECT jsonb_build_object(
        'monitoring_reader_exists', EXISTS(SELECT 1 FROM pg_roles WHERE rolname = 'monitoring_reader'),
        'monitoring_operator_exists', EXISTS(SELECT 1 FROM pg_roles WHERE rolname = 'monitoring_operator'),
        'monitoring_admin_exists', EXISTS(SELECT 1 FROM pg_roles WHERE rolname = 'monitoring_admin'),
        'monitoring_service_exists', EXISTS(SELECT 1 FROM pg_roles WHERE rolname = 'monitoring_service')
    ) INTO role_check;
    
    -- Verificar permisos críticos
    SELECT jsonb_build_object(
        'public_schema_access', has_schema_privilege('public', 'monitoring', 'USAGE'),
        'reader_can_read', has_table_privilege('monitoring_reader', 'monitoring.system_metrics', 'SELECT'),
        'admin_can_configure', has_table_privilege('monitoring_admin', 'monitoring.alert_thresholds', 'UPDATE')
    ) INTO permission_check;
    
    -- Verificar sistema de auditoría
    SELECT jsonb_build_object(
        'audit_table_exists', EXISTS(SELECT 1 FROM information_schema.tables 
                                   WHERE table_schema = 'monitoring' 
                                   AND table_name = 'security_audit_log'),
        'audit_triggers_active', (SELECT COUNT(*) FROM information_schema.triggers 
                                WHERE trigger_schema = 'monitoring' 
                                AND trigger_name LIKE 'trigger_audit_%'),
        'recent_audit_entries', (SELECT COUNT(*) FROM monitoring.security_audit_log 
                               WHERE timestamp > NOW() - INTERVAL '24 hours')
    ) INTO audit_check;
    
    -- Verificar configuraciones de seguridad
    SELECT jsonb_build_object(
        'ssl_enabled', (SELECT setting = 'on' FROM pg_settings WHERE name = 'ssl'),
        'rls_enabled_audit', (SELECT relrowsecurity FROM pg_class 
                             WHERE relname = 'security_audit_log' 
                             AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'monitoring'))
    ) INTO config_check;
    
    -- Identificar problemas
    IF NOT (role_check->>'monitoring_reader_exists')::boolean THEN
        issues_found := array_append(issues_found, 'Missing monitoring_reader role');
    END IF;
    
    IF (permission_check->>'public_schema_access')::boolean THEN
        issues_found := array_append(issues_found, 'Public has access to monitoring schema');
    END IF;
    
    IF (audit_check->>'audit_triggers_active')::integer < 2 THEN
        issues_found := array_append(issues_found, 'Audit triggers not properly configured');
    END IF;
    
    IF NOT (config_check->>'ssl_enabled')::boolean THEN
        issues_found := array_append(issues_found, 'SSL not enabled');
    END IF;
    
    -- Construir resultado final
    security_status := jsonb_build_object(
        'timestamp', NOW(),
        'overall_status', CASE 
            WHEN array_length(issues_found, 1) IS NULL THEN 'secure'
            WHEN array_length(issues_found, 1) <= 2 THEN 'warning'
            ELSE 'critical'
        END,
        'checks', jsonb_build_object(
            'roles', role_check,
            'permissions', permission_check,
            'audit_system', audit_check,
            'configuration', config_check
        ),
        'issues_found', issues_found,
        'recommendations', CASE 
            WHEN array_length(issues_found, 1) IS NULL THEN 
                ARRAY['Security configuration is optimal']
            ELSE 
                ARRAY['Address identified security issues', 'Review security policies regularly']
        END
    );
    
    -- Log del security check
    PERFORM monitoring.log_security_event(
        'security_check',
        'Security health check performed',
        'system_security',
        TRUE,
        NULL,
        security_status
    );
    
    RETURN security_status;
    
EXCEPTION WHEN OTHERS THEN
    PERFORM monitoring.log_security_event(
        'security_check',
        'Error during security health check',
        'system_security',
        FALSE,
        SQLERRM
    );
    RAISE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- CONFIGURACIÓN DE RATE LIMITING PARA SEGURIDAD
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.rate_limiting (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_identifier TEXT NOT NULL, -- username, IP, etc.
    resource_type TEXT NOT NULL, -- 'api_calls', 'login_attempts', etc.
    window_start TIMESTAMPTZ NOT NULL,
    request_count INTEGER NOT NULL DEFAULT 1,
    
    -- Configuración
    max_requests INTEGER NOT NULL DEFAULT 100,
    window_minutes INTEGER NOT NULL DEFAULT 60,
    
    -- Estado
    blocked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(user_identifier, resource_type, window_start)
);

-- Función de rate limiting
CREATE OR REPLACE FUNCTION monitoring.check_rate_limit(
    p_user_identifier TEXT,
    p_resource_type TEXT,
    p_max_requests INTEGER DEFAULT 100,
    p_window_minutes INTEGER DEFAULT 60
)
RETURNS BOOLEAN AS $$
DECLARE
    current_window TIMESTAMPTZ;
    current_count INTEGER;
    is_blocked BOOLEAN := FALSE;
BEGIN
    current_window := date_trunc('hour', NOW()) + 
                     ((EXTRACT(MINUTE FROM NOW())::integer / p_window_minutes) * p_window_minutes || ' minutes')::INTERVAL;
    
    -- Verificar si está bloqueado
    IF EXISTS (
        SELECT 1 FROM monitoring.rate_limiting 
        WHERE user_identifier = p_user_identifier 
        AND resource_type = p_resource_type
        AND blocked_until > NOW()
    ) THEN
        RETURN FALSE;
    END IF;
    
    -- Insertar o actualizar contador
    INSERT INTO monitoring.rate_limiting (
        user_identifier, resource_type, window_start, request_count, 
        max_requests, window_minutes
    ) VALUES (
        p_user_identifier, p_resource_type, current_window, 1,
        p_max_requests, p_window_minutes
    )
    ON CONFLICT (user_identifier, resource_type, window_start)
    DO UPDATE SET 
        request_count = monitoring.rate_limiting.request_count + 1;
    
    -- Verificar límite
    SELECT request_count INTO current_count
    FROM monitoring.rate_limiting
    WHERE user_identifier = p_user_identifier 
    AND resource_type = p_resource_type 
    AND window_start = current_window;
    
    IF current_count > p_max_requests THEN
        -- Bloquear por el resto de la ventana
        UPDATE monitoring.rate_limiting 
        SET blocked_until = current_window + (p_window_minutes || ' minutes')::INTERVAL
        WHERE user_identifier = p_user_identifier 
        AND resource_type = p_resource_type 
        AND window_start = current_window;
        
        -- Log del bloqueo
        PERFORM monitoring.log_security_event(
            'rate_limit_exceeded',
            'User blocked for exceeding rate limit',
            p_resource_type,
            FALSE,
            format('Exceeded %s requests in %s minutes', p_max_requests, p_window_minutes),
            jsonb_build_object('user_identifier', p_user_identifier)
        );
        
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- ÍNDICES PARA SEGURIDAD Y RENDIMIENTO
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_security_audit_log_timestamp ON monitoring.security_audit_log (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_security_audit_log_user ON monitoring.security_audit_log (user_name, event_type);
CREATE INDEX IF NOT EXISTS idx_security_audit_log_event_type ON monitoring.security_audit_log (event_type, success);

CREATE INDEX IF NOT EXISTS idx_rate_limiting_user_resource ON monitoring.rate_limiting (user_identifier, resource_type);
CREATE INDEX IF NOT EXISTS idx_rate_limiting_window ON monitoring.rate_limiting (window_start);
CREATE INDEX IF NOT EXISTS idx_rate_limiting_blocked ON monitoring.rate_limiting (blocked_until) WHERE blocked_until IS NOT NULL;

-- =====================================================
-- APLICAR CONFIGURACIONES DE SEGURIDAD
-- =====================================================

-- Ejecutar configuraciones de seguridad
SELECT monitoring.apply_security_settings();

-- Ejecutar verificación inicial de seguridad
SELECT monitoring.security_health_check();

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON TABLE monitoring.security_audit_log IS 'Log de auditoría de seguridad para todas las acciones críticas';
COMMENT ON TABLE monitoring.rate_limiting IS 'Control de rate limiting para prevenir abuso del sistema';
COMMENT ON FUNCTION monitoring.log_security_event(TEXT,TEXT,TEXT,BOOLEAN,TEXT,JSONB) IS 'Registra eventos de seguridad en el log de auditoría';
COMMENT ON FUNCTION monitoring.security_health_check() IS 'Verifica el estado de seguridad del sistema';
COMMENT ON FUNCTION monitoring.check_rate_limit(TEXT,TEXT,INTEGER,INTEGER) IS 'Verifica y aplica límites de rate limiting';

-- Verificación final
DO $$
BEGIN
    RAISE NOTICE '=== SECURITY HARDENING APLICADO EXITOSAMENTE ===';
    RAISE NOTICE 'Roles de seguridad: 4 roles creados con permisos específicos';
    RAISE NOTICE 'Sistema de auditoría: Completo con triggers automáticos';
    RAISE NOTICE 'Rate limiting: Implementado para prevenir abuso';
    RAISE NOTICE 'Configuraciones de seguridad: Aplicadas según mejores prácticas';
    RAISE NOTICE 'Row Level Security: Habilitado en tablas sensibles';
    RAISE NOTICE '';
    RAISE NOTICE 'PRÓXIMO PASO: Configurar backups automáticos y optimizaciones finales';
END $$;
