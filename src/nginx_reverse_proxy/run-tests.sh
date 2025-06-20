#!/bin/bash
# run-tests.sh - Script para ejecutar los tests del módulo nginx_reverse_proxy

set -e

echo "🧪 Iniciando tests para nginx_reverse_proxy..."
echo "================================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "config/nginx.conf" ]; then
    echo -e "${RED}❌ Error: No se encontró config/nginx.conf${NC}"
    echo "Por favor ejecuta este script desde el directorio nginx_reverse_proxy"
    exit 1
fi

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker no está instalado${NC}"
    exit 1
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: Python 3 no está instalado${NC}"
    exit 1
fi

# Crear red si no existe
echo -e "${YELLOW}📡 Verificando red Docker...${NC}"
if ! docker network ls | grep -q lamacquina_network; then
    echo "Creando red lamacquina_network..."
    docker network create lamacquina_network
fi

# Instalar dependencias si no están instaladas
if ! python3 -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}📦 Instalando dependencias de test...${NC}"
    pip install -r requirements-test.txt
fi

# Limpiar containers de tests anteriores
echo -e "${YELLOW}🧹 Limpiando containers de tests anteriores...${NC}"
docker rm -f nginx_reverse_proxy_test mock_dashboard_backend mock_dashboard_frontend 2>/dev/null || true

# Ejecutar tests
echo -e "${YELLOW}🚀 Ejecutando tests...${NC}"
echo ""

# Tests unitarios primero (rápidos)
echo -e "${GREEN}=== Tests Unitarios ===${NC}"
python3 -m pytest tests/unit/ -v --tb=short

echo ""
echo -e "${GREEN}=== Tests de Integración ===${NC}"
python3 -m pytest tests/integration/ -v --tb=short

# Generar reporte de cobertura
echo ""
echo -e "${YELLOW}📊 Generando reporte de cobertura...${NC}"
python3 -m pytest tests/ --cov=. --cov-report=term-missing --cov-report=html

# Limpiar containers de test
echo ""
echo -e "${YELLOW}🧹 Limpiando recursos de test...${NC}"
docker rm -f nginx_reverse_proxy_test mock_dashboard_backend mock_dashboard_frontend 2>/dev/null || true

echo ""
echo -e "${GREEN}✅ Tests completados!${NC}"
echo ""
echo "📊 Reporte de cobertura HTML disponible en: htmlcov/index.html"
echo ""

# Resumen de resultados
if [ $? -eq 0 ]; then
    echo -e "${GREEN}🎉 Todos los tests pasaron exitosamente!${NC}"
else
    echo -e "${RED}❌ Algunos tests fallaron. Revisa el output anterior.${NC}"
    exit 1
fi
