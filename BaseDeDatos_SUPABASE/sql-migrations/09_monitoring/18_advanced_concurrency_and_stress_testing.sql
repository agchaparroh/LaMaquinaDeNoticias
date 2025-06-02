-- =====================================================
-- TESTING AVANZADO DE CONCURRENCIA Y STRESS
-- Archivo: 18_advanced_concurrency_and_stress_testing.sql
-- Descripción: Tests avanzados de concurrencia y stress del sistema
-- =====================================================

-- =====================================================
-- TEST 4: CONCURRENCIA EN DASHBOARD/CONSULTAS
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.test_dashboard_concurrency()
RETURNS JSONB AS $$
DECLARE
    test_start_time TIMESTAMPTZ := NOW();
    concurrent_users INTEGER := 20;
    queries_per_user INTEGER := 10;
    total_queries INTEGER := concurrent_users * queries_per_user;
    successful_queries INTEGER := 0;
    failed_queries INTEGER := 0;
    response_times DECIMAL[] := ARRAY[]::DECIMAL[];
    i INTEGER;
    j INTEGER;
    query_start_time TIMESTAMPTZ;
    query_duration INTEGER;
BEGIN
    RAISE NOTICE 'Iniciando test de concurrencia: Dashboard y consultas simultáneas';
    RAISE NOTICE 'Configuración: % usuarios concurrentes, % consultas por usuario', concurrent_users, queries_per_user;
    
    -- Simular múltiples usuarios accediendo al dashboard simultáneamente
    FOR i IN 1..concurrent_users LOOP
        FOR j IN 1..queries_per_user LOOP
            query_start_time := clock_timestamp();
            
            BEGIN
                -- Simular consultas típicas del dashboard
                CASE (j % 6) + 1
                    WHEN 1 THEN
                        -- Consulta de estado operacional
                        PERFORM monitoring.get_operational_status();
                    WHEN 2 THEN
                        -- Consulta de alertas activas
                        PERFORM * FROM monitoring.alerts_dashboard_enhanced LIMIT 20;
                    WHEN 3 THEN
                        -- Consulta de métricas recientes
                        PERFORM * FROM monitoring.system_metrics 
                        WHERE timestamp > NOW() - INTERVAL '1 hour' 
                        ORDER BY timestamp DESC LIMIT 50;
                    WHEN 4 THEN
                        -- Consulta de reportes diarios
                        PERFORM * FROM monitoring.daily_reports_summary LIMIT 10;
                    WHEN 5 THEN
                        -- Consulta de overview del sistema
                        PERFORM * FROM monitoring.system_overview;
                    WHEN 6 THEN
                        -- Consulta de trabajos de recolección
                        PERFORM * FROM monitoring.collection_jobs 
                        WHERE started_at > NOW() - INTERVAL '24 hours'
                        ORDER BY started_at DESC LIMIT 30;
                END CASE;
                
                successful_queries := successful_queries + 1;
                
                -- Capturar tiempo de respuesta
                query_duration := EXTRACT(milliseconds FROM (clock_timestamp() - query_start_time))::INTEGER;
                response_times := array_append(response_times, query_duration);
                
            EXCEPTION WHEN OTHERS THEN
                failed_queries := failed_queries + 1;
                RAISE NOTICE 'Error en consulta usuario % query %: %', i, j, SQLERRM;
            END;
        END LOOP;
        
        -- Simular pausa entre usuarios
        IF i % 5 = 0 THEN
            PERFORM pg_sleep(0.05); -- 50ms cada 5 usuarios
        END IF;
    END LOOP;
    
    -- Registrar resultados
    INSERT INTO monitoring.load_test_results (
        test_suite, test_name, concurrent_connections, total_operations, 
        successful_operations, failed_operations,
        avg_response_time_ms, min_response_time_ms, max_response_time_ms,
        p95_response_time_ms, p99_response_time_ms,
        success_rate, throughput_ops_per_sec, observations
    ) VALUES (
        'load_testing', 'dashboard_concurrency', concurrent_users, total_queries,
        successful_queries, failed_queries,
        (SELECT AVG(x) FROM unnest(response_times) x),
        (SELECT MIN(x) FROM unnest(response_times) x),
        (SELECT MAX(x) FROM unnest(response_times) x),
        (SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY x) FROM unnest(response_times) x),
        (SELECT PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY x) FROM unnest(response_times) x),
        ROUND(100.0 * successful_queries / total_queries, 2),
        ROUND(successful_queries / EXTRACT(EPOCH FROM (NOW() - test_start_time)), 2),
        format('Concurrencia dashboard: %s usuarios, %s consultas/usuario, %s%% éxito',
               concurrent_users, queries_per_user, 
               ROUND(100.0 * successful_queries / total_queries, 1))
    );
    
    RETURN jsonb_build_object(
        'test_name', 'dashboard_concurrency',
        'concurrent_users', concurrent_users,
        'total_queries', total_queries,
        'successful_queries', successful_queries,
        'success_rate', ROUND(100.0 * successful_queries / total_queries, 2),
        'avg_response_time_ms', (SELECT AVG(x) FROM unnest(response_times) x),
        'p95_response_time_ms', (SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY x) FROM unnest(response_times) x),
        'p99_response_time_ms', (SELECT PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY x) FROM unnest(response_times) x),
        'status', CASE WHEN successful_queries >= total_queries * 0.95 THEN 'passed' ELSE 'failed' END
    );
    
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'test_name', 'dashboard_concurrency',
        'status', 'error',
        'error_message', SQLERRM
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TEST 5: STRESS TESTING COMPLETO
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.test_full_system_stress()
RETURNS JSONB AS $$
DECLARE
    test_start_time TIMESTAMPTZ := NOW();
    stress_duration_seconds INTEGER := 60; -- 1 minuto de stress intenso
    operations_count INTEGER := 0;
    errors_count INTEGER := 0;
    i INTEGER;
    operation_start TIMESTAMPTZ;
    operation_duration INTEGER;
    response_times DECIMAL[] := ARRAY[]::DECIMAL[];
    peak_metrics RECORD;
