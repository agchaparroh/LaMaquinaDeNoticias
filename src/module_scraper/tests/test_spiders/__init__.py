# Tests para Spiders - La Máquina de Noticias
"""
Módulo de tests para verificar que los spiders cumplen con las
especificaciones del proyecto y del generador de spiders.

Tests incluidos:
- test_universal_spider.py: Test universal para todos los spiders
- test_generator_compliance.py: Verificación de conformidad con @generador-spiders
- test_base_article.py: Tests para la clase base BaseArticleSpider
"""

# Hacer disponibles las clases principales para importación fácil
from .test_universal_spider import (
    TestUniversalSpider,
    SpiderTestCase,
    validate_spider
)

from .test_generator_compliance import (
    TestGeneratorCompliance,
    TestSpiderIntegration,
    generate_compliance_report,
    print_compliance_report
)

__all__ = [
    'TestUniversalSpider',
    'SpiderTestCase',
    'validate_spider',
    'TestGeneratorCompliance', 
    'TestSpiderIntegration',
    'generate_compliance_report',
    'print_compliance_report'
]
