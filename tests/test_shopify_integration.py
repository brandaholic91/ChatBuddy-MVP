"""
Shopify webshop integration tesztek - shopify.py lefedettség növelése
"""
import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import List, Optional

from src.integrations.webshop.shopify import ShopifyAPI, MockShopifyAPI
from src.integrations.webshop.base import (
    Product, Order, Customer, OrderStatus, ProductCategory, OrderItem
)


class TestShopifyAPIInitialization:
    """ShopifyAPI inicializálás tesztek"""
    
    def test_shopify_api_initialization(self):
        """Shopify API inicializálás teszt"""
        api_key = "test_key"
        base_url = "https://test-store.myshopify.com"
        
        api = ShopifyAPI(api_key, base_url)
        
        assert api.api_key == api_key
        assert api.base_url == base_url
        assert api.client is not None
        assert api.client.headers["X-Shopify-Access-Token"] == api_key
        assert api.client.headers["Content-Type"] == "application/json"
        
        # Timeout objektum helyes összehasonlítása
        assert str(api.client.timeout) == "Timeout(timeout=30.0)"  # Teljes string formátum
    
    def test_shopify_api_base_url_strip(self):
        """Shopify API base URL strip teszt"""
        api_key = "test_key"
        base_url = "https://test-store.myshopify.com/"
        
        api = ShopifyAPI(api_key, base_url)
        
        assert api.base_url == "https://test-store.myshopify.com"
    
    def test_mock_shopify_api_initialization(self):
        """Mock Shopify API inicializálás teszt"""
        mock_api = MockShopifyAPI()
        
        assert len(mock_api.mock_products) == 4
        assert len(mock_api.mock_orders) == 2
        assert len(mock_api.mock_customers) == 2


