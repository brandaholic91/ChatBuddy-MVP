# tests/agents/test_marketing_agent_mock.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pydantic_ai.models.test import TestModel
from src.agents.marketing.agent import create_marketing_agent, MarketingDependencies, MarketingResponse, Promotion, Newsletter
from src.models.agent import AgentResponse, AgentType

@pytest.fixture
def marketing_agent_instance():
    return create_marketing_agent()

@pytest.mark.unit
@pytest.mark.agents
@pytest.mark.fast
class TestMarketingAgentMock:

    @pytest.fixture
    def mock_marketing_dependencies(self, sample_user, mock_audit_logger):
        return MarketingDependencies(
            user_context={"user_id": sample_user.id},
            supabase_client=AsyncMock(),
            webshop_api=AsyncMock(),
            security_context=MagicMock(),
            audit_logger=mock_audit_logger
        )
    
    async def test_agent_initialization(self, marketing_agent_instance):
        """Agent inicializálás tesztje."""
        assert marketing_agent_instance.model == 'openai:gpt-4o'
        assert marketing_agent_instance.agent_type == AgentType.MARKETING
    
    async def test_successful_response(self, marketing_agent_instance, sample_user, mock_audit_logger):
        """Aktív promóciók lekérdezésének sikeres tesztje."""
        mock_response_text = "Itt vannak az aktív promóciók."
        
        # Use TestModel to mock the Pydantic AI agent behavior
        with marketing_agent_instance.override(model=TestModel()):
            result = await marketing_agent_instance.run(
                "Mutass promóciókat", 
                user=sample_user, 
                session_id="test_session",
                audit_logger=mock_audit_logger
            )
            
            assert isinstance(result, AgentResponse)
            assert result.agent_type == AgentType.MARKETING
            assert result.confidence > 0.0  # TestModel should return some confidence
            assert isinstance(result.response_text, str)
            assert len(result.response_text) > 0

    async def test_get_available_newsletters_success(self, marketing_agent_instance, sample_user, mock_audit_logger):
        """Elérhető hírlevelek lekérdezésének sikeres tesztje."""
        
        # Use TestModel to mock the Pydantic AI agent behavior
        with marketing_agent_instance.override(model=TestModel()):
            result = await marketing_agent_instance.run(
                "Milyen hírlevelek vannak?", 
                user=sample_user, 
                session_id="test_session",
                audit_logger=mock_audit_logger
            )
            
            assert isinstance(result, AgentResponse)
            assert result.agent_type == AgentType.MARKETING
            assert result.confidence > 0.0  # TestModel should return some confidence
            assert isinstance(result.response_text, str)
            assert len(result.response_text) > 0

    async def test_error_handling(self, marketing_agent_instance, sample_user, mock_audit_logger):
        """Hibakezelés tesztje."""
        # Force an error by passing invalid data
        with patch.object(marketing_agent_instance._pydantic_agent, 'run', side_effect=Exception("Marketing agent error")):
            result = await marketing_agent_instance.run(
                "test", 
                user=sample_user, 
                session_id="test_session",
                audit_logger=mock_audit_logger
            )
            
            assert isinstance(result, AgentResponse)
            assert "hiba történt" in result.response_text.lower()
            assert result.confidence == 0.0
            assert result.agent_type == AgentType.MARKETING
            assert "error_type" in result.metadata