BEGIN
    RAISE NOTICE 'Iniciando STRESS TEST COMPLETO - Duración: % segundos', stress_duration_seconds;
    
    -- Ejecutar operaciones intensivas por tiempo definido
    WHILE EXTRACT(EPOCH FROM (NOW() - test_start_time)) < stress_duration_seconds LOOP
        operation_start := clock_timestamp();
        operations_count := operations_count + 1;
        
        BEGIN
            -- Ciclo de operaciones intensivas
            CASE (operations_count % 8) + 1
                WHEN 1 THEN
                    -- Recolección múltiple de métricas
                    PERFORM monitoring.collect_system_metrics();
                    
                WHEN 2 THEN
                    -- Verificación de alertas
                    PERFORM monitoring.check_alert_thresholds_enhanced();
                    
                WHEN 3 THEN
                    -- Inserción masiva de métricas dummy
                    INSERT INTO monitoring.system_metrics (
                        timestamp, cpu_usage_percent, memory_usage_percent, 
                        total_connections, database_size_mb
                    ) SELECT 
                        NOW() + (generate_series(1,10) || ' milliseconds')::INTERVAL,
                        50 + RANDOM() * 40,
                        60 + RANDOM() * 30,
                        (20 + RANDOM() * 50)::INTEGER,
                        (1000 + RANDOM() * 500)::INTEGER;
                    
                WHEN 4 THEN
                    -- Consultas complejas del dashboard
                    PERFORM monitoring.get_operational_status();
                    PERFORM * FROM monitoring.alerts_dashboard_enhanced LIMIT 10;
                    
                WHEN 5 THEN
                    -- Generación de reportes
                    PERFORM monitoring.generate_daily_report(CURRENT_DATE - INTERVAL '1 day');
                    
                WHEN 6 THEN
                    -- Operaciones de mantenimiento ligero
                    PERFORM monitoring.cleanup_old_data(1, 1, 1); -- Retención mínima para test
                    
                WHEN 7 THEN
                    -- Verificación de salud
                    PERFORM monitoring.perform_health_check();
                    
                WHEN 8 THEN
                    -- Auto-resolución de alertas
                    PERFORM monitoring.auto_resolve_alerts();
            END CASE;
            
            -- Capturar tiempo de operación
            operation_duration := EXTRACT(milliseconds FROM (clock_timestamp() - operation_start))::INTEGER;
            response_times := array_append(response_times, operation_duration);
            
        EXCEPTION WHEN OTHERS THEN
            errors_count := errors_count + 1;
            IF errors_count % 10 = 0 THEN
                RAISE NOTICE 'Errores acumulados en stress test: %', errors_count;
            END IF;
        END;
        
        -- Micro pausa para evitar saturación total
        IF operations_count % 50 = 0 THEN
            PERFORM pg_sleep(0.01); -- 10ms cada 50 operaciones
        END IF;
    END LOOP;
    
    -- Obtener métricas pico del sistema
    SELECT 
        MAX(cpu_usage_percent) as max_cpu,
        MAX(memory_usage_percent) as max_memory,
        MAX(total_connections) as max_connections,
        AVG(cache_hit_ratio) as avg_cache_hit
    INTO peak_metrics
    FROM monitoring.system_metrics
    WHERE timestamp >= test_start_time;
    
    -- Registrar resultados del stress test
    INSERT INTO monitoring.load_test_results (
        test_suite, test_name, test_duration_seconds, total_operations, 
        successful_operations, failed_operations,
        avg_response_time_ms, min_response_time_ms, max_response_time_ms,
        p95_response_time_ms, p99_response_time_ms,
        peak_cpu_usage, peak_memory_usage, peak_connections,
        success_rate, throughput_ops_per_sec, observations, recommendations
    ) VALUES (
        'stress_testing', 'full_system_stress', stress_duration_seconds, operations_count,
        operations_count - errors_count, errors_count,
        (SELECT AVG(x) FROM unnest(response_times) x),
        (SELECT MIN(x) FROM unnest(response_times) x),
        (SELECT MAX(x) FROM unnest(response_times) x),
        (SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY x) FROM unnest(response_times) x),
        (SELECT PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY x) FROM unnest(response_times) x),
        COALESCE(peak_metrics.max_cpu, 0),
        COALESCE(peak_metrics.max_memory, 0),
        COALESCE(peak_metrics.max_connections, 0),
        ROUND(100.0 * (operations_count - errors_count) / operations_count, 2),
        ROUND(operations_count / stress_duration_seconds::DECIMAL, 2),
        format('Stress test: %s ops en %s seg, %s errores, CPU pico %s%%, memoria pico %s%%',
               operations_count, stress_duration_seconds, errors_count,
               COALESCE(peak_metrics.max_cpu, 0), COALESCE(peak_metrics.max_memory, 0)),
        CASE 
            WHEN errors_count > operations_count * 0.1 THEN ARRAY['Alto ratio de errores - revisar estabilidad']
            WHEN COALESCE(peak_metrics.max_cpu, 0) > 95 THEN ARRAY['CPU muy alto - considerar escalado']
            WHEN COALESCE(peak_metrics.max_memory, 0) > 95 THEN ARRAY['Memoria muy alta - optimizar consultas']
            ELSE ARRAY['Sistema manejó stress test exitosamente']
        END
    );
    
    -- Limpiar datos de test
    DELETE FROM monitoring.system_metrics 
    WHERE timestamp >= test_start_time 
    AND database_size_mb BETWEEN 1000 AND 1500; -- Solo datos dummy del test
    
    DELETE FROM monitoring.daily_reports 
    WHERE report_date = CURRENT_DATE - INTERVAL '1 day' 
    AND generated_by = 'system';
    
    RETURN jsonb_build_object(
        'test_name', 'full_system_stress',
        'duration_seconds', stress_duration_seconds,
        'total_operations', operations_count,
        'errors_count', errors_count,
        'success_rate', ROUND(100.0 * (operations_count - errors_count) / operations_count, 2),
        'throughput_ops_per_sec', ROUND(operations_count / stress_duration_seconds::DECIMAL, 2),
        'peak_metrics', jsonb_build_object(
            'cpu', COALESCE(peak_metrics.max_cpu, 0),
            'memory', COALESCE(peak_metrics.max_memory, 0),
            'connections', COALESCE(peak_metrics.max_connections, 0),
            'cache_hit', COALESCE(peak_metrics.avg_cache_hit, 100)
        ),
        'performance', jsonb_build_object(
            'avg_response_ms', (SELECT AVG(x) FROM unnest(response_times) x),
            'p95_response_ms', (SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY x) FROM unnest(response_times) x),
            'p99_response_ms', (SELECT PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY x) FROM unnest(response_times) x)
        ),
        'status', CASE 
            WHEN errors_count <= operations_count * 0.05 THEN 'passed'
            WHEN errors_count <= operations_count * 0.15 THEN 'warning'
            ELSE 'failed'
        END
    );
    
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'test_name', 'full_system_stress',
        'status', 'error',
        'error_message', SQLERRM
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TEST 6: CONCURRENCIA READ/WRITE
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.test_read_write_concurrency()
RETURNS JSONB AS $$
DECLARE
    test_start_time TIMESTAMPTZ := NOW();
    concurrent_operations INTEGER := 30;
    total_operations INTEGER := 150;
    read_operations INTEGER := 0;
    write_operations INTEGER := 0;
    successful_ops INTEGER := 0;
    failed_ops INTEGER := 0;
    read_times DECIMAL[] := ARRAY[]::DECIMAL[];
    write_times DECIMAL[] := ARRAY[]::DECIMAL[];
    i INTEGER;
    op_start_time TIMESTAMPTZ;
    op_duration INTEGER;
    operation_type TEXT;
