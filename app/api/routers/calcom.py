"""
Router for Cal.com endpoints.
"""
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import EmailStr

from app.exceptions import AppException, NotFoundError, ValidationError, CalComAPIError
from app.schemas.calcom import (
    BookEventRequest, 
    BookEventResponse, 
    ListEventsRequest, 
    ListEventsResponse,
    CancelEventRequest,
    CancelEventResponse,
    RescheduleEventRequest,
    RescheduleEventResponse
)
from app.services.calcom import CalComService
from app.utils.error import format_error_response, app_exception_handler
from app.utils.logging import log_request, log_response


# Create logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/calcom",
    tags=["calcom"],
    responses={
        404: {"description": "Not found"},
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"}
    }
)


# Dependency to get services
async def get_calcom_service() -> CalComService:
    """Get Cal.com service."""
    return CalComService()


@router.get("/event-types", response_model=list)
async def get_event_types(
    calcom_service: CalComService = Depends(get_calcom_service)
):
    """
    Get all event types.
    
    Args:
        calcom_service: The Cal.com service
        
    Returns:
        A list of event types
    """
    try:
        event_types = await calcom_service.get_event_types()
        return [event_type.dict() for event_type in event_types]
    
    except CalComAPIError as e:
        logger.error(f"Cal.com API error getting event types: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting event types: {str(e)}")
        raise AppException(f"Error getting event types: {str(e)}")


