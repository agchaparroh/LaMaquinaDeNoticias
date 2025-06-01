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


@pytest.fixture
def dirty_item_data_fixture():
    now_dt = datetime.now(timezone.utc)
    data = {
        'url': 'http://example.com/dirty_article_test', # Unique URL
        'storage_path': '',
        'fuente': 'mockspider_dirty_test', # Unique fuente
        'medio': '  Test Dirty Medio Test  ',
        'medio_url_principal': 'http://example.com/dirty_test',
        'pais_publicacion': 'Testlandia',
        'tipo_medio': 'Blog Post Test', # Unique type
        'titular': '  <h1>A Dirty Title Test</h1>  ',
        'fecha_publicacion': now_dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'autor': 'Mr. Messy Test', # Unique author
        'idioma': 'en',
        'seccion': '  Opinions Test  ',
        'etiquetas_fuente': [' dirty_test ', ' test_tag '],
        'es_opinion': False,
        'es_oficial': False,
        'resumen': '',
        'categorias_asignadas': [],
        'puntuacion_relevancia': 0.0,
        'fecha_recopilacion': now_dt,
        'fecha_procesamiento': None,
        'estado_procesamiento': 'pendiente',
        'error_detalle': '',
        'contenido_texto': '  <p>Some dirty text with  <b>bold tags</b> and   many extra spaces.  </p>\n\nAnother line here.  ',
        'contenido_html': '<h1>  A Dirty Title Test  </h1><p>  Some dirty text with  <b>bold tags</b> and   many extra spaces.  </p>\n\nAnother line here.  ',
        'metadata': {'original_format': ' very_messy '}
    }
    # Ensure all required fields for validation are present
    for req_field in ['url', 'titular', 'medio', 'fecha_publicacion', 'contenido_texto', 'fuente', 'pais_publicacion', 'tipo_medio']:
        if req_field not in data or not data[req_field]: # Check if field is missing or empty
             data[req_field] = f"Default value for {req_field}" # Add default if missing
    if not data['titular'].strip(): data['titular'] = "Default Dirty Title Test"
    if not data['medio'].strip(): data['medio'] = "Default Dirty Medio Test"
    return data

