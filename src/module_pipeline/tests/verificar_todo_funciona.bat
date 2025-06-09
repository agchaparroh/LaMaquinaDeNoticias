@echo off
echo ============================================================
echo VERIFICANDO QUE EL SISTEMA DE MANEJO DE ERRORES FUNCIONA
echo ============================================================
echo.
echo Ejecutando los 3 tests de verificacion...
echo.

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

echo [1/3] Test de diagnostico...
echo ----------------------------------------
python tests\test_diagnostico.py
echo.

echo [2/3] Test de verificacion rapida V2...
echo ----------------------------------------
python tests\test_quick_verification_v2.py
echo.

echo [3/3] Test unitarios con pytest (solo los primeros)...
echo ----------------------------------------
python -m pytest tests\unit\test_error_handling.py::TestCustomExceptions -v -x
echo.

echo ============================================================
echo VERIFICACION COMPLETA
echo ============================================================
pause
