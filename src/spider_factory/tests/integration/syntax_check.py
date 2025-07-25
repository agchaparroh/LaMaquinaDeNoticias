"""
Verificación de sintaxis para todos los archivos Python del proyecto
No requiere dependencias externas, solo verifica que el código sea válido
"""

import ast
import json
import os
import sys
from datetime import datetime
from pathlib import Path  # noqa: F401


def check_python_syntax(file_path):
    """
    Verifica la sintaxis de un archivo Python
    Returns: (bool, str) - (es_valido, mensaje_error)
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Intentar parsear el archivo
        ast.parse(content)
        return True, "OK"

    except SyntaxError as e:
        return False, f"SyntaxError en línea {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def check_json_syntax(file_path):
    """
    Verifica la sintaxis de archivos JSON (como .j2 que pueden tener JSON)
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()  # noqa: F841

        # Los archivos .j2 son templates, no JSON puro
        # Solo verificar que se puedan leer
        return True, "OK (Template)"

    except Exception as e:
        return False, f"Error leyendo archivo: {str(e)}"


def find_python_files(root_dir):
    """Encuentra todos los archivos Python en el directorio"""
    python_files = []

    for root, dirs, files in os.walk(root_dir):
        # Excluir directorios
        dirs[:] = [
            d
            for d in dirs
            if d
            not in [
                "__pycache__",
                ".venv",
                "venv",
                "env",
                "node_modules",
                ".git",
                "htmlcov",
                ".pytest_cache",
            ]
        ]

        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    return python_files


def check_all_files(root_dir):
    """Verifica la sintaxis de todos los archivos del proyecto"""
    results = {
        "valid": [],
        "invalid": [],
        "summary": {
            "total_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "timestamp": datetime.now().isoformat(),
        },
    }

    # Encontrar archivos Python
    python_files = find_python_files(root_dir)
    results["summary"]["total_files"] = len(python_files)

    print(f"🔍 Encontrados {len(python_files)} archivos Python")
    print("=" * 60)

    # Verificar cada archivo
    for file_path in sorted(python_files):
        relative_path = os.path.relpath(file_path, root_dir)
        is_valid, message = check_python_syntax(file_path)

        if is_valid:
            results["valid"].append(relative_path)
            print(f"✅ {relative_path}")
        else:
            results["invalid"].append({"file": relative_path, "error": message})
            print(f"❌ {relative_path}")
            print(f"   → {message}")

    results["summary"]["valid_files"] = len(results["valid"])
    results["summary"]["invalid_files"] = len(results["invalid"])

    return results


def check_imports(root_dir):
    """Verifica que los imports sean correctos"""
    print("\n🔍 Verificando imports...")
    issues = []

    python_files = find_python_files(root_dir)

    for file_path in python_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Verificar imports problemáticos conocidos
                        if alias.name in ["httpx", "redis", "pydantic", "tenacity"]:
                            relative_path = os.path.relpath(file_path, root_dir)
                            issues.append(f"{relative_path}: Requiere {alias.name}")

                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith(
                        ("httpx", "redis", "pydantic", "tenacity")
                    ):
                        relative_path = os.path.relpath(file_path, root_dir)
                        issues.append(f"{relative_path}: Requiere {node.module}")

        except:  # noqa: E722
            pass

    if issues:
        print("\n⚠️ Dependencias externas detectadas:")
        for issue in sorted(set(issues)):
            print(f"  - {issue}")
    else:
        print("✅ No se detectaron problemas de imports")

    return issues


def save_results(results, output_file):
    """Guarda los resultados en un archivo JSON"""
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Resultados guardados en: {output_file}")
    except Exception as e:
        print(f"\n❌ Error guardando resultados: {e}")


def main():
    """Función principal"""
    print("🐍 SPIDER FACTORY 2.0 - VERIFICACIÓN DE SINTAXIS")
    print("=" * 60)

    # Directorio raíz del proyecto
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

    print(f"📁 Directorio: {root_dir}\n")

    # Verificar sintaxis
    results = check_all_files(root_dir)

    # Verificar imports
    import_issues = check_imports(root_dir)
    results["import_issues"] = import_issues

    # Mostrar resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN:")
    print("=" * 60)
    print(f"Total archivos:    {results['summary']['total_files']}")
    print(f"Archivos válidos:  {results['summary']['valid_files']} ✅")
    print(f"Archivos con errores: {results['summary']['invalid_files']} ❌")

    if results["invalid"]:
        print("\n❌ ARCHIVOS CON ERRORES:")
        for item in results["invalid"]:
            print(f"\n{item['file']}:")
            print(f"  {item['error']}")

    # Guardar resultados
    output_file = os.path.join(
        root_dir,
        f"syntax_check_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )
    save_results(results, output_file)

    # Código de salida
    if results["invalid"]:
        print("\n❌ Se encontraron errores de sintaxis")
        return 1
    else:
        print("\n✅ Todos los archivos tienen sintaxis válida")
        return 0


if __name__ == "__main__":
    sys.exit(main())
