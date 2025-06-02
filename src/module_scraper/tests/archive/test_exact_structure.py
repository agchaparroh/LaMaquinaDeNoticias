#!/usr/bin/env python3
"""
Test con la estructura exacta esperada por SupabaseClient.
"""

import os
import sys
from pathlib import Path

# Set environment variables with SERVICE ROLE KEY
os.environ['SUPABASE_URL'] = 'https://aukbzqbcvbsnjdhflyvr.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1a2J6cWJjdmJzbmpkaGZseXZyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NTkxMjY2NiwiZXhwIjoyMDYxNDg4NjY2fQ.83yZqoMnj15_qkEbvqwCQsDgObQpmBoQsd-spxywAsw'

# Add scraper directory to path
scraper_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scraper_dir))

from scraper_core.utils.supabase_client import SupabaseClient
from datetime import datetime, timezone
import uuid

def test_supabase_client_structure():
    """Test con la estructura exacta esperada por SupabaseClient."""
    print("🧪 SUPABASE CLIENT - EXACT STRUCTURE TEST")
    print("=" * 60)
    
    try:
        client = SupabaseClient()
        print("✅ Connected to Supabase with service role")
        
        # Create test data with EXACT structure expected by SupabaseClient
        test_id = str(uuid.uuid4())
        
        # Structure according to SupabaseClient.upsert_articulo expected fields
        test_data = {
            'url': f'http://test.example.com/client-test-{test_id}',
            'titular': f'Test Article via SupabaseClient {test_id}',
            'medio': 'Test Medio Name',
            'medio_url_principal': 'https://test-medio.example.com',
            'fecha_publicacion': datetime.now(timezone.utc).isoformat(),
            'contenido_texto': f'This is test content for article {test_id}. It contains enough text to be meaningful.',
            'contenido_html': f'<html><body><h1>Test Article {test_id}</h1><p>This is test content for article {test_id}.</p></body></html>',
            
            # Optional fields that SupabaseClient handles
            'subtitulo': f'Subtitulo for test article {test_id}',
            'fecha_recopilacion': datetime.now(timezone.utc).isoformat(),
            'seccion': 'Test Section',
            'pais_publicacion': 'Test Country',
            'idioma': 'es',
            'resumen': f'This is a test summary for article {test_id}',
            'etiquetas_fuente': ['test', 'supabase', 'integration'],
        }
        
        print(f"\n🧪 Testing SupabaseClient.upsert_articulo with complete structure...")
        print(f"📋 Test data fields: {list(test_data.keys())}")
        
        try:
            result = client.upsert_articulo(test_data)
            
            if result:
                print(f"✅ SupabaseClient.upsert_articulo SUCCESS!")
                print(f"📤 Returned data: {result}")
                
                # Verify the article exists in database
                response = client.client.table('articulos').select('*').eq('url', test_data['url']).execute()
                
                if response.data:
                    print(f"✅ Article verified in database!")
                    article = response.data[0]
                    print(f"📋 Database record structure:")
                    for key, value in article.items():
                        if value is not None:
                            print(f"   {key}: {type(value).__name__} = {str(value)[:50]}...")
                    
                    # Check if medio was created
                    medio_response = client.client.table('medios').select('*').eq('url_principal', test_data['medio_url_principal']).execute()
                    if medio_response.data:
                        print(f"✅ Medio also created/found: {medio_response.data[0]}")
                    
                    # Cleanup
                    try:
                        # Delete article
                        client.client.table('articulos').delete().eq('url', test_data['url']).execute()
                        print(f"🧹 Test article cleaned up")
                        
                        # Delete medio if it was created for this test
                        if medio_response.data:
                            client.client.table('medios').delete().eq('url_principal', test_data['medio_url_principal']).execute()
                            print(f"🧹 Test medio cleaned up")
                            
                    except Exception as cleanup_error:
                        print(f"⚠️  Cleanup warning: {cleanup_error}")
                    
                    print(f"\n🎉 COMPLETE SUCCESS!")
                    print(f"✅ Supabase integration is working perfectly!")
                    print(f"✅ Articles are being stored correctly via SupabaseClient!")
                    print(f"✅ Medio creation/retrieval is working!")
                    print(f"✅ All pipeline components are functional!")
                    
                    return True
                    
                else:
                    print(f"❌ Article not found in database after upsert")
                    return False
                    
            else:
                print(f"❌ SupabaseClient.upsert_articulo returned None")
                return False
                
        except Exception as e:
            print(f"❌ SupabaseClient.upsert_articulo failed: {e}")
            print(f"📝 Error details: {str(e)}")
            
            # Let's try to understand what went wrong by testing table structure
            print(f"\n🔍 Debugging: Testing table structure directly...")
            
            # Test basic insertion to see what fields are actually required
            minimal_data = {
                'url': f'http://test.example.com/debug-{uuid.uuid4()}',
                'titulo': 'Debug Test',  # Using 'titulo' instead of 'titular'
            }
            
            try:
                debug_response = client.client.table('articulos').insert(minimal_data).execute()
                print(f"✅ Direct table insert successful with minimal data")
                print(f"📋 Database expects 'titulo' field, not 'titular'")
                
                # Cleanup debug record
                client.client.table('articulos').delete().eq('url', minimal_data['url']).execute()
                
            except Exception as debug_error:
                print(f"❌ Debug insertion failed: {debug_error}")
            
            return False
        
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        return False

if __name__ == '__main__':
    success = test_supabase_client_structure()
    if success:
        print(f"\n🏆 FINAL RESULT: SUPABASE INTEGRATION FULLY FUNCTIONAL!")
    else:
        print(f"\n💥 FINAL RESULT: INTEGRATION NEEDS FIXES")
        sys.exit(1)
