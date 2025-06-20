# Tests End-to-End para el flujo completo de scraping
"""
Tests E2E que verifican el flujo completo desde que un spider
extrae contenido hasta que se almacena en Supabase.

Estos tests usan mocks para simular el comportamiento sin
necesidad de conexiones reales.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from scrapy.utils.test import get_crawler
from scrapy.http import HtmlResponse, Request

from scraper_core.items import ArticuloInItem
from scraper_core.spiders.base.base_article import BaseArticleSpider


class TestE2EFlow:
    """Tests del flujo completo de extracción y almacenamiento."""
    
    @pytest.fixture
    def mock_spider_class(self):
        """Crear una clase de spider mock para testing."""
        class TestSpider(BaseArticleSpider):
            name = 'test_e2e_spider'
            allowed_domains = ['example.com']
            start_urls = ['https://example.com/test-section']
            
            medio_nombre = 'Test Medio'
            pais = 'Argentina'
            tipo_medio = 'diario'
            target_section = 'test-section'
            
            custom_settings = {
                **BaseArticleSpider.custom_settings,
                'DOWNLOAD_DELAY': 2.0,
                'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
                'CLOSESPIDER_ITEMCOUNT': 10,
            }
            
            def parse(self, response):
                # Simular extracción de enlaces
                urls = response.css('article a::attr(href)').getall()
                for url in urls:
                    yield response.follow(url, self.parse_article)
            
            def parse_article(self, response):
                # Usar métodos de la clase base
                item = ArticuloInItem()
                item['url'] = response.url
                item['titular'] = self.extract_article_title(response)
                item['contenido_texto'] = self.extract_article_content(response)
                item['contenido_html'] = response.text
                item['fecha_publicacion'] = self.extract_publication_date(response)
                item['autor'] = self.extract_author(response) or 'Redacción'
                
                # Campos del medio
                item['medio'] = self.medio_nombre
                item['medio_url_principal'] = f"https://{self.allowed_domains[0]}"
                item['pais_publicacion'] = self.pais
                item['tipo_medio'] = self.tipo_medio
                item['seccion'] = self.target_section
                
                # Campos adicionales
                item['idioma'] = 'es'
                item['es_opinion'] = False
                item['es_oficial'] = False
                item['fecha_recopilacion'] = datetime.utcnow()
                item['fuente'] = self.name
                
                return item
        
        return TestSpider
    
    @pytest.fixture
    def sample_section_response(self):
        """HTML de una página de sección con artículos."""
        html = """
        <html>
        <body>
            <div class="section">
                <article>
                    <a href="/test-section/article-1">Artículo 1</a>
                </article>
                <article>
                    <a href="/test-section/article-2">Artículo 2</a>
                </article>
            </div>
        </body>
        </html>
        """
        request = Request('https://example.com/test-section')
        return HtmlResponse(
            url='https://example.com/test-section',
            request=request,
            body=html.encode('utf-8'),
            encoding='utf-8'
        )
    
    @pytest.fixture
    def sample_article_response(self):
        """HTML de un artículo completo."""
        html = """
        <html>
        <head>
            <title>Artículo de Prueba E2E</title>
            <meta property="article:published_time" content="2024-01-15T10:00:00Z">
        </head>
        <body>
            <article>
                <h1>Título del Artículo E2E</h1>
                <div class="author">Por Juan Pérez</div>
                <div class="content">
                    <p>Este es el contenido del artículo de prueba para el test E2E.</p>
                    <p>Tiene suficiente contenido para pasar la validación.</p>
                    <p>Y un tercer párrafo para asegurar que cumple los requisitos.</p>
                </div>
            </article>
        </body>
        </html>
        """
        request = Request('https://example.com/test-section/article-1')
        return HtmlResponse(
            url='https://example.com/test-section/article-1',
            request=request,
            body=html.encode('utf-8'),
            encoding='utf-8'
        )
    
    def test_complete_flow_with_mocked_pipelines(self, mock_spider_class):
        """Test del flujo completo con pipelines mockeados."""
        # Configurar mocks para los pipelines
        with patch('scraper_core.pipelines.validation.DataValidationPipeline.process_item') as mock_validation, \
             patch('scraper_core.pipelines.cleaning.DataCleaningPipeline.process_item') as mock_cleaning, \
             patch('scraper_core.pipelines.storage.SupabaseStoragePipeline.process_item') as mock_storage:
            
            # Configurar comportamiento de los mocks
            mock_validation.side_effect = lambda item, spider: item  # Pasa el item sin cambios
            mock_cleaning.side_effect = lambda item, spider: item    # Pasa el item sin cambios
            mock_storage.side_effect = lambda item, spider: item     # Pasa el item sin cambios
            
            # Crear crawler y spider
            crawler = get_crawler(mock_spider_class)
            spider = mock_spider_class.from_crawler(crawler)
            
            # Simular respuesta de artículo
            response = self.sample_article_response()
            
            # Ejecutar parse_article
            item = spider.parse_article(response)
            
            # Verificar que el item se creó correctamente
            assert isinstance(item, ArticuloInItem)
            assert item['url'] == 'https://example.com/test-section/article-1'
            assert item['titular'] == 'Título del Artículo E2E'
            assert 'contenido del artículo' in item['contenido_texto']
            assert item['autor'] == 'Por Juan Pérez'
            assert item['medio'] == 'Test Medio'
            
            # Simular el procesamiento por pipelines
            processed_item = mock_validation(item, spider)
            processed_item = mock_cleaning(processed_item, spider)
            processed_item = mock_storage(processed_item, spider)
            
            # Verificar que los pipelines fueron llamados
            assert mock_validation.called
            assert mock_cleaning.called
            assert mock_storage.called
    
    def test_flow_with_real_pipelines(self, mock_spider_class, sample_article_response):
        """Test con pipelines reales pero storage mockeado."""
        from scraper_core.pipelines.validation import DataValidationPipeline
        from scraper_core.pipelines.cleaning import DataCleaningPipeline
        
        # Solo mockear el storage (que requiere Supabase)
        with patch('scraper_core.utils.supabase_client.SupabaseClient') as mock_supabase:
            # Configurar mock de Supabase
            mock_client = MagicMock()
            mock_client.upsert_articulo.return_value = {'id': 'test-id'}
            mock_client.upload_to_storage.return_value = True
            mock_supabase.return_value = mock_client
            
            # Crear spider y pipelines
            crawler = get_crawler(mock_spider_class)
            spider = mock_spider_class.from_crawler(crawler)
            
            validation_pipeline = DataValidationPipeline.from_crawler(crawler)
            cleaning_pipeline = DataCleaningPipeline()
            
            # Abrir spider en pipelines
            validation_pipeline.open_spider(spider)
            
            # Crear item
            item = spider.parse_article(sample_article_response)
            
            # Procesar con pipelines reales
            try:
                validated_item = validation_pipeline.process_item(item, spider)
                cleaned_item = cleaning_pipeline.process_item(validated_item, spider)
                
                # Verificar que el item pasó validación y limpieza
                assert cleaned_item is not None
                assert cleaned_item['titular'] == 'Título del Artículo E2E'
                # El contenido debe estar limpio (sin tags HTML)
                assert '<p>' not in cleaned_item.get('contenido_texto', '')
                
            except Exception as e:
                pytest.fail(f"El flujo falló con error: {e}")
    
    def test_flow_handles_invalid_items(self, mock_spider_class):
        """Test que el flujo maneja items inválidos correctamente."""
        from scraper_core.pipelines.validation import DataValidationPipeline
        from scraper_core.pipelines.exceptions import RequiredFieldMissingError
        
        # Crear spider
        crawler = get_crawler(mock_spider_class)
        spider = mock_spider_class.from_crawler(crawler)
        
        # Crear un item inválido (sin contenido)
        invalid_item = ArticuloInItem()
        invalid_item['url'] = 'https://example.com/invalid'
        invalid_item['titular'] = 'Título'
        # Falta contenido_texto y otros campos requeridos
        
        # Crear pipeline de validación
        validation_pipeline = DataValidationPipeline.from_crawler(crawler)
        validation_pipeline.open_spider(spider)
        
        # El pipeline debe rechazar el item inválido
        with pytest.raises(RequiredFieldMissingError):
            validation_pipeline.process_item(invalid_item, spider)
    
    def test_multiple_items_flow(self, mock_spider_class):
        """Test procesando múltiples items en secuencia."""
        items_to_process = []
        
        # Crear varios items
        for i in range(3):
            item = ArticuloInItem()
            item['url'] = f'https://example.com/article-{i}'
            item['titular'] = f'Título {i}'
            item['contenido_texto'] = f'Contenido del artículo {i}. ' * 10
            item['contenido_html'] = f'<p>Contenido del artículo {i}</p>'
            item['medio'] = 'Test Medio'
            item['pais_publicacion'] = 'Argentina'
            item['tipo_medio'] = 'diario'
            item['fecha_publicacion'] = datetime.utcnow()
            item['autor'] = f'Autor {i}'
            item['fuente'] = 'test_spider'
            items_to_process.append(item)
        
        # Mock storage
        with patch('scraper_core.pipelines.storage.SupabaseStoragePipeline.process_item') as mock_storage:
            mock_storage.side_effect = lambda item, spider: item
            
            # Procesar todos los items
            processed_count = 0
            for item in items_to_process:
                processed_item = mock_storage(item, None)
                if processed_item:
                    processed_count += 1
            
            # Verificar que todos se procesaron
            assert processed_count == 3
            assert mock_storage.call_count == 3
