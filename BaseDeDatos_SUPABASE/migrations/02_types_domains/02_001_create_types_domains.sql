-- =====================================================
-- CREACIÓN DE TIPOS Y DOMINIOS PERSONALIZADOS
-- =====================================================
/*
Script: 02_001_create_types_domains.sql
Categoría: types_domains
Descripción: Crear tipos de datos personalizados y dominios para validación
Dependencias: 01_001_create_extensions_schemas.sql
Rollback: Disponible en rollbacks/rollback_02_001_create_types_domains.sql
Idempotente: SÍ
Autor: TaskMaster AI
Fecha: 2025-05-24
*/

BEGIN;

DO $$
DECLARE
    script_name CONSTANT VARCHAR(255) := '02_001_create_types_domains.sql';
    script_category CONSTANT VARCHAR(50) := 'types_domains';
    start_time TIMESTAMP := clock_timestamp();
    execution_time INTEGER;
    domain_count INTEGER := 0;
    type_count INTEGER := 0;
BEGIN
    -- Verificar si ya fue ejecutado
    IF is_script_executed(script_name) THEN
        RAISE NOTICE 'Script % ya fue ejecutado anteriormente. Saltando...', script_name;
        RETURN;
    END IF;
    
    RAISE NOTICE 'Iniciando creación de tipos y dominios personalizados...';
    
    -- =====================================================
    -- DOMINIOS DE PUNTUACIÓN Y EVALUACIÓN
    -- =====================================================
    
    -- Dominio para puntuaciones de relevancia (0-10)
    IF NOT EXISTS (SELECT 1 FROM information_schema.domains WHERE domain_name = 'puntuacion_relevancia') THEN
        CREATE DOMAIN puntuacion_relevancia AS INTEGER
            CHECK (VALUE >= 0 AND VALUE <= 10);
        domain_count := domain_count + 1;
        RAISE NOTICE '✓ Dominio puntuacion_relevancia creado';
    ELSE
        RAISE NOTICE '✓ Dominio puntuacion_relevancia ya existe';
    END IF;
    
    -- Dominio para grado de contradicción (1-5)
    IF NOT EXISTS (SELECT 1 FROM information_schema.domains WHERE domain_name = 'grado_contradiccion') THEN
        CREATE DOMAIN grado_contradiccion AS INTEGER
            CHECK (VALUE >= 1 AND VALUE <= 5);
        domain_count := domain_count + 1;
        RAISE NOTICE '✓ Dominio grado_contradiccion creado';
    ELSE
        RAISE NOTICE '✓ Dominio grado_contradiccion ya existe';
    END IF;
    
    -- Dominio para nivel de confianza (0.0-1.0)
    IF NOT EXISTS (SELECT 1 FROM information_schema.domains WHERE domain_name = 'nivel_confianza') THEN
        CREATE DOMAIN nivel_confianza AS DECIMAL(3,2)
            CHECK (VALUE >= 0.00 AND VALUE <= 1.00);
        domain_count := domain_count + 1;
        RAISE NOTICE '✓ Dominio nivel_confianza creado';
    ELSE
        RAISE NOTICE '✓ Dominio nivel_confianza ya existe';
    END IF;
    
    -- =====================================================
    -- DOMINIOS DE IDENTIFICACIÓN
    -- =====================================================
    
    -- Dominio para URLs válidas
    IF NOT EXISTS (SELECT 1 FROM information_schema.domains WHERE domain_name = 'url_valida') THEN
        CREATE DOMAIN url_valida AS TEXT
            CHECK (VALUE ~ '^https?://[^\s/$.?#].[^\s]*$');
        domain_count := domain_count + 1;
        RAISE NOTICE '✓ Dominio url_valida creado';
    ELSE
        RAISE NOTICE '✓ Dominio url_valida ya existe';
    END IF;
    
    -- Dominio para códigos de país ISO (2 letras)
    IF NOT EXISTS (SELECT 1 FROM information_schema.domains WHERE domain_name = 'codigo_pais') THEN
        CREATE DOMAIN codigo_pais AS CHAR(2)
            CHECK (VALUE ~ '^[A-Z]{2}$');
        domain_count := domain_count + 1;
        RAISE NOTICE '✓ Dominio codigo_pais creado';
    ELSE
        RAISE NOTICE '✓ Dominio codigo_pais ya existe';
    END IF;
    
    -- =====================================================
    -- TIPOS ENUM PERSONALIZADOS
    -- =====================================================
    
    -- Tipo ENUM para estado de procesamiento
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estado_procesamiento') THEN
        CREATE TYPE estado_procesamiento AS ENUM (
            'pendiente',
            'procesando',
            'completado',
            'error',
            'cancelado'
        );
        type_count := type_count + 1;
        RAISE NOTICE '✓ Tipo estado_procesamiento creado';
    ELSE
        RAISE NOTICE '✓ Tipo estado_procesamiento ya existe';
    END IF;
    
    -- Tipo ENUM para tipo de entidad
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_entidad') THEN
        CREATE TYPE tipo_entidad AS ENUM (
            'persona',
            'organizacion',
            'lugar',
            'evento',
            'concepto',
            'otro'
        );
        type_count := type_count + 1;
        RAISE NOTICE '✓ Tipo tipo_entidad creado';
    ELSE
        RAISE NOTICE '✓ Tipo tipo_entidad ya existe';
    END IF;
    
    -- Tipo ENUM para nivel de actividad de hilos
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'nivel_actividad') THEN
        CREATE TYPE nivel_actividad AS ENUM (
            'muy_reciente',
            'reciente', 
            'activo',
            'seguimiento',
            'inactivo'
        );
        type_count := type_count + 1;
        RAISE NOTICE '✓ Tipo nivel_actividad creado';
    ELSE
        RAISE NOTICE '✓ Tipo nivel_actividad ya existe';
    END IF;
    
    -- Tipo ENUM para estado de eventos
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estado_evento') THEN
        CREATE TYPE estado_evento AS ENUM (
            'programado',
            'en_curso',
            'completado',
            'cancelado',
            'pospuesto'
        );
        type_count := type_count + 1;
        RAISE NOTICE '✓ Tipo estado_evento creado';
    ELSE
        RAISE NOTICE '✓ Tipo estado_evento ya existe';
    END IF;
    
    -- =====================================================
    -- TIPOS COMPOSITE PERSONALIZADOS
    -- =====================================================
    
    -- Tipo composite para coordenadas geográficas
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'coordenadas_geo') THEN
        CREATE TYPE coordenadas_geo AS (
            latitud DECIMAL(10,8),
            longitud DECIMAL(11,8),
            precision_metros INTEGER
        );
        type_count := type_count + 1;
        RAISE NOTICE '✓ Tipo coordenadas_geo creado';
    ELSE
        RAISE NOTICE '✓ Tipo coordenadas_geo ya existe';
    END IF;
    
    -- Tipo composite para métricas de calidad
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'metricas_calidad') THEN
        CREATE TYPE metricas_calidad AS (
            completitud DECIMAL(5,2),
            precision DECIMAL(5,2),
            consistencia DECIMAL(5,2),
            actualidad INTEGER,
            score_global DECIMAL(5,2)
        );
        type_count := type_count + 1;
        RAISE NOTICE '✓ Tipo metricas_calidad creado';
    ELSE
        RAISE NOTICE '✓ Tipo metricas_calidad ya existe';
    END IF;
    
    -- =====================================================
    -- VALIDACIONES FUNCIONALES
    -- =====================================================
    
    -- Función de validación para embedding vectorial
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.routines 
        WHERE routine_name = 'validar_embedding_dimension'
        AND routine_schema = 'public'
    ) THEN
        CREATE OR REPLACE FUNCTION validar_embedding_dimension(embedding vector)
        RETURNS BOOLEAN AS $func$
        BEGIN
            -- Verificar que el vector tenga exactamente 384 dimensiones
            RETURN array_length(embedding::real[], 1) = 384;
        END;
        $func$ LANGUAGE plpgsql IMMUTABLE;
        RAISE NOTICE '✓ Función validar_embedding_dimension creada';
    ELSE
        RAISE NOTICE '✓ Función validar_embedding_dimension ya existe';
    END IF;
    
    -- =====================================================
    -- DOMINIOS CON VALIDACIONES COMPLEJAS
    -- =====================================================
    
    -- Dominio para embeddings vectoriales válidos
    IF NOT EXISTS (SELECT 1 FROM information_schema.domains WHERE domain_name = 'embedding_384d') THEN
        CREATE DOMAIN embedding_384d AS vector(384)
            CHECK (validar_embedding_dimension(VALUE));
        domain_count := domain_count + 1;
        RAISE NOTICE '✓ Dominio embedding_384d creado';
    ELSE
        RAISE NOTICE '✓ Dominio embedding_384d ya existe';
    END IF;
    
    -- =====================================================
    -- VALIDACIONES POST-CREACIÓN
    -- =====================================================
    
    -- Verificar dominios críticos
    IF NOT EXISTS (SELECT 1 FROM information_schema.domains WHERE domain_name = 'puntuacion_relevancia') THEN
        RAISE EXCEPTION 'CRÍTICO: Dominio puntuacion_relevancia no pudo ser creado';
    END IF;
    
    -- Verificar tipos ENUM críticos
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estado_procesamiento') THEN
        RAISE EXCEPTION 'CRÍTICO: Tipo estado_procesamiento no pudo ser creado';
    END IF;
    
    -- =====================================================
    -- PRUEBAS DE FUNCIONALIDAD
    -- =====================================================
    
    -- Probar dominios con valores válidos
    PERFORM 5::puntuacion_relevancia;
    PERFORM 3::grado_contradiccion;
    PERFORM 0.85::nivel_confianza;
    PERFORM 'US'::codigo_pais;
    
    RAISE NOTICE '✓ Pruebas de dominios exitosas';
    
    -- Probar tipos ENUM
    PERFORM 'completado'::estado_procesamiento;
    PERFORM 'persona'::tipo_entidad;
    PERFORM 'activo'::nivel_actividad;
    
    RAISE NOTICE '✓ Pruebas de tipos ENUM exitosas';
    
    -- =====================================================
    -- REGISTRO DE EJECUCIÓN EXITOSA
    -- =====================================================
    
    execution_time := EXTRACT(epoch FROM (clock_timestamp() - start_time)) * 1000;
    
    PERFORM register_migration_execution(
        script_name,
        script_category,
        execution_time,
        'SUCCESS',
        format('Creados %s dominios y %s tipos personalizados', domain_count, type_count),
        NULL
    );
    
    RAISE NOTICE '✅ Script % completado en % ms', script_name, execution_time;
    RAISE NOTICE '📊 Resumen: % dominios creados, % tipos creados', domain_count, type_count;
    
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

-- Mostrar resumen de tipos y dominios creados
SELECT 
    'Dominios' as categoria,
    domain_name as nombre,
    data_type || 
    CASE 
        WHEN character_maximum_length IS NOT NULL 
        THEN '(' || character_maximum_length || ')'
        ELSE ''
    END as definicion
FROM information_schema.domains 
WHERE domain_schema = 'public'
    AND domain_name IN (
        'puntuacion_relevancia', 'grado_contradiccion', 'nivel_confianza',
        'url_valida', 'codigo_pais', 'embedding_384d'
    )
UNION ALL
SELECT 
    'Tipos ENUM' as categoria,
    typname as nombre,
    'ENUM(' || array_to_string(enum_range(NULL::estado_procesamiento), ', ') || ')' as definicion
FROM pg_type 
WHERE typname IN ('estado_procesamiento', 'tipo_entidad', 'nivel_actividad', 'estado_evento')
ORDER BY categoria, nombre;

\echo '✅ Tipos y dominios personalizados configurados correctamente'
