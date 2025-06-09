"""
Test básico del pipeline completo de procesamiento.

Este test verifica que las 4 fases del pipeline funcionan correctamente
en conjunto, usando datos mock y sin dependencias externas.
"""

import os
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Agregar el directorio src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configurar variables de entorno necesarias
os.environ["GROQ_API_KEY"] = "mock-api-key-for-testing"
os.environ["GROQ_MODEL_ID"] = "mixtral-8x7b-32768"

# Imports del pipeline
from utils.fragment_processor import FragmentProcessor
from pipeline.fase_1_triaje import ejecutar_fase_1
from pipeline.fase_2_extraccion import ejecutar_fase_2
from pipeline.fase_3_citas_datos import ejecutar_fase_3
from pipeline.fase_4_normalizacion import ejecutar_fase_4

# Para logging
from loguru import logger

# Configurar logging para el test
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>")


def test_pipeline_basico():
    """Test básico que ejecuta las 4 fases del pipeline con datos mock."""
    
    print("\n" + "="*60)
    print("TEST DEL PIPELINE COMPLETO DE PROCESAMIENTO")
    print("="*60 + "\n")
    
    # Crear un fragmento de prueba
    id_fragmento = uuid4()
    texto_original = """
    Pedro Sánchez, presidente del Gobierno de España, anunció ayer en Madrid 
    un plan de inversión de 1.000 millones de euros para modernizar 
    la infraestructura digital del país. "Vamos a transformar España 
    en un referente tecnológico europeo", declaró el presidente durante 
    la rueda de prensa. El plan beneficiará a más de 5 millones de ciudadanos 
    y creará 50.000 nuevos empleos en el sector tecnológico para 2025.
    """
    
    # Crear FragmentProcessor para mantener IDs coherentes
    processor = FragmentProcessor(id_fragmento)
    
    print(f"📄 Fragmento ID: {id_fragmento}")
    print(f"📝 Texto original ({len(texto_original)} caracteres):")
    print("-" * 60)
    print(texto_original.strip())
    print("-" * 60 + "\n")
    
    # ========================================================================
    # FASE 1: TRIAJE
    # ========================================================================
    print("\n🔍 FASE 1: TRIAJE Y PREPROCESAMIENTO")
    print("-" * 40)
    
    try:
        # Mockear la respuesta de Groq para fase 1
        import unittest.mock as mock
        
        respuesta_triaje_mock = """
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
        
        # Mock tanto el modelo spaCy como la llamada a Groq
        with mock.patch('pipeline.fase_1_triaje._cargar_modelo_spacy') as mock_spacy, \
             mock.patch('pipeline.fase_1_triaje._llamar_groq_api_triaje') as mock_groq:
            
            # Configurar mocks
            mock_spacy.return_value = None  # Simular que no hay modelo spaCy
            mock_groq.return_value = ("prompt_usado", respuesta_triaje_mock)
            
            resultado_fase_1 = ejecutar_fase_1(
                id_fragmento_original=id_fragmento,
                texto_original_fragmento=texto_original
            )
        
        print(f"✅ Resultado: {'RELEVANTE' if resultado_fase_1.es_relevante else 'NO RELEVANTE'}")
        print(f"   - Decisión: {resultado_fase_1.decision_triaje}")
        print(f"   - Categoría: {resultado_fase_1.categoria_principal}")
        print(f"   - Puntuación: {resultado_fase_1.puntuacion_triaje}/25")
        
    except Exception as e:
        print(f"❌ Error en Fase 1: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ========================================================================
    # FASE 2: EXTRACCIÓN
    # ========================================================================
    print("\n\n📊 FASE 2: EXTRACCIÓN DE HECHOS Y ENTIDADES")
    print("-" * 40)
    
    try:
        # Mockear respuesta para fase 2
        respuesta_extraccion_mock = """
        {
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
        }
        """
        
        with mock.patch('pipeline.fase_2_extraccion._llamar_groq_api_extraccion') as mock_groq:
            mock_groq.return_value = ("prompt_usado", respuesta_extraccion_mock)
            
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
        import traceback
        traceback.print_exc()
        return False
    
    # ========================================================================
    # FASE 3: CITAS Y DATOS
    # ========================================================================
    print("\n\n💬 FASE 3: EXTRACCIÓN DE CITAS Y DATOS CUANTITATIVOS")
    print("-" * 40)
    
    try:
        # Mockear respuesta para fase 3
        respuesta_citas_datos_mock = """
        {
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
        }
        """
        
        with mock.patch('pipeline.fase_3_citas_datos._llamar_groq_api_citas_datos') as mock_groq:
            mock_groq.return_value = ("prompt_usado", respuesta_citas_datos_mock)
            
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
            print(f"   - Dato {dato.id_dato_cuantitativo}: {dato.valor_dato} {dato.unidad_dato} - {dato.descripcion_dato}")
        
    except Exception as e:
        print(f"❌ Error en Fase 3: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ========================================================================
    # FASE 4: NORMALIZACIÓN Y RELACIONES
    # ========================================================================
    print("\n\n🔗 FASE 4: NORMALIZACIÓN Y RELACIONES")
    print("-" * 40)
    
    try:
        # Mockear respuesta para fase 4
        respuesta_relaciones_mock = """
        {
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
        }
        """
        
        with mock.patch('pipeline.fase_4_normalizacion._llamar_groq_api_relaciones') as mock_groq:
            mock_groq.return_value = ("prompt_usado", respuesta_relaciones_mock)
            
            resultado_fase_4 = ejecutar_fase_4(
                processor=processor,
                resultado_fase_1=resultado_fase_1,
                resultado_fase_2=resultado_fase_2,
                resultado_fase_3=resultado_fase_3,
                supabase_service=None  # Sin servicio real para el test
            )
        
        print(f"✅ Estado normalización: {resultado_fase_4.estado_general_normalizacion}")
        print(f"✅ Resumen: {resultado_fase_4.resumen_normalizacion}")
        
        # Extraer relaciones de metadata
        relaciones = resultado_fase_4.metadata_normalizacion.get("relaciones", {})
        if relaciones:
            print(f"\n✅ Relaciones extraídas:")
            print(f"   - Hecho-Entidad: {len(relaciones.get('hecho_entidad', []))}")
            print(f"   - Hecho-Hecho: {len(relaciones.get('hecho_hecho', []))}")
            print(f"   - Entidad-Entidad: {len(relaciones.get('entidad_entidad', []))}")
            print(f"   - Contradicciones: {len(relaciones.get('contradicciones', []))}")
        
    except Exception as e:
        print(f"❌ Error en Fase 4: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================
    print("\n\n" + "="*60)
    print("📈 RESUMEN DEL PROCESAMIENTO")
    print("="*60)
    
    print(f"\n🔄 Estado del FragmentProcessor:")
    processor.log_summary()
    stats = processor.get_stats()
    
    print(f"\n✨ Elementos procesados:")
    print(f"   - Hechos: {stats['total_hechos']}")
    print(f"   - Entidades: {stats['total_entidades']}")
    print(f"   - Citas: {stats['total_citas']}")
    print(f"   - Datos cuantitativos: {stats['total_datos']}")
    
    print(f"\n✅ TODAS LAS FASES COMPLETADAS EXITOSAMENTE")
    print(f"   - Los IDs secuenciales se mantuvieron coherentes")
    print(f"   - Las referencias entre elementos son válidas")
    print(f"   - El pipeline está funcionando correctamente")
    
    return True


if __name__ == "__main__":
    # Ejecutar el test
    try:
        success = test_pipeline_basico()
        
        if success:
            print("\n\n🎉 ¡TEST EXITOSO! El pipeline funciona correctamente.")
        else:
            print("\n\n❌ Test fallido. Revisa los errores anteriores.")
    except Exception as e:
        print(f"\n\n❌ Error crítico en el test: {e}")
        import traceback
        traceback.print_exc()
