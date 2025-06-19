#!/bin/sh
# health-check.sh - Health Check Mínimo
# Tiempo de implementación: 10 minutos
# 3 líneas de código, sin complejidad

# Verificar que nginx responde en el endpoint de health
curl -f http://localhost/nginx-health || exit 1
