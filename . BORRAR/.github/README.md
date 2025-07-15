# 🚀 CI/CD - La Máquina de Noticias

Este directorio contiene toda la configuración de **CI/CD (Integración Continua y Despliegue Continuo)** para el proyecto La Máquina de Noticias usando GitHub Actions.

> ⚡ **Estado**: Sistema CI/CD listo para pruebas - Configuración SSH verificada y funcional.

## 📁 Estructura

```
.github/
├── workflows/
│   ├── ci-tests.yml              # Tests automáticos en cada push/PR
│   └── deploy-production.yml     # Deploy a producción (branch main)
├── scripts/
│   ├── deploy.sh                 # Script manual de deploy
│   ├── health-check.sh           # Verificación de servicios
│   └── rollback.sh               # Script de rollback
├── dependabot.yml                # Actualizaciones automáticas de dependencias
└── README.md                     # Esta documentación
```

## 🔄 Flujos de Trabajo

### 1. **CI - Tests Automáticos** (`ci-tests.yml`)

**Trigger**: Push o PR en `main` o `develop`

**Incluye**:
- ✅ Tests de frontend (React + TypeScript) para ambos módulos
- ✅ Tests de backend (Python + pytest) para todos los servicios
- ✅ Tests de scraper (Scrapy + Playwright)
- ✅ Tests de integración con Docker Compose
- ✅ Validación de configuración y estructura

**Matriz de testing**:
- **Node.js**: 18.x, 20.x
- **Python**: 3.9, 3.10

### 2. **Deploy a Producción** (`deploy-production.yml`)

**Trigger**: Push a branch `main` o manual

**Flujo**:
1. ✋ **Aprobación manual requerida** (excepto hotfix)
2. 🧪 Tests completos (reutiliza ci-tests.yml)
3. 📦 Backup automático pre-deploy
4. 🚀 Deploy gradual (backend → frontend → infraestructura)
5. 🏥 Health checks exhaustivos
6. 🔄 Rollback automático si falla

**Estrategias**:
- **Rolling update** para minimizar downtime
- **Backup automático** antes de cada deploy
- **Rollback automático** si health checks fallan

## 🔧 Scripts Auxiliares

### `deploy.sh`
Script manual para deploy local o remoto.

```bash
# Ejemplos de uso
./deploy.sh staging
./deploy.sh production --no-backup
./deploy.sh production --rollback
```

### `lfs-manager.sh`
Manejo inteligente de archivos Git LFS.

```bash
# Ejemplos de uso
./lfs-manager.sh check              # Verificar archivos LFS
./lfs-manager.sh pull --timeout=600 # Descargar con timeout
./lfs-manager.sh status --verbose   # Estado detallado
./lfs-manager.sh cleanup --force    # Limpiar caché
```

### `health-check.sh`
Verificación completa del estado de todos los servicios.

```bash
# Ejemplos de uso
./health-check.sh staging
./health-check.sh production --detailed
./health-check.sh staging --json
```

### `rollback.sh`
Rollback a una versión anterior usando backups.

```bash
# Ejemplos de uso
./rollback.sh staging --auto
./rollback.sh production --backup-id=20231201_143022
./rollback.sh staging --list-backups
```

## 🔐 Configuración de Secretos

Para que el CI/CD funcione correctamente, debes configurar estos **GitHub Secrets**:

### Production Environment
```
PRODUCTION_SERVER_HOST=ip-servidor-produccion
PRODUCTION_SERVER_USER=deploy-user
PRODUCTION_SSH_PRIVATE_KEY=-----BEGIN OPENSSH PRIVATE KEY-----...
PRODUCTION_DOMAIN=lamaquinadenoticias.com

PRODUCTION_SUPABASE_URL=https://proyecto-prod.supabase.co
PRODUCTION_SUPABASE_ANON_KEY=eyJ...
PRODUCTION_SUPABASE_SERVICE_ROLE_KEY=eyJ...
PRODUCTION_GROQ_API_KEY=gsk_...
PRODUCTION_FIRECRAWL_API_KEY=fc-...
PRODUCTION_ANTHROPIC_API_KEY=sk-...

PROD_APPROVERS=usuario1,usuario2  # Usuarios que pueden aprobar deploys
```

## 🖥️ Configuración del Servidor

### Estructura esperada en el servidor:

```bash
# Producción
/opt/lamaquina-production/       # Código del proyecto
/opt/backups/lamaquina/          # Backups automáticos
```

### Requisitos del servidor:
- **Docker** y **Docker Compose** instalados
- **Git** configurado
- Usuario con permisos sudo para Docker
- Acceso SSH configurado con key

### Setup inicial del servidor:

```bash
# Crear directorios
sudo mkdir -p /opt/lamaquina-production
sudo mkdir -p /opt/backups/lamaquina

# Clonar repositorio
cd /opt/lamaquina-production  
git clone https://github.com/tu-usuario/LaMaquinaDeNoticias.git .
git checkout main

# Permisos
sudo chown -R deploy-user:docker /opt/lamaquina-production
sudo chown -R deploy-user:docker /opt/backups/lamaquina
```

