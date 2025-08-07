"""
Test helper utilities and fixtures.
"""

import pytest
import asyncio
import json
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta


class TestDataGenerator:
    """Helper class for generating test data."""
    
    @staticmethod
    def generate_user_data(user_id: str = None) -> Dict[str, Any]:
        """Generate sample user data."""
        if user_id is None:
            user_id = f"user_{datetime.now().timestamp()}"
        
        return {
            "id": user_id,
            "email": f"test_{user_id}@example.com",
            "name": f"Test User {user_id}",
            "preferences": {
                "language": "hu",
                "notifications": True,
                "theme": "dark"
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def generate_product_data(product_id: str = None) -> Dict[str, Any]:
        """Generate sample product data."""
        if product_id is None:
            product_id = f"prod_{datetime.now().timestamp()}"
        
        return {
            "id": product_id,
            "name": f"Test Product {product_id}",
            "description": f"Description for product {product_id}",
            "price": 9999.0,
            "category": "electronics",
            "available": True,
            "stock": 10,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def generate_order_data(order_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """Generate sample order data."""
        if order_id is None:
            order_id = f"order_{datetime.now().timestamp()}"
        if user_id is None:
            user_id = f"user_{datetime.now().timestamp()}"
        
        return {
            "id": order_id,
            "user_id": user_id,
            "status": "pending",
            "total": 19998.0,
            "items": [
                {
                    "product_id": f"prod_{datetime.now().timestamp()}",
                    "quantity": 2,
                    "price": 9999.0
                }
            ],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def generate_chat_message(message_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """Generate sample chat message data."""
        if message_id is None:
            message_id = f"msg_{datetime.now().timestamp()}"
        if user_id is None:
            user_id = f"user_{datetime.now().timestamp()}"
        
        return {
            "id": message_id,
            "user_id": user_id,
            "content": f"Test message {message_id}",
            "timestamp": datetime.now().isoformat(),
            "type": "user",
            "session_id": f"session_{datetime.now().timestamp()}"
        }
    
    @staticmethod
    def generate_agent_state(user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """Generate sample agent state data."""
        if user_id is None:
            user_id = f"user_{datetime.now().timestamp()}"
        if session_id is None:
            session_id = f"session_{datetime.now().timestamp()}"
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "context": {
                "current_topic": "general",
                "user_intent": "conversation",
                "conversation_history": []
            },
            "history": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }


class AsyncTestHelper:
    """Helper class for async testing."""
    
    @staticmethod
    async def wait_for_condition(condition_func, timeout: float = 5.0, interval: float = 0.1):
        """Wait for a condition to be true."""
        start_time = datetime.now()
        while datetime.now() - start_time < timedelta(seconds=timeout):
            if await condition_func():
                return True
            await asyncio.sleep(interval)
        return False
    
    @staticmethod
    async def retry_async(func, max_retries: int = 3, delay: float = 0.1):
        """Retry an async function."""
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(delay)
    
    @staticmethod
    def create_async_mock(return_value: Any = None, side_effect: Any = None):
        """Create an async mock with proper return value."""
        mock = AsyncMock()
        if return_value is not None:
            mock.return_value = return_value
        if side_effect is not None:
            mock.side_effect = side_effect
        return mock


class MockHelper:
    """Helper class for creating mocks."""
    
    @staticmethod
    def create_supabase_mock():
        """Create a comprehensive Supabase mock."""
        mock_client = Mock()
        
        # Table operations
        mock_table = Mock()
        mock_table.select = Mock(return_value=mock_table)
        mock_table.insert = Mock(return_value=mock_table)
        mock_table.update = Mock(return_value=mock_table)
        mock_table.delete = Mock(return_value=mock_table)
        mock_table.eq = Mock(return_value=mock_table)
        mock_table.execute = AsyncMock(return_value={"data": [], "error": None})
        
        mock_client.table = Mock(return_value=mock_table)
        
        # RPC operations
        mock_client.rpc = AsyncMock(return_value={"data": None, "error": None})
        
        # Auth operations
        mock_auth = Mock()
        mock_auth.get_user = AsyncMock(return_value={"user": None, "error": None})
        mock_auth.sign_up = AsyncMock(return_value={"user": None, "error": None})
        mock_auth.sign_in = AsyncMock(return_value={"user": None, "error": None})
        mock_client.auth = mock_auth
        
        # Storage operations
        mock_storage = Mock()
        mock_storage.from_ = Mock(return_value=mock_storage)
        mock_storage.upload = AsyncMock(return_value={"data": None, "error": None})
        mock_storage.download = AsyncMock(return_value={"data": None, "error": None})
        mock_client.storage = mock_storage
        
        # Functions operations
        mock_functions = Mock()
        mock_functions.invoke = AsyncMock(return_value={"data": None, "error": None})
        mock_client.functions = mock_functions
        
        return mock_client
    
    @staticmethod
    def create_redis_mock():
        """Create a comprehensive Redis mock."""
        mock_client = Mock()
        
        # Basic operations
        mock_client.get = AsyncMock(return_value=None)
        mock_client.set = AsyncMock(return_value=True)
        mock_client.delete = AsyncMock(return_value=1)
        mock_client.exists = AsyncMock(return_value=0)
        mock_client.expire = AsyncMock(return_value=True)
        
        # List operations
        mock_client.lpush = AsyncMock(return_value=1)
        mock_client.rpop = AsyncMock(return_value=None)
        mock_client.llen = AsyncMock(return_value=0)
        
        # Hash operations
        mock_client.hset = AsyncMock(return_value=1)
        mock_client.hget = AsyncMock(return_value=None)
        mock_client.hgetall = AsyncMock(return_value={})
        
        # Set operations
        mock_client.sadd = AsyncMock(return_value=1)
        mock_client.smembers = AsyncMock(return_value=set())
        mock_client.sismember = AsyncMock(return_value=False)
        
        return mock_client
    
    @staticmethod
    def create_ai_model_mock():
        """Create a comprehensive AI model mock."""
        mock_model = Mock()
        
        # Basic model operations
        mock_model.generate = AsyncMock(return_value={
            "content": "Mock AI response",
            "model": "test-model",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        })
        
        mock_model.embed = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4, 0.5])
        
        # Model configuration
        mock_model.config = {
            "model_name": "test-model",
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        return mock_model


class ValidationHelper:
    """Helper class for validation and assertions."""
    
    @staticmethod
    def validate_response_structure(response: Dict[str, Any]) -> bool:
        """Validate that a response has the expected structure."""
        required_fields = ["content", "model", "usage"]
        return all(field in response for field in required_fields)
    
    @staticmethod
    def validate_user_data(user_data: Dict[str, Any]) -> bool:
        """Validate that user data has the expected structure."""
        required_fields = ["id", "email", "name", "preferences"]
        return all(field in user_data for field in required_fields)
    
    @staticmethod
    def validate_product_data(product_data: Dict[str, Any]) -> bool:
        """Validate that product data has the expected structure."""
        required_fields = ["id", "name", "price", "category"]
        return all(field in product_data for field in required_fields)
    
    @staticmethod
    def validate_order_data(order_data: Dict[str, Any]) -> bool:
        """Validate that order data has the expected structure."""
        required_fields = ["id", "user_id", "status", "total", "items"]
        return all(field in order_data for field in required_fields)
    
    @staticmethod
    def assert_response_contains(response: Dict[str, Any], expected_content: str):
        """Assert that response contains expected content."""
        assert "content" in response, "Response missing 'content' field"
        assert expected_content.lower() in response["content"].lower(), \
            f"Response content does not contain '{expected_content}'"
    
    @staticmethod
    def assert_data_structure(data: Dict[str, Any], expected_fields: List[str]):
        """Assert that data has expected fields."""
        for field in expected_fields:
            assert field in data, f"Data missing required field: {field}"


# Pytest fixtures using the helper classes
@pytest.fixture
def test_data_generator():
    """Fixture for test data generation."""
    return TestDataGenerator()


@pytest.fixture
def async_test_helper():
    """Fixture for async test helpers."""
    return AsyncTestHelper()


@pytest.fixture
def mock_helper():
    """Fixture for mock helpers."""
    return MockHelper()


@pytest.fixture
def validation_helper():
    """Fixture for validation helpers."""
    return ValidationHelper()


@pytest.fixture
def sample_users(test_data_generator):
    """Generate multiple sample users."""
    return [
        test_data_generator.generate_user_data(f"user_{i}")
        for i in range(5)
    ]


@pytest.fixture
def sample_products(test_data_generator):
    """Generate multiple sample products."""
    return [
        test_data_generator.generate_product_data(f"prod_{i}")
        for i in range(5)
    ]


@pytest.fixture
def sample_orders(test_data_generator):
    """Generate multiple sample orders."""
    return [
        test_data_generator.generate_order_data(f"order_{i}", f"user_{i}")
        for i in range(5)
    ]


@pytest.fixture
def sample_messages(test_data_generator):
    """Generate multiple sample messages."""
    return [
        test_data_generator.generate_chat_message(f"msg_{i}", f"user_{i}")
        for i in range(5)
    ] 