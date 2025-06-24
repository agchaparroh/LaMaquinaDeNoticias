# ScrapydWeb Dockerfile for La Máquina de Noticias
# Provides a web dashboard for managing Scrapyd clusters

FROM python:3.10-slim

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
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install ScrapydWeb como root
RUN pip install --no-cache-dir scrapydweb

# Create application user for security
RUN useradd --create-home --shell /bin/bash scrapydweb

# SOLUCIÓN: Pre-crear los directorios que ScrapydWeb necesita en site-packages
# y darle ownership al usuario scrapydweb
RUN python -c "import site; print(site.getsitepackages()[0])" > /tmp/site_packages.txt && \
    SITE_PACKAGES=$(cat /tmp/site_packages.txt) && \
    mkdir -p ${SITE_PACKAGES}/scrapydweb/data/database && \
    mkdir -p ${SITE_PACKAGES}/scrapydweb/data/logs && \
    chown -R scrapydweb:scrapydweb ${SITE_PACKAGES}/scrapydweb/data && \
    rm /tmp/site_packages.txt

# Create data directory structure para nuestros datos reales
RUN mkdir -p /var/lib/scrapydweb \
             /var/lib/scrapydweb/data \
             /var/lib/scrapydweb/logs \
             /var/lib/scrapydweb/database \
             /var/lib/scrapydweb/projects \
             /var/lib/scrapydweb/jobs \
             /app/config

# Set correct ownership
RUN chown -R scrapydweb:scrapydweb /var/lib/scrapydweb /app /home/scrapydweb

# Copy scripts and configuration
COPY --chown=scrapydweb:scrapydweb startup.sh /app/startup.sh
COPY --chown=scrapydweb:scrapydweb scrapydweb_wrapper.py /app/scrapydweb_wrapper.py
RUN chmod +x /app/startup.sh /app/scrapydweb_wrapper.py

# Set environment variables for ScrapydWeb
ENV SCRAPYDWEB_BIND=0.0.0.0 \
    SCRAPYDWEB_PORT=5000 \
    SCRAPYDWEB_DATA_PATH=/var/lib/scrapydweb \
    SCRAPYDWEB_LOGS_DIR=/var/lib/scrapydweb/logs \
    SCRAPYDWEB_DATABASE_URL=sqlite:////var/lib/scrapydweb/database/scrapydweb.db \
    SCRAPYDWEB_JOBS_TO_KEEP=100 \
    SCRAPYDWEB_LOCAL_SCRAPYD_LOGS_DIR=/var/lib/scrapydweb/scrapyd_logs \
    SCRAPYDWEB_SETTINGS_PY=/app/config/scrapydweb_settings_v10.py

# Switch to non-root user
USER scrapydweb

# Expose ScrapydWeb port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000 || exit 1

# Use startup script
CMD ["/app/startup.sh"]