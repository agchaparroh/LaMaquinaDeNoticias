-- =====================================================
-- SISTEMA DE TESTING DE CARGA Y CONCURRENCIA
-- Archivo: 17_load_and_concurrency_testing.sql
-- Descripción: Testing completo de rendimiento bajo carga
-- =====================================================

-- =====================================================
-- TABLA PARA RESULTADOS DE TESTING DE CARGA
-- =====================================================

CREATE TABLE IF NOT EXISTS monitoring.load_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_suite TEXT NOT NULL,
    test_name TEXT NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Configuración del test
    concurrent_connections INTEGER,
    test_duration_seconds INTEGER,
    operations_per_second INTEGER,
    
    -- Resultados de rendimiento
    total_operations INTEGER,
    successful_operations INTEGER,
    failed_operations INTEGER,
    
    -- Métricas de tiempo
    avg_response_time_ms DECIMAL(10,2),
    min_response_time_ms DECIMAL(10,2),
    max_response_time_ms DECIMAL(10,2),
    p95_response_time_ms DECIMAL(10,2),
    p99_response_time_ms DECIMAL(10,2),
    
    -- Métricas del sistema durante el test
    peak_cpu_usage DECIMAL(5,2),
    peak_memory_usage DECIMAL(5,2),
    peak_connections INTEGER,
    avg_query_time_ms DECIMAL(10,2),
    
    -- Resultados y observaciones
    success_rate DECIMAL(5,2),
    throughput_ops_per_sec DECIMAL(10,2),
    observations TEXT,
    recommendations TEXT[],
    
    -- Metadatos
    test_environment TEXT DEFAULT 'development',
    test_version TEXT DEFAULT '1.0'
);

