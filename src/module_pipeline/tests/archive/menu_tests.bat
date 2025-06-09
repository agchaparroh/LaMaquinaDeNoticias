@echo off
cls
echo ========================================
echo     TESTS DEL PIPELINE DE PROCESAMIENTO
echo ========================================
echo.
echo Selecciona que test deseas ejecutar:
echo.
echo 1. Test completo del pipeline (4 fases con datos de ejemplo)
echo 2. Tests unitarios de cada fase individual
echo 3. Tests de integracion y manejo de errores
echo 4. Ejecutar TODOS los tests
echo 5. Salir
echo.
set /p opcion="Ingresa tu opcion (1-5): "

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

if "%opcion%"=="1" (
    echo.
    echo ===== TEST COMPLETO DEL PIPELINE =====
    echo.
    python tests\test_pipeline_completo.py
) else if "%opcion%"=="2" (
    echo.
    echo ===== TESTS UNITARIOS =====
    echo.
    python tests\test_fases_individuales.py
) else if "%opcion%"=="3" (
    echo.
    echo ===== TESTS DE INTEGRACION =====
    echo.
    python tests\test_integracion_errores.py
) else if "%opcion%"=="4" (
    echo.
    echo ===== EJECUTANDO TODOS LOS TESTS =====
    echo.
    echo [1/3] Test completo del pipeline...
    python tests\test_pipeline_completo.py
    echo.
    echo [2/3] Tests unitarios...
    python tests\test_fases_individuales.py
    echo.
    echo [3/3] Tests de integracion...
    python tests\test_integracion_errores.py
) else if "%opcion%"=="5" (
    echo.
    echo Saliendo...
    exit /b
) else (
    echo.
    echo Opcion invalida. Por favor selecciona 1-5.
)

echo.
pause
