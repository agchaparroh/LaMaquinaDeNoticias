# Dockerfile optimizado con multi-stage build
# Reducción esperada: 7GB → ~2-2.5GB

# ===== STAGE 1: Builder =====
FROM python:3.11-slim as builder

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo para el builder
WORKDIR /build

# Copiar solo requirements para aprovechar cache de Docker
COPY requirements-prod.txt .

# Crear wheels de todas las dependencias
# Esto pre-compila las dependencias para reutilizar en la imagen final
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements-prod.txt

# ===== STAGE 2: Runtime =====
FROM python:3.11-slim

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Optimizaciones de Python
    PYTHONOPTIMIZE=1

# Instalar solo dependencias runtime mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Para health checks
    curl \
    # Librerías compartidas necesarias
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Directorio de trabajo
WORKDIR /app

# Copiar wheels pre-compilados del builder
COPY --from=builder /wheels /wheels

# Copiar requirements
COPY requirements-prod.txt .

# Instalar desde wheels (mucho más rápido y sin compilación)
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements-prod.txt \
    && rm -rf /wheels

# Descargar modelos de spaCy optimizados
# Usar modelos medianos/pequeños para reducir tamaño
RUN python -m spacy download es_core_news_md && \
    python -m spacy download en_core_web_sm && \
    # Limpiar cache de pip después de descargar modelos
    rm -rf /root/.cache/pip

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash --uid 1000 pipeline && \
    mkdir -p /app/logs /app/metrics /app/prompts && \
    chown -R pipeline:pipeline /app

# Copiar código de la aplicación
COPY --chown=pipeline:pipeline src/ ./src/
COPY --chown=pipeline:pipeline prompts/ ./prompts/

# Copiar archivo de configuración de ejemplo
COPY --chown=pipeline:pipeline .env.example .env

# Cambiar a usuario no-root
USER pipeline

# Variables de entorno para la aplicación
ENV PIPELINE_API_HOST=0.0.0.0 \
    PIPELINE_API_PORT=8003 \
    LOG_LEVEL=INFO \
    DEBUG_MODE=false \
    CORS_ORIGINS='["http://localhost:3000","http://localhost:8002"]' \
    PROJECT_NAME="La Máquina de Noticias - Pipeline" \
    PROJECT_VERSION="1.0.0" \
    # Optimizaciones de Uvicorn
    WEB_CONCURRENCY=1 \
    UVICORN_WORKERS=1

# Exponer puerto
EXPOSE 8003

# Health check optimizado
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Comando de inicio optimizado (sin --reload en producción)
CMD ["python", "-m", "uvicorn", "src.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8003", \
     "--workers", "1", \
     "--loop", "uvloop", \
     "--no-access-log"]

# ===== OPTIMIZACIONES APLICADAS =====
# 1. Multi-stage build: separa compilación de runtime
# 2. Wheels pre-compilados: evita recompilación
# 3. Modelos spaCy medianos: es_core_news_md (47MB) vs lg (568MB)
# 4. Sin dependencias de desarrollo: ~200MB menos
# 5. Limpieza agresiva de cache: apt, pip
# 6. Python optimizado: PYTHONOPTIMIZE=1
# 7. Uvicorn optimizado: uvloop, sin access logs
# 8. .dockerignore mejorado: excluye ~200MB de archivos
#
# Tamaño esperado final: ~2-2.5GB (reducción del 65-70%)