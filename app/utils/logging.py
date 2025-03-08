"""
Utility functions for logging.
"""
import logging
import sys
from typing import Optional, Dict, Any

from app.core.config import settings


def setup_logging(
    level: Optional[str] = None,
    format_str: Optional[str] = None,
    log_file: Optional[str] = None
) -> None:
    """
    Set up logging configuration.
    
    Args:
        level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_str: The log format string
        log_file: The log file path
    """
    # Set default level based on debug setting
    if level is None:
        level = "DEBUG" if settings.debug else "INFO"
    
    # Set default format
    if format_str is None:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure logging
    logging_config = {
        "level": getattr(logging, level),
        "format": format_str,
        "handlers": [logging.StreamHandler(sys.stdout)]
    }
    
    # Add file handler if log file is provided
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(format_str))
        logging_config["handlers"].append(file_handler)
    
    # Apply configuration
    logging.basicConfig(**logging_config)
    
    # Set third-party loggers to a higher level to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    
    # Log startup message
    logging.info(f"Logging initialized with level {level}")


def log_request(request_data: Dict[str, Any], logger: logging.Logger) -> None:
    """
    Log request data.
    
    Args:
        request_data: The request data to log
        logger: The logger to use
    """
    # Don't log in production unless debug is enabled
    if not settings.debug:
        return
    
    # Sanitize sensitive data
    sanitized_data = sanitize_sensitive_data(request_data)
    
    # Log request
    logger.debug(f"Request data: {sanitized_data}")


def log_response(response_data: Dict[str, Any], logger: logging.Logger) -> None:
    """
    Log response data.
    
    Args:
        response_data: The response data to log
        logger: The logger to use
    """
    # Don't log in production unless debug is enabled
    if not settings.debug:
        return
    
    # Sanitize sensitive data
    sanitized_data = sanitize_sensitive_data(response_data)
    
    # Log response
    logger.debug(f"Response data: {sanitized_data}")


def sanitize_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize sensitive data in a dictionary.
    
    Args:
        data: The data to sanitize
        
    Returns:
        The sanitized data
    """
    # Create a copy of the data
    sanitized = data.copy()
    
    # List of sensitive fields to sanitize
    sensitive_fields = [
        "api_key", "key", "secret", "password", "token", "authorization",
        "access_token", "refresh_token", "private_key", "email"
    ]
    
    # Sanitize sensitive fields
    for key in sanitized:
        if isinstance(sanitized[key], dict):
            sanitized[key] = sanitize_sensitive_data(sanitized[key])
        elif isinstance(sanitized[key], str) and any(field in key.lower() for field in sensitive_fields):
            sanitized[key] = "********"
    
    return sanitized
