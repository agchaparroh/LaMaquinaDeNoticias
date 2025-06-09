@echo off
echo ====================================
echo Test Pipeline SIN IMPORTS RELATIVOS
echo ====================================
echo.

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

echo Ejecutando test del pipeline (evita imports relativos)...
python tests\test_pipeline_SIN_IMPORTS_RELATIVOS.py

echo.
pause
