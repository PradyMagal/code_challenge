"""
Script to debug Cal.com booking issues.
"""
import asyncio
import logging
import os
import json
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

async def try_booking_approaches(event_type_id, start_time, end_time):
    """Try different approaches to booking a meeting."""
    url = f"{CAL_API_BASE_URL}/bookings"
    params = {"apiKey": CAL_API_KEY}
    
    # Common booking data
    name = "John Doe"
    email = "john.doe@example.com"
    timezone = "America/Los_Angeles"
    
    # Approach 1: Basic booking with inPerson location
    logger.info("Approach 1: Basic booking with inPerson location")
    data1 = {
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
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, params=params, json=data1)
            response.raise_for_status()
            logger.info("Approach 1 succeeded!")
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Approach 1 failed: {e.response.text}")
    
    # Approach 2: With userPhone location
    logger.info("Approach 2: With userPhone location")
    data2 = {
        "eventTypeId": event_type_id,
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "responses": {
            "name": name,
            "email": email,
            "location": {
                "value": "userPhone",
                "optionValue": "+1234567890"
            }
        },
        "timeZone": timezone,
        "language": "en",
        "title": f"Meeting with {name}",
        "metadata": {}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, params=params, json=data2)
            response.raise_for_status()
            logger.info("Approach 2 succeeded!")
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Approach 2 failed: {e.response.text}")
    
    # Approach 3: With Google Meet
    logger.info("Approach 3: With Google Meet")
    data3 = {
        "eventTypeId": event_type_id,
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "responses": {
            "name": name,
            "email": email,
            "location": {
                "value": "integrations:google:meet",
                "optionValue": ""
            }
        },
        "timeZone": timezone,
        "language": "en",
        "title": f"Meeting with {name}",
        "metadata": {}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, params=params, json=data3)
            response.raise_for_status()
            logger.info("Approach 3 succeeded!")
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Approach 3 failed: {e.response.text}")
    
    # Approach 4: With Zoom
    logger.info("Approach 4: With Zoom")
    data4 = {
        "eventTypeId": event_type_id,
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "responses": {
            "name": name,
            "email": email,
            "location": {
                "value": "integrations:zoom",
                "optionValue": ""
            }
        },
        "timeZone": timezone,
        "language": "en",
        "title": f"Meeting with {name}",
        "metadata": {}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, params=params, json=data4)
            response.raise_for_status()
            logger.info("Approach 4 succeeded!")
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Approach 4 failed: {e.response.text}")
    
    # Approach 5: With status ACCEPTED
    logger.info("Approach 5: With status ACCEPTED")
    data5 = {
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
        "status": "ACCEPTED",
        "metadata": {}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, params=params, json=data5)
            response.raise_for_status()
            logger.info("Approach 5 succeeded!")
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Approach 5 failed: {e.response.text}")
    
    # Approach 6: With attendees array
    logger.info("Approach 6: With attendees array")
    data6 = {
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
        "attendees": [
            {
                "email": email,
                "name": name,
                "timezone": timezone
            }
        ],
        "timeZone": timezone,
        "language": "en",
        "title": f"Meeting with {name}",
        "metadata": {}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, params=params, json=data6)
            response.raise_for_status()
            logger.info("Approach 6 succeeded!")
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Approach 6 failed: {e.response.text}")
    
    logger.error("All booking approaches failed")
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
        today = datetime.now()
        start_date = today
        end_date = today + timedelta(days=7)
        
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
            logger.error("No available slots found")
            return
        
        # Print available slots
        logger.info(f"Found {len(available_slots)} available slots")
        for slot in available_slots[:5]:  # Show first 5 slots
            logger.info(f"  {slot}")
        
        # Use the first available slot
        slot_time = available_slots[0]
        logger.info(f"Using slot: {slot_time}")
        
        # Parse the slot time
        slot_datetime = datetime.fromisoformat(slot_time.replace("Z", "+00:00"))
        end_datetime = slot_datetime + timedelta(minutes=30)
        
        # Try different booking approaches
        booking_response = await try_booking_approaches(event_type_id, slot_datetime, end_datetime)
        
        if booking_response:
            logger.info(f"Meeting booked successfully!")
            logger.info(f"Booking response: {json.dumps(booking_response, indent=2)}")
        else:
            logger.error("Failed to book meeting with any approach")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
