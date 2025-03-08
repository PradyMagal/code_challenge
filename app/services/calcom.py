"""
Service for interacting with Cal.com API.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

import httpx
from pydantic import EmailStr

from app.core.config import settings
from app.exceptions import CalComAPIError
from app.models.calcom import Event, EventType, Booking, AvailableSlot, Attendee


logger = logging.getLogger(__name__)


class CalComService:
    """Service for interacting with Cal.com API."""
    
    def __init__(self):
        """Initialize the Cal.com service."""
        self.api_key = settings.calcom_api_key
        self.base_url = "https://api.cal.com/v1"
        self.headers = {
            "Content-Type": "application/json"
            # API key is passed as a query parameter, not in the header
        }
        self.timeout = settings.timeout_seconds
        self.max_retries = settings.max_retries
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to the Cal.com API."""
        url = f"{self.base_url}/{endpoint}"
        
        # Initialize params if None
        if params is None:
            params = {}
        
        # Add API key to query parameters
        params["apiKey"] = self.api_key
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=data,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Cal.com API error: {e.response.text}")
                raise CalComAPIError(
                    message=f"Cal.com API error: {e.response.status_code}",
                    status_code=e.response.status_code,
                    details={"response": e.response.text}
                )
            except httpx.RequestError as e:
                logger.error(f"Cal.com API request error: {str(e)}")
                raise CalComAPIError(
                    message=f"Cal.com API request error: {str(e)}",
                    details={"error": str(e)}
                )
    
    async def get_event_types(self) -> List[EventType]:
        """Get all event types."""
        response = await self._make_request("GET", "event-types")
        return [EventType(**event_type) for event_type in response.get("event_types", [])]
    
    async def get_available_slots(
        self, 
        event_type_id: int,
        start_date: datetime,
        end_date: datetime,
        timezone: str = "America/Los_Angeles"
    ) -> List[AvailableSlot]:
        """Get available slots for an event type."""
        # Log the request parameters
        logger.debug(f"Getting available slots for event type {event_type_id} from {start_date} to {end_date}")
        
        # Get event type details to determine duration
        event_types = await self.get_event_types()
        event_type = next((et for et in event_types if et.id == event_type_id), None)
        
        if not event_type:
            logger.warning(f"Event type {event_type_id} not found")
            return []
        
        # Set up parameters according to the API documentation
        params = {
            "eventTypeId": event_type_id,
            "startTime": start_date.isoformat(),
            "endTime": end_date.isoformat(),
            "timeZone": timezone
        }
        
        # Log the request parameters
        logger.debug(f"Cal.com API slots request params: {params}")
        
        try:
            response = await self._make_request("GET", "slots", params=params)
            
            # Log the raw response for debugging
            logger.debug(f"Cal.com API slots response: {response}")
            
            available_slots = []
            
            # Check if response contains the 'slots' key (according to the API docs)
            if isinstance(response, dict) and "slots" in response:
                slots_data = response["slots"]
                
                # Iterate through each date in the response
                for date_str, time_slots in slots_data.items():
                    if isinstance(time_slots, list):
                        for slot in time_slots:
                            if isinstance(slot, dict) and "time" in slot:
                                # Get the start time from the slot
                                start_time_str = slot["time"]
                                
                                # Handle different time formats
                                if "Z" in start_time_str:
                                    start_time_str = start_time_str.replace("Z", "+00:00")
                                
                                try:
                                    start_time = datetime.fromisoformat(start_time_str)
                                    
                                    # Calculate end time based on event type duration
                                    duration = 30  # Default to 30 minutes
                                    if event_type and event_type.length:
                                        duration = event_type.length
                                    
                                    end_time = start_time + timedelta(minutes=duration)
                                    
                                    # Create an AvailableSlot object
                                    available_slots.append(
                                        AvailableSlot(
                                            start=start_time,
                                            end=end_time
                                        )
                                    )
                                except ValueError as e:
                                    logger.error(f"Error parsing time {start_time_str}: {e}")
                            else:
                                logger.warning(f"Unexpected slot format: {slot}")
                    else:
                        logger.warning(f"Unexpected time_slots format for date {date_str}: {time_slots}")
            else:
                logger.error(f"Unexpected response format: {response}")
                
            # Log the number of available slots found
            logger.info(f"Found {len(available_slots)} available slots for event type {event_type_id}")
            
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return []
    
    async def book_event(
        self,
        event_type_id: int,
        start_time: datetime,
        end_time: datetime,
        name: str,
        email: EmailStr,
        title: Optional[str] = None,
        description: Optional[str] = None,
        timezone: Optional[str] = "America/Los_Angeles",
        language: Optional[str] = "en"
    ) -> Booking:
        """Book an event."""
        # Format the data according to Cal.com API requirements
        data = {
            "eventTypeId": event_type_id,
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "responses": {
                "name": name,
                "email": email,
                "location": {
                    "value": "inPerson",
                    "optionValue": ""
                }
            },
            "timeZone": timezone,
            "language": language,
            "title": title or f"Meeting with {name}",
            "description": description,
            "metadata": {}
        }
        
        logger.debug(f"Booking event with data: {data}")
        
        try:
            response = await self._make_request("POST", "bookings", data=data)
            
            # Log the response for debugging
            logger.debug(f"Booking response: {response}")
            
            # Check if the response contains the booking data
            if "booking" in response:
                return Booking(**response.get("booking", {}))
            elif "id" in response:
                # If the response is the booking itself (not wrapped in a 'booking' field)
                return Booking(**response)
            else:
                # If we can't parse the response as a Booking, return a minimal Booking object
                logger.warning(f"Unexpected booking response format: {response}")
                return Booking(
                    id=response.get("id", 0),
                    uid=response.get("uid", "unknown"),
                    title=title or f"Meeting with {name}",
                    start_time=start_time,
                    end_time=end_time,
                    status="ACCEPTED",
                    attendees=[
                        Attendee(
                            email=email,
                            name=name,
                            timezone=timezone
                        )
                    ],
                    event_type_id=event_type_id
                )
        except CalComAPIError as e:
            logger.error(f"Cal.com API error: {e.details.get('response', str(e))}")
            # Try with a different location type if needed
            if "no_available_users_found_error" in str(e.details):
                logger.info("Retrying with different location type...")
                data["responses"]["location"]["value"] = "userPhone"
                response = await self._make_request("POST", "bookings", data=data)
                
                # Handle the response the same way as above
                if "booking" in response:
                    return Booking(**response.get("booking", {}))
                elif "id" in response:
                    return Booking(**response)
                else:
                    logger.warning(f"Unexpected booking response format: {response}")
                    return Booking(
                        id=response.get("id", 0),
                        uid=response.get("uid", "unknown"),
                        title=title or f"Meeting with {name}",
                        start_time=start_time,
                        end_time=end_time,
                        status="ACCEPTED",
                        attendees=[
                            Attendee(
                                email=email,
                                name=name,
                                timezone=timezone
                            )
                        ],
                        event_type_id=event_type_id
                    )
            raise
    
    async def get_bookings(
        self,
        email: Optional[EmailStr] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[Booking]:
        """Get bookings for a user."""
        params = {}
        if email:
            params["email"] = email
        if start_date:
            params["startDate"] = start_date.isoformat()
        if end_date:
            params["endDate"] = end_date.isoformat()
        if status:
            params["status"] = status
        
        response = await self._make_request("GET", "bookings", params=params)
        bookings = [Booking(**booking) for booking in response.get("bookings", [])]
        
        # If email is provided, filter bookings to only include those where the email is an attendee
        if email:
            filtered_bookings = []
            for booking in bookings:
                # Check if the email is in the attendees list
                is_attendee = any(attendee.email.lower() == email.lower() for attendee in booking.attendees)
                
                # Check if the email is the booking owner's email (if user field exists)
                is_owner = hasattr(booking, 'user') and booking.user and booking.user.email.lower() == email.lower()
                
                if is_attendee or is_owner:
                    filtered_bookings.append(booking)
            
            return filtered_bookings
        
        return bookings
    
    async def cancel_booking(self, booking_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Cancel a booking."""
        data = {"reason": reason} if reason else {}
        return await self._make_request("DELETE", f"bookings/{booking_id}", data=data)
    
    async def reschedule_booking(
        self,
        booking_id: str,
        start_time: datetime,
        end_time: datetime,
        reason: Optional[str] = None
    ) -> Booking:
        """Reschedule a booking."""
        data = {
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        }
        if reason:
            data["reason"] = reason
        
        response = await self._make_request("PATCH", f"bookings/{booking_id}", data=data)
        return Booking(**response.get("booking", {}))
    
    async def get_event(self, booking_id: str) -> Event:
        """Get an event by booking ID."""
        response = await self._make_request("GET", f"bookings/{booking_id}")
        booking_data = response.get("booking", {})
        
        # Get event type details
        event_type_id = booking_data.get("eventTypeId")
        event_type_response = await self._make_request("GET", f"event-types/{event_type_id}")
        event_type_data = event_type_response.get("eventType", {})
        
        # Create attendees
        attendees = [
            Attendee(**attendee)
            for attendee in booking_data.get("attendees", [])
        ]
        
        # Create event
        return Event(
            id=booking_data.get("id"),
            uid=booking_data.get("uid"),
            title=booking_data.get("title"),
            description=booking_data.get("description"),
            start_time=datetime.fromisoformat(booking_data.get("startTime")),
            end_time=datetime.fromisoformat(booking_data.get("endTime")),
            status=booking_data.get("status"),
            attendees=attendees,
            event_type=EventType(**event_type_data)
        )
