-- =====================================================
-- SISTEMA INTEGRADO DE VALIDACIONES AUTOMÁTICAS
-- =====================================================
/*
Script: automated_validation_system.sql
Propósito: Coordinar validaciones pre y post migración automáticamente
Categoría: validation
Autor: TaskMaster AI
Fecha: 2025-05-24
*/

-- Función para ejecutar validaciones automáticas en el flujo de migración
CREATE OR REPLACE FUNCTION execute_automated_validations(
    p_validation_type VARCHAR(10), -- 'pre' o 'post'
    p_category VARCHAR(50) DEFAULT NULL,
    p_strict_mode BOOLEAN DEFAULT TRUE,
    p_deep_validation BOOLEAN DEFAULT FALSE
) RETURNS TABLE (
    validation_id UUID,
    validation_type VARCHAR(10),
    category VARCHAR(50),
    total_validations INTEGER,
    passed INTEGER,
    failed INTEGER,
    warnings INTEGER,
    overall_status VARCHAR(20),
    execution_time_ms INTEGER,
    report_summary TEXT
) AS $$
DECLARE
    validation_uuid UUID := gen_random_uuid();
    start_time TIMESTAMP := clock_timestamp();
    total_time INTEGER;
    validation_results RECORD;
    v_total INTEGER := 0;
    v_passed INTEGER := 0;
    v_failed INTEGER := 0;
    v_warnings INTEGER := 0;
    v_overall_status VARCHAR(20);
    v_report TEXT := '';
BEGIN
    RAISE NOTICE '🚀 Iniciando validaciones automáticas: % (ID: %)', p_validation_type, validation_uuid;
    
    -- Ejecutar validaciones según el tipo
    IF p_validation_type = 'pre' THEN
        -- Ejecutar validaciones pre-migración
        FOR validation_results IN
            SELECT * FROM execute_pre_migration_validations(p_category, p_strict_mode)
        LOOP
            v_total := v_total + 1;
            
            CASE validation_results.status
                WHEN 'PASS' THEN v_passed := v_passed + 1;
                WHEN 'FAIL' THEN v_failed := v_failed + 1;
                WHEN 'WARNING' THEN v_warnings := v_warnings + 1;
                ELSE NULL;
            END CASE;
            
            -- Agregar al reporte si es crítico
            IF validation_results.severity IN ('CRITICAL', 'WARNING') THEN
                v_report := v_report || format('[%s] %s: %s | ', 
                    validation_results.severity,
                    validation_results.validation_name, 
                    validation_results.message);
            END IF;
        END LOOP;
        
    ELSIF p_validation_type = 'post' THEN
        -- Ejecutar validaciones post-migración
        FOR validation_results IN
            SELECT * FROM execute_post_migration_validations(p_category, p_deep_validation)
        LOOP
            v_total := v_total + 1;
            
            CASE validation_results.status
                WHEN 'PASS' THEN v_passed := v_passed + 1;
                WHEN 'FAIL' THEN v_failed := v_failed + 1;
                WHEN 'WARNING' THEN v_warnings := v_warnings + 1;
                ELSE NULL;
            END CASE;
            
            -- Agregar al reporte si es crítico
            IF validation_results.severity IN ('CRITICAL', 'WARNING') THEN
                v_report := v_report || format('[%s] %s: %s | ', 
                    validation_results.severity,
                    validation_results.validation_name, 
                    validation_results.message);
            END IF;
        END LOOP;
        
    ELSE
        RAISE EXCEPTION 'Tipo de validación inválido: %. Use ''pre'' o ''post''', p_validation_type;
    END IF;
    
    -- Determinar estado general
    IF v_failed > 0 THEN
        v_overall_status := 'FAILED';
    ELSIF v_warnings > 0 THEN
        v_overall_status := 'WARNING';
    ELSE
        v_overall_status := 'PASSED';
    END IF;
    
    total_time := EXTRACT(epoch FROM (clock_timestamp() - start_time)) * 1000;
    
    -- Limpiar reporte
    IF LENGTH(v_report) > 0 THEN
        v_report := LEFT(v_report, LENGTH(v_report) - 3); -- Remover último ' | '
    ELSE
        v_report := 'Todas las validaciones pasaron sin problemas';
    END IF;
    
    -- Registrar en el sistema de tracking
    PERFORM register_migration_execution(
        format('automated_validation_%s_%s', p_validation_type, validation_uuid),
        'validation',
        total_time,
        CASE WHEN v_overall_status = 'FAILED' THEN 'FAILED' ELSE 'SUCCESS' END,
        format('Validación %s: %s total, %s passed, %s failed, %s warnings', 
               p_validation_type, v_total, v_passed, v_failed, v_warnings),
        NULL
    );
    
    -- Retornar resumen
    RETURN QUERY SELECT
        validation_uuid,
        p_validation_type,
        COALESCE(p_category, 'all'),
        v_total,
        v_passed,
        v_failed,
        v_warnings,
        v_overall_status,
        total_time,
        v_report;
    
    RAISE NOTICE '✅ Validaciones % completadas: % total, % passed, % failed, % warnings (% ms)',
                 p_validation_type, v_total, v_passed, v_failed, v_warnings, total_time;
