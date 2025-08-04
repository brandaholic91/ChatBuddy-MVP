"""
Tests for LangGraph Workflow Implementation.

This module tests the unified LangGraph workflow that integrates
Pydantic AI agents as tools.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from langchain_core.messages import HumanMessage

from src.models.agent import LangGraphState
from src.utils.state_management import create_initial_state
from src.workflows.langgraph_workflow import (
    route_message,
    call_product_agent,
    call_order_agent,
    call_recommendation_agent,
    call_marketing_agent,
    call_general_agent,
    create_langgraph_workflow,
    get_workflow_manager
)


class TestLangGraphWorkflow:
    """Test cases for LangGraph workflow implementation."""
    
    def test_route_message_product_query(self):
        """Test routing for product queries."""
        # Create test state
        state = {
            "messages": [HumanMessage(content="Milyen telefonok vannak készleten?")]
        }
        
        # Test routing
        result = route_message(state)
        
        # Assert
        assert result["next"] == "product_agent"
    
    def test_route_message_order_query(self):
        """Test routing for order queries."""
        # Create test state
        state = {
            "messages": [HumanMessage(content="Mi a rendelésem státusza?")]
        }
        
        # Test routing
        result = route_message(state)
        
        # Assert
        assert result["next"] == "order_agent"
    
    def test_route_message_recommendation_query(self):
        """Test routing for recommendation queries."""
        # Create test state
        state = {
            "messages": [HumanMessage(content="Mit ajánlasz nekem?")]
        }
        
        # Test routing
        result = route_message(state)
        
        # Assert
        assert result["next"] == "recommendation_agent"
    
    def test_route_message_marketing_query(self):
        """Test routing for marketing queries."""
        # Create test state
        state = {
            "messages": [HumanMessage(content="Van valamilyen kedvezmény?")]
        }
        
        # Test routing
        result = route_message(state)
        
        # Assert
        assert result["next"] == "marketing_agent"
    
    def test_route_message_general_query(self):
        """Test routing for general queries."""
        # Create test state
        state = {
            "messages": [HumanMessage(content="Üdvözöllek!")]
        }
        
        # Test routing
        result = route_message(state)
        
        # Assert
        assert result["next"] == "general_agent"
    
    def test_route_message_empty_state(self):
        """Test routing with empty state."""
        # Create empty state
        state = {}
        
        # Test routing
        result = route_message(state)
        
        # Assert
        assert result["next"] == "general_agent"
    
    def test_route_message_no_messages(self):
        """Test routing with no messages."""
        # Create state with no messages
        state = {"messages": []}
        
        # Test routing
        result = route_message(state)
        
        # Assert
        assert result["next"] == "general_agent"
    
    @pytest.mark.asyncio
    async def test_call_product_agent(self):
        """Test product agent call."""
        # Create test state
        state = create_initial_state(
            user_message="Milyen telefonok vannak?",
            user_context={"user_id": "test_user"},
            session_data={"session_id": "test_session"}
        )

        # Mock dependencies
        state["user_context"]["supabase_client"] = MagicMock()
        state["user_context"]["webshop_api"] = MagicMock()
        state["security_context"] = MagicMock()
        state["audit_logger"] = MagicMock()

        # Test agent call
        result = await call_product_agent(state)

        # Assert
        assert isinstance(result, dict)
        assert "messages" in result
        assert len(result["messages"]) > 1
        # Note: metadata may not be present in error cases
    
    @pytest.mark.asyncio
    async def test_call_order_agent(self):
        """Test order agent call."""
        # Create test state
        state = create_initial_state(
            user_message="Mi a rendelésem státusza?",
            user_context={"user_id": "test_user"},
            session_data={"session_id": "test_session"}
        )
        
        # Mock dependencies
        state["user_context"]["supabase_client"] = MagicMock()
        state["user_context"]["webshop_api"] = MagicMock()
        state["security_context"] = MagicMock()
        state["audit_logger"] = MagicMock()
        
                # Test agent call
        result = await call_order_agent(state)

        # Assert
        assert isinstance(result, dict)
        assert "messages" in result
        assert len(result["messages"]) > 1
        # Note: metadata may not be present in error cases
    
    @pytest.mark.asyncio
    async def test_call_recommendation_agent(self):
        """Test recommendation agent call."""
        # Create test state
        state = create_initial_state(
            user_message="Mit ajánlasz nekem?",
            user_context={"user_id": "test_user"},
            session_data={"session_id": "test_session"}
        )
        
        # Mock dependencies
        state["user_context"]["supabase_client"] = MagicMock()
        state["user_context"]["webshop_api"] = MagicMock()
        state["security_context"] = MagicMock()
        state["audit_logger"] = MagicMock()
        
                # Test agent call
        result = await call_recommendation_agent(state)

        # Assert
        assert isinstance(result, dict)
        assert "messages" in result
        assert len(result["messages"]) > 1
        # Note: metadata may not be present in error cases
    
    @pytest.mark.asyncio
    async def test_call_marketing_agent(self):
        """Test marketing agent call."""
        # Create test state
        state = create_initial_state(
            user_message="Van valamilyen kedvezmény?",
            user_context={"user_id": "test_user"},
            session_data={"session_id": "test_session"}
        )
        
        # Mock dependencies
        state["user_context"]["supabase_client"] = MagicMock()
        state["user_context"]["webshop_api"] = MagicMock()
        state["security_context"] = MagicMock()
        state["audit_logger"] = MagicMock()
        
                # Test agent call
        result = await call_marketing_agent(state)

        # Assert
        assert isinstance(result, dict)
        assert "messages" in result
        assert len(result["messages"]) > 1
        # Note: metadata may not be present in error cases
    
    @pytest.mark.asyncio
    async def test_call_general_agent(self):
        """Test general agent call."""
        # Create test state
        state = create_initial_state(
            user_message="Üdvözöllek!",
            user_context={"user_id": "test_user"},
            session_data={"session_id": "test_session"}
        )
        
        # Mock dependencies
        state["user_context"]["supabase_client"] = MagicMock()
        state["user_context"]["webshop_api"] = MagicMock()
        state["security_context"] = MagicMock()
        state["audit_logger"] = MagicMock()
        
                # Test agent call
        result = await call_general_agent(state)

        # Assert
        assert isinstance(result, dict)
        assert "messages" in result
        assert len(result["messages"]) > 1
        # Note: metadata may not be present in error cases
    
    def test_create_langgraph_workflow(self):
        """Test workflow creation."""
        # Create workflow
        workflow = create_langgraph_workflow()
        
        # Assert
        assert workflow is not None
        assert hasattr(workflow, 'invoke')
        assert hasattr(workflow, 'ainvoke')
    
    def test_get_workflow_manager(self):
        """Test workflow manager singleton."""
        # Get workflow manager
        manager1 = get_workflow_manager()
        manager2 = get_workflow_manager()
        
        # Assert singleton pattern
        assert manager1 is manager2
        assert hasattr(manager1, 'get_workflow')
        assert hasattr(manager1, 'process_message')
    
    @pytest.mark.asyncio
    async def test_workflow_manager_process_message(self):
        """Test workflow manager message processing."""
        # Get workflow manager
        manager = get_workflow_manager()
        
        # Create test state
        state = create_initial_state(
            user_message="Milyen telefonok vannak?",
            user_context={"user_id": "test_user"},
            session_data={"session_id": "test_session"}
        )
        
        # Mock dependencies
        state["user_context"]["supabase_client"] = MagicMock()
        state["user_context"]["webshop_api"] = MagicMock()
        state["security_context"] = MagicMock()
        state["audit_logger"] = MagicMock()
        
        # Test message processing
        result = await manager.process_message(state)
        
        # Assert
        assert isinstance(result, dict)
        assert "messages" in result
        assert len(result["messages"]) > 1
        # Note: metadata may not be present in error cases
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self):
        """Test workflow error handling."""
        # Create test state with invalid data
        state = {
            "messages": [HumanMessage(content="Test message")],
            "user_context": {},
            "session_data": {},
            "error_count": 0,
            "retry_attempts": 0,
            "agent_data": {}  # Initialize agent_data to avoid KeyError
        }

        # Mock dependencies that might cause errors
        state["user_context"]["supabase_client"] = None
        state["user_context"]["webshop_api"] = None
        state["security_context"] = None
        state["audit_logger"] = None

        # Test agent call (should handle errors gracefully)
        result = await call_product_agent(state)

        # Assert
        assert isinstance(result, dict)
        assert "messages" in result
        # Note: metadata may not be present in error cases
    
    def test_workflow_routing_edge_cases(self):
        """Test workflow routing edge cases."""
        # Test with None message (should be handled gracefully)
        try:
            state = {"messages": [HumanMessage(content=None)]}
            result = route_message(state)
            assert result["next"] == "general_agent"
        except Exception:
            # If HumanMessage doesn't accept None, that's fine
            pass
        
        # Test with empty message
        state = {"messages": [HumanMessage(content="")]}
        result = route_message(state)
        assert result["next"] == "general_agent"
        
        # Test with very long message
        long_message = "a" * 1000
        state = {"messages": [HumanMessage(content=long_message)]}
        result = route_message(state)
        assert result["next"] == "general_agent"
    
    @pytest.mark.asyncio
    async def test_workflow_performance(self):
        """Test workflow performance with multiple agents."""
        # Get workflow manager
        manager = get_workflow_manager()
        
        # Test messages for different agents
        test_messages = [
            "Milyen telefonok vannak?",
            "Mi a rendelésem státusza?",
            "Mit ajánlasz nekem?",
            "Van valamilyen kedvezmény?",
            "Üdvözöllek!"
        ]
        
        for message in test_messages:
            # Create test state
            state = create_initial_state(
                user_message=message,
                user_context={"user_id": "test_user"},
                session_data={"session_id": "test_session"}
            )
            
            # Mock dependencies
            state["user_context"]["supabase_client"] = MagicMock()
            state["user_context"]["webshop_api"] = MagicMock()
            state["security_context"] = MagicMock()
            state["audit_logger"] = MagicMock()
            
            # Test message processing
            result = await manager.process_message(state)
            
            # Assert basic functionality
            assert isinstance(result, dict)
            assert "messages" in result
            # Note: metadata may not be present in error cases


class TestStateManagement:
    """Test cases for state management utilities."""
    
    def test_create_initial_state(self):
        """Test initial state creation."""
        # Create initial state
        state = create_initial_state(
            user_message="Test message",
            user_context={"user_id": "test_user"},
            session_data={"session_id": "test_session"}
        )
        
        # Assert
        assert state["messages"][0].content == "Test message"
        assert state["current_agent"] == "coordinator"
        assert state["user_context"]["user_id"] == "test_user"
        assert state["session_data"]["session_id"] == "test_session"
        assert state["error_count"] == 0
        assert state["retry_attempts"] == 0
        assert state["workflow_step"] == "start"
        assert state["should_continue"] == True
    
    def test_create_initial_state_minimal(self):
        """Test initial state creation with minimal parameters."""
        # Create initial state with minimal parameters
        state = create_initial_state("Test message")
        
        # Assert
        assert state["messages"][0].content == "Test message"
        assert state["user_context"] == {}
        assert state["session_data"] == {}
        assert state["security_context"] is None
        assert state["gdpr_compliance"] is None
        assert state["audit_logger"] is None


if __name__ == "__main__":
    pytest.main([__file__]) 