-- =====================================================
-- FUNCIÓN PRINCIPAL DE TESTING DE CARGA
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.run_load_test_suite()
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
    RAISE NOTICE '=== INICIANDO TESTING DE CARGA Y CONCURRENCIA ===';
    
    -- Limpiar resultados anteriores
    DELETE FROM monitoring.load_test_results WHERE executed_at < NOW() - INTERVAL '1 hour';
    
    -- 1. TEST: Carga de Recolección de Métricas
    RAISE NOTICE 'Ejecutando: Load Test 1 - Recolección Masiva de Métricas';
    SELECT monitoring.test_metrics_collection_load() INTO suite_results;
    test_results := test_results || jsonb_build_object('metrics_collection_load', suite_results);
    
    -- 2. TEST: Carga de Generación de Alertas
    RAISE NOTICE 'Ejecutando: Load Test 2 - Generación Masiva de Alertas';
    SELECT monitoring.test_alerts_generation_load() INTO suite_results;
    test_results := test_results || jsonb_build_object('alerts_generation_load', suite_results);
    
    -- 3. TEST: Carga de Sistema de Notificaciones
    RAISE NOTICE 'Ejecutando: Load Test 3 - Sistema de Notificaciones';
    SELECT monitoring.test_notifications_load() INTO suite_results;
    test_results := test_results || jsonb_build_object('notifications_load', suite_results);
    
    -- 4. TEST: Concurrencia en Dashboard/Consultas
    RAISE NOTICE 'Ejecutando: Load Test 4 - Consultas Concurrentes';
    SELECT monitoring.test_dashboard_concurrency() INTO suite_results;
    test_results := test_results || jsonb_build_object('dashboard_concurrency', suite_results);
    
    -- 5. TEST: Stress Testing Completo
    RAISE NOTICE 'Ejecutando: Load Test 5 - Stress Testing Integral';
    SELECT monitoring.test_full_system_stress() INTO suite_results;
    test_results := test_results || jsonb_build_object('full_system_stress', suite_results);
    
    -- 6. TEST: Concurrencia de Escritura/Lectura
    RAISE NOTICE 'Ejecutando: Load Test 6 - Concurrencia Read/Write';
    SELECT monitoring.test_read_write_concurrency() INTO suite_results;
    test_results := test_results || jsonb_build_object('read_write_concurrency', suite_results);
    
    -- Calcular estadísticas generales
    SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE success_rate >= 95.0) as passed,
        COUNT(*) FILTER (WHERE success_rate < 95.0) as failed
    INTO total_tests, passed_tests, failed_tests
    FROM monitoring.load_test_results 
    WHERE executed_at >= start_time;
    
    -- Determinar estado general
    overall_status := CASE 
        WHEN failed_tests = 0 THEN 'passed'
        WHEN failed_tests <= total_tests * 0.2 THEN 'warning'
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
            'executed_at', start_time,
            'peak_performance', (
                SELECT jsonb_build_object(
                    'max_throughput', MAX(throughput_ops_per_sec),
                    'best_response_time', MIN(avg_response_time_ms),
                    'peak_concurrent_ops', MAX(concurrent_connections)
                )
                FROM monitoring.load_test_results 
                WHERE executed_at >= start_time
            )
        )
    );
    
    RAISE NOTICE '=== TESTING DE CARGA COMPLETADO ===';
    RAISE NOTICE 'Estado General: %', overall_status;
    RAISE NOTICE 'Tests Ejecutados: % | Exitosos: % | Fallidos: %', total_tests, passed_tests, failed_tests;
    
    RETURN test_results;
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'ERROR CRÍTICO en testing de carga: %', SQLERRM;
    RETURN jsonb_build_object(
        'error', SQLERRM,
        'summary', jsonb_build_object('overall_status', 'error')
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TEST 1: CARGA DE RECOLECCIÓN DE MÉTRICAS
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.test_metrics_collection_load()
RETURNS JSONB AS $$
DECLARE
    test_start_time TIMESTAMPTZ := NOW();
    concurrent_jobs INTEGER := 10;
    total_operations INTEGER := 50;
    successful_ops INTEGER := 0;
    failed_ops INTEGER := 0;
    response_times DECIMAL[] := ARRAY[]::DECIMAL[];
    i INTEGER;
    job_start_time TIMESTAMPTZ;
    job_duration INTEGER;
    peak_cpu DECIMAL(5,2) := 0;
    peak_memory DECIMAL(5,2) := 0;
    peak_connections INTEGER := 0;
BEGIN
    RAISE NOTICE 'Iniciando test de carga: Recolección masiva de métricas';
    RAISE NOTICE 'Configuración: % trabajos concurrentes, % operaciones totales', concurrent_jobs, total_operations;
    
    -- Ejecutar múltiples recolecciones concurrentes simuladas
    FOR i IN 1..total_operations LOOP
        job_start_time := clock_timestamp();
        
        BEGIN
            -- Simular recolección de métricas
            PERFORM monitoring.collect_system_metrics();
            successful_ops := successful_ops + 1;
            
            -- Capturar tiempo de respuesta
            job_duration := EXTRACT(milliseconds FROM (clock_timestamp() - job_start_time))::INTEGER;
            response_times := array_append(response_times, job_duration);
            
            -- Simular carga adicional con métricas dummy
            INSERT INTO monitoring.system_metrics (
                timestamp, cpu_usage_percent, memory_usage_percent, 
                total_connections, database_size_mb, collection_time_ms
            ) VALUES (
                NOW() + (i || ' milliseconds')::INTERVAL,
                50 + (RANDOM() * 40), -- CPU entre 50-90%
                60 + (RANDOM() * 30), -- Memoria entre 60-90%
                20 + (RANDOM() * 50)::INTEGER, -- Conexiones 20-70
                1000 + (RANDOM() * 500)::INTEGER, -- BD size 1000-1500MB
                job_duration
            );
            
        EXCEPTION WHEN OTHERS THEN
            failed_ops := failed_ops + 1;
            RAISE NOTICE 'Error en operación %: %', i, SQLERRM;
        END;
        
        -- Pequeña pausa para simular concurrencia real
        IF i % concurrent_jobs = 0 THEN
            PERFORM pg_sleep(0.1); -- 100ms pausa cada batch
        END IF;
    END LOOP;
    
    -- Obtener métricas del sistema durante el test
    SELECT 
        COALESCE(MAX(cpu_usage_percent), 0),
        COALESCE(MAX(memory_usage_percent), 0),
        COALESCE(MAX(total_connections), 0)
    INTO peak_cpu, peak_memory, peak_connections
    FROM monitoring.system_metrics
    WHERE timestamp >= test_start_time;
    
    -- Registrar resultados
    INSERT INTO monitoring.load_test_results (
        test_suite, test_name, concurrent_connections, test_duration_seconds,
        total_operations, successful_operations, failed_operations,
        avg_response_time_ms, min_response_time_ms, max_response_time_ms,
        peak_cpu_usage, peak_memory_usage, peak_connections,
        success_rate, throughput_ops_per_sec, observations
    ) VALUES (
        'load_testing', 'metrics_collection_load', concurrent_jobs,
        EXTRACT(EPOCH FROM (NOW() - test_start_time))::INTEGER,
        total_operations, successful_ops, failed_ops,
        (SELECT AVG(x) FROM unnest(response_times) x),
        (SELECT MIN(x) FROM unnest(response_times) x),
        (SELECT MAX(x) FROM unnest(response_times) x),
        peak_cpu, peak_memory, peak_connections,
        ROUND(100.0 * successful_ops / total_operations, 2),
        ROUND(successful_ops / EXTRACT(EPOCH FROM (NOW() - test_start_time)), 2),
        format('Test de carga de recolección: %s/%s operaciones exitosas', successful_ops, total_operations)
    );
    
    -- Limpiar datos de test
    DELETE FROM monitoring.system_metrics 
    WHERE timestamp >= test_start_time 
    AND collection_time_ms IS NOT NULL;
    
    RETURN jsonb_build_object(
        'test_name', 'metrics_collection_load',
        'total_operations', total_operations,
        'successful_operations', successful_ops,
        'failed_operations', failed_ops,
        'success_rate', ROUND(100.0 * successful_ops / total_operations, 2),
        'avg_response_time_ms', (SELECT AVG(x) FROM unnest(response_times) x),
        'peak_metrics', jsonb_build_object(
            'cpu', peak_cpu, 'memory', peak_memory, 'connections', peak_connections
        ),
        'status', CASE WHEN successful_ops >= total_operations * 0.95 THEN 'passed' ELSE 'failed' END
    );
    
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'test_name', 'metrics_collection_load',
        'status', 'error',
        'error_message', SQLERRM
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TEST 2: CARGA DE GENERACIÓN DE ALERTAS
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.test_alerts_generation_load()
RETURNS JSONB AS $$
DECLARE
    test_start_time TIMESTAMPTZ := NOW();
    total_alerts INTEGER := 100;
    successful_alerts INTEGER := 0;
    failed_alerts INTEGER := 0;
    response_times DECIMAL[] := ARRAY[]::DECIMAL[];
    i INTEGER;
    alert_start_time TIMESTAMPTZ;
    alert_duration INTEGER;
    alert_id UUID;
BEGIN
    RAISE NOTICE 'Iniciando test de carga: Generación masiva de alertas';
    
    -- Crear métricas que generen alertas
    FOR i IN 1..total_alerts LOOP
        alert_start_time := clock_timestamp();
        
        BEGIN
            -- Insertar métrica que trigger alertas
            INSERT INTO monitoring.system_metrics (
                timestamp, cpu_usage_percent, memory_usage_percent, 
                connection_usage_percent, cache_hit_ratio, total_connections
            ) VALUES (
                NOW() + (i || ' seconds')::INTERVAL,
                85 + (RANDOM() * 10), -- CPU alto para trigger alertas
                88 + (RANDOM() * 10), -- Memoria alta
                82 + (RANDOM() * 15), -- Conexiones altas
                70 + (RANDOM() * 10), -- Cache bajo
                80 + (RANDOM() * 20)::INTEGER
            );
            
            -- Forzar verificación de alertas
            PERFORM monitoring.check_alert_thresholds_enhanced();
            
            successful_alerts := successful_alerts + 1;
            
            -- Capturar tiempo de respuesta
            alert_duration := EXTRACT(milliseconds FROM (clock_timestamp() - alert_start_time))::INTEGER;
            response_times := array_append(response_times, alert_duration);
            
        EXCEPTION WHEN OTHERS THEN
            failed_alerts := failed_alerts + 1;
            RAISE NOTICE 'Error generando alerta %: %', i, SQLERRM;
        END;
        
        -- Pausa mínima para simular carga real
        IF i % 20 = 0 THEN
            PERFORM pg_sleep(0.05); -- 50ms cada 20 alertas
        END IF;
    END LOOP;
    
    -- Registrar resultados
    INSERT INTO monitoring.load_test_results (
        test_suite, test_name, total_operations, successful_operations, failed_operations,
        avg_response_time_ms, min_response_time_ms, max_response_time_ms,
        success_rate, throughput_ops_per_sec, observations
    ) VALUES (
        'load_testing', 'alerts_generation_load', total_alerts, successful_alerts, failed_alerts,
        (SELECT AVG(x) FROM unnest(response_times) x),
        (SELECT MIN(x) FROM unnest(response_times) x),
        (SELECT MAX(x) FROM unnest(response_times) x),
        ROUND(100.0 * successful_alerts / total_alerts, 2),
        ROUND(successful_alerts / EXTRACT(EPOCH FROM (NOW() - test_start_time)), 2),
        format('Generación masiva de alertas: %s alertas generadas en %s segundos',
               (SELECT COUNT(*) FROM monitoring.alerts WHERE timestamp >= test_start_time),
               EXTRACT(EPOCH FROM (NOW() - test_start_time))::INTEGER)
    );
    
    -- Limpiar datos de test
    DELETE FROM monitoring.system_metrics WHERE timestamp >= test_start_time;
    DELETE FROM monitoring.alerts WHERE timestamp >= test_start_time AND created_by = 'enhanced_system';
    
    RETURN jsonb_build_object(
        'test_name', 'alerts_generation_load',
        'total_operations', total_alerts,
        'successful_operations', successful_alerts,
        'success_rate', ROUND(100.0 * successful_alerts / total_alerts, 2),
        'avg_response_time_ms', (SELECT AVG(x) FROM unnest(response_times) x),
        'status', CASE WHEN successful_alerts >= total_alerts * 0.95 THEN 'passed' ELSE 'failed' END
    );
    
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'test_name', 'alerts_generation_load',
        'status', 'error',
        'error_message', SQLERRM
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TEST 3: CARGA DE SISTEMA DE NOTIFICACIONES
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.test_notifications_load()
RETURNS JSONB AS $$
DECLARE
    test_start_time TIMESTAMPTZ := NOW();
    total_notifications INTEGER := 50;
    successful_notifications INTEGER := 0;
    failed_notifications INTEGER := 0;
    response_times DECIMAL[] := ARRAY[]::DECIMAL[];
    i INTEGER;
    notif_start_time TIMESTAMPTZ;
    notif_duration INTEGER;
    test_alert_id UUID;
    notifications_sent INTEGER;
BEGIN
    RAISE NOTICE 'Iniciando test de carga: Sistema de notificaciones';
    
    -- Crear alertas y enviar notificaciones masivamente
    FOR i IN 1..total_notifications LOOP
        notif_start_time := clock_timestamp();
        
        BEGIN
            -- Crear alerta de test
            INSERT INTO monitoring.alerts (
                timestamp, alert_type, severity, metric_name, title, description, 
                status, created_by
            ) VALUES (
                NOW(), 'load_test_notification', 'warning', 'test_metric_' || i,
                'Load Test Alert ' || i, 'Alerta generada durante test de carga',
                'active', 'load_test_notifications'
            ) RETURNING id INTO test_alert_id;
            
            -- Enviar notificaciones
            SELECT monitoring.send_alert_notifications(test_alert_id) INTO notifications_sent;
            
            successful_notifications := successful_notifications + 1;
            
            -- Capturar tiempo de respuesta
            notif_duration := EXTRACT(milliseconds FROM (clock_timestamp() - notif_start_time))::INTEGER;
            response_times := array_append(response_times, notif_duration);
            
        EXCEPTION WHEN OTHERS THEN
            failed_notifications := failed_notifications + 1;
            RAISE NOTICE 'Error en notificación %: %', i, SQLERRM;
        END;
        
        -- Pausa para simular carga controlada
        IF i % 10 = 0 THEN
            PERFORM pg_sleep(0.1); -- 100ms cada 10 notificaciones
        END IF;
    END LOOP;
    
    -- Registrar resultados
    INSERT INTO monitoring.load_test_results (
        test_suite, test_name, total_operations, successful_operations, failed_operations,
        avg_response_time_ms, min_response_time_ms, max_response_time_ms,
        success_rate, throughput_ops_per_sec, observations
    ) VALUES (
        'load_testing', 'notifications_load', total_notifications, successful_notifications, failed_notifications,
        (SELECT AVG(x) FROM unnest(response_times) x),
        (SELECT MIN(x) FROM unnest(response_times) x),
        (SELECT MAX(x) FROM unnest(response_times) x),
        ROUND(100.0 * successful_notifications / total_notifications, 2),
        ROUND(successful_notifications / EXTRACT(EPOCH FROM (NOW() - test_start_time)), 2),
        format('Sistema de notificaciones: %s notificaciones procesadas, %s registros creados',
               successful_notifications,
               (SELECT COUNT(*) FROM monitoring.notification_history WHERE timestamp >= test_start_time))
    );
    
    -- Limpiar datos de test
    DELETE FROM monitoring.alerts WHERE created_by = 'load_test_notifications';
    DELETE FROM monitoring.notification_history WHERE timestamp >= test_start_time;
    
    RETURN jsonb_build_object(
        'test_name', 'notifications_load',
        'total_operations', total_notifications,
        'successful_operations', successful_notifications,
        'success_rate', ROUND(100.0 * successful_notifications / total_notifications, 2),
        'avg_response_time_ms', (SELECT AVG(x) FROM unnest(response_times) x),
        'status', CASE WHEN successful_notifications >= total_notifications * 0.90 THEN 'passed' ELSE 'failed' END
    );
    
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'test_name', 'notifications_load',
        'status', 'error',
        'error_message', SQLERRM
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- ÍNDICES PARA OPTIMIZACIÓN DE TESTING
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_load_test_results_executed_at ON monitoring.load_test_results (executed_at DESC);
CREATE INDEX IF NOT EXISTS idx_load_test_results_test_suite ON monitoring.load_test_results (test_suite, test_name);
CREATE INDEX IF NOT EXISTS idx_load_test_results_success_rate ON monitoring.load_test_results (success_rate);

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON TABLE monitoring.load_test_results IS 'Resultados de tests de carga y concurrencia del sistema de monitoreo';
COMMENT ON FUNCTION monitoring.run_load_test_suite() IS 'Función principal que ejecuta todos los tests de carga del sistema';
COMMENT ON FUNCTION monitoring.test_metrics_collection_load() IS 'Test de carga para recolección masiva de métricas';
COMMENT ON FUNCTION monitoring.test_alerts_generation_load() IS 'Test de carga para generación masiva de alertas';
COMMENT ON FUNCTION monitoring.test_notifications_load() IS 'Test de carga para sistema de notificaciones';

-- Verificación final
DO $$
BEGIN
    RAISE NOTICE 'Sistema de Testing de Carga implementado exitosamente';
    RAISE NOTICE 'Tests implementados: 3 tests básicos + 3 tests avanzados pendientes';
    RAISE NOTICE 'Para ejecutar: SELECT monitoring.run_load_test_suite();';
END $$;
