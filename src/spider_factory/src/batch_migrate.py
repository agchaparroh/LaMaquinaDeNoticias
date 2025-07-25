#!/usr/bin/env python3
"""
Script de migración en batch para múltiples spiders
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple

from src.logging_config import logger
from src.migrate_spider import SpiderMigrator
from src.validate_spiders import SpiderValidator


class BatchMigrator:
    """Migrador en batch para múltiples spiders"""

    def __init__(self, max_workers: int = 5):
        self.migrator = SpiderMigrator()
        self.validator = SpiderValidator()
        self.max_workers = max_workers
        self.results = {"success": [], "failed": [], "skipped": []}

    def migrate_directory(
        self, directory: Path, dry_run: bool = False
    ) -> Dict[str, List]:
        """
        Migra todos los spiders en un directorio

        Args:
            directory: Directorio con los spiders
            dry_run: Si True, simula sin modificar archivos

        Returns:
            Dict con resultados de migración
        """
        spider_files = list(directory.glob("*.py"))
        spider_files = [f for f in spider_files if f.name != "__init__.py"]

        logger.info(f"Encontrados {len(spider_files)} spiders para migrar")

        # Primero validar todos para identificar cuáles necesitan migración
        need_migration = []
        for spider_file in spider_files:
            validation = self.validator.validate_spider_file(spider_file)
            if not validation["valid"]:
                need_migration.append((spider_file, validation))
            else:
                self.results["skipped"].append(
                    {"file": spider_file.name, "reason": "Ya migrado/válido"}
                )

        logger.info(f"{len(need_migration)} spiders necesitan migración")

        if not need_migration:
            logger.info("No hay spiders que migrar")
            return self.results

        # Migrar en paralelo
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_spider = {
                executor.submit(
                    self._migrate_single_spider, spider_path, validation, dry_run
                ): spider_path
                for spider_path, validation in need_migration
            }

            for future in as_completed(future_to_spider):
                spider_path = future_to_spider[future]
                try:
                    success, result = future.result()
                    if success:
                        self.results["success"].append(result)
                    else:
                        self.results["failed"].append(result)
                except Exception as e:
                    self.results["failed"].append(
                        {"file": spider_path.name, "error": str(e)}
                    )

        return self.results

    def _migrate_single_spider(
        self, spider_path: Path, validation: Dict, dry_run: bool
    ) -> Tuple[bool, Dict]:
        """
        Migra un spider individual

        Returns:
            Tuple[success, result_dict]
        """
        try:
            # Detectar tipo y metadata
            spider_type, metadata = self.migrator.detect_spider_type(spider_path)
            metadata["spider_type"] = spider_type

            # Intentar extraer medio y sección de los errores de validación
            for error in validation.get("errors", []):
                if "medio" in error and "faltante" in error:
                    # Intentar deducir del nombre del archivo
                    parts = spider_path.stem.split("_")
                    if len(parts) >= 2:
                        metadata["medio"] = parts[0].title()
                        metadata["seccion"] = parts[1].title()

            # Migrar
            success = self.migrator.migrate_to_v2(spider_path, metadata, dry_run)

            if success:
                # Validar después de migración (si no es dry run)
                if not dry_run:
                    post_validation = self.migrator.validate_migration(spider_path)
                    all_valid = all(post_validation.values())

                    return True, {
                        "file": spider_path.name,
                        "type": spider_type,
                        "validation": post_validation,
                        "fully_valid": all_valid,
                    }
                else:
                    return True, {
                        "file": spider_path.name,
                        "type": spider_type,
                        "dry_run": True,
                    }
            else:
                return False, {"file": spider_path.name, "error": "Migración falló"}

        except Exception as e:
            logger.error(f"Error migrando {spider_path.name}: {e}")
            return False, {"file": spider_path.name, "error": str(e)}

    def print_report(self):
        """Imprime reporte de migración"""
        print("\n" + "=" * 60)
        print("REPORTE DE MIGRACIÓN EN BATCH")
        print("=" * 60)

        print(f"\n✅ Migrados exitosamente: {len(self.results['success'])}")
        for result in self.results["success"]:
            status = "✅" if result.get("fully_valid", True) else "⚠️"
            print(f"  {status} {result['file']} ({result.get('type', 'unknown')})")

        if self.results["failed"]:
            print(f"\n❌ Fallaron: {len(self.results['failed'])}")
            for result in self.results["failed"]:
                print(
                    f"  - {result['file']}: {result.get('error', 'Error desconocido')}"
                )

        if self.results["skipped"]:
            print(f"\n⏭️  Omitidos (ya válidos): {len(self.results['skipped'])}")
            for result in self.results["skipped"][:5]:  # Mostrar máximo 5
                print(f"  - {result['file']}")
            if len(self.results["skipped"]) > 5:
                print(f"  ... y {len(self.results['skipped']) - 5} más")

        total = (
            len(self.results["success"])
            + len(self.results["failed"])
            + len(self.results["skipped"])
        )
        print(f"\nTotal procesados: {total}")

    def generate_migration_script(self, directory: Path, output_path: Path):
        """
        Genera un script bash para migrar todos los spiders
        """
        spider_files = list(directory.glob("*.py"))
        spider_files = [f for f in spider_files if f.name != "__init__.py"]

        # Validar primero
        need_migration = []
        for spider_file in spider_files:
            validation = self.validator.validate_spider_file(spider_file)
            if not validation["valid"]:
                need_migration.append(spider_file)

        if not need_migration:
            logger.info("No hay spiders que necesiten migración")
            return

        # Generar script
        script_content = """#!/bin/bash
