"""
Verificador de Archivos de Log
==============================

Script para verificar y mostrar información sobre los archivos de log generados.
"""

import os
from pathlib import Path
from datetime import datetime

def verificar_logs():
    """Verifica y muestra información sobre los archivos de log."""
    # Obtener directorio de logs
    project_root = Path(__file__).resolve().parent.parent
    log_base = project_root / "logs"
    
    print("=== VERIFICACIÓN DE ARCHIVOS DE LOG ===\n")
    
    if not log_base.exists():
        print("❌ El directorio de logs no existe")
        return
    
    # Listar todos los entornos
    environments = [d for d in log_base.iterdir() if d.is_dir()]
    
    for env_dir in sorted(environments):
        print(f"📁 Entorno: {env_dir.name}")
        
        # Listar archivos de log
        log_files = list(env_dir.glob("*.log"))
        gz_files = list(env_dir.glob("*.log.gz"))
        
        if log_files or gz_files:
            # Archivos actuales
            if log_files:
                print("  📄 Archivos de log activos:")
                for file in sorted(log_files):
                    size = file.stat().st_size
                    modified = datetime.fromtimestamp(file.stat().st_mtime)
                    print(f"     - {file.name}")
                    print(f"       Tamaño: {size:,} bytes")
                    print(f"       Modificado: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Mostrar primeras líneas
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            print(f"       Total líneas: {len(lines)}")
                            if lines:
                                print(f"       Primera entrada: {lines[0].strip()[:80]}...")
                                print(f"       Última entrada: {lines[-1].strip()[:80]}...")
                    except Exception as e:
                        print(f"       Error leyendo archivo: {e}")
                    print()
            
            # Archivos comprimidos
            if gz_files:
                print("  🗜️  Archivos comprimidos:")
                for file in sorted(gz_files):
                    size = file.stat().st_size
                    print(f"     - {file.name} ({size:,} bytes)")
        else:
            print("  ⚠️  No hay archivos de log")
        
        print()
    
    # Estadísticas generales
    print("=== ESTADÍSTICAS GENERALES ===")
    total_logs = sum(len(list(env.glob("*.log"))) for env in environments)
    total_compressed = sum(len(list(env.glob("*.log.gz"))) for env in environments)
    total_size = sum(f.stat().st_size for env in environments for f in env.glob("*.log"))
    
    print(f"Total archivos activos: {total_logs}")
    print(f"Total archivos comprimidos: {total_compressed}")
    print(f"Tamaño total (activos): {total_size:,} bytes ({total_size/1024:.2f} KB)")
    
    # Verificar configuración
    print("\n=== CONFIGURACIÓN ACTUAL ===")
    from src.utils.logging_config import LoggingConfig
    
    env = LoggingConfig.get_environment()
    level = LoggingConfig.get_log_level()
    retention = LoggingConfig.get_retention_days()
    
    print(f"Entorno: {env}")
    print(f"Nivel de log: {level}")
    print(f"Retención: {retention} días")
    
    # Mostrar ejemplo de log reciente
    print("\n=== EJEMPLO DE ENTRADAS RECIENTES ===")
    
    today = datetime.now().strftime("%Y-%m-%d")
    current_log = log_base / env / f"pipeline_{today}.log"
    
    if current_log.exists():
        try:
            with open(current_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Mostrar últimas 5 líneas
                print(f"Últimas 5 entradas de {current_log.name}:")
                for line in lines[-5:]:
                    print(f"  {line.strip()}")
        except Exception as e:
            print(f"Error leyendo log actual: {e}")
    else:
        print("No hay log del día actual")


if __name__ == "__main__":
    verificar_logs()
