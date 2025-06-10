@echo off
cls
echo ==========================================
echo     TESTS DEL PIPELINE - VERSION CORREGIDA
echo ==========================================
echo.
echo Selecciona que test deseas ejecutar:
echo.
echo 1. Test completo del pipeline (VERSION CORREGIDA)
echo 2. Tests unitarios de cada fase (VERSION CORREGIDA)  
echo 3. Tests de integracion y errores (VERSION CORREGIDA)
echo 4. Tests ORIGINALES (posiblemente con errores)
echo 5. Ejecutar TODOS los tests corregidos
echo 6. Comparar versiones original vs corregida
echo 7. Salir
echo.
set /p opcion="Ingresa tu opcion (1-7): "

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

if "%opcion%"=="1" (
    echo.
    echo ===== TEST COMPLETO DEL PIPELINE [CORREGIDO] =====
    echo.
    python tests\test_pipeline_completo_FIXED.py
) else if "%opcion%"=="2" (
    echo.
    echo ===== TESTS UNITARIOS [CORREGIDO] =====
    echo.
    python tests\test_fases_individuales_FIXED.py
) else if "%opcion%"=="3" (
    echo.
    echo ===== TESTS DE INTEGRACION [CORREGIDO] =====
    echo.
    python tests\test_integracion_errores_FIXED.py
) else if "%opcion%"=="4" (
    echo.
    echo ===== TESTS ORIGINALES [PUEDEN FALLAR] =====
    echo.
    echo [1/3] Test completo original...
    python tests\test_pipeline_completo.py
    echo.
    echo [2/3] Tests unitarios originales...
    python tests\test_fases_individuales.py
    echo.
    echo [3/3] Tests integracion originales...
    python tests\test_integracion_errores.py
) else if "%opcion%"=="5" (
    echo.
    echo ===== EJECUTANDO TODOS LOS TESTS CORREGIDOS =====
    echo.
    echo [1/3] Test completo del pipeline...
    echo --------------------------------------------------------
    python tests\test_pipeline_completo_FIXED.py
    echo.
    echo [2/3] Tests unitarios...
    echo --------------------------------------------------------
    python tests\test_fases_individuales_FIXED.py
    echo.
    echo [3/3] Tests de integracion...
    echo --------------------------------------------------------
    python tests\test_integracion_errores_FIXED.py
) else if "%opcion%"=="6" (
    echo.
    echo ===== COMPARACION: ORIGINAL VS CORREGIDO =====
    echo.
    echo Ejecutando version ORIGINAL del test completo...
    echo --------------------------------------------------------
    python tests\test_pipeline_completo.py
    echo.
    echo Ejecutando version CORREGIDA del test completo...
    echo --------------------------------------------------------
    python tests\test_pipeline_completo_FIXED.py
) else if "%opcion%"=="7" (
    echo.
    echo Saliendo...
    exit /b
) else (
    echo.
    echo Opcion invalida. Por favor selecciona 1-7.
)

echo.
echo ==========================================
echo Presiona cualquier tecla para continuar...
pause > nul
