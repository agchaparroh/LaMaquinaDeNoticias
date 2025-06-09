@echo off
echo ====================================
echo Test Simple - VERSION 3 (sin imports relativos)
echo ====================================
echo.

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

echo Ejecutando test simple v3 (evita imports relativos)...
python tests\test_simple_verificacion_v3.py

echo.
pause
