"""
Base exceptions for the application.
"""
from typing import Any, Dict, Optional


class AppException(Exception):
    """Base exception for all application exceptions."""
    
    def __init__(
        self, 
        message: str = "An unexpected error occurred", 
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """Exception raised when a resource is not found."""
    
    def __init__(
        self, 
        message: str = "Resource not found", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=404, details=details)


class ValidationError(AppException):
    """Exception raised when validation fails."""
    
    def __init__(
        self, 
        message: str = "Validation error", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=400, details=details)


class APIError(AppException):
    """Exception raised when an external API call fails."""
    
    def __init__(
        self, 
        message: str = "External API error", 
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=status_code, details=details)


class CalComAPIError(APIError):
    """Exception raised when a Cal.com API call fails."""
    
    def __init__(
        self, 
        message: str = "Cal.com API error", 
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=status_code, details=details)


class OpenAIAPIError(APIError):
    """Exception raised when an OpenAI API call fails."""
    
    def __init__(
        self, 
        message: str = "OpenAI API error", 
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=status_code, details=details)
