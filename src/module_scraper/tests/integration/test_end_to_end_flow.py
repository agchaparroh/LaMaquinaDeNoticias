import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import json # For metadata if needed

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.spiders import Spider
from scrapy import Request

from scraper_core.items import ArticuloInItem
# Assuming pipeline classes are accessible for direct import if needed for setup,
# but end-to-end tests often rely on Scrapy to instantiate them based on settings.
# We will need SupabaseStoragePipeline for patching its methods at class level.
from scraper_core.pipelines.storage import SupabaseStoragePipeline


# Spider for end-to-end data integrity test
class DataIntegritySpider(Spider):
    name = 'dataintegrityspider'
    start_urls = ['http://httpbin.org/html'] # Simple, static HTML page

    custom_settings = {
        'DOWNLOAD_HANDLERS': { # Ensure a simple, predictable setup
            'http': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
            'https': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
        },
        'TWISTED_REACTOR': None, # Default reactor
        'ROBOTSTXT_OBEY': False, # Disable for this test
        'CRAWL_ONCE_ENABLED': False, # Disable for this test
        'ITEM_PIPELINES': { # Define the full pipeline for this e2e test
            'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
            'scraper_core.pipelines.validation.DataValidationPipeline': 300,
            'scraper_core.pipelines.storage.SupabaseStoragePipeline': 400,
        },
    }

    expected_titular_cleaned = "Herman Melville - Moby-Dick; or, The Whale"
    # This is what httpbin.org/html's <h1> contains. Cleaning should preserve it if already clean.

    def parse(self, response):
        now_dt = datetime.now(timezone.utc)
        item = ArticuloInItem()

        item['url'] = response.url
        # Extract raw titular, might have leading/trailing spaces from some sites
        item['titular'] = "  " + response.xpath('//h1/text()').get() + "  "

        # Simulate complex raw text that needs cleaning
        raw_text_parts = response.xpath('//p/text() | //body/text()[normalize-space() and not(parent::h1) and not(parent::title)]').getall()
        # Intentionally make it a bit messy for cleaning pipeline to process
        item['contenido_texto'] = "\n  " + "    ".join(p.strip() for p in raw_text_parts if p.strip()).replace('\n', ' ') + "  Trailing space. "

        item['fuente'] = self.name
        item['medio'] = 'httpbin.org_e2e_test' # Spider sets this
        item['pais_publicacion'] = 'Testland E2E Flow'
        item['tipo_medio'] = 'Test E2E Flow Site'
        item['fecha_publicacion'] = now_dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        item['fecha_recopilacion'] = now_dt
        item['contenido_html'] = response.text # Store raw HTML

        # Populate other fields for item completeness
        item['storage_path'] = ''
        item['medio_url_principal'] = 'http://httpbin.org'
        item['autor'] = 'E2E Test Author'
        item['idioma'] = 'en'
        item['seccion'] = 'E2E Test Section'
        item['etiquetas_fuente'] = ['e2e_flow', 'integrity_test']
        item['es_opinion'] = False
        item['es_oficial'] = False
        item['resumen'] = ''
        item['categorias_asignadas'] = []
        item['puntuacion_relevancia'] = 0.0
        item['fecha_procesamiento'] = None
        item['estado_procesamiento'] = 'pendiente'
        item['error_detalle'] = ''
        item['metadata'] = {'e2e_test_source': 'httpbin_html'}

        yield item

# Global variables to capture arguments passed to mocked Supabase operations
mock_supabase_upsert_args = None
mock_supabase_upload_args = None
# Global variable to capture the item as processed by the (mocked) storage pipeline
mock_item_after_storage_pipeline = None


@pytest.fixture(scope="function", autouse=True)
def reset_e2e_global_mocks(request):
    # Automatically resets global mock capture variables before each test in this module.
    # This ensures test isolation for captured arguments.
    global mock_supabase_upsert_args, mock_supabase_upload_args, mock_item_after_storage_pipeline
    mock_supabase_upsert_args = None
    mock_supabase_upload_args = None
    mock_item_after_storage_pipeline = None

# The actual test function 'test_data_integrity_e2e_flow' will be added in a subsequent step.


