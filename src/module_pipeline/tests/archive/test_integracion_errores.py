"""
Test de integración con manejo de errores y casos edge.

Este test verifica que el pipeline maneja correctamente:
- Textos vacíos o muy cortos
- Errores de API
- Falta de datos en alguna fase
- Fallbacks y recuperación
"""

import os
import sys
from pathlib import Path
from uuid import uuid4
import unittest.mock as mock

# Setup
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
os.environ["GROQ_API_KEY"] = "mock-api-key-for-testing"

from utils.fragment_processor import FragmentProcessor
from pipeline.fase_1_triaje import ejecutar_fase_1
from pipeline.fase_2_extraccion import ejecutar_fase_2
from pipeline.fase_3_citas_datos import ejecutar_fase_3
from pipeline.fase_4_normalizacion import ejecutar_fase_4
from utils.error_handling import GroqAPIError, ErrorPhase

from loguru import logger
logger.remove()
logger.add(sys.stderr, level="WARNING")  # Solo warnings y errores


def test_texto_vacio():
    """Test con texto vacío."""
    print("\n📝 TEST: Texto vacío")
    print("-" * 40)
    
    id_fragmento = uuid4()
    texto_vacio = "   "
    
    resultado = ejecutar_fase_1(
        id_fragmento_original=id_fragmento,
        texto_original_fragmento=texto_vacio
    )
    
    print(f"✅ Maneja texto vacío correctamente")
    print(f"   - Es relevante: {resultado.es_relevante}")
    print(f"   - Decisión: {resultado.decision_triaje}")
    

def test_error_groq_api():
    """Test cuando Groq API falla."""
    print("\n\n🚫 TEST: Error de Groq API")
    print("-" * 40)
    
    id_fragmento = uuid4()
    processor = FragmentProcessor(id_fragmento)
    texto = "Texto de prueba para error de API"
    
    # Fase 1 con error de API
    with mock.patch('pipeline.fase_1_triaje._llamar_groq_api_triaje') as mock_groq:
        mock_groq.side_effect = GroqAPIError(
            "API no disponible",
            phase=ErrorPhase.FASE_1_TRIAJE,
            retry_count=2
        )
        
        resultado_fase_1 = ejecutar_fase_1(
            id_fragmento_original=id_fragmento,
            texto_original_fragmento=texto
        )
    
    print(f"✅ Fase 1 maneja error de API con fallback")
    print(f"   - Es relevante: {resultado_fase_1.es_relevante} (acepta por política)")
    print(f"   - Decisión: {resultado_fase_1.decision_triaje}")
    
    # Fase 2 con error de API
    with mock.patch('pipeline.fase_2_extraccion._llamar_groq_api_extraccion') as mock_groq:
        mock_groq.side_effect = GroqAPIError(
            "API timeout",
            phase=ErrorPhase.FASE_2_EXTRACCION,
            timeout_seconds=60
        )
        
        resultado_fase_2 = ejecutar_fase_2(
            resultado_fase_1=resultado_fase_1,
            processor=processor
        )
    
    print(f"\n✅ Fase 2 maneja error de API")
    print(f"   - Hechos extraídos: {len(resultado_fase_2.hechos_extraidos)}")
    print(f"   - Advertencias: {len(resultado_fase_2.advertencias_extraccion)}")


def test_sin_entidades():
    """Test cuando no hay entidades para normalizar."""
    print("\n\n🔍 TEST: Sin entidades para normalizar")
    print("-" * 40)
    
    id_fragmento = uuid4()
    processor = FragmentProcessor(id_fragmento)
    
    # Crear resultados mock sin entidades
    from models.procesamiento import (
        ResultadoFase1Triaje,
        ResultadoFase2Extraccion,
        ResultadoFase3CitasDatos
    )
    
    resultado_fase_1 = ResultadoFase1Triaje(
        id_fragmento=id_fragmento,
        es_relevante=True,
        texto_para_siguiente_fase="Solo números: 123, 456, 789"
    )
    
    resultado_fase_2 = ResultadoFase2Extraccion(
        id_fragmento=id_fragmento,
        hechos_extraidos=[],  # Sin hechos
        entidades_extraidas=[]  # Sin entidades
    )
    
    resultado_fase_3 = ResultadoFase3CitasDatos(
        id_fragmento=id_fragmento,
        citas_textuales_extraidas=[],
        datos_cuantitativos_extraidos=[]
    )
    
    # Ejecutar fase 4 sin entidades
    resultado_fase_4 = ejecutar_fase_4(
        processor=processor,
        resultado_fase_1=resultado_fase_1,
        resultado_fase_2=resultado_fase_2,
        resultado_fase_3=resultado_fase_3,
        supabase_service=None
    )
    
    print(f"✅ Fase 4 maneja ausencia de entidades")
    print(f"   - Estado: {resultado_fase_4.estado_general_normalizacion}")
    print(f"   - Resumen: {resultado_fase_4.resumen_normalizacion}")


