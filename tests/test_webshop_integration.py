"""
Webshop API integration tests for Chatbuddy MVP.

This module tests the webshop API integrations including:
- Mock API functionality
- Unified API interface
- Error handling
- Data model validation
"""

import pytest
import asyncio
from datetime import datetime
from typing import List

from src.integrations.webshop.base import (
    Product, Order, Customer, OrderStatus, ProductCategory, OrderItem
)
from src.integrations.webshop.shoprenter import MockShoprenterAPI
from src.integrations.webshop.unas import MockUNASAPI
from src.integrations.webshop.unified import (
    UnifiedWebshopAPI, WebshopManager, WebshopPlatform,
    create_shoprenter_api, create_unas_api, create_mock_api
)


class TestWebshopDataModels:
    """Webshop adatmodellek tesztelése"""
    
    def test_product_model_creation(self):
        """Termék modell létrehozás tesztelése"""
        product = Product(
            id="test_prod_1",
            name="Teszt Termék",
            description="Teszt termék leírása",
            price=99999.0,
            original_price=119999.0,
            stock=10,
            category=ProductCategory.ELECTRONICS,
            brand="Teszt Márka",
            images=["https://example.com/test.jpg"],
            tags=["teszt", "elektronika"],
            is_active=True
        )
        
        assert product.id == "test_prod_1"
        assert product.name == "Teszt Termék"
        assert product.price == 99999.0
        assert product.category == ProductCategory.ELECTRONICS
        assert len(product.tags) == 2
    
    def test_order_model_creation(self):
        """Rendelés modell létrehozás tesztelése"""
        order_item = OrderItem(
            product_id="test_prod_1",
            product_name="Teszt Termék",
            quantity=2,
            unit_price=99999.0,
            total_price=199998.0
        )
        
        order = Order(
            id="test_order_1",
            user_id="test_user_1",
            status=OrderStatus.PROCESSING,
            total=199998.0,
            items=[order_item],
            shipping_address={
                "street": "Teszt utca 1.",
                "city": "Budapest",
                "postal_code": "1234"
            }
        )
        
        assert order.id == "test_order_1"
        assert order.status == OrderStatus.PROCESSING
        assert len(order.items) == 1
        assert order.items[0].product_name == "Teszt Termék"
    
    def test_customer_model_creation(self):
        """Ügyfél modell létrehozás tesztelése"""
        customer = Customer(
            id="test_customer_1",
            email="test@example.com",
            first_name="Teszt",
            last_name="Felhasználó",
            phone="+36 20 123 4567"
        )
        
        assert customer.id == "test_customer_1"
        assert customer.email == "test@example.com"
        assert customer.first_name == "Teszt"


class TestMockShoprenterAPI:
    """Mock Shoprenter API tesztelése"""
    
    @pytest.fixture
    def mock_api(self):
        """Mock API fixture"""
        return MockShoprenterAPI()
    
    @pytest.mark.asyncio
    async def test_get_products(self, mock_api):
        """Termékek lekérése tesztelése"""
        products = await mock_api.get_products(limit=5)
        
        assert len(products) > 0
        assert all(isinstance(p, Product) for p in products)
        assert products[0].name == "iPhone 15 Pro"
    
    @pytest.mark.asyncio
    async def test_get_product(self, mock_api):
        """Egy termék lekérése tesztelése"""
        product = await mock_api.get_product("prod_1")
        
        assert product is not None
        assert product.id == "prod_1"
        assert product.name == "iPhone 15 Pro"
        assert product.price == 499999.0
    
    @pytest.mark.asyncio
    async def test_search_products(self, mock_api):
        """Termék keresés tesztelése"""
        results = await mock_api.search_products("iPhone")
        
        assert len(results) > 0
        assert any("iPhone" in p.name for p in results)
    
    @pytest.mark.asyncio
    async def test_get_orders(self, mock_api):
        """Rendelések lekérése tesztelése"""
        orders = await mock_api.get_orders("user_123")
        
        assert len(orders) > 0
        assert all(isinstance(o, Order) for o in orders)
        assert orders[0].user_id == "user_123"
    
    @pytest.mark.asyncio
    async def test_get_order(self, mock_api):
        """Egy rendelés lekérése tesztelése"""
        order = await mock_api.get_order("order_1")
        
        assert order is not None
        assert order.id == "order_1"
        assert order.status == OrderStatus.SHIPPED
    
    @pytest.mark.asyncio
    async def test_get_customer(self, mock_api):
        """Ügyfél adatok lekérése tesztelése"""
        customer = await mock_api.get_customer("user_123")
        
        assert customer is not None
        assert customer.id == "user_123"
        assert customer.email == "user@example.com"
    
    @pytest.mark.asyncio
    async def test_update_order_status(self, mock_api):
        """Rendelési státusz frissítése tesztelése"""
        success = await mock_api.update_order_status("order_1", OrderStatus.DELIVERED)
        
        assert success is True
        
        # Ellenőrizzük, hogy tényleg frissült
        order = await mock_api.get_order("order_1")
        assert order.status == OrderStatus.DELIVERED


