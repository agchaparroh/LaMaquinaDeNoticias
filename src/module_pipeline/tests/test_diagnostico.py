"""
Test de diagnóstico para el sistema de manejo de errores
========================================================
"""

import sys
from pathlib import Path

# Añadir el directorio src al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

print("Directorio del proyecto:", project_root)
print("Python path:", sys.path[:3])

try:
    print("\n1. Importando módulo de error_handling...")
    from src.utils.error_handling import PipelineException, ErrorPhase, ErrorType
    print("✅ Importación exitosa")
    
    print("\n2. Creando PipelineException básica...")
    exc = PipelineException(
        message="Test",
        error_type=ErrorType.INTERNAL_ERROR,
        phase=ErrorPhase.GENERAL
    )
    print("✅ PipelineException creada")
    
    print("\n3. Verificando atributos...")
    print(f"   - Message: {exc.message}")
    print(f"   - Error type: {exc.error_type}")
    print(f"   - Phase: {exc.phase}")
    print(f"   - Support code: {exc.support_code}")
    print(f"   - Timestamp: {exc.timestamp}")
    print("✅ Todos los atributos accesibles")
    
    print("\n4. Importando ValidationError...")
    from src.utils.error_handling import ValidationError
    print("✅ ValidationError importada")
    
    print("\n5. Creando ValidationError...")
    val_exc = ValidationError(
        message="Test validation",
        validation_errors=["error1", "error2"]
    )
    print("✅ ValidationError creada")
    
    print("\n6. Verificando herencia...")
    print(f"   - Es PipelineException: {isinstance(val_exc, PipelineException)}")
    print(f"   - Tiene timestamp: {hasattr(val_exc, 'timestamp')}")
    if hasattr(val_exc, 'timestamp'):
        print(f"   - Valor timestamp: {val_exc.timestamp}")
    else:
        print("   ❌ NO tiene atributo timestamp")
        print(f"   - Atributos disponibles: {dir(val_exc)}")
    
    print("\n✅ Diagnóstico completado exitosamente")
    
except Exception as e:
    print(f"\n❌ Error durante diagnóstico: {e}")
    import traceback
    traceback.print_exc()