@pytest.mark.asyncio
async def test_data_integrity_e2e_flow(tmp_path, reset_e2e_global_mocks): # Added reset_e2e_global_mocks for clarity, though autouse=True means it runs anyway
    '''
    Tests data integrity from spider extraction through pipelines to (mocked) storage.
    It uses global variables (mock_supabase_upsert_args, etc.) to capture data for assertions.
    '''
    global mock_supabase_upsert_args, mock_supabase_upload_args, mock_item_after_storage_pipeline

    settings = get_project_settings()
    settings.setmodule('tests.config.test_settings', priority='project')

    # Ensure ITEM_PIPELINES are set for the e2e flow as defined in DataIntegritySpider.custom_settings
    # or override them here if custom_settings are not picked up by CrawlerProcess in this context.
    # DataIntegritySpider.custom_settings should ideally be used.
    # If not, explicitly set them:
    settings['ITEM_PIPELINES'] = {
        'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
        'scraper_core.pipelines.validation.DataValidationPipeline': 300,
        'scraper_core.pipelines.storage.SupabaseStoragePipeline': 400,
    }
    settings['SUPABASE_URL'] = 'http://mock-e2e.supabase.co' # Needed for pipeline init
    settings['SUPABASE_SERVICE_ROLE_KEY'] = 'mock-e2e-key'    # Needed for pipeline init
    settings['SUPABASE_HTML_BUCKET'] = 'mock-e2e-bucket'      # Needed for pipeline init
    settings['SCRAPY_PROJECT_ROOT'] = str(tmp_path) # For any file path needs

    # This function will be the side_effect for the mocked client's upsert method's execute call.
    # It captures the arguments and returns a mock success object.
    def capture_upsert_and_return_mock_execute(data_dict_for_db, **kwargs):
        nonlocal mock_supabase_upsert_args # To modify the global variable from the outer scope
        mock_supabase_upsert_args = data_dict_for_db

        # Simulate the structure that _get_id_primary_from_response expects
        mock_execute_response = MagicMock()
        # Ensure the 'url' in the response matches the item's URL if possible, or is a valid string
        url_in_item = data_dict_for_db.get('url', 'http://mockurl.com/default')
        mock_execute_response.data = [{'id_primary': 'mock_e2e_upsert_id_123', 'url': url_in_item}]
        return mock_execute_response

    # This function will be the side_effect for the mocked _upload_html_content_with_retry method.
    def capture_upload_and_return_path(url_hash_key, html_to_upload, item_url_for_log): # Match expected signature
        nonlocal mock_supabase_upload_args # To modify global
        mock_supabase_upload_args = {'key': url_hash_key, 'html_content': html_to_upload, 'item_url': item_url_for_log}
        # Return a plausible storage path
        year = datetime.now(timezone.utc).year
        month = datetime.now(timezone.utc).month
        return f"html_content/{year}/{month:02d}/{url_hash_key}.html"

    # This function will be the side_effect for the storage pipeline's process_item method.
    # It calls the original process_item but captures the returned item.
    original_process_item = SupabaseStoragePipeline.process_item
    def capture_item_after_storage(pipeline_instance, item, spider):
        nonlocal mock_item_after_storage_pipeline # To modify global
        # Call the original method to ensure full processing by the (mocked) pipeline
        processed_item = original_process_item(pipeline_instance, item, spider)
        mock_item_after_storage_pipeline = processed_item
        return processed_item

    # Patching strategy:
    # 1. Mock the 'client' attribute of SupabaseStoragePipeline instances.
    #    The mocked client's chained calls .table().upsert().execute() need to lead to our capture function.
    # 2. Mock the '_upload_html_content_with_retry' method of SupabaseStoragePipeline.
    # 3. Mock the 'process_item' method of SupabaseStoragePipeline to capture the final item.

    # Using new_callable=MagicMock for 'client' allows us to configure the mock instance.
    with patch.object(SupabaseStoragePipeline, 'client', new_callable=MagicMock) as mock_client_instance, \
         patch.object(SupabaseStoragePipeline, '_upload_html_content_with_retry', side_effect=capture_upload_and_return_path) as mock_upload_method, \
         patch.object(SupabaseStoragePipeline, 'process_item', side_effect=capture_item_after_storage) as mock_process_item_storage:

        # Configure the mock_client_instance that will be assigned to pipeline.client
        # self.client.table(self.table_name).upsert(item_dict).execute()
        mock_client_instance.table.return_value.upsert.return_value.execute.side_effect = capture_upsert_and_return_mock_execute

        process = CrawlerProcess(settings)
        # Spider's custom_settings should take precedence for ITEM_PIPELINES if defined there and picked up.
        # If not, the settings object passed to CrawlerProcess is the fallback.
        await process.crawl(DataIntegritySpider)
        # No process.start() needed, await crawl() handles it for a single crawl.

    # Assertions will be added in the next step, using the captured global variables.
    # For now, this step just ensures the crawl runs with mocks.
    assert mock_supabase_upsert_args is not None, "Mock for upsert was not called or args not captured."
    assert mock_supabase_upload_args is not None, "Mock for HTML upload was not called or args not captured."
    assert mock_item_after_storage_pipeline is not None, "Mock for storage pipeline process_item was not called or item not captured."

    # --- Start of assertions ---
    assert mock_supabase_upsert_args is not None, "Supabase upsert was not called (args not captured)."
    assert mock_supabase_upload_args is not None, "Supabase upload HTML was not called (args not captured)."
    assert mock_item_after_storage_pipeline is not None, "Storage pipeline did not process/return an item (or capture failed)."

    # Retrieve the spider instance to access its expected_titular_cleaned for comparison
    # This is a bit indirect; ideally, the test wouldn't rely on crawling into CrawlerProcess internals.
    # However, for this specific check, it's useful.
    # Note: Accessing _spider_loader like this is an internal detail.
    # A cleaner way if needed often is to pass expected values into the test or have spider store them on itself.
    # For now, let's assume DataIntegritySpider.expected_titular_cleaned is accessible or known.
    expected_titular_cleaned_value = DataIntegritySpider.expected_titular_cleaned

    # 1. Verify Titular (cleaned)
    # The spider yields "  Herman Melville - Moby-Dick; or, The Whale  "
    # Cleaning pipeline should strip whitespace.
    assert mock_supabase_upsert_args.get('titular') == expected_titular_cleaned_value, \
        f"Titular mismatch. Expected (cleaned): '{expected_titular_cleaned_value}', Got: '{mock_supabase_upsert_args.get('titular')}'"

    # 2. Verify Contenido_texto (cleaned)
    # Spider yields: "\n  " + "    ".join(p.strip() for p in raw_text_parts if p.strip()).replace('\n', ' ') + "  Trailing space. "
    # Cleaning pipeline should strip leading/trailing whitespace and normalize internal whitespace.
    # Exact match is hard due to complex joining in spider, so check for key properties:
    assert "Herman Melville - Moby-Dick" in mock_supabase_upsert_args.get('contenido_texto'), \
        "Key content missing from cleaned contenido_texto"
    assert mock_supabase_upsert_args.get('contenido_texto').startswith("Herman Melville"), \
        "Cleaned contenido_texto does not start as expected or has leading whitespace."
    assert not mock_supabase_upsert_args.get('contenido_texto').endswith("  "), \
        "Cleaned contenido_texto has unexpected trailing whitespace."
    assert "    " not in mock_supabase_upsert_args.get('contenido_texto'), \
        "Cleaned contenido_texto seems to have multiple spaces not normalized."

    # 3. Verify Medio (should be as set by spider)
    assert mock_supabase_upsert_args.get('medio') == 'httpbin.org_e2e_test', \
        f"Medio mismatch. Expected: 'httpbin.org_e2e_test', Got: '{mock_supabase_upsert_args.get('medio')}'"

    # 4. Verify URL (should be original URL from spider's start_urls)
    assert mock_supabase_upsert_args.get('url') == DataIntegritySpider.start_urls[0], \
        f"URL mismatch. Expected: '{DataIntegritySpider.start_urls[0]}', Got: '{mock_supabase_upsert_args.get('url')}'"

    # 5. Verify HTML content for storage (should be original HTML from response)
    # The spider sets item['contenido_html'] = response.text
    assert "<h1>Herman Melville - Moby-Dick; or, The Whale</h1>" in mock_supabase_upload_args.get('html_content'), \
        "Key H1 tag missing from HTML content intended for storage."
    assert mock_supabase_upload_args.get('item_url') == DataIntegritySpider.start_urls[0], \
        "Item URL passed to upload function is incorrect."


    # 6. Verify item after storage pipeline processing
    # Check fields set by the (mocked) storage pipeline based on mocked return values
    final_item = mock_item_after_storage_pipeline
    assert final_item.get('id_primary') == 'mock_e2e_upsert_id_123', \
        f"id_primary mismatch. Expected: 'mock_e2e_upsert_id_123', Got: '{final_item.get('id_primary')}'"

    # The expected_storage_path depends on the key used (url_hash) and the mocked return from capture_upload_and_return_path
    # The key used in capture_upload_and_return_path is url_hash_key.
    # We need to know what that hash was. The mock_supabase_upload_args['key'] will have it.
    expected_key = mock_supabase_upload_args.get('key')
    year = datetime.now(timezone.utc).year
    month = datetime.now(timezone.utc).month
    expected_path_check = f"html_content/{year}/{month:02d}/{expected_key}.html"
    assert final_item.get('storage_path') == expected_path_check, \
        f"storage_path mismatch. Expected: '{expected_path_check}', Got: '{final_item.get('storage_path')}'"

    # 7. Verify 'fuente' (spider name)
    assert mock_supabase_upsert_args.get('fuente') == DataIntegritySpider.name, \
        f"Fuente mismatch. Expected: '{DataIntegritySpider.name}', Got: '{mock_supabase_upsert_args.get('fuente')}'"


    # Note: To verify stats, you would typically access crawler.stats after the crawl.
    # This is possible if you can get a reference to the crawler instance used by CrawlerProcess.
    # For example:
    # crawler = next(iter(process.crawlers)) # Gets the first crawler instance
    # stats = crawler.stats.get_stats()
    # assert stats.get('item_scraped_count') == 1
    # assert stats.get('pipeline/validation/passed') == 1 # Example custom stat
    # This part is omitted for now as getting crawler from process can be version-dependent.
    # The primary check is the data integrity via captured arguments.

    # --- Start of NEW statistics assertions ---

    # Access the crawler instance to get stats.
    # CrawlerProcess().crawlers is a set of all crawlers managed by this process.
    # Since we run only one crawl here, it should contain one crawler.
    assert len(process.crawlers) == 1, "Expected one crawler in the process"
    crawler_instance = list(process.crawlers)[0] # Get the crawler instance
    stats = crawler_instance.stats.get_stats()

    assert stats is not None, "Failed to get stats from crawler."

    # 1. Standard Scrapy stats
    assert stats.get('item_scraped_count') == 1, \
        f"Expected 1 item scraped, got {stats.get('item_scraped_count')}"
    assert stats.get('downloader/request_count') == 1, \
        f"Expected 1 request, got {stats.get('downloader/request_count')}" # Assumes no redirects or retries for httpbin.org/html
    assert stats.get('downloader/response_count') == 1, \
        f"Expected 1 response, got {stats.get('downloader/response_count')}"
    assert stats.get('downloader/response_status_count/200') == 1, \
        f"Expected 1 response with status 200, got {stats.get('downloader/response_status_count/200')}"
    assert stats.get('finish_reason') == 'finished', \
        f"Expected finish_reason 'finished', got {stats.get('finish_reason')}"

    # 2. Pipeline-specific stats (if pipelines are designed to emit them)
    # These depend on your actual pipeline implementations.
    # Example: Check if DataValidationPipeline emits a stat for passed items.
    # This requires DataValidationPipeline to call self.stats.inc_value('validation/passed') or similar.
    # For this test, let's assume it might emit 'pipeline/validation/items_passed'.
    # If your validation pipeline (DataValidationPipeline) is set up to record stats:
    # assert stats.get('pipeline/validation/items_passed', 0) == 1,     #    "Validation pipeline did not record a passed item (check stat name and pipeline logic)"

    # Check stats from mocked SupabaseStoragePipeline (if it increments stats for success)
    # Our SupabaseStoragePipeline currently increments 'supabase/items_stored' and 'supabase/html_stored' on success.
    # Since we mocked its process_item to capture the item and did not run the original for this part,
    # these stats would not be incremented by the *original* pipeline.
    # However, the capture function for process_item could increment a test-specific stat,
    # or we can assume the mocked operations imply success.
    # For this test, we'll assume the core functionality test via captured_args is sufficient,
    # and that if storage pipeline were *not* mocked, it *would* increment these.
    # If SupabaseStoragePipeline's actual `process_item` (before mocking for capture) increments stats:
    # assert stats.get('supabase/items_stored', 0) == 1, "Supabase items_stored stat not incremented"
    # assert stats.get('supabase/html_stored', 0) == 1, "Supabase html_stored stat not incremented"

    # For the purpose of this test, the main check is that standard Scrapy stats are correct.
    # Custom stats from pipelines would require those pipelines to explicitly call stats.inc_value().
    # The current SupabaseStoragePipeline (from previous context) does call:
    # self.stats.inc_value('supabase/items_stored')
    # self.stats.inc_value('supabase/html_stored')
    # self.stats.inc_value('supabase/storage_errors')
    # Since we used a side_effect to wrap the original process_item for SupabaseStoragePipeline
    # (`capture_item_after_storage` calls `original_process_item`), these stats *should* be collected.

    assert stats.get('supabase/items_stored', 0) == 1, \
        f"Expected 'supabase/items_stored' to be 1, got {stats.get('supabase/items_stored', 0)}"
    assert stats.get('supabase/html_stored', 0) == 1, \
        f"Expected 'supabase/html_stored' to be 1, got {stats.get('supabase/html_stored', 0)}"
    assert stats.get('supabase/storage_errors', 0) == 0, \
        f"Expected 'supabase/storage_errors' to be 0 for successful flow, got {stats.get('supabase/storage_errors', 0)}"


    # --- End of NEW statistics assertions ---


