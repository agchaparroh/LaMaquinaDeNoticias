# 🔧 Configuración Centralizada - Module Pipeline
## La Máquina de Noticias

### 📋 **Descripción**

El módulo de configuración centralizada (`src/utils/config.py`) proporciona una gestión unificada de todas las variables de entorno y configuraciones del `module_pipeline`, siguiendo el patrón establecido en `module_connector/src/config.py`.

### 🎯 **Características Principales**

✅ **Validación automática** de variables críticas al cargar  
✅ **Valores por defecto seguros** para todas las configuraciones opcionales  
✅ **Funciones de utilidad** para obtener configuraciones por servicio  
✅ **Compatibilidad** con el patrón del ecosistema La Máquina de Noticias  
✅ **Manejo robusto de errores** con mensajes informativos  

### 🔑 **Variables Críticas (Obligatorias)**

Estas variables **DEBEN** estar configuradas o el sistema no arrancará:

```bash
# API Keys obligatorias
GROQ_API_KEY=gsk_tu_clave_groq_aqui
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_clave_anonima_supabase
```

### ⚙️ **Configuraciones Principales**

#### **Servidor FastAPI**
```bash
API_HOST=0.0.0.0              # Host del servidor (default: 0.0.0.0)
API_PORT=8000                 # Puerto del servidor (default: 8000)
DEBUG_MODE=false              # Modo debug (default: false)
```

#### **Procesamiento Asíncrono**
```bash
WORKER_COUNT=3                # Número de workers (default: 3)
QUEUE_MAX_SIZE=100           # Tamaño máximo de cola (default: 100)
```

#### **API de Groq**
```bash
MODEL_ID=llama-3.1-8b-instant        # Modelo LLM (default)
API_TIMEOUT=60                       # Timeout en segundos (default: 60)
API_TEMPERATURE=0.1                  # Temperatura del modelo (default: 0.1)
API_MAX_TOKENS=4000                  # Tokens máximos (default: 4000)
MAX_RETRIES=2                        # Reintentos máximos (default: 2)
```

#### **Logging**
```bash
LOG_LEVEL=INFO                       # Nivel de log (default: INFO)
ENABLE_DETAILED_LOGGING=false       # Logging detallado (default: false)
ENABLE_NOTIFICATIONS=false          # Notificaciones (default: false)
```

#### **Características Opcionales**
```bash
USE_SPACY_FILTER=false              # Usar filtro spaCy (default: false)
USE_SENTRY=false                    # Monitoreo Sentry (default: false)
SENTRY_DSN=                         # DSN de Sentry (si USE_SENTRY=true)
```

### 🛠️ **Uso en el Código**

#### **Importación Básica**
```python
from utils.config import (
    GROQ_API_KEY, SUPABASE_URL, API_PORT,
    get_groq_config, validate_configuration
)
```

#### **Configuraciones por Servicio**
```python
# Configuración para Groq
groq_config = get_groq_config()
# Retorna: {'api_key': '...', 'model_id': '...', 'timeout': 60, ...}

# Configuración para Supabase  
supabase_config = get_supabase_config()
# Retorna: {'url': '...', 'key': '...', 'pool_size': 10, ...}

# Configuración para servidor FastAPI
server_config = get_server_config()
# Retorna: {'host': '0.0.0.0', 'port': 8000, 'debug': False, ...}

# Configuración para logging
logging_config = get_logging_config()
# Retorna: {'level': 'INFO', 'detailed': False, 'log_dir': Path(...), ...}
```

#### **Validación de Configuración**
```python
from utils.config import validate_configuration, print_configuration_summary

# Validar configuración completa
if validate_configuration():
    print("✅ Configuración válida")
else:
    print("❌ Configuración inválida")

# Mostrar resumen de configuración
print_configuration_summary()
```

### 🧪 **Testing y Verificación**

#### **Script de Prueba Dedicado**
```bash
# Probar solo la configuración
python test_config.py
```

#### **Verificación Integrada**
```bash
# Verificación completa del entorno (incluye configuración)
python scripts/setup_env.py
```

#### **Modo de Prueba del Módulo**
```bash
# Ejecutar directamente el módulo de configuración
python -m src.utils.config
```

### 📁 **Estructura de Directorios Gestionados**

La configuración gestiona automáticamente estos directorios:

```
module_pipeline/
├── prompts/                 # PROMPTS_DIR (./prompts)
├── logs/                   # LOG_DIR (./logs) - creado automáticamente
├── metrics/                # METRICS_DIR (./metrics) - creado automáticamente  
└── models/                 # Para modelos ML futuros
```

### 🔍 **Validaciones Automáticas**

El módulo valida automáticamente:

✅ **Existencia de directorios** críticos  
✅ **Presencia de archivos de prompts** requeridos  
✅ **Configuración coherente** de límites y parámetros  
✅ **Variables críticas** configuradas correctamente  

### ⚠️ **Resolución de Problemas**

#### **Error: "Variable de entorno requerida no configurada"**
```bash
# Solución: Configurar la variable en .env
echo "GROQ_API_KEY=tu_clave_aqui" >> .env
```

#### **Error: "Directorio de prompts no existe"**
```bash
# Solución: Verificar estructura de directorios
ls -la prompts/
```

#### **Error: "Configuración centralizada inválida"**
```bash
# Solución: Ejecutar diagnóstico
python test_config.py
```

#### **Warning: "No se detectó entorno virtual"**
```bash
# Solución: Activar entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
```

### 🔗 **Integración con Otros Módulos**

#### **Compatibilidad con module_connector**
- ✅ Mismo patrón de configuración  
- ✅ Variables de entorno consistentes  
- ✅ Funciones de utilidad similares  

#### **Adaptaciones Específicas para Pipeline**
- 🔧 Variables específicas para Groq API  
- 🔧 Configuración de workers asíncronos  
- 🔧 Gestión de directorios de prompts  
- 🔧 Configuración de límites de contenido  

### 📝 **Próximos Pasos de Integración**

1. **Servicios de Integración** (Tarea 8-9):
   ```python
   # En src/services/groq_service.py
   from utils.config import get_groq_config
   
   # En src/services/supabase_service.py  
   from utils.config import get_supabase_config
   ```

2. **FastAPI Application** (Tarea 7):
   ```python
   # En src/main.py
   from utils.config import get_server_config, API_HOST, API_PORT
   ```

3. **Sistema de Logging** (Tarea 11):
   ```python
   # En src/utils/logging_config.py
   from utils.config import get_logging_config
   ```

### 🎯 **Beneficios Implementados**

✅ **Configuración unificada** - Un solo lugar para todas las variables  
✅ **Validación automática** - Errores detectados al cargar  
✅ **Valores seguros por defecto** - Sistema funcional sin configuración manual  
✅ **Compatibilidad ecosistémica** - Consistente con module_connector  
✅ **Facilidad de testing** - Scripts dedicados de verificación  
✅ **Documentación integrada** - Validaciones con mensajes informativos  

---

**La configuración centralizada establece una base sólida y consistente para todo el development del module_pipeline, garantizando compatibilidad y robustez desde el primer momento.**
