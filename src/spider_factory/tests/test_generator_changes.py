#!/usr/bin/env python3
"""
Test the updated generator with new mandatory fields
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from generator import SpiderGenerator
from analyzer import AnalysisResult, AnalysisStrategy, SiteSelectors


def test_generator_update():
    """Test the updated generator with mandatory fields"""
    
    # Create test analysis result
    test_analysis = AnalysisResult(
        url="https://example.com/news",
        domain="example.com",
        strategy=AnalysisStrategy.SCRAPING,
        confidence=0.85,
        selectors=SiteSelectors(
            title="h1.article-title",
            content="div.article-content",
            date="time.published",
            author="span.author"
        ),
        needs_javascript=False
    )
    
    # Create generator with correct template path
    template_dir = Path(__file__).parent / "templates" / "spiders"
    generator = SpiderGenerator(templates_dir=str(template_dir))
    
    # Test generation with new parameters
    print("Testing spider generation with mandatory fields...")
    
    try:
        spider_code = generator.generate_spider(
            analysis=test_analysis,
            medio="Test News",
            seccion="Politics",
            area_geografica="ESPAÑA",
            tipo_medio="diario",
            frecuencia_minutos=30,
            additional_config={
                "excluded_urls": ["/tags/*", "/author/*"],
                "pagination_enabled": True
            }
        )
        
        print("✓ Spider generated successfully!")
        
        # Check that mandatory fields are in the generated code
        mandatory_checks = [
            ('medio: "Test News"', "Medio field"),
            ('seccion: "Politics"', "Sección field"),
            ('area_geografica: "ESPAÑA"', "Área geográfica field"),
            ('tipo_medio: "diario"', "Tipo medio field"),
            ('frecuencia_minutos: 30', "Frecuencia field"),
            ('name = "test_news_politics"', "Spider name format"),
            ('titular', "Titular field (not titulo)"),
        ]
        
        print("\nChecking mandatory fields in generated code:")
        for check_str, field_name in mandatory_checks:
            if check_str in spider_code:
                print(f"✓ {field_name} found")
            else:
                print(f"✗ {field_name} NOT found - looking for: {check_str}")
        
        # Preview spider
        print("\nSpider preview:")
        print("=" * 80)
        preview = generator.preview_spider(
            analysis=test_analysis,
            medio="Test News",
            seccion="Politics",
            area_geografica="ESPAÑA",
            tipo_medio="diario",
            frecuencia_minutos=30,
            max_lines=25
        )
        print(preview)
        
        # Test output directory
        output_path = Path("/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/module_scraper/scraper_core/spiders/")
        print(f"\nOutput directory exists: {output_path.exists()}")
        
    except Exception as e:
        print(f"✗ Error generating spider: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_generator_update()