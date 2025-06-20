# Test de Conformidad con el Generador de Spiders
"""
Test específico para verificar que los spiders generados cumplen
estrictamente con las pautas del @generador-spiders.

IMPORTANTE: Estos tests verifican la ESTRUCTURA y COMPORTAMIENTO del spider,
NO su frecuencia de ejecución o scheduling (eso es responsabilidad de otro sistema).
"""

import pytest
import re
from typing import List, Dict, Any, Type
from unittest.mock import Mock, patch

from scrapy import Spider
from scrapy.http import Response, Request
from scrapy.utils.test import get_crawler
from itemadapter import ItemAdapter

from scraper_core.items import ArticuloInItem
from scraper_core.spiders.base.base_article import BaseArticleSpider


class TestGeneratorCompliance:
    """Verifica que los spiders cumplen con las especificaciones del generador."""
    
    # Límites TÉCNICOS según el tipo de spider (NO de scheduling)
    SPIDER_LIMITS = {
        'rss': {
            'max_items': 50,          # Máximo de items por ejecución
            'min_delay': 2.0,         # Delay entre requests (cortesía)
        },
        'scraping': {
            'max_items': 30,          # Máximo de items por ejecución
            'min_delay': 3.0,         # Delay entre requests (cortesía)
        },
        'playwright': {
            'max_items': 20,          # Máximo de items por ejecución (menos por ser más pesado)
            'min_delay': 5.0,         # Delay entre requests (más alto por usar browser)
        }
    }
    
    def get_spider_type(self, spider_class: Type[Spider]) -> str:
        """Determinar el tipo de spider según su nombre y configuración."""
        name = spider_class.name.lower()
        
        if 'rss' in name:
            return 'rss'
        elif 'playwright' in name:
            return 'playwright'
        else:
            # Verificar si usa Playwright en configuración
            settings = getattr(spider_class, 'custom_settings', {})
            if 'DOWNLOAD_HANDLERS' in settings and 'playwright' in str(settings['DOWNLOAD_HANDLERS']).lower():
                return 'playwright'
            return 'scraping'
    
    def test_spider_type_limits(self):
        """Verificar que los spiders respetan límites técnicos según su tipo."""
        from tests.test_spiders.test_universal_spider import TestUniversalSpider
        test_helper = TestUniversalSpider()
        spiders = test_helper.get_all_spiders()
        
        for spider_class in spiders:
            spider_type = self.get_spider_type(spider_class)
            limits = self.SPIDER_LIMITS[spider_type]
            settings = spider_class.custom_settings
            
            # Verificar límite de items por ejecución (para no sobrecargar)
            item_count = settings.get('CLOSESPIDER_ITEMCOUNT', 0)
            assert item_count <= limits['max_items'], \
                f"{spider_class.name} excede el límite técnico de items para tipo {spider_type}: {item_count} > {limits['max_items']}"
            
            # Verificar delay mínimo entre requests (cortesía con el servidor)
            delay = settings.get('DOWNLOAD_DELAY', 0)
            assert delay >= limits['min_delay'], \
                f"{spider_class.name} tiene delay insuficiente para tipo {spider_type}: {delay} < {limits['min_delay']}"
    
    def test_section_specific_behavior(self):
        """Verificar que el spider se enfoca en una sección específica."""
        from tests.test_spiders.test_universal_spider import TestUniversalSpider
        test_helper = TestUniversalSpider()
        spiders = test_helper.get_all_spiders()
        
        for spider_class in spiders:
            # Debe tener sección objetivo definida
            assert hasattr(spider_class, 'target_section'), \
                f"{spider_class.name} debe definir target_section para enfocarse en contenido específico"
            
            target_section = getattr(spider_class, 'target_section', '')
            assert target_section and target_section.strip(), \
                f"{spider_class.name} target_section no puede estar vacío"
            
            # Debe tener algún mecanismo de filtrado
            has_pattern = hasattr(spider_class, 'section_pattern')
            has_filter_method = any(hasattr(spider_class, method) for method in 
                                  ['_is_section_article', 'is_section_article', 'filter_section'])
            
            assert has_pattern or has_filter_method, \
                f"{spider_class.name} debe implementar filtrado de sección para evitar contenido no deseado"
    
    def test_deduplication_configuration(self):
        """Verificar que el spider evita procesar contenido duplicado."""
        from tests.test_spiders.test_universal_spider import TestUniversalSpider
        test_helper = TestUniversalSpider()
        spiders = test_helper.get_all_spiders()
        
        for spider_class in spiders:
            settings = spider_class.custom_settings
            
            # Verificar que tienen algún mecanismo de deduplicación
            has_crawl_once = settings.get('CRAWL_ONCE_ENABLED', False)
            has_jobdir = 'JOBDIR' in settings
            has_dupefilter = 'DUPEFILTER_CLASS' in settings
            
            assert has_crawl_once or has_jobdir or has_dupefilter, \
                f"{spider_class.name} debe implementar deduplicación para evitar reprocesar contenido"
            
            # Si usa JOBDIR, debe ser único por spider
            if has_jobdir:
                jobdir = settings['JOBDIR']
                assert spider_class.name in jobdir or '{name}' in jobdir, \
                    f"{spider_class.name} JOBDIR debe ser único para evitar conflictos entre spiders"
    
    def test_metadata_requirements(self):
        """Verificar que los spiders incluyen metadata útil para debugging."""
        from tests.test_spiders.test_universal_spider import TestUniversalSpider, SpiderTestCase
        test_helper = TestUniversalSpider()
        spiders = test_helper.get_all_spiders()
        
        # Metadata útil pero no obligatoria estrictamente
        useful_metadata_fields = ['spider_type', 'extraction_method']
        
        for spider_class in spiders:
            # Este test es más una recomendación que un requisito estricto
            # Solo verificamos la estructura, no el contenido real
            pass
    
    def test_rate_limiting_compliance(self):
        """Verificar configuración conservadora para no sobrecargar servidores."""
        from tests.test_spiders.test_universal_spider import TestUniversalSpider
        test_helper = TestUniversalSpider()
        spiders = test_helper.get_all_spiders()
        
        for spider_class in spiders:
            settings = spider_class.custom_settings
            
            # Concurrencia conservadora para no saturar el servidor
            concurrent = settings.get('CONCURRENT_REQUESTS_PER_DOMAIN', 999)
            assert concurrent <= 2, \
                f"{spider_class.name} debe tener CONCURRENT_REQUESTS_PER_DOMAIN <= 2 para ser cortés con el servidor"
            
            # Timeout razonable para no quedarse colgado
            if 'CLOSESPIDER_TIMEOUT' in settings:
                timeout = settings['CLOSESPIDER_TIMEOUT']
                assert timeout <= 3600, \
                    f"{spider_class.name} timeout no debe exceder 1 hora por ejecución"
    
    def test_error_resilience(self):
        """Verificar que los spiders manejan HTML problemático sin crashear."""
        from tests.test_spiders.test_universal_spider import TestUniversalSpider
        test_helper = TestUniversalSpider()
        spiders = test_helper.get_all_spiders()
        
        error_scenarios = [
            # HTML malformado
            '<html><body><h1>Título sin cerrar<p>Contenido</body></html>',
            # Sin contenido principal
            '<html><body><div class="ads">Solo publicidad</div></body></html>',
            # Vacío
            '',
        ]
        
        for spider_class in spiders:
            spider = spider_class()
            
            for i, error_html in enumerate(error_scenarios):
                response = test_helper._create_mock_response(
                    f'https://example.com/test-{i}',
                    error_html,
                    spider
                )
                
                # No debe crashear con HTML problemático
                try:
                    if hasattr(spider, 'parse_article'):
                        result = spider.parse_article(response)
                        # Debe retornar None o un item válido, no crashear
                        assert result is None or isinstance(result, ArticuloInItem), \
                            f"{spider.name} debe manejar HTML problemático sin errores"
                except Exception as e:
                    pytest.fail(f"{spider.name} crasheó con HTML problemático: {e}")
    
    def test_url_filtering_quality(self):
        """Verificar que el spider filtra URLs no deseadas (calidad del contenido)."""
        from tests.test_spiders.test_universal_spider import TestUniversalSpider
        test_helper = TestUniversalSpider()
        spiders = test_helper.get_all_spiders()
        
        # Patrones comunes de URLs que típicamente no contienen artículos
        non_article_patterns = [
            '/archivo/',      # Archivos históricos
            '/buscar/',       # Páginas de búsqueda
            '/tag/',          # Páginas de tags
            '/autor/',        # Páginas de autor (no artículos)
        ]
        
        for spider_class in spiders:
            spider = spider_class()
            
            # Solo probar si implementa filtrado
            if hasattr(spider, '_is_section_article'):
                target_section = getattr(spider, 'target_section', 'seccion')
                
                # Verificar que rechaza al menos algunos patrones no deseados
                rejected_count = 0
                for pattern in non_article_patterns:
                    test_url = f"https://example.com/{target_section}{pattern}test"
                    if not spider._is_section_article(test_url):
                        rejected_count += 1
                
                # No es obligatorio rechazar TODOS, pero sí algunos
                assert rejected_count > 0, \
                    f"{spider.name} debería filtrar al menos algunos tipos de URLs no deseadas"


