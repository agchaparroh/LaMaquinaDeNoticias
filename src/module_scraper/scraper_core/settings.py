# Scrapy settings for scraper_core project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from module_scraper/.env
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path)

BOT_NAME = "scraper_core"

SPIDER_MODULES = ["scraper_core.spiders"]
NEWSPIDER_MODULE = "scraper_core.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "LaMaquinaDeNoticias/1.0 (+https://github.com/lamaquina)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 8

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 2
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 2
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es,en;q=0.9",
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "scraper_core.middlewares.ScraperCoreSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "scraper_core.middlewares.ScraperCoreDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "scraper_core.pipelines.ExtractArticleItemsPipeline": 100,
    "scraper_core.pipelines.CleanArticleItemsPipeline": 200,
    "scraper_core.pipelines.SupabaseStoragePipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 1
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 30
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# Playwright settings
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

PLAYWRIGHT_BROWSER_TYPE = "chromium"  # Or "firefox", "webkit"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "timeout": 30 * 1000,  # 30 seconds
}

# =============================================================================
# SUPABASE CONFIGURATION
# =============================================================================

# Supabase credentials (loaded from environment variables)
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Supabase Storage configuration
SUPABASE_STORAGE_BUCKET = 'articulos-html'  # Bucket for storing compressed HTML
SUPABASE_STORAGE_PUBLIC = False  # Keep HTML storage private

# Supabase retry configuration
SUPABASE_MAX_RETRIES = 3
SUPABASE_RETRY_DELAY = 1.0  # Initial delay in seconds
SUPABASE_RETRY_BACKOFF = 2.0  # Backoff multiplier

# Supabase timeout configuration
SUPABASE_POSTGREST_TIMEOUT = 10  # Seconds for database operations
SUPABASE_STORAGE_TIMEOUT = 30  # Seconds for storage operations

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Configure logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(levelname)s:%(name)s: %(message)s'

# Log specific components at different levels
LOGGERS = {
    'scrapy': 'INFO',
    'scrapy.core.engine': 'INFO',
    'scrapy.downloadermiddlewares': 'INFO',
    'scrapy.spidermiddlewares': 'INFO',
    'scraper_core.pipelines.supabase_pipeline': 'DEBUG',
    'scraper_core.utils.supabase_client': 'DEBUG',
}

# =============================================================================
# ERROR HANDLING CONFIGURATION
# =============================================================================

# Retry configuration for failed requests
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Download timeout
DOWNLOAD_TIMEOUT = 30

# =============================================================================
# CUSTOM SETTINGS FOR PRODUCTION
# =============================================================================

# These can be overridden by environment variables or spider settings
if os.getenv('ENVIRONMENT') == 'production':
    CONCURRENT_REQUESTS = 16
    CONCURRENT_REQUESTS_PER_DOMAIN = 4
    DOWNLOAD_DELAY = 1
    AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0
    LOG_LEVEL = 'WARNING'
