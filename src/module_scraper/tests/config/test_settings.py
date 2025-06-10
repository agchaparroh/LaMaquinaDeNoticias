# src/module_scraper/tests/config/test_settings.py
from scraper_core.settings import *

# Override settings for testing
# Example: Use a different database for testing or mock external services
SUPABASE_URL = None  # Disable Supabase for most tests
SUPABASE_SERVICE_ROLE_KEY = None
SUPABASE_KEY = None

LOG_LEVEL = 'INFO'  # Less verbose logging for tests
HTTPCACHE_ENABLED = False # Disable HTTP cache for tests

# Disable crawl once for tests by default, can be enabled per test
CRAWL_ONCE_ENABLED = False

# Use a test-specific path for crawl once if enabled
CRAWL_ONCE_PATH = str(Path(__file__).resolve().parent.parent / '.scrapy_test' / 'crawl_once')


# Make sure Playwright uses a different user data dir for tests to avoid conflicts
# This is a placeholder, actual playwright settings might need more specific overrides
# depending on how tests are structured (e.g. if they run in parallel)
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "timeout": 30 * 1000,  # 30 seconds
    # "user_data_dir": str(Path(__file__).resolve().parent.parent / '.playwright_test_data') # Example
}

# Ensure a test environment marker is present
TEST_ENV = True
