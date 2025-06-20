# Configuración del Módulo Scraper

## Archivos de Configuración Actualizados/Creados

### 📄 Archivos Nuevos Creados:

1. **`.gitignore`** - Control de versiones
2. **`docker-compose.yml`** - Orquestación de contenedores
3. **`config/.env`** - Variables de entorno para desarrollo
4. **`.dockerignore`** - Exclusiones optimizadas para Docker

### ⚙️ Configuración Rápida

#### 1. Configurar Variables de Entorno

```bash
# Copiar y editar el archivo de desarrollo
cd config/
cp .env .env.local
# Editar .env.local con tus credenciales reales de Supabase
```

#### 2. Desarrollo con Docker Compose

```bash
# Levantar contenedor de desarrollo
docker-compose --profile dev up -d scraper-dev

# Entrar al contenedor para desarrollo interactivo
docker-compose exec scraper-dev bash

# Dentro del contenedor, ejecutar spiders
scrapy crawl infobae

# Ejecutar tests
docker-compose --profile test up scraper-test
```

#### 3. Desarrollo Local (sin Docker)

```bash
# Instalar dependencias
pip install -r requirements.txt

# Instalar Playwright browsers
playwright install chromium --with-deps

# Configurar entorno
export $(cat config/.env | xargs)

# Ejecutar spider
scrapy crawl infobae
```

### 🔧 Comandos Docker Útiles

```bash
# Construcción y ejecución básica
docker-compose up --build scraper

# Solo ejecutar tests
docker-compose --profile test up --build scraper-test

# Desarrollo interactivo con volúmenes montados
docker-compose --profile dev up -d scraper-dev
docker-compose exec scraper-dev bash

# Ver logs
docker-compose logs -f scraper

# Limpiar
docker-compose down --volumes --remove-orphans
```

### 📋 Estructura de Archivos de Configuración

```
module_scraper/
├── .gitignore                    # ✅ Nuevo - Control de versiones
├── .dockerignore                 # ✅ Actualizado - Exclusiones Docker
├── docker-compose.yml            # ✅ Nuevo - Orquestación
├── config/
│   ├── .env                      # ✅ Nuevo - Desarrollo local
│   ├── .env.test                 # ✅ Existente - Testing
│   └── .env.test.example         # ✅ Existente - Plantilla
├── Dockerfile                    # ✅ Existente - Configuración container
├── requirements.txt              # ✅ Existente - Dependencias
└── scrapy.cfg                    # ✅ Existente - Config Scrapy
```

### 🚨 Notas Importantes

1. **NO COMMITEAR** archivos `.env` con credenciales reales
2. **USAR** `.env.test` para testing, `.env` para desarrollo
3. **LOS VOLÚMENES** Docker permiten hot-reload durante desarrollo
4. **LA CONFIGURACIÓN** es compatible con la estructura existente

### 🔐 Seguridad

- Los archivos `.env` están en `.gitignore`
- Usar variables de entorno en producción
- El `docker-compose.yml` está configurado para desarrollo, no producción
- Revisar permisos en contenedores

### 📚 Comandos de Desarrollo Comunes

```bash
# Listar spiders disponibles
docker-compose exec scraper-dev scrapy list

# Ejecutar spider específico con logs debug
docker-compose exec scraper-dev scrapy crawl infobae -L DEBUG

# Ejecutar tests completos
docker-compose --profile test up scraper-test

# Shell de Scrapy para debugging
docker-compose exec scraper-dev scrapy shell "https://ejemplo.com"

# Verificar configuración
docker-compose exec scraper-dev scrapy check
```
