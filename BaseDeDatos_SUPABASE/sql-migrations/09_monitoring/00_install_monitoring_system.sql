-- =====================================================
-- INSTALACIÓN COMPLETA DEL SISTEMA DE MONITOREO
-- Archivo: 00_install_monitoring_system.sql
-- Descripción: Script principal para instalar todo el sistema de monitoreo
-- =====================================================

-- Verificar prerrequisitos
DO $$
BEGIN
    RAISE NOTICE '=== VERIFICANDO PRERREQUISITOS ===';
    
    -- Verificar PostgreSQL versión
    IF current_setting('server_version_num')::integer < 120000 THEN
        RAISE EXCEPTION 'Se requiere PostgreSQL 12.0 o superior. Versión actual: %', version();
    END IF;
    RAISE NOTICE 'PostgreSQL versión: % ✓', version();
    
    -- Verificar extensiones requeridas
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
        RAISE EXCEPTION 'La extensión pg_cron no está instalada. Instálala primero con: CREATE EXTENSION pg_cron;';
    END IF;
    RAISE NOTICE 'Extensión pg_cron: ✓';
    
    -- Verificar permisos
    IF NOT has_schema_privilege(current_user, 'public', 'CREATE') THEN
        RAISE EXCEPTION 'El usuario actual no tiene permisos para crear esquemas';
    END IF;
    RAISE NOTICE 'Permisos de usuario: ✓';
    
    RAISE NOTICE 'Todos los prerrequisitos cumplidos. Iniciando instalación...';
    RAISE NOTICE '';
END $$;

-- =====================================================
-- PASO 1: CREAR TABLAS Y ESTRUCTURA BASE
-- =====================================================

\echo '=== PASO 1: CREANDO TABLAS Y ESTRUCTURA BASE ==='

-- Crear esquema específico para monitoreo si no existe
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Crear tablas principales
\i '01_create_monitoring_tables.sql'

-- Verificar creación de tablas
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables 
    WHERE table_schema = 'monitoring'
    AND table_type = 'BASE TABLE';
    
    RAISE NOTICE 'Tablas creadas en esquema monitoring: %', table_count;
    
    IF table_count < 4 THEN
        RAISE EXCEPTION 'Error: No se crearon todas las tablas necesarias';
    END IF;
END $$;

-- =====================================================
-- PASO 2: CREAR FUNCIONES DE RECOLECCIÓN
-- =====================================================

\echo '=== PASO 2: CREANDO FUNCIONES DE RECOLECCIÓN ==='

\i '02_monitoring_collection_functions.sql'

-- Verificar creación de funciones
DO $$
DECLARE
    function_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO function_count
    FROM information_schema.routines 
    WHERE routine_schema = 'monitoring'
    AND routine_type = 'FUNCTION';
    
    RAISE NOTICE 'Funciones creadas en esquema monitoring: %', function_count;
    
    IF function_count < 5 THEN
        RAISE EXCEPTION 'Error: No se crearon todas las funciones necesarias';
    END IF;
END $$;

-- =====================================================
-- PASO 3: CONFIGURAR AUTOMATIZACIÓN
-- =====================================================

\echo '=== PASO 3: CONFIGURANDO AUTOMATIZACIÓN CON PG_CRON ==='

\i '03_setup_monitoring_automation.sql'

-- Verificar trabajos de pg_cron
DO $$
DECLARE
    jobs_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO jobs_count
    FROM cron.job 
    WHERE jobname LIKE '%monitoring%' OR jobname LIKE '%system%' OR jobname LIKE '%cleanup%';
    
    RAISE NOTICE 'Trabajos de pg_cron configurados: %', jobs_count;
    
    IF jobs_count < 3 THEN
        RAISE WARNING 'Advertencia: Algunos trabajos de automatización pueden no haberse creado correctamente';
    END IF;
END $$;

-- =====================================================
-- PASO 4: CREAR VISTAS Y REPORTES
-- =====================================================

\echo '=== PASO 4: CREANDO VISTAS Y REPORTES ==='

\i '04_monitoring_views_and_reports.sql'

-- Verificar creación de vistas
DO $$
DECLARE
    view_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO view_count
    FROM information_schema.views 
    WHERE table_schema = 'monitoring';
    
    RAISE NOTICE 'Vistas creadas en esquema monitoring: %', view_count;
    
    IF view_count < 6 THEN
        RAISE WARNING 'Advertencia: Algunas vistas pueden no haberse creado correctamente';
    END IF;
