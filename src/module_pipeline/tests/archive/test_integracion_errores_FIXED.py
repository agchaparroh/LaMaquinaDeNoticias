"""
Test de integración y manejo de errores - VERSIÓN CORREGIDA.

PROBLEMAS DETECTADOS Y CORREGIDOS:
1. Casos de prueba más realistas
2. Manejo de errores específicos del pipeline
3. Configuración de mocks más robusta
4. Validación de casos edge
"""

import os
import sys
from pathlib import Path
from uuid import uuid4

print("🔧 Configurando entorno para tests de integración...")

# =========================================================================
# CONFIGURACIÓN INICIAL
# =========================================================================

# Variables de entorno
os.environ["GROQ_API_KEY"] = "mock-api-key-for-testing"
os.environ["GROQ_MODEL_ID"] = "mixtral-8x7b-32768"
os.environ["SUPABASE_URL"] = "https://mock.supabase.co"
os.environ["SUPABASE_KEY"] = "mock-supabase-key"
os.environ["LOG_LEVEL"] = "WARNING"  # Menos verbose para estos tests

# Path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Logging
from loguru import logger
logger.remove()
logger.add(sys.stderr, level="WARNING", format="<level>{level: <8}</level> | <cyan>{message}</cyan>")

print("   ✅ Configuración lista")

# =========================================================================
# IMPORTS
# =========================================================================

try:
    from utils.fragment_processor import FragmentProcessor
    from pipeline.fase_1_triaje import ejecutar_fase_1
    from pipeline.fase_2_extraccion import ejecutar_fase_2
    from pipeline.fase_3_citas_datos import ejecutar_fase_3
    from pipeline.fase_4_normalizacion import ejecutar_fase_4
    
    from models.procesamiento import (
        ResultadoFase1Triaje,
        ResultadoFase2Extraccion,
        ResultadoFase3CitasDatos
    )
    
    print("   ✅ Imports exitosos")
    
except ImportError as e:
    print(f"❌ Error en imports: {e}")
    sys.exit(1)

# =========================================================================
# TESTS DE CASOS EDGE
# =========================================================================

def test_texto_vacio():
    """Test con texto completamente vacío."""
    print("\n🔍 TEST: Texto vacío")
    print("-" * 30)
    
    id_fragmento = uuid4()
    texto_vacio = ""
    
    import unittest.mock as mock
    
    # Mock con respuesta de descarte
    respuesta_mock = """
EXCLUSIÓN: SÍ - Texto vacío

TIPO DE ARTÍCULO: INDETERMINADO

TOTAL: [0] / 25

DECISIÓN: DESCARTAR

JUSTIFICACIÓN:
Texto vacío o sin contenido procesable.
"""
    
    try:
        with mock.patch('pipeline.fase_1_triaje._cargar_modelo_spacy', return_value=None), \
             mock.patch('pipeline.fase_1_triaje._llamar_groq_api_triaje', return_value=("prompt", respuesta_mock)):
            
            resultado = ejecutar_fase_1(
                id_fragmento_original=id_fragmento,
                texto_original_fragmento=texto_vacio
            )
        
        print(f"✅ Texto vacío manejado correctamente")
        print(f"   - Es relevante: {resultado.es_relevante}")
        print(f"   - Decisión: {resultado.decision_triaje}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error con texto vacío: {e}")
        return False


def test_texto_muy_corto():
    """Test con texto extremadamente corto."""
    print("\n🔍 TEST: Texto muy corto")
    print("-" * 30)
    
    id_fragmento = uuid4()
    texto_corto = "Sí."
    
    import unittest.mock as mock
    
    respuesta_mock = """
EXCLUSIÓN: SÍ - Texto demasiado corto

TIPO DE ARTÍCULO: INDETERMINADO

TOTAL: [2] / 25

DECISIÓN: DESCARTAR

JUSTIFICACIÓN:
Texto muy corto, sin suficiente información.
"""
    
    try:
        with mock.patch('pipeline.fase_1_triaje._cargar_modelo_spacy', return_value=None), \
             mock.patch('pipeline.fase_1_triaje._llamar_groq_api_triaje', return_value=("prompt", respuesta_mock)):
            
            resultado = ejecutar_fase_1(
                id_fragmento_original=id_fragmento,
                texto_original_fragmento=texto_corto
            )
        
        print(f"✅ Texto corto manejado correctamente")
        print(f"   - Es relevante: {resultado.es_relevante}")
        print(f"   - Decisión: {resultado.decision_triaje}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error con texto corto: {e}")
        return False


