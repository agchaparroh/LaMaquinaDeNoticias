# Sistema de Rollback - Máquina de Noticias

## 📋 Introducción

El sistema de rollback permite revertir cambios de migración de manera segura y controlada. Cada script de migración debe tener su correspondiente script de rollback.

## 🎯 Principios de Rollback

### 1. Orden Inverso
Los rollbacks se ejecutan en orden inverso al de instalación:
```
Instalación: 01 → 02 → 03 → 04
Rollback:    04 → 03 → 02 → 01
```

### 2. Validación de Dependencias
Antes de cada rollback se verifica:
- No hay objetos dependientes activos
- No hay transacciones en curso
- Permisos suficientes para la operación

### 3. Granularidad Flexible
Rollback puede ser:
- **Completo**: Revertir toda la migración
- **Parcial**: Revertir hasta un punto específico
- **Individual**: Revertir un script específico

## 🛠️ Plantillas de Rollback

### Plantilla Básica

```sql
-- =====================================================
-- SCRIPT DE ROLLBACK - [DESCRIPCIÓN]
-- =====================================================
/*
Script: rollback_[XX]_[NNN]_[nombre].sql
Propósito: Revertir [descripción del script original]
Script Original: [XX]_[NNN]_[nombre].sql
Categoría: [categoria]
Idempotente: SÍ
Autor: TaskMaster AI
Fecha: $(date +%Y-%m-%d)
*/

BEGIN;

DO $$
DECLARE
    script_name CONSTANT VARCHAR(255) := 'rollback_[XX]_[NNN]_[nombre].sql';
    original_script CONSTANT VARCHAR(255) := '[XX]_[NNN]_[nombre].sql';
    script_category CONSTANT VARCHAR(50) := '[categoria]';
    start_time TIMESTAMP := clock_timestamp();
    execution_time INTEGER;
    objects_dropped INTEGER := 0;
BEGIN
    -- Verificar que el script original fue ejecutado
    IF NOT is_script_executed(original_script) THEN
        RAISE NOTICE 'Script original % no ejecutado. Rollback innecesario.', original_script;
        RETURN;
    END IF;
    
    RAISE NOTICE 'Iniciando rollback de %...', original_script;
    
    -- =====================================================
    -- LÓGICA DE ROLLBACK ESPECÍFICA AQUÍ
    -- =====================================================
    
    -- [INSERTAR CÓDIGO DE ROLLBACK]
    
    -- =====================================================
    -- VALIDACIONES POST-ROLLBACK
    -- =====================================================
    
    -- [INSERTAR VALIDACIONES]
    
    -- =====================================================
    -- REGISTRO DE ROLLBACK EXITOSO
    -- =====================================================
    
    execution_time := EXTRACT(epoch FROM (clock_timestamp() - start_time)) * 1000;
    
    UPDATE migration_history 
    SET status = 'ROLLBACK',
        execution_time_ms = execution_time,
        error_message = format('Rollback ejecutado: %s objetos eliminados', objects_dropped),
        rollback_available = FALSE
    WHERE script_name = original_script;
    
    PERFORM register_migration_execution(
        script_name, script_category, execution_time,
        'SUCCESS', format('Rollback completado: %s objetos', objects_dropped), NULL
    );
    
    RAISE NOTICE '✅ Rollback completado en % ms', execution_time;
    
EXCEPTION WHEN OTHERS THEN
    execution_time := EXTRACT(epoch FROM (clock_timestamp() - start_time)) * 1000;
    PERFORM register_migration_execution(
        script_name, script_category, execution_time,
        'FAILED', 'Error durante rollback: ' || SQLERRM, NULL
    );
    RAISE EXCEPTION 'Error en rollback %: %', script_name, SQLERRM;
END
$$;

COMMIT;
```

### Rollback de Tablas

