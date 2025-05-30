# Data Validation and Cleaning Pipelines

This document describes the implementation of the Data Validation and Cleaning pipelines for the Scrapy module.

## Overview

The validation and cleaning pipelines are essential components of the scraper that ensure data quality and consistency before storage. They work in sequence:

1. **DataValidationPipeline** - Validates required fields, data types, and formats
2. **DataCleaningPipeline** - Normalizes and cleans the validated data
3. **SupabaseStoragePipeline** - Stores the clean, validated data

## DataValidationPipeline

### Purpose

The `DataValidationPipeline` ensures that all scraped articles meet minimum quality standards before processing. It performs field-by-field validation and drops items that don't meet requirements.

### Features

- **Required Field Validation**: Ensures all mandatory fields are present and non-empty
- **Data Type Checking**: Validates and converts field types where possible
- **Date Format Validation**: Ensures dates are in ISO format
- **URL Format Validation**: Checks for valid URL structure
- **Content Length Validation**: Ensures minimum length for title and content
- **Enum Validation**: Validates fields with restricted values (e.g., `tipo_medio`)
- **Default Values**: Applies defaults to optional fields

### Configuration

Configure in `settings.py`:

```python
# Validation rules
VALIDATION_MIN_CONTENT_LENGTH = 100  # Minimum characters for article content
VALIDATION_MIN_TITLE_LENGTH = 10     # Minimum characters for article title
VALIDATION_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'  # Expected date format

# Optional: Override required fields
# VALIDATION_REQUIRED_FIELDS = ['url', 'titular', 'medio', 'contenido_texto']
```

### Required Fields

By default, the following fields are required:
- `url` - Article URL
- `titular` - Article title
- `medio` - Media source name
- `pais_publicacion` - Publication country
- `tipo_medio` - Media type
- `fecha_publicacion` - Publication date
- `contenido_texto` - Article content text

### Validation Rules

1. **URLs** must have valid scheme (http/https) and netloc
2. **Dates** are normalized to ISO format (YYYY-MM-DDTHH:MM:SS)
3. **Content** must meet minimum length requirements
4. **Lists** can be provided as comma-separated strings
5. **Booleans** are converted from string representations

### Error Handling

The pipeline raises specific exceptions for different validation failures:
- `RequiredFieldMissingError` - When a required field is missing or empty
- `DataTypeError` - When a field has an incorrect data type
- `DateFormatError` - When a date field has an invalid format
- `ValidationError` - For other validation failures

Items that fail validation are dropped and logged with detailed error information.

## DataCleaningPipeline

### Purpose

The `DataCleaningPipeline` normalizes and cleans validated data to ensure consistency across all stored articles.

### Features

- **HTML Stripping**: Removes HTML tags from text fields
- **Text Normalization**: Fixes whitespace, encoding issues, and special characters
- **Date Standardization**: Ensures all dates are in ISO format
- **URL Cleaning**: Removes tracking parameters and fragments
- **Author Cleaning**: Normalizes author names and removes titles
- **List Normalization**: Cleans and deduplicates tags/categories
- **HTML Content Cleaning**: Sanitizes HTML while preserving structure

### Configuration

Configure in `settings.py`:

```python
# Cleaning options
CLEANING_STRIP_HTML = True           # Strip HTML tags from text fields
CLEANING_NORMALIZE_WHITESPACE = True # Normalize whitespace in text
CLEANING_REMOVE_EMPTY_LINES = True   # Remove empty lines from content
CLEANING_STANDARDIZE_QUOTES = True   # Standardize quote characters
CLEANING_PRESERVE_HTML_CONTENT = True # Clean but preserve HTML structure
```

### Cleaning Operations

#### 1. HTML Stripping
- Removes all HTML tags from specified fields
- Removes script and style elements
- Preserves text content with proper spacing

#### 2. Text Normalization
- Normalizes Unicode characters (NFKC normalization)
- Removes multiple consecutive spaces
- Removes zero-width characters
- Fixes common encoding issues (e.g., Ã¡ → á)
- Standardizes quote characters

