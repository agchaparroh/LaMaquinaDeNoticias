"""
Tests unitarios para analyzer.py
"""

import json
from datetime import datetime  # noqa: F401
from unittest.mock import AsyncMock, Mock, patch  # noqa: F401

import pytest

from src.analyzer import (  # noqa: F401
    AnalysisResult,
    AnalysisStrategy,
    SiteSelectors,
    SmartAnalyzer,
)
from src.config import settings  # noqa: F401


class TestSmartAnalyzer:
    """Tests para SmartAnalyzer"""

    @pytest.mark.asyncio
    async def test_analyze_rss_feed_detected(self, mock_analyzer, mock_redis_client):
        """Test cuando se detecta un feed RSS"""
        # Configurar mock de Firecrawl para devolver contenido RSS
        mock_analyzer.firecrawl.scrape = AsyncMock(
            return_value={
                "html": """
            <html>
                <head>
                    <link rel="alternate" type="application/rss+xml" href="https://example.com/feed.rss">
                </head>
                <body>
                    <h1>News Site</h1>
                </body>
            </html>
            """,
                "markdown": "# News Site",
            }
        )

        result = await mock_analyzer.analyze_site(
            url="https://example.com/news",
            medio="Example News",
            seccion="Internacional",
        )

        assert result.strategy == AnalysisStrategy.RSS
        assert result.rss_url == "https://example.com/feed.rss"
        assert result.confidence >= 0.95

    @pytest.mark.asyncio
    async def test_analyze_from_cache(self, mock_analyzer, mock_redis_client):
        """Test cuando el análisis viene del cache"""
        # Configurar cache para devolver un resultado guardado
        cached_result = {
            "url": "https://example.com/news",
            "domain": "example.com",
            "strategy": "SCRAPING",
            "confidence": 0.85,
            "selectors": {
                "title": "h1.article-title",
                "content": "div.article-content",
            },
            "medio": "Example News",
            "seccion": "Internacional",
        }

        mock_redis_client.get = AsyncMock(return_value=json.dumps(cached_result))

        result = await mock_analyzer.analyze_site(
            url="https://example.com/news",
            medio="Example News",
            seccion="Internacional",
        )

        assert result.from_cache is True
        assert result.strategy == AnalysisStrategy.SCRAPING
        assert result.confidence == 0.85

    @pytest.mark.asyncio
    async def test_analyze_pattern_match(self, mock_analyzer, mock_redis_client):
        """Test cuando se encuentra un patrón existente"""
        # Configurar patrón guardado
        pattern_key = "pattern:example.com"  # noqa: F841
        pattern_data = {
            "selectors": {"title": "h1.title", "content": "div.content"},
            "url_patterns": ["https://example.com/article/*"],
            "needs_javascript": False,
        }

        mock_redis_client.exists = AsyncMock(return_value=True)
        mock_redis_client.hgetall = AsyncMock(return_value=pattern_data)

        # Mock de Firecrawl
        mock_analyzer.firecrawl.scrape = AsyncMock(
            return_value={
                "html": '<h1 class="title">Test Article</h1><div class="content">Content</div>',
                "markdown": "# Test Article\nContent",
            }
        )

        result = await mock_analyzer.analyze_site(
            url="https://example.com/article/test", medio="Example News", seccion="Tech"
        )

        assert result.strategy == AnalysisStrategy.PATTERN
        assert result.confidence >= 0.9
        assert result.selectors.title == "h1.title"

    @pytest.mark.asyncio
    async def test_analyze_new_site(self, mock_analyzer, mock_redis_client):
        """Test análisis completo de sitio nuevo"""
        # Configurar para que no haya cache ni patrón
        mock_redis_client.get = AsyncMock(return_value=None)
        mock_redis_client.exists = AsyncMock(return_value=False)

        # Mock de Firecrawl con múltiples páginas
        mock_analyzer.firecrawl.scrape = AsyncMock(
            side_effect=[
                {
                    "html": """
                <html>
                    <body>
                        <a href="/article1">Article 1</a>
                        <a href="/article2">Article 2</a>
                    </body>
                </html>
                """,
                    "markdown": "[Article 1](/article1)\n[Article 2](/article2)",
                },
                {
                    "html": '<h1>Article 1</h1><div class="content">Content 1</div>',
                    "markdown": "# Article 1\nContent 1",
                },
                {
                    "html": '<h1>Article 2</h1><div class="content">Content 2</div>',
                    "markdown": "# Article 2\nContent 2",
                },
            ]
        )

        result = await mock_analyzer.analyze_site(
            url="https://example.com/news", medio="Example News", seccion="Nacional"
        )

        assert result.strategy == AnalysisStrategy.SCRAPING
        assert result.from_cache is False
        assert len(result.sample_articles) > 0

        # Verificar que se guardó en cache
        mock_redis_client.set.assert_called()

    @pytest.mark.asyncio
    async def test_analyze_error_handling(self, mock_analyzer, mock_redis_client):
        """Test manejo de errores en análisis"""
        # Configurar Firecrawl para que falle
        mock_analyzer.firecrawl.scrape = AsyncMock(
            side_effect=Exception("Connection error")
        )

        with pytest.raises(Exception) as exc_info:
            await mock_analyzer.analyze_site(
                url="https://example.com/news", medio="Example News", seccion="Deportes"
            )

        assert "Connection error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cache_ttl_setting(self, mock_analyzer, mock_redis_client):
        """Test que el TTL del cache se configure correctamente"""
        # Mock de Firecrawl
        mock_analyzer.firecrawl.scrape = AsyncMock(
            return_value={"html": "<h1>Test</h1>", "markdown": "# Test"}
        )

        result = await mock_analyzer.analyze_site(  # noqa: F841
            url="https://example.com/test", medio="Test News", seccion="Test"
        )

        # Verificar que se llamó expire con el TTL correcto (7 días)
        cache_key = f"analysis:example.com/test"  # noqa: F541
        mock_redis_client.expire.assert_called_with(cache_key, 604800)

    @pytest.mark.asyncio
    async def test_javascript_detection(self, mock_analyzer, mock_redis_client):
        """Test detección de sitios que requieren JavaScript"""
        # Mock de página con contenido dinámico
        mock_analyzer.firecrawl.scrape = AsyncMock(
            return_value={
                "html": """
            <html>
                <body>
                    <div id="app"></div>
                    <script src="/bundle.js"></script>
                </body>
            </html>
            """,
                "markdown": "",
            }
        )

        result = await mock_analyzer.analyze_site(
            url="https://example.com/spa", medio="SPA News", seccion="Tech"
        )

        assert result.needs_javascript is True

    def test_extract_rss_url(self, mock_analyzer):
        """Test extracción de URL RSS del HTML"""
        html = """
        <html>
            <head>
                <link rel="alternate" type="application/rss+xml" href="/feed.xml">
                <link rel="alternate" type="application/atom+xml" href="/atom.xml">
            </head>
        </html>
        """

        rss_url = mock_analyzer._extract_rss_url(html, "https://example.com")
        assert rss_url == "https://example.com/feed.xml"

    def test_extract_selectors(self, mock_analyzer):
        """Test extracción de selectores del HTML"""
        html = """
        <article>
            <h1 class="title">Article Title</h1>
            <time datetime="2024-01-01">January 1, 2024</time>
            <span class="author">John Doe</span>
            <div class="content">
                <p>Article content here...</p>
            </div>
        </article>
        """

        selectors = mock_analyzer._extract_selectors(html)

        assert selectors.title is not None
        assert selectors.content is not None
        assert selectors.date is not None
        assert selectors.author is not None
