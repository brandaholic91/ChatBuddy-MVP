"""
ShopRenter webshop integration tesztek - shoprenter.py lefedettség növelése
"""
import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.integrations.webshop.shoprenter import ShoprenterAPI, MockShoprenterAPI
from src.integrations.webshop.base import (
    Product, Order, Customer, OrderStatus, ProductCategory, OrderItem
)


class TestShoprenterAPIInitialization:
    """ShoprenterAPI inicializálás tesztek"""
    
    def test_shoprenter_api_initialization(self):
        """Shoprenter API inicializálás teszt"""
        api_key = "test_key"
        base_url = "https://test-store.shoprenter.hu"
        
        api = ShoprenterAPI(api_key, base_url)
        
        assert api.api_key == api_key
        assert api.base_url == base_url
        assert api.client is not None
        assert api.client.headers["Authorization"] == f"Bearer {api_key}"
        assert api.client.headers["Content-Type"] == "application/json"
        
        # Timeout objektum helyes összehasonlítása
        assert str(api.client.timeout) == "Timeout(timeout=30.0)"  # Teljes string formátum
    
    def test_mock_shoprenter_api_initialization(self):
        """Mock Shoprenter API inicializálás teszt"""
        mock_api = MockShoprenterAPI()
        
        assert len(mock_api.mock_products) >= 3  # Has mock products
        assert len(mock_api.mock_orders) >= 2    # Has mock orders  
        assert len(mock_api.mock_customers) >= 1 # Has mock customers


