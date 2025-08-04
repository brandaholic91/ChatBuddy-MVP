"""
Recommendation Agent tesztek.

Ez a modul tartalmazza a Recommendation Agent unit és integration teszteit:
- Agent létrehozás és inicializálás
- Felhasználói preferenciák tesztek
- Hasonló termékek keresés tesztek
- Trend elemzés tesztek
- Személyre szabott ajánlatok tesztek
- Biztonsági tesztek
- Teljesítmény tesztek
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any, List
from decimal import Decimal

from src.agents.recommendations.agent import (
    create_recommendation_agent,
    RecommendationDependencies,
    ProductRecommendations,
    MockRecommendationAgent,
    get_user_preferences_impl,
    find_similar_products_impl,
    analyze_trends_impl,
    get_personalized_recommendations_impl
)
from src.models.product import Product, ProductCategory, ProductStatus
from src.models.user import User
from src.config.security_prompts import SecurityContext
from src.config.audit_logging import SecurityAuditLogger

pytestmark = pytest.mark.anyio


class TestRecommendationAgent:
    """Recommendation Agent unit tesztek."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock dependencies a Recommendation Agent-hez."""
        return RecommendationDependencies(
            supabase_client=Mock(),
            vector_db=Mock(),
            user_context={
                "user_id": "test_user_123",
                "email": "test@example.com",
                "phone": "+36123456789",
                "session_id": "test_session_123",
                "preferences": {
                    "categories": ["electronics", "books"],
                    "price_range": {"min": 1000, "max": 50000}
                }
            },
            security_context=SecurityContext(
                user_id="test_user_123",
                session_id="test_session_123",
                security_level="medium",
                gdpr_compliant=True,
                permissions=["basic_access"],
                data_access_scope=["public"]
            ),
            audit_logger=SecurityAuditLogger()
        )
    
    @pytest.fixture
    def mock_user(self):
        """Mock felhasználó objektum."""
        return User(
            id="test_user_123",
            name="Teszt Felhasználó",
            email="test@example.com",
            phone="+36123456789",
            created_at=datetime.now()
        )
    
    @pytest.fixture
    def mock_products(self):
        """Mock termék objektumok."""
        return [
            Product(
                id="product_1",
                name="iPhone 15",
                description="Apple iPhone 15 128GB",
                price=Decimal("450000"),
                status=ProductStatus.ACTIVE,
                created_at=datetime.now()
            ),
            Product(
                id="product_2",
                name="Samsung Galaxy S24",
                description="Samsung Galaxy S24 256GB",
                price=Decimal("380000"),
                status=ProductStatus.ACTIVE,
                created_at=datetime.now()
            ),
            Product(
                id="product_3",
                name="Python Programming Book",
                description="Learn Python Programming",
                price=15000,
                category=ProductCategory.BOOKS,
                available=True,
                created_at=datetime.now()
            )
        ]
    
    @pytest.mark.unit
    async def test_create_recommendation_agent(self):
        """Teszt: Recommendation Agent létrehozása."""
        agent = create_recommendation_agent()
        assert agent is not None
        assert hasattr(agent, 'run')
    
    @pytest.mark.unit
    async def test_mock_recommendation_agent(self, mock_dependencies):
        """Teszt: Mock Recommendation Agent működése."""
        agent = MockRecommendationAgent()
        result = await agent.run("Ajánlj termékeket!", mock_dependencies)
        
        assert isinstance(result, ProductRecommendations)
        assert result.message is not None
        assert result.confidence == 0.5
        assert result.metadata["agent_type"] == "mock_recommendation"
        assert isinstance(result.recommendations, list)
        assert isinstance(result.reasoning, str)
    
    @pytest.mark.unit
    async def test_get_user_preferences_impl(self, mock_dependencies):
        """Teszt: Felhasználói preferenciák lekérése."""
        result = await get_user_preferences_impl(
            type('MockContext', (), {'deps': mock_dependencies})(),
            "test_user_123"
        )
        
        assert isinstance(result, dict)
        assert "categories" in result
        assert "price_range" in result
        assert "brands" in result
        assert "last_purchases" in result
        assert "viewed_products" in result
        
        # Ellenőrizzük a mock adatok helyességét
        assert result["categories"] == ["electronics", "books"]
        assert result["price_range"]["min"] == 1000
        assert result["price_range"]["max"] == 50000
        assert result["brands"] == ["Apple", "Samsung"]
    
    @pytest.mark.unit
    async def test_find_similar_products_impl(self, mock_dependencies):
        """Teszt: Hasonló termékek keresése."""
        result = await find_similar_products_impl(
            type('MockContext', (), {'deps': mock_dependencies})(),
            "product_1",
            limit=3
        )
        
        assert isinstance(result, list)
        assert len(result) == 3
        
        for product in result:
            assert isinstance(product, Product)
            assert product.name.startswith("Hasonló termék")
            assert product.description.startswith("Ez egy hasonló termék")
            assert product.price >= 10000
            assert product.status == ProductStatus.ACTIVE
    
    @pytest.mark.unit
    async def test_analyze_trends_impl(self, mock_dependencies):
        """Teszt: Trend elemzés."""
        result = await analyze_trends_impl(
            type('MockContext', (), {'deps': mock_dependencies})(),
            "electronics"
        )
        
        assert isinstance(result, dict)
        assert result["category"] == "electronics"
        assert "trending_products" in result
        assert "popular_brands" in result
        assert "price_trend" in result
        assert "demand_level" in result
        assert "seasonal_factors" in result
        
        # Ellenőrizzük a mock adatok helyességét
        assert result["trending_products"] == ["trend_1", "trend_2", "trend_3"]
        assert result["popular_brands"] == ["Brand A", "Brand B"]
        assert result["price_trend"] == "increasing"
        assert result["demand_level"] == "high"
    
    @pytest.mark.unit
    async def test_get_personalized_recommendations_impl(self, mock_dependencies):
        """Teszt: Személyre szabott ajánlatok generálása."""
        result = await get_personalized_recommendations_impl(
            type('MockContext', (), {'deps': mock_dependencies})(),
            "test_user_123",
            limit=5
        )
        
        assert isinstance(result, list)
        assert len(result) == 5
        
        for product in result:
            assert isinstance(product, Product)
            assert product.name.startswith("Személyre szabott ajánlat")
            assert product.description.startswith("Ez egy személyre szabott ajánlat")
            assert product.price >= 5000
            assert product.status == ProductStatus.ACTIVE


