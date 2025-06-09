"""
TEST SIMPLE PARA VERIFICAR CONFIGURACION - VERSION 3
=====================================================
Test básico que usa imports absolutos para evitar problemas con imports relativos.
"""

import os
import sys
from pathlib import Path

print("🔧 Iniciando test simple de verificación (v3)...")

# Configurar variables de entorno antes de cualquier import
os.environ["GROQ_API_KEY"] = "test-key"
os.environ["GROQ_MODEL_ID"] = "test-model"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_KEY"] = "test-key"
os.environ["LOG_LEVEL"] = "INFO"

print("✅ Variables de entorno configuradas")

# Configurar path
src_path = Path(__file__).parent.parent / "src"
print(f"📁 Path src calculado: {src_path}")
print(f"📁 Path existe: {src_path.exists()}")

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
    print(f"✅ Path agregado a sys.path")

print(f"📋 sys.path actual:")
for i, path in enumerate(sys.path[:5]):  # Solo primeros 5
    print(f"   {i}: {path}")

# Configurar logging básico
try:
    from loguru import logger
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<level>{level}</level> | <cyan>{message}</cyan>")
    print("✅ Loguru configurado")
except ImportError as e:
    print(f"❌ Error importando loguru: {e}")

# Test de imports básicos
print("\n🧪 Probando imports básicos...")

try:
    from uuid import uuid4
    test_uuid = uuid4()
    print(f"✅ UUID: {test_uuid}")
except ImportError as e:
    print(f"❌ Error con UUID: {e}")

# Test FragmentProcessor
try:
    from utils.fragment_processor import FragmentProcessor
    test_processor = FragmentProcessor(uuid4())
    print("✅ FragmentProcessor importado y creado")
    
    # Test básico de IDs
    hecho_id = test_processor.next_hecho_id("Test hecho")
    entidad_id = test_processor.next_entidad_id("Test entidad")
    print(f"✅ IDs generados - Hecho: {hecho_id}, Entidad: {entidad_id}")
    
except ImportError as e:
    print(f"❌ Error importando FragmentProcessor: {e}")
except Exception as e:
    print(f"❌ Error usando FragmentProcessor: {e}")

# Test modelos principales
try:
    from models.procesamiento import ResultadoFase1Triaje
    print("✅ Modelos de procesamiento importados")
except ImportError as e:
    print(f"❌ Error importando modelos: {e}")

# Test función específica de fase 1 - con manejo especial para imports relativos
try:
    # Intentar importar la función específica evitando imports relativos
    import importlib.util
    
    fase1_path = src_path / "pipeline" / "fase_1_triaje.py"
    print(f"📁 Intentando cargar fase_1_triaje desde: {fase1_path}")
    
    if fase1_path.exists():
        spec = importlib.util.spec_from_file_location("fase_1_triaje", fase1_path)
        if spec and spec.loader:
            # Primero, asegurar que los módulos dependientes estén disponibles
            import models.procesamiento
            import utils.error_handling
            
            # Luego intentar cargar el módulo
            fase1_module = importlib.util.module_from_spec(spec)
            sys.modules["fase_1_triaje"] = fase1_module
            spec.loader.exec_module(fase1_module)
            
            print("✅ Módulo fase_1_triaje cargado exitosamente")
            
            # Test de función específica
            if hasattr(fase1_module, 'ejecutar_fase_1'):
                print("✅ Función ejecutar_fase_1 encontrada")
            else:
                print("❌ Función ejecutar_fase_1 no encontrada")
        else:
            print("❌ No se pudo crear spec para fase_1_triaje")
    else:
        print(f"❌ Archivo fase_1_triaje.py no existe en {fase1_path}")
        
except Exception as e:
    print(f"❌ Error cargando fase_1_triaje: {e}")
    print(f"   Tipo de error: {type(e).__name__}")

# Test verificación de estructura de directorios
print("\n🗂️ Verificando estructura de directorios...")

directories_to_check = [
    "utils",
    "models", 
    "pipeline",
    "services"
]

for dir_name in directories_to_check:
    dir_path = src_path / dir_name
    if dir_path.exists():
        print(f"✅ Directorio {dir_name}: existe")
        
        # Listar algunos archivos importantes
        python_files = list(dir_path.glob("*.py"))
        if python_files:
            print(f"   📄 Archivos Python encontrados: {len(python_files)}")
            for py_file in python_files[:3]:  # Solo primeros 3
                print(f"      - {py_file.name}")
        else:
            print(f"   ⚠️ No se encontraron archivos Python")
    else:
        print(f"❌ Directorio {dir_name}: NO existe")

print("\n🏁 Test simple completado.")
print("\n📊 RESUMEN:")
print("- ✅ = Componente funcionando correctamente")
print("- ❌ = Componente con problemas") 
print("- ⚠️ = Componente parcialmente funcional")
