#!/bin/bash

# Script para ejecutar todos los tests del Dashboard Review Frontend
# con diferentes configuraciones y reportes

echo "🧪 Dashboard Review Frontend - Test Suite Completa"
echo "=================================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: No se encontró package.json${NC}"
    echo "Por favor ejecuta este script desde el directorio raíz del módulo"
    exit 1
fi

# Función para ejecutar tests y capturar resultado
run_test_suite() {
    local suite_name=$1
    local test_command=$2
    
    echo -e "${YELLOW}Ejecutando: $suite_name${NC}"
    echo "Comando: $test_command"
    echo ""
    
    if $test_command; then
        echo -e "${GREEN}✓ $suite_name completado exitosamente${NC}"
        return 0
    else
        echo -e "${RED}✗ $suite_name falló${NC}"
        return 1
    fi
    echo ""
}

# Instalar dependencias si no existen
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependencias..."
    npm install
    echo ""
fi

# Limpiar reportes anteriores
echo "🧹 Limpiando reportes anteriores..."
rm -rf coverage/
rm -rf test-results/
mkdir -p test-results
echo ""

# Variables para tracking
TOTAL_TESTS=0
FAILED_TESTS=0

# 1. Tests Unitarios
echo "1️⃣ TESTS UNITARIOS"
echo "=================="
if run_test_suite "Tests Unitarios" "npm test -- --run tests/unit"; then
    ((TOTAL_TESTS++))
else
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
fi

# 2. Tests de Integración - Flujos Editoriales
echo "2️⃣ TESTS DE INTEGRACIÓN - FLUJOS EDITORIALES"
echo "============================================"
if run_test_suite "Flujos Editoriales" "npm test -- --run tests/integration/flows/editorial-review-flow.test.tsx"; then
    ((TOTAL_TESTS++))
else
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
fi

# 3. Tests de Performance
echo "3️⃣ TESTS DE PERFORMANCE"
echo "======================="
if run_test_suite "Performance" "npm test -- --run tests/integration/performance/dashboard-performance.test.tsx"; then
    ((TOTAL_TESTS++))
else
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
fi

# 4. Tests de Concurrencia
echo "4️⃣ TESTS DE CONCURRENCIA"
echo "========================"
if run_test_suite "Concurrencia y Race Conditions" "npm test -- --run tests/integration/concurrency/concurrency-race-conditions.test.tsx"; then
    ((TOTAL_TESTS++))
else
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
fi

# 5. Tests de Error Recovery
echo "5️⃣ TESTS DE ERROR RECOVERY"
echo "=========================="
if run_test_suite "Error Recovery" "npm test -- --run tests/integration/error-recovery/error-recovery.test.tsx"; then
    ((TOTAL_TESTS++))
else
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
fi

# 6. Coverage Report
echo "📊 GENERANDO REPORTE DE COBERTURA"
echo "================================="
npm run test:coverage -- --run

# Resumen Final
echo ""
echo "📋 RESUMEN FINAL"
echo "================"
echo "Total de suites ejecutadas: $TOTAL_TESTS"
echo "Suites exitosas: $((TOTAL_TESTS - FAILED_TESTS))"
echo "Suites fallidas: $FAILED_TESTS"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ Todos los tests pasaron exitosamente!${NC}"
    echo ""
    echo "📊 Reporte de cobertura disponible en: ./coverage/index.html"
    echo "   Abre el archivo en tu navegador para ver los detalles"
    exit 0
else
    echo -e "${RED}❌ Algunos tests fallaron. Por favor revisa los logs anteriores.${NC}"
    exit 1
fi