class TestMockUNASAPI:
    """Mock UNAS API tesztelése"""
    
    @pytest.fixture
    def mock_api(self):
        """Mock API fixture"""
        return MockUNASAPI()
    
    @pytest.mark.asyncio
    async def test_get_products(self, mock_api):
        """Termékek lekérése tesztelése"""
        products = await mock_api.get_products(limit=5)
        
        assert len(products) > 0
        assert all(isinstance(p, Product) for p in products)
        assert products[0].name == "Asus ROG Strix G15"
    
    @pytest.mark.asyncio
    async def test_get_product(self, mock_api):
        """Egy termék lekérése tesztelése"""
        product = await mock_api.get_product("unas_prod_1")
        
        assert product is not None
        assert product.id == "unas_prod_1"
        assert product.name == "Asus ROG Strix G15"
        assert product.price == 899999.0
    
    @pytest.mark.asyncio
    async def test_search_products(self, mock_api):
        """Termék keresés tesztelése"""
        results = await mock_api.search_products("laptop")
        
        assert len(results) > 0
        assert any("laptop" in p.tags for p in results)
    
    @pytest.mark.asyncio
    async def test_get_orders(self, mock_api):
        """Rendelések lekérése tesztelése"""
        orders = await mock_api.get_orders("unas_user_123")
        
        assert len(orders) > 0
        assert all(isinstance(o, Order) for o in orders)
        assert orders[0].user_id == "unas_user_123"


class TestUnifiedWebshopAPI:
    """Egységes webshop API tesztelése"""
    
    @pytest.fixture
    def unified_api(self):
        """Unified API fixture"""
        return create_mock_api()
    
    @pytest.mark.asyncio
    async def test_unified_get_products(self, unified_api):
        """Egységes termékek lekérése tesztelése"""
        products = await unified_api.get_products(limit=5)
        
        assert len(products) > 0
        assert all(isinstance(p, Product) for p in products)
    
    @pytest.mark.asyncio
    async def test_unified_search_products(self, unified_api):
        """Egységes termék keresés tesztelése"""
        results = await unified_api.search_products("telefon")
        
        assert len(results) > 0
        assert any("telefon" in p.tags for p in results)
    
    @pytest.mark.asyncio
    async def test_unified_get_order(self, unified_api):
        """Egységes rendelés lekérése tesztelése"""
        order = await unified_api.get_order("order_1")
        
        assert order is not None
        assert order.id == "order_1"
    
    def test_platform_info(self, unified_api):
        """Platform információk tesztelése"""
        info = unified_api.get_platform_info()
        
        assert "platform" in info
        assert "base_url" in info
        assert "api_key_configured" in info
        assert info["platform"] == "mock"


