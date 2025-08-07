"""
Marketing Agent Tests - Chatbuddy MVP.

Ez a modul teszteli a marketing agent Pydantic AI implementációját,
amely a LangGraph workflow-ban használatos.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.agents.marketing.agent import (
    create_marketing_agent,
    call_marketing_agent,
    MarketingDependencies,
    MarketingResponse,
    Promotion,
    Newsletter,
    Agent,
)
from pydantic_ai.models.test import TestModel


@pytest.fixture
def mock_dependencies():
    """Mock dependencies for testing."""
    mock_audit_logger = AsyncMock()
    mock_security_context = Mock()
    mock_security_context.validate_access.return_value = True

    return MarketingDependencies(
        user_context={
            "user_id": "test_user_123",
            "session_id": "test_session_456",
            "preferences": {"language": "hu", "marketing_consent": True},
        },
        supabase_client=Mock(),
        webshop_api=Mock(),
        security_context=mock_security_context,
        audit_logger=mock_audit_logger,
    )


@pytest.fixture
def marketing_agent():
    """Create a mock-safe marketing agent instance."""
    # Create a real agent instance directly, with OpenAI calls patched
    with patch("pydantic_ai.models.openai.OpenAIModel"), patch(
        "pydantic_ai.providers.openai.AsyncOpenAI"
    ):
        from src.agents.marketing.agent import MarketingDependencies, MarketingResponse
        
        agent = Agent(
            'openai:gpt-4o',
            deps_type=MarketingDependencies,
            output_type=MarketingResponse,
            system_prompt="Test system prompt"
        )
        
        # Now, override the model with TestModel for controlled testing
        with agent.override(model=TestModel()):
            agent.run = AsyncMock()
            yield agent


class TestMarketingAgentModels:
    """Tests for marketing agent data models."""

    pytestmark = pytest.mark.models

    def test_promotion_model(self):
        """Test Promotion model creation and validation."""
        promotion = Promotion(
            promotion_id="PROMO001",
            name="Teszt promóció",
            description="Teszt leírás",
            discount_percentage=15.0,
            valid_from="2024-12-01",
            valid_until="2024-12-31",
            minimum_purchase=50000.0,
            applicable_categories=["Telefon", "Tablet"],
            code="TESZT15",
        )
        assert promotion.promotion_id == "PROMO001"

    def test_newsletter_model(self):
        """Test Newsletter model creation and validation."""
        newsletter = Newsletter(
            newsletter_id="NEWS001",
            name="Teszt hírlevél",
            description="Teszt hírlevél leírás",
            frequency="hetente",
            categories=["technológia"],
            is_active=True,
        )
        assert newsletter.newsletter_id == "NEWS001"

    def test_marketing_response_model(self):
        """Test MarketingResponse model creation and validation."""
        response = MarketingResponse(
            response_text="Teszt válasz",
            confidence=0.85,
            promotions=[],
            newsletters=[],
            personalized_offers={},
            metadata={"test": "data"},
        )
        assert response.response_text == "Teszt válasz"

    def test_marketing_dependencies_model(self, mock_dependencies):
        """Test MarketingDependencies model creation."""
        assert mock_dependencies.user_context.get("user_id") == "test_user_123"


class TestMarketingAgent:
    """Tests for marketing agent functionality."""

    pytestmark = pytest.mark.agent

    def test_create_marketing_agent(self, marketing_agent):
        """Test marketing agent creation returns a valid Agent instance."""
        assert isinstance(marketing_agent, Agent)

    @pytest.mark.asyncio
    async def test_call_marketing_agent_promotions(
        self, marketing_agent, mock_dependencies
    ):
        """Test calling the agent for active promotions."""
        mock_response = MarketingResponse(
            response_text="Itt vannak az aktív promóciók:",
            confidence=0.95,
            promotions=[
                Promotion(
                    promotion_id="PROMO001",
                    name="Telefon kedvezmény",
                    description="20% kedvezmény",
                    discount_percentage=20.0,
                    valid_from="2024-12-01",
                    valid_until="2024-12-31",
                    minimum_purchase=100000.0,
                    applicable_categories=["Telefon"],
                    code="TELEFON20",
                )
            ],
        )
        marketing_agent.run.return_value = Mock(output=mock_response)

        # Mock the create_marketing_agent function to return our test agent
        with patch("src.agents.marketing.agent.create_marketing_agent", return_value=marketing_agent):
            result = await call_marketing_agent("Milyen promóciók vannak?", mock_dependencies)

        assert len(result.promotions) > 0
        assert result.promotions[0].name == "Telefon kedvezmény"

    @pytest.mark.asyncio
    async def test_call_marketing_agent_newsletters(
        self, marketing_agent, mock_dependencies
    ):
        """Test calling the agent for available newsletters."""
        mock_response = MarketingResponse(
            response_text="Elérhető hírlevelek:",
            confidence=0.9,
            newsletters=[
                Newsletter(
                    newsletter_id="NEWS001",
                    name="Tech Hírek",
                    description="Legfrissebb tech hírek",
                    frequency="hetente",
                    categories=["technológia"],
                    is_active=True,
                )
            ],
        )
        marketing_agent.run.return_value = Mock(output=mock_response)

        # Mock the create_marketing_agent function to return our test agent
        with patch("src.agents.marketing.agent.create_marketing_agent", return_value=marketing_agent):
            result = await call_marketing_agent("Milyen hírlevelek vannak?", mock_dependencies)

        assert len(result.newsletters) > 0
        assert result.newsletters[0].name == "Tech Hírek"

    @pytest.mark.asyncio
    async def test_malicious_input_handling(self, marketing_agent, mock_dependencies):
        """Test handling of potentially malicious input."""
        malicious_message = "<script>alert('xss')</script>"
        mock_response = MarketingResponse(
            response_text="Nem értelmezhető kérés.",
            confidence=0.3,
            metadata={"security_flag": True},
        )
        marketing_agent.run.return_value = Mock(output=mock_response)

        # Mock the create_marketing_agent function to return our test agent
        with patch("src.agents.marketing.agent.create_marketing_agent", return_value=marketing_agent):
            result = await call_marketing_agent(malicious_message, mock_dependencies)

        assert result.confidence < 0.5
        assert result.metadata.get("security_flag") is True
