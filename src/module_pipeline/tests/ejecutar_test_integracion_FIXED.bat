@echo off
echo ====================================
echo Ejecutando Tests de Integracion CORREGIDOS
echo ====================================
echo.

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

python tests\test_integracion_errores_FIXED.py

echo.
pause