END;
$$ LANGUAGE plpgsql;

-- Función para ejecutar validaciones integradas en un script de migración
CREATE OR REPLACE FUNCTION validate_migration_step(
    p_script_name VARCHAR(255),
    p_category VARCHAR(50),
    p_validation_phase VARCHAR(10) -- 'pre' o 'post'
) RETURNS BOOLEAN AS $$
DECLARE
    validation_result RECORD;
    validation_passed BOOLEAN := TRUE;
BEGIN
    -- Ejecutar validaciones
    SELECT * INTO validation_result
    FROM execute_automated_validations(p_validation_phase, p_category);
    
    -- Verificar resultado
    IF validation_result.overall_status = 'FAILED' THEN
        validation_passed := FALSE;
        RAISE WARNING 'Validaciones % fallaron para script %: %', 
                      p_validation_phase, p_script_name, validation_result.report_summary;
    ELSIF validation_result.overall_status = 'WARNING' THEN
        RAISE NOTICE 'Validaciones % completadas con advertencias para script %: %', 
                     p_validation_phase, p_script_name, validation_result.report_summary;
    ELSE
        RAISE NOTICE 'Validaciones % pasaron exitosamente para script %', 
                     p_validation_phase, p_script_name;
    END IF;
    
    RETURN validation_passed;
END;
$$ LANGUAGE plpgsql;

-- Crear tabla para almacenar historial de validaciones
CREATE TABLE IF NOT EXISTS validation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    validation_type VARCHAR(10) NOT NULL,
    category VARCHAR(50),
    script_name VARCHAR(255),
    executed_at TIMESTAMP DEFAULT NOW(),
    total_validations INTEGER NOT NULL,
    passed INTEGER NOT NULL,
    failed INTEGER NOT NULL,
    warnings INTEGER NOT NULL,
    overall_status VARCHAR(20) NOT NULL,
    execution_time_ms INTEGER,
    report_summary TEXT,
    executed_by VARCHAR(100) DEFAULT current_user
);

-- Función para almacenar historial de validaciones
CREATE OR REPLACE FUNCTION store_validation_history(
    p_validation_type VARCHAR(10),
    p_category VARCHAR(50),
    p_script_name VARCHAR(255),
    p_total INTEGER,
    p_passed INTEGER,
    p_failed INTEGER,
    p_warnings INTEGER,
    p_status VARCHAR(20),
    p_execution_time INTEGER,
    p_report TEXT
) RETURNS UUID AS $$
DECLARE
    validation_id UUID := gen_random_uuid();
BEGIN
    INSERT INTO validation_history (
        id, validation_type, category, script_name,
        total_validations, passed, failed, warnings,
        overall_status, execution_time_ms, report_summary
    ) VALUES (
        validation_id, p_validation_type, p_category, p_script_name,
        p_total, p_passed, p_failed, p_warnings,
        p_status, p_execution_time, p_report
    );
    
    RETURN validation_id;
END;
$$ LANGUAGE plpgsql;

-- Vista para resumen de validaciones por categoría
CREATE OR REPLACE VIEW validation_summary_by_category AS
SELECT 
    category,
    validation_type,
    COUNT(*) as total_executions,
    AVG(total_validations) as avg_validations,
    AVG(execution_time_ms) as avg_execution_time_ms,
    COUNT(CASE WHEN overall_status = 'PASSED' THEN 1 END) as successful_runs,
    COUNT(CASE WHEN overall_status = 'FAILED' THEN 1 END) as failed_runs,
    COUNT(CASE WHEN overall_status = 'WARNING' THEN 1 END) as warning_runs,
    MAX(executed_at) as last_execution
