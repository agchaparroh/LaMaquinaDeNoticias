@echo off
cls
echo =========================================
echo      MENU PRINCIPAL - TESTS DEL PIPELINE
echo =========================================
echo.
echo Selecciona el test que deseas ejecutar:
echo.
echo 1. Test Principal (Pipeline Independiente) - RECOMENDADO
echo 2. Test de Verificacion Basica - Diagnostico
echo 3. Test del FragmentProcessor - IDs Secuenciales
echo 4. Ejecutar TODOS los tests
echo 5. Ver documentacion
echo 6. Salir
echo.
set /p opcion="Selecciona una opcion (1-6): "

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

if "%opcion%"=="1" (
    echo.
    echo ===== TEST PRINCIPAL DEL PIPELINE =====
    echo.
    python tests\test_pipeline_independiente.py
    
) else if "%opcion%"=="2" (
    echo.
    echo ===== VERIFICACION BASICA =====
    echo.
    python tests\test_verificacion_basica.py
    
) else if "%opcion%"=="3" (
    echo.
    echo ===== TEST FRAGMENTPROCESSOR =====
    echo.
    python tests\test_fragment_processor.py
    
) else if "%opcion%"=="4" (
    echo.
    echo ===== EJECUTANDO TODOS LOS TESTS =====
    echo.
    echo [1/3] Verificacion basica...
    echo --------------------------------------------------------
    python tests\test_verificacion_basica.py
    echo.
    echo [2/3] Test del FragmentProcessor...
    echo --------------------------------------------------------
    python tests\test_fragment_processor.py
    echo.
    echo [3/3] Test principal del pipeline...
    echo --------------------------------------------------------
    python tests\test_pipeline_independiente.py
    echo.
    echo ===== TODOS LOS TESTS COMPLETADOS =====
    
) else if "%opcion%"=="5" (
    echo.
    echo ===== DOCUMENTACION =====
    echo.
    echo Abriendo README.md...
    type tests\README.md
    
) else if "%opcion%"=="6" (
    echo.
    echo Saliendo...
    exit /b
    
) else (
    echo.
    echo Opcion invalida. Selecciona 1-6.
)

echo.
echo ==========================================
echo Presiona cualquier tecla para continuar...
pause > nul
