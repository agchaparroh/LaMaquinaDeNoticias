# Test Universal para Spiders - La Máquina de Noticias
"""
Test universal que verifica que cualquier spider cumpla con las pautas
establecidas por el generador de spiders (@generador-spiders).

Este test asegura que todos los spiders:
1. Heredan correctamente de BaseArticleSpider
2. Implementan todos los campos requeridos de ArticuloInItem
3. Usan los pipelines correctos del proyecto
4. Tienen configuración adecuada para comportamiento tipo RSS
5. Implementan filtrado por sección cuando aplica
6. Manejan errores apropiadamente
"""

import pytest
import inspect
import re
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from typing import Type, List, Dict, Any

from scrapy import Spider
from scrapy.http import Response, Request, TextResponse
from scrapy.utils.test import get_crawler
from scrapy.settings import Settings
from itemadapter import ItemAdapter

from scraper_core.items import ArticuloInItem
from scraper_core.spiders.base.base_article import BaseArticleSpider


class SpiderTestCase:
    """Clase base para configurar casos de prueba de spiders."""
    
    def __init__(self, spider_class: Type[Spider], test_data: Dict[str, Any] = None):
        self.spider_class = spider_class
        self.test_data = test_data or self._get_default_test_data()
    
    def _get_default_test_data(self) -> Dict[str, Any]:
        """Datos de prueba por defecto basados en el tipo de spider."""
        spider_name = self.spider_class.name
        
        # Detectar tipo de spider por el nombre
        if 'rss' in spider_name:
            return {
                'spider_type': 'rss',
                'sample_feed': self._get_sample_rss_feed(),
                'sample_article_html': self._get_sample_article_html(),
                'expected_items': 2
            }
        elif 'playwright' in spider_name:
            return {
                'spider_type': 'playwright',
                'sample_section_html': self._get_sample_section_html(),
                'sample_article_html': self._get_sample_article_html(),
                'expected_items': 2
            }
        else:
            return {
                'spider_type': 'scraping',
                'sample_section_html': self._get_sample_section_html(),
                'sample_article_html': self._get_sample_article_html(),
                'expected_items': 2
            }
    
    def _get_sample_rss_feed(self) -> str:
        """Feed RSS de ejemplo para testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <link>https://example.com</link>
                <item>
                    <title>Artículo de prueba 1</title>
                    <link>https://example.com/seccion/articulo-1</link>
                    <description>Descripción del artículo 1</description>
                    <pubDate>Wed, 15 Jan 2024 10:30:00 GMT</pubDate>
                    <author>Autor Test</author>
                </item>
                <item>
                    <title>Artículo de prueba 2</title>
                    <link>https://example.com/seccion/articulo-2</link>
                    <description>Descripción del artículo 2</description>
                    <pubDate>Wed, 15 Jan 2024 11:30:00 GMT</pubDate>
                </item>
            </channel>
        </rss>
        """
    
    def _get_sample_section_html(self) -> str:
        """HTML de ejemplo de una página de sección."""
        return """
        <html>
        <head><title>Sección Test</title></head>
        <body>
            <div class="section-container">
                <article>
                    <h2><a href="/seccion/articulo-1">Artículo de prueba 1</a></h2>
                    <p>Resumen del artículo 1</p>
                </article>
                <article>
                    <h2><a href="/seccion/articulo-2">Artículo de prueba 2</a></h2>
                    <p>Resumen del artículo 2</p>
                </article>
                <article>
                    <h2><a href="/otra-seccion/articulo-3">Artículo de otra sección</a></h2>
                    <p>Este no debería ser procesado</p>
                </article>
            </div>
        </body>
        </html>
        """
    
    def _get_sample_article_html(self) -> str:
        """HTML de ejemplo de un artículo completo."""
        return """
        <html>
        <head>
            <title>Artículo de prueba - Medio Test</title>
            <meta property="article:published_time" content="2024-01-15T10:30:00Z">
        </head>
        <body>
            <article>
                <h1 class="article-title">Título del artículo de prueba</h1>
                <div class="article-meta">
                    <span class="author">Por Autor Test</span>
                    <time datetime="2024-01-15T10:30:00Z">15 de enero de 2024</time>
                </div>
                <div class="article-content">
                    <p>Este es el primer párrafo del artículo de prueba con contenido suficiente para pasar la validación.</p>
                    <p>Este es el segundo párrafo con más contenido relevante y detalles importantes sobre el tema.</p>
                    <p>Y un tercer párrafo para asegurar que tenemos suficiente contenido textual.</p>
                </div>
                <div class="article-tags">
                    <a href="/tag/prueba">prueba</a>
                    <a href="/tag/test">test</a>
                </div>
            </article>
        </body>
        </html>
        """


