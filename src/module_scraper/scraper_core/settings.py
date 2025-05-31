import nest_asyncio
nest_asyncio.apply()

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
from config.rate_limits.domain_config import DOMAIN_RATE_LIMITS
from scraper_core.logging_config import LoggingConfig

# Load environment variables - check multiple locations in order of preference
# 1. Environment variables (highest priority)
# 2. config/.env.test (for testing)
# 3. config/.env (for local development)
# 4. .env (legacy location)
project_root = Path(__file__).resolve().parent.parent
env_paths = [
    project_root / 'config' / '.env.test',
    project_root / 'config' / '.env',
    project_root / '.env',  # Legacy location
]

# Load the first .env file that exists
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break

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
SPIDER_MIDDLEWARES = {
    # Enable scrapy-crawl-once for duplicate prevention
    'scrapy_crawl_once.CrawlOnceMiddleware': 100,
    # Custom spider middlewares can be added here
    # "scraper_core.middlewares.ScraperCoreSpiderMiddleware": 543,
}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    # Enable scrapy-crawl-once for duplicate prevention
    'scrapy_crawl_once.CrawlOnceMiddleware': 50,
    # Disable default user agent middleware
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    # Enable random user agent middleware
    'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
    
    # NUEVO: Middleware personalizado para Playwright para manejar respuestas vacías
    'scraper_core.middlewares.playwright_custom_middleware.PlaywrightCustomDownloaderMiddleware': 550,
    
    # Rate limit monitoring middleware (optional, enable for debugging)
    # 'scraper_core.middlewares.rate_limit_monitor.RateLimitMonitorMiddleware': 543, 
    # Custom middlewares can be added here
    # "scraper_core.middlewares.ScraperCoreDownloaderMiddleware": 543,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
    # Disable telnet console for security
    "scrapy.extensions.telnet.TelnetConsole": None,
    # Enable log rotation extension
    "scraper_core.extensions.log_rotation.LogRotationExtension": 500,
}

# Log rotation settings
LOG_ROTATION_ENABLED = True  # Enable/disable log rotation
LOG_ROTATION_PER_SPIDER = False  # Create separate rotating logs per spider

# =============================================================================
# ITEM PIPELINES CONFIGURATION
# =============================================================================
# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# ITEM_PIPELINES defines the order in which pipelines will be processed.
# Lower numbers mean higher priority.
ITEM_PIPELINES = {
    # 1. Extracción y Validación Inicial (si se implementa como pipeline)
    # 'scraper_core.pipelines.ExtractAndValidatePipeline': 100,

    # 2. Limpieza de Datos
    'scraper_core.pipelines.cleaning.DataCleaningPipeline': 200,
    # 'scraper_core.pipelines.CleanArticleItemsPipeline': 200, # Alternativa o complemento

    # 3. Validación de Datos Post-Limpieza
    'scraper_core.pipelines.validation.DataValidationPipeline': 300,

    # 4. Almacenamiento en Supabase (Descomentar para activar)
    'scraper_core.pipelines.SupabaseStoragePipeline': 400, # Asumiendo que está en scraper_core/pipelines.py
    # 'scraper_core.pipelines.supabase_pipeline.SupabaseStoragePipeline': 400, # Si se movió a un sub-módulo

    # Otros pipelines (ej. exportación a archivos, etc.)
    # 'scraper_core.pipelines.JsonWriterPipeline': 900,
}
# =============================================================================
# PLAYWRIGHT CONFIGURATION (TWISTED_REACTOR)
# =============================================================================
# For Playwright support
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "timeout": 30 * 1000,  # 30 seconds
}

# PLAYWRIGHT_CONTEXT_OPTIONS = {
#     "ignore_https_errors": True,
# }
# PLAYWRIGHT_NAVIGATION_TIMEOUT = 30 * 1000 # 30 seconds

# =============================================================================
# HTTP CACHE CONFIGURATION
# =============================================================================
# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0  # Cache forever (useful for development)
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [] # Cache all responses
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"
#HTTPCACHE_POLICY = 'scrapy.extensions.httpcache.RFC2616Policy' # Default policy

# =============================================================================
# AUTO THROTTLE CONFIGURATION
# =============================================================================
# Enable and configure AutoThrottle
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay (seconds)
AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies (seconds)
AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = False

# =============================================================================
# ROBOTS.TXT COMPLIANCE
# =============================================================================
# Obey robots.txt rules (already set above, but documented here for clarity)
# ROBOTSTXT_OBEY = True  # This is already set at the top of the file
# The RobotsTxtMiddleware is enabled by default in DOWNLOADER_MIDDLEWARES_BASE
# with priority 100, so we don't need to add it explicitly

# =============================================================================
# DOMAIN-SPECIFIC RATE LIMITING
# =============================================================================
# Configure per-domain download delays and concurrency settings
# This allows fine-grained control over request rates for specific domains
# Import configuration from domain_config module for better organization
DOWNLOAD_SLOTS = DOMAIN_RATE_LIMITS

