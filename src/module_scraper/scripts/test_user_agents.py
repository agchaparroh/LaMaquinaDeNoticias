#!/usr/bin/env python3
"""
Script para probar la funcionalidad de rotación de user agents
usando el spider useragent_test.

Ejecuta el spider y analiza los resultados para verificar que
scrapy-user-agents está funcionando correctamente.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_user_agent_test():
    """
    Ejecuta el spider de prueba de user agents y verifica los resultados.
    """
    print("🔍 Iniciando prueba de rotación de user agents...")
    print("=" * 60)
    
    # Cambiar al directorio del proyecto
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Comando para ejecutar el spider
    cmd = [
        sys.executable, "-m", "scrapy", "crawl", "useragent_test",
        "-s", "LOG_LEVEL=INFO",
        "-s", "HTTPCACHE_ENABLED=False",  # Deshabilitar cache para este test
        "-o", "test_results.json"  # Guardar resultados en JSON
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
            timeout=120  # Timeout de 2 minutos
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\\nSTDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\\n✅ Spider ejecutado exitosamente!")
            analyze_results()
        else:
            print(f"\\n❌ Error al ejecutar spider. Código de salida: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("\\n⏰ Timeout: El spider tardó más de 2 minutos en ejecutarse")
        return False
    except FileNotFoundError:
        print("\\n❌ Error: scrapy no encontrado. Asegúrate de que está instalado.")
        return False
    except Exception as e:
        print(f"\\n❌ Error inesperado: {e}")
        return False
    
    return True

def analyze_results():
    """
    Analiza los resultados del test guardados en JSON.
    """
    results_file = Path("test_results.json")
    
    if not results_file.exists():
        print("\\n⚠️  Archivo de resultados no encontrado.")
        return
    
    try:
        import json
        
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        if not results:
            print("\\n⚠️  No se encontraron resultados en el archivo.")
            return
        
        print("\\n📊 ANÁLISIS DE RESULTADOS:")
        print("=" * 40)
        
        # Extraer user agents únicos
        user_agents = set()
        for item in results:
            if 'user_agent' in item and item['user_agent'] != 'PARSE_ERROR':
                user_agents.add(item['user_agent'])
        
        print(f"Total de requests: {len(results)}")
        print(f"User agents únicos: {len(user_agents)}")
        
        if len(user_agents) >= 3:
            print("\\n✅ ÉXITO: La rotación de user agents funciona correctamente!")
        elif len(user_agents) == 1:
            print("\\n❌ FALLO: No se detectó rotación de user agents")
        else:
            print("\\n⚠️  ADVERTENCIA: Rotación limitada de user agents")
        
        print("\\nUser agents utilizados:")
        for i, ua in enumerate(sorted(user_agents), 1):
            print(f"  {i}. {ua}")
        
        # Limpiar archivo de resultados
        results_file.unlink()
        print(f"\\n🧹 Archivo de resultados limpiado: {results_file}")
        
    except json.JSONDecodeError:
        print("\\n❌ Error al parsear el archivo de resultados JSON")
    except Exception as e:
        print(f"\\n❌ Error al analizar resultados: {e}")

def main():
    """Función principal"""
    print("🕷️  SCRAPY USER AGENT ROTATION TEST")
    print("=" * 60)
    print("Este script prueba la configuración de scrapy-user-agents")
    print("ejecutando múltiples requests y verificando la rotación.")
    print()
    
    success = run_user_agent_test()
    
    print("\\n" + "=" * 60)
    if success:
        print("✅ Test completado.")
    else:
        print("❌ Test falló.")
    print("=" * 60)

if __name__ == "__main__":
    main()
