"""
Configuración centralizada para Module Pipeline
==============================================

Este módulo re-exporta la configuración desde utils.config para mantener
compatibilidad con imports existentes y añade configuración específica del pipeline.

Usar:
    from src.config import settings
    from src.config import GROQ_API_KEY, SUPABASE_URL, etc.
    from src.config import pipeline_config  # Nueva configuración del pipeline
"""

# Re-export everything from utils.config
from .utils.config import *

# Alias para compatibilidad con FastAPI patterns
from .utils.config import get_server_config

# Import pipeline-specific configuration
from .utils.config_loader import (
    get_pipeline_config,
    get_chunking_config,
    get_groq_model_config,
    get_spacy_model_config,
    get_processing_config,
    should_use_large_model,
    should_chunk_content,
    get_chunk_parallel_settings,
    get_spacy_model_name,
    get_spacy_fallback_models,
    print_pipeline_config_summary,
    SpacyModelConfig
)

# Crear objeto settings compatible con FastAPI
class Settings:
    """Wrapper de configuración compatible con FastAPI/Pydantic patterns."""
    
    def __init__(self):
        server_config = get_server_config()
        groq_config = get_groq_config()
        supabase_config = get_supabase_config()
        
        # Server config
        self.API_HOST = server_config['host']
        self.API_PORT = server_config['port'] 
        self.API_V1_STR = "/api/v1"
        self.PROJECT_NAME = "La Máquina de Noticias - Module Pipeline"
        self.PROJECT_VERSION = "0.1.0"
        
        # CORS
        self.CORS_ORIGINS = "*"
        self.CORS_ALLOW_CREDENTIALS = True
        self.CORS_ALLOW_METHODS = ["*"]
        self.CORS_ALLOW_HEADERS = ["*"]
        
        # Groq
        self.GROQ_API_KEY = groq_config['api_key']
        self.GROQ_DEFAULT_MODEL_ID = groq_config['model_id']
        
        # Supabase  
        self.SUPABASE_URL = supabase_config['url']
        self.SUPABASE_KEY = supabase_config['key']
        
        # Logging
        self.LOG_LEVEL = LOG_LEVEL
        
        # Debug mode
        self.DEBUG_MODE = True  # Default True for development
        
        # Pipeline configuration
        self.pipeline_config = get_pipeline_config()
        
        # Pipeline shortcuts for easy access
        self.chunking_config = self.pipeline_config.chunking
        self.groq_models_config = self.pipeline_config.groq_models
        self.spacy_models_config = self.pipeline_config.spacy_models
        self.processing_config = self.pipeline_config.processing

# Instancia global para compatibilidad
settings = Settings()

# Configuración de Loguru
LOGURU_CONFIG = {
    "handlers": [
        {
            "sink": "sys.stdout",
            "level": LOG_LEVEL,
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                      "<level>{level: <8}</level> | "
                      "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        }
    ]
}

# =============================================================================
# INSTANCIAS GLOBALES DE CONFIGURACIÓN DEL PIPELINE
# =============================================================================

# Configuración global del pipeline (lazy loading)
pipeline_config = get_pipeline_config()

# Configuraciones específicas para fácil acceso
chunking_config = pipeline_config.chunking
groq_models_config = pipeline_config.groq_models
spacy_models_config = pipeline_config.spacy_models
processing_config = pipeline_config.processing

# =============================================================================
# UTILIDADES DE CONFIGURACIÓN PARA EL PIPELINE
# =============================================================================

def get_model_for_content(text_length: int) -> str:
    """
    Retorna el modelo Groq apropiado basado en la longitud del contenido.
    
    Args:
        text_length: Longitud del texto en caracteres
        
    Returns:
        str: Nombre del modelo a usar
    """
    if should_use_large_model(text_length):
        return groq_models_config.large_model
    return groq_models_config.default_model

def is_chunking_needed(content_type: str, count: int, text_length: int) -> bool:
    """
    Determina si se necesita chunking para el contenido dado.
    
    Args:
        content_type: Tipo de contenido ('entities', 'quotes', 'data', 'chars')
        count: Cantidad de elementos del tipo especificado
        text_length: Longitud del texto en caracteres
        
    Returns:
        bool: True si se necesita chunking
    """
    return should_chunk_content(content_type, count, text_length)

def get_parallel_processing_config() -> dict:
    """
    Retorna configuración para procesamiento paralelo.
    
    Returns:
        dict: Configuración de paralelización
    """
    return get_chunk_parallel_settings()

def print_full_config_summary():
    """Imprime resumen completo de configuración base + pipeline."""
    from .utils.config import print_configuration_summary
    
    print("📋 CONFIGURACIÓN COMPLETA DEL MODULE PIPELINE")
    print("=" * 70)
    print()
    
    # Configuración base
    print("🔧 CONFIGURACIÓN BASE:")
    print_configuration_summary()
    print()
    
    # Configuración del pipeline
    print("🚀 CONFIGURACIÓN DEL PIPELINE:")
    print_pipeline_config_summary(pipeline_config)

# =============================================================================
# VALIDACIÓN EXTENDIDA
# =============================================================================

def validate_full_configuration() -> bool:
    """
    Valida tanto la configuración base como la del pipeline.
    
    Returns:
        bool: True si toda la configuración es válida
    """
    from .utils.config import validate_configuration
    from .utils.config_loader import validate_pipeline_config
    
    base_valid = validate_configuration()
    pipeline_valid = validate_pipeline_config(pipeline_config)
    
    return base_valid and pipeline_valid
