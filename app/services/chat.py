"""
Service for chat functionality.
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

from pydantic import EmailStr

from app.exceptions import AppException, ValidationError
from app.models.chat import ChatMessage, ChatFunction, ChatRole, ChatHistory, ChatResponse
from app.models.calcom import Event, Booking
from app.services.openai import OpenAIService
from app.services.calcom import CalComService


logger = logging.getLogger(__name__)


class ChatService:
    """Service for chat functionality."""
    
    def __init__(self, openai_service: OpenAIService, calcom_service: CalComService):
        """Initialize the chat service."""
        self.openai_service = openai_service
        self.calcom_service = calcom_service
        self.sessions: Dict[str, ChatHistory] = {}
        # Get current date and time in PDT
        from datetime import datetime
        import pytz
        pdt_timezone = pytz.timezone('America/Los_Angeles')
        current_date = datetime.now(pdt_timezone).strftime("%A, %B %d, %Y")
        
        self.system_prompt = f"""
        Cal.com Scheduling Assistant - Today is {current_date} (PDT)
        
        Your primary function is to help users manage their Cal.com calendar by booking, listing, canceling, and rescheduling events.
        
        Booking workflow:
        • Check availability with get_available_slots when a user requests a meeting
        • If the slot is available, immediately book it with book_event
        • Don't request information the user has already provided (date, time, name, email, reason)
        • Complete the booking in a single step when possible
        
        For listing events:
        • Request email if not provided, then show all scheduled events
        
        For cancellations:
        • Request email if needed, locate the event, then cancel it
        
        For rescheduling:
        • Request email if needed, locate the event, ask for new time if needed, then reschedule
        
        Always prioritize efficiency and minimize back-and-forth with users.
        """
    
    def _get_or_create_session(self, session_id: Optional[str] = None) -> Tuple[str, ChatHistory]:
        """Retrieve existing chat session or initialize a new one with system prompt."""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatHistory()
            # Add system message
            self.sessions[session_id].add_message(
                ChatMessage(role=ChatRole.SYSTEM, content=self.system_prompt)
            )
        
        return session_id, self.sessions[session_id]
    
    def _get_cal_functions(self) -> List[ChatFunction]:
        """Get the Cal.com functions for OpenAI."""
        return [
            ChatFunction(
                name="get_event_types",
                description="Get available event types for booking",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            ChatFunction(
                name="get_available_slots",
                description="Get available time slots for booking a meeting",
                parameters={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "The date to check for available slots (YYYY-MM-DD)"
                        },
                        "event_type_id": {
                            "type": "integer",
                            "description": "The event type ID (optional, will use default if not provided)"
                        },
                        "duration": {
                            "type": "integer",
                            "description": "The desired meeting duration in minutes (optional, default is 30)"
                        },
                        "timezone": {
                            "type": "string",
                            "description": "The timezone for the slots (optional, default is America/Los_Angeles)"
                        }
                    },
                    "required": ["date"]
                }
            ),
            ChatFunction(
                name="book_event",
                description="Book a new event",
                parameters={
                    "type": "object",
                    "properties": {
                        "event_type_id": {
                            "type": "integer",
                            "description": "The event type ID (optional, will use default if not provided)"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "The start time of the event (ISO format)"
                        },
                        "end_time": {
                            "type": "string",
                            "description": "The end time of the event (ISO format)"
                        },
                        "duration": {
                            "type": "integer",
                            "description": "The duration of the meeting in minutes (optional, calculated from start and end times if not provided)"
                        },
                        "name": {
                            "type": "string",
                            "description": "The name of the attendee"
                        },
                        "email": {
                            "type": "string",
                            "description": "The email of the attendee"
                        },
                        "title": {
                            "type": "string",
                            "description": "The title of the event"
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the event"
                        },
                        "timezone": {
                            "type": "string",
                            "description": "The timezone for the event (optional, default is America/Los_Angeles)"
                        },
                        "language": {
                            "type": "string",
                            "description": "The language for the event (optional, default is en)"
                        }
                    },
                    "required": ["start_time", "end_time", "name", "email"]
                }
            ),
            ChatFunction(
                name="list_events",
                description="List events for a user",
                parameters={
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "The email of the user"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "The start date for filtering events (YYYY-MM-DD)"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "The end date for filtering events (YYYY-MM-DD)"
                        },
                        "status": {
                            "type": "string",
                            "description": "The status of the events to filter (ACCEPTED, PENDING, CANCELLED, etc.)"
                        }
                    },
                    "required": ["email"]
                }
            ),
            ChatFunction(
                name="cancel_event",
                description="Cancel an event",
                parameters={
                    "type": "object",
                    "properties": {
                        "booking_id": {
                            "type": "string",
                            "description": "The booking ID"
                        },
                        "reason": {
                            "type": "string",
                            "description": "The reason for cancellation"
                        }
                    },
                    "required": ["booking_id"]
                }
            ),
            ChatFunction(
                name="reschedule_event",
                description="Reschedule an event",
                parameters={
                    "type": "object",
                    "properties": {
                        "booking_id": {
                            "type": "string",
                            "description": "The booking ID"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "The new start time of the event (ISO format)"
                        },
                        "end_time": {
                            "type": "string",
                            "description": "The new end time of the event (ISO format)"
                        },
                        "reason": {
                            "type": "string",
                            "description": "The reason for rescheduling"
                        }
                    },
                    "required": ["booking_id", "start_time", "end_time"]
                }
            )
        ]
    
    async def process_message(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> ChatResponse:
        """Process a user message."""
        # Get or create session
        session_id, history = self._get_or_create_session(session_id)
        
        # Add user message to history
        history.add_message(ChatMessage(role=ChatRole.USER, content=message))
        
        # Get functions
        functions = self._get_cal_functions()
        
        # Get chat completion
        completion = await self.openai_service.chat_completion(
            messages=history.get_messages(),
            functions=functions
        )
        
        # Parse response
        parsed_response = self.openai_service.parse_response(completion)
        
        # Add assistant message to history
        history.add_message(parsed_response["message"])
        
        # Process function calls
        function_results = None
        
        if parsed_response["function_calls"]:
            function_results = await self._process_function_calls(
                parsed_response["function_calls"],
                history
            )
        
        # Return response
        return ChatResponse(
            message=parsed_response["message"],
            function_calls=parsed_response["function_calls"],
            function_results=function_results
        )
    
    async def _get_event_types(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get available event types."""
        try:
            event_types = await self.calcom_service.get_event_types()
            
            return {
                "event_types": [
                    {
                        "id": event_type.id,
                        "title": event_type.title,
                        "description": event_type.description,
                        "length": event_type.length  # Duration in minutes
                    }
                    for event_type in event_types
                ],
                "total": len(event_types)
            }
        
        except Exception as e:
            logger.error(f"Error getting event types: {str(e)}")
            raise AppException(f"Error getting event types: {str(e)}")
    
    async def _process_function_calls(
        self,
        function_calls: List[Dict[str, Any]],
        history: ChatHistory
    ) -> Dict[str, Any]:
        """Process function calls."""
        results = {}
        
        for function_call in function_calls:
            name = function_call["name"]
            args = function_call["arguments"]
            
            try:
                if name == "get_event_types":
                    result = await self._get_event_types(args)
                elif name == "get_available_slots":
                    result = await self._get_available_slots(args)
                elif name == "book_event":
                    result = await self._book_event(args)
                elif name == "list_events":
                    result = await self._list_events(args)
                elif name == "cancel_event":
                    result = await self._cancel_event(args)
                elif name == "reschedule_event":
                    result = await self._reschedule_event(args)
                else:
                    raise ValidationError(f"Unknown function: {name}")
                
                # Add function result to history
                history.add_message(
                    ChatMessage(
                        role=ChatRole.FUNCTION,
                        name=name,
                        content=str(result)
                    )
                )
                
                results[name] = result
            
            except Exception as e:
                logger.error(f"Error processing function call {name}: {str(e)}")
                # Add error to history
                history.add_message(
                    ChatMessage(
                        role=ChatRole.FUNCTION,
                        name=name,
                        content=f"Error: {str(e)}"
                    )
                )
                
                results[name] = {"error": str(e)}
        
        return results
    
    async def _get_available_slots(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get available slots for booking a meeting."""
        date_str = args.get("date")
        event_type_id = args.get("event_type_id")
        duration = args.get("duration", 30)  # Default to 30 minutes if not specified
        timezone = args.get("timezone", "America/Los_Angeles")  # Default to Los Angeles timezone
        
        if not date_str:
            raise ValidationError("Date is required")
        
        # If event_type_id is not provided, select an appropriate event type based on duration
        if not event_type_id:
            event_types = await self.calcom_service.get_event_types()
            if not event_types:
                raise ValidationError("No event types available")
            
            # Try to find an event type with the requested duration
            matching_event_type = next((et for et in event_types if et.length == duration), None)
            
            # If no exact match, find the closest one
            if not matching_event_type:
                # Sort event types by how close they are to the requested duration
                event_types.sort(key=lambda et: abs(et.length - duration))
                matching_event_type = event_types[0]
            
            event_type_id = matching_event_type.id
            logger.info(f"Selected event type ID: {event_type_id} with duration {matching_event_type.length} minutes")
        
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            # Look for slots in a 7-day window starting from the requested date
            start_date = date
            end_date = date + timedelta(days=7)
            
            # Log the request parameters
            logger.debug(f"Checking for available slots: date={date_str}, event_type_id={event_type_id}, duration={duration}, timezone={timezone}")
            
            slots = await self.calcom_service.get_available_slots(
                event_type_id=event_type_id,
                start_date=start_date,
                end_date=end_date,
                timezone=timezone
            )
            
            if not slots:
                # If no slots are available on the requested date, suggest alternative dates
                alternative_start = date + timedelta(days=1)
                alternative_end = alternative_start + timedelta(days=14)
                
                alternative_slots = await self.calcom_service.get_available_slots(
                    event_type_id=event_type_id,
                    start_date=alternative_start,
                    end_date=alternative_end
                )
                
                # Get event type details for the response
                event_types = await self.calcom_service.get_event_types()
                event_type = next((et for et in event_types if et.id == event_type_id), None)
                event_type_name = event_type.title if event_type else f"Event Type {event_type_id}"
                
                return {
                    "slots": [],
                    "message": f"No available slots found for {event_type_name} on {date_str}.",
                    "alternative_slots": [
                        {
                            "start": slot.start.isoformat(),
                            "end": slot.end.isoformat(),
                            "date": slot.start.strftime("%Y-%m-%d")
                        }
                        for slot in alternative_slots[:10]  # Limit to 10 alternative slots
                    ] if alternative_slots else [],
                    "event_type_id": event_type_id,
                    "event_type_name": event_type_name
                }
            
            # Get event type details for the response
            event_types = await self.calcom_service.get_event_types()
            event_type = next((et for et in event_types if et.id == event_type_id), None)
            event_type_name = event_type.title if event_type else f"Event Type {event_type_id}"
            
            return {
                "slots": [
                    {
                        "start": slot.start.isoformat(),
                        "end": slot.end.isoformat(),
                        "date": slot.start.strftime("%Y-%m-%d")
                    }
                    for slot in slots
                ],
                "event_type_id": event_type_id,
                "event_type_name": event_type_name
            }
        
        except Exception as e:
            logger.error(f"Error getting available slots: {str(e)}")
            raise AppException(f"Error getting available slots: {str(e)}")
    
    async def _book_event(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Book a new event."""
        event_type_id = args.get("event_type_id")
        start_time_str = args.get("start_time")
        end_time_str = args.get("end_time")
        name = args.get("name")
        email = args.get("email")
        title = args.get("title")
        description = args.get("description")
        timezone = args.get("timezone", "America/Los_Angeles")
        language = args.get("language", "en")
        
        # If event_type_id is not provided, select an appropriate event type based on duration
        if not event_type_id:
            if start_time_str and end_time_str:
                # Calculate duration from start and end times
                start_time = datetime.fromisoformat(start_time_str)
                end_time = datetime.fromisoformat(end_time_str)
                duration_minutes = int((end_time - start_time).total_seconds() / 60)
            else:
                # Default to 30 minutes if times are not provided
                duration_minutes = 30
            
            event_types = await self.calcom_service.get_event_types()
            if not event_types:
                raise ValidationError("No event types available")
            
            # Try to find an event type with the requested duration
            matching_event_type = next((et for et in event_types if et.length == duration_minutes), None)
            
            # If no exact match, find the closest one
            if not matching_event_type:
                # Sort event types by how close they are to the requested duration
                event_types.sort(key=lambda et: abs(et.length - duration_minutes))
                matching_event_type = event_types[0]
            
            event_type_id = matching_event_type.id
            logger.info(f"Selected event type ID: {event_type_id} with duration {matching_event_type.length} minutes")
        
        if not start_time_str:
            raise ValidationError("Start time is required")
        if not end_time_str:
            raise ValidationError("End time is required")
        if not name:
            raise ValidationError("Name is required")
        if not email:
            raise ValidationError("Email is required")
        
        try:
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)
            
            # Log the booking attempt
            logger.debug(f"Attempting to book event: event_type_id={event_type_id}, start_time={start_time}, end_time={end_time}, name={name}, email={email}")
            
            booking = await self.calcom_service.book_event(
                event_type_id=event_type_id,
                start_time=start_time,
                end_time=end_time,
                name=name,
                email=email,
                title=title,
                description=description,
                timezone=timezone,
                language=language
            )
            
            # Log the booking result
            logger.debug(f"Booking successful: booking_id={booking.uid}, title={booking.title}")
            
            return {
                "booking_id": booking.uid,
                "title": booking.title,
                "start_time": booking.start_time.isoformat(),
                "end_time": booking.end_time.isoformat(),
                "status": booking.status,
                "attendees": [
                    {
                        "email": attendee.email,
                        "name": attendee.name
                    }
                    for attendee in booking.attendees
                ]
            }
        
        except Exception as e:
            logger.error(f"Error booking event: {str(e)}")
            raise AppException(f"Error booking event: {str(e)}")
    
    async def _list_events(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List events for a user."""
        email = args.get("email")
        start_date_str = args.get("start_date")
        end_date_str = args.get("end_date")
        status = args.get("status")
        
        if not email:
            raise ValidationError("Email is required")
        
        try:
            # Override with current week dates
            from datetime import datetime, timedelta
            today = datetime.now()
            # Get the start of the current week (Monday)
            start_of_week = today - timedelta(days=today.weekday())
            # Get the end of the current week (Sunday)
            end_of_week = start_of_week + timedelta(days=6)
            
            # Use current week dates regardless of what was provided
            start_date = start_of_week
            end_date = end_of_week.replace(hour=23, minute=59, second=59)
            
            logger.debug(f"Using date range: {start_date.isoformat()} to {end_date.isoformat()}")
            
            # Get bookings for the specified email and date range
            # The get_bookings method now filters by email
            bookings = await self.calcom_service.get_bookings(
                email=email,
                start_date=start_date,
                end_date=end_date,
                status=status
            )
            
            return {
                "events": [
                    {
                        "id": booking.uid,
                        "title": booking.title,
                        "start_time": booking.start_time.isoformat(),
                        "end_time": booking.end_time.isoformat(),
                        "status": booking.status,
                        "attendees": [
                            {
                                "email": attendee.email,
                                "name": attendee.name
                            }
                            for attendee in booking.attendees
                        ]
                    }
                    for booking in bookings
                ],
                "total": len(bookings)
            }
        
        except Exception as e:
            logger.error(f"Error listing events: {str(e)}")
            raise AppException(f"Error listing events: {str(e)}")
    
    async def _cancel_event(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel an event."""
        booking_id = args.get("booking_id")
        reason = args.get("reason")
        
        if not booking_id:
            raise ValidationError("Booking ID is required")
        
        try:
            result = await self.calcom_service.cancel_booking(
                booking_id=booking_id,
                reason=reason
            )
            
            return {
                "success": True,
                "booking_id": booking_id,
                "status": "CANCELLED"
            }
        
        except Exception as e:
            logger.error(f"Error cancelling event: {str(e)}")
            raise AppException(f"Error cancelling event: {str(e)}")
    
    async def _reschedule_event(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Reschedule an event."""
        booking_id = args.get("booking_id")
        start_time_str = args.get("start_time")
        end_time_str = args.get("end_time")
        reason = args.get("reason")
        
        if not booking_id:
            raise ValidationError("Booking ID is required")
        if not start_time_str:
            raise ValidationError("Start time is required")
        if not end_time_str:
            raise ValidationError("End time is required")
        
        try:
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)
            
            booking = await self.calcom_service.reschedule_booking(
                booking_id=booking_id,
                start_time=start_time,
                end_time=end_time,
                reason=reason
            )
            
            return {
                "success": True,
                "booking_id": booking.uid,
                "title": booking.title,
                "start_time": booking.start_time.isoformat(),
                "end_time": booking.end_time.isoformat(),
                "status": booking.status
            }
        
        except Exception as e:
            logger.error(f"Error rescheduling event: {str(e)}")
            raise AppException(f"Error rescheduling event: {str(e)}")