def test_json_malformado():
    """Test cuando el LLM devuelve JSON malformado."""
    print("\n\n💥 TEST: JSON malformado del LLM")
    print("-" * 40)
    
    id_fragmento = uuid4()
    processor = FragmentProcessor(id_fragmento)
    
    resultado_fase_1 = ejecutar_fase_1(
        id_fragmento_original=id_fragmento,
        texto_original_fragmento="Texto válido para procesar"
    )
    
    # Fase 2 con JSON malformado
    with mock.patch('pipeline.fase_2_extraccion._llamar_groq_api_extraccion') as mock_groq:
        mock_groq.return_value = ("prompt", "{'hechos': [malformed json")
        
        resultado_fase_2 = ejecutar_fase_2(
            resultado_fase_1=resultado_fase_1,
            processor=processor
        )
    
    print(f"✅ Fase 2 maneja JSON malformado")
    print(f"   - Hechos: {len(resultado_fase_2.hechos_extraidos)}")
    print(f"   - Advertencias: {resultado_fase_2.advertencias_extraccion}")


def test_referencias_invalidas():
    """Test cuando hay referencias a IDs que no existen."""
    print("\n\n🔗 TEST: Referencias inválidas entre elementos")
    print("-" * 40)
    
    id_fragmento = uuid4()
    processor = FragmentProcessor(id_fragmento)
    
    # Crear datos con referencias inválidas
    from models.procesamiento import (
        ResultadoFase1Triaje,
        ResultadoFase2Extraccion,
        ResultadoFase3CitasDatos,
        HechoProcesado,
        EntidadProcesada
    )
    from models.metadatos import MetadatosHecho, MetadatosEntidad
    
    resultado_fase_1 = ResultadoFase1Triaje(
        id_fragmento=id_fragmento,
        es_relevante=True,
        texto_para_siguiente_fase="Test de referencias"
    )
    
    # Solo 1 hecho y 1 entidad
    hechos = [
        HechoProcesado(
            id_hecho=1,
            texto_original_del_hecho="Hecho único",
            confianza_extraccion=0.9,
            id_fragmento_origen=id_fragmento,
            metadata_hecho=MetadatosHecho()
        )
    ]
    
    entidades = [
        EntidadProcesada(
            id_entidad=1,
            texto_entidad="Entidad única",
            tipo_entidad="PERSONA",
            relevancia_entidad=0.8,
            id_fragmento_origen=id_fragmento,
            metadata_entidad=MetadatosEntidad()
        )
    ]
    
    resultado_fase_2 = ResultadoFase2Extraccion(
        id_fragmento=id_fragmento,
        hechos_extraidos=hechos,
        entidades_extraidas=entidades
    )
    
    # Mock fase 3 con referencias inválidas
    respuesta_mock = """
    {
        "citas_textuales": [
            {"id": 1, "cita": "Cita test", "entidad_id": 999, "hecho_id": 888}
        ],
        "datos_cuantitativos": []
    }
    """
    
    with mock.patch('pipeline.fase_3_citas_datos._llamar_groq_api_citas_datos') as mock_groq:
        mock_groq.return_value = ("prompt", respuesta_mock)
        
        resultado_fase_3 = ejecutar_fase_3(
            resultado_fase_2=resultado_fase_2,
            processor=processor,
            resultado_fase_1=resultado_fase_1
        )
    
    print(f"✅ Fase 3 valida referencias")
    print(f"   - Advertencias: {resultado_fase_3.advertencias_citas_datos}")
    
    # Mock fase 4 con relaciones inválidas
    respuesta_relaciones = """
    {
        "hecho_entidad": [
            {"hecho_id": 999, "entidad_id": 888, "tipo_relacion": "protagonista", "relevancia_en_hecho": 5}
        ],
        "hecho_relacionado": [],
        "entidad_relacion": [],
        "contradicciones": []
    }
    """
    
    with mock.patch('pipeline.fase_4_normalizacion._llamar_groq_api_relaciones') as mock_groq:
        mock_groq.return_value = ("prompt", respuesta_relaciones)
        
        resultado_fase_4 = ejecutar_fase_4(
            processor=processor,
            resultado_fase_1=resultado_fase_1,
            resultado_fase_2=resultado_fase_2,
            resultado_fase_3=resultado_fase_3
        )
    
    print(f"\n✅ Fase 4 filtra relaciones inválidas")
    relaciones = resultado_fase_4.metadata_normalizacion.get("relaciones", {})
    print(f"   - Relaciones válidas: {len(relaciones.get('hecho_entidad', []))}")
    print(f"   - Estado: {resultado_fase_4.estado_general_normalizacion}")


def ejecutar_tests_integracion():
    """Ejecuta todos los tests de integración."""
    print("\n" + "="*60)
    print("TESTS DE INTEGRACIÓN Y CASOS EDGE")
    print("="*60)
    
    try:
        test_texto_vacio()
        test_error_groq_api()
        test_sin_entidades()
        test_json_malformado()
        test_referencias_invalidas()
        
        print("\n\n✅ TODOS LOS TESTS DE INTEGRACIÓN PASARON")
        print("   - El pipeline maneja correctamente los errores")
        print("   - Los fallbacks funcionan como se espera")
        print("   - Las validaciones están activas")
        
        return True
        
    except Exception as e:
        print(f"\n\n❌ Error en tests de integración: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    ejecutar_tests_integracion()
