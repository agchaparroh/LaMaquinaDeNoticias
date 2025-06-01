import pytest
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.spiders import Spider
from scrapy import Request # Ensure Request is imported
from pathlib import Path # Make sure Path is imported

# Basic spider for testing simple HTML site
class SimpleHtmlSpider(Spider):
    name = 'simplehtmlspider'
    start_urls = ['http://httpbin.org/html'] # A simple HTML page

    # Custom settings to ensure no Playwright or other complex middlewares interfere
    # unless specifically being tested.
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
            'https': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
        },
        'TWISTED_REACTOR': None, # Ensure default reactor if Playwright not needed
        'PLAYWRIGHT_INTEGRATION_ENABLED': False, # Hypothetical setting to disable Playwright
        'CRAWL_ONCE_ENABLED': False, # Disable for simplicity unless testing CrawlOnce
        'ROBOTSTXT_OBEY': False, # Disable for this test to ensure we hit the page
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items_scraped = []

    def parse(self, response):
        self.logger.info(f"SimpleHtmlSpider: Parsed URL: {response.url}, Status: {response.status}")
        # httpbin.org/html contains one <h1> tag.
        title = response.xpath('//h1/text()').get()
        if title:
            self.items_scraped.append({'title': title.strip()})
            self.crawler.stats.inc_value('simple_html_items_scraped')

        self.crawler.stats.set_value('simple_html_parse_called', True)

@pytest.mark.asyncio
async def test_simple_html_site_flow():
    '''
    Tests a spider on a simple HTML site (no JS) to verify normal data extraction.
    Ensures basic Scrapy components (engine, scheduler, downloader, spider) work together.
    '''
    settings = get_project_settings()
    settings.setmodule('tests.config.test_settings', priority='project')

    # Further override settings if needed, e.g., ensure Playwright is off
    settings['DOWNLOAD_HANDLERS'] = { # Ensure default non-Playwright handlers
        'http': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
        'https': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
    }
    settings['TWISTED_REACTOR'] = None # Reset to default if test_settings changed it
    settings['ROBOTSTXT_OBEY'] = False # Ensure we can crawl the test URL
    settings['CRAWL_ONCE_ENABLED'] = False # Avoid interference

    process = CrawlerProcess(settings)
    crawler = process.create_crawler(SimpleHtmlSpider)

    await process.crawl(SimpleHtmlSpider)

    stats = crawler.stats.get_stats()
    spider = crawler.spider

    assert stats.get('simple_html_parse_called', False) is True, "Spider's parse method was not called"
    assert stats.get('simple_html_items_scraped', 0) == 1, "Did not scrape the expected number of items"
    assert len(spider.items_scraped) == 1, "Spider did not collect the item"
    assert spider.items_scraped[0]['title'] == 'Herman Melville - Moby-Dick; or, The Whale', "Scraped title is incorrect"

    # Basic downloader stats
    assert stats.get('downloader/request_count', 0) > 0
    assert stats.get('downloader/response_count', 0) > 0
    assert stats.get('downloader/response_status_count/200', 0) > 0
    assert stats.get('finish_reason') == 'finished', "Spider did not finish successfully"


# (Ensure necessary imports are at the top: pytest, CrawlerProcess, get_project_settings, Spider, Request)
# from scrapy.utils.response import open_in_browser # Useful for debugging