# Global download delay randomization settings
# When randomize_delay is True, the actual delay will be:
# 0.5 * DOWNLOAD_DELAY to 1.5 * DOWNLOAD_DELAY
RANDOMIZE_DOWNLOAD_DELAY = True

# =============================================================================
# SUPABASE CONFIGURATION
# =============================================================================
# Supabase connection details (loaded from .env)
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') # For admin operations
SUPABASE_KEY = os.getenv('SUPABASE_KEY') # Public anon key if needed for RLS
SUPABASE_HTML_BUCKET = os.getenv('SUPABASE_HTML_BUCKET', 'html_content')

# =============================================================================
# TENACITY RETRY CONFIGURATION FOR PIPELINES (Ej. Supabase)
# =============================================================================
TENACITY_STOP_AFTER_ATTEMPT = int(os.getenv('TENACITY_STOP_AFTER_ATTEMPT', 3))
TENACITY_WAIT_MULTIPLIER = float(os.getenv('TENACITY_WAIT_MULTIPLIER', 1)) # seconds
TENACITY_WAIT_MIN = float(os.getenv('TENACITY_WAIT_MIN', 2)) # seconds
TENACITY_WAIT_MAX = float(os.getenv('TENACITY_WAIT_MAX', 10)) # seconds

# =============================================================================
# VALIDATION PIPELINE CONFIGURATION
# =============================================================================
# Fields required for an item to be considered valid
VALIDATION_REQUIRED_FIELDS = ['url', 'titulo', 'medio_nombre', 'fecha_extraccion']

# Fields that must not be empty if present
VALIDATION_NON_EMPTY_FIELDS = ['url', 'titulo', 'medio_nombre']

# Max length for certain text fields (0 means no limit)
VALIDATION_MAX_LENGTHS = {
    'url': 2048,
    'titulo': 512,
    'subtitulo': 1024,
    'autor': 256,
    'medio_nombre': 256,
    'categoria': 128,
}

# Allowed date formats for validation (ISO 8601 is preferred)
VALIDATION_DATE_FORMATS = ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"]

# Fields to check for valid URL format
VALIDATION_URL_FIELDS = ['url', 'url_original', 'medio_url_base']

# Fields that should be lists/arrays
VALIDATION_LIST_FIELDS = ['etiquetas']

# Fields that should be dictionaries/objects
# VALIDATION_DICT_FIELDS = ['metadata_extra']

# If True, items failing validation will be dropped.
# If False, they will be passed through with an 'error_validation' field.
VALIDATION_DROP_INVALID_ITEMS = False

# Fields to include in the validation summary (for logging or item field)
VALIDATION_SUMMARY_FIELDS = ['url', 'titulo', 'medio', 'contenido_texto']

# =============================================================================
# CLEANING PIPELINE CONFIGURATION
# =============================================================================

# Cleaning options
CLEANING_STRIP_HTML = True           # Strip HTML tags from text fields
CLEANING_NORMALIZE_WHITESPACE = True # Normalize whitespace in text
CLEANING_REMOVE_EMPTY_LINES = True   # Remove empty lines from content
CLEANING_STANDARDIZE_QUOTES = True   # Standardize quote characters
CLEANING_PRESERVE_HTML_CONTENT = True # Clean but preserve HTML structure

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Get logging configuration from centralized config
logging_settings = LoggingConfig.get_scrapy_settings()

# Apply logging settings
LOG_LEVEL = logging_settings['LOG_LEVEL']
LOG_FORMAT = logging_settings['LOG_FORMAT']
LOG_DATEFORMAT = logging_settings['LOG_DATEFORMAT']
LOG_STDOUT = logging_settings.get('LOG_STDOUT', False)
LOG_SHORT_NAMES = logging_settings.get('LOG_SHORT_NAMES', False)

# File logging (if enabled)
if 'LOG_FILE' in logging_settings:
    LOG_FILE = logging_settings['LOG_FILE']
    LOG_FILE_ENCODING = logging_settings.get('LOG_FILE_ENCODING', 'utf-8')

# Component-specific log levels
LOGGERS = logging_settings['LOGGERS']

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
# USER AGENT ROTATION CONFIGURATION
# =============================================================================

# scrapy-user-agents configuration
# The middleware will randomly select user agents from a predefined list
# This helps prevent detection and blocking by websites

# Optional: You can specify fallback user agents if needed
# If not specified, the middleware uses its internal list
# RANDOM_UA_TYPE = 'random'  # Options: 'random', 'desktop', 'mobile'

# =============================================================================
# SCRAPY-CRAWL-ONCE CONFIGURATION
# =============================================================================

# Enable scrapy-crawl-once middleware for duplicate prevention
CRAWL_ONCE_ENABLED = True

# Path to store crawled requests database
# By default uses .scrapy/crawl_once/ directory
CRAWL_ONCE_PATH = project_root / '.scrapy' / 'crawl_once'

# Default value for crawl_once meta key (False by default)
# When True, all requests are handled by this middleware unless disabled explicitly
# We keep it False to have explicit control over which requests to track
CRAWL_ONCE_DEFAULT = False

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
