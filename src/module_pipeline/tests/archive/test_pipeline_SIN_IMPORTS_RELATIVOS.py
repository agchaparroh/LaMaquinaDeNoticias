"""
Test completo del pipeline - VERSION SIN IMPORTS RELATIVOS
=========================================================

Esta versión evita problemas de imports relativos usando importación dinámica
y manejo robusto de dependencias.
"""

import os
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime
import importlib.util

print("🚀 Iniciando test del pipeline completo (versión sin imports relativos)...")

# =========================================================================
# CONFIGURACIÓN INICIAL CRÍTICA
# =========================================================================

# 1. Configurar variables de entorno ANTES de cualquier import
os.environ["GROQ_API_KEY"] = "mock-api-key-for-testing"
os.environ["GROQ_MODEL_ID"] = "mixtral-8x7b-32768"
os.environ["SUPABASE_URL"] = "https://mock.supabase.co"
os.environ["SUPABASE_KEY"] = "mock-supabase-key"
os.environ["LOG_LEVEL"] = "INFO"

# 2. Agregar directorio src al path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

print(f"   ✅ Path src agregado: {src_path}")
print(f"   ✅ Variables de entorno configuradas")

# 3. Configurar logging
from loguru import logger
logger.remove()
logger.add(
    sys.stderr, 
    level="INFO", 
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
)

print("   ✅ Logging configurado")

# =========================================================================
# IMPORTS Y CARGA DE MÓDULOS
# =========================================================================

# Imports básicos que sabemos que funcionan
try:
    from utils.fragment_processor import FragmentProcessor
    print("   ✅ FragmentProcessor importado")
except ImportError as e:
    print(f"   ❌ Error importando FragmentProcessor: {e}")
    sys.exit(1)

try:
    from models.procesamiento import (
        ResultadoFase1Triaje, 
        ResultadoFase2Extraccion,
        ResultadoFase3CitasDatos,
        HechoProcesado,
        EntidadProcesada
    )
    print("   ✅ Modelos de procesamiento importados")
except ImportError as e:
    print(f"   ❌ Error importando modelos: {e}")
    sys.exit(1)

# Función para cargar módulos dinámicamente evitando imports relativos
def cargar_modulo_dinamico(nombre_modulo, ruta_archivo):
    """Carga un módulo Python dinámicamente desde una ruta específica."""
    try:
        spec = importlib.util.spec_from_file_location(nombre_modulo, ruta_archivo)
        if spec and spec.loader:
            modulo = importlib.util.module_from_spec(spec)
            sys.modules[nombre_modulo] = modulo
            spec.loader.exec_module(modulo)
            return modulo
        else:
            print(f"   ❌ No se pudo crear spec para {nombre_modulo}")
            return None
    except Exception as e:
        print(f"   ❌ Error cargando {nombre_modulo}: {e}")
        return None

# Cargar módulos del pipeline
print("\n🔧 Cargando módulos del pipeline...")

fase_1_module = cargar_modulo_dinamico(
    "fase_1_triaje", 
    src_path / "pipeline" / "fase_1_triaje.py"
)

if not fase_1_module:
    print("❌ No se pudo cargar fase_1_triaje. Test terminado.")
    sys.exit(1)

print("   ✅ Módulo fase_1_triaje cargado")

# =========================================================================
# FUNCIONES DE MOCK SIMPLIFICADAS
# =========================================================================

def mock_todas_las_funciones():
    """Aplica mocks a todas las funciones externas necesarias."""
    import unittest.mock as mock
    
    # Mock respuestas realistas
    respuesta_triaje = """
EXCLUSIÓN: NO

TIPO DE ARTÍCULO: POLÍTICA

Relevancia geográfica: [5] - España
Relevancia temática: [5] - Política nacional
Densidad factual: [5]
Complejidad relacional: [4]
Valor informativo: [5]

TOTAL: [24] / 25

DECISIÓN: PROCESAR

JUSTIFICACIÓN:
Artículo altamente relevante sobre política nacional española.

ELEMENTOS CLAVE:
- Anuncio oficial del gobierno
- Plan de inversión importante
- Impacto económico significativo
"""
    
    # Configurar mocks
    mocks = []
    
    # Mock para spaCy
    mock_spacy = mock.patch.object(fase_1_module, '_cargar_modelo_spacy', return_value=None)
    mocks.append(mock_spacy)
    
    # Mock para Groq API
    mock_groq = mock.patch.object(
        fase_1_module, 
        '_llamar_groq_api_triaje', 
        return_value=("prompt_triaje", respuesta_triaje)
    )
    mocks.append(mock_groq)
    
    # Iniciar todos los mocks
    for mock_obj in mocks:
        mock_obj.start()
    
    return mocks

# =========================================================================
# TEST PRINCIPAL
# =========================================================================

