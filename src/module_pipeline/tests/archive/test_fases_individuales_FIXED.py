"""
Tests unitarios simples para cada fase del pipeline - VERSIÓN CORREGIDA.

PROBLEMAS DETECTADOS Y CORREGIDOS:
1. Imports circulares y rutas incorrectas
2. Referencias a clases inexistentes
3. Mock patterns incorrectos
4. Configuración de entorno inconsistente
5. Manejo de excepciones deficiente
"""

import os
import sys
from pathlib import Path
from uuid import uuid4

print("🔧 Configurando entorno para tests unitarios...")

# =========================================================================
# CONFIGURACIÓN INICIAL
# =========================================================================

# Configurar variables de entorno
os.environ["GROQ_API_KEY"] = "mock-api-key-for-testing"
os.environ["GROQ_MODEL_ID"] = "mixtral-8x7b-32768"
os.environ["SUPABASE_URL"] = "https://mock.supabase.co"
os.environ["SUPABASE_KEY"] = "mock-supabase-key"
os.environ["LOG_LEVEL"] = "INFO"

# Configurar path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Configurar logging
from loguru import logger
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>")

print(f"   ✅ Configuración lista")

# =========================================================================
# IMPORTS
# =========================================================================

try:
    # Utils
    from utils.fragment_processor import FragmentProcessor
    
    # Pipeline phases
    from pipeline.fase_1_triaje import ejecutar_fase_1
    from pipeline.fase_2_extraccion import ejecutar_fase_2
    from pipeline.fase_3_citas_datos import ejecutar_fase_3
    from pipeline.fase_4_normalizacion import ejecutar_fase_4
    
    # Models
    from models.procesamiento import (
        ResultadoFase1Triaje,
        ResultadoFase2Extraccion,
        ResultadoFase3CitasDatos,
        HechoProcesado,
        EntidadProcesada,
        CitaTextualProcesada,
        DatoCuantitativoProcesado
    )
    
    print("   ✅ Imports exitosos")
    
except ImportError as e:
    print(f"❌ Error en imports: {e}")
    sys.exit(1)

# =========================================================================
# TESTS UNITARIOS
# =========================================================================

def test_fase_1_simple():
    """Test simple de la Fase 1 sin dependencias externas."""
    print("\n🔍 TEST FASE 1: TRIAJE")
    print("-" * 40)
    
    # Datos de prueba
    id_fragmento = uuid4()
    texto = "El presidente anunció nuevas medidas económicas importantes para el país."
    
    import unittest.mock as mock
    
    # Mock respuesta de triaje
    respuesta_mock = """
EXCLUSIÓN: NO

TIPO DE ARTÍCULO: POLÍTICA

Relevancia geográfica: [4] - Nacional
Relevancia temática: [5] - Economía
Densidad factual: [3]
Complejidad relacional: [3]
Valor informativo: [4]

TOTAL: [19] / 25

DECISIÓN: PROCESAR

JUSTIFICACIÓN:
Artículo relevante sobre política económica nacional.

ELEMENTOS CLAVE:
- Anuncio presidencial
- Medidas económicas
"""
    
    try:
        with mock.patch('pipeline.fase_1_triaje._cargar_modelo_spacy', return_value=None), \
             mock.patch('pipeline.fase_1_triaje._llamar_groq_api_triaje', return_value=("prompt", respuesta_mock)):
            
            resultado = ejecutar_fase_1(
                id_fragmento_original=id_fragmento,
                texto_original_fragmento=texto
            )
        
        print(f"✅ ID Fragmento: {resultado.id_fragmento}")
        print(f"✅ Es relevante: {resultado.es_relevante}")
        print(f"✅ Decisión: {resultado.decision_triaje}")
        print(f"✅ Categoría: {resultado.categoria_principal}")
        print(f"✅ Puntuación: {resultado.puntuacion_triaje}")
        print(f"✅ Texto procesado: {len(resultado.texto_para_siguiente_fase)} caracteres")
        
        # Validaciones básicas
        assert resultado.id_fragmento == id_fragmento
        assert isinstance(resultado.es_relevante, bool)
        assert resultado.decision_triaje in ["PROCESAR", "DESCARTAR", "CONSIDERAR"]
        
        print("✅ FASE 1 FUNCIONANDO CORRECTAMENTE")
        return resultado
        
    except Exception as e:
        print(f"❌ Error en Fase 1: {e}")
        raise


