"""
Product Info Agent tesztek.

Ez a modul teszteli a Product Info Agent funkcionalitását:
- LangGraph workflow tesztelés
- Pydantic AI dependency injection
- Tool functions tesztelés
- Structured output validáció
"""

import os
import pytest
import asyncio
from decimal import Decimal
from unittest.mock import Mock, AsyncMock
from dotenv import load_dotenv

# Betöltjük az environment változókat
load_dotenv()

from src.agents.product_info.agent import (
    ProductInfoAgent,
    get_product_info_agent,
    ProductQueryType,
    create_product_info_agent
)
from src.agents.product_info.tools import (
    ProductInfoDependencies,
    search_products,
    get_product_details,
    get_product_reviews,
    check_product_availability,
    get_product_pricing
)
from src.models.user import User
from src.models.product import Product, ProductInfo, ProductReview


class TestProductInfoAgent:
    """Product Info Agent tesztek."""
    
    @pytest.fixture
    def mock_user(self):
        """Mock felhasználó."""
        return User(
            id="test_user_1",
            name="Teszt Felhasználó",
            email="test@example.com",
            phone="+36123456789"
        )
    
    @pytest.fixture
    def product_info_agent(self):
        """Product Info Agent instance."""
        return ProductInfoAgent(verbose=False)
    
    @pytest.fixture
    def product_info_deps(self, mock_user):
        """Product Info Dependencies."""
        return ProductInfoDependencies(
            user=mock_user,
            session_id="test_session_1"
        )
    
    def test_create_product_info_agent(self):
        """Teszt: Product Info Agent létrehozása."""
        agent = create_product_info_agent()
        assert agent is not None
        assert hasattr(agent, 'run')
        assert hasattr(agent, 'run_sync')
    
    def test_get_product_info_agent_singleton(self):
        """Teszt: Product Info Agent singleton pattern."""
        agent1 = get_product_info_agent()
        agent2 = get_product_info_agent()
        assert agent1 is agent2
    
    @pytest.mark.asyncio
    async def test_process_message_search_query(self, product_info_agent, mock_user):
        """Teszt: Termék keresési lekérdezés feldolgozása."""
        message = "Keresek iPhone telefonokat"
        
        response = await product_info_agent.process_message(
            message=message,
            user=mock_user,
            session_id="test_session_1"
        )
        
        assert response is not None
        assert response.agent_type.value == "product_info"
        assert len(response.response_text) > 0
        assert response.confidence > 0
        assert "query_type" in response.metadata
        assert response.metadata["langgraph_used"] is True
    
    @pytest.mark.asyncio
    async def test_process_message_details_query(self, product_info_agent, mock_user):
        """Teszt: Termék részletek lekérdezés feldolgozása."""
        message = "Szeretnék információt az iPhone 15 Pro-ról"
        
        response = await product_info_agent.process_message(
            message=message,
            user=mock_user,
            session_id="test_session_1"
        )
        
        assert response is not None
        assert response.agent_type.value == "product_info"
        assert len(response.response_text) > 0
        assert response.confidence > 0
    
    @pytest.mark.asyncio
    async def test_process_message_reviews_query(self, product_info_agent, mock_user):
        """Teszt: Termék értékelések lekérdezés feldolgozása."""
        message = "Mit mondanak az iPhone 15 Pro-ról?"
        
        response = await product_info_agent.process_message(
            message=message,
            user=mock_user,
            session_id="test_session_1"
        )
        
        assert response is not None
        assert response.agent_type.value == "product_info"
        assert len(response.response_text) > 0
        assert response.confidence > 0
    
    @pytest.mark.asyncio
    async def test_process_message_availability_query(self, product_info_agent, mock_user):
        """Teszt: Készlet ellenőrzés lekérdezés feldolgozása."""
        message = "Van készleten iPhone 15 Pro?"
        
        response = await product_info_agent.process_message(
            message=message,
            user=mock_user,
            session_id="test_session_1"
        )
        
        assert response is not None
        assert response.agent_type.value == "product_info"
        assert len(response.response_text) > 0
        assert response.confidence > 0
    
    @pytest.mark.asyncio
    async def test_process_message_pricing_query(self, product_info_agent, mock_user):
        """Teszt: Árazási információk lekérdezés feldolgozása."""
        message = "Mennyibe kerül az iPhone 15 Pro?"
        
        response = await product_info_agent.process_message(
            message=message,
            user=mock_user,
            session_id="test_session_1"
        )
        
        assert response is not None
        assert response.agent_type.value == "product_info"
        assert len(response.response_text) > 0
        assert response.confidence > 0
    
    def test_agent_state_management(self, product_info_agent):
        """Teszt: Agent állapot kezelés."""
        initial_state = product_info_agent.get_state()
        assert "messages" in initial_state
        
        # State reset teszt
        product_info_agent.reset_state()
        reset_state = product_info_agent.get_state()
        assert len(reset_state["messages"]) == 0


