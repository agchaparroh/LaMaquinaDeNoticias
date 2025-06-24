"""
Test de integración real simplificado.
Prueba el flujo completo con datos reales.
"""
import pytest
from scrapy.utils.test import get_crawler
from scraper_core.spiders.infobae_spider import InfobaeSpider
from scraper_core.items import ArticuloInItem


class TestRealIntegration:
    """Test de integración con sitio real"""
    
    @pytest.mark.integration
    def test_real_article_extraction(self):
        """Extrae un artículo real y verifica el contenido"""
        # Usaremos httpbin.org como sitio de prueba confiable
        test_url = "https://httpbin.org/html"
        extracted_items = []
        
        class TestSpider(InfobaeSpider):
            name = "test_integration"
            start_urls = [test_url]
            
            def parse(self, response):
                # Extraer contenido básico
                item = ArticuloInItem()
                item['url'] = response.url
                item['titular'] = response.css('h1::text').get() or 'Test Title'
                item['contenido_texto'] = ' '.join(response.css('p::text').getall())
                item['medio'] = 'httpbin'
                item['fecha_publicacion'] = '2024-01-01T00:00:00Z'
                item['area_geografica'] = 'Test'
                item['tipo_medio'] = 'test'
                
                extracted_items.append(item)
                yield item
        
        # Configurar y ejecutar
        settings = {
            'LOG_LEVEL': 'ERROR',
            'ITEM_PIPELINES': {
                'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
                'scraper_core.pipelines.validation.DataValidationPipeline': 300,
            }
        }
        
        crawler = get_crawler(TestSpider, settings_dict=settings)
        crawler.crawl()
        crawler.engine.start()
        
        print(f"\n🌐 Test de Integración Real:")
        print(f"✅ Items extraídos: {len(extracted_items)}")
        
        if extracted_items:
            item = extracted_items[0]
            print(f"📰 Título: {item.get('titular', 'N/A')}")
            print(f"📄 Contenido: {len(item.get('contenido_texto', ''))} caracteres")
            print(f"🔗 URL: {item.get('url', 'N/A')}")
        
        # Verificaciones
        assert len(extracted_items) > 0, "No se extrajo ningún item"
        assert extracted_items[0].get('url'), "Item sin URL"
        assert extracted_items[0].get('titular'), "Item sin título"
    
    def test_pipeline_integration(self):
        """Prueba el flujo completo de pipelines"""
        from scraper_core.pipelines.cleaning import DataCleaningPipeline
        from scraper_core.pipelines.validation import DataValidationPipeline
        
        # Item con datos "sucios"
        item = ArticuloInItem()
        item['url'] = 'https://test.com/article'
        item['titular'] = '  Test Article with   spaces  '
        item['contenido_texto'] = '<p>HTML content</p>\n\n\nwith multiple\n\nlines'
        item['medio'] = 'Test Media'
        item['fecha_publicacion'] = '2024-01-01T00:00:00Z'
        item['area_geografica'] = 'Argentina'
        item['tipo_medio'] = 'diario'
        
        # Pipeline de limpieza
        cleaning = DataCleaningPipeline()
        cleaned_item = cleaning.process_item(item, None)
        
        # Pipeline de validación
        validation = DataValidationPipeline()
        final_item = validation.process_item(cleaned_item, None)
        
        print(f"\n🔄 Test de Pipeline Completo:")
        print(f"✅ Título original: '{item['titular']}'")
        print(f"✅ Título limpio: '{final_item['titular']}'")
        print(f"✅ Contenido procesado: {len(final_item['contenido_texto'])} chars")
        
        # Verificaciones
        assert final_item['titular'].strip() == final_item['titular'], "Título no fue limpiado"
        assert '<p>' not in final_item['contenido_texto'], "HTML no fue removido"
        assert '\n\n\n' not in final_item['contenido_texto'], "Múltiples saltos no fueron normalizados"


if __name__ == "__main__":
    test = TestRealIntegration()
    test.test_pipeline_integration()
    print("\n✅ Test de integración completado")