def test_fase_2_simple():
    """Test simple de la Fase 2."""
    print("\n\n📊 TEST FASE 2: EXTRACCIÓN")
    print("-" * 40)
    
    # Crear datos mock de entrada
    id_fragmento = uuid4()
    resultado_fase_1 = ResultadoFase1Triaje(
        id_fragmento=id_fragmento,
        es_relevante=True,
        texto_para_siguiente_fase="El ministro anunció una inversión de 500 millones de euros."
    )
    
    processor = FragmentProcessor(id_fragmento)
    
    # Mock respuesta extracción
    respuesta_mock = """{
  "hechos": [
    {
      "id": 1,
      "contenido": "El ministro anunció una inversión de 500 millones de euros",
      "tipo_hecho": "ANUNCIO",
      "fecha": {"inicio": "2024-01-01", "fin": null},
      "pais": ["España"]
    }
  ],
  "entidades": [
    {
      "id": 1,
      "nombre": "ministro",
      "tipo": "PERSONA",
      "alias": [],
      "descripcion": "Funcionario del gobierno"
    }
  ]
}"""
    
    import unittest.mock as mock
    
    try:
        with mock.patch('pipeline.fase_2_extraccion._llamar_groq_api_extraccion', return_value=("prompt", respuesta_mock)):
            
            resultado = ejecutar_fase_2(
                resultado_fase_1=resultado_fase_1,
                processor=processor
            )
        
        print(f"✅ Hechos extraídos: {len(resultado.hechos_extraidos)}")
        print(f"✅ Entidades extraídas: {len(resultado.entidades_extraidas)}")
        
        if resultado.hechos_extraidos:
            hecho = resultado.hechos_extraidos[0]
            print(f"   - Hecho 1: ID={hecho.id_hecho}, Texto='{hecho.texto_original_del_hecho[:50]}...'")
            
        if resultado.entidades_extraidas:
            entidad = resultado.entidades_extraidas[0]
            print(f"   - Entidad 1: ID={entidad.id_entidad}, Nombre='{entidad.texto_entidad}' ({entidad.tipo_entidad})")
        
        # Validaciones
        assert resultado.id_fragmento == id_fragmento
        assert len(resultado.hechos_extraidos) > 0
        assert len(resultado.entidades_extraidas) > 0
        
        print("✅ FASE 2 FUNCIONANDO CORRECTAMENTE")
        return resultado, processor
        
    except Exception as e:
        print(f"❌ Error en Fase 2: {e}")
        raise


def test_fase_3_simple():
    """Test simple de la Fase 3."""
    print("\n\n💬 TEST FASE 3: CITAS Y DATOS")
    print("-" * 40)
    
    # Crear datos mock
    id_fragmento = uuid4()
    processor = FragmentProcessor(id_fragmento)
    
    # Crear datos realistas usando los modelos correctos
    from models.metadatos import MetadatosHecho, MetadatosEntidad
    
    # Mock de hecho
    hecho = HechoProcesado(
        id_hecho=1,
        texto_original_del_hecho="Se invertirán 500 millones en infraestructura",
        confianza_extraccion=0.9,
        id_fragmento_origen=id_fragmento,
        metadata_hecho=MetadatosHecho(tipo_hecho="ANUNCIO")
    )
    
    # Mock de entidad
    entidad = EntidadProcesada(
        id_entidad=1,
        texto_entidad="Ministro de Economía",
        tipo_entidad="PERSONA",
        relevancia_entidad=0.8,
        id_fragmento_origen=id_fragmento,
        metadata_entidad=MetadatosEntidad(tipo="PERSONA")
    )
    
    resultado_fase_2 = ResultadoFase2Extraccion(
        id_fragmento=id_fragmento,
        hechos_extraidos=[hecho],
        entidades_extraidas=[entidad]
    )
    
    # Mock respuesta para fase 3
    respuesta_mock = """{
  "citas_textuales": [
    {
      "id": 1,
      "cita": "Esta inversión transformará nuestro país",
      "entidad_id": 1,
      "hecho_id": 1,
      "relevancia": 4,
      "contexto": "Declaración pública"
    }
  ],
  "datos_cuantitativos": [
    {
      "id": 1,
      "hecho_id": 1,
      "indicador": "Inversión en infraestructura",
      "categoria": "económico",
      "valor": 500,
      "unidad": "millones de euros"
    }
  ]
}"""
    
    import unittest.mock as mock
    
    try:
        with mock.patch('pipeline.fase_3_citas_datos._llamar_groq_api_citas_datos', return_value=("prompt", respuesta_mock)):
            
            resultado = ejecutar_fase_3(
                resultado_fase_2=resultado_fase_2,
                processor=processor
            )
        
        print(f"✅ Citas extraídas: {len(resultado.citas_textuales_extraidas)}")
        print(f"✅ Datos extraídos: {len(resultado.datos_cuantitativos_extraidos)}")
        
        if resultado.citas_textuales_extraidas:
            cita = resultado.citas_textuales_extraidas[0]
            print(f"   - Cita 1: ID={cita.id_cita}, Texto='{cita.texto_cita}'")
            
        if resultado.datos_cuantitativos_extraidos:
            dato = resultado.datos_cuantitativos_extraidos[0]
            print(f"   - Dato 1: ID={dato.id_dato_cuantitativo}, Valor={dato.valor_dato} {dato.unidad_dato}")
        
        # Validaciones
        assert resultado.id_fragmento == id_fragmento
        
        print("✅ FASE 3 FUNCIONANDO CORRECTAMENTE")
        return resultado
        
    except Exception as e:
        print(f"❌ Error en Fase 3: {e}")
        raise