## 📊 Monitoreo y Logs

### URLs de monitoreo:

**Producción:**
- Dashboard: https://tu-dominio.com
- API Pipeline: https://tu-dominio.com/api/pipeline/docs
- API Dashboard: https://tu-dominio.com/api/dashboard/docs

### Logs importantes:
```bash
# Ver logs de deploy
docker-compose -p lamaquina_production logs -f

# Ver logs específicos
docker-compose -p lamaquina_production logs -f module_pipeline

# Health check manual
curl http://localhost:8003/health
```

## 🔄 Dependabot

El archivo `dependabot.yml` configura actualizaciones automáticas de:

- **Python dependencies** (requirements.txt)
- **Node.js dependencies** (package.json)
- **Docker images** en Dockerfiles
- **GitHub Actions** en workflows

**Configuración**:
- Actualizaciones semanales por módulo
- PRs automáticos con etiquetas
- Agrupación de dependencias relacionadas
- Límites en número de PRs abiertas

## 📦 Manejo de Git LFS

### **Estrategia Optimizada para Archivos Pesados**

Este CI/CD está optimizado para proyectos con **Git LFS**:

#### **✅ En CI/CD (GitHub Actions)**
- **Tests**: `lfs: false` - Solo código fuente, **10x más rápido**
- **Deploy**: LFS se maneja en el servidor, no en GitHub Actions
- **Beneficio**: Menor costo, sin timeouts, proceso más confiable

#### **✅ En el Servidor**
- **Detección automática** de archivos LFS
- **Timeouts inteligentes** (3min staging, 10min producción)
- **Descarga parcial** de archivos críticos si hay problemas
- **Continuación del deploy** aunque LFS falle parcialmente

#### **🔧 Comandos LFS Útiles**
```bash
# En el servidor - verificar estado LFS
./.github/scripts/lfs-manager.sh status --verbose

# Forzar descarga de LFS
./.github/scripts/lfs-manager.sh pull --timeout=600 --force

# Limpiar caché LFS (liberar espacio)
./.github/scripts/lfs-manager.sh cleanup --force

# Solo verificar si hay archivos LFS
./.github/scripts/lfs-manager.sh check
```

#### **⚠️ Consideraciones Importantes**
- **Costos**: LFS consume ancho de banda de GitHub (se optimiza con esta configuración)
- **Timeouts**: Archivos muy grandes pueden necesitar timeouts más largos
- **Críticos vs No-críticos**: El sistema prioriza archivos con patrones críticos (*.model, *.weights, etc.)

## 🚨 Troubleshooting

### Deploy falla
1. Verificar que los secretos están configurados
2. Comprobar conectividad SSH al servidor
3. Revisar logs en GitHub Actions
4. Ejecutar health check manual

### Tests fallan
1. Verificar que las dependencias están actualizadas
2. Comprobar variables de entorno para tests
3. Revisar cambios en el código que puedan afectar tests

### Problemas con LFS
```bash
# Verificar estado de LFS en servidor
ssh deploy-user@servidor
cd /opt/lamaquina-production
./.github/scripts/lfs-manager.sh status

# Forzar descarga de archivos LFS
./.github/scripts/lfs-manager.sh pull --timeout=600 --force

# Si hay problemas de espacio
./.github/scripts/lfs-manager.sh cleanup --force
```

### Rollback necesario
```bash
# Via GitHub Actions (automático si deploy falla)
# O manual:
ssh deploy-user@servidor
cd /opt/lamaquina-production
./.github/scripts/rollback.sh production --auto
```

## 📝 Personalización

### Modificar ambientes
Editar variables en los workflows:
- `deploy-staging.yml`: Cambiar servidor de staging
- `deploy-production.yml`: Cambiar dominio y configuración

### Añadir tests
Modificar `ci-tests.yml` para incluir nuevos tipos de tests o módulos.

### Cambiar estrategia de deploy
Modificar la sección de deploy en los workflows para usar diferentes estrategias (blue-green, canary, etc.).

---

## 🎯 Próximos Pasos

1. **Configurar secretos** en GitHub repository settings
2. **Preparar servidores** con la estructura correcta
3. **Configurar SSH keys** para acceso automático
4. **Personalizar variables** según tu entorno
5. **Hacer primer push** para probar el pipeline

¡Con esta configuración tendrás un sistema de CI/CD robusto y automatizado para La Máquina de Noticias! 🚀



[![CI - Tests Automáticos](https://github.com/agchaparroh/LaMaquinaDeNoticias/actions/workflows/ci-tests.yml/badge.svg?branch=main)](https://github.com/agchaparroh/LaMaquinaDeNoticias/actions/workflows/ci-tests.yml)
