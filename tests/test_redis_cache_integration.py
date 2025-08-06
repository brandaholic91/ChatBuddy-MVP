"""
Redis Cache Integration Tests with a real Redis client.
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage

from src.models.user import User
from src.workflows.langgraph_workflow_v2 import pydantic_ai_tool_node
from src.workflows.coordinator import CoordinatorAgent
from src.integrations.cache import get_redis_cache_service, shutdown_redis_cache_service, RedisCacheService, SessionData
from src.workflows.langgraph_workflow import LangGraphWorkflowManager
from src.integrations.cache.redis_connection_pool import get_optimized_redis_pool, OptimizedRedisConnectionPool


@pytest_asyncio.fixture(scope="function")
async def redis_cache_service(redis_test_client):
    """Fixture to get the singleton RedisCacheService instance and configure it for testing."""
    # Get the singleton service instance
    service = await get_redis_cache_service()
    
    # Get the singleton pool instance
    pool = await get_optimized_redis_pool()

    # If the pool is already initialized, shut it down to reconfigure
    if pool._connected:
        await pool.shutdown()

    # Re-initialize the pool with the test client's connection settings
    redis_url = f"redis://:{redis_test_client.connection_pool.connection_kwargs.get('password', '')}@{redis_test_client.connection_pool.connection_kwargs['host']}:{redis_test_client.connection_pool.connection_kwargs['port']}/{redis_test_client.connection_pool.connection_kwargs['db']}"
    pool.redis_url = redis_url
    await pool.initialize()
    
    # Assign the re-initialized pool to the service
    service.pool = pool
    service.session_cache.pool = pool
    service.performance_cache.pool = pool
    service.rate_limit_cache.pool = pool

    yield service
    
    # Teardown: flush the test database and shutdown the service and pool
    await redis_test_client.flushdb()
    await shutdown_redis_cache_service()
    await pool.shutdown()


@pytest.mark.asyncio
class TestRealRedisCacheIntegration:
    """
    Integration tests for the optimized Redis cache using a real Redis client.
    """

    async def test_performance_cache_set_and_get(self, redis_cache_service: RedisCacheService):
        """Test setting and getting a value from the performance cache."""
        cache_key = "test_perf_key"
        cache_value = {"response": "test_data"}
        
        await redis_cache_service.performance_cache.cache_agent_response(cache_key, cache_value)
        retrieved_value = await redis_cache_service.performance_cache.get_cached_agent_response(cache_key)
        
        assert retrieved_value is not None
        assert retrieved_value["response"] == "test_data"

    async def test_session_cache_set_and_get(self, redis_cache_service: RedisCacheService):
        """Test creating and retrieving a session from the session cache."""
        session_id = await redis_cache_service.session_cache.create_session(user_id="user_abc")
        assert session_id is not None
        
        retrieved_session = await redis_cache_service.session_cache.get_session(session_id)
        
        assert retrieved_session is not None
        assert retrieved_session.user_id == "user_abc"

    async def test_cache_expiration(self, redis_cache_service: RedisCacheService):
        """Test that cache keys expire as expected."""
        cache_key = "test_expiry_key"
        
        # Use the pool directly to set a key with a short TTL
        await redis_cache_service.pool.set(cache_key, {"data": "volatile"}, 'performance', ttl=1)
        
        # Wait for the key to expire
        await asyncio.sleep(1.5)
        
        retrieved_value = await redis_cache_service.performance_cache.get_cached_agent_response(cache_key)
        
        assert retrieved_value is None

    async def test_tool_node_with_real_cache(self, redis_cache_service: RedisCacheService):
        """Test pydantic_ai_tool_node with a real Redis connection."""
        mock_agent = Mock()
        response = {"response": "Live response"}
        mock_agent.run = AsyncMock(return_value=response)
        mock_agent_creator = Mock(return_value=mock_agent)
        
        # The tool node function itself, not a class
        tool_node = pydantic_ai_tool_node
        
        sample_state = {
            "messages": [HumanMessage(content="Cache me")],
            "user_context": {},
            "security_context": {},
            "audit_logger": None,
            "active_agent": "general",
            "current_question": "Cache me",
            "agent_responses": {},
            "workflow_steps": [],
            "cache_service": redis_cache_service  # Pass the service in the state
        }

        # Patch get_cached_agent to return our mock agent
        with patch('src.workflows.langgraph_workflow_v2.get_cached_agent', return_value=mock_agent):
            # First call, should be a cache miss
            result_miss = await tool_node(sample_state)
            assert "Live response" in str(result_miss["messages"][-1].content)
            
            # Second call, should be a cache hit
            result_hit = await tool_node(sample_state)
            assert "Live response" in str(result_hit["messages"][-1].content)
            
            # Verify the agent was called only once
            mock_agent.run.assert_called_once()

    from src.models.user import User

    async def test_coordinator_with_real_cache(self, redis_cache_service: RedisCacheService):
        """Test the CoordinatorAgent with a real Redis cache."""
        coordinator = CoordinatorAgent()
        
        # Patch the get_redis_cache_service used by the coordinator
        with patch('src.workflows.coordinator.get_redis_cache_service', new_callable=AsyncMock) as mock_get_service:
            mock_get_service.return_value = redis_cache_service
            
            # First call, should be a cache miss
            response_miss = await coordinator.process_message("test message", User(id="user123", email="test@example.com"))
            assert "Mock válasz" in response_miss.response_text or "test message" in response_miss.response_text
            
            # Second call, should be a cache hit
            response_hit = await coordinator.process_message("test message", User(id="user123", email="test@example.com"))
            assert "Mock válasz" in response_hit.response_text or "test message" in response_hit.response_text
            # Note: caching is handled at the workflow level, not coordinator level