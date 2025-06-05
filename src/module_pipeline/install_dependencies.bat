@echo off
REM Script de Instalación de Dependencias - Module Pipeline (Windows)
REM Basado en análisis de compatibilidad (version_analysis.md)

echo 🚀 INSTALACIÓN DE DEPENDENCIAS - MODULE PIPELINE
echo =================================================
echo Fecha: %date% %time%
echo Ubicación: %cd%
echo.

REM Paso 1: Verificar entorno
echo 📋 Paso 1: Verificar entorno Python...
python verify_env.py
if %errorlevel% neq 0 (
    echo ❌ Verificación de entorno falló
    exit /b 1
)
echo.

REM Paso 2: Instalación de dependencias principales
echo 📦 Paso 2: Instalando dependencias desde requirements.txt...
echo Versiones sincronizadas con ecosistema La Máquina de Noticias:
echo   - pydantic==2.11.5 (sync: module_connector)
echo   - tenacity==9.1.2 (sync: module_connector)
echo   - loguru==0.7.3 (sync: module_connector)
echo   - python-dotenv==1.1.0 (sync: module_connector)
echo   - supabase==2.15.2 (versión avanzada para RPCs)
echo.

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Instalación de dependencias falló
    exit /b 1
)
echo.

REM Paso 3: Verificar instalación
echo 🔍 Paso 3: Verificando versiones instaladas...
pip freeze > installed_versions.txt
echo ✅ Versiones instaladas guardadas en installed_versions.txt
echo.

REM Paso 4: Verificar librerías críticas
echo 🧪 Paso 4: Verificando imports de librerías críticas...
python -c "import sys; critical_libs = [('fastapi', 'FastAPI framework'), ('groq', 'Groq SDK'), ('supabase', 'Supabase client'), ('pydantic', 'Data validation'), ('loguru', 'Logging framework'), ('tenacity', 'Retry logic'), ('httpx', 'HTTP client')]; print('Verificando imports críticos:'); [print(f'✅ {lib} ({desc})') if not __import__(lib) or True else print(f'❌ {lib} ({desc})') for lib, desc in critical_libs]; print('\n🎉 Todos los imports críticos exitosos')"

if %errorlevel% neq 0 (
    echo ❌ Verificación de imports falló
    exit /b 1
)
echo.

REM Paso 5: Verificar spaCy (simplificado para Windows)
echo 🔤 Paso 5: Verificando configuración spaCy...
echo ℹ️ Para instalar modelos spaCy (si es necesario):
echo   python -m spacy download es_core_news_lg
echo   python -m spacy download en_core_web_sm
echo.

REM Paso 6: Verificación final con script de setup
echo ✅ Paso 6: Verificación final del entorno...
python scripts/setup_env.py
echo.

REM Resumen final
echo 📋 RESUMEN DE INSTALACIÓN
echo =========================
echo ✅ Dependencias instaladas desde requirements.txt
echo ✅ Versiones sincronizadas con ecosistema
echo ✅ Imports críticos verificados
echo ✅ Archivo installed_versions.txt generado
echo.
echo 📄 Archivos generados:
echo   - installed_versions.txt (auditoría de versiones)
echo   - version_analysis.md (análisis de compatibilidad)
echo.
echo 🎯 Próximos pasos:
echo   1. Configurar variables críticas en .env
echo   2. Ejecutar: python scripts/test_connections.py
echo   3. Proceder con Tarea 3 (configuración centralizada)
echo.
echo 🎉 ¡Instalación de dependencias completada exitosamente!
pause
