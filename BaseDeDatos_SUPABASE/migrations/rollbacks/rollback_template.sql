-- =====================================================
-- PLANTILLA GENÉRICA DE ROLLBACK
-- =====================================================
/*
INSTRUCCIONES PARA USO DE ESTA PLANTILLA:

1. Copiar este archivo y renombrarlo como: rollback_[XX]_[NNN]_[nombre].sql
2. Reemplazar todas las ocurrencias de [PLACEHOLDER] con valores específicos
3. Implementar la lógica específica de rollback en la sección marcada
4. Validar que el rollback funciona con datos de prueba
5. Documentar cualquier consideración especial

PLACEHOLDERS A REEMPLAZAR:
- [SCRIPT_CATEGORY]: categoria del script (schema, tables, indexes, etc.)
- [SCRIPT_NUMBER]: número del script (001, 002, etc.)
- [SCRIPT_NAME]: nombre descriptivo del script
- [ORIGINAL_SCRIPT]: nombre completo del script original
- [ROLLBACK_DESCRIPTION]: descripción de lo que hace el rollback
- [OBJECTS_TO_DROP]: lista de objetos que se van a eliminar
- [DEPENDENCIES_CHECK]: validaciones específicas de dependencias
- [SPECIFIC_LOGIC]: lógica específica del rollback
*/

-- =====================================================
-- SCRIPT DE ROLLBACK - [ROLLBACK_DESCRIPTION]
-- =====================================================
/*
Script: rollback_[SCRIPT_CATEGORY]_[SCRIPT_NUMBER]_[SCRIPT_NAME].sql
Propósito: [ROLLBACK_DESCRIPTION]
Script Original: [ORIGINAL_SCRIPT]
Categoría: [SCRIPT_CATEGORY]
Objetos afectados: [OBJECTS_TO_DROP]
Idempotente: SÍ
Autor: TaskMaster AI
Fecha: $(date +%Y-%m-%d)

ADVERTENCIAS:
- Este rollback eliminará: [OBJECTS_TO_DROP]
- Puede afectar objetos dependientes
- Crear backup antes de ejecutar en producción

DEPENDENCIAS:
- Verificar que no hay objetos dependientes antes de ejecutar
- [DEPENDENCIES_CHECK]
*/

BEGIN;

DO $$
DECLARE
    script_name CONSTANT VARCHAR(255) := 'rollback_[SCRIPT_CATEGORY]_[SCRIPT_NUMBER]_[SCRIPT_NAME].sql';
    original_script CONSTANT VARCHAR(255) := '[ORIGINAL_SCRIPT]';
    script_category CONSTANT VARCHAR(50) := '[SCRIPT_CATEGORY]';
    start_time TIMESTAMP := clock_timestamp();
    execution_time INTEGER;
    objects_dropped INTEGER := 0;
    warnings_count INTEGER := 0;
    
    -- Variables específicas para el rollback
    dependent_objects INTEGER := 0;
    backup_created BOOLEAN := FALSE;
    
