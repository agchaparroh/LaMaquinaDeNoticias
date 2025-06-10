#!/usr/bin/env python3
"""
Test script for Pipeline API client functionality
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch
import aiohttp
from aiohttp import web
import json

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test data
TEST_ARTICLE_DATA = {
    "url": "https://test.com/article/1",
    "medio": "Test Medium",
    "pais_publicacion": "Test Country", 
    "tipo_medio": "Test Type",
    "titular": "Test Title for Pipeline API",
    "fecha_publicacion": "2023-12-01T12:00:00Z",
    "contenido_texto": "Test content text for pipeline API testing"
}


async def create_mock_pipeline_server(port=8999, response_status=202, response_delay=0):
    """Create a mock Pipeline API server for testing"""
    
    async def handle_procesar(request):
        """Handle /procesar endpoint"""
        await asyncio.sleep(response_delay)  # Simulate processing time
        
        try:
            data = await request.json()
            
            if response_status == 202:
                return web.json_response({
                    "status": "recibido",
                    "mensaje": "Artículo recibido y encolado para procesamiento.",
                    "id_articulo_procesamiento": "test-123"
                }, status=202)
            elif response_status == 400:
                return web.json_response({
                    "status": "error_validacion_payload",
                    "mensaje": "Los datos del artículo proporcionados son inválidos.",
                    "detalles": [
                        {"campo": "articulo.test", "error": "Test validation error"}
                    ]
                }, status=400)
            elif response_status == 500:
                return web.json_response({
                    "status": "error_interno_pipeline",
                    "mensaje": "Ocurrió un error inesperado en el pipeline."
                }, status=500)
            elif response_status == 503:
                return web.json_response({
                    "status": "servicio_no_disponible",
                    "mensaje": "El servicio de pipeline no está disponible actualmente."
                }, status=503)
            else:
                return web.json_response({"error": "Unknown status"}, status=response_status)
                
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    app = web.Application()
    app.router.add_post('/procesar', handle_procesar)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', port)
    await site.start()
    
    return runner


async def test_pipeline_api_client():
    """Test the Pipeline API client functionality"""
    
    print("🧪 Testing Pipeline API Client")
    print("=" * 50)
    
    # Import modules we're testing
    from models import prepare_articulo
    from main import send_to_pipeline, send_articles_to_pipeline
    import config
    
    # Override config for testing
    original_api_url = config.PIPELINE_API_URL
    original_max_retries = config.MAX_RETRIES
    config.PIPELINE_API_URL = "http://localhost:8999"
    config.MAX_RETRIES = 2  # Faster testing
    
    try:
        # Prepare test article
        test_article = prepare_articulo(TEST_ARTICLE_DATA)
        
        # Test 1: Successful submission (202)
        print("\n📡 Test 1: Successful submission (202)")
        mock_server = await create_mock_pipeline_server(port=8999, response_status=202)
        
        try:
            async with aiohttp.ClientSession() as session:
                success = await send_to_pipeline(session, test_article)
                
            print(f"  Result: {success}")
            if success:
                print("  ✅ Successful submission test passed")
            else:
                print("  ❌ Successful submission test failed")
        finally:
            await mock_server.cleanup()
        
        await asyncio.sleep(0.1)  # Brief pause between tests
        
        # Test 2: Validation error (400)
        print("\n📡 Test 2: Validation error (400)")
        mock_server = await create_mock_pipeline_server(port=8999, response_status=400)
        
        try:
            async with aiohttp.ClientSession() as session:
                success = await send_to_pipeline(session, test_article)
                
            print(f"  Result: {success}")
            if not success:
                print("  ✅ Validation error test passed (correctly failed)")
            else:
                print("  ❌ Validation error test failed (should have failed)")
        finally:
            await mock_server.cleanup()
        
        await asyncio.sleep(0.1)
        
        # Test 3: Server error (500) - should retry then fail
        print("\n📡 Test 3: Server error (500)")
        mock_server = await create_mock_pipeline_server(port=8999, response_status=500)
        
        try:
            async with aiohttp.ClientSession() as session:
                success = await send_to_pipeline(session, test_article)
                
            print(f"  Result: {success}")
            if not success:
                print("  ✅ Server error test passed (correctly failed after retries)")
            else:
                print("  ❌ Server error test failed (should have failed)")
        finally:
            await mock_server.cleanup()
        
        await asyncio.sleep(0.1)
        
        # Test 4: Multiple articles
        print("\n📡 Test 4: Multiple articles (mixed results)")
        
        # Create 3 test articles
        articles = []
        for i in range(3):
            article_data = TEST_ARTICLE_DATA.copy()
            article_data['titular'] = f"Test Article {i+1}"
            article_data['url'] = f"https://test.com/article/{i+1}"
            articles.append(prepare_articulo(article_data))
        
        mock_server = await create_mock_pipeline_server(port=8999, response_status=202)
        
        try:
            success_count, failure_count = await send_articles_to_pipeline(articles)
            
            print(f"  Success count: {success_count}")
            print(f"  Failure count: {failure_count}")
            
            if success_count == 3 and failure_count == 0:
                print("  ✅ Multiple articles test passed")
            else:
                print("  ❌ Multiple articles test failed")
        finally:
            await mock_server.cleanup()
        
        await asyncio.sleep(0.1)
        
        # Test 5: Connection error (no server)
        print("\n📡 Test 5: Connection error (no server)")
        
        # No mock server running - should fail with connection error
        async with aiohttp.ClientSession() as session:
            success = await send_to_pipeline(session, test_article)
            
        print(f"  Result: {success}")
        if not success:
            print("  ✅ Connection error test passed (correctly failed)")
        else:
            print("  ❌ Connection error test failed (should have failed)")
        
        # Test 6: Empty articles list
        print("\n📡 Test 6: Empty articles list")
        
        success_count, failure_count = await send_articles_to_pipeline([])
        
        print(f"  Success count: {success_count}")
        print(f"  Failure count: {failure_count}")
        
        if success_count == 0 and failure_count == 0:
            print("  ✅ Empty articles test passed")
        else:
            print("  ❌ Empty articles test failed")
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Restore original config
        config.PIPELINE_API_URL = original_api_url
        config.MAX_RETRIES = original_max_retries
    
    print("\n" + "=" * 50)
    print("🎉 Pipeline API client tests completed!")
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_pipeline_api_client())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