class TestUniversalSpider:
    """Test universal para verificar que los spiders cumplen las pautas del generador."""
    
    # Lista de spiders a excluir del testing universal (ej: spiders de prueba)
    EXCLUDED_SPIDERS = ['crawl_once_test', 'useragent_test', 'rate_limit_test']
    
    # Campos requeridos según ArticuloInItem y el generador
    REQUIRED_FIELDS = [
        'url', 'fuente', 'titular', 'contenido_texto', 'contenido_html',
        'medio', 'medio_url_principal', 'pais_publicacion', 'tipo_medio',
        'fecha_publicacion', 'autor', 'idioma', 'seccion',
        'es_opinion', 'es_oficial', 'fecha_recopilacion'
    ]
    
    # Pipelines requeridos
    REQUIRED_PIPELINES = [
        'DataValidationPipeline',
        'DataCleaningPipeline',
        'SupabaseStoragePipeline'
    ]
    
    # Configuraciones requeridas para comportamiento tipo RSS
    REQUIRED_SETTINGS = {
        'DOWNLOAD_DELAY': lambda x: x >= 2.0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': lambda x: x == 1,
        'CLOSESPIDER_ITEMCOUNT': lambda x: 1 <= x <= 100,
        'CLOSESPIDER_TIMEOUT': lambda x: x > 0,
    }
    
    @pytest.fixture
    def mock_settings(self):
        """Configuración mock para los tests."""
        settings = Settings()
        settings.setmodule('scraper_core.settings')
        
        # Configurar pipelines requeridos
        settings['ITEM_PIPELINES'] = {
            'scraper_core.pipelines.validation.DataValidationPipeline': 100,
            'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
            'scraper_core.pipelines.storage.SupabaseStoragePipeline': 300,
        }
        
        # Configuración de Supabase
        settings['SUPABASE_URL'] = 'https://test.supabase.co'
        settings['SUPABASE_KEY'] = 'test-key'
        settings['SUPABASE_SERVICE_ROLE_KEY'] = 'test-service-key'
        
        return settings
    
    def get_all_spiders(self) -> List[Type[Spider]]:
        """Obtener todas las clases de spider del proyecto."""
        from scraper_core import spiders
        import pkgutil
        import importlib
        
        spider_classes = []
        
        # Recorrer todos los módulos en el paquete spiders
        for importer, modname, ispkg in pkgutil.walk_packages(
            path=spiders.__path__,
            prefix=spiders.__name__ + '.',
            onerror=lambda x: None
        ):
            if ispkg:
                continue
                
            try:
                module = importlib.import_module(modname)
                
                # Buscar clases que heredan de Spider
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, Spider) and 
                        obj is not Spider and 
                        obj is not BaseArticleSpider and
                        hasattr(obj, 'name') and
                        obj.name not in self.EXCLUDED_SPIDERS):
                        spider_classes.append(obj)
                        
            except Exception as e:
                print(f"Error importando {modname}: {e}")
        
        return spider_classes
    
    def test_spider_inheritance(self):
        """Verificar que todos los spiders heredan de BaseArticleSpider."""
        spiders = self.get_all_spiders()
        assert len(spiders) > 0, "No se encontraron spiders para testear"
        
        for spider_class in spiders:
            assert issubclass(spider_class, BaseArticleSpider), \
                f"{spider_class.name} debe heredar de BaseArticleSpider"
    
    def test_spider_required_attributes(self):
        """Verificar que los spiders tienen los atributos requeridos."""
        spiders = self.get_all_spiders()
        
        required_attrs = [
            'name', 'allowed_domains', 'medio_nombre', 
            'pais', 'tipo_medio', 'target_section'
        ]
        
        for spider_class in spiders:
            for attr in required_attrs:
                assert hasattr(spider_class, attr), \
                    f"{spider_class.name} debe tener el atributo '{attr}'"
                
                # Verificar que no son None o vacíos
                value = getattr(spider_class, attr)
                assert value is not None and value != '', \
                    f"{spider_class.name}.{attr} no puede ser None o vacío"
    
    def test_spider_custom_settings(self):
        """Verificar que los spiders tienen la configuración requerida."""
        spiders = self.get_all_spiders()
        
        for spider_class in spiders:
            assert hasattr(spider_class, 'custom_settings'), \
                f"{spider_class.name} debe tener custom_settings"
            
            settings = spider_class.custom_settings
            
            # Verificar configuraciones requeridas
            for setting, validator in self.REQUIRED_SETTINGS.items():
                assert setting in settings, \
                    f"{spider_class.name} debe definir {setting}"
                
                assert validator(settings[setting]), \
                    f"{spider_class.name}.{setting} = {settings[setting]} no cumple con los requisitos"
            
            # Verificar pipelines (si están definidos en custom_settings)
            if 'ITEM_PIPELINES' in settings:
                pipelines_str = str(settings['ITEM_PIPELINES'])
                for pipeline in self.REQUIRED_PIPELINES:
                    assert pipeline in pipelines_str, \
                        f"{spider_class.name} debe incluir {pipeline} en sus pipelines"
    
    def test_spider_produces_valid_items(self, mock_settings):
        """Verificar que los spiders producen items válidos con todos los campos requeridos."""
        spiders = self.get_all_spiders()
        
        for spider_class in spiders:
            # Crear instancia del spider con crawler mock
            crawler = get_crawler(spider_class, mock_settings)
            spider = spider_class.from_crawler(crawler)
            
            # Preparar caso de prueba
            test_case = SpiderTestCase(spider_class)
            
            # Crear response mock según el tipo de spider
            if test_case.test_data['spider_type'] == 'rss':
                # Simular parsing de RSS
                response = self._create_mock_response(
                    'https://example.com/feed.rss',
                    test_case.test_data['sample_feed'],
                    spider
                )
                
                # Si el spider tiene parse_feed, usarlo
                if hasattr(spider, 'parse_feed'):
                    requests = list(spider.parse_feed(response))
                    assert len(requests) > 0, f"{spider.name} no generó requests del feed"
            else:
                # Simular parsing de sección HTML
                response = self._create_mock_response(
                    'https://example.com/seccion',
                    test_case.test_data['sample_section_html'],
                    spider
                )
                
                requests = list(spider.parse(response))
                assert len(requests) > 0, f"{spider.name} no generó requests de la sección"
            
            # Simular parsing de artículo
            article_response = self._create_mock_response(
                'https://example.com/seccion/articulo-1',
                test_case.test_data['sample_article_html'],
                spider
            )
            
            # Verificar que parse_article existe y produce items
            assert hasattr(spider, 'parse_article'), \
                f"{spider.name} debe implementar parse_article"
            
            item = spider.parse_article(article_response)
            
            # El spider puede retornar None si el artículo es inválido
            # pero debe retornar un ArticuloInItem para artículos válidos
            if item is not None:
                assert isinstance(item, ArticuloInItem), \
                    f"{spider.name} debe retornar ArticuloInItem o None"
                
                # Verificar campos requeridos
                adapter = ItemAdapter(item)
                for field in self.REQUIRED_FIELDS:
                    assert field in adapter, \
                        f"{spider.name} debe incluir el campo '{field}' en el item"
                
                # Verificar que los campos críticos no están vacíos
                critical_fields = ['url', 'titular', 'contenido_texto', 'medio']
                for field in critical_fields:
                    value = adapter.get(field)
                    assert value and str(value).strip(), \
                        f"{spider.name} campo '{field}' no puede estar vacío"
    
    def test_spider_section_filtering(self):
        """Verificar que los spiders implementan filtrado por sección cuando aplica."""
        spiders = self.get_all_spiders()
        
        for spider_class in spiders:
            # Skip si es un spider genérico sin sección específica
            if not hasattr(spider_class, 'target_section'):
                continue
            
            spider = spider_class()
            
            # Verificar que tiene método de filtrado
            if hasattr(spider, '_is_section_article'):
                # URLs de prueba
                section_url = f"https://example.com/{spider.target_section}/articulo-test"
                other_section_url = "https://example.com/otra-seccion/articulo-test"
                
                # Debe aceptar URLs de la sección correcta
                assert spider._is_section_article(section_url), \
                    f"{spider.name} debe aceptar URLs de su sección"
                
                # Debe rechazar URLs de otras secciones
                assert not spider._is_section_article(other_section_url), \
                    f"{spider.name} debe rechazar URLs de otras secciones"
    
    def test_spider_crawl_once_configuration(self):
        """Verificar configuración de deduplicación para comportamiento tipo RSS."""
        spiders = self.get_all_spiders()
        
        for spider_class in spiders:
            settings = spider_class.custom_settings
            
            # Verificar configuración de scrapy-crawl-once
            if 'CRAWL_ONCE_ENABLED' in settings:
                assert settings['CRAWL_ONCE_ENABLED'] is True, \
                    f"{spider_class.name} debe tener CRAWL_ONCE_ENABLED = True"
                
                assert 'CRAWL_ONCE_PATH' in settings, \
                    f"{spider_class.name} debe definir CRAWL_ONCE_PATH"
    
    def test_spider_metadata_inclusion(self):
        """Verificar que los spiders incluyen metadata apropiada."""
        spiders = self.get_all_spiders()
        
        for spider_class in spiders:
            crawler = get_crawler(spider_class)
            spider = spider_class.from_crawler(crawler)
            
            # Crear response mock
            response = self._create_mock_response(
                'https://example.com/seccion/articulo-1',
                SpiderTestCase(spider_class).test_data['sample_article_html'],
                spider
            )
            
            # Obtener item si el spider lo produce
            if hasattr(spider, 'parse_article'):
                item = spider.parse_article(response)
                
                if item:
                    adapter = ItemAdapter(item)
                    
                    # Verificar metadata
                    assert 'metadata' in adapter, \
                        f"{spider.name} debe incluir campo 'metadata'"
                    
                    metadata = adapter.get('metadata', {})
                    
                    # Verificar que incluye tipo de spider
                    assert 'spider_type' in metadata or 'extraction_method' in metadata, \
                        f"{spider.name} debe incluir tipo de spider en metadata"
    
    def test_spider_error_handling(self):
        """Verificar que los spiders manejan errores apropiadamente."""
        spiders = self.get_all_spiders()
        
        for spider_class in spiders:
            spider = spider_class()
            
            # Verificar que no crashean con responses vacíos
            empty_response = self._create_mock_response(
                'https://example.com/empty',
                '',
                spider
            )
            
            # parse no debe lanzar excepciones no manejadas
            try:
                if hasattr(spider, 'parse'):
                    list(spider.parse(empty_response))
                    
                if hasattr(spider, 'parse_article'):
                    result = spider.parse_article(empty_response)
                    # Debe retornar None o un item válido, no crashear
                    assert result is None or isinstance(result, ArticuloInItem)
                    
            except Exception as e:
                pytest.fail(f"{spider.name} no maneja correctamente responses vacíos: {e}")
    
    def test_spider_respects_robots_txt(self):
        """Verificar que los spiders respetan robots.txt."""
        spiders = self.get_all_spiders()
        
        for spider_class in spiders:
            settings = getattr(spider_class, 'custom_settings', {})
            
            # No deben deshabilitar ROBOTSTXT_OBEY explícitamente
            assert settings.get('ROBOTSTXT_OBEY', True) is not False, \
                f"{spider_class.name} no debe deshabilitar ROBOTSTXT_OBEY"
    
    def _create_mock_response(self, url: str, body: str, spider: Spider) -> Response:
        """Crear un mock response para testing."""
        request = Request(url)
        return TextResponse(
            url=url,
            request=request,
            body=body.encode('utf-8'),
            encoding='utf-8'
        )


