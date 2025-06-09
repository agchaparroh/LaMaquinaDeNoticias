@echo off
echo ============================================================
echo EJECUTANDO DIAGNOSTICO DEL SISTEMA DE MANEJO DE ERRORES
echo ============================================================

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

echo.
python tests\test_diagnostico.py

echo.
pause
