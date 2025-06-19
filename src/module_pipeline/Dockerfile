# Use Python 3.9 slim image for smaller size and security
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for ML libraries
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    g++ \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download SpaCy models (required for pipeline processing)
RUN python -m spacy download es_core_news_lg && \
    python -m spacy download en_core_web_sm

# Create application user for security
RUN useradd --create-home --shell /bin/bash pipeline && \
    chown -R pipeline:pipeline /app

# Copy application code
COPY src/ ./src/
COPY .env.example .env

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs \
             /app/metrics \
             /app/prompts \
             /app/scripts && \
    chown -R pipeline:pipeline /app

# Switch to non-root user
USER pipeline

# Set default environment variables for FastAPI pipeline
ENV PIPELINE_API_HOST=0.0.0.0 \
    PIPELINE_API_PORT=8003 \
    LOG_LEVEL=INFO \
    DEBUG_MODE=false \
    CORS_ORIGINS=["http://localhost:3000","http://localhost:8002"] \
    PROJECT_NAME="La Máquina de Noticias - Pipeline" \
    PROJECT_VERSION="1.0.0"

# Expose FastAPI port
EXPOSE 8003

# Health check for FastAPI application
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Change to src directory and run FastAPI application
WORKDIR /app/src
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"]
