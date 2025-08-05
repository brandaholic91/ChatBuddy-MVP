import sys
import os

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""
Pytest configuration and fixtures for Chatbuddy MVP tests.
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List
from pydantic_ai.models.test import TestModel


@pytest.fixture
def test_model():
    """Test model for agent testing."""
    return TestModel()


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    mock_client = Mock()
    mock_client.table = Mock()
    mock_client.rpc = AsyncMock()
    mock_client.auth = Mock()
    mock_client.storage = Mock()
    mock_client.functions = Mock()
    return mock_client


@pytest.fixture
def mock_webshop_client():
    """Mock webshop API client for testing."""
    mock_client = Mock()
    mock_client.search_products = AsyncMock()
    mock_client.get_product = AsyncMock()
    mock_client.get_order = AsyncMock()
    mock_client.create_order = AsyncMock()
    mock_client.update_order = AsyncMock()
    return mock_client


import redis.asyncio as redis
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def redis_test_client():
    """
    Fixture to create a real Redis client for testing, connected to a test database.
    Flushes the test database after the test session.
    """
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_password = os.getenv("REDIS_PASSWORD", None)
    test_db = 1  # Use a separate DB for tests
    
    try:
        client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            db=test_db,
            decode_responses=True  # Automatically decode responses to strings
        )
        await client.ping()
    except redis.exceptions.ConnectionError as e:
        pytest.fail(f"Redis connection failed: {e}")

    yield client

    # Teardown: flush the test database and close the connection
    await client.flushdb()
    await client.close()


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    mock_client = Mock()
    mock_client.get = AsyncMock()
    mock_client.set = AsyncMock()
    mock_client.delete = AsyncMock()
    mock_client.exists = AsyncMock()
    mock_client.expire = AsyncMock()
    return mock_client


@pytest.fixture
def mock_langgraph_client():
    """Mock LangGraph client for testing."""
    mock_client = Mock()
    mock_client.invoke = AsyncMock()
    mock_client.stream = AsyncMock()
    mock_client.get_state = AsyncMock()
    return mock_client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    mock_client.chat.completions.create = AsyncMock()
    mock_client.embeddings.create = AsyncMock()
    return mock_client


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing."""
    mock_client = Mock()
    mock_client.messages.create = AsyncMock()
    return mock_client


@pytest.fixture
def mock_sendgrid_client():
    """Mock SendGrid client for testing."""
    mock_client = Mock()
    mock_client.send = AsyncMock()
    return mock_client


@pytest.fixture
def mock_twilio_client():
    """Mock Twilio client for testing."""
    mock_client = Mock()
    mock_client.messages.create = AsyncMock()
    return mock_client


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "test_user_123",
        "email": "test@example.com",
        "name": "Test User",
        "preferences": {
            "language": "hu",
            "notifications": True
        }
    }


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        "id": "prod_123",
        "name": "Test Product",
        "price": 9999.0,
        "description": "Test product description",
        "category": "electronics",
        "available": True
    }


@pytest.fixture
def sample_order_data():
    """Sample order data for testing."""
    return {
        "id": "order_123",
        "user_id": "test_user_123",
        "status": "pending",
        "total": 19998.0,
        "items": [
            {
                "product_id": "prod_123",
                "quantity": 2,
                "price": 9999.0
            }
        ]
    }


@pytest.fixture
def mock_ai_response():
    """Mock AI model response for testing."""
    return {
        "content": "Test AI response",
        "model": "test-model",
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    }


@pytest.fixture
def mock_chat_message():
    """Mock chat message for testing."""
    return {
        "id": "msg_123",
        "user_id": "test_user_123",
        "content": "Test message",
        "timestamp": "2024-01-01T12:00:00Z",
        "type": "user"
    }


@pytest.fixture
def mock_agent_state():
    """Mock agent state for testing."""
    return {
        "user_id": "test_user_123",
        "session_id": "session_123",
        "context": {
            "current_topic": "product_inquiry",
            "user_intent": "search"
        },
        "history": []
    }


@pytest.fixture
def mock_workflow_config():
    """Mock workflow configuration for testing."""
    return {
        "max_turns": 10,
        "timeout": 30,
        "fallback_agent": "general",
        "enable_logging": True
    }


@pytest_asyncio.fixture
async def mock_event_loop():
    """Mock event loop for async testing."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter for testing."""
    mock_limiter = Mock()
    mock_limiter.is_allowed = Mock(return_value=True)
    mock_limiter.record_request = Mock()
    return mock_limiter


@pytest.fixture
def mock_security_validator():
    """Mock security validator for testing."""
    mock_validator = Mock()
    mock_validator.validate_input = Mock(return_value=True)
    mock_validator.sanitize_output = Mock(return_value="sanitized_output")
    mock_validator.check_permissions = Mock(return_value=True)
    return mock_validator


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    mock_logger = Mock()
    mock_logger.info = Mock()
    mock_logger.error = Mock()
    mock_logger.warning = Mock()
    mock_logger.debug = Mock()
    return mock_logger


@pytest.fixture
def sample_test_data():
    """Comprehensive test data for various scenarios."""
    return {
        "users": [
            {
                "id": "user_1",
                "email": "user1@example.com",
                "name": "User One",
                "preferences": {"language": "hu", "notifications": True}
            },
            {
                "id": "user_2", 
                "email": "user2@example.com",
                "name": "User Two",
                "preferences": {"language": "en", "notifications": False}
            }
        ],
        "products": [
            {
                "id": "prod_1",
                "name": "Laptop",
                "price": 150000.0,
                "category": "electronics",
                "available": True
            },
            {
                "id": "prod_2",
                "name": "Phone",
                "price": 80000.0,
                "category": "electronics", 
                "available": False
            }
        ],
        "orders": [
            {
                "id": "order_1",
                "user_id": "user_1",
                "status": "completed",
                "total": 150000.0
            },
            {
                "id": "order_2",
                "user_id": "user_2", 
                "status": "pending",
                "total": 80000.0
            }
        ]
    }
