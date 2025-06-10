# Sistema de Orquestación de Migración - Máquina de Noticias

## 📋 Introducción

El sistema de orquestación coordina la ejecución completa de migración de base de datos, incluyendo validaciones automáticas, manejo de errores, rollbacks y monitoreo en tiempo real.

## 🛠️ Componentes del Sistema

### 1. Script Principal de Orquestación
**Archivo:** `deploy.sh`  
**Propósito:** Coordinar toda la migración con control granular

```bash
# Migración completa con backup
./deploy.sh --backup --verbose

# Solo una categoría específica
./deploy.sh --category 03_tables

# Dry run para verificar
./deploy.sh --dry-run

# Migración desde un punto específico
./deploy.sh --start-from 04_indexes --stop-at 06_triggers
```

### 2. Sistema de Testing
**Archivo:** `test_migration.sh`  
**Propósito:** Validar migración antes de producción

```bash
# Test completo con BD temporal
./test_migration.sh --mode full --create-test-db --cleanup

# Test de idempotencia
./test_migration.sh --mode idempotency --iterations 3

# Test de stress
./test_migration.sh --mode stress
```

### 3. Configuración de Entornos
**Archivo:** `config/environments.conf`  
**Propósito:** Configuraciones específicas por entorno

```bash
# Cargar configuración
source config/environments.conf

# Configurar entorno de desarrollo
set_environment development

# Configurar producción con migración inicial
set_environment production initial
```

## 🚀 Guía de Uso Rápido

### Primera Migración (Clean Database)

```bash
# 1. Configurar entorno
source config/environments.conf
set_environment development initial

# 2. Verificar configuración
show_current_config

# 3. Test completo
./test_migration.sh --mode full --create-test-db --cleanup

# 4. Dry run
./deploy.sh --dry-run --backup

# 5. Ejecución real
./deploy.sh --backup --verbose
```

### Migración Incremental

```bash
# 1. Configurar para incremental
source config/environments.conf
set_environment staging incremental

# 2. Migración específica
./deploy.sh --category 05_functions --backup

# 3. Validaciones post-migración
./deploy.sh --skip-validations --dry-run
```

### Despliegue en Producción

```bash
# 1. Configurar producción (DRY_RUN=true por defecto)
source config/environments.conf
set_environment production

# 2. Dry run obligatorio
./deploy.sh --verbose

# 3. Testing exhaustivo
./test_migration.sh --mode full

# 4. Habilitar ejecución real (con confirmación)
enable_real_execution

# 5. Ejecución real con máxima seguridad
./deploy.sh --backup --stop-on-error
```

## ⚙️ Opciones de Configuración

### Variables de Entorno Principales

| Variable | Descripción | Default |
|----------|-------------|---------|
| `MIGRATION_ENV` | Entorno actual | development |
| `PGHOST` | Host PostgreSQL | localhost |
| `PGPORT` | Puerto PostgreSQL | 5432 |
| `PGDATABASE` | Base de datos | (requerido) |
| `PGUSER` | Usuario PostgreSQL | (requerido) |
| `MIGRATION_TIMEOUT` | Timeout por script (s) | 300 |
| `DRY_RUN` | Modo simulación | false |
| `STOP_ON_ERROR` | Parar en errores | true |
| `BACKUP_BEFORE_DEPLOY` | Crear backup | false |

### Opciones del Script deploy.sh

| Opción | Descripción |
|--------|-------------|
| `--dry-run` | Modo simulación sin cambios reales |
| `--category CATEGORIA` | Ejecutar solo una categoría |
| `--start-from CATEGORIA` | Iniciar desde categoría específica |
| `--stop-at CATEGORIA` | Parar en categoría específica |
| `--skip-validations` | Omitir validaciones pre/post |
| `--force` | Continuar a pesar de advertencias |
| `--backup` | Crear backup antes de migración |
| `--verbose` | Output detallado |
| `--continue-on-error` | Continuar en errores no críticos |

## 📊 Categorías de Migración

El sistema ejecuta las categorías en orden específico:

1. **01_schema** - Extensiones y esquemas básicos
2. **02_types_domains** - Tipos y dominios personalizados  
3. **03_tables** - Tablas principales y particiones
4. **04_indexes** - Índices B-tree, GIN y vectoriales
5. **05_functions** - Funciones PL/pgSQL y RPC
6. **06_triggers** - Triggers y automatizaciones
7. **07_materialized_views** - Vistas materializadas
8. **08_reference_data** - Datos de referencia y testing

### Ejecución Granular

```bash
# Solo esquemas y tipos
./deploy.sh --start-from 01_schema --stop-at 02_types_domains

# Solo índices
./deploy.sh --category 04_indexes

# Desde funciones hasta el final
./deploy.sh --start-from 05_functions
```

## 🔍 Sistema de Validaciones Integrado

### Validaciones Automáticas

El sistema ejecuta automáticamente:
- **Pre-migración**: Verificar entorno, extensiones, conflictos
- **Post-migración**: Verificar objetos creados, integridad, funcionalidad

### Control de Validaciones

```bash
# Con validaciones completas (recomendado)
./deploy.sh --verbose

# Omitir validaciones (solo en desarrollo)
./deploy.sh --skip-validations

# Forzar continuación en advertencias
./deploy.sh --force
```

## 📈 Monitoreo y Logging

### Logs Automáticos

Todos los scripts generan logs detallados:
- `logs/deployment_YYYYMMDD_HHMMSS.log` - Log de migración
- `logs/test_migration_YYYYMMDD_HHMMSS.log` - Log de testing
- `logs/rollback_YYYYMMDD.log` - Log de rollbacks