#### 3. URL Cleaning
- Removes URL fragments (#section)
- Removes trailing slashes
- Removes common tracking parameters (utm_*, etc.)

#### 4. Author Cleaning
- Removes common prefixes (Por, By, De, From)
- Handles multiple authors with consistent separators
- Removes titles and suffixes (Dr., PhD, etc.)
- Removes email addresses and social media handles

#### 5. List Normalization
- Converts string lists to arrays
- Normalizes case to lowercase
- Removes duplicates
- Strips quotes and extra whitespace

#### 6. HTML Content Cleaning
- Removes dangerous tags (script, iframe, etc.)
- Removes HTML comments
- Removes empty tags
- Strips unwanted attributes (onclick, style, etc.)
- Minifies HTML by removing unnecessary whitespace

### Error Handling

Cleaning errors are non-fatal. If a cleaning operation fails:
- The error is logged with details
- The error is added to the item's `error_detalle` field
- The item continues to the next pipeline

## Integration

### Pipeline Order

The pipelines must be configured in the correct order in `settings.py`:

```python
ITEM_PIPELINES = {
    "scraper_core.pipelines.validation.DataValidationPipeline": 100,
    "scraper_core.pipelines.cleaning.DataCleaningPipeline": 200,
    "scraper_core.pipelines.SupabaseStoragePipeline": 300,
}
```

### Custom Exceptions

The pipelines use custom exceptions for better error handling:

```python
from scraper_core.pipelines.exceptions import (
    ValidationError,
    RequiredFieldMissingError,
    DataTypeError,
    DateFormatError,
    CleaningError
)
```

### Statistics

Both pipelines track statistics that can be accessed after spider execution:

```python
# Validation statistics
validation_stats = {
    'total_items': 0,
    'valid_items': 0,
    'invalid_items': 0,
    'validation_errors': {}  # Count by error type
}

# Cleaning statistics
cleaning_stats = {
    'total_items': 0,
    'items_cleaned': 0,
    'html_stripped': 0,
    'text_normalized': 0,
    'dates_standardized': 0,
    'urls_normalized': 0
}
```

## Testing

### Unit Tests

Comprehensive unit tests are provided for both pipelines:
- `tests/test_pipelines/test_validation.py` - Tests for validation pipeline
- `tests/test_pipelines/test_cleaning.py` - Tests for cleaning pipeline

Run tests with:
```bash
pytest tests/test_pipelines/
```

### Example Usage

See `examples/pipeline_example.py` for a complete example demonstrating:
- Creating items with various issues
- Processing through both pipelines
- Handling validation errors
- Viewing cleaning results

## Best Practices

1. **Configure pipelines appropriately** for your use case
2. **Monitor statistics** to identify common validation failures
3. **Log validation errors** for debugging spider issues
4. **Test with diverse data** to ensure pipelines handle edge cases
5. **Adjust validation rules** based on your data sources
6. **Keep cleaning non-destructive** when possible

## Troubleshooting

### Common Issues

1. **Items being dropped unexpectedly**
   - Check validation rules and required fields
   - Review logs for specific validation errors
   - Verify data types match expectations

2. **Dates not parsing correctly**
   - Check date format configuration
   - Ensure dates are in expected format
   - Add new date formats to parsing list if needed

3. **HTML not being cleaned properly**
   - Verify BeautifulSoup is installed
   - Check HTML structure for unusual tags
   - Review cleaning configuration

4. **Performance issues**
   - Consider disabling unnecessary cleaning operations
   - Check for large HTML content
   - Profile pipeline execution time

### Logging

Enable detailed logging to troubleshoot issues:

```python
# In settings.py
LOG_LEVEL = 'DEBUG'
LOGGERS = {
    'scraper_core.pipelines.validation': 'DEBUG',
    'scraper_core.pipelines.cleaning': 'DEBUG',
}
```

## Future Enhancements

Potential improvements for the pipelines:

1. **Async Processing**: Convert to async methods for better performance
2. **Custom Validators**: Allow per-spider validation rules
3. **Machine Learning**: Use ML for content quality scoring
4. **Language Detection**: Automatic language detection and validation
5. **Duplicate Detection**: Integrate with DeltaFetch for duplicate checking
6. **Content Extraction**: Advanced content extraction using readability algorithms
