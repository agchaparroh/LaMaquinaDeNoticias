#!/usr/bin/env python3
"""
Verificación rápida de entorno Python para instalación de dependencias
"""
import sys
import os
from pathlib import Path

print("🐍 Verificación de Entorno Python")
print("=" * 40)

# Verificar versión de Python
print(f"Versión de Python: {sys.version}")
version_info = sys.version_info
if version_info.major >= 3 and version_info.minor >= 8:
    print("✅ Versión de Python compatible (3.8+)")
else:
    print("❌ Python 3.8+ requerido")
    sys.exit(1)

# Verificar entorno virtual
in_venv = hasattr(sys, 'real_prefix') or (
    hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
)

if in_venv:
    print("✅ Entorno virtual detectado")
    print(f"   Prefix: {sys.prefix}")
else:
    print("⚠️ No se detectó entorno virtual")
    print("   Continuando instalación...")

# Verificar directorio actual
current_dir = Path.cwd()
print(f"📁 Directorio actual: {current_dir}")

# Verificar que requirements.txt existe
req_file = current_dir / "requirements.txt"
if req_file.exists():
    print(f"✅ requirements.txt encontrado ({req_file.stat().st_size} bytes)")
else:
    print("❌ requirements.txt no encontrado")
    sys.exit(1)

print("\n🚀 Entorno listo para instalación de dependencias")
