"""
Unit tests for all agent components.
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.agents.general.agent import GeneralAgent
from src.agents.marketing.agent import MarketingAgent
from src.agents.order_status.agent import OrderStatusAgent
from src.agents.product_info.agent import ProductInfoAgent
from src.agents.recommendations.agent import RecommendationsAgent


class TestGeneralAgent:
    """Unit tests for GeneralAgent."""
    
    @pytest.mark.unit
    @pytest.mark.agent
    def test_general_agent_initialization(self, test_model):
        """Test GeneralAgent initialization."""
        agent = GeneralAgent(model=test_model)
        assert agent is not None
        assert agent.model == test_model
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_general_agent_process_message(self, test_model, mock_chat_message):
        """Test GeneralAgent message processing."""
        agent = GeneralAgent(model=test_model)
        response = await agent.process_message(mock_chat_message)
        assert response is not None
        assert "content" in response
    
    @pytest.mark.unit
    @pytest.mark.agent
    def test_general_agent_get_capabilities(self, test_model):
        """Test GeneralAgent capabilities."""
        agent = GeneralAgent(model=test_model)
        capabilities = agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) > 0


class TestMarketingAgent:
    """Unit tests for MarketingAgent."""
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.marketing
    def test_marketing_agent_initialization(self, test_model):
        """Test MarketingAgent initialization."""
        agent = MarketingAgent(model=test_model)
        assert agent is not None
        assert agent.model == test_model
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.marketing
    @pytest.mark.asyncio
    async def test_marketing_agent_process_message(self, test_model, mock_chat_message):
        """Test MarketingAgent message processing."""
        agent = MarketingAgent(model=test_model)
        response = await agent.process_message(mock_chat_message)
        assert response is not None
        assert "content" in response
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.marketing
    def test_marketing_agent_get_capabilities(self, test_model):
        """Test MarketingAgent capabilities."""
        agent = MarketingAgent(model=test_model)
        capabilities = agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert "marketing" in [cap.lower() for cap in capabilities]


class TestOrderStatusAgent:
    """Unit tests for OrderStatusAgent."""
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.order_status
    def test_order_status_agent_initialization(self, test_model):
        """Test OrderStatusAgent initialization."""
        agent = OrderStatusAgent(model=test_model)
        assert agent is not None
        assert agent.model == test_model
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.order_status
    @pytest.mark.asyncio
    async def test_order_status_agent_process_message(self, test_model, mock_chat_message):
        """Test OrderStatusAgent message processing."""
        agent = OrderStatusAgent(model=test_model)
        response = await agent.process_message(mock_chat_message)
        assert response is not None
        assert "content" in response
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.order_status
    def test_order_status_agent_get_capabilities(self, test_model):
        """Test OrderStatusAgent capabilities."""
        agent = OrderStatusAgent(model=test_model)
        capabilities = agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert "order" in [cap.lower() for cap in capabilities]


class TestProductInfoAgent:
    """Unit tests for ProductInfoAgent."""
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.product_info
    def test_product_info_agent_initialization(self, test_model):
        """Test ProductInfoAgent initialization."""
        agent = ProductInfoAgent(model=test_model)
        assert agent is not None
        assert agent.model == test_model
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.product_info
    @pytest.mark.asyncio
    async def test_product_info_agent_process_message(self, test_model, mock_chat_message):
        """Test ProductInfoAgent message processing."""
        agent = ProductInfoAgent(model=test_model)
        response = await agent.process_message(mock_chat_message)
        assert response is not None
        assert "content" in response
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.product_info
    def test_product_info_agent_get_capabilities(self, test_model):
        """Test ProductInfoAgent capabilities."""
        agent = ProductInfoAgent(model=test_model)
        capabilities = agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert "product" in [cap.lower() for cap in capabilities]


class TestRecommendationsAgent:
    """Unit tests for RecommendationsAgent."""
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.recommendations
    def test_recommendations_agent_initialization(self, test_model):
        """Test RecommendationsAgent initialization."""
        agent = RecommendationsAgent(model=test_model)
        assert agent is not None
        assert agent.model == test_model
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.recommendations
    @pytest.mark.asyncio
    async def test_recommendations_agent_process_message(self, test_model, mock_chat_message):
        """Test RecommendationsAgent message processing."""
        agent = RecommendationsAgent(model=test_model)
        response = await agent.process_message(mock_chat_message)
        assert response is not None
        assert "content" in response
    
    @pytest.mark.unit
    @pytest.mark.agent
    @pytest.mark.recommendations
    def test_recommendations_agent_get_capabilities(self, test_model):
        """Test RecommendationsAgent capabilities."""
        agent = RecommendationsAgent(model=test_model)
        capabilities = agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert "recommendation" in [cap.lower() for cap in capabilities] 