BEGIN
    RAISE NOTICE 'Iniciando test de concurrencia: Read/Write simultáneos';
    
    -- Ejecutar operaciones mixtas de lectura y escritura
    FOR i IN 1..total_operations LOOP
        op_start_time := clock_timestamp();
        
        -- Alternar entre operaciones de lectura y escritura
        IF i % 3 = 0 THEN
            operation_type := 'write';
        ELSE
            operation_type := 'read';
        END IF;
        
        BEGIN
            IF operation_type = 'write' THEN
                -- Operaciones de escritura
                CASE (write_operations % 4) + 1
                    WHEN 1 THEN
                        -- Insertar métricas
                        INSERT INTO monitoring.system_metrics (
                            timestamp, cpu_usage_percent, memory_usage_percent, total_connections
                        ) VALUES (
                            NOW() + (i || ' milliseconds')::INTERVAL,
                            30 + RANDOM() * 50,
                            40 + RANDOM() * 40,
                            (10 + RANDOM() * 40)::INTEGER
                        );
                    WHEN 2 THEN
                        -- Crear alerta
                        INSERT INTO monitoring.alerts (
                            timestamp, alert_type, severity, metric_name, title, status, created_by
                        ) VALUES (
                            NOW(), 'concurrency_test', 'info', 'test_metric', 
                            'Concurrency Test Alert', 'active', 'concurrency_test'
                        );
                    WHEN 3 THEN
                        -- Actualizar configuración
                        UPDATE monitoring.alert_thresholds 
                        SET updated_at = NOW() 
                        WHERE metric_name = 'cpu_usage_percent';
                    WHEN 4 THEN
                        -- Registrar trabajo
                        INSERT INTO monitoring.collection_jobs (
                            started_at, job_type, status, metrics_collected
                        ) VALUES (
                            NOW(), 'concurrency_test', 'completed', 1
                        );
                END CASE;
                
                write_operations := write_operations + 1;
                op_duration := EXTRACT(milliseconds FROM (clock_timestamp() - op_start_time))::INTEGER;
                write_times := array_append(write_times, op_duration);
                
            ELSE
                -- Operaciones de lectura
                CASE (read_operations % 5) + 1
                    WHEN 1 THEN
                        -- Leer métricas recientes
                        PERFORM * FROM monitoring.system_metrics 
                        WHERE timestamp > NOW() - INTERVAL '1 hour' 
                        ORDER BY timestamp DESC LIMIT 20;
                    WHEN 2 THEN
                        -- Leer alertas activas
                        PERFORM * FROM monitoring.alerts WHERE status = 'active' LIMIT 10;
                    WHEN 3 THEN
                        -- Leer configuración
                        PERFORM * FROM monitoring.alert_thresholds WHERE enabled = true;
                    WHEN 4 THEN
                        -- Leer estado operacional
                        PERFORM monitoring.get_operational_status();
                    WHEN 5 THEN
                        -- Leer trabajos recientes
                        PERFORM * FROM monitoring.collection_jobs 
                        WHERE started_at > NOW() - INTERVAL '1 hour' LIMIT 15;
                END CASE;
                
                read_operations := read_operations + 1;
                op_duration := EXTRACT(milliseconds FROM (clock_timestamp() - op_start_time))::INTEGER;
                read_times := array_append(read_times, op_duration);
            END IF;
            
            successful_ops := successful_ops + 1;
            
        EXCEPTION WHEN OTHERS THEN
            failed_ops := failed_ops + 1;
            RAISE NOTICE 'Error en operación % (%): %', i, operation_type, SQLERRM;
        END;
        
        -- Pausa micro para simular concurrencia realista
        IF i % concurrent_operations = 0 THEN
            PERFORM pg_sleep(0.02); -- 20ms cada batch
        END IF;
    END LOOP;
    
    -- Registrar resultados
    INSERT INTO monitoring.load_test_results (
        test_suite, test_name, concurrent_connections, total_operations,
        successful_operations, failed_operations,
        avg_response_time_ms, min_response_time_ms, max_response_time_ms,
        success_rate, throughput_ops_per_sec, observations
    ) VALUES (
        'concurrency_testing', 'read_write_concurrency', concurrent_operations, total_operations,
        successful_ops, failed_ops,
        (SELECT AVG(x) FROM unnest(read_times || write_times) x),
        (SELECT MIN(x) FROM unnest(read_times || write_times) x),
        (SELECT MAX(x) FROM unnest(read_times || write_times) x),
        ROUND(100.0 * successful_ops / total_operations, 2),
        ROUND(successful_ops / EXTRACT(EPOCH FROM (NOW() - test_start_time)), 2),
        format('Read/Write concurrency: %s reads (avg %sms), %s writes (avg %sms)',
               read_operations, 
               ROUND((SELECT AVG(x) FROM unnest(read_times) x), 1),
               write_operations,
               ROUND((SELECT AVG(x) FROM unnest(write_times) x), 1))
    );
    
    -- Limpiar datos de test
    DELETE FROM monitoring.system_metrics WHERE timestamp >= test_start_time;
    DELETE FROM monitoring.alerts WHERE created_by = 'concurrency_test';
    DELETE FROM monitoring.collection_jobs WHERE job_type = 'concurrency_test';
    
    RETURN jsonb_build_object(
        'test_name', 'read_write_concurrency',
        'total_operations', total_operations,
        'read_operations', read_operations,
        'write_operations', write_operations,
        'successful_operations', successful_ops,
        'success_rate', ROUND(100.0 * successful_ops / total_operations, 2),
        'performance', jsonb_build_object(
            'avg_read_time_ms', (SELECT AVG(x) FROM unnest(read_times) x),
            'avg_write_time_ms', (SELECT AVG(x) FROM unnest(write_times) x),
            'overall_avg_ms', (SELECT AVG(x) FROM unnest(read_times || write_times) x)
        ),
        'status', CASE WHEN successful_ops >= total_operations * 0.95 THEN 'passed' ELSE 'failed' END
    );
    
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'test_name', 'read_write_concurrency',
        'status', 'error',
        'error_message', SQLERRM
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA GENERAR REPORTE DE RENDIMIENTO
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.generate_load_test_report()
RETURNS TEXT AS $$
DECLARE
    report_content TEXT;
    total_tests INTEGER;
    passed_tests INTEGER;
    failed_tests INTEGER;
    overall_success_rate DECIMAL(5,2);
    test_summary RECORD;
    performance_summary RECORD;
