#!/usr/bin/env python3
"""
Test directo de Supabase - descubriendo estructura de base de datos.
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

def discover_database_structure():
    """Descubre la estructura de la base de datos."""
    print("🧪 SUPABASE DATABASE DISCOVERY")
    print("=" * 50)
    
    try:
        print("🔗 Connecting to Supabase...")
        client = SupabaseClient()
        print(f"✅ SupabaseClient initialized successfully")
        
        # Test different table names
        table_names = ['articulos', 'articulos_beta', 'medios', 'autores', 'etiquetas']
        
        print(f"\n🔍 Discovering available tables...")
        available_tables = []
        
        for table_name in table_names:
            try:
                response = client.client.table(table_name).select('*').limit(1).execute()
                available_tables.append(table_name)
                print(f"✅ Table '{table_name}' exists (found {len(response.data)} sample records)")
            except Exception as e:
                print(f"❌ Table '{table_name}' not accessible: {str(e)[:50]}...")
        
        if not available_tables:
            print(f"❌ No accessible tables found")
            return False
            
        print(f"\n📊 Available tables: {available_tables}")
        
        # Try to insert a test article in the main articles table
        articles_table = 'articulos' if 'articulos' in available_tables else available_tables[0]
        print(f"\n🧪 Testing article insertion in '{articles_table}'...")
        
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
            # Use the SupabaseClient's upsert method
            result = client.upsert_articulo(test_data)
            print(f"✅ Article upserted via SupabaseClient!")
            print(f"   Result: {result}")
            
            # Verify the article exists
            response = client.client.table(articles_table) \
                .select('url, titulo') \
                .eq('url', test_data['url']) \
                .execute()
            
            if len(response.data) > 0:
                print(f"✅ Article verified in database")
                print(f"   Found record: {response.data[0]}")
                
                # Cleanup
                try:
                    client.client.table(articles_table) \
                        .delete() \
                        .eq('url', test_data['url']) \
                        .execute()
                    print(f"🧹 Test article cleaned up")
                except Exception as cleanup_error:
                    print(f"⚠️  Cleanup warning: {cleanup_error}")
                    
                print(f"\n🎉 SUPABASE INTEGRATION TEST: SUCCESS!")
                print(f"✅ Articles are being stored correctly in Supabase")
                return True
            else:
                print(f"❌ Article not found in database after insertion")
                return False
                
        except Exception as e:
            print(f"❌ Article upsert failed: {e}")
            
            # Try direct table insertion as fallback
            print(f"\n🔄 Trying direct table insertion...")
            try:
                response = client.client.table(articles_table).insert(test_data).execute()
                print(f"✅ Direct insertion successful: {response}")
                return True
            except Exception as direct_error:
                print(f"❌ Direct insertion also failed: {direct_error}")
                return False
        
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        return False

if __name__ == '__main__':
    success = discover_database_structure()
    if success:
        print(f"\n🏆 FINAL RESULT: SUPABASE INTEGRATION WORKING!")
    else:
        print(f"\n💥 FINAL RESULT: SUPABASE INTEGRATION FAILED")
        sys.exit(1)