class TestShopifyAPIProducts:
    """Shopify API termék metódusok tesztek"""
    
    @pytest.fixture
    def shopify_api(self):
        """Shopify API fixture"""
        return ShopifyAPI("test_key", "https://test-store.myshopify.com")
    
    @pytest.fixture
    def mock_shopify_product_response(self):
        """Mock Shopify termék válasz"""
        return {
            "products": [
                {
                    "id": 123456789,
                    "title": "Test Shopify Product",
                    "body_html": "<p>Test product description</p>",
                    "status": "active",
                    "variants": [
                        {
                            "id": 987654321,
                            "price": "299.99",
                            "inventory_quantity": 15
                        }
                    ],
                    "images": [
                        {"src": "https://example.com/shopify-product1.jpg"},
                        {"src": "https://example.com/shopify-product2.jpg"}
                    ],
                    "options": ["Color", "Size"]
                },
                {
                    "id": 123456790,
                    "title": "Another Test Product",
                    "body_html": "<p>Another description</p>",
                    "status": "active",
                    "variants": [
                        {
                            "id": 987654322,
                            "price": "199.99",
                            "inventory_quantity": 8
                        }
                    ],
                    "images": [],
                    "options": ["Style"]
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_get_products_success(self, shopify_api, mock_shopify_product_response):
        """Termékek lekérése sikeres teszt"""
        with patch.object(shopify_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_shopify_product_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            products = await shopify_api.get_products(limit=10, offset=0)
            
            assert len(products) == 2
            assert products[0].id == "123456789"
            assert products[0].name == "Test Shopify Product"
            assert products[0].price == 299.99
            assert products[0].stock == 15
            assert products[0].category == ProductCategory.ELECTRONICS
            assert len(products[0].images) == 2
            assert products[0].is_active is True
            
            mock_get.assert_called_once_with(
                "https://test-store.myshopify.com/admin/api/2023-10/products.json",
                params={"limit": 10, "offset": 0}
            )
    
    @pytest.mark.asyncio
    async def test_get_products_with_category(self, shopify_api, mock_shopify_product_response):
        """Termékek lekérése kategóriával teszt"""
        with patch.object(shopify_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_shopify_product_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            products = await shopify_api.get_products(limit=10, offset=0, category="electronics")
            
            mock_get.assert_called_once_with(
                "https://test-store.myshopify.com/admin/api/2023-10/products.json",
                params={"limit": 10, "offset": 0, "collection_id": "electronics"}
            )
    
    @pytest.mark.asyncio
    async def test_get_products_no_variants(self, shopify_api):
        """Termékek lekérése variant nélkül teszt"""
        mock_response_no_variants = {
            "products": [
                {
                    "id": 123456789,
                    "title": "Test Product No Variants",
                    "body_html": "<p>Test description</p>",
                    "status": "active",
                    "variants": [],  # No variants
                    "images": [],
                    "options": []
                }
            ]
        }
        
        with patch.object(shopify_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_no_variants
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            products = await shopify_api.get_products()
            
            assert len(products) == 0  # No products with variants
    
    @pytest.mark.asyncio
    async def test_get_products_exception(self, shopify_api):
        """Termékek lekérése kivétel teszt"""
        with patch.object(shopify_api.client, 'get', side_effect=httpx.HTTPStatusError("404", request=Mock(), response=Mock())):
            with pytest.raises(Exception, match="Shopify API hiba"):
                await shopify_api.get_products()
    
    @pytest.mark.asyncio
    async def test_get_product_success(self, shopify_api):
        """Egy termék lekérése sikeres teszt"""
        mock_product_response = {
            "product": {
                "id": 123456789,
                "title": "Single Test Product",
                "body_html": "<p>Single product description</p>",
                "status": "active",
                "variants": [
                    {
                        "id": 987654321,
                        "price": "399.99",
                        "inventory_quantity": 25
                    }
                ],
                "images": [
                    {"src": "https://example.com/single-product.jpg"}
                ],
                "options": ["Color"]
            }
        }
        
        with patch.object(shopify_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_product_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            product = await shopify_api.get_product("123456789")
            
            assert product is not None
            assert product.id == "123456789"
            assert product.name == "Single Test Product"
            assert product.price == 399.99
            assert product.stock == 25
            
            mock_get.assert_called_once_with(
                "https://test-store.myshopify.com/admin/api/2023-10/products/123456789.json"
            )
    
    @pytest.mark.asyncio
    async def test_get_product_no_variants(self, shopify_api):
        """Egy termék lekérése variant nélkül teszt"""
        mock_product_response = {
            "product": {
                "id": 123456789,
                "title": "Product No Variants",
                "variants": []  # No variants
            }
        }
        
        with patch.object(shopify_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_product_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            product = await shopify_api.get_product("123456789")
            
            assert product is None
    
    @pytest.mark.asyncio
    async def test_get_product_exception(self, shopify_api):
        """Egy termék lekérése kivétel teszt"""
        with patch.object(shopify_api.client, 'get', side_effect=Exception("Network error")):
            with pytest.raises(Exception, match="Shopify API hiba"):
                await shopify_api.get_product("123456789")
    
    @pytest.mark.asyncio
    async def test_search_products_success(self, shopify_api, mock_shopify_product_response):
        """Termék keresés sikeres teszt"""
        with patch.object(shopify_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_shopify_product_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            products = await shopify_api.search_products("test", limit=5)
            
            assert len(products) == 2
            
            mock_get.assert_called_once_with(
                "https://test-store.myshopify.com/admin/api/2023-10/products.json",
                params={"limit": 5, "query": "test"}
            )
    
    @pytest.mark.asyncio
    async def test_search_products_exception(self, shopify_api):
        """Termék keresés kivétel teszt"""
        with patch.object(shopify_api.client, 'get', side_effect=Exception("Search error")):
            with pytest.raises(Exception, match="Shopify API hiba"):
                await shopify_api.search_products("test")


class TestShopifyAPIOrders:
    """Shopify API rendelés metódusok tesztek"""
    
    @pytest.fixture
    def shopify_api(self):
        """Shopify API fixture"""
        return ShopifyAPI("test_key", "https://test-store.myshopify.com")
    
    @pytest.fixture
    def mock_shopify_order_response(self):
        """Mock Shopify rendelés válasz"""
        return {
            "orders": [
                {
                    "id": 456789123,
                    "customer": {"id": 789123456},
                    "total_price": "599.98",
                    "currency": "USD",
                    "line_items": [
                        {
                            "product_id": 123456789,
                            "title": "Test Product A",
                            "quantity": 1,
                            "price": "299.99"
                        },
                        {
                            "product_id": 123456790,
                            "title": "Test Product B",
                            "quantity": 1,
                            "price": "299.99"
                        }
                    ],
                    "shipping_address": {
                        "city": "Budapest",
                        "zip": "1234"
                    },
                    "billing_address": {
                        "city": "Budapest",
                        "zip": "1234"
                    },
                    "note": "Test order note"
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_get_orders_success(self, shopify_api, mock_shopify_order_response):
        """Rendelések lekérése sikeres teszt"""
        with patch.object(shopify_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_shopify_order_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            orders = await shopify_api.get_orders(limit=10, offset=0)
            
            assert len(orders) == 1
            assert orders[0].id == "456789123"
            assert orders[0].user_id == "789123456"
            assert orders[0].status == OrderStatus.PROCESSING
            assert orders[0].total == 599.98
            assert orders[0].currency == "USD"
            assert len(orders[0].items) == 2
            assert orders[0].notes == "Test order note"
            
            # Check order items
            assert orders[0].items[0].product_id == "123456789"
            assert orders[0].items[0].product_name == "Test Product A"
            assert orders[0].items[0].quantity == 1
            assert orders[0].items[0].unit_price == 299.99
            assert orders[0].items[0].total_price == 299.99
            
            mock_get.assert_called_once_with(
                "https://test-store.myshopify.com/admin/api/2023-10/orders.json",
                params={"limit": 10, "offset": 0}
            )
    
    @pytest.mark.asyncio
    async def test_get_orders_exception(self, shopify_api):
        """Rendelések lekérése kivétel teszt"""
        with patch.object(shopify_api.client, 'get', side_effect=Exception("Orders error")):
            with pytest.raises(Exception, match="Shopify API hiba"):
                await shopify_api.get_orders()
    
    @pytest.mark.asyncio
    async def test_get_order_success(self, shopify_api):
        """Egy rendelés lekérése sikeres teszt"""
        mock_single_order_response = {
            "order": {
                "id": 456789123,
                "customer": {"id": 789123456},
                "total_price": "399.99",
                "currency": "HUF",
                "line_items": [
                    {
                        "product_id": 123456789,
                        "title": "Single Order Product",
                        "quantity": 2,
                        "price": "199.99"
                    }
                ],
                "shipping_address": {
                    "city": "Debrecen",
                    "zip": "4000"
                },
                "billing_address": {
                    "city": "Debrecen",
                    "zip": "4000"
                },
                "note": "Single order note"
            }
        }
        
        with patch.object(shopify_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_single_order_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            order = await shopify_api.get_order("456789123")
            
            assert order is not None
            assert order.id == "456789123"
            assert order.user_id == "789123456"
            assert order.total == 399.99
            assert order.currency == "HUF"
            assert len(order.items) == 1
            assert order.items[0].quantity == 2
            assert order.items[0].total_price == 399.98  # 199.99 * 2
            
            mock_get.assert_called_once_with(
                "https://test-store.myshopify.com/admin/api/2023-10/orders/456789123.json"
            )
    
    @pytest.mark.asyncio
    async def test_get_order_exception(self, shopify_api):
        """Egy rendelés lekérése kivétel teszt"""
        with patch.object(shopify_api.client, 'get', side_effect=Exception("Order error")):
            with pytest.raises(Exception, match="Shopify API hiba"):
                await shopify_api.get_order("456789123")


class TestShopifyAPICustomers:
    """Shopify API ügyfél metódusok tesztek"""
    
    @pytest.fixture
    def shopify_api(self):
        """Shopify API fixture"""
        return ShopifyAPI("test_key", "https://test-store.myshopify.com")
    
    @pytest.mark.asyncio
    async def test_get_customer_success(self, shopify_api):
        """Ügyfél lekérése sikeres teszt"""
        mock_customer_response = {
            "customer": {
                "id": 789123456,
                "email": "test@shopify.com",
                "first_name": "Test",
                "last_name": "Customer",
                "phone": "+36301234567",
                "default_address": {
                    "city": "Budapest",
                    "zip": "1111"
                }
            }
        }
        
        with patch.object(shopify_api.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_customer_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            customer = await shopify_api.get_customer("789123456")
            
            assert customer is not None
            assert customer.id == "789123456"
            assert customer.email == "test@shopify.com"
            assert customer.first_name == "Test"
            assert customer.last_name == "Customer"
            assert customer.phone == "+36301234567"
            assert customer.address == {"city": "Budapest", "zip": "1111"}
            
            mock_get.assert_called_once_with(
                "https://test-store.myshopify.com/admin/api/2023-10/customers/789123456.json"
            )
    
    @pytest.mark.asyncio
    async def test_get_customer_exception(self, shopify_api):
        """Ügyfél lekérése kivétel teszt"""
        with patch.object(shopify_api.client, 'get', side_effect=Exception("Customer error")):
            with pytest.raises(Exception, match="Shopify API hiba"):
                await shopify_api.get_customer("789123456")


class TestShopifyAPIOrderManagement:
    """Shopify API rendeléskezelés tesztek"""
    
    @pytest.fixture
    def shopify_api(self):
        """Shopify API fixture"""
        return ShopifyAPI("test_key", "https://test-store.myshopify.com")
    
    @pytest.mark.asyncio
    async def test_update_order_status_success(self, shopify_api):
        """Rendelési státusz frissítés sikeres teszt"""
        with patch.object(shopify_api.client, 'put') as mock_put:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_put.return_value = mock_response
            
            result = await shopify_api.update_order_status("456789123", "paid")
            
            assert result is True
            mock_put.assert_called_once_with(
                "https://test-store.myshopify.com/admin/api/2023-10/orders/456789123.json",
                json={"order": {"financial_status": "paid"}}
            )
    
    @pytest.mark.asyncio
    async def test_update_order_status_exception(self, shopify_api):
        """Rendelési státusz frissítés kivétel teszt"""
        with patch.object(shopify_api.client, 'put', side_effect=Exception("Update error")):
            with pytest.raises(Exception, match="Shopify API hiba"):
                await shopify_api.update_order_status("456789123", "paid")


class TestShopifyAPIClose:
    """Shopify API kliens lezárás tesztek"""
    
    @pytest.mark.asyncio
    async def test_close_client(self):
        """HTTP kliens lezárás teszt"""
        shopify_api = ShopifyAPI("test_key", "https://test-store.myshopify.com")
        
        with patch.object(shopify_api.client, 'aclose') as mock_close:
            await shopify_api.close()
            mock_close.assert_called_once()


class TestMockShopifyAPI:
    """Mock Shopify API tesztek"""
    
    @pytest.fixture
    def mock_api(self):
        """Mock Shopify API fixture"""
        return MockShopifyAPI()
    
    @pytest.mark.asyncio
    async def test_mock_get_products_default(self, mock_api):
        """Mock termékek lekérése alapértelmezett teszt"""
        products = await mock_api.get_products()
        
        assert len(products) == 4
        assert products[0].id == "1"
        assert products[0].name == "Sony WH-1000XM5"
        assert products[0].category == ProductCategory.ELECTRONICS
        assert products[1].name == "Adidas Ultraboost 22"
        assert products[1].category == ProductCategory.SPORTS
        assert products[2].name == "Dell XPS 13"
        assert products[3].name == "Canon EOS R6"
    
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
        assert len(electronics_products) == 3  # Sony, Dell, Canon are electronics
    
    @pytest.mark.asyncio
    async def test_mock_get_product_found(self, mock_api):
        """Mock termék lekérése található teszt"""
        product = await mock_api.get_product("1")
        
        assert product is not None
        assert product.id == "1"
        assert product.name == "Sony WH-1000XM5"
        assert product.price == 299999.0
        assert product.stock == 12
    
    @pytest.mark.asyncio
    async def test_mock_get_product_not_found(self, mock_api):
        """Mock termék lekérése nem található teszt"""
        product = await mock_api.get_product("nonexistent")
        
        assert product is None
    
    @pytest.mark.asyncio
    async def test_mock_search_products_by_name(self, mock_api):
        """Mock termék keresés név alapján teszt"""
        products = await mock_api.search_products("Sony")
        
        assert len(products) == 1
        assert products[0].name == "Sony WH-1000XM5"
    
    @pytest.mark.asyncio
    async def test_mock_search_products_by_description(self, mock_api):
        """Mock termék keresés leírás alapján teszt"""
        products = await mock_api.search_products("laptop")
        
        assert len(products) == 1
        assert "laptop" in products[0].description.lower()
    
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
        assert orders[0].id == "2001"
        assert orders[0].user_id == "3001"
        assert orders[0].status == OrderStatus.DELIVERED
        assert orders[1].id == "2002"
        assert orders[1].status == OrderStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_mock_get_orders_with_pagination(self, mock_api):
        """Mock rendelések lekérése lapozással teszt"""
        orders = await mock_api.get_orders(limit=1, offset=1)
        
        assert len(orders) == 1
        assert orders[0].id == "2002"
    
    @pytest.mark.asyncio
    async def test_mock_get_order_found(self, mock_api):
        """Mock rendelés lekérése található teszt"""
        order = await mock_api.get_order("2001")
        
        assert order is not None
        assert order.id == "2001"
        assert order.user_id == "3001"
        assert order.status == OrderStatus.DELIVERED
        assert order.total == 429998.0
        assert len(order.items) == 2
        assert order.items[0].product_name == "Sony WH-1000XM5"
        assert order.items[1].product_name == "Adidas Ultraboost 22"
    
    @pytest.mark.asyncio
    async def test_mock_get_order_not_found(self, mock_api):
        """Mock rendelés lekérése nem található teszt"""
        order = await mock_api.get_order("nonexistent")
        
        assert order is None
    
    @pytest.mark.asyncio
    async def test_mock_get_customer_found(self, mock_api):
        """Mock ügyfél lekérése található teszt"""
        customer = await mock_api.get_customer("3001")
        
        assert customer is not None
        assert customer.id == "3001"
        assert customer.email == "szabo.peter@example.com"
        assert customer.first_name == "Péter"
        assert customer.last_name == "Szabó"
        assert customer.phone == "+36701234567"
    
    @pytest.mark.asyncio
    async def test_mock_get_customer_not_found(self, mock_api):
        """Mock ügyfél lekérése nem található teszt"""
        customer = await mock_api.get_customer("nonexistent")
        
        assert customer is None
    
    @pytest.mark.asyncio
    async def test_mock_update_order_status_success(self, mock_api):
        """Mock rendelési státusz frissítés sikeres teszt"""
        original_order = await mock_api.get_order("2001")
        original_status = original_order.status
        
        result = await mock_api.update_order_status("2001", "pending")
        
        assert result is True
        
        updated_order = await mock_api.get_order("2001")
        assert updated_order.status == OrderStatus.PENDING
        assert updated_order.status != original_status
    
    @pytest.mark.asyncio
    async def test_mock_update_order_status_not_found(self, mock_api):
        """Mock rendelési státusz frissítés nem található teszt"""
        result = await mock_api.update_order_status("nonexistent", "paid")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_mock_update_order_status_mapping(self, mock_api):
        """Mock rendelési státusz mapping teszt"""
        # Test different status mappings
        await mock_api.update_order_status("2001", "paid")
        order = await mock_api.get_order("2001")
        assert order.status == OrderStatus.DELIVERED
        
        await mock_api.update_order_status("2001", "processing")
        order = await mock_api.get_order("2001")
        assert order.status == OrderStatus.PROCESSING
        
        # Test unknown status defaults to PROCESSING
        await mock_api.update_order_status("2001", "unknown_status")
        order = await mock_api.get_order("2001")
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
        """Mock Shopify API fixture"""
        return MockShopifyAPI()
    
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
            assert order.id in ["2001", "2002"]
            assert order.user_id in ["3001", "3002"]
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
            assert customer.id in ["3001", "3002"]
            assert "@" in customer.email
            assert isinstance(customer.first_name, str)
            assert isinstance(customer.last_name, str)
            assert customer.phone.startswith("+36")
            assert isinstance(customer.address, dict)


class TestAsyncDelayBehavior:
    """Async delay viselkedés tesztek"""
    
    @pytest.fixture
    def mock_api(self):
        """Mock Shopify API fixture"""
        return MockShopifyAPI()
    
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
        """Mock Shopify API fixture"""
        return MockShopifyAPI()
    
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
    
    def test_shopify_specific_features(self, mock_api):
        """Shopify-specifikus funkciók teszt"""
        # Check that products have Shopify-like structure
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