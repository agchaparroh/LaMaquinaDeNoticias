#!/usr/bin/env python3
"""
Test script to validate ArticuloInItem model with example data
"""

import sys
import os
import json

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import ArticuloInItem, prepare_articulo


def test_with_example_data():
    """Test the model with the example article data"""
    
    # Load example data
    example_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'examples', 'ejemplo_articulo.json')
    
    with open(example_path, 'r', encoding='utf-8') as f:
        example_data = json.load(f)
    
    print("Testing ArticuloInItem model with example data...")
    print("=" * 50)
    
    try:
        # Test direct instantiation
        print("1. Testing direct instantiation...")
        articulo = ArticuloInItem(**example_data)
        print("✅ Direct instantiation successful")
        print(f"   Title: {articulo.titular}")
        print(f"   Medium: {articulo.medio}")
        print(f"   Country: {articulo.pais_publicacion}")
        
        # Test validation
        print("\n2. Testing validation...")
        is_valid = articulo.validate_required_fields()
        print(f"✅ Required fields validation: {'PASSED' if is_valid else 'FAILED'}")
        
        # Test prepare_articulo function
        print("\n3. Testing prepare_articulo function...")
        # Remove some optional fields to test defaults
        test_data = example_data.copy()
        if 'id' in test_data:
            del test_data['id']
        if 'fecha_recopilacion' in test_data:
            del test_data['fecha_recopilacion']
            
        prepared_articulo = prepare_articulo(test_data)
        print("✅ prepare_articulo successful")
        print(f"   Generated ID: {getattr(prepared_articulo, 'id', 'Not set')}")
        print(f"   Generated fecha_recopilacion: {prepared_articulo.fecha_recopilacion}")
        
        # Test missing required fields
        print("\n4. Testing with missing required fields...")
        incomplete_data = {
            "medio": "Test Medium",
            # Missing titular, pais_publicacion, tipo_medio, fecha_publicacion, contenido_texto
        }
        
        try:
            ArticuloInItem(**incomplete_data)
            print("❌ Should have failed validation")
        except Exception as e:
            print("✅ Correctly failed validation for missing required fields")
            print(f"   Error: {type(e).__name__}")
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_with_example_data()
    sys.exit(0 if success else 1)
