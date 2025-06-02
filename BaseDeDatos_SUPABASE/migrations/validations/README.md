# Sistema de Validaciones Automáticas - Máquina de Noticias

## 📋 Introducción

El sistema de validaciones automáticas garantiza la integridad y completitud de las migraciones mediante verificaciones exhaustivas antes y después de cada paso de migración.

## 🎯 Tipos de Validaciones

### 1. Validaciones Pre-Migración
Verifican que el entorno esté listo para ejecutar la migración:
- ✅ **Entorno**: Versión PostgreSQL, permisos, espacio en disco
- ✅ **Extensiones**: Disponibilidad de extensiones requeridas
- ✅ **Estado BD**: Conexiones activas, transacciones largas
- ✅ **Conflictos**: Objetos existentes que podrían conflictuar

### 2. Validaciones Post-Migración
Verifican que la migración se ejecutó correctamente:
- ✅ **Objetos Creados**: Extensiones, esquemas, tipos, tablas
- ✅ **Estructura**: Claves primarias, índices, triggers
- ✅ **Funcionalidad**: Funciones RPC, vistas materializadas
- ✅ **Integridad**: Datos consistentes, referencias válidas

## 🛠️ Funciones Principales

### execute_pre_migration_validations()
```sql
-- Ejecutar todas las validaciones pre-migración
SELECT * FROM execute_pre_migration_validations();

-- Validaciones específicas por categoría
SELECT * FROM execute_pre_migration_validations('schema', true);

-- Parámetros:
-- p_target_category: 'schema', 'tables', 'indexes', etc. (NULL = todas)
-- p_strict_mode: true = falla en warnings, false = solo en errores críticos
```

### execute_post_migration_validations()
```sql
-- Ejecutar todas las validaciones post-migración
SELECT * FROM execute_post_migration_validations();

-- Validaciones profundas (más lentas pero exhaustivas)
SELECT * FROM execute_post_migration_validations(NULL, true);

-- Parámetros:
-- p_target_category: categoría específica a validar
-- p_deep_validation: validación profunda de integridad y rendimiento
```

### execute_automated_validations()
```sql
-- Función integrada que combina pre/post validaciones
SELECT * FROM execute_automated_validations('pre', 'schema');
SELECT * FROM execute_automated_validations('post', NULL, false, true);

-- Parámetros:
-- p_validation_type: 'pre' o 'post'
-- p_category: categoría específica (opcional)
-- p_strict_mode: modo estricto para pre-validaciones
-- p_deep_validation: validación profunda para post-validaciones
```

### validate_migration_step()
```sql
-- Validar un paso específico de migración
SELECT validate_migration_step(
    '01_001_create_extensions_schemas.sql',
    'schema',
    'pre'
);

-- Retorna: BOOLEAN (true = validaciones pasaron, false = fallaron)
```

## 📊 Categorías de Validación

| Categoría | Pre-Migración | Post-Migración | Descripción |
|-----------|---------------|----------------|-------------|
| `environment` | ✅ | ❌ | Entorno y prerrequisitos |
| `extensions` | ✅ | ✅ | Extensiones PostgreSQL |
| `schemas` | ✅ | ✅ | Esquemas y namespaces |
| `types_domains` | ✅ | ✅ | Tipos y dominios personalizados |
| `tables` | ✅ | ✅ | Tablas y estructura |
| `indexes` | ❌ | ✅ | Índices y optimización |
| `functions` | ❌ | ✅ | Funciones PL/pgSQL |
| `triggers` | ❌ | ✅ | Triggers automáticos |
| `materialized_views` | ❌ | ✅ | Vistas materializadas |
| `conflicts` | ✅ | ❌ | Conflictos de nombres |
| `performance` | ❌ | ✅* | Rendimiento (* solo deep) |
| `deep_validation` | ❌ | ✅* | Integridad profunda (* solo deep) |

## 🔍 Estados de Validación

### Estados de Resultado
- **PASS**: Validación exitosa ✅
- **FAIL**: Validación fallida ❌
- **WARNING**: Advertencia ⚠️
- **INFO**: Información 📋

### Niveles de Severidad
- **CRITICAL**: Error crítico que bloquea migración
- **WARNING**: Advertencia que requiere atención
- **INFO**: Información general

## 📈 Monitoreo y Reporting

### Vista de Resumen por Categoría
```sql
SELECT * FROM validation_summary_by_category;
```

### Historial de Validaciones
```sql
-- Ver últimas 10 validaciones
SELECT 
    validation_type,
    category,
    overall_status,
    total_validations,
    execution_time_ms,
    executed_at
FROM validation_history
ORDER BY executed_at DESC
LIMIT 10;
```

### Reporte de Validaciones
```sql
-- Reporte de los últimos 7 días
SELECT * FROM generate_validation_report(7);

-- Métricas incluidas:
-- - Total validaciones ejecutadas
-- - Tasa de éxito/fallo
-- - Tiempo promedio de ejecución
-- - Categoría más problemática
```

## 🔧 Integración en Scripts de Migración

