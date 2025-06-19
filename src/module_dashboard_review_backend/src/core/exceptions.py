"""
Exception handlers for Dashboard Review Backend
Provides centralized error handling with consistent JSON responses
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger

# Import custom exceptions from utils
from utils.exceptions import BaseAPIException


async def base_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """
    Handle all BaseAPIException and its subclasses.
    
    Args:
        request: The FastAPI request object
        exc: The exception instance
        
    Returns:
        JSONResponse with consistent error format
    """
    # Log the error with structured context
    logger.error(
        f"API error: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": str(request.url.path),
            "method": request.method,
            "request_id": getattr(request.state, "request_id", None)
        }
    )
    
    # Return consistent JSON response
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors from request parsing.
    
    Args:
        request: The FastAPI request object
        exc: The RequestValidationError instance
        
    Returns:
        JSONResponse with validation error details
    """
    # Log validation error with context
    logger.error(
        "Request validation error",
        extra={
            "errors": exc.errors(),
            "path": str(request.url.path),
            "method": request.method,
            "request_id": getattr(request.state, "request_id", None)
        }
    )
    
    # Return structured validation error response
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors()
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle any unhandled exceptions.
    
    This is the fallback handler for any exceptions not caught by specific handlers.
    In production, it returns a generic error message to avoid leaking sensitive information.
    
    Args:
        request: The FastAPI request object
        exc: The exception instance
        
    Returns:
        JSONResponse with generic error message
    """
    # Log the full exception details
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "path": str(request.url.path),
            "method": request.method,
            "request_id": getattr(request.state, "request_id", None)
        },
        exc_info=True  # Include full traceback in logs
    )
    
    # Return generic error response (no sensitive details)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"}
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI app.
    
    This function should be called after creating the FastAPI app instance
    to set up centralized error handling.
    
    Args:
        app: The FastAPI application instance
    """
    # Register handler for custom API exceptions
    app.add_exception_handler(BaseAPIException, base_exception_handler)
    
    # Register handler for request validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Register general handler for any unhandled exceptions
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers registered successfully")