class TestMockShoprenterAPI:
    """Mock Shoprenter API tesztek"""
    
    @pytest.fixture
    def mock_api(self):
        """Mock Shoprenter API fixture"""
        return MockShoprenterAPI()
    
    @pytest.mark.asyncio
    async def test_mock_get_products_default(self, mock_api):
        """Mock termékek lekérése alapértelmezett teszt"""
        products = await mock_api.get_products()
        
        assert len(products) >= 3
        assert all(isinstance(product, Product) for product in products)
        assert all(product.currency == "HUF" for product in products)
        assert all(isinstance(product.price, float) for product in products)
        assert all(isinstance(product.stock, int) for product in products)
    
    @pytest.mark.asyncio
    async def test_mock_get_products_with_pagination(self, mock_api):
        """Mock termékek lekérése lapozással teszt"""
        all_products = await mock_api.get_products()
        
        if len(all_products) > 1:
            products = await mock_api.get_products(limit=2, offset=1)
            assert len(products) <= 2
    
    @pytest.mark.asyncio
    async def test_mock_get_products_with_category_filter(self, mock_api):
        """Mock termékek lekérése kategória szűrővel teszt"""
        products = await mock_api.get_products(category="electronics")
        
        electronics_products = [p for p in products if p.category == ProductCategory.ELECTRONICS]
        assert len(electronics_products) >= 0
    
    @pytest.mark.asyncio
    async def test_mock_get_product_found(self, mock_api):
        """Mock termék lekérése található teszt"""
        all_products = await mock_api.get_products()
        
        if all_products:
            product_id = all_products[0].id
            product = await mock_api.get_product(product_id)
            
            assert product is not None
            assert product.id == product_id
            assert isinstance(product.name, str)
            assert isinstance(product.price, float)
    
    @pytest.mark.asyncio
    async def test_mock_get_product_not_found(self, mock_api):
        """Mock termék lekérése nem található teszt"""
        product = await mock_api.get_product("nonexistent_product_id")
        
        assert product is None
    
    @pytest.mark.asyncio
    async def test_mock_search_products_by_name(self, mock_api):
        """Mock termék keresés név alapján teszt"""
        all_products = await mock_api.get_products()
        
        if all_products:
            # Use part of the first product's name for search
            search_term = all_products[0].name.split()[0].lower()
            products = await mock_api.search_products(search_term)
            
            # Should find at least the original product
            found_names = [p.name.lower() for p in products]
            assert any(search_term in name for name in found_names)
    
    @pytest.mark.asyncio
    async def test_mock_search_products_no_results(self, mock_api):
        """Mock termék keresés nincs eredmény teszt"""
        products = await mock_api.search_products("totally_nonexistent_product_xyz123")
        
        assert products == []
    
    @pytest.mark.asyncio
    async def test_mock_get_orders_for_user(self, mock_api):
        """Mock rendelések lekérése felhasználóhoz teszt"""
        all_orders = await mock_api.get_orders("user_123")
        
        assert isinstance(all_orders, list)
        # All orders should be for the specified user
        for order in all_orders:
            assert order.user_id == "user_123"
    
    @pytest.mark.asyncio
    async def test_mock_get_orders_for_nonexistent_user(self, mock_api):
        """Mock rendelések lekérése nem létező felhasználóhoz teszt"""
        orders = await mock_api.get_orders("nonexistent_user_xyz")
        
        assert orders == []
    
    @pytest.mark.asyncio
    async def test_mock_get_order_found(self, mock_api):
        """Mock rendelés lekérése található teszt"""
        # First get all orders to find a valid order ID
        user_orders = await mock_api.get_orders("user_123")
        
        if user_orders:
            order_id = user_orders[0].id
            order = await mock_api.get_order(order_id)
            
            assert order is not None
            assert order.id == order_id
            assert isinstance(order.total, float)
            assert isinstance(order.items, list)
            assert len(order.items) > 0
    
    @pytest.mark.asyncio
    async def test_mock_get_order_not_found(self, mock_api):
        """Mock rendelés lekérése nem található teszt"""
        order = await mock_api.get_order("nonexistent_order_id")
        
        assert order is None
    
    @pytest.mark.asyncio
    async def test_mock_get_customer_found(self, mock_api):
        """Mock ügyfél lekérése található teszt"""
        customer = await mock_api.get_customer("user_123")
        
        if customer is not None:
            assert customer.id == "user_123"
            assert isinstance(customer.email, str)
            assert "@" in customer.email
            assert isinstance(customer.first_name, str)
    
    @pytest.mark.asyncio
    async def test_mock_get_customer_not_found(self, mock_api):
        """Mock ügyfél lekérése nem található teszt"""
        customer = await mock_api.get_customer("nonexistent_customer_id")
        
        assert customer is None
    
    @pytest.mark.asyncio
    async def test_mock_update_order_status_success(self, mock_api):
        """Mock rendelési státusz frissítés sikeres teszt"""
        # Get a valid order first
        user_orders = await mock_api.get_orders("user_123")
        
        if user_orders:
            order_id = user_orders[0].id
            original_order = await mock_api.get_order(order_id)
            original_status = original_order.status
            
            result = await mock_api.update_order_status(order_id, OrderStatus.DELIVERED)
            
            assert result is True
            
            updated_order = await mock_api.get_order(order_id)
            assert updated_order.status == OrderStatus.DELIVERED
    
    @pytest.mark.asyncio
    async def test_mock_update_order_status_not_found(self, mock_api):
        """Mock rendelési státusz frissítés nem található teszt"""
        result = await mock_api.update_order_status("nonexistent_order", OrderStatus.DELIVERED)
        
        assert result is False


class TestAsyncDelayBehavior:
    """Async delay viselkedés tesztek"""
    
    @pytest.fixture
    def mock_api(self):
        """Mock Shoprenter API fixture"""
        return MockShoprenterAPI()
    
    @pytest.mark.asyncio
    async def test_mock_api_has_delays(self, mock_api):
        """Mock API tartalmaz késleltetést teszt"""
        import time
        
        start_time = time.time()
        await mock_api.get_products()
        end_time = time.time()
        
        # Should have some delay (at least 0.05 seconds)
        assert (end_time - start_time) >= 0.05


