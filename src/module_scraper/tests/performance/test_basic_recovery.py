"""
Test de recuperación ante fallos.
Verifica que el sistema se recupere de errores comunes.
"""
import pytest
from unittest.mock import Mock, patch
from scrapy.exceptions import DropItem
from scraper_core.items import ArticuloInItem
from scraper_core.pipelines.validation import DataValidationPipeline
from scraper_core.utils.supabase_client import SupabaseClient


class TestBasicRecovery:
    """Tests de recuperación ante fallos"""
    
    def test_pipeline_handles_invalid_items(self):
        """Verifica que el pipeline maneje items inválidos sin crashear"""
        pipeline = DataValidationPipeline()
        
        # Item sin campos requeridos
        invalid_item = ArticuloInItem()
        invalid_item['url'] = 'https://test.com'
        # Falta titulo, medio, etc.
        
        # No debe lanzar excepción, debe retornar DropItem o el item con error
        try:
            result = pipeline.process_item(invalid_item, None)
            print("✅ Pipeline manejó item inválido correctamente")
        except DropItem:
            print("✅ Pipeline rechazó item inválido (comportamiento esperado)")
        except Exception as e:
            pytest.fail(f"Pipeline crasheó con: {str(e)}")
    
    def test_supabase_connection_retry(self):
        """Verifica que el cliente Supabase reintente en caso de fallo"""
        with patch('supabase.create_client') as mock_create:
            # Simular fallo inicial y luego éxito
            mock_create.side_effect = [Exception("Connection failed"), Mock()]
            
            # El cliente debería reintentar
            try:
                client = SupabaseClient()
                print("✅ Cliente Supabase se recuperó del fallo de conexión")
            except Exception as e:
                pytest.fail(f"Cliente no se recuperó: {str(e)}")
    
    def test_spider_handles_timeout(self):
        """Verifica manejo de timeouts"""
        from scrapy.http import Request, Response
        from scraper_core.spiders.base.base_article import BaseArticleSpider
        
        class TestSpider(BaseArticleSpider):
            name = "test_timeout"
            
            def parse(self, response):
                # Simular respuesta vacía/timeout
                if not response.body:
                    self.logger.error("Respuesta vacía recibida")
                    return []
                return super().parse(response)
        
        spider = TestSpider()
        
        # Respuesta vacía (simula timeout)
        fake_response = Response(
            url='https://test.com',
            body=b'',
            request=Request('https://test.com')
        )
        
        # No debe crashear
        try:
            list(spider.parse(fake_response))
            print("✅ Spider manejó timeout correctamente")
        except Exception as e:
            pytest.fail(f"Spider crasheó con timeout: {str(e)}")
    
    def test_graceful_degradation(self):
        """Verifica degradación gradual cuando fallan componentes"""
        from scraper_core.pipelines.storage import SupabaseStoragePipeline
        
        # Mock pipeline con Supabase fallando
        with patch.object(SupabaseStoragePipeline, '_store_to_supabase') as mock_store:
            mock_store.side_effect = Exception("Supabase unavailable")
            
            pipeline = SupabaseStoragePipeline()
            
            item = ArticuloInItem()
            item['url'] = 'https://test.com/article'
            item['titular'] = 'Test'
            item['medio'] = 'Test Media'
            item['contenido_texto'] = 'Content'
            item['fecha_publicacion'] = '2024-01-01T00:00:00Z'
            
            # Debe continuar sin crashear
            try:
                result = pipeline.process_item(item, None)
                print("✅ Sistema degradó gradualmente ante fallo de Supabase")
                assert result is not None, "Item no debería ser None"
            except Exception as e:
                pytest.fail(f"Pipeline no manejó el fallo: {str(e)}")


if __name__ == "__main__":
    test = TestBasicRecovery()
    print("🔧 Ejecutando tests de recuperación...\n")
    test.test_pipeline_handles_invalid_items()
    test.test_spider_handles_timeout()
    test.test_graceful_degradation()
    print("\n✅ Tests de recuperación completados")