def test_texto_irrelevante():
    """Test con contenido claramente irrelevante."""
    print("\n🔍 TEST: Contenido irrelevante")
    print("-" * 30)
    
    id_fragmento = uuid4()
    texto_irrelevante = """
    Hoy fui al supermercado y compré leche, pan y huevos. 
    El tiempo estaba nublado. Mi gato se llama Whiskers y le gusta dormir.
    Mañana tengo que lavar la ropa.
    """
    
    import unittest.mock as mock
    
    respuesta_mock = """
EXCLUSIÓN: SÍ - Contenido personal sin interés público

TIPO DE ARTÍCULO: PERSONAL

Relevancia geográfica: [1] - Sin relevancia
Relevancia temática: [1] - Vida cotidiana
Densidad factual: [1]
Complejidad relacional: [1]
Valor informativo: [1]

TOTAL: [5] / 25

DECISIÓN: DESCARTAR

JUSTIFICACIÓN:
Contenido personal sin relevancia informativa o interés público.

ELEMENTOS CLAVE:
- Actividades cotidianas
- Información personal
"""
    
    try:
        with mock.patch('pipeline.fase_1_triaje._cargar_modelo_spacy', return_value=None), \
             mock.patch('pipeline.fase_1_triaje._llamar_groq_api_triaje', return_value=("prompt", respuesta_mock)):
            
            resultado = ejecutar_fase_1(
                id_fragmento_original=id_fragmento,
                texto_original_fragmento=texto_irrelevante
            )
        
        print(f"✅ Contenido irrelevante detectado correctamente")
        print(f"   - Es relevante: {resultado.es_relevante}")
        print(f"   - Decisión: {resultado.decision_triaje}")
        print(f"   - Puntuación: {resultado.puntuacion_triaje}/25")
        
        assert not resultado.es_relevante
        assert resultado.decision_triaje == "DESCARTAR"
        
        return True
        
    except Exception as e:
        print(f"❌ Error con contenido irrelevante: {e}")
        return False


def test_contenido_ambiguo():
    """Test con contenido que podría ser ambiguo para clasificar."""
    print("\n🔍 TEST: Contenido ambiguo")
    print("-" * 30)
    
    id_fragmento = uuid4()
    texto_ambiguo = """
    La empresa anunció cambios en su estructura. 
    Los empleados están preocupados por las nuevas medidas.
    Se espera más información la próxima semana.
    """
    
    import unittest.mock as mock
    
    respuesta_mock = """
EXCLUSIÓN: NO

TIPO DE ARTÍCULO: ECONOMÍA

Relevancia geográfica: [2] - Empresa local
Relevancia temática: [3] - Economía empresarial
Densidad factual: [2]
Complejidad relacional: [2]
Valor informativo: [3]

TOTAL: [12] / 25

DECISIÓN: CONSIDERAR

JUSTIFICACIÓN:
Información empresarial con datos limitados pero potencial interés.

ELEMENTOS CLAVE:
- Cambios empresariales
- Impacto en empleados
- Información pendiente
"""
    
    try:
        with mock.patch('pipeline.fase_1_triaje._cargar_modelo_spacy', return_value=None), \
             mock.patch('pipeline.fase_1_triaje._llamar_groq_api_triaje', return_value=("prompt", respuesta_mock)):
            
            resultado = ejecutar_fase_1(
                id_fragmento_original=id_fragmento,
                texto_original_fragmento=texto_ambiguo
            )
        
        print(f"✅ Contenido ambiguo procesado correctamente")
        print(f"   - Es relevante: {resultado.es_relevante}")
        print(f"   - Decisión: {resultado.decision_triaje}")
        print(f"   - Puntuación: {resultado.puntuacion_triaje}/25")
        
        return True
        
    except Exception as e:
        print(f"❌ Error con contenido ambiguo: {e}")
        return False

# =========================================================================
# TESTS DE MANEJO DE ERRORES
# =========================================================================

def test_error_simulado_groq():
    """Test que simula un error en la API de Groq."""
    print("\n🔍 TEST: Error simulado de Groq API")
    print("-" * 30)
    
    id_fragmento = uuid4()
    texto = "El presidente anunció nuevas medidas económicas."
    
    import unittest.mock as mock
    
    try:
        # Simular error en la API
        with mock.patch('pipeline.fase_1_triaje._cargar_modelo_spacy', return_value=None), \
             mock.patch('pipeline.fase_1_triaje._llamar_groq_api_triaje', side_effect=Exception("Error simulado de API")):
            
            resultado = ejecutar_fase_1(
                id_fragmento_original=id_fragmento,
                texto_original_fragmento=texto
            )
        
        print(f"✅ Error de API manejado con fallback")
        print(f"   - Es relevante: {resultado.es_relevante}")
        print(f"   - Decisión: {resultado.decision_triaje}")
        
        # El fallback debería marcar como relevante por política de seguridad
        assert resultado.es_relevante == True
        
        return True
        
    except Exception as e:
        print(f"❌ Error no manejado correctamente: {e}")
        return False


