-- =====================================================
-- PLANTILLA DE SCRIPT IDEMPOTENTE
-- =====================================================
-- PLANTILLA PARA: Scripts de extensiones/esquemas
-- Uso: Copiar y adaptar para crear scripts idempotentes
-- Archivo: idempotent_template.sql

-- HEADER OBLIGATORIO PARA TODOS LOS SCRIPTS
/*
Script: [NOMBRE_DEL_SCRIPT].sql
Categoría: [CATEGORIA]
Descripción: [DESCRIPCIÓN_DETALLADA]
Dependencias: [SCRIPTS_PREVIOS_REQUERIDOS]
Rollback: Disponible en rollbacks/rollback_[NOMBRE_DEL_SCRIPT].sql
Idempotente: SÍ
Autor: TaskMaster AI
Fecha: $(date +%Y-%m-%d)
*/

-- =====================================================
-- PLANTILLA BÁSICA DE IDEMPOTENCIA
-- =====================================================

BEGIN;

-- PASO 1: Verificar si el script ya fue ejecutado
DO $$
DECLARE
    script_name CONSTANT VARCHAR(255) := 'NOMBRE_DEL_SCRIPT.sql';
    script_category CONSTANT VARCHAR(50) := 'CATEGORIA';
    start_time TIMESTAMP := clock_timestamp();
    execution_time INTEGER;
BEGIN
    -- Verificar si ya fue ejecutado
    IF is_script_executed(script_name) THEN
        RAISE NOTICE 'Script % ya fue ejecutado anteriormente. Saltando...', script_name;
        RETURN;
    END IF;
    
    RAISE NOTICE 'Iniciando ejecución de script: %', script_name;
    
    -- =====================================================
    -- LÓGICA ESPECÍFICA DEL SCRIPT AQUÍ
    -- =====================================================
    
    -- Ejemplo para EXTENSIONES:
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
    
    -- Ejemplo para ESQUEMAS:
    CREATE SCHEMA IF NOT EXISTS analytics;
    
    -- Ejemplo para DOMINIOS:
    DO $domain$
    BEGIN
        CREATE DOMAIN puntuacion_relevancia AS INTEGER
            CHECK (VALUE >= 0 AND VALUE <= 10);
    EXCEPTION WHEN duplicate_object THEN
        RAISE NOTICE 'Dominio puntuacion_relevancia ya existe';
    END
    $domain$;
    
    -- Ejemplo para TABLAS:
    CREATE TABLE IF NOT EXISTS ejemplo_tabla (
        id SERIAL PRIMARY KEY,
        nombre VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    -- Ejemplo para ÍNDICES:
    CREATE INDEX IF NOT EXISTS idx_ejemplo_tabla_nombre
    ON ejemplo_tabla(nombre);
    
    -- =====================================================
    -- VALIDACIONES POST-EJECUCIÓN
    -- =====================================================
    
    -- Validar que los objetos fueron creados correctamente
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'analytics') THEN
        RAISE EXCEPTION 'Fallo en creación de esquema analytics';
    END IF;
    
    -- =====================================================
    -- REGISTRO DE EJECUCIÓN EXITOSA
    -- =====================================================
    
    execution_time := EXTRACT(epoch FROM (clock_timestamp() - start_time)) * 1000;
    
    PERFORM register_migration_execution(
        script_name,
        script_category,
        execution_time,
        'SUCCESS',
        'Script ejecutado exitosamente',
        NULL
    );
    
    RAISE NOTICE 'Script % completado en % ms', script_name, execution_time;
    
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

-- =====================================================
-- PATRONES DE IDEMPOTENCIA ESPECÍFICOS
-- =====================================================

-- PATRÓN 1: Verificación de Existencia para Extensiones
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        CREATE EXTENSION vector;
        RAISE NOTICE 'Extensión vector creada';
    ELSE
        RAISE NOTICE 'Extensión vector ya existe';
    END IF;
END
$$;

-- PATRÓN 2: Verificación de Existencia para Funciones
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.routines 
        WHERE routine_name = 'mi_funcion'
        AND routine_schema = 'public'
    ) THEN
        -- Crear función aquí
        RAISE NOTICE 'Función mi_funcion creada';
    ELSE
        RAISE NOTICE 'Función mi_funcion ya existe';
    END IF;
END
$$;

-- PATRÓN 3: Verificación de Existencia para Triggers
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.triggers 
        WHERE trigger_name = 'mi_trigger'
    ) THEN
        -- Crear trigger aquí
        RAISE NOTICE 'Trigger mi_trigger creado';
    ELSE
        RAISE NOTICE 'Trigger mi_trigger ya existe';
    END IF;
END
$$;

-- PATRÓN 4: Verificación de Existencia para Columnas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'mi_tabla' 
        AND column_name = 'nueva_columna'
    ) THEN
        ALTER TABLE mi_tabla ADD COLUMN nueva_columna TEXT;
        RAISE NOTICE 'Columna nueva_columna agregada';
    ELSE
        RAISE NOTICE 'Columna nueva_columna ya existe';
    END IF;
END
$$;

-- PATRÓN 5: Verificación de Existencia para Índices con Manejo de Conflictos
DO $$
BEGIN
    -- Verificar si el índice ya existe
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'mi_indice'
    ) THEN
        CREATE INDEX mi_indice ON mi_tabla(mi_columna);
        RAISE NOTICE 'Índice mi_indice creado';
    ELSE
        RAISE NOTICE 'Índice mi_indice ya existe';
    END IF;
EXCEPTION WHEN duplicate_table THEN
    RAISE NOTICE 'Índice mi_indice ya existe (capturado por excepción)';
END
$$;

-- PATRÓN 6: Actualización Condicional de Datos
DO $$
BEGIN
    -- Solo insertar si no existe
    INSERT INTO configuracion (clave, valor)
    SELECT 'mi_config', 'mi_valor'
    WHERE NOT EXISTS (
        SELECT 1 FROM configuracion WHERE clave = 'mi_config'
    );
    
    -- Informar sobre el resultado
    IF FOUND THEN
        RAISE NOTICE 'Configuración mi_config insertada';
    ELSE
        RAISE NOTICE 'Configuración mi_config ya existe';
    END IF;
END
$$;

-- =====================================================
-- MACROS ÚTILES PARA SCRIPTS IDEMPOTENTES
-- =====================================================

-- Macro para verificar y crear esquema
CREATE OR REPLACE FUNCTION create_schema_if_not_exists(schema_name TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = $1) THEN
        EXECUTE format('CREATE SCHEMA %I', $1);
        RAISE NOTICE 'Esquema % creado', $1;
        RETURN TRUE;
    ELSE
        RAISE NOTICE 'Esquema % ya existe', $1;
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Macro para verificar y crear tabla
CREATE OR REPLACE FUNCTION table_exists(table_name TEXT, schema_name TEXT DEFAULT 'public')
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = $2 
        AND table_name = $1
    );
END;
$$ LANGUAGE plpgsql;
