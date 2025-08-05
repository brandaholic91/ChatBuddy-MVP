"""
Teszt az optimalizált LangGraph workflow-hoz.

Ez a teszt ellenőrzi az új optimalizált workflow funkcionalitását.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage

from langgraph.types import CachePolicy
from langgraph.cache.memory import InMemoryCache
from src.workflows.langgraph_workflow import (
    OptimizedPydanticAIToolNode,
    route_message_enhanced,
    LangGraphWorkflowManager,
    get_workflow_manager
)
from src.models.agent import LangGraphState


class TestOptimizedPydanticAIToolNode:
    """Teszt az optimalizált Pydantic AI Tool Node-hoz."""
    
    @pytest.fixture
    def mock_agent_creator(self):
        """Mock agent creator."""
        mock_agent = Mock()
        mock_agent.run = AsyncMock(return_value=Mock(
            response_text="Test response",
            confidence=0.9,
            metadata={"test": "data"}
        ))
        return Mock(return_value=mock_agent)
    
    @pytest.fixture
    def mock_dependencies_class(self):
        """Mock dependencies class."""
        return Mock
    
    @pytest.fixture
    def tool_node(self, mock_agent_creator, mock_dependencies_class):
        """Tool node létrehozása."""
        return OptimizedPydanticAIToolNode(
            mock_agent_creator,
            mock_dependencies_class,
            "test_agent"
        )
    
    @pytest.fixture
    def sample_state(self):
        """Minta state."""
        return {
            "messages": [HumanMessage(content="Test message")],
            "user_context": {"user_id": "test_user"},
            "security_context": Mock(),
            "audit_logger": Mock(),
            "error_count": 0
        }
    
    @pytest.mark.asyncio
    async def test_tool_node_initialization(self, tool_node):
        """Teszt a tool node inicializálását."""
        assert tool_node.agent_name == "test_agent"
        assert tool_node._agent is None
        assert tool_node._dependencies is None
    
    @pytest.mark.asyncio
    async def test_tool_node_caching(self, tool_node, sample_state, mock_agent_creator):
        """Teszt az agent caching funkcionalitását."""
        # Első hívás
        result1 = await tool_node(sample_state)
        
        # Második hívás - ugyanazt az agent-et kellene használnia
        result2 = await tool_node(sample_state)
        
        # Ellenőrizzük, hogy csak egyszer hívtuk meg az agent creator-t
        assert mock_agent_creator.call_count == 1
        assert tool_node._agent is not None
        assert tool_node._dependencies is not None


class TestEnhancedRouting:
    """Teszt a fejlesztett routing logikához."""
    
    @pytest.fixture
    def sample_state(self):
        """Minta state routing teszteléshez."""
        return {
            "messages": [HumanMessage(content="Test message")],
            "user_context": {"user_id": "test_user"},
            "audit_logger": Mock()
        }
    
    def test_marketing_routing(self, sample_state):
        """Teszt marketing agent routing-ot."""
        sample_state["messages"][0].content = "Szeretnék kedvezményt kapni"
        result = route_message_enhanced(sample_state)
        assert result["next"] == "marketing_agent"
    
    def test_product_routing(self, sample_state):
        """Teszt product agent routing-ot."""
        sample_state["messages"][0].content = "Keresek egy telefont"
        result = route_message_enhanced(sample_state)
        assert result["next"] == "product_agent"
    
    def test_order_routing(self, sample_state):
        """Teszt order agent routing-ot."""
        sample_state["messages"][0].content = "Hol van a rendelésem"
        result = route_message_enhanced(sample_state)
        assert result["next"] == "order_agent"
    
    def test_recommendation_routing(self, sample_state):
        """Teszt recommendation agent routing-ot."""
        sample_state["messages"][0].content = "Mit ajánlanál nekem"
        result = route_message_enhanced(sample_state)
        assert result["next"] == "recommendation_agent"
    
    def test_general_fallback(self, sample_state):
        """Teszt general agent fallback-ot."""
        sample_state["messages"][0].content = "Random üzenet"
        result = route_message_enhanced(sample_state)
        assert result["next"] == "general_agent"
    
    def test_weighted_scoring(self, sample_state):
        """Teszt a súlyozott scoring rendszert."""
        # Több marketing keyword
        sample_state["messages"][0].content = "Kedvezmény akció promóció kupon"
        result = route_message_enhanced(sample_state)
        assert result["next"] == "marketing_agent"


class TestWorkflowManager:
    """Teszt a workflow manager-hoz."""
    
    @pytest.fixture
    def workflow_manager(self):
        """Workflow manager létrehozása."""
        return LangGraphWorkflowManager()
    
    def test_manager_initialization(self, workflow_manager):
        """Teszt a manager inicializálását."""
        assert workflow_manager._workflow is None
        assert workflow_manager._initialized is False
        assert workflow_manager._performance_metrics["total_requests"] == 0
    
    def test_performance_metrics(self, workflow_manager):
        """Teszt a teljesítmény metrikák kezelését."""
        metrics = workflow_manager.get_performance_metrics()
        assert "total_requests" in metrics
        assert "successful_requests" in metrics
        assert "failed_requests" in metrics
        assert "average_response_time" in metrics
    
    @pytest.mark.asyncio
    async def test_workflow_manager_singleton(self):
        """Teszt a singleton pattern-t."""
        manager1 = get_workflow_manager()
        manager2 = get_workflow_manager()
        assert manager1 is manager2


class TestIntegration:
    """Integrációs tesztek."""
    
    @pytest.mark.asyncio
    async def test_enhanced_workflow_integration(self):
        """Teszt az optimalizált workflow integrációját."""
        # Ellenőrizzük, hogy a workflow létrehozható
        manager = get_workflow_manager()
        workflow = manager.get_workflow()
        
        # Ellenőrizzük, hogy a workflow nem None
        assert workflow is not None
        
        # Ellenőrizzük a teljesítmény metrikákat
        metrics = manager.get_performance_metrics()
        assert isinstance(metrics, dict)
        assert "total_requests" in metrics


if __name__ == "__main__":
    pytest.main([__file__]) 