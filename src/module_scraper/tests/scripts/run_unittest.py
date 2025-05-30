#!/usr/bin/env python
"""
Script alternativo para ejecutar tests con unittest (no requiere pytest)
"""
import os
import sys
import unittest
from pathlib import Path

# Configurar el path
module_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(module_dir))

# Cargar el .env.test
from dotenv import load_dotenv
env_test_path = module_dir / '.env.test'
if env_test_path.exists():
    load_dotenv(env_test_path, override=True)
    print(f"✓ Cargado .env.test desde: {env_test_path}")

# Cambiar al directorio del módulo
os.chdir(module_dir)

# Importar y ejecutar los tests
if __name__ == "__main__":
    # Descubrir y ejecutar tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_supabase_integration.py')
    
    # Ejecutar con verbosidad
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Retornar código de salida apropiado
    sys.exit(0 if result.wasSuccessful() else 1)
