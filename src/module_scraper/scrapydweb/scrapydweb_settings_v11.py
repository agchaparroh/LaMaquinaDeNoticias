"""
ScrapydWeb Settings for La Máquina de Noticias
Configuration file for the ScrapydWeb dashboard
"""

import os

############################## IMPORTANT ######################################
# DATA_PATH configuration to avoid permission issues in Docker
DATA_PATH = os.environ.get("SCRAPYDWEB_DATA_PATH", "/var/lib/scrapydweb")

# Create subdirectories structure
SCRAPYDWEB_LOGS_DIR = os.path.join(DATA_PATH, "logs")
SCRAPYDWEB_DATA_DIR = os.path.join(DATA_PATH, "data")
SCRAPYDWEB_DATABASE_DIR = os.path.join(DATA_PATH, "database")
SCRAPYDWEB_JOBS_DIR = os.path.join(DATA_PATH, "jobs")

# Create directories if running locally (not in Docker)
if not os.path.exists("/.dockerenv"):
    for directory in [
        DATA_PATH,
        SCRAPYDWEB_LOGS_DIR,
        SCRAPYDWEB_DATA_DIR,
        SCRAPYDWEB_DATABASE_DIR,
        SCRAPYDWEB_JOBS_DIR,
    ]:
        os.makedirs(directory, exist_ok=True)

############################## ScrapydWeb #####################################
# Bind address and port
# The default is '0.0.0.0:5000', set it to '127.0.0.1:5000' to disable external access.
SCRAPYDWEB_BIND = os.environ.get("SCRAPYDWEB_BIND", "0.0.0.0")
SCRAPYDWEB_PORT = int(os.environ.get("SCRAPYDWEB_PORT", 5000))

# Enable debug mode to output additional information on the web page
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# Full path to the certificate key file to enable HTTPS
# e.g. '/home/username/cert/cert.key'
CERTIFICATE_FILEPATH = ""
PRIVATEKEY_FILEPATH = ""

############################## Authentication #################################
# Enable basic authentication
ENABLE_AUTH = True

# Basic auth credentials
USERNAME = os.getenv("SCRAPYDWEB_USERNAME", "admin")
PASSWORD = os.getenv("SCRAPYDWEB_PASSWORD", "lamaquina2025")

############################## Scrapy Projects ################################
# ScrapydWeb is able to locate projects in the SCRAPY_PROJECTS_DIR,
# so that you can simply select a project to deploy without entering its path
SCRAPY_PROJECTS_DIR = os.path.join(DATA_PATH, "projects")

############################## Local Scrapyd ##################################
# 'username:password@localhost:6801#group', 'localhost:6801', ('username', 'password', 'localhost', 6801, 'group'), or ('localhost', 6801)
LOCAL_SCRAPYD_SERVER = ""

# Set to True to hide the Items page and hide the Items column in the Jobs page
HIDE_SCRAPYD_ITEMS = False

# Path where Scrapyd stores logs (mounted volume)
LOCAL_SCRAPYD_LOGS_DIR = os.environ.get(
    "SCRAPYDWEB_LOCAL_SCRAPYD_LOGS_DIR", os.path.join(DATA_PATH, "scrapyd_logs")
)

############################## Scrapyd Cluster ################################
# e.g. [
# 'username:password@192.168.1.1:6801#group',
# 'username:password@192.168.1.2:6801#group',
# ]
SCRAPYD_SERVERS = [
    # Main Scrapyd server (running in Docker network)
    "scrapyd:6800",
    # Local Scrapyd server (if running outside Docker)
    # 'localhost:6800',
]

# Set to True to fetch HTML and XML response directly from your Scrapyd servers,
# instead of via the ScrapydWeb server.
SCRAPYD_SERVERS_PUBLIC_URLS = False

# Group servers for simultaneous job runs
SCRAPYD_SERVERS_GROUPS = []

# Update the Group column in the Servers page
SCRAPYD_SERVERS_AUTHS = []

############################## Timer Tasks ####################################
# Set to True to enable timer tasks for periodically checking and running jobs
ENABLE_TIMER = True

# How often to check for jobs to run, in seconds
TIMER_JOBS_INTERVAL = 300  # 5 minutes

# Timezone for the Timer Tasks
# e.g. 'Asia/Shanghai', 'Europe/London', check out https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
TIMEZONE = "America/Buenos_Aires"

############################## Email Notification ############################
# Set to True to enable email notification
ENABLE_EMAIL = os.environ.get("ENABLE_EMAIL_ALERT", "False").lower() == "true"

# SMTP settings
SMTP_SERVER = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_OVER_SSL = False
SMTP_CONNECTION_TIMEOUT = 10

