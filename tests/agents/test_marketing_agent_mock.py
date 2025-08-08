# tests/agents/test_marketing_agent_mock.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
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
    
    async def test_successful_response(self, marketing_agent_instance, mock_marketing_dependencies):
        """Aktív promóciók lekérdezésének sikeres tesztje."""
        mock_promotions = [
            Promotion(
                promotion_id="PROMO001",
                name="Test Promo",
                description="Test Description",
                discount_percentage=10.0,
                valid_from="2024-01-01",
                valid_until="2024-12-31",
                minimum_purchase=100.0,
                applicable_categories=["Electronics"],
                code="TEST10"
            )
        ]
        
        with patch.object(marketing_agent_instance._agent, 'run') as mock_run:
            mock_run.return_value = MarketingResponse(
                response_text="Itt vannak az aktív promóciók.",
                confidence=1.0,
                promotions=mock_promotions
            )
            
            result = await marketing_agent_instance.run("Mutass promóciókat", deps=mock_marketing_dependencies)
            
            assert isinstance(result, AgentResponse)
            assert "promóciók" in result.response_text
            assert result.confidence == 1.0
            assert result.agent_type == AgentType.MARKETING
            assert result.metadata["promotions"] == [p.model_dump() for p in mock_promotions]
            mock_marketing_dependencies.audit_logger.log_agent_interaction.assert_called_once()

    async def test_get_available_newsletters_success(self, marketing_agent_instance, mock_marketing_dependencies):
        """Elérhető hírlevelek lekérdezésének sikeres tesztje."""
        mock_newsletters = [
            Newsletter(
                newsletter_id="NEWS001",
                name="Tech News",
                description="Latest tech news",
                frequency="weekly",
                categories=["tech"],
                is_active=True
            )
        ]

        with patch.object(marketing_agent_instance._agent, 'run') as mock_run:
            mock_run.return_value = MarketingResponse(
                response_text="Itt vannak az elérhető hírlevelek.",
                confidence=1.0,
                newsletters=mock_newsletters
            )
            
            result = await marketing_agent_instance.run("Milyen hírlevelek vannak?", deps=mock_marketing_dependencies)
            
            assert isinstance(result, AgentResponse)
            assert "hírlevelek" in result.response_text
            assert result.confidence == 1.0
            assert result.agent_type == AgentType.MARKETING
            assert result.metadata["newsletters"] == [n.model_dump() for n in mock_newsletters]
            mock_marketing_dependencies.audit_logger.log_agent_interaction.assert_called_once()

    async def test_error_handling(self, marketing_agent_instance, mock_marketing_dependencies):
        """Hibakezelés tesztje."""
        with patch.object(marketing_agent_instance._agent, 'run') as mock_run:
            mock_run.side_effect = Exception("Marketing agent error")
            
            result = await marketing_agent_instance.run("test", deps=mock_marketing_dependencies)
            
            assert isinstance(result, AgentResponse)
            assert "hiba történt" in result.response_text.lower()
            assert result.confidence == 0.0
            assert result.agent_type == AgentType.MARKETING
            assert "error_type" in result.metadata
            mock_marketing_dependencies.audit_logger.log_agent_interaction.assert_called_once()
            mock_marketing_dependencies.audit_logger.log_error.assert_called_once()
