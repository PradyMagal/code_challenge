"""
Script to directly interact with the Cal.com API.
"""
import asyncio
import logging
import os
import httpx
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get API key from environment
CAL_API_KEY = os.environ.get("CAL_KEY")
if not CAL_API_KEY:
    logger.error("CAL_KEY environment variable not set")
    exit(1)

# Cal.com API configuration
CAL_API_BASE_URL = "https://api.cal.com/v1"

async def get_event_types():
    """Get all event types from Cal.com API."""
    url = f"{CAL_API_BASE_URL}/event-types"
    params = {"apiKey": CAL_API_KEY}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json().get("event_types", [])
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Error getting event types: {str(e)}")
            return []

async def get_available_slots(event_type_id, start_date, end_date, timezone="America/Los_Angeles"):
    """Get available slots for an event type."""
    url = f"{CAL_API_BASE_URL}/slots"
    params = {
        "apiKey": CAL_API_KEY,
        "eventTypeId": event_type_id,
        "startTime": start_date.isoformat(),
        "endTime": end_date.isoformat(),
        "timeZone": timezone
    }
    
    logger.info(f"Getting slots with params: {params}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.text}")
            return {}
        except Exception as e:
            logger.error(f"Error getting slots: {str(e)}")
            return {}

async def book_event(event_type_id, start_time, end_time, name, email, timezone="America/Los_Angeles"):
    """Book an event directly with Cal.com API."""
    url = f"{CAL_API_BASE_URL}/bookings"
    
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
        "language": "en",
        "title": f"Meeting with {name}",
        "metadata": {}
    }
    
    params = {"apiKey": CAL_API_KEY}
    
    logger.info(f"Booking event with data: {data}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, params=params, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.text}")
            # Try with a different location type
            if "no_available_users_found_error" in e.response.text:
                logger.info("Retrying with different location type...")
                data["responses"]["location"]["value"] = "userPhone"
                try:
                    response = await client.post(url, params=params, json=data)
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPStatusError as retry_e:
                    logger.error(f"HTTP error on retry: {retry_e.response.text}")
                    return None
            return None
        except Exception as e:
            logger.error(f"Error booking event: {str(e)}")
            return None

async def main():
    """Main function."""
    try:
        # Get event types
        event_types = await get_event_types()
        if not event_types:
            logger.error("No event types available")
            return
        
        # Print event types
        logger.info("Available event types:")
        for et in event_types:
            logger.info(f"ID: {et['id']}, Title: {et['title']}, Length: {et.get('length')} minutes")
        
        # Find a 30-minute event type
        event_type = next((et for et in event_types if et.get("length") == 30), None)
        if not event_type:
            # If no 30-minute event type, use the first one
            event_type = event_types[0]
        
        event_type_id = event_type["id"]
        logger.info(f"Using event type: {event_type['title']} (ID: {event_type_id}, Duration: {event_type.get('length')} minutes)")
        
        # Set date range for available slots
        date_str = "2025-03-12"
        start_date = datetime.fromisoformat(f"{date_str}T00:00:00")
        end_date = datetime.fromisoformat(f"{date_str}T23:59:59")
        
        # Get available slots
        slots_response = await get_available_slots(event_type_id, start_date, end_date)
        
        # Parse slots from response
        available_slots = []
        if "slots" in slots_response:
            for date, times in slots_response["slots"].items():
                for slot in times:
                    if "time" in slot:
                        available_slots.append(slot["time"])
        
        if not available_slots:
            logger.error(f"No available slots for {date_str}")
            return
        
        # Print available slots
        logger.info(f"Available slots for {date_str}:")
        for slot in available_slots:
            logger.info(f"  {slot}")
        
        # Try to find a slot at 2:30 PM
        target_time = "14:30:00"
        slot_time = next((s for s in available_slots if target_time in s), None)
        
        if not slot_time:
            logger.warning(f"No slot available at {target_time}")
            # Use the first available slot
            slot_time = available_slots[0]
            logger.info(f"Using alternative slot: {slot_time}")
        
        # Parse the slot time
        slot_datetime = datetime.fromisoformat(slot_time.replace("Z", "+00:00"))
        end_datetime = slot_datetime + timedelta(minutes=30)
        
        # Book the meeting
        logger.info(f"Booking meeting: {slot_datetime.isoformat()} to {end_datetime.isoformat()}")
        booking_response = await book_event(
            event_type_id=event_type_id,
            start_time=slot_datetime,
            end_time=end_datetime,
            name="John Doe",
            email="john.doe@example.com"
        )
        
        if booking_response:
            logger.info(f"Meeting booked successfully!")
            logger.info(f"Booking response: {booking_response}")
        else:
            logger.error("Failed to book meeting")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
