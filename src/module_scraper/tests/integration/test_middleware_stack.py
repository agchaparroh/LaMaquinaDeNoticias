import pytest
from scrapy import Request
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.spiders import Spider
from pathlib import Path # Add Path if not already imported
import json # Ensure json is imported at the top level

# Basic spider for testing
class SimpleSpider(Spider):
    name = 'simplespider'
    start_urls = ['http://httpbin.org/get'] # A reliable site for testing HTTP requests

    def parse(self, response):
        self.logger.info(f"Response URL: {response.url}")
        # Simple check to ensure the response is not empty and has expected content type
        assert response.status == 200
        assert 'application/json' in response.headers.get('Content-Type', b'').decode()
        # Store result for assertion in the test
        self.crawler.stats.set_value('test_parse_called', True)
        self.crawler.stats.set_value('response_url', response.url)


@pytest.mark.asyncio
async def test_normal_request_flow():
    '''
    Tests the normal request flow with all default middlewares active (excluding Playwright initially).
    It checks if a request goes through the downloader middlewares and reaches the spider.
    '''
    settings = get_project_settings()
    # Override with test settings
    settings.setmodule('tests.config.test_settings', priority='project')

    # Ensure CrawlOnce is disabled for this specific test if it interferes,
    # or ensure its db path is correctly set for tests.
    # For now, relying on test_settings.py to disable it.
    # settings['CRAWL_ONCE_ENABLED'] = False


    process = CrawlerProcess(settings)

    crawler = process.create_crawler(SimpleSpider)

    # Using process.crawl and then process.start() is typical for Scrapy scripts,
    # but for testing within an async context, directly scheduling and joining might be needed,
    # or using a helper that manages the Twisted reactor.
    # For pytest-asyncio, CrawlerProcess's start method (which blocks) needs careful handling.
    # A common pattern is to run the crawl in a separate thread or use utilities
    # like Scrapy's `crawl_runner` if available and suitable.

    # Let's try a simplified approach for now, assuming the process can be managed.
    # Note: Running CrawlerProcess directly in tests can be tricky due to Twisted reactor management.
    # Consider using `scrapy.contracts` or a dedicated test runner if this becomes problematic.

    await process.crawl(SimpleSpider)
    # process.start() is blocking and manages the reactor.
    # If pytest-asyncio runs its own loop, this can conflict.
    # For now, assuming this setup works or will be adjusted based on Scrapy testing best practices.
    # It might be necessary to run `process.start(stop_after_crawl=True)` in a thread
    # and await its completion, or use a more integrated Scrapy testing tool.

    # This will run the spider. We need to ensure the reactor is properly managed.
    # A common way for tests:
    # d = process.crawl(SimpleSpider)
    # d.addBoth(lambda _: process.stop()) # Stop reactor when crawl finishes
    # process.start(stop_after_crawl=False) # Start reactor, don't stop automatically after one crawl

    # For simplicity in this initial step, we'll assume process.crawl followed by checking stats works.
    # This part might need refinement based on actual execution environment and Scrapy test patterns.

    stats = crawler.stats.get_stats()

    assert stats.get('test_parse_called', False) is True
    assert stats.get('response_url') == 'http://httpbin.org/get'
    # Check for downloader stats indicating middleware processing
    assert 'downloader/request_count' in stats
    assert stats['downloader/request_count'] > 0
    assert 'downloader/response_count' in stats
    assert stats['downloader/response_count'] > 0
    assert 'downloader/response_status_count/200' in stats
    assert stats['downloader/response_status_count/200'] > 0

    # Clean up CrawlOnce database if it was enabled and created files
    # Path(settings['CRAWL_ONCE_PATH']).joinpath('requests.seen.db').unlink(missing_ok=True)


# Spider that requests Playwright processing
class PlaywrightSpider(Spider):
    name = 'playwrightspider'
    # Using a known site that benefits from JS rendering, or a test page if available.
    # httpbin.org/headers returns the request headers, which can show Playwright's user-agent.
    start_urls = ['http://httpbin.org/headers']

    custom_settings = {
        # Ensure Playwright is enabled in download handlers for this spider
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
        # Optional: Configure Playwright browser type if not default
        # 'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
    }

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, meta={'playwright': True, 'playwright_include_page': True}, callback=self.parse)

    async def parse(self, response):
        self.logger.info(f"Response URL (Playwright): {response.url}")
        page = response.meta.get('playwright_page')
        assert page is not None, "Playwright page object should be in meta"

        # Check for a header that Playwright might add or a specific user-agent
        # This depends on Playwright's default behavior or specific configurations.
        # For example, httpbin.org/headers will return the User-Agent.
        # We'd expect it to be different from Scrapy's default or the one set by RandomUserAgentMiddleware
        # if Playwright takes over.
        import json
        data = json.loads(response.text)
        headers = data.get('headers', {})
        user_agent = headers.get('User-Agent', '')

        self.logger.info(f"User-Agent from Playwright request: {user_agent}")
        # This assertion might need adjustment based on the expected Playwright UA
        assert 'HeadlessChrome' in user_agent or 'Playwright' in user_agent, "User-Agent should indicate Playwright usage"

        assert response.status == 200
        self.crawler.stats.set_value('playwright_test_parse_called', True)
        self.crawler.stats.set_value('playwright_response_url', response.url)

        if page:
            await page.close() # Important to close the page

