"""
Health router - health check endpoints
"""

import time
from typing import Dict
from fastapi import APIRouter
from loguru import logger

from ..models.responses import HealthResponse, DetailedHealthResponse
from ..services.supabase_client import SupabaseClient
from ..main import START_TIME

# Create router instance
router = APIRouter()


async def check_supabase_health() -> Dict:
    """
    Check Supabase connection health and return status details.
    
    Performs a simple query to test the connection and measures response time.
    
    Returns:
        Dict containing:
        - status: 'ok' if successful, 'error' if failed
        - response_time_ms: Response time in milliseconds (if successful)
        - error: Error message (if failed)
    """
    try:
        start_time = time.time()
        
        # Define simple health check query
        def health_query():
            client = SupabaseClient.get_client()
            # Simple query to test connection - just select one ID
            return client.table('hechos').select('id').limit(1).execute()
        
        # Execute with retry
        await SupabaseClient.execute_with_retry(health_query)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        return {
            "status": "ok",
            "response_time_ms": round(response_time * 1000, 2)
        }
        
    except Exception as e:
        logger.error(f"Supabase health check failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint that returns service status.
    
    Returns:
        HealthResponse: Basic health status with 'ok' status and current version
    
    Example response:
        {
            "status": "ok",
            "version": "1.0.0"
        }
    """
    return {
        "status": "ok",
        "version": "1.0.0"
    }


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """
    Detailed health check that includes dependency statuses and uptime.
    
    Checks the health of all service dependencies (currently Supabase)
    and calculates the service uptime since startup.
    
    Returns:
        DetailedHealthResponse: Detailed health status including:
        - status: Overall service status ('ok' or 'degraded')
        - version: API version
        - dependencies: Status of each dependency
        - uptime: Service uptime in seconds
    
    Example response:
        {
            "status": "ok",
            "version": "1.0.0",
            "dependencies": {
                "supabase": {
                    "status": "ok",
                    "response_time_ms": 123.45
                }
            },
            "uptime": 3600.5
        }
    """
    # Check Supabase connection
    supabase_details = await check_supabase_health()
    
    # Get service uptime
    uptime = time.time() - START_TIME
    
    # Determine overall status based on dependencies
    overall_status = "ok" if supabase_details["status"] == "ok" else "degraded"
    
    return {
        "status": overall_status,
        "version": "1.0.0",
        "dependencies": {
            "supabase": supabase_details
        },
        "uptime": uptime
    }
