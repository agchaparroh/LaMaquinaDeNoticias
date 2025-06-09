@echo off
echo ====================================
echo Ejecutando TODOS los Tests CORREGIDOS
echo ====================================
echo.

cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

echo [1/3] Ejecutando Test Pipeline Completo...
echo --------------------------------------------------------
python tests\test_pipeline_completo_FIXED.py
echo.

echo [2/3] Ejecutando Tests Unitarios...
echo --------------------------------------------------------
python tests\test_fases_individuales_FIXED.py
echo.

echo [3/3] Ejecutando Tests de Integracion...
echo --------------------------------------------------------
python tests\test_integracion_errores_FIXED.py
echo.

echo ====================================
echo TODOS LOS TESTS COMPLETADOS
echo ====================================
pause
