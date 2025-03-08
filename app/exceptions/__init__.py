# This file makes the exceptions directory a Python package
from app.exceptions.base import (
    AppException, 
    NotFoundError, 
    ValidationError, 
    APIError,
    CalComAPIError,
    OpenAIAPIError
)