END $$;

-- =====================================================
-- PASO 5: CONFIGURACIÓN INICIAL Y PRUEBAS
-- =====================================================

\echo '=== PASO 5: CONFIGURACIÓN INICIAL Y PRUEBAS ==='

-- Insertar configuraciones adicionales si no existen
INSERT INTO monitoring.system_config (key, value, description) VALUES
    ('installation_date', NOW()::TEXT, 'Fecha de instalación del sistema de monitoreo'),
    ('version', '1.0.0', 'Versión del sistema de monitoreo'),
    ('installed_by', current_user, 'Usuario que instaló el sistema'),
    ('environment', 'production', 'Ambiente donde está instalado (development/staging/production)')
ON CONFLICT (key) DO NOTHING;

-- Ejecutar primera recolección de métricas para verificar funcionamiento
DO $$
DECLARE
    job_id UUID;
    test_result JSONB;
BEGIN
    RAISE NOTICE 'Ejecutando primera recolección de métricas de prueba...';
    
    SELECT monitoring.collect_system_metrics() INTO job_id;
    
    IF job_id IS NOT NULL THEN
        RAISE NOTICE 'Primera recolección exitosa. Job ID: %', job_id;
        
        -- Verificar que se insertaron datos
        IF EXISTS (SELECT 1 FROM monitoring.system_metrics WHERE timestamp > NOW() - INTERVAL '1 minute') THEN
            RAISE NOTICE 'Datos de métricas verificados ✓';
        ELSE
            RAISE WARNING 'No se encontraron datos de métricas recientes';
        END IF;
        
        -- Probar función de dashboard
        SELECT monitoring.get_dashboard_metrics() INTO test_result;
        IF test_result IS NOT NULL THEN
            RAISE NOTICE 'Función de dashboard funcionando ✓';
        END IF;
        
    ELSE
        RAISE WARNING 'La primera recolección no devolvió un job_id válido';
    END IF;
    
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'Error en la primera recolección: %', SQLERRM;
END $$;

-- =====================================================
-- PASO 6: OTORGAR PERMISOS
-- =====================================================

\echo '=== PASO 6: CONFIGURANDO PERMISOS ==='

-- Otorgar permisos de lectura a rol de aplicación (si existe)
DO $$
BEGIN
    -- Verificar si existe un rol común de aplicación
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname IN ('app_user', 'readonly', 'supabase_read_only_user')) THEN
        -- Otorgar permisos de lectura en esquema monitoring
        EXECUTE format('GRANT USAGE ON SCHEMA monitoring TO %I', 
            (SELECT rolname FROM pg_roles WHERE rolname IN ('app_user', 'readonly', 'supabase_read_only_user') LIMIT 1));
        
        EXECUTE format('GRANT SELECT ON ALL TABLES IN SCHEMA monitoring TO %I', 
            (SELECT rolname FROM pg_roles WHERE rolname IN ('app_user', 'readonly', 'supabase_read_only_user') LIMIT 1));
        
        EXECUTE format('GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA monitoring TO %I', 
            (SELECT rolname FROM pg_roles WHERE rolname IN ('app_user', 'readonly', 'supabase_read_only_user') LIMIT 1));
        
        RAISE NOTICE 'Permisos otorgados a rol de aplicación';
    ELSE
        RAISE NOTICE 'No se encontró rol de aplicación estándar. Otorga permisos manualmente si es necesario.';
    END IF;
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error otorgando permisos: %. Configura permisos manualmente.', SQLERRM;
END $$;

-- =====================================================
-- VERIFICACIÓN FINAL Y REPORTE DE INSTALACIÓN
-- =====================================================

\echo '=== VERIFICACIÓN FINAL E INFORMACIÓN DEL SISTEMA ==='

DO $$
DECLARE
    installation_report JSONB;
    table_count INTEGER;
    function_count INTEGER;
    view_count INTEGER;
    jobs_count INTEGER;
    config_count INTEGER;
    latest_metrics RECORD;
