# Data Validation Pipeline
"""
Pipeline for validating extracted data before storage.
Performs field-by-field validation for ArticuloInItem instances.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from itemadapter import ItemAdapter
from scrapy import Spider

from scraper_core.items import ArticuloInItem
from .exceptions import (
    RequiredFieldMissingError,
    DataTypeError,
    DateFormatError,
    ValidationError
)

logger = logging.getLogger(__name__)


class DataValidationPipeline:
    """
    Validates scraped articles before they are processed and stored.
    
    This pipeline performs:
    - Required field validation
    - Data type checking and conversion
    - Date format validation
    - URL format validation
    - Content length validation
    """
    
    # Required fields configuration
    REQUIRED_FIELDS = [
        'url',
        'titular',
        'medio',
        'pais_publicacion',
        'tipo_medio',
        'fecha_publicacion',
        'contenido_texto'
    ]
    
    # Optional fields with default values
    OPTIONAL_FIELDS_DEFAULTS = {
        'autor': 'Desconocido',
        'idioma': 'es',
        'es_opinion': False,
        'es_oficial': False,
        'estado_procesamiento': 'pendiente'
    }
    
    # Field type specifications
    FIELD_TYPES = {
        'url': str,
        'titular': str,
        'medio': str,
        'pais_publicacion': str,
        'tipo_medio': str,
        'fecha_publicacion': (str, datetime),  # Can be string or datetime
        'contenido_texto': str,
        'contenido_html': str,
        'autor': str,
        'idioma': str,
        'seccion': str,
        'etiquetas_fuente': list,
        'es_opinion': bool,
        'es_oficial': bool,
        'resumen': str,
        'categorias_asignadas': list,
        'puntuacion_relevancia': (int, float),
        'fecha_recopilacion': (str, datetime),
        'fecha_procesamiento': (str, datetime),
        'estado_procesamiento': str,
        'error_detalle': str,
        'storage_path': str,
        'metadata': dict
    }
    
    # Valid values for enum-like fields
    VALID_TIPOS_MEDIO = [
        'diario', 'agencia', 'television', 'radio', 
        'revista', 'blog', 'institucional', 'otro'
    ]
    
    VALID_ESTADOS_PROCESAMIENTO = [
        'pendiente', 'procesando', 'completado', 'error', 'descartado'
    ]
    
    def __init__(self):
        self.validation_stats = {
            'total_items': 0,
            'valid_items': 0,
            'invalid_items': 0,
            'validation_errors': {}
        }
    
    @classmethod
    def from_crawler(cls, crawler):
        """Initialize from crawler with custom settings."""
        instance = cls()
        
        # Load custom validation rules from settings if available
        custom_required_fields = crawler.settings.getlist('VALIDATION_REQUIRED_FIELDS')
        if custom_required_fields:
            instance.REQUIRED_FIELDS = custom_required_fields
        
        # Load minimum content length from settings
        instance.min_content_length = crawler.settings.getint('VALIDATION_MIN_CONTENT_LENGTH', 100)
        instance.min_title_length = crawler.settings.getint('VALIDATION_MIN_TITLE_LENGTH', 10)
        
        # Load date format from settings
        instance.date_format = crawler.settings.get('VALIDATION_DATE_FORMAT', '%Y-%m-%dT%H:%M:%S')
        instance.drop_invalid_items = crawler.settings.getbool('VALIDATION_DROP_INVALID_ITEMS', False)
        
        logger.info(
            f"DataValidationPipeline initialized with {len(instance.REQUIRED_FIELDS)} required fields, "
            f"min_content_length={instance.min_content_length}, date_format={instance.date_format}"
        )
        
        return instance
    
    def open_spider(self, spider: Spider):
        """Called when spider opens."""
        logger.info(f"DataValidationPipeline opened for spider: {spider.name}")
        self.spider_name = spider.name
    
    def close_spider(self, spider: Spider):
        """Called when spider closes. Log validation statistics."""
        logger.info(
            f"DataValidationPipeline closed for spider: {spider.name}. "
            f"Stats: {self.validation_stats}"
        )
    
    def process_item(self, item, spider: Spider):
        """Main processing method that validates each item."""
        if not isinstance(item, ArticuloInItem):
            logger.debug(f"Item is not ArticuloInItem, skipping validation: {type(item)}")
            return item
        
        adapter = ItemAdapter(item)
        item_url = adapter.get('url', 'Unknown URL')
        
        self.validation_stats['total_items'] += 1
        
        try:
            # Perform all validations
            self._validate_required_fields(adapter, item_url)
            self._validate_field_types(adapter, item_url)
            self._validate_url_format(adapter, item_url)
            self._validate_dates(adapter, item_url)
            self._validate_content_length(adapter, item_url)
            self._validate_enums(adapter, item_url)
            self._apply_defaults(adapter)
            
            # If we get here, validation passed
            self.validation_stats['valid_items'] += 1
            logger.debug(f"Item validated successfully: {item_url}")
            
        except ValidationError as e:
            self.validation_stats['invalid_items'] += 1
            error_type = type(e).__name__
            self.validation_stats['validation_errors'][error_type] = \
                self.validation_stats['validation_errors'].get(error_type, 0) + 1
            
            logger.warning(f"Validation failed for {item_url}: {e}")
            
            # Add error details to item for tracking
            adapter['error_detalle'] = str(e)
            adapter['estado_procesamiento'] = 'error'
            
            if self.drop_invalid_items:
                logger.warning(f"Validation failed for {item_url} and VALIDATION_DROP_INVALID_ITEMS is True. Dropping item: {e}")
                raise # Re-raise to drop the item
            else:
                logger.warning(f"Validation failed for {item_url} but VALIDATION_DROP_INVALID_ITEMS is False. Passing item with error details: {e}")
                return item # Pass the item to the next stage
        
        return item
    
    def _validate_required_fields(self, adapter: ItemAdapter, item_url: str):
        """Check that all required fields are present and non-empty."""
        for field in self.REQUIRED_FIELDS:
            value = adapter.get(field)
            
            if value is None or (isinstance(value, str) and not value.strip()):
                raise RequiredFieldMissingError(field=field, item_url=item_url)
    
    def _validate_field_types(self, adapter: ItemAdapter, item_url: str):
        """Validate and convert field types where possible."""
        for field, expected_types in self.FIELD_TYPES.items():
            if field not in adapter:
                continue
            
            value = adapter.get(field)
            if value is None:
                continue
            
            # Handle tuple of allowed types
            if isinstance(expected_types, tuple):
                if not isinstance(value, expected_types):
                    # Try type conversion for common cases
                    if str in expected_types and not isinstance(value, str):
                        adapter[field] = str(value)
                    elif bool in expected_types and not isinstance(value, bool):
                        adapter[field] = bool(value)
                    else:
                        raise DataTypeError(
                            field=field,
                            expected_type=str(expected_types),
                            actual_type=type(value).__name__,
                            item_url=item_url
                        )
            else:
                if not isinstance(value, expected_types):
                    # Try type conversion
                    try:
                        if expected_types == str:
                            adapter[field] = str(value)
                        elif expected_types == bool:
                            adapter[field] = bool(value)
                        elif expected_types == list and isinstance(value, str):
                            # Convert comma-separated string to list
                            adapter[field] = [x.strip() for x in value.split(',') if x.strip()]
                        elif expected_types == dict and isinstance(value, str):
                            # Try to parse JSON string
                            import json
                            adapter[field] = json.loads(value)
                        else:
                            raise DataTypeError(
                                field=field,
                                expected_type=expected_types.__name__,
                                actual_type=type(value).__name__,
                                item_url=item_url
                            )
                    except (ValueError, json.JSONDecodeError) as e:
                        raise DataTypeError(
                            field=field,
                            expected_type=expected_types.__name__,
                            actual_type=type(value).__name__,
                            item_url=item_url
                        )
    
    def _validate_url_format(self, adapter: ItemAdapter, item_url: str):
        """Validate URL format."""
        url = adapter.get('url')
        if not url:
            return
        
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValidationError(
                    f"Invalid URL format: missing scheme or netloc",
                    field='url',
                    item_url=item_url
                )
            
            if parsed.scheme not in ['http', 'https']:
                raise ValidationError(
                    f"Invalid URL scheme: {parsed.scheme}",
                    field='url',
                    item_url=item_url
                )
        except Exception as e:
            raise ValidationError(
                f"Invalid URL format: {e}",
                field='url',
                item_url=item_url
            )
    
    def _validate_dates(self, adapter: ItemAdapter, item_url: str):
        """Validate and normalize date fields."""
        date_fields = ['fecha_publicacion', 'fecha_recopilacion', 'fecha_procesamiento']
        
        for field in date_fields:
            value = adapter.get(field)
            if not value:
                continue
            
            # If already datetime, convert to ISO string
            if isinstance(value, datetime):
                adapter[field] = value.isoformat()
                continue
            
            # Try to parse string dates
            if isinstance(value, str):
                # Try multiple date formats
                date_formats = [
                    self.date_format,
                    '%Y-%m-%d',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%dT%H:%M:%S.%f',
                    '%Y-%m-%dT%H:%M:%S.%fZ'
                ]
                
                parsed = False
                for fmt in date_formats:
                    try:
                        dt = datetime.strptime(value, fmt)
                        adapter[field] = dt.isoformat()
                        parsed = True
                        break
                    except ValueError:
                        continue
                
                if not parsed:
                    raise DateFormatError(
                        field=field,
                        value=value,
                        expected_format=self.date_format,
                        item_url=item_url
                    )
    
    def _validate_content_length(self, adapter: ItemAdapter, item_url: str):
        """Validate minimum content lengths."""
        # Check title length
        titular = adapter.get('titular', '')
        if len(titular) < self.min_title_length:
            raise ValidationError(
                f"Title too short: {len(titular)} chars (minimum: {self.min_title_length})",
                field='titular',
                item_url=item_url
            )
        
        # Check content length
        content = adapter.get('contenido_texto', '')
        if len(content) < self.min_content_length:
            raise ValidationError(
                f"Content too short: {len(content)} chars (minimum: {self.min_content_length})",
                field='contenido_texto',
                item_url=item_url
            )
    
    def _validate_enums(self, adapter: ItemAdapter, item_url: str):
        """Validate enum-like fields against allowed values."""
        # Validate tipo_medio
        tipo_medio = adapter.get('tipo_medio')
        if tipo_medio and tipo_medio.lower() not in self.VALID_TIPOS_MEDIO:
            logger.warning(
                f"Unknown tipo_medio '{tipo_medio}' for {item_url}. "
                f"Valid values: {self.VALID_TIPOS_MEDIO}"
            )
            # Don't raise error, just normalize to 'otro'
            adapter['tipo_medio'] = 'otro'
        
        # Validate estado_procesamiento
        estado = adapter.get('estado_procesamiento')
        if estado and estado not in self.VALID_ESTADOS_PROCESAMIENTO:
            logger.warning(
                f"Unknown estado_procesamiento '{estado}' for {item_url}. "
                f"Setting to 'pendiente'"
            )
            adapter['estado_procesamiento'] = 'pendiente'
    
    def _apply_defaults(self, adapter: ItemAdapter):
        """Apply default values to optional fields."""
        for field, default_value in self.OPTIONAL_FIELDS_DEFAULTS.items():
            if adapter.get(field) is None:
                adapter[field] = default_value
        
        # Set fecha_recopilacion if not present
        if not adapter.get('fecha_recopilacion'):
            adapter['fecha_recopilacion'] = datetime.utcnow().isoformat()
