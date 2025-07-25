"""
Test de performance básico para el módulo scraper.
Mide tiempos de procesamiento y uso de recursos.
"""

import time

import psutil
import pytest  # noqa: F401
from scraper_core.spiders.infobae_spider import InfobaeSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


class TestBasicPerformance:
    """Tests simples de rendimiento"""

    def test_single_page_performance(self):
        """Mide el tiempo de procesamiento de una página"""
        # Configuración para test
        settings = get_project_settings()
        settings.update(
            {
                "LOG_LEVEL": "ERROR",
                "HTTPCACHE_ENABLED": True,  # Usar cache para consistencia
                "CONCURRENT_REQUESTS": 1,
                "ITEM_PIPELINES": {
                    "scraper_core.pipelines.cleaning.DataCleaningPipeline": 200,
                    "scraper_core.pipelines.validation.DataValidationPipeline": 300,
                },
            }
        )

        # Métricas iniciales
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Ejecutar spider con una URL
        process = CrawlerProcess(settings)
        process.crawl(InfobaeSpider, limit_items=1)
        process.start()

        # Métricas finales
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Resultados
        elapsed_time = end_time - start_time
        memory_used = end_memory - start_memory

        print(f"\n📊 Resultados de Performance:")  # noqa: F541
        print(f"⏱️  Tiempo total: {elapsed_time:.2f} segundos")
        print(f"💾 Memoria utilizada: {memory_used:.2f} MB")

        # Verificaciones básicas
        assert elapsed_time < 30, "El procesamiento tardó más de 30 segundos"
        assert memory_used < 100, "Se usó más de 100MB de memoria"

    def test_pipeline_performance(self):
        """Mide el tiempo de cada pipeline individualmente"""
        from scraper_core.items import ArticuloInItem
        from scraper_core.pipelines.cleaning import DataCleaningPipeline
        from scraper_core.pipelines.validation import DataValidationPipeline

        # Item de prueba
        item = ArticuloInItem()
        item["url"] = "https://test.com/article"
        item["titular"] = "Test Article"
        item["contenido_texto"] = "Lorem ipsum " * 100
        item["medio"] = "Test Media"
        item["fecha_publicacion"] = "2024-01-01T00:00:00Z"

        # Test pipeline de limpieza
        cleaning_pipeline = DataCleaningPipeline()
        start = time.time()
        cleaned_item = cleaning_pipeline.process_item(item, None)
        cleaning_time = time.time() - start

        # Test pipeline de validación
        validation_pipeline = DataValidationPipeline()
        start = time.time()
        validated_item = validation_pipeline.process_item(cleaned_item, None)  # noqa: F841
        validation_time = time.time() - start

        print(f"\n⚡ Tiempos de Pipeline:")  # noqa: F541
        print(f"🧹 Limpieza: {cleaning_time * 1000:.2f} ms")
        print(f"✅ Validación: {validation_time * 1000:.2f} ms")

        # Verificaciones
        assert cleaning_time < 0.1, "Pipeline de limpieza muy lento"
        assert validation_time < 0.1, "Pipeline de validación muy lento"


if __name__ == "__main__":
    test = TestBasicPerformance()
    test.test_pipeline_performance()
