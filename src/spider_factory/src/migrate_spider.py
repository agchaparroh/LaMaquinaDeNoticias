#!/usr/bin/env python3
"""
Script de migración de spiders existentes a Spider Factory 2.0
"""

import argparse
import ast  # noqa: F401
import os  # noqa: F401
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple  # noqa: F401

from src.config import AREAS_GEOGRAFICAS_VALIDAS  # noqa: F401
from src.logging_config import logger


class SpiderMigrator:
    """Migrador de spiders a la nueva versión"""

    def __init__(self, backup_dir: str = "backups/migrations"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def detect_spider_type(self, file_path: Path) -> Tuple[str, Dict[str, str]]:
        """
        Detecta el tipo de spider y extrae metadata

        Returns:
            Tuple[tipo, metadata]
        """
        content = file_path.read_text(encoding="utf-8")

        # Detectar tipo
        spider_type = "scraping"  # Por defecto
        if "RssXMLSpider" in content or "feedparser" in content:
            spider_type = "rss"
        elif "playwright" in content or "PlaywrightSpider" in content:
            spider_type = "playwright"

        # Extraer metadata existente
        metadata = {}

        # Buscar nombre del spider
        name_match = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", content)
        if name_match:
            metadata["original_name"] = name_match.group(1)

        # Buscar medio y sección del nombre o comentarios
        if "original_name" in metadata:
            parts = metadata["original_name"].split("_")
            if len(parts) >= 2:
                metadata["medio"] = parts[0].replace("-", " ").title()
                metadata["seccion"] = parts[1].replace("-", " ").title()

        # Buscar custom_settings
        if "custom_settings" in content:
            metadata["has_custom_settings"] = True

        # Buscar si ya tiene campos nuevos
        if "area_geografica" in content:
            metadata["already_migrated"] = True

        logger.info(f"Detectado spider tipo '{spider_type}' con metadata: {metadata}")
        return spider_type, metadata

    def backup_spider(self, file_path: Path) -> Path:
        """
        Crea backup del spider antes de migrar

        Returns:
            Path al archivo de backup
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}.py.bak"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(file_path, backup_path)
        logger.info(f"Backup creado: {backup_path}")

        return backup_path

    def migrate_to_v2(
        self, file_path: Path, metadata: Dict[str, str], dry_run: bool = False
    ) -> bool:
        """
        Migra spider a versión 2.0 con campos obligatorios

        Args:
            file_path: Ruta al spider
            metadata: Metadata adicional para la migración
            dry_run: Si True, no modifica el archivo

        Returns:
            True si la migración fue exitosa
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # Si ya está migrado, no hacer nada
            if metadata.get("already_migrated"):
                logger.info(f"Spider {file_path.name} ya está migrado")
                return True

            # Detectar medio y sección
            medio = metadata.get("medio", "Unknown")
            seccion = metadata.get("seccion", "General")

            # Normalizar nombre del spider
            new_name = (
                f"{medio.lower().replace(' ', '_')}_{seccion.lower().replace(' ', '_')}"
            )

            # 1. Actualizar nombre del spider
            content = re.sub(
                r"name\s*=\s*['\"]([^'\"]+)['\"]", f'name = "{new_name}"', content
            )

            # 2. Agregar campos obligatorios después de 'name'
            if "medio =" not in content:
                name_line = re.search(r"(name\s*=\s*['\"][^'\"]+['\"])", content)
                if name_line:
                    insert_pos = name_line.end()
                    new_fields = f'''
    
    # Campos obligatorios Spider Factory 2.0
    medio = "{medio}"
    seccion = "{seccion}"
    area_geografica = "{self._guess_area_geografica(medio)}"
    tipo_medio = "diario"  # TODO: Ajustar según corresponda (diario|revista|agencia)'''

                    content = content[:insert_pos] + new_fields + content[insert_pos:]

            # 3. Cambiar 'titulo' por 'titular' en items
            content = re.sub(r"item\['titulo'\]", "item['titular']", content)
            content = re.sub(r'item\["titulo"\]', 'item["titular"]', content)

            # 4. Agregar campos faltantes en parse/parse_item
            fields_to_add = [
                "item['medio'] = self.medio",
                "item['medio_url_principal'] = response.url",
                "item['area_geografica'] = self.area_geografica",
                "item['tipo_medio'] = self.tipo_medio",
                "item['seccion'] = self.seccion",
                "item['fuente'] = 'spider_factory_2.0'",
                "item['metadata'] = {",
                "    'spider_type': '{}',".format(
                    metadata.get("spider_type", "scraping")
                ),
                "    'extraction_method': 'css',",
                "    'section_filter': True",
                "}",
            ]

            # Buscar dónde insertar los campos
            parse_method = re.search(
                r"def\s+parse(_item|_article|_news)?\s*\([^)]+\):", content
            )
            if parse_method:
                # Buscar el primer yield/return dentro del método
                yield_match = re.search(
                    r"(yield\s+item|return\s+item)", content[parse_method.end() :]
                )
                if yield_match:
                    insert_pos = parse_method.end() + yield_match.start()

                    # Verificar qué campos ya existen
                    existing_content = content[parse_method.end() : insert_pos]
                    fields_text = "\n        "

                    for field in fields_to_add:
                        field_name = field.split("[")[1].split("]")[0].strip("'\"")
                        if (
                            f"['{field_name}']" not in existing_content
                            and f'["{field_name}"]' not in existing_content
                        ):
                            fields_text += field + "\n        "

                    if fields_text.strip():
                        content = (
                            content[:insert_pos]
                            + fields_text
                            + "\n        "
                            + content[insert_pos:]
                        )

            # 5. Agregar/actualizar custom_settings para scrapy-crawl-once
            if "custom_settings" not in content:
                # Buscar dónde insertar custom_settings
                class_match = re.search(r"class\s+\w+Spider[^:]*:", content)
                if class_match:
                    # Insertar después de los campos obligatorios
                    insert_match = re.search(
                        r"tipo_medio\s*=\s*['\"][^'\"]+['\"]", content
                    )
                    if insert_match:
                        insert_pos = insert_match.end()
                        custom_settings = f"""
    
    custom_settings = {{
        'CRAWL_ONCE_ENABLED': True,
        'CRAWL_ONCE_PATH': f'.scrapy/crawl_once/{new_name}',
        'CRAWL_ONCE_DEFAULT': False,
    }}"""
                        content = (
                            content[:insert_pos]
                            + custom_settings
                            + content[insert_pos:]
                        )
            else:
                # Actualizar custom_settings existente
                content = re.sub(
                    r"'CRAWL_ONCE_PATH':\s*['\"][^'\"]+['\"]",
                    f"'CRAWL_ONCE_PATH': f'.scrapy/crawl_once/{new_name}'",
                    content,
                )

            # 6. Formatear con Black si está disponible
            try:
                import black

                content = black.format_str(content, mode=black.Mode())
            except ImportError:
                logger.warning("Black no disponible, omitiendo formateo")
            except Exception as e:
                logger.warning(f"Error al formatear con Black: {e}")

            # Guardar cambios
            if not dry_run:
                # Crear backup primero
                self.backup_spider(file_path)

                # Escribir contenido migrado
                file_path.write_text(content, encoding="utf-8")
                logger.info(f"Spider {file_path.name} migrado exitosamente")
            else:
                logger.info(f"[DRY RUN] Spider {file_path.name} sería migrado")
                # Mostrar diff
                self._show_diff(original_content, content)

            return True

        except Exception as e:
            logger.error(f"Error migrando spider {file_path.name}: {e}")
            return False

    def validate_migration(self, file_path: Path) -> Dict[str, bool]:
        """
        Valida que el spider tenga todos los campos obligatorios

        Returns:
            Dict con el estado de validación de cada campo
        """
        content = file_path.read_text(encoding="utf-8")

        validations = {
            "name_format": False,
            "medio_field": False,
            "seccion_field": False,
            "area_geografica_field": False,
            "tipo_medio_field": False,
            "titular_not_titulo": False,
            "item_medio": False,
            "item_area_geografica": False,
            "item_tipo_medio": False,
            "item_seccion": False,
            "item_metadata": False,
            "custom_settings": False,
            "crawl_once_enabled": False,
        }

        # Verificar formato de nombre
        name_match = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", content)
        if name_match:
            name = name_match.group(1)
            validations["name_format"] = "_" in name

        # Verificar campos de clase
        validations["medio_field"] = (
            re.search(r"medio\s*=\s*['\"][^'\"]+['\"]", content) is not None
        )
        validations["seccion_field"] = (
            re.search(r"seccion\s*=\s*['\"][^'\"]+['\"]", content) is not None
        )
        validations["area_geografica_field"] = (
            re.search(r"area_geografica\s*=\s*['\"][^'\"]+['\"]", content) is not None
        )
        validations["tipo_medio_field"] = (
            re.search(r"tipo_medio\s*=\s*['\"][^'\"]+['\"]", content) is not None
        )

        # Verificar que no use 'titulo'
        validations["titular_not_titulo"] = (
            "item['titulo']" not in content and 'item["titulo"]' not in content
        )

        # Verificar campos en items
        validations["item_medio"] = (
            "item['medio']" in content or 'item["medio"]' in content
        )
        validations["item_area_geografica"] = (
            "item['area_geografica']" in content or 'item["area_geografica"]' in content
        )
        validations["item_tipo_medio"] = (
            "item['tipo_medio']" in content or 'item["tipo_medio"]' in content
        )
        validations["item_seccion"] = (
            "item['seccion']" in content or 'item["seccion"]' in content
        )
        validations["item_metadata"] = (
            "item['metadata']" in content or 'item["metadata"]' in content
        )

        # Verificar custom_settings
        validations["custom_settings"] = "custom_settings" in content
        validations["crawl_once_enabled"] = "'CRAWL_ONCE_ENABLED': True" in content

        return validations

    def _guess_area_geografica(self, medio: str) -> str:
        """Intenta adivinar el área geográfica basándose en el nombre del medio"""
        medio_lower = medio.lower()

        # Mapeo básico de medios conocidos
        mapping = {
            "pais": "ESPAÑA",
            "mundo": "ESPAÑA",
            "abc": "ESPAÑA",
            "vanguardia": "ESPAÑA",
            "nacion": "ARGENTINA",
            "clarin": "ARGENTINA",
            "universal": "MEXICO",
            "reforma": "MEXICO",
            "mercurio": "CHILE",
            "comercio": "PERU",
            "globo": "BRASIL",
            "tiempo": "COLOMBIA",
            "espectador": "COLOMBIA",
        }

        for key, area in mapping.items():
            if key in medio_lower:
                return area

        return "GLOBAL"  # Por defecto

    def _show_diff(self, original: str, modified: str):
        """Muestra las diferencias entre el original y modificado"""
        import difflib

        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile="original",
            tofile="migrated",
        )

        print("\n=== CAMBIOS A REALIZAR ===")
        print("".join(diff))
        print("=========================\n")