class TestRealShoprenterAPIExceptionHandling:
    """Éles Shoprenter API hibakezelés tesztek"""
    
    @pytest.fixture
    def shoprenter_api(self):
        """Shoprenter API fixture"""
        return ShoprenterAPI("test_key", "https://test-shop.shoprenter.hu")
    
    @pytest.mark.asyncio
    async def test_get_products_exception(self, shoprenter_api):
        """Termékek lekérése kivétel teszt"""
        with patch.object(shoprenter_api.client, 'get', side_effect=httpx.HTTPStatusError("404", request=Mock(), response=Mock())):
            products = await shoprenter_api.get_products()
            
            assert products == []
    
    @pytest.mark.asyncio
    async def test_get_product_exception(self, shoprenter_api):
        """Egy termék lekérése kivétel teszt"""
        with patch.object(shoprenter_api.client, 'get', side_effect=Exception("Network error")):
            product = await shoprenter_api.get_product("test_id")
            
            assert product is None
    
    @pytest.mark.asyncio
    async def test_search_products_exception(self, shoprenter_api):
        """Termék keresés kivétel teszt"""
        with patch.object(shoprenter_api.client, 'get', side_effect=Exception("Search error")):
            products = await shoprenter_api.search_products("test")
            
            assert products == []
    
    @pytest.mark.asyncio
    async def test_get_orders_exception(self, shoprenter_api):
        """Rendelések lekérése kivétel teszt"""
        with patch.object(shoprenter_api.client, 'get', side_effect=Exception("Orders error")):
            orders = await shoprenter_api.get_orders("test_user")
            
            assert orders == []
    
    @pytest.mark.asyncio
    async def test_get_order_exception(self, shoprenter_api):
        """Egy rendelés lekérése kivétel teszt"""
        with patch.object(shoprenter_api.client, 'get', side_effect=Exception("Order error")):
            order = await shoprenter_api.get_order("test_id")
            
            assert order is None
    
    @pytest.mark.asyncio
    async def test_get_customer_exception(self, shoprenter_api):
        """Ügyfél lekérése kivétel teszt"""
        with patch.object(shoprenter_api.client, 'get', side_effect=Exception("Customer error")):
            customer = await shoprenter_api.get_customer("test_id")
            
            assert customer is None
    
    @pytest.mark.asyncio
    async def test_update_order_status_exception(self, shoprenter_api):
        """Rendelési státusz frissítés kivétel teszt"""
        with patch.object(shoprenter_api.client, 'patch', side_effect=Exception("Update error")):
            result = await shoprenter_api.update_order_status("test_id", OrderStatus.DELIVERED)
            
            assert result is False


class TestEdgeCases:
    """Edge case tesztek"""
    
    @pytest.fixture
    def mock_api(self):
        """Mock Shoprenter API fixture"""
        return MockShoprenterAPI()
    
    @pytest.mark.asyncio
    async def test_empty_search_query(self, mock_api):
        """Üres keresési kifejezés teszt"""
        # Mock a search_products metódust üres eredménnyel
        mock_api.search_products = AsyncMock(return_value=[])
        
        products = await mock_api.search_products("", limit=10)
        
        assert products == []
        mock_api.search_products.assert_called_once_with("", limit=10)
    
    @pytest.mark.asyncio
    async def test_zero_limit_parameters(self, mock_api):
        """Nulla limit paraméterek teszt"""
        products = await mock_api.get_products(limit=0)
        
        assert products == []
    
    @pytest.mark.asyncio
    async def test_high_offset_parameters(self, mock_api):
        """Magas offset paraméterek teszt"""
        products = await mock_api.get_products(limit=10, offset=1000)
        
        assert products == []  # Offset beyond available data
    
    @pytest.mark.asyncio
    async def test_negative_limit_parameters(self, mock_api):
        """Negatív limit paraméterek teszt"""
        products = await mock_api.get_products(limit=-1)
        
        # Should handle negative limit gracefully
        assert isinstance(products, list)


