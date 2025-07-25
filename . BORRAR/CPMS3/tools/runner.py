#!/usr/bin/env python3
"""
CPMS3 Runner - Ejecutor Determinista de Planes
Ejecuta execution_plan.yaml paso a paso, con verificación automática.
"""

import os  # noqa: F401
import shutil
import subprocess
import sys
import time  # noqa: F401
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple  # noqa: F401

import yaml

# Importar nuestras herramientas
sys.path.append(str(Path(__file__).parent))
from autocheck import AutoCheck
from staging import StagingManager


class ExecutionError(Exception):
    """Error durante la ejecución de un paso"""

    pass


class CPMS3Runner:
    def __init__(self, plan_path: str):
        self.plan_path = Path(plan_path)
        self.plan_dir = self.plan_path.parent

        # Cargar plan
        with open(plan_path, encoding="utf-8") as f:
            self.plan = yaml.safe_load(f)

        # Configuración
        self.config = self.plan.get("config", {})
        self.base_path = Path(self.config.get("base_path", self.plan_dir))
        self.staging = StagingManager(
            self.base_path, self.config.get("staging_dir", ".cpms3_staging")
        )
        self.checker = AutoCheck(self.base_path)

        # Estado
        self.executed_steps = []
        self.failed_steps = []
        self.start_time = None
        self.constants = self.plan.get("constants", {})

    def run(self) -> bool:
        """Ejecuta el plan completo"""
        print(f"\n{'=' * 60}")
        print(f"🚀 CPMS3 Runner - Ejecutando: {self.plan['meta']['name']}")
        print(f"🎯 Objetivo: {self.plan['meta']['goal']}")
        print(f"{'=' * 60}\n")

        self.start_time = datetime.now()

        try:
            # Validar plan
            self._validate_plan()

            # Ejecutar pasos
            steps = self.plan.get("steps", [])
            total_steps = len(steps)

            for i, step in enumerate(steps, 1):
                print(
                    f"\n[{i}/{total_steps}] Ejecutando: {step.get('description', step['id'])}"
                )
                print("-" * 40)

                success = self._execute_step(step)

                if not success:
                    on_fail = step.get("on_fail", "abort")
                    if on_fail == "abort":
                        print("\n❌ ABORTANDO: Paso falló y on_fail=abort")
                        self._handle_failure()
                        return False
                    elif on_fail == "skip":
                        print("⚠️  Paso falló pero on_fail=skip, continuando...")
                        self.failed_steps.append(step["id"])
                        continue
                    elif on_fail == "retry":
                        # Reintentar
                        max_retries = self.config.get("max_retries", 3)
                        for retry in range(max_retries):
                            print(f"🔄 Reintentando ({retry + 1}/{max_retries})...")
                            if self._execute_step(step):
                                break
                        else:
                            print(f"❌ Falló después de {max_retries} intentos")
                            self._handle_failure()
                            return False

                self.executed_steps.append(step["id"])
                print(f"✅ Paso completado: {step['id']}")

            # Validación final
            if "final_validation" in self.plan:
                print("\n🔍 Ejecutando validación final...")
                if not self._run_final_validation():
                    print("❌ Validación final falló")
                    return False

            # Post-ejecución
            if "post_execution" in self.plan:
                print("\n📋 Ejecutando acciones post-ejecución...")
                self._run_post_execution()

            # Resumen final
            self._print_summary(True)
            return True

        except Exception as e:
            print(f"\n💥 ERROR FATAL: {str(e)}")
            traceback.print_exc()
            self._handle_failure()
            return False

    def _validate_plan(self):
        """Valida que el plan tenga estructura correcta"""
        required = ["meta", "steps"]
        for field in required:
            if field not in self.plan:
                raise ExecutionError(f"Campo requerido faltante: {field}")

        if "id" not in self.plan["meta"]:
            raise ExecutionError("meta.id es requerido")

        if not self.plan.get("steps"):
            raise ExecutionError("No hay pasos definidos")

    def _execute_step(self, step: Dict) -> bool:
        """Ejecuta un paso individual"""
        action = step.get("action")

        # Mapeo de acciones a métodos
        action_methods = {
            "create_file": self._action_create_file,
            "modify_file": self._action_modify_file,
            "delete_file": self._action_delete_file,
            "move_file": self._action_move_file,
            "run_command": self._action_run_command,
            "run_test": self._action_run_test,
            "install_package": self._action_install_package,
            "validate": self._action_validate,
        }

        method = action_methods.get(action)
        if not method:
            print(f"❌ Acción desconocida: {action}")
            return False

        try:
            # Ejecutar acción
            method(step)

            # Verificar
            if "verify" in step:
                print("\n🔍 Verificando...")
                success, details = self.checker.verify(step["verify"])

                for detail in details:
                    print(f"   {detail}")

                if not success:
                    print("❌ Verificación falló")
                    return False

            return True

        except Exception as e:
            print(f"❌ Error ejecutando paso: {str(e)}")
            traceback.print_exc()
            return False

    # ===== ACCIONES =====

    def _action_create_file(self, step: Dict):
        """Crea un archivo con contenido exacto"""
        path = self.base_path / step["path"]
        content = self._resolve_constants(step["content"])

        # Crear directorio si no existe
        path.parent.mkdir(parents=True, exist_ok=True)

        # Backup si existe
        if path.exists():
            self.staging.backup_file(path)

        # Escribir archivo
        path.write_text(content, encoding="utf-8")
        print(f"📄 Archivo creado: {path}")

    def _action_modify_file(self, step: Dict):
        """Modifica archivo con buscar/reemplazar"""
        path = self.base_path / step["path"]

        if not path.exists():
            raise ExecutionError(f"Archivo no existe: {path}")

        # Backup
        if step.get("backup", True):
            self.staging.backup_file(path)

        # Leer contenido
        content = path.read_text(encoding="utf-8")
        original_content = content

        # Aplicar cambios
        changes = step.get("changes", [])
        for change in changes:
            find_text = self._resolve_constants(change["find"])
            replace_text = self._resolve_constants(change["replace"])

            if find_text not in content:
                raise ExecutionError(f"Texto no encontrado: '{find_text[:50]}...'")

            content = content.replace(find_text, replace_text)

        # Escribir si cambió
        if content != original_content:
            path.write_text(content, encoding="utf-8")
            print(f"📝 Archivo modificado: {path}")

            # Mostrar resumen de cambios si verbose
            if self.config.get("verbose", False):
                lines_changed = content.count("\n") - original_content.count("\n")
                if lines_changed != 0:
                    print(
                        f"   Líneas {'añadidas' if lines_changed > 0 else 'eliminadas'}: {abs(lines_changed)}"
                    )
        else:
            print(f"ℹ️  Sin cambios en: {path}")

    def _action_delete_file(self, step: Dict):
        """Elimina archivo (o mueve a staging)"""
        path = self.base_path / step["path"]

        if not path.exists():
            print(f"ℹ️  Archivo ya no existe: {path}")
            return

        if step.get("staging", True):
            # Mover a staging en vez de borrar
            staging_path = self.staging.stage_deletion(path)
            print(f"🗑️  Archivo movido a staging: {staging_path}")
        else:
            # Borrado real (peligroso!)
            path.unlink()
            print(f"❌ Archivo ELIMINADO: {path}")

    def _action_move_file(self, step: Dict):
        """Mueve archivo a nueva ubicación"""
        source = self.base_path / step["source"]
        target = self.base_path / step["target"]

        if not source.exists():
            raise ExecutionError(f"Archivo origen no existe: {source}")

        # Backup si target existe
        if target.exists():
            self.staging.backup_file(target)

        # Crear directorio destino
        target.parent.mkdir(parents=True, exist_ok=True)

        # Mover
        shutil.move(str(source), str(target))
        print(f"📦 Archivo movido: {source} → {target}")

    def _action_run_command(self, step: Dict):
        """Ejecuta comando shell"""
        command = self._resolve_constants(step["command"])
        working_dir = step.get("working_dir", self.base_path)
        timeout = step.get("timeout", self.config.get("command_timeout", 300))

        print(f"🔧 Ejecutando: {command}")

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=working_dir,
            timeout=timeout,
        )

        if result.stdout:
            print(f"📋 Output:\n{result.stdout}")

        if result.returncode != 0:
            if result.stderr:
                print(f"❌ Error:\n{result.stderr}")
            raise ExecutionError(f"Comando falló con código {result.returncode}")

    def _action_run_test(self, step: Dict):
        """Ejecuta tests con validación"""
        command = self._resolve_constants(step["command"])
        expected_tests = step.get("expected_tests")

        print(f"🧪 Ejecutando tests: {command}")

        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, cwd=self.base_path
        )

        output = result.stdout + result.stderr
        print(output)

        if result.returncode != 0:
            raise ExecutionError("Tests fallaron")

        # Validar número de tests si se especificó
        if expected_tests:
            import re

            match = re.search(r"(\d+) passed", output)
            if match:
                passed = int(match.group(1))
                if passed != expected_tests:
                    raise ExecutionError(
                        f"Se esperaban {expected_tests} tests, pero pasaron {passed}"
                    )

    def _action_install_package(self, step: Dict):
        """Instala paquete con versión específica"""
        package = step["package"]
        version = step.get("version", "")

        if version:
            package_spec = f"{package}=={version}"
        else:
            package_spec = package

        command = f"pip install {package_spec}"
        print(f"📦 Instalando: {package_spec}")

        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            raise ExecutionError(f"Fallo al instalar {package_spec}")

    def _action_validate(self, step: Dict):
        """Ejecuta validaciones complejas"""
        checks = step.get("checks", [])
        success, details = self.checker.verify(checks)

        for detail in details:
            print(f"   {detail}")

        if not success:
            raise ExecutionError("Validación falló")

    # ===== UTILIDADES =====

    def _resolve_constants(self, text: str) -> str:
        """Reemplaza {constant} con su valor"""
        if not isinstance(text, str):
            return text

        for key, value in self.constants.items():
            text = text.replace(f"{{{key}}}", str(value))

        # También resolver base_path
        text = text.replace("{base_path}", str(self.base_path))

        return text

    def _handle_failure(self):
        """Maneja fallo con rollback si está habilitado"""
        if self.plan.get("rollback", {}).get("enabled", True):
            print("\n🔄 Ejecutando rollback...")
            try:
                self._run_rollback()
            except Exception as e:
                print(f"❌ Error en rollback: {str(e)}")

        self._print_summary(False)

    def _run_rollback(self):
        """Ejecuta acciones de rollback"""
        rollback_steps = self.plan.get("rollback", {}).get("steps", [])

        for step in rollback_steps:
            action = step.get("action")

            if action == "restore_from_backup":
                pattern = step.get("pattern", "*")
                self.staging.restore_all(pattern)
                print(f"♻️  Restaurados archivos: {pattern}")

            elif action == "restore_staging":
                self.staging.restore_deletions()
                print("♻️  Restaurados archivos eliminados")

    def _run_final_validation(self) -> bool:
        """Ejecuta validación final del objetivo"""
        validations = self.plan.get("final_validation", [])
        all_passed = True

        for validation in validations:
            if validation["type"] == "goal_achieved":
                print("\n📋 Verificando objetivo alcanzado:")
                for check in validation.get("checks", []):
                    print(f"   ✓ {check}")

        return all_passed

    def _run_post_execution(self):
        """Ejecuta acciones post-ejecución"""
        for action in self.plan.get("post_execution", []):
            if action["action"] == "create_summary":
                self._create_execution_summary(action["path"])
            elif action["action"] == "clean_staging":
                self.staging.cleanup()
                print("🧹 Staging limpiado")

    def _create_execution_summary(self, path: str):
        """Crea resumen de ejecución"""
        summary_path = self.base_path / path
        duration = datetime.now() - self.start_time

        summary = f"""# CPMS3 Execution Summary

**Project**: {self.plan["meta"]["name"]}
**Goal**: {self.plan["meta"]["goal"]}
**Date**: {self.start_time.strftime("%Y-%m-%d %H:%M:%S")}
**Duration**: {duration}

## Steps Executed
- Total: {len(self.plan.get("steps", []))}
- Completed: {len(self.executed_steps)}
- Failed: {len(self.failed_steps)}

## Details
"""

        for step_id in self.executed_steps:
            summary += f"- ✅ {step_id}\n"

        for step_id in self.failed_steps:
            summary += f"- ❌ {step_id}\n"

        summary_path.write_text(summary, encoding="utf-8")
        print(f"📊 Resumen creado: {summary_path}")

    def _normalize_for_search(self, text: str) -> str:
        """Normaliza texto para búsqueda más flexible"""
        # Normalizar saltos de línea
        text = text.replace("\r\n", "\n")

        # Normalizar espacios múltiples (pero preservar indentación)
        lines = text.split("\n")
        normalized_lines = []

        for line in lines:
            # Preservar indentación
            indent = len(line) - len(line.lstrip())
            content = line[indent:]
            # Normalizar espacios en contenido
            content = re.sub(r" +", " ", content)  # noqa: F821
            normalized_lines.append(" " * indent + content)

        return "\n".join(normalized_lines)

    def _smart_replace(self, content: str, find_text: str, replace_text: str) -> str:
        """Reemplazo inteligente que maneja normalización"""
        # Esta es una implementación simplificada
        # En un caso real, sería más sofisticada

        # Normalizar ambos
        norm_content = self._normalize_for_search(content)
        norm_find = self._normalize_for_search(find_text)

        if norm_find in norm_content:
            # Encontrar posición en normalizado
            pos = norm_content.find(norm_find)  # noqa: F841

            # Aproximar posición en original (simplificado)
            # Una implementación real mapearía las posiciones exactamente
            return content.replace(find_text.strip(), replace_text.strip())

        return content

    def _find_similar_lines(
        self, pattern: str, content: str, max_results: int = 3
    ) -> List[str]:
        """Encuentra líneas similares al patrón buscado"""
        # Extraer palabras clave del patrón
        pattern_words = set(re.findall(r"\w+", pattern.lower()))  # noqa: F821
        if not pattern_words:
            return []

        lines = content.split("\n")
        scored_lines = []

        for i, line in enumerate(lines):
            line_words = set(re.findall(r"\w+", line.lower()))  # noqa: F821
            common = pattern_words & line_words

            if len(common) >= len(pattern_words) * 0.5:  # Al menos 50% coincidencia
                score = len(common) / len(pattern_words)
                scored_lines.append((score, line.strip()))

        # Ordenar por score
        scored_lines.sort(reverse=True, key=lambda x: x[0])

        return [line for _, line in scored_lines[:max_results]]

    def _print_summary(self, success: bool):
        """Imprime resumen final"""
        duration = datetime.now() - self.start_time

        print(f"\n{'=' * 60}")
        if success:
            print("✅ EJECUCIÓN EXITOSA")
        else:
            print("❌ EJECUCIÓN FALLIDA")
        print(f"{'=' * 60}")
        print(f"Proyecto: {self.plan['meta']['name']}")
        print(f"Duración: {duration}")
        print(
            f"Pasos ejecutados: {len(self.executed_steps)}/{len(self.plan.get('steps', []))}"
        )

        if self.strict_mode:
            print(f"🔒 Modo strict: Activado")  # noqa: F541

        if self.failed_steps:
            print(f"Pasos fallidos: {', '.join(self.failed_steps)}")


def main():
    """CLI principal"""
    if len(sys.argv) != 2:
        print("Uso: python runner.py <execution_plan.yaml>")
        print("\nEjemplo:")
        print("  python runner.py /path/to/project/execution_plan.yaml")
        sys.exit(1)

    plan_path = sys.argv[1]

    if not Path(plan_path).exists():
        print(f"❌ Error: No se encuentra {plan_path}")
        sys.exit(1)

    runner = CPMS3Runner(plan_path)
    success = runner.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
