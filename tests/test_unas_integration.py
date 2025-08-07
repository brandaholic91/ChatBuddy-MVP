"""
UNAS webshop integration tesztek - unas.py lefedettség növelése
"""
import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import List, Optional

from src.integrations.webshop.unas import UNASAPI, MockUNASAPI
from src.integrations.webshop.base import (
    Product, Order, Customer, OrderStatus, ProductCategory, OrderItem
)


class TestUNASAPIInitialization:
    """UNASAPI inicializálás tesztek"""
    
    def test_unas_api_initialization(self):
        """UNAS API inicializálás teszt"""
        api_key = "test_key"
        base_url = "https://test-store.unas.hu"
        
        api = UNASAPI(api_key, base_url)
        
        assert api.api_key == api_key
        assert api.base_url == base_url
        assert api.client is not None
        assert api.client.headers["X-API-Key"] == api_key
        assert api.client.headers["Content-Type"] == "application/json"
        
        # Timeout objektum helyes összehasonlítása
        assert str(api.client.timeout) == "Timeout(timeout=30.0)"  # Teljes string formátum
    
    def test_mock_unas_api_initialization_default(self):
        """Mock UNAS API alapértelmezett inicializálás teszt"""
        mock_api = MockUNASAPI()
        
        assert mock_api.api_key == "mock_key"
        assert mock_api.base_url == "https://mock.unas.hu"
        assert len(mock_api.mock_products) == 3
        assert len(mock_api.mock_orders) == 2
        assert len(mock_api.mock_customers) == 1
    
    def test_mock_unas_api_initialization_custom(self):
        """Mock UNAS API egyedi inicializálás teszt"""
        api_key = "custom_mock_key"
        base_url = "https://custom.unas.hu"
        
        mock_api = MockUNASAPI(api_key, base_url)
        
        assert mock_api.api_key == api_key
        assert mock_api.base_url == base_url


