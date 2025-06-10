#!/usr/bin/env python3
"""
Test para descubrir la estructura exacta de la tabla articulos.
"""

import os
import sys
from pathlib import Path

# Set environment variables directly
os.environ['SUPABASE_URL'] = 'https://aukbzqbcvbsnjdhflyvr.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1a2J6cWJjdmJzbmpkaGZseXZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5MTI2NjYsImV4cCI6MjA2MTQ4ODY2Nn0.KfRQ1Jv7HIGwMHUS8e8IgN92iv1go7VvyK-6wqgog3s'

# Add scraper directory to path
scraper_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scraper_dir))

from scraper_core.utils.supabase_client import SupabaseClient
from datetime import datetime, timezone
import uuid

def discover_table_structure():
    """Descubre la estructura exacta de la tabla articulos."""
    print("🧪 DISCOVERING ARTICULOS TABLE STRUCTURE")
    print("=" * 60)
    
    try:
        client = SupabaseClient()
        print("✅ Connected to Supabase")
        
        # Try to get schema information or any existing record to see structure
        print("\n🔍 Attempting to discover table structure...")
        
        # Method 1: Try to insert with minimal data to see what fields are required
        test_data_minimal = {
            'url': f'http://test.example.com/structure-test-{uuid.uuid4()}',
        }
        
        try:
            response = client.client.table('articulos').insert(test_data_minimal).execute()
            print(f"✅ Minimal insertion successful: {response}")
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️  Minimal insertion failed (expected): {error_msg}")
            
            # Parse error message to understand required fields
            if "null value in column" in error_msg:
                print("📋 Found required fields from error message:")
                # Extract field names from error
                import re
                matches = re.findall(r'column "(\w+)"', error_msg)
                if matches:
                    print(f"   Required fields detected: {matches}")
        
        # Method 2: Try common field combinations
        print(f"\n🧪 Testing common field structures...")
        
        test_variations = [
            {
                'url': f'http://test.example.com/test1-{uuid.uuid4()}',
                'titular': 'Test Article',  # usando 'titular' en lugar de 'titulo'
                'medio_nombre': 'Test Medio',
                'fecha_extraccion': datetime.now(timezone.utc).isoformat(),
            },
            {
                'url': f'http://test.example.com/test2-{uuid.uuid4()}',
                'titular': 'Test Article 2',
                'medio': 'Test Medio',  # probando 'medio' en lugar de 'medio_nombre'
                'fecha_extraccion': datetime.now(timezone.utc).isoformat(),
            },
            {
                'url': f'http://test.example.com/test3-{uuid.uuid4()}',
                'titular': 'Test Article 3',
                'fecha_extraccion': datetime.now(timezone.utc).isoformat(),
                'contenido_texto': 'Test content',
            }
        ]
        
        successful_structure = None
        
        for i, test_data in enumerate(test_variations, 1):
            try:
                print(f"\n   Variation {i}: {list(test_data.keys())}")
                response = client.client.table('articulos').insert(test_data).execute()
                print(f"   ✅ SUCCESS! Structure working: {list(test_data.keys())}")
                successful_structure = test_data
                
                # Verify insertion
                inserted_url = test_data['url']
                verify_response = client.client.table('articulos').select('*').eq('url', inserted_url).execute()
                if verify_response.data:
                    print(f"   ✅ Verification successful. Record structure:")
                    record = verify_response.data[0]
                    for key, value in record.items():
                        print(f"      {key}: {type(value).__name__} = {value}")
                    
                    # Cleanup
                    try:
                        client.client.table('articulos').delete().eq('url', inserted_url).execute()
                        print(f"   🧹 Test record cleaned up")
                    except:
                        print(f"   ⚠️  Could not clean up test record")
                
                break
                
            except Exception as e:
                print(f"   ❌ Failed: {str(e)[:100]}...")
        
        if successful_structure:
            print(f"\n🎉 SUCCESSFUL TABLE STRUCTURE DISCOVERED!")
            print(f"✅ Working field structure: {list(successful_structure.keys())}")
            
            # Now test the SupabaseClient with correct structure
            print(f"\n🧪 Testing SupabaseClient with correct structure...")
            
            # Update test data to match working structure
            corrected_data = successful_structure.copy()
            corrected_data['url'] = f'http://test.example.com/client-test-{uuid.uuid4()}'
            
            try:
                result = client.upsert_articulo(corrected_data)
                print(f"✅ SupabaseClient.upsert_articulo successful!")
                print(f"   Result: {result}")
                
                # Verify
                verify_response = client.client.table('articulos').select('*').eq('url', corrected_data['url']).execute()
                if verify_response.data:
                    print(f"✅ SupabaseClient insertion verified in database")
                    
                    # Cleanup
                    try:
                        client.client.table('articulos').delete().eq('url', corrected_data['url']).execute()
                        print(f"🧹 SupabaseClient test record cleaned up")
                    except:
                        print(f"⚠️  Could not clean up SupabaseClient test record")
                    
                    return True
                else:
                    print(f"❌ SupabaseClient record not found after insertion")
                    return False
                
            except Exception as e:
                print(f"❌ SupabaseClient test failed: {e}")
                return False
        else:
            print(f"\n❌ Could not determine working table structure")
            return False
            
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        return False

if __name__ == '__main__':
    success = discover_table_structure()
    if success:
        print(f"\n🏆 SUCCESS: Supabase integration working with correct structure!")
    else:
        print(f"\n💥 FAILED: Could not establish working integration")
        sys.exit(1)
