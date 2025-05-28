# Test Data Validation Pipeline
"""
Unit tests for the DataValidationPipeline.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from scrapy import Spider
from scrapy.http import Response, Request
from itemadapter import ItemAdapter

from scraper_core.items import ArticuloInItem
from scraper_core.pipelines.validation import DataValidationPipeline
from scraper_core.pipelines.exceptions import (
    RequiredFieldMissingError,
    DataTypeError,
    DateFormatError,
    ValidationError
)


class TestDataValidationPipeline:
    """Test suite for DataValidationPipeline."""
    
    @pytest.fixture
    def spider(self):
        """Create a mock spider."""
        spider = Mock(spec=Spider)
        spider.name = 'test_spider'
        return spider
    
    @pytest.fixture
    def pipeline(self):
        """Create a pipeline instance."""
        pipeline = DataValidationPipeline()
        pipeline.min_content_length = 50
        pipeline.min_title_length = 5
        pipeline.date_format = '%Y-%m-%dT%H:%M:%S'
        return pipeline
    
    @pytest.fixture
    def valid_item(self):
        """Create a valid ArticuloInItem."""
        return ArticuloInItem({
            'url': 'https://example.com/article',
            'titular': 'Test Article Title',
            'medio': 'Test Media',
            'pais_publicacion': 'España',
            'tipo_medio': 'diario',
            'fecha_publicacion': '2024-01-15T10:30:00',
            'contenido_texto': 'This is a test article content that is long enough to pass validation.'
        })
    
    def test_valid_item_passes_validation(self, pipeline, spider, valid_item):
        """Test that a valid item passes all validations."""
        result = pipeline.process_item(valid_item, spider)
        
        assert result is valid_item
        assert pipeline.validation_stats['valid_items'] == 1
        assert pipeline.validation_stats['invalid_items'] == 0
    
    def test_missing_required_field_raises_error(self, pipeline, spider, valid_item):
        """Test that missing required fields raise RequiredFieldMissingError."""
        # Remove a required field
        del valid_item['titular']
        
        with pytest.raises(RequiredFieldMissingError) as exc_info:
            pipeline.process_item(valid_item, spider)
        
        assert exc_info.value.field == 'titular'
        assert pipeline.validation_stats['invalid_items'] == 1
    
    def test_empty_required_field_raises_error(self, pipeline, spider, valid_item):
        """Test that empty required fields raise RequiredFieldMissingError."""
        valid_item['contenido_texto'] = '   '  # Only whitespace
        
        with pytest.raises(RequiredFieldMissingError) as exc_info:
            pipeline.process_item(valid_item, spider)
        
        assert exc_info.value.field == 'contenido_texto'
    
    def test_incorrect_field_type_conversion(self, pipeline, spider, valid_item):
        """Test field type conversion."""
        # Set boolean field as string
        valid_item['es_opinion'] = 'true'
        
        result = pipeline.process_item(valid_item, spider)
        adapter = ItemAdapter(result)
        
        # Should be converted to boolean
        assert adapter.get('es_opinion') is True
    
    def test_list_field_from_string(self, pipeline, spider, valid_item):
        """Test conversion of comma-separated string to list."""
        valid_item['etiquetas_fuente'] = 'tag1, tag2, tag3'
        
        result = pipeline.process_item(valid_item, spider)
        adapter = ItemAdapter(result)
        
        assert adapter.get('etiquetas_fuente') == ['tag1', 'tag2', 'tag3']
    
    def test_invalid_url_format(self, pipeline, spider, valid_item):
        """Test that invalid URLs raise ValidationError."""
        valid_item['url'] = 'not-a-valid-url'
        
        with pytest.raises(ValidationError) as exc_info:
            pipeline.process_item(valid_item, spider)
        
        assert 'Invalid URL format' in str(exc_info.value)
        assert exc_info.value.field == 'url'
    
    def test_date_normalization(self, pipeline, spider, valid_item):
        """Test date field normalization."""
        # Test various date formats
        test_dates = [
            ('2024-01-15', '2024-01-15T00:00:00'),
            ('2024-01-15T10:30:00Z', '2024-01-15T10:30:00'),
            (datetime(2024, 1, 15, 10, 30), '2024-01-15T10:30:00')
        ]
        
        for input_date, expected in test_dates:
            valid_item['fecha_publicacion'] = input_date
            result = pipeline.process_item(valid_item, spider)
            adapter = ItemAdapter(result)
            
            assert adapter.get('fecha_publicacion') == expected
    
    def test_invalid_date_format(self, pipeline, spider, valid_item):
        """Test that invalid date formats raise DateFormatError."""
        valid_item['fecha_publicacion'] = 'invalid-date'
        
        with pytest.raises(DateFormatError) as exc_info:
            pipeline.process_item(valid_item, spider)
        
        assert exc_info.value.field == 'fecha_publicacion'
    
    def test_content_too_short(self, pipeline, spider, valid_item):
        """Test that short content raises ValidationError."""
        valid_item['contenido_texto'] = 'Too short'
        
        with pytest.raises(ValidationError) as exc_info:
            pipeline.process_item(valid_item, spider)
        
        assert 'Content too short' in str(exc_info.value)
    
    def test_title_too_short(self, pipeline, spider, valid_item):
        """Test that short title raises ValidationError."""
        valid_item['titular'] = 'Tiny'
        
        with pytest.raises(ValidationError) as exc_info:
            pipeline.process_item(valid_item, spider)
        
        assert 'Title too short' in str(exc_info.value)
    
    def test_enum_validation(self, pipeline, spider, valid_item):
        """Test enum field validation and normalization."""
        # Invalid tipo_medio should be normalized to 'otro'
        valid_item['tipo_medio'] = 'invalid_type'
        
        result = pipeline.process_item(valid_item, spider)
        adapter = ItemAdapter(result)
        
        assert adapter.get('tipo_medio') == 'otro'
    
    def test_default_values_applied(self, pipeline, spider, valid_item):
        """Test that default values are applied to optional fields."""
        result = pipeline.process_item(valid_item, spider)
        adapter = ItemAdapter(result)
        
        assert adapter.get('autor') == 'Desconocido'
        assert adapter.get('idioma') == 'es'
        assert adapter.get('es_opinion') is False
        assert adapter.get('es_oficial') is False
        assert adapter.get('estado_procesamiento') == 'pendiente'
    
    def test_fecha_recopilacion_auto_set(self, pipeline, spider, valid_item):
        """Test that fecha_recopilacion is automatically set."""
        result = pipeline.process_item(valid_item, spider)
        adapter = ItemAdapter(result)
        
        fecha_recopilacion = adapter.get('fecha_recopilacion')
        assert fecha_recopilacion is not None
        
        # Verify it's a valid ISO format datetime
        datetime.fromisoformat(fecha_recopilacion)
    
    def test_statistics_tracking(self, pipeline, spider, valid_item):
        """Test that validation statistics are properly tracked."""
        # Process valid item
        pipeline.process_item(valid_item, spider)
        
        # Process invalid item
        invalid_item = ArticuloInItem({'url': 'https://example.com'})
        try:
            pipeline.process_item(invalid_item, spider)
        except RequiredFieldMissingError:
            pass
        
        assert pipeline.validation_stats['total_items'] == 2
        assert pipeline.validation_stats['valid_items'] == 1
        assert pipeline.validation_stats['invalid_items'] == 1
        assert 'RequiredFieldMissingError' in pipeline.validation_stats['validation_errors']
    
    def test_non_articulo_item_skipped(self, pipeline, spider):
        """Test that non-ArticuloInItem items are skipped."""
        other_item = {'some': 'data'}
        
        result = pipeline.process_item(other_item, spider)
        
        assert result is other_item
        assert pipeline.validation_stats['total_items'] == 0
    
    def test_from_crawler_configuration(self):
        """Test pipeline configuration from crawler settings."""
        crawler = Mock()
        crawler.settings = Mock()
        crawler.settings.getlist = Mock(return_value=['url', 'titular'])
        crawler.settings.getint = Mock(side_effect=lambda key, default: {
            'VALIDATION_MIN_CONTENT_LENGTH': 200,
            'VALIDATION_MIN_TITLE_LENGTH': 20
        }.get(key, default))
        crawler.settings.get = Mock(return_value='%Y-%m-%d')
        
        pipeline = DataValidationPipeline.from_crawler(crawler)
        
        assert pipeline.REQUIRED_FIELDS == ['url', 'titular']
        assert pipeline.min_content_length == 200
        assert pipeline.min_title_length == 20
        assert pipeline.date_format == '%Y-%m-%d'
