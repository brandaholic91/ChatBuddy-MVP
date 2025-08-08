# tests/agents/test_general_agent_mock.py

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic_ai.models.test import TestModel
from src.agents.general.agent import create_general_agent, GeneralResponse
from src.models.agent import AgentResponse, AgentType

@pytest_asyncio.fixture
async def general_agent_instance():
    """Create general agent instance for testing with proper mocking."""
    # Set test environment variable to avoid OpenAI API calls
    import os
    os.environ["OPENAI_API_KEY"] = "test-key"
    
    return create_general_agent()


@pytest.mark.unit
@pytest.mark.agents
@pytest.mark.fast
class TestGeneralAgentMock:
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, general_agent_instance):
        """Agent inicializálás tesztje."""
        assert general_agent_instance.model is not None
        assert general_agent_instance.agent_type == AgentType.GENERAL
    
    @pytest.mark.asyncio
    async def test_successful_response(self, general_agent_instance, mock_audit_logger, sample_user):
        """Sikeres válasz tesztje using Pydantic AI TestModel."""
        # Create a TestModel that returns structured response
        test_model = TestModel(
            custom_output_text='{"response_text": "Mock AI response from general agent", "confidence": 1.0, "metadata": {}}'
        )
        
        # Use the Pydantic AI override pattern
        with general_agent_instance.override(model=test_model):
            result = await general_agent_instance.run("Hello", user=sample_user, session_id="test_session", audit_logger=mock_audit_logger)
            
            assert isinstance(result, AgentResponse)
            assert result.agent_type == AgentType.GENERAL
            assert result.confidence >= 0.0
            assert result.confidence <= 1.0
            # Response will be structured by our wrapper
            # Note: In successful case, audit logging is typically done outside the wrapper
    
    @pytest.mark.asyncio
    async def test_error_handling(self, general_agent_instance, mock_audit_logger, sample_user):
        """Hibakezelés tesztje."""
        # Mock the internal Pydantic AI agent to raise an error
        with patch.object(general_agent_instance._pydantic_agent, 'run', side_effect=Exception("Mock error")):
            result = await general_agent_instance.run("test", user=sample_user, session_id="test_session", audit_logger=mock_audit_logger)
            
            assert isinstance(result, AgentResponse)
            assert "hiba történt" in result.response_text.lower()
            assert result.confidence == 0.0
            assert result.agent_type == AgentType.GENERAL
            assert "error_type" in result.metadata
            # Verify that audit logging was called for error case
            mock_audit_logger.log_agent_event.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_model_override(self, general_agent_instance):
        """Test that the agent can be overridden with TestModel for deterministic responses."""
        test_model = TestModel(custom_output_text='{"response_text": "Deterministic test response", "confidence": 0.95, "metadata": {"test": true}}')
        
        # Verify override functionality works
        override_context = general_agent_instance.override(model=test_model)
        assert override_context is not None
