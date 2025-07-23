# Dockerfile simplificado para supabase-mcp-server
FROM python:3.12-slim-bookworm

# Crear usuario no privilegiado
RUN groupadd --gid 1000 mcpuser && \
    useradd --uid 1000 --gid mcpuser --shell /bin/bash --create-home mcpuser

# Crear directorio de aplicación
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Instalar el paquete directamente desde PyPI
RUN pip install --no-cache-dir supabase-mcp-server

# Crear directorios necesarios con permisos correctos
RUN mkdir -p /home/mcpuser/.local/share/supabase-mcp && \
    chown -R mcpuser:mcpuser /home/mcpuser/.local

# Variables de entorno por defecto
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SUPABASE_PROJECT_REF="127.0.0.1:54322" \
    SUPABASE_DB_PASSWORD="postgres" \
    SUPABASE_REGION="us-east-1" \
    QUERY_API_KEY="test-key"

# Cambiar a usuario no privilegiado
USER mcpuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import supabase_mcp; print('OK')" || exit 1

# Comando por defecto
CMD ["supabase-mcp-server"]