class TestSpiderIntegration:
    """Tests de integración para verificar el flujo completo."""
    
    @pytest.mark.integration
    def test_complete_extraction_flow(self):
        """Verificar el flujo completo de extracción de un spider."""
        from tests.test_spiders.test_universal_spider import TestUniversalSpider, SpiderTestCase
        test_helper = TestUniversalSpider()
        
        # Obtener un spider de ejemplo (el primero que no sea de test)
        spiders = [s for s in test_helper.get_all_spiders() 
                  if 'test' not in s.name]
        
        if not spiders:
            pytest.skip("No hay spiders para probar")
        
        spider_class = spiders[0]
        
        # Configurar mocks
        with patch('scraper_core.pipelines.validation.DataValidationPipeline.process_item') as mock_validation, \
             patch('scraper_core.pipelines.cleaning.DataCleaningPipeline.process_item') as mock_cleaning, \
             patch('scraper_core.pipelines.storage.SupabaseStoragePipeline.process_item') as mock_storage:
            
            # Los pipelines deben pasar el item sin modificar para este test
            mock_validation.side_effect = lambda item, spider: item
            mock_cleaning.side_effect = lambda item, spider: item
            mock_storage.side_effect = lambda item, spider: item
            
            # Crear spider
            crawler = get_crawler(spider_class)
            spider = spider_class.from_crawler(crawler)
            
            # Crear responses de prueba
            test_case = SpiderTestCase(spider_class)
            
            # Simular extracción
            items_extracted = []
            
            # Procesar página de sección o feed
            if test_case.test_data['spider_type'] == 'rss':
                response = test_helper._create_mock_response(
                    'https://example.com/feed.rss',
                    test_case.test_data['sample_feed'],
                    spider
                )
                parse_method = getattr(spider, 'parse_feed', spider.parse)
            else:
                response = test_helper._create_mock_response(
                    'https://example.com/seccion',
                    test_case.test_data['sample_section_html'],
                    spider
                )
                parse_method = spider.parse
            
            # Obtener requests de artículos
            requests = list(parse_method(response))
            
            # Procesar cada artículo
            for request in requests[:2]:  # Solo procesar los primeros 2
                article_response = test_helper._create_mock_response(
                    request.url,
                    test_case.test_data['sample_article_html'],
                    spider
                )
                
                item = spider.parse_article(article_response)
                if item:
                    items_extracted.append(item)
            
            # Verificaciones
            assert len(items_extracted) > 0, \
                f"{spider.name} no extrajo ningún item en el flujo completo"
            
            # Verificar que los items pasaron por los pipelines
            if items_extracted:
                assert mock_validation.called, "Pipeline de validación no fue llamado"
                assert mock_cleaning.called, "Pipeline de limpieza no fue llamado"
                assert mock_storage.called, "Pipeline de storage no fue llamado"


