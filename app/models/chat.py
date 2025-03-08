"""
Models for chat functionality.
"""
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class ChatRole(str, Enum):
    """Enum for chat message roles."""
    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class ChatMessage(BaseModel):
    """Model for chat message."""
    
    role: ChatRole
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = Field(None, alias="function_call")
    
    class Config:
        from_attributes = True
        populate_by_name = True


class ChatFunction(BaseModel):
    """Model for function definition in OpenAI API."""
    
    name: str
    description: str
    parameters: Dict[str, Any]
    
    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """Model for chat response."""
    
    message: ChatMessage
    function_calls: Optional[List[Dict[str, Any]]] = None
    function_results: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ChatHistory(BaseModel):
    """Model for chat history."""
    
    messages: List[ChatMessage] = []
    
    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the chat history."""
        self.messages.append(message)
    
    def get_messages(self) -> List[ChatMessage]:
        """Get all messages in the chat history."""
        return self.messages
    
    def clear(self) -> None:
        """Clear the chat history."""
        self.messages = []
