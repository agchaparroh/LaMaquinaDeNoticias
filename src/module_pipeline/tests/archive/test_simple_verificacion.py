"""
TEST SIMPLE PARA VERIFICAR CONFIGURACION
=========================================
Test básico para verificar que la configuración y los imports funcionan.
"""

import os
import sys
from pathlib import Path

print("🔧 Iniciando test simple de verificación...")

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

# Test fase 1
try:
    from pipeline.fase_1_triaje import ejecutar_fase_1
    print("✅ fase_1_triaje importada")
except ImportError as e:
    print(f"❌ Error importando fase_1_triaje: {e}")

# Test modelos
try:
    from models.procesamiento import ResultadoFase1Triaje
    print("✅ Modelos de procesamiento importados")
except ImportError as e:
    print(f"❌ Error importando modelos: {e}")

print("\n🏁 Test simple completado.")
print("Si todos los elementos muestran ✅, la configuración está correcta.")
