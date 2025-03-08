import logging
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any

from app.core.config import settings
from app.exceptions import AppException, NotFoundError, ValidationError, APIError
from app.utils.error import app_exception_handler
from app.utils.logging import setup_logging
from app.api import chat_router, calcom_router

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A chatbot for booking and managing Cal.com events using OpenAI function calling",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(NotFoundError, app_exception_handler)
app.add_exception_handler(ValidationError, app_exception_handler)
app.add_exception_handler(APIError, app_exception_handler)


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint that returns a welcome message
    """
    return {
        "message": f"Welcome to {settings.app_name} API, by Pradyun Magal",
        "version": settings.app_version,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint to verify the application is running correctly
    """
    # Check if API keys are available
    api_keys_available = bool(settings.openai_api_key) and bool(settings.calcom_api_key)
    
    # Determine overall status
    status = "healthy" if api_keys_available else "degraded"
    
    return {
        "status": status,
        "version": settings.app_version,
        "timestamp": import_time(),
        "checks": {
            "api_keys": {
                "status": "available" if api_keys_available else "missing",
                "openai": bool(settings.openai_api_key),
                "calcom": bool(settings.calcom_api_key),
            },
            "config": {
                "status": "loaded",
                "app_name": settings.app_name,
            }
        }
    }


def import_time() -> str:
    """Get current time in ISO format"""
    from datetime import datetime
    return datetime.now().isoformat()


# Include routers
app.include_router(chat_router, prefix="/api")
app.include_router(calcom_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler
    """
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler
    """
    logger.info(f"Shutting down {settings.app_name}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
