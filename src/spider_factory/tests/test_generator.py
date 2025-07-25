"""
Tests unitarios para generator.py
"""

import shutil
import tempfile  # noqa: F401
from pathlib import Path  # noqa: F401

import pytest

from src.analyzer import AnalysisResult, AnalysisStrategy, SiteSelectors  # noqa: F401
from src.generator import SpiderGenerator  # noqa: F401
from src.models import GenerateSpiderRequest


class TestSpiderGenerator:
    """Tests para SpiderGenerator"""

    def test_generate_rss_spider(self, mock_generator, sample_analysis_result):
        """Test generación de spider RSS"""
        # Configurar resultado de análisis para RSS
        sample_analysis_result.strategy = AnalysisStrategy.RSS
        sample_analysis_result.rss_url = "https://example.com/feed.rss"

        request = GenerateSpiderRequest(
            medio="Example News",
            seccion="Internacional",
            area_geografica="GLOBAL",
            tipo_medio="diario",
            analysis_result=sample_analysis_result,
        )

        code = mock_generator.generate_spider(request)

        assert "rss_spider.j2" in code or "RSS Spider" in code
        assert "Example News" in code
        assert "Internacional" in code
        assert "example_news_internacional" in code

    def test_generate_scraping_spider(self, mock_generator, sample_analysis_result):
        """Test generación de spider de scraping"""
        sample_analysis_result.strategy = AnalysisStrategy.SCRAPING

        request = GenerateSpiderRequest(
            medio="Test Site",
            seccion="Deportes",
            area_geografica="ESPAÑA",
            tipo_medio="diario",
            analysis_result=sample_analysis_result,
        )

        code = mock_generator.generate_spider(request)

        assert "scraping_spider.j2" in code or "Scraping Spider" in code
        assert "test_site_deportes" in code
        assert "ESPAÑA" in code

    def test_generate_playwright_spider(self, mock_generator, sample_analysis_result):
        """Test generación de spider con Playwright"""
        sample_analysis_result.strategy = AnalysisStrategy.SCRAPING
        sample_analysis_result.needs_javascript = True

        request = GenerateSpiderRequest(
            medio="SPA News",
            seccion="Tech",
            area_geografica="USA",
            tipo_medio="revista",
            analysis_result=sample_analysis_result,
        )

        code = mock_generator.generate_spider(request)

        assert "playwright_spider.j2" in code or "Playwright Spider" in code
        assert "spa_news_tech" in code

    def test_spider_name_generation(self, mock_generator):
        """Test generación automática de nombre de spider"""
        request = GenerateSpiderRequest(
            medio="El País",
            seccion="Internacional",
            area_geografica="ESPAÑA",
            tipo_medio="diario",
            analysis_result=None,
        )

        # El nombre debe generarse automáticamente
        assert request.spider_name == "el_pais_internacional"

    def test_spider_name_sanitization(self, mock_generator):
        """Test sanitización de nombres de spider"""
        request = GenerateSpiderRequest(
            medio="CNN en Español",
            seccion="Última Hora",
            area_geografica="GLOBAL",
            tipo_medio="agencia",
            analysis_result=None,
        )

        assert request.spider_name == "cnn_en_espanol_ultima_hora"

    def test_save_spider_to_file(self, mock_generator):
        """Test guardado de spider en archivo"""
        code = '''# -*- coding: utf-8 -*-
"""Test Spider"""
class TestSpider:
    name = "test_spider"
'''

        file_path = mock_generator.save_spider(code, "test_spider")

        assert file_path.exists()
        assert file_path.name == "test_spider.py"
        assert file_path.read_text() == code

    def test_template_not_found_error(self, mock_generator):
        """Test error cuando no se encuentra template"""
        # Eliminar temporalmente los templates
        templates_dir = mock_generator.templates_dir
        if templates_dir.exists():
            shutil.rmtree(templates_dir)

        request = GenerateSpiderRequest(
            medio="Test",
            seccion="Test",
            area_geografica="GLOBAL",
            tipo_medio="diario",
            analysis_result=None,
        )

        with pytest.raises(FileNotFoundError):
            mock_generator.generate_spider(request)

    def test_format_spider_code(self, mock_generator):
        """Test formateo de código con Black"""
        unformatted_code = """class   TestSpider:
    name="test"
    def   parse(self,response):
        return{"title":response.css("h1::text").get()}"""

        formatted = mock_generator._format_code(unformatted_code)

        # Si Black está disponible, el código debe estar formateado
        # Si no, debe devolver el código original
        assert formatted  # No debe ser None o vacío
        assert "class" in formatted
        assert "TestSpider" in formatted

    def test_metadata_in_generated_spider(self, mock_generator, sample_analysis_result):
        """Test que metadata esté incluida en el spider generado"""
        request = GenerateSpiderRequest(
            medio="La Nación",
            seccion="Economía",
            area_geografica="ARGENTINA",
            tipo_medio="diario",
            frecuencia_minutos=120,
            analysis_result=sample_analysis_result,
        )

        code = mock_generator.generate_spider(request)

        # Verificar metadata
        assert "La Nación" in code
        assert "Economía" in code
        assert "ARGENTINA" in code
        assert "diario" in code

    def test_selectors_in_scraping_spider(self, mock_generator, sample_analysis_result):
        """Test que selectores estén correctamente incluidos"""
        sample_analysis_result.selectors = SiteSelectors(
            title="h1.article-title",
            content="div.article-body",
            date="time.published",
            author="span.author-name",
        )

        request = GenerateSpiderRequest(
            medio="Test News",
            seccion="Local",
            area_geografica="MEXICO",
            tipo_medio="diario",
            analysis_result=sample_analysis_result,
        )

        code = mock_generator.generate_spider(request)

        # Los selectores deben estar en el código generado
        assert "h1.article-title" in code or "article-title" in code
        assert "div.article-body" in code or "article-body" in code

    def test_output_directory_creation(self, mock_generator):
        """Test creación automática de directorio de salida"""
        # Eliminar directorio si existe
        if mock_generator.output_dir.exists():
            shutil.rmtree(mock_generator.output_dir)

        assert not mock_generator.output_dir.exists()

        # Generar spider debe crear el directorio
        code = "class TestSpider: pass"
        mock_generator.save_spider(code, "test_spider")

        assert mock_generator.output_dir.exists()

    def test_spider_with_url_patterns(self, mock_generator, sample_analysis_result):
        """Test spider con patrones de URL específicos"""
        sample_analysis_result.url_patterns = [
            "https://example.com/news/*",
            "https://example.com/*/article/*",
        ]

        request = GenerateSpiderRequest(
            medio="Example",
            seccion="News",
            area_geografica="USA",
            tipo_medio="diario",
            analysis_result=sample_analysis_result,
        )

        code = mock_generator.generate_spider(request)

        # Los patrones deben estar incluidos de alguna forma
        assert "example.com" in code
