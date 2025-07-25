"""
Spider Factory 2.0 - Sistema inteligente de generación de spiders

Este módulo proporciona un sistema automatizado para analizar sitios web
y generar spiders de Scrapy optimizados basándose en la estructura detectada.
"""

__version__ = "2.0.0"
__author__ = "La Máquina de Noticias Team"

# Importaciones del módulo de configuración
# Importaciones del analyzer
from .analyzer import (
    AnalysisConfidence,
    AnalysisResult,
    AnalysisStrategy,
    SiteAnalysisRequest,
    SiteSelectors,
    SmartAnalyzer,
)
from .config import (
    RedisConfig,
    RedisKeys,
    RedisManager,
    SpiderFactoryConfig,
    check_system_health,
    config,
    get_redis_client,
    redis_manager,
)

# Importaciones del generator
from .generator import SpiderGenerator

# Importaciones de patterns
from .patterns import Pattern, PatternMetadata, PatternStatus, PatternStorage

# Importaciones de la API (solo si se necesitan)
try:
    from .api import app  # noqa: F401
    from .models import *  # noqa: F403

    _api_available = True
except ImportError:
    _api_available = False

__all__ = [
    # Metadata
    "__version__",
    "__author__",
    # Configuración
    "RedisConfig",
    "SpiderFactoryConfig",
    "RedisManager",
    "RedisKeys",
    "config",
    "redis_manager",
    "get_redis_client",
    "check_system_health",
    # Analyzer
    "SmartAnalyzer",
    "AnalysisStrategy",
    "AnalysisConfidence",
    "SiteSelectors",
    "AnalysisResult",
    "SiteAnalysisRequest",
    # Patterns
    "PatternStorage",
    "Pattern",
    "PatternStatus",
    "PatternMetadata",
    # Generator
    "SpiderGenerator",
]

# Agregar API si está disponible
if _api_available:
    __all__.append("app")