def test_dirty_item_cleaning_and_validation_flow(mock_crawler_fixture, dirty_item_data_fixture):
    spider = mock_crawler_fixture.spider
    item = ArticuloInItem(dirty_item_data_fixture)

    # Configure cleaning settings on the mock crawler for the pipeline to use
    # These names must match what DataCleaningPipeline expects from Scrapy settings
    mock_crawler_fixture.settings['CLEANING_STRIP_HTML_FIELDS'] = ['titular', 'contenido_texto', 'medio', 'seccion']
    mock_crawler_fixture.settings['CLEANING_NORMALIZE_WHITESPACE_FIELDS'] = ['titular', 'contenido_texto', 'medio', 'seccion', 'autor']
    mock_crawler_fixture.settings['CLEANING_NORMALIZE_LIST_STR_FIELDS'] = ['etiquetas_fuente']
    # Example: If DataCleaningPipeline has a setting to preserve original HTML for storage
    mock_crawler_fixture.settings['CLEANING_PRESERVE_HTML_FOR_STORAGE'] = True


    cleaning_pipeline = DataCleaningPipeline()
    # Manually call open_spider if it initializes from settings
    if hasattr(cleaning_pipeline, 'from_crawler'):
        cleaning_pipeline = DataCleaningPipeline.from_crawler(mock_crawler_fixture)
    cleaning_pipeline.open_spider(spider) # Ensure settings are loaded if pipeline uses open_spider

    processed_item_cleaned = cleaning_pipeline.process_item(item, spider)
    assert processed_item_cleaned is not None

    assert processed_item_cleaned['titular'] == "A Dirty Title Test", f"Titular cleaning failed: got '{processed_item_cleaned['titular']}'"
    assert processed_item_cleaned['medio'] == "Test Dirty Medio Test", f"Medio cleaning failed: got '{processed_item_cleaned['medio']}'"
    assert "<b>" not in processed_item_cleaned['contenido_texto'], "HTML <b> tag not stripped"
    assert "  " not in processed_item_cleaned['contenido_texto'], "Extra spaces not normalized"
    assert processed_item_cleaned['etiquetas_fuente'] == ['dirty_test', 'test_tag'], f"etiquetas_fuente cleaning failed: got '{processed_item_cleaned['etiquetas_fuente']}'"

    validation_pipeline = DataValidationPipeline.from_crawler(mock_crawler_fixture)
    validation_pipeline.open_spider(spider)
    processed_item_validated = validation_pipeline.process_item(processed_item_cleaned, spider)

    assert processed_item_validated is not None, "Validation pipeline dropped cleaned item"
    assert 'error_validation' not in processed_item_validated, f"Cleaned item marked with validation error: {processed_item_validated.get('error_validation')}"

    storage_pipeline = SupabaseStoragePipeline.from_crawler(mock_crawler_fixture)
    storage_pipeline.open_spider(spider)
    mock_supabase_client = MagicMock()
    storage_pipeline.client = mock_supabase_client

    mock_upsert_result = MagicMock()
    mock_upsert_result.data = [{'id_primary': 'mock-dirty-id-101', 'url': processed_item_validated['url']}]
    mock_supabase_client.table.return_value.upsert.return_value.execute = MagicMock(return_value=mock_upsert_result)

    # Use the actual _generate_url_hash from the pipeline instance for the key
    url_hash_key = storage_pipeline._generate_url_hash(processed_item_validated['url'])
    expected_storage_path = f"html_content/{datetime.now(timezone.utc).year}/{datetime.now(timezone.utc).month:02d}/{url_hash_key}.html"

    # Determine what HTML content is expected for storage
    # If CLEANING_PRESERVE_HTML_FOR_STORAGE is True, original HTML is used.
    # Otherwise, the cleaned item's 'contenido_html' (if cleaning modifies it) or original.
    # For this test, let's assume original HTML is stored.
    html_content_for_storage = dirty_item_data_fixture['contenido_html']


    with patch.object(storage_pipeline, '_upload_html_content_with_retry', return_value=expected_storage_path) as mock_upload_html:
        final_item = storage_pipeline.process_item(processed_item_validated, spider)

    assert final_item is not None
    mock_supabase_client.table.assert_called_once_with(storage_pipeline.table_name)

    upsert_call_args = mock_supabase_client.table.return_value.upsert.call_args[0][0]
    assert upsert_call_args['titular'] == "A Dirty Title Test" # Check cleaned data sent to DB

    mock_upload_html.assert_called_once_with(url_hash_key, html_content_for_storage)

    assert final_item.get('storage_path') == expected_storage_path
    assert final_item.get('id_primary') == 'mock-dirty-id-101'

    storage_pipeline.close_spider(spider)
    validation_pipeline.close_spider(spider)
    if hasattr(cleaning_pipeline, 'close_spider'):
        cleaning_pipeline.close_spider(spider)


@pytest.fixture
def item_invalid_url_and_missing_titular_fixture():
    now_dt = datetime.now(timezone.utc)
    data = {
        'url': 'this is not a valid url', # Clearly invalid URL
        'fuente': 'mockspider_invalid_url_titular',
        'medio': 'Test Invalid URL & Titular Medio',
        # 'titular': 'This field is deliberately missing', # Missing 'titular'
        'fecha_publicacion': now_dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'contenido_texto': 'Some valid content for this invalid item test.',
        'pais_publicacion': 'Testlandia',
        'tipo_medio': 'Test Type',
        'fecha_recopilacion': now_dt,
        'contenido_html': '<p>Some HTML for invalid item</p>',
        'storage_path': '',
        'medio_url_principal': 'http://example.com', # This one can be valid for now
        'autor': 'Author Name',
        'idioma': 'es',
        'seccion': 'News',
        'etiquetas_fuente': [],
        'es_opinion': False,
        'es_oficial': False,
        'resumen': '',
        'categorias_asignadas': [],
        'puntuacion_relevancia': 0.0,
        'fecha_procesamiento': None,
        'estado_procesamiento': 'pendiente',
        'error_detalle': '',
        'metadata': {}
    }
    return data

@pytest.fixture
def item_missing_titular_fixture(): # Simplified invalid item
    now_dt = datetime.now(timezone.utc)
    data = {
        'url': 'http://example.com/missing_titular_test',
        'fuente': 'mockspider_invalid_titular',
        'medio': 'Test Missing Titular Medio',
        # 'titular': 'This field is deliberately missing', # Missing 'titular'
        'fecha_publicacion': now_dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'contenido_texto': 'Some valid content for this test.',
        'pais_publicacion': 'Testlandia',
        'tipo_medio': 'Test Type',
        'fecha_recopilacion': now_dt,
        'contenido_html': '<p>Some HTML</p>',
        # Add other fields to satisfy ArticuloInItem structure if not strictly required by validation for this test focus
        'storage_path': '',
        'medio_url_principal': 'http://example.com',
        'autor': 'Author Name',
        'idioma': 'es',
        'seccion': 'News',
        'etiquetas_fuente': [],
        'es_opinion': False,
        'es_oficial': False,
        'resumen': '',
        'categorias_asignadas': [],
        'puntuacion_relevancia': 0.0,
        'fecha_procesamiento': None,
        'estado_procesamiento': 'pendiente',
        'error_detalle': '',
        'metadata': {}
    }
    return data

