"""
Utility functions for date handling.
"""
import logging
from datetime import datetime, date, timedelta
from typing import Optional, Union, Tuple, Dict, Any

from app.services.openai import OpenAIService
from app.models.chat import ChatMessage, ChatRole


logger = logging.getLogger(__name__)


async def parse_date_with_llm(date_str: str, openai_service: OpenAIService) -> Optional[Dict[str, Any]]:
    """
    Use OpenAI to parse a date string into structured date information.
   
    Args:
        date_str: The date/time string to parse
        openai_service: An instance of the OpenAIService
        
    Returns:
        A dictionary with parsed date information or None if parsing fails
    """
    try:
        # Create system and user messages
        messages = [
            ChatMessage(
                role=ChatRole.SYSTEM,
                content="""You are a helpful assistant that extracts date and time information from text.
                Extract the date, start time, and end time if present. Return ISO format dates and 24-hour times.
                If no specific date is mentioned, assume today's date. If no specific time is mentioned, return null for times."""
            ),
            ChatMessage(
                role=ChatRole.USER,
                content=f"Parse the following date/time: {date_str}"
            )
        ]
        
        # Define the function for OpenAI to call
        functions = [{
            "name": "extract_datetime",
            "description": "Extract date and time information from text",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "The extracted date in ISO format (YYYY-MM-DD)"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "The extracted start time in 24-hour format (HH:MM), or null if not present"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "The extracted end time in 24-hour format (HH:MM), or null if not present"
                    },
                    "is_specific": {
                        "type": "boolean",
                        "description": "Whether the date/time is specific or approximate"
                    }
                },
                "required": ["date", "is_specific"]
            }
        }]
        
        # Get completion from OpenAI
        completion = await openai_service.chat_completion(
            messages=messages,
            functions=functions,
            temperature=0.1  # Low temperature for more deterministic results
        )
        
        # Parse response
        parsed_response = openai_service.parse_response(completion)
        
        # Extract function call results
        if parsed_response.get("function_calls"):
            for function_call in parsed_response["function_calls"]:
                if function_call["name"] == "extract_datetime":
                    return function_call["arguments"]
        
        return None
    
    except Exception as e:
        logger.error(f"Error parsing date with LLM: {str(e)}")
        return None


def format_date(date_obj: Union[date, datetime], format_str: str = "%Y-%m-%d") -> str:
    """
    Format a date object into a string.
    
    Args:
        date_obj: The date or datetime object to format
        format_str: The format string to use
        
    Returns:
        A formatted date string
    """
    if isinstance(date_obj, datetime):
        return date_obj.strftime(format_str)
    return date_obj.strftime(format_str)


def is_valid_date(date_str: str) -> bool:
    """
    Check if a string is a valid date in ISO format.
    
    Args:
        date_str: The date string to check (YYYY-MM-DD)
        
    Returns:
        True if the string is a valid date, False otherwise
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def get_date_range(range_type: str, reference_date: Optional[date] = None) -> Tuple[date, date]:
    """
    Get a date range based on a range type.
    
    Args:
        range_type: The type of range ('today', 'this_week', 'this_month', 'next_week', etc.)
        reference_date: The reference date (defaults to today)
        
    Returns:
        A tuple of (start_date, end_date)
    """
    if reference_date is None:
        reference_date = datetime.now().date()
    
    if range_type == 'today':
        return reference_date, reference_date
    
    elif range_type == 'tomorrow':
        tomorrow = reference_date + timedelta(days=1)
        return tomorrow, tomorrow
    
    elif range_type == 'this_week':
        # Get the start of the week (Monday)
        start = reference_date - timedelta(days=reference_date.weekday())
        # End of the week (Sunday)
        end = start + timedelta(days=6)
        return start, end
    
    elif range_type == 'next_week':
        # Start of next week
        start = reference_date + timedelta(days=7 - reference_date.weekday())
        # End of next week
        end = start + timedelta(days=6)
        return start, end
    
    elif range_type == 'this_month':
        # Start of the month
        start = reference_date.replace(day=1)
        # End of the month (simplified approach)
        if reference_date.month == 12:
            end = date(reference_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(reference_date.year, reference_date.month + 1, 1) - timedelta(days=1)
        return start, end
    
    # Default to today
    return reference_date, reference_date
