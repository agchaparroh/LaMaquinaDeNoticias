"""
Tests unitarios para models.py
"""

import pytest
from pydantic import ValidationError

from src.config import AREAS_GEOGRAFICAS_VALIDAS  # noqa: F401
from src.models import (
    AnalysisRequest,
    BatchProcessRequest,
    BatchSite,
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    GenerateSpiderRequest,
)


class TestModels:
    """Tests para modelos de datos"""

    def test_analysis_request_valid(self):
        """Test creación de AnalysisRequest válido"""
        request = AnalysisRequest(
            url="https://example.com/news",
            medio="Example News",
            seccion="Internacional",
            area_geografica="GLOBAL",
            tipo_medio="diario",
            frecuencia_minutos=60,
        )

        assert request.url == "https://example.com/news"
        assert request.medio == "Example News"
        assert request.seccion == "Internacional"

    def test_analysis_request_backward_compatibility(self):
        """Test compatibilidad hacia atrás con campo 'name'"""
        request = AnalysisRequest(url="https://example.com", name="Old Style Name")

        # El campo name debe funcionar
        assert request.name == "Old Style Name"
        # Pero medio y seccion deben tener valores por defecto
        assert request.medio is not None
        assert request.seccion is not None

    def test_generate_spider_request_auto_name(self):
        """Test generación automática de nombre de spider"""
        request = GenerateSpiderRequest(
            medio="El País",
            seccion="Internacional",
            area_geografica="ESPAÑA",
            tipo_medio="diario",
        )

        assert request.spider_name == "el_pais_internacional"

    def test_generate_spider_request_special_chars(self):
        """Test sanitización de caracteres especiales en nombre"""
        request = GenerateSpiderRequest(
            medio="CNN en Español",
            seccion="Última Hora",
            area_geografica="GLOBAL",
            tipo_medio="agencia",
        )

        assert request.spider_name == "cnn_en_espanol_ultima_hora"

    def test_duplicate_check_request(self):
        """Test DuplicateCheckRequest"""
        request = DuplicateCheckRequest(medio="La Nación", seccion="Economía")

        assert request.medio == "La Nación"
        assert request.seccion == "Economía"

    def test_duplicate_check_response(self):
        """Test DuplicateCheckResponse"""
        response = DuplicateCheckResponse(
            exists=True,
            spider_name="la_nacion_economia",
            message="Spider already exists",
        )

        assert response.exists is True
        assert response.spider_name == "la_nacion_economia"

    def test_batch_site_valid(self):
        """Test BatchSite con todos los campos"""
        site = BatchSite(
            medio="Test News",
            seccion="Local",
            url="https://test.com/local",
            area_geografica="MEXICO",
            tipo_medio="diario",
            frecuencia_minutos=120,
            rss_url="https://test.com/rss",
        )

        assert site.medio == "Test News"
        assert site.frecuencia_minutos == 120
        assert site.rss_url == "https://test.com/rss"

    def test_batch_site_defaults(self):
        """Test BatchSite con valores por defecto"""
        site = BatchSite(
            medio="Test",
            seccion="Test",
            url="https://test.com",
            area_geografica="GLOBAL",
            tipo_medio="diario",
        )

        assert site.frecuencia_minutos == 60  # Valor por defecto
        assert site.rss_url is None

    def test_area_geografica_validation(self):
        """Test validación de área geográfica"""
        # Área válida
        request = AnalysisRequest(
            url="https://test.com",
            medio="Test",
            seccion="Test",
            area_geografica="ESPAÑA",
            tipo_medio="diario",
        )
        assert request.area_geografica == "ESPAÑA"

        # Área inválida debe fallar
        with pytest.raises(ValidationError) as exc_info:
            AnalysisRequest(
                url="https://test.com",
                medio="Test",
                seccion="Test",
                area_geografica="INVALID_AREA",
                tipo_medio="diario",
            )

        assert "area_geografica" in str(exc_info.value)

    def test_tipo_medio_validation(self):
        """Test validación de tipo de medio"""
        # Tipos válidos
        for tipo in ["diario", "revista", "agencia"]:
            request = GenerateSpiderRequest(
                medio="Test", seccion="Test", area_geografica="GLOBAL", tipo_medio=tipo
            )
            assert request.tipo_medio == tipo

        # Tipo inválido debe fallar
        with pytest.raises(ValidationError):
            GenerateSpiderRequest(
                medio="Test",
                seccion="Test",
                area_geografica="GLOBAL",
                tipo_medio="invalid_type",
            )

    def test_batch_process_request(self):
        """Test BatchProcessRequest con límites"""
        sites = [
            BatchSite(
                medio=f"Site{i}",
                seccion="News",
                url=f"https://site{i}.com",
                area_geografica="GLOBAL",
                tipo_medio="diario",
            )
            for i in range(10)
        ]

        request = BatchProcessRequest(sites=sites)
        assert len(request.sites) == 10

    def test_batch_process_request_limit(self):
        """Test límite máximo de batch"""
        # Crear 101 sitios (más del límite)
        sites = [
            BatchSite(
                medio=f"Site{i}",
                seccion="News",
                url=f"https://site{i}.com",
                area_geografica="GLOBAL",
                tipo_medio="diario",
            )
            for i in range(101)
        ]

        with pytest.raises(ValidationError) as exc_info:
            BatchProcessRequest(sites=sites)

        assert "100" in str(exc_info.value)  # Debe mencionar el límite

    def test_url_validation(self):
        """Test validación de URLs"""
        # URL válida
        request = AnalysisRequest(
            url="https://valid-url.com/news", medio="Test", seccion="Test"
        )
        assert str(request.url) == "https://valid-url.com/news"

        # URL inválida
        with pytest.raises(ValidationError):
            AnalysisRequest(url="not-a-url", medio="Test", seccion="Test")

    def test_frecuencia_minutos_range(self):
        """Test rango de frecuencia en minutos"""
        # Valores válidos
        for freq in [15, 30, 60, 120, 1440]:
            site = BatchSite(
                medio="Test",
                seccion="Test",
                url="https://test.com",
                area_geografica="GLOBAL",
                tipo_medio="diario",
                frecuencia_minutos=freq,
            )
            assert site.frecuencia_minutos == freq

    def test_model_schema_examples(self):
        """Test que los modelos tengan ejemplos en schema"""
        # Verificar que GenerateSpiderRequest tiene ejemplo
        schema = GenerateSpiderRequest.model_json_schema()
        assert "example" in schema or "examples" in schema

        # Verificar AnalysisRequest
        schema = AnalysisRequest.model_json_schema()
        assert "properties" in schema

    def test_optional_fields(self):
        """Test campos opcionales"""
        request = GenerateSpiderRequest(
            medio="Test",
            seccion="Test",
            area_geografica="GLOBAL",
            tipo_medio="diario",
            comentarios="Este es un comentario de prueba",
        )

        assert request.comentarios == "Este es un comentario de prueba"

        # Sin comentarios
        request2 = GenerateSpiderRequest(
            medio="Test", seccion="Test", area_geografica="GLOBAL", tipo_medio="diario"
        )

        assert request2.comentarios is None
