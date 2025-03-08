"""
Test script for Cal.com API connection.
This script tests basic Cal.com API functions to verify the connection is working.
"""
import asyncio
import logging
from datetime import datetime, timedelta

from app.services.calcom import CalComService
from app.core.config import settings

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_get_event_types():
    """Test getting event types from Cal.com."""
    logger.info("Testing get_event_types...")
    cal_service = CalComService()
    
    try:
        event_types = await cal_service.get_event_types()
        logger.info(f"Successfully retrieved {len(event_types)} event types")
        
        if event_types:
            for i, event_type in enumerate(event_types):
                logger.info(f"Event Type {i+1}: ID={event_type.id}, Title={event_type.title}")
            
            # Return the first event type ID for other tests
            return event_types[0].id
        else:
            logger.warning("No event types found. Make sure you have event types configured in Cal.com")
            return None
    
    except Exception as e:
        logger.error(f"Error getting event types: {str(e)}")
        return None


async def test_get_available_slots(event_type_id):
    """Test getting available slots for an event type."""
    if not event_type_id:
        logger.warning("Skipping test_get_available_slots: No event type ID provided")
        return
    
    logger.info(f"Testing get_available_slots for event type ID {event_type_id}...")
    cal_service = CalComService()
    
    # Get slots for the next 7 days
    today = datetime.now()
    start_date = today
    end_date = today + timedelta(days=7)
    
    try:
        slots = await cal_service.get_available_slots(
            event_type_id=event_type_id,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"Successfully retrieved {len(slots)} available slots")
        
        if slots:
            for i, slot in enumerate(slots[:5]):  # Show first 5 slots
                logger.info(f"Slot {i+1}: {slot.start.isoformat()} - {slot.end.isoformat()}")
        else:
            logger.warning("No available slots found for the next 7 days")
    
    except Exception as e:
        logger.error(f"Error getting available slots: {str(e)}")


async def test_get_bookings(email="magal.pradyun@gmail.com"):
    """Test getting bookings for a user."""
    logger.info(f"Testing get_bookings for email {email}...")
    cal_service = CalComService()
    
    # Get bookings for the current week
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    try:
        bookings = await cal_service.get_bookings(
            email=email,
            start_date=start_of_week,
            end_date=end_of_week
        )
        
        logger.info(f"Successfully retrieved {len(bookings)} bookings")
        
        if bookings:
            for i, booking in enumerate(bookings):
                logger.info(f"Booking {i+1}: ID={booking.uid}, Title={booking.title}, " +
                           f"Time={booking.start_time.isoformat()} - {booking.end_time.isoformat()}")
        else:
            logger.warning(f"No bookings found for {email} this week")
    
    except Exception as e:
        logger.error(f"Error getting bookings: {str(e)}")


async def test_cal_api():
    """Run all Cal.com API tests."""
    logger.info("Starting Cal.com API tests...")
    logger.info(f"Using Cal.com API key: {settings.calcom_api_key[:5]}...{settings.calcom_api_key[-5:]}")
    
    # Test getting event types
    event_type_id = await test_get_event_types()
    
    # Test getting available slots
    await test_get_available_slots(event_type_id)
    
    # Test getting bookings
    await test_get_bookings()
    
    logger.info("Cal.com API tests completed")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_cal_api())