# Script de migración generado automáticamente
# Fecha: {date}
# Spiders a migrar: {count}

set -e  # Detener en caso de error

echo "=== MIGRACIÓN DE SPIDERS A SPIDER FACTORY 2.0 ==="
echo "Spiders a migrar: {count}"
echo ""

# Crear directorio de backups
mkdir -p backups/migrations

# Migrar cada spider
""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M"), count=len(need_migration))

        for i, spider_path in enumerate(need_migration, 1):
            script_content += f"""
echo "[{i}/{len(need_migration)}] Migrando {spider_path.name}..."
python3 migrate_spider.py "{spider_path}"
if [ $? -eq 0 ]; then
    echo "  ✅ Migrado exitosamente"
else
    echo "  ❌ Error en migración"
fi
"""

        script_content += """
echo ""
echo "=== MIGRACIÓN COMPLETADA ==="
echo "Ejecuta validate_spiders.py para verificar los resultados"
"""

        output_path.write_text(script_content)
        output_path.chmod(0o755)  # Hacer ejecutable

        logger.info(f"Script de migración generado: {output_path}")
        print(f"\nScript de migración generado: {output_path}")
        print(f"Spiders que necesitan migración: {len(need_migration)}")
        print("\nPara ejecutar:")
        print(f"  ./{output_path.name}")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Migración en batch de spiders")
    parser.add_argument(
        "--spiders-dir",
        type=Path,
        default=Path(
            "/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/module_scraper/scraper_core/spiders"
        ),
        help="Directorio con los spiders",
    )
    parser.add_argument("--dry-run", action="store_true", help="Simula sin modificar")
    parser.add_argument("--workers", type=int, default=5, help="Workers paralelos")
    parser.add_argument(
        "--generate-script", action="store_true", help="Genera script de migración"
    )
    parser.add_argument(
        "--script-output",
        type=Path,
        default=Path("migrate_all.sh"),
        help="Archivo de salida del script",
    )

    args = parser.parse_args()

    if not args.spiders_dir.exists():
        logger.error(f"Directorio no encontrado: {args.spiders_dir}")
        sys.exit(1)

    migrator = BatchMigrator(max_workers=args.workers)

    if args.generate_script:
        # Solo generar script
        migrator.generate_migration_script(args.spiders_dir, args.script_output)
    else:
        # Ejecutar migración
        if args.dry_run:
            print("=== MODO DRY RUN - No se modificarán archivos ===\n")

        results = migrator.migrate_directory(args.spiders_dir, dry_run=args.dry_run)
        migrator.print_report()

        # Código de salida
        if results["failed"]:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    from datetime import datetime

    main()
