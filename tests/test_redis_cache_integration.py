"""
Redis Cache Integration Tests with a real Redis client.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage

from src.workflows.langgraph_workflow import OptimizedPydanticAIToolNode, LangGraphWorkflowManager
from src.workflows.coordinator import CoordinatorAgent
from src.integrations.cache import RedisCacheService, PerformanceCache, SessionCache, CacheConfig


@pytest.fixture(scope="function")
def redis_cache_service(redis_test_client):
    """Fixture to create a RedisCacheService instance with the real test client."""
    config = CacheConfig(
        agent_response_ttl=60,
        session_ttl=120,
    )
    return RedisCacheService(config=config, redis_client=redis_test_client)


@pytest.mark.asyncio
class TestRealRedisCacheIntegration:
    """
    Integration tests for Redis cache using a real Redis client connected to a test database.
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
        """Test setting and getting a session from the session cache."""
        session_id = "test_session_123"
        session_data = {"user_id": "user_abc", "session_id": session_id}
        
        await redis_cache_service.session_cache.update_session(session_id, session_data)
        retrieved_session = await redis_cache_service.session_cache.get_session(session_id)
        
        assert retrieved_session is not None
        assert retrieved_session.user_id == "user_abc"

    async def test_cache_expiration(self, redis_cache_service: RedisCacheService):
        """Test that cache keys expire as expected."""
        cache_key = "test_expiry_key"
        cache_value = {"data": "volatile"}
        
        await redis_cache_service.performance_cache.redis_client.setex(
            f"performance:{cache_key}", 1, '{"data": "volatile"}'
        )
        
        # Wait for the key to expire
        await asyncio.sleep(1.5)
        
        retrieved_value = await redis_cache_service.performance_cache.get_cached_agent_response(cache_key)
        
        assert retrieved_value is None

    async def test_tool_node_with_real_cache(self, redis_cache_service: RedisCacheService):
        """Test OptimizedPydanticAIToolNode with a real Redis connection."""
        mock_agent = Mock()
        # Create a response that matches the LangGraph RunContext format
        response = {
            "response": {
                "response_text": "Live response",
                "model": "test_model",
                "usage": {"total_tokens": 10},
                "confidence": 0.9,
                "metadata": {
                    "cache_hit": False
                }
            }
        }
        
        # Mock the agent's run method to return this response
        mock_agent.run = AsyncMock(return_value=response)
        mock_agent_creator = Mock(return_value=mock_agent)
        
        tool_node = OptimizedPydanticAIToolNode(
            agent_creator_func=mock_agent_creator,
            dependencies_class=Mock,
            agent_name="caching_agent"
        )
        
        # Create a sample state with proper message objects
        sample_state = {
            "messages": [HumanMessage(content="Cache me")],
            "user_context": {},
            "security_context": {},
            "audit_logger": None
        }

        # Patch the get_redis_cache_service to return our real service
        with patch('src.workflows.langgraph_workflow.get_redis_cache_service', return_value=redis_cache_service):
            # First call, should be a cache miss
            result_miss = await tool_node(sample_state)
            assert "Live response" in str(result_miss["messages"][-1].content)
            
            # Second call, should be a cache hit
            result_hit = await tool_node(sample_state)
            assert "Live response" in str(result_hit["messages"][-1].content)
            assert result_hit["metadata"]["cache_hit"] is True
            
            # Agent creator should only be called once
            mock_agent_creator.assert_called_once()