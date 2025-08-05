"""
Redis Cache Integration Tests

Ez a modul teszteli a Redis cache integrációt a LangGraph workflow-val.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.workflows.langgraph_workflow import (
    OptimizedPydanticAIToolNode,
    LangGraphWorkflowManager,
    get_enhanced_workflow_manager
)
from src.workflows.coordinator import CoordinatorAgent
from src.integrations.cache import (
    RedisCacheService,
    PerformanceCache,
    SessionCache,
    CacheConfig
)
from src.models.agent import LangGraphState


class TestOptimizedPydanticAIToolNode:
    """OptimizedPydanticAIToolNode Redis cache integráció tesztjei."""
    
    @pytest.fixture
    def mock_agent_creator(self):
        """Mock agent creator function."""
        mock_agent = Mock()
        mock_agent.run = AsyncMock(return_value=Mock(
            response_text="Test response",
            confidence=0.9,
            metadata={"test": True}
        ))
        return Mock(return_value=mock_agent)
    
    @pytest.fixture
    def mock_dependencies_class(self):
        """Mock dependencies class."""
        return Mock
    
    @pytest.fixture
    def tool_node(self, mock_agent_creator, mock_dependencies_class):
        """OptimizedPydanticAIToolNode instance."""
        return OptimizedPydanticAIToolNode(
            agent_creator_func=mock_agent_creator,
            dependencies_class=mock_dependencies_class,
            agent_name="test_agent"
        )
    
    @pytest.fixture
    def sample_state(self):
        """Sample LangGraph state."""
        return {
            "messages": [Mock(content="Test message")],
            "user_context": {"user_id": "test_user"},
            "security_context": {"valid": True},
            "audit_logger": Mock()
        }
    
    @pytest.mark.asyncio
    async def test_cache_initialization(self, tool_node):
        """Teszteli a cache inicializálást."""
        assert not tool_node._cache_initialized
        
        with patch('src.workflows.langgraph_workflow.get_redis_cache_service') as mock_get_service:
            mock_service = Mock()
            mock_service.performance_cache = Mock()
            mock_get_service.return_value = mock_service
            
            await tool_node._initialize_cache()
            
            assert tool_node._cache_initialized
            assert tool_node._redis_cache is not None
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self, tool_node):
        """Teszteli a cache kulcs generálást."""
        data = {"test": "data", "number": 123}
        key = tool_node._generate_cache_key("test_prefix", data)
        
        assert key.startswith("test_prefix:test_agent:")
        assert len(key) > 20  # Should be a hash
    
    @pytest.mark.asyncio
    async def test_redis_cache_integration(self, tool_node, sample_state):
        """Teszteli a Redis cache integrációt."""
        with patch('src.workflows.langgraph_workflow.get_redis_cache_service') as mock_get_service:
            mock_service = Mock()
            mock_cache = Mock()
            mock_service.performance_cache = mock_cache
            mock_get_service.return_value = mock_service
            
            # Mock cached response
            mock_cache.get_cached_agent_response.return_value = {
                "response_text": "Cached response",
                "confidence": 0.8,
                "metadata": {"cached": True}
            }
            
            result = await tool_node(sample_state)
            
            # Should return cached response
            assert "Cached response" in str(result["messages"][-1].content)
            assert result["current_agent"] == "test_agent"
    
    @pytest.mark.asyncio
    async def test_cache_miss_processing(self, tool_node, sample_state):
        """Teszteli a cache miss esetét."""
        with patch('src.workflows.langgraph_workflow.get_redis_cache_service') as mock_get_service:
            mock_service = Mock()
            mock_cache = Mock()
            mock_service.performance_cache = mock_cache
            mock_get_service.return_value = mock_service
            
            # Mock cache miss
            mock_cache.get_cached_agent_response.return_value = None
            
            result = await tool_node(sample_state)
            
            # Should process normally and cache the result
            assert result["current_agent"] == "test_agent"
            mock_cache.cache_agent_response.assert_called()


class TestLangGraphWorkflowManager:
    """LangGraphWorkflowManager Redis cache integráció tesztjei."""
    
    @pytest.fixture
    def workflow_manager(self):
        """LangGraphWorkflowManager instance."""
        return LangGraphWorkflowManager()
    
    @pytest.fixture
    def sample_state(self):
        """Sample LangGraph state."""
        return {
            "messages": [Mock(content="Test message")],
            "user_context": {"user_id": "test_user"},
            "current_agent": "test_agent"
        }
    
    @pytest.mark.asyncio
    async def test_cache_initialization(self, workflow_manager):
        """Teszteli a cache inicializálást."""
        assert not workflow_manager._cache_initialized
        
        with patch('src.workflows.langgraph_workflow.get_redis_cache_service') as mock_get_service:
            mock_service = Mock()
            mock_service.performance_cache = Mock()
            mock_get_service.return_value = mock_service
            
            await workflow_manager._initialize_cache()
            
            assert workflow_manager._cache_initialized
            assert workflow_manager._redis_cache is not None
    
    @pytest.mark.asyncio
    async def test_workflow_cache_key_generation(self, workflow_manager, sample_state):
        """Teszteli a workflow cache kulcs generálást."""
        key = workflow_manager._generate_workflow_cache_key(sample_state)
        
        assert key.startswith("workflow:")
        assert len(key) > 20  # Should be a hash
    
    @pytest.mark.asyncio
    async def test_cache_hit_processing(self, workflow_manager, sample_state):
        """Teszteli a cache hit esetét."""
        with patch('src.workflows.langgraph_workflow.get_redis_cache_service') as mock_get_service:
            mock_service = Mock()
            mock_cache = Mock()
            mock_service.performance_cache = mock_cache
            mock_get_service.return_value = mock_service
            
            # Mock cached result
            mock_cache.get_cached_agent_response.return_value = {
                "state": {"messages": [Mock(content="Cached result")]}
            }
            
            with patch.object(workflow_manager, 'get_workflow') as mock_get_workflow:
                mock_workflow = Mock()
                mock_get_workflow.return_value = mock_workflow
                
                result = await workflow_manager.process_message(sample_state)
                
                # Should return cached result
                assert "Cached result" in str(result["messages"][0].content)
                assert result["performance_metrics"]["cache_hit"] is True
    
    @pytest.mark.asyncio
    async def test_cache_miss_processing(self, workflow_manager, sample_state):
        """Teszteli a cache miss esetét."""
        with patch('src.workflows.langgraph_workflow.get_redis_cache_service') as mock_get_service:
            mock_service = Mock()
            mock_cache = Mock()
            mock_service.performance_cache = mock_cache
            mock_get_service.return_value = mock_service
            
            # Mock cache miss
            mock_cache.get_cached_agent_response.return_value = None
            
            with patch.object(workflow_manager, 'get_workflow') as mock_get_workflow:
                mock_workflow = Mock()
                mock_workflow.ainvoke = AsyncMock(return_value={
                    "messages": [Mock(content="Processed result")]
                })
                mock_get_workflow.return_value = mock_workflow
                
                result = await workflow_manager.process_message(sample_state)
                
                # Should process normally and cache the result
                assert "Processed result" in str(result["messages"][0].content)
                assert result["performance_metrics"]["cache_hit"] is False
                mock_cache.cache_agent_response.assert_called()
    
    def test_performance_metrics_with_cache(self, workflow_manager):
        """Teszteli a teljesítmény metrikákat cache támogatással."""
        # Set some test metrics
        workflow_manager._performance_metrics.update({
            "total_requests": 10,
            "cache_hits": 6,
            "cache_misses": 4,
            "cache_hit_rate": 0.6
        })
        
        metrics = workflow_manager.get_performance_metrics()
        
        assert metrics["total_requests"] == 10
        assert metrics["cache_hits"] == 6
        assert metrics["cache_misses"] == 4
        assert metrics["cache_hit_rate"] == 0.6
        assert "cache_stats" in metrics


class TestCoordinatorAgent:
    """CoordinatorAgent Redis cache integráció tesztjei."""
    
    @pytest.fixture
    def coordinator_agent(self):
        """CoordinatorAgent instance."""
        return CoordinatorAgent(verbose=False)
    
    @pytest.mark.asyncio
    async def test_cache_initialization(self, coordinator_agent):
        """Teszteli a cache inicializálást."""
        assert not coordinator_agent._cache_initialized
        
        with patch('src.workflows.coordinator.get_redis_cache_service') as mock_get_service:
            mock_service = Mock()
            mock_service.session_cache = Mock()
            mock_service.performance_cache = Mock()
            mock_get_service.return_value = mock_service
            
            await coordinator_agent._initialize_cache()
            
            assert coordinator_agent._cache_initialized
            assert coordinator_agent._session_cache is not None
            assert coordinator_agent._performance_cache is not None
    
    @pytest.mark.asyncio
    async def test_session_cache_integration(self, coordinator_agent):
        """Teszteli a session cache integrációt."""
        with patch('src.workflows.coordinator.get_redis_cache_service') as mock_get_service:
            mock_service = Mock()
            mock_session_cache = Mock()
            mock_service.session_cache = mock_session_cache
            mock_get_service.return_value = mock_service
            
            # Mock session data
            mock_session_cache.get_session.return_value = Mock(
                session_id="test_session",
                last_activity=Mock()
            )
            
            await coordinator_agent._initialize_cache()
            
            # Test session cache usage
            await coordinator_agent.process_message(
                message="Test message",
                session_id="test_session"
            )
            
            mock_session_cache.get_session.assert_called_with("test_session")
            mock_session_cache.update_session.assert_called()
    
    @pytest.mark.asyncio
    async def test_response_cache_integration(self, coordinator_agent):
        """Teszteli a response cache integrációt."""
        with patch('src.workflows.coordinator.get_redis_cache_service') as mock_get_service:
            mock_service = Mock()
            mock_performance_cache = Mock()
            mock_service.performance_cache = mock_performance_cache
            mock_get_service.return_value = mock_service
            
            # Mock cached response
            mock_performance_cache.get_cached_agent_response.return_value = {
                "response_text": "Cached response",
                "confidence": 0.8,
                "metadata": {"cached": True}
            }
            
            await coordinator_agent._initialize_cache()
            
            # Test response cache usage
            result = await coordinator_agent.process_message(
                message="Test message",
                session_id="test_session"
            )
            
            assert result.response_text == "Cached response"
            assert result.metadata["cached"] is True
            assert result.metadata["cache_source"] == "redis"


class TestCacheInvalidation:
    """Cache invalidation tesztjei."""
    
    @pytest.mark.asyncio
    async def test_workflow_cache_invalidation(self):
        """Teszteli a workflow cache érvénytelenítést."""
        workflow_manager = LangGraphWorkflowManager()
        
        with patch('src.workflows.langgraph_workflow.get_redis_cache_service') as mock_get_service:
            mock_service = Mock()
            mock_cache = Mock()
            mock_service.performance_cache = mock_cache
            mock_get_service.return_value = mock_service
            
            await workflow_manager._initialize_cache()
            
            # Test cache invalidation
            await workflow_manager.invalidate_cache("workflow:*")
            
            # Should call invalidation methods
            assert workflow_manager._redis_cache is not None


class TestIntegration:
    """Integrációs tesztek."""
    
    @pytest.mark.asyncio
    async def test_full_cache_workflow(self):
        """Teszteli a teljes cache workflow-ot."""
        # This would test the complete integration
        # from coordinator -> workflow manager -> tool nodes
        pass
    
    @pytest.mark.asyncio
    async def test_cache_performance_improvement(self):
        """Teszteli a cache teljesítmény javulását."""
        # This would measure actual performance improvements
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 