FROM validation_history
GROUP BY category, validation_type
ORDER BY category, validation_type;

-- Función para generar reporte completo de validaciones
CREATE OR REPLACE FUNCTION generate_validation_report(
    p_days_back INTEGER DEFAULT 7
) RETURNS TABLE (
    metric VARCHAR(100),
    value TEXT
) AS $$
DECLARE
    total_validations INTEGER;
    successful_validations INTEGER;
    failed_validations INTEGER;
    avg_execution_time DECIMAL(10,2);
    most_problematic_category VARCHAR(50);
BEGIN
    -- Métricas generales
    SELECT 
        COUNT(*),
        COUNT(CASE WHEN overall_status = 'PASSED' THEN 1 END),
        COUNT(CASE WHEN overall_status = 'FAILED' THEN 1 END),
        AVG(execution_time_ms)
    INTO total_validations, successful_validations, failed_validations, avg_execution_time
    FROM validation_history
    WHERE executed_at >= NOW() - INTERVAL '%s days' % p_days_back;
    
    -- Categoría más problemática
    SELECT category INTO most_problematic_category
    FROM validation_history
    WHERE executed_at >= NOW() - INTERVAL '%s days' % p_days_back
    AND overall_status = 'FAILED'
    GROUP BY category
    ORDER BY COUNT(*) DESC
    LIMIT 1;
    
    -- Retornar métricas
    RETURN QUERY SELECT 'Total Validaciones'::VARCHAR(100), total_validations::TEXT;
    RETURN QUERY SELECT 'Validaciones Exitosas'::VARCHAR(100), successful_validations::TEXT;
    RETURN QUERY SELECT 'Validaciones Fallidas'::VARCHAR(100), failed_validations::TEXT;
    RETURN QUERY SELECT 'Tiempo Promedio (ms)'::VARCHAR(100), ROUND(avg_execution_time, 2)::TEXT;
    RETURN QUERY SELECT 'Categoría Más Problemática'::VARCHAR(100), COALESCE(most_problematic_category, 'Ninguna');
    
    RETURN QUERY SELECT 'Tasa de Éxito (%)'::VARCHAR(100), 
        CASE WHEN total_validations > 0 
             THEN ROUND((successful_validations::DECIMAL / total_validations * 100), 2)::TEXT
             ELSE '0' END;
END;
$$ LANGUAGE plpgsql;

-- Crear índices para optimizar consultas de validación
CREATE INDEX IF NOT EXISTS idx_validation_history_executed_at 
ON validation_history(executed_at DESC);

CREATE INDEX IF NOT EXISTS idx_validation_history_category_status 
ON validation_history(category, overall_status);

CREATE INDEX IF NOT EXISTS idx_validation_history_type_status 
ON validation_history(validation_type, overall_status);

-- Registrar este script
SELECT register_migration_execution(
    'automated_validation_system.sql',
    'validation',
    NULL,
    'SUCCESS',
    'Sistema integrado de validaciones automáticas configurado',
    NULL
);

-- =====================================================
-- EJEMPLOS DE USO
-- =====================================================

/*
-- Ejecutar validaciones pre-migración generales
SELECT * FROM execute_automated_validations('pre');

-- Ejecutar validaciones post-migración para categoría específica
SELECT * FROM execute_automated_validations('post', 'tables', false, true);

-- Validar un paso específico de migración
SELECT validate_migration_step('01_001_create_extensions_schemas.sql', 'schema', 'pre');

-- Ver resumen por categoría
SELECT * FROM validation_summary_by_category;

-- Generar reporte de los últimos 7 días
SELECT * FROM generate_validation_report(7);

-- Ver historial reciente de validaciones
SELECT 
    validation_type,
    category,
    overall_status,
    total_validations,
    execution_time_ms,
    executed_at
FROM validation_history
ORDER BY executed_at DESC
LIMIT 10;
*/

\echo '✅ Sistema integrado de validaciones automáticas configurado'
\echo 'ℹ️  Funciones principales:'
\echo '   - execute_automated_validations(type, category)'
\echo '   - validate_migration_step(script, category, phase)'
\echo '   - generate_validation_report(days)'
\echo 'ℹ️  Vistas disponibles: validation_summary_by_category'
