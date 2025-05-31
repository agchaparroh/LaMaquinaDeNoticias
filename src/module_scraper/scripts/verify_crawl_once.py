#!/usr/bin/env python3
"""
Script de verificación para scrapy-crawl-once
Verifica que la dependencia esté correctamente instalada y sea compatible.
"""

import sys
import subprocess
from pathlib import Path

def check_scrapy_crawl_once_installation():
    """
    Verifica que scrapy-crawl-once esté instalado correctamente.
    """
    print("🔍 Verificando instalación de scrapy-crawl-once...")
    print("=" * 60)
    
    try:
        # Intentar importar scrapy-crawl-once
        import scrapy_crawl_once
        print("✅ scrapy-crawl-once importado exitosamente")
        
        # Verificar versión
        try:
            version = scrapy_crawl_once.__version__
            print(f"📦 Versión instalada: {version}")
        except AttributeError:
            print("📦 Versión: No disponible (pero el paquete está instalado)")
        
        # Verificar componentes principales
        from scrapy_crawl_once.middleware import CrawlOnceMiddleware
        print("✅ CrawlOnceMiddleware importado correctamente")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error al importar scrapy-crawl-once: {e}")
        print("💡 Ejecuta: pip install scrapy-crawl-once")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def check_scrapy_compatibility():
    """
    Verifica compatibilidad con la versión actual de Scrapy.
    """
    try:
        import scrapy
        scrapy_version = scrapy.__version__
        print(f"🕷️  Scrapy versión: {scrapy_version}")
        
        # scrapy-crawl-once es compatible con Scrapy 2.x
        major_version = int(scrapy_version.split('.')[0])
        if major_version >= 2:
            print("✅ Versión de Scrapy compatible con scrapy-crawl-once")
            return True
        else:
            print("⚠️  Versión de Scrapy puede no ser compatible")
            return False
            
    except Exception as e:
        print(f"❌ Error al verificar compatibilidad: {e}")
        return False

def verify_requirements_file():
    """
    Verifica que scrapy-crawl-once esté en requirements.txt
    """
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    
    if not requirements_path.exists():
        print("❌ requirements.txt no encontrado")
        return False
    
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    if 'scrapy-crawl-once' in content:
        print("✅ scrapy-crawl-once está listado en requirements.txt")
        return True
    else:
        print("❌ scrapy-crawl-once NO está en requirements.txt")
        return False

def install_if_missing():
    """
    Instala scrapy-crawl-once si no está disponible.
    """
    print("\\n🔧 Intentando instalar scrapy-crawl-once...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "scrapy-crawl-once"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ scrapy-crawl-once instalado exitosamente")
            return True
        else:
            print(f"❌ Error en instalación: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout durante la instalación")
        return False
    except Exception as e:
        print(f"❌ Error durante instalación: {e}")
        return False

def main():
    """Función principal de verificación"""
    print("🕷️  VERIFICACIÓN DE SCRAPY-CRAWL-ONCE")
    print("=" * 60)
    
    # Verificar requirements.txt
    req_ok = verify_requirements_file()
    
    # Verificar instalación
    install_ok = check_scrapy_crawl_once_installation()
    
    if not install_ok:
        print("\\n🔧 Dependencia no encontrada. Intentando instalar...")
        install_ok = install_if_missing()
        if install_ok:
            install_ok = check_scrapy_crawl_once_installation()
    
    # Verificar compatibilidad
    compat_ok = check_scrapy_compatibility()
    
    print("\\n" + "=" * 60)
    print("📋 RESUMEN DE VERIFICACIÓN:")
    print(f"   Requirements.txt: {'✅' if req_ok else '❌'}")
    print(f"   Instalación: {'✅' if install_ok else '❌'}")
    print(f"   Compatibilidad: {'✅' if compat_ok else '❌'}")
    
    if req_ok and install_ok and compat_ok:
        print("\\n🎉 scrapy-crawl-once está listo para usar!")
        return True
    else:
        print("\\n⚠️  Se encontraron problemas. Revisa los errores arriba.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
