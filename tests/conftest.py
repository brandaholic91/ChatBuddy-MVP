import sys
import os

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Pytest konfigurációk és fixtures."""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from tests.mocks import MockAIMessage, MockHumanMessage, MockChatOpenAI, MockSupabaseClient, MockRedisClient

# ===========================================
# MOCK FIXTURES (90% tesztek)
# ===========================================

@pytest.fixture(autouse=True, scope="session")
def mock_external_dependencies():
    """Auto-mock only essential external dependencies to avoid conflicts."""

    patches = [
        # LangChain core components
        patch('langchain_core.messages.AIMessage', MockAIMessage),
        patch('langchain_core.messages.HumanMessage', MockHumanMessage),
        patch('langchain_openai.ChatOpenAI', MockChatOpenAI),

        # OpenAI clients - use AsyncMock where awaited
        patch('openai.AsyncOpenAI', AsyncMock),
        patch('openai.OpenAI', MagicMock),

        # External HTTP requests
        patch('requests.get', MagicMock),
    ]

    # Start all patches
    mocks = [p.start() for p in patches]
    yield mocks

    # Stop all patches
    for p in patches:
        p.stop()

# ===========================================
# REAL INTEGRATION FIXTURES (10% tesztek)
# ===========================================

@pytest.fixture(scope="session")
def real_openai_client():
    """Valódi OpenAI kliens integráció tesztekhez."""
    import openai
    return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", "test-key"))

@pytest.fixture(scope="session")
def real_supabase_client():
    """Valódi Supabase kliens integráció tesztekhez."""
    from supabase import create_client
    return create_client(
        os.getenv("SUPABASE_URL", "http://localhost:54321"),
        os.getenv("SUPABASE_ANON_KEY", "test-key")
    )

# ===========================================
# COMMON AGENT FIXTURES
# ===========================================

@pytest.fixture
def mock_audit_logger():
    """Common audit logger mock for all agent tests."""
    from src.config.audit_logging import AuditLogger
    return AsyncMock(spec=AuditLogger)

@pytest.fixture
def sample_user():
    """Common user fixture for all agent tests."""
    from src.models.user import User
    return User(id="test_user_123", email="test@example.com")

# ===========================================
# TEST DATA FIXTURES
# ===========================================

@pytest.fixture
def sample_user_context():
    return {
        "user_id": "test_user_123",
        "session_id": "session_456",
        "language": "hu",
        "timezone": "Europe/Budapest"
    }

@pytest.fixture
def sample_chat_request():
    return {
        "message": "Szia! Segítenél termékeket keresni?",
        "user_id": "test_user_123",
        "session_id": "session_456"
    }

@pytest.fixture
def sample_products():
    return [
        {"id": 1, "name": "iPhone 15", "price": 350000, "category": "electronics"},
        {"id": 2, "name": "Samsung Galaxy", "price": 280000, "category": "electronics"},
        {"id": 3, "name": "Nike cipő", "price": 45000, "category": "fashion"}
    ]

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "test_user_1",
        "email": "user1@example.com",
        "name": "User One",
        "preferences": {"language": "hu", "notifications": True}
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
