#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ScrapydWeb Wrapper for La Máquina de Noticias
Soluciona el problema de permisos creando los directorios necesarios antes de importar ScrapydWeb
"""
import os
import sys
import site

def setup_scrapydweb_directories():
    """
    Crea los directorios que ScrapydWeb espera encontrar en su ubicación de instalación.
    Esto es necesario porque ScrapydWeb intenta crear estos directorios durante la importación
    del módulo, antes de leer cualquier configuración.
    """
    # Obtener la ubicación de site-packages
    site_packages = site.getsitepackages()[0]
    scrapydweb_data_dir = os.path.join(site_packages, 'scrapydweb', 'data')
    
    # Directorios que ScrapydWeb intenta crear
    directories = [
        scrapydweb_data_dir,
        os.path.join(scrapydweb_data_dir, 'database'),
        os.path.join(scrapydweb_data_dir, 'logs'),
    ]
    
    # Crear directorios si no existen
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✓ Directorio creado/verificado: {directory}")
        except Exception as e:
            print(f"✗ Error creando directorio {directory}: {e}")
            # Intentar continuar de todos modos
    
    # Verificar permisos
    for directory in directories:
        if os.path.exists(directory):
            print(f"  Permisos de {directory}: {oct(os.stat(directory).st_mode)[-3:]}")

def main():
    """
    Punto de entrada principal del wrapper
    """
    print("=== ScrapydWeb Wrapper ===")
    print("Configurando entorno...")
    
    # Configurar directorios antes de importar ScrapydWeb
    setup_scrapydweb_directories()
    
    # Configurar variables de entorno si no están establecidas
    if 'SCRAPYDWEB_SETTINGS_PY' not in os.environ:
        os.environ['SCRAPYDWEB_SETTINGS_PY'] = '/app/config/scrapydweb_settings_v10.py'
    
    # IMPORTANTE: Cambiar al directorio /app para que ScrapydWeb encuentre el archivo de configuración
    os.chdir('/app')
    
    # Verificar si existe nuestro archivo de configuración
    config_file = os.environ.get('SCRAPYDWEB_SETTINGS_PY', '/app/config/scrapydweb_settings_v10.py')
    if os.path.exists(config_file):
        print(f"Archivo de configuración encontrado: {config_file}")
    else:
        print(f"ADVERTENCIA: No se encontró el archivo de configuración: {config_file}")
    
    print("Iniciando ScrapydWeb...")
    print("=" * 25)
    
    # Ahora es seguro importar y ejecutar ScrapydWeb
    try:
        # Agregar argumentos de línea de comandos para ScrapydWeb
        sys.argv = [
            'scrapydweb',
            '--bind', os.environ.get('SCRAPYDWEB_BIND', '0.0.0.0'),
            '--port', os.environ.get('SCRAPYDWEB_PORT', '5000'),
            '-ss', 'scrapyd:6800',  # Usar -ss en lugar de --scrapyd_server
        ]
        
        from scrapydweb.run import main as scrapydweb_main
        sys.exit(scrapydweb_main())
    except ImportError as e:
        print(f"Error importando ScrapydWeb: {e}")
        print("Asegúrate de que ScrapydWeb esté instalado: pip install scrapydweb")
        sys.exit(1)
    except Exception as e:
        print(f"Error ejecutando ScrapydWeb: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()