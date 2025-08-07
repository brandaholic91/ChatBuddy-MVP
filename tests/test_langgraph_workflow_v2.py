
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage

from src.workflows.langgraph_workflow_v2 import (
    create_correct_langgraph_workflow,
    LangGraphWorkflowManagerV2,
    agent_selector_node,
    pydantic_ai_tool_node,
    should_continue,
    AgentState
)

@pytest.fixture
def initial_state_v2():
    """Fixture for initial AgentState"""
    return AgentState(
        messages=[HumanMessage(content="Hello")],
        current_question="Hello",
        active_agent="",
        user_context={},
        security_context={},
        workflow_steps=[],
        agent_responses={},
        metadata={}
    )

@pytest.mark.asyncio
async def test_agent_selector_node(initial_state_v2):
    """Test agent selector node"""
    initial_state_v2["current_question"] = "Mi a rendelésem állapota?"
    state = await agent_selector_node(initial_state_v2)
    assert state["active_agent"] == "order"

@pytest.mark.asyncio
@patch('src.workflows.langgraph_workflow_v2.get_cached_agent')
async def test_pydantic_ai_tool_node(mock_get_agent, initial_state_v2):
    """Test Pydantic AI tool node"""
    mock_agent = MagicMock()
    mock_agent.run = AsyncMock(return_value=MagicMock(data={"response_text": "response"}))
    mock_get_agent.return_value = mock_agent
    
    initial_state_v2["active_agent"] = "general"
    state = await pydantic_ai_tool_node(initial_state_v2)
    assert "response" in state["messages"][-1].content

def test_should_continue(initial_state_v2):
    """Test should_continue decision function"""
    assert should_continue(initial_state_v2) == "continue"
    initial_state_v2["agent_responses"]["general"] = {}
    initial_state_v2["active_agent"] = "general"
    assert should_continue(initial_state_v2) == "end"

def test_create_correct_langgraph_workflow():
    """Test correct workflow creation"""
    workflow = create_correct_langgraph_workflow()
    assert workflow is not None
    assert "agent_selector" in workflow.nodes
    assert "tool_executor" in workflow.nodes

@pytest.mark.asyncio
async def test_workflow_manager_v2_process_message():
    """Test V2 workflow manager processing a message"""
    manager = LangGraphWorkflowManagerV2()
    # Mock the workflow to avoid full execution
    mock_workflow = MagicMock()
    
    # Mock both ainvoke and astream methods
    test_state = AgentState(
        messages=[HumanMessage(content="test"), AIMessage(content="response")],
        current_question="test",
        active_agent="general",
        user_context={},
        security_context={},
        workflow_steps=[],
        agent_responses={},
        metadata={}
    )
    
    mock_workflow.ainvoke = AsyncMock(return_value=test_state)
    
    # Mock astream to return an async generator with the test state
    async def mock_astream(*args, **kwargs):
        yield test_state
    
    mock_workflow.astream = mock_astream
    manager._workflow = mock_workflow
    manager._initialized = True

    final_state = await manager.process_message("test")
    assert "response" in final_state["messages"][-1].content
