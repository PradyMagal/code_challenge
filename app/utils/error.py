"""
Utility functions for error handling.
"""
from typing import Dict, Any, Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions import AppException


def format_error_response(
    error: Exception,
    status_code: int = 500,
    error_code: str = "internal_error",
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format an error response.
    
    Args:
        error: The exception that occurred
        status_code: The HTTP status code
        error_code: A machine-readable error code
        details: Additional error details
        
    Returns:
        A dictionary with error information
    """
    # Get error message
    message = str(error)
    
    # If it's an AppException, use its properties
    if isinstance(error, AppException):
        status_code = error.status_code
        details = error.details
    
    # Create response
    response = {
        "error": {
            "code": error_code,
            "message": message,
            "status_code": status_code
        }
    }
    
    # Add details if provided
    if details:
        response["error"]["details"] = details
    
    return response


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle AppException instances.
    
    Args:
        request: The request that caused the exception
        exc: The exception that occurred
        
    Returns:
        A JSON response with error information
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            error=exc,
            status_code=exc.status_code,
            error_code=exc.__class__.__name__.lower(),
            details=exc.details
        )
    )