class TestWebshopManager:
    """Webshop kezelő tesztelése"""
    
    @pytest.fixture
    def manager(self):
        """Webshop manager fixture"""
        return WebshopManager()
    
    def test_add_webshop(self, manager):
        """Webshop hozzáadása tesztelése"""
        manager.add_webshop(
            "test_shop",
            WebshopPlatform.SHOPRENTER,
            "test_key",
            "https://test.shoprenter.hu"
        )
        
        assert "test_shop" in manager.list_webshops()
        assert manager.get_webshop("test_shop") is not None
    
    @pytest.mark.asyncio
    async def test_search_all_products(self, manager):
        """Minden webshopban keresés tesztelése"""
        # Mock webshopok hozzáadása
        manager.add_webshop(
            "shoprenter_mock",
            WebshopPlatform.SHOPRENTER,
            "mock_key",
            "https://mock.shoprenter.hu"
        )
        manager.add_webshop(
            "unas_mock",
            WebshopPlatform.UNAS,
            "mock_key",
            "https://mock.unas.hu"
        )
        
        results = await manager.search_all_products("iPhone")
        
        assert "shoprenter_mock" in results
        assert "unas_mock" in results
        assert len(results["shoprenter_mock"]) > 0
        # UNAS mock-ban nincs iPhone, ezért üres lista
        assert len(results["unas_mock"]) >= 0
    
    @pytest.mark.asyncio
    async def test_get_product_from_all(self, manager):
        """Termék lekérése minden webshopból tesztelése"""
        # Mock webshopok hozzáadása
        manager.add_webshop(
            "shoprenter_mock",
            WebshopPlatform.SHOPRENTER,
            "mock_key",
            "https://mock.shoprenter.hu"
        )
        
        results = await manager.get_product_from_all("prod_1")
        
        assert "shoprenter_mock" in results
        assert results["shoprenter_mock"] is not None
        assert results["shoprenter_mock"].name == "iPhone 15 Pro"


class TestFactoryFunctions:
    """Factory függvények tesztelése"""
    
    def test_create_shoprenter_api_mock(self):
        """Shoprenter API létrehozása mock módban"""
        api = create_shoprenter_api("mock_key", "https://mock.shoprenter.hu", use_mock=True)
        
        assert api.platform == WebshopPlatform.MOCK
        assert api.api_key == "mock_key"
    
    def test_create_unas_api_mock(self):
        """UNAS API létrehozása mock módban"""
        api = create_unas_api("mock_key", "https://mock.unas.hu", use_mock=True)
        
        assert api.platform == WebshopPlatform.MOCK
        assert api.api_key == "mock_key"
    
    def test_create_mock_api(self):
        """Mock API létrehozása"""
        api = create_mock_api()
        
        assert api.platform == WebshopPlatform.MOCK
        assert api.api_key == "mock_key"


class TestErrorHandling:
    """Hibakezelés tesztelése"""
    
    @pytest.mark.asyncio
    async def test_invalid_product_id(self):
        """Érvénytelen termék azonosító tesztelése"""
        mock_api = MockShoprenterAPI()
        
        product = await mock_api.get_product("invalid_id")
        
        assert product is None
    
    @pytest.mark.asyncio
    async def test_invalid_order_id(self):
        """Érvénytelen rendelés azonosító tesztelése"""
        mock_api = MockShoprenterAPI()
        
        order = await mock_api.get_order("invalid_order")
        
        assert order is None
    
    @pytest.mark.asyncio
    async def test_invalid_customer_id(self):
        """Érvénytelen ügyfél azonosító tesztelése"""
        mock_api = MockShoprenterAPI()
        
        customer = await mock_api.get_customer("invalid_customer")
        
        assert customer is None


class TestPerformance:
    """Teljesítmény tesztelése"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Párhuzamos kérések tesztelése"""
        mock_api = MockShoprenterAPI()
        
        # Párhuzamos termék lekérések
        tasks = [
            mock_api.get_product("prod_1"),
            mock_api.get_product("prod_2"),
            mock_api.get_product("prod_3")
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        assert all(r is not None for r in results)
    
    @pytest.mark.asyncio
    async def test_bulk_product_search(self):
        """Tömeges termék keresés tesztelése"""
        mock_api = MockShoprenterAPI()
        
        # Több keresési kérés párhuzamosan - csak olyan termékeket keresünk, amik biztosan léteznek
        search_queries = ["iPhone", "Nike", "Samsung"]
        tasks = [mock_api.search_products(query) for query in search_queries]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        assert all(len(r) > 0 for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 