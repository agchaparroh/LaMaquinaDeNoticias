"""
Dashboard Review Backend - La Máquina de Noticias
FastAPI application for editorial review dashboard
"""

import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Import configuration settings
from .utils.config import settings
from .utils.logging_config import log_request

# Import placeholder routers directly
from .api import dashboard, feedback, health

# Import exception handlers
from .core.exceptions import register_exception_handlers

# Global variable to track service start time
START_TIME = time.time()

# Initialize FastAPI app with title
app = FastAPI(title="Dashboard Review API")

# Configure logging
logger.configure(**settings.LOGGING_CONFIG)
logger.info("Dashboard Review API starting up", extra={"environment": settings.environment})

# Configure CORS from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming HTTP requests"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Add request ID to request state for use in endpoints
    request.state.request_id = request_id
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Log request details
    log_request(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms
    )
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    return response


# Include placeholder routers
app.include_router(health.router, tags=["Health"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(feedback.router, prefix="/dashboard/feedback", tags=["Feedback"])


# Root endpoint
@app.get("/")
async def read_root():
    logger.debug("Root endpoint accessed")
    return {"message": "Dashboard Review API - La Máquina de Noticias"}


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    logger.info(
        "Dashboard Review API started successfully",
        extra={
            "host": settings.api_host,
            "port": settings.api_port,
            "environment": settings.environment,
            "log_level": settings.log_level
        }
    )


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown"""
    logger.info("Dashboard Review API shutting down")


# For running with uvicorn programmatically (optional)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_config=None  # Use loguru instead of uvicorn's logger
    )
