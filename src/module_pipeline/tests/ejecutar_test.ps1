Write-Host ""
Write-Host "===================================="
Write-Host "Ejecutando Test del Pipeline Completo"
Write-Host "===================================="
Write-Host ""

Set-Location "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"

python tests\test_pipeline_completo.py

Write-Host ""
Write-Host "Presiona cualquier tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