class PlaywrightMetadataSpider(Spider):
    name = 'playwrightmetadataspider'
    # Using a site that requires JS, quotes.toscrape.com/js/ is good.
    # Or httpbin.org/headers to check Playwright's User-Agent. Let's use /js for content.
    start_urls = ['https://quotes.toscrape.com/js/']

    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        'PLAYWRIGHT_LAUNCH_OPTIONS': {"headless": True},
        'ROBOTSTXT_OBEY': False,
        'CRAWL_ONCE_ENABLED': False,
        'ITEM_PIPELINES': { # Full pipeline
            'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
            'scraper_core.pipelines.validation.DataValidationPipeline': 300,
            'scraper_core.pipelines.storage.SupabaseStoragePipeline': 400,
        },
        # Ensure playwright_custom_middleware.PlaywrightCustomDownloaderMiddleware is active if it's separate
        # It is part of the default middlewares in settings.py, so should be included.
    }

    async def parse(self, response):
        now_dt = datetime.now(timezone.utc)
        item = ArticuloInItem()

        page = response.meta.get('playwright_page')
        assert page is not None, "Playwright page object missing in response.meta"

        # Example: Extract something that relies on JS execution
        # On quotes.toscrape.com/js/, quotes are in <div class="quote">
        # Let's get the count of quotes as a piece of metadata.
        try:
            await page.wait_for_selector("div.quote", timeout=5000)
        except Exception: # Playwright TimeoutError
            self.logger.warning("Timeout waiting for div.quote on Playwright page.")
            # Fallback or error state for item if needed
            item['metadata'] = {'playwright_info': 'div.quote not found', 'quote_count': 0}
        else:
            quotes_count = len(await page.query_selector_all("div.quote"))
            item['metadata'] = {'playwright_info': 'processed_with_playwright', 'quote_count': quotes_count}


        item['url'] = response.url
        item['titular'] = await page.title() # Get title via Playwright
        item['contenido_texto'] = f"Page content from {response.url} processed by Playwright. Title: {item['titular']}. Quotes found: {item['metadata'].get('quote_count', 0)}"

        # Standard fields
        item['fuente'] = self.name
        item['medio'] = 'quotes.toscrape.com'
        item['pais_publicacion'] = 'PlaywrightLand'
        item['tipo_medio'] = 'JS Site'
        item['fecha_publicacion'] = now_dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        item['fecha_recopilacion'] = now_dt
        item['contenido_html'] = await page.content() # Get full HTML after JS

        # Populate other fields for item completeness
        item['storage_path'] = ''
        item['medio_url_principal'] = 'https://quotes.toscrape.com'
        item['autor'] = 'Playwright Author'
        item['idioma'] = 'en'
        item['seccion'] = 'JS Quotes'
        item['etiquetas_fuente'] = ['playwright_e2e', 'js_test']
        item['es_opinion'] = False
        item['es_oficial'] = False
        item['resumen'] = ''
        item['categorias_asignadas'] = []
        item['puntuacion_relevancia'] = 0.0
        item['fecha_procesamiento'] = None
        item['estado_procesamiento'] = 'pendiente'
        item['error_detalle'] = ''
        # metadata already set above

        if page: # Close the page if it was included
            await page.close()

        yield item

    def start_requests(self):
        for url in self.start_urls:
            # Request Playwright processing and include the page
            yield Request(url, meta={'playwright': True, 'playwright_include_page': True}, callback=self.parse)