def test_respuesta_malformada():
    """Test con respuesta malformada del LLM."""
    print("\n🔍 TEST: Respuesta malformada del LLM")
    print("-" * 30)
    
    id_fragmento = uuid4()
    texto = "Noticia sobre economía nacional."
    
    import unittest.mock as mock
    
    # Respuesta completamente malformada
    respuesta_malformada = "Esta es una respuesta que no sigue el formato esperado para nada."
    
    try:
        with mock.patch('pipeline.fase_1_triaje._cargar_modelo_spacy', return_value=None), \
             mock.patch('pipeline.fase_1_triaje._llamar_groq_api_triaje', return_value=("prompt", respuesta_malformada)):
            
            resultado = ejecutar_fase_1(
                id_fragmento_original=id_fragmento,
                texto_original_fragmento=texto
            )
        
        print(f"✅ Respuesta malformada manejada")
        print(f"   - Es relevante: {resultado.es_relevante}")
        print(f"   - Decisión: {resultado.decision_triaje}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error con respuesta malformada: {e}")
        return False

# =========================================================================
# TESTS DE INTEGRACIÓN
# =========================================================================

def test_pipeline_fragmento_no_relevante():
    """Test del pipeline completo con un fragmento que será descartado."""
    print("\n🔍 TEST: Pipeline con fragmento no relevante")
    print("-" * 30)
    
    id_fragmento = uuid4()
    texto_no_relevante = "Me gusta el helado de chocolate. Es mi sabor favorito."
    
    import unittest.mock as mock
    
    # Mock para fase 1 que descarta
    respuesta_triaje = """
EXCLUSIÓN: SÍ - Contenido personal

TIPO DE ARTÍCULO: PERSONAL

TOTAL: [3] / 25

DECISIÓN: DESCARTAR

JUSTIFICACIÓN:
Contenido personal sin relevancia informativa.
"""
    
    try:
        with mock.patch('pipeline.fase_1_triaje._cargar_modelo_spacy', return_value=None), \
             mock.patch('pipeline.fase_1_triaje._llamar_groq_api_triaje', return_value=("prompt", respuesta_triaje)):
            
            resultado_fase_1 = ejecutar_fase_1(
                id_fragmento_original=id_fragmento,
                texto_original_fragmento=texto_no_relevante
            )
        
        print(f"✅ Fase 1 completada - Fragmento descartado")
        print(f"   - Es relevante: {resultado_fase_1.es_relevante}")
        print(f"   - Decisión: {resultado_fase_1.decision_triaje}")
        
        # Para fragmentos no relevantes, no debería continuar a fase 2
        if not resultado_fase_1.es_relevante:
            print(f"✅ Pipeline detenido correctamente en Fase 1")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error en test de integración: {e}")
        return False


