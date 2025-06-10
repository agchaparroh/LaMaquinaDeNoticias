#!/usr/bin/env python3
"""
Mock Pipeline API server for testing Module Connector
"""

import asyncio
import json
from aiohttp import web
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def handle_procesar(request):
    """Handle /procesar endpoint for testing"""
    try:
        # Parse request
        data = await request.json()
        
        logger.info(f"Received article: {data.get('articulo', {}).get('titular', 'Unknown title')}")
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Return success response
        response_data = {
            "status": "recibido",
            "mensaje": "Artículo recibido y encolado para procesamiento.",
            "id_articulo_procesamiento": f"mock-{id(data)}"
        }
        
        return web.json_response(response_data, status=202)
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return web.json_response({
            "status": "error_interno_pipeline",
            "mensaje": f"Error en mock pipeline: {str(e)}"
        }, status=500)


async def handle_health(request):
    """Health check endpoint"""
    return web.json_response({"status": "healthy", "service": "mock-pipeline"})


async def init_app():
    """Initialize the mock pipeline application"""
    app = web.Application()
    
    # Add routes
    app.router.add_post('/procesar', handle_procesar)
    app.router.add_get('/health', handle_health)
    
    return app


async def main():
    """Main function to run the mock pipeline server"""
    app = await init_app()
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', 8001)
    await site.start()
    
    logger.info("Mock Pipeline API started on http://0.0.0.0:8001")
    logger.info("Available endpoints:")
    logger.info("  POST /procesar - Process articles")
    logger.info("  GET /health - Health check")
    
    try:
        # Keep the server running
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Shutting down mock pipeline server...")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
