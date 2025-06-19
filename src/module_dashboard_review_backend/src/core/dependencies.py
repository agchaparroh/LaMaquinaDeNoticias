"""
FastAPI Dependency Injection Configuration
Provides service dependencies for routers
"""

from typing import Generator, Optional
from loguru import logger

# Import real implementations
from services.supabase_client import SupabaseClient
from services.hechos_service import HechosService
from services.feedback_service import FeedbackService


# Singleton instances (will be replaced with proper initialization in future tasks)
_supabase_client: Optional[SupabaseClient] = None
_hechos_service: Optional[HechosService] = None
_feedback_service: Optional[FeedbackService] = None


# Dependency functions for FastAPI
def get_supabase_client() -> SupabaseClient:
    """
    Provides Supabase client instance for dependency injection
    
    Returns:
        SupabaseClient instance
    """
    # Return the real SupabaseClient singleton
    return SupabaseClient()


def get_hechos_service() -> HechosService:
    """
    Provides HechosService instance for dependency injection
    
    Returns:
        HechosService instance
    """
    global _hechos_service
    if _hechos_service is None:
        # HechosService now manages its own Supabase client
        _hechos_service = HechosService()
    return _hechos_service


def get_feedback_service() -> FeedbackService:
    """
    Provides FeedbackService instance for dependency injection
    
    Returns:
        FeedbackService instance
    """
    global _feedback_service
    if _feedback_service is None:
        # FeedbackService manages its own Supabase client
        _feedback_service = FeedbackService()
    return _feedback_service


# Optional: Request-scoped dependencies (for future use)
def get_request_id(request) -> str:
    """
    Extract request ID from request state
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Request ID string
    """
    return getattr(request.state, 'request_id', 'unknown')


# Future dependencies placeholders (for extensibility)
def get_current_user_optional():
    """
    Placeholder for optional authentication
    Will be implemented when auth is added
    """
    return None


def get_rate_limiter():
    """
    Placeholder for rate limiting
    Will be implemented when rate limiting is added
    """
    return None
