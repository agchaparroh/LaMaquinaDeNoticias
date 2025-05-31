#!/usr/bin/env python3
"""
Script automatizado para probar scrapy-crawl-once.
Ejecuta el spider dos veces para verificar que los duplicados son bloqueados.
"""

import subprocess
import sys
import os
import time
import json
from pathlib import Path

def run_spider(second_run=False):
    """
    Ejecuta el spider de prueba de crawl-once.
    """
    run_type = "segundo" if second_run else "primer"
    print(f"🕷️  Ejecutando {run_type} run del spider...")
    
    # Cambiar al directorio del proyecto
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Comando para ejecutar el spider
    cmd = [
        sys.executable, "-m", "scrapy", "crawl", "crawl_once_test",
        "-s", "LOG_LEVEL=INFO",
        "-s", "HTTPCACHE_ENABLED=False",  # Deshabilitar cache para este test
    ]
    
    # Agregar parámetro para segundo run
    if second_run:
        cmd.extend(["-a", "second_run=true"])
    
    # Archivo de salida
    output_file = f"crawl_once_test_run{'2' if second_run else '1'}.json"
    cmd.extend(["-o", output_file])
    
    try:
        print(f"Ejecutando: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # Timeout de 1 minuto
        )
        
        print(f"\\n📄 LOGS DEL {run_type.upper()} RUN:")
        print("=" * 50)
        print(result.stdout)
        
        if result.stderr:
            print(f"\\n⚠️  STDERR del {run_type} run:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"\\n✅ {run_type.capitalize()} run completado exitosamente")
            return True, output_file
        else:
            print(f"\\n❌ Error en {run_type} run. Código: {result.returncode}")
            return False, None
            
    except subprocess.TimeoutExpired:
        print(f"\\n⏰ Timeout en {run_type} run")
        return False, None
    except Exception as e:
        print(f"\\n❌ Error inesperado en {run_type} run: {e}")
        return False, None

def analyze_results(run1_file, run2_file):
    """
    Analiza los resultados de ambos runs para verificar el comportamiento.
    """
    print("\\n📊 ANÁLISIS DE RESULTADOS:")
    print("=" * 50)
    
    try:
        # Leer resultados del primer run
        run1_data = []
        if run1_file and Path(run1_file).exists():
            with open(run1_file, 'r') as f:
                run1_data = json.load(f)
        
        # Leer resultados del segundo run
        run2_data = []
        if run2_file and Path(run2_file).exists():
            with open(run2_file, 'r') as f:
                run2_data = json.load(f)
        
        print(f"📈 Primer run: {len(run1_data)} items procesados")
        print(f"📈 Segundo run: {len(run2_data)} items procesados")
        
        # Analizar primer run
        if run1_data:
            run1_normal = [item for item in run1_data if item.get('test_type') == 'normal']
            run1_crawl_once = [item for item in run1_data if item.get('test_type') == 'crawl_once']
            
            print(f"\\n🔍 PRIMER RUN (baseline):")
            print(f"   Normal requests: {len(run1_normal)}")
            print(f"   Crawl-once requests: {len(run1_crawl_once)}")
        
        # Analizar segundo run
        if run2_data:
            run2_normal = [item for item in run2_data if item.get('test_type') == 'normal']
            run2_crawl_once = [item for item in run2_data if item.get('test_type') == 'crawl_once']
            
            print(f"\\n🔍 SEGUNDO RUN (test de duplicados):")
            print(f"   Normal requests: {len(run2_normal)}")
            print(f"   Crawl-once requests: {len(run2_crawl_once)}")
            
            # Verificar comportamiento esperado
            if len(run2_normal) > 0 and len(run2_crawl_once) == 0:
                print(f"\\n✅ ¡ÉXITO! scrapy-crawl-once funciona correctamente:")
                print(f"   ✓ Requests normales procesados: {len(run2_normal)}")
                print(f"   ✓ Requests crawl-once bloqueados: {len(run2_crawl_once)} (esperado: 0)")
                return True
            elif len(run2_crawl_once) > 0:
                print(f"\\n❌ FALLO: scrapy-crawl-once NO está bloqueando duplicados")
                print(f"   ✗ {len(run2_crawl_once)} requests crawl-once fueron procesados (deberían ser 0)")
                return False
            else:
                print(f"\\n⚠️  ADVERTENCIA: No se procesaron requests normales en el segundo run")
                return False
        else:
            print(f"\\n⚠️  No hay datos del segundo run para analizar")
            return False
            
    except json.JSONDecodeError as e:
        print(f"\\n❌ Error al parsear archivos JSON: {e}")
        return False
    except Exception as e:
        print(f"\\n❌ Error al analizar resultados: {e}")
        return False

def cleanup_files(*files):
    """
    Limpia archivos de test.
    """
    for file in files:
        if file and Path(file).exists():
            try:
                Path(file).unlink()
                print(f"🧹 Limpiado: {file}")
            except Exception as e:
                print(f"⚠️  No se pudo limpiar {file}: {e}")

def check_crawl_once_database():
    """
    Verifica que se haya creado la base de datos de crawl_once.
    """
    project_root = Path(__file__).parent.parent
    db_dir = project_root / '.scrapy' / 'crawl_once'
    
    print(f"\\n🗃️  VERIFICACIÓN DE BASE DE DATOS:")
    print(f"Directorio esperado: {db_dir}")
    
    if db_dir.exists():
        db_files = list(db_dir.glob('*.sqlite'))
        print(f"✅ Directorio existe con {len(db_files)} archivos SQLite")
        for db_file in db_files:
            print(f"   📁 {db_file.name} ({db_file.stat().st_size} bytes)")
        return True
    else:
        print(f"❌ Directorio de base de datos no encontrado")
        return False

def main():
    """
    Función principal del test automatizado.
    """
    print("🕷️  TEST AUTOMATIZADO DE SCRAPY-CRAWL-ONCE")
    print("=" * 60)
    print("Este test ejecuta el spider dos veces para verificar")
    print("que los requests marcados con crawl_once=True son")
    print("bloqueados en ejecuciones subsecuentes.")
    print()
    
    # Ejecutar primer run
    print("🚀 FASE 1: Primer run (baseline)")
    print("-" * 30)
    success1, file1 = run_spider(second_run=False)
    
    if not success1:
        print("❌ Primer run falló. Abortando test.")
        return False
    
    # Pequeña pausa entre runs
    print("\\n⏳ Esperando 2 segundos entre runs...")
    time.sleep(2)
    
    # Ejecutar segundo run
    print("\\n🚀 FASE 2: Segundo run (test de duplicados)")
    print("-" * 30)
    success2, file2 = run_spider(second_run=True)
    
    if not success2:
        print("❌ Segundo run falló.")
        cleanup_files(file1)
        return False
    
    # Analizar resultados
    success = analyze_results(file1, file2)
    
    # Verificar base de datos
    check_crawl_once_database()
    
    # Limpiar archivos de test
    print("\\n🧹 LIMPIEZA:")
    cleanup_files(file1, file2)
    
    # Reporte final
    print("\\n" + "=" * 60)
    if success:
        print("🎉 TEST EXITOSO: scrapy-crawl-once funciona correctamente!")
        print("   Los requests duplicados están siendo bloqueados.")
    else:
        print("❌ TEST FALLÓ: Hay problemas con la configuración.")
        print("   Revisa los logs arriba para más detalles.")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
