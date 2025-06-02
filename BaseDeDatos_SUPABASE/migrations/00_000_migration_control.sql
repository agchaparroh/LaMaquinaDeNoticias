-- =====================================================
-- TABLA DE CONTROL DE MIGRACIÓN
-- =====================================================
-- Archivo: 00_000_migration_control.sql
-- Propósito: Crear tabla de control para tracking de migración
-- Prioridad: CRÍTICA - Debe ejecutarse antes que cualquier otro script
-- Idempotente: SÍ

BEGIN;

-- Crear tabla de control de migración si no existe
CREATE TABLE IF NOT EXISTS migration_history (
    id SERIAL PRIMARY KEY,
    script_name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    executed_at TIMESTAMP DEFAULT NOW(),
    execution_time_ms INTEGER,
    status VARCHAR(20) DEFAULT 'SUCCESS' CHECK (status IN ('SUCCESS', 'FAILED', 'ROLLBACK')),
    error_message TEXT,
    rollback_available BOOLEAN DEFAULT TRUE,
    checksum VARCHAR(64), -- Para verificar integridad del script
    created_by VARCHAR(100) DEFAULT current_user
);

-- Crear índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_migration_history_script_name 
ON migration_history(script_name);

CREATE INDEX IF NOT EXISTS idx_migration_history_category 
ON migration_history(category);

CREATE INDEX IF NOT EXISTS idx_migration_history_executed_at 
ON migration_history(executed_at DESC);

CREATE INDEX IF NOT EXISTS idx_migration_history_status 
ON migration_history(status);

-- Función para registrar ejecución de script
CREATE OR REPLACE FUNCTION register_migration_execution(
    p_script_name VARCHAR(255),
    p_category VARCHAR(50),
    p_execution_time_ms INTEGER DEFAULT NULL,
    p_status VARCHAR(20) DEFAULT 'SUCCESS',
    p_error_message TEXT DEFAULT NULL,
    p_checksum VARCHAR(64) DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    v_id INTEGER;
BEGIN
    INSERT INTO migration_history (
        script_name,
        category,
        execution_time_ms,
        status,
        error_message,
        rollback_available,
        checksum,
        created_by
    ) VALUES (
        p_script_name,
        p_category,
        p_execution_time_ms,
        p_status,
        p_error_message,
        CASE WHEN p_status = 'SUCCESS' THEN TRUE ELSE FALSE END,
        p_checksum,
        current_user
    )
    ON CONFLICT (script_name) 
    DO UPDATE SET
        executed_at = NOW(),
        execution_time_ms = p_execution_time_ms,
        status = p_status,
        error_message = p_error_message,
        created_by = current_user
    RETURNING id INTO v_id;
    
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- Función para verificar si un script ya fue ejecutado
CREATE OR REPLACE FUNCTION is_script_executed(p_script_name VARCHAR(255)) 
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM migration_history 
        WHERE script_name = p_script_name 
        AND status = 'SUCCESS'
    );
END;
$$ LANGUAGE plpgsql;

-- Función para obtener el último script ejecutado por categoría
CREATE OR REPLACE FUNCTION get_last_executed_script(p_category VARCHAR(50)) 
RETURNS VARCHAR(255) AS $$
DECLARE
    v_script_name VARCHAR(255);
BEGIN
    SELECT script_name INTO v_script_name
    FROM migration_history 
    WHERE category = p_category 
    AND status = 'SUCCESS'
    ORDER BY executed_at DESC 
    LIMIT 1;
    
    RETURN COALESCE(v_script_name, 'NONE');
END;
$$ LANGUAGE plpgsql;

-- Función para obtener estadísticas de migración
CREATE OR REPLACE FUNCTION get_migration_stats() 
RETURNS TABLE (
    category VARCHAR(50),
    total_scripts INTEGER,
    successful_scripts INTEGER,
    failed_scripts INTEGER,
    last_execution TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mh.category,
        COUNT(*)::INTEGER as total_scripts,
        COUNT(CASE WHEN mh.status = 'SUCCESS' THEN 1 END)::INTEGER as successful_scripts,
        COUNT(CASE WHEN mh.status = 'FAILED' THEN 1 END)::INTEGER as failed_scripts,
        MAX(mh.executed_at) as last_execution
    FROM migration_history mh
    GROUP BY mh.category
    ORDER BY mh.category;
END;
$$ LANGUAGE plpgsql;

-- Registrar la creación de esta tabla de control
SELECT register_migration_execution(
    '00_000_migration_control.sql',
    'infrastructure',
    NULL,
    'SUCCESS',
    'Tabla de control de migración creada exitosamente',
    NULL
);

-- Mostrar información de la tabla creada
SELECT 
    'migration_history' as table_name,
    COUNT(*) as initial_records,
    NOW() as created_at;

COMMIT;

-- Mensaje de confirmación
\echo 'Tabla de control de migración creada exitosamente'
\echo 'Funciones auxiliares disponibles:'
\echo '- register_migration_execution(): Registra ejecución de script'
\echo '- is_script_executed(): Verifica si script ya fue ejecutado'
\echo '- get_last_executed_script(): Obtiene último script por categoría'
\echo '- get_migration_stats(): Estadísticas de migración'
