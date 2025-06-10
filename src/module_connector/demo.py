#!/usr/bin/env python3
"""
Quick demo script to test the Module Connector with sample data
"""

import asyncio
import os
import gzip
import json
import tempfile
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))


async def create_demo_file():
    """Create a demo file with sample article data"""
    
    # Sample article data
    demo_article = {
        "url": "https://demo.com/article/123",
        "storage_path": "/demo/article_123.json.gz",
        "fuente": "demo_spider",
        "medio": "Demo News",
        "medio_url_principal": "https://demo.com",
        "pais_publicacion": "Demo Country",
        "tipo_medio": "Digital Newspaper",
        "titular": "Demo Article: Module Connector Test",
        "fecha_publicacion": "2023-12-01T10:00:00Z",
        "autor": "Demo Author",
        "idioma": "es",
        "seccion": "Technology",
        "etiquetas_fuente": ["demo", "test", "module-connector"],
        "es_opinion": False,
        "es_oficial": False,
        "resumen": "This is a demo article to test the Module Connector functionality.",
        "categorias_asignadas": ["technology", "testing"],
        "puntuacion_relevancia": 8.5,
        "fecha_recopilacion": "2023-12-01T10:05:00Z",
        "fecha_procesamiento": None,
        "estado_procesamiento": "pendiente_connector",
        "error_detalle": None,
        "contenido_texto": "This is the demo content of the article. It contains sample text to test the Module Connector's ability to process articles and send them to the Pipeline API. The content should be long enough to simulate a real article while remaining clearly identifiable as test data.",
        "contenido_html": "<html><body><h1>Demo Article</h1><p>This is the demo content...</p></body></html>",
        "metadata": {
            "demo_mode": True,
            "test_id": "module_connector_demo",
            "created_by": "demo_script"
        }
    }
    
    print("📝 Creating demo article file...")
    
    # Create temporary demo file
    demo_dir = Path("demo_input")
    demo_dir.mkdir(exist_ok=True)
    
    demo_file = demo_dir / "demo_article.json.gz"
    
    with gzip.open(demo_file, 'wt', encoding='utf-8') as f:
        json.dump(demo_article, f, indent=2)
    
    print(f"✅ Demo file created: {demo_file}")
    print(f"   Article title: {demo_article['titular']}")
    print(f"   Medium: {demo_article['medio']}")
    print(f"   Content length: {len(demo_article['contenido_texto'])} characters")
    
    return str(demo_file)


async def run_demo():
    """Run a quick demo of the Module Connector"""
    
    print("🚀 Module Connector Demo")
    print("=" * 40)
    
    try:
        # Create demo file
        demo_file = await create_demo_file()
        
        print(f"\n📁 Demo file ready at: {demo_file}")
        
        # Import and test components
        print("\n🔧 Testing Module Connector components...")
        
        # Test 1: File processing
        print("\n1. Testing file processing...")
        from main import process_file
        
        valid_articles, invalid_articles, has_valid = await process_file(demo_file)
        
        print(f"   Valid articles: {len(valid_articles)}")
        print(f"   Invalid articles: {len(invalid_articles)}")
        print(f"   Has valid: {has_valid}")
        
        if has_valid and valid_articles:
            article = valid_articles[0]
            print(f"   Article title: {article.titular}")
            print(f"   Article medium: {article.medio}")
            
        # Test 2: Model validation
        print("\n2. Testing Pydantic model...")
        from models import prepare_articulo
        
        with gzip.open(demo_file, 'rt', encoding='utf-8') as f:
            article_data = json.load(f)
        
        validated_article = prepare_articulo(article_data)
        print(f"   Model validation: ✅ Success")
        print(f"   Generated ID: {getattr(validated_article, 'id', 'N/A')}")
        
        # Test 3: Configuration
        print("\n3. Testing configuration...")
        import config
        
        print(f"   Scraper output dir: {config.SCRAPER_OUTPUT_DIR}")
        print(f"   Pipeline API URL: {config.PIPELINE_API_URL}")
        print(f"   Polling interval: {config.POLLING_INTERVAL}s")
        print(f"   Max retries: {config.MAX_RETRIES}")
        
        # Test 4: Logging setup
        print("\n4. Testing logging setup...")
        from main import setup_logging
        
        setup_logging()
        
        from loguru import logger
        logger.info("Demo log message from Module Connector")
        
        print("   Logging: ✅ Setup complete")
        
        print("\n" + "=" * 40)
        print("🎉 Demo completed successfully!")
        print(f"\n💡 To run the full Module Connector:")
        print(f"   1. Set up your environment variables (.env file)")
        print(f"   2. Ensure the Pipeline API is running")
        print(f"   3. Run: python src/main.py")
        print(f"\n📁 Demo file location: {demo_file}")
        print(f"   (You can use this file to test the full workflow)")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(run_demo())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
        sys.exit(1)
