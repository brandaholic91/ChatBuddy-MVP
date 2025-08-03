"""
Pytest configuration and fixtures for Chatbuddy MVP tests.
"""

import pytest
from unittest.mock import Mock, AsyncMock
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
    return mock_client


@pytest.fixture
def mock_webshop_client():
    """Mock webshop API client for testing."""
    mock_client = Mock()
    mock_client.search_products = AsyncMock()
    mock_client.get_product = AsyncMock()
    mock_client.get_order = AsyncMock()
    return mock_client


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    mock_client = Mock()
    mock_client.get = AsyncMock()
    mock_client.set = AsyncMock()
    mock_client.delete = AsyncMock()
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