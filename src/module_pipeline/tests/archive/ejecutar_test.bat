@echo off
echo.
echo ====================================
echo Ejecutando Test del Pipeline Completo
echo ====================================
echo.

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

python tests\test_pipeline_completo.py

echo.
pause
