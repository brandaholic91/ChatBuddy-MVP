
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.workflows.coordinator import (
    CoordinatorAgent,
    get_coordinator_agent,
    process_coordinator_message,
    process_coordinator_message_single
)
from src.models.agent import AgentResponse, AgentType
from src.models.user import User

@pytest.fixture
def mock_user():
    """Fixture for a mock User"""
    return User(id="user1", email="test@test.com")

@pytest.fixture
@patch('src.workflows.coordinator.get_correct_workflow_manager')
async def coordinator_agent(mock_get_manager):
    """Fixture for CoordinatorAgent"""
    mock_manager = MagicMock()
    
    # Mock the stream_message method to return an async generator with a mock state
    async def mock_stream_message(*args, **kwargs):
        mock_state = {
            "messages": [],
            "agent_responses": {"general": {"response_text": "mocked response", "confidence": 0.8}},
            "active_agent": "general",
            "metadata": {}
        }
        yield mock_state
    
    mock_manager.stream_message = mock_stream_message
    mock_get_manager.return_value = mock_manager
    agent = CoordinatorAgent(verbose=False)
    # Manually set initialized flags to avoid actual cache/preload calls
    agent._cache_initialized = True
    agent._agents_preloaded = True
    return agent

@pytest.mark.asyncio
async def test_coordinator_process_message(coordinator_agent, mock_user):
    """Test coordinator processing a message"""
    response = await coordinator_agent.process_message("Hello", user=mock_user)
    assert isinstance(response, AgentResponse)
    assert "mocked response" in response.response_text

@pytest.mark.asyncio
async def test_coordinator_threat_detection(coordinator_agent, mock_user):
    """Test threat detection in coordinator"""
    with patch.object(coordinator_agent._threat_detector, 'analyze_message', return_value={"threat_level": "high"}):
        response = await coordinator_agent.process_message("malicious input", user=mock_user)
        assert "biztonsági okokból" in response.response_text

@pytest.mark.asyncio
async def test_coordinator_cache_hit(coordinator_agent, mock_user):
    """Test response caching in coordinator"""
    mock_cache = MagicMock()
    mock_cache.get_cached_agent_response = AsyncMock(return_value={"response_text": "cached_response"})
    coordinator_agent._performance_cache = mock_cache
    
    response = await coordinator_agent.process_message("Hello again", user=mock_user)
    assert response.response_text == "cached_response"
    assert response.metadata["cached"] is True

def test_get_coordinator_agent():
    """Test singleton instance of coordinator agent"""
    agent1 = get_coordinator_agent()
    agent2 = get_coordinator_agent()
    assert agent1 is agent2

@pytest.mark.asyncio
async def test_process_coordinator_message(mock_user):
    """Test the global process_coordinator_message_single function"""
    with patch('src.workflows.coordinator.CoordinatorAgent.process_message', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = AgentResponse(agent_type=AgentType.COORDINATOR, response_text="mocked_response", confidence=0.9)
        response = await process_coordinator_message_single("Test message", user=mock_user)
        assert response.response_text == "mocked_response"
