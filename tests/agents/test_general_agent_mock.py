# tests/agents/test_general_agent_mock.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.agents.general.agent import create_general_agent
from src.models.agent import AgentResponse, AgentType

@pytest.fixture
def general_agent_instance():
    return create_general_agent()


@pytest.mark.unit
@pytest.mark.agents
@pytest.mark.fast
class TestGeneralAgentMock:
    
    async def test_agent_initialization(self, general_agent_instance):
        """Agent inicializálás tesztje."""
        assert general_agent_instance.model is not None
        assert general_agent_instance.agent_type == AgentType.GENERAL
    
    async def test_successful_response(self, general_agent_instance, mock_audit_logger, sample_user):
        """Sikeres válasz tesztje."""
        # Mock the internal LLM call
        with patch.object(general_agent_instance, '_agent') as mock_llm_agent:
            mock_llm_agent.run.return_value = "Mock AI response from general agent"
            
            result = await general_agent_instance.run("Hello", user=sample_user, session_id="test_session", audit_logger=mock_audit_logger)
            
            assert isinstance(result, AgentResponse)
            assert result.response_text == "Mock AI response from general agent"
            assert result.confidence == 1.0
            assert result.agent_type == AgentType.GENERAL
            assert result.metadata == {}
            mock_audit_logger.log_agent_interaction.assert_called_once()
    
    async def test_error_handling(self, general_agent_instance, mock_audit_logger, sample_user):
        """Hibakezelés tesztje."""
        # Force error in internal LLM call
        with patch.object(general_agent_instance, '_agent') as mock_llm_agent:
            mock_llm_agent.run.side_effect = Exception("Mock error")
            
            result = await general_agent_instance.run("test", user=sample_user, session_id="test_session", audit_logger=mock_audit_logger)
            
            assert isinstance(result, AgentResponse)
            assert "hiba történt" in result.response_text.lower()
            assert result.confidence == 0.0
            assert result.agent_type == AgentType.GENERAL
            assert "error_type" in result.metadata
            mock_audit_logger.log_agent_interaction.assert_called_once()
            mock_audit_logger.log_error.assert_called_once()
