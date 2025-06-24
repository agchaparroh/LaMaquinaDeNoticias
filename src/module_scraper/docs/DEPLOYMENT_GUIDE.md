# Guía de Deployment de Spiders - La Máquina de Noticias

Esta guía explica cómo preparar, desplegar y gestionar spiders en el entorno de producción usando Scrapyd.

## 📋 Índice
1. [Conceptos Básicos](#conceptos-básicos)
2. [Preparación del Spider](#preparación-del-spider)
3. [Proceso de Deployment](#proceso-de-deployment)
4. [Gestión de Versiones](#gestión-de-versiones)
5. [Deployment Automatizado](#deployment-automatizado)
6. [Mejores Prácticas](#mejores-prácticas)
7. [Rollback y Recuperación](#rollback-y-recuperación)

---

## 🎯 Conceptos Básicos

### ¿Qué es el deployment de spiders?

El deployment es el proceso de:
1. **Empaquetar** el código del spider
2. **Subir** el paquete a Scrapyd
3. **Registrar** la nueva versión
4. **Activar** el spider para ejecución

### Arquitectura de deployment

```
Desarrollo Local              Servidor Scrapyd
┌─────────────┐              ┌──────────────┐
│   Spider    │              │    Eggs      │
│   Code      │─── Deploy ──►│  Directory   │
│ (scrapy.cfg)│              │ (versiones)  │
└─────────────┘              └──────────────┘
                                    │
                                    ▼
                             ┌──────────────┐
                             │   Ejecución  │
                             │   Runtime    │
                             └──────────────┘
```

### Requisitos previos

1. **Spider funcionando localmente**
2. **Scrapyd corriendo** (puerto 6800)
3. **scrapy.cfg configurado**
4. **scrapyd-client instalado**

---

## 🔧 Preparación del Spider

### 1. Verificar spider localmente

**Antes de desplegar, SIEMPRE probar:**

```bash
# Navegar al directorio del módulo
cd /ruta/a/LaMaquinaDeNoticias/src/module_scraper

# Ejecutar spider en modo debug
scrapy crawl nombre_spider -L DEBUG

# Verificar extracción básica (solo 5 items)
scrapy crawl nombre_spider -L INFO -s CLOSESPIDER_ITEMCOUNT=5

# Verificar sin seguir robots.txt (temporal)
scrapy crawl nombre_spider -s ROBOTSTXT_OBEY=False
```

### 2. Configurar settings específicos

**En el spider (`spiders/nombre_spider.py`):**

```python
class NombreSpider(scrapy.Spider):
    name = 'nombre_spider'
    
    # Settings específicos para producción
    custom_settings = {
        'DOWNLOAD_DELAY': 2,  # Ajustar según el sitio
        'CONCURRENT_REQUESTS': 2,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
        # Spidermon específico si es necesario
        'SPIDERMON_MIN_ITEMS_SCRAPED': 20,
    }
```

### 3. Validar estructura del proyecto

```bash
# Estructura esperada:
module_scraper/
├── scrapy.cfg          # Configuración de deployment
├── scrapyd.conf        # Configuración del servidor
├── scraper_core/       # Módulo principal
│   ├── __init__.py
│   ├── settings.py
│   ├── items.py
│   ├── pipelines.py
│   ├── spiders/
│   │   ├── __init__.py
│   │   └── nombre_spider.py
│   └── monitors/       # Spidermon
└── requirements.txt
```

### 4. Verificar scrapy.cfg

```ini
# scrapy.cfg
[settings]
default = scraper_core.settings

[deploy]
url = http://localhost:6800/
project = scraper_core
```

---

## 🚀 Proceso de Deployment

### Método 1: Deployment manual (Recomendado para producción)

#### Paso 1: Construir el egg (paquete)

```bash
# Desde el directorio module_scraper
cd /ruta/a/LaMaquinaDeNoticias/src/module_scraper

# Construir egg sin desplegar
scrapyd-deploy --build-egg=scraper_core.egg
```

#### Paso 2: Verificar el egg

```bash
# Ver contenido del egg
unzip -l scraper_core.egg | head -20

# Verificar que incluye tu spider
unzip -l scraper_core.egg | grep nombre_spider
```

#### Paso 3: Desplegar a Scrapyd

```bash
# Desplegar proyecto
scrapyd-deploy default -p scraper_core

# Output esperado:
# Packing version 1642789456
# Deploying to project "scraper_core" in http://localhost:6800/addversion.json
# Server response (200):
# {"status": "ok", "project": "scraper_core", "version": "1642789456", "spiders": 3}
```

### Método 2: Deployment directo (Desarrollo)

```bash
# Un solo comando que construye y despliega
scrapyd-deploy

# Con target específico
scrapyd-deploy production -p scraper_core
```

### Verificar deployment exitoso

```bash
# 1. Listar versiones desplegadas
curl http://localhost:6800/listversions.json?project=scraper_core | python -m json.tool

# 2. Listar spiders disponibles
curl http://localhost:6800/listspiders.json?project=scraper_core | python -m json.tool

# 3. Verificar en ScrapydWeb
# Ir a http://localhost:5000 → Deploy → Ver proyecto y spiders
```

---

## 📦 Gestión de Versiones

### Sistema de versionado automático

Scrapyd usa timestamps como versiones:
- **Formato**: Unix timestamp (ej: 1642789456)
- **Ventaja**: Orden cronológico automático
- **Desventaja**: No es semántico

### Implementar versionado semántico

**En `setup.py` (crear si no existe):**

```python
from setuptools import setup, find_packages

setup(
    name='scraper_core',
    version='1.2.3',  # Versión semántica
    packages=find_packages(),
    entry_points={
        'scrapy': [
            'settings = scraper_core.settings',
        ],
    },
)
```

**Desplegar con versión específica:**

```bash
# Usar versión del setup.py
scrapyd-deploy default --version $(python setup.py --version)

# O especificar manualmente
scrapyd-deploy default --version 1.2.3
```

### Listar y gestionar versiones

```bash
# Ver todas las versiones
curl http://localhost:6800/listversions.json?project=scraper_core

# Ejecutar spider con versión específica
curl http://localhost:6800/schedule.json \
  -d project=scraper_core \
  -d spider=nombre_spider \
  -d _version=1642789456
```

### Eliminar versiones antiguas

```bash
# Eliminar versión específica
curl http://localhost:6800/delversion.json \
  -d project=scraper_core \
  -d version=1642789456
```

---

## 🤖 Deployment Automatizado

### Script de deployment con validaciones

**Crear `deploy.sh`:**

```bash
#!/bin/bash
# deploy.sh - Script de deployment seguro

set -e  # Salir si hay errores

echo "=== DEPLOYMENT DE SPIDERS ==="

# 1. Verificar ambiente
if [ "$1" != "production" ] && [ "$1" != "staging" ]; then
    echo "Uso: ./deploy.sh [production|staging]"
    exit 1
fi

ENVIRONMENT=$1
echo "Deploying to: $ENVIRONMENT"

# 2. Verificar que Scrapyd está corriendo
echo -n "Verificando Scrapyd... "
if curl -s http://localhost:6800/daemonstatus.json > /dev/null; then
    echo "OK"
else
    echo "FALLO - Scrapyd no responde"
    exit 1
fi

# 3. Ejecutar tests locales
echo "Ejecutando tests..."
python -m pytest tests/ -v || {
    echo "Tests fallaron. Abortando deployment."
    exit 1
}

# 4. Verificar spiders
echo "Verificando spiders..."
scrapy list || {
    echo "No se pueden listar spiders. Verificar configuración."
    exit 1
}

# 5. Crear backup de versión actual
CURRENT_VERSION=$(curl -s http://localhost:6800/listversions.json?project=scraper_core | \
    python -c "import sys, json; print(json.load(sys.stdin)['versions'][-1])")
echo "Versión actual: $CURRENT_VERSION"

# 6. Construir y verificar egg
echo "Construyendo paquete..."
scrapyd-deploy --build-egg=scraper_core_new.egg

# 7. Verificar tamaño del egg
EGG_SIZE=$(stat -f%z scraper_core_new.egg 2>/dev/null || stat -c%s scraper_core_new.egg)
if [ $EGG_SIZE -lt 1000 ]; then
    echo "ERROR: Egg muy pequeño ($EGG_SIZE bytes). Posible error de empaquetado."
    exit 1
fi

# 8. Deploy
echo "Desplegando..."
if [ "$ENVIRONMENT" = "production" ]; then
    scrapyd-deploy production -p scraper_core
else
    scrapyd-deploy staging -p scraper_core
fi

# 9. Verificar deployment
sleep 2
NEW_VERSION=$(curl -s http://localhost:6800/listversions.json?project=scraper_core | \
    python -c "import sys, json; print(json.load(sys.stdin)['versions'][-1])")

if [ "$NEW_VERSION" != "$CURRENT_VERSION" ]; then
    echo "✅ Deployment exitoso. Nueva versión: $NEW_VERSION"
    
    # 10. Ejecutar spider de prueba
    echo "Ejecutando spider de prueba..."
    curl http://localhost:6800/schedule.json \
        -d project=scraper_core \
        -d spider=test_spider \
        -d setting=CLOSESPIDER_ITEMCOUNT=5
else
    echo "❌ Deployment falló. Versión no cambió."
    exit 1
fi

# 11. Limpiar
rm -f scraper_core_new.egg

echo "=== DEPLOYMENT COMPLETADO ==="
```

### GitHub Actions para CI/CD

**`.github/workflows/deploy-spiders.yml`:**

```yaml
name: Deploy Spiders

on:
  push:
    branches: [main]
    paths:
      - 'src/module_scraper/**'
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r src/module_scraper/requirements.txt
        pip install scrapyd-client
    
    - name: Run tests
      run: |
        cd src/module_scraper
        python -m pytest tests/
    
    - name: Deploy to Scrapyd
      env:
        SCRAPYD_URL: ${{ secrets.SCRAPYD_URL }}
        SCRAPYD_USERNAME: ${{ secrets.SCRAPYD_USERNAME }}
        SCRAPYD_PASSWORD: ${{ secrets.SCRAPYD_PASSWORD }}
      run: |
        cd src/module_scraper
        scrapyd-deploy production \
          --username $SCRAPYD_USERNAME \
          --password $SCRAPYD_PASSWORD
```

---

## 📚 Mejores Prácticas

### 1. Pre-deployment checklist

- [ ] Spider funciona localmente
- [ ] Tests pasan
- [ ] Configuración revisada (delays, concurrencia)
- [ ] Selectores robustos (no frágiles)
- [ ] Manejo de errores implementado
- [ ] Logs informativos agregados
- [ ] Spidermon configurado

### 2. Estrategia de deployment

```
Desarrollo → Staging → Producción
    │           │           │
  Local      Testing    Live Data
```

### 3. Configuración por ambiente

```python
# settings.py
import os

ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    DOWNLOAD_DELAY = 3
    CONCURRENT_REQUESTS = 2
    LOG_LEVEL = 'WARNING'
elif ENVIRONMENT == 'staging':
    DOWNLOAD_DELAY = 2
    CONCURRENT_REQUESTS = 4
    LOG_LEVEL = 'INFO'
else:  # development
    DOWNLOAD_DELAY = 1
    CONCURRENT_REQUESTS = 8
    LOG_LEVEL = 'DEBUG'
```

### 4. Monitoreo post-deployment

```bash
# Script de monitoreo
#!/bin/bash
# monitor_deployment.sh

SPIDER=$1
echo "Monitoreando spider: $SPIDER"

# Ejecutar spider
JOB_ID=$(curl -s http://localhost:6800/schedule.json \
  -d project=scraper_core \
  -d spider=$SPIDER | \
  python -c "import sys, json; print(json.load(sys.stdin)['jobid'])")

echo "Job ID: $JOB_ID"

# Monitorear progreso
while true; do
    STATUS=$(curl -s http://localhost:6800/listjobs.json?project=scraper_core | \
        python -c "import sys, json; jobs=json.load(sys.stdin); \
        running=[j for j in jobs['running'] if j['id']=='$JOB_ID']; \
        finished=[j for j in jobs['finished'] if j['id']=='$JOB_ID']; \
        print('running' if running else ('finished' if finished else 'pending'))")
    
    if [ "$STATUS" = "finished" ]; then
        echo "Spider completado"
        break
    fi
    
    echo "Estado: $STATUS"
    sleep 10
done
```

---

## 🔄 Rollback y Recuperación

### Rollback manual

```bash
# 1. Listar versiones
curl http://localhost:6800/listversions.json?project=scraper_core

# 2. Identificar versión estable anterior
STABLE_VERSION="1642789000"

# 3. Ejecutar con versión específica
curl http://localhost:6800/schedule.json \
  -d project=scraper_core \
  -d spider=nombre_spider \
  -d _version=$STABLE_VERSION
```

### Script de rollback automático

```bash
#!/bin/bash
# rollback.sh

# Obtener penúltima versión
PREVIOUS_VERSION=$(curl -s http://localhost:6800/listversions.json?project=scraper_core | \
    python -c "import sys, json; versions=json.load(sys.stdin)['versions']; \
    print(versions[-2] if len(versions)>1 else 'none')")

if [ "$PREVIOUS_VERSION" = "none" ]; then
    echo "No hay versión anterior para rollback"
    exit 1
fi

echo "Rolling back to version: $PREVIOUS_VERSION"

# Eliminar versión actual
CURRENT_VERSION=$(curl -s http://localhost:6800/listversions.json?project=scraper_core | \
    python -c "import sys, json; print(json.load(sys.stdin)['versions'][-1])")

curl http://localhost:6800/delversion.json \
  -d project=scraper_core \
  -d version=$CURRENT_VERSION

echo "Rollback completado. Versión activa: $PREVIOUS_VERSION"
```

### Recuperación de desastres

1. **Backup de eggs:**
   ```bash
   # Backup después de cada deployment exitoso
   cp ~/.scrapyd/eggs/scraper_core/$VERSION/*.egg backups/
   ```

2. **Restaurar desde backup:**
   ```bash
   # Copiar egg al directorio de Scrapyd
   cp backups/scraper_core_stable.egg ~/.scrapyd/eggs/scraper_core/manual/
   
   # Registrar versión manualmente
   # (Requiere acceso directo al servidor Scrapyd)
   ```

---

## 🎯 Resumen de comandos

```bash
# Desarrollo
scrapy crawl spider_name                    # Ejecutar localmente
scrapyd-deploy --build-egg=test.egg        # Construir sin desplegar

# Deployment
scrapyd-deploy                              # Desplegar versión actual
scrapyd-deploy --version 1.2.3              # Desplegar versión específica

# Verificación
curl http://localhost:6800/listversions.json?project=scraper_core
curl http://localhost:6800/listspiders.json?project=scraper_core

# Ejecución
curl http://localhost:6800/schedule.json -d project=scraper_core -d spider=name

# Gestión
curl http://localhost:6800/cancel.json -d project=scraper_core -d job=ID
curl http://localhost:6800/delversion.json -d project=scraper_core -d version=VER
```

---

## 📖 Referencias

- [Documentación oficial Scrapyd](https://scrapyd.readthedocs.io)
- [scrapyd-client](https://github.com/scrapy/scrapyd-client)
- [Scrapy deployment](https://docs.scrapy.org/en/latest/topics/deploy.html)

---

✅ **Deployment exitoso** = Spider empaquetado + Subido a Scrapyd + Verificado + Monitoreado