#!/usr/bin/env python3
"""
CPMS3 Validator - Valida precondiciones antes de ejecutar planes
"""

import ast  # noqa: F401
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple  # noqa: F401


class PlanValidator:
    """Valida que un plan pueda ejecutarse exitosamente"""

    def __init__(self, plan: Dict, base_path: Optional[str] = None):
        self.plan = plan
        self.base_path = Path(base_path or plan.get("config", {}).get("base_path", "."))
        self.errors = []
        self.warnings = []
        self.info = []

    def validate(self) -> Tuple[bool, List[str], List[str], List[str]]:
        """
        Valida el plan completo
        Retorna: (es_valido, errores, advertencias, info)
        """
        # 1. Validar archivos referenciados
        self._validate_referenced_files()

        # 2. Validar patrones de búsqueda
        self._validate_search_patterns()

        # 3. Validar comandos
        self._validate_commands()

        # 4. Validar sintaxis de código
        self._validate_code_syntax()

        # 5. Validar permisos
        self._validate_permissions()

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings, self.info

    def _validate_referenced_files(self):
        """Valida que todos los archivos referenciados existan cuando deberían"""
        steps = self.plan.get("steps", [])

        for step in steps:
            action = step.get("action")
            step_id = step.get("id", "unknown")

            if action == "modify_file":
                path = self._resolve_path(step.get("path", ""))
                if not path.exists():
                    self.errors.append(
                        f"{step_id}: Archivo a modificar no existe: {path}"
                    )
                else:
                    self.info.append(f"{step_id}: Archivo verificado: {path}")

            elif action == "delete_file":
                path = self._resolve_path(step.get("path", ""))
                if not path.exists():
                    self.warnings.append(
                        f"{step_id}: Archivo a eliminar no existe: {path}"
                    )

            elif action == "create_file":
                path = self._resolve_path(step.get("path", ""))
                if path.exists():
                    self.warnings.append(
                        f"{step_id}: Archivo a crear ya existe: {path}"
                    )
                # Verificar que el directorio padre exista o se pueda crear
                parent = path.parent
                if not parent.exists():
                    try:
                        # Verificar si se puede crear
                        parent.mkdir(parents=True, exist_ok=True)
                        parent.rmdir()  # Limpieza
                        self.info.append(f"{step_id}: Directorio se creará: {parent}")
                    except Exception as e:
                        self.errors.append(
                            f"{step_id}: No se puede crear directorio: {parent} - {e}"
                        )

    def _validate_search_patterns(self):
        """Valida que los patrones de búsqueda existan en los archivos"""
        steps = self.plan.get("steps", [])

        for step in steps:
            if step.get("action") != "modify_file":
                continue

            step_id = step.get("id", "unknown")
            path = self._resolve_path(step.get("path", ""))

            if not path.exists():
                continue  # Ya reportado en _validate_referenced_files

            try:
                content = path.read_text(encoding="utf-8")
            except Exception as e:
                self.errors.append(f"{step_id}: No se puede leer archivo: {path} - {e}")
                continue

            changes = step.get("changes", [])
            for i, change in enumerate(changes):
                find_text = change.get("find", "")

                if find_text not in content:
                    # Intentar búsqueda normalizada
                    normalized_content = self._normalize_for_search(content)
                    normalized_find = self._normalize_for_search(find_text)

                    if normalized_find in normalized_content:
                        self.warnings.append(
                            f"{step_id}.change[{i}]: Patrón encontrado solo "
                            f"con normalización (espacios/saltos de línea)"
                        )
                    else:
                        # Mostrar contexto para ayudar al debug
                        preview = (
                            find_text[:50] + "..." if len(find_text) > 50 else find_text
                        )
                        self.errors.append(
                            f"{step_id}.change[{i}]: Patrón no encontrado en {path}: "
                            f"'{preview}'"
                        )

                        # Buscar coincidencias parciales para ayudar
                        suggestions = self._find_similar_text(find_text, content)
                        if suggestions:
                            self.info.append(
                                f"  Sugerencia: Se encontró texto similar: "
                                f"'{suggestions[0][:50]}...'"
                            )
                else:
                    self.info.append(
                        f"{step_id}.change[{i}]: Patrón verificado en {path}"
                    )

    def _validate_commands(self):
        """Valida que los comandos sean ejecutables"""
        steps = self.plan.get("steps", [])

        for step in steps:
            if step.get("action") != "run_command":
                continue

            step_id = step.get("id", "unknown")
            command = step.get("command", "")

            # Extraer el ejecutable principal
            executable = self._extract_executable(command)

            if executable:
                # Verificar si el ejecutable existe
                if not self._command_exists(executable):
                    self.warnings.append(
                        f"{step_id}: Comando no encontrado: {executable}"
                    )
                else:
                    self.info.append(f"{step_id}: Comando verificado: {executable}")

    def _validate_code_syntax(self):
        """Valida la sintaxis de código Python en create_file"""
        steps = self.plan.get("steps", [])

        for step in steps:
            if step.get("action") != "create_file":
                continue

            step_id = step.get("id", "unknown")
            path = step.get("path", "")
            content = step.get("content", "")

            # Solo validar archivos Python
            if path.endswith(".py"):
                try:
                    compile(content, path, "exec")
                    self.info.append(f"{step_id}: Sintaxis Python válida")
                except SyntaxError as e:
                    self.errors.append(
                        f"{step_id}: Error de sintaxis Python en línea {e.lineno}: {e.msg}"
                    )

    def _validate_permissions(self):
        """Valida permisos de escritura en directorios"""
        # Recolectar todos los directorios que necesitaremos
        directories = set()

        steps = self.plan.get("steps", [])
        for step in steps:
            action = step.get("action")

            if action in ["create_file", "modify_file", "delete_file"]:
                path = self._resolve_path(step.get("path", ""))
                directories.add(path.parent)
            elif action == "move_file":
                source = self._resolve_path(step.get("source", ""))
                target = self._resolve_path(step.get("target", ""))
                directories.add(source.parent)
                directories.add(target.parent)

        # Verificar permisos
        for directory in directories:
            if directory.exists():
                if not os.access(directory, os.W_OK):
                    self.errors.append(f"Sin permisos de escritura en: {directory}")
            else:
                # Verificar el padre más cercano que exista
                parent = directory
                while not parent.exists() and parent.parent != parent:
                    parent = parent.parent

                if not os.access(parent, os.W_OK):
                    self.errors.append(f"Sin permisos para crear: {directory}")

    # === Métodos auxiliares ===

    def _resolve_path(self, path: str) -> Path:
        """Resuelve una ruta relativa al base_path"""
        if not path:
            return Path()

        p = Path(path)
        if p.is_absolute():
            return p
        else:
            return self.base_path / p

    def _normalize_for_search(self, text: str) -> str:
        """Normaliza texto para búsqueda flexible"""
        # Normalizar saltos de línea
        text = text.replace("\r\n", "\n")

        # Normalizar espacios múltiples
        text = re.sub(r" +", " ", text)

        # Normalizar espacios alrededor de símbolos
        text = re.sub(r"\s*([=:{},\[\]])\s*", r"\1", text)

        return text

    def _find_similar_text(
        self, pattern: str, content: str, max_results: int = 3
    ) -> List[str]:
        """Encuentra texto similar al patrón buscado"""
        similar = []

        # Buscar líneas que contengan palabras clave del patrón
        pattern_words = set(re.findall(r"\w+", pattern))
        if not pattern_words:
            return similar

        lines = content.split("\n")
        scored_lines = []

        for i, line in enumerate(lines):
            line_words = set(re.findall(r"\w+", line))
            common_words = pattern_words & line_words

            if common_words:
                score = len(common_words) / len(pattern_words)
                scored_lines.append((score, i, line))

        # Ordenar por score y tomar los mejores
        scored_lines.sort(reverse=True, key=lambda x: x[0])

        for score, line_num, line in scored_lines[:max_results]:
            # Incluir contexto (líneas anteriores y posteriores)
            start = max(0, line_num - 1)
            end = min(len(lines), line_num + 2)
            context = "\n".join(lines[start:end])
            similar.append(context)

        return similar

    def _extract_executable(self, command: str) -> Optional[str]:
        """Extrae el ejecutable principal de un comando"""
        # Manejar comandos complejos
        command = command.strip()

        # Si empieza con cd, buscar el siguiente comando
        if command.startswith("cd "):
            parts = command.split("&&", 1)
            if len(parts) > 1:
                command = parts[1].strip()

        # Extraer primera palabra (ejecutable)
        parts = command.split()
        if parts:
            executable = parts[0]
            # Remover opciones de shell
            if executable in ["!", "sudo", "time"]:
                executable = parts[1] if len(parts) > 1 else None
            return executable

        return None

    def _command_exists(self, command: str) -> bool:
        """Verifica si un comando existe en el sistema"""
        # Comandos built-in de shell
        shell_builtins = [
            "cd",
            "echo",
            "pwd",
            "export",
            "alias",
            "source",
            "test",
            "mkdir",
            "cp",
            "mv",
            "rm",
            "cat",
            "grep",
        ]

        if command in shell_builtins:
            return True

        # Verificar con which
        try:
            result = subprocess.run(["which", command], capture_output=True, text=True)
            return result.returncode == 0
        except:  # noqa: E722
            # En Windows, intentar where
            try:
                result = subprocess.run(
                    ["where", command], capture_output=True, text=True, shell=True
                )
                return result.returncode == 0
            except:  # noqa: E722
                return False


