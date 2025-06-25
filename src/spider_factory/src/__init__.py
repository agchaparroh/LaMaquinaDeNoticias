"""
Spider Factory 2.0 - Core Components
Sistema inteligente de generación de spiders para scraping de noticias
"""

from .analyzer import SmartAnalyzer
from .generator import SpiderGenerator
from .patterns import PatternStorage
from .config import ConnectionManager, settings
from .models import (
    AnalysisRequest,
    AnalysisResponse,
    GenerateRequest,
    GenerateResponse,
    PatternSearchRequest,
    SiteInfo,
    AnalysisResult
)

__all__ = [
    'SmartAnalyzer',
    'SpiderGenerator',
    'PatternStorage',
    'ConnectionManager',
    'settings',
    'AnalysisRequest',
    'AnalysisResponse',
    'GenerateRequest',
    'GenerateResponse',
    'PatternSearchRequest',
    'SiteInfo',
    'AnalysisResult'
]

__version__ = '2.0.0'