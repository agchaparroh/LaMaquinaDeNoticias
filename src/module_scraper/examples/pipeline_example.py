# Example: Using Validation and Cleaning Pipelines
"""
This example demonstrates how the DataValidationPipeline and DataCleaningPipeline
work together to process scraped articles.
"""

import json
from datetime import datetime
from scrapy import Spider
from itemadapter import ItemAdapter

from scraper_core.items import ArticuloInItem
from scraper_core.pipelines.validation import DataValidationPipeline
from scraper_core.pipelines.cleaning import DataCleaningPipeline
from scraper_core.pipelines.exceptions import ValidationError


def create_sample_items():
    """Create sample items with various issues to demonstrate pipeline functionality."""
    return [
        # Valid item
        ArticuloInItem({
            'url': 'https://example.com/article1?utm_source=twitter',
            'titular': '<h1>Breaking News: <strong>Important Event</strong></h1>',
            'medio': 'Example News',
            'pais_publicacion': 'España',
            'tipo_medio': 'diario',
            'fecha_publicacion': '2024-01-15 10:30:00',
            'contenido_texto': '''<p>This is the article content with <b>HTML tags</b> 
                and     multiple    spaces.</p>
                <script>alert("XSS")</script>
                <p>More content here.</p>''',
            'contenido_html': '''
                <article>
                    <script>console.log("tracking");</script>
                    <h1>Article Title</h1>
                    <p style="color: red;">Content paragraph</p>
                    <p></p>
                    <!-- Hidden comment -->
                </article>
            ''',
            'autor': 'Por María García y Juan López',
            'etiquetas_fuente': 'Politics, BREAKING NEWS, politics'
        }),
        
        # Item with missing required fields
        ArticuloInItem({
            'url': 'https://example.com/article2',
            'medio': 'Example News',
            # Missing: titular, pais_publicacion, tipo_medio, fecha_publicacion, contenido_texto
        }),
        
        # Item with invalid data types and formats
        ArticuloInItem({
            'url': 'not-a-valid-url',
            'titular': 'Too',  # Too short
            'medio': 'Example News',
            'pais_publicacion': 'España',
            'tipo_medio': 'invalid_type',
            'fecha_publicacion': 'invalid-date',
            'contenido_texto': 'Short',  # Too short
            'es_opinion': 'yes',  # Should be boolean
        }),
        
        # Item with encoding issues
        ArticuloInItem({
            'url': 'https://example.com/article3',
            'titular': 'La programaciÃ³n en EspaÃ±a',
            'medio': 'Test\u200bMedia',  # Zero-width space
            'pais_publicacion': 'España',
            'tipo_medio': 'blog',
            'fecha_publicacion': '2024-01-16T15:45:00Z',
            'contenido_texto': 'ArtÃ­culo sobre cÃ³digo con problemas de codificaciÃ³n.',
            'autor': 'Dr. José Martínez, PhD <jose@example.com>',
        }),
    ]


def process_item_through_pipelines(item, validation_pipeline, cleaning_pipeline, spider):
    """Process an item through both pipelines and return the result."""
    try:
        # First, validate the item
        print(f"\n{'='*60}")
        print(f"Processing item: {item.get('url', 'No URL')}")
        print(f"{'='*60}")
        
        print("\n1. VALIDATION PIPELINE:")
        validated_item = validation_pipeline.process_item(item, spider)
        print("   ✓ Validation passed")
        
        # Then, clean the item
        print("\n2. CLEANING PIPELINE:")
        cleaned_item = cleaning_pipeline.process_item(validated_item, spider)
        print("   ✓ Cleaning completed")
        
        # Show the results
        adapter = ItemAdapter(cleaned_item)
        print("\n3. FINAL RESULT:")
        
        # Show key fields
        print(f"   - URL: {adapter.get('url')}")
        print(f"   - Title: {adapter.get('titular')}")
        print(f"   - Author: {adapter.get('autor')}")
        print(f"   - Publication Date: {adapter.get('fecha_publicacion')}")
        print(f"   - Tags: {adapter.get('etiquetas_fuente')}")
        print(f"   - Content Length: {len(adapter.get('contenido_texto', ''))}")
        print(f"   - HTML Present: {'Yes' if adapter.get('contenido_html') else 'No'}")
        
        return cleaned_item
        
    except ValidationError as e:
        print(f"\n❌ VALIDATION ERROR: {e}")
        if hasattr(e, 'field'):
            print(f"   Field: {e.field}")
        return None
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return None


def main():
    """Run the example."""
    # Create mock spider
    class MockSpider(Spider):
        name = 'example_spider'
    
    spider = MockSpider()
    
    # Create pipeline instances
    validation_pipeline = DataValidationPipeline()
    validation_pipeline.min_content_length = 50
    validation_pipeline.min_title_length = 5
    validation_pipeline.date_format = '%Y-%m-%dT%H:%M:%S'
    
    cleaning_pipeline = DataCleaningPipeline()
    cleaning_pipeline.strip_html = True
    cleaning_pipeline.normalize_whitespace = True
    cleaning_pipeline.remove_empty_lines = True
    cleaning_pipeline.standardize_quotes = True
    cleaning_pipeline.preserve_html_content = True
    
    # Process sample items
    items = create_sample_items()
    successful_items = []
    
    for i, item in enumerate(items, 1):
        print(f"\n\n{'#'*60}")
        print(f"EXAMPLE {i} OF {len(items)}")
        print(f"{'#'*60}")
        
        result = process_item_through_pipelines(
            item, validation_pipeline, cleaning_pipeline, spider
        )
        
        if result:
            successful_items.append(result)
    
    # Show statistics
    print(f"\n\n{'='*60}")
    print("FINAL STATISTICS")
    print(f"{'='*60}")
    print(f"\nValidation Pipeline Stats:")
    print(f"  - Total items: {validation_pipeline.validation_stats['total_items']}")
    print(f"  - Valid items: {validation_pipeline.validation_stats['valid_items']}")
    print(f"  - Invalid items: {validation_pipeline.validation_stats['invalid_items']}")
    print(f"  - Error types: {validation_pipeline.validation_stats['validation_errors']}")
    
    print(f"\nCleaning Pipeline Stats:")
    print(f"  - Total items: {cleaning_pipeline.cleaning_stats['total_items']}")
    print(f"  - Items cleaned: {cleaning_pipeline.cleaning_stats['items_cleaned']}")
    print(f"  - HTML stripped: {cleaning_pipeline.cleaning_stats['html_stripped']}")
    print(f"  - Text normalized: {cleaning_pipeline.cleaning_stats['text_normalized']}")
    print(f"  - URLs normalized: {cleaning_pipeline.cleaning_stats['urls_normalized']}")
    
    print(f"\nSuccess rate: {len(successful_items)}/{len(items)} items processed successfully")
    
    # Save successful items to file
    if successful_items:
        output_file = 'processed_items_example.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            items_data = []
            for item in successful_items:
                adapter = ItemAdapter(item)
                item_dict = adapter.asdict()
                # Remove HTML content for cleaner output
                if 'contenido_html' in item_dict:
                    item_dict['contenido_html'] = f"<HTML content: {len(item_dict['contenido_html'])} chars>"
                items_data.append(item_dict)
            
            json.dump(items_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Successful items saved to: {output_file}")


if __name__ == '__main__':
    main()
