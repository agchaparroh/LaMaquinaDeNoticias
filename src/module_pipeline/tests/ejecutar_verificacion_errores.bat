@echo off
echo ============================================================
echo EJECUTANDO VERIFICACION RAPIDA DEL SISTEMA DE MANEJO DE ERRORES
echo ============================================================

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

echo.
echo Ejecutando test de verificacion...
python tests\test_quick_verification.py

echo.
echo ============================================================
echo VERIFICACION COMPLETADA
echo ============================================================
echo.
echo Para ejecutar todos los tests unitarios:
echo python -m pytest tests\unit\test_error_handling.py -v
echo.
pause
