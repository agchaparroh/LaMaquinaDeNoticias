#!/usr/bin/env python
"""
Script de prueba para ejecutar el spider v2 de Europa Press Sudamérica
"""

import os
import subprocess
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Ejecutar el spider con configuración básica"""
    print("=== Ejecutando spider europapress_sudamerica_v2 ===")

    # Cambiar al directorio del módulo scraper
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Comando scrapy con configuración
    cmd = [
        sys.executable,
        "-m",
        "scrapy",
        "crawl",
        "europapress_sudamerica_v2",
        "-L",
        "INFO",
        "-s",
        "CLOSESPIDER_ITEMCOUNT=5",  # Solo 5 items para prueba
        "-s",
        "DOWNLOAD_DELAY=2",
        "-s",
        "ITEM_PIPELINES={}",  # Sin pipelines para prueba inicial
        "-o",
        "test_output_v2.json",  # Salida a archivo JSON
    ]

    print(f"Ejecutando: {' '.join(cmd)}")

    try:
        # Ejecutar el comando
        result = subprocess.run(cmd, capture_output=True, text=True)

        print("\n=== STDOUT ===")
        print(result.stdout)

        if result.stderr:
            print("\n=== STDERR ===")
            print(result.stderr)

        print(f"\n=== Código de salida: {result.returncode} ===")

        # Verificar si se creó el archivo de salida
        if os.path.exists("test_output_v2.json"):
            print("\n=== Archivo de salida creado ===")
            with open("test_output_v2.json", encoding="utf-8") as f:
                content = f.read()
                print(f"Tamaño del archivo: {len(content)} bytes")
                if len(content) > 0:
                    print("Primeros 500 caracteres:")
                    print(content[:500])
        else:
            print("\n=== No se creó archivo de salida ===")

    except Exception as e:
        print(f"\n=== ERROR: {str(e)} ===")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