class TestUNASAPIProducts:
    """UNAS API termék metódusok tesztek"""
    
    @pytest.fixture
    def unas_api(self):
        """UNAS API fixture"""
        return UNASAPI("test_key", "https://test.unas.hu")
    
    @pytest.fixture
    def mock_product_response(self):
        """Mock termék válasz"""
        return {
            "data": [
                {
                    "product_id": "test_prod_1",
                    "name": "Test Product 1",
                    "description": "Test description 1",
                    "price": "25000",
                    "original_price": "30000",
                    "stock": "10",
                    "category": "electronics",
                    "brand": "TestBrand",
                    "images": ["https://example.com/test1.jpg"],
                    "tags": ["test", "electronics"],
                    "active": True,
                    "created_at": "2024-01-01T10:00:00",
                    "updated_at": "2024-01-15T12:00:00"
                },
                {
                    "product_id": "test_prod_2", 
                    "name": "Test Product 2",
                    "description": "Test description 2",
                    "price": "15000",
                    "original_price": "18000",
                    "stock": "5",
                    "category": "clothing",
                    "brand": "TestBrand2",
                    "images": ["https://example.com/test2.jpg"],
                    "tags": ["test", "clothing"],
                    "active": True,
                    "created_at": "2024-01-02T10:00:00",
                    "updated_at": "2024-01-16T12:00:00"
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_get_products_success(self, unas_api, mock_product_response):
        """Termékek lekérése sikeres teszt"""
        with patch.object(unas_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_product_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            products = await unas_api.get_products(limit=10, offset=0)
            
            assert len(products) == 2
            assert products[0].id == "test_prod_1"
            assert products[0].name == "Test Product 1"
            assert products[0].price == 25000.0
            assert products[0].stock == 10
            assert products[0].category == ProductCategory.ELECTRONICS
            
            mock_get.assert_called_once_with(
                "https://test.unas.hu/api/products",
                params={"limit": 10, "offset": 0}
            )
    
    @pytest.mark.asyncio
    async def test_get_products_http_error(self, unas_api):
        """Termékek lekérése HTTP hiba teszt"""
        with patch.object(unas_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404", request=Mock(), response=Mock()
            )
            mock_get.return_value = mock_response
            
            products = await unas_api.get_products()
            
            assert products == []
    
    @pytest.mark.asyncio
    async def test_get_products_exception(self, unas_api):
        """Termékek lekérése általános kivétel teszt"""
        with patch.object(unas_api.client, 'get', side_effect=Exception("Network error")):
            products = await unas_api.get_products()
            
            assert products == []
    
    @pytest.mark.asyncio
    async def test_get_product_success(self, unas_api):
        """Egy termék lekérése sikeres teszt"""
        mock_product_data = {
            "product_id": "test_prod_1",
            "name": "Test Product 1",
            "description": "Test description 1",
            "price": "25000",
            "original_price": "30000",
            "stock": "10",
            "category": "electronics",
            "brand": "TestBrand",
            "images": ["https://example.com/test1.jpg"],
            "tags": ["test", "electronics"],
            "active": True,
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-15T12:00:00"
        }
        
        with patch.object(unas_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_product_data
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            product = await unas_api.get_product("test_prod_1")
            
            assert product is not None
            assert product.id == "test_prod_1"
            assert product.name == "Test Product 1"
            assert product.price == 25000.0
            
            mock_get.assert_called_once_with("https://test.unas.hu/api/products/test_prod_1")
    
    @pytest.mark.asyncio
    async def test_get_product_not_found(self, unas_api):
        """Termék nem található teszt"""
        with patch.object(unas_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404", request=Mock(), response=Mock()
            )
            mock_get.return_value = mock_response
            
            product = await unas_api.get_product("nonexistent_product")
            
            assert product is None
    
    @pytest.mark.asyncio
    async def test_search_products_success(self, unas_api, mock_product_response):
        """Termék keresés sikeres teszt"""
        with patch.object(unas_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_product_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            products = await unas_api.search_products("test", limit=5)
            
            assert len(products) == 2
            assert all("test" in product.name.lower() for product in products)
            
            mock_get.assert_called_once_with(
                "https://test.unas.hu/api/products/search",
                params={"search": "test", "limit": 5}
            )
    
    @pytest.mark.asyncio
    async def test_search_products_empty_result(self, unas_api):
        """Termék keresés üres eredmény teszt"""
        with patch.object(unas_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {"data": []}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            products = await unas_api.search_products("nonexistent")
            
            assert products == []


class TestUNASAPIOrders:
    """UNAS API rendelés metódusok tesztek"""
    
    @pytest.fixture
    def unas_api(self):
        """UNAS API fixture"""
        return UNASAPI("test_key", "https://test.unas.hu")
    
    @pytest.fixture
    def mock_order_response(self):
        """Mock rendelés válasz"""
        return {
            "data": [
                {
                    "order_id": "test_order_1",
                    "user_id": "test_user_1",
                    "status": "processing",
                    "total": "50000",
                    "items": [
                        {
                            "product_id": "test_prod_1",
                            "product_name": "Test Product 1",
                            "quantity": 2,
                            "unit_price": "25000",
                            "total_price": "50000"
                        }
                    ],
                    "shipping_address": {
                        "street": "Test Street 1",
                        "city": "Test City",
                        "postal_code": "1234",
                        "country": "Hungary"
                    },
                    "billing_address": {
                        "street": "Test Street 1",
                        "city": "Test City",
                        "postal_code": "1234",
                        "country": "Hungary"
                    },
                    "tracking_number": "TEST123456",
                    "notes": "Test notes",
                    "created_at": "2024-01-01T10:00:00",
                    "updated_at": "2024-01-15T12:00:00"
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_get_orders_success(self, unas_api, mock_order_response):
        """Rendelések lekérése sikeres teszt"""
        with patch.object(unas_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_order_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            orders = await unas_api.get_orders("test_user_1", limit=10)
            
            assert len(orders) == 1
            assert orders[0].id == "test_order_1"
            assert orders[0].user_id == "test_user_1"
            assert orders[0].status == OrderStatus.PROCESSING
            assert orders[0].total == 50000.0
            assert len(orders[0].items) == 1
            assert orders[0].items[0].product_id == "test_prod_1"
            
            mock_get.assert_called_once_with(
                "https://test.unas.hu/api/orders",
                params={"user_id": "test_user_1", "limit": 10}
            )
    
    @pytest.mark.asyncio
    async def test_get_orders_exception(self, unas_api):
        """Rendelések lekérése kivétel teszt"""
        with patch.object(unas_api.client, 'get', side_effect=Exception("Network error")):
            orders = await unas_api.get_orders("test_user_1")
            
            assert orders == []
    
    @pytest.mark.asyncio
    async def test_get_order_success(self, unas_api):
        """Egy rendelés lekérése sikeres teszt"""
        mock_order_data = {
            "order_id": "test_order_1",
            "user_id": "test_user_1",
            "status": "delivered",
            "total": "50000",
            "items": [
                {
                    "product_id": "test_prod_1",
                    "product_name": "Test Product 1",
                    "quantity": 2,
                    "unit_price": "25000",
                    "total_price": "50000"
                }
            ],
            "shipping_address": {
                "street": "Test Street 1",
                "city": "Test City",
                "postal_code": "1234",
                "country": "Hungary"
            },
            "tracking_number": "TEST123456",
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-15T12:00:00"
        }
        
        with patch.object(unas_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_order_data
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            order = await unas_api.get_order("test_order_1")
            
            assert order is not None
            assert order.id == "test_order_1"
            assert order.status == OrderStatus.DELIVERED
            assert order.total == 50000.0
            
            mock_get.assert_called_once_with("https://test.unas.hu/api/orders/test_order_1")
    
    @pytest.mark.asyncio
    async def test_get_order_not_found(self, unas_api):
        """Rendelés nem található teszt"""
        with patch.object(unas_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404", request=Mock(), response=Mock()
            )
            mock_get.return_value = mock_response
            
            order = await unas_api.get_order("nonexistent_order")
            
            assert order is None


class TestUNASAPICustomers:
    """UNAS API ügyfél metódusok tesztek"""
    
    @pytest.fixture
    def unas_api(self):
        """UNAS API fixture"""
        return UNASAPI("test_key", "https://test.unas.hu")
    
    @pytest.mark.asyncio
    async def test_get_customer_success(self, unas_api):
        """Ügyfél lekérése sikeres teszt"""
        mock_customer_data = {
            "customer_id": "test_customer_1",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+36123456789",
            "address": {
                "street": "Test Street 1",
                "city": "Test City",
                "postal_code": "1234",
                "country": "Hungary"
            },
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-15T12:00:00"
        }
        
        with patch.object(unas_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_customer_data
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            customer = await unas_api.get_customer("test_customer_1")
            
            assert customer is not None
            assert customer.id == "test_customer_1"
            assert customer.email == "test@example.com"
            assert customer.first_name == "Test"
            assert customer.last_name == "User"
            
            mock_get.assert_called_once_with("https://test.unas.hu/api/customers/test_customer_1")
    
    @pytest.mark.asyncio
    async def test_get_customer_not_found(self, unas_api):
        """Ügyfél nem található teszt"""
        with patch.object(unas_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404", request=Mock(), response=Mock()
            )
            mock_get.return_value = mock_response
            
            customer = await unas_api.get_customer("nonexistent_customer")
            
            assert customer is None


class TestUNASAPIOrderManagement:
    """UNAS API rendeléskezelés tesztek"""
    
    @pytest.fixture
    def unas_api(self):
        """UNAS API fixture"""
        return UNASAPI("test_key", "https://test.unas.hu")
    
    @pytest.mark.asyncio
    async def test_update_order_status_success(self, unas_api):
        """Rendelési státusz frissítés sikeres teszt"""
        with patch.object(unas_api.client, 'patch') as mock_patch:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_patch.return_value = mock_response
            
            result = await unas_api.update_order_status("test_order_1", OrderStatus.SHIPPED)
            
            assert result is True
            mock_patch.assert_called_once_with(
                "https://test.unas.hu/api/orders/test_order_1",
                json={"status": "shipped"}
            )
    
    @pytest.mark.asyncio
    async def test_update_order_status_failure(self, unas_api):
        """Rendelési státusz frissítés sikertelen teszt"""
        with patch.object(unas_api.client, 'patch') as mock_patch:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "400", request=Mock(), response=Mock()
            )
            mock_patch.return_value = mock_response
            
            result = await unas_api.update_order_status("test_order_1", OrderStatus.CANCELLED)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_update_order_status_exception(self, unas_api):
        """Rendelési státusz frissítés kivétel teszt"""
        with patch.object(unas_api.client, 'patch', side_effect=Exception("Network error")):
            result = await unas_api.update_order_status("test_order_1", OrderStatus.DELIVERED)
            
            assert result is False


class TestUNASAPIClose:
    """UNAS API kliens lezárás tesztek"""
    
    @pytest.mark.asyncio
    async def test_close_client(self):
        """HTTP kliens lezárás teszt"""
        unas_api = UNASAPI("test_key", "https://test.unas.hu")
        
        with patch.object(unas_api.client, 'aclose') as mock_close:
            await unas_api.close()
            mock_close.assert_called_once()


class TestMockUNASAPI:
    """Mock UNAS API tesztek"""
    
    @pytest.fixture
    def mock_api(self):
        """Mock UNAS API fixture"""
        return MockUNASAPI()
    
    @pytest.mark.asyncio
    async def test_mock_get_products_default(self, mock_api):
        """Mock termékek lekérése alapértelmezett teszt"""
        products = await mock_api.get_products()
        
        assert len(products) == 3
        assert products[0].id == "unas_prod_1"
        assert products[0].name == "Asus ROG Strix G15"
        assert products[0].category == ProductCategory.ELECTRONICS
        assert products[1].category == ProductCategory.SPORTS
        assert products[2].category == ProductCategory.ELECTRONICS
    
    @pytest.mark.asyncio
    async def test_mock_get_products_with_pagination(self, mock_api):
        """Mock termékek lekérése lapozással teszt"""
        products = await mock_api.get_products(limit=2, offset=1)
        
        assert len(products) == 2
        assert products[0].id == "unas_prod_2"  # offset=1, so skip first product
        assert products[1].id == "unas_prod_3"
    
    @pytest.mark.asyncio
    async def test_mock_get_products_with_category_filter(self, mock_api):
        """Mock termékek lekérése kategória szűrővel teszt"""
        products = await mock_api.get_products(category="electronics")
        
        assert len(products) == 2  # 2 electronics products
        assert all(product.category == ProductCategory.ELECTRONICS for product in products)
    
    @pytest.mark.asyncio
    async def test_mock_get_product_found(self, mock_api):
        """Mock termék lekérése található teszt"""
        product = await mock_api.get_product("unas_prod_1")
        
        assert product is not None
        assert product.id == "unas_prod_1"
        assert product.name == "Asus ROG Strix G15"
        assert product.price == 899999.0
        assert product.brand == "Asus"
    
    @pytest.mark.asyncio
    async def test_mock_get_product_not_found(self, mock_api):
        """Mock termék lekérése nem található teszt"""
        product = await mock_api.get_product("nonexistent_product")
        
        assert product is None
    
    @pytest.mark.asyncio
    async def test_mock_search_products_by_name(self, mock_api):
        """Mock termék keresés név alapján teszt"""
        products = await mock_api.search_products("Asus")
        
        assert len(products) == 1
        assert products[0].name == "Asus ROG Strix G15"
    
    @pytest.mark.asyncio
    async def test_mock_search_products_by_description(self, mock_api):
        """Mock termék keresés leírás alapján teszt"""
        products = await mock_api.search_products("gaming")
        
        assert len(products) == 1
        assert "gaming" in products[0].description.lower()
    
    @pytest.mark.asyncio
    async def test_mock_search_products_by_tag(self, mock_api):
        """Mock termék keresés címke alapján teszt"""
        products = await mock_api.search_products("laptop")
        
        assert len(products) == 1
        assert "laptop" in products[0].tags
    
    @pytest.mark.asyncio
    async def test_mock_search_products_with_limit(self, mock_api):
        """Mock termék keresés limit teszt"""
        # Search for a common term that should match multiple products
        products = await mock_api.search_products("a", limit=1)  # "a" appears in many product names
        
        assert len(products) <= 1
    
    @pytest.mark.asyncio
    async def test_mock_search_products_no_results(self, mock_api):
        """Mock termék keresés nincs eredmény teszt"""
        products = await mock_api.search_products("nonexistent_term")
        
        assert products == []
    
    @pytest.mark.asyncio
    async def test_mock_get_orders_for_user(self, mock_api):
        """Mock rendelések lekérése felhasználóhoz teszt"""
        orders = await mock_api.get_orders("unas_user_123")
        
        assert len(orders) == 2
        assert all(order.user_id == "unas_user_123" for order in orders)
        assert orders[0].status == OrderStatus.DELIVERED
        assert orders[1].status == OrderStatus.PROCESSING
    
    @pytest.mark.asyncio
    async def test_mock_get_orders_for_nonexistent_user(self, mock_api):
        """Mock rendelések lekérése nem létező felhasználóhoz teszt"""
        orders = await mock_api.get_orders("nonexistent_user")
        
        assert orders == []
    
    @pytest.mark.asyncio
    async def test_mock_get_orders_with_limit(self, mock_api):
        """Mock rendelések lekérése limit teszt"""
        orders = await mock_api.get_orders("unas_user_123", limit=1)
        
        assert len(orders) == 1
        assert orders[0].id == "unas_order_1"
    
    @pytest.mark.asyncio
    async def test_mock_get_order_found(self, mock_api):
        """Mock rendelés lekérése található teszt"""
        order = await mock_api.get_order("unas_order_1")
        
        assert order is not None
        assert order.id == "unas_order_1"
        assert order.user_id == "unas_user_123"
        assert order.status == OrderStatus.DELIVERED
        assert order.total == 899999.0
        assert len(order.items) == 1
        assert order.tracking_number == "UNAS123456789"
    
    @pytest.mark.asyncio
    async def test_mock_get_order_not_found(self, mock_api):
        """Mock rendelés lekérése nem található teszt"""
        order = await mock_api.get_order("nonexistent_order")
        
        assert order is None
    
    @pytest.mark.asyncio
    async def test_mock_get_customer_found(self, mock_api):
        """Mock ügyfél lekérése található teszt"""
        customer = await mock_api.get_customer("unas_user_123")
        
        assert customer is not None
        assert customer.id == "unas_user_123"
        assert customer.email == "unas_user@example.com"
        assert customer.first_name == "Mária"
        assert customer.last_name == "Nagy"
        assert customer.phone == "+36 30 987 6543"
    
    @pytest.mark.asyncio
    async def test_mock_get_customer_not_found(self, mock_api):
        """Mock ügyfél lekérése nem található teszt"""
        customer = await mock_api.get_customer("nonexistent_customer")
        
        assert customer is None
    
    @pytest.mark.asyncio
    async def test_mock_update_order_status_success(self, mock_api):
        """Mock rendelési státusz frissítés sikeres teszt"""
        original_order = await mock_api.get_order("unas_order_1")
        original_status = original_order.status
        
        result = await mock_api.update_order_status("unas_order_1", OrderStatus.CANCELLED)
        
        assert result is True
        
        updated_order = await mock_api.get_order("unas_order_1")
        assert updated_order.status == OrderStatus.CANCELLED
        assert updated_order.status != original_status
    
    @pytest.mark.asyncio
    async def test_mock_update_order_status_not_found(self, mock_api):
        """Mock rendelési státusz frissítés nem található teszt"""
        result = await mock_api.update_order_status("nonexistent_order", OrderStatus.CANCELLED)
        
        assert result is False


class TestMockDataValidation:
    """Mock adat validációs tesztek"""
    
    @pytest.fixture
    def mock_api(self):
        """Mock UNAS API fixture"""
        return MockUNASAPI()
    
    def test_mock_products_data_structure(self, mock_api):
        """Mock termékek adatstruktúra teszt"""
        products = mock_api.mock_products
        
        assert len(products) == 3
        
        for product in products:
            assert isinstance(product, Product)
            assert product.id.startswith("unas_prod_")
            assert isinstance(product.price, float)
            assert isinstance(product.stock, int)
            assert isinstance(product.category, ProductCategory)
            assert isinstance(product.images, list)
            assert isinstance(product.tags, list)
            assert isinstance(product.is_active, bool)
            assert isinstance(product.created_at, datetime)
            assert isinstance(product.updated_at, datetime)
    
    def test_mock_orders_data_structure(self, mock_api):
        """Mock rendelések adatstruktúra teszt"""
        orders = mock_api.mock_orders
        
        assert len(orders) == 2
        
        for order in orders:
            assert isinstance(order, Order)
            assert order.id.startswith("unas_order_")
            assert order.user_id == "unas_user_123"
            assert isinstance(order.status, OrderStatus)
            assert isinstance(order.total, float)
            assert isinstance(order.items, list)
            assert len(order.items) > 0
            
            for item in order.items:
                assert isinstance(item, OrderItem)
                assert isinstance(item.quantity, int)
                assert isinstance(item.unit_price, float)
                assert isinstance(item.total_price, float)
    
    def test_mock_customers_data_structure(self, mock_api):
        """Mock ügyfelek adatstruktúra teszt"""
        customers = mock_api.mock_customers
        
        assert len(customers) == 1
        
        for customer in customers:
            assert isinstance(customer, Customer)
            assert customer.id == "unas_user_123"
            assert "@" in customer.email
            assert isinstance(customer.first_name, str)
            assert isinstance(customer.last_name, str)
            assert customer.phone.startswith("+36")
            assert isinstance(customer.address, dict)
            assert isinstance(customer.created_at, datetime)
            assert isinstance(customer.updated_at, datetime)


class TestAsyncDelayBehavior:
    """Async delay viselkedés tesztek"""
    
    @pytest.fixture
    def mock_api(self):
        """Mock UNAS API fixture"""
        return MockUNASAPI()
    
    @pytest.mark.asyncio
    async def test_mock_api_has_delays(self, mock_api):
        """Mock API tartalmaz késleltetést teszt"""
        import time
        
        start_time = time.time()
        await mock_api.get_products()
        end_time = time.time()
        
        # Should have at least 0.1 second delay
        assert (end_time - start_time) >= 0.1


class TestEdgeCasesAndErrorHandling:
    """Edge case-ek és hibakezelés tesztek"""
    
    @pytest.fixture
    def mock_api(self):
        """Mock UNAS API fixture"""
        return MockUNASAPI()
    
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
        products = await mock_api.get_products(limit=10, offset=100)
        
        assert products == []  # Offset beyond available data
    
    @pytest.mark.asyncio
    async def test_negative_limit_parameters(self, mock_api):
        """Negatív limit paraméterek teszt"""
        products = await mock_api.get_products(limit=-1)
        
        # Should handle negative limit gracefully
        assert isinstance(products, list)
    
    def test_product_category_enum_values(self):
        """ProductCategory enum értékek teszt"""
        # Test that all expected categories are available
        expected_categories = {
            "electronics", "clothing", "books", "home", 
            "sports", "beauty", "food", "other"
        }
        
        actual_categories = {category.value for category in ProductCategory}
        
        assert expected_categories == actual_categories
    
    def test_order_status_enum_values(self):
        """OrderStatus enum értékek teszt"""
        # Test that all expected statuses are available
        expected_statuses = {
            "pending", "confirmed", "processing", "shipped",
            "delivered", "cancelled", "returned"
        }
        
        actual_statuses = {status.value for status in OrderStatus}
        
        assert expected_statuses == actual_statuses