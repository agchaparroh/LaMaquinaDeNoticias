#!/usr/bin/env python3
"""
Test script para validar corrección de E004
"""
import sys
import os
import uuid
from datetime import datetime

# Agregar el directorio src al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Imports necesarios
from src.controller import PipelineController
from src.models.entrada import FragmentoProcesableItem

def main():
    print("=== TEST PIPELINE E004 ===")
    print(f"Timestamp: {datetime.now()}")
    
    # Crear controller
    controller = PipelineController()
    print("✓ Controller creado")
    
    # Crear fragmento de prueba
    fragmento_data = {
        "id_fragmento": str(uuid.uuid4()),
        "texto_original": """
        El presidente Pedro Sánchez anunció hoy nuevas medidas económicas 
        destinadas a combatir la inflación. El paquete incluye una inversión 
        de 2.500 millones de euros y beneficiará a más de 3 millones de familias.
        "Es fundamental proteger el poder adquisitivo", declaró Sánchez.
        La inflación alcanzó el 5.5% en el último trimestre.
        """,
        "id_articulo_fuente": "test_article_e004",
        "orden_en_articulo": 1
    }
    
    fragmento = FragmentoProcesableItem(**fragmento_data)
    print(f"✓ Fragmento creado: {fragmento.id_fragmento}")
    
    # Ejecutar pipeline
    try:
        resultado = controller.pipeline_coordinator.ejecutar_pipeline_completo(
            fragmento=fragmento,
            modelo_spacy="es_core_news_lg",
            request_id=str(uuid.uuid4()),
            groq_api_key=os.environ.get("GROQ_API_KEY"),
            contexto_articulo={
                "titulo": "Test Article E004",
                "fecha_publicacion": datetime.now().isoformat(),
                "fuente": "test"
            }
        )
        
        print(f"\n✓ Pipeline ejecutado")
        print(f"  - Éxito: {resultado['exito']}")
        print(f"  - Fase completada: {resultado['fase_completada']}")
        print(f"  - Errores: {resultado['errores']}")
        
        if resultado['exito']:
            print("\n✅ E004 CORREGIDO - Pipeline completado exitosamente")
            if 'metadatos' in resultado and 'processor_stats' in resultado['metadatos']:
                stats = resultado['metadatos']['processor_stats']
                print(f"\nEstadísticas:")
                print(f"  - Hechos: {stats.get('total_hechos', 0)}")
                print(f"  - Entidades: {stats.get('total_entidades', 0)}")
                print(f"  - Citas: {stats.get('total_citas', 0)}")
                print(f"  - Datos: {stats.get('total_datos', 0)}")
        else:
            print(f"\n❌ Pipeline falló: {resultado['errores']}")
            
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()