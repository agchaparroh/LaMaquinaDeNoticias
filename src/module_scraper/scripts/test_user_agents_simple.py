#!/usr/bin/env python3
"""
Script simplificado para probar scrapy-user-agents sin dependencias de Supabase.
Solo verifica la rotación de user agents.
"""

import subprocess
import sys
import os
import json
from pathlib import Path

def run_simplified_user_agent_test():
    """
    Ejecuta una versión simplificada del test de user agents.
    """
    print("🔍 Iniciando prueba simplificada de rotación de user agents...")
    print("=" * 60)
    
    # Cambiar al directorio del proyecto
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Comando para ejecutar el spider con configuración simplificada
    cmd = [
        sys.executable, "-m", "scrapy", "crawl", "useragent_test",
        "-s", "LOG_LEVEL=INFO",
        "-s", "HTTPCACHE_ENABLED=False",
        "-s", "ITEM_PIPELINES={}",  # Deshabilitar todas las pipelines
        "-o", "test_results.json"
    ]
    
    try:
        print("Ejecutando comando:")
        print(f"  {' '.join(cmd)}")
        print()
        
        # Ejecutar el spider
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # Timeout de 1 minuto
        )
        
        print("📄 LOGS DEL SPIDER:")
        print("=" * 40)
        print(result.stdout)
        
        if result.stderr:
            print("\n⚠️  STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✅ Spider ejecutado exitosamente!")
            analyze_results()
            return True
        else:
            print(f"\n❌ Error al ejecutar spider. Código de salida: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n⏰ Timeout: El spider tardó más de 1 minuto")
        return False
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        return False

def analyze_results():
    """
    Analiza los resultados del test guardados en JSON.
    """
    results_file = Path("test_results.json")
    
    if not results_file.exists():
        print("\n⚠️  Archivo de resultados no encontrado.")
        return
    
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        if not results:
            print("\n⚠️  No se encontraron resultados.")
            return
        
        print("\n📊 ANÁLISIS DE RESULTADOS:")
        print("=" * 40)
        
        # Extraer user agents únicos
        user_agents = set()
        for item in results:
            if 'user_agent' in item and item['user_agent'] != 'PARSE_ERROR':
                user_agents.add(item['user_agent'])
        
        print(f"Total de requests: {len(results)}")
        print(f"User agents únicos detectados: {len(user_agents)}")
        
        if len(user_agents) >= 3:
            print("\n✅ ÉXITO: La rotación de user agents funciona correctamente!")
        elif len(user_agents) == 1:
            print("\n❌ FALLO: No se detectó rotación de user agents")
        else:
            print("\n⚠️  ADVERTENCIA: Rotación limitada de user agents")
        
        print("\nUser agents utilizados:")
        for i, ua in enumerate(sorted(user_agents), 1):
            # Mostrar solo los primeros 80 caracteres para legibilidad
            ua_short = ua[:80] + '...' if len(ua) > 80 else ua
            print(f"  {i}. {ua_short}")
        
        # Limpiar archivo de resultados
        results_file.unlink()
        print(f"\n🧹 Archivo de resultados limpiado: {results_file}")
        
    except json.JSONDecodeError:
        print("\n❌ Error al parsear el archivo de resultados JSON")
    except Exception as e:
        print(f"\n❌ Error al analizar resultados: {e}")

def main():
    """Función principal"""
    print("🕷️  SCRAPY USER AGENT ROTATION TEST (SIMPLIFICADO)")
    print("=" * 60)
    print("Este script prueba la rotación de user agents sin dependencias")
    print("de Supabase o pipelines de almacenamiento.")
    print()
    
    success = run_simplified_user_agent_test()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Test completado.")
    else:
        print("❌ Test falló.")
    print("=" * 60)

if __name__ == "__main__":
    main()
