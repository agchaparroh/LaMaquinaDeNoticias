@echo off
REM run-tests.bat - Script para ejecutar los tests en Windows

echo =========================================
echo 🧪 Tests para nginx_reverse_proxy
echo =========================================

REM Verificar que estamos en el directorio correcto
if not exist "config\nginx.conf" (
    echo ❌ Error: No se encontro nginx.conf. Asegurate de ejecutar desde el directorio nginx_reverse_proxy
    exit /b 1
)

REM Verificar Docker
echo.
echo 📋 Verificando requisitos...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker no esta instalado
    exit /b 1
)
echo ✅ Docker encontrado

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no esta instalado
    exit /b 1
)
echo ✅ Python encontrado

REM Crear red si no existe
echo.
echo 🔗 Verificando red Docker...
docker network ls | findstr lamacquina_network >nul 2>&1
if errorlevel 1 (
    echo Creando red lamacquina_network...
    docker network create lamacquina_network
)
echo ✅ Red lamacquina_network disponible

REM Instalar dependencias
echo.
echo 📦 Instalando dependencias de Python...
if exist "requirements-test.txt" (
    pip install -q -r requirements-test.txt
    echo ✅ Dependencias instaladas
) else (
    echo ❌ No se encontro requirements-test.txt
    exit /b 1
)

REM Limpiar containers anteriores
echo.
echo 🧹 Limpiando containers de tests anteriores...
docker rm -f nginx_reverse_proxy_test mock_dashboard_backend mock_dashboard_frontend >nul 2>&1

REM Ejecutar tests
echo.
echo 🚀 Ejecutando tests...

REM Tests unitarios
echo.
echo 📝 Tests Unitarios...
pytest tests\unit\ --tb=short
if errorlevel 1 (
    echo ❌ Tests unitarios fallaron
    exit /b 1
)
echo ✅ Tests unitarios completados

REM Tests de integración
echo.
echo 🔗 Tests de Integracion...
pytest tests\integration\ --tb=short
if errorlevel 1 (
    echo ❌ Tests de integracion fallaron
    exit /b 1
)
echo ✅ Tests de integracion completados

REM Limpiar
echo.
echo 🧹 Limpiando recursos de test...
docker rm -f nginx_reverse_proxy_test mock_dashboard_backend mock_dashboard_frontend >nul 2>&1

REM Resumen
echo.
echo =========================================
echo ✅ Todos los tests pasaron exitosamente!
echo =========================================
