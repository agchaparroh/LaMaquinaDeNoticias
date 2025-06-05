"""
Configuración centralizada para Module Pipeline
==============================================

Este módulo re-exporta la configuración desde utils.config para mantener
compatibilidad con imports existentes.

Usar:
    from src.config import settings
    from src.config import GROQ_API_KEY, SUPABASE_URL, etc.
"""

# Re-export everything from utils.config
from .utils.config import *

# Alias para compatibilidad con FastAPI patterns
from .utils.config import get_server_config

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
