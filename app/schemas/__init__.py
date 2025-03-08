# This file makes the schemas directory a Python package
from app.schemas.chat import ChatRequest, ChatResponse
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
