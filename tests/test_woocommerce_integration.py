"""
WooCommerce webshop integration tesztek - woocommerce.py lefedettség növelése
"""
import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import List, Optional

from src.integrations.webshop.woocommerce import WooCommerceAPI, MockWooCommerceAPI
from src.integrations.webshop.base import (
    Product, Order, Customer, OrderStatus, ProductCategory, OrderItem
)


class TestWooCommerceAPIInitialization:
    """WooCommerceAPI inicializálás tesztek"""
    
    def test_woocommerce_api_initialization(self):
        """WooCommerce API inicializálás teszt"""
        api_key = "test_key"
        base_url = "https://test-store.example.com"
        
        api = WooCommerceAPI(api_key, base_url)
        
        assert api.api_key == api_key
        assert api.base_url == base_url
        assert api.client is not None
        assert api.client.headers["Authorization"] == f"Bearer {api_key}"
        assert api.client.headers["Content-Type"] == "application/json"
        
        # Timeout objektum helyes összehasonlítása
        assert str(api.client.timeout) == "Timeout(timeout=30.0)"  # Teljes string formátum
    
    def test_woocommerce_api_base_url_strip(self):
        """WooCommerce API base URL strip teszt"""
        api_key = "test_key"
        base_url = "https://test-store.com/"
        
        api = WooCommerceAPI(api_key, base_url)
        
        assert api.base_url == "https://test-store.com"
    
    def test_mock_woocommerce_api_initialization(self):
        """Mock WooCommerce API inicializálás teszt"""
        mock_api = MockWooCommerceAPI()
        
        assert len(mock_api.mock_products) == 4
        assert len(mock_api.mock_orders) == 2
        assert len(mock_api.mock_customers) == 2


