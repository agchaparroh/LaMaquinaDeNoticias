"""
Custom exceptions for Dashboard Review Backend
Handles database connection errors and other custom exceptions
"""

from typing import Optional


class BaseAPIException(Exception):
    """
    Base exception class for all API-specific exceptions.
    
    This provides a common interface for handling application errors
    with consistent status codes and error messages.
    
    Attributes:
        status_code (int): HTTP status code for the error
        detail (str): Human-readable error message
    """
    
    def __init__(self, status_code: int, detail: str) -> None:
        """
        Initialize the BaseAPIException.
        
        Args:
            status_code: HTTP status code for the error response
            detail: Error message to be returned to the client
        """
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.detail)


class DatabaseConnectionError(BaseAPIException):
    """
    Exception raised when database connection fails.
    
    This exception is used to signal issues with Supabase connectivity,
    including initial connection failures and retry exhaustion.
    
    Example:
        >>> raise DatabaseConnectionError("Could not connect to Supabase")
        >>> raise DatabaseConnectionError("Connection timeout: All retry attempts exhausted")
    """
    
    def __init__(self, detail: str = "Database connection error") -> None:
        """
        Initialize the DatabaseConnectionError.
        
        Args:
            detail: The error message describing the connection issue
        """
        super().__init__(status_code=503, detail=detail)


class ResourceNotFoundError(BaseAPIException):
    """
    Exception raised when a requested resource is not found.
    
    This exception should be used when a specific resource (like a hecho,
    article, or user) cannot be found in the database.
    
    Example:
        >>> raise ResourceNotFoundError("Hecho with ID 123 not found")
        >>> raise ResourceNotFoundError("No hechos found matching the criteria")
    """
    
    def __init__(self, detail: str = "Resource not found") -> None:
        """
        Initialize the ResourceNotFoundError.
        
        Args:
            detail: The error message describing what resource was not found
        """
        super().__init__(status_code=404, detail=detail)


class ValidationError(BaseAPIException):
    """
    Exception raised for custom validation errors.
    
    This exception should be used for business logic validation errors
    that are not caught by Pydantic's request validation.
    
    Example:
        >>> raise ValidationError("Start date cannot be after end date")
        >>> raise ValidationError("Invalid importance range")
    """
    
    def __init__(self, detail: str = "Validation error") -> None:
        """
        Initialize the ValidationError.
        
        Args:
            detail: The error message describing the validation failure
        """
        super().__init__(status_code=422, detail=detail)
