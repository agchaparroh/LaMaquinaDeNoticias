"""
Configuración centralizada para Module Pipeline
==============================================

Sigue el patrón establecido en module_connector/src/config.py
Adaptado para las necesidades específicas del pipeline de procesamiento.

Variables de entorno requeridas:
- GROQ_API_KEY: API key para Groq (obligatoria)
- SUPABASE_URL: URL del proyecto Supabase (obligatoria)  
- SUPABASE_KEY: Clave anónima de Supabase (obligatoria)

Todas las demás variables tienen valores por defecto seguros.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# =============================================================================
# VALIDACIÓN DE VARIABLES CRÍTICAS
# =============================================================================

def _get_required_env(var_name: str) -> str:
    """Obtiene una variable de entorno requerida o falla con error claro."""
    value = os.getenv(var_name)
    if not value:
        print(f"❌ ERROR: Variable de entorno requerida no configurada: {var_name}")
        print(f"   Configurar en archivo .env: {var_name}=tu_valor_aqui")
        sys.exit(1)
    return value

def _get_bool_env(var_name: str, default: bool = False) -> bool:
    """Convierte variable de entorno a booleano con manejo robusto."""
    value = os.getenv(var_name, str(default)).lower()
    return value in ('true', '1', 'yes', 'on', 'enabled')

def _get_int_env(var_name: str, default: int) -> int:
    """Convierte variable de entorno a entero con manejo de errores."""
    try:
        return int(os.getenv(var_name, str(default)))
    except ValueError:
        print(f"⚠️  WARNING: Variable {var_name} no es un número válido, usando default: {default}")
        return default

def _get_float_env(var_name: str, default: float) -> float:
    """Convierte variable de entorno a float con manejo de errores."""
    try:
        return float(os.getenv(var_name, str(default)))
    except ValueError:
        print(f"⚠️  WARNING: Variable {var_name} no es un número válido, usando default: {default}")
        return default

def _get_list_env(var_name: str, default: List[str], separator: str = ',') -> List[str]:
    """Convierte variable de entorno a lista separada por comas."""
    value = os.getenv(var_name, '')
    if not value:
        return default
    return [item.strip() for item in value.split(separator) if item.strip()]

# =============================================================================
# VARIABLES CRÍTICAS (REQUERIDAS)
# =============================================================================

# API Keys obligatorias
GROQ_API_KEY = _get_required_env('GROQ_API_KEY')
SUPABASE_URL = _get_required_env('SUPABASE_URL')  
SUPABASE_KEY = _get_required_env('SUPABASE_KEY')

# Clave de servicio opcional (para operaciones avanzadas)
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

# =============================================================================
# CONFIGURACIÓN DEL SERVIDOR FASTAPI
# =============================================================================

API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = _get_int_env('API_PORT', 8000)
DEBUG_MODE = _get_bool_env('DEBUG_MODE', False)

# =============================================================================
# CONFIGURACIÓN DE PROCESAMIENTO ASÍNCRONO
# =============================================================================

WORKER_COUNT = _get_int_env('WORKER_COUNT', 3)
QUEUE_MAX_SIZE = _get_int_env('QUEUE_MAX_SIZE', 100)

# =============================================================================
# CONFIGURACIÓN DE GROQ API
# =============================================================================

MODEL_ID = os.getenv('MODEL_ID', 'llama-3.1-8b-instant')
API_TIMEOUT = _get_int_env('API_TIMEOUT', 60)
API_TEMPERATURE = _get_float_env('API_TEMPERATURE', 0.1)
API_MAX_TOKENS = _get_int_env('API_MAX_TOKENS', 4000)
MAX_RETRIES = _get_int_env('MAX_RETRIES', 2)
MAX_WAIT_SECONDS = _get_int_env('MAX_WAIT_SECONDS', 60)

# =============================================================================
# LÍMITES DE CONTENIDO
# =============================================================================

MIN_CONTENT_LENGTH = _get_int_env('MIN_CONTENT_LENGTH', 100)
MAX_CONTENT_LENGTH = _get_int_env('MAX_CONTENT_LENGTH', 50000)

# =============================================================================
# CONFIGURACIÓN DE DIRECTORIOS
# =============================================================================

# Directorios base (relativos al proyecto)
PROJECT_ROOT = Path(__file__).parent.parent.parent
PROMPTS_DIR = Path(os.getenv('PROMPTS_DIR', './prompts'))
METRICS_DIR = Path(os.getenv('METRICS_DIR', './metrics'))
LOG_DIR = Path(os.getenv('LOG_DIR', './logs'))

# Asegurar que los directorios existen
METRICS_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# =============================================================================
# CONFIGURACIÓN DE LOGGING
# =============================================================================

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
ENABLE_DETAILED_LOGGING = _get_bool_env('ENABLE_DETAILED_LOGGING', False)
ENABLE_NOTIFICATIONS = _get_bool_env('ENABLE_NOTIFICATIONS', False)

# Validar nivel de logging
VALID_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
if LOG_LEVEL not in VALID_LOG_LEVELS:
    print(f"⚠️  WARNING: LOG_LEVEL '{LOG_LEVEL}' no válido, usando 'INFO'")
    LOG_LEVEL = 'INFO'

# =============================================================================
# FLAGS OPCIONALES
# =============================================================================

USE_SPACY_FILTER = _get_bool_env('USE_SPACY_FILTER', False)
STORE_METRICS = _get_bool_env('STORE_METRICS', True)

# =============================================================================
# CONFIGURACIÓN DE JOB TRACKING
# =============================================================================

JOB_RETENTION_MINUTES = _get_int_env('JOB_RETENTION_MINUTES', 60)  # Default: 1 hora  
JOB_CLEANUP_INTERVAL_MINUTES = _get_int_env('JOB_CLEANUP_INTERVAL_MINUTES', 5)  # Default: cada 5 minutos
JOB_MAX_STORED = _get_int_env('JOB_MAX_STORED', 10000)  # Límite máximo de jobs en memoria

# =============================================================================
# CONFIGURACIÓN DE MONITOREO (OPCIONAL)
# =============================================================================

USE_SENTRY = _get_bool_env('USE_SENTRY', False)
SENTRY_DSN = os.getenv('SENTRY_DSN', '')

# Validar configuración de Sentry
if USE_SENTRY and not SENTRY_DSN:
    print("⚠️  WARNING: USE_SENTRY=true pero SENTRY_DSN no configurado. Deshabilitando Sentry.")
    USE_SENTRY = False

# =============================================================================
# CONFIGURACIÓN AVANZADA
# =============================================================================

# Modelo de importancia (Fase 4.5)
IMPORTANCE_MODEL_PATH = Path(os.getenv('IMPORTANCE_MODEL_PATH', './models/importance_model.pkl'))
IMPORTANCE_MODEL_VERSION = os.getenv('IMPORTANCE_MODEL_VERSION', '1.0')
IMPORTANCE_DEFAULT = _get_int_env('IMPORTANCE_DEFAULT', 5)

# Configuración de embeddings (si se usan)
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
EMBEDDING_DIMENSION = _get_int_env('EMBEDDING_DIMENSION', 384)

# =============================================================================
# CONFIGURACIÓN DE BASE DE DATOS AVANZADA
# =============================================================================

DB_POOL_SIZE = _get_int_env('DB_POOL_SIZE', 10)
DB_MAX_OVERFLOW = _get_int_env('DB_MAX_OVERFLOW', 20)
DB_POOL_TIMEOUT = _get_int_env('DB_POOL_TIMEOUT', 30)

# =============================================================================
# CONFIGURACIÓN DE RENDIMIENTO
# =============================================================================

LLM_BATCH_SIZE = _get_int_env('LLM_BATCH_SIZE', 1)
LLM_CONCURRENT_REQUESTS = _get_int_env('LLM_CONCURRENT_REQUESTS', 3)

# =============================================================================
# CONFIGURACIÓN DE DESARROLLO
# =============================================================================

ENABLE_DEV_ENDPOINTS = _get_bool_env('ENABLE_DEV_ENDPOINTS', False)

# =============================================================================
# CONFIGURACIÓN DE ALERTAS
# =============================================================================

# Umbrales de alertas
ALERT_ERROR_RATE_THRESHOLD = _get_float_env('ALERT_ERROR_RATE_THRESHOLD', 0.10)  # 10%
ALERT_LATENCY_THRESHOLD_SECONDS = _get_float_env('ALERT_LATENCY_THRESHOLD_SECONDS', 30.0)  # 30 segundos
ALERT_THROTTLE_MINUTES = _get_int_env('ALERT_THROTTLE_MINUTES', 1)  # 1 minuto entre alertas del mismo tipo
ALERT_RETENTION_HOURS = _get_int_env('ALERT_RETENTION_HOURS', 24)  # Retener alertas por 24 horas

# Habilitación de alertas
ENABLE_ALERTS = _get_bool_env('ENABLE_ALERTS', True)
ENABLE_ALERT_NOTIFICATIONS = _get_bool_env('ENABLE_ALERT_NOTIFICATIONS', False)

# Directorio de alertas
ALERT_CONFIG_DIR = Path(os.getenv('ALERT_CONFIG_DIR', '.alerts'))
ALERT_CONFIG_DIR.mkdir(exist_ok=True)

# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def get_groq_config() -> dict:
    """Retorna configuración para cliente Groq."""
    return {
        'api_key': GROQ_API_KEY,
        'model_id': MODEL_ID,
        'timeout': API_TIMEOUT,
        'temperature': API_TEMPERATURE,
        'max_tokens': API_MAX_TOKENS,
        'max_retries': MAX_RETRIES,
        'max_wait_seconds': MAX_WAIT_SECONDS
    }

def get_supabase_config() -> dict:
    """Retorna configuración para cliente Supabase."""
    return {
        'url': SUPABASE_URL,
        'key': SUPABASE_KEY,
        'service_role_key': SUPABASE_SERVICE_ROLE_KEY,
        'pool_size': DB_POOL_SIZE,
        'max_overflow': DB_MAX_OVERFLOW,
        'pool_timeout': DB_POOL_TIMEOUT
    }

def get_server_config() -> dict:
    """Retorna configuración para servidor FastAPI."""
    return {
        'host': API_HOST,
        'port': API_PORT,
        'debug': DEBUG_MODE,
        'workers': WORKER_COUNT,
        'queue_max_size': QUEUE_MAX_SIZE
    }

def get_logging_config() -> dict:
    """Retorna configuración para sistema de logging."""
    return {
        'level': LOG_LEVEL,
        'detailed': ENABLE_DETAILED_LOGGING,
        'notifications': ENABLE_NOTIFICATIONS,
        'log_dir': LOG_DIR,
        'use_sentry': USE_SENTRY,
        'sentry_dsn': SENTRY_DSN
    }

def get_alert_config() -> dict:
    """Retorna configuración para sistema de alertas."""
    return {
        'enabled': ENABLE_ALERTS,
        'error_rate_threshold': ALERT_ERROR_RATE_THRESHOLD,
        'latency_threshold_seconds': ALERT_LATENCY_THRESHOLD_SECONDS,
        'throttle_minutes': ALERT_THROTTLE_MINUTES,
        'retention_hours': ALERT_RETENTION_HOURS,
        'notifications_enabled': ENABLE_ALERT_NOTIFICATIONS,
        'config_dir': ALERT_CONFIG_DIR
    }

def validate_configuration() -> bool:
    """
    Valida que la configuración esté completa y sea válida.
    
    Returns:
        bool: True si la configuración es válida, False en caso contrario
    """
    errors = []
    
    # Verificar que los directorios de prompts existan
    if not PROMPTS_DIR.exists():
        errors.append(f"Directorio de prompts no existe: {PROMPTS_DIR}")
    
    # Verificar que los archivos de prompts críticos existan
    required_prompts = [
        'Prompt_1_filtrado.md',
        'Prompt_2_elementos_basicos.md', 
        'Prompt_3_citas_datos.md',
        'Prompt_4_relaciones.md'
    ]
    
    for prompt_file in required_prompts:
        prompt_path = PROMPTS_DIR / prompt_file
        if not prompt_path.exists():
            errors.append(f"Prompt requerido no encontrado: {prompt_path}")
    
    # Verificar límites de contenido
    if MIN_CONTENT_LENGTH >= MAX_CONTENT_LENGTH:
        errors.append("MIN_CONTENT_LENGTH debe ser menor que MAX_CONTENT_LENGTH")
    
    # Verificar configuración de workers
    if WORKER_COUNT <= 0:
        errors.append("WORKER_COUNT debe ser mayor que 0")
    
    if QUEUE_MAX_SIZE <= 0:
        errors.append("QUEUE_MAX_SIZE debe ser mayor que 0")
    
    # Mostrar errores si los hay
    if errors:
        print("❌ ERRORES DE CONFIGURACIÓN:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    return True

def print_configuration_summary():
    """Imprime un resumen de la configuración actual."""
    print("🔧 CONFIGURACIÓN DEL MODULE PIPELINE")
    print("=" * 50)
    print(f"Servidor FastAPI: {API_HOST}:{API_PORT} (debug: {DEBUG_MODE})")
    print(f"Workers: {WORKER_COUNT}, Cola máx: {QUEUE_MAX_SIZE}")
    print(f"Modelo LLM: {MODEL_ID}")
    print(f"Logging: {LOG_LEVEL} (detallado: {ENABLE_DETAILED_LOGGING})")
    print(f"spaCy filtro: {USE_SPACY_FILTER}")
    print(f"Sentry: {USE_SENTRY}")
    print(f"Directorios:")
    print(f"  - Prompts: {PROMPTS_DIR}")
    print(f"  - Logs: {LOG_DIR}")
    print(f"  - Métricas: {METRICS_DIR}")
    print("=" * 50)

# =============================================================================
# INICIALIZACIÓN AUTOMÁTICA
# =============================================================================

# Validar configuración al importar el módulo
if __name__ != '__main__':
    is_valid = validate_configuration()
    if not is_valid:
        print("⚠️  Configuración incompleta. Revisar variables de entorno.")
    elif ENABLE_DETAILED_LOGGING:
        print("✅ Configuración cargada correctamente")

# Modo de prueba: mostrar configuración si se ejecuta directamente
if __name__ == '__main__':
    print_configuration_summary()
    print(f"\nValidación: {'✅ VÁLIDA' if validate_configuration() else '❌ INVÁLIDA'}")
