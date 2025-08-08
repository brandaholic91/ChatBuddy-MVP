# tests/agents/test_recommendations_agent_mock.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.agents.recommendations.agent import create_recommendation_agent, RecommendationDependencies, RecommendationResponse, ProductRecommendation
from src.models.agent import AgentResponse, AgentType
from src.models.user import User
from src.config.audit_logging import AuditLogger

@pytest.fixture
def recommendation_agent_instance():
    return create_recommendation_agent()

@pytest.mark.unit
@pytest.mark.agents
@pytest.mark.fast
class TestRecommendationAgentMock:
    
    @pytest.fixture
    def mock_audit_logger(self):
        return AsyncMock(spec=AuditLogger)

    @pytest.fixture
    def sample_user(self):
        return User(id="test_user_123", email="test@example.com")

    @pytest.fixture
    def mock_recommendation_dependencies(self, sample_user, mock_audit_logger):
        return RecommendationDependencies(
            user_context={"user_id": sample_user.id},
            supabase_client=AsyncMock(),
            webshop_api=AsyncMock(),
            security_context=MagicMock(),
            audit_logger=mock_audit_logger
        )
    
    async def test_agent_initialization(self, recommendation_agent_instance):
        """Agent inicializálás tesztje."""
        assert recommendation_agent_instance.model == 'openai:gpt-4o'
        assert recommendation_agent_instance.agent_type == AgentType.RECOMMENDATIONS
    
    async def test_get_user_preferences_success(self, recommendation_agent_instance, mock_recommendation_dependencies):
        """Felhasználói preferenciák lekérdezésének sikeres tesztje."""
        mock_preferences = {
            "preferred_categories": ["Telefon"],
            "price_range": {"min": 100000, "max": 500000}
        }

        with patch.object(recommendation_agent_instance._agent, 'run') as mock_run:
            mock_run.return_value = RecommendationResponse(
                response_text="Itt vannak a preferenciáid.",
                confidence=1.0,
                user_preferences=mock_preferences
            )
            
            result = await recommendation_agent_instance.run("Mik a preferenciáim?", deps=mock_recommendation_dependencies)
            
            assert isinstance(result, AgentResponse)
            assert "preferenciáid" in result.response_text
            assert result.confidence == 1.0
            assert result.agent_type == AgentType.RECOMMENDATIONS
            assert result.metadata["user_preferences"] == mock_preferences
            mock_recommendation_dependencies.audit_logger.log_agent_interaction.assert_called_once()

    async def test_get_popular_products_success(self, recommendation_agent_instance, mock_recommendation_dependencies):
        """Népszerű termékek lekérdezésének sikeres tesztje."""
        mock_products = [
            ProductRecommendation(
                product_id="PROD001",
                name="Popular Phone",
                price=1000.0,
                description="A popular phone",
                category="Electronics",
                rating=4.5,
                review_count=100,
                image_url="popular.jpg",
                recommendation_reason="Very popular",
                confidence_score=0.9
            )
        ]

        with patch.object(recommendation_agent_instance._agent, 'run') as mock_run:
            mock_run.return_value = RecommendationResponse(
                response_text="Itt vannak a népszerű termékek.",
                confidence=1.0,
                popular_products=[p.model_dump() for p in mock_products]
            )
            
            result = await recommendation_agent_instance.run("Mutass népszerű termékeket", deps=mock_recommendation_dependencies)
            
            assert isinstance(result, AgentResponse)
            assert "népszerű termékek" in result.response_text
            assert result.confidence == 1.0
            assert result.agent_type == AgentType.RECOMMENDATIONS
            assert len(result.metadata["popular_products"]) == 1
            mock_recommendation_dependencies.audit_logger.log_agent_interaction.assert_called_once()

    async def test_error_handling(self, recommendation_agent_instance, mock_recommendation_dependencies):
        """Hibakezelés tesztje."""
        with patch.object(recommendation_agent_instance._agent, 'run') as mock_run:
            mock_run.side_effect = Exception("Recommendation agent error")
            
            result = await recommendation_agent_instance.run("test", deps=mock_recommendation_dependencies)
            
            assert isinstance(result, AgentResponse)
            assert "hiba történt" in result.response_text.lower()
            assert result.confidence == 0.0
            assert result.agent_type == AgentType.RECOMMENDATIONS
            assert "error_type" in result.metadata
            mock_recommendation_dependencies.audit_logger.log_agent_interaction.assert_called_once()
            mock_recommendation_dependencies.audit_logger.log_error.assert_called_once()
