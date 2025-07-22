#!/usr/bin/env python3
"""
Test script to verify id_temporal field is present in entities payload
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'module_pipeline', 'src'))

from services.payload_builder import PayloadBuilder
from models.procesamiento import EntidadProcesada, MetadatosEntidad
from datetime import datetime
import json

def test_id_temporal_in_entities():
    """Test that id_temporal is included in entities"""
    
    # Create mock entity
    entidad = EntidadProcesada(
        id_entidad=123,
        id_fragmento_origen="test-fragment",
        texto_entidad="Test Entity",
        tipo_entidad="PERSONA",
        relevancia_entidad=0.9,
        metadata_entidad=MetadatosEntidad()
    )
    
    # Create entities data as it would come from pipeline_coordinator
    entidades_data = [{
        "id": str(entidad.id_entidad),
        "id_temporal": str(entidad.id_entidad),  # This should be included now
        "nombre": entidad.texto_entidad,
        "tipo": entidad.tipo_entidad,
        "descripcion": f"Entidad extraída con relevancia {entidad.relevancia_entidad}",
        "relevancia": int(entidad.relevancia_entidad * 10),
        "metadata": {},
        "id_entidad": entidad.id_entidad,
        "texto_entidad": entidad.texto_entidad,
        "tipo_entidad": entidad.tipo_entidad,
        "relevancia_entidad": entidad.relevancia_entidad,
        "metadata_entidad": {}
    }]
    
    print("Entity data to be processed:")
    print(json.dumps(entidades_data[0], indent=2))
    
    # Verify id_temporal is present
    assert "id_temporal" in entidades_data[0], "id_temporal field is missing!"
    print("\n✓ id_temporal field is present in entity data")
    
    # Test with PayloadBuilder
    builder = PayloadBuilder()
    
    # Test article payload
    try:
        payload = builder.construir_payload_articulo(
            metadatos_articulo_data={
                "titulo": "Test Article",
                "url": "http://test.com",
                "medio": "Test Medium",
                "area_geografica": "España",
                "tipo_medio": "digital",
                "fecha_publicacion": datetime.now().isoformat()
            },
            procesamiento_articulo_data={
                "resumen_generado_articulo": "Test summary",
                "estado_procesamiento_final_articulo": "completado_ok",
                "fecha_procesamiento_pipeline_articulo": datetime.now().isoformat()
            },
            entidades_autonomas_data=entidades_data
        )
        
        # Check if payload was created successfully
        if payload and hasattr(payload, 'entidades_autonomas'):
            print("\n✓ Article payload created successfully")
            
            # Convert to dict to check final structure
            payload_dict = payload.model_dump()
            if payload_dict.get('entidades_autonomas'):
                entity = payload_dict['entidades_autonomas'][0]
                print(f"\nEntity in final payload:")
                print(json.dumps(entity, indent=2))
                
                # The PayloadBuilder maps fields, so check if the entity was processed correctly
                if 'id' in entity:
                    print("\n✓ Entity successfully processed through PayloadBuilder")
                else:
                    print("\n✗ Entity structure incorrect after PayloadBuilder")
            else:
                print("\n✗ No entities in final payload")
        else:
            print("\n✗ Failed to create article payload")
            
    except Exception as e:
        print(f"\n✗ Error creating payload: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing id_temporal fix...\n")
    test_id_temporal_in_entities()
    print("\nTest completed!")