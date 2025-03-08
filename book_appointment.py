"""
Script to book a specific appointment with Cal.com based on available slots.
"""
import asyncio
import json
import logging
from datetime import datetime

from app.services.calcom import CalComService
from app.exceptions import CalComAPIError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def book_appointment():
    """Book a specific appointment with Cal.com."""
    try:
        # Initialize the Cal.com service
        calcom_service = CalComService()
        
        # Parse the available slots from the previous response
        # This is the response from the get_available_slots function call
        slots_response = """{'slots': [{'start': '2025-03-14T09:00:00-07:00', 'end': '2025-03-14T09:30:00-07:00', 'date': '2025-03-14'}, {'start': '2025-03-14T09:30:00-07:00', 'end': '2025-03-14T10:00:00-07:00', 'date': '2025-03-14'}, {'start': '2025-03-14T10:00:00-07:00', 'end': '2025-03-14T10:30:00-07:00', 'date': '2025-03-14'}, {'start': '2025-03-14T10:30:00-07:00', 'end': '2025-03-14T11:00:00-07:00', 'date': '2025-03-14'}, {'start': '2025-03-14T11:00:00-07:00', 'end': '2025-03-14T11:30:00-07:00', 'date': '2025-03-14'}, {'start': '2025-03-14T11:30:00-07:00', 'end': '2025-03-14T12:00:00-07:00', 'date': '2025-03-14'}, {'start': '2025-03-14T12:00:00-07:00', 'end': '2025-03-14T12:30:00-07:00', 'date': '2025-03-14'}, {'start': '2025-03-14T12:30:00-07:00', 'end': '2025-03-14T13:00:00-07:00', 'date': '2025-03-14'}, {'start': '2025-03-14T13:00:00-07:00', 'end': '2025-03-14T13:30:00-07:00', 'date': '2025-03-14'}, {'start': '2025-03-14T13:30:00-07:00', 'end': '2025-03-14T14:00:00-07:00', 'date': '2025-03-14'}, {'start': '2025-03-14T14:00:00-07:00', 'end': '2025-03-14T14:30:00-07:00', 'date': '2025-03-14'}, {'start': '2025-03-14T14:30:00-07:00', 'end': '2025-03-14T15:00:00-07:00', 'date': '2025-03-14'}, {'start': '2025-03-14T15:00:00-07:00', 'end': '2025-03-14T15:30:00-07:00', 'date': '2025-03-14'}, {'start': '2025-03-14T15:30:00-07:00', 'end': '2025-03-14T16:00:00-07:00', 'date': '2025-03-14'}, {'start': '2025-03-14T16:00:00-07:00', 'end': '2025-03-14T16:30:00-07:00', 'date': '2025-03-14'}, {'start': '2025-03-14T16:30:00-07:00', 'end': '2025-03-14T17:00:00-07:00', 'date': '2025-03-14'}, {'start': '2025-03-17T13:00:00-07:00', 'end': '2025-03-17T13:30:00-07:00', 'date': '2025-03-17'}, {'start': '2025-03-17T13:30:00-07:00', 'end': '2025-03-17T14:00:00-07:00', 'date': '2025-03-17'}, {'start': '2025-03-17T14:00:00-07:00', 'end': '2025-03-17T14:30:00-07:00', 'date': '2025-03-17'}, {'start': '2025-03-17T14:30:00-07:00', 'end': '2025-03-17T15:00:00-07:00', 'date': '2025-03-17'}, {'start': '2025-03-17T15:00:00-07:00', 'end': '2025-03-17T15:30:00-07:00', 'date': '2025-03-17'}, {'start': '2025-03-17T15:30:00-07:00', 'end': '2025-03-17T16:00:00-07:00', 'date': '2025-03-17'}, {'start': '2025-03-17T16:00:00-07:00', 'end': '2025-03-17T16:30:00-07:00', 'date': '2025-03-17'}, {'start': '2025-03-18T09:00:00-07:00', 'end': '2025-03-18T09:30:00-07:00', 'date': '2025-03-18'}, {'start': '2025-03-18T09:30:00-07:00', 'end': '2025-03-18T10:00:00-07:00', 'date': '2025-03-18'}, {'start': '2025-03-18T10:00:00-07:00', 'end': '2025-03-18T10:30:00-07:00', 'date': '2025-03-18'}, {'start': '2025-03-18T10:30:00-07:00', 'end': '2025-03-18T11:00:00-07:00', 'date': '2025-03-18'}, {'start': '2025-03-18T11:00:00-07:00', 'end': '2025-03-18T11:30:00-07:00', 'date': '2025-03-18'}, {'start': '2025-03-18T11:30:00-07:00', 'end': '2025-03-18T12:00:00-07:00', 'date': '2025-03-18'}, {'start': '2025-03-18T12:00:00-07:00', 'end': '2025-03-18T12:30:00-07:00', 'date': '2025-03-18'}, {'start': '2025-03-18T12:30:00-07:00', 'end': '2025-03-18T13:00:00-07:00', 'date': '2025-03-18'}, {'start': '2025-03-18T13:00:00-07:00', 'end': '2025-03-18T13:30:00-07:00', 'date': '2025-03-18'}, {'start': '2025-03-18T13:30:00-07:00', 'end': '2025-03-18T14:00:00-07:00', 'date': '2025-03-18'}, {'start': '2025-03-18T14:00:00-07:00', 'end': '2025-03-18T14:30:00-07:00', 'date': '2025-03-18'}, {'start': '2025-03-18T14:30:00-07:00', 'end': '2025-03-18T15:00:00-07:00', 'date': '2025-03-18'}, {'start': '2025-03-18T15:00:00-07:00', 'end': '2025-03-18T15:30:00-07:00', 'date': '2025-03-18'}, {'start': '2025-03-18T15:30:00-07:00', 'end': '2025-03-18T16:00:00-07:00', 'date': '2025-03-18'}, {'start': '2025-03-18T16:00:00-07:00', 'end': '2025-03-18T16:30:00-07:00', 'date': '2025-03-18'}, {'start': '2025-03-18T16:30:00-07:00', 'end': '2025-03-18T17:00:00-07:00', 'date': '2025-03-18'}, {'start': '2025-03-19T09:00:00-07:00', 'end': '2025-03-19T09:30:00-07:00', 'date': '2025-03-19'}, {'start': '2025-03-19T09:30:00-07:00', 'end': '2025-03-19T10:00:00-07:00', 'date': '2025-03-19'}, {'start': '2025-03-19T10:00:00-07:00', 'end': '2025-03-19T10:30:00-07:00', 'date': '2025-03-19'}, {'start': '2025-03-19T10:30:00-07:00', 'end': '2025-03-19T11:00:00-07:00', 'date': '2025-03-19'}, {'start': '2025-03-19T11:00:00-07:00', 'end': '2025-03-19T11:30:00-07:00', 'date': '2025-03-19'}, {'start': '2025-03-19T11:30:00-07:00', 'end': '2025-03-19T12:00:00-07:00', 'date': '2025-03-19'}, {'start': '2025-03-19T12:00:00-07:00', 'end': '2025-03-19T12:30:00-07:00', 'date': '2025-03-19'}, {'start': '2025-03-19T12:30:00-07:00', 'end': '2025-03-19T13:00:00-07:00', 'date': '2025-03-19'}, {'start': '2025-03-19T13:00:00-07:00', 'end': '2025-03-19T13:30:00-07:00', 'date': '2025-03-19'}, {'start': '2025-03-19T13:30:00-07:00', 'end': '2025-03-19T14:00:00-07:00', 'date': '2025-03-19'}, {'start': '2025-03-19T14:00:00-07:00', 'end': '2025-03-19T14:30:00-07:00', 'date': '2025-03-19'}, {'start': '2025-03-19T14:30:00-07:00', 'end': '2025-03-19T15:00:00-07:00', 'date': '2025-03-19'}, {'start': '2025-03-19T15:00:00-07:00', 'end': '2025-03-19T15:30:00-07:00', 'date': '2025-03-19'}, {'start': '2025-03-19T15:30:00-07:00', 'end': '2025-03-19T16:00:00-07:00', 'date': '2025-03-19'}, {'start': '2025-03-19T16:00:00-07:00', 'end': '2025-03-19T16:30:00-07:00', 'date': '2025-03-19'}, {'start': '2025-03-19T16:30:00-07:00', 'end': '2025-03-19T17:00:00-07:00', 'date': '2025-03-19'}, {'start': '2025-03-20T09:00:00-07:00', 'end': '2025-03-20T09:30:00-07:00', 'date': '2025-03-20'}, {'start': '2025-03-20T09:30:00-07:00', 'end': '2025-03-20T10:00:00-07:00', 'date': '2025-03-20'}, {'start': '2025-03-20T10:00:00-07:00', 'end': '2025-03-20T10:30:00-07:00', 'date': '2025-03-20'}, {'start': '2025-03-20T10:30:00-07:00', 'end': '2025-03-20T11:00:00-07:00', 'date': '2025-03-20'}, {'start': '2025-03-20T11:00:00-07:00', 'end': '2025-03-20T11:30:00-07:00', 'date': '2025-03-20'}, {'start': '2025-03-20T11:30:00-07:00', 'end': '2025-03-20T12:00:00-07:00', 'date': '2025-03-20'}, {'start': '2025-03-20T12:00:00-07:00', 'end': '2025-03-20T12:30:00-07:00', 'date': '2025-03-20'}, {'start': '2025-03-20T12:30:00-07:00', 'end': '2025-03-20T13:00:00-07:00', 'date': '2025-03-20'}, {'start': '2025-03-20T13:00:00-07:00', 'end': '2025-03-20T13:30:00-07:00', 'date': '2025-03-20'}, {'start': '2025-03-20T13:30:00-07:00', 'end': '2025-03-20T14:00:00-07:00', 'date': '2025-03-20'}, {'start': '2025-03-20T14:00:00-07:00', 'end': '2025-03-20T14:30:00-07:00', 'date': '2025-03-20'}, {'start': '2025-03-20T14:30:00-07:00', 'end': '2025-03-20T15:00:00-07:00', 'date': '2025-03-20'}, {'start': '2025-03-20T15:00:00-07:00', 'end': '2025-03-20T15:30:00-07:00', 'date': '2025-03-20'}, {'start': '2025-03-20T15:30:00-07:00', 'end': '2025-03-20T16:00:00-07:00', 'date': '2025-03-20'}, {'start': '2025-03-20T16:00:00-07:00', 'end': '2025-03-20T16:30:00-07:00', 'date': '2025-03-20'}, {'start': '2025-03-20T16:30:00-07:00', 'end': '2025-03-20T17:00:00-07:00', 'date': '2025-03-20'}], 'event_type_id': 2009270, 'event_type_name': '30 Min Meeting'}"""
        
        # Convert the string to a dictionary
        slots_data = eval(slots_response)
        
        # Get the event type ID from the response
        event_type_id = slots_data.get('event_type_id')
        if not event_type_id:
            logger.error("No event type ID found in the response")
            return
        
        # Find the 2:30 PM slot on March 14th
        target_date = "2025-03-14"
        target_time = "14:30:00"  # 2:30 PM in 24-hour format
        
        # Find the slot
        target_slot = None
        for slot in slots_data.get('slots', []):
            if slot.get('date') == target_date and target_time in slot.get('start'):
                target_slot = slot
                break
        
        if not target_slot:
            logger.error(f"No slot found for {target_date} at {target_time}")
            return
        
        # Parse the start and end times
        start_time = datetime.fromisoformat(target_slot.get('start'))
        end_time = datetime.fromisoformat(target_slot.get('end'))
        
        # Book the appointment
        logger.info(f"Booking appointment for Prad M on {target_date} at {target_time}")
        booking = await calcom_service.book_event(
            event_type_id=event_type_id,
            start_time=start_time,
            end_time=end_time,
            name="Prad M",
            email="prad@praddesigns.com",
            title="Appointment with Prad M",
            description="Scheduled appointment for Prad M"
        )
        
        logger.info(f"Appointment booked successfully!")
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
    asyncio.run(book_appointment())
