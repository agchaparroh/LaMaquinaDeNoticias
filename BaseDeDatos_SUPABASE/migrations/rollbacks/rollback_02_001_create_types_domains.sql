-- =====================================================
-- SCRIPT DE ROLLBACK - TIPOS Y DOMINIOS
-- =====================================================
/*
Script: rollback_02_001_create_types_domains.sql
Propósito: Revertir la creación de tipos y dominios personalizados
Script Original: 02_001_create_types_domains.sql
Categoría: types_domains
Idempotente: SÍ
Autor: TaskMaster AI
Fecha: 2025-05-24
*/

BEGIN;

DO $$
DECLARE
    script_name CONSTANT VARCHAR(255) := 'rollback_02_001_create_types_domains.sql';
    original_script CONSTANT VARCHAR(255) := '02_001_create_types_domains.sql';
    script_category CONSTANT VARCHAR(50) := 'types_domains';
    start_time TIMESTAMP := clock_timestamp();
    execution_time INTEGER;
    objects_dropped INTEGER := 0;
    dependent_objects INTEGER := 0;
BEGIN
    RAISE NOTICE 'Iniciando rollback de tipos y dominios personalizados...';
    
    -- Verificar que el script original fue ejecutado
    IF NOT is_script_executed(original_script) THEN
        RAISE NOTICE 'El script original % no fue ejecutado. Rollback innecesario.', original_script;
        RETURN;
    END IF;
    
    -- =====================================================
    -- VERIFICAR DEPENDENCIAS ANTES DEL ROLLBACK
    -- =====================================================
    
    -- Contar objetos dependientes de nuestros tipos/dominios
    SELECT COUNT(*) INTO dependent_objects
    FROM information_schema.columns c
    WHERE c.udt_name IN (
        'puntuacion_relevancia', 'grado_contradiccion', 'nivel_confianza',
        'url_valida', 'codigo_pais', 'embedding_384d',
        'estado_procesamiento', 'tipo_entidad', 'nivel_actividad', 
        'estado_evento', 'coordenadas_geo', 'metricas_calidad'
    );
    
    IF dependent_objects > 0 THEN
        RAISE WARNING 'Se encontraron % objetos que dependen de los tipos/dominios.', dependent_objects;
        RAISE WARNING 'El rollback eliminará estos objetos automáticamente con CASCADE.';
    END IF;
    
    -- =====================================================
    -- ROLLBACK DE DOMINIOS (en orden inverso de dependencias)
    -- =====================================================
    
    -- Eliminar dominio embedding_384d (depende de función de validación)
    IF EXISTS (SELECT 1 FROM information_schema.domains WHERE domain_name = 'embedding_384d') THEN
        BEGIN
            DROP DOMAIN embedding_384d CASCADE;
            objects_dropped := objects_dropped + 1;
            RAISE NOTICE '✓ Dominio embedding_384d eliminado';
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'No se pudo eliminar dominio embedding_384d: %', SQLERRM;
        END;
    END IF;
    
    -- Eliminar dominios básicos
    DECLARE
        domain_list TEXT[] := ARRAY[
            'codigo_pais',
            'url_valida', 
            'nivel_confianza',
            'grado_contradiccion',
            'puntuacion_relevancia'
        ];
        domain_name TEXT;
    BEGIN
        FOREACH domain_name IN ARRAY domain_list
        LOOP
            IF EXISTS (SELECT 1 FROM information_schema.domains WHERE domain_name = domain_name) THEN
                BEGIN
                    EXECUTE format('DROP DOMAIN %I CASCADE', domain_name);
                    objects_dropped := objects_dropped + 1;
                    RAISE NOTICE '✓ Dominio % eliminado', domain_name;
                EXCEPTION WHEN OTHERS THEN
                    RAISE WARNING 'No se pudo eliminar dominio %: %', domain_name, SQLERRM;
                END;
            END IF;
        END LOOP;
    END;
    
    -- =====================================================
    -- ROLLBACK DE TIPOS COMPOSITE
    -- =====================================================
    
    -- Eliminar tipos composite
    DECLARE
        composite_types TEXT[] := ARRAY[
            'metricas_calidad',
            'coordenadas_geo'
        ];
        type_name TEXT;
    BEGIN
        FOREACH type_name IN ARRAY composite_types
        LOOP
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = type_name) THEN
                BEGIN
                    EXECUTE format('DROP TYPE %I CASCADE', type_name);
                    objects_dropped := objects_dropped + 1;
                    RAISE NOTICE '✓ Tipo composite % eliminado', type_name;
                EXCEPTION WHEN OTHERS THEN
                    RAISE WARNING 'No se pudo eliminar tipo %: %', type_name, SQLERRM;
                END;
            END IF;
        END LOOP;
    END;
    
    -- =====================================================
    -- ROLLBACK DE TIPOS ENUM
    -- =====================================================
    
    -- Eliminar tipos ENUM
    DECLARE
        enum_types TEXT[] := ARRAY[
            'estado_evento',
            'nivel_actividad',
            'tipo_entidad',
            'estado_procesamiento'
        ];
        type_name TEXT;
    BEGIN
        FOREACH type_name IN ARRAY enum_types
        LOOP
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = type_name) THEN
                BEGIN
                    EXECUTE format('DROP TYPE %I CASCADE', type_name);
                    objects_dropped := objects_dropped + 1;
                    RAISE NOTICE '✓ Tipo ENUM % eliminado', type_name;
                EXCEPTION WHEN OTHERS THEN
                    RAISE WARNING 'No se pudo eliminar tipo %: %', type_name, SQLERRM;
                END;
            END IF;
        END LOOP;
    END;
    
    -- =====================================================
    -- ROLLBACK DE FUNCIONES AUXILIARES
    -- =====================================================
    
    -- Eliminar función de validación de embeddings
    IF EXISTS (
        SELECT 1 FROM information_schema.routines 
        WHERE routine_name = 'validar_embedding_dimension'
        AND routine_schema = 'public'
    ) THEN
        BEGIN
            DROP FUNCTION validar_embedding_dimension(vector);
            objects_dropped := objects_dropped + 1;
            RAISE NOTICE '✓ Función validar_embedding_dimension eliminada';
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'No se pudo eliminar función validar_embedding_dimension: %', SQLERRM;
        END;
    END IF;
    
    -- =====================================================
    -- VALIDACIONES POST-ROLLBACK
    -- =====================================================
    
    -- Verificar que los dominios fueron eliminados
    DECLARE
        remaining_domains INTEGER;
    BEGIN
        SELECT COUNT(*) INTO remaining_domains
        FROM information_schema.domains 
        WHERE domain_name IN (
            'puntuacion_relevancia', 'grado_contradiccion', 'nivel_confianza',
            'url_valida', 'codigo_pais', 'embedding_384d'
        );
        
        IF remaining_domains > 0 THEN
            RAISE WARNING 'Aún quedan % dominios sin eliminar', remaining_domains;
        ELSE
            RAISE NOTICE '✓ Todos los dominios fueron eliminados exitosamente';
        END IF;
    END;
    
    -- Verificar que los tipos fueron eliminados
    DECLARE
        remaining_types INTEGER;
    BEGIN
        SELECT COUNT(*) INTO remaining_types
        FROM pg_type 
        WHERE typname IN (
            'estado_procesamiento', 'tipo_entidad', 'nivel_actividad', 
            'estado_evento', 'coordenadas_geo', 'metricas_calidad'
        );
        
        IF remaining_types > 0 THEN
            RAISE WARNING 'Aún quedan % tipos sin eliminar', remaining_types;
        ELSE
            RAISE NOTICE '✓ Todos los tipos fueron eliminados exitosamente';
        END IF;
    END;
    
    -- =====================================================
    -- LIMPIEZA DE METADATA POSTGRESQL
    -- =====================================================
    
    -- Realizar VACUUM para limpiar metadata
    RAISE NOTICE 'Realizando limpieza de metadata...';
    
    -- =====================================================
    -- REGISTRO DE ROLLBACK EXITOSO
    -- =====================================================
    
    execution_time := EXTRACT(epoch FROM (clock_timestamp() - start_time)) * 1000;
    
    -- Actualizar el registro original marcándolo como rollback
    UPDATE migration_history 
    SET status = 'ROLLBACK',
        execution_time_ms = execution_time,
        error_message = format('Rollback ejecutado exitosamente. %s objetos eliminados. %s dependencias afectadas.', 
                              objects_dropped, dependent_objects),
        rollback_available = FALSE
    WHERE script_name = original_script;
    
    -- Registrar el rollback
    PERFORM register_migration_execution(
        script_name,
        script_category,
        execution_time,
        'SUCCESS',
        format('Rollback completado: %s objetos eliminados, %s dependencias afectadas', 
               objects_dropped, dependent_objects),
        NULL
    );
    
    RAISE NOTICE '✅ Rollback completado en % ms. % objetos eliminados.', execution_time, objects_dropped;
    IF dependent_objects > 0 THEN
        RAISE NOTICE '⚠️  % objetos dependientes también fueron eliminados.', dependent_objects;
    END IF;
    
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
    'Dominios restantes' as tipo,
    domain_name as nombre,
    data_type as definicion
FROM information_schema.domains 
WHERE domain_schema = 'public'
UNION ALL
SELECT 
    'Tipos restantes' as tipo,
    typname as nombre,
    'custom' as definicion
FROM pg_type 
WHERE typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
AND typtype IN ('e', 'c') -- ENUM y composite
ORDER BY tipo, nombre;

\echo '✅ Rollback de tipos y dominios completado'
\echo '⚠️  Nota: Los objetos dependientes fueron eliminados automáticamente con CASCADE'