class TestWooCommerceAPIProducts:
    """WooCommerce API termék metódusok tesztek"""
    
    @pytest.fixture
    def woocommerce_api(self):
        """WooCommerce API fixture"""
        return WooCommerceAPI("test_key", "https://test-store.com")
    
    @pytest.fixture
    def mock_woocommerce_product_response(self):
        """Mock WooCommerce termék válasz"""
        return [
            {
                "id": 101,
                "name": "Test WooCommerce Product",
                "description": "Test product description",
                "price": "199.99",
                "status": "publish",
                "stock_quantity": 20,
                "images": [
                    "https://example.com/woocommerce-product1.jpg",
                    "https://example.com/woocommerce-product2.jpg"
                ],
                "attributes": ["color", "size"]
            },
            {
                "id": 102,
                "name": "Another Test Product",
                "description": "Another description",
                "price": "99.99",
                "status": "publish",
                "stock_quantity": 15,
                "images": [],
                "attributes": ["style"]
            }
        ]
    
    @pytest.mark.asyncio
    async def test_get_products_success(self, woocommerce_api, mock_woocommerce_product_response):
        """Termékek lekérése sikeres teszt"""
        with patch.object(woocommerce_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_woocommerce_product_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            products = await woocommerce_api.get_products(limit=10, offset=0)
            
            assert len(products) == 2
            assert products[0].id == "101"
            assert products[0].name == "Test WooCommerce Product"
            assert products[0].price == 199.99
            assert products[0].stock == 20
            assert products[0].category == ProductCategory.ELECTRONICS
            assert len(products[0].images) == 2
            assert products[0].is_active is True
            
            mock_get.assert_called_once_with(
                "https://test-store.com/wp-json/wc/v3/products",
                params={"per_page": 10, "offset": 0}
            )
    
    @pytest.mark.asyncio
    async def test_get_products_with_category(self, woocommerce_api, mock_woocommerce_product_response):
        """Termékek lekérése kategóriával teszt"""
        with patch.object(woocommerce_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_woocommerce_product_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            products = await woocommerce_api.get_products(limit=10, offset=0, category="electronics")
            
            mock_get.assert_called_once_with(
                "https://test-store.com/wp-json/wc/v3/products",
                params={"per_page": 10, "offset": 0, "category": "electronics"}
            )
    
    @pytest.mark.asyncio
    async def test_get_products_exception(self, woocommerce_api):
        """Termékek lekérése kivétel teszt"""
        with patch.object(woocommerce_api.client, 'get', side_effect=httpx.HTTPStatusError("404", request=Mock(), response=Mock())):
            with pytest.raises(Exception, match="WooCommerce API hiba"):
                await woocommerce_api.get_products()
    
    @pytest.mark.asyncio
    async def test_get_product_success(self, woocommerce_api):
        """Egy termék lekérése sikeres teszt"""
        mock_product_response = {
            "id": 101,
            "name": "Single Test Product",
            "description": "Single product description",
            "price": "299.99",
            "status": "publish",
            "stock_quantity": 30,
            "images": [
                "https://example.com/single-product.jpg"
            ],
            "attributes": ["color"]
        }
        
        with patch.object(woocommerce_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_product_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            product = await woocommerce_api.get_product("101")
            
            assert product is not None
            assert product.id == "101"
            assert product.name == "Single Test Product"
            assert product.price == 299.99
            assert product.stock == 30
            
            mock_get.assert_called_once_with(
                "https://test-store.com/wp-json/wc/v3/products/101"
            )
    
    @pytest.mark.asyncio
    async def test_get_product_exception(self, woocommerce_api):
        """Egy termék lekérése kivétel teszt"""
        with patch.object(woocommerce_api.client, 'get', side_effect=Exception("Network error")):
            with pytest.raises(Exception, match="WooCommerce API hiba"):
                await woocommerce_api.get_product("101")
    
    @pytest.mark.asyncio
    async def test_search_products_success(self, woocommerce_api, mock_woocommerce_product_response):
        """Termék keresés sikeres teszt"""
        with patch.object(woocommerce_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_woocommerce_product_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            products = await woocommerce_api.search_products("test", limit=5)
            
            assert len(products) == 2
            
            mock_get.assert_called_once_with(
                "https://test-store.com/wp-json/wc/v3/products",
                params={"search": "test", "per_page": 5}
            )
    
    @pytest.mark.asyncio
    async def test_search_products_exception(self, woocommerce_api):
        """Termék keresés kivétel teszt"""
        with patch.object(woocommerce_api.client, 'get', side_effect=Exception("Search error")):
            with pytest.raises(Exception, match="WooCommerce API hiba"):
                await woocommerce_api.search_products("test")


class TestWooCommerceAPIOrders:
    """WooCommerce API rendelés metódusok tesztek"""
    
    @pytest.fixture
    def woocommerce_api(self):
        """WooCommerce API fixture"""
        return WooCommerceAPI("test_key", "https://test-store.com")
    
    @pytest.fixture
    def mock_woocommerce_order_response(self):
        """Mock WooCommerce rendelés válasz"""
        return [
            {
                "id": 501,
                "customer_id": 301,
                "total": "399.98",
                "currency": "HUF",
                "line_items": [
                    {
                        "product_id": 101,
                        "name": "Test Product A",
                        "quantity": 1,
                        "price": "199.99",
                        "total": "199.99"
                    },
                    {
                        "product_id": 102,
                        "name": "Test Product B",
                        "quantity": 2,
                        "price": "100.00",
                        "total": "200.00"
                    }
                ],
                "shipping": {
                    "city": "Budapest",
                    "postcode": "1111"
                },
                "billing": {
                    "city": "Budapest",
                    "postcode": "1111"
                },
                "customer_note": "Test order note"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_get_orders_success(self, woocommerce_api, mock_woocommerce_order_response):
        """Rendelések lekérése sikeres teszt"""
        with patch.object(woocommerce_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_woocommerce_order_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            orders = await woocommerce_api.get_orders(limit=10, offset=0)
            
            assert len(orders) == 1
            assert orders[0].id == "501"
            assert orders[0].user_id == "301"
            assert orders[0].status == OrderStatus.PROCESSING
            assert orders[0].total == 399.98
            assert orders[0].currency == "HUF"
            assert len(orders[0].items) == 2
            assert orders[0].notes == "Test order note"
            
            # Check order items
            assert orders[0].items[0].product_id == "101"
            assert orders[0].items[0].product_name == "Test Product A"
            assert orders[0].items[0].quantity == 1
            assert orders[0].items[0].unit_price == 199.99
            assert orders[0].items[0].total_price == 199.99
            
            mock_get.assert_called_once_with(
                "https://test-store.com/wp-json/wc/v3/orders",
                params={"per_page": 10, "offset": 0}
            )
    
    @pytest.mark.asyncio
    async def test_get_orders_exception(self, woocommerce_api):
        """Rendelések lekérése kivétel teszt"""
        with patch.object(woocommerce_api.client, 'get', side_effect=Exception("Orders error")):
            with pytest.raises(Exception, match="WooCommerce API hiba"):
                await woocommerce_api.get_orders()
    
    @pytest.mark.asyncio
    async def test_get_order_success(self, woocommerce_api):
        """Egy rendelés lekérése sikeres teszt"""
        mock_single_order_response = {
            "id": 501,
            "customer_id": 301,
            "total": "299.99",
            "currency": "HUF",
            "line_items": [
                {
                    "product_id": 101,
                    "name": "Single Order Product",
                    "quantity": 3,
                    "price": "99.99",
                    "total": "299.97"
                }
            ],
            "shipping": {
                "city": "Debrecen",
                "postcode": "4000"
            },
            "billing": {
                "city": "Debrecen",
                "postcode": "4000"
            },
            "customer_note": "Single order note"
        }
        
        with patch.object(woocommerce_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_single_order_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            order = await woocommerce_api.get_order("501")
            
            assert order is not None
            assert order.id == "501"
            assert order.user_id == "301"
            assert order.total == 299.99
            assert order.currency == "HUF"
            assert len(order.items) == 1
            assert order.items[0].quantity == 3
            assert order.items[0].total_price == 299.97
            
            mock_get.assert_called_once_with(
                "https://test-store.com/wp-json/wc/v3/orders/501"
            )
    
    @pytest.mark.asyncio
    async def test_get_order_exception(self, woocommerce_api):
        """Egy rendelés lekérése kivétel teszt"""
        with patch.object(woocommerce_api.client, 'get', side_effect=Exception("Order error")):
            with pytest.raises(Exception, match="WooCommerce API hiba"):
                await woocommerce_api.get_order("501")


class TestWooCommerceAPICustomers:
    """WooCommerce API ügyfél metódusok tesztek"""
    
    @pytest.fixture
    def woocommerce_api(self):
        """WooCommerce API fixture"""
        return WooCommerceAPI("test_key", "https://test-store.com")
    
    @pytest.mark.asyncio
    async def test_get_customer_success(self, woocommerce_api):
        """Ügyfél lekérése sikeres teszt"""
        mock_customer_response = {
            "id": 301,
            "email": "test@woocommerce.com",
            "first_name": "Test",
            "last_name": "Customer",
            "billing": {
                "phone": "+36301234567",
                "city": "Budapest",
                "postcode": "1111"
            }
        }
        
        with patch.object(woocommerce_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_customer_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            customer = await woocommerce_api.get_customer("301")
            
            assert customer is not None
            assert customer.id == "301"
            assert customer.email == "test@woocommerce.com"
            assert customer.first_name == "Test"
            assert customer.last_name == "Customer"
            assert customer.phone == "+36301234567"
            assert customer.address == {"phone": "+36301234567", "city": "Budapest", "postcode": "1111"}
            
            mock_get.assert_called_once_with(
                "https://test-store.com/wp-json/wc/v3/customers/301"
            )
    
    @pytest.mark.asyncio
    async def test_get_customer_exception(self, woocommerce_api):
        """Ügyfél lekérése kivétel teszt"""
        with patch.object(woocommerce_api.client, 'get', side_effect=Exception("Customer error")):
            with pytest.raises(Exception, match="WooCommerce API hiba"):
                await woocommerce_api.get_customer("301")


class TestWooCommerceAPIOrderManagement:
    """WooCommerce API rendeléskezelés tesztek"""
    
    @pytest.fixture
    def woocommerce_api(self):
        """WooCommerce API fixture"""
        return WooCommerceAPI("test_key", "https://test-store.com")
    
    @pytest.mark.asyncio
    async def test_update_order_status_success(self, woocommerce_api):
        """Rendelési státusz frissítés sikeres teszt"""
        with patch.object(woocommerce_api.client, 'put') as mock_put:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_put.return_value = mock_response
            
            result = await woocommerce_api.update_order_status("501", "completed")
            
            assert result is True
            mock_put.assert_called_once_with(
                "https://test-store.com/wp-json/wc/v3/orders/501",
                json={"status": "completed"}
            )
    
    @pytest.mark.asyncio
    async def test_update_order_status_exception(self, woocommerce_api):
        """Rendelési státusz frissítés kivétel teszt"""
        with patch.object(woocommerce_api.client, 'put', side_effect=Exception("Update error")):
            with pytest.raises(Exception, match="WooCommerce API hiba"):
                await woocommerce_api.update_order_status("501", "completed")


class TestWooCommerceAPIClose:
    """WooCommerce API kliens lezárás tesztek"""
    
    @pytest.mark.asyncio
    async def test_close_client(self):
        """HTTP kliens lezárás teszt"""
        woocommerce_api = WooCommerceAPI("test_key", "https://test-store.com")
        
        with patch.object(woocommerce_api.client, 'aclose') as mock_close:
            await woocommerce_api.close()
            mock_close.assert_called_once()


class TestMockWooCommerceAPI:
    """Mock WooCommerce API tesztek"""
    
    @pytest.fixture
    def mock_api(self):
        """Mock WooCommerce API fixture"""
        return MockWooCommerceAPI()
    
    @pytest.mark.asyncio
    async def test_mock_get_products_default(self, mock_api):
        """Mock termékek lekérése alapértelmezett teszt"""
        products = await mock_api.get_products()
        
        assert len(products) == 4
        assert products[0].id == "1"
        assert products[0].name == "iPhone 15 Pro"
        assert products[0].category == ProductCategory.ELECTRONICS
        assert products[1].name == "Samsung Galaxy S24"
        assert products[1].category == ProductCategory.ELECTRONICS
        assert products[2].name == "Nike Air Max 270"
        assert products[2].category == ProductCategory.SPORTS
        assert products[3].name == "MacBook Pro 14"
        assert products[3].category == ProductCategory.ELECTRONICS
    
    @pytest.mark.asyncio
    async def test_mock_get_products_with_pagination(self, mock_api):
        """Mock termékek lekérése lapozással teszt"""
        products = await mock_api.get_products(limit=2, offset=1)
        
        assert len(products) == 2
        assert products[0].id == "2"  # offset=1, skip first product
        assert products[1].id == "3"
    
    @pytest.mark.asyncio
    async def test_mock_get_products_with_category_filter(self, mock_api):
        """Mock termékek lekérése kategória szűrővel teszt"""
        products = await mock_api.get_products(category="electronics")
        
        electronics_products = [p for p in products if p.category == ProductCategory.ELECTRONICS]
        assert len(electronics_products) == 3  # iPhone, Samsung, MacBook are electronics
    
    @pytest.mark.asyncio
    async def test_mock_get_product_found(self, mock_api):
        """Mock termék lekérése található teszt"""
        product = await mock_api.get_product("1")
        
        assert product is not None
        assert product.id == "1"
        assert product.name == "iPhone 15 Pro"
        assert product.price == 499999.0
        assert product.stock == 15
    
    @pytest.mark.asyncio
    async def test_mock_get_product_not_found(self, mock_api):
        """Mock termék lekérése nem található teszt"""
        product = await mock_api.get_product("nonexistent")
        
        assert product is None
    
    @pytest.mark.asyncio
    async def test_mock_search_products_by_name(self, mock_api):
        """Mock termék keresés név alapján teszt"""
        products = await mock_api.search_products("iPhone")
        
        assert len(products) == 1
        assert products[0].name == "iPhone 15 Pro"
    
    @pytest.mark.asyncio
    async def test_mock_search_products_by_description(self, mock_api):
        """Mock termék keresés leírás alapján teszt"""
        products = await mock_api.search_products("Apple")
        
        # Should find both iPhone and MacBook (both have Apple in description)
        assert len(products) == 2
        apple_products = [p for p in products if "apple" in p.description.lower()]
        assert len(apple_products) == 2
    
    @pytest.mark.asyncio
    async def test_mock_search_products_with_limit(self, mock_api):
        """Mock termék keresés limit teszt"""
        # Search for common term that appears in multiple products
        products = await mock_api.search_products("a", limit=2)  # "a" appears in many names
        
        assert len(products) <= 2
    
    @pytest.mark.asyncio
    async def test_mock_search_products_no_results(self, mock_api):
        """Mock termék keresés nincs eredmény teszt"""
        products = await mock_api.search_products("nonexistent_term")
        
        assert products == []
    
    @pytest.mark.asyncio
    async def test_mock_get_orders_default(self, mock_api):
        """Mock rendelések lekérése alapértelmezett teszt"""
        orders = await mock_api.get_orders()
        
        assert len(orders) == 2
        assert orders[0].id == "1001"
        assert orders[0].user_id == "2001"
        assert orders[0].status == OrderStatus.PROCESSING
        assert orders[1].id == "1002"
        assert orders[1].status == OrderStatus.DELIVERED
    
    @pytest.mark.asyncio
    async def test_mock_get_orders_with_pagination(self, mock_api):
        """Mock rendelések lekérése lapozással teszt"""
        orders = await mock_api.get_orders(limit=1, offset=1)
        
        assert len(orders) == 1
        assert orders[0].id == "1002"
    
    @pytest.mark.asyncio
    async def test_mock_get_order_found(self, mock_api):
        """Mock rendelés lekérése található teszt"""
        order = await mock_api.get_order("1001")
        
        assert order is not None
        assert order.id == "1001"
        assert order.user_id == "2001"
        assert order.status == OrderStatus.PROCESSING
        assert order.total == 589998.0
        assert len(order.items) == 2
        assert order.items[0].product_name == "iPhone 15 Pro"
        assert order.items[1].product_name == "Nike Air Max 270"
    
    @pytest.mark.asyncio
    async def test_mock_get_order_not_found(self, mock_api):
        """Mock rendelés lekérése nem található teszt"""
        order = await mock_api.get_order("nonexistent")
        
        assert order is None
    
    @pytest.mark.asyncio
    async def test_mock_get_customer_found(self, mock_api):
        """Mock ügyfél lekérése található teszt"""
        customer = await mock_api.get_customer("2001")
        
        assert customer is not None
        assert customer.id == "2001"
        assert customer.email == "kiss.janos@example.com"
        assert customer.first_name == "János"
        assert customer.last_name == "Kiss"
        assert customer.phone == "+36201234567"
    
    @pytest.mark.asyncio
    async def test_mock_get_customer_not_found(self, mock_api):
        """Mock ügyfél lekérése nem található teszt"""
        customer = await mock_api.get_customer("nonexistent")
        
        assert customer is None
    
    @pytest.mark.asyncio
    async def test_mock_update_order_status_success(self, mock_api):
        """Mock rendelési státusz frissítés sikeres teszt"""
        original_order = await mock_api.get_order("1001")
        original_status = original_order.status
        
        result = await mock_api.update_order_status("1001", "completed")
        
        assert result is True
        
        updated_order = await mock_api.get_order("1001")
        assert updated_order.status == OrderStatus.DELIVERED
        assert updated_order.status != original_status
    
    @pytest.mark.asyncio
    async def test_mock_update_order_status_not_found(self, mock_api):
        """Mock rendelési státusz frissítés nem található teszt"""
        result = await mock_api.update_order_status("nonexistent", "completed")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_mock_update_order_status_mapping(self, mock_api):
        """Mock rendelési státusz mapping teszt"""
        # Test different status mappings
        await mock_api.update_order_status("1001", "completed")
        order = await mock_api.get_order("1001")
        assert order.status == OrderStatus.DELIVERED
        
        await mock_api.update_order_status("1001", "processing")
        order = await mock_api.get_order("1001")
        assert order.status == OrderStatus.PROCESSING
        
        await mock_api.update_order_status("1001", "pending")
        order = await mock_api.get_order("1001")
        assert order.status == OrderStatus.PENDING
        
        # Test unknown status defaults to PROCESSING
        await mock_api.update_order_status("1001", "unknown_status")
        order = await mock_api.get_order("1001")
        assert order.status == OrderStatus.PROCESSING
    
    @pytest.mark.asyncio
    async def test_mock_close(self, mock_api):
        """Mock close metódus teszt"""
        # Should not raise exception
        await mock_api.close()


class TestMockDataValidation:
    """Mock adat validációs tesztek"""
    
    @pytest.fixture
    def mock_api(self):
        """Mock WooCommerce API fixture"""
        return MockWooCommerceAPI()
    
    def test_mock_products_data_structure(self, mock_api):
        """Mock termékek adatstruktúra teszt"""
        products = mock_api.mock_products
        
        assert len(products) == 4
        
        for product in products:
            assert isinstance(product, Product)
            assert product.id in ["1", "2", "3", "4"]
            assert isinstance(product.price, float)
            assert isinstance(product.stock, int)
            assert isinstance(product.category, ProductCategory)
            assert product.currency == "HUF"
            assert isinstance(product.images, list)
            assert isinstance(product.tags, list)
            assert isinstance(product.is_active, bool)
            assert product.is_active is True  # All mock products are active
    
    def test_mock_orders_data_structure(self, mock_api):
        """Mock rendelések adatstruktúra teszt"""
        orders = mock_api.mock_orders
        
        assert len(orders) == 2
        
        for order in orders:
            assert isinstance(order, Order)
            assert order.id in ["1001", "1002"]
            assert order.user_id in ["2001", "2002"]
            assert isinstance(order.status, OrderStatus)
            assert isinstance(order.total, float)
            assert order.currency == "HUF"
            assert isinstance(order.items, list)
            assert len(order.items) >= 1
            
            for item in order.items:
                assert isinstance(item, OrderItem)
                assert isinstance(item.quantity, int)
                assert isinstance(item.unit_price, float)
                assert isinstance(item.total_price, float)
    
    def test_mock_customers_data_structure(self, mock_api):
        """Mock ügyfelek adatstruktúra teszt"""
        customers = mock_api.mock_customers
        
        assert len(customers) == 2
        
        for customer in customers:
            assert isinstance(customer, Customer)
            assert customer.id in ["2001", "2002"]
            assert "@" in customer.email
            assert isinstance(customer.first_name, str)
            assert isinstance(customer.last_name, str)
            assert customer.phone.startswith("+36")
            assert isinstance(customer.address, dict)


class TestAsyncDelayBehavior:
    """Async delay viselkedés tesztek"""
    
    @pytest.fixture
    def mock_api(self):
        """Mock WooCommerce API fixture"""
        return MockWooCommerceAPI()
    
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
        """Mock WooCommerce API fixture"""
        return MockWooCommerceAPI()
    
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
    
    def test_woocommerce_specific_features(self, mock_api):
        """WooCommerce-specifikus funkciók teszt"""
        # Check that products have WooCommerce-like structure
        products = mock_api.mock_products
        
        # All products should have proper IDs (string format)
        for product in products:
            assert isinstance(product.id, str)
            assert product.id.isdigit()
        
        # Check orders have proper structure
        orders = mock_api.mock_orders
        for order in orders:
            assert isinstance(order.id, str)
            assert order.id.isdigit()
            assert order.currency == "HUF"
        
        # Check that WooCommerce products have expected brands/names
        product_names = [p.name for p in products]
        assert "iPhone 15 Pro" in product_names
        assert "Samsung Galaxy S24" in product_names
        assert "Nike Air Max 270" in product_names
        assert "MacBook Pro 14" in product_names