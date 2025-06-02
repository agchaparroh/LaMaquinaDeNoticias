-- =====================================================
-- CREACIÓN DE EXTENSIONES Y ESQUEMAS BÁSICOS
-- =====================================================
/*
Script: 01_001_create_extensions_schemas.sql
Categoría: schema
Descripción: Crear extensiones PostgreSQL necesarias y esquemas básicos
Dependencias: 00_000_migration_control.sql
Rollback: Disponible en rollbacks/rollback_01_001_create_extensions_schemas.sql
Idempotente: SÍ
Autor: TaskMaster AI
Fecha: 2025-05-24
*/

BEGIN;

DO $$
DECLARE
    script_name CONSTANT VARCHAR(255) := '01_001_create_extensions_schemas.sql';
    script_category CONSTANT VARCHAR(50) := 'schema';
    start_time TIMESTAMP := clock_timestamp();
    execution_time INTEGER;
BEGIN
    -- Verificar si ya fue ejecutado
    IF is_script_executed(script_name) THEN
        RAISE NOTICE 'Script % ya fue ejecutado anteriormente. Saltando...', script_name;
        RETURN;
    END IF;
    
    RAISE NOTICE 'Iniciando creación de extensiones y esquemas...';
    
    -- =====================================================
    -- CREACIÓN DE EXTENSIONES NECESARIAS
    -- =====================================================
    
    -- Extensión para vectores (pgvector)
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        CREATE EXTENSION vector;
        RAISE NOTICE '✓ Extensión vector creada';
    ELSE
        RAISE NOTICE '✓ Extensión vector ya existe';
    END IF;
    
    -- Extensión para similitud de texto (pg_trgm)
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm') THEN
        CREATE EXTENSION pg_trgm;
        RAISE NOTICE '✓ Extensión pg_trgm creada';
    ELSE
        RAISE NOTICE '✓ Extensión pg_trgm ya existe';
    END IF;
    
    -- Extensión para cron jobs (pg_cron)
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
        BEGIN
            CREATE EXTENSION pg_cron;
            RAISE NOTICE '✓ Extensión pg_cron creada';
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'No se pudo crear pg_cron (normal en Supabase): %', SQLERRM;
        END;
    ELSE
        RAISE NOTICE '✓ Extensión pg_cron ya existe';
    END IF;
    
    -- Extensión para UUID (si no viene por defecto)
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'uuid-ossp') THEN
        BEGIN
            CREATE EXTENSION "uuid-ossp";
            RAISE NOTICE '✓ Extensión uuid-ossp creada';
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'uuid-ossp no disponible o ya existe';
        END;
    ELSE
        RAISE NOTICE '✓ Extensión uuid-ossp ya existe';
    END IF;
    
    -- =====================================================
    -- CREACIÓN DE ESQUEMAS ORGANIZACIONALES
    -- =====================================================
    
    -- Esquema para analytics y reporting
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'analytics') THEN
        CREATE SCHEMA analytics;
        RAISE NOTICE '✓ Esquema analytics creado';
    ELSE
        RAISE NOTICE '✓ Esquema analytics ya existe';
    END IF;
    
    -- Esquema para funciones auxiliares
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'utils') THEN
        CREATE SCHEMA utils;
        RAISE NOTICE '✓ Esquema utils creado';
    ELSE
        RAISE NOTICE '✓ Esquema utils ya existe';
    END IF;
    
    -- Esquema para logging y auditoria
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'audit') THEN
        CREATE SCHEMA audit;
        RAISE NOTICE '✓ Esquema audit creado';
    ELSE
        RAISE NOTICE '✓ Esquema audit ya existe';
    END IF;
    
    -- =====================================================
    -- CONFIGURACIÓN DE SEARCH_PATH
    -- =====================================================
    
    -- Configurar search_path por defecto para incluir nuevos esquemas
    ALTER DATABASE current_database() SET search_path TO public, analytics, utils, audit;
    RAISE NOTICE '✓ Search path configurado';
    
    -- =====================================================
    -- VALIDACIONES POST-CREACIÓN
    -- =====================================================
    
    -- Validar extensiones críticas
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE EXCEPTION 'CRÍTICO: Extensión vector no pudo ser creada';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm') THEN
        RAISE EXCEPTION 'CRÍTICO: Extensión pg_trgm no pudo ser creada';
    END IF;
    
    -- Validar esquemas críticos
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'analytics') THEN
        RAISE EXCEPTION 'CRÍTICO: Esquema analytics no pudo ser creado';
    END IF;
    
    -- =====================================================
    -- INFORMACIÓN DE VERSIONES
    -- =====================================================
    
    -- Mostrar información de extensiones instaladas
    RAISE NOTICE 'Extensiones instaladas:';
    FOR ext_info IN 
        SELECT extname, extversion 
        FROM pg_extension 
        WHERE extname IN ('vector', 'pg_trgm', 'pg_cron', 'uuid-ossp')
        ORDER BY extname
    LOOP
        RAISE NOTICE '  - %: versión %', ext_info.extname, ext_info.extversion;
    END LOOP;
    
    -- =====================================================
    -- REGISTRO DE EJECUCIÓN EXITOSA
    -- =====================================================
    
    execution_time := EXTRACT(epoch FROM (clock_timestamp() - start_time)) * 1000;
    
    PERFORM register_migration_execution(
        script_name,
        script_category,
        execution_time,
        'SUCCESS',
        'Extensiones y esquemas creados exitosamente',
        NULL
    );
    
    RAISE NOTICE '✅ Script % completado en % ms', script_name, execution_time;
    
EXCEPTION WHEN OTHERS THEN
    -- En caso de error, registrar el fallo
    execution_time := EXTRACT(epoch FROM (clock_timestamp() - start_time)) * 1000;
    
    PERFORM register_migration_execution(
        script_name,
        script_category,
        execution_time,
        'FAILED',
        SQLERRM,
        NULL
    );
    
    RAISE EXCEPTION 'Error en script %: %', script_name, SQLERRM;
END
$$;

COMMIT;

-- Mostrar resumen final
SELECT 
    'Extensiones disponibles' as tipo,
    extname as nombre,
    extversion as version
FROM pg_extension 
WHERE extname IN ('vector', 'pg_trgm', 'pg_cron', 'uuid-ossp')
UNION ALL
SELECT 
    'Esquemas creados' as tipo,
    schema_name as nombre,
    'N/A' as version
FROM information_schema.schemata 
WHERE schema_name IN ('analytics', 'utils', 'audit')
ORDER BY tipo, nombre;

\echo '✅ Extensiones y esquemas base configurados correctamente'