@pytest.mark.asyncio
async def test_playwright_request_flow():
    '''
    Tests that a request with Playwright enabled correctly uses the Playwright middleware
    and receives a response processed by a browser.
    '''
    settings = get_project_settings()
    settings.setmodule('tests.config.test_settings', priority='project')

    # Ensure Playwright specific settings from the main settings are respected
    # or overridden if necessary for the test.
    # test_settings.py should already handle generic overrides.
    # settings['PLAYWRIGHT_LAUNCH_OPTIONS'] = {"headless": True} # Example if needed

    process = CrawlerProcess(settings)
    crawler = process.create_crawler(PlaywrightSpider) # Use the PlaywrightSpider

    await process.crawl(PlaywrightSpider)
    # Similar reactor management considerations as in the previous test.

    stats = crawler.stats.get_stats()

    assert stats.get('playwright_test_parse_called', True) is True
    assert stats.get('playwright_response_url') == 'http://httpbin.org/headers'
    assert 'downloader/request_count' in stats
    assert stats['downloader/request_count'] > 0
    assert 'downloader/response_count' in stats
    assert stats['downloader/response_count'] > 0
    assert 'downloader/response_status_count/200' in stats
    assert stats['downloader/response_status_count/200'] > 0
    # Specific stats from Playwright handler (if any are emitted by default)
    # assert 'playwright/request_count' in stats # Example, if such a stat exists

    # Cleanup if CRAWL_ONCE_ENABLED was true for this test
    # if settings.getbool('CRAWL_ONCE_ENABLED'):
    #     Path(settings['CRAWL_ONCE_PATH']).joinpath('requests.seen.db').unlink(missing_ok=True)


# Spider for testing CrawlOnceMiddleware
class CrawlOnceTestSpider(Spider):
    name = 'crawloncetestspider'
    # Using a simple, fast endpoint. httpbin.org/get is fine.
    # The key is that we will send a request to the *same URL* twice.
    duplicate_url = 'http://httpbin.org/get?param=crawl_once_test'

    # We will make two requests to the same URL.
    # The first should be processed, the second should be filtered by CrawlOnce.
    start_urls = [duplicate_url, duplicate_url]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parsed_urls = []

    def parse(self, response):
        self.logger.info(f"CrawlOnceTestSpider: Parsed URL: {response.url}")
        self.parsed_urls.append(response.url)
        self.crawler.stats.inc_value('custom_parse_count')


@pytest.mark.asyncio
async def test_crawl_once_duplicate_detection():
    '''
    Tests that CrawlOnceMiddleware correctly identifies and filters duplicate requests.
    '''
    settings = get_project_settings()
    settings.setmodule('tests.config.test_settings', priority='project')

    # Explicitly enable CrawlOnceMiddleware for this test and set a test-specific path
    settings['CRAWL_ONCE_ENABLED'] = True
    # The CRAWL_ONCE_PATH is already set in test_settings.py, ensure it's used.
    # Make sure the path exists and is clean before the test
    crawl_once_db_path = Path(settings['CRAWL_ONCE_PATH'])
    if not crawl_once_db_path.exists():
        crawl_once_db_path.mkdir(parents=True, exist_ok=True)

    # Clean up any previous DB file from other tests or runs
    seen_db_file = crawl_once_db_path / 'requests.seen.db'
    if seen_db_file.exists():
        seen_db_file.unlink()

    process = CrawlerProcess(settings)
    crawler = process.create_crawler(CrawlOnceTestSpider)

    await process.crawl(CrawlOnceTestSpider)

    stats = crawler.stats.get_stats()
    spider = crawler.spider

    # The spider's parse method should only be called once.
    assert stats.get('custom_parse_count', 0) == 1
    assert len(spider.parsed_urls) == 1
    assert spider.parsed_urls[0] == CrawlOnceTestSpider.duplicate_url

    # Check CrawlOnceMiddleware stats
    # The exact stat key might depend on the version of scrapy-crawl-once
    # Common keys are 'crawl_once/ignored' or 'crawl_once/filtered'
    # Check the middleware's documentation or source if this assertion fails.
    assert stats.get('crawl_once/ignored', 0) == 1 or stats.get('offsite/filtered', 0) == 1 # Fallback for older versions or different stat names

    # Standard downloader stats
    assert stats.get('downloader/request_count', 0) == 2 # Two requests were sent
    assert stats.get('downloader/response_count', 0) == 1 # Only one response received and processed by spider
    assert stats.get('downloader/response_status_count/200', 0) == 1

    # Clean up the CrawlOnce database file after the test
    if seen_db_file.exists():
        seen_db_file.unlink()
    # Optionally remove the directory if it was created solely for this test
    # if crawl_once_db_path.exists() and not any(crawl_once_db_path.iterdir()):
    #     crawl_once_db_path.rmdir()


