"""
Test de concurrencia básico.
Verifica que múltiples spiders pueden ejecutarse sin conflictos.
"""
import threading
import time
import pytest
from scrapy import Spider
from scrapy.http import Request
from scrapy.utils.test import get_crawler
from scraper_core.items import ArticuloInItem


class TestSimpleConcurrency:
    """Tests de concurrencia básicos"""
    
    def test_multiple_spiders_basic(self):
        """Ejecuta 3 spiders dummy simultáneamente"""
        results = {'spider1': 0, 'spider2': 0, 'spider3': 0}
        errors = []
        
        class DummySpider(Spider):
            name = "dummy"
            
            def __init__(self, spider_id, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.spider_id = spider_id
                self.start_urls = ['http://httpbin.org/delay/1']
            
            def parse(self, response):
                # Simular procesamiento
                time.sleep(0.5)
                results[self.spider_id] += 1
                yield {'spider': self.spider_id, 'status': 'ok'}
        
        def run_spider(spider_id):
            try:
                crawler = get_crawler(DummySpider)
                crawler.crawl(spider_id=spider_id)
                crawler.engine.start()
            except Exception as e:
                errors.append(f"{spider_id}: {str(e)}")
        
        # Ejecutar spiders en threads
        threads = []
        for i in range(1, 4):
            spider_id = f'spider{i}'
            t = threading.Thread(target=run_spider, args=(spider_id,))
            threads.append(t)
            t.start()
        
        # Esperar a que terminen
        for t in threads:
            t.join(timeout=10)
        
        print(f"\n🔄 Resultados de Concurrencia:")
        print(f"✅ Spider 1: {results['spider1']} items")
        print(f"✅ Spider 2: {results['spider2']} items")
        print(f"✅ Spider 3: {results['spider3']} items")
        print(f"❌ Errores: {len(errors)}")
        
        # Verificaciones
        assert len(errors) == 0, f"Hubo errores: {errors}"
        assert all(count > 0 for count in results.values()), "Algún spider no procesó items"
    
    def test_concurrent_pipeline_processing(self):
        """Verifica que los pipelines manejen items concurrentes"""
        from scraper_core.pipelines.cleaning import DataCleaningPipeline
        from concurrent.futures import ThreadPoolExecutor
        
        pipeline = DataCleaningPipeline()
        items_processed = []
        
        def process_item(index):
            item = ArticuloInItem()
            item['url'] = f'https://test.com/article{index}'
            item['titular'] = f'Article {index}'
            item['contenido_texto'] = f'Content {index}'
            item['medio'] = 'Test'
            item['fecha_publicacion'] = '2024-01-01T00:00:00Z'
            
            processed = pipeline.process_item(item, None)
            items_processed.append(processed)
            return processed
        
        # Procesar 10 items concurrentemente
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_item, i) for i in range(10)]
            results = [f.result() for f in futures]
        
        print(f"\n⚡ Procesamiento Concurrente:")
        print(f"✅ Items procesados: {len(items_processed)}")
        print(f"✅ Sin errores de concurrencia")
        
        # Verificaciones
        assert len(items_processed) == 10, "No todos los items fueron procesados"
        assert all(item is not None for item in items_processed), "Algunos items son None"


if __name__ == "__main__":
    test = TestSimpleConcurrency()
    test.test_concurrent_pipeline_processing()
