#!/usr/bin/env python3
"""
Script de prueba para la configuración centralizada
==================================================

Verifica que todas las variables de configuración se cargan correctamente
y que la validación funciona como esperado.
"""

import sys
import os
from pathlib import Path

# Añadir src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_configuration():
    """Prueba la configuración centralizada."""
    print("🧪 TESTING CONFIGURACIÓN CENTRALIZADA")
    print("=" * 50)
    
    try:
        # Importar configuración
        print("📦 Importando módulo de configuración...")
        from utils.config import (
            # Variables críticas
            GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY,
            # Configuración de servidor
            API_HOST, API_PORT, DEBUG_MODE,
            # Funciones de utilidad
            get_groq_config, get_supabase_config, get_server_config,
            validate_configuration, print_configuration_summary
        )
        print("✅ Importación exitosa")
        
        # Mostrar resumen de configuración
        print("\n📋 Resumen de configuración:")
        print_configuration_summary()
        
        # Validar configuración
        print("\n🔍 Validando configuración...")
        is_valid = validate_configuration()
        
        if is_valid:
            print("✅ Configuración válida")
        else:
            print("❌ Configuración inválida")
            return False
        
        # Probar funciones de configuración
        print("\n🔧 Probando funciones de configuración...")
        
        groq_config = get_groq_config()
        print(f"✅ Groq config: modelo={groq_config['model_id']}, timeout={groq_config['timeout']}s")
        
        supabase_config = get_supabase_config()
        print(f"✅ Supabase config: URL configurada, pool_size={supabase_config['pool_size']}")
        
        server_config = get_server_config()
        print(f"✅ Server config: {server_config['host']}:{server_config['port']}, workers={server_config['workers']}")
        
        # Verificar variables críticas (sin mostrar valores completos por seguridad)
        print("\n🔑 Verificando variables críticas:")
        
        if GROQ_API_KEY:
            print(f"✅ GROQ_API_KEY: {GROQ_API_KEY[:8]}...{GROQ_API_KEY[-4:]}")
        else:
            print("❌ GROQ_API_KEY no configurada")
            return False
            
        if SUPABASE_URL:
            print(f"✅ SUPABASE_URL: {SUPABASE_URL}")
        else:
            print("❌ SUPABASE_URL no configurada")
            return False
            
        if SUPABASE_KEY:
            print(f"✅ SUPABASE_KEY: {SUPABASE_KEY[:8]}...{SUPABASE_KEY[-4:]}")
        else:
            print("❌ SUPABASE_KEY no configurada")
            return False
        
        print("\n🎉 ¡Todas las pruebas de configuración exitosas!")
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_environment_variables():
    """Prueba que las variables de entorno se están leyendo correctamente."""
    print("\n🌍 TESTING VARIABLES DE ENTORNO")
    print("=" * 40)
    
    critical_vars = ['GROQ_API_KEY', 'SUPABASE_URL', 'SUPABASE_KEY']
    optional_vars = ['API_HOST', 'API_PORT', 'DEBUG_MODE', 'LOG_LEVEL']
    
    print("Variables críticas:")
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: configurada")
        else:
            print(f"❌ {var}: NO configurada")
    
    print("\nVariables opcionales:")
    for var in optional_vars:
        value = os.getenv(var)
        print(f"{'✅' if value else 'ℹ️ '} {var}: {value or 'default'}")

def main():
    """Función principal de testing."""
    success = True
    
    # Test 1: Variables de entorno
    test_environment_variables()
    
    # Test 2: Configuración centralizada
    config_success = test_configuration()
    success = success and config_success
    
    # Resultado final
    print("\n" + "=" * 50)
    print("📊 RESULTADO FINAL")
    print("=" * 50)
    
    if success:
        print("🎉 ¡Configuración centralizada funcionando correctamente!")
        print("\n📝 Próximos pasos:")
        print("1. Proceder con implementación de modelos Pydantic")
        print("2. Configurar servicios de integración (Groq, Supabase)")
        print("3. Implementar fases del pipeline")
        return 0
    else:
        print("❌ Problemas detectados en la configuración")
        print("\n🔧 Acciones requeridas:")
        print("1. Verificar variables de entorno en .env")
        print("2. Revisar estructura de directorios")
        print("3. Corregir errores reportados arriba")
        return 1

if __name__ == "__main__":
    sys.exit(main())
