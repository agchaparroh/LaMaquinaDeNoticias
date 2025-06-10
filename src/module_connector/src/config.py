import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Directory paths
SCRAPER_OUTPUT_DIR = os.getenv('SCRAPER_OUTPUT_DIR', '/data/scrapy_output/pending')
PIPELINE_PENDING_DIR = os.getenv('PIPELINE_PENDING_DIR', '/data/pipeline_input/pending')
PIPELINE_COMPLETED_DIR = os.getenv('PIPELINE_COMPLETED_DIR', '/data/pipeline_input/completed')
PIPELINE_ERROR_DIR = os.getenv('PIPELINE_ERROR_DIR', '/data/pipeline_input/error')

# API configuration
PIPELINE_API_URL = os.getenv('PIPELINE_API_URL', 'http://localhost:8001')

# Polling interval in seconds
POLLING_INTERVAL = int(os.getenv('POLLING_INTERVAL', '5'))

# Retry configuration  
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
RETRY_BACKOFF = float(os.getenv('RETRY_BACKOFF', '2.0'))

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Optional Sentry configuration
ENABLE_SENTRY = os.getenv('ENABLE_SENTRY', 'false').lower() == 'true'
SENTRY_DSN = os.getenv('SENTRY_DSN', '')
