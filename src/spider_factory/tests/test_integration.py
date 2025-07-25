"""
Tests de integración end-to-end
"""

import json
from pathlib import Path  # noqa: F401
from unittest.mock import AsyncMock, Mock, patch  # noqa: F401

import pytest

from src.analyzer import AnalysisStrategy, SmartAnalyzer  # noqa: F401
from src.generator import SpiderGenerator  # noqa: F401
from src.metrics import Metrics  # noqa: F401
from src.models import AnalysisRequest, GenerateSpiderRequest  # noqa: F401
from src.patterns import PatternStorage  # noqa: F401


class TestIntegration:
    """Tests de integración del sistema completo"""

    @pytest.mark.asyncio
    async def test_full_flow_rss_site(
        self, mock_analyzer, mock_generator, mock_redis_client
    ):
        """Test flujo completo para sitio con RSS"""
        # 1. Análisis inicial encuentra RSS
        mock_analyzer.firecrawl.scrape = AsyncMock(
            return_value={
                "html": """
            <html>
                <head>
                    <link rel="alternate" type="application/rss+xml" href="/feed.xml">
                </head>
                <body>
                    <h1>News Site</h1>
                </body>
            </html>
            """,
                "markdown": "# News Site",
            }
        )

        # 2. Analizar sitio
        analysis_result = await mock_analyzer.analyze_site(
            url="https://example.com", medio="Example News", seccion="Internacional"
        )

        assert analysis_result.strategy == AnalysisStrategy.RSS
        assert analysis_result.rss_url is not None

        # 3. Generar spider
        request = GenerateSpiderRequest(
            medio="Example News",
            seccion="Internacional",
            area_geografica="GLOBAL",
            tipo_medio="diario",
            analysis_result=analysis_result,
        )

        spider_code = mock_generator.generate_spider(request)

        assert "RSS Spider" in spider_code or "rss_spider" in spider_code
        assert "example_news_internacional" in spider_code

        # 4. Guardar spider
        file_path = mock_generator.save_spider(spider_code, request.spider_name)
        assert file_path.exists()

    @pytest.mark.asyncio
    async def test_full_flow_scraping_site(
        self, mock_analyzer, mock_generator, mock_pattern_storage, mock_redis_client
    ):
        """Test flujo completo para sitio de scraping"""
        # 1. No hay RSS, se hace análisis completo
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
                    "markdown": "[Article 1](/article1)",
                },
                {
                    "html": """
                <article>
                    <h1 class="title">Article 1</h1>
                    <div class="content">Content 1</div>
                </article>
                """,
                    "markdown": "# Article 1\nContent 1",
                },
            ]
        )

        # 2. Analizar sitio
        analysis_result = await mock_analyzer.analyze_site(
            url="https://newssite.com", medio="News Site", seccion="Tech"
        )

        assert analysis_result.strategy == AnalysisStrategy.SCRAPING
        assert analysis_result.selectors is not None

        # 3. Guardar patrón
        await mock_pattern_storage.save_pattern_from_analysis(
            analysis_result, "newssite.com"
        )

        # 4. Generar spider
        request = GenerateSpiderRequest(
            medio="News Site",
            seccion="Tech",
            area_geografica="USA",
            tipo_medio="revista",
            analysis_result=analysis_result,
        )

        spider_code = mock_generator.generate_spider(request)
        assert "Scraping Spider" in spider_code or "scraping_spider" in spider_code

    @pytest.mark.asyncio
    async def test_full_flow_cached_result(
        self, mock_analyzer, mock_generator, mock_redis_client
    ):
        """Test flujo con resultado cacheado"""
        # 1. Configurar resultado en cache
        cached_data = {
            "url": "https://cached.com",
            "strategy": "RSS",
            "rss_url": "https://cached.com/feed",
            "confidence": 0.98,
            "medio": "Cached News",
            "seccion": "Local",
        }

        mock_redis_client.get = AsyncMock(return_value=json.dumps(cached_data))

        # 2. Analizar (debe venir del cache)
        analysis_result = await mock_analyzer.analyze_site(
            url="https://cached.com", medio="Cached News", seccion="Local"
        )

        assert analysis_result.from_cache is True
        assert analysis_result.strategy == AnalysisStrategy.RSS

        # 3. Generar spider desde cache
        request = GenerateSpiderRequest(
            medio="Cached News",
            seccion="Local",
            area_geografica="MEXICO",
            tipo_medio="diario",
            analysis_result=analysis_result,
        )

        spider_code = mock_generator.generate_spider(request)
        assert spider_code is not None

    @pytest.mark.asyncio
    async def test_full_flow_with_pattern(
        self, mock_analyzer, mock_generator, mock_pattern_storage, mock_redis_client
    ):
        """Test flujo usando patrón existente"""
        # 1. Configurar patrón existente
        pattern_data = {
            "selectors": json.dumps(
                {"title": "h1.article-title", "content": "div.article-content"}
            ),
            "url_patterns": json.dumps(["https://patterned.com/news/*"]),
            "needs_javascript": "false",
        }

        mock_redis_client.exists = AsyncMock(return_value=True)
        mock_redis_client.hgetall = AsyncMock(return_value=pattern_data)

        # 2. Mock de validación del patrón
        mock_analyzer.firecrawl.scrape = AsyncMock(
            return_value={
                "html": '<h1 class="article-title">Test</h1><div class="article-content">Content</div>',
                "markdown": "# Test\nContent",
            }
        )

        # 3. Analizar (debe usar patrón)
        analysis_result = await mock_analyzer.analyze_site(
            url="https://patterned.com/news/test",
            medio="Patterned News",
            seccion="General",
        )

        assert analysis_result.strategy == AnalysisStrategy.PATTERN

    @pytest.mark.asyncio
    async def test_batch_processing(
        self, mock_analyzer, mock_generator, mock_batch_sites
    ):
        """Test procesamiento en batch de múltiples sitios"""
        results = []

        # Procesar cada sitio
        for site in mock_batch_sites:
            # Mock diferentes estrategias para cada sitio
            if "elpais" in site["url"]:
                mock_analyzer.firecrawl.scrape = AsyncMock(
                    return_value={
                        "html": '<link rel="alternate" type="application/rss+xml" href="/rss">',
                        "markdown": "",
                    }
                )
            else:
                mock_analyzer.firecrawl.scrape = AsyncMock(
                    return_value={
                        "html": "<h1>Article</h1><div>Content</div>",
                        "markdown": "# Article\nContent",
                    }
                )

            # Analizar
            analysis_result = await mock_analyzer.analyze_site(
                url=site["url"], medio=site["medio"], seccion=site["seccion"]
            )

            # Generar spider
            request = GenerateSpiderRequest(
                medio=site["medio"],
                seccion=site["seccion"],
                area_geografica=site["area_geografica"],
                tipo_medio=site["tipo_medio"],
                frecuencia_minutos=site.get("frecuencia_minutos", 60),
                analysis_result=analysis_result,
            )

            spider_code = mock_generator.generate_spider(request)  # noqa: F841
            results.append(
                {
                    "medio": site["medio"],
                    "seccion": site["seccion"],
                    "spider_name": request.spider_name,
                    "strategy": analysis_result.strategy.value,
                }
            )

        assert len(results) == len(mock_batch_sites)
        assert all(r["spider_name"] for r in results)

    @pytest.mark.asyncio
    async def test_metrics_tracking(
        self, mock_analyzer, mock_generator, mock_metrics, mock_redis_client
    ):
        """Test seguimiento de métricas durante el flujo"""
        # Configurar mocks para métricas
        mock_redis_client.incr = AsyncMock(return_value=1)
        mock_redis_client.lpush = AsyncMock(return_value=1)

        # 1. Análisis con tracking de tiempo
        start_time = await mock_metrics.start_timer("analysis")

        analysis_result = await mock_analyzer.analyze_site(
            url="https://metrics-test.com", medio="Metrics News", seccion="Test"
        )

        await mock_metrics.end_timer("analysis", start_time)

        # 2. Generación con tracking
        start_time = await mock_metrics.start_timer("generation")

        request = GenerateSpiderRequest(
            medio="Metrics News",
            seccion="Test",
            area_geografica="GLOBAL",
            tipo_medio="diario",
            analysis_result=analysis_result,
        )

        spider_code = mock_generator.generate_spider(request)  # noqa: F841

        await mock_metrics.end_timer("generation", start_time)

        # Verificar que se registraron métricas
        assert mock_redis_client.incr.called
        assert mock_redis_client.lpush.called

    @pytest.mark.asyncio
    async def test_error_recovery_flow(
        self, mock_analyzer, mock_generator, mock_redis_client
    ):
        """Test recuperación de errores en el flujo"""
        # 1. Primera llamada falla
        mock_analyzer.firecrawl.scrape = AsyncMock(
            side_effect=[
                Exception("Network error"),
                {  # Segunda llamada exitosa
                    "html": "<h1>Recovery Test</h1>",
                    "markdown": "# Recovery Test",
                },
            ]
        )

        # 2. Primer intento falla
        with pytest.raises(Exception):
            await mock_analyzer.analyze_site(
                url="https://error-test.com", medio="Error News", seccion="Test"
            )

        # 3. Segundo intento exitoso
        analysis_result = await mock_analyzer.analyze_site(
            url="https://error-test.com", medio="Error News", seccion="Test"
        )

        assert analysis_result is not None

    @pytest.mark.asyncio
    async def test_duplicate_check_flow(self, mock_redis_client):
        """Test verificación de duplicados"""
        # 1. Primera verificación - no existe
        mock_redis_client.exists = AsyncMock(return_value=False)

        spider_name = "test_news_local"
        exists = await mock_redis_client.exists(f"spider:{spider_name}")

        assert not exists

        # 2. Marcar como existente
        mock_redis_client.set = AsyncMock(return_value=True)
        await mock_redis_client.set(f"spider:{spider_name}", "1")

        # 3. Segunda verificación - ya existe
        mock_redis_client.exists = AsyncMock(return_value=True)
        exists = await mock_redis_client.exists(f"spider:{spider_name}")

        assert exists
