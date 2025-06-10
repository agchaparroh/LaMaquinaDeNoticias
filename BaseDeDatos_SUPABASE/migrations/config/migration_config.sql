-- =====================================================
-- CONFIGURACIÓN DE MIGRACIÓN - MÁQUINA DE NOTICIAS
-- =====================================================
-- Archivo: migration_config.sql
-- Propósito: Variables de configuración global para migración
-- Versión: 1.0
-- Fecha: 2025-05-24

-- Variables de configuración global
SET statement_timeout = '300s';  -- 5 minutos timeout para statements complejos
SET lock_timeout = '30s';        -- 30 segundos timeout para locks
SET idle_in_transaction_session_timeout = '600s'; -- 10 minutos para transacciones idle

-- Variables para logging y debugging
SET log_statement = 'all';       -- Loggear todas las statements durante migración
SET log_min_duration_statement = 1000; -- Loggear statements que tomen >1s

-- Configuración para creación de objetos
SET search_path = public;        -- Path de búsqueda por defecto

-- Variables específicas del proyecto
\set PROJECT_NAME 'maquina_noticias'
\set MIGRATION_VERSION '1.0.0'
\set MIGRATION_DATE '2025-05-24'

-- Configuración de memoria para operaciones complejas
SET work_mem = '256MB';          -- Memoria para ordenamientos e índices
SET maintenance_work_mem = '512MB'; -- Memoria para operaciones de mantenimiento

-- Configuración específica para vectores (si pgvector está disponible)
-- Nota: Estas configuraciones se aplicarán solo si pgvector está habilitado
\set VECTOR_DIMENSION 384
\set IVFFLAT_LISTS_DEFAULT 100

-- Variables de control de migración
\set ON_ERROR_STOP on           -- Detener en caso de error
\set ECHO all                   -- Mostrar todos los comandos ejecutados

-- Información del entorno
SELECT 
    version() as postgresql_version,
    current_database() as database_name,
    current_user as migration_user,
    now() as migration_start_time;

-- Verificación de prerrequisitos
DO $$
BEGIN
    -- Verificar versión mínima de PostgreSQL (14+)
    IF substring(version() from 'PostgreSQL (\d+)')::int < 14 THEN
        RAISE EXCEPTION 'PostgreSQL versión 14 o superior requerida. Versión actual: %', version();
    END IF;
    
    -- Informar sobre extensiones disponibles
    RAISE NOTICE 'Verificando extensiones disponibles...';
    
    -- Verificar que el usuario tiene permisos suficientes
    IF NOT has_database_privilege(current_user, current_database(), 'CREATE') THEN
        RAISE EXCEPTION 'Usuario % no tiene permisos CREATE en la base de datos %', 
                       current_user, current_database();
    END IF;
    
    RAISE NOTICE 'Configuración de migración cargada exitosamente';
    RAISE NOTICE 'Proyecto: %, Versión: %, Fecha: %', 
                 :'PROJECT_NAME', :'MIGRATION_VERSION', :'MIGRATION_DATE';
END
$$;
