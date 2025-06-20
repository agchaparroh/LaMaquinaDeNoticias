# Configuración de pytest y fixtures compartidos
"""
Configuración global de pytest para los tests del module_scraper.
Incluye fixtures compartidos y configuraciones comunes.
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Añadir el directorio del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scrapy.http import HtmlResponse, Request, TextResponse
from scrapy.settings import Settings
from scrapy.utils.test import get_crawler

from scraper_core.items import ArticuloInItem
from scraper_core.spiders.base.base_article import BaseArticleSpider


# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================

def pytest_configure(config):
    """Configuración inicial de pytest."""
    # Marcar tests custom
    config.addinivalue_line(
        "markers", "integration: marca tests de integración"
    )
    config.addinivalue_line(
        "markers", "slow: marca tests que son lentos"
    )
    config.addinivalue_line(
        "markers", "spider: marca tests específicos de spiders"
    )


# ============================================================================
# FIXTURES DE CONFIGURACIÓN
# ============================================================================

@pytest.fixture
def mock_settings():
    """Settings de Scrapy mockeados para testing."""
    settings = Settings()
    
    # Configuración básica
    settings['BOT_NAME'] = 'test_bot'
    settings['ROBOTSTXT_OBEY'] = True
    settings['CONCURRENT_REQUESTS'] = 1
    settings['DOWNLOAD_DELAY'] = 0
    
    # Pipelines
    settings['ITEM_PIPELINES'] = {
        'scraper_core.pipelines.validation.DataValidationPipeline': 100,
        'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
        'scraper_core.pipelines.storage.SupabaseStoragePipeline': 300,
    }
    
    # Supabase mock
    settings['SUPABASE_URL'] = 'https://test.supabase.co'
    settings['SUPABASE_KEY'] = 'test-key'
    settings['SUPABASE_SERVICE_ROLE_KEY'] = 'test-service-key'
    settings['SUPABASE_HTML_BUCKET'] = 'test-bucket'
    
    # Validación
    settings['VALIDATION_MIN_CONTENT_LENGTH'] = 100
    settings['VALIDATION_MIN_TITLE_LENGTH'] = 5
    
    return settings


@pytest.fixture
def mock_crawler(mock_settings):
    """Crawler de Scrapy mockeado."""
    crawler = get_crawler(spidercls=BaseArticleSpider, settings_dict=mock_settings)
    return crawler


# ============================================================================
# FIXTURES DE RESPONSES
# ============================================================================

@pytest.fixture
def create_response():
    """Factory para crear responses HTML de prueba."""
    def _create_response(url, body, encoding='utf-8', headers=None):
        request = Request(url=url, headers=headers or {})
        return HtmlResponse(
            url=url,
            request=request,
            body=body.encode(encoding),
            encoding=encoding,
            headers=headers or {}
        )
    return _create_response


@pytest.fixture
def sample_article_html():
    """HTML de ejemplo de un artículo completo."""
    return """
    <html>
    <head>
        <title>Artículo de Prueba - Medio Test</title>
        <meta property="og:title" content="Título del Artículo de Prueba">
        <meta property="article:published_time" content="2024-01-15T10:30:00Z">
        <meta name="author" content="Autor de Prueba">
        <meta name="description" content="Descripción del artículo de prueba">
    </head>
    <body>
        <article>
            <h1 class="article-title">Título del Artículo de Prueba</h1>
            <div class="article-meta">
                <span class="author">Por Autor de Prueba</span>
                <time datetime="2024-01-15T10:30:00Z">15 de enero de 2024</time>
            </div>
            <div class="article-content">
                <p>Este es el primer párrafo del artículo de prueba con contenido suficiente para pasar validación.</p>
                <p>El segundo párrafo contiene información adicional importante y relevante al tema.</p>
                <p>Un tercer párrafo para asegurar suficiente contenido y cumplir con los requisitos mínimos.</p>
                <p>Finalmente, un cuarto párrafo que completa el artículo con más detalles.</p>
            </div>
            <div class="article-tags">
                <a href="/tag/prueba">prueba</a>
                <a href="/tag/test">test</a>
            </div>
        </article>
    </body>
    </html>
    """


@pytest.fixture
def sample_section_html():
    """HTML de ejemplo de una página de sección con listado de artículos."""
    return """
    <html>
    <head>
        <title>Sección Test - Medio de Prueba</title>
    </head>
    <body>
        <div class="section-container">
            <h1>Sección Test</h1>
            <div class="article-list">
                <article>
                    <h2><a href="/seccion-test/articulo-1">Primer artículo de la sección</a></h2>
                    <p>Resumen del primer artículo</p>
                    <time>2024-01-15</time>
                </article>
                <article>
                    <h2><a href="/seccion-test/articulo-2">Segundo artículo de la sección</a></h2>
                    <p>Resumen del segundo artículo</p>
                    <time>2024-01-14</time>
                </article>
                <article>
                    <h2><a href="/otra-seccion/articulo-3">Artículo de otra sección</a></h2>
                    <p>Este artículo no debería ser procesado</p>
                    <time>2024-01-13</time>
                </article>
            </div>
            <div class="pagination">
                <a href="/seccion-test?page=2" class="next">Siguiente</a>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_rss_feed():
    """Feed RSS de ejemplo."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
        <channel>
            <title>Feed de Prueba - Sección Test</title>
            <link>https://example.com/seccion-test</link>
            <description>Feed RSS de la sección de prueba</description>
            <language>es</language>
            <lastBuildDate>Mon, 15 Jan 2024 12:00:00 GMT</lastBuildDate>
            <item>
                <title>Primer artículo del feed RSS</title>
                <link>https://example.com/seccion-test/articulo-rss-1</link>
                <description>Descripción del primer artículo del feed</description>
                <pubDate>Mon, 15 Jan 2024 10:30:00 GMT</pubDate>
                <author>autor@example.com (Autor RSS)</author>
                <category>Tecnología</category>
                <category>Pruebas</category>
                <content:encoded><![CDATA[
                    <p>Contenido completo del artículo RSS con HTML.</p>
                    <p>Incluye varios párrafos para testing.</p>
                ]]></content:encoded>
            </item>
            <item>
                <title>Segundo artículo del feed RSS</title>
                <link>https://example.com/seccion-test/articulo-rss-2</link>
                <description>Descripción del segundo artículo</description>
                <pubDate>Sun, 14 Jan 2024 15:45:00 GMT</pubDate>
            </item>
        </channel>
    </rss>
    """


