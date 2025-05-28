# Tests para Items y ItemLoaders
import unittest
from datetime import datetime
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
