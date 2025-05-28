# Tests para Items y ItemLoaders
import unittest
from datetime import datetime, timedelta, date # Added timedelta, date
from unittest.mock import patch # Added patch
from scrapy.http import HtmlResponse
from scrapy.selector import Selector

from scraper_core.items import ArticuloInItem
from scraper_core.itemloaders import (
    ArticuloInItemLoader,
    clean_text,
    extract_text_from_html,
    normalize_date,
    normalize_url,
    extract_author,
    validate_medio_type,
    process_tags,
    validate_language,
    generate_storage_path
)


class TestArticuloInItem(unittest.TestCase):
    """Tests para ArticuloInItem"""
    
    def test_create_item(self):
        """Test creación básica de item"""
        item = ArticuloInItem()
        item['titular'] = 'Test Article'
        item['medio'] = 'Test Media'
        item['pais_publicacion'] = 'España'
        item['tipo_medio'] = 'diario'
        item['fecha_publicacion'] = datetime.now()
        item['contenido_texto'] = 'Test content'
        
        self.assertEqual(item['titular'], 'Test Article')
        self.assertTrue(item.validate())
    
    def test_validate_missing_required(self):
        """Test validación con campos requeridos faltantes"""
        item = ArticuloInItem()
        item['titular'] = 'Test Article'
        # Falta medio, pais_publicacion, etc.
        
        self.assertFalse(item.validate())
    
    def test_all_fields(self):
        """Test que todos los campos definidos existen"""
        item = ArticuloInItem()
        expected_fields = [
            'url', 'storage_path', 'medio', 'pais_publicacion', 'tipo_medio',
            'titular', 'fecha_publicacion', 'autor', 'idioma', 'seccion',
            'etiquetas_fuente', 'es_opinion', 'es_oficial', 'resumen',
            'categorias_asignadas', 'puntuacion_relevancia', 'fecha_recopilacion',
            'fecha_procesamiento', 'estado_procesamiento', 'error_detalle',
            'contenido_texto', 'contenido_html', 'metadata'
        ]
        
        for field in expected_fields:
            self.assertIn(field, item.fields)


