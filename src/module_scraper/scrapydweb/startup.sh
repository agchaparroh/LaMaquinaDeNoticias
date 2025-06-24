#!/bin/bash
# Startup script for ScrapydWeb
# La Máquina de Noticias

set -e

echo "=== Iniciando ScrapydWeb ==="
echo "Fecha: $(date)"
echo "Usuario: $(whoami)"
echo "DATA_PATH: ${SCRAPYDWEB_DATA_PATH}"

# Crear directorios necesarios si no existen
echo "Creando directorios de datos..."
mkdir -p ${SCRAPYDWEB_DATA_PATH}/data
mkdir -p ${SCRAPYDWEB_DATA_PATH}/logs
mkdir -p ${SCRAPYDWEB_DATA_PATH}/database
mkdir -p ${SCRAPYDWEB_DATA_PATH}/projects
mkdir -p ${SCRAPYDWEB_DATA_PATH}/jobs
mkdir -p ${SCRAPYDWEB_DATA_PATH}/scrapyd_logs

# Verificar permisos
echo "Verificando permisos..."
ls -la ${SCRAPYDWEB_DATA_PATH}/

# IMPORTANTE: Copiar nuestro archivo de configuración al directorio de trabajo
# ScrapydWeb busca scrapydweb_settings_v10.py en el directorio actual
if [ -f "/app/config/scrapydweb_settings_v10.py" ]; then
    echo "Copiando archivo de configuración personalizado..."
    cp /app/config/scrapydweb_settings_v10.py /app/scrapydweb_settings_v10.py
    # También crear un enlace como v11 por si ScrapydWeb lo busca
    cp /app/config/scrapydweb_settings_v10.py /app/scrapydweb_settings_v11.py
    echo "Archivos de configuración copiados."
else
    echo "ERROR: No se encontró el archivo de configuración personalizado"
fi

# Configurar variables de entorno adicionales
export SCRAPYDWEB_SCRAPYD_SERVERS=${SCRAPYDWEB_SCRAPYD_SERVERS:-"['scrapyd:6800']"}

echo "=== Configuración ==="
echo "BIND: ${SCRAPYDWEB_BIND}:${SCRAPYDWEB_PORT}"
echo "SCRAPYD_SERVERS: ${SCRAPYDWEB_SCRAPYD_SERVERS}"
echo "SETTINGS_PY: ${SCRAPYDWEB_SETTINGS_PY}"
echo "===================="

# Verificar que Scrapyd esté disponible
echo "Verificando conectividad con Scrapyd..."
for i in {1..10}; do
    if curl -s http://scrapyd:6800/daemonstatus.json > /dev/null 2>&1; then
        echo "✓ Scrapyd está disponible"
        break
    else
        echo "Esperando a Scrapyd... intento $i/10"
        sleep 2
    fi
done

# Usar el wrapper para iniciar ScrapydWeb
echo "Iniciando ScrapydWeb con wrapper..."
cd /app
exec python /app/scrapydweb_wrapper.py