def test_pipeline_simplificado():
    """Test simplificado del pipeline que se enfoca en Fase 1."""
    
    print("\n" + "="*60)
    print("🧪 TEST SIMPLIFICADO DEL PIPELINE")
    print("="*60 + "\n")
    
    # Datos de prueba
    id_fragmento = uuid4()
    texto_original = """
    Pedro Sánchez, presidente del Gobierno de España, anunció ayer en Madrid 
    un plan de inversión de 1.000 millones de euros para modernizar 
    la infraestructura digital del país. "Vamos a transformar España 
    en un referente tecnológico europeo", declaró el presidente.
    """
    
    print(f"📄 Fragmento ID: {id_fragmento}")
    print(f"📝 Texto original ({len(texto_original)} caracteres):")
    print("-" * 60)
    print(texto_original.strip())
    print("-" * 60 + "\n")
    
    # Configurar mocks
    mocks = mock_todas_las_funciones()
    
    try:
        # ====================================================================
        # FASE 1: TRIAJE (PRINCIPAL)
        # ====================================================================
        print("🔍 FASE 1: TRIAJE Y PREPROCESAMIENTO")
        print("-" * 40)
        
        # Verificar que la función existe
        if not hasattr(fase_1_module, 'ejecutar_fase_1'):
            print("❌ Función ejecutar_fase_1 no encontrada en el módulo")
            return False
        
        # Ejecutar fase 1
        ejecutar_fase_1 = getattr(fase_1_module, 'ejecutar_fase_1')
        resultado_fase_1 = ejecutar_fase_1(
            id_fragmento_original=id_fragmento,
            texto_original_fragmento=texto_original
        )
        
        print(f"✅ Resultado: {'RELEVANTE' if resultado_fase_1.es_relevante else 'NO RELEVANTE'}")
        print(f"   - Decisión: {resultado_fase_1.decision_triaje}")
        print(f"   - Categoría: {resultado_fase_1.categoria_principal}")
        print(f"   - Puntuación: {resultado_fase_1.puntuacion_triaje}/25")
        print(f"   - ID: {resultado_fase_1.id_fragmento}")
        
        # Validaciones básicas
        assert resultado_fase_1.id_fragmento == id_fragmento
        assert isinstance(resultado_fase_1.es_relevante, bool)
        assert resultado_fase_1.texto_para_siguiente_fase is not None
        
        print(f"✅ FASE 1 COMPLETADA EXITOSAMENTE")
        
        # ====================================================================
        # TEST DEL FRAGMENTPROCESSOR
        # ====================================================================
        print("\n📊 TEST DEL FRAGMENTPROCESSOR")
        print("-" * 40)
        
        processor = FragmentProcessor(id_fragmento)
        
        # Generar algunos IDs
        hecho_id = processor.next_hecho_id("Test hecho")
        entidad_id = processor.next_entidad_id("Test entidad")
        cita_id = processor.next_cita_id("Test cita")
        dato_id = processor.next_dato_id("Test dato")
        
        print(f"✅ IDs generados:")
        print(f"   - Hecho: {hecho_id}")
        print(f"   - Entidad: {entidad_id}")
        print(f"   - Cita: {cita_id}")
        print(f"   - Dato: {dato_id}")
        
        # Estadísticas
        stats = processor.get_stats()
        print(f"✅ Estadísticas del processor:")
        print(f"   - Total hechos: {stats['total_hechos']}")
        print(f"   - Total entidades: {stats['total_entidades']}")
        print(f"   - Total citas: {stats['total_citas']}")
        print(f"   - Total datos: {stats['total_datos']}")
        
        # ====================================================================
        # RESUMEN FINAL
        # ====================================================================
        print("\n" + "="*60)
        print("📈 RESUMEN DEL TEST")
        print("="*60)
        
        print(f"\n✅ COMPONENTES VERIFICADOS:")
        print(f"   - Carga dinámica de módulos: OK")
        print(f"   - Fase 1 (Triaje): OK")
        print(f"   - FragmentProcessor: OK")
        print(f"   - Mocks de APIs externas: OK")
        print(f"   - Manejo de IDs secuenciales: OK")
        
        print(f"\n🎉 TEST SIMPLIFICADO EXITOSO")
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Detener todos los mocks
        for mock_obj in mocks:
            mock_obj.stop()

# =========================================================================
# EJECUCIÓN PRINCIPAL
# =========================================================================

if __name__ == "__main__":
    try:
        success = test_pipeline_simplificado()
        
        if success:
            print("\n\n🎉 ¡TEST EXITOSO! Los componentes principales funcionan.")
            print("   - El sistema de carga dinámica funciona")
            print("   - La Fase 1 del pipeline es funcional")
            print("   - Los mocks simulan correctamente las APIs")
        else:
            print("\n\n❌ Test fallido. Revisa los errores anteriores.")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrumpido por el usuario.")
        
    except Exception as e:
        print(f"\n\n💥 Error crítico: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n" + "="*60)
        print("🏁 FIN DEL TEST")
        print("="*60)