### Métricas en Tiempo Real

```bash
# Progreso visual durante ejecución
[2025-05-24 10:30:15] [INFO] [1/8] Ejecutando: 01_001_create_extensions_schemas.sql
Progreso: [=========>                     ] 30% - 03_tables
```

### Información de Estado

```bash
# Ver configuración actual
show_current_config

# Validar entorno
validate_environment production

# Ver logs recientes
tail -f logs/deployment_$(date +%Y%m%d)*.log
```

## 🛡️ Estrategias de Seguridad

### Entornos de Producción

1. **DRY_RUN obligatorio**: Siempre ejecutar dry-run primero
2. **Backup automático**: Backup completo antes de cambios
3. **Validaciones estrictas**: Sin omitir validaciones
4. **Confirmación explícita**: Requiere confirmación para ejecución real

### Manejo de Errores

```bash
# Parar en primer error (recomendado para producción)
./deploy.sh --stop-on-error

# Continuar en errores menores (desarrollo)
./deploy.sh --continue-on-error --force
```

### Rollback de Emergencia

```bash
# Rollback completo
./rollback.sh --confirm

# Rollback hasta punto específico
./rollback.sh --to 03_001_create_tables.sql --confirm
```

## 🧪 Testing y Validación

### Tipos de Testing

| Modo | Descripción | Uso |
|------|-------------|-----|
| `full` | Testing completo con rollback | Pre-producción |
| `quick` | Validaciones rápidas | Desarrollo |
| `rollback` | Testing específico de rollbacks | Validar rollbacks |
| `stress` | Testing de carga concurrente | Performance |
| `idempotency` | Múltiples ejecuciones | Validar idempotencia |

### Estrategia de Testing Recomendada

```bash
# 1. Test rápido durante desarrollo
./test_migration.sh --mode quick

# 2. Test completo antes de staging
./test_migration.sh --mode full --create-test-db --cleanup

# 3. Test de idempotencia
./test_migration.sh --mode idempotency --iterations 3

# 4. Test de stress antes de producción
./test_migration.sh --mode stress
```

## 🔄 Flujo de Despliegue Completo

### Desarrollo → Staging → Producción

```bash
# DESARROLLO
set_environment development
./test_migration.sh --mode quick
./deploy.sh --verbose

# STAGING  
set_environment staging
./test_migration.sh --mode full --create-test-db --cleanup
./deploy.sh --backup --verbose

# PRODUCCIÓN
set_environment production
./deploy.sh --dry-run --verbose              # Obligatorio
./test_migration.sh --mode stress            # Recomendado
enable_real_execution                        # Con confirmación
./deploy.sh --backup --stop-on-error         # Ejecución real
```

## 🚨 Troubleshooting

### Errores Comunes

**Error de conexión:**
```bash
# Verificar variables de entorno
echo $PGHOST $PGPORT $PGDATABASE $PGUSER

# Test de conexión manual
psql -c "SELECT version();"
```

**Script falla en categoría específica:**
```bash
# Ver log detallado
tail -f logs/deployment_*.log

# Ejecutar solo esa categoría
./deploy.sh --category 03_tables --verbose

# Verificar scripts en la categoría
ls -la 03_tables/
```

**Validaciones fallan:**
```bash
# Ver detalles de validaciones
psql -c "SELECT * FROM execute_pre_migration_validations();"

# Ejecutar con forzado (solo desarrollo)
./deploy.sh --force --continue-on-error
```

### Recuperación de Errores

```bash
# 1. Verificar estado actual
psql -c "SELECT * FROM migration_history ORDER BY executed_at DESC LIMIT 5;"

# 2. Rollback si es necesario
./rollback.sh --dry-run
./rollback.sh --confirm

# 3. Corregir problema y reintentar
./deploy.sh --start-from <ultima_categoria_exitosa>
```

## 📚 Scripts de Utilidad

### Verificación de Estado

```bash
# Ver últimas migraciones
psql -c "SELECT script_name, status, executed_at FROM migration_history ORDER BY executed_at DESC LIMIT 10;"

# Ver rollbacks disponibles
psql -c "SELECT * FROM list_available_rollbacks();"

# Estadísticas de validaciones
psql -c "SELECT * FROM generate_validation_report(7);"
```

### Mantenimiento

```bash
# Limpiar logs antiguos (>30 días)
find logs/ -name "*.log" -mtime +30 -delete

# Verificar estructura de migración
./verify_structure.sh

# Validar rollbacks disponibles
psql -c "SELECT * FROM validate_rollback_implementation();"
```

## 🎯 Mejores Prácticas

### Antes de Migración

1. ✅ **Backup completo** de base de datos de producción
2. ✅ **Testing exhaustivo** en entorno idéntico
3. ✅ **Dry-run** múltiples veces
4. ✅ **Validar rollbacks** disponibles
5. ✅ **Coordinar con equipo** y stakeholders

### Durante Migración

1. 📊 **Monitorear logs** en tiempo real
2. 🚨 **Tener rollback listo** para ejecutar
3. ⏱️ **Respetar timeouts** configurados
4. 📞 **Mantener comunicación** con equipo
5. 📝 **Documentar problemas** encontrados

### Después de Migración

1. ✅ **Ejecutar validaciones post** completas
2. 🧪 **Testing funcional** de aplicación
3. 📊 **Verificar métricas** de rendimiento
4. 📚 **Actualizar documentación**
5. 🎉 **Celebrar éxito** del equipo

---

**💡 Tip**: Para nuevos usuarios, comenzar siempre con `./deploy.sh --dry-run` y `./test_migration.sh --mode quick` para familiarizarse con el sistema.
