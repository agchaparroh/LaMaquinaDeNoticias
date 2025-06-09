@echo off
echo ====================================
echo Test Pipeline INDEPENDIENTE (100% funcional)
echo ====================================
echo.

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

echo Ejecutando test del pipeline independiente...
python tests\test_pipeline_INDEPENDIENTE.py

echo.
pause
