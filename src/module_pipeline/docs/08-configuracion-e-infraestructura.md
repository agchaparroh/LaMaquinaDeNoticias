# 🛠️ Configuración e Infraestructura

# Especificación Técnica de Configuración e Infraestructura

## 1. Lenguajes de Programación

**Python:** Se recomienda versión 3.8 o superior, especialmente para compatibilidad con Groq SDK.

**⚠️ NOTA CRÍTICA DE COMPATIBILIDAD:**
Actualmente se requiere **NumPy 1.x** (no 2.x) debido a conflictos de compatibilidad binaria con spaCy 3.8.7 y sentence-transformers 2.9.0. Las versiones especificadas en requirements.txt han sido verificadas para compatibilidad mutua.

## 2. Frameworks y Librerías Principales

### 2.1. Framework Web y Servidor
- **FastAPI:** `0.116.2` (para la API web). Context7 ID: `/tiangolo/fastapi`
- **Uvicorn:** `0.35.1` (servidor ASGI, usar con `[standard]` para dependencias opcionales). Context7 ID: `/encode/uvicorn`

### 2.2. Integración con Servicios Externos
- **Groq Python SDK (`groq`):** `0.26.0` (interacción con la API de Groq, requiere Python 3.8+). Context7 ID: `/groq/groq-typescript`
- **Supabase Python SDK (`supabase`):** `2.15.2` (interacción con Supabase DB y Storage). Context7 ID: `/supabase/supabase-py`

### 2.3. Validación y Configuración
- **Pydantic:** `2.11.5` (validación de datos y configuración, junto con Pydantic-Settings). Context7 ID: `/pydantic/pydantic`
- **python-dotenv:** `1.1.0` (carga de variables de entorno desde archivos `.env`)

### 2.4. Logging y Utilidades
- **Loguru:** `0.7.3` (sistema de logging). Context7 ID: `/delgan/loguru`
- **json-repair:** `0.27.1` (para reparar JSON malformado proveniente de LLMs)
- **tenacity:** `9.1.2` (para reintentos robustos). Context7 ID: `/jd/tenacity`
- **python-dateutil:** `2.9.0` (parsing de fechas). Context7 ID: `/dateutil/dateutil`

### 2.5. Procesamiento de Lenguaje Natural y ML
- **spaCy:** `3.8.7` (opcional, para filtrado en Fase 1 y otras tareas NLP. Requiere descarga de modelos, ej: `python -m spacy download en_core_web_sm`). Context7 ID: `/explosion/spacy`
- **sentence-transformers:** `2.9.0` (para embeddings si se usan). Context7 ID: `/ukplab/sentence-transformers`
- **langdetect:** `1.0.9` (detección de idioma)
- **langid:** `1.1.6` (alternativa para detección de idioma). Context7 ID: `/mimino666/langdetect`
- **tiktoken:** `0.8.0` (tokenización OpenAI para segmentación)

## 3. Librerías Adicionales

### 3.1. Procesamiento Asíncrono
- `asyncio` (para procesamiento asíncrono y gestión de cola/workers)
- **tenacity:** `9.1.2` (para reintentos en llamadas a Groq)
- **nest-asyncio:** `1.6.0` (compatibilidad asyncio)
- **httpx:** `0.27.2` (cliente HTTP asíncrono). Context7 ID: `/encode/httpx`

### 3.2. Utilidades de Procesamiento
- **numpy:** `>=1.21.0,<2.0.0` (procesamiento numérico, compatible con spaCy y sentence-transformers). Context7 ID: `/numpy/numpy`
- **psycopg2-binary:** `2.9.10` (driver PostgreSQL). Context7 ID: `/psycopg/psycopg2`

### 3.3. Monitoreo (Opcional)
- **sentry-sdk:** `2.29.0` (opcional, para monitorización de errores)

## 4. Herramientas de Infraestructura

### 4.1. Contenización y Despliegue
- **Docker** (para despliegue y contenización)

### 4.2. Base de Datos
- **PostgreSQL** (base de datos subyacente)
- **pgvector** (extensión para embeddings)
- **pg_trgm** (extensión para similitud de texto)

## 5. Dependencias Externas

### 5.1. Otros Módulos del Sistema
- **`module_connector`:** Proporciona la entrada de artículos de noticias
- **`module_ingestion_engine`:** Proporciona la entrada de fragmentos de documentos y realiza la segmentación

### 5.2. Servicios Externos
- **Groq API:** Para el procesamiento LLM en Fases 1, 2, 3, 4
- **Sentry:** (opcional) Para monitorización de errores en tiempo real

### 5.3. Base de Datos
- **PostgreSQL (gestionada por Supabase):** Almacenamiento principal del sistema

## 6. Configuración Completa de Variables de Entorno

