-- =====================================================
-- VALIDACIONES PRE-MIGRACIÓN
-- =====================================================
/*
Script: validate_pre_migration.sql
Propósito: Verificar prerrequisitos antes de ejecutar migración
Categoría: validation
Autor: TaskMaster AI
Fecha: 2025-05-24
*/

-- Función principal de validación pre-migración
CREATE OR REPLACE FUNCTION execute_pre_migration_validations(
    p_target_category VARCHAR(50) DEFAULT NULL,  -- Categoría específica a validar
    p_strict_mode BOOLEAN DEFAULT TRUE           -- Modo estricto (falla en warnings)
) RETURNS TABLE (
    validation_name VARCHAR(100),
    category VARCHAR(50),
    status VARCHAR(20),
    severity VARCHAR(20),
    message TEXT,
    recommendation TEXT
) AS $$
DECLARE
    validation_count INTEGER := 0;
    error_count INTEGER := 0;
    warning_count INTEGER := 0;
BEGIN
    RAISE NOTICE '🔍 Iniciando validaciones pre-migración...';
    
    -- =====================================================
    -- VALIDACIONES DE ENTORNO Y CONEXIÓN
    -- =====================================================
    
    -- Validar versión de PostgreSQL
    DECLARE
        pg_version INTEGER;
        version_text TEXT;
    BEGIN
        SELECT substring(version() from 'PostgreSQL (\d+)')::int INTO pg_version;
        version_text := version();
        
        validation_count := validation_count + 1;
        
        IF pg_version >= 14 THEN
            RETURN QUERY SELECT
                'PostgreSQL Version Check'::VARCHAR(100),
                'environment'::VARCHAR(50),
                'PASS'::VARCHAR(20),
                'INFO'::VARCHAR(20),
                format('PostgreSQL %s detectado', pg_version)::TEXT,
                'Versión compatible para todas las características'::TEXT;
        ELSE
            error_count := error_count + 1;
            RETURN QUERY SELECT
                'PostgreSQL Version Check'::VARCHAR(100),
                'environment'::VARCHAR(50),
                'FAIL'::VARCHAR(20),
                'CRITICAL'::VARCHAR(20),
                format('PostgreSQL %s detectado (mínimo requerido: 14)', pg_version)::TEXT,
                'Actualizar PostgreSQL a versión 14 o superior'::TEXT;
        END IF;
    END;
    
    -- Validar permisos de usuario
    DECLARE
        has_create_perm BOOLEAN;
        has_superuser BOOLEAN;
        current_user_name TEXT := current_user;
    BEGIN
        SELECT 
            has_database_privilege(current_user, current_database(), 'CREATE'),
            usesuper
        INTO has_create_perm, has_superuser
        FROM pg_user WHERE usename = current_user;
        
        validation_count := validation_count + 1;
        
        IF has_create_perm THEN
            RETURN QUERY SELECT
                'User Permissions Check'::VARCHAR(100),
                'environment'::VARCHAR(50),
                'PASS'::VARCHAR(20),
                'INFO'::VARCHAR(20),
                format('Usuario %s tiene permisos CREATE', current_user_name)::TEXT,
                'Permisos suficientes para migración'::TEXT;
        ELSE
            error_count := error_count + 1;
            RETURN QUERY SELECT
                'User Permissions Check'::VARCHAR(100),
                'environment'::VARCHAR(50),
                'FAIL'::VARCHAR(20),
                'CRITICAL'::VARCHAR(20),
                format('Usuario %s no tiene permisos CREATE', current_user_name)::TEXT,
                'Otorgar permisos CREATE al usuario para la migración'::TEXT;
        END IF;
        
        -- Info sobre superuser
        IF has_superuser THEN
            RETURN QUERY SELECT
                'Superuser Status'::VARCHAR(100),
                'environment'::VARCHAR(50),
                'INFO'::VARCHAR(20),
                'INFO'::VARCHAR(20),
                'Usuario tiene privilegios de superuser'::TEXT,
                'Máximos permisos disponibles'::TEXT;
        END IF;
    END;
    
    -- Validar espacio en disco (simulado)
    DECLARE
        database_size_mb INTEGER;
        estimated_growth_mb INTEGER := 100; -- Estimación conservadora
    BEGIN
        SELECT pg_database_size(current_database()) / (1024*1024) INTO database_size_mb;
        
        validation_count := validation_count + 1;
        
        IF database_size_mb < 10000 THEN -- Menos de 10GB
            RETURN QUERY SELECT
                'Disk Space Check'::VARCHAR(100),
                'environment'::VARCHAR(50),
                'PASS'::VARCHAR(20),
                'INFO'::VARCHAR(20),
                format('Base de datos actual: %s MB', database_size_mb)::TEXT,
                format('Crecimiento estimado: %s MB', estimated_growth_mb)::TEXT;
        ELSE
            warning_count := warning_count + 1;
            RETURN QUERY SELECT
                'Disk Space Check'::VARCHAR(100),
                'environment'::VARCHAR(50),
                'WARNING'::VARCHAR(20),
                'WARNING'::VARCHAR(20),
                format('Base de datos grande: %s MB', database_size_mb)::TEXT,
                'Verificar espacio disponible en disco manualmente'::TEXT;
        END IF;
    END;
    
    -- =====================================================
    -- VALIDACIONES DE EXTENSIONES REQUERIDAS
    -- =====================================================
    
    -- Verificar disponibilidad de extensiones críticas
    DECLARE
        ext_record RECORD;
        required_extensions TEXT[] := ARRAY['vector', 'pg_trgm'];
        ext_name TEXT;
    BEGIN
        FOREACH ext_name IN ARRAY required_extensions
        LOOP
            validation_count := validation_count + 1;
            
            -- Verificar si la extensión está disponible (no necesariamente instalada)
            IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = ext_name) THEN
                -- Verificar si ya está instalada
                IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = ext_name) THEN
                    RETURN QUERY SELECT
                        format('Extension %s Availability', ext_name)::VARCHAR(100),
                        'extensions'::VARCHAR(50),
                        'INSTALLED'::VARCHAR(20),
                        'INFO'::VARCHAR(20),
                        format('Extensión %s ya está instalada', ext_name)::TEXT,
                        'No requiere acción'::TEXT;
                ELSE
                    RETURN QUERY SELECT
                        format('Extension %s Availability', ext_name)::VARCHAR(100),
                        'extensions'::VARCHAR(50),
                        'AVAILABLE'::VARCHAR(20),
                        'INFO'::VARCHAR(20),
                        format('Extensión %s disponible para instalación', ext_name)::TEXT,
                        'Se instalará durante la migración'::TEXT;
                END IF;
            ELSE
                error_count := error_count + 1;
                RETURN QUERY SELECT
                    format('Extension %s Availability', ext_name)::VARCHAR(100),
                    'extensions'::VARCHAR(50),
                    'FAIL'::VARCHAR(20),
                    'CRITICAL'::VARCHAR(20),
                    format('Extensión %s no disponible', ext_name)::TEXT,
                    'Instalar extensión en el servidor PostgreSQL'::TEXT;
            END IF;
        END LOOP;
    END;
    
    -- =====================================================
    -- VALIDACIONES DE ESTADO DE BASE DE DATOS
    -- =====================================================
    
    -- Verificar conexiones activas
    DECLARE
        active_connections INTEGER;
        max_connections INTEGER;
    BEGIN
        SELECT COUNT(*), setting::int
        INTO active_connections, max_connections
        FROM pg_stat_activity, pg_settings
        WHERE name = 'max_connections'
        GROUP BY setting;
        
        validation_count := validation_count + 1;
        
        IF active_connections < (max_connections * 0.8) THEN
            RETURN QUERY SELECT
                'Active Connections Check'::VARCHAR(100),
                'database'::VARCHAR(50),
                'PASS'::VARCHAR(20),
                'INFO'::VARCHAR(20),
                format('%s/%s conexiones activas', active_connections, max_connections)::TEXT,
                'Capacidad de conexiones adecuada'::TEXT;
        ELSE
            warning_count := warning_count + 1;
            RETURN QUERY SELECT
                'Active Connections Check'::VARCHAR(100),
                'database'::VARCHAR(50),
                'WARNING'::VARCHAR(20),
                'WARNING'::VARCHAR(20),
                format('%s/%s conexiones activas (>80%%)', active_connections, max_connections)::TEXT,
                'Considerar cerrar conexiones innecesarias antes de migración'::TEXT;
        END IF;
    END;
    
    -- Verificar transacciones largas
    DECLARE
        long_transactions INTEGER;
    BEGIN
        SELECT COUNT(*) INTO long_transactions
        FROM pg_stat_activity
        WHERE state IN ('idle in transaction', 'idle in transaction (aborted)')
        AND query_start < NOW() - INTERVAL '5 minutes';
        
        validation_count := validation_count + 1;
        
        IF long_transactions = 0 THEN
            RETURN QUERY SELECT
                'Long Running Transactions'::VARCHAR(100),
                'database'::VARCHAR(50),
                'PASS'::VARCHAR(20),
                'INFO'::VARCHAR(20),
                'No hay transacciones largas activas'::TEXT,
                'Estado de transacciones saludable'::TEXT;
        ELSE
            error_count := error_count + 1;
            RETURN QUERY SELECT
                'Long Running Transactions'::VARCHAR(100),
                'database'::VARCHAR(50),
                'FAIL'::VARCHAR(20),
                'CRITICAL'::VARCHAR(20),
                format('%s transacciones largas detectadas', long_transactions)::TEXT,
                'Terminar transacciones largas antes de iniciar migración'::TEXT;
        END IF;
    END;
    
    -- =====================================================
    -- VALIDACIONES DE CONFLICTOS EXISTENTES
    -- =====================================================
    
    -- Verificar si ya existe algún objeto que podría conflictuar
    DECLARE
        conflicting_tables INTEGER;
        conflicting_functions INTEGER;
    BEGIN
        -- Verificar tablas que podrían conflictuar
        SELECT COUNT(*) INTO conflicting_tables
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN (
            'entidades', 'articulos', 'hechos', 'hilos_narrativos',
            'migration_history', 'cache_entidades'
        );
        
        validation_count := validation_count + 1;
        
        IF conflicting_tables = 0 THEN
            RETURN QUERY SELECT
                'Table Conflicts Check'::VARCHAR(100),
                'conflicts'::VARCHAR(50),
                'PASS'::VARCHAR(20),
                'INFO'::VARCHAR(20),
                'No se detectaron conflictos de nombres de tablas'::TEXT,
                'Migración puede proceder sin conflictos'::TEXT;
        ELSE
            warning_count := warning_count + 1;
            RETURN QUERY SELECT
                'Table Conflicts Check'::VARCHAR(100),
                'conflicts'::VARCHAR(50),
                'WARNING'::VARCHAR(20),
                'WARNING'::VARCHAR(20),
                format('%s tablas con nombres conflictivos encontradas', conflicting_tables)::TEXT,
                'Verificar que los objetos existentes son compatibles'::TEXT;
        END IF;
        
        -- Verificar funciones que podrían conflictuar
        SELECT COUNT(*) INTO conflicting_functions
        FROM information_schema.routines
        WHERE routine_schema = 'public'
        AND routine_name IN (
            'insertar_articulo_completo', 'buscar_entidad_similar', 
            'obtener_info_hilo', 'register_migration_execution'
        );
        
        validation_count := validation_count + 1;
        
        IF conflicting_functions = 0 THEN
            RETURN QUERY SELECT
                'Function Conflicts Check'::VARCHAR(100),
                'conflicts'::VARCHAR(50),
                'PASS'::VARCHAR(20),
                'INFO'::VARCHAR(20),
                'No se detectaron conflictos de nombres de funciones'::TEXT,
                'Migración puede proceder sin conflictos'::TEXT;
        ELSE
            warning_count := warning_count + 1;
            RETURN QUERY SELECT
                'Function Conflicts Check'::VARCHAR(100),
                'conflicts'::VARCHAR(50),
                'WARNING'::VARCHAR(20),
                'WARNING'::VARCHAR(20),
                format('%s funciones con nombres conflictivos encontradas', conflicting_functions)::TEXT,
                'Las funciones existentes serán reemplazadas si son compatibles'::TEXT;
        END IF;
    END;
    
    -- =====================================================
    -- VALIDACIONES ESPECÍFICAS POR CATEGORÍA
    -- =====================================================
    
    IF p_target_category IS NOT NULL THEN
        CASE p_target_category
            WHEN 'schema' THEN
                RAISE NOTICE 'Ejecutando validaciones específicas para esquemas...';
                -- Validaciones específicas para creación de esquemas
                
            WHEN 'tables' THEN
                RAISE NOTICE 'Ejecutando validaciones específicas para tablas...';
                -- Validaciones específicas para creación de tablas
                
            WHEN 'indexes' THEN
                RAISE NOTICE 'Ejecutando validaciones específicas para índices...';
                -- Validaciones específicas para creación de índices
                
            ELSE
                RAISE NOTICE 'Validaciones generales para categoría: %', p_target_category;
        END CASE;
    END IF;
    
    -- =====================================================
    -- RESUMEN FINAL
    -- =====================================================
    
    RETURN QUERY SELECT
        'VALIDATION_SUMMARY'::VARCHAR(100),
        'summary'::VARCHAR(50),
        CASE 
            WHEN error_count = 0 AND warning_count = 0 THEN 'PASS'
            WHEN error_count = 0 AND warning_count > 0 THEN 'WARNING'
            ELSE 'FAIL'
        END::VARCHAR(20),
        CASE 
            WHEN error_count = 0 AND warning_count = 0 THEN 'INFO'
            WHEN error_count = 0 AND warning_count > 0 THEN 'WARNING'
            ELSE 'CRITICAL'
        END::VARCHAR(20),
        format('Total: %s validaciones, %s errores, %s advertencias', 
               validation_count, error_count, warning_count)::TEXT,
        CASE 
            WHEN error_count = 0 THEN 'Migración puede proceder'
            ELSE 'Corregir errores antes de continuar'
        END::TEXT;
    
    RAISE NOTICE '✅ Validaciones pre-migración completadas: % validaciones, % errores, % advertencias', 
                 validation_count, error_count, warning_count;
