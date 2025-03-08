"""
Models for Cal.com API integration.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EventType(BaseModel):
    """Model for Cal.com event type."""
    
    id: int
    slug: str
    title: str
    description: Optional[str] = None
    length: int  # Duration in minutes
    hidden: bool = False
    
    class Config:
        from_attributes = True


class AvailableSlot(BaseModel):
    """Model for available time slot."""
    
    start: datetime
    end: datetime
    
    class Config:
        from_attributes = True


class Attendee(BaseModel):
    """Model for event attendee."""
    
    email: str
    name: str
    timezone: Optional[str] = None
    
    class Config:
        from_attributes = True


class Booking(BaseModel):
    """Model for Cal.com booking."""
    
    id: int
    uid: str
    title: str
    description: Optional[str] = None
    start_time: datetime = Field(..., alias="startTime")
    end_time: datetime = Field(..., alias="endTime")
    status: str  # ACCEPTED, PENDING, CANCELLED, etc.
    attendees: List[Attendee]
    event_type_id: int = Field(..., alias="eventTypeId")
    
    class Config:
        from_attributes = True
        populate_by_name = True


class Event(BaseModel):
    """Model for Cal.com event (combines booking and event type info)."""
    
    id: int
    uid: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    status: str
    attendees: List[Attendee]
    event_type: EventType
    
    class Config:
        from_attributes = True