@router.get("/slots", response_model=list)
async def get_available_slots(
    event_type_id: int = Query(..., description="Event type ID"),
    date: str = Query(..., description="Date (YYYY-MM-DD)"),
    calcom_service: CalComService = Depends(get_calcom_service)
):
    """
    Get available slots for an event type.
    
    Args:
        event_type_id: The event type ID
        date: The date to check for available slots
        calcom_service: The Cal.com service
        
    Returns:
        A list of available slots
    """
    try:
        # Parse date
        try:
            start_date = datetime.strptime(date, "%Y-%m-%d")
            end_date = datetime.strptime(date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        except ValueError:
            raise ValidationError(f"Invalid date format: {date}. Expected format: YYYY-MM-DD")
        
        # Get slots
        slots = await calcom_service.get_available_slots(
            event_type_id=event_type_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return [
            {
                "start": slot.start.isoformat(),
                "end": slot.end.isoformat()
            }
            for slot in slots
        ]
    
    except ValidationError as e:
        logger.error(f"Validation error getting available slots: {str(e)}")
        raise
    except CalComAPIError as e:
        logger.error(f"Cal.com API error getting available slots: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting available slots: {str(e)}")
        raise AppException(f"Error getting available slots: {str(e)}")


@router.post("/bookings", response_model=BookEventResponse)
async def book_event(
    request: BookEventRequest,
    calcom_service: CalComService = Depends(get_calcom_service)
) -> BookEventResponse:
    """
    Book a new event.
    
    Args:
        request: The booking request
        calcom_service: The Cal.com service
        
    Returns:
        The booking response
    """
    try:
        # Log request
        log_request(request.dict(), logger)
        
        # Get first attendee
        if not request.attendees:
            raise ValidationError(
                message="At least one attendee is required",
                details={"field": "attendees"}
            )
        
        attendee = request.attendees[0]
        
        # Book event
        booking = await calcom_service.book_event(
            event_type_id=request.event_type_id,
            start_time=request.start_time,
            end_time=request.end_time,
            name=attendee.name,
            email=attendee.email,
            title=request.title,
            description=request.description,
            timezone=attendee.timezone
        )
        
        # Create response
        response = BookEventResponse(
            booking_id=booking.uid,
            event_title=booking.title,
            start_time=booking.start_time,
            end_time=booking.end_time,
            attendees=request.attendees,
            status=booking.status
        )
        
        # Log response
        log_response(response.dict(), logger)
        
        return response
    
    except ValidationError as e:
        logger.error(f"Validation error booking event: {str(e)}")
        raise
    except CalComAPIError as e:
        logger.error(f"Cal.com API error booking event: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error booking event: {str(e)}")
        raise AppException(f"Error booking event: {str(e)}")


@router.post("/events", response_model=ListEventsResponse)
async def list_events(
    request: ListEventsRequest,
    calcom_service: CalComService = Depends(get_calcom_service)
) -> ListEventsResponse:
    """
    List events for a user.
    
    Args:
        request: The list events request
        calcom_service: The Cal.com service
        
    Returns:
        The list events response
    """
    try:
        # Log request
        log_request(request.dict(), logger)
        
        # Get bookings
        bookings = await calcom_service.get_bookings(
            email=request.user_email,
            start_date=request.start_date,
            end_date=request.end_date,
            status=request.status
        )
        
        # Create response
        events = []
        for booking in bookings:
            try:
                # Get event details
                event = await calcom_service.get_event(booking.uid)
                
                # Add to events list
                events.append({
                    "id": event.uid,
                    "title": event.title,
                    "description": event.description,
                    "start_time": event.start_time,
                    "end_time": event.end_time,
                    "status": event.status,
                    "attendees": [
                        {
                            "email": attendee.email,
                            "name": attendee.name,
                            "timezone": attendee.timezone
                        }
                        for attendee in event.attendees
                    ]
                })
            except Exception as event_error:
                logger.warning(f"Error getting event details for booking {booking.uid}: {str(event_error)}")
                # Continue with next booking
        
        # Create response
        response = ListEventsResponse(
            events=events,
            total=len(events)
        )
        
        # Log response
        log_response(response.dict(), logger)
        
        return response
    
    except ValidationError as e:
        logger.error(f"Validation error listing events: {str(e)}")
        raise
    except CalComAPIError as e:
        logger.error(f"Cal.com API error listing events: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing events: {str(e)}")
        raise AppException(f"Error listing events: {str(e)}")


@router.delete("/bookings/{booking_id}", response_model=CancelEventResponse)
async def cancel_event(
    booking_id: str,
    reason: Optional[str] = None,
    calcom_service: CalComService = Depends(get_calcom_service)
) -> CancelEventResponse:
    """
    Cancel an event.
    
    Args:
        booking_id: The booking ID
        reason: The reason for cancellation
        calcom_service: The Cal.com service
        
    Returns:
        The cancel event response
    """
    try:
        # Log request
        log_request({"booking_id": booking_id, "reason": reason}, logger)
        
        # Check if booking exists
        try:
            await calcom_service.get_event(booking_id)
        except Exception:
            raise NotFoundError(
                message=f"Booking with ID {booking_id} not found",
                details={"booking_id": booking_id}
            )
        
        # Cancel booking
        await calcom_service.cancel_booking(
            booking_id=booking_id,
            reason=reason
        )
        
        # Create response
        response = CancelEventResponse(
            success=True,
            booking_id=booking_id,
            status="CANCELLED"
        )
        
        # Log response
        log_response(response.dict(), logger)
        
        return response
    
    except NotFoundError as e:
        logger.error(f"Booking not found: {str(e)}")
        raise
    except CalComAPIError as e:
        logger.error(f"Cal.com API error cancelling event: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error cancelling event: {str(e)}")
        raise AppException(f"Error cancelling event: {str(e)}")


@router.patch("/bookings/{booking_id}", response_model=RescheduleEventResponse)
async def reschedule_event(
    booking_id: str,
    request: RescheduleEventRequest,
    calcom_service: CalComService = Depends(get_calcom_service)
) -> RescheduleEventResponse:
    """
    Reschedule an event.
    
    Args:
        booking_id: The booking ID
        request: The reschedule event request
        calcom_service: The Cal.com service
        
    Returns:
        The reschedule event response
    """
    try:
        # Log request
        log_request({**request.dict(), "booking_id": booking_id}, logger)
        
        # Check if booking exists
        try:
            await calcom_service.get_event(booking_id)
        except Exception:
            raise NotFoundError(
                message=f"Booking with ID {booking_id} not found",
                details={"booking_id": booking_id}
            )
        
        # Reschedule booking
        booking = await calcom_service.reschedule_booking(
            booking_id=booking_id,
            start_time=request.new_start_time,
            end_time=request.new_end_time,
            reason=request.reason
        )
        
        # Create response
        response = RescheduleEventResponse(
            success=True,
            booking_id=booking.uid,
            event_title=booking.title,
            start_time=booking.start_time,
            end_time=booking.end_time,
            status=booking.status
        )
        
        # Log response
        log_response(response.dict(), logger)
        
        return response
    
    except NotFoundError as e:
        logger.error(f"Booking not found: {str(e)}")
        raise
    except ValidationError as e:
        logger.error(f"Validation error rescheduling event: {str(e)}")
        raise
    except CalComAPIError as e:
        logger.error(f"Cal.com API error rescheduling event: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error rescheduling event: {str(e)}")
        raise AppException(f"Error rescheduling event: {str(e)}")
