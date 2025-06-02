# 🗄️ Base de Datos Máquina de Noticias - Supabase

## 📖 Introducción

Esta documentación contiene todo lo necesario para entender, implementar y operar la base de datos PostgreSQL de la **Máquina de Noticias** en Supabase. El sistema está diseñado para procesar grandes volúmenes de información periodística mediante inteligencia artificial y proporcionar interfaces avanzadas de consulta.

## 🎯 ¿Qué puedo hacer aquí?

- **🏗️ Implementar** la base de datos completa en Supabase
- **🔧 Entender** la arquitectura y relaciones de datos
- **⚙️ Operar** el sistema en producción
- **🔍 Consultar** información mediante herramientas especializadas
- **📊 Monitorear** el sistema y resolver problemas

## 🗺️ Mapa de Navegación

### 🚀 **Para empezar (orden recomendado):**

1. **📋 Contexto general** → [`documentación/Explicación técnica v2.3.md`](./documentación/Explicación%20técnica%20v2.3.md)
2. **🏗️ Arquitectura de datos** → [`documentación/Arquitectura de la base de datos.sql`](./documentación/Arquitectura%20de%20la%20base%20de%20datos.sql)
3. **🚀 Implementar en Supabase** → [`migrations/MIGRATION_GUIDE.md`](./migrations/MIGRATION_GUIDE.md)

### 📚 **Por tipo de usuario:**

#### 👨‍💻 **Desarrollador Backend/Fullstack**
```
📖 EMPEZAR AQUÍ:
├── documentación/Explicación técnica v2.3.md      # Contexto del sistema
├── documentación/Query Tools Detalladas.md        # APIs de consulta
├── migrations/MIGRATION_GUIDE.md                  # Cómo implementar
└── scripts/prd.txt                               # Requerimientos completos
```

#### 🗄️ **Database Administrator (DBA)**
```
🔧 EMPEZAR AQUÍ:
├── documentación/Arquitectura de la base de datos.sql    # Esquema completo
├── documentación/Funciones-triggers.sql                 # Lógica de BD
├── documentación/Vistas materializadas.sql              # Optimizaciones
├── migrations/                                         # Sistema de migración
└── documentación/Runbooks_Operacionales.md             # Operación diaria
```

#### 🚨 **DevOps/Site Reliability Engineer**
```
⚙️ EMPEZAR AQUÍ:
├── documentación/Indice_Maestro_Documentacion_Operacional.md  # Centro de control
├── documentación/Runbooks_Operacionales.md                   # Procedimientos
├── sql-migrations/09_monitoring/                            # Sistema de monitoreo
└── migrations/config/environments.conf                       # Configuraciones
```

#### 📊 **Data Analyst/Scientist**
```
📈 EMPEZAR AQUÍ:
├── documentación/Explicación técnica v2.3.md        # Modelo de datos
├── documentación/Query Tools Detalladas.md          # Herramientas de consulta
├── documentación/Vistas materializadas.sql          # Datos precalculados
└── documentación/Criterios_de_Importancia_Guia.md   # Lógica de negocio
```

## 🎯 Casos de Uso Rápidos

### 🚀 "Quiero implementar la BD en mi Supabase"

1. **Leer contexto**: [`documentación/Explicación técnica v2.3.md`](./documentación/Explicación%20técnica%20v2.3.md)
2. **Configurar entorno**: [`migrations/config/environments.conf`](./migrations/config/environments.conf)
3. **Ejecutar migración**: [`migrations/MIGRATION_GUIDE.md`](./migrations/MIGRATION_GUIDE.md) (sección "Supabase")
4. **Verificar instalación**: [`migrations/validations/`](./migrations/validations/)

### 🔍 "Quiero consultar datos desde mi aplicación"

1. **Entender estructura**: [`documentación/Arquitectura de la base de datos.sql`](./documentación/Arquitectura%20de%20la%20base%20de%20datos.sql)
2. **APIs disponibles**: [`documentación/Query Tools Detalladas.md`](./documentación/Query%20Tools%20Detalladas.md)
3. **Funciones RPC**: [`documentación/Funciones-triggers.sql`](./documentación/Funciones-triggers.sql)

### ⚡ "Quiero optimizar el rendimiento"

1. **Vistas materializadas**: [`documentación/Vistas materializadas.sql`](./documentación/Vistas%20materializadas.sql)
2. **Índices estratégicos**: [`documentación/Arquitectura de la base de datos.sql`](./documentación/Arquitectura%20de%20la%20base%20de%20datos.sql) (sección 9)
3. **Monitoreo**: [`sql-migrations/09_monitoring/`](./sql-migrations/09_monitoring/)

### 🚨 "Tengo un problema en producción"

1. **Runbooks**: [`documentación/Runbooks_Operacionales.md`](./documentación/Runbooks_Operacionales.md)
2. **Centro de control**: [`documentación/Indice_Maestro_Documentacion_Operacional.md`](./documentación/Indice_Maestro_Documentacion_Operacional.md)
3. **Sistema de alertas**: [`sql-migrations/09_monitoring/README_alertas.md`](./sql-migrations/09_monitoring/README_alertas.md)

## 📁 Estructura de Directorios

