-- =====================================================
-- SISTEMA DE TESTING Y VALIDACIÓN COMPLETO
-- Archivo: 14_comprehensive_testing_and_validation.sql
-- Descripción: Testing integral del sistema de monitoreo
-- =====================================================

-- =====================================================
-- TABLA PARA REGISTRAR RESULTADOS DE TESTS
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_suite TEXT NOT NULL,
    test_name TEXT NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Resultado del test
    status TEXT NOT NULL CHECK (status IN ('passed', 'failed', 'warning', 'skipped')),
    execution_time_ms INTEGER,
    
    -- Detalles
    description TEXT,
    expected_result TEXT,
    actual_result TEXT,
    error_message TEXT,
    
    -- Métricas del test
    test_data JSONB DEFAULT '{}'::jsonb,
    
    -- Metadatos
    test_version TEXT DEFAULT '1.0',
    environment TEXT DEFAULT 'development'
);

-- =====================================================
-- FUNCIÓN PRINCIPAL DE TESTING INTEGRAL
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.run_comprehensive_tests()
RETURNS JSONB AS $$
DECLARE
    test_results JSONB := '{}'::jsonb;
    suite_results JSONB;
    overall_status TEXT := 'passed';
    total_tests INTEGER := 0;
    passed_tests INTEGER := 0;
    failed_tests INTEGER := 0;
    start_time TIMESTAMPTZ := NOW();
