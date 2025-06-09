@echo off
echo ========================================
echo Verificador de Archivos de Log
echo ========================================
echo.

cd /d %~dp0..

python -m tests.verificar_logs

echo.
echo Verificacion completada. Presiona cualquier tecla para salir...
pause > nul
