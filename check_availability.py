"""
Script to check availability of slots for a Cal.com event type.
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
    url = f"{CAL_API_BASE_URL}/availability"
    params = {
        "apiKey": CAL_API_KEY,
        "eventTypeId": event_type_id,
        "startTime": start_date.isoformat(),
        "endTime": end_date.isoformat(),
        "timeZone": timezone
    }
    
    logger.info(f"Getting availability with params: {params}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.text}")
            return {}
        except Exception as e:
            logger.error(f"Error getting availability: {str(e)}")
            return {}

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
        
        # Check availability for the next 7 days
        today = datetime.now()
        start_date = today
        end_date = today + timedelta(days=7)
        
        logger.info(f"Checking availability from {start_date.date()} to {end_date.date()}")
        
        # Get available slots
        availability = await get_available_slots(event_type_id, start_date, end_date)
        
        # Print availability response
        logger.info(f"Availability response: {availability}")
        
        # Try using the slots endpoint
        url = f"{CAL_API_BASE_URL}/slots"
        params = {
            "apiKey": CAL_API_KEY,
            "eventTypeId": event_type_id,
            "startTime": start_date.isoformat(),
            "endTime": end_date.isoformat(),
            "timeZone": "America/Los_Angeles"
        }
        
        logger.info(f"Getting slots with params: {params}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                slots_response = response.json()
                logger.info(f"Slots response: {slots_response}")
                
                # Parse slots from response
                available_slots = []
                if "slots" in slots_response:
                    for date, times in slots_response["slots"].items():
                        logger.info(f"Date: {date}, Slots: {len(times)}")
                        for slot in times:
                            if "time" in slot:
                                available_slots.append(slot["time"])
                
                if available_slots:
                    logger.info(f"Found {len(available_slots)} available slots")
                    for slot in available_slots[:5]:  # Show first 5 slots
                        logger.info(f"  {slot}")
                    if len(available_slots) > 5:
                        logger.info(f"  ... and {len(available_slots) - 5} more")
                else:
                    logger.error("No available slots found")
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.text}")
            except Exception as e:
                logger.error(f"Error getting slots: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
