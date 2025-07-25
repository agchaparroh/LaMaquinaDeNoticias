#!/usr/bin/env python3
"""
Configuración centralizada integrada con setup_env.py
===================================================

Este script verifica que:
1. Python y pip están disponibles
2. Las dependencias se pueden instalar
3. Los directorios necesarios existen
4. Las variables de entorno básicas están configuradas
5. LA CONFIGURACIÓN CENTRALIZADA FUNCIONA CORRECTAMENTE
"""

import os
import subprocess  # noqa: F401
import sys
from pathlib import Path


def check_python_version():
    """Verificar que la versión de Python es compatible."""
    print("🐍 Verificando versión de Python...")

    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(
            f"❌ Error: Se requiere Python 3.8+, encontrado {version.major}.{version.minor}"
        )
        return False

    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True


def check_virtual_environment():
    """Verificar si estamos en un entorno virtual."""
    print("\n🔧 Verificando entorno virtual...")

    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )

    if in_venv:
        print("✅ Entorno virtual activo")
        return True
    else:
        print("⚠️  No se detectó entorno virtual activo")
        print("   Recomendación: crear y activar un entorno virtual")
        return False


def check_dependencies():
    """Verificar si las dependencias críticas están instaladas."""
    print("\n📦 Verificando dependencias críticas...")

    critical_deps = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "python-dotenv",
        "loguru",
        "groq",
        "supabase",
    ]

    missing_deps = []

    for dep in critical_deps:
        try:
            __import__(dep.replace("-", "_"))
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep}")
            missing_deps.append(dep)

    if missing_deps:
        print(f"\n⚠️  Dependencias faltantes: {', '.join(missing_deps)}")
        print("   Ejecutar: pip install -r requirements.txt")
        return False

    return True


def check_directory_structure():
    """Verificar que la estructura de directorios existe."""
    print("\n📁 Verificando estructura de directorios...")

    required_dirs = [
        "src",
        "src/models",
        "src/phases",
        "src/services",
        "src/utils",
        "src/api",
        "prompts",
        "logs",
        "tests",
        "models",
    ]

    missing_dirs = []

    for dir_path in required_dirs:
        full_path = Path(dir_path)
        if full_path.exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/")
            missing_dirs.append(dir_path)

    if missing_dirs:
        print(f"\n⚠️  Directorios faltantes: {', '.join(missing_dirs)}")
        return False

    return True


def check_env_file():
    """Verificar que existe el archivo .env."""
    print("\n🔧 Verificando archivo de configuración...")

    env_file = Path(".env")
    if env_file.exists():
        print("✅ Archivo .env encontrado")

        # Verificar variables críticas
        try:
            from dotenv import load_dotenv

            load_dotenv()

            critical_vars = ["GROQ_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]
            missing_vars = []

            for var in critical_vars:
                value = os.getenv(var)
                if (
                    value
                    and value != f"your_{var.lower()}_here"
                    and not value.startswith("your_")
                ):
                    print(f"✅ {var} configurado")
                else:
                    print(f"⚠️  {var} no configurado")
                    missing_vars.append(var)

            if missing_vars:
                print(
                    f"\n⚠️  Variables de entorno pendientes: {', '.join(missing_vars)}"
                )
                print("   Editar .env con las claves reales")
                return False

        except ImportError:
            print("⚠️  python-dotenv no instalado, no se pueden verificar variables")
            return False

        return True
    else:
        print("❌ Archivo .env no encontrado")
        print("   Ejecutar: cp .env.example .env")
        return False


def check_prompts():
    """Verificar que los prompts están disponibles."""
    print("\n📝 Verificando prompts...")

    prompt_files = [
        "prompts/Prompt_1_filtrado.md",
        "prompts/Prompt_2_elementos_basicos.md",
        "prompts/Prompt_3_citas_datos.md",
        "prompts/Prompt_4_relaciones.md",
    ]

    missing_prompts = []

    for prompt_file in prompt_files:
        full_path = Path(prompt_file)
        if full_path.exists():
            print(f"✅ {prompt_file}")
        else:
            print(f"❌ {prompt_file}")
            missing_prompts.append(prompt_file)

    if missing_prompts:
        print(f"\n⚠️  Prompts faltantes: {', '.join(missing_prompts)}")
        return False

    return True


def check_centralized_config():
    """Verificar que la configuración centralizada funciona."""
    print("\n⚙️  Verificando configuración centralizada...")

    try:
        # Añadir src al path
        sys.path.insert(0, str(Path.cwd() / "src"))

        # Intentar importar la configuración
        from utils.config import (
            GROQ_API_KEY,  # noqa: F401
            SUPABASE_KEY,
            SUPABASE_URL,
            get_groq_config,
            validate_configuration,
        )

        print("✅ Módulo de configuración importado correctamente")

        # Validar configuración
        is_valid = validate_configuration()
        if is_valid:
            print("✅ Configuración centralizada válida")
        else:
            print("❌ Configuración centralizada inválida")
            return False

        # Verificar funciones de configuración
        groq_config = get_groq_config()
        if groq_config and groq_config.get("api_key"):
            print("✅ Funciones de configuración funcionando")
        else:
            print("❌ Funciones de configuración fallando")
            return False

        return True

    except ImportError as e:
        print(f"❌ Error importando configuración: {e}")
        return False
    except Exception as e:
        print(f"❌ Error en configuración centralizada: {e}")
        return False


def main():
    """Función principal del script."""
    print("🚀 Configuración inicial - Module Pipeline")
    print("=" * 50)

    checks = [
        ("Versión de Python", check_python_version),
        ("Entorno Virtual", check_virtual_environment),
        ("Dependencias", check_dependencies),
        ("Estructura de Directorios", check_directory_structure),
        ("Archivo de Configuración", check_env_file),
        ("Prompts", check_prompts),
        ("Configuración Centralizada", check_centralized_config),  # ← NUEVO
    ]

    results = []

    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error en {name}: {e}")
            results.append((name, False))

    # Resumen final
    print("\n" + "=" * 50)
    print("📋 RESUMEN DE VERIFICACIÓN")
    print("=" * 50)

    passed = 0
    total = len(results)

    for name, result in results:
        status = "✅ CORRECTO" if result else "❌ PENDIENTE"
        print(f"{name:.<30} {status}")
        if result:
            passed += 1

    print(f"\nResultado: {passed}/{total} verificaciones pasaron")

    if passed == total:
        print("\n🎉 ¡Configuración completa! El module_pipeline está listo.")
        print("\n📝 Próximos pasos:")
        print("1. Ejecutar: python test_config.py (prueba configuración)")
        print("2. Proceder con Tarea 4 (modelos Pydantic)")
        print("3. Implementar servicios y fases del pipeline")
    else:
        print("\n⚠️  Configuración incompleta. Revisar elementos pendientes.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
