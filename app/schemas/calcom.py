"""
Schemas for Cal.com API endpoints.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class AttendeeSchema(BaseModel):
    """Schema for event attendee."""
    
    email: EmailStr = Field(..., description="Attendee email")
    name: str = Field(..., description="Attendee name")
    timezone: Optional[str] = Field(None, description="Attendee timezone")


class BookEventRequest(BaseModel):
    """Schema for booking an event."""
    
    event_type_id: int = Field(..., description="Event type ID")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    title: Optional[str] = Field(None, description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    attendees: List[AttendeeSchema] = Field(..., description="Event attendees")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type_id": 123,
                "start_time": "2025-03-10T14:00:00Z",
                "end_time": "2025-03-10T15:00:00Z",
                "title": "Project Discussion",
                "description": "Discuss the new project requirements",
                "attendees": [
                    {
                        "email": "user@example.com",
                        "name": "John Doe",
                        "timezone": "America/Los_Angeles"
                    }
                ]
            }
        }


class BookEventResponse(BaseModel):
    """Schema for booking event response."""
    
    booking_id: str = Field(..., description="Booking ID")
    event_title: str = Field(..., description="Event title")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    attendees: List[AttendeeSchema] = Field(..., description="Event attendees")
    status: str = Field(..., description="Booking status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "booking_id": "booking123",
                "event_title": "Project Discussion",
                "start_time": "2025-03-10T14:00:00Z",
                "end_time": "2025-03-10T15:00:00Z",
                "attendees": [
                    {
                        "email": "user@example.com",
                        "name": "John Doe",
                        "timezone": "America/Los_Angeles"
                    }
                ],
                "status": "ACCEPTED"
            }
        }


class ListEventsRequest(BaseModel):
    """Schema for listing events."""
    
    user_email: EmailStr = Field(..., description="User email")
    start_date: Optional[datetime] = Field(None, description="Start date for filtering events")
    end_date: Optional[datetime] = Field(None, description="End date for filtering events")
    status: Optional[str] = Field(None, description="Event status for filtering")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_email": "user@example.com",
                "start_date": "2025-03-01T00:00:00Z",
                "end_date": "2025-03-31T23:59:59Z",
                "status": "ACCEPTED"
            }
        }


class EventSchema(BaseModel):
    """Schema for event in list response."""
    
    id: str = Field(..., description="Event ID")
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    status: str = Field(..., description="Event status")
    attendees: List[AttendeeSchema] = Field(..., description="Event attendees")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "event123",
                "title": "Project Discussion",
                "description": "Discuss the new project requirements",
                "start_time": "2025-03-10T14:00:00Z",
                "end_time": "2025-03-10T15:00:00Z",
                "status": "ACCEPTED",
                "attendees": [
                    {
                        "email": "user@example.com",
                        "name": "John Doe",
                        "timezone": "America/Los_Angeles"
                    }
                ]
            }
        }


class ListEventsResponse(BaseModel):
    """Schema for listing events response."""
    
    events: List[EventSchema] = Field(..., description="List of events")
    total: int = Field(..., description="Total number of events")
    
    class Config:
        json_schema_extra = {
            "example": {
                "events": [
                    {
                        "id": "event123",
                        "title": "Project Discussion",
                        "description": "Discuss the new project requirements",
                        "start_time": "2025-03-10T14:00:00Z",
                        "end_time": "2025-03-10T15:00:00Z",
                        "status": "ACCEPTED",
                        "attendees": [
                            {
                                "email": "user@example.com",
                                "name": "John Doe",
                                "timezone": "America/Los_Angeles"
                            }
                        ]
                    }
                ],
                "total": 1
            }
        }


class CancelEventRequest(BaseModel):
    """Schema for cancelling an event."""
    
    booking_id: str = Field(..., description="Booking ID")
    reason: Optional[str] = Field(None, description="Cancellation reason")
    
    class Config:
        json_schema_extra = {
            "example": {
                "booking_id": "booking123",
                "reason": "Schedule conflict"
            }
        }


class CancelEventResponse(BaseModel):
    """Schema for cancelling event response."""
    
    success: bool = Field(..., description="Whether the cancellation was successful")
    booking_id: str = Field(..., description="Booking ID")
    status: str = Field(..., description="New booking status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "booking_id": "booking123",
                "status": "CANCELLED"
            }
        }


class RescheduleEventRequest(BaseModel):
    """Schema for rescheduling an event."""
    
    booking_id: str = Field(..., description="Booking ID")
    new_start_time: datetime = Field(..., description="New event start time")
    new_end_time: datetime = Field(..., description="New event end time")
    reason: Optional[str] = Field(None, description="Rescheduling reason")
    
    class Config:
        json_schema_extra = {
            "example": {
                "booking_id": "booking123",
                "new_start_time": "2025-03-11T14:00:00Z",
                "new_end_time": "2025-03-11T15:00:00Z",
                "reason": "Schedule conflict"
            }
        }


class RescheduleEventResponse(BaseModel):
    """Schema for rescheduling event response."""
    
    success: bool = Field(..., description="Whether the rescheduling was successful")
    booking_id: str = Field(..., description="Booking ID")
    event_title: str = Field(..., description="Event title")
    start_time: datetime = Field(..., description="New event start time")
    end_time: datetime = Field(..., description="New event end time")
    status: str = Field(..., description="Booking status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "booking_id": "booking123",
                "event_title": "Project Discussion",
                "start_time": "2025-03-11T14:00:00Z",
                "end_time": "2025-03-11T15:00:00Z",
                "status": "ACCEPTED"
            }
        }
