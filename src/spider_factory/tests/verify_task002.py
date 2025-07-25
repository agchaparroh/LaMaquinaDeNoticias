#!/usr/bin/env python3
"""
Verify TASK-002 completion - Template refactoring
"""

import os  # noqa: F401
from pathlib import Path


def check_template_updates():
    """Check all templates have been updated correctly"""

    base_dir = Path(__file__).parent
    template_dir = base_dir / "templates" / "spiders"

    print("TASK-002: Template Refactoring Verification")
    print("=" * 50)

    # Check if templates exist
    templates = {
        "base_spider.j2": "Base template with common configuration",
        "rss_spider.j2": "RSS spider template",
        "scraping_spider.j2": "Traditional scraping spider template",
        "playwright_spider.j2": "JavaScript-heavy sites spider template",
    }

    print("\n1. Checking template files exist:")
    for template, desc in templates.items():
        path = template_dir / template
        exists = path.exists()
        print(f"   {'✓' if exists else '✗'} {template} - {desc}")

    # Check mandatory fields in templates
    print("\n2. Checking mandatory fields in templates:")

    mandatory_fields = [
        "medio",
        "seccion",
        "area_geografica",
        "tipo_medio",
        "frecuencia_minutos",
        "generation_date",
        "titular",  # Not "titulo"
    ]

    for template in templates:
        path = template_dir / template
        if path.exists():
            content = path.read_text()
            print(f"\n   {template}:")
            for field in mandatory_fields:
                if field in content:
                    print(f"      ✓ {field}")
                else:
                    print(f"      ✗ {field} NOT FOUND")

    # Check generator.py updates
    print("\n3. Checking generator.py updates:")
    generator_path = base_dir / "src" / "generator.py"

    if generator_path.exists():
        content = generator_path.read_text()

        checks = [
            ("medio: str,", "medio parameter"),
            ("seccion: str,", "seccion parameter"),
            ("area_geografica: str,", "area_geografica parameter"),
            ("tipo_medio: str,", "tipo_medio parameter"),
            ("frecuencia_minutos: int", "frecuencia_minutos parameter"),
            ('spider_name = f"{medio}_{seccion}"', "automatic spider_name generation"),
            ("/src/module_scraper/scraper_core/spiders/", "output directory"),
            ("generation_date", "generation_date in context"),
        ]

        for check_str, desc in checks:
            if check_str in content:
                print(f"   ✓ {desc}")
            else:
                print(f"   ✗ {desc} NOT FOUND")

    # Check _is_section_article method
    print("\n4. Checking _is_section_article method in templates:")
    for template in ["scraping_spider.j2", "playwright_spider.j2"]:
        path = template_dir / template
        if path.exists():
            content = path.read_text()
            if "_is_section_article" in content:
                print(f"   ✓ {template} has _is_section_article method")
            else:
                print(f"   ✗ {template} missing _is_section_article method")

    print("\n" + "=" * 50)
    print("TASK-002 Verification Complete")


if __name__ == "__main__":
    check_template_updates()
