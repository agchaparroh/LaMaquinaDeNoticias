@echo off
echo ====================================
echo Test del FragmentProcessor
echo ====================================
echo.

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

echo Ejecutando tests del FragmentProcessor...
python tests\test_fragment_processor.py

echo.
pause
