#!/usr/bin/env python3
"""
Script de demostración de ejecución de tests para module_connector
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n{'='*60}")
    print(f"📋 {description}")
    print(f"💻 Comando: {cmd}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("✅ SALIDA:")
        print(result.stdout)
    
    if result.stderr:
        print("⚠️  ERRORES:")
        print(result.stderr)
    
    return result.returncode == 0

def main():
    """Ejecuta una demostración de los tests"""
    print("🚀 DEMOSTRACIÓN DE TESTS - MODULE CONNECTOR")
    print("="*60)
    
    # Cambiar al directorio del módulo
    module_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(module_dir)
    
    # Lista de comandos a ejecutar
    commands = [
        # 1. Verificar que pytest está instalado
        ("python -m pytest --version", "Verificando instalación de pytest"),
        
        # 2. Listar tests disponibles
        ("python -m pytest tests/ --collect-only -q", "Listando todos los tests disponibles"),
        
        # 3. Ejecutar tests unitarios
        ("python -m pytest tests/unit/test_models.py -v", "Ejecutando tests del modelo ArticuloInItem"),
        
        # 4. Ejecutar un test específico
        ("python -m pytest tests/unit/test_models.py::TestArticuloInItem::test_valid_article_minimal_data -v", 
         "Ejecutando un test específico"),
        
        # 5. Ejecutar tests con cobertura
        ("python -m pytest tests/unit/ --cov=src --cov-report=term-missing", 
         "Ejecutando tests unitarios con análisis de cobertura"),
        
        # 6. Ejecutar tests de integración (solo algunos rápidos)
        ("python -m pytest tests/integration/test_file_processing.py::TestProcessFile::test_process_valid_single_article -v", 
         "Ejecutando test de procesamiento de archivo"),
    ]
    
    # Ejecutar cada comando
    success_count = 0
    for cmd, desc in commands:
        if run_command(cmd, desc):
            success_count += 1
        else:
            print(f"❌ Falló: {desc}")
    
    # Resumen final
    print(f"\n{'='*60}")
    print(f"📊 RESUMEN DE EJECUCIÓN")
    print(f"{'='*60}")
    print(f"✅ Comandos exitosos: {success_count}/{len(commands)}")
    print(f"❌ Comandos fallidos: {len(commands) - success_count}/{len(commands)}")
    
    if success_count == len(commands):
        print("\n🎉 ¡Todos los tests se ejecutaron correctamente!")
    else:
        print("\n⚠️  Algunos tests fallaron. Revisa los mensajes de error arriba.")
    
    # Información adicional
    print(f"\n📚 INFORMACIÓN ADICIONAL:")
    print(f"- Para ejecutar todos los tests: python -m pytest tests/ -v")
    print(f"- Para ver cobertura completa: python -m pytest tests/ --cov=src --cov-report=html")
    print(f"- Para tests en paralelo: python -m pytest tests/ -n auto")
    print(f"- Documentación completa en: tests/README.md")

if __name__ == "__main__":
    main()
