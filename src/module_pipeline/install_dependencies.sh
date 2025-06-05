#!/bin/bash
# Script de Instalación de Dependencias - Module Pipeline
# Basado en análisis de compatibilidad (version_analysis.md)

echo "🚀 INSTALACIÓN DE DEPENDENCIAS - MODULE PIPELINE"
echo "================================================="
echo "Fecha: $(date)"
echo "Ubicación: $(pwd)"
echo ""

# Paso 1: Verificar entorno
echo "📋 Paso 1: Verificar entorno Python..."
python verify_env.py
if [ $? -ne 0 ]; then
    echo "❌ Verificación de entorno falló"
    exit 1
fi
echo ""

# Paso 2: Instalación de dependencias principales
echo "📦 Paso 2: Instalando dependencias desde requirements.txt..."
echo "Versiones sincronizadas con ecosistema La Máquina de Noticias:"
echo "  - pydantic==2.11.5 (sync: module_connector)"
echo "  - tenacity==9.1.2 (sync: module_connector)"
echo "  - loguru==0.7.3 (sync: module_connector)"
echo "  - python-dotenv==1.1.0 (sync: module_connector)"
echo "  - supabase==2.15.2 (versión avanzada para RPCs)"
echo ""

pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Instalación de dependencias falló"
    exit 1
fi
echo ""

# Paso 3: Verificar instalación
echo "🔍 Paso 3: Verificando versiones instaladas..."
pip freeze > installed_versions.txt
echo "✅ Versiones instaladas guardadas en installed_versions.txt"
echo ""

# Paso 4: Verificar librerías críticas
echo "🧪 Paso 4: Verificando imports de librerías críticas..."
python -c "
import sys
critical_libs = [
    ('fastapi', 'FastAPI framework'),
    ('groq', 'Groq SDK'),
    ('supabase', 'Supabase client'),
    ('pydantic', 'Data validation'),
    ('loguru', 'Logging framework'),
    ('tenacity', 'Retry logic'),
    ('httpx', 'HTTP client')
]

print('Verificando imports críticos:')
for lib, desc in critical_libs:
    try:
        __import__(lib)
        print(f'✅ {lib} ({desc})')
    except ImportError as e:
        print(f'❌ {lib} ({desc}) - {e}')
        sys.exit(1)

print('\n🎉 Todos los imports críticos exitosos')
"

if [ $? -ne 0 ]; then
    echo "❌ Verificación de imports falló"
    exit 1
fi
echo ""

# Paso 5: Verificar spaCy (si está habilitado)
echo "🔤 Paso 5: Verificando configuración spaCy..."
USE_SPACY=$(grep -o 'USE_SPACY_FILTER.*' .env 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "false")
echo "USE_SPACY_FILTER: $USE_SPACY"

if [ "$USE_SPACY" = "true" ]; then
    echo "📥 Instalando modelos spaCy..."
    python -m spacy download es_core_news_lg
    python -m spacy download en_core_web_sm
    echo "✅ Modelos spaCy instalados"
else
    echo "ℹ️ spaCy deshabilitado en configuración"
fi
echo ""

# Paso 6: Verificación final con script de setup
echo "✅ Paso 6: Verificación final del entorno..."
python scripts/setup_env.py
echo ""

# Resumen final
echo "📋 RESUMEN DE INSTALACIÓN"
echo "========================="
echo "✅ Dependencias instaladas desde requirements.txt"
echo "✅ Versiones sincronizadas con ecosistema"
echo "✅ Imports críticos verificados"
echo "✅ Archivo installed_versions.txt generado"
echo ""
echo "📄 Archivos generados:"
echo "  - installed_versions.txt (auditoría de versiones)"
echo "  - version_analysis.md (análisis de compatibilidad)"
echo ""
echo "🎯 Próximos pasos:"
echo "  1. Configurar variables críticas en .env"
echo "  2. Ejecutar: python scripts/test_connections.py"
echo "  3. Proceder con Tarea 3 (configuración centralizada)"
echo ""
echo "🎉 ¡Instalación de dependencias completada exitosamente!"