### Plantilla Básica
```sql
-- Al inicio del script de migración
DO $$
DECLARE
    script_name CONSTANT VARCHAR(255) := 'mi_script.sql';
    script_category CONSTANT VARCHAR(50) := 'tables';
BEGIN
    -- Validaciones pre-migración
    IF NOT validate_migration_step(script_name, script_category, 'pre') THEN
        RAISE EXCEPTION 'Pre-validaciones fallaron para %', script_name;
    END IF;
    
    -- LÓGICA DE MIGRACIÓN AQUÍ
    -- ...
    
    -- Validaciones post-migración
    IF NOT validate_migration_step(script_name, script_category, 'post') THEN
        RAISE WARNING 'Post-validaciones fallaron para %', script_name;
    END IF;
END
$$;
```

### Validaciones Automáticas en Master Script
```sql
-- En el script maestro de migración
SELECT * FROM execute_automated_validations('pre');  -- Antes de migración
-- ... ejecutar scripts de migración ...
SELECT * FROM execute_automated_validations('post', NULL, false, true);  -- Después de migración
```

## ⚙️ Configuración Avanzada

### Validaciones Específicas de Supabase
```sql
-- Verificar entorno Supabase
SELECT * FROM validate_supabase_environment();
```

### Validaciones de Funcionalidad del Sistema
```sql
-- Tests funcionales básicos
SELECT * FROM validate_system_functionality();
```

### Personalización de Validaciones
```sql
-- Ejemplo: Agregar validación personalizada
CREATE OR REPLACE FUNCTION validate_custom_requirement()
RETURNS TABLE (
    validation_name VARCHAR(100),
    status VARCHAR(20),
    message TEXT
) AS $$
BEGIN
    -- Lógica de validación personalizada
    IF EXISTS (SELECT 1 FROM mi_tabla_critica WHERE estado = 'error') THEN
        RETURN QUERY SELECT
            'Custom Data Validation'::VARCHAR(100),
            'FAIL'::VARCHAR(20),
            'Se encontraron datos en estado de error'::TEXT;
    ELSE
        RETURN QUERY SELECT
            'Custom Data Validation'::VARCHAR(100),
            'PASS'::VARCHAR(20),
            'Datos en estado correcto'::TEXT;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

## 🚨 Manejo de Errores

### Estrategias de Respuesta

1. **CRITICAL Errors**: Detener migración inmediatamente
2. **WARNING Alerts**: Continuar con precaución
3. **INFO Messages**: Registrar para referencia

### Ejemplo de Manejo de Errores
```sql
DO $$
DECLARE
    validation_result RECORD;
BEGIN
    SELECT * INTO validation_result
    FROM execute_automated_validations('pre', 'tables');
    
    CASE validation_result.overall_status
        WHEN 'FAILED' THEN
            RAISE EXCEPTION 'Validaciones críticas fallaron: %', 
                          validation_result.report_summary;
        WHEN 'WARNING' THEN
            RAISE NOTICE 'Validaciones completadas con advertencias: %', 
                        validation_result.report_summary;
        ELSE
            RAISE NOTICE 'Todas las validaciones pasaron exitosamente';
    END CASE;
END
$$;
```

## 📋 Checklist de Validaciones

### Pre-Migración ✅
- [ ] PostgreSQL versión >= 14
- [ ] Usuario tiene permisos CREATE
- [ ] Extensiones requeridas disponibles
- [ ] Sin transacciones largas activas
- [ ] Espacio en disco suficiente
- [ ] Sin conflictos de nombres de objetos

### Post-Migración ✅
- [ ] Extensiones instaladas correctamente
- [ ] Esquemas creados y accesibles
- [ ] Tipos y dominios funcionando
- [ ] Tablas con estructura correcta
- [ ] Índices creados y optimizados
- [ ] Funciones RPC operativas
- [ ] Triggers funcionando automáticamente
- [ ] Vistas materializadas pobladas
- [ ] Integridad referencial mantenida

## 🎯 Mejores Prácticas

1. **Ejecutar siempre pre-validaciones** antes de cualquier migración
2. **Usar modo estricto** en entornos de producción
3. **Ejecutar validaciones profundas** después de migraciones mayores
4. **Monitorear métricas** de validación regularmente
5. **Documentar validaciones personalizadas** específicas del proyecto
6. **Crear alertas** para validaciones fallidas frecuentes
7. **Revisar reportes** semanalmente para identificar tendencias

## 📚 Archivos del Sistema

- `validate_pre_migration.sql` - Validaciones preliminares
- `validate_post_migration.sql` - Validaciones posteriores
- `automated_validation_system.sql` - Sistema integrado
- `README.md` - Esta documentación

## 🔗 Referencias

- PostgreSQL Documentation: [System Catalogs](https://postgresql.org/docs/current/catalogs.html)
- Supabase Documentation: [Extensions](https://supabase.com/docs/guides/database/extensions)
- Migration Best Practices: [Database Migrations](https://martinfowler.com/articles/evodb.html)

---

**💡 Nota**: El sistema de validaciones está diseñado para ser exhaustivo pero eficiente. Las validaciones profundas solo deben usarse cuando sea necesario debido a su mayor tiempo de ejecución.
