"""
Spider Factory 2.0 - Core Components
Sistema inteligente de generación de spiders para scraping de noticias
"""

from .analyzer import SmartAnalyzer
from .generator import SpiderGenerator
from .patterns import PatternStorage
from .config import settings
from .websocket_manager import ConnectionManager
from .models import (
    AnalysisRequest,
    AnalysisResponse,
    GenerateSpiderRequest,
    GenerateSpiderResponse,
    PatternSearchRequest
)

__all__ = [
    'SmartAnalyzer',
    'SpiderGenerator',
    'PatternStorage',
    'ConnectionManager',
    'settings',
    'AnalysisRequest',
    'AnalysisResponse',
    'GenerateSpiderRequest',
    'GenerateSpiderResponse',
    'PatternSearchRequest'
]

__version__ = '2.0.0'