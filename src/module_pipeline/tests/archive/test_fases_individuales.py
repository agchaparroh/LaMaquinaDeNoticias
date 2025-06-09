"""
Tests unitarios simples para cada fase del pipeline.

Estos tests permiten probar cada fase de forma individual.
"""

import os
import sys
from pathlib import Path
from uuid import uuid4

# Configurar path y variables de entorno
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
os.environ["GROQ_API_KEY"] = "mock-api-key-for-testing"

# Imports
from utils.fragment_processor import FragmentProcessor
from models.procesamiento import (
    ResultadoFase1Triaje,
    ResultadoFase2Extraccion,
    HechoProcesado,
    EntidadProcesada
)
from models.metadatos import MetadatosHecho, MetadatosEntidad


def test_fase_1_simple():
    """Test simple de la Fase 1 sin dependencias externas."""
    print("\n🔍 TEST FASE 1: TRIAJE")
    print("-" * 40)
    
    from pipeline.fase_1_triaje import ejecutar_fase_1
    
    # Datos de prueba
    id_fragmento = uuid4()
    texto = "El presidente anunció nuevas medidas económicas."
    
    # Ejecutar con modelo spacy mockeado
    import unittest.mock as mock
    with mock.patch('pipeline.fase_1_triaje._cargar_modelo_spacy') as mock_spacy:
        mock_spacy.return_value = None  # Simular fallo de spacy
        
        resultado = ejecutar_fase_1(
            id_fragmento_original=id_fragmento,
            texto_original_fragmento=texto
        )
    
    print(f"✅ ID Fragmento: {resultado.id_fragmento}")
    print(f"✅ Es relevante: {resultado.es_relevante}")
    print(f"✅ Decisión: {resultado.decision_triaje}")
    print(f"✅ Texto procesado: {len(resultado.texto_para_siguiente_fase)} caracteres")
    
    return resultado


def test_fase_2_simple():
    """Test simple de la Fase 2."""
    print("\n\n📊 TEST FASE 2: EXTRACCIÓN")
    print("-" * 40)
    
    from pipeline.fase_2_extraccion import ejecutar_fase_2
    
    # Crear datos mock de fase 1
    id_fragmento = uuid4()
    resultado_fase_1 = ResultadoFase1Triaje(
        id_fragmento=id_fragmento,
        es_relevante=True,
        texto_para_siguiente_fase="El presidente anunció nuevas medidas."
    )
    
    # Crear processor
    processor = FragmentProcessor(id_fragmento)
    
    # Mockear respuesta
    import unittest.mock as mock
    respuesta_mock = """
    {
        "hechos": [
            {"id": 1, "contenido": "El presidente anunció medidas", "tipo_hecho": "ANUNCIO"}
        ],
        "entidades": [
            {"id": 1, "nombre": "presidente", "tipo": "PERSONA"}
        ]
    }
    """
    
    with mock.patch('pipeline.fase_2_extraccion._llamar_groq_api_extraccion') as mock_groq:
        mock_groq.return_value = ("prompt", respuesta_mock)
        
        resultado = ejecutar_fase_2(
            resultado_fase_1=resultado_fase_1,
            processor=processor
        )
    
    print(f"✅ Hechos extraídos: {len(resultado.hechos_extraidos)}")
    print(f"✅ Entidades extraídas: {len(resultado.entidades_extraidas)}")
    
    if resultado.hechos_extraidos:
        print(f"   - Hecho 1: ID={resultado.hechos_extraidos[0].id_hecho}")
    if resultado.entidades_extraidas:
        print(f"   - Entidad 1: ID={resultado.entidades_extraidas[0].id_entidad}")
    
    return resultado, processor


def test_fase_3_simple():
    """Test simple de la Fase 3."""
    print("\n\n💬 TEST FASE 3: CITAS Y DATOS")
    print("-" * 40)
    
    from pipeline.fase_3_citas_datos import ejecutar_fase_3
    
    # Crear datos mock
    id_fragmento = uuid4()
    processor = FragmentProcessor(id_fragmento)
    
    # Mock de fase 2
    hechos = [
        HechoProcesado(
            id_hecho=1,
            texto_original_del_hecho="Se invertirán 100 millones",
            confianza_extraccion=0.9,
            id_fragmento_origen=id_fragmento,
            metadata_hecho=MetadatosHecho(tipo_hecho="ANUNCIO")
        )
    ]
    
    entidades = [
        EntidadProcesada(
            id_entidad=1,
            texto_entidad="Ministro",
            tipo_entidad="PERSONA",
            relevancia_entidad=0.8,
            id_fragmento_origen=id_fragmento,
            metadata_entidad=MetadatosEntidad(tipo="PERSONA")
        )
    ]
    
    resultado_fase_2 = ResultadoFase2Extraccion(
        id_fragmento=id_fragmento,
        hechos_extraidos=hechos,
        entidades_extraidas=entidades
    )
    
    # Mockear respuesta
    import unittest.mock as mock
    respuesta_mock = """
    {
        "citas_textuales": [
            {"id": 1, "cita": "Es importante invertir", "entidad_id": 1, "relevancia": 4}
        ],
        "datos_cuantitativos": [
            {"id": 1, "indicador": "Inversión", "valor": 100, "unidad": "millones"}
        ]
    }
    """
    
    with mock.patch('pipeline.fase_3_citas_datos._llamar_groq_api_citas_datos') as mock_groq:
        mock_groq.return_value = ("prompt", respuesta_mock)
        
        resultado = ejecutar_fase_3(
            resultado_fase_2=resultado_fase_2,
            processor=processor
        )
    
    print(f"✅ Citas extraídas: {len(resultado.citas_textuales_extraidas)}")
    print(f"✅ Datos extraídos: {len(resultado.datos_cuantitativos_extraidos)}")
    
    return resultado


def test_fase_4_simple():
    """Test simple de la Fase 4."""
    print("\n\n🔗 TEST FASE 4: NORMALIZACIÓN")
    print("-" * 40)
    
    from pipeline.fase_4_normalizacion import ejecutar_fase_4
    
    # Usar resultados de tests anteriores o crear mocks
    id_fragmento = uuid4()
    processor = FragmentProcessor(id_fragmento)
    
    # Mocks mínimos
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
    
    from models.procesamiento import ResultadoFase3CitasDatos
    resultado_fase_3 = ResultadoFase3CitasDatos(
        id_fragmento=id_fragmento,
        citas_textuales_extraidas=[],
        datos_cuantitativos_extraidos=[]
    )
    
    # Ejecutar
    resultado = ejecutar_fase_4(
        processor=processor,
        resultado_fase_1=resultado_fase_1,
        resultado_fase_2=resultado_fase_2,
        resultado_fase_3=resultado_fase_3,
        supabase_service=None
    )
    
    print(f"✅ Estado: {resultado.estado_general_normalizacion}")
    print(f"✅ Resumen: {resultado.resumen_normalizacion}")
    
    return resultado


def ejecutar_todos_los_tests():
    """Ejecuta todos los tests unitarios."""
    print("\n" + "="*60)
    print("EJECUTANDO TESTS UNITARIOS")
    print("="*60)
    
    try:
        # Test Fase 1
        test_fase_1_simple()
        
        # Test Fase 2
        test_fase_2_simple()
        
        # Test Fase 3
        test_fase_3_simple()
        
        # Test Fase 4
        test_fase_4_simple()
        
        print("\n\n✅ TODOS LOS TESTS UNITARIOS PASARON")
        return True
        
    except Exception as e:
        print(f"\n\n❌ Error en tests: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    ejecutar_todos_los_tests()
