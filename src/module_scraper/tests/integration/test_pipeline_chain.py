import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone # Ensure timezone is imported

from scraper_core.items import ArticuloInItem
from scraper_core.pipelines.cleaning import DataCleaningPipeline
from scraper_core.pipelines.validation import DataValidationPipeline
# Removed InvalidItemError import as it's not used directly in this test yet
from scraper_core.pipelines.storage import SupabaseStoragePipeline

from scrapy.utils.project import get_project_settings
from scrapy.statscollectors import StatsCollector # Corrected import
from scrapy.crawler import Crawler

class MockSpider:
    name = 'mockspider'
    logger = MagicMock()
    custom_settings = {}

@pytest.fixture
def mock_crawler_fixture(tmp_path):
    settings = get_project_settings()
    settings.setmodule('tests.config.test_settings', priority='project')

    settings['VALIDATION_REQUIRED_FIELDS'] = ['url', 'titular', 'medio', 'fecha_publicacion', 'contenido_texto', 'fuente', 'pais_publicacion', 'tipo_medio']
    settings['VALIDATION_NON_EMPTY_FIELDS'] = ['url', 'titular', 'medio']
    settings['VALIDATION_URL_FIELDS'] = ['url', 'medio_url_principal']
    settings['VALIDATION_MAX_LENGTHS'] = {'url': 2048, 'titular': 512}
    settings['VALIDATION_DATE_FORMATS'] = ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"]
    settings['VALIDATION_DROP_INVALID_ITEMS'] = False

    settings['SUPABASE_URL'] = 'http://mock.supabase.co'
    settings['SUPABASE_SERVICE_ROLE_KEY'] = 'mock_key'
    settings['SUPABASE_HTML_BUCKET'] = 'mock-bucket'
    settings['SCRAPY_PROJECT_ROOT'] = str(tmp_path) # For pipelines needing file paths

    crawler = MagicMock(spec=Crawler)
    crawler.settings = settings
    crawler.stats = MagicMock(spec=StatsCollector)

    spider_instance = MockSpider()
    spider_instance.settings = settings
    crawler.spider = spider_instance

    return crawler

@pytest.fixture
def valid_item_data_fixture():
    now_dt = datetime.now(timezone.utc) # Use timezone.utc
    data = {
        'url': 'http://example.com/article1',
        'storage_path': '',
        'fuente': 'mockspider',
        'medio': 'Test Medio',
        'medio_url_principal': 'http://example.com',
        'pais_publicacion': 'Testland',
        'tipo_medio': 'Diario Digital',
        'titular': 'Valid Test Article Title For Pipeline', # Ensure it's a good title
        'fecha_publicacion': now_dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'autor': 'Test Author',
        'idioma': 'es',
        'seccion': 'News',
        'etiquetas_fuente': ['test', 'valid'],
        'es_opinion': False,
        'es_oficial': False,
        'resumen': '',
        'categorias_asignadas': [],
        'puntuacion_relevancia': 0.0,
        'fecha_recopilacion': now_dt,
        'fecha_procesamiento': None,
        'estado_procesamiento': 'pendiente',
        'error_detalle': '',
        'contenido_texto': 'This is the valid textual content of the article for testing purposes. It is clean and proper.',
        'contenido_html': '<h1>Valid Test Article Title</h1><p>This is the valid HTML content.</p>',
        'metadata': {'extra_info': 'some_value_here'}
    }
    return data

def test_valid_item_full_pipeline_flow(mock_crawler_fixture, valid_item_data_fixture):
    spider = mock_crawler_fixture.spider
    item = ArticuloInItem(valid_item_data_fixture)

    cleaning_pipeline = DataCleaningPipeline()
    processed_item_cleaned = cleaning_pipeline.process_item(item, spider)
    assert processed_item_cleaned is not None

    validation_pipeline = DataValidationPipeline.from_crawler(mock_crawler_fixture)
    validation_pipeline.open_spider(spider)
    processed_item_validated = validation_pipeline.process_item(processed_item_cleaned, spider)
    assert processed_item_validated is not None
    assert 'error_validation' not in processed_item_validated, f"Valid item marked with error: {processed_item_validated.get('error_validation')}"

    storage_pipeline = SupabaseStoragePipeline.from_crawler(mock_crawler_fixture)
    storage_pipeline.open_spider(spider)
    mock_supabase_client = MagicMock()
    storage_pipeline.client = mock_supabase_client

    mock_upsert_execute_result = MagicMock()
    mock_upsert_execute_result.data = [{'id_primary': 'mock-db-id-456', 'url': item['url']}]
    mock_supabase_client.table.return_value.upsert.return_value.execute = MagicMock(return_value=mock_upsert_execute_result)

    # Simplified expected path for predictability in test
    # The actual SupabaseStoragePipeline._generate_url_hash might be complex
    # For the purpose of this test, we assume a predictable output or mock _generate_url_hash too.
    # Let's mock _generate_url_hash for simplicity and predictability here.
    url_hash_mock = "mocked_url_hash_123"
    expected_storage_path = f"html_content/{datetime.now(timezone.utc).year}/{datetime.now(timezone.utc).month:02d}/{url_hash_mock}.html"

    with patch.object(storage_pipeline, '_generate_url_hash', return_value=url_hash_mock), \
         patch.object(storage_pipeline, '_upload_html_content_with_retry', return_value=expected_storage_path) as mock_upload_html:
        final_item = storage_pipeline.process_item(processed_item_validated, spider)

    assert final_item is not None
    mock_supabase_client.table.assert_called_once_with(storage_pipeline.table_name)
    assert mock_supabase_client.table.return_value.upsert.call_count == 1

    upsert_called_data = mock_supabase_client.table.return_value.upsert.call_args[0][0]
    assert upsert_called_data['url'] == item['url']

    mock_upload_html.assert_called_once()
    upload_args, _ = mock_upload_html.call_args
    assert upload_args[0] == url_hash_mock # Check the key used for upload (the mocked hash)
    assert upload_args[1] == item['contenido_html']

    assert final_item.get('storage_path') == expected_storage_path
    assert final_item.get('id_primary') == 'mock-db-id-456'

    storage_pipeline.close_spider(spider)
    validation_pipeline.close_spider(spider)
