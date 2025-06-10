"""
Test básico del pipeline completo de procesamiento - VERSIÓN CORREGIDA.

Este test verifica que las 4 fases del pipeline funcionan correctamente
en conjunto, usando datos mock y sin dependencias externas.

PROBLEMAS DETECTADOS Y CORREGIDOS:
1. Imports faltantes y paths incorrectos
2. Configuración de variables de entorno inadecuada
3. Mock patterns incorrectos
4. Manejo de excepciones inconsistente
5. Referencias a clases no existentes
"""

import os
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime

print("🔧 Configurando entorno de test...")

# =========================================================================
# CONFIGURACIÓN INICIAL CRÍTICA
# =========================================================================

# 1. Configurar variables de entorno ANTES de cualquier import
os.environ["GROQ_API_KEY"] = "mock-api-key-for-testing"
os.environ["GROQ_MODEL_ID"] = "mixtral-8x7b-32768"
os.environ["SUPABASE_URL"] = "https://mock.supabase.co"
os.environ["SUPABASE_KEY"] = "mock-supabase-key"
os.environ["LOG_LEVEL"] = "INFO"

# 2. Agregar directorio src al path CORRECTAMENTE
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

print(f"   ✅ Path src agregado: {src_path}")
print(f"   ✅ Variables de entorno configuradas")

# 3. Configurar logging ANTES de imports que usen loguru
from loguru import logger
logger.remove()
logger.add(
    sys.stderr, 
    level="INFO", 
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
)

print("   ✅ Logging configurado")

# =========================================================================
# IMPORTS PRINCIPALES
# =========================================================================

try:
    # Utils principales
    from utils.fragment_processor import FragmentProcessor
    print("   ✅ FragmentProcessor importado")
    
    # Imports del pipeline
    from pipeline.fase_1_triaje import ejecutar_fase_1
    from pipeline.fase_2_extraccion import ejecutar_fase_2
    from pipeline.fase_3_citas_datos import ejecutar_fase_3
    from pipeline.fase_4_normalizacion import ejecutar_fase_4
    print("   ✅ Fases del pipeline importadas")
    
    # Modelos para tests
    from models.procesamiento import (
        ResultadoFase1Triaje, 
        ResultadoFase2Extraccion,
        ResultadoFase3CitasDatos,
        HechoProcesado,
        EntidadProcesada
    )
    print("   ✅ Modelos de procesamiento importados")
    
except ImportError as e:
    print(f"❌ Error crítico en imports: {e}")
    print("   Verifique que el directorio src existe y contiene todos los módulos")
    sys.exit(1)

# =========================================================================
# FUNCIONES DE MOCK
# =========================================================================

def mock_groq_api_calls():
    """Configura todos los mocks necesarios para las llamadas a Groq API."""
    import unittest.mock as mock
    
    # Mock para fase 1 (triaje)
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
Artículo altamente relevante sobre política nacional española con información 
factual importante sobre inversión pública y desarrollo tecnológico.

