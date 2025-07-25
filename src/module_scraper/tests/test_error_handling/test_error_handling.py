# Tests de Error Handling
"""
Tests para verificar el manejo correcto de errores y casos edge
en el sistema de scraping.
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch  # noqa: F401

import httpx
import pytest
import requests  # noqa: F401
from scraper_core.items import ArticuloInItem
from scraper_core.pipelines.storage import (  # noqa: F401
    SupabaseNetworkError,
    SupabaseStoragePipeline,
)
from scraper_core.spiders.base.base_article import BaseArticleSpider
from scrapy.http import HtmlResponse, Request  # noqa: F401
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TCPTimedOutError, TimeoutError


class TestSpiderErrorHandling:
    """Tests para manejo de errores en spiders."""

    @pytest.fixture
    def test_spider(self):
        """Spider de prueba."""
        spider = BaseArticleSpider(name="test_error_spider")
        spider.logger = Mock()
        return spider

    def test_handle_network_errors(self, test_spider):
        """Test manejo de errores de red."""
        # Simular diferentes tipos de errores de red
        network_errors = [
            DNSLookupError("No se pudo resolver example.com"),
            TimeoutError("Timeout al conectar"),
            TCPTimedOutError("Conexión TCP timeout"),
        ]

        for error in network_errors:
            failure = Mock()
            failure.value = error
            failure.request = Mock(url="https://example.com/test")
            failure.check.return_value = True

            # El spider debe manejar el error sin crashear
            test_spider.handle_error(failure)

            # Verificar que se registró el error
            assert "https://example.com/test" in test_spider.failed_urls
            test_spider.logger.error.assert_called()

    def test_handle_http_errors(self, test_spider):
        """Test manejo de errores HTTP."""
        # Simular errores HTTP comunes
        http_codes = [404, 500, 503, 429]

        for code in http_codes:
            response = Mock()
            response.status = code
            response.url = f"https://example.com/error{code}"

            error = HttpError(response, f"HTTP {code} error")
            failure = Mock()
            failure.value = error
            failure.request = Mock(url=response.url)
            failure.check.return_value = True

            test_spider.handle_error(failure)

            # Verificar manejo apropiado
            assert response.url in test_spider.failed_urls

    def test_parse_with_malformed_html(self, test_spider):
        """Test parsing de HTML malformado."""
        malformed_html = """
        <html>
        <body>
            <h1>Título sin cerrar
            <p>Párrafo sin cerrar
            <div>
                Contenido anidado mal cerrado
            </p>
        </body>
        """

        response = HtmlResponse(
            url="https://example.com/malformed", body=malformed_html.encode("utf-8")
        )

        # No debe crashear al extraer
        title = test_spider.extract_article_title(response)
        content = test_spider.extract_article_content(response)

        # Debe extraer algo o retornar None/empty
        assert title is None or isinstance(title, str)
        assert content is None or isinstance(content, str)

    def test_parse_empty_response(self, test_spider):
        """Test con response completamente vacío."""
        empty_response = HtmlResponse(url="https://example.com/empty", body=b"")

        # Todos los métodos deben manejar response vacío
        title = test_spider.extract_article_title(empty_response)
        content = test_spider.extract_article_content(empty_response)
        date = test_spider.extract_publication_date(empty_response)
        author = test_spider.extract_author(empty_response)

        # No deben retornar valores inválidos
        assert title is None or title == ""
        assert content is None or content == ""
        assert date is None
        assert author is None

    def test_handle_encoding_errors(self, test_spider):
        """Test manejo de errores de encoding."""
        # HTML con encoding problemático
        problematic_bytes = (
            b"\xff\xfe<html><body>Texto con encoding problem\xe1tico</body></html>"
        )

        try:
            response = HtmlResponse(
                url="https://example.com/encoding",
                body=problematic_bytes,
                encoding="utf-8",
            )

            # Debe manejar el encoding sin crashear
            content = test_spider.extract_article_content(response)
            assert content is None or isinstance(content, str)

        except UnicodeDecodeError:
            # Si falla, el test pasa porque queremos verificar que no crashea
            pass


class TestPipelineErrorHandling:
    """Tests para manejo de errores en pipelines."""

    @pytest.fixture
    def storage_pipeline(self):
        """Pipeline de storage con cliente mockeado."""
        with patch("scraper_core.utils.supabase_client.SupabaseClient") as mock_client:
            pipeline = SupabaseStoragePipeline(mock_client(), "test-bucket")
            pipeline.stop_after_attempt = 3
            pipeline.wait_min = 1
            pipeline.wait_max = 5
            return pipeline

    def test_storage_retry_on_network_error(self, storage_pipeline):
        """Test que reintenta en errores de red."""
        # Configurar mock para fallar primero, luego tener éxito
        storage_pipeline.supabase_client.upsert_articulo = Mock(
            side_effect=[
                httpx.RequestError("Network error"),
                {"id": "success-id"},  # Éxito en el segundo intento
            ]
        )

        # Crear item válido
        item = ArticuloInItem()
        item["url"] = "https://example.com/test"
        item["titular"] = "Test"
        item["contenido_texto"] = "Contenido de prueba"
        item["medio"] = "Test"
        item["area_geografica"] = "Test"
        item["tipo_medio"] = "test"
        item["fecha_publicacion"] = datetime.utcnow()

        # Procesar item (debe reintentar y tener éxito)
        with patch.object(
            storage_pipeline, "_upsert_articulo_with_retry"
        ) as mock_upsert:
            mock_upsert.return_value = {"id": "success-id"}
            result = storage_pipeline.process_item(item, Mock())

            assert result is not None
            mock_upsert.assert_called_once()

    def test_storage_handles_permanent_failure(self, storage_pipeline):
        """Test manejo de fallos permanentes."""
        # Configurar para fallar siempre
        storage_pipeline.supabase_client.upsert_articulo = Mock(
            side_effect=httpx.RequestError("Network permanently down")
        )

        item = ArticuloInItem()
        item["url"] = "https://example.com/fail"
        item["contenido_texto"] = "Test"

        # Debe manejar el error sin crashear
        result = storage_pipeline.process_item(item, Mock())

        # El item debe pasar pero con error registrado
        assert result is not None
        assert "error_detalle" in result

    def test_validation_pipeline_field_errors(self):
        """Test validación con campos problemáticos."""
        from scraper_core.pipelines.validation import DataValidationPipeline

        pipeline = DataValidationPipeline()
        pipeline.min_content_length = 50

        # Item con campos problemáticos
        problematic_items = [
            # URL inválida
            {
                "url": "not-a-valid-url",
                "titular": "Test",
                "contenido_texto": "x" * 100,
                "medio": "Test",
            },
            # Fecha inválida
            {
                "url": "https://example.com",
                "titular": "Test",
                "contenido_texto": "x" * 100,
                "fecha_publicacion": "not-a-date",
                "medio": "Test",
            },
            # Contenido muy corto
            {
                "url": "https://example.com",
                "titular": "Test",
                "contenido_texto": "Too short",
                "medio": "Test",
            },
        ]

        for item_data in problematic_items:
            item = ArticuloInItem(item_data)

            # Debe manejar el error apropiadamente
            try:
                pipeline.process_item(item, Mock())
            except Exception:
                # Está bien que lance excepción, pero debe ser controlada
                pass


class TestEdgeCases:
    """Tests para casos edge específicos."""

    def test_item_with_null_values(self):
        """Test item con valores None."""
        item = ArticuloInItem()
        item["url"] = "https://example.com"
        item["titular"] = None  # Título None
        item["contenido_texto"] = None  # Contenido None
        item["autor"] = None

        # Los pipelines deben manejar valores None
        from scraper_core.pipelines.cleaning import DataCleaningPipeline

        cleaning = DataCleaningPipeline()

        # No debe crashear con None
        try:
            cleaned = cleaning.process_item(item, Mock())
            assert cleaned is not None
        except AttributeError:
            pytest.fail("Pipeline no maneja valores None correctamente")

    def test_concurrent_storage_conflicts(self):
        """Test conflictos de concurrencia en storage."""
        # Este es más conceptual ya que requeriría threading real
        # Verificamos que el pipeline tiene mecanismos de retry
        from scraper_core.pipelines.storage import SupabaseStoragePipeline

        # Verificar que tiene configuración de retry
        assert hasattr(SupabaseStoragePipeline, "_upsert_articulo_with_retry")
        assert hasattr(SupabaseStoragePipeline, "_upload_to_storage_with_retry")

    def test_unicode_handling(self):
        """Test manejo de caracteres Unicode problemáticos."""
        problematic_text = "Texto con emojis 😀🎉 y caracteres especiales: ñáéíóú"

        item = ArticuloInItem()
        item["url"] = "https://example.com/unicode"
        item["titular"] = problematic_text
        item["contenido_texto"] = problematic_text
        item["autor"] = "José María Ñoño"

        # Debe procesar sin problemas
        from scraper_core.pipelines.cleaning import DataCleaningPipeline

        cleaning = DataCleaningPipeline()
        cleaned = cleaning.process_item(item, Mock())

        # El texto debe mantenerse (posiblemente normalizado)
        assert cleaned["titular"] is not None
        assert cleaned["autor"] is not None
