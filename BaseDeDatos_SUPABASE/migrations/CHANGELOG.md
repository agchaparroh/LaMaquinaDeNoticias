# Changelog - Sistema de Migración Máquina de Noticias

Todos los cambios notables en el sistema de migración de base de datos serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto sigue [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-05-24

### Agregado
- Sistema completo de migración idempotente para PostgreSQL
- Arquitectura base de datos para Máquina de Noticias
- Sistema de orquestación automática con scripts shell
- Validaciones automáticas pre y post migración
- Sistema completo de rollback con seguridad
- Testing integrado con múltiples modos
- Soporte para múltiples entornos (dev, staging, prod, supabase)
- Documentación completa y guías de uso

#### Scripts de Migración Implementados

##### [00_000] - Infraestructura
- `00_000_migration_control.sql` - Sistema de control y tracking de migración
  - Tabla `migration_history` para tracking de scripts ejecutados
  - Funciones auxiliares: `register_migration_execution()`, `is_script_executed()`
  - Sistema de validación de checksums y control de versiones

##### [01_001] - Esquemas y Extensiones
- `01_001_create_extensions_schemas.sql` - Extensiones PostgreSQL y esquemas base
  - Extensión `vector` para embeddings vectoriales (384 dimensiones)
  - Extensión `pg_trgm` para similitud de texto (umbral 0.3)
  - Extensión `pg_cron` para trabajos programados (opcional)
  - Esquemas organizacionales: `analytics`, `utils`, `audit`
  - Configuración de `search_path` optimizado

##### [02_001] - Tipos y Dominios
- `02_001_create_types_domains.sql` - Tipos personalizados y dominios de validación
  - **Dominios de puntuación**: `puntuacion_relevancia` (0-10), `grado_contradiccion` (1-5)
  - **Dominios de validación**: `url_valida`, `codigo_pais` (ISO 2 letras), `nivel_confianza` (0.0-1.0)
  - **Tipos ENUM**: `estado_procesamiento`, `tipo_entidad`, `nivel_actividad`, `estado_evento`
  - **Tipos composite**: `coordenadas_geo`, `metricas_calidad`
  - **Validación vectorial**: `embedding_384d` con función de validación de dimensiones

#### Funciones RPC Críticas Implementadas

##### Sistema de Artículos y Contenido
- `insertar_articulo_completo()` - Inserción atómica de artículos con metadatos
- `insertar_fragmento_completo()` - Inserción de fragmentos con referencias
- `buscar_entidad_similar()` - Búsqueda semántica con similitud de texto

##### Sistema de Hilos Narrativos
- `obtener_info_hilo()` - Recuperación completa de información de hilos
- `actualizar_hilo_metadatos()` - Actualización de metadatos de hilos

##### Sistema de Cache y Sincronización
- `sync_cache_entidades()` - Sincronización automática de cache
- `update_hilo_fecha_ultimo_hecho()` - Actualización de fechas en hilos
- `actualizar_estado_eventos_programados()` - Gestión de eventos futuros
- `insertar_evento_programado_inicial()` - Creación automática de eventos

#### Triggers Automáticos Implementados

##### Triggers de Sincronización
- `sync_cache_entidades` en tabla `entidades` (INSERT/UPDATE/DELETE)
- `update_hilo_fecha_ultimo_hecho` en tabla `hecho_hilo` (INSERT/UPDATE/DELETE)

##### Triggers de Eventos Programados  
- `actualizar_estado_eventos_programados` en todas las particiones de `hechos` (UPDATE)
- `insertar_evento_programado_inicial` en todas las particiones de `hechos` (INSERT)

#### Vistas Materializadas Implementadas

##### Vistas Básicas de Análisis
- `estadisticas_globales` - Métricas completas del sistema con totales por tipo
- `entidades_relevantes_recientes` - Top entidades últimos 30 días con score de relevancia
- `resumen_hilos_activos` - Estado de hilos narrativos con métricas de actividad
- `agenda_eventos_proximos` - Eventos futuros organizados por horizonte temporal

##### Vistas Analíticas Avanzadas
- `tendencias_temas` - Evolución de etiquetas en últimos 90 días con cambio porcentual
- `correlaciones_temporales` - Correlaciones entre entidades a lo largo del tiempo
- `patrones_emergentes_anomalias` - Detección automática de anomalías y patrones
- `redes_entidades_centralidad` - Análisis de centralidad en redes de entidades

##### Vistas de Calidad y Sugerencias
- `metricas_calidad_datos` - Score de calidad global con recomendaciones
- `contradicciones_conflictos` - Detección automática de contradicciones
- `hilos_sugeridos_hechos` - Sugerencias automáticas de vinculación de hechos

#### Índices Optimizados Implementados

##### Índices B-Tree Fundamentales
- Claves primarias en todas las tablas principales
- Claves foráneas para optimizar JOINs
- Campos de búsqueda frecuente (fechas, nombres, estados)

##### Índices GIN para Arrays y Texto
- `idx_hechos_etiquetas_gin` - Búsqueda en arrays de etiquetas
- `idx_entidades_aliases_gin` - Búsqueda en aliases de entidades
- `idx_articulos_palabras_clave_gin` - Búsqueda en palabras clave
- Índices de texto completo para campos de contenido

##### Índices pg_trgm para Similitud
- `idx_entidades_nombre_trgm` - Similitud en nombres de entidades
- `idx_articulos_titulo_trgm` - Similitud en títulos de artículos
- Configuración de umbral de similitud al 30%

##### Índices Vectoriales pgvector
- `idx_hechos_embedding_ivfflat` - Búsqueda vectorial en hechos
- `idx_entidades_embedding_ivfflat` - Búsqueda vectorial en entidades
- `idx_hilos_embedding_ivfflat` - Búsqueda vectorial en hilos
- Configuración optimizada de parámetros IVFFLAT

#### Tablas Principales Implementadas

##### Tablas de Entidades Core
- `entidades` - Entidades principales (personas, organizaciones, lugares)
- `articulos` - Artículos de noticias con metadatos completos
- `documentos_extensos` - Documentos largos con fragmentación
- `fragmentos_extensos` - Fragmentos de documentos con referencias

##### Tablas de Hechos y Narrativa
- `hechos` - Tabla principal particionada por fecha_ocurrencia (10 particiones)
- `hilos_narrativos` - Hilos de discusión y narrativas
- `citas_textuales` - Citas extraídas de documentos
- `datos_cuantitativos` - Datos numéricos y estadísticos

##### Tablas de Relaciones
- `hecho_entidad` - Relaciones many-to-many entre hechos y entidades
- `hecho_hilo` - Vinculación de hechos con hilos narrativos
- `hecho_articulo` - Referencias de hechos a artículos fuente
- `contradicciones` - Contradicciones identificadas entre hechos

##### Tablas de Soporte
- `cache_entidades` - Cache optimizado de información de entidades
- `eventos_futuros` - Eventos programados para el futuro
- `consultas_queries` - Log de consultas realizadas
- `feedback_usuarios` - Feedback y evaluaciones de usuarios

#### Sistema de Validaciones Implementado

##### Validaciones Pre-Migración
- Verificación de versión PostgreSQL (mínimo 14)
- Validación de permisos de usuario (CREATE, SUPERUSER)
- Verificación de extensiones disponibles
- Análisis de espacio en disco
- Detección de conflictos de nombres
- Verificación de conexiones activas y transacciones largas

##### Validaciones Post-Migración
- Verificación de objetos creados (extensiones, esquemas, tipos, tablas)
- Validación de estructura (PKs, índices, triggers, funciones)
- Tests de funcionalidad del sistema
- Verificación de vistas materializadas pobladas
- Validaciones profundas de integridad y rendimiento

##### Sistema de Validación Automática
- `execute_automated_validations()` - Coordina validaciones pre/post
- `validation_history` - Tabla de tracking de validaciones con métricas
- `validation_summary_by_category` - Vista de resumen por categoría
- Reportes automáticos con tendencias y métricas de calidad

#### Sistema de Rollback Implementado

##### Scripts de Rollback Específicos
- `rollback_01_001_create_extensions_schemas.sql` - Rollback de extensiones/esquemas
- `rollback_02_001_create_types_domains.sql` - Rollback de tipos/dominios
- Plantilla genérica `rollback_template.sql` para nuevos rollbacks

##### Sistema de Rollback Maestro
- `execute_master_rollback()` - Coordina rollbacks en orden inverso
- `is_rollback_safe()` - Verifica seguridad antes de rollback
- `list_available_rollbacks()` - Lista rollbacks disponibles
- `validate_pre_rollback()` - Validaciones preliminares de rollback

##### Herramientas de Rollback
- `rollback.sh` - Script shell automatizado con validaciones
- Soporte para rollback completo, parcial o individual
- Confirmaciones de seguridad para operaciones destructivas
- Logging detallado de operaciones de rollback

#### Sistema de Orquestación Implementado

##### Script Principal de Orquestación
- `deploy.sh` - Coordina migración completa con control granular
- Ejecución secuencial por categorías (01_schema → 08_reference_data)
- Validaciones automáticas integradas pre/post migración
- Progress bar visual y logging detallado con timestamps
- Manejo robusto de errores con estrategias por severidad

##### Sistema de Testing Integrado
- `test_migration.sh` - Testing con 5 modos especializados
  - `full`: Testing completo con rollback incluido
  - `quick`: Validaciones rápidas para desarrollo
  - `rollback`: Testing específico de rollbacks
  - `stress`: Testing de carga concurrente
  - `idempotency`: Testing de múltiples ejecuciones

##### Configuración de Entornos
- `config/environments.conf` - Configuraciones por entorno
- Soporte para 5 entornos: development, staging, production, testing, supabase
- Validaciones específicas por entorno
- Confirmación explícita para ejecución en producción

##### Utilidades de Soporte
- `migration_utils.sh` - 10 comandos de utilidad
  - `status`: Estado completo del sistema
  - `history`: Historial de migraciones
  - `validate`: Validación profunda del sistema
  - `cleanup`: Limpieza de logs y temporales
  - `backup`: Backup manual con compresión
  - `check-deps`: Verificación de dependencias
  - `generate-report`: Reportes automáticos

#### Datos de Referencia y Testing

##### Datos Estructurados de Prueba
- 29 entidades de prueba (personas, organizaciones, lugares)
- 205 hechos distribuidos en múltiples particiones
- 7 hilos narrativos con relaciones complejas
- 1 artículo de referencia con metadatos completos
- Embeddings vectoriales de 384 dimensiones para búsqueda semántica

##### Configuración de Testing
- Particionamiento funcional con 10 particiones por fecha
- Índices vectoriales optimizados con parámetros específicos
- Vistas materializadas pobladas con datos reales
- Sistema de cache sincronizado automáticamente

### Configuraciones Implementadas

#### Configuración Global del Sistema
- Timeouts configurables por entorno (60-600 segundos)
- Logging jerárquico con rotación automática
- Variables de entorno específicas por tipo de despliegue
- Configuración de memoria para operaciones complejas (256MB work_mem, 512MB maintenance_work_mem)

#### Configuración de Extensiones
- pgvector configurado para embeddings de 384 dimensiones
- pg_trgm con umbral de similitud al 30%
- Parámetros IVFFLAT optimizados según volumen de datos

#### Configuración de Seguridad
- DRY_RUN por defecto en entorno de producción
- Backup automático antes de migraciones críticas
- Confirmaciones explícitas para operaciones destructivas
- Validación de permisos antes de cada operación

### Herramientas de Desarrollo

#### Plantillas y Guías
- `config/idempotent_template.sql` - Plantilla base para scripts idempotentes
- `rollbacks/rollback_template.sql` - Plantilla para scripts de rollback
- `config/idempotency_best_practices.md` - Guía de mejores prácticas
- `MIGRATION_GUIDE.md` - Guía completa de uso del sistema

#### Scripts de Utilidad
- `verify_structure.sh` - Verificación de estructura de migración
- Generación automática de reportes con métricas
- Validación automática de rollbacks disponibles
- Corrección automática de permisos de archivos

### Documentación Implementada

#### Documentación Técnica
- `README.md` - Documentación principal del sistema
- `README_orchestration.md` - Guía específica de orquestación
- `validations/README.md` - Documentación de sistema de validaciones
- `rollbacks/README.md` - Documentación de sistema de rollbacks

#### Guías de Usuario
- `MIGRATION_GUIDE.md` - Guía completa con ejemplos prácticos
- Troubleshooting con soluciones a problemas comunes
- Mejores prácticas para desarrollo y producción
- Referencias completas de APIs y funciones

### Métricas y Monitoreo

#### Sistema de Métricas
- Tracking completo de ejecución con timestamps y duración
- Métricas de calidad de datos con score global (77/100)
- Estadísticas de validaciones por categoría
- Análisis de tendencias y patrones de ejecución

#### Monitoreo en Tiempo Real
- Progress bar visual durante ejecución
- Logging detallado con rotación automática
- Alertas automáticas para errores críticos
- Reportes post-migración con métricas de éxito

## [Unreleased]

### Planificado para v1.1.0
- Integración con herramientas de CI/CD (GitHub Actions, GitLab CI)
- Sistema de notificaciones (Slack, email) para eventos críticos
- Dashboard web para monitoreo visual de migraciones
- Métricas avanzadas de rendimiento con Prometheus/Grafana
- Soporte para migraciones distribuidas en múltiples bases de datos

### Planificado para v1.2.0
- Auto-generación de scripts de migración desde cambios de esquema
- Integración con herramientas de versionado de esquemas
- Sistema de aprobaciones para migraciones en producción
- Análisis de impacto automático antes de migraciones
- Rollback automático basado en métricas de salud del sistema

---

## Guía de Versionado

Este proyecto sigue [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Cambios incompatibles en API o estructura de BD
- **MINOR** (0.X.0): Nueva funcionalidad compatible con versiones anteriores
- **PATCH** (0.0.X): Corrección de errores y mejoras menores

## Tipos de Cambios

- `Agregado` para nuevas funcionalidades
- `Cambiado` para cambios en funcionalidad existente
- `Obsoleto` para funcionalidad que será removida
- `Removido` para funcionalidad removida
- `Corregido` para corrección de errores
- `Seguridad` para vulnerabilidades corregidas

## Contribuciones

Para agregar nuevas migraciones:

1. Crear script en la categoría apropiada siguiendo convención `[CATEGORIA]_[NUMERO]_[DESCRIPCION].sql`
2. Crear script de rollback correspondiente en `rollbacks/`
3. Actualizar este CHANGELOG con descripción detallada
4. Testing exhaustivo en entorno de desarrollo
5. Revisión de código antes de merge

## Links Útiles

- [Documentación PostgreSQL](https://www.postgresql.org/docs/)
- [Guía de pgvector](https://github.com/pgvector/pgvector)
- [Documentación Supabase](https://supabase.com/docs)
- [Keep a Changelog](https://keepachangelog.com/)
