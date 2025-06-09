@echo off
echo ====================================
echo Test de Verificacion Basica
echo ====================================
echo.

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

echo Ejecutando verificacion basica del sistema...
python tests\test_verificacion_basica.py

echo.
pause
