#!/usr/bin/env python3
"""
Script de validación de spiders para Spider Factory 2.0
Verifica que todos los spiders cumplan con los requisitos obligatorios
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple  # noqa: F401

from src.config import AREAS_GEOGRAFICAS_VALIDAS
from src.logging_config import logger


class SpiderValidator:
    """Validador de spiders según requisitos de Spider Factory 2.0"""

    # Campos obligatorios en la clase del spider
    REQUIRED_CLASS_FIELDS = [
        "name",
        "medio",
        "seccion",
        "area_geografica",
        "tipo_medio",
    ]

    # Campos obligatorios en los items
    REQUIRED_ITEM_FIELDS = [
        "titular",  # NO 'titulo'
        "medio",
        "medio_url_principal",
        "area_geografica",
        "tipo_medio",
        "seccion",
        "fecha_publicacion",
        "contenido_texto",
        "contenido_html",
        "fuente",
        "metadata",
    ]

    # Configuraciones Scrapy requeridas
    REQUIRED_SETTINGS = {
        "CRAWL_ONCE_ENABLED": True,
        "CRAWL_ONCE_PATH": str,  # Debe ser string
        "CRAWL_ONCE_DEFAULT": False,
    }

    def __init__(self):
        self.validation_results = []
        self.summary = {
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "warnings": 0,
            "by_type": defaultdict(int),
            "common_issues": defaultdict(int),
        }

    def validate_spider_file(self, file_path: Path) -> Dict[str, any]:
        """
        Valida un archivo de spider individual

        Returns:
            Dict con los resultados de validación
        """
        result = {
            "file": file_path.name,
            "path": str(file_path),
            "valid": True,
            "errors": [],
            "warnings": [],
            "spider_type": "unknown",
            "fields_status": {},
        }

        try:
            content = file_path.read_text(encoding="utf-8")

            # Detectar tipo de spider
            result["spider_type"] = self._detect_spider_type(content)
            self.summary["by_type"][result["spider_type"]] += 1

            # Validar nombre del spider
            name_validation = self._validate_spider_name(content)
            if not name_validation["valid"]:
                result["errors"].append(
                    f"Nombre inválido: {name_validation['message']}"
                )
                result["valid"] = False

            # Validar campos de clase
            class_fields = self._validate_class_fields(content)
            result["fields_status"]["class_fields"] = class_fields
            for field, status in class_fields.items():
                if not status["present"]:
                    result["errors"].append(f"Campo de clase faltante: {field}")
                    result["valid"] = False
                elif status.get("warning"):
                    result["warnings"].append(status["warning"])

            # Validar campos de items
            item_fields = self._validate_item_fields(content)
            result["fields_status"]["item_fields"] = item_fields
            for field, status in item_fields.items():
                if (
                    not status["present"] and field != "metadata"
                ):  # metadata es opcional en algunos casos
                    result["errors"].append(f"Campo de item faltante: item['{field}']")
                    result["valid"] = False

            # Validar que no use 'titulo' en lugar de 'titular'
            if self._uses_titulo_field(content):
                result["errors"].append("Usa 'titulo' en lugar de 'titular' en items")
                result["valid"] = False
                self.summary["common_issues"]["uses_titulo"] += 1

            # Validar custom_settings
            settings_validation = self._validate_custom_settings(content)
            result["fields_status"]["custom_settings"] = settings_validation
            if not settings_validation["valid"]:
                for error in settings_validation["errors"]:
                    result["errors"].append(f"Custom settings: {error}")
                    result["valid"] = False

            # Validar área geográfica
            area_validation = self._validate_area_geografica(content)
            if not area_validation["valid"]:
                result["errors"].append(
                    f"Área geográfica inválida: {area_validation['value']}"
                )
                result["valid"] = False
                self.summary["common_issues"]["invalid_area"] += 1

            # Validar tipo de medio
            tipo_validation = self._validate_tipo_medio(content)
            if not tipo_validation["valid"]:
                result["errors"].append(
                    f"Tipo de medio inválido: {tipo_validation['value']}"
                )
                result["valid"] = False
                self.summary["common_issues"]["invalid_tipo"] += 1

        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Error al leer archivo: {str(e)}")

        # Actualizar resumen
        self.summary["total"] += 1
        if result["valid"]:
            self.summary["valid"] += 1
        else:
            self.summary["invalid"] += 1
        if result["warnings"]:
            self.summary["warnings"] += 1

        return result

    def validate_all_spiders(self, directory: Path) -> List[Dict]:
        """
        Valida todos los spiders en un directorio

        Returns:
            Lista con los resultados de validación
        """
        spider_files = list(directory.glob("*.py"))
        spider_files = [f for f in spider_files if f.name != "__init__.py"]

        logger.info(f"Encontrados {len(spider_files)} archivos de spider para validar")

        for spider_file in spider_files:
            result = self.validate_spider_file(spider_file)
            self.validation_results.append(result)

        return self.validation_results

    def generate_compatibility_report(self) -> Dict[str, any]:
        """
        Genera reporte detallado de compatibilidad

        Returns:
            Dict con el reporte completo
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.summary,
            "valid_spiders": [],
            "invalid_spiders": [],
            "spiders_with_warnings": [],
            "field_coverage": self._calculate_field_coverage(),
            "recommendations": self._generate_recommendations(),
        }

        # Clasificar spiders
        for result in self.validation_results:
            if result["valid"] and not result["warnings"]:
                report["valid_spiders"].append(
                    {"name": result["file"], "type": result["spider_type"]}
                )
            elif result["valid"] and result["warnings"]:
                report["spiders_with_warnings"].append(
                    {
                        "name": result["file"],
                        "type": result["spider_type"],
                        "warnings": result["warnings"],
                    }
                )
            else:
                report["invalid_spiders"].append(
                    {
                        "name": result["file"],
                        "type": result["spider_type"],
                        "errors": result["errors"],
                    }
                )

        return report

    def save_report(self, report: Dict, output_path: Path):
        """Guarda el reporte en formato JSON"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Reporte guardado en: {output_path}")

    def print_summary(self):
        """Imprime resumen en consola"""
        print("\n" + "=" * 60)
        print("RESUMEN DE VALIDACIÓN DE SPIDERS")
        print("=" * 60)
        print(f"Total de spiders analizados: {self.summary['total']}")
        print(f"✅ Válidos: {self.summary['valid']}")
        print(f"❌ Inválidos: {self.summary['invalid']}")
        print(f"⚠️  Con advertencias: {self.summary['warnings']}")

        if self.summary["by_type"]:
            print("\nPor tipo de spider:")
            for spider_type, count in self.summary["by_type"].items():
                print(f"  - {spider_type}: {count}")

        if self.summary["common_issues"]:
            print("\nProblemas comunes encontrados:")
            for issue, count in self.summary["common_issues"].items():
                print(f"  - {issue}: {count} spiders")

        print("\nSpiders que necesitan migración:")
        for result in self.validation_results:
            if not result["valid"]:
                print(f"\n❌ {result['file']}:")
                for error in result["errors"][:3]:  # Mostrar máximo 3 errores
                    print(f"   - {error}")
                if len(result["errors"]) > 3:
                    print(f"   ... y {len(result['errors']) - 3} errores más")

    def _detect_spider_type(self, content: str) -> str:
        """Detecta el tipo de spider basándose en el contenido"""
        if "RssXMLSpider" in content or "feedparser" in content:
            return "rss"
        elif "playwright" in content or "PlaywrightSpider" in content:
            return "playwright"
        else:
            return "scraping"

    def _validate_spider_name(self, content: str) -> Dict[str, any]:
        """Valida el formato del nombre del spider"""
        name_match = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", content)

        if not name_match:
            return {"valid": False, "message": "No se encontró el campo name"}

        name = name_match.group(1)

        # Debe tener formato medio_seccion
        if "_" not in name:
            return {
                "valid": False,
                "message": f"'{name}' no sigue formato medio_seccion",
            }

        # No debe tener caracteres especiales excepto _
        if not re.match(r"^[a-z0-9_]+$", name):
            return {
                "valid": False,
                "message": f"'{name}' contiene caracteres no permitidos",
            }

        return {"valid": True, "name": name}

    def _validate_class_fields(self, content: str) -> Dict[str, Dict]:
        """Valida la presencia de campos obligatorios en la clase"""
        results = {}

        for field in self.REQUIRED_CLASS_FIELDS:
            pattern = rf"{field}\s*=\s*['\"]([^'\"]+)['\"]"
            match = re.search(pattern, content)

            if match:
                value = match.group(1)
                results[field] = {"present": True, "value": value}

                # Validaciones específicas
                if (
                    field == "area_geografica"
                    and value not in AREAS_GEOGRAFICAS_VALIDAS
                ):
                    results[field]["warning"] = (
                        f"Área geográfica '{value}' no está en la lista válida"
                    )
                elif field == "tipo_medio" and value not in [
                    "diario",
                    "revista",
                    "agencia",
                ]:
                    results[field]["warning"] = (
                        f"Tipo de medio '{value}' debe ser: diario, revista o agencia"
                    )
            else:
                results[field] = {"present": False}

        return results

    def _validate_item_fields(self, content: str) -> Dict[str, Dict]:
        """Valida la presencia de campos obligatorios en items"""
        results = {}

        for field in self.REQUIRED_ITEM_FIELDS:
            # Buscar diferentes formas de asignar el campo
            patterns = [
                rf"item\['{field}'\]",
                rf'item\["{field}"\]',
                rf"item\.get\('{field}'",
                rf'item\.get\("{field}"',
            ]

            found = any(re.search(pattern, content) for pattern in patterns)
            results[field] = {"present": found}

        return results

    def _uses_titulo_field(self, content: str) -> bool:
        """Verifica si usa 'titulo' en lugar de 'titular'"""
        patterns = [
            r"item\['titulo'\]",
            r'item\["titulo"\]',
            r"item\.get\('titulo'",
            r'item\.get\("titulo"',
        ]

        return any(re.search(pattern, content) for pattern in patterns)

    def _validate_custom_settings(self, content: str) -> Dict[str, any]:
        """Valida la configuración custom_settings"""
        result = {"valid": True, "errors": [], "settings": {}}

        # Buscar custom_settings
        settings_match = re.search(
            r"custom_settings\s*=\s*{([^}]+)}", content, re.DOTALL
        )

        if not settings_match:
            result["valid"] = False
            result["errors"].append("No se encontró custom_settings")
            return result

        settings_content = settings_match.group(1)

        # Validar configuraciones requeridas
        for setting, expected in self.REQUIRED_SETTINGS.items():
            pattern = rf"'{setting}':\s*([^,\n]+)"
            match = re.search(pattern, settings_content)

            if match:
                value = match.group(1).strip()
                result["settings"][setting] = value

                # Validar valor
                if expected == True and value != "True":  # noqa: E712
                    result["errors"].append(f"{setting} debe ser True")
                    result["valid"] = False
                elif expected == False and value != "False":  # noqa: E712
                    result["errors"].append(f"{setting} debe ser False")
                    result["valid"] = False
            else:
                result["errors"].append(f"Falta configuración: {setting}")
                result["valid"] = False

        return result

    def _validate_area_geografica(self, content: str) -> Dict[str, any]:
        """Valida que el área geográfica sea válida"""
        match = re.search(r"area_geografica\s*=\s*['\"]([^'\"]+)['\"]", content)

        if not match:
            return {"valid": False, "value": None}

        value = match.group(1)
        return {"valid": value in AREAS_GEOGRAFICAS_VALIDAS, "value": value}

    def _validate_tipo_medio(self, content: str) -> Dict[str, any]:
        """Valida que el tipo de medio sea válido"""
        match = re.search(r"tipo_medio\s*=\s*['\"]([^'\"]+)['\"]", content)

        if not match:
            return {"valid": False, "value": None}

        value = match.group(1)
        return {"valid": value in ["diario", "revista", "agencia"], "value": value}

    def _calculate_field_coverage(self) -> Dict[str, float]:
        """Calcula el porcentaje de cobertura de cada campo"""
        coverage = {"class_fields": defaultdict(int), "item_fields": defaultdict(int)}

        total = len(self.validation_results)
        if total == 0:
            return {}

        for result in self.validation_results:
            if "fields_status" in result:
                # Campos de clase
                for field, status in (
                    result["fields_status"].get("class_fields", {}).items()
                ):
                    if status["present"]:
                        coverage["class_fields"][field] += 1

                # Campos de items
                for field, status in (
                    result["fields_status"].get("item_fields", {}).items()
                ):
                    if status["present"]:
                        coverage["item_fields"][field] += 1

        # Convertir a porcentajes
        for category in coverage:
            for field in coverage[category]:
                coverage[category][field] = round(
                    coverage[category][field] / total * 100, 1
                )

        return dict(coverage)

    def _generate_recommendations(self) -> List[str]:
        """Genera recomendaciones basadas en los resultados"""
        recommendations = []

        if self.summary["invalid"] > 0:
            recommendations.append(
                f"Migrar {self.summary['invalid']} spiders inválidos usando migrate_spider.py"
            )

        if self.summary["common_issues"].get("uses_titulo", 0) > 0:
            recommendations.append("Cambiar campo 'titulo' por 'titular' en items")

        if self.summary["common_issues"].get("invalid_area", 0) > 0:
            recommendations.append(
                "Actualizar áreas geográficas a valores válidos de la lista AREAS_GEOGRAFICAS_VALIDAS"
            )

        if self.summary["warnings"] > 0:
            recommendations.append(
                f"Revisar {self.summary['warnings']} spiders con advertencias"
            )

        return recommendations


def main():
    """Función principal del script de validación"""
    parser = argparse.ArgumentParser(description="Valida spiders de Spider Factory 2.0")
    parser.add_argument(
        "--spiders-dir",
        type=Path,
        default=Path(
            "/mnt/c/Users/DELL/Desktop/PruebaWindsurfAI/LaMaquinaDeNoticias/src/module_scraper/scraper_core/spiders"
        ),
        help="Directorio con los spiders a validar",
    )
    parser.add_argument(
        "--report", action="store_true", help="Genera reporte detallado"
    )
    parser.add_argument("--output", type=Path, help="Archivo de salida para el reporte")
    parser.add_argument("--spider", type=Path, help="Validar un spider específico")

    args = parser.parse_args()

    validator = SpiderValidator()

    if args.spider:
        # Validar un solo spider
        if not args.spider.exists():
            logger.error(f"Spider no encontrado: {args.spider}")
            sys.exit(1)

        result = validator.validate_spider_file(args.spider)

        print(f"\n=== Validación de {args.spider.name} ===")
        if result["valid"]:
            print("✅ El spider es válido")
        else:
            print("❌ El spider tiene errores:")
            for error in result["errors"]:
                print(f"  - {error}")

        if result["warnings"]:
            print("\n⚠️  Advertencias:")
            for warning in result["warnings"]:
                print(f"  - {warning}")

    else:
        # Validar todos los spiders
        if not args.spiders_dir.exists():
            logger.error(f"Directorio no encontrado: {args.spiders_dir}")
            sys.exit(1)

        validator.validate_all_spiders(args.spiders_dir)

        if args.report:
            # Generar reporte completo
            report = validator.generate_compatibility_report()

            # Guardar reporte
            output_path = args.output or Path(
                f"spider_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            validator.save_report(report, output_path)

        # Mostrar resumen
        validator.print_summary()

    # Retornar código de salida basado en validación
    if validator.summary["invalid"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
