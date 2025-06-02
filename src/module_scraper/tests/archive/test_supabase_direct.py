#!/usr/bin/env python3
"""
Test directo de Supabase con credenciales hardcodeadas temporalmente.
"""

import os
import sys
from pathlib import Path

# Set environment variables directly (for testing only)
os.environ['SUPABASE_URL'] = 'https://aukbzqbcvbsnjdhflyvr.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1a2J6cWJjdmJzbmpkaGZseXZyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5MTI2NjYsImV4cCI6MjA2MTQ4ODY2Nn0.KfRQ1Jv7HIGwMHUS8e8IgN92iv1go7VvyK-6wqgog3s'

# Add the scraper directory to Python path
scraper_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scraper_dir))

from scraper_core.utils.supabase_client import SupabaseClient
from datetime import datetime, timezone
import uuid

def test_supabase_direct():
    """Test directo de Supabase."""
    print("🧪 SUPABASE DIRECT TEST")
    print("=" * 50)
    
    try:
        print("🔗 Connecting to Supabase...")
        client = SupabaseClient()
        print(f"✅ SupabaseClient initialized successfully")
        
        print(f"🔍 URL: {os.getenv('SUPABASE_URL')}")
        print(f"🔍 Key: ***{os.getenv('SUPABASE_KEY')[-10:]}")
        
        # Test 1: Basic connection with a simple query
        print("\n🧪 Test 1: Basic connection...")
        try:
            response = client.client.table('articulos_beta').select('count').limit(1).execute()
            print(f"✅ Connection successful!")
            print(f"   Tables accessible: articulos_beta")
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
        
        # Test 2: Insert a test article
        print("\n🧪 Test 2: Article upsert...")
        test_id = str(uuid.uuid4())
        test_data = {
            'url': f'http://test.example.com/article-{test_id}',
            'titulo': f'Test Article {test_id}',
            'medio_nombre': 'Test Medio',
            'fecha_extraccion': datetime.now(timezone.utc).isoformat(),
            'categoria_principal': 'Test',
            'contenido_texto': f'Test content for article {test_id}',
        }
        
        try:
            result = client.upsert_articulo(test_data)
            print(f"✅ Article upserted successfully!")
            print(f"   Result: {result}")
            
            # Verify the article exists
            response = client.client.table('articulos_beta') \
                .select('url, titulo') \
                .eq('url', test_data['url']) \
                .execute()
            
            if len(response.data) > 0:
                print(f"✅ Article verified in database")
                print(f"   Found: {response.data[0]}")
                
                # Cleanup
                try:
                    client.client.table('articulos_beta') \
                        .delete() \
                        .eq('url', test_data['url']) \
                        .execute()
                    print(f"🧹 Test article cleaned up")
                except Exception as cleanup_error:
                    print(f"⚠️  Cleanup warning: {cleanup_error}")
            else:
                print(f"❌ Article not found in database")
                return False
                
        except Exception as e:
            print(f"❌ Article upsert failed: {e}")
            return False
        
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ Supabase integration is working correctly")
        return True
        
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        return False

if __name__ == '__main__':
    success = test_supabase_direct()
    if success:
        print("\n🏆 INTEGRATION TEST: SUCCESS")
    else:
        print("\n💥 INTEGRATION TEST: FAILED")
        sys.exit(1)
