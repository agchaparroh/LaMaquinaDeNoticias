@echo off
echo ============================================================
echo EJECUTANDO VERIFICACION RAPIDA V2 - SISTEMA DE ERRORES
echo ============================================================

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

echo.
echo Ejecutando test de verificacion corregido...
python tests\test_quick_verification_v2.py

echo.
echo ============================================================
echo VERIFICACION COMPLETADA
echo ============================================================
echo.
pause