```sql
-- Ejemplo específico para rollback de tablas
DO $$
DECLARE
    table_list TEXT[] := ARRAY[
        'tabla_secundaria',  -- Eliminar en orden de dependencias
        'tabla_principal'
    ];
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY table_list
    LOOP
        IF EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = table_name
        ) THEN
            -- Verificar si la tabla tiene datos
            DECLARE
                row_count INTEGER;
            BEGIN
                EXECUTE format('SELECT COUNT(*) FROM %I', table_name) INTO row_count;
                
                IF row_count > 0 THEN
                    RAISE WARNING 'Tabla % contiene % registros que serán eliminados', 
                                  table_name, row_count;
                END IF;
                
                EXECUTE format('DROP TABLE %I CASCADE', table_name);
                objects_dropped := objects_dropped + 1;
                RAISE NOTICE '✓ Tabla % eliminada', table_name;
            END;
        END IF;
    END LOOP;
END;
```

### Rollback de Índices

```sql
-- Ejemplo específico para rollback de índices
DO $$
DECLARE
    index_list TEXT[] := ARRAY[
        'idx_usuarios_email',
        'idx_articulos_fecha',
        'idx_hechos_embedding'
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
        END IF;
    END LOOP;
END;
```

### Rollback de Funciones

```sql
-- Ejemplo específico para rollback de funciones
DO $$
DECLARE
    function_list TEXT[] := ARRAY[
        'insertar_articulo_completo(TEXT, TEXT, TEXT[])',
        'buscar_entidad_similar(TEXT, INTEGER)',
        'obtener_info_hilo(INTEGER)'
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
        END;
    END LOOP;
END;
```

### Rollback de Triggers

```sql
-- Ejemplo específico para rollback de triggers
DO $$
DECLARE
    trigger_info RECORD;
BEGIN
    -- Eliminar triggers específicos
    FOR trigger_info IN
        SELECT trigger_name, event_object_table
        FROM information_schema.triggers
        WHERE trigger_name IN (
            'sync_cache_entidades',
            'update_hilo_fecha_ultimo_hecho',
            'actualizar_estado_eventos_programados'
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
```

## 🔧 Scripts de Utilidad

### Script Shell para Rollback Automático

```bash
#!/bin/bash
# rollback.sh - Script para ejecutar rollbacks

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROLLBACK_DIR="$SCRIPT_DIR/rollbacks"
LOG_DIR="$SCRIPT_DIR/logs"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Función de ayuda
show_help() {
    echo "Uso: ./rollback.sh [OPCIONES]"
    echo ""
    echo "OPCIONES:"
    echo "  --list              Listar rollbacks disponibles"
    echo "  --dry-run           Mostrar qué se ejecutaría sin hacer cambios"
    echo "  --to SCRIPT         Rollback hasta un script específico"
    echo "  --single SCRIPT     Rollback de un solo script"
    echo "  --force             Forzar rollback ignorando dependencias"
    echo "  --confirm           Confirmar rollback destructivo"
    echo "  --help              Mostrar esta ayuda"
    echo ""
    echo "EJEMPLOS:"
    echo "  ./rollback.sh --list"
    echo "  ./rollback.sh --dry-run"
    echo "  ./rollback.sh --to 02_001_create_types_domains.sql --confirm"
    echo "  ./rollback.sh --single 03_001_create_tables.sql --confirm"
}

# Función para listar rollbacks disponibles
list_rollbacks() {
    echo -e "${GREEN}Rollbacks disponibles:${NC}"
    psql -c "SELECT * FROM list_available_rollbacks();" -t
}

# Función para dry run
dry_run() {
    local target_script="$1"
    echo -e "${YELLOW}DRY RUN - Rollback hasta: ${target_script:-COMPLETO}${NC}"
    
    if [ -z "$target_script" ]; then
        psql -c "SELECT * FROM execute_master_rollback();" -t
    else
        psql -c "SELECT * FROM execute_master_rollback('$target_script');" -t
    fi
}

# Función para ejecutar rollback real
execute_rollback() {
    local target_script="$1"
    local force_flag="$2"
    
    echo -e "${RED}EJECUTANDO ROLLBACK REAL...${NC}"
    echo -e "${RED}Esta operación es DESTRUCTIVA e IRREVERSIBLE${NC}"
    
    if [ -z "$target_script" ]; then
        psql -c "SELECT * FROM execute_master_rollback(NULL, FALSE, $force_flag);" -t
    else
        psql -c "SELECT * FROM execute_master_rollback('$target_script', FALSE, $force_flag);" -t
    fi
}

# Procesamiento de argumentos
DRY_RUN=false
LIST_ONLY=false
TARGET_SCRIPT=""
SINGLE_SCRIPT=""
FORCE=false
CONFIRM=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --list)
            LIST_ONLY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --to)
            TARGET_SCRIPT="$2"
            shift 2
            ;;
        --single)
            SINGLE_SCRIPT="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --confirm)
            CONFIRM=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Ejecutar según las opciones
if [ "$LIST_ONLY" = true ]; then
    list_rollbacks
elif [ "$DRY_RUN" = true ]; then
    dry_run "$TARGET_SCRIPT"
elif [ "$CONFIRM" = true ]; then
    execute_rollback "$TARGET_SCRIPT" "$FORCE"
else
    echo -e "${YELLOW}Use --dry-run para ver qué se ejecutaría, o --confirm para ejecutar realmente${NC}"
    show_help
    exit 1
fi
```