BEGIN
    RAISE NOTICE '🔄 Iniciando rollback: %', script_name;
    RAISE NOTICE 'Script original: %', original_script;
    
    -- =====================================================
    -- VALIDACIONES PREVIAS
    -- =====================================================
    
    -- Verificar que el script original fue ejecutado
    IF NOT is_script_executed(original_script) THEN
        RAISE NOTICE '⚠️  Script original % no fue ejecutado. Rollback innecesario.', original_script;
        RETURN;
    END IF;
    
    -- Verificar dependencias específicas del tipo de objeto
    CASE script_category
        WHEN 'schema' THEN
            -- Para esquemas: verificar que están vacíos
            SELECT COUNT(*) INTO dependent_objects
            FROM information_schema.tables
            WHERE table_schema IN ('[SCHEMAS_TO_CHECK]');
            
        WHEN 'tables' THEN
            -- Para tablas: verificar referencias FK
            SELECT COUNT(*) INTO dependent_objects
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND kcu.referenced_table_name IN ('[TABLES_TO_CHECK]');
            
        WHEN 'types_domains' THEN
            -- Para tipos: verificar columnas que los usan
            SELECT COUNT(*) INTO dependent_objects
            FROM information_schema.columns
            WHERE udt_name IN ('[TYPES_TO_CHECK]');
            
        WHEN 'functions' THEN
            -- Para funciones: verificar triggers y views que las usan
            SELECT COUNT(*) INTO dependent_objects
            FROM information_schema.routines r
            WHERE r.specific_name IN ('[FUNCTIONS_TO_CHECK]');
            
        ELSE
            -- Para otros tipos: validación genérica
            dependent_objects := 0;
    END CASE;
    
    -- Advertir sobre dependencias
    IF dependent_objects > 0 THEN
        RAISE WARNING '⚠️  Se encontraron % objetos dependientes que serán afectados', dependent_objects;
        warnings_count := warnings_count + 1;
    END IF;
    
    -- =====================================================
    -- CREAR BACKUP DE SEGURIDAD (OPCIONAL)
    -- =====================================================
    
    -- Crear backup de objetos críticos antes de eliminar
    /*
    BEGIN
        -- Ejemplo: backup de datos de tabla antes de DROP
        EXECUTE format('CREATE TABLE backup_%s_% AS SELECT * FROM %s',
                      '[TABLE_NAME]', 
                      to_char(NOW(), 'YYYYMMDD_HH24MISS'),
                      '[TABLE_NAME]');
        backup_created := TRUE;
        RAISE NOTICE '✓ Backup de seguridad creado';
    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'No se pudo crear backup: %', SQLERRM;
    END;
    */
    
    -- =====================================================
    -- LÓGICA ESPECÍFICA DE ROLLBACK
    -- =====================================================
    
    RAISE NOTICE '🗑️  Iniciando eliminación de objetos...';
    
    -- [SPECIFIC_LOGIC]
    -- NOTA: Reemplazar esta sección con la lógica específica de rollback
    
    -- EJEMPLO 1: Rollback de tablas (en orden de dependencias)
    /*
    DECLARE
        table_list TEXT[] := ARRAY[
            'tabla_hija_1',
            'tabla_hija_2', 
            'tabla_padre'
        ];
        table_name TEXT;
        row_count INTEGER;
    BEGIN
        FOREACH table_name IN ARRAY table_list
        LOOP
            IF EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = table_name AND table_schema = 'public'
            ) THEN
                -- Contar registros antes de eliminar
                EXECUTE format('SELECT COUNT(*) FROM %I', table_name) INTO row_count;
                
                IF row_count > 0 THEN
                    RAISE WARNING 'Tabla % contiene % registros que serán eliminados', 
                                  table_name, row_count;
                    warnings_count := warnings_count + 1;
                END IF;
                
                EXECUTE format('DROP TABLE %I CASCADE', table_name);
                objects_dropped := objects_dropped + 1;
                RAISE NOTICE '✓ Tabla % eliminada (%s registros)', table_name, row_count;
            ELSE
                RAISE NOTICE '⚠️  Tabla % no existe, saltando...', table_name;
            END IF;
        END LOOP;
    END;
    */
    
    -- EJEMPLO 2: Rollback de funciones
    /*
    DECLARE
        function_list TEXT[] := ARRAY[
            'mi_funcion(INTEGER)',
            'otra_funcion(TEXT, INTEGER)',
            'funcion_compleja(TEXT[], JSONB)'
        ];
        func_signature TEXT;
    BEGIN
        FOREACH func_signature IN ARRAY function_list
        LOOP
            BEGIN
                EXECUTE format('DROP FUNCTION IF EXISTS %s CASCADE', func_signature);
                objects_dropped := objects_dropped + 1;
                RAISE NOTICE '✓ Función % eliminada', func_signature;
            EXCEPTION WHEN OTHERS THEN
                RAISE WARNING 'No se pudo eliminar función %: %', func_signature, SQLERRM;
                warnings_count := warnings_count + 1;
            END;
        END LOOP;
    END;
    */
    
    -- EJEMPLO 3: Rollback de índices
    /*
    DECLARE
        index_list TEXT[] := ARRAY[
            'idx_tabla_columna1',
            'idx_tabla_columna2_gin',
            'idx_tabla_embedding_ivfflat'
        ];
        index_name TEXT;
    BEGIN
        FOREACH index_name IN ARRAY index_list
        LOOP
            IF EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE indexname = index_name
            ) THEN
                EXECUTE format('DROP INDEX IF EXISTS %I', index_name);
                objects_dropped := objects_dropped + 1;
                RAISE NOTICE '✓ Índice % eliminado', index_name;
            ELSE
                RAISE NOTICE '⚠️  Índice % no existe, saltando...', index_name;
            END IF;
        END LOOP;
    END;
    */
    
    -- EJEMPLO 4: Rollback de triggers
    /*
    DECLARE
        trigger_info RECORD;
    BEGIN
        FOR trigger_info IN
            SELECT trigger_name, event_object_table
            FROM information_schema.triggers
            WHERE trigger_name IN (
                'mi_trigger_1',
                'mi_trigger_2',
                'trigger_automatico'
            )
        LOOP
            EXECUTE format('DROP TRIGGER IF EXISTS %I ON %I', 
                          trigger_info.trigger_name, 
                          trigger_info.event_object_table);
            objects_dropped := objects_dropped + 1;
            RAISE NOTICE '✓ Trigger % eliminado de tabla %', 
                         trigger_info.trigger_name, 
                         trigger_info.event_object_table;
        END LOOP;
    END;
    */
    
    -- =====================================================
    -- VALIDACIONES POST-ROLLBACK
    -- =====================================================
    
    RAISE NOTICE '🔍 Ejecutando validaciones post-rollback...';
    
    -- Validaciones específicas según el tipo de rollback
    -- [POST_ROLLBACK_VALIDATIONS]
    
    -- EJEMPLO: Verificar que las tablas fueron eliminadas
    /*
    DECLARE
        remaining_tables INTEGER;
    BEGIN
        SELECT COUNT(*) INTO remaining_tables
        FROM information_schema.tables
        WHERE table_name IN ('tabla1', 'tabla2', 'tabla3')
        AND table_schema = 'public';
        
        IF remaining_tables > 0 THEN
            RAISE WARNING 'Aún quedan % tablas sin eliminar', remaining_tables;
            warnings_count := warnings_count + 1;
        ELSE
            RAISE NOTICE '✓ Todas las tablas fueron eliminadas exitosamente';
        END IF;
    END;
    */
    
    -- =====================================================
    -- LIMPIEZA FINAL
    -- =====================================================
    
    -- Ejecutar VACUUM para limpiar metadata (opcional para objetos grandes)
    /*
    IF objects_dropped > 10 THEN
        RAISE NOTICE '🧹 Ejecutando limpieza de metadata...';
        -- VACUUM se ejecutaría fuera de la transacción
    END IF;
    */
    
    -- =====================================================
    -- REGISTRO DE ROLLBACK EXITOSO
    -- =====================================================
    
    execution_time := EXTRACT(epoch FROM (clock_timestamp() - start_time)) * 1000;
    
    -- Actualizar el registro original marcándolo como rollback
    UPDATE migration_history 
    SET status = 'ROLLBACK',
        execution_time_ms = execution_time,
        error_message = format('Rollback ejecutado exitosamente. %s objetos eliminados, %s advertencias.', 
                              objects_dropped, warnings_count),
        rollback_available = FALSE
    WHERE script_name = original_script;
    
    -- Registrar la ejecución del rollback
    PERFORM register_migration_execution(
        script_name,
        script_category,
        execution_time,
        'SUCCESS',
        format('Rollback completado: %s objetos eliminados, %s dependencias afectadas, %s advertencias', 
               objects_dropped, dependent_objects, warnings_count),
        NULL
    );
    
    -- Mensaje final
    RAISE NOTICE '✅ Rollback % completado en % ms', script_name, execution_time;
    RAISE NOTICE '📊 Resumen: % objetos eliminados, % advertencias', objects_dropped, warnings_count;
    
    IF warnings_count > 0 THEN
        RAISE NOTICE '⚠️  Revisar advertencias arriba para posibles problemas';
    END IF;
    
    IF backup_created THEN
        RAISE NOTICE '💾 Backup de seguridad disponible para recuperación';
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
    
    RAISE EXCEPTION '❌ Error en rollback %: %', script_name, SQLERRM;
