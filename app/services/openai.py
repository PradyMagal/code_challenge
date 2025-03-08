"""
Service for interacting with OpenAI API.
"""
import logging
import json
from typing import List, Optional, Dict, Any, Union

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from app.core.config import settings
from app.exceptions import OpenAIAPIError
from app.models.chat import ChatMessage, ChatFunction, ChatRole


logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API."""
    
    def __init__(self):
        """Initialize the OpenAI service."""
        self.api_key = settings.openai_api_key
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = "gpt-4-turbo"  # Default model
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        functions: Optional[List[ChatFunction]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> ChatCompletion:
        """Get a chat completion from OpenAI."""
        try:
            # Convert messages to the format expected by OpenAI
            openai_messages = [
                {
                    "role": message.role.value,
                    "content": message.content,
                    **({"name": message.name} if message.name else {}),
                    **({"function_call": message.function_call} if message.function_call else {})
                }
                for message in messages
            ]
            
            # Convert functions to the format expected by OpenAI
            openai_functions = None
            if functions:
                openai_functions = [
                    {
                        "name": function.name,
                        "description": function.description,
                        "parameters": function.parameters
                    }
                    for function in functions
                ]
            
            # Create the request parameters
            params = {
                "model": self.model,
                "messages": openai_messages,
                "temperature": temperature
            }
            
            # Add optional parameters
            if max_tokens:
                params["max_tokens"] = max_tokens
            
            # Add functions if provided
            if openai_functions:
                params["tools"] = [
                    {
                        "type": "function",
                        "function": function
                    }
                    for function in openai_functions
                ]
                params["tool_choice"] = "auto"
            
            # Make the request
            response = await self.client.chat.completions.create(**params)
            return response
        
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise OpenAIAPIError(
                message=f"OpenAI API error: {str(e)}",
                details={"error": str(e)}
            )
    
    def parse_response(self, response: ChatCompletion) -> Dict[str, Any]:
        """Parse the response from OpenAI."""
        try:
            # Get the message
            message = response.choices[0].message
            
            # Check if there's a function call
            function_calls = []
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call.type == "function":
                        function_call = {
                            "name": tool_call.function.name,
                            "arguments": json.loads(tool_call.function.arguments)
                        }
                        function_calls.append(function_call)
            
            # Create the response
            return {
                "message": ChatMessage(
                    role=ChatRole.ASSISTANT,
                    content=message.content or ""
                ),
                "function_calls": function_calls if function_calls else None
            }
        
        except Exception as e:
            logger.error(f"Error parsing OpenAI response: {str(e)}")
            raise OpenAIAPIError(
                message=f"Error parsing OpenAI response: {str(e)}",
                details={"error": str(e)}
            )
