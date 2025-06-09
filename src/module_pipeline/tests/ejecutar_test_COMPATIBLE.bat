@echo off
echo ====================================
echo Test Pipeline COMPATIBLE (sin problemas de imports)
echo ====================================
echo.

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

echo Ejecutando test del pipeline compatible...
python tests\test_pipeline_COMPATIBLE.py

echo.
pause