END
$$;

COMMIT;

-- =====================================================
-- VALIDACIONES POST-COMMIT (OPCIONAL)
-- =====================================================

-- Mostrar estado final de objetos relevantes
/*
SELECT 
    'Objetos restantes después del rollback' as info,
    schemaname,
    tablename
FROM pg_tables 
WHERE tablename LIKE '%[PATTERN]%'
ORDER BY schemaname, tablename;
*/

-- Mostrar resumen del rollback
SELECT 
    mh.script_name,
    mh.status,
    mh.executed_at,
    mh.execution_time_ms,
    mh.error_message
FROM migration_history mh
WHERE mh.script_name LIKE '%[SCRIPT_NAME]%'
ORDER BY mh.executed_at DESC
LIMIT 5;

\echo '✅ Rollback [ROLLBACK_DESCRIPTION] completado'
\echo 'ℹ️  Revisar logs para detalles adicionales'

-- =====================================================
-- NOTAS PARA EL DESARROLLADOR
-- =====================================================
/*
CHECKLIST ANTES DE USAR ESTA PLANTILLA:

□ Reemplazar todos los [PLACEHOLDERS] con valores reales
□ Implementar lógica específica de rollback en la sección marcada
□ Agregar validaciones específicas del tipo de objeto
□ Probar el rollback en un entorno de desarrollo
□ Documentar cualquier efecto secundario esperado
□ Verificar que el rollback es verdaderamente idempotente
□ Confirmar que se manejan apropiadamente las dependencias

CONSIDERACIONES ESPECIALES:

1. ORDEN DE ELIMINACIÓN: Los objetos deben eliminarse en orden 
   inverso a su creación para evitar errores de dependencias.

2. CASCADE vs RESTRICT: Usar CASCADE con cuidado ya que puede 
   eliminar objetos no intencionados.

3. BACKUP DE DATOS: Para tablas con datos importantes, considerar
   crear un backup antes de la eliminación.

4. OBJETOS COMPARTIDOS: Algunos objetos (extensiones, esquemas) 
   pueden ser compartidos con otros sistemas.

5. PERMISOS: El rollback debe ejecutarse con permisos suficientes
   para eliminar todos los objetos target.

TESTING DEL ROLLBACK:

1. Ejecutar el script original en un entorno limpio
2. Ejecutar el rollback y verificar que todos los objetos se eliminan
3. Verificar que el rollback es idempotente (se puede ejecutar múltiples veces)
4. Probar el rollback con datos de prueba en las tablas
5. Verificar el manejo de errores y situaciones excepcionales
*/
