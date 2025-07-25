#!/usr/bin/env python3
"""
Script de verificación post-fix para validar que las correcciones funcionan correctamente.
Ejecutar después de aplicar la migración SQL.
"""

import json
import subprocess
import sys  # noqa: F401
from datetime import datetime


def ejecutar_prueba():
    """Ejecuta una prueba completa del pipeline con un artículo de prueba."""

    print("=" * 80)
    print("VERIFICACIÓN DE CORRECCIONES DE NOMENCLATURA")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # 1. Verificar que existe el archivo de prueba
    print("\n1. Verificando archivo de prueba...")
    try:
        with open("test_article_relevante.json") as f:
            articulo = json.load(f)
            print(f"   ✓ Artículo de prueba cargado: ID {articulo.get('id', 'N/A')}")
    except FileNotFoundError:
        print("   ✗ ERROR: No se encuentra test_article_relevante.json")
        print(
            "   Ejecute primero: docker-compose run --rm module_scraper scrapy crawl infobae_america_latina -a max_articles=1"
        )
        return False

    # 2. Ejecutar el pipeline
    print("\n2. Ejecutando pipeline...")
    cmd = [
        "docker-compose",
        "run",
        "--rm",
        "module_pipeline",
        "python",
        "run_single_article.py",
        "test_article_relevante.json",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        # 3. Analizar resultados
        print("\n3. Analizando resultados...")

        # Buscar indicadores de éxito
        success_indicators = [
            "Artículo procesado exitosamente",
            "entidades_insertadas",
            "status': 'exito'",
            "hechos_insertados",
        ]

        # Buscar indicadores de error
        error_indicators = [
            "null value in column 'nombre'",
            'null value in column "nombre"',
            "violates not-null constraint",
            "nombre_entidad",
            "tipo_entidad",
            "descripcion_entidad",
        ]

        output = result.stdout + result.stderr

        # Verificar éxito
        exitos_encontrados = []
        for indicator in success_indicators:
            if indicator in output:
                exitos_encontrados.append(indicator)

        # Verificar errores
        errores_encontrados = []
        for indicator in error_indicators:
            if indicator in output:
                errores_encontrados.append(indicator)

        # 4. Mostrar resultados
        print("\n4. RESULTADOS:")
        print("-" * 40)

        if errores_encontrados:
            print("   ✗ ERRORES DETECTADOS:")
            for error in errores_encontrados:
                print(f"     - {error}")
            print("\n   LA CORRECCIÓN NO FUE EXITOSA")
            print("   Verifique que la migración SQL se aplicó correctamente")

            # Mostrar extracto del error
            if "null value in column" in output:
                lines = output.split("\n")
                for i, line in enumerate(lines):
                    if "null value in column" in line:
                        print(f"\n   Contexto del error:")  # noqa: F541
                        start = max(0, i - 3)
                        end = min(len(lines), i + 4)
                        for j in range(start, end):
                            print(f"     {lines[j]}")
                        break

        elif exitos_encontrados:
            print("   ✓ ÉXITO: Pipeline ejecutado correctamente")
            print(f"   Indicadores encontrados: {', '.join(exitos_encontrados)}")

            # Buscar contadores
            import re

            entidades_match = re.search(
                r"entidades_insertadas['\"]?\s*:\s*(\d+)", output
            )
            hechos_match = re.search(r"hechos_insertados['\"]?\s*:\s*(\d+)", output)

            if entidades_match:
                print(f"   - Entidades insertadas: {entidades_match.group(1)}")
            if hechos_match:
                print(f"   - Hechos insertados: {hechos_match.group(1)}")

        else:
            print("   ⚠ No se encontraron indicadores claros de éxito o error")
            print("   Revise el output completo del pipeline")

        # 5. Guardar logs para análisis
        log_file = f"verificacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        with open(log_file, "w") as f:
            f.write(f"=== STDOUT ===\n{result.stdout}\n\n")
            f.write(f"=== STDERR ===\n{result.stderr}\n")
        print(f"\n   Logs guardados en: {log_file}")

        return not bool(errores_encontrados)

    except subprocess.CalledProcessError as e:
        print(f"   ✗ ERROR al ejecutar el pipeline: {e}")
        return False
    except Exception as e:
        print(f"   ✗ ERROR inesperado: {e}")
        return False


def main():
    """Función principal."""
    print(
        "\nEste script verificará que las correcciones de nomenclatura funcionan correctamente."
    )
    print(
        "Asegúrese de haber aplicado la migración SQL antes de ejecutar este script.\n"
    )

    input("Presione ENTER para continuar...")

    if ejecutar_prueba():
        print("\n✅ VERIFICACIÓN EXITOSA")
        print("Las correcciones de nomenclatura están funcionando correctamente.")
    else:
        print("\n❌ VERIFICACIÓN FALLIDA")
        print("Las correcciones no se aplicaron correctamente o hay otros problemas.")
        print("\nPasos a seguir:")
        print("1. Verifique que la migración SQL se aplicó en Supabase")
        print("2. Reconstruya el contenedor: docker-compose build module_pipeline")
        print("3. Revise los logs generados para más detalles")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
