"""
Logging configuration using loguru following module_pipeline pattern
Provides structured logging for the Dashboard Review Backend
"""

import sys
from loguru import logger
from typing import Dict, Any


def setup_logging(log_level: str = "INFO", environment: str = "development") -> Dict[str, Any]:
    """
    Configure loguru for structured logging following module_pipeline pattern
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        environment: Environment (development, production)
    
    Returns:
        Dictionary with logging configuration for settings
    """
    # Remove default handler
    logger.remove()
    
    # Format for console output - structured for module_pipeline compatibility
    if environment == "development":
        # Human-readable format for development
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    else:
        # JSON format for production (compatible with log aggregators)
        log_format = (
            '{"timestamp": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
            '"level": "{level}", '
            '"module": "{module}", '
            '"function": "{function}", '
            '"line": "{line}", '
            '"message": "{message}"}'
        )
    
    # Add console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level,
        colorize=environment == "development",
        serialize=environment == "production",
        backtrace=True,
        diagnose=environment == "development",
        enqueue=True  # Thread-safe logging
    )
    
    # Return configuration dictionary for settings
    return {
        "handlers": [
            {
                "sink": sys.stdout,
                "format": log_format,
                "level": log_level,
                "colorize": environment == "development",
                "serialize": environment == "production",
                "backtrace": True,
                "diagnose": environment == "development",
                "enqueue": True
            }
        ]
    }


def log_request(request_id: str, method: str, path: str, status_code: int, duration_ms: float):
    """
    Log HTTP request details in structured format
    
    Args:
        request_id: Unique request identifier
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
    """
    logger.info(
        f"HTTP Request | {method} {path} | Status: {status_code} | Duration: {duration_ms:.2f}ms",
        extra={
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms
        }
    )
