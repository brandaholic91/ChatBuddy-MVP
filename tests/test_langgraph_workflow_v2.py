"""
Tests for the correct LangGraph + Pydantic AI integration implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.workflows.langgraph_workflow_v2 import (
    AgentState,
    agent_selector_node,
    pydantic_ai_tool_node,
    should_continue,
    create_correct_langgraph_workflow,
    LangGraphWorkflowManagerV2,
    get_correct_workflow_manager,
    create_agent_dependencies
)


class TestAgentState:
    """Test AgentState TypedDict functionality."""
    
    def test_agent_state_creation(self):
        """Test creating an AgentState."""
        state: AgentState = {
            "messages": [HumanMessage(content="test")],
            "current_question": "test question",
            "active_agent": "general",
            "user_context": {"user_id": "test"},
            "security_context": {},
            "workflow_steps": ["step1"],
            "agent_responses": {},
            "metadata": {}
        }
        
        assert state["current_question"] == "test question"
        assert state["active_agent"] == "general"
        assert len(state["messages"]) == 1
        assert state["user_context"]["user_id"] == "test"


class TestAgentSelectorNode:
    """Test agent selector node functionality."""
    
    @pytest.mark.asyncio
    async def test_product_agent_selection(self):
        """Test product agent selection."""
        state: AgentState = {
            "messages": [HumanMessage(content="Milyen telefonjaink vannak?")],
            "current_question": "Milyen telefonjaink vannak?",
            "active_agent": "",
            "user_context": {},
            "security_context": {},
            "workflow_steps": [],
            "agent_responses": {},
            "metadata": {}
        }
        
        result = await agent_selector_node(state)
        
        assert result["active_agent"] == "product"
        assert "agent_selected_product" in result["workflow_steps"]
    
    @pytest.mark.asyncio
    async def test_order_agent_selection(self):
        """Test order agent selection."""
        state: AgentState = {
            "messages": [HumanMessage(content="Hol a rendelesem?")],
            "current_question": "Hol a rendelesem?",
            "active_agent": "",
            "user_context": {},
            "security_context": {},
            "workflow_steps": [],
            "agent_responses": {},
            "metadata": {}
        }
        
        result = await agent_selector_node(state)
        
        assert result["active_agent"] == "order"
        assert "agent_selected_order" in result["workflow_steps"]
    
    @pytest.mark.asyncio
    async def test_marketing_agent_selection(self):
        """Test marketing agent selection."""
        state: AgentState = {
            "messages": [HumanMessage(content="Van kedvezmeny?")],
            "current_question": "Van kedvezmeny?",
            "active_agent": "",
            "user_context": {},
            "security_context": {},
            "workflow_steps": [],
            "agent_responses": {},
            "metadata": {}
        }
        
        result = await agent_selector_node(state)
        
        assert result["active_agent"] == "marketing"
        assert "agent_selected_marketing" in result["workflow_steps"]
    
    @pytest.mark.asyncio
    async def test_recommendation_agent_selection(self):
        """Test recommendation agent selection."""
        state: AgentState = {
            "messages": [HumanMessage(content="Mit ajanlasz?")],
            "current_question": "Mit ajanlasz?",
            "active_agent": "",
            "user_context": {},
            "security_context": {},
            "workflow_steps": [],
            "agent_responses": {},
            "metadata": {}
        }
        
        result = await agent_selector_node(state)
        
        assert result["active_agent"] == "recommendation"
        assert "agent_selected_recommendation" in result["workflow_steps"]
    
    @pytest.mark.asyncio
    async def test_general_agent_fallback(self):
        """Test general agent as fallback."""
        state: AgentState = {
            "messages": [HumanMessage(content="Szia!")],
            "current_question": "Szia!",
            "active_agent": "",
            "user_context": {},
            "security_context": {},
            "workflow_steps": [],
            "agent_responses": {},
            "metadata": {}
        }
        
        result = await agent_selector_node(state)
        
        assert result["active_agent"] == "general"
        assert "agent_selected_general" in result["workflow_steps"]


class TestPydanticAIToolNode:
    """Test Pydantic AI tool node functionality."""
    
    @pytest.mark.asyncio
    async def test_tool_node_mock_response(self):
        """Test tool node with mock response (API key missing)."""
        state: AgentState = {
            "messages": [HumanMessage(content="test")],
            "current_question": "test question",
            "active_agent": "general",
            "user_context": {"user_id": "test"},
            "security_context": {},
            "workflow_steps": [],
            "agent_responses": {},
            "metadata": {}
        }
        
        result = await pydantic_ai_tool_node(state)
        
        # Should have AI message added
        assert len(result["messages"]) == 2
        assert isinstance(result["messages"][-1], AIMessage)
        
        # Should have agent response
        assert "general" in result["agent_responses"]
        agent_response = result["agent_responses"]["general"]
        
        # Could be either mock response OR real response (if API key is available)
        response_text = agent_response["response_text"]
        is_mock_mode = agent_response.get("metadata", {}).get("mock_mode", False)
        
        # Accept either mock or real response
        assert (
            "Mock válasz" in response_text or  # Mock mode
            len(response_text) > 10  # Real response (should be longer)
        ), f"Unexpected response: {response_text}"
        
        # Should have workflow step
        assert "agent_executed_general" in result["workflow_steps"]


class TestShouldContinue:
    """Test continuation logic."""
    
    def test_should_end_with_response(self):
        """Test that workflow ends when response is available."""
        state: AgentState = {
            "messages": [HumanMessage(content="test"), AIMessage(content="response")],
            "current_question": "test",
            "active_agent": "general",
            "user_context": {},
            "security_context": {},
            "workflow_steps": ["agent_executed_general"],
            "agent_responses": {"general": {"response_text": "test response"}},
            "metadata": {}
        }
        
        result = should_continue(state)
        assert result == "end"
    
    def test_should_end_with_error(self):
        """Test that workflow ends when there's an error."""
        state: AgentState = {
            "messages": [HumanMessage(content="test")],
            "current_question": "test",
            "active_agent": "general",
            "user_context": {},
            "security_context": {},
            "workflow_steps": ["agent_error_something"],
            "agent_responses": {},
            "metadata": {}
        }
        
        result = should_continue(state)
        assert result == "end"