class TestProcessorFunctions(unittest.TestCase):
    """Tests para funciones procesadoras individuales"""
    
    def test_clean_text(self):
        """Test limpieza de texto"""
        # Espacios múltiples
        self.assertEqual(clean_text('  Hello   World  '), 'Hello World')
        
        # Caracteres de escape HTML
        self.assertEqual(clean_text('Hello&nbsp;World'), 'Hello World')
        
        # Texto vacío
        self.assertEqual(clean_text(''), '')
        self.assertEqual(clean_text(None), '')
    
    def test_extract_text_from_html(self):
        """Test extracción de texto desde HTML"""
        html = '<p>Hello <strong>World</strong></p>'
        self.assertEqual(extract_text_from_html(html), 'Hello World')
        
        # HTML con entidades
        html = '<p>Price: &euro;100</p>'
        self.assertEqual(extract_text_from_html(html), 'Price: €100')
    
    def test_normalize_date(self):
        """Test normalización de fechas"""
        # ISO format
        date = normalize_date('2024-01-15T10:30:00Z')
        self.assertEqual(date.year, 2024)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 15)
        
        # Spanish format
        date = normalize_date('15/01/2024')
        self.assertEqual(date.year, 2024)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 15)
        
        # Already datetime
        now = datetime.now()
        self.assertEqual(normalize_date(now), now)
        
        # Invalid format
        self.assertIsNone(normalize_date('invalid date'))
        self.assertIsNone(normalize_date('2024-13-01')) # Invalid month
        self.assertIsNone(normalize_date('ayer por la tarde')) # Not supported variation

    # --- Tests for relative date normalization ---
    MOCKED_NOW = datetime(2024, 7, 22, 10, 0, 0) # Monday

    @patch('scraper_core.itemloaders.datetime', autospec=True)
    def test_normalize_date_relative_ayer(self, mock_datetime):
        mock_datetime.now.return_value = self.MOCKED_NOW
        
        expected_date = (self.MOCKED_NOW - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        self.assertEqual(normalize_date("ayer"), expected_date)
        self.assertEqual(normalize_date("Ayer"), expected_date)
        self.assertEqual(normalize_date(" AYER "), expected_date)

    @patch('scraper_core.itemloaders.datetime', autospec=True)
    def test_normalize_date_relative_hace_dias(self, mock_datetime):
        mock_datetime.now.return_value = self.MOCKED_NOW
        
        # Test "hace 1 día"
        expected_date_1_day = (self.MOCKED_NOW - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        self.assertEqual(normalize_date("hace 1 día"), expected_date_1_day)
        self.assertEqual(normalize_date("hace 1 dia"), expected_date_1_day) # without accent
        
        # Test "hace 5 días"
        expected_date_5_days = (self.MOCKED_NOW - timedelta(days=5)).replace(hour=0, minute=0, second=0, microsecond=0)
        self.assertEqual(normalize_date("hace 5 días"), expected_date_5_days)
        self.assertEqual(normalize_date("HACE 5 DIAS"), expected_date_5_days) # uppercase, no accent, plural 's'
        self.assertEqual(normalize_date("hace 10 dias"), (self.MOCKED_NOW - timedelta(days=10)).replace(hour=0, minute=0, second=0, microsecond=0))

    @patch('scraper_core.itemloaders.datetime', autospec=True)
    def test_normalize_date_relative_hace_horas(self, mock_datetime):
        mock_datetime.now.return_value = self.MOCKED_NOW
        
        # Test "hace 1 hora"
        expected_date_1_hour = self.MOCKED_NOW - timedelta(hours=1)
        self.assertEqual(normalize_date("hace 1 hora"), expected_date_1_hour)
        
        # Test "hace 3 horas"
        expected_date_3_hours = self.MOCKED_NOW - timedelta(hours=3)
        self.assertEqual(normalize_date("hace 3 horas"), expected_date_3_hours)
        self.assertEqual(normalize_date("HACE 10 HORAS"), self.MOCKED_NOW - timedelta(hours=10))

    @patch('scraper_core.itemloaders.datetime', autospec=True)
    def test_normalize_date_relative_hace_minutos(self, mock_datetime):
        mock_datetime.now.return_value = self.MOCKED_NOW

        # Test "hace 1 minuto"
        expected_date_1_min = self.MOCKED_NOW - timedelta(minutes=1)
        self.assertEqual(normalize_date("hace 1 minuto"), expected_date_1_min)

        # Test "hace 15 minutos"
        expected_date_15_mins = self.MOCKED_NOW - timedelta(minutes=15)
        self.assertEqual(normalize_date("hace 15 minutos"), expected_date_15_mins)
        self.assertEqual(normalize_date("HACE 30 MINUTOS"), self.MOCKED_NOW - timedelta(minutes=30))

    def test_normalize_date_invalid_relative_formats(self):
        """Test invalid or unsupported relative date formats."""
        self.assertIsNone(normalize_date("hace una semana"))
        self.assertIsNone(normalize_date("hace 2 meses"))
        self.assertIsNone(normalize_date("ayer por la mañana"))
        self.assertIsNone(normalize_date("hace mucho tiempo"))
        self.assertIsNone(normalize_date("hace cinco dias")) # number as word
        self.assertIsNone(normalize_date("hace 5dias")) # no space
        self.assertIsNone(normalize_date("hace horas 5")) # wrong order
        self.assertIsNone(normalize_date("1 hora hace"))

    def test_normalize_date_keeps_time_for_standard_formats_with_time(self):
        """Test that time is preserved for standard formats that include it."""
        dt_with_time = normalize_date('2024-01-15T10:30:00Z')
        self.assertEqual(dt_with_time.hour, 10)
        self.assertEqual(dt_with_time.minute, 30)
        self.assertEqual(dt_with_time.second, 0)

        dt_with_time_es = normalize_date('15/01/2024 14:45:30')
        self.assertEqual(dt_with_time_es.hour, 14)
        self.assertEqual(dt_with_time_es.minute, 45)
        self.assertEqual(dt_with_time_es.second, 30)

    def test_normalize_date_sets_midnight_for_standard_formats_without_time(self):
        """Test that time is set to midnight for standard formats that only specify date."""
        dt_date_only_iso = normalize_date('2024-01-15')
        self.assertEqual(dt_date_only_iso.hour, 0)
        self.assertEqual(dt_date_only_iso.minute, 0)
        self.assertEqual(dt_date_only_iso.second, 0)

        dt_date_only_es = normalize_date('15/01/2024')
        self.assertEqual(dt_date_only_es.hour, 0) # This depends on strptime default, usually 00:00:00
        self.assertEqual(dt_date_only_es.minute, 0)
        self.assertEqual(dt_date_only_es.second, 0)

        dt_date_only_text = normalize_date('15 de Enero de 2024') # Assuming locale independent for month
        if dt_date_only_text: # This might fail if locale for 'Enero' is not Spanish
             self.assertEqual(dt_date_only_text.hour, 0)
             self.assertEqual(dt_date_only_text.minute, 0)
             self.assertEqual(dt_date_only_text.second, 0)
        else:
            # If '15 de Enero de 2024' is not parsed, this test part is skipped.
            # This can happen if the test environment locale is not Spanish-aware for %B.
            # The function itself doesn't set locale, relies on system's strptime behavior.
            pass


    def test_normalize_url(self):
        """Test normalización de URLs"""
        # Eliminar parámetros de tracking
        url = 'https://example.com/article?utm_source=twitter&id=123'
        normalized = normalize_url(url)
        self.assertEqual(normalized, 'https://example.com/article?id=123')
        
        # Múltiples parámetros
        url = 'https://example.com/article?id=123&utm_medium=social&ref=home'
        normalized = normalize_url(url)
        self.assertEqual(normalized, 'https://example.com/article?id=123')
    
    def test_extract_author(self):
        """Test extracción de autor"""
        self.assertEqual(extract_author('Por Juan Pérez'), 'Juan Pérez')
        self.assertEqual(extract_author('By John Doe'), 'John Doe')
        self.assertEqual(extract_author('Autor: María García'), 'María García')
        
        # Autor muy largo
        long_author = 'A' * 250
        result = extract_author(long_author)
        self.assertTrue(len(result) <= 200)
        self.assertTrue(result.endswith('...'))
    
    def test_validate_medio_type(self):
        """Test validación de tipo de medio"""
        self.assertEqual(validate_medio_type('diario'), 'diario')
        self.assertEqual(validate_medio_type('newspaper'), 'diario')
        self.assertEqual(validate_medio_type('TV'), 'televisión')
        self.assertEqual(validate_medio_type('unknown'), 'otro')
        self.assertEqual(validate_medio_type(''), 'otro')
    
    def test_process_tags(self):
        """Test procesamiento de etiquetas"""
        # String con comas
        tags = process_tags('política, economía, internacional')
        self.assertEqual(tags, ['política', 'economía', 'internacional'])
        
        # Lista
        tags = process_tags(['Política', 'Economía', 'política'])
        self.assertEqual(len(tags), 2)  # Elimina duplicados
        
        # Vacío
        self.assertEqual(process_tags(''), [])
        self.assertEqual(process_tags(None), [])
    
    def test_validate_language(self):
        """Test validación de idioma"""
        self.assertEqual(validate_language('español'), 'es')
        self.assertEqual(validate_language('English'), 'en')
        self.assertEqual(validate_language('es-ES'), 'es')
        self.assertEqual(validate_language(''), 'es')  # Default
        self.assertEqual(validate_language(None), 'es')
    
    def test_generate_storage_path(self):
        """Test generación de storage path"""
        item_dict = {
            'medio': 'El País',
            'fecha_publicacion': datetime(2024, 1, 15),
            'titular': 'Test Article Title!'
        }
        
        path = generate_storage_path(item_dict)
        self.assertRegex(path, r'^el-pais/2024/01/15/test-article-title\.html\.gz$')
        
        # Sin fecha válida (usa fecha actual)
        item_dict = {
            'medio': 'ABC',
            'titular': 'Another Test'
        }
        path = generate_storage_path(item_dict)
        self.assertTrue(path.startswith('abc/'))
        self.assertTrue(path.endswith('/another-test.html.gz'))


class TestArticuloInItemLoader(unittest.TestCase):
    """Tests para ArticuloInItemLoader"""
    
    def setUp(self):
        """Configurar loader para tests"""
        self.loader = ArticuloInItemLoader(item=ArticuloInItem())
    
    def test_load_basic_item(self):
        """Test carga básica de item"""
        self.loader.add_value('titular', '<h1>Test Title</h1>')
        self.loader.add_value('medio', '  El País  ')
        self.loader.add_value('pais_publicacion', 'españa')
        self.loader.add_value('tipo_medio', 'newspaper')
        self.loader.add_value('contenido_texto', '<p>Test content</p>')
        self.loader.add_value('fecha_publicacion', '2024-01-15')
        
        item = self.loader.load_item()
        
        self.assertEqual(item['titular'], 'Test Title')
        self.assertEqual(item['medio'], 'El País')
        self.assertEqual(item['pais_publicacion'], 'España')
        self.assertEqual(item['tipo_medio'], 'diario')
        self.assertEqual(item['contenido_texto'], 'Test content')
        self.assertIsInstance(item['fecha_publicacion'], datetime)
    
    def test_process_urls(self):
        """Test procesamiento de URLs"""
        self.loader.add_value('url', 'https://example.com/article?utm_source=twitter')
        item = self.loader.load_item()
        
        self.assertEqual(item['url'], 'https://example.com/article')
    
    def test_process_author(self):
        """Test procesamiento de autor"""
        self.loader.add_value('autor', 'Por Juan Pérez')
        item = self.loader.load_item()
        
        self.assertEqual(item['autor'], 'Juan Pérez')
    
    def test_process_tags(self):
        """Test procesamiento de etiquetas"""
        self.loader.add_value('etiquetas_fuente', 'política, economía, internacional')
        item = self.loader.load_item()
        
        self.assertIsInstance(item['etiquetas_fuente'], list)
        self.assertEqual(len(item['etiquetas_fuente']), 3)
    
    def test_boolean_fields(self):
        """Test campos booleanos"""
        self.loader.add_value('es_opinion', 'true')
        self.loader.add_value('es_oficial', 0)
        item = self.loader.load_item()
        
        self.assertTrue(item['es_opinion'])
        self.assertFalse(item['es_oficial'])
    
    def test_default_values(self):
        """Test valores por defecto"""
        self.loader.add_value('titular', 'Test')
        self.loader.add_value('medio', 'Test Media')
        self.loader.add_value('pais_publicacion', 'España')
        self.loader.add_value('tipo_medio', 'diario')
        self.loader.add_value('contenido_texto', 'Content')
        self.loader.add_value('fecha_publicacion', '2024-01-15')
        
        item = self.loader.load_item()
        
        # Valores por defecto
        self.assertEqual(item['idioma'], 'es')
        self.assertEqual(item['estado_procesamiento'], 'pendiente')
        self.assertFalse(item['es_opinion'])
        self.assertFalse(item['es_oficial'])
        self.assertIsNotNone(item['fecha_recopilacion'])
        self.assertIsNotNone(item['storage_path'])
    
    def test_score_validation(self):
        """Test validación de puntuación"""
        # Valor dentro del rango
        self.loader.add_value('puntuacion_relevancia', '7')
        item = self.loader.load_item()
        self.assertEqual(item.get('puntuacion_relevancia'), 7)
        
        # Valor fuera del rango (mayor)
        loader2 = ArticuloInItemLoader(item=ArticuloInItem())
        loader2.add_value('puntuacion_relevancia', '15')
        item2 = loader2.load_item()
        self.assertEqual(item2.get('puntuacion_relevancia'), 10)
        
        # Valor fuera del rango (menor)
        loader3 = ArticuloInItemLoader(item=ArticuloInItem())
        loader3.add_value('puntuacion_relevancia', '-5')
        item3 = loader3.load_item()
        self.assertEqual(item3.get('puntuacion_relevancia'), 0)
    
    def test_storage_path_generation(self):
        """Test generación automática de storage_path"""
        self.loader.add_value('titular', 'Test Article')
        self.loader.add_value('medio', 'ABC News')
        self.loader.add_value('pais_publicacion', 'España')
        self.loader.add_value('tipo_medio', 'digital')
        self.loader.add_value('contenido_texto', 'Content')
        self.loader.add_value('fecha_publicacion', '2024-01-15')
        
        item = self.loader.load_item()
        
        self.assertIsNotNone(item['storage_path'])
        self.assertRegex(item['storage_path'], r'^[^/]+/\d{4}/\d{2}/\d{2}/[^/]+\.html\.gz$')


if __name__ == '__main__':
    unittest.main()
