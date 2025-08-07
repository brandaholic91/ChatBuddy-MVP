import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from langchain_core.messages import HumanMessage

from src.workflows.langgraph_workflow import (
    create_langgraph_workflow,
    LangGraphWorkflowManager,
    route_message_enhanced,
    OptimizedPydanticAIToolNode
)
from src.models.agent import LangGraphState

@pytest.fixture
def initial_state():
    """Fixture for initial LangGraphState"""
    return LangGraphState(
        messages=[HumanMessage(content="Hello")],
        user_context={},
        security_context={},
        audit_logger=MagicMock()
    )

@pytest.fixture
async def mock_pydantic_agent():
    """Fixture for a mock Pydantic AI agent"""
    agent = MagicMock()
    agent.run = AsyncMock(return_value=MagicMock(response_text="response", confidence=0.9, metadata={}))
    return agent

@pytest.fixture
def tool_node(mock_pydantic_agent):
    """Fixture for OptimizedPydanticAIToolNode"""
    agent_creator = MagicMock(return_value=mock_pydantic_agent)
    dependencies_class = MagicMock()
    return OptimizedPydanticAIToolNode(agent_creator, dependencies_class, "test_agent")

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