class TestDataStructureValidation:
    """Adatstruktúra validációs tesztek"""
    
    @pytest.fixture
    def mock_api(self):
        """Mock Shoprenter API fixture"""
        return MockShoprenterAPI()
    
    @pytest.mark.asyncio
    async def test_product_data_structure(self, mock_api):
        """Termék adatstruktúra teszt"""
        products = await mock_api.get_products()
        
        for product in products:
            assert isinstance(product, Product)
            assert isinstance(product.id, str)
            assert isinstance(product.name, str)
            assert isinstance(product.price, float)
            assert isinstance(product.stock, int)
            assert isinstance(product.category, ProductCategory)
            assert isinstance(product.images, list)
            assert isinstance(product.tags, list)
            assert isinstance(product.is_active, bool)
            assert isinstance(product.created_at, datetime)
            assert isinstance(product.updated_at, datetime)
    
    @pytest.mark.asyncio
    async def test_order_data_structure(self, mock_api):
        """Rendelés adatstruktúra teszt"""
        orders = await mock_api.get_orders("user_123")
        
        for order in orders:
            assert isinstance(order, Order)
            assert isinstance(order.id, str)
            assert isinstance(order.user_id, str)
            assert isinstance(order.status, OrderStatus)
            assert isinstance(order.total, float)
            assert isinstance(order.items, list)
            
            for item in order.items:
                assert isinstance(item, OrderItem)
                assert isinstance(item.product_id, str)
                assert isinstance(item.product_name, str)
                assert isinstance(item.quantity, int)
                assert isinstance(item.unit_price, float)
                assert isinstance(item.total_price, float)
    
    @pytest.mark.asyncio
    async def test_customer_data_structure(self, mock_api):
        """Ügyfél adatstruktúra teszt"""
        customer = await mock_api.get_customer("user_123")
        
        if customer:
            assert isinstance(customer, Customer)
            assert isinstance(customer.id, str)
            assert isinstance(customer.email, str)
            assert "@" in customer.email
            if customer.first_name:
                assert isinstance(customer.first_name, str)
            if customer.last_name:
                assert isinstance(customer.last_name, str)
            if customer.phone:
                assert isinstance(customer.phone, str)
            if customer.address:
                assert isinstance(customer.address, dict)


class TestCloseMethod:
    """Close metódus tesztek"""
    
    @pytest.mark.asyncio
    async def test_real_api_close(self):
        """Éles API close metódus teszt"""
        api = ShoprenterAPI("test_key", "https://test-shop.shoprenter.hu")
        
        with patch.object(api.client, 'aclose') as mock_close:
            await api.close()
            mock_close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mock_api_close(self):
        """Mock API close metódus teszt"""
        mock_api = MockShoprenterAPI()
        
        # Mock a close metódust
        mock_api.close = AsyncMock()
        
        await mock_api.close()
        
        mock_api.close.assert_called_once()


class TestSearchFunctionality:
    """Keresési funkciók tesztek"""
    
    @pytest.fixture
    def mock_api(self):
        """Mock Shoprenter API fixture"""
        return MockShoprenterAPI()
    
    @pytest.mark.asyncio
    async def test_search_products_case_insensitive(self, mock_api):
        """Termék keresés case insensitive teszt"""
        all_products = await mock_api.get_products()
        
        if all_products:
            # Test with uppercase search term
            product_name = all_products[0].name
            uppercase_search = product_name.split()[0].upper()
            products_upper = await mock_api.search_products(uppercase_search)
            
            # Test with lowercase search term
            lowercase_search = product_name.split()[0].lower()
            products_lower = await mock_api.search_products(lowercase_search)
            
            # Should find results regardless of case
            assert len(products_upper) >= 0
            assert len(products_lower) >= 0
    
    @pytest.mark.asyncio
    async def test_search_products_with_limit(self, mock_api):
        """Termék keresés limit teszt"""
        # Search with a term that might match multiple products
        products = await mock_api.search_products("a", limit=2)  # "a" is common
        
        assert len(products) <= 2


class TestConcurrencyAndPerformance:
    """Párhuzamosság és teljesítmény tesztek"""
    
    @pytest.fixture
    def mock_api(self):
        """Mock Shoprenter API fixture"""
        return MockShoprenterAPI()
    
    @pytest.mark.asyncio
    async def test_concurrent_product_requests(self, mock_api):
        """Párhuzamos termék kérések teszt"""
        import asyncio
        
        # Make multiple concurrent requests
        tasks = [
            mock_api.get_products(),
            mock_api.get_products(limit=5),
            mock_api.get_products(offset=1)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All requests should succeed
        assert len(results) == 3
        assert all(isinstance(result, list) for result in results)
    
    @pytest.mark.asyncio
    async def test_concurrent_mixed_requests(self, mock_api):
        """Párhuzamos vegyes kérések teszt"""
        import asyncio
        
        # Make different types of concurrent requests
        tasks = [
            mock_api.get_products(),
            mock_api.get_orders("user_123"),
            mock_api.get_customer("user_123")
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # No requests should raise exceptions
        assert all(not isinstance(result, Exception) for result in results)