## ⚠️ Consideraciones de Seguridad

### 1. Backup Antes de Rollback
```sql
-- Crear backup antes de rollback destructivo
CREATE TABLE backup_migration_history AS 
SELECT * FROM migration_history;

-- Restaurar si es necesario
INSERT INTO migration_history 
SELECT * FROM backup_migration_history
WHERE NOT EXISTS (
    SELECT 1 FROM migration_history 
    WHERE script_name = backup_migration_history.script_name
);
```

### 2. Verificación de Dependencias
```sql
-- Verificar objetos que dependen antes de rollback
SELECT 
    schemaname,
    tablename,
    attname,
    typename
FROM pg_stats
WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
AND typename IN (
    'puntuacion_relevancia', 'estado_procesamiento', 
    'tipo_entidad', 'embedding_384d'
);
```

### 3. Logs de Rollback
```sql
-- Crear tabla de logs de rollback
CREATE TABLE IF NOT EXISTS rollback_logs (
    id SERIAL PRIMARY KEY,
    rollback_session_id UUID DEFAULT gen_random_uuid(),
    script_name VARCHAR(255),
    operation VARCHAR(100),
    object_name VARCHAR(255),
    before_state JSONB,
    after_state JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    user_name VARCHAR(100) DEFAULT current_user
);
```

## 📊 Monitoreo de Rollbacks

### Dashboard de Estado
```sql
-- Vista de resumen de rollbacks
CREATE OR REPLACE VIEW rollback_dashboard AS
SELECT 
    mh.category,
    COUNT(*) as total_scripts,
    COUNT(CASE WHEN mh.status = 'SUCCESS' THEN 1 END) as active_scripts,
    COUNT(CASE WHEN mh.status = 'ROLLBACK' THEN 1 END) as rolled_back,
    COUNT(CASE WHEN mh.rollback_available THEN 1 END) as rollback_available,
    MAX(mh.executed_at) as last_activity
FROM migration_history mh
GROUP BY mh.category
ORDER BY mh.category;
```

## 🎯 Mejores Prácticas

1. **Siempre probar con --dry-run primero**
2. **Crear backups antes de rollbacks destructivos**
3. **Verificar dependencias antes de rollback**
4. **Documentar razones para rollback**
5. **Coordinar con el equipo antes de rollbacks en producción**
6. **Mantener logs detallados de todas las operaciones**

---

**⚠️ IMPORTANTE**: Los rollbacks son operaciones críticas que pueden resultar en pérdida de datos. Siempre verificar y confirmar antes de ejecutar en entornos productivos.