BEGIN
    RAISE NOTICE '=== INICIANDO TESTING INTEGRAL DEL SISTEMA DE MONITOREO ===';
    
    -- Limpiar resultados de tests anteriores
    DELETE FROM monitoring.test_results WHERE executed_at < NOW() - INTERVAL '1 hour';
    
    -- 1. TEST SUITE: Funciones Básicas
    RAISE NOTICE 'Ejecutando: Test Suite 1 - Funciones Básicas';
    SELECT monitoring.test_basic_functions() INTO suite_results;
    test_results := test_results || jsonb_build_object('basic_functions', suite_results);
    
    -- 2. TEST SUITE: Recolección de Métricas
    RAISE NOTICE 'Ejecutando: Test Suite 2 - Recolección de Métricas';
    SELECT monitoring.test_metrics_collection() INTO suite_results;
    test_results := test_results || jsonb_build_object('metrics_collection', suite_results);
    
    -- 3. TEST SUITE: Sistema de Alertas
    RAISE NOTICE 'Ejecutando: Test Suite 3 - Sistema de Alertas';
    SELECT monitoring.test_alert_system() INTO suite_results;
    test_results := test_results || jsonb_build_object('alert_system', suite_results);
    
    -- 4. TEST SUITE: Sistema de Notificaciones
    RAISE NOTICE 'Ejecutando: Test Suite 4 - Sistema de Notificaciones';
    SELECT monitoring.test_notification_system() INTO suite_results;
    test_results := test_results || jsonb_build_object('notification_system', suite_results);
    
    -- 5. TEST SUITE: Control Anti-Flood
    RAISE NOTICE 'Ejecutando: Test Suite 5 - Control Anti-Flood';
    SELECT monitoring.test_flood_control() INTO suite_results;
    test_results := test_results || jsonb_build_object('flood_control', suite_results);
    
    -- 6. TEST SUITE: Sistema de Reportes
    RAISE NOTICE 'Ejecutando: Test Suite 6 - Sistema de Reportes';
    SELECT monitoring.test_reporting_system() INTO suite_results;
    test_results := test_results || jsonb_build_object('reporting_system', suite_results);
    
    -- 7. TEST SUITE: Automatización pg_cron
    RAISE NOTICE 'Ejecutando: Test Suite 7 - Automatización';
    SELECT monitoring.test_automation_system() INTO suite_results;
    test_results := test_results || jsonb_build_object('automation_system', suite_results);
    
    -- 8. TEST SUITE: Rendimiento y Carga
    RAISE NOTICE 'Ejecutando: Test Suite 8 - Rendimiento';
    SELECT monitoring.test_performance() INTO suite_results;
    test_results := test_results || jsonb_build_object('performance', suite_results);
    
    -- Calcular estadísticas generales
    SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE status = 'passed') as passed,
        COUNT(*) FILTER (WHERE status = 'failed') as failed
    INTO total_tests, passed_tests, failed_tests
    FROM monitoring.test_results 
    WHERE executed_at >= start_time;
    
    -- Determinar estado general
    overall_status := CASE 
        WHEN failed_tests = 0 THEN 'passed'
        WHEN failed_tests <= total_tests * 0.1 THEN 'warning'
        ELSE 'failed'
    END;
    
    -- Construir resultado final
    test_results := test_results || jsonb_build_object(
        'summary', jsonb_build_object(
            'overall_status', overall_status,
            'total_tests', total_tests,
            'passed_tests', passed_tests,
            'failed_tests', failed_tests,
            'success_rate', ROUND(100.0 * passed_tests / GREATEST(total_tests, 1), 2),
            'execution_time_seconds', EXTRACT(EPOCH FROM (NOW() - start_time))::INTEGER,
            'executed_at', start_time
        )
    );
    
    RAISE NOTICE '=== TESTING COMPLETADO ===';
    RAISE NOTICE 'Estado General: %', overall_status;
    RAISE NOTICE 'Tests Ejecutados: % | Exitosos: % | Fallidos: %', total_tests, passed_tests, failed_tests;
    RAISE NOTICE 'Tasa de Éxito: %% | Tiempo Total: %s', 
        ROUND(100.0 * passed_tests / GREATEST(total_tests, 1), 2),
        EXTRACT(EPOCH FROM (NOW() - start_time))::INTEGER;
    
    RETURN test_results;
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'ERROR CRÍTICO en testing integral: %', SQLERRM;
    RETURN jsonb_build_object(
        'error', SQLERRM,
        'summary', jsonb_build_object('overall_status', 'error')
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TEST SUITE 1: FUNCIONES BÁSICAS
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.test_basic_functions()
RETURNS JSONB AS $$
DECLARE
    test_start_time TIMESTAMPTZ := NOW();
    test_result TEXT;
    test_status TEXT;
    results JSONB := '{}'::jsonb;
    test_count INTEGER := 0;
    passed_count INTEGER := 0;
BEGIN
    -- Test 1.1: Verificar esquema monitoring existe
    BEGIN
        test_count := test_count + 1;
        IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'monitoring') THEN
            test_status := 'passed';
            test_result := 'Esquema monitoring existe correctamente';
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'Esquema monitoring no encontrado';
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('basic_functions', 'schema_exists', test_status, 'Verificar existencia del esquema monitoring', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('basic_functions', 'schema_exists', 'failed', SQLERRM);
    END;
    
    -- Test 1.2: Verificar tablas principales existen
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'monitoring' AND table_name = 'system_metrics') AND
           EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'monitoring' AND table_name = 'alerts') AND
           EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'monitoring' AND table_name = 'alert_thresholds') THEN
            test_status := 'passed';
            test_result := 'Todas las tablas principales existen';
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'Faltan tablas principales del sistema';
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('basic_functions', 'tables_exist', test_status, 'Verificar existencia de tablas principales', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('basic_functions', 'tables_exist', 'failed', SQLERRM);
    END;
    
    -- Test 1.3: Verificar función get_system_status
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        SELECT monitoring.get_system_status() INTO test_result;
        
        IF test_result IS NOT NULL AND test_result::jsonb ? 'timestamp' THEN
            test_status := 'passed';
            test_result := 'Función get_system_status responde correctamente';
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'Función get_system_status no responde correctamente';
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('basic_functions', 'get_system_status', test_status, 'Verificar función de estado del sistema', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('basic_functions', 'get_system_status', 'failed', SQLERRM);
    END;
    
    -- Test 1.4: Verificar configuración de umbrales por defecto
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        IF (SELECT COUNT(*) FROM monitoring.alert_thresholds WHERE enabled = TRUE) >= 5 THEN
            test_status := 'passed';
            test_result := format('%s umbrales configurados correctamente', 
                           (SELECT COUNT(*) FROM monitoring.alert_thresholds WHERE enabled = TRUE));
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'Configuración insuficiente de umbrales por defecto';
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('basic_functions', 'default_thresholds', test_status, 'Verificar configuración de umbrales por defecto', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('basic_functions', 'default_thresholds', 'failed', SQLERRM);
    END;
    
    -- Construir resultado del suite
    results := jsonb_build_object(
        'suite_name', 'basic_functions',
        'total_tests', test_count,
        'passed_tests', passed_count,
        'success_rate', ROUND(100.0 * passed_count / test_count, 2),
        'status', CASE WHEN passed_count = test_count THEN 'passed' ELSE 'failed' END
    );
    
    RETURN results;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TEST SUITE 2: RECOLECCIÓN DE MÉTRICAS
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.test_metrics_collection()
RETURNS JSONB AS $$
DECLARE
    test_start_time TIMESTAMPTZ := NOW();
    test_result TEXT;
    test_status TEXT;
    results JSONB := '{}'::jsonb;
    test_count INTEGER := 0;
    passed_count INTEGER := 0;
    job_id UUID;
    metrics_before INTEGER;
    metrics_after INTEGER;
BEGIN
    -- Test 2.1: Ejecutar recolección manual de métricas
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        SELECT COUNT(*) INTO metrics_before FROM monitoring.system_metrics;
        SELECT monitoring.collect_system_metrics() INTO job_id;
        SELECT COUNT(*) INTO metrics_after FROM monitoring.system_metrics;
        
        IF job_id IS NOT NULL AND metrics_after > metrics_before THEN
            test_status := 'passed';
            test_result := format('Métricas recolectadas exitosamente. Job ID: %s', job_id);
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'Fallo en recolección de métricas';
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms, test_data)
        VALUES ('metrics_collection', 'manual_collection', test_status, 'Ejecutar recolección manual de métricas', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER,
                jsonb_build_object('job_id', job_id, 'metrics_before', metrics_before, 'metrics_after', metrics_after));
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('metrics_collection', 'manual_collection', 'failed', SQLERRM);
    END;
    
    -- Test 2.2: Verificar calidad de métricas recolectadas
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        IF EXISTS (
            SELECT 1 FROM monitoring.system_metrics 
            WHERE timestamp > NOW() - INTERVAL '5 minutes'
            AND total_connections IS NOT NULL 
            AND database_size_mb IS NOT NULL
            AND cache_hit_ratio IS NOT NULL
        ) THEN
            test_status := 'passed';
            test_result := 'Métricas recientes contienen datos válidos';
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'Métricas recolectadas contienen datos nulos o inválidos';
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('metrics_collection', 'metrics_quality', test_status, 'Verificar calidad de métricas recolectadas', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('metrics_collection', 'metrics_quality', 'failed', SQLERRM);
    END;
    
    -- Test 2.3: Verificar registro de trabajos de recolección
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        IF EXISTS (
            SELECT 1 FROM monitoring.collection_jobs 
            WHERE job_type = 'system_metrics' 
            AND status = 'completed'
            AND started_at > NOW() - INTERVAL '5 minutes'
        ) THEN
            test_status := 'passed';
            test_result := 'Trabajos de recolección se registran correctamente';
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'No se encontraron trabajos de recolección registrados';
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('metrics_collection', 'job_tracking', test_status, 'Verificar registro de trabajos de recolección', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('metrics_collection', 'job_tracking', 'failed', SQLERRM);
    END;
    
    -- Construir resultado del suite
    results := jsonb_build_object(
        'suite_name', 'metrics_collection',
        'total_tests', test_count,
        'passed_tests', passed_count,
        'success_rate', ROUND(100.0 * passed_count / test_count, 2),
        'status', CASE WHEN passed_count = test_count THEN 'passed' ELSE 'failed' END
    );
    
    RETURN results;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TEST SUITE 3: SISTEMA DE ALERTAS
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.test_alert_system()
RETURNS JSONB AS $$
DECLARE
    test_start_time TIMESTAMPTZ := NOW();
    test_result TEXT;
    test_status TEXT;
    results JSONB := '{}'::jsonb;
    test_count INTEGER := 0;
    passed_count INTEGER := 0;
    alerts_before INTEGER;
    alerts_after INTEGER;
    test_alert_id UUID;
BEGIN
    -- Test 3.1: Crear alerta de prueba manual
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        SELECT COUNT(*) INTO alerts_before FROM monitoring.alerts;
        
        INSERT INTO monitoring.alerts (
            timestamp, alert_type, severity, metric_name, title, description, status, created_by
        ) VALUES (
            NOW(), 'test_alert', 'warning', 'test_metric', 'Test Alert', 'Alerta de prueba para testing', 'active', 'test_system'
        ) RETURNING id INTO test_alert_id;
        
        SELECT COUNT(*) INTO alerts_after FROM monitoring.alerts;
        
        IF test_alert_id IS NOT NULL AND alerts_after > alerts_before THEN
            test_status := 'passed';
            test_result := format('Alerta de prueba creada exitosamente: %s', test_alert_id);
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'Fallo al crear alerta de prueba';
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms, test_data)
        VALUES ('alert_system', 'create_test_alert', test_status, 'Crear alerta de prueba manual', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER,
                jsonb_build_object('test_alert_id', test_alert_id));
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('alert_system', 'create_test_alert', 'failed', SQLERRM);
    END;
    
    -- Test 3.2: Verificar sistema de verificación de umbrales
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        -- Ejecutar verificación de umbrales
        PERFORM monitoring.check_alert_thresholds_enhanced();
        
        test_status := 'passed';
        test_result := 'Sistema de verificación de umbrales ejecutado sin errores';
        passed_count := passed_count + 1;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('alert_system', 'threshold_checking', test_status, 'Verificar sistema de umbrales', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('alert_system', 'threshold_checking', 'failed', SQLERRM);
    END;
    
    -- Test 3.3: Verificar auto-resolución de alertas
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        -- Ejecutar auto-resolución
        PERFORM monitoring.auto_resolve_alerts();
        
        test_status := 'passed';
        test_result := 'Sistema de auto-resolución ejecutado sin errores';
        passed_count := passed_count + 1;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('alert_system', 'auto_resolution', test_status, 'Verificar auto-resolución de alertas', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('alert_system', 'auto_resolution', 'failed', SQLERRM);
    END;
    
    -- Test 3.4: Limpiar alerta de prueba
    BEGIN
        IF test_alert_id IS NOT NULL THEN
            DELETE FROM monitoring.alerts WHERE id = test_alert_id;
        END IF;
    EXCEPTION WHEN OTHERS THEN
        -- Ignorar errores de limpieza
        NULL;
    END;
    
    -- Construir resultado del suite
    results := jsonb_build_object(
        'suite_name', 'alert_system',
        'total_tests', test_count,
        'passed_tests', passed_count,
        'success_rate', ROUND(100.0 * passed_count / test_count, 2),
        'status', CASE WHEN passed_count = test_count THEN 'passed' ELSE 'failed' END
    );
    
    RETURN results;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TEST SUITE 4: SISTEMA DE NOTIFICACIONES
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.test_notification_system()
RETURNS JSONB AS $$
DECLARE
    test_start_time TIMESTAMPTZ := NOW();
    test_result TEXT;
    test_status TEXT;
    results JSONB := '{}'::jsonb;
    test_count INTEGER := 0;
    passed_count INTEGER := 0;
    test_alert_id UUID;
    notifications_sent INTEGER;
BEGIN
    -- Test 4.1: Verificar configuración de canales
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        IF (SELECT COUNT(*) FROM monitoring.notification_config WHERE enabled = TRUE) >= 1 THEN
            test_status := 'passed';
            test_result := format('%s canales de notificación configurados', 
                           (SELECT COUNT(*) FROM monitoring.notification_config WHERE enabled = TRUE));
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'No hay canales de notificación configurados';
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('notification_system', 'channel_config', test_status, 'Verificar configuración de canales', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('notification_system', 'channel_config', 'failed', SQLERRM);
    END;
    
    -- Test 4.2: Test de envío de notificaciones
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        -- Crear alerta de prueba para notificaciones
        INSERT INTO monitoring.alerts (
            timestamp, alert_type, severity, metric_name, title, description, status, created_by
        ) VALUES (
            NOW(), 'test_notification', 'warning', 'test_metric', 'Test Notification Alert', 
            'Alerta de prueba para testing de notificaciones', 'active', 'notification_test_system'
        ) RETURNING id INTO test_alert_id;
        
        -- Intentar enviar notificaciones
        SELECT monitoring.send_alert_notifications(test_alert_id) INTO notifications_sent;
        
        IF notifications_sent IS NOT NULL THEN
            test_status := 'passed';
            test_result := format('Sistema de notificaciones funcional. Notificaciones enviadas: %s', notifications_sent);
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'Sistema de notificaciones no responde';
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms, test_data)
        VALUES ('notification_system', 'send_notifications', test_status, 'Test de envío de notificaciones', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER,
                jsonb_build_object('test_alert_id', test_alert_id, 'notifications_sent', notifications_sent));
                
        -- Limpiar alerta de prueba
        DELETE FROM monitoring.alerts WHERE id = test_alert_id;
        DELETE FROM monitoring.notification_history WHERE alert_id = test_alert_id;
        
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('notification_system', 'send_notifications', 'failed', SQLERRM);
        
        -- Limpiar en caso de error
        IF test_alert_id IS NOT NULL THEN
            DELETE FROM monitoring.alerts WHERE id = test_alert_id;
            DELETE FROM monitoring.notification_history WHERE alert_id = test_alert_id;
        END IF;
    END;
    
    -- Construir resultado del suite
    results := jsonb_build_object(
        'suite_name', 'notification_system',
        'total_tests', test_count,
        'passed_tests', passed_count,
        'success_rate', ROUND(100.0 * passed_count / test_count, 2),
        'status', CASE WHEN passed_count = test_count THEN 'passed' ELSE 'failed' END
    );
    
    RETURN results;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- ÍNDICES Y COMENTARIOS
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_test_results_suite_status ON monitoring.test_results (test_suite, status);
CREATE INDEX IF NOT EXISTS idx_test_results_executed_at ON monitoring.test_results (executed_at DESC);

COMMENT ON TABLE monitoring.test_results IS 'Registro de resultados de todos los tests del sistema de monitoreo';
COMMENT ON FUNCTION monitoring.run_comprehensive_tests() IS 'Función principal que ejecuta todos los test suites del sistema';

-- Verificación inicial
DO $$
BEGIN
    RAISE NOTICE 'Sistema de Testing y Validación creado exitosamente';
    RAISE NOTICE 'Test Suites implementados: 4 (básicos, métricas, alertas, notificaciones)';
    RAISE NOTICE 'Para ejecutar: SELECT monitoring.run_comprehensive_tests();';
END $$;
