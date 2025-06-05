#!/usr/bin/env python3
"""
Health Check independiente para Module Pipeline
==============================================

Script que puede ejecutarse independientemente para verificar
el estado básico del sistema sin iniciar el servidor completo.

Uso:
    python scripts/health_check.py
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Añadir src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv no disponible")


def check_environment():
    """Verificar configuración del entorno."""
    print("🔧 Verificando entorno...")
    
    critical_vars = {
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
        'SUPABASE_URL': os.getenv('SUPABASE_URL'),
        'SUPABASE_KEY': os.getenv('SUPABASE_KEY')
    }
    
    all_configured = True
    
    for var_name, var_value in critical_vars.items():
        if not var_value or var_value.startswith('your_') or 'your_key_here' in var_value:
            print(f"❌ {var_name} no configurada")
            all_configured = False
        else:
            # Mostrar solo los primeros y últimos caracteres por seguridad
            masked_value = var_value[:8] + "..." + var_value[-4:] if len(var_value) > 12 else "***"
            print(f"✅ {var_name} = {masked_value}")
    
    return all_configured


def check_file_structure():
    """Verificar estructura de archivos críticos."""
    print("\n📁 Verificando archivos críticos...")
    
    critical_files = [
        'requirements.txt',
        '.env',
        'prompts/Prompt_1_filtrado.md',
        'prompts/Prompt_2_elementos_basicos.md',
        'prompts/Prompt_3_citas_datos.md',
        'prompts/Prompt_4_relaciones.md'
    ]
    
    all_present = True
    
    for file_path in critical_files:
        full_path = Path(file_path)
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"✅ {file_path} ({size} bytes)")
        else:
            print(f"❌ {file_path} faltante")
            all_present = False
    
    return all_present


def check_python_imports():
    """Verificar que las dependencias críticas se pueden importar."""
    print("\n📦 Verificando imports críticos...")
    
    critical_imports = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('pydantic', 'Pydantic'),
        ('loguru', 'Loguru'),
        ('groq', 'Groq SDK'),
        ('supabase', 'Supabase SDK')
    ]
    
    all_available = True
    
    for module_name, display_name in critical_imports:
        try:
            __import__(module_name.replace('-', '_'))
            print(f"✅ {display_name}")
        except ImportError as e:
            print(f"❌ {display_name} - {e}")
            all_available = False
    
    return all_available


def check_directories():
    """Verificar que los directorios necesarios existen y son escribibles."""
    print("\n📂 Verificando directorios...")
    
    required_dirs = [
        ('logs', True),  # (path, writable)
        ('prompts', False),
        ('src', False),
        ('src/models', False),
        ('src/phases', False),
        ('src/services', False),
        ('src/utils', False),
        ('src/api', False)
    ]
    
    all_ok = True
    
    for dir_path, needs_write in required_dirs:
        full_path = Path(dir_path)
        
        if not full_path.exists():
            print(f"❌ {dir_path}/ no existe")
            all_ok = False
            continue
        
        if not full_path.is_dir():
            print(f"❌ {dir_path} no es un directorio")
            all_ok = False
            continue
        
        # Verificar permisos de escritura si es necesario
        if needs_write:
            try:
                test_file = full_path / f'.test_write_{int(time.time())}'
                test_file.touch()
                test_file.unlink()
                print(f"✅ {dir_path}/ (escribible)")
            except Exception as e:
                print(f"⚠️  {dir_path}/ (no escribible: {e})")
                # No marcamos como fallo crítico, solo advertencia
        else:
            print(f"✅ {dir_path}/")
    
    return all_ok


def system_info():
    """Mostrar información del sistema."""
    print("\n💻 Información del sistema:")
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Plataforma: {sys.platform}")
    print(f"   Directorio actual: {Path.cwd()}")
    print(f"   Timestamp: {datetime.now().isoformat()}")
    
    # Información de memoria si está disponible
    try:
        import psutil
        memory = psutil.virtual_memory()
        print(f"   Memoria total: {memory.total // (1024**3)} GB")
        print(f"   Memoria disponible: {memory.available // (1024**3)} GB")
    except ImportError:
        print("   Memoria: no disponible (psutil no instalado)")


def main():
    """Función principal del health check."""
    print("🩺 Health Check - Module Pipeline")
    print("=" * 40)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 40)
    
    checks = [
        ("Configuración de entorno", check_environment),
        ("Estructura de archivos", check_file_structure),
        ("Dependencias Python", check_python_imports),
        ("Directorios", check_directories)
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error en {name}: {e}")
            results.append((name, False))
    
    # Información del sistema
    system_info()
    
    # Resumen final
    print("\n" + "=" * 40)
    print("📋 RESUMEN DEL HEALTH CHECK")
    print("=" * 40)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ OK" if result else "❌ FALLO"
        print(f"{name:.<25} {status}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} verificaciones exitosas")
    
    if passed == total:
        print("\n🎉 Sistema en buen estado!")
        print("✅ Module Pipeline listo para ejecutar")
        
        # Sugerir próximos pasos
        print("\n📝 Próximos pasos sugeridos:")
        print("1. Verificar conectividad: python scripts/test_connections.py")
        print("2. Iniciar servidor: python main.py")
        print("3. Probar health endpoint: curl http://localhost:8000/health")
        
        return 0
    else:
        print("\n⚠️  Sistema con problemas detectados")
        print("🔧 Revisar elementos marcados como FALLO")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