```bash
# ===================================================================
# CONFIGURACIÓN DEL MODULE_PIPELINE - ENTORNO DE PRODUCCIÓN
# ===================================================================
# Este archivo contiene todas las variables de entorno necesarias para
# el funcionamiento del module_pipeline en un entorno de producción.

# === CONFIGURACIÓN DEL SERVIDOR FASTAPI ===
API_HOST=0.0.0.0
API_PORT=8000
DEBUG_MODE=false

# === CONFIGURACIÓN DE PROCESAMIENTO ASÍNCRONO ===
WORKER_COUNT=3
QUEUE_MAX_SIZE=100

# === CONFIGURACIÓN DE GROQ API ===
# REQUERIDO: Obtener API key de https://console.groq.com/
GROQ_API_KEY=gsk_your_groq_api_key_here
MODEL_ID=llama-3.1-8b-instant
API_TIMEOUT=30
API_TEMPERATURE=0.1
API_MAX_TOKENS=4000
MAX_RETRIES=3
MAX_WAIT_SECONDS=60

# === CONFIGURACIÓN DE SUPABASE ===
# REQUERIDO: URL y claves de tu proyecto Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your_service_role_key_here

# === LÍMITES DE CONTENIDO ===
MIN_CONTENT_LENGTH=100
MAX_CONTENT_LENGTH=50000

# === CONFIGURACIÓN DE DIRECTORIOS ===
PROMPTS_DIR=./prompts
METRICS_DIR=./metrics
LOG_DIR=./logs

# === CONFIGURACIÓN DE LOGGING ===
LOG_LEVEL=INFO
ENABLE_NOTIFICATIONS=false

# === FLAGS OPCIONALES ===
# spaCy para filtrado adicional en Fase 1 (requiere modelo descargado)
USE_SPACY_FILTER=false

# Almacenamiento de métricas en base de datos
STORE_METRICS=true

# === CONFIGURACIÓN DE MONITOREO (OPCIONAL) ===
# Sentry para tracking de errores
USE_SENTRY=false
SENTRY_DSN=https://your-sentry-dsn-here@sentry.io/project

# === CONFIGURACIÓN AVANZADA ===
# Configuración específica para el modelo de importancia (Fase 4.5)
IMPORTANCE_MODEL_PATH=./models/importance_model.pkl
IMPORTANCE_MODEL_VERSION=1.0

# Configuración de embeddings (si se usan)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# === CONFIGURACIÓN DE BASE DE DATOS AVANZADA ===
# Pool de conexiones de Supabase
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30

# === CONFIGURACIÓN DE RENDIMIENTO ===
# Configuración específica del LLM para optimización
LLM_BATCH_SIZE=1
LLM_CONCURRENT_REQUESTS=3

# === CONFIGURACIÓN DE DESARROLLO ===
# Solo para debugging - NO usar en producción
ENABLE_DEV_ENDPOINTS=false
ENABLE_DETAILED_LOGGING=false
```

## 7. Archivos de Configuración Requeridos

### 7.1. Configuración de Entorno
- **`.env`:** Para cargar variables de entorno en desarrollo
- **`.env.example`:** Plantilla de configuración con valores de ejemplo

### 7.2. Prompts del LLM
Archivos de texto en `PROMPTS_DIR` conteniendo las plantillas de los prompts para el LLM:
- `Prompt_1_ filtrado.md`
- `Prompt_2_elementos_basicos.md`
- `Prompt_3_citas_datos.md`
- `Prompt_4_relaciones.md`

## 8. Requisitos del Sistema

### 8.1. Modelos de Procesamiento de Lenguaje Natural
- **Modelo spaCy:** `es_core_news_lg` descargado si `USE_SPACY_FILTER` es True
- **Comando de instalación:** `python -m spacy download es_core_news_lg`

### 8.2. Conectividad de Red
- **Acceso a internet:** Para conexión con API de Groq y Supabase
- **Puertos requeridos:** Puerto configurado en `API_PORT` (default: 8000)

### 8.3. Permisos del Sistema
- **Directorio de logs:** `/var/log/maquina_noticias` con permisos de escritura
- **Archivos de configuración:** Permisos de lectura para archivos `.env` y prompts
- **Modelos ML:** Permisos de lectura para archivos de modelos en `./models/`

### 8.4. Base de Datos
- **Esquema configurado:** Base de datos con el esquema correcto implementado
- **Funciones RPC:** Funciones implementadas:
  - `insertar_articulo_completo`
  - `insertar_fragmento_completo`
  - `buscar_entidad_similar`
  - `buscar_posibles_duplicados_lote`

## 9. Dependencias Python (requirements.txt)

**IMPORTANTE:** NumPy 2.x causa conflictos de compatibilidad binaria con spaCy 3.8.7 y sentence-transformers 2.9.0. Se requiere NumPy 1.x hasta que haya soporte oficial.

