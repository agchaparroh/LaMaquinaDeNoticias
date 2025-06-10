# Script PowerShell para ejecutar tests corregidos
# Versión mejorada con mejor manejo de errores

Write-Host "🚀 EJECUTOR DE TESTS - PIPELINE PROCESAMIENTO" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""

# Cambiar al directorio del proyecto
$projectDir = "C:\Users\DELL\Desktop\PruebaWindsurfAI\LaMaquinaDeNoticias\src\module_pipeline"
Set-Location $projectDir

Write-Host "📁 Directorio de trabajo: $projectDir" -ForegroundColor Cyan
Write-Host ""

# Función para ejecutar un test con manejo de errores
function Ejecutar-Test {
    param(
        [string]$NombreTest,
        [string]$ArchivoTest
    )
    
    Write-Host "🧪 Ejecutando: $NombreTest" -ForegroundColor Yellow
    Write-Host "📄 Archivo: $ArchivoTest" -ForegroundColor Gray
    Write-Host ("-" * 50) -ForegroundColor Gray
    
    try {
        $proceso = Start-Process -FilePath "python" -ArgumentList $ArchivoTest -Wait -PassThru -NoNewWindow
        
        if ($proceso.ExitCode -eq 0) {
            Write-Host "✅ $NombreTest: EXITOSO" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ $NombreTest: FALLIDO (Exit Code: $($proceso.ExitCode))" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "💥 $NombreTest: ERROR - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    finally {
        Write-Host ""
    }
}

# Menú de opciones
do {
    Write-Host "🎯 OPCIONES DISPONIBLES:" -ForegroundColor Cyan
    Write-Host "1. Test completo del pipeline (CORREGIDO)" -ForegroundColor White
    Write-Host "2. Tests unitarios (CORREGIDO)" -ForegroundColor White
    Write-Host "3. Tests de integración (CORREGIDO)" -ForegroundColor White
    Write-Host "4. Ejecutar TODOS los tests corregidos" -ForegroundColor White
    Write-Host "5. Verificar dependencias" -ForegroundColor White
    Write-Host "6. Salir" -ForegroundColor White
    Write-Host ""
    
    $opcion = Read-Host "Selecciona una opción (1-6)"
    Write-Host ""
    
    switch ($opcion) {
        "1" {
            Ejecutar-Test "Test Completo Pipeline" "tests\test_pipeline_completo_FIXED.py"
        }
        "2" {
            Ejecutar-Test "Tests Unitarios" "tests\test_fases_individuales_FIXED.py"
        }
        "3" {
            Ejecutar-Test "Tests Integración" "tests\test_integracion_errores_FIXED.py"
        }
        "4" {
            Write-Host "🔄 EJECUTANDO SUITE COMPLETA DE TESTS..." -ForegroundColor Magenta
            Write-Host "========================================" -ForegroundColor Magenta
            Write-Host ""
            
            $resultados = @()
            
            $resultados += Ejecutar-Test "Test Completo Pipeline" "tests\test_pipeline_completo_FIXED.py"
            $resultados += Ejecutar-Test "Tests Unitarios" "tests\test_fases_individuales_FIXED.py"
            $resultados += Ejecutar-Test "Tests Integración" "tests\test_integracion_errores_FIXED.py"
            
            # Resumen final
            Write-Host "📊 RESUMEN FINAL" -ForegroundColor Magenta
            Write-Host "================" -ForegroundColor Magenta
            
            $exitosos = ($resultados | Where-Object { $_ -eq $true }).Count
            $total = $resultados.Count
            $porcentaje = if ($total -gt 0) { ($exitosos / $total) * 100 } else { 0 }
            
            Write-Host "✅ Tests exitosos: $exitosos/$total" -ForegroundColor Green
            Write-Host "📈 Tasa de éxito: $([math]::Round($porcentaje, 1))%" -ForegroundColor Cyan
            
            if ($exitosos -eq $total) {
                Write-Host "🎉 ¡TODOS LOS TESTS PASARON!" -ForegroundColor Green
            } else {
                Write-Host "⚠️ Algunos tests fallaron. Revisa los errores." -ForegroundColor Yellow
            }
            Write-Host ""
        }
        "5" {
            Write-Host "🔍 VERIFICANDO DEPENDENCIAS..." -ForegroundColor Yellow
            Write-Host ""
            
            # Verificar Python
            try {
                $pythonVersion = python --version 2>&1
                Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
            }
            catch {
                Write-Host "❌ Python no encontrado" -ForegroundColor Red
            }
            
            # Verificar dependencias del requirements.txt
            $dependencias = @("fastapi", "loguru", "pydantic", "groq", "supabase")
            
            foreach ($dep in $dependencias) {
                try {
                    $resultado = python -c "import $dep; print('$dep: OK')" 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "✅ $dep: Instalado" -ForegroundColor Green
                    } else {
                        Write-Host "❌ $dep: No instalado" -ForegroundColor Red
                    }
                }
                catch {
                    Write-Host "❌ $dep: Error al verificar" -ForegroundColor Red
                }
            }
            Write-Host ""
        }
        "6" {
            Write-Host "👋 Saliendo..." -ForegroundColor Cyan
            break
        }
        default {
            Write-Host "❌ Opción inválida. Selecciona 1-6." -ForegroundColor Red
            Write-Host ""
        }
    }
} while ($opcion -ne "6")

Write-Host "🏁 Fin del script." -ForegroundColor Green
