#!/bin/bash
# =====================================================
# VERIFICACIÓN DE ESTRUCTURA DE MIGRACIÓN
# =====================================================
# Archivo: verify_structure.sh
# Propósito: Verificar que la estructura de migración esté correcta
# Uso: ./verify_structure.sh

echo "🔍 Verificando estructura de migración..."
echo "========================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contadores
ERRORS=0
WARNINGS=0
SUCCESS=0

# Función para verificar directorio
check_directory() {
    local dir=$1
    local description=$2
    
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $description: $dir"
        ((SUCCESS++))
    else
        echo -e "${RED}✗${NC} $description: $dir (FALTANTE)"
        ((ERRORS++))
    fi
}

# Función para verificar archivo
check_file() {
    local file=$1
    local description=$2
    local required=$3  # true/false
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description: $file"
        ((SUCCESS++))
    else
        if [ "$required" = "true" ]; then
            echo -e "${RED}✗${NC} $description: $file (REQUERIDO - FALTANTE)"
            ((ERRORS++))
        else
            echo -e "${YELLOW}⚠${NC} $description: $file (OPCIONAL - FALTANTE)"
            ((WARNINGS++))
        fi
    fi
}

echo -e "${BLUE}📁 Verificando estructura de directorios...${NC}"

# Directorio principal
check_directory "migrations" "Directorio principal de migración"

# Directorios por categoría (en orden de ejecución)
check_directory "migrations/config" "Configuración global"
check_directory "migrations/01_schema" "Esquemas y extensiones"
check_directory "migrations/02_types_domains" "Tipos y dominios"
check_directory "migrations/03_tables" "Tablas principales"
check_directory "migrations/04_indexes" "Índices"
check_directory "migrations/05_functions" "Funciones PL/pgSQL"
check_directory "migrations/06_triggers" "Triggers"
check_directory "migrations/07_materialized_views" "Vistas materializadas"
check_directory "migrations/08_reference_data" "Datos de referencia"

# Directorios de apoyo
check_directory "migrations/rollbacks" "Scripts de rollback"
check_directory "migrations/validations" "Scripts de validación"

echo ""
echo -e "${BLUE}📄 Verificando archivos críticos...${NC}"

# Archivos críticos
check_file "migrations/README.md" "Documentación principal" "true"
check_file "migrations/config/migration_config.sql" "Configuración SQL" "true"
check_file "migrations/00_000_migration_control.sql" "Control de migración" "true"

# Crear directorio de logs si no existe
if [ ! -d "migrations/logs" ]; then
    mkdir -p "migrations/logs"
    echo -e "${GREEN}✓${NC} Directorio de logs creado: migrations/logs"
    ((SUCCESS++))
else
    echo -e "${GREEN}✓${NC} Directorio de logs existe: migrations/logs"
    ((SUCCESS++))
fi

echo ""
echo -e "${BLUE}🔧 Verificando convenciones de nomenclatura...${NC}"

# Verificar que los directorios siguen la convención numérica
declare -a expected_dirs=(
    "01_schema"
    "02_types_domains" 
    "03_tables"
    "04_indexes"
    "05_functions"
    "06_triggers"
    "07_materialized_views"
    "08_reference_data"
)

echo "Verificando convención numérica de directorios:"
for dir in "${expected_dirs[@]}"; do
    if [ -d "migrations/$dir" ]; then
        echo -e "${GREEN}✓${NC} $dir (convención correcta)"
    else
        echo -e "${RED}✗${NC} $dir (convención incorrecta o faltante)"
        ((ERRORS++))
    fi
done

echo ""
echo -e "${BLUE}📊 Verificando permisos y accesibilidad...${NC}"

# Verificar permisos de escritura
if [ -w "migrations" ]; then
    echo -e "${GREEN}✓${NC} Permisos de escritura en directorio migrations"
    ((SUCCESS++))
else
    echo -e "${RED}✗${NC} Sin permisos de escritura en directorio migrations"
    ((ERRORS++))
fi

# Verificar que los archivos SQL son legibles
sql_files_count=$(find migrations -name "*.sql" 2>/dev/null | wc -l)
echo -e "${GREEN}✓${NC} Archivos SQL encontrados: $sql_files_count"

echo ""
echo -e "${BLUE}📋 Generando reporte de estructura...${NC}"

# Crear reporte de estructura
cat > "migrations/structure_report.txt" << EOF
REPORTE DE ESTRUCTURA DE MIGRACIÓN
==================================
Generado: $(date)
Usuario: $(whoami)
Directorio: $(pwd)

ESTRUCTURA DE DIRECTORIOS:
$(tree migrations 2>/dev/null || find migrations -type d | sort)

ARCHIVOS POR CATEGORÍA:
EOF

# Contar archivos por directorio
for dir in migrations/*/; do
    if [ -d "$dir" ]; then
        dir_name=$(basename "$dir")
        file_count=$(find "$dir" -name "*.sql" 2>/dev/null | wc -l)
        echo "$dir_name: $file_count archivos SQL" >> "migrations/structure_report.txt"
    fi
done

echo -e "${GREEN}✓${NC} Reporte generado: migrations/structure_report.txt"

echo ""
echo "========================================"
echo -e "${BLUE}📊 RESUMEN DE VERIFICACIÓN${NC}"
echo "========================================"
echo -e "${GREEN}✓ Éxitos: $SUCCESS${NC}"
echo -e "${YELLOW}⚠ Advertencias: $WARNINGS${NC}"
echo -e "${RED}✗ Errores: $ERRORS${NC}"

if [ $ERRORS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 ESTRUCTURA VÁLIDA${NC}"
    echo "La estructura de migración está correctamente configurada."
    exit 0
else
    echo ""
    echo -e "${RED}❌ ESTRUCTURA INCOMPLETA${NC}"
    echo "Se encontraron $ERRORS errores que deben corregirse."
    exit 1
fi