def test_item_invalid_data_fails_validation(mock_crawler_fixture, item_invalid_url_and_missing_titular_fixture): # Use new fixture
    spider = mock_crawler_fixture.spider
    item = ArticuloInItem(item_invalid_url_and_missing_titular_fixture) # Use new fixture

    mock_crawler_fixture.settings['VALIDATION_DROP_INVALID_ITEMS'] = False
    # Ensure 'url' is validated as a URL. This is already in mock_crawler_fixture settings.
    # mock_crawler_fixture.settings['VALIDATION_URL_FIELDS'] = ['url', 'medio_url_principal']

    cleaning_pipeline = DataCleaningPipeline()
    if hasattr(cleaning_pipeline, 'from_crawler'):
        cleaning_pipeline = DataCleaningPipeline.from_crawler(mock_crawler_fixture)
    cleaning_pipeline.open_spider(spider)
    processed_item_cleaned = cleaning_pipeline.process_item(item, spider)
    assert processed_item_cleaned is not None

    validation_pipeline = DataValidationPipeline.from_crawler(mock_crawler_fixture)
    validation_pipeline.open_spider(spider)
    processed_item_validated = validation_pipeline.process_item(processed_item_cleaned, spider)

    assert processed_item_validated is not None
    assert 'error_validation' in processed_item_validated
    error_summary_validation = " ".join(processed_item_validated['error_validation']).lower()

    assert "titular" in error_summary_validation, "Validation error message does not mention missing 'titular'"
    assert "url" in error_summary_validation and ("format" in error_summary_validation or "valid" in error_summary_validation or "scheme" in error_summary_validation), \
        "Validation error message does not mention invalid URL format"


    storage_pipeline = SupabaseStoragePipeline.from_crawler(mock_crawler_fixture)
    storage_pipeline.open_spider(spider)
    mock_supabase_client = MagicMock()
    storage_pipeline.client = mock_supabase_client

    with patch.object(storage_pipeline, '_upload_html_content_with_retry') as mock_upload_html:
        final_item = storage_pipeline.process_item(processed_item_validated, spider)

    assert final_item is processed_item_validated
    mock_supabase_client.table.return_value.upsert.assert_not_called()
    mock_upload_html.assert_not_called()

    if hasattr(cleaning_pipeline, 'close_spider'):
        cleaning_pipeline.close_spider(spider)
    validation_pipeline.close_spider(spider)
    storage_pipeline.close_spider(spider)


# Assume Supabase client might raise generic Exception or a specific one.
# For tests, a generic Exception is often sufficient to simulate failure.
# from postgrest.exceptions import APIError # Example of a specific exception