```
# === FRAMEWORKS WEB ===
fastapi==0.116.2
uvicorn[standard]==0.35.1

# === IA/ML ===
groq==0.26.0
spacy==3.8.7
sentence-transformers==2.9.0
langid==1.1.6

# === BASE DE DATOS ===
supabase==2.15.2
psycopg2-binary==2.9.10

# === VALIDACIÓN Y CONFIGURACIÓN ===
pydantic==2.11.5
python-dotenv==1.1.0

# === HTTP CLIENTS ===
httpx==0.27.2

# === UTILIDADES ===
tenacity==9.1.2
loguru==0.7.3
python-dateutil==2.9.0

# === PROCESAMIENTO ===
numpy>=1.21.0,<2.0.0

# === TESTING ===
pytest==8.4.0
pytest-mock==3.14.1
pytest-asyncio==0.24.0

# === INFRAESTRUCTURA ===
nest-asyncio==1.6.0

# === DEPENDENCIAS ADICIONALES ===
json-repair==0.27.1
langdetect==1.0.9
tiktoken==0.8.0
sentry-sdk==2.29.0
```

## 10. Configuración del Servidor

### 10.1. Inicialización con Uvicorn
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=DEBUG_MODE,
        access_log=True,
        log_level="info"
    )
```

### 10.2. Configuración de Producción
```python
# Configuración recomendada para producción
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=8000,
    workers=1,  # FastAPI maneja concurrencia internamente
    reload=False,
    access_log=True,
    log_level="warning"
)
```

## 11. Estructura de Directorios

```
module_pipeline/
├── prompts/                    # Archivos de prompts externos
│   ├── Prompt_1_ filtrado.md
│   ├── Prompt_2_elementos_basicos.md
│   ├── Prompt_3_citas_datos.md
│   └── Prompt_4_relaciones.md
├── logs/                       # Directorio de logs
│   ├── pipeline.log
│   ├── errors/
│   └── api/
├── metrics/                    # Métricas del sistema
├── models/                     # Modelos ML (si se usan)
│   └── importance_model.pkl
├── src/                        # Código fuente
│   ├── main.py
│   ├── controller.py
│   ├── phases/
│   └── utils/
├── tests/                      # Tests unitarios
├── docker/                     # Configuración Docker
├── .env                        # Variables de entorno
├── .env.example               # Plantilla de configuración
├── requirements.txt           # Dependencias Python
└── README.md                  # Documentación
```

## 12. Proceso de Instalación y Setup

### 12.1. Instalación de Dependencias
```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias (verificadas para compatibilidad)
pip install -r requirements.txt
```

**⚠️ IMPORTANTE:** Si tienes NumPy 2.x instalado previamente, deberás desinstalarlo primero:
```bash
pip uninstall numpy
pip install -r requirements.txt
```

### 12.2. Configuración de spaCy (Opcional)
```bash
# Solo si USE_SPACY_FILTER=true
python -m spacy download en_core_web_sm
python -m spacy download es_core_news_lg
```

### 12.3. Configuración de Variables de Entorno
```bash
# Copiar plantilla de configuración
cp .env.example .env

# Editar .env con las configuraciones específicas del entorno
nano .env
```

### 12.4. Verificación de Conectividad
```bash
# Verificar conexión a Groq
curl -H "Authorization: Bearer $GROQ_API_KEY" https://api.groq.com/openai/v1/models

# Verificar conexión a Supabase
curl -H "apikey: $SUPABASE_KEY" "$SUPABASE_URL/rest/v1/"
```

## 13. Consideraciones de Rendimiento

### 13.1. Optimizaciones Recomendadas
- **Conexiones persistentes:** Reutilización de conexiones HTTP para APIs externas
- **Pool de conexiones de BD:** Configuración optimizada para múltiples workers
- **Caché de prompts:** Carga única de prompts al inicializar el sistema
- **Lazy loading:** Carga diferida de modelos ML hasta su primer uso

### 13.2. Configuración de Recursos
```bash
# Configuración de memoria para modelos grandes
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
```

## 14. Notas Adicionales

### 14.1. Arquitectura Modular
- El pipeline está diseñado para ser modular, permitiendo la modificación o reemplazo de fases individuales
- La calidad de la extracción depende significativamente de la calidad de los prompts y de la capacidad del modelo LLM (`llama-3.1-8b-instant`)

### 14.2. Integraciones Críticas
- **Fase 4:** Crucial para la integración con los datos existentes en la base de datos
- **Fase 5:** Garantiza la atomicidad de la inserción de datos complejos mediante el uso de RPCs

### 14.3. Escalabilidad
- **Escalamiento horizontal:** Posibilidad de ejecutar múltiples instancias del pipeline
- **Load balancing:** Distribución de carga entre instancias múltiples
- **Monitoreo:** Herramientas de observabilidad para producción