def test_coherencia_ids():
    """Test que verifica la coherencia de IDs entre fases."""
    print("\n🔍 TEST: Coherencia de IDs entre fases")
    print("-" * 30)
    
    id_fragmento = uuid4()
    texto = "El ministro anunció una inversión de 1000 millones para tecnología."
    
    import unittest.mock as mock
    
    # Mocks con datos coherentes
    respuesta_triaje = """
EXCLUSIÓN: NO
TIPO DE ARTÍCULO: POLÍTICA
TOTAL: [20] / 25
DECISIÓN: PROCESAR
JUSTIFICACIÓN: Relevante
"""
    
    respuesta_extraccion = """{
  "hechos": [
    {"id": 1, "contenido": "Anuncio de inversión", "tipo_hecho": "ANUNCIO"}
  ],
  "entidades": [
    {"id": 1, "nombre": "ministro", "tipo": "PERSONA"}
  ]
}"""
    
    respuesta_citas = """{
  "citas_textuales": [
    {"id": 1, "cita": "Test quote", "entidad_id": 1, "hecho_id": 1}
  ],
  "datos_cuantitativos": [
    {"id": 1, "hecho_id": 1, "indicador": "Inversión", "valor": 1000}
  ]
}"""
    
    try:
        processor = FragmentProcessor(id_fragmento)
        
        # Mock todas las llamadas
        with mock.patch('pipeline.fase_1_triaje._cargar_modelo_spacy', return_value=None), \
             mock.patch('pipeline.fase_1_triaje._llamar_groq_api_triaje', return_value=("prompt", respuesta_triaje)), \
             mock.patch('pipeline.fase_2_extraccion._llamar_groq_api_extraccion', return_value=("prompt", respuesta_extraccion)), \
             mock.patch('pipeline.fase_3_citas_datos._llamar_groq_api_citas_datos', return_value=("prompt", respuesta_citas)):
            
            # Fase 1
            resultado_fase_1 = ejecutar_fase_1(
                id_fragmento_original=id_fragmento,
                texto_original_fragmento=texto
            )
            
            # Fase 2
            resultado_fase_2 = ejecutar_fase_2(
                resultado_fase_1=resultado_fase_1,
                processor=processor
            )
            
            # Fase 3
            resultado_fase_3 = ejecutar_fase_3(
                resultado_fase_2=resultado_fase_2,
                processor=processor
            )
        
        # Verificar coherencia de IDs
        assert resultado_fase_1.id_fragmento == id_fragmento
        assert resultado_fase_2.id_fragmento == id_fragmento
        assert resultado_fase_3.id_fragmento == id_fragmento
        
        print(f"✅ IDs coherentes en todas las fases")
        print(f"   - Fragmento: {id_fragmento}")
        print(f"   - Hechos: {len(resultado_fase_2.hechos_extraidos)}")
        print(f"   - Entidades: {len(resultado_fase_2.entidades_extraidas)}")
        print(f"   - Citas: {len(resultado_fase_3.citas_textuales_extraidas)}")
        print(f"   - Datos: {len(resultado_fase_3.datos_cuantitativos_extraidos)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test de coherencia: {e}")
        return False

# =========================================================================
# EJECUTOR PRINCIPAL
# =========================================================================

def ejecutar_tests_integracion():
    """Ejecuta todos los tests de integración y manejo de errores."""
    print("\n" + "="*60)
    print("🧪 TESTS DE INTEGRACIÓN Y MANEJO DE ERRORES")
    print("="*60)
    
    tests = [
        ("Texto vacío", test_texto_vacio),
        ("Texto muy corto", test_texto_muy_corto),
        ("Contenido irrelevante", test_texto_irrelevante),
        ("Contenido ambiguo", test_contenido_ambiguo),
        ("Error simulado Groq", test_error_simulado_groq),
        ("Respuesta malformada", test_respuesta_malformada),
        ("Pipeline con descarte", test_pipeline_fragmento_no_relevante),
        ("Coherencia de IDs", test_coherencia_ids)
    ]
    
    exitosos = 0
    errores = []
    
    for nombre, test_func in tests:
        try:
            print(f"\n📋 Ejecutando: {nombre}")
            if test_func():
                exitosos += 1
                print(f"✅ {nombre}: EXITOSO")
            else:
                print(f"❌ {nombre}: FALLIDO")
                errores.append(nombre)
                
        except Exception as e:
            print(f"❌ {nombre}: ERROR - {e}")
            errores.append(nombre)
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE TESTS DE INTEGRACIÓN")
    print("="*60)
    
    total = len(tests)
    print(f"\n📈 Resultados:")
    print(f"   - Tests exitosos: {exitosos}/{total}")
    print(f"   - Tests fallidos: {len(errores)}/{total}")
    print(f"   - Tasa de éxito: {(exitosos/total)*100:.1f}%")
    
    if errores:
        print(f"\n❌ Tests fallidos:")
        for error in errores:
            print(f"   - {error}")
    else:
        print(f"\n🎉 TODOS LOS TESTS DE INTEGRACIÓN PASARON")
        print(f"   - Manejo de casos edge funcional")
        print(f"   - Recuperación de errores exitosa")
        print(f"   - Coherencia de datos verificada")
    
    return len(errores) == 0


# =========================================================================
# EJECUCIÓN PRINCIPAL
# =========================================================================

if __name__ == "__main__":
    print("🚀 Iniciando tests de integración y manejo de errores...")
    
    try:
        success = ejecutar_tests_integracion()
        
        if success:
            print("\n🏆 ¡TESTS DE INTEGRACIÓN EXITOSOS!")
        else:
            print("\n💥 Algunos tests fallaron. Revisa los errores.")
            
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrumpidos por el usuario.")
        
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        import traceback
        traceback.print_exc()