class JavaScriptSiteSpider(Spider):
    name = 'javascriptsitespider'
    # This site loads its content using JavaScript.
    start_urls = ['https://quotes.toscrape.com/js/']

    custom_settings = {
        # Enable Playwright via Scrapy-Playwright handler
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        # Essential for Playwright with asyncio
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        # Optional: Define Playwright browser options if needed
        'PLAYWRIGHT_LAUNCH_OPTIONS': {"headless": True},
        'ROBOTSTXT_OBEY': False, # Disable for this test to ensure we hit the page
        'CRAWL_ONCE_ENABLED': False, # Disable for simplicity
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quotes_scraped = []

    def start_requests(self):
        for url in self.start_urls:
            # Crucial: Request Playwright processing and include the page object
            yield Request(url, meta={'playwright': True, 'playwright_include_page': True}, callback=self.parse)

    async def parse(self, response):
        self.logger.info(f"JavaScriptSiteSpider: Parsed URL: {response.url}, Status: {response.status}")

        page = response.meta.get('playwright_page')
        assert page is not None, "Playwright page object should be in response.meta"

        # Quotes are within <div class="quote"> elements, which are loaded by JS.
        # We'll wait for one such element to ensure JS has likely run.
        # This explicit wait might be necessary if content loads asynchronously after page load.
        try:
            await page.wait_for_selector("div.quote", timeout=10000) # Wait up to 10 seconds
        except Exception as e: # TimeoutError from Playwright if selector not found
            self.logger.error(f"Playwright wait_for_selector timed out or failed: {e}")
            # open_in_browser(response) # Debug: opens response in browser
            # HTML content might be useful for debugging if selector fails
            self.logger.info(f"HTML content when selector failed: {await page.content()}")


        quotes = response.xpath('//div[@class="quote"]')
        assert len(quotes) > 0, "No quotes found. JS might not have executed or page structure changed."

        for quote_sel in quotes:
            text = quote_sel.xpath('.//span[@class="text"]/text()').get()
            author = quote_sel.xpath('.//small[@class="author"]/text()').get()
            if text and author:
                self.quotes_scraped.append({'text': text, 'author': author})

        self.crawler.stats.set_value('js_site_parse_called', True)
        self.crawler.stats.set_value('js_site_quotes_scraped_count', len(self.quotes_scraped))

        if page:
            await page.close() # Always close the Playwright page

@pytest.mark.asyncio
async def test_javascript_site_playwright_activation():
    '''
    Tests a spider on a JavaScript-heavy site (quotes.toscrape.com/js/).
    Verifies that Playwright is activated and content generated by JS is correctly scraped.
    '''
    settings = get_project_settings()
    settings.setmodule('tests.config.test_settings', priority='project')

    # Ensure Playwright settings are active for this test
    settings['DOWNLOAD_HANDLERS'] = {
        "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    }
    settings['TWISTED_REACTOR'] = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
    settings['PLAYWRIGHT_LAUNCH_OPTIONS'] = {"headless": True, "timeout": 35000} # Increased timeout
    settings['ROBOTSTXT_OBEY'] = False
    settings['CRAWL_ONCE_ENABLED'] = False
    # The playwright_custom_middleware.py should be active as per main settings.py
    # Ensure it's included if not by default in test settings.
    # settings['DOWNLOADER_MIDDLEWARES'].update({
    #    'scraper_core.middlewares.playwright_custom_middleware.PlaywrightCustomDownloaderMiddleware': 550,
    # })


    process = CrawlerProcess(settings)
    crawler = process.create_crawler(JavaScriptSiteSpider)

    await process.crawl(JavaScriptSiteSpider)

    stats = crawler.stats.get_stats()
    spider = crawler.spider

    assert stats.get('js_site_parse_called', False) is True, "Spider's parse method was not called"
    assert stats.get('js_site_quotes_scraped_count', 0) > 0, "No quotes were scraped from JS site"
    assert len(spider.quotes_scraped) > 0, "Spider did not collect any quotes"

    # Verify some basic properties of scraped data if consistent
    # For example, check if 'text' and 'author' keys exist in the first scraped item
    if spider.quotes_scraped:
        assert 'text' in spider.quotes_scraped[0]
        assert 'author' in spider.quotes_scraped[0]

    assert stats.get('downloader/request_count', 0) > 0
    assert stats.get('downloader/response_count', 0) > 0
    assert stats.get('downloader/response_status_count/200', 0) > 0
    assert stats.get('finish_reason') == 'finished', "Spider did not finish successfully"
    # Check if Playwright middleware added any specific stats (optional)
    # e.g., assert 'playwright/request_count' in stats or similar


# (Ensure necessary imports are at the top: pytest, CrawlerProcess, get_project_settings, Spider, Request)

class RobotsTxtSpider(Spider):
    name = 'robotstxtspider'
    # This URL is disallowed by httpbin.org/robots.txt
    # robots.txt content:
    # User-agent: *
    # Disallow: /deny
    start_urls = ['http://httpbin.org/deny']

    custom_settings = {
        'ROBOTSTXT_OBEY': True, # Crucial: ensure robots.txt is obeyed
        'DOWNLOAD_HANDLERS': { # Ensure default non-Playwright handlers
            'http': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
            'https': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
        },
        'TWISTED_REACTOR': None,
        'CRAWL_ONCE_ENABLED': False,
        # Optional: Add a specific user agent if httpbin.org/robots.txt has agent-specific rules
        # 'USER_AGENT': 'TestRobotsSpider/1.0'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parse_called = False
        self.unhandled_error = None

    def parse(self, response):
        # This method should NOT be called if robots.txt is obeyed for /deny
        self.logger.error(f"RobotsTxtSpider: Parse was called for {response.url}, which should be disallowed!")
        self.parse_called = True
        self.crawler.stats.set_value('robots_test_parse_called_unexpectedly', True)

    def error_handler(self, failure):
        # This is a generic error handler you might add to a base spider.
        # For robots.txt, Scrapy usually just filters the request,
        # it might not raise an error that this specific callback catches unless it's an unhandled one.
        # Filtered requests due to robots.txt are typically logged by Scrapy's RobotsTxtMiddleware.
        self.logger.info(f"RobotsTxtSpider: Error handler caught failure: {failure.getErrorMessage()}")
        self.unhandled_error = failure


@pytest.mark.asyncio
async def test_robots_txt_blocking():
    '''
    Tests that Scrapy respects robots.txt rules and blocks requests to disallowed URLs
    when ROBOTSTXT_OBEY is True.
    '''
    settings = get_project_settings()
    settings.setmodule('tests.config.test_settings', priority='project')

    # Explicitly enable ROBOTSTXT_OBEY for this test
    settings['ROBOTSTXT_OBEY'] = True
    # Ensure non-Playwright handlers
    settings['DOWNLOAD_HANDLERS'] = {
        'http': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
        'https': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
    }
    settings['TWISTED_REACTOR'] = None
    settings['CRAWL_ONCE_ENABLED'] = False
    # It's good to also ensure the RobotsTxtMiddleware is present in the downloader middlewares.
    # It is by default in Scrapy unless explicitly removed.
    # settings['DOWNLOADER_MIDDLEWARES'].update({'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': 100})


    process = CrawlerProcess(settings)
    # Bind error handler for more insight if needed, though not strictly necessary for robots.txt check
    # crawler = process.create_crawler(RobotsTxtSpider)
    # crawler.signals.connect(RobotsTxtSpider().error_handler, signal=signals.spider_error) # Example, if spider had error signal connection

    crawler = process.create_crawler(RobotsTxtSpider)

    await process.crawl(RobotsTxtSpider)

    stats = crawler.stats.get_stats()
    spider = crawler.spider

    # The spider's parse method should NOT have been called for the /deny URL.
    assert not spider.parse_called, "Spider's parse method was called for a disallowed URL"
    assert stats.get('robots_test_parse_called_unexpectedly', False) is False

    # Check for specific stats from RobotsTxtMiddleware.
    # Scrapy logs a message like "DEBUG: Forbidden by robots.txt: <GET http://httpbin.org/deny>"
    # And increments 'robotstxt/forbidden' or similar stat.
    # The exact stat key can vary or might need to be inferred from logs if not directly available.
    # A common one is 'downloader/response_status_count/403' if server returns 403,
    # but robots.txt middleware often filters *before* the request is made.
    # The most reliable check is that parse() isn't called and requests are filtered.

    # Expected behavior:
    # 1. Request to /robots.txt is made: 'downloader/request_count' will be at least 1 (for robots.txt).
    # 2. Request to /deny is filtered: 'downloader/request_count' might be 1 (only robots.txt) or 2 if /deny was attempted and then dropped.
    #    The 'offsite/filtered' or a similar stat from RobotsTxtMiddleware might be more indicative.
    #    Scrapy's RobotsTxtMiddleware (scrapy.downloadermiddlewares.robotstxt) adds 'robotstxt/request_count' and 'robotstxt/forbidden_count'.

    assert stats.get('downloader/request_count', 0) >= 1 # At least the robots.txt request
    # Check if the request to /deny was even attempted or just filtered out early.
    # If filtered early, response_count for /deny will be 0.
    assert stats.get('downloader/response_count', 0) <= 1 # Should only be response for robots.txt, not for /deny

    # The key evidence: parse() was not called for the disallowed URL.
    # And a stat indicating it was forbidden by robots.txt
    # This stat key 'robotstxt/forbidden_count' is provided by Scrapy's built-in RobotsTxtMiddleware
    assert stats.get('robotstxt/forbidden_count', 0) == 1, "RobotsTxtMiddleware did not record a forbidden URL"
    assert stats.get('finish_reason') == 'finished'


class SpiderCrawlOnceTestSpider(Spider):
    name = 'spidercrawloncetestspider'
    # A unique URL for this test
    test_url = 'http://httpbin.org/get?param=spider_crawl_once'

    custom_settings = {
        'CRAWL_ONCE_ENABLED': True,
        # CRAWL_ONCE_PATH will be taken from test_settings.py
        'DOWNLOAD_HANDLERS': { # Ensure default non-Playwright handlers
            'http': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
            'https': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
        },
        'TWISTED_REACTOR': None,
        'ROBOTSTXT_OBEY': False,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parse_call_count = 0
        self.urls_parsed = []

    def start_requests(self):
        # Yield the same request twice.
        # The meta key 'crawl_once': True can be used for finer control if CRAWL_ONCE_DEFAULT is False.
        # If CRAWL_ONCE_DEFAULT is True (as often configured), just yielding is enough.
        # Assuming CRAWL_ONCE_ENABLED=True and CRAWL_ONCE_DEFAULT=False (from settings.py),
        # we need to explicitly mark requests for CrawlOnce.
        # However, our main settings.py has CRAWL_ONCE_DEFAULT = False, and enabled via middleware.
        # The middleware itself (scrapy_crawl_once.CrawlOnceMiddleware) when enabled typically
        # makes all requests subject to crawl_once logic by default unless specific meta keys override.
        # Let's assume the default behavior of the middleware is to track all GET requests.

        yield Request(self.test_url, callback=self.parse, dont_filter=False) # dont_filter=False is default
        yield Request(self.test_url, callback=self.parse, dont_filter=False) # Second request to same URL

    def parse(self, response):
        self.logger.info(f"SpiderCrawlOnceTestSpider: Parsed URL: {response.url}")
        self.parse_call_count += 1
        self.urls_parsed.append(response.url)
        self.crawler.stats.inc_value('spider_crawl_once_parse_count')

@pytest.mark.asyncio
async def test_spider_crawl_once_prevention():
    '''
    Tests CrawlOnceMiddleware duplicate URL prevention from a spider's perspective.
    Ensures a spider attempting to request the same URL twice only processes it once.
    '''
    settings = get_project_settings()
    settings.setmodule('tests.config.test_settings', priority='project')

    # Explicitly enable CrawlOnce and set path (test_settings.py should provide a default path)
    settings['CRAWL_ONCE_ENABLED'] = True
    crawl_once_db_path_str = settings.get('CRAWL_ONCE_PATH', 'tests/.scrapy_test/crawl_once') # Fallback if not in test_settings
    crawl_once_db_path = Path(crawl_once_db_path_str)

    if not crawl_once_db_path.exists():
        crawl_once_db_path.mkdir(parents=True, exist_ok=True)

    seen_db_file = crawl_once_db_path / 'requests.seen.db'
    if seen_db_file.exists():
        seen_db_file.unlink() # Clean up before test

    # Ensure non-Playwright handlers
    settings['DOWNLOAD_HANDLERS'] = {
        'http': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
        'https': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
    }
    settings['TWISTED_REACTOR'] = None
    settings['ROBOTSTXT_OBEY'] = False


    process = CrawlerProcess(settings)
    crawler = process.create_crawler(SpiderCrawlOnceTestSpider)

    await process.crawl(SpiderCrawlOnceTestSpider)

    stats = crawler.stats.get_stats()
    spider = crawler.spider

    # Spider's parse method should only be called once for the unique URL
    assert spider.parse_call_count == 1, "Parse method called more than once for the same URL with CrawlOnce enabled"
    assert len(spider.urls_parsed) == 1, "URL list contains more than one entry"
    assert spider.urls_parsed[0] == SpiderCrawlOnceTestSpider.test_url if spider.urls_parsed else False
    assert stats.get('spider_crawl_once_parse_count', 0) == 1

    # Check CrawlOnceMiddleware stats
    # Expected: one request processed, one ignored/filtered.
    assert stats.get('crawl_once/ignored', 0) == 1 or stats.get('offsite/filtered', 0) == 1 # Check common stat keys

    # Standard downloader stats: two requests initiated by spider, but only one should fully download and parse.
    assert stats.get('downloader/request_count', 0) == 2 # Spider sent two requests
    assert stats.get('downloader/response_count', 0) == 1 # Only one actual download & response to spider
    assert stats.get('downloader/response_status_count/200', 0) == 1
    assert stats.get('finish_reason') == 'finished'

    # Clean up CrawlOnce database file after the test
    if seen_db_file.exists():
        seen_db_file.unlink()
    # Optional: rmdir if created for this test and empty
    # if crawl_once_db_path.exists() and not any(crawl_once_db_path.iterdir()):
    #     crawl_once_db_path.rmdir()


# (Ensure necessary imports are at the top: pytest, CrawlerProcess, get_project_settings, Spider, Request)
# from scrapy import signals # For connecting to signals if needed

class NetworkErrorSpider(Spider):
    name = 'networkerrorspider'
    # This URL will cause a DNS lookup error as the domain is unlikely to exist.
    start_urls = ['http://nonexistentsite.nosuchdomain/']

    custom_settings = {
        'RETRY_ENABLED': True, # Ensure RetryMiddleware is active
        'RETRY_TIMES': 2,      # Number of retries (excluding the first attempt)
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429], # Default retry codes
        # DNS, timeout, and connection refused errors are typically retried by default.
        'DOWNLOAD_HANDLERS': { # Ensure default non-Playwright handlers
            'http': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
            'https': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
        },
        'TWISTED_REACTOR': None,
        'ROBOTSTXT_OBEY': False, # Not relevant here, but good to be explicit
        'CRAWL_ONCE_ENABLED': False, # Not relevant here
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parse_called = False
        self.errors_received = []

    def parse(self, response):
        # This method should ideally not be called if the request fails repeatedly.
        self.logger.info(f"NetworkErrorSpider: Parse called for {response.url} (UNEXPECTED for network error)")
        self.parse_called = True
        self.crawler.stats.inc_value('network_error_test_parse_called_unexpectedly')

    def errback_default(self, failure):
        # This errback will be called if the request fails after all retries.
        self.logger.info(f"NetworkErrorSpider: Default errback caught failure for {failure.request.url if failure.request else 'N/A'}: {failure.getErrorMessage()}")
        self.errors_received.append(failure)
        self.crawler.stats.inc_value('network_error_test_errback_called')
        # You can inspect failure.type here, e.g., DNSLookupError, TimeoutError, etc.
        # from twisted.internet.error import DNSLookupError
        # assert isinstance(failure.value, DNSLookupError)

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.parse, errback=self.errback_default)


@pytest.mark.asyncio
async def test_spider_network_error_handling():
    '''
    Tests how a spider (and Scrapy) handles network errors (e.g., DNS lookup failure).
    Verifies that retries occur and the error is caught by the spider's errback.
    '''
    settings = get_project_settings()
    settings.setmodule('tests.config.test_settings', priority='project')

    settings['RETRY_ENABLED'] = True
    settings['RETRY_TIMES'] = 2 # Total 3 attempts (initial + 2 retries)
    # Ensure non-Playwright handlers and no interference from other settings
    settings['DOWNLOAD_HANDLERS'] = {
        'http': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
        'https': 'scrapy.core.downloader.handlers.http11.HTTP11DownloadHandler',
    }
    settings['TWISTED_REACTOR'] = None
    settings['ROBOTSTXT_OBEY'] = False
    settings['CRAWL_ONCE_ENABLED'] = False

    process = CrawlerProcess(settings)
    crawler = process.create_crawler(NetworkErrorSpider)

    await process.crawl(NetworkErrorSpider)

    stats = crawler.stats.get_stats()
    spider = crawler.spider

    assert not spider.parse_called, "Parse method was called despite expected network errors"
    assert stats.get('network_error_test_parse_called_unexpectedly', 0) == 0

    assert len(spider.errors_received) == 1, "Spider's errback was not called or called multiple times for one URL"
    assert stats.get('network_error_test_errback_called', 0) == 1

    # Check retry stats. For DNS error, retries should happen.
    # The number of retries is RETRY_TIMES (default 2 for HTTP errors, DNS might have its own default or use general).
    # Stat key for retries is 'retry/count'.
    # Total attempts = initial + RETRY_TIMES.
    # If RETRY_TIMES = 2, then 3 total attempts.
    assert stats.get('retry/count', 0) == settings.getint('RETRY_TIMES', 2), \
        f"Expected {settings.getint('RETRY_TIMES', 2)} retries, got {stats.get('retry/count', 0)}"

    # Check the reason for retry, if available and specific (e.g., 'retry/reason_count/twisted.internet.error.DNSLookupError')
    # This exact stat key might vary based on Scrapy version and error type.
    # For a DNS error:
    dns_error_key_part = 'DNSLookupError' # Part of the Twisted error class name
    found_dns_retry_reason = False
    for stat_key in stats.keys():
        if 'retry/reason_count' in stat_key and dns_error_key_part in stat_key:
            assert stats[stat_key] == settings.getint('RETRY_TIMES', 2) # Each retry for this reason
            found_dns_retry_reason = True
            break
    assert found_dns_retry_reason, f"Retry reason for DNSLookupError not found or count incorrect in stats: {stats}"


    # The request should have ultimately failed.
    # 'downloader/request_count' should reflect all attempts (initial + retries).
    expected_attempts = 1 + settings.getint('RETRY_TIMES', 2)
    assert stats.get('downloader/request_count', 0) == expected_attempts
    assert stats.get('downloader/response_count', 0) == 0 # No successful responses

    assert stats.get('finish_reason') == 'finished', "Spider did not finish successfully"
    # Check for logged errors if Scrapy logs them with specific messages or levels.
    # This would require inspecting logs, which is outside typical stat checks.