# Email credentials
EMAIL_USERNAME = os.getenv("SMTP_USER", "")
EMAIL_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# Sender and recipients
FROM_ADDR = os.getenv("SMTP_FROM", "scrapydweb@lamaquina.com")
TO_ADDRS = (
    os.getenv("SMTP_TO", "alertas@lamaquina.com").split(",")
    if os.getenv("SMTP_TO")
    else []
)

# Subject prefix
EMAIL_SUBJECT_PREFIX = "[ScrapydWeb Alert]"

# Attachment settings
SMTP_ATTACHMENT_SIZE_LIMIT = 10 * 1024 * 1024  # 10 MB

############################## Webhook Notification ##########################
# Set to True to enable webhook notification
ENABLE_WEBHOOK = True if os.getenv("SPIDERMON_WEBHOOK_URL") else False

# Webhook URL for notifications
WEBHOOK_URL = os.getenv("SPIDERMON_WEBHOOK_URL", "")

# Additional headers for webhook requests
WEBHOOK_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "ScrapydWeb/LaMaquina",
}

# Timeout for webhook requests
WEBHOOK_TIMEOUT = 10

############################## Log Analysis ###################################
# Whether to enable LogParser for Scrapy log analysis and visualization
ENABLE_LOGPARSER = True

############################## Database #######################################
# The database URL for storing timer tasks, running stats, and logs parsing results
# Using SQLite in the configured data directory
DATABASE_URL = os.environ.get(
    "SCRAPYDWEB_DATABASE_URL",
    f"sqlite:///{os.path.join(SCRAPYDWEB_DATABASE_DIR, 'scrapydweb.db')}",
)

############################## Other Settings #################################
# Set to True to enable caching database query results in the memory, but RAM would be consumed
ENABLE_CACHE = True

# The interval between database backup, in seconds
DATABASE_BACKUP_INTERVAL = 86400  # 24 hours

# Jobs to keep in the database
JOBS_TO_KEEP = int(os.environ.get("SCRAPYDWEB_JOBS_TO_KEEP", 1000))
FINISHED_TO_KEEP = int(os.environ.get("SCRAPYDWEB_FINISHED_TO_KEEP", 1000))

# Request timeout for Scrapyd servers
REQUEST_TIMEOUT = 60

# Page size for pagination
ITEMS_PER_PAGE = 100

# Show crawl stats in the Jobs page
SHOW_CRAWL_STATS = True

# Show dashboard charts
SHOW_DASHBOARD_CHARTS = True

# Chart height in pixels
CHART_HEIGHT = 400

# Maximum number of points in charts
CHART_MAX_POINTS = 1000

############################## Monitoring & Alerts ############################
# Enable monitoring
ENABLE_MONITOR = os.environ.get("ENABLE_MONITOR", "False").lower() == "true"

# Alert thresholds
ALERT_THRESHOLD_ERROR_RATE = 0.1  # 10% error rate
ALERT_THRESHOLD_MIN_ITEMS = int(os.environ.get("SPIDERMON_MIN_ITEMS_SCRAPED", 1))
ALERT_THRESHOLD_RESPONSE_TIME = int(os.environ.get("SPIDERMON_MAX_RESPONSE_TIME", 5000))

# Alert cooldown period (to avoid spam)
ALERT_COOLDOWN = 3600  # 1 hour

# Monitor all spiders or specific ones
MONITOR_ALL_SPIDERS = True
MONITORED_SPIDERS = []  # e.g. ['spider1', 'spider2']

############################## Slack Notification #############################
ENABLE_SLACK_ALERT = os.environ.get("ENABLE_SLACK_ALERT", "False").lower() == "true"
SLACK_TOKEN = os.environ.get("SLACK_TOKEN", "")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "general")

############################## Telegram Notification ##########################
ENABLE_TELEGRAM_ALERT = (
    os.environ.get("ENABLE_TELEGRAM_ALERT", "False").lower() == "true"
)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID", "0"))

############################## Custom Settings ################################
# Add any custom settings below
# These will be available in ScrapydWeb via app.config['YOUR_SETTING']

# La Máquina de Noticias specific settings
PROJECT_NAME = "La Máquina de Noticias"
PROJECT_VERSION = "1.0.0"

# Integration with module_pipeline
PIPELINE_API_URL = os.getenv("PIPELINE_API_URL", "http://module_pipeline:8003")

# Integration with module_dashboard_review_backend
DASHBOARD_API_URL = os.getenv(
    "DASHBOARD_API_URL", "http://module_dashboard_review_backend:8004"
)

# Verbose logging
VERBOSE = os.environ.get("VERBOSE", "False").lower() == "true"