# ============================================================================
# FIXTURES DE ITEMS
# ============================================================================

@pytest.fixture
def valid_article_item():
    """ArticuloInItem válido para testing."""
    item = ArticuloInItem()
    item['url'] = 'https://example.com/test-article'
    item['titular'] = 'Título del Artículo de Prueba'
    item['medio'] = 'Medio Test'
    item['medio_url_principal'] = 'https://example.com'
    item['pais_publicacion'] = 'Argentina'
    item['tipo_medio'] = 'diario'
    item['fecha_publicacion'] = datetime(2024, 1, 15, 10, 30)
    item['contenido_texto'] = 'Este es el contenido del artículo. ' * 20  # Suficiente contenido
    item['contenido_html'] = '<p>Este es el contenido del artículo.</p>' * 20
    item['autor'] = 'Autor Test'
    item['idioma'] = 'es'
    item['seccion'] = 'test'
    item['es_opinion'] = False
    item['es_oficial'] = False
    item['fecha_recopilacion'] = datetime.utcnow()
    item['fuente'] = 'test_spider'
    return item


@pytest.fixture
def invalid_article_item():
    """ArticuloInItem inválido (falta contenido)."""
    item = ArticuloInItem()
    item['url'] = 'https://example.com/invalid'
    item['titular'] = 'Título'
    item['medio'] = 'Medio Test'
    # Falta contenido y otros campos requeridos
    return item


