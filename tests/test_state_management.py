
import pytest
from langchain_core.messages import HumanMessage, AIMessage

from src.utils.state_management import (
    create_initial_state,
    update_state_with_response,
    update_state_with_error,
    finalize_state,
    get_state_summary,
    validate_state,
    reset_state_for_retry,
    add_agent_data,
    get_agent_data,
    update_performance_metrics
)

@pytest.fixture
def initial_state():
    """Fixture for an initial state"""
    return create_initial_state("Hello")

def test_create_initial_state():
    """Test initial state creation"""
    state = create_initial_state("Hi")
    assert isinstance(state["messages"][0], HumanMessage)
    assert state["current_agent"] == "coordinator"

def test_update_state_with_response(initial_state):
    """Test updating state with a response"""
    state = update_state_with_response(initial_state, "Hi there", "general")
    assert isinstance(state["messages"][-1], AIMessage)
    assert "Hi there" in state["messages"][-1].content
    assert state["agent_data"]["agent_responses"][0]["agent"] == "general"

def test_update_state_with_error(initial_state):
    """Test updating state with an error"""
    state = update_state_with_error(initial_state, "An error occurred", "general")
    assert state["error_count"] == 1
    assert "An error occurred" in state["messages"][-1].content

def test_finalize_state(initial_state):
    """Test finalizing the state"""
    state = finalize_state(initial_state)
    assert state["workflow_step"] == "completed"
    assert state["should_continue"] is False
    assert state["processing_end_time"] is not None

def test_get_state_summary(initial_state):
    """Test getting a state summary"""
    summary = get_state_summary(initial_state)
    assert summary["total_messages"] == 1
    assert summary["current_agent"] == "coordinator"

def test_validate_state(initial_state):
    """Test state validation"""
    assert validate_state(initial_state) is True
    invalid_state = initial_state.copy()
    del invalid_state["messages"]
    assert validate_state(invalid_state) is False

def test_reset_state_for_retry(initial_state):
    """Test resetting state for retry"""
    state = reset_state_for_retry(initial_state)
    assert state["retry_attempts"] == 1
    assert state["workflow_step"] == "retry"

def test_add_and_get_agent_data(initial_state):
    """Test adding and getting agent-specific data"""
    state = add_agent_data(initial_state, "test_agent", {"key": "value"})
    agent_data = get_agent_data(state, "test_agent")
    assert agent_data["key"] == "value"

def test_get_agent_data_non_existent(initial_state):
    """Test getting data for a non-existent agent"""
    agent_data = get_agent_data(initial_state, "non_existent_agent")
    assert agent_data == {}

def test_update_performance_metrics(initial_state):
    """Test updating performance metrics"""
    state = update_performance_metrics(initial_state, tokens_used=100, cost=0.01)
    assert state["tokens_used"] == 100
    assert state["cost"] == 0.01

def test_validate_state_invalid_types(initial_state):
    """Test state validation with invalid data types"""
    invalid_state = initial_state.copy()
    invalid_state["messages"] = "not a list"
    assert validate_state(invalid_state) is False

def test_finalize_state_with_final_response(initial_state):
    """Test finalizing the state with a final response"""
    state = finalize_state(initial_state, final_response="Goodbye!")
    assert state["messages"][-1].content == "Goodbye!"
