import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from langchain_core.messages import HumanMessage

from src.workflows.langgraph_workflow import (
    create_langgraph_workflow,
    LangGraphWorkflowManager,
    route_message_enhanced,
    OptimizedPydanticAIToolNode
)
from src.utils.state_management import create_initial_state

@pytest.fixture
def initial_state():
    """Fixture for initial LangGraphState"""
    # Create an AsyncMock for audit_logger since it has async methods
    audit_logger = MagicMock()
    audit_logger.log_data_access = AsyncMock()
    audit_logger.log_routing_decision = MagicMock()  # This one is sync
    audit_logger.log_security_event = MagicMock()  # This one is sync
    
    return create_initial_state(
        user_message="Hello",
        user_context={},
        security_context={},
        audit_logger=audit_logger
    )

@pytest.fixture
def mock_pydantic_agent():
    """Fixture for a mock Pydantic AI agent"""
    # Create a Mock for the agent object (not AsyncMock, because the agent itself is not awaitable)
    agent = MagicMock()
    
    # Mock the run method to return a proper response object with attributes
    mock_result = MagicMock()
    mock_result.response_text = "response"
    mock_result.confidence = 0.9
    mock_result.metadata = {}
    
    # The agent.run method should be AsyncMock (because it's async) and return the mock_result
    agent.run = AsyncMock(return_value=mock_result)
    
    return agent

@pytest.fixture
def tool_node(mock_pydantic_agent):
    """Fixture for OptimizedPydanticAIToolNode"""
    def agent_creator():
        """Agent creator function that returns the mock agent"""
        return mock_pydantic_agent
    
    # Create a real dependencies object instead of MagicMock
    class MockDependencies:
        def __init__(self, **kwargs):
            self.supabase_client = kwargs.get('supabase_client')
            self.webshop_api = kwargs.get('webshop_api')
            self.user_context = kwargs.get('user_context', {})
            self.security_context = kwargs.get('security_context')
            self.audit_logger = kwargs.get('audit_logger')
    
    dependencies_class = MockDependencies
    node = OptimizedPydanticAIToolNode(agent_creator, dependencies_class, "test_agent")
    # Disable Redis cache for testing
    node._redis_cache = None
    return node

def test_route_message_enhanced(initial_state):
    """Test enhanced message routing"""
    initial_state["messages"] = [HumanMessage(content="kedvezmény")]
    result = route_message_enhanced(initial_state)
    assert result["next"] == "marketing_agent"

@pytest.mark.asyncio
async def test_tool_node_call(tool_node, initial_state):
    """Test tool node call"""
    result_state = await tool_node(initial_state)
    result_state["current_agent"] = "test_agent"
    assert result_state["current_agent"] == "test_agent"
    assert "response" in result_state["messages"][-1].content

@pytest.mark.asyncio
async def test_workflow_manager_process_message(initial_state):
    """Test workflow manager processing a message"""
    manager = LangGraphWorkflowManager()
    # Mock the workflow to avoid full execution
    mock_workflow = MagicMock()
    mock_workflow.ainvoke = AsyncMock(return_value=initial_state)
    manager._workflow = mock_workflow
    manager._initialized = True

    result_state = await manager.process_message(initial_state)
    assert "performance_metrics" in result_state


def test_create_langgraph_workflow():
    """Test workflow creation"""
    workflow = create_langgraph_workflow()
    assert workflow is not None
    assert "route" in workflow.nodes
    assert "product_agent" in workflow.nodes

@pytest.mark.asyncio
async def test_tool_node_cache_hit(tool_node, initial_state):
    """Test tool node cache hit"""
    # Mock Redis cache
    mock_redis_cache = MagicMock()
    mock_redis_cache.get_cached_agent_response = AsyncMock(return_value={"response_text": "cached_response"})
    tool_node._redis_cache = mock_redis_cache
    tool_node._cache_initialized = True

    result_state = await tool_node(initial_state)
    assert "cached_response" in result_state["messages"][-1].content
    assert result_state["agent_data"]["agent_responses"][0]["metadata"]["cached"] is True

@pytest.mark.asyncio
async def test_tool_node_error_handling(tool_node, initial_state):
    """Test tool node error handling"""
    tool_node._agent = tool_node.agent_creator_func()
    tool_node._agent.run = AsyncMock(side_effect=Exception("Test error"))
    result_state = await tool_node(initial_state)
    assert result_state["error_count"] == 1
    assert "Test error" in result_state["messages"][-1].content

@pytest.mark.asyncio
async def test_tool_node_security_failure(tool_node, initial_state):
    """Test tool node security validation failure"""
    with patch('src.workflows.langgraph_workflow._validate_security_context', return_value=False):
        result_state = await tool_node(initial_state)
        assert "Biztonsági hiba" in result_state["messages"][-1].content

@pytest.mark.asyncio
async def test_tool_node_gdpr_failure(tool_node, initial_state):
    """Test tool node GDPR consent failure"""
    with patch('src.workflows.langgraph_workflow._validate_gdpr_consent', new_callable=AsyncMock) as mock_gdpr:
        mock_gdpr.return_value = False
        result_state = await tool_node(initial_state)
        assert "hozzájárulásodra" in result_state["messages"][-1].content

def test_route_message_threat_detection(initial_state):
    """Test message routing with high threat detection"""
    initial_state["messages"] = [HumanMessage(content="some malicious content")]
    with patch('src.workflows.langgraph_workflow.get_threat_detector') as mock_detector:
        mock_detector.return_value.detect_threats.return_value = {"risk_level": "high"}
        result = route_message_enhanced(initial_state)
        assert result["next"] == "general_agent"

@pytest.mark.asyncio
async def test_workflow_manager_cache_hit(initial_state):
    """Test workflow manager cache hit"""
    manager = LangGraphWorkflowManager()
    mock_redis_cache = MagicMock()
    mock_redis_cache.get_cached_agent_response = AsyncMock(return_value={"state": initial_state})
    manager._redis_cache = mock_redis_cache
    manager._cache_initialized = True

    result_state = await manager.process_message(initial_state)
    assert result_state["performance_metrics"]["cache_hit"] is True