class TestProductInfoTools:
    """Product Info Tools tesztek."""
    
    @pytest.fixture
    def mock_deps(self):
        """Mock dependencies."""
        return ProductInfoDependencies(
            user=User(
                id="test_user_1",
                name="Teszt Felhasználó",
                email="test@example.com"
            ),
            session_id="test_session_1"
        )
    
    @pytest.mark.asyncio
    async def test_search_products(self, mock_deps):
        """Teszt: Termék keresés."""
        result = await search_products(
            ctx=Mock(deps=mock_deps),
            query="iPhone",
            limit=5
        )
        
        assert result is not None
        assert hasattr(result, 'products')
        assert hasattr(result, 'total_count')
        assert hasattr(result, 'search_query')
        assert result.search_query == "iPhone"
        assert len(result.products) > 0
    
    @pytest.mark.asyncio
    async def test_search_products_with_filters(self, mock_deps):
        """Teszt: Termék keresés szűrőkkel."""
        result = await search_products(
            ctx=Mock(deps=mock_deps),
            query="telefon",
            category_id="phones",
            min_price=Decimal("300000"),
            max_price=Decimal("500000"),
            in_stock=True,
            limit=3
        )
        
        assert result is not None
        assert result.filters_applied["category_id"] == "phones"
        assert result.filters_applied["min_price"] == Decimal("300000")
        assert result.filters_applied["max_price"] == Decimal("500000")
        assert result.filters_applied["in_stock"] is True
    
    @pytest.mark.asyncio
    async def test_get_product_details(self, mock_deps):
        """Teszt: Termék részletes információk."""
        result = await get_product_details(
            ctx=Mock(deps=mock_deps),
            product_id="1"
        )
        
        assert result is not None
        assert hasattr(result, 'product')
        assert hasattr(result, 'product_info')
        assert hasattr(result, 'reviews')
        assert hasattr(result, 'related_products')
        assert hasattr(result, 'availability')
        assert hasattr(result, 'pricing')
        
        assert result.product.id == "1"
        assert result.product.name == "iPhone 15 Pro"
        assert result.product_info is not None
        assert len(result.reviews) > 0
        assert len(result.related_products) > 0
    
    @pytest.mark.asyncio
    async def test_get_product_reviews(self, mock_deps):
        """Teszt: Termék értékelések."""
        reviews = await get_product_reviews(
            ctx=Mock(deps=mock_deps),
            product_id="1",
            limit=3
        )
        
        assert reviews is not None
        assert len(reviews) > 0
        assert len(reviews) <= 3
        
        for review in reviews:
            assert review.product_id == "1"
            assert 1 <= review.rating <= 5
            assert review.user_id is not None
    
    @pytest.mark.asyncio
    async def test_get_product_reviews_with_rating_filter(self, mock_deps):
        """Teszt: Termék értékelések rating szűrővel."""
        reviews = await get_product_reviews(
            ctx=Mock(deps=mock_deps),
            product_id="1",
            limit=5,
            rating_filter=5
        )
        
        assert reviews is not None
        for review in reviews:
            assert review.rating == 5
    
    @pytest.mark.asyncio
    async def test_check_product_availability(self, mock_deps):
        """Teszt: Termék készlet ellenőrzés."""
        availability = await check_product_availability(
            ctx=Mock(deps=mock_deps),
            product_id="1"
        )
        
        assert availability is not None
        assert "product_id" in availability
        assert "in_stock" in availability
        assert "stock_quantity" in availability
        assert "shipping_options" in availability
        assert availability["product_id"] == "1"
    
    @pytest.mark.asyncio
    async def test_get_product_pricing(self, mock_deps):
        """Teszt: Termék árazási információk."""
        pricing = await get_product_pricing(
            ctx=Mock(deps=mock_deps),
            product_id="1"
        )
        
        assert pricing is not None
        assert "product_id" in pricing
        assert "current_price" in pricing
        assert "currency" in pricing
        assert "installment_options" in pricing
        assert pricing["product_id"] == "1"
        assert pricing["currency"] == "HUF"


class TestProductQueryTypes:
    """Product Query Types tesztek."""
    
    def test_product_query_types(self):
        """Teszt: Product Query Types enum."""
        assert ProductQueryType.SEARCH.value == "search"
        assert ProductQueryType.DETAILS.value == "details"
        assert ProductQueryType.REVIEWS.value == "reviews"
        assert ProductQueryType.RELATED.value == "related"
        assert ProductQueryType.AVAILABILITY.value == "availability"
        assert ProductQueryType.PRICING.value == "pricing"
        assert ProductQueryType.COMPARISON.value == "comparison"
        assert ProductQueryType.RECOMMENDATION.value == "recommendation"


class TestProductInfoDependencies:
    """Product Info Dependencies tesztek."""
    
    def test_product_info_dependencies(self):
        """Teszt: Product Info Dependencies."""
        deps = ProductInfoDependencies(
            user=User(
                id="test_user_1",
                name="Teszt Felhasználó",
                email="test@example.com"
            ),
            session_id="test_session_1"
        )
        
        assert deps.user is not None
        assert deps.session_id == "test_session_1"
        assert deps.database_connection is None
        assert deps.cache_client is None


if __name__ == "__main__":
    pytest.main([__file__]) 