@pytest.mark.asyncio
async def test_playwright_metadata_e2e_flow(tmp_path, reset_e2e_global_mocks):
    global mock_supabase_upsert_args, mock_supabase_upload_args, mock_item_after_storage_pipeline

    settings = get_project_settings()
    settings.setmodule('tests.config.test_settings', priority='project')
    # Spider's custom_settings should handle ITEM_PIPELINES, DOWNLOAD_HANDLERS, TWISTED_REACTOR etc.
    # Ensure Supabase settings for pipeline init
    settings['SUPABASE_URL'] = 'http://mock-e2e-pw.supabase.co'
    settings['SUPABASE_SERVICE_ROLE_KEY'] = 'mock-e2e-pw-key'
    settings['SUPABASE_HTML_BUCKET'] = 'mock-e2e-pw-bucket'
    settings['SCRAPY_PROJECT_ROOT'] = str(tmp_path)

    # Define capture functions (can be reused or made more generic if placed in fixture)
    def capture_upsert_pw(data_dict_for_db, **kwargs):
        nonlocal mock_supabase_upsert_args
        mock_supabase_upsert_args = data_dict_for_db
        # Simulate the structure that _get_id_primary_from_response expects
        mock_execute_response = MagicMock()
        # Ensure the 'url' in the response matches the item's URL if possible, or is a valid string
        url_in_item = data_dict_for_db.get('url', 'http://mockurl.com/default') # Use a default if 'url' isn't in data_dict_for_db
        mock_execute_response.data = [{'id_primary': 'mock_pw_e2e_id_456', 'url': url_in_item}]
        return mock_execute_response


    def capture_upload_pw(url_hash_key, html_to_upload, item_url_for_log):
        nonlocal mock_supabase_upload_args
        mock_supabase_upload_args = {'key': url_hash_key, 'html_content': html_to_upload, 'item_url': item_url_for_log}
        year = datetime.now(timezone.utc).year; month = datetime.now(timezone.utc).month
        return f"html_content/{year}/{month:02d}/{url_hash_key}.html"

    original_pw_process_item = SupabaseStoragePipeline.process_item
    def capture_item_after_storage_pw(pipeline_instance, item, spider):
        nonlocal mock_item_after_storage_pipeline
        processed_item = original_pw_process_item(pipeline_instance, item, spider)
        mock_item_after_storage_pipeline = processed_item
        return processed_item

    with patch.object(SupabaseStoragePipeline, 'client', new_callable=MagicMock) as mock_client_pw, \
         patch.object(SupabaseStoragePipeline, '_upload_html_content_with_retry', side_effect=capture_upload_pw) as mock_upload_pw, \
         patch.object(SupabaseStoragePipeline, 'process_item', side_effect=capture_item_after_storage_pw) as mock_process_item_pw:

        # Corrected mock setup for the client:
        # The side_effect should be on the 'execute' method, not the return_value of execute.
        mock_client_pw.table.return_value.upsert.return_value.execute.side_effect = capture_upsert_pw

        process = CrawlerProcess(settings)
        await process.crawl(PlaywrightMetadataSpider)

    assert mock_supabase_upsert_args is not None, "Upsert not called for Playwright item"
    assert mock_supabase_upload_args is not None, "HTML upload not called for Playwright item"
    assert mock_item_after_storage_pipeline is not None, "Storage pipeline process_item not called for Playwright item"

    # Assertions for Playwright metadata / JS-dependent data
    # 1. Check metadata field in upserted data
    upserted_metadata = mock_supabase_upsert_args.get('metadata', {})
    assert upserted_metadata.get('playwright_info') == 'processed_with_playwright'
    assert upserted_metadata.get('quote_count', -1) > 0 # Expecting at least one quote

    # 2. Check titular (obtained via page.title())
    assert "Quotes to Scrape" in mock_supabase_upsert_args.get('titular'), \
        "Titular from Playwright page.title() seems incorrect"

    # 3. Check contenido_html (obtained via page.content() after JS)
    # It should contain quotes, which are loaded by JS.
    assert '<div class="quote">' in mock_supabase_upload_args.get('html_content'), \
        "HTML content for storage doesn't seem to include JS-loaded quotes."

    # 4. Check final item state
    final_item_pw = mock_item_after_storage_pipeline
    assert final_item_pw.get('id_primary') == 'mock_pw_e2e_id_456'
    final_item_metadata = final_item_pw.get('metadata', {})
    assert final_item_metadata.get('quote_count', -1) > 0

    # 5. Check that the URL is correct
    assert mock_supabase_upsert_args.get('url') == PlaywrightMetadataSpider.start_urls[0]