# Tests específicos para tipos de spider

class TestRSSSpiders:
    """Tests específicos para spiders tipo RSS."""
    
    def test_rss_spider_handles_feed_parsing(self):
        """Verificar que los spiders RSS manejan feeds correctamente."""
        spiders = [s for s in TestUniversalSpider().get_all_spiders() 
                  if 'rss' in s.name.lower()]
        
        for spider_class in spiders:
            spider = spider_class()
            
            # Debe tener método parse_feed
            assert hasattr(spider, 'parse_feed'), \
                f"Spider RSS {spider.name} debe implementar parse_feed"
            
            # Debe tener feed_url configurado
            assert hasattr(spider, 'feed_url'), \
                f"Spider RSS {spider.name} debe tener feed_url configurado"


class TestPlaywrightSpiders:
    """Tests específicos para spiders con Playwright."""
    
    def test_playwright_spider_configuration(self):
        """Verificar configuración específica de Playwright."""
        spiders = [s for s in TestUniversalSpider().get_all_spiders() 
                  if 'playwright' in s.name.lower()]
        
        for spider_class in spiders:
            settings = spider_class.custom_settings
            
            # Debe tener handlers de Playwright configurados
            assert 'DOWNLOAD_HANDLERS' in settings, \
                f"{spider_class.name} debe configurar DOWNLOAD_HANDLERS"
            
            handlers = settings['DOWNLOAD_HANDLERS']
            assert 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler' in str(handlers), \
                f"{spider_class.name} debe usar ScrapyPlaywrightDownloadHandler"
            
            # Debe tener configuración de browser
            assert 'PLAYWRIGHT_BROWSER_TYPE' in settings, \
                f"{spider_class.name} debe configurar PLAYWRIGHT_BROWSER_TYPE"


# Funciones helper para testing manual de spiders específicos

def validate_spider(spider_class: Type[Spider], sample_urls: List[str] = None):
    """
    Función helper para validar un spider específico manualmente.
    
    Uso:
        from scraper_core.spiders.mi_spider import MiSpider
        validate_spider(MiSpider, ['https://example.com/seccion/test'])
    """
    test = TestUniversalSpider()
    
    print(f"\n=== Validando Spider: {spider_class.name} ===\n")
    
    # Verificar herencia
    try:
        test.test_spider_inheritance()
        print("✓ Herencia correcta de BaseArticleSpider")
    except AssertionError as e:
        print(f"✗ Error en herencia: {e}")
    
    # Verificar atributos
    try:
        test.test_spider_required_attributes()
        print("✓ Atributos requeridos presentes")
    except AssertionError as e:
        print(f"✗ Error en atributos: {e}")
    
    # Verificar configuración
    try:
        test.test_spider_custom_settings()
        print("✓ Configuración correcta")
    except AssertionError as e:
        print(f"✗ Error en configuración: {e}")
    
    # Más validaciones...
    print("\n=== Validación completa ===\n")


if __name__ == "__main__":
    # Ejecutar tests manualmente
    pytest.main([__file__, "-v"])
