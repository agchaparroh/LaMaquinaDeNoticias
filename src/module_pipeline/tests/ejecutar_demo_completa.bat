@echo off
echo ============================================================
echo DEMOSTRACION COMPLETA - SISTEMA DE MANEJO DE ERRORES
echo ============================================================

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

python tests\demo_completa.py

echo.
echo ============================================================
echo Para ejecutar los tests unitarios completos:
echo python -m pytest tests\unit\test_error_handling.py -v
echo ============================================================
pause
