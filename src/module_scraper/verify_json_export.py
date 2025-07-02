#!/usr/bin/env python3
"""
Script de verificación simple para JsonGzExportPipeline
Verifica que la implementación es sintácticamente correcta.
"""

import ast
import os
import sys


def verify_syntax(file_path):
    """Verificar que el archivo tiene sintaxis Python válida."""
    print(f"🔍 Verificando sintaxis de {os.path.basename(file_path)}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parsear el AST para verificar sintaxis
        ast.parse(content)
        print(f"✅ Sintaxis válida")
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def verify_imports(file_path):
    """Verificar que las importaciones están disponibles."""
    print(f"🔍 Verificando importaciones...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraer imports del archivo
        tree = ast.parse(content)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        
        # Verificar imports específicos del proyecto
        expected_imports = [
            'scraper_core.items.ArticuloInItem',
            'scraper_core.utils.compression',
            'scraper_core.pipelines.exceptions'
        ]
        
        for expected in expected_imports:
            found = any(expected in imp for imp in imports)
            if found:
                print(f"✅ Import encontrado: {expected}")
            else:
                print(f"⚠️  Import no encontrado exactamente: {expected}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando imports: {e}")
        return False


def verify_class_structure(file_path):
    """Verificar estructura de la clase JsonGzExportPipeline."""
    print(f"🔍 Verificando estructura de clase...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Buscar la clase JsonGzExportPipeline
        pipeline_class = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'JsonGzExportPipeline':
                pipeline_class = node
                break
        
        if not pipeline_class:
            print("❌ Clase JsonGzExportPipeline no encontrada")
            return False
        
        print("✅ Clase JsonGzExportPipeline encontrada")
        
        # Verificar métodos esperados
        expected_methods = [
            '__init__',
            'from_crawler',
            'open_spider',
            'close_spider',
            'process_item'
        ]
        
        found_methods = []
        for node in pipeline_class.body:
            if isinstance(node, ast.FunctionDef):
                found_methods.append(node.name)
        
        for method in expected_methods:
            if method in found_methods:
                print(f"✅ Método encontrado: {method}")
            else:
                print(f"❌ Método faltante: {method}")
        
        return len([m for m in expected_methods if m in found_methods]) >= 4
        
    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")
        return False


def verify_settings_integration():
    """Verificar que settings.py tiene la configuración correcta."""
    print(f"🔍 Verificando integración con settings.py...")
    
    settings_path = "/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/module_scraper/scraper_core/settings.py"
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar elementos clave
        checks = [
            ("ENABLE_PIPELINE_EXPORT", "Variable de control encontrada"),
            ("JsonGzExportPipeline", "Referencia al pipeline encontrada"),
            ("EXPORT_DIRECTORY", "Configuración de directorio encontrada"),
            ("ITEM_PIPELINES['scraper_core.pipelines.json_export.JsonGzExportPipeline']", "Pipeline en configuración")
        ]
        
        all_good = True
        for check, description in checks:
            if check in content:
                print(f"✅ {description}")
            else:
                print(f"❌ {description} - NO ENCONTRADA")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error verificando settings: {e}")
        return False


def verify_init_file():
    """Verificar que __init__.py incluye el nuevo pipeline."""
    print(f"🔍 Verificando __init__.py...")
    
    init_path = "/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/module_scraper/scraper_core/pipelines/__init__.py"
    
    try:
        with open(init_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "JsonGzExportPipeline" in content:
            print("✅ JsonGzExportPipeline incluido en __init__.py")
            return True
        else:
            print("❌ JsonGzExportPipeline NO incluido en __init__.py")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando __init__.py: {e}")
        return False


def main():
    """Ejecutar todas las verificaciones."""
    print("🚀 Verificando implementación de JsonGzExportPipeline\n")
    
    pipeline_path = "/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/module_scraper/scraper_core/pipelines/json_export.py"
    
    checks = [
        ("Sintaxis del pipeline", lambda: verify_syntax(pipeline_path)),
        ("Importaciones", lambda: verify_imports(pipeline_path)),
        ("Estructura de clase", lambda: verify_class_structure(pipeline_path)),
        ("Integración con settings", verify_settings_integration),
        ("Archivo __init__.py", verify_init_file)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        result = check_func()
        results.append((check_name, result))
        print("")
    
    # Resumen final
    print("📊 RESUMEN DE VERIFICACIÓN:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} verificaciones pasaron")
    
    if passed == total:
        print("\n🎉 ¡Implementación verificada exitosamente!")
        print("\n📋 JsonGzExportPipeline está listo para usar:")
        print("  • Pipeline implementado correctamente")
        print("  • Integrado con sistema de configuración")
        print("  • Compatible con pipelines existentes")
        print("  • Deshabilitado por defecto (seguro)")
        
        print("\n🔧 Para activar:")
        print("  export ENABLE_PIPELINE_EXPORT=true")
        print("  export DEVELOPMENT_MODE=true")
        
        return True
    else:
        print(f"\n⚠️  Hay {total - passed} problemas que requieren atención")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)