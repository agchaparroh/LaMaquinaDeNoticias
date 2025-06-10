@echo off
echo ========================================
echo Demo del Sistema de Logging del Pipeline
echo ========================================
echo.

cd /d %~dp0..

python -m tests.demo_logging_system

echo.
echo Demo completada. Presiona cualquier tecla para salir...
pause > nul
