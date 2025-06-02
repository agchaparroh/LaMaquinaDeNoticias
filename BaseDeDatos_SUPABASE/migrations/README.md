# Sistema de Migración - Máquina de Noticias

## 📁 Estructura de Directorios

La estructura de migración está organizada por tipo de objeto y orden de ejecución:

```
migrations/
├── config/                 # Configuraciones globales
│   └── migration_config.sql
├── 01_schema/             # Creación de esquemas y extensiones
├── 02_types_domains/      # Tipos personalizados y dominios
├── 03_tables/             # Creación de tablas (principales y particiones)
├── 04_indexes/            # Índices (B-tree, GIN, vectoriales)
├── 05_functions/          # Funciones PL/pgSQL y RPC
├── 06_triggers/           # Triggers y automatizaciones
├── 07_materialized_views/ # Vistas materializadas
├── 08_reference_data/     # Datos de referencia y testing
├── rollbacks/             # Scripts de rollback por categoría
├── validations/           # Scripts de validación pre/post migración
└── logs/                  # Logs de ejecución (generados automáticamente)
```

## 🔢 Convenciones de Nomenclatura

### Scripts de Migración
```
[CATEGORIA]_[NUMERO]_[DESCRIPCION].sql

Ejemplos:
- 01_001_create_extensions.sql
- 02_001_create_domains.sql
- 03_001_create_main_tables.sql
- 04_001_create_btree_indexes.sql
```

### Scripts de Rollback
```
rollback_[CATEGORIA]_[NUMERO]_[DESCRIPCION].sql

Ejemplos:
- rollback_01_001_create_extensions.sql
- rollback_03_001_create_main_tables.sql
```

### Scripts de Validación
```
validate_[PRE|POST]_[CATEGORIA].sql

Ejemplos:
- validate_pre_schema.sql
- validate_post_tables.sql
- validate_post_indexes.sql
```

## 📋 Orden de Ejecución

1. **config/migration_config.sql** - Configuración global (siempre primero)
2. **validations/validate_pre_*.sql** - Validaciones preliminares
3. **01_schema/** - Extensiones y esquemas
4. **02_types_domains/** - Tipos y dominios personalizados
5. **03_tables/** - Tablas principales y particiones
6. **04_indexes/** - Todos los índices
7. **05_functions/** - Funciones PL/pgSQL
8. **06_triggers/** - Triggers y automatizaciones
9. **07_materialized_views/** - Vistas materializadas
10. **08_reference_data/** - Datos de referencia y testing
11. **validations/validate_post_*.sql** - Validaciones finales

## 🔄 Principios de Idempotencia

Todos los scripts deben seguir estos principios:

### ✅ Verificaciones de Existencia
```sql
-- Para extensiones
CREATE EXTENSION IF NOT EXISTS vector;

-- Para esquemas
CREATE SCHEMA IF NOT EXISTS analytics;

-- Para tablas
CREATE TABLE IF NOT EXISTS entidades (
    id SERIAL PRIMARY KEY,
    -- ...
);

-- Para índices
CREATE INDEX IF NOT EXISTS idx_entidades_nombre 
ON entidades(nombre);
```

### ✅ Control de Versiones
```sql
-- Verificar si un script ya se ejecutó
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM migration_history 
        WHERE script_name = '03_001_create_main_tables.sql'
    ) THEN
        RAISE NOTICE 'Script ya ejecutado anteriormente';
        RETURN;
    END IF;
    
    -- Código del script aquí...
    
    -- Registrar ejecución
    INSERT INTO migration_history (script_name, executed_at)
    VALUES ('03_001_create_main_tables.sql', NOW());
END
$$;
```

### ✅ Transacciones Atómicas
```sql
BEGIN;

-- Verificaciones previas
-- Creación de objetos
-- Validaciones posteriores

COMMIT;
```

## 🛡️ Estrategia de Rollback

### Rollback Individual
```bash
# Rollback de un script específico
psql -f rollbacks/rollback_03_001_create_main_tables.sql
```

### Rollback Completo
```bash
# Rollback de toda la migración (en orden inverso)
./rollback_all.sh
```

### Puntos de Control
- Cada categoría puede ser rollback independientemente
- Los rollbacks se ejecutan en orden inverso a la instalación
- Validaciones automáticas antes de cada rollback

## 📊 Logging y Monitoreo

### Tabla de Control de Migración
```sql
CREATE TABLE IF NOT EXISTS migration_history (
    id SERIAL PRIMARY KEY,
    script_name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    executed_at TIMESTAMP DEFAULT NOW(),
    execution_time_ms INTEGER,
    status VARCHAR(20) DEFAULT 'SUCCESS',
    error_message TEXT,
    rollback_available BOOLEAN DEFAULT TRUE
);
```

### Logs Automáticos
- Todos los scripts generan logs en `migrations/logs/`
- Timestamps completos de inicio/fin
- Métricas de rendimiento
- Errores detallados para debugging

## 🔧 Scripts de Utilidad

### deploy.sh - Script Principal
```bash
#!/bin/bash
# Ejecuta migración completa con validaciones
./deploy.sh [--dry-run] [--stop-on-error] [--category=03_tables]
```

### validate.sh - Solo Validaciones
```bash
#!/bin/bash
# Ejecuta solo las validaciones
./validate.sh [--pre] [--post] [--category=tables]
```

### rollback.sh - Rollback Controlado
```bash
#!/bin/bash
# Rollback hasta un punto específico
./rollback.sh [--to-category=02_types_domains] [--confirm]
```

## 🎯 Variables de Entorno

```bash
# Configuración de conexión
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=maquina_noticias
export PGUSER=supabase_admin

# Configuración de migración
export MIGRATION_MODE=production  # development|staging|production
export DRY_RUN=false
export STOP_ON_ERROR=true
export LOG_LEVEL=INFO
```

## 📚 Documentación Adicional

- `validations/README.md` - Guía de validaciones
- `rollbacks/README.md` - Procedimientos de rollback
- `config/README.md` - Configuraciones avanzadas
- `logs/README.md` - Interpretación de logs

---

**⚠️ IMPORTANTE**: Todos los scripts deben ser probados en un entorno de desarrollo antes de ejecutar en producción. La estructura está diseñada para máxima robustez y trazabilidad.