```
📂 documentación/           # 📖 Documentos técnicos principales
├── 🏗️ Arquitectura de la base de datos.sql
├── ⚙️ Funciones-triggers.sql  
├── 📊 Vistas materializadas.sql
├── 📝 Explicación técnica v2.3.md
├── 🔍 Query Tools Detalladas.md
├── 📋 Criterios_de_Importancia_Guia.md
├── 🚨 Runbooks_Operacionales.md
└── 📇 Indice_Maestro_Documentacion_Operacional.md

📂 migrations/              # 🚀 Sistema de migración idempotente
├── 📋 MIGRATION_GUIDE.md           # Guía completa de implementación
├── 🔧 deploy.sh                   # Script principal de migración
├── ↩️ rollback.sh                 # Sistema de rollback
├── ✅ validations/                # Validaciones automáticas
├── 🗂️ 01_schema/ → 08_reference_data/  # Scripts organizados
└── ⚙️ config/                     # Configuraciones por entorno

📂 scripts/                # 🔧 Scripts auxiliares
├── 📄 prd.txt                     # Product Requirements Document
└── 🔢 embeddings/                 # Configuración de vectores

📂 sql-migrations/          # 🔍 Scripts específicos de Supabase
└── 📊 09_monitoring/              # Sistema de monitoreo avanzado
```

## ⚡ Inicio Rápido

### Para Implementación Nueva (15 minutos)

```bash
# 1. Configurar Supabase
# - Crear proyecto en supabase.com
# - Obtener credenciales de conexión

# 2. Configurar entorno local
cd migrations/
source config/environments.conf
set_environment supabase

# 3. Ejecutar migración completa
./deploy.sh --backup --verbose

# 4. Verificar instalación
./migration_utils.sh status
```

### Para Desarrollo/Testing (5 minutos)

```bash
# 1. Entorno de desarrollo
set_environment development

# 2. Dry-run (simulación)
./deploy.sh --dry-run --verbose

# 3. Testing completo
./test_migration.sh --mode full --create-test-db --cleanup
```

## 🔑 Conceptos Clave

| Concepto | Descripción | Documento de Referencia |
|----------|-------------|------------------------|
| **Memoria Profunda** | Archivos originales en Supabase Storage | [`Explicación técnica v2.3.md`](./documentación/Explicación%20técnica%20v2.3.md) |
| **Memoria Relacional** | Datos estructurados en PostgreSQL | [`Arquitectura de la base de datos.sql`](./documentación/Arquitectura%20de%20la%20base%20de%20datos.sql) |
| **Memoria Superficial** | Vistas materializadas y cachés | [`Vistas materializadas.sql`](./documentación/Vistas%20materializadas.sql) |
| **Hilos Narrativos** | Agrupaciones temáticas de información | [`Explicación técnica v2.3.md`](./documentación/Explicación%20técnica%20v2.3.md) |
| **Query Tools** | Herramientas de consulta especializadas | [`Query Tools Detalladas.md`](./documentación/Query%20Tools%20Detalladas.md) |
| **RPC Functions** | Funciones para operaciones complejas | [`Funciones-triggers.sql`](./documentación/Funciones-triggers.sql) |

## 🏷️ Tecnologías Utilizadas

- **🐘 PostgreSQL 14+** con extensiones `vector`, `pg_trgm`, `pg_cron`
- **☁️ Supabase** como plataforma de base de datos
- **🔢 pgvector** para embeddings semánticos (384 dimensiones)
- **🔍 pg_trgm** para búsquedas por similitud
- **⏰ pg_cron** para trabajos programados
- **🗂️ Particionamiento** por fecha para escalabilidad

## 📞 ¿Necesitas Ayuda?

### 🎯 Preguntas Frecuentes

| Pregunta | Documento de Respuesta |
|----------|----------------------|
| "¿Cómo funciona el sistema?" | [`documentación/Explicación técnica v2.3.md`](./documentación/Explicación%20técnica%20v2.3.md) |
| "¿Cómo implemento en Supabase?" | [`migrations/MIGRATION_GUIDE.md`](./migrations/MIGRATION_GUIDE.md) |
| "¿Qué APIs puedo usar?" | [`documentación/Query Tools Detalladas.md`](./documentación/Query%20Tools%20Detalladas.md) |
| "¿Cómo resuelvo problemas?" | [`documentación/Runbooks_Operacionales.md`](./documentación/Runbooks_Operacionales.md) |
| "¿Cómo optimizo rendimiento?" | [`documentación/Vistas materializadas.sql`](./documentación/Vistas%20materializadas.sql) |

### 🚨 En Caso de Emergencia

1. **Consultar runbooks**: [`documentación/Runbooks_Operacionales.md`](./documentación/Runbooks_Operacionales.md)
2. **Revisar monitoreo**: [`sql-migrations/09_monitoring/README.md`](./sql-migrations/09_monitoring/README.md)
3. **Ejecutar rollback**: [`migrations/rollback.sh`](./migrations/rollback.sh) (si es necesario)

---

## 📈 Estado del Proyecto

- ✅ **Arquitectura**: Completa y documentada
- ✅ **Migración**: Sistema idempotente funcional
- ✅ **Monitoreo**: Sistema avanzado implementado
- ✅ **Documentación**: Completa y actualizada
- ✅ **Testing**: Suite completa de validaciones

---

**🎯 Objetivo**: Proporcionar una base de datos robusta, escalable y bien documentada para el procesamiento inteligente de información periodística en Supabase.

**📅 Última actualización**: Mayo 2024
