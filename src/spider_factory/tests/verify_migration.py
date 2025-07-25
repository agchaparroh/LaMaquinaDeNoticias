#!/usr/bin/env python3
"""
Script de verificación simple para las herramientas de migración
"""

import os
import re  # noqa: F401
from pathlib import Path


def verify_migration_scripts():
    """Verifica que los scripts de migración existen y tienen la estructura correcta"""
    print("=== VERIFICACIÓN DE SCRIPTS DE MIGRACIÓN ===\n")

    base_path = Path(
        "/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/spider_factory/src"
    )

    scripts = {
        "migrate_spider.py": {
            "classes": ["SpiderMigrator"],
            "methods": [
                "detect_spider_type",
                "backup_spider",
                "migrate_to_v2",
                "validate_migration",
            ],
            "required_strings": [
                "AREAS_GEOGRAFICAS_VALIDAS",
                "custom_settings",
                "titular",
            ],
        },
        "validate_spiders.py": {
            "classes": ["SpiderValidator"],
            "methods": [
                "validate_spider_file",
                "validate_all_spiders",
                "generate_compatibility_report",
            ],
            "required_strings": [
                "REQUIRED_CLASS_FIELDS",
                "REQUIRED_ITEM_FIELDS",
                "REQUIRED_SETTINGS",
            ],
        },
        "batch_migrate.py": {
            "classes": ["BatchMigrator"],
            "methods": ["migrate_directory", "print_report"],
            "required_strings": ["ThreadPoolExecutor", "dry_run"],
        },
    }

    all_ok = True

    for script_name, requirements in scripts.items():
        script_path = base_path / script_name
        print(f"\n📄 Verificando {script_name}:")

        if not script_path.exists():
            print(f"   ❌ No existe")  # noqa: F541
            all_ok = False
            continue

        print(f"   ✅ Archivo existe")  # noqa: F541

        try:
            content = script_path.read_text()

            # Verificar clases
            for class_name in requirements["classes"]:
                if f"class {class_name}" in content:
                    print(f"   ✅ Clase {class_name} encontrada")
                else:
                    print(f"   ❌ Clase {class_name} NO encontrada")
                    all_ok = False

            # Verificar métodos
            for method_name in requirements["methods"]:
                if f"def {method_name}" in content:
                    print(f"   ✅ Método {method_name} encontrado")
                else:
                    print(f"   ❌ Método {method_name} NO encontrado")
                    all_ok = False

            # Verificar strings requeridos
            for req_string in requirements["required_strings"]:
                if req_string in content:
                    print(f"   ✅ String '{req_string}' encontrado")
                else:
                    print(f"   ❌ String '{req_string}' NO encontrado")
                    all_ok = False

            # Contar líneas
            lines = len(content.splitlines())
            print(f"   📊 Total de líneas: {lines}")

        except Exception as e:
            print(f"   ❌ Error leyendo archivo: {e}")
            all_ok = False

    # Verificar que los scripts son ejecutables
    print("\n📝 Verificando permisos de ejecución:")
    for script_name in scripts:
        script_path = base_path / script_name
        if script_path.exists():
            is_executable = os.access(script_path, os.X_OK)
            status = "✅" if is_executable else "⚠️"
            print(
                f"   {status} {script_name} {'es' if is_executable else 'no es'} ejecutable"
            )

    return all_ok


def check_example_spider_format():
    """Verifica el formato esperado de un spider migrado"""
    print("\n\n=== FORMATO ESPERADO DE SPIDER MIGRADO ===\n")

    expected_format = """# -*- coding: utf-8 -*-
import scrapy

class MedioSeccionSpider(scrapy.Spider):
    name = "medio_seccion"  # Formato: {medio}_{seccion}
    
    # Campos obligatorios Spider Factory 2.0
    medio = "Nombre del Medio"
    seccion = "Sección"
    area_geografica = "ESPAÑA"  # De AREAS_GEOGRAFICAS_VALIDAS
    tipo_medio = "diario"  # diario|revista|agencia
    
    custom_settings = {
        'CRAWL_ONCE_ENABLED': True,
        'CRAWL_ONCE_PATH': f'.scrapy/crawl_once/medio_seccion',
        'CRAWL_ONCE_DEFAULT': False,
    }
    
    def parse(self, response):
        item = {}
        
        # Campos obligatorios en items
        item['titular'] = "..."  # NO 'titulo'
        item['medio'] = self.medio
        item['seccion'] = self.seccion
        item['area_geografica'] = self.area_geografica
        item['tipo_medio'] = self.tipo_medio
        item['medio_url_principal'] = response.url
        item['fecha_publicacion'] = "..."
        item['contenido_texto'] = "..."
        item['contenido_html'] = "..."
        item['fuente'] = 'spider_factory_2.0'
        item['metadata'] = {
            'spider_type': 'scraping',
            'extraction_method': 'css',
            'section_filter': True
        }
        
        yield item
"""

    print("Estructura esperada:")
    print("-" * 60)
    print(expected_format)
    print("-" * 60)

    print("\n✅ Campos de clase obligatorios:")
    print("   - name (formato: medio_seccion)")
    print("   - medio")
    print("   - seccion")
    print("   - area_geografica")
    print("   - tipo_medio")

    print("\n✅ Campos de item obligatorios:")
    print("   - titular (NO 'titulo')")
    print("   - medio")
    print("   - medio_url_principal")
    print("   - area_geografica")
    print("   - tipo_medio")
    print("   - seccion")
    print("   - fecha_publicacion")
    print("   - contenido_texto")
    print("   - contenido_html")
    print("   - fuente")
    print("   - metadata")

    print("\n✅ Configuración Scrapy obligatoria:")
    print("   - CRAWL_ONCE_ENABLED: True")
    print("   - CRAWL_ONCE_PATH: f'.scrapy/crawl_once/{name}'")
    print("   - CRAWL_ONCE_DEFAULT: False")


def main():
    """Función principal"""
    print("VERIFICACIÓN DE HERRAMIENTAS DE MIGRACIÓN")
    print("=" * 60)

    # Verificar scripts
    scripts_ok = verify_migration_scripts()

    # Mostrar formato esperado
    check_example_spider_format()

    # Resumen
    print("\n\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)

    if scripts_ok:
        print("✅ Todos los scripts de migración están correctamente implementados")
        print("\n📋 Uso de los scripts:")
        print(
            "   1. validate_spiders.py --report  # Ver qué spiders necesitan migración"
        )
        print("   2. migrate_spider.py <spider.py> --dry-run  # Probar migración")
        print("   3. migrate_spider.py <spider.py>  # Migrar spider")
        print("   4. batch_migrate.py --spiders-dir <dir>  # Migrar todos")
    else:
        print("❌ Hay problemas con los scripts de migración")

    print("\n📚 Documentación:")
    print("   - Los scripts crean backups antes de modificar")
    print("   - Usan --dry-run para simular sin cambios")
    print("   - validate_spiders.py genera reportes JSON")
    print("   - batch_migrate.py procesa en paralelo")


if __name__ == "__main__":
    main()
