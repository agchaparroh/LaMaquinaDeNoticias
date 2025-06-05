# Module Pipeline - La Máquina de Noticias

Núcleo de procesamiento inteligente para extracción de información estructurada de artículos de noticias usando LLMs.

## 🏗️ Arquitectura

```
Pipeline de 4 Fases:
ArticuloInItem/FragmentoProcesableItem
    ↓
1️⃣ Triaje y Preprocesamiento
    ↓
2️⃣ Extracción de Elementos Básicos
    ↓
3️⃣ Extracción de Citas y Datos Cuantitativos
    ↓
4️⃣ Normalización, Vinculación y Relaciones
    ↓
Persistencia en Supabase
```

**Stack tecnológico:**
- **API**: FastAPI + Uvicorn
- **LLM**: Groq API 
- **NLP**: spaCy + sentence-transformers
- **BD**: Supabase/PostgreSQL con RPCs
- **Validación**: Pydantic v2

## 📁 Estructura del Proyecto

```
module_pipeline/
├── src/
│   ├── main.py              # FastAPI application
│   ├── controller.py        # Pipeline controller
│   ├── config.py           # Configuration wrapper
│   ├── models/             # Pydantic models
│   │   ├── entrada.py      # Input models (FragmentoProcesableItem)
│   │   ├── procesamiento.py # Processing models (HechoBase, EntidadBase, etc.)
│   │   └── persistencia.py # Persistence models (JSONB payloads)
│   ├── pipeline/           # Pipeline phases
│   │   ├── fase_1_triaje.py
│   │   ├── fase_2_extraccion.py
│   │   ├── fase_3_citas_datos.py
│   │   └── fase_4_normalizacion.py
│   ├── services/           # External integrations
│   │   ├── groq_service.py      # Groq API client
│   │   ├── supabase_service.py  # Supabase client
│   │   ├── entity_normalizer.py # Entity normalization
│   │   └── payload_builder.py   # JSONB payload builder
│   └── utils/
│       └── config.py       # Centralized configuration
├── tests/                  # Organized test suite
│   ├── conftest.py        # Test configuration
│   ├── test_api/          # API endpoint tests
│   ├── test_phases/       # Pipeline phase tests
│   ├── test_services/     # Service tests
│   └── test_utils/        # Utility tests
├── prompts/               # LLM prompts
├── docs/                  # Technical documentation
└── .taskmaster/           # Project management
```

## 🚀 Configuración de Desarrollo

### 1. Entorno
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Variables de entorno
```bash
cp .env.example .env
# Editar .env con tus claves
```

**Variables requeridas:**
```
GROQ_API_KEY=gsk_your_key_here
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=your_anon_key
```

### 3. Ejecutar
```bash
python src/main.py
```

## 🔧 Configuración

La configuración está centralizada en `src/utils/config.py` con:
- Validación automática de variables requeridas
- Valores por defecto para desarrollo
- Funciones de utilidad por componente

```python
# Acceso a configuración
from src.utils.config import GROQ_API_KEY, SUPABASE_URL
from src.utils.config import get_groq_config, get_supabase_config

# Compatible con FastAPI
from src.config import settings
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Tests específicos
pytest tests/test_services/
pytest tests/test_models/

# Con cobertura
pytest --cov=src tests/
```

**Configuración de tests:** `tests/conftest.py` incluye fixtures para mocks de Groq, Supabase y datos de prueba.

## 📡 API Endpoints

- `GET /health` - Health check
- `POST /procesar_articulo` - Procesar artículo completo
- `POST /procesar_fragmento` - Procesar fragmento de documento
- `GET /status/{job_id}` - Estado de procesamiento

## 🔀 Pipeline de Procesamiento

### Fase 1: Triaje
- Limpieza de texto
- Detección de idioma
- Evaluación de relevancia

### Fase 2: Extracción Básica  
- Hechos principales
- Entidades mencionadas

### Fase 3: Citas y Datos
- Citas textuales
- Datos cuantitativos

### Fase 4: Normalización
- Vinculación de entidades
- Relaciones entre elementos

## 🗄️ Modelos de Datos

### Entrada
- `FragmentoProcesableItem`: Fragmentos de documentos
- `ArticuloInItem`: Artículos completos (desde module_connector)

### Procesamiento
- `HechoBase/HechoProcesado`: Hechos extraídos
- `EntidadBase/EntidadProcesada`: Entidades identificadas
- `CitaTextual`: Citas directas
- `DatosCuantitativos`: Datos numéricos
- `ResultadoFaseX`: Resultados por fase

### Persistencia
- Payloads JSONB para RPCs de Supabase
- `insertar_articulo_completo()`
- `insertar_fragmento_completo()`

## 🔗 Integraciones

**Groq API:**
- Cliente con retry logic
- Manejo de timeouts y rate limits
- Prompts externos en `/prompts/`

**Supabase:**
- Cliente Singleton
- RPCs especializadas
- Normalización de entidades via `buscar_entidad_similar`

## 📝 Desarrollo

### Añadir nueva fase
1. Crear módulo en `src/pipeline/`
2. Implementar función `ejecutar_faseX()`
3. Integrar en `controller.py`
4. Añadir tests en `tests/test_phases/`

### Añadir nuevo servicio
1. Crear módulo en `src/services/`
2. Implementar cliente/wrapper
3. Configurar en `src/utils/config.py`
4. Añadir tests en `tests/test_services/`

---

**La Máquina de Noticias** - Transformando información no estructurada en conocimiento conectado.
