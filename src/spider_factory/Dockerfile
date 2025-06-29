# Multi-stage build para Spider Factory 2.0 Backend
FROM python:3.9-slim-bullseye AS builder

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libssl-dev \
    libffi-dev \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /build

# Copiar requirements y instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage final - imagen más ligera
FROM python:3.9-slim-bullseye

# Instalar solo dependencias runtime
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad
RUN groupadd -r spiderfactory && useradd -r -g spiderfactory spiderfactory

# Establecer directorio de trabajo
WORKDIR /app

# Copiar dependencias Python desde el builder
COPY --from=builder /root/.local /home/spiderfactory/.local

# Copiar código de la aplicación
COPY --chown=spiderfactory:spiderfactory . .

# Crear directorios necesarios con permisos correctos
RUN mkdir -p logs generated_spiders templates/spiders backups/migrations \
    && chown -R spiderfactory:spiderfactory /app

# Configurar PATH para incluir paquetes de usuario
ENV PATH=/home/spiderfactory/.local/bin:$PATH

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    REDIS_HOST=redis \
    REDIS_PORT=6379 \
    SPIDER_FACTORY_ENV=production

# Cambiar a usuario no-root
USER spiderfactory

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando optimizado para producción (sin --reload)
CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]