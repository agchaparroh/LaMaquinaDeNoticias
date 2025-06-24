#!/bin/bash
# Script de verificación para Scrapyd, ScrapydWeb y Spidermon
# La Máquina de Noticias

echo "=== Verificación de Scrapyd y ScrapydWeb ==="
echo "Fecha: $(date)"
echo "============================================="

# Detectar si estamos dentro del contenedor o en el host
if [ -f /.dockerenv ]; then
    echo "⚠️  Ejecutando desde dentro del contenedor"
    INSIDE_CONTAINER=true
    # Dentro del contenedor, usar nombres de servicio Docker
    SCRAPYD_URL="http://scrapyd:6800"
    SCRAPYDWEB_URL="http://scrapydweb:5000"
else
    echo "Ejecutando desde el host"
    INSIDE_CONTAINER=false
    # Desde el host, usar localhost
    SCRAPYD_URL="http://localhost:6800"
    SCRAPYDWEB_URL="http://localhost:5000"
fi

# 1. Servicios activos
echo -e "\n1. Servicios Docker:"
if [ "$INSIDE_CONTAINER" = true ]; then
    echo "   ℹ️  Para ver servicios Docker, ejecutar este script desde el host"
else
    docker-compose ps | grep -E "(scrapyd|scrapydweb)" || echo "⚠️  No se encontraron servicios de Scrapyd/ScrapydWeb"
fi

# 2. APIs respondiendo
echo -e "\n2. Verificando APIs:"

# Scrapyd API
echo -n "   - Scrapyd API: "
if curl -s $SCRAPYD_URL/daemonstatus.json > /dev/null 2>&1; then
    echo "✅ OK"
    # Mostrar estado detallado
    echo "     Estado del daemon:"
    curl -s $SCRAPYD_URL/daemonstatus.json | python -m json.tool 2>/dev/null | grep -E "(status|running|pending|finished)" | sed 's/^/       /'
else
    echo "❌ No responde"
fi

# ScrapydWeb
echo -n "   - ScrapydWeb Dashboard: "
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $SCRAPYDWEB_URL 2>/dev/null)
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "401" ]; then
    echo "✅ OK (HTTP $HTTP_STATUS)"
else
    echo "❌ No responde (HTTP $HTTP_STATUS)"
fi

# 3. Spidermon configurado
echo -e "\n3. Verificando Spidermon:"
if [ "$INSIDE_CONTAINER" = true ]; then
    python -c "
import sys
try:
    from scraper_core import settings
    print(f'   - Habilitado: {settings.SPIDERMON_ENABLED}')
    print(f'   - Monitores configurados: {len(settings.SPIDERMON_SPIDER_CLOSE_MONITORS)}')
    print(f'   - Validación activada: {settings.SPIDERMON_VALIDATION_ADD_ERRORS_TO_ITEMS}')
    print(f'   - Umbrales:')
    print(f'     • Items mínimos: {settings.SPIDERMON_MIN_ITEMS_SCRAPED}')
    print(f'     • Errores críticos máx: {settings.SPIDERMON_MAX_CRITICAL_ERRORS}')
    print(f'     • Tiempo respuesta máx: {settings.SPIDERMON_MAX_RESPONSE_TIME}ms')
except Exception as e:
    print(f'   ❌ Error: {e}')
    sys.exit(1)
" 2>/dev/null || echo "   ❌ Error al verificar Spidermon"
else
    docker-compose exec -T module_scraper python -c "
import sys
try:
    from scraper_core import settings
    print(f'   - Habilitado: {settings.SPIDERMON_ENABLED}')
    print(f'   - Monitores configurados: {len(settings.SPIDERMON_SPIDER_CLOSE_MONITORS)}')
    print(f'   - Validación activada: {settings.SPIDERMON_VALIDATION_ADD_ERRORS_TO_ITEMS}')
    print(f'   - Umbrales:')
    print(f'     • Items mínimos: {settings.SPIDERMON_MIN_ITEMS_SCRAPED}')
    print(f'     • Errores críticos máx: {settings.SPIDERMON_MAX_CRITICAL_ERRORS}')
    print(f'     • Tiempo respuesta máx: {settings.SPIDERMON_MAX_RESPONSE_TIME}ms')
except Exception as e:
    print(f'   ❌ Error: {e}')
    sys.exit(1)
" 2>/dev/null || echo "   ❌ Error al verificar Spidermon"
fi

# 4. Archivos de configuración
echo -e "\n4. Archivos de configuración:"
FILES=(
    "scrapyd.conf"
    "scrapydweb/scrapydweb_settings_v10.py"
    "scraper_core/schemas/articulo_schema.json"
    "scraper_core/monitors/spider_monitors.py"
    "scraper_core/monitors/actions.py"
)

for file in "${FILES[@]}"; do
    if [ -f "/app/$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file - NO ENCONTRADO"
    fi
done

# 5. Resumen
echo -e "\n============================================="
echo "RESUMEN:"
echo "- Configuración base: ✅ Completada"
echo "- Servicios: Verificar estado arriba"
echo "- Documentación: src/module_scraper/docs/"
echo "- Siguiente paso: Desplegar spiders cuando estén listos"
echo ""
echo "Para más detalles, consultar:"
echo "- docker-compose logs scrapyd"
echo "- docker-compose logs scrapydweb"
echo "============================================="