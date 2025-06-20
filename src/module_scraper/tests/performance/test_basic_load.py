"""
Test de carga básico.
Verifica límites del sistema con múltiples requests.
"""
import time
import pytest
from concurrent.futures import ThreadPoolExecutor
from scraper_core.items import ArticuloInItem
from scraper_core.pipelines.cleaning import DataCleaningPipeline
from scraper_core.pipelines.validation import DataValidationPipeline


class TestBasicLoad:
    """Tests de carga simples"""
    
    def test_pipeline_load(self):
        """Procesa muchos items para verificar estabilidad"""
        cleaning = DataCleaningPipeline()
        validation = DataValidationPipeline()
        
        num_items = 100
        start_time = time.time()
        errors = []
        
        for i in range(num_items):
            item = ArticuloInItem()
            item['url'] = f'https://test.com/article{i}'
            item['titular'] = f'Article {i} - ' + 'Lorem ipsum ' * 10
            item['contenido_texto'] = 'Content ' * 100
            item['medio'] = 'Test Media'
            item['fecha_publicacion'] = '2024-01-01T00:00:00Z'
            item['pais_publicacion'] = 'Test'
            item['tipo_medio'] = 'test'
            
            try:
                # Procesar por ambos pipelines
                cleaned = cleaning.process_item(item, None)
                validated = validation.process_item(cleaned, None)
            except Exception as e:
                errors.append(f"Item {i}: {str(e)}")
        
        elapsed_time = time.time() - start_time
        items_per_second = num_items / elapsed_time
        
        print(f"\n📊 Test de Carga - Pipeline:")
        print(f"✅ Items procesados: {num_items}")
        print(f"⏱️  Tiempo total: {elapsed_time:.2f} segundos")
        print(f"⚡ Velocidad: {items_per_second:.2f} items/segundo")
        print(f"❌ Errores: {len(errors)}")
        
        # Verificaciones
        assert len(errors) == 0, f"Hubo {len(errors)} errores durante el procesamiento"
        assert items_per_second > 10, "Procesamiento muy lento (menos de 10 items/seg)"
    
    def test_concurrent_load(self):
        """Test de carga con procesamiento concurrente"""
        cleaning = DataCleaningPipeline()
        results = {'processed': 0, 'errors': []}
        
        def process_batch(batch_id, batch_size=10):
            local_processed = 0
            for i in range(batch_size):
                item = ArticuloInItem()
                item['url'] = f'https://test.com/batch{batch_id}/article{i}'
                item['titular'] = f'Batch {batch_id} Article {i}'
                item['contenido_texto'] = 'Content ' * 50
                item['medio'] = 'Test'
                item['fecha_publicacion'] = '2024-01-01T00:00:00Z'
                
                try:
                    cleaning.process_item(item, None)
                    local_processed += 1
                except Exception as e:
                    results['errors'].append(f"Batch {batch_id}, Item {i}: {str(e)}")
            
            results['processed'] += local_processed
        
        # Ejecutar 10 batches concurrentemente
        num_batches = 10
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_batch, i) for i in range(num_batches)]
            for future in futures:
                future.result()
        
        elapsed_time = time.time() - start_time
        total_items = num_batches * 10
        
        print(f"\n🔄 Test de Carga Concurrente:")
        print(f"✅ Items procesados: {results['processed']}/{total_items}")
        print(f"⏱️  Tiempo total: {elapsed_time:.2f} segundos")
        print(f"⚡ Throughput: {results['processed']/elapsed_time:.2f} items/segundo")
        print(f"❌ Errores: {len(results['errors'])}")
        
        # Verificaciones
        assert results['processed'] == total_items, "No todos los items fueron procesados"
        assert len(results['errors']) == 0, f"Errores encontrados: {results['errors'][:5]}"
    
    def test_memory_stability(self):
        """Verifica que no haya memory leaks con muchos items"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        cleaning = DataCleaningPipeline()
        
        # Procesar muchos items
        for i in range(1000):
            item = ArticuloInItem()
            item['url'] = f'https://test.com/article{i}'
            item['titular'] = 'Test ' * 100  # Título largo
            item['contenido_texto'] = 'Content ' * 1000  # Contenido muy largo
            item['medio'] = 'Test'
            item['fecha_publicacion'] = '2024-01-01T00:00:00Z'
            
            cleaned = cleaning.process_item(item, None)
            
            # Forzar garbage collection cada 100 items
            if i % 100 == 0:
                gc.collect()
        
        # Forzar limpieza final
        gc.collect()
        time.sleep(0.5)  # Dar tiempo al GC
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"\n💾 Test de Estabilidad de Memoria:")
        print(f"📊 Memoria inicial: {initial_memory:.2f} MB")
        print(f"📊 Memoria final: {final_memory:.2f} MB")
        print(f"📈 Incremento: {memory_increase:.2f} MB")
        
        # Verificación - no debe crecer más de 50MB
        assert memory_increase < 50, f"Posible memory leak: {memory_increase:.2f} MB de incremento"


if __name__ == "__main__":
    test = TestBasicLoad()
    print("🚀 Ejecutando tests de carga...\n")
    test.test_pipeline_load()
    test.test_concurrent_load()
    test.test_memory_stability()
    print("\n✅ Tests de carga completados")
