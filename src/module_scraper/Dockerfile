# Use Python 3.10 slim image (optimal for Scrapy + Playwright)
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for Scrapy and Playwright
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (required for scrapy-playwright)
RUN playwright install chromium --with-deps

# Create application user for security
RUN useradd --create-home --shell /bin/bash scraper && \
    chown -R scraper:scraper /app

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs \
             /app/data \
             /app/output \
             /app/.scrapy && \
    chown -R scraper:scraper /app

# Switch to non-root user
USER scraper

# Set default environment variables for Scrapy
ENV SCRAPY_SETTINGS_MODULE=scraper_core.settings \
    LOG_LEVEL=INFO \
    SCRAPY_PROJECT=scraper_core \
    CONCURRENT_REQUESTS=16 \
    DOWNLOAD_DELAY=1 \
    PYTHONPATH=/app

# Health check - verify scrapy is available
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD scrapy version || exit 1

# Default command - keep container running
# To run a spider, use: docker exec lamacquina_scraper scrapy crawl spider_name
CMD ["tail", "-f", "/dev/null"]
