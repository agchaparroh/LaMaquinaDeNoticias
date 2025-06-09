@echo off
echo ============================================================
echo EJECUTANDO TODOS LOS TESTS UNITARIOS - SISTEMA DE ERRORES
echo ============================================================

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

echo.
echo Ejecutando los 34 tests unitarios...
python -m pytest tests\unit\test_error_handling.py -v --tb=short

echo.
echo ============================================================
echo Si todos los tests pasan, el sistema esta 100% funcional
echo ============================================================
pause