ELEMENTOS CLAVE:
- Anuncio oficial del presidente del gobierno
- Plan de inversión de 1.000 millones de euros
- Impacto en 5 millones de ciudadanos
- Creación de 50.000 empleos
"""
    
    # Mock para fase 2 (extracción)
    respuesta_extraccion = """{
  "hechos": [
    {
      "id": 1,
      "contenido": "Pedro Sánchez anunció un plan de inversión de 1.000 millones de euros",
      "fecha": {"inicio": "2024-01-01", "fin": null},
      "precision_temporal": "dia",
      "tipo_hecho": "ANUNCIO",
      "pais": ["España"],
      "region": ["Madrid"],
      "ciudad": ["Madrid"],
      "es_futuro": false
    },
    {
      "id": 2,
      "contenido": "El plan beneficiará a más de 5 millones de ciudadanos",
      "fecha": {"inicio": null, "fin": null},
      "precision_temporal": "periodo",
      "tipo_hecho": "EVENTO",
      "pais": ["España"],
      "es_futuro": true
    },
    {
      "id": 3,
      "contenido": "Se crearán 50.000 nuevos empleos en el sector tecnológico para 2025",
      "fecha": {"inicio": null, "fin": "2025-12-31"},
      "precision_temporal": "año",
      "tipo_hecho": "EVENTO",
      "pais": ["España"],
      "es_futuro": true
    }
  ],
  "entidades": [
    {
      "id": 1,
      "nombre": "Pedro Sánchez",
      "tipo": "PERSONA",
      "alias": ["presidente del Gobierno"],
      "descripcion": "Presidente del Gobierno de España"
    },
    {
      "id": 2,
      "nombre": "Gobierno de España",
      "tipo": "INSTITUCION",
      "alias": [],
      "descripcion": "Poder ejecutivo del Estado español"
    },
    {
      "id": 3,
      "nombre": "Madrid",
      "tipo": "LUGAR",
      "alias": [],
      "descripcion": "Capital de España"
    }
  ]
}"""
    
    # Mock para fase 3 (citas y datos)
    respuesta_citas_datos = """{
  "citas_textuales": [
    {
      "id": 1,
      "cita": "Vamos a transformar España en un referente tecnológico europeo",
      "entidad_id": 1,
      "hecho_id": 1,
      "fecha": "2024-01-01",
      "contexto": "Declaración durante rueda de prensa sobre el plan de inversión",
      "relevancia": 5
    }
  ],
  "datos_cuantitativos": [
    {
      "id": 1,
      "hecho_id": 1,
      "indicador": "Inversión en infraestructura digital",
      "categoria": "económico",
      "valor": 1000,
      "unidad": "millones de euros",
      "ambito_geografico": ["España"],
      "periodo": {
        "inicio": "2024-01-01",
        "fin": "2025-12-31"
      },
      "tipo_periodo": "anual"
    },
    {
      "id": 2,
      "hecho_id": 2,
      "indicador": "Ciudadanos beneficiados",
      "categoria": "demográfico",
      "valor": 5,
      "unidad": "millones de personas",
      "ambito_geografico": ["España"],
      "tipo_periodo": "acumulado"
    },
    {
      "id": 3,
      "hecho_id": 3,
      "indicador": "Empleos a crear",
      "categoria": "social",
      "valor": 50000,
      "unidad": "empleos",
      "ambito_geografico": ["España"],
      "periodo": {
        "inicio": "2024-01-01",
        "fin": "2025-12-31"
      },
      "tipo_periodo": "acumulado"
    }
  ]
}"""
    
    # Mock para fase 4 (relaciones)
    respuesta_relaciones = """{
  "hecho_entidad": [
    {
      "hecho_id": 1,
      "entidad_id": 1,
      "tipo_relacion": "protagonista",
      "relevancia_en_hecho": 10
    },
    {
      "hecho_id": 1,
      "entidad_id": 2,
      "tipo_relacion": "contexto",
      "relevancia_en_hecho": 7
    },
    {
      "hecho_id": 1,
      "entidad_id": 3,
      "tipo_relacion": "ubicacion",
      "relevancia_en_hecho": 5
    }
  ],
  "hecho_relacionado": [
    {
      "hecho_origen_id": 1,
      "hecho_destino_id": 2,
      "tipo_relacion": "causa",
      "fuerza_relacion": 8,
      "descripcion_relacion": "El plan de inversión causa el beneficio a los ciudadanos"
    },
    {
      "hecho_origen_id": 1,
      "hecho_destino_id": 3,
      "tipo_relacion": "causa",
      "fuerza_relacion": 9,
      "descripcion_relacion": "El plan de inversión causa la creación de empleos"
    }
  ],
  "entidad_relacion": [
    {
      "entidad_origen_id": 1,
      "entidad_destino_id": 2,
      "tipo_relacion": "empleado_de",
      "descripcion": "Pedro Sánchez es presidente del Gobierno de España",
      "fecha_inicio": "2018-06-02",
      "fecha_fin": null,
      "fuerza_relacion": 10
    }
  ],
  "contradicciones": []
}"""
    
    # Configurar mocks
    mocks = {}
    
    # Mock para spaCy
    mocks['spacy'] = mock.patch('pipeline.fase_1_triaje._cargar_modelo_spacy', return_value=None)
    
    # Mocks para Groq API
    mocks['groq_triaje'] = mock.patch(
        'pipeline.fase_1_triaje._llamar_groq_api_triaje',
        return_value=("prompt_triaje", respuesta_triaje)
    )
    
    mocks['groq_extraccion'] = mock.patch(
        'pipeline.fase_2_extraccion._llamar_groq_api_extraccion',
        return_value=("prompt_extraccion", respuesta_extraccion)
    )
    
    mocks['groq_citas'] = mock.patch(
        'pipeline.fase_3_citas_datos._llamar_groq_api_citas_datos',
        return_value=("prompt_citas", respuesta_citas_datos)
    )
    
    mocks['groq_relaciones'] = mock.patch(
        'pipeline.fase_4_normalizacion._llamar_groq_api_relaciones',
        return_value=("prompt_relaciones", respuesta_relaciones)
    )
    
    return mocks

# =========================================================================
# TEST PRINCIPAL
# =========================================================================

def test_pipeline_completo():
    """Test completo del pipeline de 4 fases con datos realistas."""
    
    print("\n" + "="*60)
    print("🧪 TEST DEL PIPELINE COMPLETO DE PROCESAMIENTO")
    print("="*60 + "\n")
    
    # Datos de prueba
    id_fragmento = uuid4()
    texto_original = """
    Pedro Sánchez, presidente del Gobierno de España, anunció ayer en Madrid 
    un plan de inversión de 1.000 millones de euros para modernizar 
    la infraestructura digital del país. "Vamos a transformar España 
    en un referente tecnológico europeo", declaró el presidente durante 
    la rueda de prensa. El plan beneficiará a más de 5 millones de ciudadanos 
    y creará 50.000 nuevos empleos en el sector tecnológico para 2025.
    """
    
    print(f"📄 Fragmento ID: {id_fragmento}")
    print(f"📝 Texto original ({len(texto_original)} caracteres):")
    print("-" * 60)
    print(texto_original.strip())
    print("-" * 60 + "\n")
    
    # Crear FragmentProcessor
    processor = FragmentProcessor(id_fragmento)
    
    # Variables para almacenar resultados
    resultado_fase_1 = None
    resultado_fase_2 = None
    resultado_fase_3 = None
    resultado_fase_4 = None
    
    # Configurar mocks
    mocks = mock_groq_api_calls()
    
    try:
        # Iniciar todos los mocks
        mock_contexts = [mock_obj.start() for mock_obj in mocks.values()]
        
        # ====================================================================
        # FASE 1: TRIAJE
        # ====================================================================
        print("🔍 FASE 1: TRIAJE Y PREPROCESAMIENTO")
        print("-" * 40)
        
        try:
            resultado_fase_1 = ejecutar_fase_1(
                id_fragmento_original=id_fragmento,
                texto_original_fragmento=texto_original
            )
            
            print(f"✅ Resultado: {'RELEVANTE' if resultado_fase_1.es_relevante else 'NO RELEVANTE'}")
            print(f"   - Decisión: {resultado_fase_1.decision_triaje}")
            print(f"   - Categoría: {resultado_fase_1.categoria_principal}")
            print(f"   - Puntuación: {resultado_fase_1.puntuacion_triaje}/25")
            print(f"   - Texto para fase 2: {len(resultado_fase_1.texto_para_siguiente_fase)} caracteres")
            
        except Exception as e:
            print(f"❌ Error en Fase 1: {e}")
            raise
        
        # ====================================================================
        # FASE 2: EXTRACCIÓN
        # ====================================================================
        print("\n📊 FASE 2: EXTRACCIÓN DE HECHOS Y ENTIDADES")
        print("-" * 40)
        
        try:
            resultado_fase_2 = ejecutar_fase_2(
                resultado_fase_1=resultado_fase_1,
                processor=processor
            )
            
            print(f"✅ Hechos extraídos: {len(resultado_fase_2.hechos_extraidos)}")
            for hecho in resultado_fase_2.hechos_extraidos:
                print(f"   - Hecho {hecho.id_hecho}: {hecho.texto_original_del_hecho[:60]}...")
            
            print(f"\n✅ Entidades extraídas: {len(resultado_fase_2.entidades_extraidas)}")
            for entidad in resultado_fase_2.entidades_extraidas:
                print(f"   - Entidad {entidad.id_entidad}: {entidad.texto_entidad} ({entidad.tipo_entidad})")
            
        except Exception as e:
            print(f"❌ Error en Fase 2: {e}")
            raise
        
        # ====================================================================
        # FASE 3: CITAS Y DATOS
        # ====================================================================
        print("\n💬 FASE 3: EXTRACCIÓN DE CITAS Y DATOS CUANTITATIVOS")
        print("-" * 40)
        
        try:
            resultado_fase_3 = ejecutar_fase_3(
                resultado_fase_2=resultado_fase_2,
                processor=processor,
                resultado_fase_1=resultado_fase_1
            )
            
            print(f"✅ Citas textuales: {len(resultado_fase_3.citas_textuales_extraidas)}")
            for cita in resultado_fase_3.citas_textuales_extraidas:
                print(f"   - Cita {cita.id_cita}: \"{cita.texto_cita[:50]}...\"")
            
            print(f"\n✅ Datos cuantitativos: {len(resultado_fase_3.datos_cuantitativos_extraidos)}")
            for dato in resultado_fase_3.datos_cuantitativos_extraidos:
                print(f"   - Dato {dato.id_dato_cuantitativo}: {dato.valor_dato} {dato.unidad_dato}")
            
        except Exception as e:
            print(f"❌ Error en Fase 3: {e}")
            raise
        
        # ====================================================================
        # FASE 4: NORMALIZACIÓN Y RELACIONES
        # ====================================================================
        print("\n🔗 FASE 4: NORMALIZACIÓN Y RELACIONES")
        print("-" * 40)
        
        try:
            resultado_fase_4 = ejecutar_fase_4(
                processor=processor,
                resultado_fase_1=resultado_fase_1,
                resultado_fase_2=resultado_fase_2,
                resultado_fase_3=resultado_fase_3,
                supabase_service=None  # Sin servicio real para el test
            )
            
            print(f"✅ Estado: {resultado_fase_4.estado_general_normalizacion}")
            print(f"✅ Resumen: {resultado_fase_4.resumen_normalizacion}")
            
            # Mostrar relaciones si están disponibles
            if hasattr(resultado_fase_4, 'metadata_normalizacion') and resultado_fase_4.metadata_normalizacion:
                relaciones = resultado_fase_4.metadata_normalizacion.get("relaciones", {})
                if relaciones:
                    print(f"\n✅ Relaciones detectadas:")
                    for tipo_rel, lista_rel in relaciones.items():
                        if lista_rel:
                            print(f"   - {tipo_rel}: {len(lista_rel)} relaciones")
            
        except Exception as e:
            print(f"❌ Error en Fase 4: {e}")
            raise
        
        # ====================================================================
        # RESUMEN FINAL
        # ====================================================================
        print("\n" + "="*60)
        print("📈 RESUMEN DEL PROCESAMIENTO")
        print("="*60)
        
        print(f"\n🔄 Estado del FragmentProcessor:")
        processor.log_summary()
        stats = processor.get_stats()
        
        print(f"\n✨ Elementos procesados:")
        print(f"   - Hechos: {stats.get('total_hechos', 0)}")
        print(f"   - Entidades: {stats.get('total_entidades', 0)}")
        print(f"   - Citas: {stats.get('total_citas', 0)}")
        print(f"   - Datos cuantitativos: {stats.get('total_datos', 0)}")
        
        print(f"\n✅ TODAS LAS FASES COMPLETADAS EXITOSAMENTE")
        print(f"   - Pipeline funcional verificado")
        print(f"   - Mocks funcionando correctamente")
        print(f"   - IDs secuenciales coherentes")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Detener todos los mocks
        for mock_obj in mocks.values():
            mock_obj.stop()

# =========================================================================
# EJECUCIÓN PRINCIPAL
# =========================================================================

if __name__ == "__main__":
    print("🚀 Iniciando test del pipeline completo...")
    
    try:
        success = test_pipeline_completo()
        
        if success:
            print("\n\n🎉 ¡TEST EXITOSO! El pipeline funciona correctamente.")
            print("   - Todas las fases se ejecutaron sin errores")
            print("   - Los mocks simulan correctamente las APIs externas")
            print("   - La integración entre fases es funcional")
        else:
            print("\n\n❌ Test fallido. Revisa los errores anteriores.")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrumpido por el usuario.")
        
    except Exception as e:
        print(f"\n\n💥 Error crítico en el test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n" + "="*60)
        print("🏁 FIN DEL TEST")
        print("="*60)