class ErrorRecoverySpider(Spider):
    name = 'errorrecoveryspider'

    # URL1 will initially fail then succeed. URL2 will always succeed.
    url_retry_once = 'http://httpbin.org/status/500,200' # httpbin.org endpoint to control response sequence
    url_always_ok = 'http://httpbin.org/html' # Standard simple HTML page

    start_urls = [url_retry_once, url_always_ok]

    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
            'https': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
        },
        'TWISTED_REACTOR': None,
        'ROBOTSTXT_OBEY': False,
        'CRAWL_ONCE_ENABLED': False, # Disable to ensure both URLs are processed distinctly if test is re-run
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 2, # Allow retries
        'RETRY_HTTP_CODES': [500], # Ensure 500 is retried
        'ITEM_PIPELINES': {
            'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
            'scraper_core.pipelines.validation.DataValidationPipeline': 300,
            'scraper_core.pipelines.storage.SupabaseStoragePipeline': 400,
        },
    }

    def parse(self, response):
        now_dt = datetime.now(timezone.utc)
        item = ArticuloInItem()
        item['url'] = response.url

        if response.url == self.url_retry_once:
            # This URL should have initially returned 500, then 200 on retry.
            # httpbin.org/status/500,200 returns 500 first, then 200.
            # The response.text for a 200 from this endpoint is empty.
            item['titular'] = "Item From Retry Success"
            item['contenido_texto'] = "Content after retry for " + response.url
            item['contenido_html'] = "<html><body>Retry Success</body></html>"
            item['medio'] = 'httpbin.org_retry_status'
        elif response.url == self.url_always_ok:
            item['titular'] = response.xpath('//h1/text()').get().strip()
            raw_text_parts = response.xpath('//p/text() | //body/text()[normalize-space() and not(parent::h1) and not(parent::title)]').getall()
            item['contenido_texto'] = " ".join(p.strip() for p in raw_text_parts if p.strip()).replace('\n', ' ').strip()
            item['contenido_html'] = response.text
            item['medio'] = 'httpbin.org_html_ok'
        else: # Should not happen
            item['titular'] = "Unknown URL source in E2E Error Recovery"
            item['contenido_texto'] = "Error: Unknown URL processed."
            item['contenido_html'] = "<html><body>Error</body></html>"
            item['medio'] = 'unknown_error_source'

        # Common fields
        item['fuente'] = self.name
        item['pais_publicacion'] = 'Testland E2E Recovery'
        item['tipo_medio'] = 'Test E2E Recovery Site'
        item['fecha_publicacion'] = now_dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        item['fecha_recopilacion'] = now_dt
        item['storage_path'] = ''
        item['medio_url_principal'] = 'http://httpbin.org'
        item['autor'] = 'E2E Recovery Author'
        item['idioma'] = 'en'
        item['seccion'] = 'E2E Recovery Section'
        item['etiquetas_fuente'] = ['e2e_recovery', 'resilience_test']
        item['es_opinion'] = False
        item['es_oficial'] = False
        item['resumen'] = ''
        item['categorias_asignadas'] = []
        item['puntuacion_relevancia'] = 0.0
        item['fecha_procesamiento'] = None
        item['estado_procesamiento'] = 'pendiente'
        item['error_detalle'] = ''
        item['metadata'] = {'test_type': 'error_recovery', 'original_url_for_item': response.url}

        yield item