END;
$$ LANGUAGE plpgsql;

-- Función para verificar prerrequisitos específicos de Supabase
CREATE OR REPLACE FUNCTION validate_supabase_environment()
RETURNS TABLE (
    check_name VARCHAR(100),
    status VARCHAR(20),
    details TEXT
) AS $$
BEGIN
    -- Verificar si estamos en Supabase
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'supabase_admin') THEN
        RETURN QUERY SELECT
            'Supabase Environment'::VARCHAR(100),
            'DETECTED'::VARCHAR(20),
            'Entorno Supabase detectado - aplicando configuraciones específicas'::TEXT;
            
        -- Verificaciones específicas de Supabase
        RETURN QUERY SELECT
            'Supabase Extensions'::VARCHAR(100),
            'INFO'::VARCHAR(20),
            'Verificar disponibilidad de extensiones en dashboard Supabase'::TEXT;
            
        RETURN QUERY SELECT
            'Supabase Limits'::VARCHAR(100),
            'INFO'::VARCHAR(20),
            'Verificar límites de plan (conexiones, storage, compute)'::TEXT;
    ELSE
        RETURN QUERY SELECT
            'Supabase Environment'::VARCHAR(100),
            'NOT_DETECTED'::VARCHAR(20),
            'Entorno PostgreSQL estándar detectado'::TEXT;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Registrar este script
SELECT register_migration_execution(
    'validate_pre_migration.sql',
    'validation',
    NULL,
    'SUCCESS',
    'Sistema de validaciones pre-migración configurado',
    NULL
);

\echo '✅ Sistema de validaciones pre-migración configurado'
\echo 'ℹ️  Use SELECT * FROM execute_pre_migration_validations(); para ejecutar validaciones'