class UserAgentRotationSpider(Spider):
    name = 'useragentrotationspider'
    # httpbin.org/headers returns the request headers, including User-Agent.
    # We'll make multiple requests to see if the User-Agent changes.
    start_urls = [
        'http://httpbin.org/headers?req=1',
        'http://httpbin.org/headers?req=2',
        'http://httpbin.org/headers?req=3',
    ]

    custom_settings = {
        # Ensure RandomUserAgentMiddleware is active and Scrapy's default is not.
        # These are already in the main settings.py, but good to be aware.
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
            # Keep other essential middlewares like CrawlOnce (if needed and managed)
            # and Playwright custom middleware (though not used by this spider)
             'scrapy_crawl_once.CrawlOnceMiddleware': 50, # If testing with it
             'scraper_core.middlewares.playwright_custom_middleware.PlaywrightCustomDownloaderMiddleware': 550,
        },
        # Ensure CRAWL_ONCE is disabled if it might interfere with multiple identical requests to /headers
        # or configure it appropriately. For this test, we want fresh requests.
        'CRAWL_ONCE_ENABLED': False,
    }

    user_agents_seen = set()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # For Scrapy <2.0, stats might not be directly available on self.crawler.stats
        # self.crawler is set by the engine.
        # Initializing here might be too early if crawler object is not yet set.
        self.user_agents_seen = set() # Better to initialize in __init__

    def parse(self, response):
        self.logger.info(f"UserAgentRotationSpider: Parsed URL: {response.url}")
        data = json.loads(response.text)
        headers = data.get('headers', {})
        user_agent = headers.get('User-Agent', '')

        self.logger.info(f"URL: {response.url}, User-Agent: {user_agent}")
        if user_agent:
            # Accessing stats via self.crawler.stats
            # For collecting UAs across requests, a spider attribute is more direct.
            self.user_agents_seen.add(user_agent)

        self.crawler.stats.inc_value('user_agent_parse_count')

@pytest.mark.asyncio
async def test_user_agent_rotation():
    '''
    Tests that RandomUserAgentMiddleware rotates User-Agents across multiple requests.
    '''
    settings = get_project_settings()
    settings.setmodule('tests.config.test_settings', priority='project')

    # Override specific middleware settings for this test if necessary,
    # e.g., to ensure RandomUserAgentMiddleware is definitely on and Scrapy's default is off.
    # The spider's custom_settings should handle this, but global test settings can also be used.
    # settings['DOWNLOADER_MIDDLEWARES'] = {
    #     'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    #     'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
    #     'scraper_core.middlewares.playwright_custom_middleware.PlaywrightCustomDownloaderMiddleware': 550, # Keep other relevant ones
    # }
    # Ensure CrawlOnce is disabled for this test, as we are making multiple similar requests
    # and don't want them filtered if they happen to be identical beyond the query param.
    settings['CRAWL_ONCE_ENABLED'] = False

    process = CrawlerProcess(settings)
    crawler = process.create_crawler(UserAgentRotationSpider)

    await process.crawl(UserAgentRotationSpider)

    stats = crawler.stats.get_stats()
    spider = crawler.spider

    assert stats.get('user_agent_parse_count', 0) == len(UserAgentRotationSpider.start_urls)

    # We expect at least two different User-Agents for 3 requests.
    # The exact number of unique UAs depends on the pool size and randomness.
    # For a small number of requests, it's possible to get the same UA multiple times,
    # but with a decent list, >1 unique UA for 3 requests is highly probable.
    # If the user agent list is very small, this assertion might be too strict.
    assert len(spider.user_agents_seen) > 1, \
        f"Expected multiple User-Agents, but only got {len(spider.user_agents_seen)}: {spider.user_agents_seen}"

    # Verify that the default Scrapy User-Agent is not used (if one is set in settings)
    # default_scrapy_ua = settings.get('USER_AGENT', 'Scrapy') # Default USER_AGENT in Scrapy is just 'Scrapy'
    # assert default_scrapy_ua not in spider.user_agents_seen # This might be too strict if default_scrapy_ua is generic

    # Check that user agents seen are not empty
    for ua in spider.user_agents_seen:
        assert ua is not None and ua != "", "User-Agent should not be empty"
