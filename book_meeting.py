"""
Script to book a meeting with Cal.com.
"""
import asyncio
import logging
from datetime import datetime, timedelta

from app.services.calcom import CalComService
from app.exceptions import CalComAPIError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def book_meeting():
    """Book a meeting with Cal.com."""
    try:
        # Initialize the Cal.com service
        calcom_service = CalComService()
        
        # Get event types
        event_types = await calcom_service.get_event_types()
        if not event_types:
            logger.error("No event types available")
            return
        
        # Find a 30-minute event type
        event_type = next((et for et in event_types if et.length == 30), None)
        if not event_type:
            # If no 30-minute event type, use the first one
            event_type = event_types[0]
        
        event_type_id = event_type.id
        logger.info(f"Using event type: {event_type.title} (ID: {event_type_id}, Duration: {event_type.length} minutes)")
        
        # Set date range for available slots
        date_str = "2025-03-12"
        start_date = datetime.fromisoformat(f"{date_str}T00:00:00")
        end_date = datetime.fromisoformat(f"{date_str}T23:59:59")
        
        # Get available slots
        available_slots = await calcom_service.get_available_slots(
            event_type_id=event_type_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not available_slots:
            logger.error(f"No available slots for {date_str}")
            return
        
        # Find a slot at 2:30 PM
        target_time = "14:30:00"
        slot = next((s for s in available_slots if target_time in s.start.isoformat()), None)
        
        if not slot:
            logger.warning(f"No slot available at {target_time}")
            # Use the first available slot
            slot = available_slots[0]
            logger.info(f"Using alternative slot: {slot.start.isoformat()} to {slot.end.isoformat()}")
        
        # Book the meeting
        logger.info(f"Booking meeting: {slot.start.isoformat()} to {slot.end.isoformat()}")
        booking = await calcom_service.book_event(
            event_type_id=event_type_id,
            start_time=slot.start,
            end_time=slot.end,
            name="John Doe",
            email="john.doe@example.com",
            title="Project Discussion",
            description="Meeting to discuss the project"
        )
        
        logger.info(f"Meeting booked successfully!")
        logger.info(f"Booking ID: {booking.uid}")
        logger.info(f"Title: {booking.title}")
        logger.info(f"Start time: {booking.start_time.isoformat()}")
        logger.info(f"End time: {booking.end_time.isoformat()}")
        logger.info(f"Status: {booking.status}")
        logger.info(f"Attendees: {', '.join([attendee.name for attendee in booking.attendees])}")
    
    except CalComAPIError as e:
        logger.error(f"Cal.com API error: {e.message}")
        if hasattr(e, 'details') and e.details:
            logger.error(f"Details: {e.details}")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(book_meeting())