class TestCreateAgentDependencies:
    """Test agent dependencies creation."""
    
    def test_product_dependencies(self):
        """Test product agent dependencies creation."""
        state: AgentState = {
            "messages": [],
            "current_question": "",
            "active_agent": "",
            "user_context": {"user_id": "test"},
            "security_context": {"test": True},
            "workflow_steps": [],
            "agent_responses": {},
            "metadata": {}
        }
        
        deps = create_agent_dependencies(state, "product")
        
        assert deps.user_context["user_id"] == "test"
        assert deps.security_context["test"] is True
    
    def test_general_dependencies_fallback(self):
        """Test fallback to general dependencies."""
        state: AgentState = {
            "messages": [],
            "current_question": "",
            "active_agent": "",
            "user_context": {},
            "security_context": {},
            "workflow_steps": [],
            "agent_responses": {},
            "metadata": {}
        }
        
        deps = create_agent_dependencies(state, "unknown")
        
        # Should create GeneralDependencies for unknown agent type
        from src.agents.general.agent import GeneralDependencies
        assert isinstance(deps, GeneralDependencies)


class TestWorkflowCreation:
    """Test workflow creation and compilation."""
    
    def test_create_workflow(self):
        """Test workflow creation."""
        workflow = create_correct_langgraph_workflow()
        
        # Should be compiled workflow
        assert workflow is not None
        
        # Should have proper nodes
        # Note: We can't easily test node names without accessing internals


class TestLangGraphWorkflowManagerV2:
    """Test the new workflow manager."""
    
    def test_manager_initialization(self):
        """Test workflow manager initialization."""
        manager = LangGraphWorkflowManagerV2()
        
        assert manager._workflow is None
        assert manager._initialized is False
    
    def test_get_workflow_lazy_loading(self):
        """Test lazy loading of workflow."""
        manager = LangGraphWorkflowManagerV2()
        
        workflow = manager.get_workflow()
        
        assert workflow is not None
        assert manager._initialized is True
        assert manager._workflow is workflow
        
        # Second call should return same instance
        workflow2 = manager.get_workflow()
        assert workflow2 is workflow
    
    @pytest.mark.asyncio
    async def test_process_message_basic(self):
        """Test basic message processing."""
        manager = LangGraphWorkflowManagerV2()
        
        result = await manager.process_message(
            user_message="Szia!",
            user_context={"user_id": "test"},
            security_context={}
        )
        
        # Should have proper initial state structure
        assert result["current_question"] == "Szia!"
        assert result["user_context"]["user_id"] == "test"
        assert "workflow_started" in result["workflow_steps"]
        
        # Should have selected agent
        assert result["active_agent"] == "general"
        
        # Should have messages
        assert len(result["messages"]) >= 1
        assert result["messages"][0].content == "Szia!"
    
    @pytest.mark.asyncio
    async def test_process_message_error_handling(self):
        """Test error handling in message processing."""
        manager = LangGraphWorkflowManagerV2()
        
        # Test with None message (should handle gracefully)
        result = await manager.process_message(
            user_message="",  # Empty message
            user_context=None,
            security_context=None
        )
        
        # Should still work with empty/None values
        assert result is not None
        assert "messages" in result
        assert "workflow_steps" in result


class TestWorkflowManagerSingleton:
    """Test workflow manager singleton functionality."""
    
    def test_singleton_instance(self):
        """Test that get_correct_workflow_manager returns singleton."""
        manager1 = get_correct_workflow_manager()
        manager2 = get_correct_workflow_manager()
        
        assert manager1 is manager2
    
    def test_singleton_type(self):
        """Test singleton returns correct type."""
        manager = get_correct_workflow_manager()
        
        assert isinstance(manager, LangGraphWorkflowManagerV2)


class TestIntegration:
    """Integration tests for the complete workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_integration(self):
        """Test complete workflow from start to finish."""
        manager = get_correct_workflow_manager()
        
        # Test different agent types
        test_cases = [
            ("Milyen telefonjaink vannak?", "product"),
            ("Hol a rendelesem?", "order"),
            ("Mit ajanlasz?", "recommendation"),
            ("Van akcio?", "marketing"),
            ("Segitesz?", "general")
        ]
        
        for message, expected_agent in test_cases:
            result = await manager.process_message(
                user_message=message,
                user_context={"user_id": "test"},
                security_context={}
            )
            
            # Check agent selection
            assert result["active_agent"] == expected_agent, f"Failed for message: {message}"
            
            # Check workflow completion
            assert len(result["messages"]) >= 2  # Human + AI message
            assert result["agent_responses"]  # Should have agent response
            assert f"agent_selected_{expected_agent}" in result["workflow_steps"]
            assert f"agent_executed_{expected_agent}" in result["workflow_steps"]


# Pytest configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v"])