def test_storage_pipeline_handles_upsert_error_gracefully(mock_crawler_fixture, valid_item_data_fixture):
    '''
    Tests that SupabaseStoragePipeline handles errors during the upsert operation gracefully.
    '''
    spider = mock_crawler_fixture.spider
    item = ArticuloInItem(valid_item_data_fixture)

    # Minimal cleaning and validation pass for this test's focus
    cleaning_pipeline = DataCleaningPipeline()
    if hasattr(cleaning_pipeline, 'from_crawler'):
        cleaning_pipeline = DataCleaningPipeline.from_crawler(mock_crawler_fixture)
    cleaning_pipeline.open_spider(spider)
    item_cleaned = cleaning_pipeline.process_item(item, spider)

    validation_pipeline = DataValidationPipeline.from_crawler(mock_crawler_fixture)
    validation_pipeline.open_spider(spider)
    item_validated = validation_pipeline.process_item(item_cleaned, spider)
    assert 'error_validation' not in item_validated, "Item unexpectedly failed validation before storage test"

    storage_pipeline = SupabaseStoragePipeline.from_crawler(mock_crawler_fixture)
    storage_pipeline.open_spider(spider)
    mock_supabase_client = MagicMock()
    storage_pipeline.client = mock_supabase_client

    # Simulate an error during the upsert operation
    simulated_db_error = Exception("Simulated DB Upsert Error")
    mock_supabase_client.table.return_value.upsert.return_value.execute.side_effect = simulated_db_error

    # We also need to mock _get_id_primary_from_response because it's called after execute()
    # and would fail if execute() raised an error and didn't return the expected structure.
    # Or, ensure the pipeline's try-except for upsert also covers _get_id_primary_from_response if it can fail.
    # For this test, if execute() fails, _get_id_primary_from_response might not be reached
    # if the exception is caught early. Let's assume the except block handles this.

    with patch.object(storage_pipeline, 'logger') as mock_pipeline_logger, \
         patch.object(storage_pipeline, '_upload_html_content_with_retry', return_value="mock/path.html") as mock_upload_html:

        processed_item_storage = storage_pipeline.process_item(item_validated, spider)

    assert processed_item_storage is not None, "Storage pipeline dropped item on upsert error"
    assert 'error_detalle' in processed_item_storage, "Item does not have 'error_detalle' after upsert failure"
    assert "Simulated DB Upsert Error" in processed_item_storage['error_detalle'], "Error message not correctly set"

    mock_pipeline_logger.error.assert_called_once()
    log_args, _ = mock_pipeline_logger.error.call_args
    assert "Error storing item" in log_args[0] # Check part of the log message
    assert item['url'] in log_args[1] # Check if URL is in log context
    assert str(simulated_db_error) in str(log_args[2]) # Check if exception is in log context

    # Depending on pipeline logic, if upsert fails, HTML upload might not be attempted.
    # If SupabaseStoragePipeline's process_item has a broad try-except around both upsert and upload,
    # then upload might still be tried or skipped. If it's sequential and upsert is first, upload won't run.
    # Let's assume if upsert fails, we don't proceed to upload.
    mock_upload_html.assert_not_called()


    # Check stats
    actual_stat_value = mock_crawler_fixture.stats.get_value('supabase/storage_errors', 0)
    assert actual_stat_value == 1, f"Supabase storage error stat incorrect: expected 1, got {actual_stat_value}"

    if hasattr(cleaning_pipeline, 'close_spider'): cleaning_pipeline.close_spider(spider)
    validation_pipeline.close_spider(spider)
    storage_pipeline.close_spider(spider)

def test_storage_pipeline_handles_html_upload_error_gracefully(mock_crawler_fixture, valid_item_data_fixture):
    '''
    Tests that SupabaseStoragePipeline handles errors during HTML content upload gracefully.
    '''
    spider = mock_crawler_fixture.spider
    item = ArticuloInItem(valid_item_data_fixture)

    # Simulate item has passed previous steps and has an ID
    item['id_primary'] = 'test-id-for-html-upload-123'

    storage_pipeline = SupabaseStoragePipeline.from_crawler(mock_crawler_fixture)
    storage_pipeline.open_spider(spider)
    mock_supabase_client = MagicMock()
    storage_pipeline.client = mock_supabase_client

    # Simulate successful upsert (or assume it happened and id_primary is set)
    mock_upsert_result = MagicMock()
    mock_upsert_result.data = [{'id_primary': item['id_primary'], 'url': item['url']}]
    mock_supabase_client.table.return_value.upsert.return_value.execute = MagicMock(return_value=mock_upsert_result)

    # Simulate an error during HTML upload by making _upload_html_content_with_retry raise an exception
    simulated_html_error = Exception("Simulated HTML Upload Error")
    # We patch the method within the already instantiated pipeline object
    with patch.object(storage_pipeline, 'logger') as mock_pipeline_logger, \
         patch.object(storage_pipeline, '_upload_html_content_with_retry', side_effect=simulated_html_error) as mock_upload_call:

        processed_item_storage = storage_pipeline.process_item(item, spider)

    assert processed_item_storage is not None
    assert 'error_detalle' in processed_item_storage
    assert "Simulated HTML Upload Error" in processed_item_storage['error_detalle']
    # storage_path should not be set, or be empty, if upload failed
    assert not processed_item_storage.get('storage_path'), "storage_path was set despite HTML upload error"


    mock_pipeline_logger.error.assert_called_once()
    log_args, _ = mock_pipeline_logger.error.call_args
    assert "Error uploading HTML content" in log_args[0] # Check part of log message
    assert item['url'] in log_args[1] # Check URL in log context
    assert str(simulated_html_error) in str(log_args[2]) # Check exception in log context

    mock_upload_call.assert_called_once() # Make sure the _upload_html_content_with_retry method was attempted

    actual_stat_value = mock_crawler_fixture.stats.get_value('supabase/storage_errors', 0)
    assert actual_stat_value == 1, f"Supabase storage error stat for HTML incorrect: expected 1, got {actual_stat_value}"

    storage_pipeline.close_spider(spider)
