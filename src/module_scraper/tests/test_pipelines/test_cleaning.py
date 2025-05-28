# Test Data Cleaning Pipeline
"""
Unit tests for the DataCleaningPipeline.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from scrapy import Spider
from itemadapter import ItemAdapter

from scraper_core.items import ArticuloInItem
from scraper_core.pipelines.cleaning import DataCleaningPipeline
from scraper_core.pipelines.exceptions import CleaningError


class TestDataCleaningPipeline:
    """Test suite for DataCleaningPipeline."""
    
    @pytest.fixture
    def spider(self):
        """Create a mock spider."""
        spider = Mock(spec=Spider)
        spider.name = 'test_spider'
        return spider
    
    @pytest.fixture
    def pipeline(self):
        """Create a pipeline instance with default settings."""
        pipeline = DataCleaningPipeline()
        pipeline.strip_html = True
        pipeline.normalize_whitespace = True
        pipeline.remove_empty_lines = True
        pipeline.standardize_quotes = True
        pipeline.preserve_html_content = True
        return pipeline
    
    @pytest.fixture
    def item_with_html(self):
        """Create an item with HTML content."""
        return ArticuloInItem({
            'url': 'https://example.com/article?utm_source=test&utm_campaign=test',
            'titular': '<h1>Test Article <strong>Title</strong></h1>',
            'medio': 'Test Media',
            'pais_publicacion': 'España',
            'tipo_medio': 'diario',
            'fecha_publicacion': '2024-01-15T10:30:00',
            'contenido_texto': '<p>This is <b>test</b> content with <script>alert("xss")</script> HTML.</p>',
            'contenido_html': '''
                <div class="article">
                    <script>console.log("remove me")</script>
                    <p style="color: red;">Article content</p>
                    <p></p>
                    <!-- Comment to remove -->
                    <iframe src="ad.html"></iframe>
                </div>
            ''',
            'autor': 'Por John Doe',
            'etiquetas_fuente': 'tag1, tag2, TAG3'
        })
    
    def test_html_stripping(self, pipeline, spider, item_with_html):
        """Test HTML tag removal from text fields."""
        result = pipeline.process_item(item_with_html, spider)
        adapter = ItemAdapter(result)
        
        # Check HTML was stripped
        assert adapter.get('titular') == 'Test Article Title'
        assert adapter.get('contenido_texto') == 'This is test content with HTML.'
        assert '<' not in adapter.get('titular')
        assert '<' not in adapter.get('contenido_texto')
    
    def test_text_normalization(self, pipeline, spider):
        """Test text normalization features."""
        item = ArticuloInItem({
            'url': 'https://example.com',
            'titular': 'Test   Article    Title',  # Multiple spaces
            'medio': 'Test\u200bMedia',  # Zero-width space
            'contenido_texto': '''
                
                Line 1
                
                
                Line 2
                
            ''',  # Multiple empty lines
            'pais_publicacion': 'España',
            'tipo_medio': 'diario',
            'fecha_publicacion': '2024-01-15'
        })
        
        result = pipeline.process_item(item, spider)
        adapter = ItemAdapter(result)
        
        # Check whitespace normalization
        assert adapter.get('titular') == 'Test Article Title'
        assert adapter.get('medio') == 'TestMedia'
        
        # Check empty lines removed
        content = adapter.get('contenido_texto')
        assert content == 'Line 1\nLine 2'
    
    def test_quote_standardization(self, pipeline, spider):
        """Test quote character standardization."""
        item = ArticuloInItem({
            'url': 'https://example.com',
            'titular': '"Smart quotes" and 'apostrophes'',
            'contenido_texto': 'He said "Hello" and I replied 'Hi'',
            'medio': 'Test Media',
            'pais_publicacion': 'España',
            'tipo_medio': 'diario',
            'fecha_publicacion': '2024-01-15'
        })
        
        result = pipeline.process_item(item, spider)
        adapter = ItemAdapter(result)
        
        assert adapter.get('titular') == '"Smart quotes" and \'apostrophes\''
        assert adapter.get('contenido_texto') == 'He said "Hello" and I replied \'Hi\''
    
    def test_url_cleaning(self, pipeline, spider):
        """Test URL cleaning and normalization."""
        test_cases = [
            (
                'https://example.com/article?utm_source=test&id=123',
                'https://example.com/article?id=123'
            ),
            (
                'https://example.com/article/',
                'https://example.com/article'
            ),
            (
                'https://example.com/article#section',
                'https://example.com/article'
            )
        ]
        
        for input_url, expected_url in test_cases:
            item = ArticuloInItem({
                'url': input_url,
                'titular': 'Test',
                'medio': 'Test',
                'pais_publicacion': 'Test',
                'tipo_medio': 'diario',
                'fecha_publicacion': '2024-01-15',
                'contenido_texto': 'Test content'
            })
            
            result = pipeline.process_item(item, spider)
            adapter = ItemAdapter(result)
            
            assert adapter.get('url') == expected_url
    
    def test_date_standardization(self, pipeline, spider):
        """Test date field standardization to ISO format."""
        item = ArticuloInItem({
            'url': 'https://example.com',
            'titular': 'Test',
            'medio': 'Test',
            'pais_publicacion': 'Test',
            'tipo_medio': 'diario',
            'fecha_publicacion': '2024-01-15 10:30:00',
            'fecha_recopilacion': datetime(2024, 1, 20, 15, 45, 30),
            'contenido_texto': 'Test content'
        })
        
        result = pipeline.process_item(item, spider)
        adapter = ItemAdapter(result)
        
        assert adapter.get('fecha_publicacion') == '2024-01-15T10:30:00'
        assert adapter.get('fecha_recopilacion') == '2024-01-20T15:45:30'
    
    def test_author_cleaning(self, pipeline, spider):
        """Test author name cleaning."""
        test_cases = [
            ('Por John Doe', 'John Doe'),
            ('By Jane Smith', 'Jane Smith'),
            ('Dr. Roberto García', 'Roberto García'),
            ('Maria Lopez, PhD', 'Maria Lopez'),
            ('Carlos Ruiz y Ana Martín', 'Carlos Ruiz, Ana Martín'),
            ('John Doe <john@example.com>', 'John Doe'),
            ('@reporter_twitter', ''),
        ]
        
        for input_author, expected_author in test_cases:
            item = ArticuloInItem({
                'url': 'https://example.com',
                'titular': 'Test',
                'medio': 'Test',
                'pais_publicacion': 'Test',
                'tipo_medio': 'diario',
                'fecha_publicacion': '2024-01-15',
                'contenido_texto': 'Test content',
                'autor': input_author
            })
            
            result = pipeline.process_item(item, spider)
            adapter = ItemAdapter(result)
            
            assert adapter.get('autor') == expected_author
    
    def test_list_normalization(self, pipeline, spider):
        """Test normalization of list fields."""
        item = ArticuloInItem({
            'url': 'https://example.com',
            'titular': 'Test',
            'medio': 'Test',
            'pais_publicacion': 'Test',
            'tipo_medio': 'diario',
            'fecha_publicacion': '2024-01-15',
            'contenido_texto': 'Test content',
            'etiquetas_fuente': 'Tag1, TAG2, "tag3", tag1',  # Duplicates and quotes
            'categorias_asignadas': ['Cat1', 'CAT2', 'cat1']  # Already a list
        })
        
        result = pipeline.process_item(item, spider)
        adapter = ItemAdapter(result)
        
        # Should be normalized to lowercase, no duplicates
        assert adapter.get('etiquetas_fuente') == ['tag1', 'tag2', 'tag3']
        assert adapter.get('categorias_asignadas') == ['cat1', 'cat2']
    
    def test_html_content_cleaning(self, pipeline, spider, item_with_html):
        """Test HTML content cleaning while preserving structure."""
        result = pipeline.process_item(item_with_html, spider)
        adapter = ItemAdapter(result)
        
        html_content = adapter.get('contenido_html')
        
        # Scripts should be removed
        assert '<script>' not in html_content
        assert 'console.log' not in html_content
        
        # Style attributes should be removed
        assert 'style=' not in html_content
        
        # Comments should be removed
        assert '<!--' not in html_content
        
        # Iframes should be removed
        assert '<iframe' not in html_content
        
        # Empty paragraphs should be removed
        assert '<p></p>' not in html_content
        
        # Content should still be there
        assert 'Article content' in html_content
    
    def test_encoding_fixes(self, pipeline, spider):
        """Test fixing of common encoding issues."""
        item = ArticuloInItem({
            'url': 'https://example.com',
            'titular': 'La programaciÃ³n es Ãºtil',
            'contenido_texto': 'ArtÃ­culo sobre cÃ³digo en EspaÃ±a',
            'medio': 'Test',
            'pais_publicacion': 'España',
            'tipo_medio': 'diario',
            'fecha_publicacion': '2024-01-15'
        })
        
        result = pipeline.process_item(item, spider)
        adapter = ItemAdapter(result)
        
        assert adapter.get('titular') == 'La programación es útil'
        assert adapter.get('contenido_texto') == 'Artículo sobre código en España'
    
    def test_statistics_tracking(self, pipeline, spider, item_with_html):
        """Test that cleaning statistics are properly tracked."""
        pipeline.process_item(item_with_html, spider)
        
        assert pipeline.cleaning_stats['total_items'] == 1
        assert pipeline.cleaning_stats['items_cleaned'] == 1
        assert pipeline.cleaning_stats['html_stripped'] > 0
        assert pipeline.cleaning_stats['text_normalized'] > 0
        assert pipeline.cleaning_stats['urls_normalized'] > 0
    
    def test_non_articulo_item_skipped(self, pipeline, spider):
        """Test that non-ArticuloInItem items are skipped."""
        other_item = {'some': 'data'}
        
        result = pipeline.process_item(other_item, spider)
        
        assert result is other_item
        assert pipeline.cleaning_stats['total_items'] == 0
    
    def test_cleaning_error_handling(self, pipeline, spider):
        """Test that cleaning errors don't drop items."""
        item = ArticuloInItem({
            'url': 'https://example.com',
            'titular': 'Test',
            'medio': 'Test',
            'pais_publicacion': 'Test',
            'tipo_medio': 'diario',
            'fecha_publicacion': 'invalid-date-that-might-cause-error',
            'contenido_texto': 'Test content'
        })
        
        # Should not raise exception
        result = pipeline.process_item(item, spider)
        adapter = ItemAdapter(result)
        
        # Item should still be returned
        assert result is item
        # But might have error detail
        # (depending on implementation)
    
    def test_from_crawler_configuration(self):
        """Test pipeline configuration from crawler settings."""
        crawler = Mock()
        crawler.settings = Mock()
        crawler.settings.getbool = Mock(side_effect=lambda key, default: {
            'CLEANING_STRIP_HTML': False,
            'CLEANING_NORMALIZE_WHITESPACE': False,
            'CLEANING_REMOVE_EMPTY_LINES': True,
            'CLEANING_STANDARDIZE_QUOTES': False,
            'CLEANING_PRESERVE_HTML_CONTENT': True
        }.get(key, default))
        
        pipeline = DataCleaningPipeline.from_crawler(crawler)
        
        assert pipeline.strip_html is False
        assert pipeline.normalize_whitespace is False
        assert pipeline.remove_empty_lines is True
        assert pipeline.standardize_quotes is False
        assert pipeline.preserve_html_content is True
