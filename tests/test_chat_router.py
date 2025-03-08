"""
Tests for the chat router.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.models.chat import ChatMessage, ChatRole, ChatResponse
from app.services.chat import ChatService


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_chat_service():
    """Mock chat service fixture."""
    with patch("app.api.routers.chat.get_chat_service") as mock_get_service:
        mock_service = AsyncMock(spec=ChatService)
        mock_get_service.return_value = mock_service
        yield mock_service


def test_send_message(client, mock_chat_service):
    """Test sending a message."""
    # Mock the response from the chat service
    mock_response = ChatResponse(
        message=ChatMessage(
            role=ChatRole.ASSISTANT,
            content="Hello! How can I help you with Cal.com today?"
        ),
        function_calls=None
    )
    mock_chat_service.process_message.return_value = mock_response
    
    # Send a message
    response = client.post(
        "/api/chat/message",
        json={
            "message": "Hello",
            "user_id": "test_user",
            "session_id": "test_session"
        }
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Hello! How can I help you with Cal.com today?"
    assert data["session_id"] == "test_session"
    assert data["requires_action"] is False
    assert data["action_details"] is None
    
    # Check that the chat service was called correctly
    mock_chat_service.process_message.assert_called_once_with(
        message="Hello",
        user_id="test_user",
        session_id="test_session"
    )


def test_send_message_with_function_call(client, mock_chat_service):
    """Test sending a message that triggers a function call."""
    # Mock the response from the chat service
    mock_response = ChatResponse(
        message=ChatMessage(
            role=ChatRole.ASSISTANT,
            content="I'll help you book a meeting. Let me check available slots."
        ),
        function_calls=[
            {
                "name": "get_available_slots",
                "arguments": {
                    "date": "2025-03-15",
                    "event_type_id": 123
                }
            }
        ]
    )
    mock_chat_service.process_message.return_value = mock_response
    
    # Send a message
    response = client.post(
        "/api/chat/message",
        json={
            "message": "I want to book a meeting on March 15th",
            "user_id": "test_user",
            "session_id": "test_session"
        }
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "I'll help you book a meeting" in data["response"]
    assert data["session_id"] == "test_session"
    assert data["requires_action"] is True
    assert data["action_details"]["name"] == "get_available_slots"
    assert data["action_details"]["arguments"]["date"] == "2025-03-15"
    
    # Check that the chat service was called correctly
    mock_chat_service.process_message.assert_called_once_with(
        message="I want to book a meeting on March 15th",
        user_id="test_user",
        session_id="test_session"
    )


def test_send_message_error(client, mock_chat_service):
    """Test sending a message that causes an error."""
    # Mock an error in the chat service
    mock_chat_service.process_message.side_effect = Exception("Test error")
    
    # Send a message
    response = client.post(
        "/api/chat/message",
        json={
            "message": "Hello",
            "user_id": "test_user",
            "session_id": "test_session"
        }
    )
    
    # Check the response
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert "Test error" in data["error"]["message"]
