@echo off
echo Ejecutando test especifico que fallaba...
cd /d "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"
python -m pytest tests\unit\test_error_handling.py::TestRetryDecorators::test_retry_groq_api_decorator -v
pause
