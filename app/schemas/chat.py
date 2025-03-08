"""
Schemas for chat API endpoints.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for chat request."""
    
    message: str = Field(..., description="User message")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Help me book a meeting for tomorrow at 2pm",
                "user_id": "user123",
                "session_id": "session456"
            }
        }


class ChatResponse(BaseModel):
    """Schema for chat response."""
    
    response: str = Field(..., description="Assistant response or function result")
    session_id: str = Field(..., description="Session identifier")
    requires_action: bool = Field(False, description="Whether the response requires user action")
    action_details: Optional[Dict[str, Any]] = Field(None, description="Details of the required action")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "I've booked a meeting for tomorrow at 2pm. You'll receive a confirmation email shortly.",
                "session_id": "session456",
                "requires_action": False,
                "action_details": None
            }
        }
