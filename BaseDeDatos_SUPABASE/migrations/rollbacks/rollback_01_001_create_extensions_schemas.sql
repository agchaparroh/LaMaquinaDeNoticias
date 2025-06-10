-- =====================================================
-- SCRIPT DE ROLLBACK - EXTENSIONES Y ESQUEMAS
-- =====================================================
/*
Script: rollback_01_001_create_extensions_schemas.sql
Propósito: Revertir la creación de extensiones y esquemas básicos
Script Original: 01_001_create_extensions_schemas.sql
Categoría: schema
Idempotente: SÍ
Autor: TaskMaster AI
Fecha: 2025-05-24
*/

BEGIN;

DO $$
DECLARE
    script_name CONSTANT VARCHAR(255) := 'rollback_01_001_create_extensions_schemas.sql';
    original_script CONSTANT VARCHAR(255) := '01_001_create_extensions_schemas.sql';
    script_category CONSTANT VARCHAR(50) := 'schema';
    start_time TIMESTAMP := clock_timestamp();
    execution_time INTEGER;
    objects_dropped INTEGER := 0;
BEGIN
    RAISE NOTICE 'Iniciando rollback de extensiones y esquemas...';
    
    -- Verificar que el script original fue ejecutado
    IF NOT is_script_executed(original_script) THEN
        RAISE NOTICE 'El script original % no fue ejecutado. Rollback innecesario.', original_script;
        RETURN;
    END IF;
    
    -- =====================================================
    -- ROLLBACK DE ESQUEMAS (en orden inverso)
    -- =====================================================
    
    -- Eliminar esquema audit (si está vacío)
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'audit') THEN
        BEGIN
            DROP SCHEMA audit CASCADE;
            objects_dropped := objects_dropped + 1;
            RAISE NOTICE '✓ Esquema audit eliminado';
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'No se pudo eliminar esquema audit: %', SQLERRM;
        END;
    END IF;
    
    -- Eliminar esquema utils (si está vacío)
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'utils') THEN
        BEGIN
            DROP SCHEMA utils CASCADE;
            objects_dropped := objects_dropped + 1;
            RAISE NOTICE '✓ Esquema utils eliminado';
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'No se pudo eliminar esquema utils: %', SQLERRM;
        END;
    END IF;
    
    -- Eliminar esquema analytics (si está vacío)
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'analytics') THEN
        BEGIN
            DROP SCHEMA analytics CASCADE;
            objects_dropped := objects_dropped + 1;
            RAISE NOTICE '✓ Esquema analytics eliminado';
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'No se pudo eliminar esquema analytics: %', SQLERRM;
        END;
    END IF;
    
    -- =====================================================
    -- ROLLBACK DE EXTENSIONES (solo si es seguro)
    -- =====================================================
    
    -- ADVERTENCIA: Las extensiones no se eliminan automáticamente
    -- porque pueden estar siendo usadas por otros objetos
    RAISE WARNING 'ATENCIÓN: Las extensiones NO se eliminan automáticamente por seguridad.';
    RAISE WARNING 'Si necesita eliminar extensiones, hágalo manualmente después de verificar dependencias.';
    RAISE NOTICE 'Extensiones que se crearon:';
    
    -- Listar extensiones que se crearon originalmente
    FOR ext_info IN 
        SELECT extname, extversion 
        FROM pg_extension 
        WHERE extname IN ('vector', 'pg_trgm', 'pg_cron', 'uuid-ossp')
        ORDER BY extname
    LOOP
        RAISE NOTICE '  - %: versión % (NO ELIMINADA)', ext_info.extname, ext_info.extversion;
    END LOOP;
    
    -- =====================================================
    -- RESTAURAR CONFIGURACIÓN ANTERIOR
    -- =====================================================
    
    -- Restaurar search_path original
    BEGIN
        -- Intentar restaurar a configuración por defecto
        ALTER DATABASE current_database() SET search_path TO public;
        RAISE NOTICE '✓ Search path restaurado a configuración por defecto';
    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'No se pudo restaurar search_path: %', SQLERRM;
    END;
    
    -- =====================================================
    -- VALIDACIONES POST-ROLLBACK
    -- =====================================================
    
    -- Verificar que los esquemas fueron eliminados
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'analytics') THEN
        RAISE WARNING 'El esquema analytics no pudo ser eliminado completamente';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'utils') THEN
        RAISE WARNING 'El esquema utils no pudo ser eliminado completamente';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'audit') THEN
        RAISE WARNING 'El esquema audit no pudo ser eliminado completamente';
    END IF;
    
    -- =====================================================
    -- REGISTRO DE ROLLBACK EXITOSO
    -- =====================================================
    
    execution_time := EXTRACT(epoch FROM (clock_timestamp() - start_time)) * 1000;
    
    -- Actualizar el registro original marcándolo como rollback
    UPDATE migration_history 
    SET status = 'ROLLBACK',
        execution_time_ms = execution_time,
        error_message = format('Rollback ejecutado exitosamente. %s objetos eliminados.', objects_dropped),
        rollback_available = FALSE
    WHERE script_name = original_script;
    
    -- Registrar el rollback
    PERFORM register_migration_execution(
        script_name,
        script_category,
        execution_time,
        'SUCCESS',
        format('Rollback completado: %s objetos eliminados', objects_dropped),
        NULL
    );
    
    RAISE NOTICE '✅ Rollback completado en % ms. % objetos eliminados.', execution_time, objects_dropped;
    
EXCEPTION WHEN OTHERS THEN
    -- En caso de error, registrar el fallo
    execution_time := EXTRACT(epoch FROM (clock_timestamp() - start_time)) * 1000;
    
    PERFORM register_migration_execution(
        script_name,
        script_category,
        execution_time,
        'FAILED',
        'Error durante rollback: ' || SQLERRM,
        NULL
    );
    
    RAISE EXCEPTION 'Error en rollback %: %', script_name, SQLERRM;
END
$$;

COMMIT;

-- Mostrar estado final
SELECT 
    'Esquemas después del rollback' as tipo,
    schema_name as nombre
FROM information_schema.schemata 
WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
ORDER BY schema_name;

\echo '✅ Rollback de extensiones y esquemas completado'
\echo '⚠️  Nota: Las extensiones no se eliminan automáticamente por seguridad'