def print_validation_report(
    is_valid: bool, errors: List[str], warnings: List[str], info: List[str]
):
    """Imprime un reporte formateado de validación"""
    print("\n" + "=" * 60)
    print("📋 CPMS3 Validation Report")
    print("=" * 60)

    if errors:
        print(f"\n❌ Errores ({len(errors)}):")
        for error in errors:
            print(f"   • {error}")

    if warnings:
        print(f"\n⚠️  Advertencias ({len(warnings)}):")
        for warning in warnings:
            print(f"   • {warning}")

    if info and len(info) <= 10:  # Solo mostrar si hay pocos
        print(f"\n✅ Verificaciones exitosas ({len(info)}):")
        for i in info:
            print(f"   • {i}")
    elif info:
        print(f"\n✅ Verificaciones exitosas: {len(info)}")

    print("\n" + "-" * 60)
    if is_valid:
        print("✅ RESULTADO: Plan válido y listo para ejecutar")
    else:
        print("❌ RESULTADO: Plan tiene errores que deben corregirse")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # Para testing standalone
    import sys

    import yaml

    if len(sys.argv) != 2:
        print("Uso: python validator.py <plan.yaml>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        plan = yaml.safe_load(f)

    validator = PlanValidator(plan)
    is_valid, errors, warnings, info = validator.validate()

    print_validation_report(is_valid, errors, warnings, info)

    sys.exit(0 if is_valid else 1)