@pytest.mark.asyncio
async def test_error_recovery_e2e_flow(tmp_path, reset_e2e_global_mocks):
    global mock_supabase_upsert_args, mock_supabase_upload_args, mock_item_after_storage_pipeline

    # We need to capture multiple items, so let's make these lists
    captured_upserts = []
    captured_uploads = []
    captured_final_items = []

    # Modify reset fixture or manually reset here for list-based capture
    mock_supabase_upsert_args = None # Will be overwritten by list append
    mock_supabase_upload_args = None
    mock_item_after_storage_pipeline = None


    settings = get_project_settings()
    settings.setmodule('tests.config.test_settings', priority='project')
    # Spider's custom_settings should handle ITEM_PIPELINES, RETRY_SETTINGS etc.
    settings['SUPABASE_URL'] = 'http://mock-e2e-recovery.supabase.co'
    settings['SUPABASE_SERVICE_ROLE_KEY'] = 'mock-e2e-recovery-key'
    settings['SUPABASE_HTML_BUCKET'] = 'mock-e2e-recovery-bucket'
    settings['SCRAPY_PROJECT_ROOT'] = str(tmp_path)

    def capture_upsert_recovery(data_dict_for_db, **kwargs):
        nonlocal captured_upserts
        captured_upserts.append(data_dict_for_db)
        execute_mock = MagicMock()
        url_in_item = data_dict_for_db.get('url', '')
        # Differentiate mock IDs for different items
        mock_id = f"mock_recovery_id_{len(captured_upserts)}"
        execute_mock.data = [{'id_primary': mock_id, 'url': url_in_item}] # Corrected: set data on the mock object directly
        return execute_mock

    def capture_upload_recovery(url_hash_key, html_to_upload, item_url_for_log):
        nonlocal captured_uploads
        captured_uploads.append({'key': url_hash_key, 'html_content': html_to_upload, 'item_url': item_url_for_log})
        year = datetime.now(timezone.utc).year; month = datetime.now(timezone.utc).month
        return f"html_content/{year}/{month:02d}/{url_hash_key}.html_{len(captured_uploads)}"

    original_recovery_process_item = SupabaseStoragePipeline.process_item
    def capture_item_after_storage_recovery(pipeline_instance, item, spider):
        nonlocal captured_final_items
        processed_item = original_recovery_process_item(pipeline_instance, item, spider)
        captured_final_items.append(processed_item)
        return processed_item

    with patch.object(SupabaseStoragePipeline, 'client', new_callable=MagicMock) as mock_client_recovery, \
         patch.object(SupabaseStoragePipeline, '_upload_html_content_with_retry', side_effect=capture_upload_recovery) as mock_upload_recovery, \
         patch.object(SupabaseStoragePipeline, 'process_item', side_effect=capture_item_after_storage_recovery) as mock_process_item_recovery:

        mock_client_recovery.table.return_value.upsert.return_value.execute.side_effect = capture_upsert_recovery

        process = CrawlerProcess(settings)
        # Need to get crawler to check stats later
        # crawler = process.create_crawler(ErrorRecoverySpider)
        # await process.crawl(crawler) # This is one way
        await process.crawl(ErrorRecoverySpider)


    assert len(captured_upserts) == 2, f"Expected 2 items to be upserted, got {len(captured_upserts)}"
    assert len(captured_uploads) == 2, f"Expected 2 HTML contents to be uploaded, got {len(captured_uploads)}"
    assert len(captured_final_items) == 2, f"Expected 2 items from storage pipeline, got {len(captured_final_items)}"

    # Sort items by URL to make assertions predictable if order isn't guaranteed
    captured_upserts.sort(key=lambda x: x.get('url', ''))
    captured_uploads.sort(key=lambda x: x.get('item_url', '')) # Assuming item_url is the original URL
    captured_final_items.sort(key=lambda x: x.get('url', ''))


    # Item 1 (from url_always_ok: http://httpbin.org/html)
    item1_upsert = next(u for u in captured_upserts if u['url'] == ErrorRecoverySpider.url_always_ok)
    item1_upload = next(u for u in captured_uploads if u['item_url'] == ErrorRecoverySpider.url_always_ok)
    item1_final = next(i for i in captured_final_items if i['url'] == ErrorRecoverySpider.url_always_ok)

    assert "Herman Melville - Moby-Dick" in item1_upsert.get('titular')
    assert "Herman Melville - Moby-Dick" in item1_upload.get('html_content') # Check raw HTML
    assert item1_final.get('id_primary') is not None
    assert ErrorRecoverySpider.url_always_ok in item1_final.get('storage_path', '')


    # Item 2 (from url_retry_once: http://httpbin.org/status/500,200)
    item2_upsert = next(u for u in captured_upserts if u['url'] == ErrorRecoverySpider.url_retry_once)
    item2_upload = next(u for u in captured_uploads if u['item_url'] == ErrorRecoverySpider.url_retry_once)
    item2_final = next(i for i in captured_final_items if i['url'] == ErrorRecoverySpider.url_retry_once)

    assert item2_upsert.get('titular') == "Item From Retry Success"
    assert "Retry Success" in item2_upload.get('html_content') # Check raw HTML
    assert item2_final.get('id_primary') is not None
    assert ErrorRecoverySpider.url_retry_once in item2_final.get('storage_path', '') # Path might not contain full URL

    # Check retry stats from the crawler instance
    # This requires getting the crawler from CrawlerProcess, which can be tricky.
    # For now, the successful processing of both items (one after retry) is the main check.
    # If a crawler instance `cr` was obtained:
    # stats = cr.stats.get_stats()
    # assert stats.get('retry/count', 0) >= 1 # At least one retry attempt for the 500 error
    # assert stats.get('retry/reason_count/500 Server Error', 0) >=1 # Or specific code for 500
    # assert stats.get('downloader/response_status_count/500', 0) >= 1
    # assert stats.get('downloader/response_status_count/200', 0) == 2 # Both URLs eventually gave 200