BEGIN
    -- Contar objetos creados
    SELECT COUNT(*) INTO table_count FROM information_schema.tables WHERE table_schema = 'monitoring' AND table_type = 'BASE TABLE';
    SELECT COUNT(*) INTO function_count FROM information_schema.routines WHERE routine_schema = 'monitoring' AND routine_type = 'FUNCTION';
    SELECT COUNT(*) INTO view_count FROM information_schema.views WHERE table_schema = 'monitoring';
    SELECT COUNT(*) INTO jobs_count FROM cron.job WHERE jobname LIKE '%monitoring%' OR jobname LIKE '%system%' OR jobname LIKE '%cleanup%';
    SELECT COUNT(*) INTO config_count FROM monitoring.system_config;
    
    -- Obtener última métrica
    SELECT * INTO latest_metrics FROM monitoring.system_metrics ORDER BY timestamp DESC LIMIT 1;
    
    -- Crear reporte de instalación
    installation_report := jsonb_build_object(
        'installation_completed_at', NOW(),
        'database_version', version(),
        'objects_created', jsonb_build_object(
            'tables', table_count,
            'functions', function_count,
            'views', view_count,
            'cron_jobs', jobs_count,
            'configurations', config_count
        ),
        'first_metrics_collected', latest_metrics.timestamp IS NOT NULL,
        'system_ready', table_count >= 4 AND function_count >= 5 AND latest_metrics.timestamp IS NOT NULL
    );
    
    RAISE NOTICE '';
    RAISE NOTICE '==========================================';
    RAISE NOTICE '   INSTALACIÓN DEL SISTEMA DE MONITOREO  ';
    RAISE NOTICE '==========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'ESTADO: %', CASE WHEN (installation_report->>'system_ready')::boolean THEN 'COMPLETADO ✓' ELSE 'CON ERRORES ⚠' END;
    RAISE NOTICE '';
    RAISE NOTICE 'OBJETOS CREADOS:';
    RAISE NOTICE '  - Tablas: %', table_count;
    RAISE NOTICE '  - Funciones: %', function_count;
    RAISE NOTICE '  - Vistas: %', view_count;
    RAISE NOTICE '  - Trabajos pg_cron: %', jobs_count;
    RAISE NOTICE '  - Configuraciones: %', config_count;
    RAISE NOTICE '';
    RAISE NOTICE 'CARACTERÍSTICAS PRINCIPALES:';
    RAISE NOTICE '  - Recolección automática cada 5 minutos';
    RAISE NOTICE '  - Sistema de alertas configurado';
    RAISE NOTICE '  - Dashboard en tiempo real disponible';
    RAISE NOTICE '  - Limpieza automática de datos antiguos';
    RAISE NOTICE '  - Monitoreo de consultas lentas';
    RAISE NOTICE '  - Análisis de tendencias y rendimiento';
    RAISE NOTICE '';
    RAISE NOTICE 'COMANDOS ÚTILES:';
    RAISE NOTICE '  - Estado del sistema: SELECT monitoring.get_dashboard_metrics();';
    RAISE NOTICE '  - Reporte de salud: SELECT monitoring.generate_system_health_report(24);';
    RAISE NOTICE '  - Trabajos pg_cron: SELECT * FROM monitoring.get_cron_jobs_status();';
    RAISE NOTICE '  - Alertas activas: SELECT * FROM monitoring.active_alerts_dashboard;';
    RAISE NOTICE '  - Métricas recientes: SELECT * FROM monitoring.metrics_realtime LIMIT 10;';
    RAISE NOTICE '';
    RAISE NOTICE 'CONFIGURACIÓN:';
    RAISE NOTICE '  - Esquema: monitoring';
    RAISE NOTICE '  - Retención métricas: 30 días';
    RAISE NOTICE '  - Retención alertas: 90 días';
    RAISE NOTICE '  - Retención trabajos: 7 días';
    RAISE NOTICE '';
    
    IF (installation_report->>'system_ready')::boolean THEN
        RAISE NOTICE 'El sistema de monitoreo está LISTO y funcionando.';
        RAISE NOTICE 'Primera métrica recolectada: %', latest_metrics.timestamp;
    ELSE
        RAISE NOTICE 'ATENCIÓN: Revisa los errores anteriores antes de usar el sistema.';
    END IF;
    
    RAISE NOTICE '';
    RAISE NOTICE '==========================================';
    
    -- Guardar reporte en configuración
    INSERT INTO monitoring.system_config (key, value, description) 
    VALUES ('installation_report', installation_report::text, 'Reporte de instalación del sistema')
    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
    
END $$;

-- Mensaje final
\echo ''
\echo '✓ Instalación del Sistema de Monitoreo completada'
\echo ''
\echo 'Para verificar el estado del sistema ejecuta:'
\echo 'SELECT monitoring.get_dashboard_metrics();'
\echo ''