def main():
    """Función principal del script de migración"""
    parser = argparse.ArgumentParser(description="Migra spiders a Spider Factory 2.0")
    parser.add_argument("spider_path", help="Ruta al spider a migrar")
    parser.add_argument(
        "--dry-run", action="store_true", help="Simula migración sin modificar archivos"
    )
    parser.add_argument("--medio", help="Nombre del medio (si no se puede detectar)")
    parser.add_argument(
        "--seccion", help="Nombre de la sección (si no se puede detectar)"
    )
    parser.add_argument(
        "--validate-only", action="store_true", help="Solo valida sin migrar"
    )

    args = parser.parse_args()

    spider_path = Path(args.spider_path)
    if not spider_path.exists():
        logger.error(f"Archivo no encontrado: {spider_path}")
        sys.exit(1)

    migrator = SpiderMigrator()

    if args.validate_only:
        # Solo validar
        validations = migrator.validate_migration(spider_path)
        print(f"\n=== Validación de {spider_path.name} ===")
        all_valid = True
        for check, passed in validations.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")
            if not passed:
                all_valid = False

        if all_valid:
            print("\n✅ El spider cumple con todos los requisitos")
        else:
            print("\n❌ El spider necesita migración")

        sys.exit(0 if all_valid else 1)

    # Detectar tipo y metadata
    spider_type, metadata = migrator.detect_spider_type(spider_path)

    # Sobrescribir con argumentos si se proporcionaron
    if args.medio:
        metadata["medio"] = args.medio
    if args.seccion:
        metadata["seccion"] = args.seccion

    metadata["spider_type"] = spider_type

    # Migrar
    success = migrator.migrate_to_v2(spider_path, metadata, dry_run=args.dry_run)

    if success and not args.dry_run:
        # Validar después de migrar
        validations = migrator.validate_migration(spider_path)
        if all(validations.values()):
            print(f"\n✅ Migración exitosa de {spider_path.name}")
        else:
            print(f"\n⚠️  Migración completada pero hay validaciones pendientes")  # noqa: F541
            for check, passed in validations.items():
                if not passed:
                    print(f"  ❌ {check}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
