#!/usr/bin/env python3
"""
CPMS3 Staging Manager - Gestión Segura de Cambios
Maneja backups y staging para operaciones peligrosas.
"""

import json
import os  # noqa: F401
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional  # noqa: F401


class StagingManager:
    def __init__(self, base_path: Path, staging_dir: str = ".cpms3_staging"):
        self.base_path = Path(base_path)
        self.staging_root = self.base_path / staging_dir

        # Subdirectorios de staging
        self.backup_dir = self.staging_root / "backups"
        self.deleted_dir = self.staging_root / "deleted"
        self.temp_dir = self.staging_root / "temp"

        # Crear estructura
        self._init_staging()

        # Registro de operaciones
        self.manifest_file = self.staging_root / "manifest.json"
        self.manifest = self._load_manifest()

    def _init_staging(self):
        """Inicializa estructura de staging"""
        for dir_path in [self.backup_dir, self.deleted_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _load_manifest(self) -> Dict:
        """Carga manifest de operaciones"""
        if self.manifest_file.exists():
            with open(self.manifest_file) as f:
                return json.load(f)
        return {"backups": {}, "deletions": {}, "operations": []}

    def _save_manifest(self):
        """Guarda manifest"""
        with open(self.manifest_file, "w") as f:
            json.dump(self.manifest, f, indent=2)

    def backup_file(self, file_path: Path) -> Path:
        """Crea backup de un archivo"""
        file_path = Path(file_path)
        if not file_path.exists():
            return None

        # Generar nombre único para backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        relative_path = file_path.relative_to(self.base_path)
        backup_name = f"{timestamp}_{relative_path.name}"
        backup_path = self.backup_dir / relative_path.parent / backup_name

        # Crear directorio si no existe
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        # Copiar archivo
        shutil.copy2(file_path, backup_path)

        # Registrar en manifest
        self.manifest["backups"][str(file_path)] = {
            "original": str(file_path),
            "backup": str(backup_path),
            "timestamp": timestamp,
        }
        self._save_manifest()

        return backup_path

    def stage_deletion(self, file_path: Path) -> Path:
        """Mueve archivo a staging en vez de borrarlo"""
        file_path = Path(file_path)
        if not file_path.exists():
            return None

        # Generar path en staging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        relative_path = file_path.relative_to(self.base_path)
        staged_name = f"{timestamp}_{relative_path.name}"
        staged_path = self.deleted_dir / relative_path.parent / staged_name

        # Crear directorio si no existe
        staged_path.parent.mkdir(parents=True, exist_ok=True)

        # Mover archivo
        shutil.move(str(file_path), str(staged_path))

        # Registrar en manifest
        self.manifest["deletions"][str(file_path)] = {
            "original": str(file_path),
            "staged": str(staged_path),
            "timestamp": timestamp,
        }
        self._save_manifest()

        return staged_path

    def restore_file(self, original_path: str) -> bool:
        """Restaura un archivo desde backup"""
        if original_path not in self.manifest["backups"]:
            return False

        backup_info = self.manifest["backups"][original_path]
        backup_path = Path(backup_info["backup"])
        original = Path(backup_info["original"])

        if not backup_path.exists():
            return False

        # Restaurar
        shutil.copy2(backup_path, original)

        # Log operación
        self.manifest["operations"].append(
            {
                "type": "restore_backup",
                "file": original_path,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._save_manifest()

        return True

    def restore_deletion(self, original_path: str) -> bool:
        """Restaura un archivo eliminado desde staging"""
        if original_path not in self.manifest["deletions"]:
            return False

        deletion_info = self.manifest["deletions"][original_path]
        staged_path = Path(deletion_info["staged"])
        original = Path(deletion_info["original"])

        if not staged_path.exists():
            return False

        # Crear directorio si no existe
        original.parent.mkdir(parents=True, exist_ok=True)

        # Restaurar
        shutil.move(str(staged_path), str(original))

        # Eliminar del manifest
        del self.manifest["deletions"][original_path]

        # Log operación
        self.manifest["operations"].append(
            {
                "type": "restore_deletion",
                "file": original_path,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._save_manifest()

        return True

    def restore_all(self, pattern: str = "*") -> int:
        """Restaura todos los backups que coincidan con patrón"""
        import fnmatch

        restored = 0

        for original_path in list(self.manifest["backups"].keys()):
            if fnmatch.fnmatch(original_path, pattern):
                if self.restore_file(original_path):
                    restored += 1

        return restored

    def restore_deletions(self, pattern: str = "*") -> int:
        """Restaura todos los archivos eliminados que coincidan"""
        import fnmatch

        restored = 0

        for original_path in list(self.manifest["deletions"].keys()):
            if fnmatch.fnmatch(original_path, pattern):
                if self.restore_deletion(original_path):
                    restored += 1

        return restored

    def create_temp_file(self, content: str, suffix: str = ".tmp") -> Path:
        """Crea archivo temporal en staging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        temp_file = self.temp_dir / f"temp_{timestamp}{suffix}"
        temp_file.write_text(content, encoding="utf-8")
        return temp_file

    def cleanup(self, keep_backups: bool = False):
        """Limpia el staging"""
        # Limpiar temporales siempre
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir.mkdir()

        # Limpiar otros si se indica
        if not keep_backups:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
                self.backup_dir.mkdir()

            if self.deleted_dir.exists():
                shutil.rmtree(self.deleted_dir)
                self.deleted_dir.mkdir()

            # Limpiar manifest
            self.manifest = {"backups": {}, "deletions": {}, "operations": []}
            self._save_manifest()

    def get_status(self) -> Dict:
        """Obtiene estado del staging"""
        return {
            "backups": len(self.manifest["backups"]),
            "deletions": len(self.manifest["deletions"]),
            "operations": len(self.manifest["operations"]),
            "size": self._get_dir_size(self.staging_root),
        }

    def _get_dir_size(self, path: Path) -> int:
        """Calcula tamaño de directorio en bytes"""
        total = 0
        for entry in path.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
        return total

    def list_backups(self) -> List[Dict]:
        """Lista todos los backups"""
        backups = []
        for original, info in self.manifest["backups"].items():
            backups.append(
                {
                    "original": original,
                    "backup": info["backup"],
                    "timestamp": info["timestamp"],
                    "exists": Path(info["backup"]).exists(),
                }
            )
        return backups

    def list_deletions(self) -> List[Dict]:
        """Lista todos los archivos en deletion staging"""
        deletions = []
        for original, info in self.manifest["deletions"].items():
            deletions.append(
                {
                    "original": original,
                    "staged": info["staged"],
                    "timestamp": info["timestamp"],
                    "exists": Path(info["staged"]).exists(),
                }
            )
        return deletions


def main():
    """CLI para testing"""
    import sys

    if len(sys.argv) < 2:
        print("Uso: python staging.py <comando> [args]")
        print("\nComandos:")
        print("  status <base_path>")
        print("  list-backups <base_path>")
        print("  list-deletions <base_path>")
        print("  cleanup <base_path>")
        sys.exit(1)

    command = sys.argv[1]
    base_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()

    staging = StagingManager(base_path)

    if command == "status":
        status = staging.get_status()
        print(f"Staging Status:")  # noqa: F541
        print(f"  Backups: {status['backups']}")
        print(f"  Deletions: {status['deletions']}")
        print(f"  Operations: {status['operations']}")
        print(f"  Size: {status['size'] / 1024:.2f} KB")

    elif command == "list-backups":
        backups = staging.list_backups()
        print(f"Backups ({len(backups)}):")
        for backup in backups:
            status = "✓" if backup["exists"] else "✗"
            print(f"  {status} {backup['original']} → {backup['backup']}")

    elif command == "list-deletions":
        deletions = staging.list_deletions()
        print(f"Deletions ({len(deletions)}):")
        for deletion in deletions:
            status = "✓" if deletion["exists"] else "✗"
            print(f"  {status} {deletion['original']} → {deletion['staged']}")

    elif command == "cleanup":
        staging.cleanup()
        print("Staging cleaned")

    else:
        print(f"Comando desconocido: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