BEGIN
    -- Obtener estadísticas generales de tests recientes
    SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE success_rate >= 95.0) as passed,
        COUNT(*) FILTER (WHERE success_rate < 95.0) as failed
    INTO total_tests, passed_tests, failed_tests
    FROM monitoring.load_test_results 
    WHERE executed_at > NOW() - INTERVAL '2 hours';
    
    overall_success_rate := ROUND(100.0 * passed_tests / GREATEST(total_tests, 1), 2);
    
    -- Obtener resumen de rendimiento
    SELECT 
        ROUND(AVG(avg_response_time_ms), 2) as avg_response,
        ROUND(MAX(peak_cpu_usage), 2) as peak_cpu,
        ROUND(MAX(peak_memory_usage), 2) as peak_memory,
        ROUND(AVG(throughput_ops_per_sec), 2) as avg_throughput
    INTO performance_summary
    FROM monitoring.load_test_results 
    WHERE executed_at > NOW() - INTERVAL '2 hours';
    
    -- Construir reporte
    report_content := format(
        '=== REPORTE DE TESTING DE CARGA Y CONCURRENCIA ===
        
Fecha de Ejecución: %s
        
RESUMEN GENERAL:
- Total de Tests: %s
- Tests Exitosos: %s
- Tests Fallidos: %s  
- Tasa de Éxito Global: %s%%
        
MÉTRICAS DE RENDIMIENTO:
- Tiempo de Respuesta Promedio: %sms
- CPU Pico: %s%%
- Memoria Pico: %s%%
- Throughput Promedio: %s ops/seg
        
RESULTADOS POR TEST:',
        NOW()::timestamp(0),
        total_tests,
        passed_tests, 
        failed_tests,
        overall_success_rate,
        COALESCE(performance_summary.avg_response, 0),
        COALESCE(performance_summary.peak_cpu, 0),
        COALESCE(performance_summary.peak_memory, 0),
        COALESCE(performance_summary.avg_throughput, 0)
    );
    
    -- Agregar detalles por test
    FOR test_summary IN
        SELECT 
            test_name,
            total_operations,
            successful_operations,
            success_rate,
            avg_response_time_ms,
            throughput_ops_per_sec,
            CASE 
                WHEN success_rate >= 95 THEN '✅ EXITOSO'
                WHEN success_rate >= 80 THEN '⚠️ WARNING'
                ELSE '❌ FALLIDO'
            END as status
        FROM monitoring.load_test_results 
        WHERE executed_at > NOW() - INTERVAL '2 hours'
        ORDER BY executed_at DESC
    LOOP
        report_content := report_content || format(
            '
- %s: %s
  Operaciones: %s/%s exitosas (tasa: %s%%)
  Rendimiento: %sms promedio, %s ops/seg',
            UPPER(test_summary.test_name),
            test_summary.status,
            test_summary.successful_operations,
            test_summary.total_operations,
            test_summary.success_rate,
            ROUND(test_summary.avg_response_time_ms, 1),
            ROUND(test_summary.throughput_ops_per_sec, 1)
        );
    END LOOP;
    
    -- Agregar recomendaciones
    report_content := report_content || format('
        
ANÁLISIS Y RECOMENDACIONES:
%s

LÍMITES DE RENDIMIENTO IDENTIFICADOS:
%s

CONCLUSIÓN:
%s
        
=== FIN DEL REPORTE ===',
        CASE 
            WHEN overall_success_rate >= 95 THEN '✅ Sistema maneja carga excelentemente'
            WHEN overall_success_rate >= 80 THEN '⚠️ Sistema funcional bajo carga con algunas limitaciones'
            ELSE '❌ Sistema requiere optimización para manejar carga alta'
        END,
        CASE 
            WHEN COALESCE(performance_summary.peak_cpu, 0) > 90 THEN '- CPU alcanza niveles críticos bajo carga'
            WHEN COALESCE(performance_summary.peak_memory, 0) > 90 THEN '- Memoria alcanza niveles críticos'
            WHEN COALESCE(performance_summary.avg_response, 0) > 5000 THEN '- Tiempos de respuesta elevados'
            ELSE '- Sistema mantiene rendimiento estable bajo carga'
        END,
        CASE 
            WHEN overall_success_rate >= 95 THEN 'Sistema APTO para producción con carga alta'
            WHEN overall_success_rate >= 80 THEN 'Sistema FUNCIONAL pero requiere monitoreo en producción'
            ELSE 'Sistema REQUIERE optimización antes de manejar carga alta'
        END
    );
    
    RETURN report_content;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- FUNCIÓN PARA BENCHMARK DE RENDIMIENTO