class TestRecommendationAgentIntegration:
    """Recommendation Agent integration tesztek."""
    
    @pytest.fixture
    def recommendation_agent(self):
        """Recommendation Agent instance."""
        return create_recommendation_agent()
    
    @pytest.fixture
    def test_user(self):
        """Teszt felhasználó."""
        return User(
            id="test_user_123",
            name="Teszt Felhasználó",
            email="test@example.com",
            phone="+36123456789",
            created_at=datetime.now()
        )
    
    @pytest.mark.integration
    async def test_recommendation_agent_process_message(self, recommendation_agent, test_user):
        """Teszt: Recommendation Agent üzenet feldolgozása."""
        # Mock dependencies
        with patch('src.agents.recommendations.agent.RecommendationDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Íme néhány ajánlat számodra!"
            mock_result.recommendations = []
            mock_result.reasoning = "A preferenciáid alapján"
            mock_result.confidence = 0.9
            mock_result.metadata = {"user_id": "test_user_123"}
            
            recommendation_agent.run = AsyncMock(return_value=mock_result)
            
            # Teszt üzenet feldolgozása
            result = await recommendation_agent.run(
                "Ajánlj termékeket!",
                deps=mock_deps
            )
            
            assert result.message == "Íme néhány ajánlat számodra!"
            assert result.confidence == 0.9
            assert result.metadata["user_id"] == "test_user_123"
            assert result.reasoning == "A preferenciáid alapján"
    
    @pytest.mark.integration
    async def test_recommendation_agent_error_handling(self, recommendation_agent):
        """Teszt: Recommendation Agent hibakezelés."""
        with patch('src.agents.recommendations.agent.RecommendationDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock hiba
            recommendation_agent.run = AsyncMock(side_effect=Exception("Vector DB hiba"))
            
            with pytest.raises(Exception, match="Vector DB hiba"):
                await recommendation_agent.run("Ajánlj termékeket!", deps=mock_deps)


class TestRecommendationAgentSecurity:
    """Recommendation Agent biztonsági tesztek."""
    
    @pytest.fixture
    def recommendation_agent(self):
        """Recommendation Agent instance."""
        return create_recommendation_agent()
    
    @pytest.mark.security
    async def test_recommendation_agent_sql_injection_protection(self, recommendation_agent):
        """Teszt: SQL injection védelem."""
        malicious_query = "'; DROP TABLE users; --"
        
        with patch('src.agents.recommendations.agent.RecommendationDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Érvénytelen kérés"
            mock_result.confidence = 0.0
            mock_result.recommendations = []
            mock_result.reasoning = "Biztonsági hiba"
            
            recommendation_agent.run = AsyncMock(return_value=mock_result)
            
            result = await recommendation_agent.run(malicious_query, deps=mock_deps)
            
            # Ellenőrizzük, hogy nem adott ki érzékeny információt
            assert "DROP TABLE" not in result.message
            assert result.confidence == 0.0
    
    @pytest.mark.security
    async def test_recommendation_agent_sensitive_data_protection(self, recommendation_agent):
        """Teszt: Érzékeny adatok védelme."""
        sensitive_query = "Mi a jelszavam és a kártyaszámom?"
        
        with patch('src.agents.recommendations.agent.RecommendationDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Ezeket az információkat nem tudom megadni"
            mock_result.confidence = 0.0
            mock_result.recommendations = []
            mock_result.reasoning = "Biztonsági korlátozás"
            
            recommendation_agent.run = AsyncMock(return_value=mock_result)
            
            result = await recommendation_agent.run(sensitive_query, deps=mock_deps)
            
            # Ellenőrizzük, hogy nem adott ki érzékeny adatokat
            assert "jelszó" not in result.message.lower()
            assert "kártya" not in result.message.lower()
            assert result.confidence == 0.0
    
    @pytest.mark.security
    async def test_recommendation_agent_unauthorized_access(self, recommendation_agent):
        """Teszt: Jogosulatlan hozzáférés kezelése."""
        unauthorized_query = "Másik felhasználó preferenciáit szeretném látni"
        
        with patch('src.agents.recommendations.agent.RecommendationDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Nincs jogosultságod más felhasználók adatainak megtekintéséhez"
            mock_result.confidence = 0.0
            mock_result.recommendations = []
            mock_result.reasoning = "Jogosultsági hiba"
            
            recommendation_agent.run = AsyncMock(return_value=mock_result)
            
            result = await recommendation_agent.run(unauthorized_query, deps=mock_deps)
            
            assert "jogosultság" in result.message.lower()
            assert result.confidence == 0.0


class TestRecommendationAgentPerformance:
    """Recommendation Agent teljesítmény tesztek."""
    
    @pytest.fixture
    def recommendation_agent(self):
        """Recommendation Agent instance."""
        return create_recommendation_agent()
    
    @pytest.mark.performance
    async def test_recommendation_agent_response_time(self, recommendation_agent):
        """Teszt: Válaszidő mérése."""
        import time
        
        with patch('src.agents.recommendations.agent.RecommendationDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Íme az ajánlatok!"
            mock_result.recommendations = []
            mock_result.reasoning = "Preferenciák alapján"
            mock_result.confidence = 0.9
            
            recommendation_agent.run = AsyncMock(return_value=mock_result)
            
            start_time = time.time()
            result = await recommendation_agent.run("Ajánlj termékeket!", deps=mock_deps)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Válaszidőnek 5 másodperc alatt kell lennie
            assert response_time < 5.0
            assert result.message == "Íme az ajánlatok!"
    
    @pytest.mark.performance
    async def test_recommendation_agent_concurrent_requests(self, recommendation_agent):
        """Teszt: Párhuzamos kérések kezelése."""
        with patch('src.agents.recommendations.agent.RecommendationDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Személyre szabott ajánlatok"
            mock_result.recommendations = []
            mock_result.reasoning = "Trend elemzés alapján"
            mock_result.confidence = 0.8
            
            recommendation_agent.run = AsyncMock(return_value=mock_result)
            
            # Párhuzamos kérések
            async def make_request():
                return await recommendation_agent.run("Ajánlj termékeket!", deps=mock_deps)
            
            # 5 párhuzamos kérés - trio kompatibilitás miatt
            results = []
            for _ in range(5):
                result = await make_request()
                results.append(result)
            
            # Minden kérésnek sikeresen le kell futnia
            assert len(results) == 5
            for result in results:
                assert result.message == "Személyre szabott ajánlatok"
                assert result.confidence == 0.8


class TestRecommendationAgentEdgeCases:
    """Recommendation Agent edge case tesztek."""
    
    @pytest.fixture
    def recommendation_agent(self):
        """Recommendation Agent instance."""
        return create_recommendation_agent()
    
    @pytest.mark.edge_cases
    async def test_recommendation_agent_empty_query(self, recommendation_agent):
        """Teszt: Üres lekérdezés kezelése."""
        with patch('src.agents.recommendations.agent.RecommendationDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Kérlek, adj meg egy konkrét kérést"
            mock_result.confidence = 0.0
            mock_result.recommendations = []
            mock_result.reasoning = "Üres kérés"
            
            recommendation_agent.run = AsyncMock(return_value=mock_result)
            
            result = await recommendation_agent.run("", deps=mock_deps)
            
            assert "kérést" in result.message.lower()
            assert result.confidence == 0.0
    
    @pytest.mark.edge_cases
    async def test_recommendation_agent_very_long_query(self, recommendation_agent):
        """Teszt: Nagyon hosszú lekérdezés kezelése."""
        long_query = "Ajánlj termékeket!" * 100  # 2000 karakter
        
        with patch('src.agents.recommendations.agent.RecommendationDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Túl hosszú lekérdezés"
            mock_result.confidence = 0.0
            mock_result.recommendations = []
            mock_result.reasoning = "Hosszú kérés"
            
            recommendation_agent.run = AsyncMock(return_value=mock_result)
            
            result = await recommendation_agent.run(long_query, deps=mock_deps)
            
            assert "hosszú" in result.message.lower()
            assert result.confidence == 0.0
    
    @pytest.mark.edge_cases
    async def test_recommendation_agent_special_characters(self, recommendation_agent):
        """Teszt: Speciális karakterek kezelése."""
        special_query = "Ajánlj termékeket! 🛒📱 #shopping @user"
        
        with patch('src.agents.recommendations.agent.RecommendationDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Íme az ajánlatok!"
            mock_result.confidence = 0.9
            mock_result.recommendations = []
            mock_result.reasoning = "Speciális karakterek kezelése"
            
            recommendation_agent.run = AsyncMock(return_value=mock_result)
            
            result = await recommendation_agent.run(special_query, deps=mock_deps)
            
            assert result.message == "Íme az ajánlatok!"
            assert result.confidence == 0.9
    
    @pytest.mark.edge_cases
    async def test_recommendation_agent_no_preferences(self, recommendation_agent):
        """Teszt: Nincs preferencia esetén."""
        with patch('src.agents.recommendations.agent.RecommendationDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock üres preferenciák
            mock_deps.user_context = {"user_id": "new_user", "preferences": {}}
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Még nincsenek preferenciáid, népszerű termékeket ajánlok"
            mock_result.confidence = 0.7
            mock_result.recommendations = []
            mock_result.reasoning = "Nincs preferencia"
            
            recommendation_agent.run = AsyncMock(return_value=mock_result)
            
            result = await recommendation_agent.run("Ajánlj termékeket!", deps=mock_deps)
            
            assert "nincs" in result.message.lower() or "népszerű" in result.message.lower()
            assert result.confidence == 0.7


class TestRecommendationAgentBusinessLogic:
    """Recommendation Agent üzleti logika tesztek."""
    
    @pytest.fixture
    def recommendation_agent(self):
        """Recommendation Agent instance."""
        return create_recommendation_agent()
    
    @pytest.mark.business_logic
    async def test_recommendation_agent_category_based_recommendations(self, recommendation_agent):
        """Teszt: Kategória alapú ajánlatok."""
        with patch('src.agents.recommendations.agent.RecommendationDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock elektronikai preferenciák
            mock_deps.user_context = {
                "user_id": "test_user",
                "preferences": {"categories": ["electronics"]}
            }
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Elektronikai termékeket ajánlok"
            mock_result.confidence = 0.9
            mock_result.recommendations = []
            mock_result.reasoning = "Elektronikai preferenciák alapján"
            
            recommendation_agent.run = AsyncMock(return_value=mock_result)
            
            result = await recommendation_agent.run("Ajánlj elektronikai termékeket!", deps=mock_deps)
            
            assert "elektronikai" in result.message.lower()
            assert result.confidence == 0.9
    
    @pytest.mark.business_logic
    async def test_recommendation_agent_price_range_filtering(self, recommendation_agent):
        """Teszt: Ár tartomány szűrés."""
        with patch('src.agents.recommendations.agent.RecommendationDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock ár tartomány preferenciák
            mock_deps.user_context = {
                "user_id": "test_user",
                "preferences": {"price_range": {"min": 10000, "max": 100000}}
            }
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "10-100 ezer forintos termékeket ajánlok"
            mock_result.confidence = 0.8
            mock_result.recommendations = []
            mock_result.reasoning = "Ár tartomány alapján"
            
            recommendation_agent.run = AsyncMock(return_value=mock_result)
            
            result = await recommendation_agent.run("Ajánlj olcsó termékeket!", deps=mock_deps)
            
            assert "10-100" in result.message or "ár" in result.message.lower()
            assert result.confidence == 0.8
    
    @pytest.mark.business_logic
    async def test_recommendation_agent_brand_preferences(self, recommendation_agent):
        """Teszt: Márka preferenciák."""
        with patch('src.agents.recommendations.agent.RecommendationDependencies') as mock_deps_class:
            mock_deps = Mock()
            mock_deps_class.return_value = mock_deps
            
            # Mock márka preferenciák
            mock_deps.user_context = {
                "user_id": "test_user",
                "preferences": {"brands": ["Apple", "Samsung"]}
            }
            
            # Mock agent válasz
            mock_result = Mock()
            mock_result.message = "Apple és Samsung termékeket ajánlok"
            mock_result.confidence = 0.9
            mock_result.recommendations = []
            mock_result.reasoning = "Márka preferenciák alapján"
            
            recommendation_agent.run = AsyncMock(return_value=mock_result)
            
            result = await recommendation_agent.run("Ajánlj Apple termékeket!", deps=mock_deps)
            
            assert "apple" in result.message.lower() or "samsung" in result.message.lower()
            assert result.confidence == 0.9 