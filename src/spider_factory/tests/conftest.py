"""
Configuración y fixtures compartidas para tests
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import tempfile
import sys

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.analyzer import SmartAnalyzer, AnalysisStrategy, AnalysisResult, SiteSelectors
from src.generator import SpiderGenerator
from src.patterns import PatternStorage, Pattern
from src.metrics import Metrics
from src.redis_pool import RedisConnectionPool


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_redis_client():
    """Mock de cliente Redis para tests"""
    client = AsyncMock()
    
    # Configurar comportamientos por defecto
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock(return_value=True)
    client.exists = AsyncMock(return_value=False)
    client.hgetall = AsyncMock(return_value={})
    client.hset = AsyncMock(return_value=True)
    client.incr = AsyncMock(return_value=1)
    client.lpush = AsyncMock(return_value=1)
    client.lrange = AsyncMock(return_value=[])
    client.expire = AsyncMock(return_value=True)
    client.ping = AsyncMock(return_value=True)
    
    return client


@pytest.fixture
def mock_firecrawl_client():
    """Mock de cliente Firecrawl para tests"""
    client = AsyncMock()
    
    # Respuesta por defecto de Firecrawl
    client.scrape = AsyncMock(return_value={
        'markdown': '# Test Article\n\nTest content',
        'html': '<html><body><h1>Test Article</h1><p>Test content</p></body></html>',
        'screenshot': 'base64_screenshot_data',
        'metadata': {
            'title': 'Test Article',
            'description': 'Test description'
        }
    })
    
    return client


@pytest.fixture
def sample_analysis_result():
    """Resultado de análisis de ejemplo para tests"""
    return AnalysisResult(
        url="https://example.com/news",
        domain="example.com",
        strategy=AnalysisStrategy.SCRAPING,
        confidence=0.85,
        rss_url=None,
        selectors=SiteSelectors(
            title="h1.article-title",
            content="div.article-content",
            date="time.published",
            author="span.author"
        ),
        needs_javascript=False,
        url_patterns=["https://example.com/news/*"],
        sample_articles=[
            {
                "url": "https://example.com/news/article1",
                "title": "Test Article 1",
                "content": "Test content 1"
            }
        ],
        from_cache=False,
        medio="Example News",
        seccion="Internacional",
        area_geografica="GLOBAL",
        tipo_medio="diario",
        frecuencia_minutos=60
    )


@pytest.fixture
def mock_analyzer(mock_redis_client, mock_firecrawl_client):
    """Analyzer mockeado para tests"""
    with patch('src.analyzer.get_redis_client', return_value=mock_redis_client):
        with patch('src.analyzer.Firecrawl', return_value=mock_firecrawl_client):
            analyzer = SmartAnalyzer()
            return analyzer


@pytest.fixture
def temp_templates_dir():
    """Directorio temporal para templates de tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        templates_path = Path(tmpdir) / "templates" / "spiders"
        templates_path.mkdir(parents=True)
        
        # Crear templates básicos
        base_template = '''# -*- coding: utf-8 -*-
"""
Spider generado automáticamente por Spider Factory 2.0
{{ metadata }}
"""
class {{ spider_name }}Spider:
    name = "{{ spider_name }}"
    medio = "{{ medio }}"
    seccion = "{{ seccion }}"
'''
        
        (templates_path / "base_spider.j2").write_text(base_template)
        (templates_path / "rss_spider.j2").write_text(base_template + "\n    # RSS Spider")
        (templates_path / "scraping_spider.j2").write_text(base_template + "\n    # Scraping Spider")
        (templates_path / "playwright_spider.j2").write_text(base_template + "\n    # Playwright Spider")
        
        yield tmpdir


@pytest.fixture
def mock_generator(temp_templates_dir):
    """Generator mockeado para tests"""
    with patch('src.generator.SpiderGenerator.templates_dir', Path(temp_templates_dir) / "templates" / "spiders"):
        generator = SpiderGenerator()
        generator.output_dir = Path(temp_templates_dir) / "output"
        generator.output_dir.mkdir(exist_ok=True)
        return generator


@pytest.fixture
async def mock_pattern_storage(mock_redis_client):
    """PatternStorage mockeado para tests"""
    with patch('src.patterns.get_redis_client', return_value=mock_redis_client):
        storage = PatternStorage()
        return storage


@pytest.fixture
def sample_spider_code():
    """Código de spider de ejemplo para tests"""
    return '''# -*- coding: utf-8 -*-
"""
Spider generado automáticamente por Spider Factory 2.0
Medio: El País
Sección: Internacional
"""
import scrapy

class ElPaisInternacionalSpider(scrapy.Spider):
    name = "el_pais_internacional"
    medio = "El País"
    seccion = "Internacional"
    area_geografica = "ESPAÑA"
    tipo_medio = "diario"
    
    allowed_domains = ["elpais.com"]
    start_urls = ["https://elpais.com/internacional"]
    
    def parse(self, response):
        # Implementación del spider
        pass
'''


@pytest.fixture
def mock_batch_sites():
    """Lista de sitios para batch processing"""
    return [
        {
            "medio": "El País",
            "seccion": "Internacional",
            "url": "https://elpais.com/internacional",
            "area_geografica": "ESPAÑA",
            "tipo_medio": "diario",
            "frecuencia_minutos": 60
        },
        {
            "medio": "La Nación",
            "seccion": "Economía",
            "url": "https://lanacion.com.ar/economia",
            "area_geografica": "ARGENTINA",
            "tipo_medio": "diario",
            "frecuencia_minutos": 120
        }
    ]


@pytest.fixture
async def mock_metrics(mock_redis_client):
    """Sistema de métricas mockeado"""
    with patch('src.metrics.Metrics.redis', mock_redis_client):
        metrics = Metrics(mock_redis_client)
        return metrics


@pytest.fixture
def api_client():
    """Cliente de test para la API FastAPI"""
    from fastapi.testclient import TestClient
    from src.api import app
    
    return TestClient(app)


# Configuración de mocks globales para evitar conexiones reales
@pytest.fixture(autouse=True)
def no_real_connections(monkeypatch):
    """Previene conexiones reales a servicios externos"""
    # Mock Redis
    monkeypatch.setattr('redis.Redis', Mock)
    monkeypatch.setattr('redis.asyncio.Redis', AsyncMock)
    
    # Mock HTTP clients
    monkeypatch.setattr('httpx.AsyncClient', AsyncMock)
    monkeypatch.setattr('httpx.Client', Mock)
    
    # Mock Firecrawl
    def mock_firecrawl(*args, **kwargs):
        return Mock()
    monkeypatch.setattr('firecrawl.FirecrawlApp', mock_firecrawl)