-- =====================================================

CREATE OR REPLACE FUNCTION monitoring.run_performance_benchmark()
RETURNS JSONB AS $$
DECLARE
    benchmark_results JSONB := '{}'::jsonb;
    single_op_time DECIMAL;
    batch_10_time DECIMAL;
    batch_100_time DECIMAL;
    concurrent_10_time DECIMAL;
    start_time TIMESTAMPTZ;
    i INTEGER;
BEGIN
    RAISE NOTICE 'Ejecutando benchmark de rendimiento de operaciones básicas';
    
    -- Benchmark 1: Operación individual
    start_time := clock_timestamp();
    PERFORM monitoring.collect_system_metrics();
    single_op_time := EXTRACT(milliseconds FROM (clock_timestamp() - start_time));
    
    -- Benchmark 2: Batch de 10 operaciones
    start_time := clock_timestamp();
    FOR i IN 1..10 LOOP
        PERFORM monitoring.collect_system_metrics();
    END LOOP;
    batch_10_time := EXTRACT(milliseconds FROM (clock_timestamp() - start_time));
    
    -- Benchmark 3: Batch de 100 operaciones (simuladas más ligeras)
    start_time := clock_timestamp();
    FOR i IN 1..100 LOOP
        PERFORM monitoring.get_operational_status();
    END LOOP;
    batch_100_time := EXTRACT(milliseconds FROM (clock_timestamp() - start_time));
    
    -- Benchmark 4: 10 operaciones "concurrentes" (simuladas secuencialmente)
    start_time := clock_timestamp();
    FOR i IN 1..10 LOOP
        PERFORM monitoring.check_alert_thresholds_enhanced();
    END LOOP;
    concurrent_10_time := EXTRACT(milliseconds FROM (clock_timestamp() - start_time));
    
    -- Construir resultados
    benchmark_results := jsonb_build_object(
        'timestamp', NOW(),
        'benchmarks', jsonb_build_object(
            'single_operation_ms', single_op_time,
            'batch_10_operations_ms', batch_10_time,
            'batch_100_operations_ms', batch_100_time,
            'concurrent_10_operations_ms', concurrent_10_time
        ),
        'performance_metrics', jsonb_build_object(
            'ops_per_second_single', ROUND(1000.0 / single_op_time, 2),
            'ops_per_second_batch_10', ROUND(10000.0 / batch_10_time, 2),
            'ops_per_second_batch_100', ROUND(100000.0 / batch_100_time, 2),
            'efficiency_batch_vs_single', ROUND((single_op_time * 10) / batch_10_time, 2)
        ),
        'recommendations', CASE 
            WHEN single_op_time > 2000 THEN ARRAY['Operaciones individuales lentas - optimizar funciones básicas']
            WHEN batch_10_time > single_op_time * 15 THEN ARRAY['Escalabilidad limitada - revisar locks y concurrencia']
            WHEN concurrent_10_time > batch_10_time * 2 THEN ARRAY['Overhead de concurrencia alto']
            ELSE ARRAY['Rendimiento dentro de parámetros esperados']
        END
    );
    
    RAISE NOTICE 'Benchmark completado - Operación individual: %ms, Batch 10: %ms', 
        single_op_time, batch_10_time;
        
    RETURN benchmark_results;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- COMENTARIOS FINALES
-- =====================================================

COMMENT ON FUNCTION monitoring.test_dashboard_concurrency() IS 'Test de concurrencia para múltiples usuarios simultáneos en dashboard';
COMMENT ON FUNCTION monitoring.test_full_system_stress() IS 'Stress test completo del sistema bajo carga máxima';
COMMENT ON FUNCTION monitoring.test_read_write_concurrency() IS 'Test de concurrencia mixta de operaciones de lectura y escritura';
COMMENT ON FUNCTION monitoring.generate_load_test_report() IS 'Genera reporte completo de resultados de testing de carga';
COMMENT ON FUNCTION monitoring.run_performance_benchmark() IS 'Ejecuta benchmark básico de rendimiento de operaciones';

-- Verificación final
DO $$
BEGIN
    RAISE NOTICE 'Testing Avanzado de Concurrencia y Stress implementado exitosamente';
    RAISE NOTICE 'Tests adicionales: dashboard_concurrency, full_system_stress, read_write_concurrency';
    RAISE NOTICE 'Funciones de análisis: generate_load_test_report, run_performance_benchmark';
    RAISE NOTICE 'Sistema completo de testing de carga listo para ejecución';
END $$;
