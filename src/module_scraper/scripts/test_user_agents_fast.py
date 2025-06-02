#!/usr/bin/env python3
"""
Script ultra-rápido para probar scrapy-user-agents.
Usa configuración optimizada para velocidad.
"""

import subprocess
import sys
import os
import json
from pathlib import Path

def run_fast_user_agent_test():
    """
    Ejecuta un test rápido de user agents con configuración optimizada.
    """
    print("🚀 Iniciando test RÁPIDO de rotación de user agents...")
    print("=" * 60)
    
    # Cambiar al directorio del proyecto
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Comando optimizado para velocidad
    cmd = [
        sys.executable, "-m", "scrapy", "crawl", "useragent_test",
        "-s", "LOG_LEVEL=WARNING",  # Menos logs para velocidad
        "-s", "HTTPCACHE_ENABLED=False",
        "-s", "ITEM_PIPELINES={}",  # Sin pipelines
        "-s", "DOWNLOAD_DELAY=0",   # Sin delay entre requests
        "-s", "RANDOMIZE_DOWNLOAD_DELAY=False",  # Sin delay aleatorio
        "-s", "CONCURRENT_REQUESTS=16",  # Más requests concurrentes
        "-s", "CONCURRENT_REQUESTS_PER_DOMAIN=8",  # Más concurrencia por dominio
        "-s", "DOWNLOAD_TIMEOUT=10",  # Timeout más corto
        "-s", "AUTOTHROTTLE_ENABLED=False",  # Deshabilitar auto-throttle
        "-s", "ROBOTSTXT_OBEY=False",  # Ignorar robots.txt para velocidad
        "-o", "test_results.json"
    ]
    
    try:
        print("Ejecutando comando optimizado para velocidad:")
        print(f"  {' '.join(cmd)}")
        print("\n⏱️  Ejecutando (timeout: 30 segundos)...")
        
        # Ejecutar con timeout más corto
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # Timeout de solo 30 segundos
        )
        
        if result.returncode == 0:
            print("✅ Spider ejecutado exitosamente!")
            analyze_results()
            return True
        else:
            print(f"❌ Error al ejecutar spider. Código: {result.returncode}")
            print("\n📄 STDOUT:")
            print(result.stdout[-1000:])  # Últimas 1000 chars
            print("\n⚠️  STDERR:")
            print(result.stderr[-1000:])  # Últimas 1000 chars
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout después de 30 segundos")
        print("❌ El test aún es demasiado lento. Verificando conectividad...")
        test_connectivity()
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_connectivity():
    """Test rápido de conectividad a httpbin.org"""
    print("\n🌐 Probando conectividad a httpbin.org...")
    try:
        import requests
        response = requests.get("https://httpbin.org/user-agent", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Conectividad OK. User-Agent detectado: {data.get('user-agent', 'Unknown')}")
        else:
            print(f"⚠️  Respuesta inesperada: {response.status_code}")
    except Exception as e:
        print(f"❌ Error de conectividad: {e}")
        print("💡 Sugerencia: Verificar conexión a internet o usar test offline")

def analyze_results():
    """Análisis rápido de resultados"""
    results_file = Path("test_results.json")
    
    if not results_file.exists():
        print("\n⚠️  Archivo de resultados no encontrado")
        return
    
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        if not results:
            print("\n⚠️  No se encontraron resultados")
            return
        
        print(f"\n📊 RESULTADOS RÁPIDOS:")
        print("=" * 30)
        
        user_agents = set()
        valid_results = 0
        
        for item in results:
            if 'user_agent' in item and item['user_agent'] != 'PARSE_ERROR':
                user_agents.add(item['user_agent'])
                valid_results += 1
        
        print(f"✅ Requests válidos: {valid_results}")
        print(f"✅ User agents únicos: {len(user_agents)}")
        
        # Resultado del test
        if len(user_agents) >= 3:
            print(f"\n🎉 ÉXITO: Rotación funcionando ({len(user_agents)} user agents distintos)")
            success_rate = len(user_agents) / valid_results * 100
            print(f"📈 Tasa de variación: {success_rate:.1f}%")
        elif len(user_agents) == 1:
            print(f"\n❌ FALLO: Sin rotación (solo 1 user agent)")
        else:
            print(f"\n⚠️  PARCIAL: Rotación limitada ({len(user_agents)} user agents)")
        
        # Limpiar archivo
        results_file.unlink()
        print(f"\n🧹 Resultados limpiados")
        
    except Exception as e:
        print(f"\n❌ Error en análisis: {e}")

def main():
    """Función principal optimizada"""
    print("🕷️  SCRAPY USER AGENT TEST (ULTRA-RÁPIDO)")
    print("=" * 50)
    print("Test optimizado para velocidad máxima")
    print()
    
    success = run_fast_user_agent_test()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Test completado exitosamente")
    else:
        print("❌ Test falló o fue muy lento")
        print("💡 Alternativa: Revisar configuración de red")
    print("=" * 50)

if __name__ == "__main__":
    main()