# ============================================================================
# FIXTURES DE SPIDERS
# ============================================================================

@pytest.fixture
def mock_spider(mock_crawler):
    """Spider base mockeado para testing."""
    spider = BaseArticleSpider.from_crawler(mock_crawler)
    spider.name = 'test_spider'
    spider.allowed_domains = ['example.com']
    spider.medio_nombre = 'Medio Test'
    spider.pais = 'Argentina'
    spider.tipo_medio = 'diario'
    spider.target_section = 'test'
    return spider


@pytest.fixture
def mock_spider_with_section_filter(mock_spider):
    """Spider con filtrado de sección implementado."""
    import re
    
    mock_spider.section_pattern = re.compile(r'/seccion-test/')
    
    def _is_section_article(url):
        return bool(mock_spider.section_pattern.search(url))
    
    mock_spider._is_section_article = _is_section_article
    return mock_spider


# ============================================================================
# FIXTURES DE MOCKS
# ============================================================================

@pytest.fixture
def mock_supabase_client():
    """Cliente de Supabase mockeado."""
    client = MagicMock()
    client.upsert_articulo = MagicMock(return_value={'id': 'test-id'})
    client.upload_to_storage = MagicMock(return_value=True)
    client.create_bucket_if_not_exists = MagicMock(return_value=True)
    return client


@pytest.fixture
def mock_logger():
    """Logger mockeado."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.debug = MagicMock()
    return logger


# ============================================================================
# FIXTURES AUXILIARES
# ============================================================================

@pytest.fixture
def temp_crawl_dir(tmp_path):
    """Directorio temporal para crawl state."""
    crawl_dir = tmp_path / '.scrapy' / 'crawl_once'
    crawl_dir.mkdir(parents=True)
    return crawl_dir


@pytest.fixture
def sample_urls():
    """URLs de ejemplo para testing."""
    return {
        'valid_section': [
            'https://example.com/seccion-test/articulo-1',
            'https://example.com/seccion-test/articulo-2',
            'https://example.com/seccion-test/subseccion/articulo-3',
        ],
        'invalid_section': [
            'https://example.com/otra-seccion/articulo',
            'https://example.com/archivo/articulo',
            'https://example.com/tag/test',
            'https://example.com/buscar?q=test',
        ],
        'excluded_patterns': [
            'https://example.com/seccion-test/archivo/old',
            'https://example.com/seccion-test/galeria/fotos',
            'https://example.com/seccion-test/video/123',
            'https://example.com/seccion-test/podcast/episodio',
        ]
    }


# ============================================================================
# HELPERS
# ============================================================================

@pytest.fixture
def assert_spider_compliance():
    """Helper para verificar conformidad de spiders."""
    def _assert_compliance(spider_class):
        # Verificar herencia
        assert issubclass(spider_class, BaseArticleSpider), \
            f"{spider_class.__name__} debe heredar de BaseArticleSpider"
        
        # Verificar atributos requeridos
        required_attrs = ['medio_nombre', 'pais', 'tipo_medio', 'target_section']
        for attr in required_attrs:
            assert hasattr(spider_class, attr), \
                f"{spider_class.__name__} debe tener atributo '{attr}'"
        
        # Verificar configuración
        assert hasattr(spider_class, 'custom_settings'), \
            f"{spider_class.__name__} debe tener custom_settings"
        
        settings = spider_class.custom_settings
        assert settings.get('DOWNLOAD_DELAY', 0) >= 2.0, \
            "DOWNLOAD_DELAY debe ser >= 2.0 segundos"
        assert settings.get('CONCURRENT_REQUESTS_PER_DOMAIN') == 1, \
            "CONCURRENT_REQUESTS_PER_DOMAIN debe ser 1"
        
        return True
    
    return _assert_compliance