def test_fase_4_simple():
    """Test simple de la Fase 4."""
    print("\n\n🔗 TEST FASE 4: NORMALIZACIÓN")
    print("-" * 40)
    
    # Usar datos mínimos para la fase 4
    id_fragmento = uuid4()
    processor = FragmentProcessor(id_fragmento)
    
    # Crear resultados mínimos de fases anteriores
    resultado_fase_1 = ResultadoFase1Triaje(
        id_fragmento=id_fragmento,
        es_relevante=True,
        texto_para_siguiente_fase="Texto de prueba"
    )
    
    resultado_fase_2 = ResultadoFase2Extraccion(
        id_fragmento=id_fragmento,
        hechos_extraidos=[],
        entidades_extraidas=[]
    )
    
    resultado_fase_3 = ResultadoFase3CitasDatos(
        id_fragmento=id_fragmento,
        citas_textuales_extraidas=[],
        datos_cuantitativos_extraidos=[]
    )
    
    # Mock respuesta para relaciones
    respuesta_mock = """{
  "hecho_entidad": [],
  "hecho_relacionado": [],
  "entidad_relacion": [],
  "contradicciones": []
}"""
    
    import unittest.mock as mock
    
    try:
        with mock.patch('pipeline.fase_4_normalizacion._llamar_groq_api_relaciones', return_value=("prompt", respuesta_mock)):
            
            resultado = ejecutar_fase_4(
                processor=processor,
                resultado_fase_1=resultado_fase_1,
                resultado_fase_2=resultado_fase_2,
                resultado_fase_3=resultado_fase_3,
                supabase_service=None
            )
        
        print(f"✅ Estado: {resultado.estado_general_normalizacion}")
        print(f"✅ Resumen: {resultado.resumen_normalizacion}")
        
        # Validaciones básicas
        assert resultado.id_fragmento == id_fragmento
        assert resultado.estado_general_normalizacion in ["COMPLETADO", "PARCIAL", "ERROR"]
        
        print("✅ FASE 4 FUNCIONANDO CORRECTAMENTE")
        return resultado
        
    except Exception as e:
        print(f"❌ Error en Fase 4: {e}")
        raise


def ejecutar_todos_los_tests():
    """Ejecuta todos los tests unitarios en secuencia."""
    print("\n" + "="*60)
    print("🧪 EJECUTANDO TESTS UNITARIOS DEL PIPELINE")
    print("="*60)
    
    resultados = {}
    errores = []
    
    # Lista de tests a ejecutar
    tests = [
        ("Fase 1 - Triaje", test_fase_1_simple),
        ("Fase 2 - Extracción", test_fase_2_simple),
        ("Fase 3 - Citas y Datos", test_fase_3_simple),
        ("Fase 4 - Normalización", test_fase_4_simple)
    ]
    
    for nombre_test, funcion_test in tests:
        try:
            print(f"\n📋 Ejecutando test: {nombre_test}")
            resultado = funcion_test()
            resultados[nombre_test] = resultado
            print(f"✅ {nombre_test}: EXITOSO")
            
        except Exception as e:
            print(f"❌ {nombre_test}: FALLIDO")
            print(f"   Error: {e}")
            errores.append((nombre_test, str(e)))
    
    # Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN DE TESTS UNITARIOS")
    print("="*60)
    
    exitosos = len(resultados) - len(errores)
    total = len(tests)
    
    print(f"\n📈 Resultados:")
    print(f"   - Tests exitosos: {exitosos}/{total}")
    print(f"   - Tests fallidos: {len(errores)}/{total}")
    print(f"   - Tasa de éxito: {(exitosos/total)*100:.1f}%")
    
    if errores:
        print(f"\n❌ Errores encontrados:")
        for nombre, error in errores:
            print(f"   - {nombre}: {error}")
    else:
        print(f"\n🎉 TODOS LOS TESTS UNITARIOS PASARON")
        print(f"   - Las 4 fases del pipeline son funcionales")
        print(f"   - Los mocks están trabajando correctamente")
        print(f"   - La estructura de datos es coherente")
    
    return len(errores) == 0


# =========================================================================
# EJECUCIÓN PRINCIPAL
# =========================================================================

if __name__ == "__main__":
    print("🚀 Iniciando tests unitarios del pipeline...")
    
    try:
        success = ejecutar_todos_los_tests()
        
        if success:
            print("\n🏆 ¡TESTS UNITARIOS EXITOSOS!")
        else:
            print("\n💥 Algunos tests fallaron. Revisa los errores.")
            
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrumpidos por el usuario.")
        
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        import traceback
        traceback.print_exc()
