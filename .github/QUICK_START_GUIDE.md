# 🚀 Guía Rápida - CI/CD Setup

Esta guía te llevará de 0 a un CI/CD completamente funcional en **30 minutos**.

## ⚡ **Resumen Super Rápido**

1. **Configurar Secrets en GitHub** (5 min)
2. **Preparar Servidores** (15 min) 
3. **Configurar SSH** (5 min)
4. **Primer Deploy** (5 min)

---

## 📋 **PASO 1: GitHub Secrets (5 minutos)**

### 1.1 Ir a GitHub Secrets
```
Tu Repo → Settings → Secrets and variables → Actions → New repository secret
```

### 1.2 Crear estos Secrets:

**Para Producción:**
```
PRODUCTION_SERVER_HOST = [IP de tu servidor producción]
PRODUCTION_SERVER_USER = deploy
PRODUCTION_SSH_PRIVATE_KEY = [tu SSH private key]
PRODUCTION_DOMAIN = [tu-dominio.com]
PRODUCTION_SUPABASE_URL = [tu URL de Supabase prod]
PRODUCTION_SUPABASE_ANON_KEY = [clave anónima prod]
PRODUCTION_SUPABASE_SERVICE_ROLE_KEY = [clave servicio prod]
PRODUCTION_GROQ_API_KEY = [API key Groq prod]
PRODUCTION_FIRECRAWL_API_KEY = [API key Firecrawl prod]
PRODUCTION_ANTHROPIC_API_KEY = [API key Claude]
PRODUCTION_SCRAPYDWEB_PASSWORD = [password prod]
PROD_APPROVERS = [tu-usuario-github]
```
---

## 🖥️ **PASO 2: Configurar Servidores (15 minutos)**

### 2.1 Script Automático (Recomendado)

**En tu servidor:**

```bash
# Conectar por SSH como root
ssh root@tu-servidor

# Descargar script de configuración
wget https://raw.githubusercontent.com/tu-usuario/LaMaquinaDeNoticias/main/.github/scripts/setup-server.sh
chmod +x setup-server.sh

# Ejecutar para producción
sudo ./setup-server.sh production --repo-url=https://github.com/tu-usuario/LaMaquinaDeNoticias.git
```

### 2.2 Configuración Manual (Si prefieres paso a paso)

<details>
<summary>Click para ver configuración manual</summary>

```bash
# 1. Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Instalar Git LFS
sudo apt install git-lfs -y

# 4. Crear usuario deploy
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG docker deploy

# 5. Crear directorios
sudo mkdir -p /opt/lamaquina-production
sudo mkdir -p /opt/backups/lamaquina

# 6. Dar permisos
sudo chown -R deploy:docker /opt/lamaquina-production
sudo chown -R deploy:docker /opt/backups/lamaquina

# 7. Clonar repo en producción
sudo su - deploy
cd /opt/lamaquina-production  
git clone https://github.com/tu-usuario/LaMaquinaDeNoticias.git .
git checkout main
git lfs install
```

</details>

---

## 🔑 **PASO 3: Configurar SSH (5 minutos)**

### 3.1 Generar SSH Key (en tu máquina local)

```bash
# Generar key específica para deploy
ssh-keygen -t ed25519 -f ~/.ssh/deploy_key -C "deploy@lamaquina"

# Mostrar private key (copiar COMPLETA para GitHub Secrets)
cat ~/.ssh/deploy_key

# Mostrar public key (para servidores)
cat ~/.ssh/deploy_key.pub
```

### 3.2 Instalar Public Key en Servidores

```bash
# Copiar public key a producción
ssh-copy-id -i ~/.ssh/deploy_key.pub deploy@IP-PRODUCCION
```

### 3.3 Probar Conexiones

```bash
# Probar producción
ssh -i ~/.ssh/deploy_key deploy@IP-PRODUCCION "echo 'SSH Producción OK'"
```

---

## 🚀 **PASO 4: Primer Deploy (5 minutos)**

### 4.1 Verificar Configuración

```bash
# En tu proyecto local
./.github/scripts/verify-setup.sh all
```

### 4.2 Primer Commit

```bash
# Añadir archivos CI/CD
git add .github/

# Commit
git commit -m "feat: add CI/CD configuration

- Add comprehensive GitHub Actions workflows
- Add deployment automation for production  
- Add Git LFS optimization
- Add health checks and rollback capabilities

🤖 Generated with Claude Code"

# Push a main (para producción)
git push origin main
```

### 4.3 Monitorear Deploy

1. **Ver GitHub Actions:**
   - Ve a tu repo → Actions
   - Verifica que "CI - Tests Automáticos" esté en verde
   - Verifica que "Deploy a Producción" solicite aprobación manual

2. **Aprobar Deploy:**
   - En GitHub Actions → Deploy a Producción
   - Revisar los cambios y aprobar el deploy
   - El workflow continuará automáticamente

3. **Verificar Producción:**
   ```bash
   curl https://tu-dominio.com/health
   open https://tu-dominio.com
   ```

---

## ✅ **Verificación Final**

### URLs de Verificación:

**Producción:**
- Dashboard: `https://tu-dominio.com`
- Monitoring: `https://tu-dominio.com/health`

### Comandos de Verificación:

```bash
# Health checks
curl https://tu-dominio.com/health

# Ver logs en servidor
ssh deploy@IP-SERVIDOR
cd /opt/lamaquina-production
docker-compose logs -f

# Status de servicios
docker-compose ps
```

---

## 🆘 **Troubleshooting Rápido**

### ❌ **Tests fallan**
```bash
# Verificar sintaxis
docker-compose config -q

# Verificar dependencias
npm install  # en frontends
pip install -r requirements.txt  # en backends
```

### ❌ **Deploy falla**
```bash
# Verificar secrets
echo $STAGING_SERVER_HOST  # En GitHub Actions logs

# Verificar SSH
ssh -i ~/.ssh/deploy_key deploy@IP-STAGING

# Verificar servidor
./.github/scripts/health-check.sh staging
```

### ❌ **Problemas LFS**
```bash
# En el servidor
./.github/scripts/lfs-manager.sh status
./.github/scripts/lfs-manager.sh pull --timeout=600
```

### ❌ **Servicios no inician**
```bash
# En el servidor
cd /opt/lamaquina-staging
docker-compose down
docker-compose build --no-cache
docker-compose up -d
docker-compose logs -f
```

---

## 🎉 **¡Listo!**

Con estos pasos tendrás:

- ✅ **Tests automáticos** en cada push
- ✅ **Deploy controlado a producción** desde main
- ✅ **Manejo optimizado de Git LFS**
- ✅ **Health checks y rollback automático**
- ✅ **Monitoreo completo**

**Tu CI/CD está funcionando al 100%** 🚀

### **Enlaces Útiles:**
- [Documentación Completa](.github/README.md)
- [Scripts de Utilidad](.github/scripts/)
- [Troubleshooting Avanzado](.github/README.md#troubleshooting)

**¿Problemas?** Ejecuta `./.github/scripts/verify-setup.sh` para diagnóstico completo.