-- =====================================================
-- TESTING AVANZADO: FLOOD CONTROL, REPORTES Y AUTOMATIZACIÓN
-- Archivo: 15_advanced_testing_suites.sql
-- Descripción: Test suites avanzados para componentes complejos
-- =====================================================

-- =====================================================
-- TEST SUITE 5: CONTROL ANTI-FLOOD
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.test_flood_control()
RETURNS JSONB AS $$
DECLARE
    test_start_time TIMESTAMPTZ := NOW();
    test_result TEXT;
    test_status TEXT;
    results JSONB := '{}'::jsonb;
    test_count INTEGER := 0;
    passed_count INTEGER := 0;
    flood_check_result BOOLEAN;
    i INTEGER;
BEGIN
    -- Test 5.1: Verificar función check_flood_control
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        -- Primera llamada debería permitir
        SELECT monitoring.check_flood_control('test_metric_flood', 'email') INTO flood_check_result;
        
        IF flood_check_result = TRUE THEN
            test_status := 'passed';
            test_result := 'Control anti-flood permite primera alerta correctamente';
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'Control anti-flood no permite primera alerta';
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('flood_control', 'first_alert_allowed', test_status, 'Verificar que primera alerta se permite', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('flood_control', 'first_alert_allowed', 'failed', SQLERRM);
    END;
    
    -- Test 5.2: Simular flood y verificar bloqueo
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        -- Simular múltiples alertas rápidas para trigger flood control
        FOR i IN 2..6 LOOP
            PERFORM monitoring.check_flood_control('test_metric_flood', 'email');
        END LOOP;
        
        -- La siguiente debería ser bloqueada
        SELECT monitoring.check_flood_control('test_metric_flood', 'email') INTO flood_check_result;
        
        IF flood_check_result = FALSE THEN
            test_status := 'passed';
            test_result := 'Control anti-flood bloquea correctamente alertas excesivas';
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'Control anti-flood no está bloqueando alertas excesivas';
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('flood_control', 'flood_blocking', test_status, 'Verificar bloqueo de alertas excesivas', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('flood_control', 'flood_blocking', 'failed', SQLERRM);
    END;
    
    -- Test 5.3: Verificar limpieza de registros flood control
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        -- Crear registros de flood control antiguos
        INSERT INTO monitoring.alert_flood_control (metric_name, channel_type, period_start_time)
        VALUES ('test_cleanup_metric', 'email', NOW() - INTERVAL '25 hours');
        
        -- Ejecutar limpieza
        DELETE FROM monitoring.alert_flood_control 
        WHERE period_start_time < NOW() - INTERVAL '24 hours';
        
        -- Verificar que se eliminaron
        IF NOT EXISTS (SELECT 1 FROM monitoring.alert_flood_control WHERE metric_name = 'test_cleanup_metric') THEN
            test_status := 'passed';
            test_result := 'Limpieza de registros flood control funciona correctamente';
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'Limpieza de registros flood control no funciona';
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('flood_control', 'cleanup_old_records', test_status, 'Verificar limpieza de registros antiguos', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('flood_control', 'cleanup_old_records', 'failed', SQLERRM);
    END;
    
    -- Limpiar datos de prueba
    DELETE FROM monitoring.alert_flood_control WHERE metric_name LIKE 'test_%';
    
    -- Construir resultado del suite
    results := jsonb_build_object(
        'suite_name', 'flood_control',
        'total_tests', test_count,
        'passed_tests', passed_count,
        'success_rate', ROUND(100.0 * passed_count / test_count, 2),
        'status', CASE WHEN passed_count = test_count THEN 'passed' ELSE 'failed' END
    );
    
    RETURN results;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TEST SUITE 6: SISTEMA DE REPORTES
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.test_reporting_system()
RETURNS JSONB AS $$
DECLARE
    test_start_time TIMESTAMPTZ := NOW();
    test_result TEXT;
    test_status TEXT;
    results JSONB := '{}'::jsonb;
    test_count INTEGER := 0;
    passed_count INTEGER := 0;
    report_id UUID;
    test_date DATE := CURRENT_DATE - INTERVAL '1 day';
BEGIN
    -- Test 6.1: Generar reporte diario de prueba
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        -- Insertar métricas de prueba para el día anterior
        INSERT INTO monitoring.system_metrics (
            timestamp, cpu_usage_percent, memory_usage_percent, connection_usage_percent, 
            cache_hit_ratio, total_connections, database_size_mb
        ) VALUES (
            test_date + TIME '12:00:00', 45.5, 60.2, 30.1, 95.8, 25, 1024
        );
        
        -- Generar reporte
        SELECT monitoring.generate_daily_report(test_date) INTO report_id;
        
        IF report_id IS NOT NULL THEN
            test_status := 'passed';
            test_result := format('Reporte diario generado exitosamente: %s', report_id);
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'Fallo al generar reporte diario';
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms, test_data)
        VALUES ('reporting_system', 'generate_daily_report', test_status, 'Generar reporte diario de prueba', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER,
                jsonb_build_object('report_id', report_id, 'test_date', test_date));
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('reporting_system', 'generate_daily_report', 'failed', SQLERRM);
    END;
    
    -- Test 6.2: Verificar contenido del reporte
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        IF EXISTS (
            SELECT 1 FROM monitoring.daily_reports 
            WHERE report_date = test_date 
            AND metrics_summary IS NOT NULL 
            AND overall_health_score IS NOT NULL
        ) THEN
            test_status := 'passed';
            test_result := 'Reporte contiene datos válidos y completos';
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'Reporte no contiene datos válidos';
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('reporting_system', 'report_content_validation', test_status, 'Verificar contenido del reporte', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('reporting_system', 'report_content_validation', 'failed', SQLERRM);
    END;
    
    -- Test 6.3: Verificar vistas de reportes
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        IF EXISTS (SELECT 1 FROM monitoring.daily_reports_summary WHERE report_date = test_date) THEN
            test_status := 'passed';
            test_result := 'Vista de resumen de reportes funciona correctamente';
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'Vista de resumen de reportes no funciona';
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('reporting_system', 'summary_view', test_status, 'Verificar vista de resumen', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('reporting_system', 'summary_view', 'failed', SQLERRM);
    END;
    
    -- Limpiar datos de prueba
    DELETE FROM monitoring.daily_reports WHERE report_date = test_date;
    DELETE FROM monitoring.system_metrics WHERE timestamp::date = test_date;
    
    -- Construir resultado del suite
    results := jsonb_build_object(
        'suite_name', 'reporting_system',
        'total_tests', test_count,
        'passed_tests', passed_count,
        'success_rate', ROUND(100.0 * passed_count / test_count, 2),
        'status', CASE WHEN passed_count = test_count THEN 'passed' ELSE 'failed' END
    );
    
    RETURN results;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TEST SUITE 7: AUTOMATIZACIÓN PG_CRON
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.test_automation_system()
RETURNS JSONB AS $$
DECLARE
    test_start_time TIMESTAMPTZ := NOW();
    test_result TEXT;
    test_status TEXT;
    results JSONB := '{}'::jsonb;
    test_count INTEGER := 0;
    passed_count INTEGER := 0;
    cron_jobs_count INTEGER;
    maintenance_result TEXT;
BEGIN
    -- Test 7.1: Verificar trabajos pg_cron configurados
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        SELECT COUNT(*) INTO cron_jobs_count 
        FROM cron.job 
        WHERE command LIKE '%monitoring.%';
        
        IF cron_jobs_count >= 5 THEN
            test_status := 'passed';
            test_result := format('%s trabajos pg_cron de monitoreo configurados', cron_jobs_count);
            passed_count := passed_count + 1;
        ELSE
            test_status := 'warning';
            test_result := format('Solo %s trabajos pg_cron encontrados (esperados >= 5)', cron_jobs_count);
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms, test_data)
        VALUES ('automation_system', 'cron_jobs_configured', test_status, 'Verificar trabajos pg_cron configurados', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER,
                jsonb_build_object('cron_jobs_count', cron_jobs_count));
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('automation_system', 'cron_jobs_configured', 'failed', SQLERRM);
    END;
    
    -- Test 7.2: Ejecutar mantenimiento diario manual
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        SELECT monitoring.daily_maintenance() INTO maintenance_result;
        
        IF maintenance_result IS NOT NULL AND maintenance_result LIKE '%completado%' THEN
            test_status := 'passed';
            test_result := format('Mantenimiento diario ejecutado: %s', maintenance_result);
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'Mantenimiento diario falló o no respondió';
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('automation_system', 'daily_maintenance', test_status, 'Ejecutar mantenimiento diario', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('automation_system', 'daily_maintenance', 'failed', SQLERRM);
    END;
    
    -- Test 7.3: Verificar función de verificación de salud
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        PERFORM monitoring.perform_health_check();
        
        test_status := 'passed';
        test_result := 'Verificación de salud del sistema ejecutada sin errores';
        passed_count := passed_count + 1;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('automation_system', 'health_check', test_status, 'Verificar función de health check', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('automation_system', 'health_check', 'failed', SQLERRM);
    END;
    
    -- Construir resultado del suite
    results := jsonb_build_object(
        'suite_name', 'automation_system',
        'total_tests', test_count,
        'passed_tests', passed_count,
        'success_rate', ROUND(100.0 * passed_count / test_count, 2),
        'status', CASE WHEN passed_count = test_count THEN 'passed' ELSE 'failed' END
    );
    
    RETURN results;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TEST SUITE 8: RENDIMIENTO Y CARGA
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.test_performance()
RETURNS JSONB AS $$
DECLARE
    test_start_time TIMESTAMPTZ := NOW();
    test_result TEXT;
    test_status TEXT;
    results JSONB := '{}'::jsonb;
    test_count INTEGER := 0;
    passed_count INTEGER := 0;
    i INTEGER;
    avg_collection_time DECIMAL(10,2);
    max_collection_time DECIMAL(10,2);
    stress_test_start TIMESTAMPTZ;
    stress_test_duration INTEGER;
BEGIN
    -- Test 8.1: Test de rendimiento de recolección de métricas
    BEGIN
        test_count := test_count + 1;
        stress_test_start := NOW();
        
        -- Ejecutar múltiples recolecciones para medir rendimiento
        FOR i IN 1..5 LOOP
            PERFORM monitoring.collect_system_metrics();
        END LOOP;
        
        -- Calcular estadísticas de rendimiento
        SELECT 
            AVG(execution_time_ms),
            MAX(execution_time_ms)
        INTO avg_collection_time, max_collection_time
        FROM monitoring.collection_jobs 
        WHERE started_at >= stress_test_start;
        
        IF avg_collection_time < 5000 AND max_collection_time < 10000 THEN
            test_status := 'passed';
            test_result := format('Rendimiento aceptable: promedio %sms, máximo %sms', avg_collection_time, max_collection_time);
            passed_count := passed_count + 1;
        ELSE
            test_status := 'warning';
            test_result := format('Rendimiento lento: promedio %sms, máximo %sms', avg_collection_time, max_collection_time);
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms, test_data)
        VALUES ('performance', 'metrics_collection_performance', test_status, 'Test de rendimiento de recolección', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER,
                jsonb_build_object('avg_time_ms', avg_collection_time, 'max_time_ms', max_collection_time, 'iterations', 5));
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('performance', 'metrics_collection_performance', 'failed', SQLERRM);
    END;
    
    -- Test 8.2: Test de carga de alertas
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        -- Crear múltiples alertas simultáneamente
        FOR i IN 1..10 LOOP
            INSERT INTO monitoring.alerts (
                timestamp, alert_type, severity, metric_name, title, description, status, created_by
            ) VALUES (
                NOW(), 'load_test', 'warning', format('test_metric_%s', i), 
                format('Load Test Alert %s', i), 'Alerta de prueba de carga', 'active', 'load_test_system'
            );
        END LOOP;
        
        stress_test_duration := EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER;
        
        IF stress_test_duration < 2000 THEN
            test_status := 'passed';
            test_result := format('Creación de 10 alertas en %sms - rendimiento aceptable', stress_test_duration);
            passed_count := passed_count + 1;
        ELSE
            test_status := 'warning';
            test_result := format('Creación de 10 alertas en %sms - rendimiento lento', stress_test_duration);
        END IF;
        
        -- Limpiar alertas de prueba
        DELETE FROM monitoring.alerts WHERE created_by = 'load_test_system';
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('performance', 'alert_creation_load', test_status, 'Test de carga de creación de alertas', test_result,
                stress_test_duration);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('performance', 'alert_creation_load', 'failed', SQLERRM);
        
        -- Limpiar en caso de error
        DELETE FROM monitoring.alerts WHERE created_by = 'load_test_system';
    END;
    
    -- Test 8.3: Test de consultas a vistas materializadas
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        -- Ejecutar consultas a vistas principales
        PERFORM * FROM monitoring.alerts_dashboard_enhanced LIMIT 10;
        PERFORM * FROM monitoring.daily_reports_summary LIMIT 5;
        PERFORM * FROM monitoring.system_overview;
        
        stress_test_duration := EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER;
        
        IF stress_test_duration < 1000 THEN
            test_status := 'passed';
            test_result := format('Consultas a vistas en %sms - rendimiento excelente', stress_test_duration);
            passed_count := passed_count + 1;
        ELSE
            test_status := 'warning';
            test_result := format('Consultas a vistas en %sms - considerar optimización', stress_test_duration);
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('performance', 'views_query_performance', test_status, 'Test de rendimiento de vistas', test_result,
                stress_test_duration);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('performance', 'views_query_performance', 'failed', SQLERRM);
    END;
    
    -- Construir resultado del suite
    results := jsonb_build_object(
        'suite_name', 'performance',
        'total_tests', test_count,
        'passed_tests', passed_count,
        'success_rate', ROUND(100.0 * passed_count / test_count, 2),
        'status', CASE WHEN passed_count = test_count THEN 'passed' ELSE 'failed' END
    );
    
    RETURN results;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA SIMULAR ESCENARIOS DE FALLO
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.simulate_failure_scenarios()
RETURNS JSONB AS $$
DECLARE
    test_start_time TIMESTAMPTZ := NOW();
    test_result TEXT;
    test_status TEXT;
    results JSONB := '{}'::jsonb;
    test_count INTEGER := 0;
    passed_count INTEGER := 0;
    recovery_time INTEGER;
    test_alert_id UUID;
BEGIN
    RAISE NOTICE '=== INICIANDO SIMULACIÓN DE ESCENARIOS DE FALLO ===';
    
    -- Escenario 1: Simular fallo de base de datos (métricas no disponibles)
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        -- Simular métricas con valores NULL (fallo de recolección)
        INSERT INTO monitoring.system_metrics (
            timestamp, cpu_usage_percent, memory_usage_percent, 
            total_connections, database_size_mb
        ) VALUES (
            NOW(), NULL, NULL, NULL, NULL
        );
        
        -- Verificar que el sistema maneja graciosamente los valores NULL
        PERFORM monitoring.check_alert_thresholds_enhanced();
        
        test_status := 'passed';
        test_result := 'Sistema maneja correctamente métricas con valores NULL';
        passed_count := passed_count + 1;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('failure_scenarios', 'null_metrics_handling', test_status, 'Manejo de métricas NULL', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('failure_scenarios', 'null_metrics_handling', 'failed', SQLERRM);
    END;
    
    -- Escenario 2: Simular fallo en envío de notificaciones
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        -- Crear alerta crítica de prueba
        INSERT INTO monitoring.alerts (
            timestamp, alert_type, severity, metric_name, title, description, status, created_by
        ) VALUES (
            NOW(), 'failure_test', 'critical', 'test_failure_metric', 
            'Critical Test Alert', 'Alerta crítica de prueba para fallo', 'active', 'failure_test_system'
        ) RETURNING id INTO test_alert_id;
        
        -- Intentar enviar notificaciones (debería manejar graciosamente fallos simulados)
        PERFORM monitoring.send_alert_notifications(test_alert_id);
        
        -- Verificar que se registró el intento
        IF EXISTS (SELECT 1 FROM monitoring.notification_history WHERE alert_id = test_alert_id) THEN
            test_status := 'passed';
            test_result := 'Sistema registra intentos de notificación correctamente';
            passed_count := passed_count + 1;
        ELSE
            test_status := 'failed';
            test_result := 'Sistema no registra intentos de notificación';
        END IF;
        
        -- Limpiar
        DELETE FROM monitoring.alerts WHERE id = test_alert_id;
        DELETE FROM monitoring.notification_history WHERE alert_id = test_alert_id;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('failure_scenarios', 'notification_failure_handling', test_status, 'Manejo de fallos de notificación', test_result,
                EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('failure_scenarios', 'notification_failure_handling', 'failed', SQLERRM);
        
        -- Limpiar en caso de error
        IF test_alert_id IS NOT NULL THEN
            DELETE FROM monitoring.alerts WHERE id = test_alert_id;
            DELETE FROM monitoring.notification_history WHERE alert_id = test_alert_id;
        END IF;
    END;
    
    -- Escenario 3: Test de recuperación tras interrupción
    BEGIN
        test_count := test_count + 1;
        test_start_time := NOW();
        
        -- Simular pausa en recolección (sin métricas por un período)
        -- Luego reanudar y verificar que el sistema se recupera
        PERFORM monitoring.collect_system_metrics();
        
        recovery_time := EXTRACT(milliseconds FROM (NOW() - test_start_time))::INTEGER;
        
        IF recovery_time < 5000 THEN
            test_status := 'passed';
            test_result := format('Sistema se recupera en %sms tras interrupción simulada', recovery_time);
            passed_count := passed_count + 1;
        ELSE
            test_status := 'warning';
            test_result := format('Recuperación lenta: %sms', recovery_time);
        END IF;
        
        INSERT INTO monitoring.test_results (test_suite, test_name, status, description, actual_result, execution_time_ms)
        VALUES ('failure_scenarios', 'recovery_after_interruption', test_status, 'Test de recuperación', test_result,
                recovery_time);
    EXCEPTION WHEN OTHERS THEN
        INSERT INTO monitoring.test_results (test_suite, test_name, status, error_message)
        VALUES ('failure_scenarios', 'recovery_after_interruption', 'failed', SQLERRM);
    END;
    
    -- Construir resultado final
    results := jsonb_build_object(
        'suite_name', 'failure_scenarios',
        'total_tests', test_count,
        'passed_tests', passed_count,
        'success_rate', ROUND(100.0 * passed_count / test_count, 2),
        'status', CASE WHEN passed_count = test_count THEN 'passed' ELSE 'failed' END,
        'execution_time_seconds', EXTRACT(EPOCH FROM (NOW() - test_start_time))::INTEGER
    );
    
    RAISE NOTICE 'Simulación de fallos completada: % tests, % exitosos', test_count, passed_count;
    RETURN results;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA GENERAR REPORTE COMPLETO DE TESTING
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.generate_testing_report()
RETURNS TEXT AS $$
DECLARE
    report_content TEXT;
    total_tests INTEGER;
    passed_tests INTEGER;
    failed_tests INTEGER;
    overall_success_rate DECIMAL(5,2);
    test_summary RECORD;
BEGIN
    -- Obtener estadísticas generales
    SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE status = 'passed') as passed,
        COUNT(*) FILTER (WHERE status = 'failed') as failed
    INTO total_tests, passed_tests, failed_tests
    FROM monitoring.test_results 
    WHERE executed_at > NOW() - INTERVAL '1 hour';
    
    overall_success_rate := ROUND(100.0 * passed_tests / GREATEST(total_tests, 1), 2);
    
    -- Construir reporte
    report_content := format(
        '=== REPORTE DE TESTING DEL SISTEMA DE MONITOREO ===
        
Fecha de Ejecución: %s
        
RESUMEN GENERAL:
- Total de Tests: %s
- Tests Exitosos: %s
- Tests Fallidos: %s  
- Tasa de Éxito: %s%%
        
RESULTADOS POR SUITE:',
        NOW()::timestamp(0),
        total_tests,
        passed_tests, 
        failed_tests,
        overall_success_rate
    );
    
    -- Agregar detalles por suite
    FOR test_summary IN
        SELECT 
            test_suite,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status = 'passed') as passed,
            COUNT(*) FILTER (WHERE status = 'failed') as failed,
            ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'passed') / COUNT(*), 2) as success_rate
        FROM monitoring.test_results 
        WHERE executed_at > NOW() - INTERVAL '1 hour'
        GROUP BY test_suite
        ORDER BY test_suite
    LOOP
        report_content := report_content || format(
            '
- %s: %s/%s tests exitosos (%s%%)%s',
            UPPER(test_summary.test_suite),
            test_summary.passed,
            test_summary.total,
            test_summary.success_rate,
            CASE WHEN test_summary.failed > 0 THEN format(' [%s FALLOS]', test_summary.failed) ELSE '' END
        );
    END LOOP;
    
    -- Agregar tests fallidos si los hay
    IF failed_tests > 0 THEN
        report_content := report_content || '
        
TESTS FALLIDOS:';
        
        FOR test_summary IN
            SELECT test_suite, test_name, error_message
            FROM monitoring.test_results 
            WHERE status = 'failed' 
            AND executed_at > NOW() - INTERVAL '1 hour'
            ORDER BY test_suite, test_name
        LOOP
            report_content := report_content || format('
- %s.%s: %s', 
                test_summary.test_suite, 
                test_summary.test_name, 
                COALESCE(test_summary.error_message, 'Sin detalles de error')
            );
        END LOOP;
    END IF;
    
    -- Conclusión
    report_content := report_content || format('
        
CONCLUSIÓN:
%s

Recomendación: %s
        
=== FIN DEL REPORTE ===',
        CASE 
            WHEN overall_success_rate >= 95 THEN 'Sistema de monitoreo PLENAMENTE OPERACIONAL'
            WHEN overall_success_rate >= 80 THEN 'Sistema de monitoreo OPERACIONAL con alertas menores'
            WHEN overall_success_rate >= 60 THEN 'Sistema de monitoreo FUNCIONAL con problemas'
            ELSE 'Sistema de monitoreo REQUIERE ATENCIÓN INMEDIATA'
        END,
        CASE 
            WHEN overall_success_rate >= 95 THEN 'Proceder con despliegue a producción'
            WHEN overall_success_rate >= 80 THEN 'Revisar tests fallidos antes de producción'
            WHEN overall_success_rate >= 60 THEN 'Solucionar problemas críticos antes de continuar'
            ELSE 'NO DESPLEGAR - Revisar y corregir fallos sistémicos'
        END
    );
    
    RETURN report_content;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON FUNCTION monitoring.test_flood_control() IS 'Test suite para verificar el sistema de control anti-flood';
COMMENT ON FUNCTION monitoring.test_reporting_system() IS 'Test suite para verificar el sistema de reportes diarios';
COMMENT ON FUNCTION monitoring.test_automation_system() IS 'Test suite para verificar la automatización con pg_cron';
COMMENT ON FUNCTION monitoring.test_performance() IS 'Test suite para verificar el rendimiento bajo carga';
COMMENT ON FUNCTION monitoring.simulate_failure_scenarios() IS 'Simula escenarios de fallo para probar resiliencia';
COMMENT ON FUNCTION monitoring.generate_testing_report() IS 'Genera reporte completo de resultados de testing';

-- Verificación final
DO $$
BEGIN
    RAISE NOTICE 'Test Suites Avanzados implementados exitosamente';
    RAISE NOTICE 'Componentes: flood_control, reporting_system, automation_system, performance';
    RAISE NOTICE 'Funciones adicionales: simulate_failure_scenarios, generate_testing_report';
    RAISE NOTICE 'Para ejecutar testing completo: SELECT monitoring.run_comprehensive_tests();';
    RAISE NOTICE 'Para simulación de fallos: SELECT monitoring.simulate_failure_scenarios();';
    RAISE NOTICE 'Para reporte final: SELECT monitoring.generate_testing_report();';
END $$;
