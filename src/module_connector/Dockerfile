# Use Python 3.9 slim image for smaller size and security
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create application user for security
RUN useradd --create-home --shell /bin/bash connector && \
    chown -R connector:connector /app

# Copy application code
COPY src/ ./src/
COPY .env.example .env

# Create necessary directories with proper permissions
RUN mkdir -p /data/scrapy_output/pending \
             /data/pipeline_input/pending \
             /data/pipeline_input/completed \
             /data/pipeline_input/error \
             /app/logs && \
    chown -R connector:connector /data /app

# Switch to non-root user
USER connector

# Set default environment variables (can be overridden)
ENV SCRAPER_OUTPUT_DIR=/data/scrapy_output/pending \
    PIPELINE_PENDING_DIR=/data/pipeline_input/pending \
    PIPELINE_COMPLETED_DIR=/data/pipeline_input/completed \
    PIPELINE_ERROR_DIR=/data/pipeline_input/error \
    PIPELINE_API_URL=http://module-pipeline:8001 \
    POLLING_INTERVAL=5 \
    MAX_RETRIES=3 \
    RETRY_BACKOFF=2.0 \
    LOG_LEVEL=INFO

# Expose no ports (this is a worker service)

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/data/pipeline_input/pending') else 1)"

# Change to src directory and run the application
WORKDIR /app/src
CMD ["python", "main.py"]