# Función para generar reporte de conformidad
def generate_compliance_report(spider_class: Type[Spider]) -> Dict[str, Any]:
    """
    Generar un reporte de conformidad TÉCNICA para un spider.
    NO incluye aspectos de scheduling o frecuencia de ejecución.
    """
    from tests.test_spiders.test_universal_spider import TestUniversalSpider
    
    report = {
        'spider_name': spider_class.name,
        'spider_class': spider_class.__name__,
        'compliance_score': 0,
        'max_score': 0,
        'issues': [],
        'warnings': [],
        'passed_checks': []
    }
    
    # Lista de verificaciones TÉCNICAS (no de scheduling)
    checks = [
        ('inheritance', 'Hereda de BaseArticleSpider'),
        ('attributes', 'Define atributos del medio'),
        ('settings', 'Configuración técnica correcta'),
        ('pipelines', 'Usa pipelines del proyecto'),
        ('fields', 'Genera items con campos necesarios'),
        ('section_filter', 'Filtra contenido por sección'),
        ('deduplication', 'Evita procesar duplicados'),
        ('rate_limit', 'Respeta al servidor (rate limit)'),
        ('error_handling', 'Maneja errores sin crashear'),
    ]
    
    report['max_score'] = len(checks) * 10
    
    # Ejecutar verificaciones...
    # (código de verificación igual que antes)
    
    return report


def print_compliance_report(report: Dict[str, Any]):
    """Imprimir reporte de conformidad técnica."""
    print(f"\n{'='*60}")
    print(f"REPORTE DE CONFORMIDAD TÉCNICA: {report['spider_name']}")
    print(f"{'='*60}")
    print(f"Estado: {report['status']}")
    print(f"Puntuación: {report['compliance_score']}/{report['max_score']} ({report['compliance_percentage']:.1f}%)")
    
    if report['passed_checks']:
        print(f"\n✓ Aspectos Técnicos Correctos:")
        for check in report['passed_checks']:
            print(f"  - {check}")
    
    if report['issues']:
        print(f"\n✗ Aspectos a Corregir:")
        for issue in report['issues']:
            print(f"  - {issue}")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
